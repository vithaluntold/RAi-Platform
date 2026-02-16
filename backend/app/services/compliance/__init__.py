"""
Compliance Analysis Agent — services package.

Modules:
  azure_openai_client    — Multi-endpoint round-robin Azure OpenAI wrapper
  document_extractor     — Azure Document Intelligence PDF/DOCX extraction
  chunking_service       — Semantic boundary chunking + taxonomy tagging
  search_service         — Azure AI Search indexing + retrieval
  analysis_engine        — Core compliance analysis (two-phase, batching, validation)
  compliance_orchestrator — Ties everything together, called by AgentExecution
"""
