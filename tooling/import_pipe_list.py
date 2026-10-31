"""Derive local technical pipe registry from the supplied normalized source."""
import json
import hashlib
from decimal import Decimal, getcontext
getcontext().prec=40
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'VINAFCO268_LOCAL_HANDOFF_V1_1/data/LIST_BALTIMORE_HOA_PHAT_NOV.normalized.json'
target=ROOT/'services/backend/data/pipe_list/baltimore.json'
raw=source.read_bytes()
if hashlib.sha256(raw).hexdigest() != '8e212c52f3f9b5bf3a13e558b14be67a6c7adc64c977c06a27755f22f1cf4d05': raise ValueError('Unexpected normalized source hash')
data=json.loads(raw)
if data['source']['sha256'] != '66e51b53b07ea4be550e5705230de060829ff5cff92c8f4b89e36c4069757824': raise ValueError('Unexpected workbook hash')
groups=[]
for group in data['groups']:
    cells=group['source_cells']; row=group['source_row']
    def num(col): return Decimal(format(Decimal(cells[col]['raw_xml_value']),'.15g'))
    dims=[num(x)*1000000 for x in ('I','P','Q')]
    mass=num('K')*num('L')*1000
    if any(v!=v.to_integral_value() for v in [*dims,mass]): raise ValueError(f'Not integral at row {row}')
    groups.append({'group_id':group['id'],'source_row':row,'bundle_count':int(num('M')),'pieces_per_bundle':int(num('L')),'dimensions_um':[int(v) for v in dims],'mass_g':int(mass),'source_line_t':str(num('O')),'source_cbm_m3':str(num('R')),'envelope_cbm_m3':str(num('I')*num('P')*num('Q')*num('M')),'dimension_warning':'packaging_envelope_conflict' in group['issue_codes'],'issue_codes':group['issue_codes'],'outside_diameter_mm':str(num('E')),'wall_thickness_mm':str(num('G'))})
if len(groups)!=31 or sum(g['bundle_count'] for g in groups)!=1076 or sum(g['bundle_count']*g['pieces_per_bundle'] for g in groups)!=21226 or sum(g['bundle_count']*g['mass_g'] for g in groups)!=1125551030: raise ValueError('Unexpected source group totals')
if sum(Decimal(g['source_line_t']) for g in groups)!=Decimal('1125.52') or sum(Decimal(g['source_cbm_m3']) for g in groups)!=Decimal('1130.96964733156') or sum(Decimal(g['envelope_cbm_m3']) for g in groups)!=Decimal('1157.54318105797'): raise ValueError('Unexpected source mass or CBM totals')
result={'dataset_id':'BALTIMORE-PIPE-V1-1','workbook_sha256':data['source']['sha256'],'sheet':'Sheet1','assigned_vessel':None,'mass_basis':'K(kg/pipe) × L(pipes/bundle); calculated, not weighed','groups':groups,'source_mass_t':'1125.52','calculated_mass_t':'1125.55103','source_cbm_m3':'1130.96964733156','envelope_cbm_m3':'1157.54318105797'}
target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('wrote',target,'groups',len(groups),'bundles',sum(g['bundle_count'] for g in groups))
