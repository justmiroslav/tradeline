from dataclasses import asdict

from fastapi import APIRouter

from domain.plans import PLANS, max_history_months
from features.plans.schemas import PlanOut

router = APIRouter(prefix="/plans", tags=["plans"])

@router.get("/", response_model=list[PlanOut])
async def list_plans() -> list[PlanOut]:
    return [
        PlanOut(tier=tier, trade_history_months=max_history_months(tier), **asdict(plan))
        for tier, plan in PLANS.items()
    ]
