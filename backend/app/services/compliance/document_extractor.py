"""
Document Extractor — Azure Document Intelligence wrapper for PDF/DOCX → structured text.

Uses Azure AI Document Intelligence (Form Recognizer) to extract:
  - Full text content with page/paragraph structure
  - Tables (preserved as markdown)
  - Key-value pairs
  - Document metadata

Can also work in "local" mode for plain text / simple extraction when
Azure is not configured.
"""
import logging
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ExtractedPage:
    """A single page of extracted content"""
    page_number: int
    content: str
    tables: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ExtractionResult:
    """Full extraction result from a document"""
    filename: str
    total_pages: int
    full_text: str
    pages: List[ExtractedPage] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    key_value_pairs: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentExtractor:
    """
    Extracts text from PDF/DOCX using Azure Document Intelligence.
    Falls back to basic text extraction if Azure is not configured.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self._endpoint = endpoint
        self._api_key = api_key
        self._client = None

        if endpoint and api_key:
            try:
                from azure.ai.documentintelligence import DocumentIntelligenceClient
                from azure.core.credentials import AzureKeyCredential

                self._client = DocumentIntelligenceClient(
                    endpoint=endpoint,
                    credential=AzureKeyCredential(api_key),
                )
                logger.info("Azure Document Intelligence client initialized")
            except Exception as e:
                logger.warning("Failed to initialize Azure Document Intelligence: %s", e)

    @classmethod
    def from_settings(cls, settings) -> "DocumentExtractor":
        """Create from app settings"""
        return cls(
            endpoint=settings.AZURE_DOC_INTELLIGENCE_ENDPOINT,
            api_key=settings.AZURE_DOC_INTELLIGENCE_KEY,
        )

    @classmethod
    def from_agent_config(cls, backend_config: dict) -> "DocumentExtractor":
        """Create from Agent.backend_config JSON"""
        doc_intel = backend_config.get("document_intelligence", {})
        return cls(
            endpoint=doc_intel.get("endpoint", ""),
            api_key=doc_intel.get("api_key", ""),
        )

    def extract(self, file_path: str) -> ExtractionResult:
        """
        Extract text from a document file.

        Args:
            file_path: Path to the PDF/DOCX file

        Returns:
            ExtractionResult with full text, pages, tables, metadata
        """
        filename = os.path.basename(file_path)

        if self._client:
            return self._extract_azure(file_path, filename)
        return self._extract_local(file_path, filename)

    def _extract_azure(self, file_path: str, filename: str) -> ExtractionResult:
        """Extract using Azure Document Intelligence"""
        from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        poller = self._client.begin_analyze_document(
            model_id="prebuilt-layout",
            body=AnalyzeDocumentRequest(bytes_source=file_bytes),
        )
        result = poller.result()

        pages = []
        tables = []
        full_text_parts = []

        # Extract pages
        for page in (result.pages or []):
            page_text_parts = []
            for line in (page.lines or []):
                page_text_parts.append(line.content)
            page_text = "\n".join(page_text_parts)
            pages.append(ExtractedPage(
                page_number=page.page_number,
                content=page_text,
            ))
            full_text_parts.append(page_text)

        # Extract tables as markdown
        for idx, table in enumerate(result.tables or []):
            table_data = {
                "index": idx,
                "row_count": table.row_count,
                "column_count": table.column_count,
                "cells": [],
            }
            md_rows = {}
            for cell in (table.cells or []):
                row_idx = cell.row_index
                col_idx = cell.column_index
                if row_idx not in md_rows:
                    md_rows[row_idx] = {}
                md_rows[row_idx][col_idx] = cell.content or ""
                table_data["cells"].append({
                    "row": row_idx,
                    "col": col_idx,
                    "content": cell.content or "",
                    "kind": getattr(cell, "kind", "content"),
                })

            # Convert to markdown table
            if md_rows:
                sorted_rows = sorted(md_rows.keys())
                col_count = table.column_count
                md_lines = []
                for r_idx, row_key in enumerate(sorted_rows):
                    row = md_rows[row_key]
                    cells_text = [row.get(c, "") for c in range(col_count)]
                    md_lines.append("| " + " | ".join(cells_text) + " |")
                    if r_idx == 0:
                        md_lines.append("| " + " | ".join(["---"] * col_count) + " |")
                table_data["markdown"] = "\n".join(md_lines)

            tables.append(table_data)

        # Extract key-value pairs
        kv_pairs = {}
        for kv in (result.key_value_pairs or []):
            if kv.key and kv.value:
                kv_pairs[kv.key.content] = kv.value.content

        full_text = "\n\n".join(full_text_parts)

        return ExtractionResult(
            filename=filename,
            total_pages=len(pages),
            full_text=full_text,
            pages=pages,
            tables=tables,
            key_value_pairs=kv_pairs,
            metadata={
                "extraction_method": "azure_document_intelligence",
                "model_id": "prebuilt-layout",
                "content_length": len(full_text),
            },
        )

    def _extract_local(self, file_path: str, filename: str) -> ExtractionResult:
        """
        Basic local text extraction fallback.
        Reads file as UTF-8 text (works for .txt, basic .csv).
        For PDF/DOCX without Azure, returns an error message guiding configuration.
        """
        ext = os.path.splitext(filename)[1].lower()

        if ext in (".txt", ".csv", ".md"):
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            return ExtractionResult(
                filename=filename,
                total_pages=1,
                full_text=text,
                pages=[ExtractedPage(page_number=1, content=text)],
                metadata={
                    "extraction_method": "local_text",
                    "content_length": len(text),
                },
            )

        # For PDF/DOCX without Azure — inform user
        msg = (
            f"Document '{filename}' requires Azure Document Intelligence for extraction. "
            f"Please configure AZURE_DOC_INTELLIGENCE_ENDPOINT and AZURE_DOC_INTELLIGENCE_KEY "
            f"in your environment, or provide Azure config in the agent's backend_config."
        )
        logger.warning(msg)
        return ExtractionResult(
            filename=filename,
            total_pages=0,
            full_text="",
            metadata={
                "extraction_method": "none",
                "error": msg,
            },
        )
