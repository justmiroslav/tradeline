from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from domain.config import get_config
from domain.models import User
from features.ai.schemas import AiFeedbackIn, AiInsightOut
from features.ai.service import AiService
from shared.deps import get_current_user, get_session

router = APIRouter(prefix="/ai", tags=["ai"])

def _service(request: Request, session: AsyncSession) -> AiService:
    return AiService(session, request.app.state.rest_http, request.app.state.analytics_cache, get_config())

@router.get("/insight", response_model=AiInsightOut)
async def get_insight(request: Request, user: User = Depends(get_current_user),
                      session: AsyncSession = Depends(get_session)) -> AiInsightOut:
    return _service(request, session).state(user)

@router.post("/insight", response_model=AiInsightOut)
async def generate_insight(request: Request, user: User = Depends(get_current_user),
                           session: AsyncSession = Depends(get_session)) -> AiInsightOut:
    return await _service(request, session).generate(user)

@router.post("/insight/feedback", response_model=AiInsightOut)
async def insight_feedback(body: AiFeedbackIn, request: Request, user: User = Depends(get_current_user),
                           session: AsyncSession = Depends(get_session)) -> AiInsightOut:
    return await _service(request, session).feedback(user, body.helpful)

@router.post("/insight/stream")
async def stream_insight(request: Request, user: User = Depends(get_current_user),
                         session: AsyncSession = Depends(get_session)) -> EventSourceResponse:
    service = _service(request, session)
    analytics = await service.prepare(user)

    async def events():
        async for kind, value in service.stream(user, analytics):
            yield {"event": kind, "data": value if kind == "token" else value.model_dump_json()}

    return EventSourceResponse(events())
