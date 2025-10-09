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
    """Remove markdown code fence markers and extract JSON from response."""
    logger.debug("Stripping code fences from response")
    s = s.strip()
    
    s = re.sub(r"^\s*```(?:json)?\s*", "", s, flags=re.I | re.M)
    s = re.sub(r"```\s*$", "", s, flags=re.I | re.M)
    
    json_match = re.search(r'\{.*\}', s, re.DOTALL)
    if json_match:
        logger.debug("Found JSON object in response")
        result = json_match.group(0)
        
        # Fix common LLM JSON errors
        # 1. Remove duplicate closing braces (e.g., "} }")
        result = re.sub(r'\}\s*\}+\s*$', '}', result)
        
        # 2. Fix unterminated strings
        open_quotes = result.count('"') - result.count('\\"')
        if open_quotes % 2 != 0:
            logger.debug("Detected unterminated string, fixing")
            result = result.rstrip() + '"'
        
        # 3. Fix unclosed brackets/braces
        open_brackets = result.count('[')
        close_brackets = result.count(']')
        open_braces = result.count('{')
        close_braces = result.count('}')
        
        # Close arrays first (nested inside objects)
        if close_brackets < open_brackets:
            missing = open_brackets - close_brackets
            logger.debug("Adding %d missing ]", missing)
            # Insert ] before the last }
            last_brace_pos = result.rfind('}')
            if last_brace_pos != -1:
                result = result[:last_brace_pos] + ']' * missing + result[last_brace_pos:]
            else:
                result += ']' * missing
        
        # Close objects
        if close_braces < open_braces:
            missing = open_braces - close_braces
            logger.debug("Adding %d missing }", missing)
            result += '}' * missing
        
        return result
    
    logger.debug("No JSON object found, returning cleaned string")
    return s


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

        # Try multiple parsing strategies to handle LLM errors
        try:
            # First try: standard JSON parsing with strict=False
            data = json.loads(cleaned, strict=False)
            logger.debug("Successfully parsed JSON on first attempt")
        except json.JSONDecodeError as e1:
            logger.debug("First parse failed at pos %d: %s", e1.pos, str(e1))
            
            # The _strip_code_fences function already fixed most issues,
            # but let's try a few more strategies
            
            # Second try: UTF-8 encoding cleanup
            try:
                logger.debug("Trying UTF-8 encode/decode")
                cleaned_bytes = cleaned.encode('utf-8', errors='ignore').decode('utf-8')
                # Remove control characters except newlines
                cleaned_bytes = ''.join(char for char in cleaned_bytes if ord(char) >= 32 or char in '\n\r\t')
                data = json.loads(cleaned_bytes, strict=False)
                logger.debug("UTF-8 encoding fix successful")
            except json.JSONDecodeError as e2:
                logger.debug("Second parse failed at pos %d: %s", e2.pos, str(e2))
                
                # Third try: Remove special characters
                try:
                    logger.debug("Trying character replacement")
                    cleaned_fixed = cleaned.replace('®', '(R)').replace('™', '(TM)').replace('©', '(C)')
                    cleaned_fixed = ''.join(char for char in cleaned_fixed if ord(char) >= 32 or char in '\n\r\t')
                    data = json.loads(cleaned_fixed, strict=False)
                    logger.debug("Character replacement successful")
                except json.JSONDecodeError as e3:
                    logger.debug("Third parse failed at pos %d: %s", e3.pos, str(e3))
                    
                    # Fourth try: Fix trailing commas
                    try:
                        logger.debug("Trying to remove trailing commas")
                        cleaned_fixed = re.sub(r',(\s*[}\]])', r'\1', cleaned_fixed)
                        data = json.loads(cleaned_fixed, strict=False)
                        logger.debug("Trailing comma fix successful")
                    except json.JSONDecodeError:
                        # All parsing attempts failed, re-raise first error
                        logger.error("All parsing strategies failed, re-raising original error")
                        raise e1
        
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
        logger.error("Cleaned response was: %s", cleaned[:500])
        logger.error("Raw response was: %s", raw[:500])
        logger.error("Cleaned response length: %d chars", len(cleaned))
        logger.error("Raw response length: %d chars", len(raw))
        logger.error("Error position: line %d, column %d, char %d", 
                     e.lineno, e.colno, e.pos)
        if e.pos < len(cleaned):
            logger.error("Context around error (±20 chars): %s", 
                         repr(cleaned[max(0, e.pos-20):min(len(cleaned), e.pos+20)]))
        logger.error("Last 50 chars of cleaned: %s", repr(cleaned[-50:]))
        logger.error("First 50 chars of cleaned: %s", repr(cleaned[:50]))
        raise
    except Exception as e:
        logger.error("Failed to parse alternatives: %s", e)
        logger.debug("Full error details:", exc_info=True)
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
    """
    Generate alternative questions for FAQ items using LLM.
    
    This function is resilient to failures:
    - LLM client has built-in retry logic (3 attempts with exponential backoff)
    - If all retries fail for an item, it logs the error and continues
    - Returns results with empty alternatives for failed items
    - Tracks success/failure statistics
    
    Args:
        items: List of FAQ items to process
        lm_client: LLM client instance with retry capability
        qmin: Minimum number of questions per item
        qmax: Maximum number of questions per item
        max_words: Maximum words per question
        limit: Optional limit on number of items to process
        
    Returns:
        List of results with alternatives for each item
    """
    total_items = len(items[:limit] if limit else items)
    logger.info("=" * 80)
    logger.info("Starting resilient question generation for %d FAQ items", total_items)
    logger.info("Parameters: qmin=%d, qmax=%d, max_words=%d", qmin, qmax, max_words)
    logger.info("LLM client configured with automatic retry and validation")
    logger.info("=" * 80)

    results = []
    successful = 0
    failed = 0
    failed_items = []

    for i, item in enumerate(items[:limit] if limit else items):
        item_num = i + 1
        logger.info("")
        logger.info("=" * 80)
        logger.info("Processing item %d/%d: %s", item_num, total_items, item["slug"])
        logger.info("=" * 80)

        heading = item["heading"]
        logger.debug("Item heading: %s", heading)

        try:
            answer_html = extract_answer_html(item["fragment_html"])
            logger.debug("Extracted answer HTML: %d characters", len(answer_html))

            raw_answer_html = extract_answer_html(item["fragment_html"])
            compact = html_to_compact_text(raw_answer_html, max_chars=18000)
            logger.debug("Compacted text: %d characters", len(compact))
            
            messages = build_question_messages(
                heading, compact, qmin, qmax, max_words
            )
            logger.debug("Built %d messages for LLM", len(messages))

            logger.info("→ Requesting question generation from LLM (with auto-retry)")
            
            # LLM client will handle retries internally
            content = lm_client.chat(messages, max_tokens=256)

            logger.debug("→ Parsing LLM response for alternatives")
            alternatives = parse_alternatives(content, qmin, qmax, max_words)
            successful += 1

            logger.info("✓ Successfully generated %d alternatives for %s",
                        len(alternatives), item["slug"])
            logger.info("  Alternatives: %s", alternatives[:3])  # Show first 3

        except json.JSONDecodeError as e:
            logger.error("✗ JSON parsing failed for item %s: %s", item["slug"], e)
            logger.error("  This may indicate malformed LLM response")
            logger.debug("Full error details:", exc_info=True)
            alternatives = []
            failed += 1
            failed_items.append({
                "item": item["slug"],
                "error": f"JSON parsing error: {str(e)}"
            })

        except ValueError as e:
            logger.error("✗ Validation failed for item %s: %s", item["slug"], e)
            logger.error("  LLM response did not meet quality requirements")
            logger.debug("Full error details:", exc_info=True)
            alternatives = []
            failed += 1
            failed_items.append({
                "item": item["slug"],
                "error": f"Validation error: {str(e)}"
            })

        except Exception as e:
            logger.error("✗ Failed to generate questions for item %s: %s",
                         item["slug"], e)
            logger.error("  Error type: %s", type(e).__name__)
            logger.debug("Full error details:", exc_info=True)
            alternatives = []
            failed += 1
            failed_items.append({
                "item": item["slug"],
                "error": f"{type(e).__name__}: {str(e)}"
            })

        result = {
            "slug": item["slug"],
            "heading": heading,
            "level": item["level"],
            "alternatives": alternatives
        }
        results.append(result)

        # Progress summary
        logger.info("-" * 80)
        logger.info("Item %d/%d completed | Success: %d | Failed: %d | Rate: %.1f%%",
                    item_num, total_items, successful, failed,
                    (successful / item_num * 100))
        logger.info("-" * 80)

    # Final summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("QUESTION GENERATION COMPLETED")
    logger.info("=" * 80)
    logger.info("Total items processed: %d", total_items)
    logger.info("✓ Successful: %d (%.1f%%)", successful,
                (successful / total_items * 100) if total_items > 0 else 0)
    logger.info("✗ Failed: %d (%.1f%%)", failed,
                (failed / total_items * 100) if total_items > 0 else 0)
    
    if failed_items:
        logger.warning("")
        logger.warning("Failed items detail:")
        for fail in failed_items:
            logger.warning("  - %s: %s", fail["item"], fail["error"])
    
    logger.info("=" * 80)
    
    return results
