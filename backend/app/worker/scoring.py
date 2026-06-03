from app.models.assessment import RAGStatus, Recommendation
from app.models.finding import Category

DEFAULT_WEIGHTS = {
    Category.VENDOR_TRUST: 1.0,
    Category.CVE: 2.0,
    Category.MAINTENANCE: 1.5,
    Category.DEPENDENCY: 1.5,
    Category.ENCRYPTION: 1.5,
    Category.LOGGING: 1.0,
    Category.DATA_EXFILTRATION: 1.5,
    Category.THIRD_PARTY: 1.0,
}

def score_to_rag(score: float) -> RAGStatus:
    if score >= 7.5:
        return RAGStatus.GREEN
    if score >= 5.0:
        return RAGStatus.AMBER
    return RAGStatus.RED

def derive_recommendation(rag: RAGStatus) -> Recommendation:
    return {
        RAGStatus.GREEN: Recommendation.APPROVE,
        RAGStatus.AMBER: Recommendation.CONDITIONAL,
        RAGStatus.RED: Recommendation.REJECT,
    }[rag]

def aggregate_scores(scores: dict[str, float], weights: dict[str, float]) -> float:
    total_weight = sum(weights[k] for k in scores if k in weights)
    if total_weight == 0:
        return 0.0
    weighted_sum = sum(scores[k] * weights.get(k, 1.0) for k in scores)
    return round(weighted_sum / total_weight, 2)
