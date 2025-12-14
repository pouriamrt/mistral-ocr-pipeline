from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import fitz
from loguru import logger

from pdf_section_stripper.config import StripConfig
from pdf_section_stripper.models import SectionCuts
from pdf_section_stripper.outline_detector import detect_cuts_from_outline
from pdf_section_stripper.heading_detector import find_headings_in_page
from pdf_section_stripper.planner import build_plan
from pdf_section_stripper.writer import write_stripped_pdf


def detect_cuts_from_layout(doc: fitz.Document, cfg: StripConfig) -> SectionCuts:
    cuts = SectionCuts()
    n = doc.page_count

    # early pages: intro + methods
    scan_n = min(n, max(cfg.max_scan_pages_for_intro, 1))
    for i in range(scan_n):
        hs = find_headings_in_page(doc[i], i, cfg)
        for h in hs:
            if h.kind == "intro" and cuts.intro_start is None:
                cuts.intro_start = i
                cuts.intro_heading = h
            elif h.kind == "methods" and cuts.methods_start is None:
                cuts.methods_start = i

    # all pages: ack + refs (usually end)
    for i in range(n):
        hs = find_headings_in_page(doc[i], i, cfg)
        for h in hs:
            if h.kind == "ack" and cuts.ack_start is None:
                cuts.ack_start = i
                cuts.ack_heading = h
            elif h.kind == "refs" and cuts.refs_start is None:
                cuts.refs_start = i
                cuts.refs_heading = h

    return cuts


@dataclass
class StripResult:
    output_path: Path
    kept_pages: int
    total_pages: int
    cuts: SectionCuts


class PDFSectionStripper:
    def __init__(self, cfg: Optional[StripConfig] = None):
        self.cfg = cfg or StripConfig()

    def process_pdf(
        self, input_path: str | Path, output_path: str | Path
    ) -> StripResult:
        input_path = Path(input_path)
        output_path = Path(output_path)

        doc = fitz.open(str(input_path))
        try:
            outline_cuts = detect_cuts_from_outline(doc, self.cfg)
            layout_cuts = detect_cuts_from_layout(doc, self.cfg)

            plan = build_plan(doc, outline_cuts, layout_cuts, self.cfg)

            if self.cfg.debug:
                logger.debug(f"Cuts: {plan.cuts}")
                logger.debug(f"Keep pages: {len(plan.keep_pages)} / {doc.page_count}")

            output_path.parent.mkdir(parents=True, exist_ok=True)
            write_stripped_pdf(doc, plan, str(output_path))

            return StripResult(
                output_path=output_path,
                kept_pages=len(plan.keep_pages),
                total_pages=doc.page_count,
                cuts=plan.cuts,
            )
        finally:
            doc.close()
