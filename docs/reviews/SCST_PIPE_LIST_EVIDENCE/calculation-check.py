from pathlib import Path
import importlib.util,json,hashlib
from decimal import Decimal,ROUND_HALF_UP,getcontext
from zipfile import ZipFile
from xml.etree import ElementTree as ET
getcontext().prec=40
base=Path('VINAFCO268_LOCAL_HANDOFF_V1_1')
manifest=json.loads((base/'MANIFEST.json').read_text(encoding='utf8'))
for entry in manifest['files']:
 raw=(base/entry['path']).read_bytes();assert len(raw)==entry['size_bytes'];assert hashlib.sha256(raw).hexdigest()==entry['sha256']
xlsx=base/'source/LIST_BALTIMORE_HOA_PHAT_NOV.xlsx'
spec=importlib.util.spec_from_file_location('source_import',base/'tools/import_cargo_list.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
data,report=mod.normalize(xlsx)
original=json.loads((base/'data/LIST_BALTIMORE_HOA_PHAT_NOV.normalized.json').read_text(encoding='utf8'))
assert data==original
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with ZipFile(xlsx) as z: xml=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
cells={c.attrib['r']:c for c in xml.findall('.//m:c',ns)}
def d(col,row): return Decimal(format(Decimal(cells[f'{col}{row}'].find('m:v',ns).text),'.15g'))
count=pipes=0;mass=Decimal(0);source_mass=Decimal(0);cbm=Decimal(0);source_cbm=Decimal(0);fractional=0;dims=[];rows=[]
for row,g in zip(range(2,33),data['groups']):
 n=int(d('M',row));per=int(d('L',row));assert per*n==d('N',row)==g['piece_count']
 bundle_g=d('K',row)*per*1000;assert bundle_g==int(bundle_g)
 assert (d('K',row)*per*n/1000).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)==d('O',row)
 values=[d(c,row) for c in 'IPQ'];um=[v*1000000 for v in values];assert all(v==int(v) for v in um)
 dims.extend(map(int,um));fractional+=sum(v*1000 != (v*1000).to_integral_value() for v in values)
 rows.append({'row':row,'bundles':n,'pipes_per_bundle':per,'bundle_mass_g':int(bundle_g),'dimensions_um':list(map(int,um)),'source_line_t':str(d('O',row))})
 count+=n;pipes+=n*per;mass+=bundle_g*n;source_mass+=d('O',row);cbm+=values[0]*values[1]*values[2]*n;source_cbm+=d('R',row)
conflicts=[g for g in data['groups'] if g['bundle']['geometry_status']=='needs_dimensions_review']
assert count==1076 and pipes==21226 and mass==1125551030 and source_mass==Decimal('1125.52')
assert cbm==Decimal('1157.54318105797')
assert sum(g['bundle_count'] for g in conflicts)==16
assert hashlib.sha256((base/'model/VINAFCO268_HN2642_3D.glb').read_bytes()).digest()==hashlib.sha256(Path('services/backend/data/vessels/vinafco268/model.glb').read_bytes()).digest()
result={'status':'PASS','scope':'Focused quantity, mass, dimensions and CBM calculation verification; not full spreadsheet audit','manifest_files_verified':len(manifest['files']),'normalized_rebuild_matches_supplied':True,'source_workbook_sha256':hashlib.sha256(xlsx.read_bytes()).hexdigest(),'supported_formula_checks':report['formula_checks']['supported_and_verified'],'formula_mismatches':report['formula_checks']['mismatches'],'groups':31,'bundles':count,'pipes':pipes,'calculated_bundle_basis':'K kg/pipe * L pipes/bundle, exact integer grams; no O/M allocation','calculated_mass_g':int(mass),'source_line_mass_t':str(source_mass),'difference_g':int(mass-source_mass*1000000),'source_cbm_m3':str(source_cbm),'computed_envelope_cbm_m3':str(cbm),'cbm_difference_m3':str(cbm-source_cbm),'exact_micrometre_dimensions':len(dims),'fractional_millimetre_dimensions':fractional,'dimension_review_rows':[g['source_row'] for g in conflicts],'dimension_review_bundles':16,'hull_glb_byte_identical':True,'rows':rows}
out=Path('docs/reviews/SCST_PIPE_LIST_EVIDENCE');out.mkdir(exist_ok=True,parents=True);(out/'calculation-receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False,indent=2))
