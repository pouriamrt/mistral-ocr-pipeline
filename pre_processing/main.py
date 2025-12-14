from pathlib import Path
from loguru import logger
import sys
import os

from pdf_section_stripper.pipeline import PDFSectionStripper
from pdf_section_stripper.config import StripConfig
from rich.progress import track


def setup_logging():
    """Setup logging for the application."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
        level="INFO",
    )


def main():
    setup_logging()

    # ----------- configure your run here -----------
    INPUT_DIR = Path("papers/todo")
    OUTPUT_DIR = Path("papers/todo_stripped")

    cfg = StripConfig(
        remove_intro=True,
        remove_background=True,
        remove_ack=True,
        remove_refs=True,
        keep_first_n_pages_always=1,
        keep_abstract_pages=1,
        max_scan_pages_for_intro=12,
        min_heading_score=78,
        debug=True,
    )
    # ----------------------------------------------

    stripper = PDFSectionStripper(cfg)

    pdfs = sorted(INPUT_DIR.glob("*.pdf"))
    if not pdfs:
        logger.error(f"No PDFs found in {INPUT_DIR}")
        return

    for p in track(pdfs, description="Processing PDFs"):
        out = OUTPUT_DIR / p.name
        result = stripper.process_pdf(p, out)
        logger.debug(
            f"Processed {p.name} -> {out.name} with {result.kept_pages}/{result.total_pages} pages"
        )


if __name__ == "__main__":
    expected_cwd = Path(__file__).parent.parent.resolve()
    actual_cwd = Path.cwd().resolve()
    if actual_cwd != expected_cwd:
        os.chdir(expected_cwd)
        print(f"Changed working directory to: {expected_cwd}")

    main()
