import os
import json
import asyncio
from time import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from alive_progress import alive_bar
from loguru import logger
import sys

from mistralai import Mistral

from to_markdown import convert_to_markdown
from get_annotations import run_all_payloads 
from utils import encode_pdf, get_pdf_page_count, merge_multiple_dicts_async, file_name_sha1, load_existing_index, append_csv_row, ParquetAppender

load_dotenv(override=True)

OUTPUT_DIR = Path("output")
FINAL_OUTPUT_DIR = OUTPUT_DIR / "aggregated"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
FINAL_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "3"))
MAX_PAGES_PER_REQ = 8
IMAGE_ANNOTATION = True
OVERWRITE_MD = True

logger.remove()
logger.add(sys.stderr, 
           format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
           colorize=True,
           level="INFO")
logger.add("logs/pipeline.log", format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}", 
           rotation="1 MB", retention="10 days", level="DEBUG",
           enqueue=True, backtrace=True, diagnose=False)

async def process_one_pdf_chunk(pdf_path: Path, base64_pdf: str, client: Mistral, sem: asyncio.Semaphore, pages_chunk: list[int], image_annotation: bool = False) -> dict | None:
    """Process a single PDF:
       - encode PDF
       - call OCR with annotations (offloaded)
       - write markdown
       - return normalized dict for DataFrame row
    """
    chunk_start = pages_chunk[0]
    async with sem:
        # 1) OCR call (blocking network)
        try:
            annotations_response, ocr_response = await run_all_payloads(client, base64_pdf, pages=pages_chunk, image_annotation=image_annotation)
        except Exception as e:
            logger.error(f"OCR failed for {pdf_path.name}: {e}")
            return None

        # 2) Parse annotations -> dict row
        try:
            document_annotations = annotations_response
            row = {k: document_annotations.get(k) for k in document_annotations.keys()}
        except Exception as e:
            logger.error(f"Failed to parse annotations for {pdf_path.name}: {e}")
            row = None

        # 3) Write markdown to file
        out_md = OUTPUT_DIR / f"{pdf_path.stem}_{int(min(pages_chunk)/MAX_PAGES_PER_REQ)}.md"
        if not Path(out_md).exists() or OVERWRITE_MD:
            try:
                await asyncio.to_thread(convert_to_markdown, document_annotations, ocr_response, str(out_md))
            except Exception as e:
                logger.error(f"Writing markdown failed for {pdf_path.name}: {e}")

        return {"__chunk_start__": chunk_start, **(row or {})}

async def process_one_pdf(pdf_path: Path, client: Mistral, sem: asyncio.Semaphore, image_annotation: bool = False) -> dict | None:
    pages = await get_pdf_page_count(pdf_path)
    if pages <= 0:
        return None
    
    base64_pdf = await encode_pdf(pdf_path)
    if not base64_pdf:
        logger.warning(f"Skipping {pdf_path.name}: could not base64 encode.")
        return None
    
    if pages <= MAX_PAGES_PER_REQ:
        return await process_one_pdf_chunk(pdf_path, base64_pdf, client, sem, list(range(pages)), image_annotation)

    chunk_tasks = []
    for start in range(0, pages, MAX_PAGES_PER_REQ):
        end = min(start + MAX_PAGES_PER_REQ, pages)
        chunk_tasks.append(
            process_one_pdf_chunk(pdf_path, base64_pdf, client, sem, list(range(start, end)), image_annotation)
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

    merged = await merge_multiple_dicts_async(rows)
    merged["__source_file__"] = file_name_sha1(pdf_path.name)
    return merged
        

async def amain():
    try:
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise RuntimeError("MISTRAL_API_KEY is not set")
        
        csv_path = FINAL_OUTPUT_DIR / "df_annotations.csv"
        parquet_path = FINAL_OUTPUT_DIR / "df_annotations.parquet"
        
        # Resume index: skip files that already exist in CSV if OVERWRITE_MD is False
        already_processed = load_existing_index(csv_path) if not OVERWRITE_MD else set()

        async with Mistral(api_key=api_key) as client:
            list_of_pdfs = list(Path("papers").glob("*.pdf"))
            if not list_of_pdfs:
                logger.error("No PDFs found in ./papers")
                return
            
            todo = [p for p in list_of_pdfs if (file_name_sha1(p.name) not in already_processed)]
            skipped = len(list_of_pdfs) - len(todo)
            if skipped:
                logger.info(f"Resume mode: skipping {skipped} already-processed PDFs (OVERWRITE_MD={OVERWRITE_MD}).")

            logger.info(f"Processing {len(todo)} PDFs with image annotation: {IMAGE_ANNOTATION}")
            
            sem = asyncio.Semaphore(MAX_CONCURRENCY)
            start_time = time()

            # launch all tasks
            tasks = [process_one_pdf(p, client, sem, image_annotation=IMAGE_ANNOTATION) for p in todo]

            row_count = 0
            with ParquetAppender(parquet_path) as pw:
                with alive_bar(len(tasks), title="Processing PDFs") as bar:
                    for fut in asyncio.as_completed(tasks):
                        result = await fut
                        if result is not None:
                            # offload the blocking disk writes
                            await asyncio.to_thread(append_csv_row, csv_path, result)
                            await asyncio.to_thread(pw.append, result)

                            row_count += 1
                            logger.debug(f"row appended ({row_count}) -> {result.get('__source_file__')}")
                        else:
                            logger.debug("Skipped a PDF because it returned None")

                        bar()

        logger.info(f"Saved {row_count} rows to {parquet_path} and {csv_path}")
        logger.info(f"Time taken: {time() - start_time:.2f} seconds")
        
    except KeyboardInterrupt:
        logger.error("Keyboard interrupt received. Exiting...")
        sys.exit()

if __name__ == "__main__":
    asyncio.run(amain())
