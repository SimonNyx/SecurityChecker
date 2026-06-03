def test_score_to_rag_green():
    from app.worker.scoring import score_to_rag
    from app.models.assessment import RAGStatus
    assert score_to_rag(8.0) == RAGStatus.GREEN
    assert score_to_rag(7.5) == RAGStatus.GREEN
    assert score_to_rag(10.0) == RAGStatus.GREEN

def test_score_to_rag_amber():
    from app.worker.scoring import score_to_rag
    from app.models.assessment import RAGStatus
    assert score_to_rag(7.4) == RAGStatus.AMBER
    assert score_to_rag(5.0) == RAGStatus.AMBER

def test_score_to_rag_red():
    from app.worker.scoring import score_to_rag
    from app.models.assessment import RAGStatus
    assert score_to_rag(4.9) == RAGStatus.RED
    assert score_to_rag(0.0) == RAGStatus.RED

def test_derive_recommendation():
    from app.worker.scoring import derive_recommendation
    from app.models.assessment import RAGStatus, Recommendation
    assert derive_recommendation(RAGStatus.GREEN) == Recommendation.APPROVE
    assert derive_recommendation(RAGStatus.AMBER) == Recommendation.CONDITIONAL
    assert derive_recommendation(RAGStatus.RED) == Recommendation.REJECT

def test_aggregate_scores_equal_weights():
    from app.worker.scoring import aggregate_scores
    scores = {"vendor_trust": 8.0, "cve": 6.0, "maintenance": 7.0,
              "dependency": 5.0, "encryption": 9.0, "logging": 6.0,
              "data_exfiltration": 7.0, "third_party": 8.0}
    weights = {k: 1.0 for k in scores}
    result = aggregate_scores(scores, weights)
    assert abs(result - 7.0) < 0.01

def test_aggregate_scores_weighted():
    from app.worker.scoring import aggregate_scores
    scores = {"vendor_trust": 10.0, "cve": 0.0}
    weights = {"vendor_trust": 1.0, "cve": 3.0}
    result = aggregate_scores(scores, weights)
    assert abs(result - 2.5) < 0.01
