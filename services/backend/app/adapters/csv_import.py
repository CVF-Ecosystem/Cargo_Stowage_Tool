"""Strict CSV preview; no workspace mutation."""
import csv
import io
import re
from pydantic import BaseModel, ValidationError
from ..domain.model import CargoUnit, Plan

HEADERS = ['id','name','kind','requirement','length_mm','width_mm','height_mm','mass_kg']

class CsvRequest(BaseModel):
    plan: Plan
    csv_text: str

class CsvError(BaseModel):
    row: int
    field: str
    message: str

class CsvPreview(BaseModel):
    valid: bool
    errors: list[CsvError]
    count: int
    total_mass_g: int
    candidate: Plan | None


def preview(payload: CsvRequest) -> CsvPreview:
    errors = []
    units = []
    def err(row, field, message):
        errors.append(CsvError(row=row, field=field, message=message))
    try:
        if len(payload.csv_text.encode('utf-8')) > 1_048_576:
            err(0, 'file', 'Tệp CSV vượt 1 MiB.')
            return CsvPreview(valid=False, errors=errors, count=0, total_mass_g=0, candidate=None)
        reader = csv.reader(io.StringIO(payload.csv_text.lstrip('\ufeff'), newline=''), strict=True)
        header = next(reader, None)
        if header != HEADERS:
            err(1, 'header', 'Header CSV không đúng thứ tự hoặc tên trường.')
            return CsvPreview(valid=False, errors=errors, count=0, total_mass_g=0, candidate=None)
        ids = set()
        previous_line = 1
        for row_count, fields in enumerate(reader, start=1):
            number = previous_line + 1
            previous_line = reader.line_num
            if row_count > 200:
                err(number, 'row', 'Tối đa 200 dòng hàng.')
                break
            if len(fields) != len(HEADERS):
                err(number, 'row', 'Dòng phải có đúng 8 trường.')
                continue
            d = dict(zip(HEADERS, fields))
            bad = False
            for k in ('length_mm','width_mm','height_mm'):
                if not re.fullmatch(r'[0-9]+', d[k]):
                    err(number,k,'Cần số nguyên dương mm.'); bad=True
                else:
                    d[k]=int(d[k])
            mass=d.pop('mass_kg')
            if not re.fullmatch(r'[0-9]+(?:\.[0-9]{1,3})?',mass):
                err(number,'mass_kg','Cần kg dấu chấm, tối đa 3 chữ số thập phân.'); bad=True
            else:
                parts=mass.split('.')
                d['mass_g']=int(parts[0])*1000+int((parts[1] if len(parts)>1 else '').ljust(3,'0'))
            if d['id'] in ids:
                err(number,'id','ID bị trùng.'); bad=True
            ids.add(d['id'])
            try:
                unit = CargoUnit.model_validate(d)
            except ValidationError as e:
                for item in e.errors():
                    key = str(item['loc'][0])
                    field = 'mass_kg' if key == 'mass_g' else key
                    if not any(x.row == number and x.field == field for x in errors):
                        err(number, field, 'Giá trị không hợp lệ.')
                bad = True
            if not bad:
                units.append(unit)
        if not units and not errors:
            err(2, 'row', 'CSV cần ít nhất một dòng hàng.')
        if errors:
            return CsvPreview(valid=False,errors=errors,count=0,total_mass_g=0,candidate=None)
        candidate = payload.plan.model_dump()
        candidate.update(contract_version='scst.m2a.v1', cargo_source='USER_ENTERED', units=[u.model_dump() for u in units], placements=[])
        return CsvPreview(valid=True,errors=[],count=len(units),total_mass_g=sum(u.mass_g for u in units),candidate=Plan.model_validate(candidate))
    except (csv.Error, UnicodeError, OverflowError, ValueError):
        err(getattr(locals().get('reader'), 'line_num', 0), 'csv', 'CSV không hợp lệ.')
        return CsvPreview(valid=False,errors=errors,count=0,total_mass_g=0,candidate=None)
