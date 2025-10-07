from mistralai import Mistral
from mistralai.extra import response_format_from_pydantic_model
from extration_payload import Image, ExtractionPayload
from mistralai.models import OCRResponse


def get_annotation(client: Mistral, base64_pdf: str, image_annotation: bool = False) -> OCRResponse:
    # OCR Call with Annotations
    if image_annotation == True:
        annotations_response = client.ocr.process(
            model="mistral-ocr-latest",
            pages=list(range(8)), 
            document={
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{base64_pdf}"
            },
            bbox_annotation_format=response_format_from_pydantic_model(Image),
            document_annotation_format=response_format_from_pydantic_model(ExtractionPayload),
            include_image_base64=True
        )
    else:
        annotations_response = client.ocr.process(
            model="mistral-ocr-latest",
            pages=list(range(8)), 
            document={
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{base64_pdf}"
            },
            document_annotation_format=response_format_from_pydantic_model(ExtractionPayload),
            include_image_base64=False
        )

    return annotations_response