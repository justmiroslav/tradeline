from pydantic import BaseModel

class MarketTickerOut(BaseModel):
    symbol: str
    price: float
    change_pct: float
