import asyncio
from typing import List, Type, Optional, Dict, Any
import json

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from mistralai import Mistral
from mistralai.extra import response_format_from_pydantic_model
from mistralai.models import OCRResponse
from loguru import logger

from extraction_payload import (
    Image,
    ExtractionMetaDesign,               # class 1
    ExtractionPopulationIndications,    # class 2
    ExtractionMethods,                  # class 3
    ExtractionOutcomes,                 # class 4
)

from utils import merge_multiple_dicts_async

# ---------------- core OCR call (sync) ----------------

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=15))
def _get_annotation_sync(
    client: Mistral,
    payload_cls: Type[BaseModel],
    base64_pdf: str,
    pages: List[int],
    image_annotation: bool = False,
    model_name: str = "mistral-ocr-latest",
) -> OCRResponse:
    if not pages:
        logger.warning("OCR called with empty pages. Skipping.")
        return None

    kwargs = {
        "model": model_name,
        "pages": pages,
        "document": {
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{base64_pdf}",
        },
        "document_annotation_format": response_format_from_pydantic_model(payload_cls),
        # keep image bytes off to avoid huge payloads by default
        "include_image_base64": False,
    }

    if image_annotation:
        kwargs["bbox_annotation_format"] = response_format_from_pydantic_model(Image)
        # If you truly need raw image bytes in the response, flip to True
        # kwargs["include_image_base64"] = True

    try:
        return client.ocr.process(**kwargs)
    except Exception as e:
        logger.error(f"Error in OCR: {e}")
        return None


# ---------------- async thin wrapper ----------------

async def get_annotation_async(
    client: Mistral,
    payload_cls: Type[BaseModel],
    base64_pdf: str,
    pages: List[int],
    image_annotation: bool = False,
    model_name: str = "mistral-ocr-latest",
) -> OCRResponse:
    return await asyncio.to_thread(
        _get_annotation_sync, client, payload_cls, base64_pdf, pages, image_annotation, model_name
    )


# ---------------- convenience: run all payload schemas ----------------

async def run_all_payloads(
    client: Mistral,
    base64_pdf: str,
    pages: List[int],
    image_annotation: bool = False,
    model_name: str = "mistral-ocr-latest",
) -> Dict[str, Any]:
    """
    Executes OCR with all payload schemas and merges the
    document_annotation JSON objects into one flat dict.
    """
    payload_classes: List[Type[BaseModel]] = [
        ExtractionMetaDesign,
        ExtractionPopulationIndications,
        ExtractionMethods,
        ExtractionOutcomes,
    ]

    merged: Dict[str, Any] = {}
    for cls in payload_classes:
        resp: OCRResponse = await get_annotation_async(
            client, cls, base64_pdf, pages, image_annotation=image_annotation, model_name=model_name
        )
        
        resp_dict = json.loads(resp.model_dump_json())
        doc_anno_str = resp_dict.get("document_annotation", "{}")
        doc_anno: Dict[str, Any] = {}
        try:
            doc_anno = json.loads(doc_anno_str) if isinstance(doc_anno_str, str) else (doc_anno_str or {})
        except Exception:
            doc_anno = {}
            
        merged = await merge_multiple_dicts_async([merged, doc_anno])
            
    return merged, resp
