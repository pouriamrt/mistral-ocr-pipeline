
# 🧠 Mistral OCR Annotation Pipeline
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/) 
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](#-license) 
[![Build](https://img.shields.io/badge/status-async%20pipeline-success)](#-quickstart)

A **high‑throughput, asynchronous** pipeline for **OCR-driven extraction, annotation, and markdown generation** from scientific PDFs using **Mistral OCR**.  
Outputs include **annotated Markdown** files and an **aggregated CSV/Parquet** of structured fields defined by a robust **Pydantic schema**.

---

## ✨ Highlights
- ⚡ **Asynchronous batching** of PDFs with configurable concurrency
- 🧩 **Schema-driven extraction** via `ExtractionPayload` (Pydantic)
- 📝 **Markdown reports** with optional image annotations (base64 inlined)
- 📊 **Aggregated outputs** in CSV and Parquet for downstream analysis
- 🛡️ **Graceful error handling** with per-chunk resilience
- 📝 **Logging** to `logs/pipeline.log` with `loguru`

---

## 🗂️ Project Structure
> The repository ships with a minimal, code-first layout. At runtime the pipeline creates output folders.

```
.
├─ extraction_payload.py        # Pydantic schema capturing all target fields
├─ get_annotations.py           # Mistral OCR client + async wrapper
├─ main.py                      # Orchestrates concurrency, aggregation, and persistence
├─ to_markdown.py               # Transforms OCR response to Markdown with image annotations
├─ utils.py                     # Async I/O utilities: base64 encode, page count, dict merging
├─ uv.lock                      # (uv) resolved dependency lock
├─ pyproject.toml               # Project metadata / dependencies (for uv/pip)
├─ .python-version               # python version pin (e.g., 3.10.x / 3.11.x)
├─ .env.example                 # Example environment variables (copy to .env)
├─ papers/                      # (create) input PDFs to process
│  └─ your_paper_1.pdf
│  └─ your_paper_2.pdf
├─ output/                      # (auto-created) per-chunk Markdown exports
│  ├─ <paper_stem>_0.md
│  ├─ <paper_stem>_1.md
│  └─ aggregated/               # (auto-created) final tabular outputs
│     ├─ df_annotations.csv
│     └─ df_annotations.parquet
logs/                           # (auto-created) logs
│     └─ pipeline.log 
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
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Minimal requirements (if you’re installing manually):**
```bash
pip install mistralai pydantic aiofiles pypdf python-dotenv pandas tqdm pyarrow
```

### 3) Environment
Create a `.env` from the example and add your key:
```bash
cp .env.example .env
# then edit .env
MISTRAL_API_KEY=your_api_key_here
MAX_CONCURRENCY=3
```

### 4) Input PDFs
Place files in `./papers/`. The pipeline will scan `*.pdf` automatically.

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
1. **Load & Encode** — `utils.encode_pdf` base64-encodes PDFs asynchronously.  
2. **OCR + Annotation** — `get_annotations.py` calls Mistral OCR with a **document annotation format** mapped to `ExtractionPayload`.  
3. **Chunking** — Large PDFs are processed in **MAX_PAGES_PER_REQ** chunks with **async concurrency**.  
4. **Markdown** — `to_markdown.py` builds consolidated Markdown with (optional) image annotations.  
5. **Aggregation** — Partial rows from chunks are **deduped/merged** and written to CSV/Parquet.

**Ascii flow:**  
```
PDFs -> base64 -> Mistral OCR -> JSON (ExtractionPayload) -> Markdown + Tabular -> CSV/Parquet
```

---

## 🔧 Configuration
Tune behavior via `.env`:
```ini
MISTRAL_API_KEY=...     # required
MAX_CONCURRENCY=3       # concurrent OCR calls
```
Edit constants in `main.py` for chunk sizing:
```python
MAX_PAGES_PER_REQ = 8
```

---

## 📘 Usage Notes
- For **very long PDFs**, results are merged across chunks (`merge_multiple_dicts_async`).  
- To **enable image annotations**, switch `image_annotation=True` in `get_annotation_async` call inside `process_one_pdf_chunk`.  
- Parquet output requires `pyarrow` (or `fastparquet`).

---

## 🧪 Testing Locally
```bash
# Dry-run with a single sample
python -c "from pathlib import Path; print(list(Path('papers').glob('*.pdf'))[:1])"
python main.py
```

---

## 🛠️ Troubleshooting
- **`MISTRAL_API_KEY is not set`** → Ensure `.env` is present and loaded, or export variable in shell.  
- **Parquet save failed** → Install `pyarrow`: `pip install pyarrow`.  
- **No PDFs found** → Confirm files exist in `./papers/` and match `*.pdf`.  
- **Rate limits / timeouts** → Lower `MAX_CONCURRENCY` or `MAX_PAGES_PER_REQ`.

---

## 🗺️ Roadmap
- [ ] CLI flags (input dir, output dir, page range)  
- [ ] Optional **image annotation** mode in CLI  
- [ ] Retry & backoff on transient OCR errors  
- [ ] Rich HTML report export with assets

---

## 🙌 Acknowledgments
- **Mistral AI** — OCR + annotation interfaces  
- **Pydantic** — robust schema modeling  
- **pandas / pyarrow** — analytics-ready outputs  
- **pypdf** — fast PDF metadata access
- **loguru** — logging

---

## 🪪 License
MIT © 2025 Pouria Mortezaagha
