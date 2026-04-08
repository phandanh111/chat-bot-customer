"""
Document loader utilities.
Handles reading different file formats and returning raw text.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Supported file extensions
SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def load_document(file_path: str | Path) -> str:
    """
    Load a document and return its text content.

    Supports: .txt, .md, .pdf, .docx

    Args:
        file_path: Path to the document file.

    Returns:
        Text content of the document.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is not supported.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    extension = file_path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format: '{extension}'. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    if extension in (".txt", ".md"):
        return _load_text_file(file_path)
    elif extension == ".pdf":
        return _load_pdf_file(file_path)
    elif extension == ".docx":
        return _load_docx_file(file_path)

    return ""


# ──────────────────────────────────────────────
# Private Loaders
# ──────────────────────────────────────────────


def _load_text_file(file_path: Path) -> str:
    """Load a plain text or markdown file."""
    logger.debug("Loading text file: %s", file_path.name)
    return file_path.read_text(encoding="utf-8")


def _load_pdf_file(file_path: Path) -> str:
    """
    Load a PDF file.
    Requires PyPDF2 (install: pip install PyPDF2).
    """
    try:
        from PyPDF2 import PdfReader

        logger.debug("Loading PDF file: %s", file_path.name)
        reader = PdfReader(str(file_path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)

    except ImportError:
        logger.error(
            "PyPDF2 is not installed. Run: pip install PyPDF2"
        )
        raise ImportError(
            "PyPDF2 is required to load PDF files. "
            "Install it with: pip install PyPDF2"
        )


def _load_docx_file(file_path: Path) -> str:
    """
    Load a DOCX file.
    Requires python-docx (install: pip install python-docx).
    """
    try:
        from docx import Document

        logger.debug("Loading DOCX file: %s", file_path.name)
        doc = Document(str(file_path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)

    except ImportError:
        logger.error(
            "python-docx is not installed. Run: pip install python-docx"
        )
        raise ImportError(
            "python-docx is required to load DOCX files. "
            "Install it with: pip install python-docx"
        )
