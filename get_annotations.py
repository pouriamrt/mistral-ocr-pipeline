import asyncio
from mistralai import Mistral
from mistralai.extra import response_format_from_pydantic_model
from mistralai.models import OCRResponse
from extraction_payload import Image, ExtractionPayload

def _get_annotation_sync(client: Mistral, base64_pdf: str, pages: list[int], image_annotation: bool = False) -> OCRResponse:
    if image_annotation is True:
        return client.ocr.process(
            model="mistral-ocr-latest",
            pages=pages,
            document={
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{base64_pdf}",
            },
            bbox_annotation_format=response_format_from_pydantic_model(Image),
            document_annotation_format=response_format_from_pydantic_model(ExtractionPayload),
            include_image_base64=True,
        )
    else:
        return client.ocr.process(
            model="mistral-ocr-latest",
            pages=pages,
            document={
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{base64_pdf}",
            },
            document_annotation_format=response_format_from_pydantic_model(ExtractionPayload),
            include_image_base64=False,
        )

async def get_annotation_async(client: Mistral, base64_pdf: str, pages: list[int], image_annotation: bool = False) -> OCRResponse:
    """Async wrapper running the blocking API call in a thread."""
    return await asyncio.to_thread(_get_annotation_sync, client, base64_pdf, pages, image_annotation)
