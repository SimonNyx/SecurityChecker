import json
from app.worker.modules.base import BaseModule, ModuleResult
from app.worker.scoring import score_to_rag

ADVISORS = [
    {
        "name": "Threat Modeler",
        "prefix": (
            "You are a Threat Modeler specialising in STRIDE methodology, attack trees, and adversarial thinking. "
            "Approach this analysis by identifying realistic attack vectors, threat actors, and exploit scenarios. "
            "Consider supply-chain attacks, insider threats, and nation-state adversaries where relevant. "
            "Score conservatively — if a credible attack path exists, it should lower the score."
        ),
    },
    {
        "name": "Compliance Officer",
        "prefix": (
            "You are a Compliance Officer specialising in UK Defence cyber standards: Cyber Essentials, "
            "Cyber Essentials Plus, NCSC Cyber Assessment Framework (CAF), JSP 440, JSP 604, and MOD security "
            "policies. Also consider ISO 27001, SOC 2 Type II, and UK GDPR. Assess whether this product meets "
            "the baseline required for use in UK public sector and defence environments. "
            "Flag any compliance gaps that would block approval under these frameworks."
        ),
    },
    {
        "name": "Risk Analyst",
        "prefix": (
            "You are a Risk Analyst who uses quantitative and qualitative risk assessment. "
            "Consider impact (confidentiality, integrity, availability), likelihood, and residual risk after controls. "
            "Map findings to a risk register perspective: what is the inherent risk, what mitigations exist, "
            "and what residual risk remains? Score based on the overall risk posture, not just presence of features."
        ),
    },
    {
        "name": "Devil's Advocate",
        "prefix": (
            "You are a Devil's Advocate. Your job is to challenge every positive claim, find the weakest points, "
            "and argue the worst-case scenario. Assume the vendor's documentation is marketing, not ground truth. "
            "Look for what is NOT said, what claims are unverified, and what could go catastrophically wrong. "
            "If the evidence looks solid, dig deeper for hidden problems. Score pessimistically — "
            "overconfidence in security is itself a risk."
        ),
    },
    {
        "name": "Pragmatist",
        "prefix": (
            "You are a Pragmatist security advisor. You focus on what is operationally realistic, "
            "cost-effective, and proportionate for a mid-sized UK organisation. "
            "Balance security idealism against real-world usability and deployment constraints. "
            "Consider: is this product good enough for its risk tier? Are the gaps theoretical or exploitable in practice? "
            "Score based on whether this product is fit for purpose, not whether it achieves perfection."
        ),
    },
]

PEER_REVIEW_SYSTEM = (
    "You are reviewing security assessment outputs. Be direct and specific. "
    "Respond with JSON only. Schema: "
    '{\"strongest\": \"<letter>\", \"strongest_reason\": \"<why>\", '
    '\"weakest\": \"<letter>\", \"blind_spot\": \"<what it missed>\", '
    '\"all_missed\": \"<what ALL responses overlooked>\"}'
)

CHAIRMAN_SYSTEM = (
    "You are the Chairman synthesising a security council's findings into a final assessment. "
    "You have received 5 independent advisor assessments and 5 peer reviews. "
    "Produce a balanced final verdict. Respond with JSON only. "
    "Schema: {\"score\": <float 0-10>, \"summary\": \"<2-3 sentences>\", "
    "\"consensus\": \"<what advisors agreed on>\", \"disagreements\": \"<genuine conflicts>\", "
    "\"blind_spots\": \"<what peer review surfaced>\", \"findings\": {}}"
)


def _anonymise(advisor_results: list[dict]) -> dict[str, dict]:
    letters = list("ABCDE")
    return {
        letters[i]: {
            "score": advisor_results[i]["score"],
            "summary": advisor_results[i]["summary"],
        }
        for i in range(len(advisor_results))
    }


async def run_council(module: BaseModule) -> ModuleResult:
    """Run module through 5-advisor council with peer review and chairman synthesis."""

    # Step 1: 5 advisor runs
    advisor_results = []
    for advisor in ADVISORS:
        module._advisor_prefix = advisor["prefix"]
        result = await module.run()
        advisor_results.append({
            "advisor": advisor["name"],
            "score": result.score,
            "summary": result.summary,
            "detail": result.detail,
        })
    module._advisor_prefix = ""

    # Step 2: Peer reviews (anonymised)
    anon = _anonymise(advisor_results)
    letters = list("ABCDE")
    anon_text = "\n\n".join(
        f"Response {l}:\nScore: {anon[l]['score']}/10\nSummary: {anon[l]['summary']}"
        for l in letters
    )

    peer_reviews = []
    for advisor in ADVISORS:
        review_prompt = (
            f"Five security advisors independently assessed the same product module. "
            f"Review their outputs and answer the three questions.\n\n{anon_text}\n\n"
            "1. Which response is strongest and why?\n"
            "2. Which response has the biggest blind spot?\n"
            "3. What did ALL responses miss?\nReturn JSON only."
        )
        review = await module.ai.complete(review_prompt, PEER_REVIEW_SYSTEM)
        peer_reviews.append(review)

    # Step 3: Chairman synthesis
    advisor_block = "\n\n".join(
        f"{r['advisor']} (score {r['score']}/10): {r['summary']}"
        for r in advisor_results
    )
    reviews_block = "\n\n".join(f"Review {i+1}: {r}" for i, r in enumerate(peer_reviews))

    synthesis_prompt = (
        f"You have received 5 independent security advisor assessments and 5 peer reviews "
        f"for the same analysis module on: {module.assessment.product_name}\n\n"
        f"ADVISOR ASSESSMENTS:\n{advisor_block}\n\n"
        f"PEER REVIEWS:\n{reviews_block}\n\n"
        "Synthesise into a final council verdict. Return JSON only."
    )

    chairman_response = await module.ai.complete(synthesis_prompt, CHAIRMAN_SYSTEM)

    try:
        clean = chairman_response.strip().strip("```json").strip("```").strip()
        data = json.loads(clean)
    except json.JSONDecodeError:
        avg_score = sum(r["score"] for r in advisor_results) / len(advisor_results)
        data = {"score": avg_score, "summary": chairman_response[:300], "findings": {}}

    score = float(data.get("score", 5.0))
    return ModuleResult(
        score=score,
        rag=score_to_rag(score),
        summary=data.get("summary", ""),
        detail={
            "council_mode": True,
            "advisor_results": advisor_results,
            "consensus": data.get("consensus", ""),
            "disagreements": data.get("disagreements", ""),
            "blind_spots": data.get("blind_spots", ""),
            "findings": data.get("findings", {}),
        },
    )
