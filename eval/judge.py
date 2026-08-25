from typing import Any, cast

from agent.graph import MODEL
from agent.llm_client import get_groq_client

JUDGE_SYSTEM_PROMPT = (
    "You are a strict grader. You will receive a question, a reference answer, "
    "and a candidate answer. Reply with exactly one word: YES if the candidate "
    "answer is factually consistent with the reference answer, NO otherwise."
)


def judge_answer(question: str, reference: str, candidate: str) -> bool:
    client = get_groq_client()
    user_content = (
        f"Question: {question}\nReference answer: {reference}\nCandidate answer: {candidate}"
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=cast(
            Any,
            [
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        ),
    )
    verdict = (response.choices[0].message.content or "").strip().upper()
    return verdict.startswith("YES")
