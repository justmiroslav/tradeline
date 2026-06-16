from fastapi import APIRouter, Request

from features.market.schemas import MarketTickerOut

router = APIRouter(prefix="/market", tags=["market"])

@router.get("/tickers", response_model=list[MarketTickerOut])
async def tickers(request: Request) -> list:
    return request.app.state.market_ticker_worker.tickers
