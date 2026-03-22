# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

**ie-mistral** is an async pipeline that OCR-extracts structured biomedical data from scientific PDFs using Mistral OCR. It targets DOAC (Direct Oral Anticoagulant) studies — extracting study design, population, methods, outcomes, and diagnostic performance metrics into CSV/Parquet tables.

## Commands

```bash
# Install dependencies
uv sync

# Run the main extraction pipeline
python main.py

# Pre-process PDFs (strip intro/refs/acknowledgments before OCR)
python pre_processing/main.py

# Lint & format
ruff check --fix
ruff format

# Type check (no ruff/mypy config in pyproject.toml yet — use defaults)
mypy --strict

# Pre-commit hooks (ruff check + format)
pre-commit run --all-files
```

No automated test suite exists yet. Validation is done manually via notebooks.

## Architecture

### Pipeline Flow

```
PDFs (papers/todo/) → Pre-processing (optional strip sections) → Base64 encode
  → Mistral OCR (async, rate-limited, 8-page chunks) → 5 extraction schemas in parallel
  → Deep-merge chunk results → Markdown + CSV/Parquet → Post-processing (LLM validation)
```

### Core Modules

- **`main.py`** — Orchestrator. Controls concurrency (`asyncio.Semaphore`), chunking (8 pages/request), resume tracking (SHA1 hashes in CSV), and aggregation to CSV/Parquet.

- **`info_extraction/extraction_payload.py`** (~2100 lines) — The heart of the project. Five Pydantic V2 models defining 60+ fields with aliases, descriptions, and extraction guidelines:
  1. `ExtractionMetaDesign` — bibliography, study design, country
  2. `ExtractionPopulationIndications` — demographics, indications, subgroups
  3. `ExtractionMethods` — sample size, dosing, assay methods, timing
  4. `ExtractionOutcomes` — endpoints, events, hazard ratios, bleeding
  5. `ExtractionDiagnosticPerformance` — sensitivity, specificity, ROC-AUC, cutoffs

  Each field has a paired `_sentence_from_text` field for traceability. Schema changes auto-propagate to CSV/Parquet columns via `df_cols_from_models()`.

- **`info_extraction/get_annotations.py`** — Mistral OCR client. `_AsyncRateLimiter` (default 5 req/s), `tenacity` retry with exponential backoff, `run_all_payloads()` runs all 5 extraction classes in parallel per chunk.

- **`info_extraction/to_markdown.py`** — Converts OCR response to Markdown with optional base64-inlined images.

- **`utils/utils.py`** — Async helpers: `encode_pdf()`, `get_pdf_page_count()`, `merge_multiple_dicts_async()` (deep-merges dicts from chunks — dedup lists, merge nested), `ParquetAppender` (incremental writes with schema alignment via `table_cast_like()`), `append_csv_row()`, `file_name_sha1()`.

- **`pre_processing/pdf_section_stripper/`** — Removes unwanted PDF sections before OCR. Dual detection: outline/bookmarks (`outline_detector.py`) + fuzzy heading matching via `rapidfuzz` (`heading_detector.py`). Configured via `StripConfig`.

- **`post_processing/`** — LLM-based validation using `langchain` + OpenAI. Checks extracted values against supporting sentences. Field rules in `FieldValidationConfig` (`unstack_payloads.py`).

### Key Design Decisions

- **Chunking + merging**: Large PDFs split into 8-page chunks processed concurrently, then deep-merged. This is central — changes to merging logic in `merge_multiple_dicts_async` affect all extraction.
- **Schema-driven**: Pydantic models are the single source of truth for both the Mistral API contract and output column definitions. Add a field to a model → it appears in CSV/Parquet.
- **Resume mode**: SHA1 of filename tracked in CSV. Set `OVERWRITE_MD=False` to skip already-processed PDFs.
- **Incremental I/O**: Rows append to CSV/Parquet one at a time (no in-memory DataFrame accumulation).

## Configuration

Via `.env` (loaded with `python-dotenv`, `override=True`):

| Variable | Default | Purpose |
|---|---|---|
| `MISTRAL_API_KEY` | *required* | Mistral API key |
| `MAX_CONCURRENCY` | `3` | Concurrent OCR tasks |
| `MAX_PAGES_PER_REQ` | `8` (hardcoded in main.py) | Pages per OCR chunk |
| `IMAGE_ANNOTATION` | `False` | Base64 inline images in markdown |
| `OVERWRITE_MD` | `True` | Overwrite existing markdown / reprocess PDFs |
| `MODEL_JUDGE` | `gpt-5-mini` | LLM for post-processing validation |
| `INPUT_DIR` | `papers/todo` | PDF input directory |
| `OCR_RPS` | `5` (hardcoded in get_annotations.py) | OCR requests per second rate limit |

## Conventions

- **Python 3.13+** required. Uses `winloop` on Windows, `uvloop` on Unix for the async event loop.
- **Async-first**: All I/O is async (`aiofiles`, `asyncio`). New I/O code should follow this pattern.
- **Pydantic V2** with `model_config = ConfigDict(populate_by_name=True)` and field aliases for CSV column names.
- **Logging**: `loguru` everywhere. Console (stderr, INFO) + rotating file (`logs/pipeline.log`, 1MB rotation, 10-day retention).
- **Package manager**: `uv` with `uv.lock` for reproducible installs.
- **Pre-commit**: ruff check + ruff format only (no mypy hook yet).
- **Active development area**: Prompt engineering in `extraction_payload.py` field descriptions — these directly control extraction quality.
