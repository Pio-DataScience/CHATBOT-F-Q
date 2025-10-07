from bs4 import BeautifulSoup
import logging
import re
import hashlib

AR_RE = re.compile(r"[\u0600-\u06FF]")
logger = logging.getLogger(__name__)
HEADING_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6"]


def slugify_heading_text(text: str) -> str:
    """
    Arabic-safe slugification:
    - Convert Arabic-Indic digits to Latin for numeric outlines (e.g., '٣.٢' -> '3.2')
    - If a numeric outline exists, prefer it (e.g., '3.1' -> 'sec-3-1')
    - Otherwise, keep Unicode word chars (Arabic included), replace non-word with '-'
    - If still empty, fall back to an 8-char SHA1 hash of the original text
    """
    arabic_indic_map = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    normalized_text = text.translate(arabic_indic_map)

    # Prefer numeric outline if present (e.g., 3.1.2 → sec-3-1-2)
    digits = re.findall(r"[\d]+(?:\.[\d]+)*", normalized_text)
    if digits:
        core = digits[0].replace(".", "-")
    else:
        # Keep Unicode letters/digits/underscore; collapse others to hyphens
        core = re.sub(r"[^\w]+", "-", normalized_text, flags=re.UNICODE).strip("-")
        if not core:
            core = hashlib.sha1(normalized_text.encode("utf-8")).hexdigest()[:8]

    return f"sec-{core.lower()}"


def split_into_faq_items(html: str):
    """Split HTML content into individual FAQ items based on headings."""
    logger.info("Starting to split HTML into FAQ items")
    logger.debug("HTML content length: %d characters", len(html))

    try:
        soup = BeautifulSoup(html, "lxml")
        logger.debug("Successfully parsed HTML with BeautifulSoup")
    except Exception as e:
        logger.error("Failed to parse HTML with BeautifulSoup: %s", e)
        raise

    headings = list(soup.find_all(HEADING_TAGS))
    logger.info("Found %d headings in HTML", len(headings))

    for i, h in enumerate(headings):
        logger.debug(
            "Heading %d: <%s> '%s'", i + 1, h.name, h.get_text(strip=True)[:50]
        )

    items = []
    for i, h in enumerate(headings):
        logger.debug("Processing heading %d/%d", i + 1, len(headings))
        next_heading = headings[i + 1] if i + 1 < len(headings) else None

        parts = []
        node = h.next_sibling
        content_nodes = 0

        while node and node is not next_heading:
            if getattr(node, "name", None) in HEADING_TAGS:
                logger.debug("Stopped at nested heading: <%s>", node.name)
                break  # stop at ANY heading (1.1, 1.1.1, etc.)
            if str(node).strip():
                parts.append(str(node))
                content_nodes += 1
            node = node.next_sibling

        logger.debug("Found %d content nodes for this section", content_nodes)

        heading_text = h.get_text(strip=True)
        slug = slugify_heading_text(heading_text)

        # Detect Arabic content for RTL direction
        is_arabic_content = is_arabic(heading_text) or any(
            is_arabic(str(part)) for part in parts
        )
        dir_attr = ' dir="rtl"' if is_arabic_content else ' dir="auto"'

        fragment_html = f"""
<section class="faq-item" data-level="{int(h.name[1])}" id="{slug}">
  <{h.name} class="faq-q"{dir_attr} style="font-size: 1.2em; margin-bottom: 0.5em;">{heading_text}</{h.name}>
  <div class="faq-a"{dir_attr}>
    {"".join(parts)}
  </div>
</section>
""".strip()

        item = {
            "slug": slug,
            "level": int(h.name[1]),
            "heading": heading_text,
            "fragment_html": fragment_html,
        }
        items.append(item)

        logger.debug(
            "Created FAQ item: %s (level %d, %d chars)",
            slug,
            item["level"],
            len(fragment_html),
        )

    logger.info("Successfully created %d FAQ items", len(items))
    return items


def is_arabic(s: str) -> bool:
    return bool(AR_RE.search(s or ""))
