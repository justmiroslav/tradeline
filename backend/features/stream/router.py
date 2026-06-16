import json

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse

from domain.models import User
from shared.deps import get_current_user

router = APIRouter(tags=["stream"])

@router.get("/stream")
async def stream(request: Request, user: User = Depends(get_current_user)):
    bus = request.app.state.event_bus

    async def gen():
        async with bus.subscribe(user.id) as queue:
            while True:
                envelope = await queue.get()
                yield {"event": envelope["type"], "data": json.dumps(envelope["data"], default=str)}

    return EventSourceResponse(gen(), ping=15)
