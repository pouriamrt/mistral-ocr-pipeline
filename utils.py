import base64
import aiofiles
import os
from collections.abc import Mapping
from typing import Any, Dict, Iterable
from pypdf import PdfReader
import asyncio
import re


REF_HEADER_RE = re.compile(
    r"(?i)^\s*(references?|bibliography|works\s+cited)\s*:?\s*$",
    re.MULTILINE,
)

async def encode_pdf(pdf_path: str) -> str | None:
    """Asynchronously encode a PDF file to base64."""
    try:
        if not os.path.exists(pdf_path):
            print(f"[ERROR] The file {pdf_path} was not found.")
            return None

        async with aiofiles.open(pdf_path, "rb") as pdf_file:
            data = await pdf_file.read()
            return base64.b64encode(data).decode("utf-8")

    except FileNotFoundError:
        print(f"[ERROR] The file {pdf_path} was not found.")
        return None
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return None


async def get_pdf_page_count(path: str) -> int:
    def _count():
        with open(path, "rb") as f:
            reader = PdfReader(f)
            for i, page in enumerate(reader.pages):
                try:
                    txt = page.extract_text() or ""
                except:
                    txt = ""
                if REF_HEADER_RE.search(txt):
                    return i
            return len(reader.pages)

    return await asyncio.to_thread(_count)

async def _merge_values_async(a: Any, b: Any) -> Any:
    def _normalize_str(x):
        return x.strip() if isinstance(x, str) else x
    
    def _is_empty(v: Any) -> bool:
        return v in (None, "", [], {})
    
    a = _normalize_str(a)
    b = _normalize_str(b)
    if _is_empty(a):
        return b
    if isinstance(a, list) and isinstance(b, list):
        seen = set()
        out = []
        for x in a + b:
            key = repr(x)
            if key not in seen:
                seen.add(key)
                out.append(x)
        return out
    if isinstance(a, Mapping) and isinstance(b, Mapping):
        return await merge_multiple_dicts_async([dict(a), dict(b)])
    return a


async def merge_multiple_dicts_async(dicts: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Asynchronously merge multiple dictionaries using async merge logic."""
    dicts = list(dicts)
    if not dicts:
        return {}
    if len(dicts) == 1:
        return dict(dicts[0])

    merged = dict(dicts[0])
    for extra in dicts[1:]:
        for k, v in extra.items():
            if k not in merged:
                merged[k] = v
            else:
                merged[k] = await _merge_values_async(merged[k], v)
    return merged
