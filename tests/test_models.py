def test_all_models_importable():
    from app.models import (
        User, Role, Assessment, InputType, AssessmentStatus,
        RAGStatus, Recommendation, ReviewMode, AssessmentFinding,
        Category, ProductConfirmation, AIProviderConfig, AIProvider, AuditLog
    )
    assert Role.ADMIN == "admin"
    assert AssessmentStatus.PENDING == "pending"
    assert Category.VENDOR_TRUST == "vendor_trust"
    assert AIProvider.OPENWEBUI == "openwebui"
