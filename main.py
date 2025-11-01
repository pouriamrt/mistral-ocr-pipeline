import os
import json
import asyncio
from time import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from alive_progress import alive_bar

from mistralai import Mistral

from to_markdown import convert_to_markdown
from get_annotations import run_all_payloads 
from utils import encode_pdf, get_pdf_page_count, merge_multiple_dicts_async

load_dotenv(override=True)

OUTPUT_DIR = Path("output")
FINAL_OUTPUT_DIR = OUTPUT_DIR / "aggregated"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
FINAL_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "3"))
MAX_PAGES_PER_REQ = 8
IMAGE_ANNOTATION = True
OVERWRITE_MD = True

async def process_one_pdf_chunk(pdf_path: Path, client: Mistral, sem: asyncio.Semaphore, pages_chunk: list[int], image_annotation: bool = False) -> dict | None:
    """Process a single PDF:
       - encode PDF
       - call OCR with annotations (offloaded)
       - write markdown
       - return normalized dict for DataFrame row
    """
    chunk_start = pages_chunk[0]
    async with sem:
        # 1) encode PDF (blocking disk I/O)
        base64_pdf = await encode_pdf(pdf_path)
        if not base64_pdf:
            print(f"[WARN] Skipping {pdf_path.name}: could not base64 encode.")
            return None

        # 2) OCR call (blocking network)
        try:
            annotations_response, ocr_response = await run_all_payloads(client, base64_pdf, pages=pages_chunk, image_annotation=image_annotation)
        except Exception as e:
            print(f"[ERROR] OCR failed for {pdf_path.name}: {e}")
            return None

        # 3) Parse annotations -> dict row
        try:
            document_annotations = annotations_response
            row = {k: document_annotations.get(k) for k in document_annotations.keys()}
        except Exception as e:
            print(f"[ERROR] Failed to parse annotations for {pdf_path.name}: {e}")
            row = None

        # 4) Write markdown to file
        out_md = OUTPUT_DIR / f"{pdf_path.stem}_{int(min(pages_chunk)/MAX_PAGES_PER_REQ)}.md"
        if not Path(out_md).exists() or OVERWRITE_MD:
            try:
                await asyncio.to_thread(convert_to_markdown, document_annotations, ocr_response, str(out_md))
            except Exception as e:
                print(f"[ERROR] Writing markdown failed for {pdf_path.name}: {e}")

        return {"__chunk_start__": chunk_start, **(row or {})}

async def process_one_pdf(pdf_path: Path, client: Mistral, sem: asyncio.Semaphore, image_annotation: bool = False) -> dict | None:
    pages = await get_pdf_page_count(pdf_path)
    if pages <= 0:
        return None
    
    if pages <= MAX_PAGES_PER_REQ:
        return await process_one_pdf_chunk(pdf_path, client, sem, list(range(pages)), image_annotation)

    chunk_tasks = []
    for start in range(0, pages, MAX_PAGES_PER_REQ):
        end = min(start + MAX_PAGES_PER_REQ, pages)
        chunk_tasks.append(
            process_one_pdf_chunk(pdf_path, client, sem, list(range(start, end)), image_annotation)
        )

    chunk_results = []
    for fut in asyncio.as_completed(chunk_tasks):
        r = await fut
        if r is not None:
            chunk_results.append(r)
            
    # sort by earliest pages
    chunk_results.sort(key=lambda d: d.get("__chunk_start__", 10**3))

    # strip helper key
    rows = [{k: v for k, v in d.items() if k != "__chunk_start__"} for d in chunk_results]

    return await merge_multiple_dicts_async(rows)
        

async def amain():
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY is not set")

    async with Mistral(api_key=api_key) as client:
        list_of_pdfs = list(Path("papers").glob("*.pdf"))
        if not list_of_pdfs:
            print("[ERROR] No PDFs found in ./papers")
            return
        print(f"[INFO] Processing {len(list_of_pdfs)} PDFs with image annotation: {IMAGE_ANNOTATION}")
        
        sem = asyncio.Semaphore(MAX_CONCURRENCY)
        start_time = time()

        # launch all tasks
        tasks = [process_one_pdf(p, client, sem, image_annotation=IMAGE_ANNOTATION) for p in list_of_pdfs]

        rows = []
        # progress over as_completed to keep alive_bar responsive
        with alive_bar(len(tasks), title="Processing PDFs") as bar:
            for fut in asyncio.as_completed(tasks):
                result = await fut
                if result is not None:
                    rows.append(result)
                bar()

    # build & save dataframe
    if rows:
        df_annotations = pd.DataFrame(rows)
        if "__chunk_start__" in df_annotations.columns:
            df_annotations = df_annotations.drop(columns=["__chunk_start__"])
        csv_path = FINAL_OUTPUT_DIR / "df_annotations.csv"
        parquet_path = FINAL_OUTPUT_DIR / "df_annotations.parquet"

        df_annotations.to_csv(csv_path, index=False)
        try:
            df_annotations.to_parquet(parquet_path, index=False)
        except Exception as e:
            print(f"[WARN] Parquet save failed: {e}")

        print(f"[INFO] Saved {len(df_annotations)} rows to: {csv_path}")
    else:
        print("[WARN] No successful rows to save.")

    end_time = time()
    print(f"[INFO] Time taken: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(amain())
