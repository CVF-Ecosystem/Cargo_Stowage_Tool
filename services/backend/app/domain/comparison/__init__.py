"""Read-only exact comparison of two independently evaluated plans."""
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict
from ..model import Plan
from ..rules import evaluate

class CompareRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    before: Plan
    after: Plan

class FieldChange(BaseModel):
    field: str
    before: Any
    after: Any

class CompareSummary(BaseModel):
    manifest_mass_g: int
    placed_mass_g: int
    remaining_capacity_g: int
    placed_count: int
    unplaced_count: int
    excluded_count: int
    issue_count: int
    status: str
    basic_checks_passed: bool
    unchecked: list[str]
    operational_eligible: Literal[False] = False

class CompareDelta(BaseModel):
    manifest_mass_g: int
    placed_mass_g: int
    remaining_capacity_g: int
    placed_count: int
    unplaced_count: int
    excluded_count: int
    issue_count: int

class CompareRow(BaseModel):
    unit_id: str
    status: Literal['ADDED','REMOVED','CHANGED','UNCHANGED']
    changes: list[FieldChange]
    source_identity_warning: bool
    in_after: bool

class CompareResult(BaseModel):
    before: CompareSummary
    after: CompareSummary
    delta: CompareDelta
    context_changes: list[FieldChange]
    counts: dict[str,int]
    rows: list[CompareRow]


def flatten(data, prefix=''):
    output={}
    for key,value in data.items():
        path=f'{prefix}.{key}' if prefix else key
        if isinstance(value,dict): output.update(flatten(value,path))
        else: output[path]=value
    return output


def differences(before,after):
    return [FieldChange(field=k,before=before.get(k),after=after.get(k)) for k in sorted(set(before)|set(after)) if before.get(k)!=after.get(k)]


def summary(result):
    s=result.summary
    return CompareSummary(manifest_mass_g=s.manifest_mass_g,placed_mass_g=s.placed_mass_g,remaining_capacity_g=s.remaining_capacity_g,placed_count=s.placed_count,unplaced_count=len(s.unplaced_ids),excluded_count=len(s.excluded_ids),issue_count=result.total_issues if result.total_issues is not None else len(result.issues),status=result.status,basic_checks_passed=result.basic_checks_passed,unchecked=result.unchecked,operational_eligible=result.operational_eligible)


def context(plan):
    data=plan.model_dump(mode='json',exclude={'units','placements'})
    # Both absent and present vessel objects have predictable leaf names.
    vessel=data.pop('vessel')
    data['vessel']={'vessel_id':vessel['vessel_id'] if vessel else None,'case_id':vessel['case_id'] if vessel else None}
    return flatten(data)


def unit_details(unit,placement):
    if unit is None: return {}
    data=unit.model_dump(mode='json',exclude={'id'})
    data['placement']=placement.model_dump(mode='json',exclude={'unit_id'}) if placement else None
    return flatten(data)


def compare(before:Plan,after:Plan)->CompareResult:
    a=summary(evaluate(before));b=summary(evaluate(after))
    numeric=('manifest_mass_g','placed_mass_g','remaining_capacity_g','placed_count','unplaced_count','excluded_count','issue_count')
    delta=CompareDelta(**{field:getattr(b,field)-getattr(a,field) for field in numeric})
    au={u.id:u for u in before.units};bu={u.id:u for u in after.units}
    ap={p.unit_id:p for p in before.placements};bp={p.unit_id:p for p in after.placements}
    rows=[];counts={x:0 for x in ('ADDED','REMOVED','CHANGED','UNCHANGED')}
    for uid in sorted(set(au)|set(bu)):
        left=au.get(uid);right=bu.get(uid)
        changes=differences(unit_details(left,ap.get(uid)),unit_details(right,bp.get(uid)))
        status='ADDED' if left is None else 'REMOVED' if right is None else 'CHANGED' if changes else 'UNCHANGED'
        warning=bool(left is not None and right is not None and left.source_ref != right.source_ref)
        counts[status]+=1
        rows.append(CompareRow(unit_id=uid,status=status,changes=changes,source_identity_warning=warning,in_after=right is not None))
    return CompareResult(before=a,after=b,delta=delta,context_changes=differences(context(before),context(after)),counts=counts,rows=rows)
