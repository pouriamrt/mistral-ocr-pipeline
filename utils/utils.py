import base64
import aiofiles
import io
import os
import json
from collections.abc import Mapping
from typing import Any, Iterable, List
from pypdf import PdfReader, PdfWriter
import fitz as pymupdf
import asyncio
import re
import hashlib
from pathlib import Path
from loguru import logger
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc
from pyarrow import types as pat
import pandas as pd

REF_HEADER_RE = re.compile(
    r"(?i)^\s*(references?|bibliography|works\s+cited)\s*:?\s*$",
    re.MULTILINE,
)


def _repair_pdf_bytes(raw: bytes) -> bytes:
    """Rebuild PDF from scratch to fix structural issues.

    Some PDFs have non-standard internal structures that cause Mistral's
    parser to reject them.  A two-pass rebuild (pypdf page extraction,
    then PyMuPDF clean-up) produces a fully clean PDF.
    """
    try:
        # Pass 1: rebuild page-by-page with pypdf (strips bad internal refs)
        reader = PdfReader(io.BytesIO(raw))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        intermediate = buf.getvalue()

        # Pass 2: clean up with PyMuPDF (garbage collection + deflation)
        doc = pymupdf.open(stream=intermediate, filetype="pdf")
        repaired = doc.tobytes(deflate=True, garbage=4)
        doc.close()
        return repaired
    except Exception:
        return raw  # return original if repair fails


async def encode_pdf(pdf_path: str | Path) -> str | None:
    """Asynchronously encode a PDF file to base64.

    Sends the original PDF bytes without modification. PDF repair is NOT
    applied here because it strips fonts/metadata that Mistral uses for
    extraction. The image-based fallback in get_annotations handles the
    rare PDFs that Mistral's parser rejects.
    """
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


async def get_pdf_page_count(path: str | Path) -> int:
    def _count():
        with open(path, "rb") as f:
            reader = PdfReader(f)
            for i, page in enumerate(reader.pages):
                try:
                    txt = page.extract_text() or ""
                except Exception:
                    txt = ""
                if REF_HEADER_RE.search(txt):
                    return i
            return len(reader.pages)

    return await asyncio.to_thread(_count)


def _merge_values(a: Any, b: Any) -> Any:
    def _normalize_str(x):
        return x.strip() if isinstance(x, str) else x

    def _is_empty(v: Any) -> bool:
        return v in (None, "", [], {})

    a = _normalize_str(a)
    b = _normalize_str(b)
    if _is_empty(a):
        return b
    if isinstance(a, list) and isinstance(b, list):
        seen: set[str] = set()
        out: list[Any] = []
        for x in a + b:
            key = (
                json.dumps(x, sort_keys=True, ensure_ascii=False)
                if isinstance(x, (dict, list))
                else repr(x)
            )
            if key not in seen:
                seen.add(key)
                out.append(x)
        return out
    if isinstance(a, Mapping) and isinstance(b, Mapping):
        return merge_dicts([dict(a), dict(b)])
    return a


def merge_dicts(dicts: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Deeply merge multiple dictionaries: dedup lists, recurse into nested dicts."""
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
                merged[k] = _merge_values(merged[k], v)
    return merged


# Backward-compatible async wrapper (calls sync merge under the hood)
async def merge_multiple_dicts_async(dicts: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Async wrapper around merge_dicts for backward compatibility."""
    return merge_dicts(dicts)


def file_name_sha1(name: str) -> str:
    """Hash filename for resume-mode identity tracking. Uses SHA256 despite the name."""
    return hashlib.sha256(name.encode("utf-8")).hexdigest()


# ---------- Realtime writers ----------
def append_csv_row(csv_path: Path, row: dict, cols: List[str]):
    try:
        exists = csv_path.exists()
        df = pd.DataFrame([row], columns=cols)
        df.to_csv(csv_path, mode="a", header=not exists, index=False)
    except Exception as e:
        logger.error(f"Error appending row to {csv_path}: {e}")
        raise e


class ParquetAppender:
    """
    Incremental Parquet writer using pyarrow. Creates the writer lazily on first row.
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
        table = pa.Table.from_pandas(pd.DataFrame([row]), preserve_index=False)
        if self._writer is None:
            if self.parquet_path.exists():
                try:
                    self.drop_empty_rows_pq()
                    existing = pq.read_table(self.parquet_path)
                    self._schema = existing.schema
                except Exception as e:
                    logger.warning(
                        f"Could not read existing Parquet file, starting fresh: {e}"
                    )
                    self._schema = table.schema
                # Align new table to existing schema (add missing cols, order)
                table = table_cast_like(table, self._schema)
                self._writer = pq.ParquetWriter(
                    self.parquet_path, self._schema, use_dictionary=True
                )
            else:
                self._schema = table.schema
                self._writer = pq.ParquetWriter(
                    self.parquet_path, self._schema, use_dictionary=True
                )

        table = table_cast_like(table, self._schema)
        self._writer.write_table(table)

    def drop_empty_rows_pq(self):
        """
        Arrow-native filter:
        - Keep rows where '__source_file__' is not null/empty.
        - Drop rows where 'Journal' is numeric (int/float), or a numeric-looking string
            (e.g., '123', '  12.5  ', '+3e-2'). Null 'Journal' is kept.
        """
        table = pq.read_table(self.parquet_path, memory_map=True)
        mask = None

        if "__source_file__" in table.column_names:
            src = table["__source_file__"]
            mask = pc.and_(pc.is_valid(src), pc.not_equal(src, ""))

        if "Journal" in table.column_names:
            j = table["Journal"]
            t = j.type
            if pat.is_integer(t) or pat.is_floating(t):
                mask_journal_keep = pc.is_null(j)
            elif pat.is_string(t) or pat.is_large_string(t):
                is_numeric_str = pc.match_substring_regex(
                    j, r"^\s*[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?\s*$"
                )
                mask_journal_keep = pc.or_(pc.is_null(j), pc.invert(is_numeric_str))
            else:
                mask_journal_keep = pc.is_valid(j)
            mask = (
                pc.and_(mask, mask_journal_keep)
                if mask is not None
                else mask_journal_keep
            )

        if mask is not None:
            filtered = table.filter(mask)
        else:
            filtered = table

        pq.write_table(
            filtered,
            self.parquet_path,
            use_dictionary=True,
            compression="zstd",
            write_statistics=True,
        )


def table_cast_like(table: pa.Table, target_schema: pa.schema) -> pa.Table:
    """
    Cast 'table' to 'target_schema' column order and types.
    - Adds any missing columns as null.
    - Drops extra columns not in target schema.
    """

    def _is_null_type(arrow_type):
        """Check if type is null or contains null (e.g., list<item: null>)."""
        if pa.types.is_null(arrow_type):
            return True
        if pa.types.is_list(arrow_type) or pa.types.is_large_list(arrow_type):
            return _is_null_type(arrow_type.value_type)
        return False

    cols = []
    for field in target_schema:
        name = field.name
        if name in table.column_names:
            col = table[name]
            # Check if target type is null (including nested nulls in lists)
            if _is_null_type(field.type):
                # If target expects null but source has data, convert to null
                cols.append(pa.nulls(len(table), type=field.type))
                continue
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
        drop_empty_rows(csv_path)
        df = pd.read_csv(csv_path, usecols=["__source_file__"])
        return set(df["__source_file__"].dropna().astype(str).tolist())
    except Exception as e:
        logger.error(f"Error loading existing index from {csv_path}: {e}")
        return set()


def drop_empty_rows(csv_path: Path):
    """
    Drop rows with:
      - NaN in '__source_file__'
      - 'Journal' that is numeric (int-like or float-like)
    """
    df = pd.read_csv(csv_path)
    if "__source_file__" in df.columns:
        df = df.dropna(subset=["__source_file__"])

    if "Journal" in df.columns:

        def is_numeric(x):
            try:
                float(str(x).strip())
                return True
            except Exception:
                return False

        df = df[~df["Journal"].apply(is_numeric)]
    df.to_csv(csv_path, index=False)
