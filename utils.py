import base64
import aiofiles
import os
from collections.abc import Mapping
from typing import Any, Dict, Iterable
from pypdf import PdfReader
import asyncio
import re
import hashlib
from pathlib import Path
from loguru import logger
from datetime import datetime, timezone
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

REF_HEADER_RE = re.compile(
    r"(?i)^\s*(references?|bibliography|works\s+cited)\s*:?\s*$",
    re.MULTILINE,
)

async def encode_pdf(pdf_path: str) -> str | None:
    """Asynchronously encode a PDF file to base64."""
    try:
        if not os.path.exists(pdf_path):
            logger.error(f"The file {pdf_path} was not found.")
            return None

        async with aiofiles.open(pdf_path, "rb") as pdf_file:
            data = await pdf_file.read()
            return base64.b64encode(data).decode("utf-8")

    except FileNotFoundError:
        logger.error(f"The file {pdf_path} was not found.")
        return None
    except Exception as e:
        logger.error(f"Error: {e}")
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


def file_name_sha1(name: str) -> str:
    return hashlib.sha1(name.encode("utf-8")).hexdigest()


# ---------- Realtime writers ----------
def _normalize_record(record: dict, source_file: str) -> dict:
    """Add tracking columns and ensure JSON-serializable types."""
    rec = dict(record or {})
    rec["__source_file__"] = source_file
    rec["__processed_at__"] = datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z"
    return rec

def append_csv_row(csv_path: Path, row: dict):
    try:
        exists = csv_path.exists()
        df = pd.DataFrame([row])
        df.to_csv(csv_path, mode="a", header=not exists, index=False)
    except Exception as e:
        logger.error(f"Error appending row to {csv_path}: {e}")
        raise e

class ParquetAppender:
    """
    Incremental Parquet writer using pyarrow. Creates the writer lazily on first row.
    Ensures schema stability. Call .close() at the end.
    """
    def __init__(self, parquet_path: Path):
        self.parquet_path = parquet_path
        self._writer = None
        self._schema = None

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if self._writer is not None:
            self._writer.close()
        return False

    def append(self, row: dict):
        # Convert to Arrow Table
        table = pa.Table.from_pandas(pd.DataFrame([row]), preserve_index=False)
        if self._writer is None:
            if self.parquet_path.exists():
                existing = pq.read_table(self.parquet_path)
                self._schema = existing.schema
                # Align new table to existing schema (add missing cols, order)
                table = table_cast_like(table, self._schema)
                self._writer = pq.ParquetWriter(self.parquet_path, self._schema, use_dictionary=True)
            else:
                self._schema = table.schema
                self._writer = pq.ParquetWriter(self.parquet_path, self._schema, use_dictionary=True)
        else:
            table = table_cast_like(table, self._schema)

        self._writer.write_table(table)


def table_cast_like(table: pa.Table, target_schema: pa.schema) -> pa.Table:
    """
    Cast 'table' to 'target_schema' column order and types.
    - Adds any missing columns as null.
    - Drops extra columns not in target schema.
    """
    cols = []
    for field in target_schema:
        name = field.name
        if name in table.column_names:
            col = table[name]
            # Try to cast if needed
            try:
                col = col.cast(field.type)
            except Exception:
                # Fallback: best effort—let Arrow do implicit cast where possible
                pass
            cols.append(col)
        else:
            cols.append(pa.nulls(len(table), type=field.type))
    return pa.table(cols, schema=target_schema)


def load_existing_index(csv_path: Path) -> set[str]:
    """
    When OVERWRITE_MD is False, we skip PDFs already present in the CSV.
    Uses the '__source_file__' column as the id.
    """
    if not csv_path.exists():
        return set()
    try:
        df = pd.read_csv(csv_path, usecols=["__source_file__"])
        return set(df["__source_file__"].dropna().astype(str).tolist())
    except Exception as e:
        logger.error(f"Error loading existing index from {csv_path}: {e}")
        return set()
