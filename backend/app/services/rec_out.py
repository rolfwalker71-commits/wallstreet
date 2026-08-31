from app.schemas.recommendation import RecommendationOut
from app.services.outcomes import outcome_to_dict


def recommendation_out(rec) -> RecommendationOut:
    data = RecommendationOut.model_validate(rec)
    return data.model_copy(update={"outcome": outcome_to_dict(getattr(rec, "outcome", None))})
