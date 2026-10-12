"""Pure display-data encoding and ADM1 SVG preparation; no modelling."""

import base64
from html import escape
import json
import math
from pathlib import Path
import re

import numpy as np
import pandas as pd

from airalerts.grid import _window

NAME_MAP: dict[str, tuple[str, str]] = {
    'Cherkaska oblast': ('UA-71', 'Черкаська область'),
    'Chernihivska oblast': ('UA-74', 'Чернігівська область'),
    'Chernivetska oblast': ('UA-77', 'Чернівецька область'),
    'Dnipropetrovska oblast': ('UA-12', 'Дніпропетровська область'),
    'Donetska oblast': ('UA-14', 'Донецька область'),
    'Ivano-Frankivska oblast': ('UA-26', 'Івано-Франківська область'),
    'Kharkivska oblast': ('UA-63', 'Харківська область'),
    'Khersonska oblast': ('UA-65', 'Херсонська область'),
    'Khmelnytska oblast': ('UA-68', 'Хмельницька область'),
    'Kirovohradska oblast': ('UA-35', 'Кіровоградська область'),
    'Kyiv City': ('UA-30', 'Київ'),
    'Kyivska oblast': ('UA-32', 'Київська область'),
    'Lvivska oblast': ('UA-46', 'Львівська область'),
    'Mykolaivska oblast': ('UA-48', 'Миколаївська область'),
    'Odeska oblast': ('UA-51', 'Одеська область'),
    'Poltavska oblast': ('UA-53', 'Полтавська область'),
    'Rivnenska oblast': ('UA-56', 'Рівненська область'),
    'Sumska oblast': ('UA-59', 'Сумська область'),
    'Ternopilska oblast': ('UA-61', 'Тернопільська область'),
    'Vinnytska oblast': ('UA-05', 'Вінницька область'),
    'Volynska oblast': ('UA-07', 'Волинська область'),
    'Zakarpatska oblast': ('UA-21', 'Закарпатська область'),
    'Zaporizka oblast': ('UA-23', 'Запорізька область'),
    'Zhytomyrska oblast': ('UA-18', 'Житомирська область'),
}
UNMODELLED = {'UA-09':'Луганська область', 'UA-43':'Крим', 'UA-40':'Севастополь'}


def pack_bits(values: np.ndarray) -> str:
    if not np.isin(values, [0,1]).all():
        raise ValueError('Binary data required')
    return base64.b64encode(np.packbits(values.astype(np.uint8),bitorder='little').tobytes()).decode('ascii')


def unpack_bits(encoded: str, count: int) -> np.ndarray:
    raw=np.frombuffer(base64.b64decode(encoded),dtype=np.uint8)
    if len(raw)!=(count+7)//8:raise ValueError('Bit-packed length differs')
    return np.unpackbits(raw,bitorder='little')[:count]


def encode_frames(frame: pd.DataFrame, names: list[str]) -> dict:
    if frame.duplicated(['lead','T','oblast']).any():raise ValueError('Duplicate display cells')
    if not np.isfinite(frame.p).all() or not frame.p.between(0,1).all():raise ValueError('Invalid probabilities')
    if not frame.y.isin([0,1]).all():raise ValueError('Invalid outcomes')
    ordered=[]; leads=[]; offset=0
    for lead,rows in frame.groupby('lead',sort=True):
        times=pd.DatetimeIndex(sorted(rows['T'].unique()))
        if any(times!=times.floor('h')) or any(times[1:]-times[:-1]!=pd.Timedelta(hours=1)):
            raise ValueError('Display times must be consecutive whole UTC hours')
        index=pd.MultiIndex.from_product([times,names],names=['T','oblast'])
        rows=rows.set_index(['T','oblast'])
        if len(rows)!=len(index) or set(rows.index)!=set(index):raise ValueError('Missing display cells; no filling allowed')
        aligned=rows.reindex(index)
        ordered.append(aligned)
        leads.append({'lead':int(lead),'start':int(times[0].timestamp()*1000),'count':len(times),'offset':offset,
                      'last':int(times[-1].timestamp()*1000)})
        offset+=len(aligned)
    combined=pd.concat(ordered,ignore_index=True)
    values=np.rint(combined.p.to_numpy()*1000).astype('<u2')
    probabilities=base64.b64encode(values.tobytes()).decode('ascii')
    decoded=np.frombuffer(base64.b64decode(probabilities),dtype='<u2').astype(float)/1000
    if np.max(np.abs(decoded-combined.p.to_numpy()))>.0005+1e-12:
        raise ValueError('Probability round trip exceeds per-mille tolerance')
    outcomes=pack_bits(combined.y.to_numpy())
    if not np.array_equal(unpack_bits(outcomes,len(combined)),combined.y.to_numpy()):
        raise ValueError('Outcome round trip failed')
    # Preserve the requested error threshold exactly despite probability rounding.
    errors=pack_bits((np.abs(combined.p.to_numpy()-combined.y.to_numpy())>=.5).astype(np.uint8))
    state_column=next((c for c in ['state_at_T','active_now','state'] if c in combined),None)
    return {'regions':[{'name':name,'label':NAME_MAP[name][1]} for name in names], 'leads':leads,
            'probabilities':probabilities,'outcomes':outcomes,'errors':errors,
            'states':pack_bits(combined[state_column].to_numpy()) if state_column else None,
            'cells':len(combined),'encoding':'little-endian uint16 per-mille; little-bit-order outcomes/errors'}


def match_geometry(names: list[str], features: list[dict]) -> dict[str, dict]:
    if len(names)!=len(set(names)) or set(names)-set(NAME_MAP):raise ValueError('Unknown/duplicate panel name')
    found={}
    for name in names:
        code=NAME_MAP[name][0]
        candidates=[f for f in features if (f['properties'].get('iso_3166_2') or f['properties'].get('shapeISO'))==code]
        if len(candidates)!=1:raise ValueError(f'{name}: need exactly one polygon for {code}, found {len(candidates)}')
        if code in found:raise ValueError('A polygon is matched twice')
        found[code]=candidates[0]
    return found


def rings(geometry: dict) -> list[list[list[float]]]:
    if geometry['type']=='Polygon':return geometry['coordinates']
    if geometry['type']=='MultiPolygon':return [ring for polygon in geometry['coordinates'] for ring in polygon]
    raise ValueError('Polygon/MultiPolygon geometry required')


def rdp(points: list[tuple[float,float]], tolerance: float) -> list[tuple[float,float]]:
    """Iterative Ramer–Douglas–Peucker; retains endpoints deterministically."""
    keep={0,len(points)-1}; stack=[(0,len(points)-1)]
    while stack:
        first,last=stack.pop()
        ax,ay=points[first];bx,by=points[last];dx,dy=bx-ax,by-ay;length=dx*dx+dy*dy
        maximum=0.; chosen=None
        for i in range(first+1,last):
            x,y=points[i];ratio=max(0.,min(1.,((x-ax)*dx+(y-ay)*dy)/length)) if length else 0.
            distance=(x-ax-ratio*dx)**2+(y-ay-ratio*dy)**2
            if distance>maximum:maximum=distance;chosen=i
        if chosen is not None and maximum>tolerance*tolerance:
            keep.add(chosen);stack.extend([(first,chosen),(chosen,last)])
    return [points[i] for i in sorted(keep)]


def simplify_ring(points: list[tuple[float,float]], tolerance: float) -> list[tuple[float,float]]:
    if points[0]==points[-1]:points=points[:-1]
    if len(points)<3:raise ValueError('Degenerate source ring')
    pivot=max(range(1,len(points)),key=lambda i:(points[i][0]-points[0][0])**2+(points[i][1]-points[0][1])**2)
    result=rdp(points[:pivot+1],tolerance)[:-1]+rdp(points[pivot:]+[points[0]],tolerance)
    return result if len(set(result))>=3 else points+[points[0]]


def svg_geometry(names: list[str], features: list[dict], tolerance: float=.8) -> tuple[str,str,int]:
    matched=match_geometry(names,features)
    for code in UNMODELLED:
        candidates=[f for f in features if (f['properties'].get('iso_3166_2') or f['properties'].get('shapeISO'))==code]
        if len(candidates)!=1:raise ValueError(f'Missing/duplicate unmodelled polygon {code}')
        matched[code]=candidates[0]
    cosine=math.cos(math.radians(49))
    coordinates=[(point[0]*cosine,-point[1]) for f in matched.values() for ring in rings(f['geometry']) for point in ring]
    minx,maxx=min(p[0] for p in coordinates),max(p[0] for p in coordinates)
    miny,maxy=min(p[1] for p in coordinates),max(p[1] for p in coordinates)
    scale=940/(maxx-minx);height=(maxy-miny)*scale+60
    def project(point):return ((point[0]*cosine-minx)*scale+30,(-point[1]-miny)*scale+30)
    paths=[];path_bytes=0;centers={}
    for code,f in matched.items():
        paths_data=[];points_all=[]
        for ring in rings(f['geometry']):
            points=[project(point) for point in ring];points_all.extend(points)
            simple=simplify_ring(points,tolerance)
            paths_data.append('M'+'L'.join(f'{x:.1f},{y:.1f}' for x,y in simple[:-1])+'Z')
        d=''.join(paths_data);path_bytes+=len(d.encode())
        centers[code]=((min(x for x,y in points_all)+max(x for x,y in points_all))/2,(min(y for x,y in points_all)+max(y for x,y in points_all))/2)
        if code in UNMODELLED:
            label=UNMODELLED[code]
            paths.append(f'<path class="neutral" d="{d}" fill="url(#unmodelled)" fill-rule="evenodd" tabindex="0" role="button" aria-label="{escape(label)}: не моделюється" data-neutral="{escape(label)}"/>')
        else:
            name=next(n for n in names if NAME_MAP[n][0]==code);index=names.index(name)
            paths.append(f'<path id="region-{index}" class="region" data-region="{index}" d="{d}" fill-rule="evenodd" tabindex="0" role="button" aria-label="{escape(NAME_MAP[name][1])}"/>')
    for code in ['UA-09','UA-43']:
        x,y=centers[code]
        paths.append(f'<text class="neutral-label" x="{x:.1f}" y="{y:.1f}" text-anchor="middle">{UNMODELLED[code]}<tspan x="{x:.1f}" dy="21">не моделюється</tspan></text>')
    x,y=centers['UA-30'];index=names.index('Kyiv City');cx,cy=x+20,y-30
    paths.extend([f'<line class="city-leader" x1="{x:.1f}" y1="{y:.1f}" x2="{cx:.1f}" y2="{cy:.1f}"/>',
        f'<circle id="kyiv-marker" class="region city-marker" data-region="{index}" cx="{cx:.1f}" cy="{cy:.1f}" r="14" tabindex="0" role="button" aria-label="Київ"/>',
        f'<text class="city-label" x="{cx+20:.1f}" y="{cy+6:.1f}">Київ</text>'])
    if path_bytes>150000:raise ValueError(f'SVG path data {path_bytes} exceeds 150 KB')
    return '\n'.join(paths),f'0 0 1000 {height:.1f}',path_bytes


def assemble_html(template: str, payload: dict, svg: str, viewbox: str) -> str:
    data=json.dumps(payload,ensure_ascii=False,separators=(',',':'),allow_nan=False).replace('<','\\u003c')
    html=template.replace('@@SVG@@',svg).replace('@@VIEWBOX@@',viewbox).replace('@@DATA@@',data)
    if re.search(r'@@[A-Z]+@@',html):raise ValueError('Unfilled template marker')
    if len(html.encode('utf-8'))>2000000:raise ValueError(f'HTML {len(html.encode())} exceeds 2 MB; do not shrink silently')
    return html


def load_payload(predictions: Path,metrics_path: Path,bootstrap_path: Path,config_path: Path,state_path: Path) -> tuple[dict,list[str]]:
    frame=pd.read_csv(predictions,parse_dates=['T'],low_memory=False)
    required={'oblast','T','p','y','lead','model','run_id','git_commit'}
    if not required<=set(frame) or len(frame)!=181152:raise ValueError('STOP: prediction schema/row count differs')
    if set(frame.lead)!={0,1,2,3,4,5,6,12,24} or set(frame.oblast)!=set(NAME_MAP):raise ValueError('Unexpected TEST leads/oblasts')
    config=json.loads(config_path.read_text());state=json.loads(state_path.read_text())
    start,end=_window(state['test_start'],state['test_end'])
    if start!=pd.Timestamp(config['test_start'],tz='UTC') or not frame.git_commit.eq(state['commit']).all():raise ValueError('TEST/commit provenance differs')
    if not frame.run_id.eq(state['run_id']).all() or state['status']!='complete':raise ValueError('FINAL run mismatch/incomplete')
    if frame['T'].lt(start).any() or (frame['T']+pd.to_timedelta(frame.lead+1,unit='h')).gt(end).any():raise ValueError('Only TEST target windows may be displayed')
    names=sorted(frame.oblast.unique());payload=encode_frames(frame,names)
    metrics=pd.read_csv(metrics_path);intervals=pd.read_csv(bootstrap_path)
    for item in payload['leads']:
        k=item['lead'];model=config['models'][str(k)]['model']
        if not frame.loc[frame.lead.eq(k),'model'].eq(model).all():raise ValueError('Saved/frozen model differs')
        row=metrics.loc[metrics.lead.eq(k)&metrics.scope.eq('ALL')&metrics.fold_id.eq('test')]
        if len(row)!=1 or row.iloc[0].run_id!=state['run_id']:raise ValueError('TEST summary mismatch')
        row=row.iloc[0]
        ci={}
        for reference in ['clim','ses']:
            values=intervals.loc[intervals.lead.eq(k)&intervals.scope.eq('ALL')&intervals.reference.eq(reference)]
            if len(values)!=1:raise ValueError('Missing/duplicate pooled CI')
            ci[reference]=[float(values.iloc[0].low),float(values.iloc[0].high)]
        item.update(model=model,brier=float(row.brier),bss_clim=float(row.bss_vs_clim),bss_ses=float(row.bss_vs_ses),ci=ci)
    payload.update(test_start=int(start.timestamp()*1000),test_end=int(end.timestamp()*1000),commit=state['commit'])
    return payload,names
