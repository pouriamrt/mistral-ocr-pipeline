import asyncio
from typing import List, Type, Optional, Dict, Any, Tuple
import json

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

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
from time import monotonic

# tokens per second; tune in .env (e.g., OCR_RPS=4 → max 4 requests/sec)
_OCR_RPS = 5

class _AsyncRateLimiter:
    def __init__(self, rps: float):
        self._interval = 1.0 / max(rps, 1e-6)
        self._lock = asyncio.Lock()
        self._last = 0.0
    async def wait(self):
        async with self._lock:
            now = monotonic()
            wait = max(0.0, self._last + self._interval - now)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = monotonic()

_rate_limiter = _AsyncRateLimiter(_OCR_RPS)

# ---------------- core OCR call (sync) ----------------
def _is_rate_limit(e: Exception) -> bool:
    txt = str(e).lower()
    code = getattr(e, "status_code", None)
    return code == 429 or "rate" in txt or "quota" in txt or "too many requests" in txt

@retry(reraise=True, stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=60), retry=retry_if_exception(_is_rate_limit))
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
        if _is_rate_limit(e):
            raise
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
    await _rate_limiter.wait()
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
) -> Tuple[Dict[str, Any], OCRResponse]:
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

    tasks = [
        get_annotation_async(client, cls, base64_pdf, pages,
                             image_annotation=image_annotation, model_name=model_name)
        for cls in payload_classes
    ]
    responses: List[OCRResponse | None] = await asyncio.gather(*tasks, return_exceptions=False)

    merged: Dict[str, Any] = {}
    last_resp = None
    for resp in responses:
        if not resp:
            continue
        last_resp = resp

        resp_dict = json.loads(resp.model_dump_json())
        doc_anno_obj = resp_dict.get("document_annotation") or {}
        if isinstance(doc_anno_obj, str):
            try:
                doc_anno_obj = json.loads(doc_anno_obj)
            except Exception:
                doc_anno_obj = {}

        merged = await merge_multiple_dicts_async([merged, doc_anno_obj])

    return merged, last_resp
