import base64
import os

MATERIALS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "materials")


def ensure_materials_dir():
    os.makedirs(MATERIALS_DIR, exist_ok=True)
    return MATERIALS_DIR


def list_pdfs():
    ensure_materials_dir()
    return sorted(f for f in os.listdir(MATERIALS_DIR) if f.lower().endswith(".pdf"))


def pdf_document_block(filename):
    path = os.path.join(MATERIALS_DIR, filename)
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return {
        "type": "document",
        "source": {
            "type": "base64",
            "media_type": "application/pdf",
            "data": data,
        },
        "title": filename,
    }
