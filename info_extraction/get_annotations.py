import asyncio
import base64
import os
from typing import List, Type, Dict, Any, Tuple
import json
import uuid
from pathlib import Path

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from mistralai import Mistral
from mistralai.extra import response_format_from_pydantic_model
from mistralai.models import OCRResponse
from loguru import logger
import fitz as pymupdf

from info_extraction.extraction_payload import (
    Image,
    EXTRACTION_SCHEMAS,
)

from utils.utils import merge_multiple_dicts_async
from time import monotonic

_OCR_RPS = float(os.getenv("OCR_RPS", "5"))


class _AsyncRateLimiter:
    def __init__(self, rps: float):
        self._interval = 1.0 / max(rps, 1e-6)
        self._lock: asyncio.Lock | None = None
        self._last = 0.0

    async def wait(self):
        # Lazy-init lock inside the running event loop (safe across loop restarts)
        if self._lock is None:
            self._lock = asyncio.Lock()
        async with self._lock:
            now = monotonic()
            wait = max(0.0, self._last + self._interval - now)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = monotonic()


_rate_limiter = _AsyncRateLimiter(_OCR_RPS)


# ---------------- core OCR call (sync) ----------------
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _is_retryable(e: Exception) -> bool:
    txt = str(e).lower()
    code = getattr(e, "status_code", None)
    if code in _RETRYABLE_STATUS_CODES:
        return True
    return (
        "rate" in txt
        or "quota" in txt
        or "too many requests" in txt
        or "timeout" in txt
    )


def _is_invalid_pdf_error(e: Exception) -> bool:
    """Check if the error is specifically a 'not a valid PDF' rejection."""
    txt = str(e).lower()
    return "document_parser_invalid_file" in txt or "not a valid pdf" in txt


def _render_pages_to_images(
    pdf_path: str | Path, pages: List[int], dpi: int = 200
) -> List[str]:
    """Render specific PDF pages to base64 PNG images using PyMuPDF."""
    doc = pymupdf.open(str(pdf_path))
    images = []
    for page_num in pages:
        if page_num >= len(doc):
            continue
        page = doc[page_num]
        pix = page.get_pixmap(dpi=dpi)
        img_bytes = pix.tobytes("png")
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        images.append(b64)
    doc.close()
    return images


@retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=120),
    retry=retry_if_exception(_is_retryable),
)
def _get_annotation_sync(
    client: Mistral,
    payload_cls: Type[BaseModel],
    base64_pdf: str,
    pages: List[int],
    image_annotation: bool = False,
    model_name: str = "mistral-ocr-latest",
) -> OCRResponse | None:
    if not pages:
        logger.warning("OCR called with empty pages. Skipping.")
        return None

    kwargs = {
        "id": str(uuid.uuid4()),
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

    try:
        return client.ocr.process(**kwargs)
    except Exception as e:
        if _is_retryable(e):
            raise
        logger.error(f"Non-retryable OCR error: {e}")
        return None


@retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=120),
    retry=retry_if_exception(_is_retryable),
)
def _get_annotation_from_image_sync(
    client: Mistral,
    payload_cls: Type[BaseModel],
    base64_image: str,
    model_name: str = "mistral-ocr-latest",
) -> OCRResponse | None:
    """OCR a single page rendered as a PNG image."""
    kwargs = {
        "id": str(uuid.uuid4()),
        "model": model_name,
        "document": {
            "type": "image_url",
            "image_url": f"data:image/png;base64,{base64_image}",
        },
        "document_annotation_format": response_format_from_pydantic_model(payload_cls),
        "include_image_base64": False,
    }
    try:
        return client.ocr.process(**kwargs)
    except Exception as e:
        if _is_retryable(e):
            raise
        logger.error(f"Non-retryable image OCR error: {e}")
        return None


# ---------------- async thin wrapper ----------------


async def get_annotation_async(
    client: Mistral,
    payload_cls: Type[BaseModel],
    base64_pdf: str,
    pages: List[int],
    image_annotation: bool = False,
    model_name: str = "mistral-ocr-latest",
    pdf_path: str | Path | None = None,
) -> OCRResponse | None:
    await _rate_limiter.wait()
    result = await asyncio.to_thread(
        _get_annotation_sync,
        client,
        payload_cls,
        base64_pdf,
        pages,
        image_annotation,
        model_name,
    )

    # If PDF-based OCR returned None and we have a PDF path, try image fallback
    if result is None and pdf_path is not None:
        logger.info(
            f"PDF OCR failed for {Path(pdf_path).name}, "
            f"falling back to image-based OCR for pages {pages}"
        )
        base64_images = await asyncio.to_thread(
            _render_pages_to_images, pdf_path, pages
        )
        if not base64_images:
            return None

        # OCR each page image and merge into a single combined response
        image_tasks = []
        for b64_img in base64_images:
            await _rate_limiter.wait()
            image_tasks.append(
                asyncio.to_thread(
                    _get_annotation_from_image_sync,
                    client,
                    payload_cls,
                    b64_img,
                    model_name,
                )
            )
        image_results = await asyncio.gather(*image_tasks, return_exceptions=True)

        # Return the first successful response (annotations merge at a higher level)
        for r in image_results:
            if isinstance(r, OCRResponse) and r is not None:
                return r
        return None

    return result


# ---------------- convenience: run all payload schemas ----------------


async def run_all_payloads(
    client: Mistral,
    base64_pdf: str,
    pages: List[int],
    image_annotation: bool = False,
    model_name: str = "mistral-ocr-latest",
    pdf_path: str | Path | None = None,
) -> Tuple[Dict[str, Any], OCRResponse]:
    """
    Executes OCR with all payload schemas and merges the
    document_annotation JSON objects into one flat dict.

    If pdf_path is provided and PDF-based OCR fails (e.g., "not a valid PDF"),
    falls back to rendering pages as images and using image-based OCR.
    """
    payload_classes = EXTRACTION_SCHEMAS

    tasks = [
        get_annotation_async(
            client,
            cls,
            base64_pdf,
            pages,
            image_annotation=image_annotation,
            model_name=model_name,
            pdf_path=pdf_path,
        )
        for cls in payload_classes
    ]
    raw_responses = await asyncio.gather(*tasks, return_exceptions=True)

    merged: Dict[str, Any] = {}
    last_resp = None
    for resp in raw_responses:
        if isinstance(resp, BaseException):
            logger.error(f"OCR schema task failed: {resp}")
            continue
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
