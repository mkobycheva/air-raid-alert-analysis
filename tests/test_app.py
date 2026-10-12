import base64
import copy
import json
from pathlib import Path
import re
import shutil
import subprocess

import numpy as np
import pandas as pd
import pytest

from airalerts.appdata import NAME_MAP,UNMODELLED,pack_bits,unpack_bits,encode_frames,match_geometry,svg_geometry,assemble_html


def synthetic_frame(names=None):
    names=names or sorted(NAME_MAP)
    rows=[]
    for lead,count in [(1,3),(24,1)]:
        for t in pd.date_range('2026-08-01',periods=count,freq='h',tz='UTC'):
            for i,name in enumerate(names):
                p=[0.,.0005,.0497,.4996,.5,.9995,1.][i%7]
                rows.append({'oblast':name,'T':t,'lead':lead,'p':p,'y':i%2})
    return pd.DataFrame(rows)


def synthetic_geometry():
    features=[]
    for i,code in enumerate([v[0] for v in NAME_MAP.values()]+list(UNMODELLED)):
        x=22+i*.4;y=45+(i%4)*.5
        features.append({'properties':{'shapeISO':code},'geometry':{'type':'Polygon','coordinates':[[[x,y],[x+.3,y],[x+.3,y+.3],[x,y+.3],[x,y]]]}})
    return features


def fixture_html():
    names=sorted(NAME_MAP);frame=synthetic_frame(names);data=encode_frames(frame,names)
    for lead in data['leads']:
        lead.update(model='synthetic',brier=.1,bss_clim=.01,bss_ses=.02,ci={'clim':[-.01,.03],'ses':[-.01,.04]})
    data.update(test_start=data['leads'][0]['start'],test_end=data['leads'][1]['last']+25*3600000,commit='synthetic',
                geometry={'licence':'synthetic offline fixture','source':'https://example.invalid/attribution-text-only','sha256':'synthetic'})
    svg,viewbox,_=svg_geometry(names,synthetic_geometry())
    return assemble_html(Path('app/template.html').read_text(),data,svg,viewbox),data


def test_round_trip_fewer_lead_rows_and_exact_error_threshold():
    frame=synthetic_frame();data=encode_frames(frame,sorted(NAME_MAP))
    ordered=frame.sort_values(['lead','T','oblast'])
    decoded=np.frombuffer(base64.b64decode(data['probabilities']),dtype='<u2')/1000
    np.testing.assert_allclose(decoded,ordered.p,atol=.0005+1e-12,rtol=0)
    np.testing.assert_array_equal(unpack_bits(data['outcomes'],len(frame)),ordered.y)
    np.testing.assert_array_equal(unpack_bits(data['errors'],len(frame)),np.abs(ordered.p-ordered.y)>=.5)
    assert data['leads'][0]['count']==3 and data['leads'][1]['count']==1
    assert data['leads'][1]['last']==int(frame.loc[frame.lead.eq(24),'T'].max().timestamp()*1000)
    assert data['leads'][1]['start']+(data['leads'][1]['count']-1)*3600000==data['leads'][1]['last']
    assert data['states'] is None
    with pytest.raises(ValueError,match='Missing display cells'):encode_frames(frame.iloc[1:],sorted(NAME_MAP))


@pytest.mark.parametrize('count',[0,1,7,8,9,17])
def test_bit_packing_edges(count):
    bits=np.arange(count)%2
    np.testing.assert_array_equal(unpack_bits(pack_bits(bits),count),bits)


def test_name_mapping_and_failures():
    expected={'Cherkaska','Chernihivska','Chernivetska','Dnipropetrovska','Donetska','Ivano-Frankivska','Kharkivska','Khersonska','Khmelnytska','Kirovohradska','Kyivska','Lvivska','Mykolaivska','Odeska','Poltavska','Rivnenska','Sumska','Ternopilska','Vinnytska','Volynska','Zakarpatska','Zaporizka','Zhytomyrska'}
    assert set(NAME_MAP)=={name+' oblast' for name in expected}|{'Kyiv City'}
    assert len({code for code,label in NAME_MAP.values()})==24
    features=synthetic_geometry()
    assert len(match_geometry(sorted(NAME_MAP),features))==24
    with pytest.raises(ValueError,match='exactly one polygon'):match_geometry(sorted(NAME_MAP),features[1:])
    with pytest.raises(ValueError,match='exactly one polygon'):match_geometry(sorted(NAME_MAP),features+[copy.deepcopy(features[0])])


def test_deterministic_html_and_no_external_resources():
    html,_=fixture_html();again,_=fixture_html()
    assert html==again
    assert 'fetch(' not in html and 'XMLHttpRequest' not in html and 'localStorage' not in html
    assert not re.search(r'(?:src|href)\s*=\s*["\']https?://|url\(\s*["\']?https?://|import\s+.*https?://',html,re.I)
    assert len(html.encode())<2000000
    assert len(re.findall(r'<path[^>]+data-region=',html))==24
    assert 'id="kyiv-marker"' in html


def test_node_decode_render_synthetic(tmp_path):
    node=shutil.which('node')
    if not node:pytest.skip('Node unavailable; JS smoke not run')
    html,data=fixture_html()
    script=re.findall(r'<script>(.*?)</script>',html,re.S)[0]
    # Minimal offline DOM for the exact page script, not a reimplementation.
    harness=r'''
const fs=require('node:fs'),vm=require('node:vm');
const payload=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
class Element {constructor(){this.attrs={};this.children=[];this.style={};this.dataset={};this.value='1';this.textContent='';this.classList={toggle(){}};}setAttribute(k,v){this.attrs[k]=v;}append(...a){this.children.push(...a);}replaceChildren(...a){this.children=a;}addEventListener(k,f){this[k]=f;}}
const ids=new Map(),paths=Array.from({length:24},()=>new Element());
global.document={getElementById(id){if(!ids.has(id))ids.set(id,new Element());return ids.get(id);},createElement(){return new Element();},createTextNode(text){return text;},querySelectorAll(q){const m=q.match(/data-region="(\d+)"/);return m?[paths[+m[1]]]:[];}};
global.window={addEventListener(){}};
document.getElementById('display-data').textContent=JSON.stringify(payload);
vm.runInThisContext(fs.readFileSync(process.argv[3],'utf8'));
if(paths[0].attrs.fill!=='#90a4bd')throw Error('Synthetic frame has unexpected region fill');
if(viewer.probabilityColor(0)===viewer.probabilityColor(50))throw Error('Continuous colour scale collapsed into a bucket');
if(document.getElementById('slider').max!=='2')throw Error('Incorrect lead-1 slider range');
document.getElementById('lead').change({target:{value:'24'}});
if(document.getElementById('slider').max!=='0')throw Error('Withheld lead-24 tail extrapolated');
console.log('JS decode + render passed; known fill and lead-dependent slider bounds verified');
'''
    paths=[tmp_path/'data.json',tmp_path/'page.js',tmp_path/'smoke.cjs']
    paths[0].write_text(json.dumps(data));paths[1].write_text(script);paths[2].write_text(harness)
    result=subprocess.run([node,str(paths[2]),str(paths[0]),str(paths[1])],text=True,capture_output=True,check=True)
    assert 'passed' in result.stdout
