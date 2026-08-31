from sqlalchemy import inspect as sa_inspect

from app.schemas.recommendation import RecommendationOut
from app.services.outcomes import outcome_to_dict


def _rel_if_loaded(obj, name, default=None):
    try:
        insp = sa_inspect(obj)
    except Exception:
        return getattr(obj, name, default)
    if name in insp.unloaded:
        return default
    try:
        return getattr(obj, name)
    except Exception:
        return default


def recommendation_out(rec) -> RecommendationOut:
    """Kein Lazy-Load: outcome/agent_logs nur wenn schon geladen (sonst MissingGreenlet)."""
    payload = {
        "id": rec.id,
        "run_id": rec.run_id,
        "action": rec.action,
        "confidence": rec.confidence,
        "risk_reward_ratio": rec.risk_reward_ratio,
        "rationale": rec.rationale,
        "news_summary": rec.news_summary,
        "news_sources": rec.news_sources,
        "technicals": rec.technicals,
        "proposed_qty": rec.proposed_qty,
        "proposed_price": rec.proposed_price,
        "status": rec.status,
        "glossary_terms": rec.glossary_terms,
        "suggested_symbols": getattr(rec, "suggested_symbols", None),
        "created_at": rec.created_at,
        "asset": rec.asset,
        "agent_logs": _rel_if_loaded(rec, "agent_logs", []) or [],
        "outcome": outcome_to_dict(_rel_if_loaded(rec, "outcome")),
    }
    return RecommendationOut.model_validate(payload)
