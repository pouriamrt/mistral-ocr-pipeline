from typing import List, Tuple, Optional

import fitz
from rapidfuzz import fuzz

from pdf_section_stripper.config import StripConfig
from pdf_section_stripper.models import SectionCuts

INTRO_TITLES = ["introduction", "background"]
METHODS_TITLES = [
    "methods",
    "materials and methods",
    "patients and methods",
    "methodology",
    "experimental procedures",
]
ACK_TITLES = ["acknowledgements", "acknowledgments"]
REF_TITLES = ["references", "bibliography", "works cited"]


def _norm(s: str) -> str:
    return " ".join(s.strip().lower().split())


def _best_title_match(text: str, candidates: List[str]) -> Tuple[Optional[str], int]:
    nt = _norm(text)
    best = None
    best_score = -1
    for c in candidates:
        score = max(
            fuzz.partial_ratio(nt, c),
            fuzz.token_set_ratio(nt, c),
            fuzz.ratio(nt, c),
        )
        if score > best_score:
            best_score = score
            best = c
    return best, best_score


def _extract_outline_entries(doc: fitz.Document) -> List[Tuple[int, str]]:
    toc = doc.get_toc(simple=True)  # [ [level, title, page], ... ] page is 1-based
    out: List[Tuple[int, str]] = []
    for level, title, page1 in toc:
        if not title or not page1:
            continue
        out.append((page1 - 1, title))
    return out


def detect_cuts_from_outline(doc: fitz.Document, cfg: StripConfig) -> SectionCuts:
    cuts = SectionCuts()
    entries = _extract_outline_entries(doc)
    if not entries:
        return cuts

    for p, title in entries:
        t = _norm(title)

        if cuts.refs_start is None and cfg.remove_refs:
            m, s = _best_title_match(t, REF_TITLES)
            if m and s >= cfg.min_heading_score:
                cuts.refs_start = p

        if cuts.ack_start is None and cfg.remove_ack:
            m, s = _best_title_match(t, ACK_TITLES)
            if m and s >= cfg.min_heading_score:
                cuts.ack_start = p

        if cuts.intro_start is None and (cfg.remove_intro or cfg.remove_background):
            m, s = _best_title_match(t, INTRO_TITLES)
            if m and s >= cfg.min_heading_score:
                cuts.intro_start = p

        if cuts.methods_start is None:
            m, s = _best_title_match(t, METHODS_TITLES)
            if m and s >= cfg.min_heading_score:
                cuts.methods_start = p

    return cuts
