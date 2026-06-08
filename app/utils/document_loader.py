import logging
from pathlib import Path

from app.constants import SUPPORTED_DOCUMENT_EXTENSIONS

logger = logging.getLogger(__name__)


def load_document(file_path: str | Path) -> str:
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    extension = file_path.suffix.lower()

    if extension not in SUPPORTED_DOCUMENT_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format: '{extension}'. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_DOCUMENT_EXTENSIONS))}"
        )

    if extension in (".txt", ".md"):
        return _load_text_file(file_path)
    elif extension == ".pdf":
        return _load_pdf_file(file_path)
    elif extension == ".docx":
        return _load_docx_file(file_path)

    return ""


def _load_text_file(file_path: Path) -> str:
    logger.debug("Loading text file: %s", file_path.name)
    return file_path.read_text(encoding="utf-8")


def _load_pdf_file(file_path: Path) -> str:
    try:
        from PyPDF2 import PdfReader

        logger.debug("Loading PDF file: %s", file_path.name)
        reader = PdfReader(str(file_path))
        return "\n\n".join(
            text for page in reader.pages if (text := page.extract_text())
        )
    except ImportError:
        raise ImportError("PyPDF2 is required to load PDF files. Install with: pip install PyPDF2")


def _load_docx_file(file_path: Path) -> str:
    try:
        from docx import Document

        logger.debug("Loading DOCX file: %s", file_path.name)
        doc = Document(str(file_path))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        raise ImportError("python-docx is required to load DOCX files. Install with: pip install python-docx")
