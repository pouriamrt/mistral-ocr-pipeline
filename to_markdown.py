from mistralai.models import OCRResponse
from utils import encode_pdf
from pathlib import Path
from mistralai import Mistral


def replace_images_in_markdown_annotated(markdown_str: str, images_dict: dict) -> str:
    """
    Replace image placeholders in markdown with base64-encoded images and their annotation.

    Args:
        markdown_str: Markdown text containing image placeholders
        images_dict: Dictionary mapping image IDs to base64 strings

    Returns:
        Markdown text with images replaced by base64 data and their annotation
    """
    for img_name, data in images_dict.items():
        markdown_str = markdown_str.replace(
            f"![{img_name}]({img_name})", f"![{img_name}]({data['image']})\n\n**{data['annotation']}**"
        )
    return markdown_str

def get_combined_markdown_annotated(ocr_response: OCRResponse) -> str:
    """
    Combine OCR text, annotation and images into a single markdown document.

    Args:
        ocr_response: Response from OCR processing containing text and images

    Returns:
        Combined markdown string with embedded images and their annotation
    """
    markdowns: list[str] = ["**" + ocr_response.document_annotation + "**"]
    # Extract images from page
    for page in ocr_response.pages:
        image_data = {}
        for img in page.images:
            image_data[img.id] = {"image":img.image_base64, "annotation": img.image_annotation}
        # Replace image placeholders with actual images
        markdowns.append(replace_images_in_markdown_annotated(page.markdown, image_data))

    return "\n\n".join(markdowns)


def convert_to_markdown(annotations_response: OCRResponse, out_file: str) -> str:
    markdown = get_combined_markdown_annotated(annotations_response)
    Path(out_file).write_text(markdown, encoding="utf-8")
    return markdown
