"""Fixed local technical derivative; source workbook is not accessed at runtime."""
import json
from pathlib import Path

PATH=Path(__file__).resolve().parents[2]/'data'/'pipe_list'/'baltimore.json'
REGISTRY=json.loads(PATH.read_text(encoding='utf-8'))
DATASET=REGISTRY['dataset_id']
GROUPS={g['group_id']:g for g in REGISTRY['groups']}

def units():
    result=[]
    for g in REGISTRY['groups']:
        for index in range(1,g['bundle_count']+1):
            row=g['source_row']; dims=g['dimensions_um']
            result.append({'id':f'PIPE-R{row:03d}-B{index:04d}', 'name':f'Ống thép nhóm {row:03d}', 'kind':'PIPE_BUNDLE','requirement':'optional', 'length_mm':(dims[0]+999)//1000,'width_mm':(dims[1]+999)//1000,'height_mm':(dims[2]+999)//1000,'mass_g':g['mass_g'], 'dimensions_um':dims,'source_ref':{'dataset_id':DATASET,'workbook_sha256':REGISTRY['workbook_sha256'],'sheet':REGISTRY['sheet'],'group_id':g['group_id'],'source_row':row,'bundle_index':index,'pieces':g['pieces_per_bundle'],'dimension_warning':g['dimension_warning']}})
    return result

EXPECTED={u['id']:u for u in units()}
