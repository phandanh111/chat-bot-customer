"""
Document Ingestion CLI Script.

Usage:
    python ingest.py                        # Ingest all files in data/documents/
    python ingest.py --file path/to/doc.txt # Ingest a specific file
    python ingest.py --clear                # Clear collection before ingesting
"""

import argparse
import logging
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.rag_service import RAGService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Ingest documents into the RAG vector store."
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to a specific file to ingest.",
    )
    parser.add_argument(
        "--dir",
        type=str,
        default="data/documents",
        help="Directory containing documents to ingest (default: data/documents).",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear the vector store before ingesting.",
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("RAG Document Ingestion")
    logger.info("=" * 60)

    service = RAGService()

    # Clear collection if requested
    if args.clear:
        logger.info("Clearing vector store collection...")
        service._vector_store.clear_collection()
        logger.info("Collection cleared.")

    # Ingest specific file or directory
    if args.file:
        file_path = Path(args.file)
        logger.info("Ingesting file: %s", file_path)
        n_chunks = service.ingest_file(file_path)
        logger.info("✅ Done! Created %d chunks from '%s'.", n_chunks, file_path.name)
    else:
        dir_path = Path(args.dir)
        logger.info("Ingesting directory: %s", dir_path)
        result = service.ingest_directory(dir_path)
        logger.info("✅ Done! %s", result.message)
        for fname in result.files_processed:
            logger.info("   - %s", fname)

    # Show collection info
    info = service._vector_store.get_collection_info()
    logger.info("-" * 40)
    logger.info("Collection: %s", info["collection_name"])
    logger.info("Total documents: %d", info["total_documents"])
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
