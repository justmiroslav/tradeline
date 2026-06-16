from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from domain.filters import AnalyticsFilters
from domain.models import User
from features.analytics.deps import filters_query
from features.analytics.schemas import AnalyticsOut
from features.analytics.service import AnalyticsService
from shared.deps import get_current_user, get_session

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/overview", response_model=AnalyticsOut)
async def overview(request: Request, filters: AnalyticsFilters = Depends(filters_query),
                   user: User = Depends(get_current_user),
                   session: AsyncSession = Depends(get_session)) -> AnalyticsOut:
    return await AnalyticsService(session, request.app.state.analytics_cache).get_overview(user.id, filters)
