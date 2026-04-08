"""
Markdown Header Chunking Service.
Uses MarkdownHeaderTextSplitter to split structured markdown documents
by headers, keeping each section as an independent semantic unit.

Includes chunk enrichment: converts structured bullet-list data into
natural language sentences for better embedding similarity matching.

Best for: structured documents with clear headings (e.g. lists, FAQs, entity catalogs).
"""

import hashlib
import logging
import re
from typing import Optional

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from app.config import get_settings
from app.models.schemas import DocumentChunk

logger = logging.getLogger(__name__)


class MarkdownChunkingService:
    """
    Service for splitting structured markdown documents by headers.

    Strategy:
        1. Split by markdown headers (##, ###, etc.) → each section = 1 chunk
        2. Enrich structured data (bullet lists) into natural language
        3. If any section exceeds chunk_size, apply RecursiveCharacterTextSplitter
           as a fallback to split it further.

    This ensures each entity (e.g. a club, a product, an FAQ item) stays
    in its own chunk and is not mixed with other entities.
    """

    # Headers to split on, ordered by level
    HEADERS_TO_SPLIT = [
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
    ]

    # Fallback separators for oversized sections
    FALLBACK_SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]

    # Pattern to detect structured bullet-list lines: "- Key: Value" or "-   Key: Value"
    _BULLET_PATTERN = re.compile(r"^-\s+(.+?):\s*(.*)$")

    def __init__(self) -> None:
        settings = get_settings()

        self._header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.HEADERS_TO_SPLIT,
            strip_headers=False,
        )

        # Fallback splitter for oversized chunks
        self._fallback_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.EXERCISE_EMBED_LIMIT,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=self.FALLBACK_SEPARATORS,
            length_function=len,
        )

        self._max_chunk_size = settings.EXERCISE_EMBED_LIMIT

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    def chunk_text(
        self,
        text: str,
        source: str = "unknown",
        extra_metadata: Optional[dict] = None,
    ) -> list[DocumentChunk]:
        """
        Split a markdown text into chunks by headers, then enrich
        structured data into natural language for better retrieval.

        Args:
            text: The markdown content to chunk.
            source: Source identifier (e.g., filename).
            extra_metadata: Additional metadata to attach.

        Returns:
            List of DocumentChunk objects, one per section.
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking, skipping.")
            return []

        # Step 1: Split by markdown headers
        header_docs = self._header_splitter.split_text(text)

        chunks: list[DocumentChunk] = []
        chunk_idx = 0

        for doc in header_docs:
            raw_content = doc.page_content
            header_metadata = doc.metadata  # e.g. {"h2": "Club 1"}

            # Step 2: Enrich structured content into natural language
            enriched_content = self._enrich_content(raw_content, header_metadata)

            # Step 3: If section is too long, split further
            if len(enriched_content) > self._max_chunk_size:
                sub_chunks = self._fallback_splitter.split_text(enriched_content)
                for sub_idx, sub_content in enumerate(sub_chunks):
                    metadata = self._build_metadata(
                        source=source,
                        chunk_index=chunk_idx,
                        total_chunks=-1,  # will be updated after
                        header_metadata=header_metadata,
                        extra_metadata=extra_metadata,
                        is_sub_chunk=True,
                        sub_chunk_index=sub_idx,
                        raw_content=raw_content,
                    )
                    chunk_id = self._generate_chunk_id(
                        source, chunk_idx, sub_content
                    )
                    chunks.append(
                        DocumentChunk(
                            content=sub_content,
                            metadata=metadata,
                            chunk_id=chunk_id,
                        )
                    )
                    chunk_idx += 1
            else:
                metadata = self._build_metadata(
                    source=source,
                    chunk_index=chunk_idx,
                    total_chunks=-1,
                    header_metadata=header_metadata,
                    extra_metadata=extra_metadata,
                    raw_content=raw_content,
                )
                chunk_id = self._generate_chunk_id(source, chunk_idx, enriched_content)
                chunks.append(
                    DocumentChunk(
                        content=enriched_content,
                        metadata=metadata,
                        chunk_id=chunk_id,
                    )
                )
                chunk_idx += 1

        # Update total_chunks in all metadata
        for chunk in chunks:
            chunk.metadata["total_chunks"] = len(chunks)

        logger.info(
            "Markdown-chunked '%s' into %d chunks (by headers, enriched, max_size=%d)",
            source,
            len(chunks),
            self._max_chunk_size,
        )
        return chunks

    # ──────────────────────────────────────────
    # Chunk Enrichment
    # ──────────────────────────────────────────

    def _enrich_content(self, content: str, header_metadata: dict) -> str:
        """
        Convert structured bullet-list content into natural language sentences.

        Example:
            Input:
                ## Club 12
                -   Tên club: The New Gym Quang Trung
                -   Địa chỉ: 185 Đ. Quang Trung, Gò Vấp, TP HCM
                -   Quận: Gò Vấp

            Output:
                Chi nhánh The New Gym Quang Trung.
                Tên club là The New Gym Quang Trung.
                Địa chỉ tại 185 Đ. Quang Trung, Gò Vấp, TP HCM.
                Thuộc quận Gò Vấp.
                Link: thenewgym.vn/gym/quang-trung.

        If the content is NOT structured (no bullet lists), return it as-is.
        """
        lines = content.strip().split("\n")
        fields: dict[str, str] = {}
        non_bullet_lines: list[str] = []
        has_bullets = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Skip markdown headers (they're in metadata already)
            if stripped.startswith("#"):
                continue

            match = self._BULLET_PATTERN.match(stripped)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                if value:  # Only store non-empty values
                    fields[key] = value
                has_bullets = True
            else:
                non_bullet_lines.append(stripped)

        # If no bullet-list structure detected, return original content
        if not has_bullets or not fields:
            return content

        # Build natural language sentences from structured fields
        sentences: list[str] = []

        # Extract common field names (case-insensitive matching)
        name = fields.get("Tên club") or fields.get("Tên") or fields.get("Tên sản phẩm", "")
        address = fields.get("Địa chỉ", "")
        district = fields.get("Quận", "")
        province = fields.get("Tỉnh (Thành phố)") or fields.get("Tỉnh", "")
        link = fields.get("Link", "")

        # Normalize district: "5" → "Quận 5", "Gò Vấp" → "quận Gò Vấp"
        district_label = ""
        if district:
            if district.isdigit():
                district_label = f"Quận {district}"
            else:
                district_label = f"quận {district}"

        # Build rich intro sentence with name + location
        if name:
            intro_parts = [f"Chi nhánh {name}"]
            if district_label:
                intro_parts.append(f"tại {district_label}")
            if province and province != district:
                intro_parts.append(f"thuộc {province}")
            sentences.append(", ".join(intro_parts) + ".")

        # Add synonyms and detailed info for stronger embedding match
        if name:
            sentences.append(f"Tên club là {name}.")
            sentences.append(f"Phòng gym {name}.")
        if address:
            sentences.append(f"Địa chỉ tại {address}.")
        if district_label:
            sentences.append(f"Thuộc {district_label}.")
            sentences.append(f"Cơ sở tại {district_label}.")
            sentences.append(f"Nằm ở khu vực {district_label}.")
            sentences.append(f"Phòng tập gym ở {district_label}.")
            # Add common query patterns for better retrieval
            if name:
                sentences.append(f"Tập gym ở {district_label} tại {name}.")
        if province:
            sentences.append(f"Tỉnh thành: {province}.")
        if link:
            sentences.append(f"Link: {link}.")

        # Add any remaining fields not covered above
        known_keys = {"Tên club", "Tên", "Tên sản phẩm", "Địa chỉ", "Quận",
                       "Tỉnh (Thành phố)", "Tỉnh", "Link"}
        for key, value in fields.items():
            if key not in known_keys:
                sentences.append(f"{key}: {value}.")

        # Add any non-bullet lines
        sentences.extend(non_bullet_lines)

        enriched = " ".join(sentences)
        logger.debug("Enriched chunk: %s", enriched[:150])
        return enriched

    # ──────────────────────────────────────────
    # Private Helpers
    # ──────────────────────────────────────────

    @staticmethod
    def _build_metadata(
        source: str,
        chunk_index: int,
        total_chunks: int,
        header_metadata: dict,
        extra_metadata: Optional[dict] = None,
        is_sub_chunk: bool = False,
        sub_chunk_index: int = 0,
        raw_content: str = "",
    ) -> dict:
        """Build metadata dict for a chunk."""
        metadata = {
            "source": source,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "chunking_strategy": "markdown_header",
        }
        # Flatten header metadata (e.g. h1, h2, h3)
        for key, value in header_metadata.items():
            metadata[f"header_{key}"] = value

        if is_sub_chunk:
            metadata["is_sub_chunk"] = True
            metadata["sub_chunk_index"] = sub_chunk_index

        if extra_metadata:
            metadata.update(extra_metadata)

        return metadata

    @staticmethod
    def _generate_chunk_id(source: str, index: int, content: str) -> str:
        """Generate a deterministic chunk ID."""
        hash_input = f"{source}:md:{index}:{content[:100]}"
        return hashlib.md5(hash_input.encode("utf-8")).hexdigest()
    