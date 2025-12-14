import re
from typing import List, Tuple, Optional, Dict

import fitz
from rapidfuzz import fuzz

from pdf_section_stripper.config import StripConfig
from pdf_section_stripper.models import FoundHeading


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
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _page_median_fontsize(page: fitz.Page) -> float:
    sizes = []
    d = page.get_text("dict")
    for b in d.get("blocks", []):
        for ln in b.get("lines", []):
            for sp in ln.get("spans", []):
                sz = sp.get("size")
                if isinstance(sz, (int, float)):
                    sizes.append(float(sz))
    if not sizes:
        return 0.0
    sizes.sort()
    return sizes[len(sizes) // 2]


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


def _is_heading_like(
    line_text: str, fontsize: float, median_font: float, cfg: StripConfig
) -> bool:
    t = line_text.strip()
    if not t:
        return False
    if len(t) > cfg.heading_max_chars:
        return False

    # If we have font info, enforce "heading larger than typical text"
    if median_font > 0 and fontsize > 0:
        if fontsize / median_font < cfg.heading_min_fontsize_ratio:
            return False

    # Avoid lines that look like full sentences
    if t.endswith(".") and len(t.split()) > 3:
        return False

    return True


def find_headings_in_page(
    page: fitz.Page, page_index: int, cfg: StripConfig
) -> List[FoundHeading]:
    d = page.get_text("dict")
    median_font = _page_median_fontsize(page)
    candidates: List[FoundHeading] = []

    for b in d.get("blocks", []):
        if b.get("type") != 0:
            continue
        lines = b.get("lines", [])
        if not lines:
            continue

        # Take first line of each text block as a heading candidate
        first_line = lines[0]
        line_text = "".join(
            sp.get("text", "") for sp in first_line.get("spans", [])
        ).strip()
        if not line_text:
            continue

        sizes = [
            float(sp.get("size", 0.0))
            for sp in first_line.get("spans", [])
            if sp.get("size")
        ]
        fontsize = max(sizes) if sizes else 0.0

        if not _is_heading_like(line_text, fontsize, median_font, cfg):
            continue

        rects = [
            fitz.Rect(sp["bbox"]) for sp in first_line.get("spans", []) if "bbox" in sp
        ]
        if not rects:
            continue
        r = rects[0]
        for rr in rects[1:]:
            r |= rr

        kind = None
        score = -1

        # classify by best match
        m, s = _best_title_match(line_text, METHODS_TITLES)
        if m and s > score:
            kind, score = "methods", s

        if cfg.remove_refs:
            m, s = _best_title_match(line_text, REF_TITLES)
            if m and s > score:
                kind, score = "refs", s

        if cfg.remove_ack:
            m, s = _best_title_match(line_text, ACK_TITLES)
            if m and s > score:
                kind, score = "ack", s

        if cfg.remove_intro or cfg.remove_background:
            m, s = _best_title_match(line_text, INTRO_TITLES)
            if m and s > score:
                kind, score = "intro", s

        if kind and score >= cfg.min_heading_score:
            candidates.append(
                FoundHeading(
                    page=page_index,
                    y0=r.y0,
                    y1=r.y1,
                    text=line_text,
                    kind=kind,
                    score=score,
                )
            )

    # keep best per kind per page
    best_by_kind: Dict[str, FoundHeading] = {}
    for h in candidates:
        prev = best_by_kind.get(h.kind)
        if prev is None or h.score > prev.score:
            best_by_kind[h.kind] = h

    return list(best_by_kind.values())
