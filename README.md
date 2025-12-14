
# 🧠 Mistral OCR Annotation Pipeline
[![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/) 
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](#-license) 
[![Build](https://img.shields.io/badge/status-async%20pipeline-success)](#-quickstart)

A **high‑throughput, asynchronous** pipeline for **OCR-driven extraction, annotation, and markdown generation** from scientific PDFs using **Mistral OCR**.  
Outputs include **annotated Markdown** files and an **aggregated CSV/Parquet** of structured fields defined by a robust **Pydantic schema**.

---

## ✨ Highlights
- ⚡ **Asynchronous batching** of PDFs with configurable concurrency and rate limiting
- 🧩 **Schema-driven extraction** via `ExtractionPayload` (Pydantic) with multiple extraction classes
- ✂️ **PDF pre-processing** to strip unwanted sections (intro, background, acknowledgments, references) before OCR
- 📝 **Markdown reports** with optional image annotations (base64 inlined)
- 📊 **Aggregated outputs** in CSV and Parquet for downstream analysis
- 🛡️ **Graceful error handling** with per-chunk resilience and retry logic
- 🔍 **Post-processing validation** with LLM-based field verification
- 📝 **Logging** to `logs/pipeline.log` with `loguru` and rich console output
- 🔄 **Resume capability** to skip already-processed PDFs

---

## 🗂️ Project Structure
> The repository ships with a modular, package-based layout. At runtime the pipeline creates output folders.

```
.
├─ info_extraction/             # Core extraction package
│  ├─ __init__.py
│  ├─ extraction_payload.py    # Pydantic schema capturing all target fields
│  ├─ get_annotations.py        # Mistral OCR client + async wrapper with rate limiting
│  └─ to_markdown.py            # Transforms OCR response to Markdown with image annotations
├─ utils/                       # Utility functions package
│  ├─ __init__.py
│  ├─ utils.py                  # Async I/O utilities: base64 encode, page count, dict merging
│  └─ diagram.py                # Flow diagram generation for pipeline visualization
├─ pre_processing/              # PDF pre-processing package
│  ├─ __init__.py
│  ├─ main.py                   # Entry point for PDF section stripping
│  └─ pdf_section_stripper/     # PDF section removal utilities
│     ├─ __init__.py
│     ├─ config.py              # Configuration for section stripping behavior
│     ├─ models.py              # Data models for sections and cuts
│     ├─ outline_detector.py    # Detects sections from PDF outline/bookmarks
│     ├─ heading_detector.py    # Detects section headings via layout analysis
│     ├─ planner.py             # Builds page removal plan from detected sections
│     ├─ pipeline.py            # Main PDFSectionStripper class
│     └─ writer.py              # Writes stripped PDFs to disk
├─ post_processing/             # Post-processing and validation package
│  ├─ __init__.py
│  ├─ post_processing.py        # LLM-based field validation and quality checks
│  └─ unstack_payloads.py       # Field configuration and payload unstacking utilities
├─ main.py                      # Orchestrates concurrency, aggregation, and persistence
├─ pyproject.toml               # Project metadata / dependencies (for uv/pip)
├─ uv.lock                      # (uv) resolved dependency lock
├─ .env.example                 # Example environment variables (copy to .env)
├─ papers/                      # (create) input PDFs directory
│  ├─ todo/                     # Place PDFs here for processing
│  │  └─ your_paper_1.pdf
│  │  └─ your_paper_2.pdf
│  └─ todo_stripped/            # (auto-created) pre-processed PDFs with sections removed
├─ output/                      # (auto-created) per-chunk Markdown exports
│  ├─ <paper_stem>_0.md
│  ├─ <paper_stem>_1.md
│  └─ aggregated/               # (auto-created) final tabular outputs
│     ├─ df_annotations.csv
│     └─ df_annotations.parquet
├─ logs/                        # (auto-created) logs
│  ├─ pipeline.log              # Main pipeline execution logs
│  └─ pre_processing.log        # Pre-processing step logs
├─ data/                        # (optional) Additional data files for analysis
└─ README.md
```

---

## 🧩 Data Model (ExtractionPayload)
The pipeline extracts a rich set of biomedical/experimental fields (journal, design, cohorts, assay methods, timing, thresholds, outcomes, etc.) encoded in `extraction_payload.py`.  
Use these fields directly in analytics or dashboards (e.g., study design distribution, assay performance summaries).

> **Tip:** You can extend the schema at any time—new fields flow through to CSV/Parquet automatically.

---

## ⚙️ Setup

### 1) Clone
```bash
git clone https://github.com/yourname/mistral-ocr-pipeline.git
cd mistral-ocr-pipeline
```

### 2) Python & Dependencies
**Requires Python 3.13+**

Using `uv` (recommended):
```bash
uv sync
```

Or using `pip`:
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

**Key dependencies:**
- `mistralai` - Mistral OCR API client
- `pydantic` - Schema validation
- `aiofiles` - Async file I/O
- `pypdf` - PDF metadata extraction
- `pymupdf` (fitz) - PDF manipulation and section stripping
- `rapidfuzz` - Fuzzy string matching for heading detection
- `pandas` / `pyarrow` - Data aggregation
- `langchain` / `langchain-openai` - Post-processing validation
- `loguru` - Structured logging
- `tenacity` - Retry logic with exponential backoff
- `winloop` / `uvloop` - High-performance async event loop
- `rich` / `tqdm` - Progress bars and enhanced console output

### 3) Environment
Create a `.env` from the example and add your key:
```bash
cp .env.example .env
# then edit .env
MISTRAL_API_KEY=your_api_key_here
MAX_CONCURRENCY=3
IMAGE_ANNOTATION=False
OVERWRITE_MD=True
MODEL_JUDGE=gpt-5-mini  # For post-processing validation (optional)
```

### 4) Input PDFs
Place files in `./papers/todo/`. The pipeline will scan `*.pdf` automatically.

### 5) Pre-processing (Optional)
Before running the main pipeline, you may want to strip unwanted sections (intro, background, acknowledgments, references) from PDFs to reduce processing time and focus on core content:

```bash
python pre_processing/main.py
```

This will:
- Read PDFs from `papers/todo/`
- Detect section boundaries using outline detection and heading analysis
- Remove configured sections (customizable via `StripConfig` in `pre_processing/main.py`)
- Output cleaned PDFs to `papers/todo_stripped/`

You can then process the stripped PDFs by updating the input path in `main.py` or manually moving them.

---

## 🚀 Quickstart
```bash
python main.py
```

**What you’ll get**
- `output/<paper>_*.md` — readable per-chunk Markdown (includes document annotation and inlined images if enabled)
- `output/aggregated/df_annotations.csv` — one row per processed PDF with structured fields
- `output/aggregated/df_annotations.parquet` — fast, columnar equivalent (if `pyarrow` is installed)

---

## 🧠 How It Works
1. **Pre-processing** (optional) — `pre_processing/pdf_section_stripper` removes unwanted sections (intro, background, acknowledgments, references) using outline detection and heading analysis via PyMuPDF.
2. **Load & Encode** — `utils.utils.encode_pdf` base64-encodes PDFs asynchronously.  
3. **OCR + Annotation** — `info_extraction.get_annotations` calls Mistral OCR with rate limiting and retry logic, using **document annotation format** mapped to `ExtractionPayload` classes.  
4. **Chunking** — Large PDFs are processed in **MAX_PAGES_PER_REQ** chunks with **async concurrency** and semaphore-based rate limiting.  
5. **Markdown** — `info_extraction.to_markdown` builds consolidated Markdown with (optional) image annotations.  
6. **Aggregation** — Partial rows from chunks are **deduped/merged** using `merge_multiple_dicts_async` and written to CSV/Parquet.  
7. **Post-processing** (optional) — `post_processing.post_processing` provides LLM-based validation of extracted fields.

**Ascii flow:**  
```
PDFs -> [Pre-processing: strip sections] -> base64 -> Mistral OCR (rate-limited) -> JSON (ExtractionPayload) -> Markdown + Tabular -> CSV/Parquet
                                                                                                                              ↓
                                                                                                                    Post-processing (validation)
```

---

## 🔧 Configuration
Tune behavior via `.env`:
```ini
MISTRAL_API_KEY=...     # required
MAX_CONCURRENCY=3       # concurrent OCR calls
IMAGE_ANNOTATION=False  # enable base64 image inlining in markdown
OVERWRITE_MD=True       # overwrite existing markdown files
MODEL_JUDGE=gpt-5-mini  # LLM model for post-processing validation
```

Edit constants in `main.py` for chunk sizing:
```python
MAX_PAGES_PER_REQ = 8  # pages per OCR request
```

The pipeline uses `winloop` (Windows) or `uvloop` (Unix) for high-performance async I/O.

---

## 📘 Usage Notes
- **Pre-processing step**: Run `python pre_processing/main.py` first to strip unwanted sections and reduce processing time. Configure which sections to remove in `pre_processing/main.py` via `StripConfig`.
- For **very long PDFs**, results are merged across chunks using `merge_multiple_dicts_async`.  
- To **enable image annotations**, set `IMAGE_ANNOTATION=True` in `.env` or pass `image_annotation=True` to the processing function.  
- Parquet output requires `pyarrow` (included in dependencies).  
- The pipeline supports **resume mode**: if `OVERWRITE_MD=False`, already-processed PDFs (tracked by SHA1 hash) are skipped.  
- Rate limiting is built into the OCR client to respect API limits (configurable via `OCR_RPS`).
- Input PDFs should be placed in `papers/todo/` directory (not directly in `papers/`).

---

## 🧪 Testing Locally
```bash
# Dry-run with a single sample
python -c "from pathlib import Path; print(list(Path('papers/todo').glob('*.pdf'))[:1])"

# Optional: Pre-process PDFs to strip sections
python pre_processing/main.py

# Run main pipeline
python main.py
```

---

## 🛠️ Troubleshooting
- **`MISTRAL_API_KEY is not set`** → Ensure `.env` is present and loaded, or export variable in shell.  
- **Parquet save failed** → Install `pyarrow`: `pip install pyarrow`.  
- **No PDFs found** → Confirm files exist in `./papers/todo/` and match `*.pdf`.  
- **Rate limits / timeouts** → Lower `MAX_CONCURRENCY` or `MAX_PAGES_PER_REQ`.
- **Pre-processing not detecting sections** → Adjust `min_heading_score` in `StripConfig` or check PDF outline/bookmarks. Enable `debug=True` for detailed logging.

---

## 🗺️ Roadmap

We’re continuously evolving to make your experience better! Here are some highlights:

- ✅ Reliable: Automatic retry & backoff for transient OCR errors using `tenacity`
- ✅ Smooth operation: Built-in rate limiting for safe and efficient OCR API usage
- ✅ Robust: Effortless resume for already-processed PDFs—no lost progress
- ✅ Quality assurance: Integrated LLM-powered post-processing validation

**Coming soon to make your workflow even more seamless:**
- 🚀 Flexible CLI flags (customize input/output directories, select page ranges)
- 🌈 Beautiful rich HTML reports with embedded assets
- 📊 Enhanced batch processing with intuitive progress bars

Have feedback or ideas? We’d love to hear from you as we continue to build!

---

## 🙌 Acknowledgments
- **Mistral AI** — OCR + annotation interfaces  
- **Pydantic** — robust schema modeling  
- **pandas / pyarrow** — analytics-ready outputs  
- **pypdf** — fast PDF metadata access
- **PyMuPDF (fitz)** — PDF manipulation and section detection
- **rapidfuzz** — fuzzy string matching for heading detection
- **loguru** — structured logging
- **langchain** — LLM integration for post-processing
- **winloop / uvloop** — high-performance async event loops
- **tenacity** — retry logic with exponential backoff
- **rich / tqdm** — enhanced progress bars and console output

---

## 🪪 License
MIT © 2025 Pouria Mortezaagha
