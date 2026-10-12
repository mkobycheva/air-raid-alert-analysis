"""Build a self-contained retrospective TEST viewer; never fits or predicts."""

import argparse
import hashlib
import json
from pathlib import Path

from airalerts.appdata import NAME_MAP,load_payload,svg_geometry,assemble_html


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--predictions',type=Path,default=Path('data/processed/predictions/final_test.csv.gz'))
    parser.add_argument('--metrics',type=Path,default=Path('reports/model/final_test_metrics.csv'))
    parser.add_argument('--bootstrap',type=Path,default=Path('reports/model/final_test_bootstrap.csv'))
    parser.add_argument('--config',type=Path,default=Path('config/final_config.json'))
    parser.add_argument('--state',type=Path,default=Path('data/processed/predictions/final_checkpoint/state.json'))
    parser.add_argument('--geometry',type=Path,default=Path('geoBoundaries-UKR-ADM1.geojson'))
    parser.add_argument('--metadata',type=Path,default=Path('metadata-geoboundaries-ukr-adm1-geojson.json'))
    parser.add_argument('--source-url',help='Exact supplied boundary download URL; used as attribution text only')
    parser.add_argument('--licence',default='geoBoundaries / William & Mary geoLab, gbOpen — CC BY 4.0',help='Supplied boundary licence and attribution')
    parser.add_argument('--output',type=Path,default=Path('docs/index.html'))
    args=parser.parse_args()
    payload,names=load_payload(args.predictions,args.metrics,args.bootstrap,args.config,args.state)
    if not args.geometry.exists():
        raise SystemExit(f'STOP: place a Ukraine ADM1 GeoJSON (including Kyiv City) at {args.geometry}; no download will be attempted')
    source=args.source_url
    if source is None:
        source=json.loads(args.metadata.read_text()).get('download_url')
    if not source:raise SystemExit('STOP: exact boundary download URL is required in metadata')
    raw=args.geometry.read_bytes();geometry=json.loads(raw)
    svg,viewbox,path_bytes=svg_geometry(names,geometry['features'])
    payload['geometry']={'source':source,'licence':args.licence,'sha256':hashlib.sha256(raw).hexdigest(),
                         'projection':'Equirectangular, standard parallel 49° N','simplification':'RDP, 0.8 SVG units; coordinates rounded to 0.1'}
    html=assemble_html(Path('app/template.html').read_text(),payload,svg,viewbox)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(html.encode('utf-8'))
    print(f'HTML={len(html.encode()):,} bytes; data JSON={len(json.dumps(payload,ensure_ascii=False,separators=(",",":")).encode()):,} bytes; SVG paths={path_bytes:,} bytes; raw geometry={len(raw):,} bytes')
    print('Geometry SHA256:',payload['geometry']['sha256'])
    for name in names:print(name,'|',NAME_MAP[name][0],'|',NAME_MAP[name][1])
    for lead in payload['leads']:print('lead',lead['lead'],'start_ms',lead['start'],'last_ms',lead['last'],'frames',lead['count'])


if __name__=='__main__':main()
