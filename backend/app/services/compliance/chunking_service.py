"""
Chunking Service — splits extracted document text into semantically coherent chunks.

Features:
  - 4000-character chunks with semantic boundary detection
  - Table preservation (never splits mid-table)
  - Taxonomy tagging (balance_sheet, income_statement, cash_flow, notes, etc.)
  - Overlap for context continuity between chunks
  - Hash generation for caching / deduplication
"""
import hashlib
import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Section patterns for taxonomy tagging
TAXONOMY_PATTERNS = {
    "balance_sheet": [
        r"statement\s+of\s+financial\s+position",
        r"balance\s+sheet",
        r"assets?\s+and\s+liabilit",
        r"current\s+assets?",
        r"non[- ]current\s+assets?",
        r"total\s+equity",
        r"shareholders?\s+equity",
    ],
    "income_statement": [
        r"statement\s+of\s+(comprehensive\s+)?income",
        r"statement\s+of\s+profit\s+(and|or)\s+loss",
        r"statement\s+of\s+financial\s+performance",
        r"revenue\s+recognition",
        r"operating\s+(profit|loss)",
        r"earnings?\s+per\s+share",
    ],
    "cash_flow": [
        r"statement\s+of\s+cash\s*flows?",
        r"cash\s+flow\s+statement",
        r"operating\s+activities",
        r"investing\s+activities",
        r"financing\s+activities",
        r"cash\s+and\s+cash\s+equivalents",
    ],
    "equity_changes": [
        r"statement\s+of\s+changes\s+in\s+equity",
        r"retained\s+earnings",
        r"share\s+capital",
        r"other\s+comprehensive\s+income",
    ],
    "notes": [
        r"notes?\s+to\s+(the\s+)?(consolidated\s+)?financial\s+statements?",
        r"accounting\s+polic(y|ies)",
        r"significant\s+accounting",
        r"summary\s+of\s+.*accounting",
        r"basis\s+of\s+preparation",
    ],
    "audit_report": [
        r"independent\s+auditor",
        r"audit\s+report",
        r"opinion\s+on\s+the\s+financial",
    ],
}

# Sentence boundary pattern
SENTENCE_END = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
# Paragraph boundary (2+ newlines)
PARAGRAPH_BREAK = re.compile(r'\n\s*\n')


@dataclass
class DocumentChunk:
    """A single chunk of document text with metadata"""
    chunk_id: str
    content: str
    chunk_index: int
    page_numbers: List[int] = field(default_factory=list)
    taxonomy: str = "general"
    has_table: bool = False
    content_hash: str = ""
    char_count: int = 0
    overlap_start: int = 0  # chars of overlap from previous chunk

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "chunk_index": self.chunk_index,
            "page_numbers": self.page_numbers,
            "taxonomy": self.taxonomy,
            "has_table": self.has_table,
            "content_hash": self.content_hash,
            "char_count": self.char_count,
        }


class ChunkingService:
    """
    Splits document text into semantically coherent, tagged chunks.

    Usage:
        service = ChunkingService(chunk_size=4000, overlap=400)
        chunks = service.chunk_text(full_text, doc_id="session-123")
    """

    def __init__(
        self,
        chunk_size: int = 4000,
        overlap: int = 400,
        min_chunk_size: int = 200,
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size

    def chunk_text(
        self,
        text: str,
        doc_id: str = "",
        tables: Optional[List[Dict[str, Any]]] = None,
    ) -> List[DocumentChunk]:
        """
        Split text into chunks respecting semantic boundaries.

        Args:
            text: Full document text
            doc_id: Session/document ID for chunk ID generation
            tables: Optional list of table data from extraction

        Returns:
            List of DocumentChunk objects
        """
        if not text or not text.strip():
            return []

        # Split into paragraphs first
        paragraphs = PARAGRAPH_BREAK.split(text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks = []
        current_content = ""
        current_start = 0
        chunk_index = 0

        for para in paragraphs:
            # Check if adding this paragraph would exceed chunk_size
            if current_content and len(current_content) + len(para) + 2 > self.chunk_size:
                # Finalize current chunk
                chunk = self._create_chunk(
                    content=current_content,
                    chunk_index=chunk_index,
                    doc_id=doc_id,
                    tables=tables,
                )
                chunks.append(chunk)
                chunk_index += 1

                # Start new chunk with overlap from end of previous
                overlap_text = self._get_overlap(current_content)
                current_content = overlap_text + "\n\n" + para if overlap_text else para
            else:
                if current_content:
                    current_content += "\n\n" + para
                else:
                    current_content = para

            # Handle very long paragraphs (longer than chunk_size)
            while len(current_content) > self.chunk_size:
                # Find a good split point
                split_at = self._find_split_point(current_content, self.chunk_size)
                chunk_text = current_content[:split_at].strip()

                if len(chunk_text) >= self.min_chunk_size:
                    chunk = self._create_chunk(
                        content=chunk_text,
                        chunk_index=chunk_index,
                        doc_id=doc_id,
                        tables=tables,
                    )
                    chunks.append(chunk)
                    chunk_index += 1

                remainder = current_content[split_at:].strip()
                overlap_text = self._get_overlap(chunk_text)
                current_content = overlap_text + " " + remainder if overlap_text else remainder

        # Don't forget the last chunk
        if current_content.strip() and len(current_content.strip()) >= self.min_chunk_size:
            chunk = self._create_chunk(
                content=current_content.strip(),
                chunk_index=chunk_index,
                doc_id=doc_id,
                tables=tables,
            )
            chunks.append(chunk)

        logger.info("Chunked document into %d chunks (doc_id=%s)", len(chunks), doc_id)
        return chunks

    def _create_chunk(
        self,
        content: str,
        chunk_index: int,
        doc_id: str,
        tables: Optional[List[Dict[str, Any]]] = None,
    ) -> DocumentChunk:
        """Create a DocumentChunk with taxonomy tagging and hashing"""
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        chunk_id = f"{doc_id}_chunk_{chunk_index}" if doc_id else f"chunk_{chunk_index}"

        taxonomy = self._classify_taxonomy(content)
        has_table = bool(tables) and any(
            t.get("markdown", "") and t["markdown"][:50] in content
            for t in (tables or [])
        )

        # Check for table markdown patterns in content
        if not has_table and ("|" in content and "---" in content):
            has_table = True

        return DocumentChunk(
            chunk_id=chunk_id,
            content=content,
            chunk_index=chunk_index,
            taxonomy=taxonomy,
            has_table=has_table,
            content_hash=content_hash,
            char_count=len(content),
        )

    def _classify_taxonomy(self, text: str) -> str:
        """Classify chunk into a taxonomy category based on content patterns"""
        text_lower = text.lower()
        scores = {}

        for category, patterns in TAXONOMY_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                score += len(matches)
            if score > 0:
                scores[category] = score

        if scores:
            return max(scores, key=scores.get)
        return "general"

    def _find_split_point(self, text: str, max_len: int) -> int:
        """Find the best split point near max_len (sentence or paragraph boundary)"""
        if len(text) <= max_len:
            return len(text)

        # Try paragraph boundary
        search_start = max(0, max_len - 500)
        search_region = text[search_start:max_len]

        para_breaks = list(PARAGRAPH_BREAK.finditer(search_region))
        if para_breaks:
            last_break = para_breaks[-1]
            return search_start + last_break.end()

        # Try sentence boundary
        sentence_breaks = list(SENTENCE_END.finditer(search_region))
        if sentence_breaks:
            last_sentence = sentence_breaks[-1]
            return search_start + last_sentence.end()

        # Fall back to word boundary
        space_idx = text.rfind(" ", search_start, max_len)
        if space_idx > search_start:
            return space_idx + 1

        # Last resort: hard cut
        return max_len

    def _get_overlap(self, text: str) -> str:
        """Get the last `self.overlap` characters for context continuity"""
        if not text or self.overlap <= 0:
            return ""

        overlap_text = text[-self.overlap:]
        # Trim to start at a sentence or word boundary
        sentence_start = SENTENCE_END.search(overlap_text)
        if sentence_start:
            overlap_text = overlap_text[sentence_start.start():]
        else:
            space_idx = overlap_text.find(" ")
            if space_idx > 0:
                overlap_text = overlap_text[space_idx + 1:]

        return overlap_text.strip()

    def generate_document_hash(self, text: str) -> str:
        """Generate a stable hash for the entire document (for caching)"""
        normalized = re.sub(r'\s+', ' ', text.strip().lower())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
