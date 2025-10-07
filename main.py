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

load_dotenv(override=True)

def main():
    api_key = os.getenv("MISTRAL_API_KEY")
    client = Mistral(api_key=api_key)

    list_of_pdfs = list(Path("papers").glob("*.pdf"))
    start_time = time()
    for pdf_path in tqdm(list_of_pdfs, desc="Processing PDFs", total=len(list_of_pdfs)):
        base64_pdf = encode_pdf(pdf_path=pdf_path)
        annotations_response = get_annotation(client, base64_pdf)
        response_dict = json.loads(annotations_response.model_dump_json())
        print(json.dumps(response_dict, indent=4))
        convert_to_markdown(annotations_response, f"output/{pdf_path.stem}.md")
        break
    
    end_time = time()
    print(f"Time taken: {end_time - start_time} seconds")
    
if __name__ == "__main__":
    main()