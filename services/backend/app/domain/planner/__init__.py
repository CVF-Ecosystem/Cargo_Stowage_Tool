"""Deterministic, conservative single-layer guillotine suggestion; not an optimizer."""
from typing import Literal
from pydantic import BaseModel
from ..model import Evaluation, Placement, Plan
from ..rules import evaluate

class UnplacedReason(BaseModel):
    unit_id: str
    code: Literal['EXCLUDED','TOO_HIGH','FOOTPRINT_TOO_LARGE','MASS_LIMIT','HEURISTIC_NO_SPACE','STACK_HEIGHT']
    message: str

class PlannerPreview(BaseModel):
    algorithm: Literal['guillotine-single-layer-v1','columns-v1'] = 'guillotine-single-layer-v1'
    evaluation: Evaluation
    unplaced: list[UnplacedReason]

MESSAGES = {
    'EXCLUDED': 'Bó được loại trừ khỏi xếp thử.',
    'TOO_HIGH': 'Chiều cao bó vượt chiều cao hầm.',
    'FOOTPRINT_TOO_LARGE': 'Khối bao không vừa hầm theo cả hai hướng.',
    'MASS_LIMIT': 'Vượt giới hạn khối lượng còn lại của chuyến.',
    'HEURISTIC_NO_SPACE': 'Cách xếp thử chưa tìm được chỗ; có thể tồn tại cách xếp khác.',
    'STACK_HEIGHT': 'Các cột cùng kích thước đã đủ chiều cao hầm và không còn chỗ sàn cho cột mới.',
}

def grid_dims(unit):
    if unit.dimensions_um:
        return tuple((x+999)//1000 for x in unit.dimensions_um)
    return unit.length_mm,unit.width_mm,unit.height_mm

def exact_height_um(unit):
    return unit.dimensions_um[2] if unit.dimensions_um else unit.height_mm*1000

def _blocked(plan, unit, length, width, height, mass, available):
    if unit.requirement=='excluded': return 'EXCLUDED'
    if height>plan.hold.height_mm: return 'TOO_HIGH'
    if not ((length<=plan.hold.length_mm and width<=plan.hold.width_mm) or (width<=plan.hold.length_mm and length<=plan.hold.width_mm)): return 'FOOTPRINT_TOO_LARGE'
    if mass+unit.mass_g>available: return 'MASS_LIMIT'
    return None

def _floor_slot(rects, length, width):
    # Best area fit; then lowest y/x, yaw and free-rectangle index. Consumes the chosen free rectangle.
    options=[]
    for index,(x,y,rw,rh) in enumerate(rects):
        for yaw,w,h in ((0,length,width),(90,width,length)):
            if w<=rw and h<=rh: options.append((rw*rh-w*h,y,x,yaw,index,w,h))
    if not options: return None
    _,y,x,yaw,index,w,h=min(options)
    _,_,rw,rh=rects.pop(index)
    if rw>w: rects.append((x+w,y,rw-w,h))
    if rh>h: rects.append((x,y+h,rw,rh-h))
    rects.sort(key=lambda r:(r[1],r[0],r[2],r[3]))
    return x,y,yaw

def _candidate(plan, placed, stacking=None):
    payload=plan.model_dump(mode='json');payload['placements']=[p.model_dump(mode='json') for p in placed]
    if stacking: payload['stacking']=stacking
    return Plan.model_validate(payload)

def preview(plan: Plan, algorithm: str='guillotine-single-layer-v1') -> PlannerPreview:
    if algorithm=='columns-v1': return _preview_columns(plan)
    # Source extents are conservatively reserved on the mm grid; the existing
    # domain validator checks exact micrometre bounds after placement.
    rects=[(0,0,plan.hold.length_mm,plan.hold.width_mm)]
    placed=[]; unplaced=[]; mass=0
    eligible=sorted(plan.units,key=lambda u:(0 if u.requirement=='required' else 1 if u.requirement=='optional' else 2,-grid_dims(u)[0]*grid_dims(u)[1],u.id))
    available=plan.limits.voyage_cargo_limit_g-plan.limits.cargo_onboard_g
    for unit in eligible:
        length,width,height=grid_dims(unit)
        code=_blocked(plan,unit,length,width,height,mass,available)
        if not code:
            slot=_floor_slot(rects,length,width)
            if slot:
                x,y,yaw=slot
                placed.append(Placement(unit_id=unit.id,x_mm=x,y_mm=y,z_mm=0,layer=0,supported_by=[],yaw_deg=yaw))
                mass+=unit.mass_g
                continue
            code='HEURISTIC_NO_SPACE'
        unplaced.append(UnplacedReason(unit_id=unit.id,code=code,message=MESSAGES[code]))
    return PlannerPreview(evaluation=evaluate(_candidate(plan,placed)),unplaced=unplaced)

def _preview_columns(plan: Plan) -> PlannerPreview:
    """Vertical columns of same-grid-size units. One open column per grid-dims key; deterministic."""
    rects=[(0,0,plan.hold.length_mm,plan.hold.width_mm)]
    placed=[]; unplaced=[]; mass=0
    rank=lambda u:0 if u.requirement=='required' else 1 if u.requirement=='optional' else 2
    eligible=sorted(plan.units,key=lambda u:(rank(u),-grid_dims(u)[0]*grid_dims(u)[1],grid_dims(u),u.id))
    available=plan.limits.voyage_cargo_limit_g-plan.limits.cargo_onboard_g
    hold_um=plan.hold.height_mm*1000
    open_col={}      # dims -> (x, y, yaw, top Placement, grid height of the top unit)
    column_count={}  # dims -> columns opened so far
    for unit in eligible:
        dims=grid_dims(unit); length,width,height=dims
        code=_blocked(plan,unit,length,width,height,mass,available)
        if not code:
            col=open_col.get(dims)
            if col:
                x,y,yaw,below,h=col
                z=below.z_mm+h
                if z*1000+exact_height_um(unit)<=hold_um:
                    p=Placement(unit_id=unit.id,x_mm=x,y_mm=y,z_mm=z,layer=below.layer+1,supported_by=[below.unit_id],yaw_deg=yaw)
                    placed.append(p); open_col[dims]=(x,y,yaw,p,height); mass+=unit.mass_g
                    continue
            slot=_floor_slot(rects,length,width)
            if slot:
                x,y,yaw=slot
                p=Placement(unit_id=unit.id,x_mm=x,y_mm=y,z_mm=0,layer=0,supported_by=[],yaw_deg=yaw)
                placed.append(p); open_col[dims]=(x,y,yaw,p,height); column_count[dims]=column_count.get(dims,0)+1; mass+=unit.mass_g
                continue
            code='STACK_HEIGHT' if column_count.get(dims) else 'HEURISTIC_NO_SPACE'
        unplaced.append(UnplacedReason(unit_id=unit.id,code=code,message=MESSAGES[code]))
    return PlannerPreview(algorithm='columns-v1',evaluation=evaluate(_candidate(plan,placed,'COLUMNS_V1')),unplaced=unplaced)
