"""
Search Service — Azure AI Search integration for compliance document chunks.

Features:
  - Index creation with semantic search scoring profiles
  - Chunk indexing with taxonomy and hash metadata
  - Semantic search retrieval filtered by document hash
  - Context routing (notes_only / financial_statements / full)
  - Works with both env-var config AND agent backend_config JSON
"""
import logging
import hashlib
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Stop words to filter from local search queries
STOP_WORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could", "of", "in", "to",
    "for", "with", "on", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "under",
    "and", "but", "or", "nor", "not", "so", "yet", "both", "either",
    "neither", "each", "every", "all", "any", "few", "more", "most",
    "other", "some", "such", "no", "only", "own", "same", "than", "too",
    "very", "just", "because", "if", "when", "where", "how", "what",
    "which", "who", "whom", "this", "that", "these", "those", "it", "its",
})

# Index field definitions
INDEX_FIELDS = [
    {"name": "id", "type": "Edm.String", "key": True, "filterable": True},
    {"name": "content", "type": "Edm.String", "searchable": True},
    {"name": "chunk_index", "type": "Edm.Int32", "filterable": True, "sortable": True},
    {"name": "document_hash", "type": "Edm.String", "filterable": True},
    {"name": "session_id", "type": "Edm.String", "filterable": True},
    {"name": "taxonomy", "type": "Edm.String", "filterable": True, "facetable": True},
    {"name": "has_table", "type": "Edm.Boolean", "filterable": True},
    {"name": "char_count", "type": "Edm.Int32", "sortable": True},
    {"name": "source_file", "type": "Edm.String", "filterable": True},
]


@dataclass
class SearchResult:
    """A single search result from Azure AI Search"""
    chunk_id: str
    content: str
    score: float
    taxonomy: str = "general"
    chunk_index: int = 0
    has_table: bool = False


class SearchService:
    """
    Azure AI Search integration for indexing and retrieving document chunks.

    Usage:
        service = SearchService.from_settings(settings)
        # or
        service = SearchService.from_agent_config(backend_config)

        # Index chunks
        service.index_chunks(chunks, session_id, document_hash)

        # Search
        results = service.search("revenue recognition policy", document_hash)
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        admin_key: Optional[str] = None,
        index_name: str = "compliance-chunks",
        semantic_config: str = "compliance-semantic",
    ):
        self._endpoint = endpoint
        self._admin_key = admin_key
        self._index_name = index_name
        self._semantic_config = semantic_config
        self._search_client = None
        self._index_client = None

        if endpoint and admin_key:
            try:
                from azure.search.documents import SearchClient
                from azure.search.documents.indexes import SearchIndexClient
                from azure.core.credentials import AzureKeyCredential

                credential = AzureKeyCredential(admin_key)
                self._search_client = SearchClient(
                    endpoint=endpoint,
                    index_name=index_name,
                    credential=credential,
                )
                self._index_client = SearchIndexClient(
                    endpoint=endpoint,
                    credential=credential,
                )
                logger.info("Azure AI Search client initialized (index=%s)", index_name)
            except Exception as e:
                logger.warning("Failed to initialize Azure AI Search: %s", e)

    @classmethod
    def from_settings(cls, settings) -> "SearchService":
        """Create from app settings"""
        return cls(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            admin_key=settings.AZURE_SEARCH_ADMIN_KEY,
            index_name=settings.AZURE_SEARCH_INDEX_NAME,
            semantic_config=getattr(settings, "AZURE_SEARCH_SEMANTIC_CONFIG", "compliance-semantic"),
        )

    @classmethod
    def from_agent_config(cls, backend_config: dict) -> "SearchService":
        """Create from Agent.backend_config JSON"""
        search_cfg = backend_config.get("search", {})
        return cls(
            endpoint=search_cfg.get("endpoint", ""),
            admin_key=search_cfg.get("admin_key", ""),
            index_name=search_cfg.get("index_name", "compliance-chunks"),
            semantic_config=search_cfg.get("semantic_config", "compliance-semantic"),
        )

    @property
    def is_available(self) -> bool:
        """Check if Azure Search is configured and available"""
        return self._search_client is not None

    def search_for_context_local(
        self,
        question: str,
        chunks: list,
        top: int = 5,
    ) -> list:
        """
        Fallback local search when Azure Search is not configured.
        Uses keyword matching with stop-word filtering and deduplication.
        """
        from app.services.compliance.chunking_service import DocumentChunk

        if not chunks:
            return []

        query_words = {
            w for w in question.lower().split()
            if w not in STOP_WORDS and len(w) > 2
        }
        if not query_words:
            query_words = set(question.lower().split())

        scored = []
        seen_content_hashes = set()
        for chunk in chunks:
            content = chunk.content if isinstance(chunk, DocumentChunk) else str(chunk)
            content_lower = content.lower()

            # Dedup by content hash
            content_hash = hashlib.md5(content_lower[:200].encode()).hexdigest()
            if content_hash in seen_content_hashes:
                continue
            seen_content_hashes.add(content_hash)

            score = sum(1 for w in query_words if w in content_lower)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, chunk in scored[:top]:
            results.append(SearchResult(
                chunk_id=chunk.chunk_id if isinstance(chunk, DocumentChunk) else "",
                content=chunk.content if isinstance(chunk, DocumentChunk) else str(chunk),
                score=float(score),
                taxonomy=chunk.taxonomy if isinstance(chunk, DocumentChunk) else "general",
                chunk_index=chunk.chunk_index if isinstance(chunk, DocumentChunk) else 0,
                has_table=chunk.has_table if isinstance(chunk, DocumentChunk) else False,
            ))
        return results

    def ensure_index(self) -> bool:
        """
        Create the search index if it doesn't exist.
        Returns True if index is ready.
        """
        if not self._index_client:
            logger.warning("Search index client not available — cannot ensure index")
            return False

        try:
            from azure.search.documents.indexes.models import (
                SearchIndex,
                SearchField,
                SearchFieldDataType,
                SemanticConfiguration,
                SemanticSettings,
                SemanticPrioritizedFields,
                SemanticField,
            )

            # Check if index already exists
            try:
                self._index_client.get_index(self._index_name)
                logger.info("Search index '%s' already exists", self._index_name)
                return True
            except Exception:
                pass

            # Build fields
            fields = [
                SearchField(
                    name="id",
                    type=SearchFieldDataType.String,
                    key=True,
                    filterable=True,
                ),
                SearchField(
                    name="content",
                    type=SearchFieldDataType.String,
                    searchable=True,
                ),
                SearchField(
                    name="chunk_index",
                    type=SearchFieldDataType.Int32,
                    filterable=True,
                    sortable=True,
                ),
                SearchField(
                    name="document_hash",
                    type=SearchFieldDataType.String,
                    filterable=True,
                ),
                SearchField(
                    name="session_id",
                    type=SearchFieldDataType.String,
                    filterable=True,
                ),
                SearchField(
                    name="taxonomy",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    facetable=True,
                ),
                SearchField(
                    name="has_table",
                    type=SearchFieldDataType.Boolean,
                    filterable=True,
                ),
                SearchField(
                    name="char_count",
                    type=SearchFieldDataType.Int32,
                    sortable=True,
                ),
                SearchField(
                    name="source_file",
                    type=SearchFieldDataType.String,
                    filterable=True,
                ),
            ]

            # Create with semantic configuration
            semantic_config = SemanticConfiguration(
                name="compliance-semantic",
                prioritized_fields=SemanticPrioritizedFields(
                    content_fields=[SemanticField(field_name="content")],
                ),
            )

            index = SearchIndex(
                name=self._index_name,
                fields=fields,
                semantic_settings=SemanticSettings(
                    configurations=[semantic_config],
                ),
            )

            self._index_client.create_index(index)
            logger.info("Created search index '%s'", self._index_name)
            return True

        except Exception as e:
            logger.error("Failed to ensure search index: %s", e)
            return False

    def index_chunks(
        self,
        chunks: List[Any],
        session_id: str,
        document_hash: str,
        source_file: str = "",
    ) -> int:
        """
        Index document chunks into Azure AI Search.

        Args:
            chunks: List of DocumentChunk objects
            session_id: Compliance session ID
            document_hash: Hash of the source document
            source_file: Source filename

        Returns:
            Number of chunks successfully indexed
        """
        if not self._search_client:
            logger.warning("Search client not available — skipping indexing")
            return 0

        documents = []
        for chunk in chunks:
            doc_id = f"{session_id}_{chunk.chunk_index}"
            documents.append({
                "id": doc_id,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "document_hash": document_hash,
                "session_id": session_id,
                "taxonomy": chunk.taxonomy,
                "has_table": chunk.has_table,
                "char_count": chunk.char_count,
                "source_file": source_file,
            })

        try:
            result = self._search_client.upload_documents(documents=documents)
            succeeded = sum(1 for r in result if r.succeeded)
            logger.info(
                "Indexed %d/%d chunks for session %s",
                succeeded, len(documents), session_id,
            )
            return succeeded
        except Exception as e:
            logger.error("Failed to index chunks: %s", e)
            return 0

    def search(
        self,
        query: str,
        document_hash: Optional[str] = None,
        session_id: Optional[str] = None,
        taxonomy_filter: Optional[List[str]] = None,
        top: int = 5,
    ) -> List[SearchResult]:
        """
        Search for relevant document chunks.

        Args:
            query: Search query text
            document_hash: Filter to specific document
            session_id: Filter to specific session
            taxonomy_filter: Filter to specific taxonomy categories
            top: Max results to return

        Returns:
            List of SearchResult objects sorted by relevance
        """
        if not self._search_client:
            logger.warning("Search client not available — returning empty results")
            return []

        # Build filter expression
        filters = []
        if document_hash:
            filters.append(f"document_hash eq '{document_hash}'")
        if session_id:
            filters.append(f"session_id eq '{session_id}'")
        if taxonomy_filter:
            tax_clauses = " or ".join(
                f"taxonomy eq '{t}'" for t in taxonomy_filter
            )
            filters.append(f"({tax_clauses})")

        filter_expr = " and ".join(filters) if filters else None

        try:
            # Use semantic search when config is available
            search_kwargs = {
                "search_text": query,
                "filter": filter_expr,
                "top": top,
                "include_total_count": True,
            }

            if self._semantic_config:
                try:
                    from azure.search.documents.models import QueryType
                    search_kwargs["query_type"] = QueryType.SEMANTIC
                    search_kwargs["semantic_configuration_name"] = self._semantic_config
                except (ImportError, Exception):
                    pass

            results = self._search_client.search(**search_kwargs)

            search_results = []
            seen_hashes = set()
            for result in results:
                # Dedup by content prefix
                content = result.get("content", "")
                content_hash = hashlib.md5(content[:200].encode()).hexdigest()
                if content_hash in seen_hashes:
                    continue
                seen_hashes.add(content_hash)

                search_results.append(SearchResult(
                    chunk_id=result["id"],
                    content=content,
                    score=result.get("@search.score", 0.0),
                    taxonomy=result.get("taxonomy", "general"),
                    chunk_index=result.get("chunk_index", 0),
                    has_table=result.get("has_table", False),
                ))

            return search_results

        except Exception as e:
            logger.error("Search failed: %s", e)
            return []

    def search_for_context(
        self,
        question: str,
        context_required: str,
        document_hash: Optional[str] = None,
        session_id: Optional[str] = None,
        top: int = 5,
    ) -> List[SearchResult]:
        """
        Search with context routing based on question's context_required field.

        Routes to appropriate taxonomy categories:
          - notes_only → notes
          - financial_statements → balance_sheet, income_statement, cash_flow, equity_changes
          - full → all categories
          - specific taxonomy → that taxonomy only
        """
        taxonomy_map = {
            "notes_only": ["notes"],
            "notes": ["notes"],
            "financial_statements": [
                "balance_sheet",
                "income_statement",
                "cash_flow",
                "equity_changes",
            ],
            "balance_sheet": ["balance_sheet"],
            "income_statement": ["income_statement"],
            "cash_flow": ["cash_flow"],
            "equity_changes": ["equity_changes"],
            "full": None,  # No filter — search everything
        }

        taxonomy_filter = taxonomy_map.get(context_required, None)

        return self.search(
            query=question,
            document_hash=document_hash,
            session_id=session_id,
            taxonomy_filter=taxonomy_filter,
            top=top,
        )

    def delete_session_chunks(self, session_id: str) -> int:
        """Delete all chunks for a session (cleanup)"""
        if not self._search_client:
            return 0

        try:
            # Search for all documents with this session_id
            results = self._search_client.search(
                search_text="*",
                filter=f"session_id eq '{session_id}'",
                select=["id"],
                top=10000,
            )

            docs_to_delete = [{"id": r["id"]} for r in results]
            if docs_to_delete:
                self._search_client.delete_documents(documents=docs_to_delete)
                logger.info("Deleted %d chunks for session %s", len(docs_to_delete), session_id)
                return len(docs_to_delete)
            return 0

        except Exception as e:
            logger.error("Failed to delete session chunks: %s", e)
            return 0
