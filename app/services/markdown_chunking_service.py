import hashlib
import logging
import re
from typing import Optional

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from app.config import get_settings
from app.constants import MARKDOWN_KNOWN_FIELDS
from app.models.schemas import DocumentChunk

logger = logging.getLogger(__name__)

HEADERS_TO_SPLIT = [("#", "h1"), ("##", "h2"), ("###", "h3")]
FALLBACK_SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]
_BULLET_PATTERN = re.compile(r"^-\s+(.+?):\s*(.*)$")


class MarkdownChunkingService:
    def __init__(self) -> None:
        settings = get_settings()
        self._header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=HEADERS_TO_SPLIT, strip_headers=False
        )
        self._fallback_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.EXERCISE_EMBED_LIMIT,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=FALLBACK_SEPARATORS,
            length_function=len,
        )
        self._max_chunk_size = settings.EXERCISE_EMBED_LIMIT

    def chunk_text(self, text: str, source: str = "unknown", extra_metadata: Optional[dict] = None) -> list[DocumentChunk]:
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking, skipping.")
            return []

        header_docs = self._header_splitter.split_text(text)
        chunks: list[DocumentChunk] = []
        chunk_idx = 0

        for doc in header_docs:
            raw_content = doc.page_content
            header_metadata = doc.metadata
            enriched_content = self._enrich_content(raw_content, header_metadata)

            if len(enriched_content) > self._max_chunk_size:
                for sub_idx, sub_content in enumerate(self._fallback_splitter.split_text(enriched_content)):
                    metadata = self._build_metadata(source, chunk_idx, -1, header_metadata, extra_metadata, True, sub_idx, raw_content)
                    chunks.append(DocumentChunk(
                        content=sub_content,
                        metadata=metadata,
                        chunk_id=self._generate_chunk_id(source, chunk_idx, sub_content),
                    ))
                    chunk_idx += 1
            else:
                metadata = self._build_metadata(source, chunk_idx, -1, header_metadata, extra_metadata, raw_content=raw_content)
                chunks.append(DocumentChunk(
                    content=enriched_content,
                    metadata=metadata,
                    chunk_id=self._generate_chunk_id(source, chunk_idx, enriched_content),
                ))
                chunk_idx += 1

        for chunk in chunks:
            chunk.metadata["total_chunks"] = len(chunks)

        logger.info("Markdown-chunked '%s' into %d chunks (max_size=%d)", source, len(chunks), self._max_chunk_size)
        return chunks

    def _enrich_content(self, content: str, header_metadata: dict) -> str:
        lines = content.strip().split("\n")
        fields: dict[str, str] = {}
        non_bullet_lines: list[str] = []
        has_bullets = False

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = _BULLET_PATTERN.match(stripped)
            if match:
                key, value = match.group(1).strip(), match.group(2).strip()
                if value:
                    fields[key] = value
                has_bullets = True
            else:
                non_bullet_lines.append(stripped)

        if not has_bullets or not fields:
            return content

        sentences: list[str] = []
        name = fields.get("Tên club") or fields.get("Tên") or fields.get("Tên sản phẩm", "")
        address = fields.get("Địa chỉ", "")
        district = fields.get("Quận", "")
        province = fields.get("Tỉnh (Thành phố)") or fields.get("Tỉnh", "")
        link = fields.get("Link", "")

        district_label = ""
        if district:
            district_label = f"Quận {district}" if district.isdigit() else f"quận {district}"

        if name:
            intro_parts = [f"Chi nhánh {name}"]
            if district_label:
                intro_parts.append(f"tại {district_label}")
            if province and province != district:
                intro_parts.append(f"thuộc {province}")
            sentences.append(", ".join(intro_parts) + ".")

        if name:
            sentences.append(f"Tên club là {name}.")
            sentences.append(f"Phòng gym {name}.")
        if address:
            sentences.append(f"Địa chỉ tại {address}.")
        if district_label:
            sentences.extend([
                f"Thuộc {district_label}.",
                f"Cơ sở tại {district_label}.",
                f"Nằm ở khu vực {district_label}.",
                f"Phòng tập gym ở {district_label}.",
            ])
            if name:
                sentences.append(f"Tập gym ở {district_label} tại {name}.")
        if province:
            sentences.append(f"Tỉnh thành: {province}.")
        if link:
            sentences.append(f"Link: {link}.")

        for key, value in fields.items():
            if key not in MARKDOWN_KNOWN_FIELDS:
                sentences.append(f"{key}: {value}.")

        sentences.extend(non_bullet_lines)
        return " ".join(sentences)

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
        metadata = {
            "source": source,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "chunking_strategy": "markdown_header",
        }
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
        return hashlib.md5(f"{source}:md:{index}:{content[:100]}".encode("utf-8")).hexdigest()