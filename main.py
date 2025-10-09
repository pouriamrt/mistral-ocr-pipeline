import os
import json
import asyncio
from time import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

from mistralai import Mistral

from to_markdown import convert_to_markdown
from get_annotations import get_annotation_async 
from utils import encode_pdf, get_pdf_page_count, merge_multiple_dicts_async

load_dotenv(override=True)

OUTPUT_DIR = Path("output")
FINAL_OUTPUT_DIR = OUTPUT_DIR / "aggregated"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
FINAL_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "3"))
MAX_PAGES_PER_REQ = 8

async def process_one_pdf_chunk(pdf_path: Path, client: Mistral, sem: asyncio.Semaphore, pages_chunk: list[int]) -> dict | None:
    """Process a single PDF:
       - encode PDF
       - call OCR with annotations (offloaded)
       - write markdown
       - return normalized dict for DataFrame row
    """
    async with sem:
        # 1) encode PDF (blocking disk I/O)
        base64_pdf = await encode_pdf(pdf_path)
        if not base64_pdf:
            print(f"[WARN] Skipping {pdf_path.name}: could not base64 encode.")
            return None

        # 2) OCR call (blocking network)
        try:
            annotations_response = await get_annotation_async(client, base64_pdf, pages=pages_chunk, image_annotation=False)
        except Exception as e:
            print(f"[ERROR] OCR failed for {pdf_path.name}: {e}")
            return None

        # 3) Parse annotations -> dict row
        try:
            response_dict = json.loads(annotations_response.model_dump_json())
            document_annotations = json.loads(response_dict["document_annotation"])
            row = {k: document_annotations.get(k) for k in document_annotations.keys()}
        except Exception as e:
            print(f"[ERROR] Failed to parse annotations for {pdf_path.name}: {e}")
            row = None

        # 4) Write markdown to file
        out_md = OUTPUT_DIR / f"{pdf_path.stem}_{int(min(pages_chunk)/MAX_PAGES_PER_REQ)}.md"
        try:
            await asyncio.to_thread(convert_to_markdown, annotations_response, str(out_md))
        except Exception as e:
            print(f"[ERROR] Writing markdown failed for {pdf_path.name}: {e}")

        return row

async def process_one_pdf(pdf_path: Path, client: Mistral, sem: asyncio.Semaphore) -> dict | None:
    pages = await get_pdf_page_count(pdf_path)
    
    if pages < MAX_PAGES_PER_REQ:
        return await process_one_pdf_chunk(pdf_path, client, sem, pages_chunk=list(range(pages)))
    else:
        rows = []
        for chunk in range(0, pages, MAX_PAGES_PER_REQ):
            result = await process_one_pdf_chunk(pdf_path, client, sem, pages_chunk=list(range(chunk, chunk + MAX_PAGES_PER_REQ)))
            if result is not None:
                rows.append(result)
        return await merge_multiple_dicts_async(rows)
        

async def amain():
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY is not set")

    client = Mistral(api_key=api_key)

    list_of_pdfs = list(Path("papers").glob("*.pdf"))
    if not list_of_pdfs:
        print("No PDFs found in ./papers")
        return

    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    start_time = time()

    # launch all tasks
    tasks = [process_one_pdf(p, client, sem) for p in list_of_pdfs]

    rows = []
    # progress over as_completed to keep tqdm responsive
    for fut in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Processing PDFs"):
        result = await fut
        if result is not None:
            rows.append(result)

    # build & save dataframe
    if rows:
        df_annotations = pd.DataFrame(rows)
        csv_path = FINAL_OUTPUT_DIR / "df_annotations.csv"
        parquet_path = FINAL_OUTPUT_DIR / "df_annotations.parquet"

        # CSV
        df_annotations.to_csv(csv_path, index=False)
        try:
            # Parquet (requires pyarrow or fastparquet)
            df_annotations.to_parquet(parquet_path, index=False)  # pip install pyarrow
        except Exception as e:
            print(f"[WARN] Parquet save failed: {e}")

        print(f"Saved {len(df_annotations)} rows to: {csv_path}")
    else:
        print("No successful rows to save.")

    end_time = time()
    print(f"Time taken: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(amain())
