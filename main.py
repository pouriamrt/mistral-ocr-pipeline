from mistralai import Mistral
from dotenv import load_dotenv
import os
from to_markdown import convert_to_markdown
from get_annotations import get_annotation
from utils import encode_pdf
from pathlib import Path
from tqdm import tqdm
from time import time
import json
import pandas as pd

load_dotenv(override=True)

def main():
    api_key = os.getenv("MISTRAL_API_KEY")
    client = Mistral(api_key=api_key)

    list_of_pdfs = list(Path("papers").glob("*.pdf"))
    df_annotations = pd.DataFrame()
    start_time = time()
    for pdf_path in tqdm(list_of_pdfs, desc="Processing PDFs", total=len(list_of_pdfs)):
        base64_pdf = encode_pdf(pdf_path=pdf_path)
        annotations_response = get_annotation(client, base64_pdf)
        response_dict = json.loads(annotations_response.model_dump_json())
        
        document_annotations = json.loads(response_dict["document_annotation"])
        document_annotations_normalized = {}
        for k, v in document_annotations.items():
            document_annotations_normalized[k] = [v]
        df_annotations = pd.concat([df_annotations, pd.DataFrame(document_annotations_normalized)], ignore_index=True)
        
        convert_to_markdown(annotations_response, f"output/{pdf_path.stem}.md")
        break
    
    end_time = time()
    print(f"Time taken: {end_time - start_time} seconds")
    
if __name__ == "__main__":
    main()