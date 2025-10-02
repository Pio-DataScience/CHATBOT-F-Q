# src/llm/prompts.py
def build_question_messages(heading: str, answer_html: str, qmin=3,
                            qmax=8, max_words=12):
    sys = (
        "You generate alternative FAQ question phrasings. "
        "Do NOT change the answer. Do NOT summarize or quote it. "
        "Return ONLY valid JSON: {\"alternatives\": [\"q1\", \"q2\", ...]} "
        f"Generate between {qmin} and {qmax} concise questions,\n"
        f"each ≤ {max_words} words."
    )
    user = (
        f"Heading (question base): \"{heading}\"\n\n"
        "Answer HTML (read-only context):\n"
        f"{answer_html}\n\n"
        "Constraints:\n"
        "- Keep intent identical to the heading/section.\n"
        "- No duplication; vary phrasing.\n"
        "- No punctuation except a trailing question mark if natural.\n"
        "- Match the language of the heading/content (Arabic, English, etc.).\n"
        "Output JSON only."
    )
    return [{"role": "system", "content": sys},
            {"role": "user", "content": user}]
