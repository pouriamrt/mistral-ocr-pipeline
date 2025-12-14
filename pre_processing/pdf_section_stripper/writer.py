import fitz
from pdf_section_stripper.models import Plan
from loguru import logger


def write_stripped_pdf(original: fitz.Document, plan: Plan, output_path: str) -> None:
    keep = plan.keep_pages
    if not keep:
        logger.error("No pages left after filtering.")
        return

    out = fitz.open()

    # Insert pages losslessly
    for i in keep:
        out.insert_pdf(original, from_page=i, to_page=i)

    # Map old page index -> new page index
    old_to_new = {old: new for new, old in enumerate(keep)}

    # Apply redactions in the new document coordinates
    for old_i, rects in plan.redactions.items():
        if old_i not in old_to_new:
            continue
        new_i = old_to_new[old_i]
        page = out[new_i]
        for r in rects:
            page.add_redact_annot(r, fill=(1, 1, 1))
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

    out.save(output_path, deflate=True, garbage=4)
    out.close()
