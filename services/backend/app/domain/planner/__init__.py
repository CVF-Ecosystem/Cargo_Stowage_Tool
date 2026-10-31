"""Deterministic, conservative single-layer guillotine suggestion; not an optimizer."""
from typing import Literal
from pydantic import BaseModel
from ..model import Evaluation, Placement, Plan
from ..rules import evaluate

class UnplacedReason(BaseModel):
    unit_id: str
    code: Literal['EXCLUDED','TOO_HIGH','FOOTPRINT_TOO_LARGE','MASS_LIMIT','HEURISTIC_NO_SPACE']
    message: str

class PlannerPreview(BaseModel):
    algorithm: Literal['guillotine-single-layer-v1'] = 'guillotine-single-layer-v1'
    evaluation: Evaluation
    unplaced: list[UnplacedReason]

MESSAGES = {
    'EXCLUDED': 'Bó được loại trừ khỏi xếp thử.',
    'TOO_HIGH': 'Chiều cao bó vượt chiều cao hầm.',
    'FOOTPRINT_TOO_LARGE': 'Khối bao không vừa hầm theo cả hai hướng.',
    'MASS_LIMIT': 'Vượt giới hạn khối lượng còn lại của chuyến.',
    'HEURISTIC_NO_SPACE': 'Cách xếp thử chưa tìm được chỗ; có thể tồn tại cách xếp khác.',
}

def grid_dims(unit):
    if unit.dimensions_um:
        return tuple((x+999)//1000 for x in unit.dimensions_um)
    return unit.length_mm,unit.width_mm,unit.height_mm

def preview(plan: Plan) -> PlannerPreview:
    # Source extents are conservatively reserved on the mm grid; the existing
    # domain validator checks exact micrometre bounds after placement.
    rects=[(0,0,plan.hold.length_mm,plan.hold.width_mm)]
    placed=[]; unplaced=[]; mass=0
    eligible=sorted(plan.units,key=lambda u:(0 if u.requirement=='required' else 1 if u.requirement=='optional' else 2,-grid_dims(u)[0]*grid_dims(u)[1],u.id))
    available=plan.limits.voyage_cargo_limit_g-plan.limits.cargo_onboard_g
    for unit in eligible:
        length,width,height=grid_dims(unit)
        if unit.requirement=='excluded': code='EXCLUDED'
        elif height>plan.hold.height_mm: code='TOO_HIGH'
        elif not ((length<=plan.hold.length_mm and width<=plan.hold.width_mm) or (width<=plan.hold.length_mm and length<=plan.hold.width_mm)): code='FOOTPRINT_TOO_LARGE'
        elif mass+unit.mass_g>available: code='MASS_LIMIT'
        else:
            # Best area fit; then lowest y/x, yaw and free-rectangle index.
            options=[]
            for index,(x,y,rw,rh) in enumerate(rects):
                for yaw,w,h in ((0,length,width),(90,width,length)):
                    if w<=rw and h<=rh: options.append((rw*rh-w*h,y,x,yaw,index,w,h))
            if not options: code='HEURISTIC_NO_SPACE'
            else:
                _,y,x,yaw,index,w,h=min(options)
                _,_,rw,rh=rects.pop(index)
                if rw>w: rects.append((x+w,y,rw-w,h))
                if rh>h: rects.append((x,y+h,rw,rh-h))
                rects.sort(key=lambda r:(r[1],r[0],r[2],r[3]))
                placed.append(Placement(unit_id=unit.id,x_mm=x,y_mm=y,z_mm=0,layer=0,supported_by=[],yaw_deg=yaw))
                mass+=unit.mass_g
                continue
        unplaced.append(UnplacedReason(unit_id=unit.id,code=code,message=MESSAGES[code]))
    payload=plan.model_dump(mode='json');payload['placements']=[p.model_dump(mode='json') for p in placed]
    candidate=Plan.model_validate(payload)
    return PlannerPreview(evaluation=evaluate(candidate),unplaced=unplaced)
