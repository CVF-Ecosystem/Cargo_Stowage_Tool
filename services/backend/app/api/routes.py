from fastapi import APIRouter

from ..demo import demo_plan
from ..domain.model import Evaluation, Plan
from ..domain.rules import evaluate

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0", "mode": "synthetic-demo", "ai": "off"}


@router.get("/demo", response_model=Evaluation)
def demo() -> Evaluation:
    return evaluate(demo_plan())


@router.post("/validate", response_model=Evaluation)
def validate(plan: Plan) -> Evaluation:
    return evaluate(plan)
