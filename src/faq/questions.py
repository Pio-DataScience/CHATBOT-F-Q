# src/faq/questions.py
import json
import logging
import re
from bs4 import BeautifulSoup
# local import to avoid circulars
from src.llm.prompts import build_question_messages

AR_RE = re.compile(r'[\u0600-\u06FF]')
logger = logging.getLogger(__name__)


def _ensure_qmark(s: str) -> str:
    # Preserve if ends with either Western or Arabic question mark
    if s.endswith("?") or s.endswith("؟"):
        return s
    # Use Arabic question mark if any Arabic letters exist; else '?'
    return s + ("؟" if AR_RE.search(s) else "?")


def extract_answer_html(fragment_html: str) -> str:
    """Extract the answer content from FAQ fragment HTML."""
    logger.debug("Extracting answer HTML from fragment")
    soup = BeautifulSoup(fragment_html, "lxml")
    div = soup.select_one("div.faq-a")
    result = str(div) if div else ""
    logger.debug("Extracted answer HTML: %d characters", len(result))
    return result


def _strip_code_fences(s: str) -> str:
    """Remove markdown code fence markers from string."""
    logger.debug("Stripping code fences from response")
    return re.sub(
        r"^\s*```(?:json)?|```\s*$", "", s.strip(), flags=re.I | re.M
    )


def _normalize_list(xs):
    """Remove duplicates and normalize whitespace in list of strings."""
    logger.debug("Normalizing list of %d items", len(xs))
    seen, out = set(), []
    for x in xs:
        q = re.sub(r"\s+", " ", x.strip())
        if q and q.lower() not in seen:
            seen.add(q.lower())
            out.append(q)
    logger.debug("Normalized to %d unique items", len(out))
    return out


def parse_alternatives(raw: str, qmin=3, qmax=8, max_words=12):
    """Parse LLM response to extract alternative questions."""
    logger.debug("Parsing alternatives from LLM response (%d chars)", len(raw))

    try:
        cleaned = _strip_code_fences(raw)
        logger.debug(
            "Cleaned response: %s",
            cleaned[:100] + "..." if len(cleaned) > 100 else cleaned
        )

        data = json.loads(cleaned)
        alts = data.get("alternatives", [])
        logger.debug("Found %d raw alternatives", len(alts))

        # enforce limits
        alts = [_ensure_qmark(a) for a in alts]
        logger.debug("Added question marks where needed")

        alts = [a for a in alts if len(a.split()) <= max_words]
        logger.debug(
            "Filtered by max words (%d): %d alternatives remain", max_words,
            len(alts)
        )

        alts = _normalize_list(alts)[:qmax]
        logger.debug(
            "After normalization and limit: %d alternatives", len(alts)
        )

        if len(alts) < qmin:
            logger.warning(
                "Only %d alternatives found, need at least %d", len(alts), qmin
            )
            raise ValueError("Too few valid alternatives")

        logger.info("Successfully parsed %d alternatives", len(alts))
        return alts

    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON from LLM response: %s", e)
        logger.debug("Raw response: %s", raw)
        raise
    except Exception as e:
        logger.error("Failed to parse alternatives: %s", e)
        raise


def html_to_compact_text(answer_html: str, max_chars: int = 15000) -> str:
    soup = BeautifulSoup(answer_html, "lxml")

    # 1) Remove images/base64 & non-texty stuff
    for tag in soup.find_all(["img", "style", "script"]):
        tag.decompose()

    # 2) Keep tables but as readable text
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = ([
                c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])
            ])
            rows.append(" | ".join(cells))
        table.replace_with("\n".join(rows))

    text = soup.get_text("\n", strip=True)
    # Clean extra newlines/spaces
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text[:max_chars]


def generate_questions_for_items(
    items, lm_client, qmin=3, qmax=8, max_words=12, limit=None
):
    """Generate alternative questions for FAQ items using LLM."""
    total_items = len(items[:limit] if limit else items)
    logger.info("Starting question generation for %d FAQ items", total_items)
    logger.info(
        "Parameters: qmin=%d, qmax=%d, max_words=%d", qmin, qmax, max_words
    )

    results = []
    successful = 0
    failed = 0

    for i, item in enumerate(items[:limit] if limit else items):
        logger.info(
            "Processing item %d/%d: %s", i + 1, total_items, item["slug"]
        )

        heading = item["heading"]
        logger.debug("Item heading: %s", heading)

        try:
            answer_html = extract_answer_html(item["fragment_html"])
            logger.debug(
                "Extracted answer HTML: %d characters", len(answer_html)
            )

            raw_answer_html = extract_answer_html(item["fragment_html"])
            compact = html_to_compact_text(raw_answer_html, max_chars=18000)
            messages = build_question_messages(
                heading, compact, qmin, qmax, max_words
            )

            logger.debug("Built %d messages for LLM", len(messages))

            logger.info(
                "Sending request to LLM for item %d/%d", i + 1, total_items
            )
            content = lm_client.chat(messages, max_tokens=256)

            logger.debug("Parsing LLM response for alternatives")
            alternatives = parse_alternatives(content, qmin, qmax, max_words)
            successful += 1

            logger.info(
                "Successfully generated %d alternatives for %s",
                len(alternatives), item["slug"]
            )

        except Exception as e:
            logger.error(
                "Failed to generate questions for item %s: %s", item["slug"], e
            )
            logger.debug("Full error details:", exc_info=True)
            alternatives = []
            failed += 1

        result = {
            "slug": item["slug"],
            "heading": heading,
            "level": item["level"],
            "alternatives": alternatives
        }
        results.append(result)

        logger.debug(
            "Item %d completed. Success: %d, Failed: %d", i + 1, successful,
            failed
        )

    logger.info(
        "Question generation completed. Successful: %d, Failed: %d",
        successful, failed
    )
    return results
