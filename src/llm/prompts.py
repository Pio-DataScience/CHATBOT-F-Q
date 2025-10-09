# src/llm/prompts.py
def build_question_messages(heading: str, answer_html: str, qmin=3,
                            qmax=8, max_words=12):
    """
    Build messages for LLM to generate alternative FAQ questions.
    
    Optimized for non-reasoning models like Qwen3-14B that output JSON directly.
    """
    sys = (
        "You are a precise JSON generator. "
        f"Output ONLY valid JSON: {{\"alternatives\": [\"q1\", \"q2\", ...]}} with {qmin}-{qmax} questions. "
        f"Each question ≤ {max_words} words. "
        "NO thinking, NO markdown, NO text before/after JSON. "
        "ALWAYS close arrays ] and objects } properly."
    )
    user = (
        f"Base question: \"{heading}\"\n\n"
        f"Context:\n{answer_html[:500]}...\n\n"
        "Create alternative phrasings of the base question. "
        f"Rules: same meaning, different wording, ≤{max_words} words, "
        "add ? if needed, match language.\n\n"
        "Output ONLY JSON now:"
    )
    return [{"role": "system", "content": sys},
            {"role": "user", "content": user}]
