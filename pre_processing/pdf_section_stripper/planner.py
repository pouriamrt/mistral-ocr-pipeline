from typing import Dict, List, Optional
import fitz

from pdf_section_stripper.config import StripConfig
from pdf_section_stripper.models import SectionCuts, Plan, FoundHeading
from loguru import logger


def _merge_cuts(primary: SectionCuts, secondary: SectionCuts) -> SectionCuts:
    return SectionCuts(
        intro_start=primary.intro_start
        if primary.intro_start is not None
        else secondary.intro_start,
        methods_start=primary.methods_start
        if primary.methods_start is not None
        else secondary.methods_start,
        ack_start=primary.ack_start
        if primary.ack_start is not None
        else secondary.ack_start,
        refs_start=primary.refs_start
        if primary.refs_start is not None
        else secondary.refs_start,
        intro_heading=primary.intro_heading or secondary.intro_heading,
        ack_heading=primary.ack_heading or secondary.ack_heading,
        refs_heading=primary.refs_heading or secondary.refs_heading,
    )


def build_plan(
    doc: fitz.Document,
    outline_cuts: SectionCuts,
    layout_cuts: SectionCuts,
    cfg: StripConfig,
) -> Plan:
    cuts = _merge_cuts(outline_cuts, layout_cuts)

    n = doc.page_count
    keep_pages = set(range(n))
    redactions: Dict[int, List[fitz.Rect]] = {}

    protected_until = min(n, cfg.keep_first_n_pages_always + cfg.keep_abstract_pages)

    # 1) References: drop from refs start to end
    if cfg.remove_refs and cuts.refs_start is not None:
        for i in range(cuts.refs_start, n):
            keep_pages.discard(i)

    # 2) Acknowledgements: drop from ack start to refs start (or end)
    if cfg.remove_ack and cuts.ack_start is not None:
        end = cuts.refs_start if cuts.refs_start is not None else n
        for i in range(cuts.ack_start, end):
            keep_pages.discard(i)

    # 3) Intro/background: drop from intro start to methods start (only if methods is found and after intro)
    if (cfg.remove_intro or cfg.remove_background) and cuts.intro_start is not None:
        if cuts.methods_start is not None and cuts.methods_start > cuts.intro_start:
            for i in range(cuts.intro_start, cuts.methods_start):
                if i < protected_until:
                    continue
                keep_pages.discard(i)
        else:
            logger.debug(
                "Planner: Methods boundary not found or not after intro; skipping intro removal for safety."
            )

    # Always keep first N pages (safety)
    for i in range(min(cfg.keep_first_n_pages_always, n)):
        keep_pages.add(i)

    # Boundary redactions (if a section starts mid-page and that page is otherwise kept)
    def add_redaction(h: Optional[FoundHeading]):
        if not h:
            return
        if h.page not in keep_pages:
            return
        page = doc[h.page]
        pr = page.rect
        # redact everything below the heading line (small padding)
        r = fitz.Rect(pr.x0, h.y1 + 2, pr.x1, pr.y1)
        redactions.setdefault(h.page, []).append(r)

    if cfg.remove_refs:
        add_redaction(cuts.refs_heading)
    if cfg.remove_ack:
        add_redaction(cuts.ack_heading)
    if cfg.remove_intro or cfg.remove_background:
        add_redaction(cuts.intro_heading)

    return Plan(
        keep_pages=sorted(keep_pages),
        redactions=redactions,
        cuts=cuts,
    )
