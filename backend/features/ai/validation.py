import re

from features.ai.schemas import AiInsightBody
from features.analytics.schemas import AnalyticsOut

_SYMBOL_RE = re.compile(r"\b([A-Z0-9]{2,12}(?:USDT|USDC|BUSD|FDUSD|USD))\b")

def _to_float(value: str | None) -> float:
    try:
        return float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0

def _expected_verdict(net: float) -> str:
    if net > 0:
        return "profitable"
    if net < 0:
        return "unprofitable"
    return "breakeven"

def validate_insight(body: AiInsightBody, analytics: AnalyticsOut) -> dict:
    """Objective grounding of an AI insight against the trader's own realized data.

    verdict_match : did the model's verdict follow the real net P&L sign (the rule it was given)?
    grounding     : of the symbols it cited, how many the trader actually traded (hallucination guard).
    """
    net = _to_float(analytics.kpis.net_pnl)
    verdict_match = body.verdict == _expected_verdict(net)

    real = {(b.key or "").upper() for b in analytics.by_symbol if b.key}
    text = " ".join([body.headline, *body.edge, *body.leaks, *body.actions]).upper()
    cited = set(_SYMBOL_RE.findall(text))
    hallucinated = sorted(c for c in cited if c not in real)
    grounding = 1.0 if not cited else round((len(cited) - len(hallucinated)) / len(cited), 3)

    return {
        "verdict_match": verdict_match,
        "grounding_score": grounding,
        "hallucinated": hallucinated,
        "verified": verdict_match and not hallucinated
    }
