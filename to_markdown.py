from pathlib import Path
from mistralai.models import OCRResponse

def replace_images_in_markdown_annotated(markdown_str: str, images_dict: dict) -> str:
    for img_name, data in images_dict.items():
        markdown_str = markdown_str.replace(
            f"![{img_name}]({img_name})",
            f"![{img_name}]({data['image']})\n\n**{data['annotation']}**",
        )
    return markdown_str

def get_combined_markdown_annotated(ocr_response: OCRResponse) -> str:
    markdowns: list[str] = ["**" + ocr_response.document_annotation + "**"]
    for page in ocr_response.pages:
        image_data = {}
        for img in getattr(page, "images", []):
            image_data[img.id] = {"image": img.image_base64, "annotation": img.image_annotation}
        markdowns.append(replace_images_in_markdown_annotated(page.markdown, image_data))
    return "\n\n".join(markdowns)

def convert_to_markdown(annotations_response: OCRResponse, out_file: str) -> str:
    markdown = get_combined_markdown_annotated(annotations_response)
    Path(out_file).write_text(markdown, encoding="utf-8")
    return markdown
