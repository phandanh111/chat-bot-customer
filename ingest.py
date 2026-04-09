import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.constants import LOG_DATE_FORMAT, LOG_FORMAT
from app.services.rag_service import RAGService

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into the RAG vector store.")
    parser.add_argument("--file", type=str, help="Path to a specific file to ingest.")
    parser.add_argument("--dir", type=str, default="data/documents", help="Directory to ingest (default: data/documents).")
    parser.add_argument("--clear", action="store_true", help="Clear the vector store before ingesting.")
    args = parser.parse_args()

    service = RAGService()

    if args.clear:
        service._vector_store.clear_collection()
        logger.info("Collection cleared.")

    if args.file:
        file_path = Path(args.file)
        n_chunks = service.ingest_file(file_path)
        logger.info("Done! Created %d chunks from '%s'.", n_chunks, file_path.name)
    else:
        dir_path = Path(args.dir)
        result = service.ingest_directory(dir_path)
        logger.info("Done! %s", result.message)
        for fname in result.files_processed:
            logger.info("   - %s", fname)

    info = service._vector_store.get_collection_info()
    logger.info("Collection: %s | Total documents: %d", info["collection_name"], info["total_documents"])


if __name__ == "__main__":
    main()
