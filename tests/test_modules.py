from unittest.mock import AsyncMock

async def test_resolve_product_parses_json():
    from app.worker.product_lookup import resolve_product
    from app.worker.ai_client import AIClient

    mock_config = {"provider": "openwebui", "base_url": "http://x", "api_key": "", "model_name": "m"}
    client = AIClient(mock_config)
    client.complete = AsyncMock(return_value='{"name":"Slack","vendor":"Salesforce","url":"https://slack.com","confidence":"high","description":"Team messaging"}')

    result = await resolve_product("Slack", client)
    assert result["name"] == "Slack"
    assert result["vendor"] == "Salesforce"
    assert result["confidence"] == "high"

async def test_resolve_product_handles_bad_json():
    from app.worker.product_lookup import resolve_product
    from app.worker.ai_client import AIClient

    mock_config = {"provider": "openwebui", "base_url": "http://x", "api_key": "", "model_name": "m"}
    client = AIClient(mock_config)
    client.complete = AsyncMock(return_value="I cannot identify that product.")

    result = await resolve_product("??gibberish??", client)
    assert result["name"] == "??gibberish??"
    assert result["confidence"] == "low"

async def test_vendor_trust_module_returns_result():
    from app.worker.modules.vendor_trust import VendorTrustModule
    from app.worker.ai_client import AIClient
    from app.models.assessment import Assessment, InputType, ReviewMode, AssessmentStatus
    import uuid

    assessment = Assessment(
        product_name="Slack",
        product_url="https://slack.com",
        input_type=InputType.URL,
        review_mode=ReviewMode.STANDARD,
        status=AssessmentStatus.RUNNING,
        submitted_by=uuid.uuid4(),
    )
    config = {"provider": "openwebui", "base_url": "http://x", "api_key": "", "model_name": "m"}
    client = AIClient(config)
    client.complete = AsyncMock(return_value='{"score": 8.5, "summary": "Trusted vendor.", "findings": {"company": "Salesforce"}}')

    module = VendorTrustModule(assessment, client)
    result = await module.run()

    assert result.score == 8.5
    assert result.summary == "Trusted vendor."
    from app.models.assessment import RAGStatus
    assert result.rag == RAGStatus.GREEN

async def test_module_handles_invalid_ai_json():
    from app.worker.modules.vendor_trust import VendorTrustModule
    from app.worker.ai_client import AIClient
    from app.models.assessment import Assessment, InputType, ReviewMode, AssessmentStatus
    import uuid

    assessment = Assessment(
        product_name="Unknown",
        input_type=InputType.NAME,
        review_mode=ReviewMode.STANDARD,
        status=AssessmentStatus.RUNNING,
        submitted_by=uuid.uuid4(),
    )
    config = {"provider": "openwebui", "base_url": "http://x", "api_key": "", "model_name": "m"}
    client = AIClient(config)
    client.complete = AsyncMock(return_value="This is not JSON at all.")

    module = VendorTrustModule(assessment, client)
    result = await module.run()
    assert result.score == 5.0  # default fallback


async def test_council_produces_result():
    from app.worker.council import run_council
    from app.worker.modules.vendor_trust import VendorTrustModule
    from app.worker.ai_client import AIClient
    from app.models.assessment import Assessment, InputType, ReviewMode, AssessmentStatus
    import uuid

    assessment = Assessment(
        product_name="TestProduct",
        input_type=InputType.NAME,
        review_mode=ReviewMode.DEEP_REVIEW,
        status=AssessmentStatus.RUNNING,
        submitted_by=uuid.uuid4(),
    )
    config = {"provider": "openwebui", "base_url": "http://x", "api_key": "", "model_name": "m"}
    client = AIClient(config)

    call_count = 0

    async def mock_complete(prompt, system=""):
        nonlocal call_count
        call_count += 1
        # Advisor runs (5) return module JSON; peer reviews (5) and chairman (1) return council JSON
        if call_count <= 5:
            return '{"score": 7.0, "summary": "Advisor assessment.", "findings": {}}'
        elif call_count <= 10:
            return '{"strongest": "A", "strongest_reason": "Most detailed", "weakest": "B", "blind_spot": "Missed CVEs", "all_missed": "Nothing major"}'
        else:
            return '{"score": 7.5, "summary": "Council verdict.", "consensus": "Generally positive.", "disagreements": "None significant.", "blind_spots": "Regulatory gap.", "findings": {}}'

    client.complete = mock_complete

    module = VendorTrustModule(assessment, client)
    result = await run_council(module)

    assert result.score == 7.5
    assert result.summary == "Council verdict."
    assert result.detail["council_mode"] is True
    assert len(result.detail["advisor_results"]) == 5
    assert call_count == 11  # 5 advisors + 5 peer reviews + 1 chairman


async def test_council_falls_back_on_bad_chairman_json():
    from app.worker.council import run_council
    from app.worker.modules.vendor_trust import VendorTrustModule
    from app.worker.ai_client import AIClient
    from app.models.assessment import Assessment, InputType, ReviewMode, AssessmentStatus
    import uuid

    assessment = Assessment(
        product_name="BadProduct",
        input_type=InputType.NAME,
        review_mode=ReviewMode.DEEP_REVIEW,
        status=AssessmentStatus.RUNNING,
        submitted_by=uuid.uuid4(),
    )
    config = {"provider": "openwebui", "base_url": "http://x", "api_key": "", "model_name": "m"}
    client = AIClient(config)

    call_count = 0

    async def mock_complete(prompt, system=""):
        nonlocal call_count
        call_count += 1
        if call_count <= 5:
            return '{"score": 6.0, "summary": "Advisor.", "findings": {}}'
        elif call_count <= 10:
            return '{"strongest": "A", "strongest_reason": "ok", "weakest": "B", "blind_spot": "x", "all_missed": "y"}'
        else:
            return "This chairman response is not valid JSON at all."

    client.complete = mock_complete

    module = VendorTrustModule(assessment, client)
    result = await run_council(module)

    # Falls back to average of advisor scores
    assert result.score == 6.0
