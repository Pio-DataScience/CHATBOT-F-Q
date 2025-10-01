from bs4 import BeautifulSoup
import logging
import re

logger = logging.getLogger(__name__)
HEADING_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6"]


def slugify_heading_text(text: str) -> str:
    """Convert heading text to a URL-friendly slug."""
    logger.debug("Slugifying heading text: '%s'", text)
    digits = re.findall(r"[\d]+(?:\.[\d]+)*", text)
    core = (
        digits[0].replace(".", "-")
        if digits
        else re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-")
    )
    slug = f"sec-{core.lower()}"
    logger.debug("Generated slug: '%s'", slug)
    return slug


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
        logger.debug("Heading %d: <%s> '%s'", i+1, h.name,
                     h.get_text(strip=True)[:50])

    items = []
    for i, h in enumerate(headings):
        logger.debug("Processing heading %d/%d", i+1, len(headings))
        next_heading = headings[i+1] if i+1 < len(headings) else None

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

        fragment_html = f"""
<section class="faq-item" data-level="{int(h.name[1])}" id="{slug}">
  <{h.name} class="faq-q">{heading_text}</{h.name}>
  <div class="faq-a">
    {''.join(parts)}
  </div>
</section>
""".strip()

        item = {
            "slug": slug,
            "level": int(h.name[1]),
            "heading": heading_text,
            "fragment_html": fragment_html
        }
        items.append(item)

        logger.debug("Created FAQ item: %s (level %d, %d chars)",
                     slug, item['level'], len(fragment_html))

    logger.info("Successfully created %d FAQ items", len(items))
    return items
