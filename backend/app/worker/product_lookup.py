import json
from app.worker.ai_client import AIClient

LOOKUP_SYSTEM = """You are a software product identification assistant.
Given a product name, identify the correct software product.
Respond with JSON only, no markdown, in this exact format:
{"name": "...", "vendor": "...", "url": "...", "confidence": "high|medium|low", "description": "..."}"""

async def resolve_product(product_name: str, ai_client: AIClient) -> dict:
    """Ask the AI to identify a product by name. Returns suggestion dict."""
    prompt = f"""Identify this software product: "{product_name}"

Return the official product name, the vendor/company that makes it,
the official website URL, your confidence level, and a one-sentence description.
If this is an open-source project, the vendor is the maintainer organisation.
Respond with JSON only."""

    response = await ai_client.complete(prompt, system=LOOKUP_SYSTEM)

    try:
        # Strip any accidental markdown fences
        clean = response.strip().strip("```json").strip("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return {
            "name": product_name,
            "vendor": "Unknown",
            "url": "",
            "confidence": "low",
            "description": response[:200],
        }
