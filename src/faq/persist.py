# src/faq/persist.py
import json
from bs4 import BeautifulSoup


def load_fragments_map(path_html: str):
    """ returns slug -> (heading_text, answer_html) """
    html = open(path_html, "r", encoding="utf-8").read()
    soup = BeautifulSoup(html, "lxml")
    out = {}
    for sec in soup.select("section.faq-item"):
        slug = sec.get("id")
        h = sec.select_one(".faq-q")
        a = sec.select_one(".faq-a")
        out[slug] = (h.get_text(strip=True) if h else "", str(a) if a else "")
    return out


def load_questions_jsonl(path_jsonl: str):
    rows = []
    with open(path_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows
