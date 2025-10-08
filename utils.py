import base64
import aiofiles
import os

async def encode_pdf(pdf_path: str) -> str | None:
    """Asynchronously encode a PDF file to base64."""
    try:
        if not os.path.exists(pdf_path):
            print(f"Error: The file {pdf_path} was not found.")
            return None

        async with aiofiles.open(pdf_path, "rb") as pdf_file:
            data = await pdf_file.read()
            return base64.b64encode(data).decode("utf-8")

    except FileNotFoundError:
        print(f"Error: The file {pdf_path} was not found.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None
