"""
Compliance API Endpoints — session management, file upload, decision tree access,
and the AI-powered analysis processing pipeline.

Provides the backend for the Compliance Analysis UI:
  - Session CRUD (create, list, get, update, delete)
  - File upload (financial statements + notes)
  - Decision tree browsing (standards list, detail, search)
  - Chat messages
  - Processing pipeline (extract, metadata, analyze, stream)
  - AI standard suggestions
"""
import json
import logging
import os
import re
import uuid
import shutil
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.schemas.compliance import (
    ComplianceSessionCreate,
    ComplianceSessionUpdate,
    ComplianceSessionResponse,
    ComplianceSessionListResponse,
    FileUploadResponse,
    StandardsSummary,
    ComplianceStandardDetail,
    AnalysisResponse,
    MetadataExtractionResponse,
    StandardSuggestionResponse,
    ChunkPreviewResponse,
    ChunkPreviewItem,
    ChunkRevalidateRequest,
    ChunkRevalidateResponse,
    FinancialValidationResponse,
    FinancialValidationResult,
    QuestionFilterRequest,
    QuestionFilterResponse,
    ChatConversationCreate,
    ChatConversationResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSendResponse,
    SavedResultResponse,
    AnalysisJobStatus,
    AnalysisProgressItem,
    HealthCheckResponse,
)
from app.services.compliance_service import (
    ComplianceSessionService,
    DecisionTreeService,
)

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "uploads",
    "compliance",
)


# ─── Session CRUD ──────────────────────────────────────────────────────────

@router.post("/sessions", response_model=ComplianceSessionResponse, status_code=201)
def create_session(
    payload: ComplianceSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new compliance analysis session"""
    session = ComplianceSessionService.create_session(
        db, payload.model_dump(), current_user.id
    )
    return session


@router.get("/sessions", response_model=list[ComplianceSessionListResponse])
def list_sessions(
    status: str = Query(None),
    framework: str = Query(None),
    mine_only: bool = Query(True, description="Only show current user's sessions"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List compliance sessions"""
    created_by = current_user.id if mine_only else None
    return ComplianceSessionService.list_sessions(
        db, created_by=created_by, status=status, framework=framework
    )


@router.get("/sessions/{session_id}", response_model=ComplianceSessionResponse)
def get_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a compliance session by ID"""
    session = ComplianceSessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/sessions/{session_id}", response_model=ComplianceSessionResponse)
def update_session(
    session_id: uuid.UUID,
    payload: ComplianceSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a compliance session"""
    session = ComplianceSessionService.update_session(
        db, session_id, payload.model_dump(exclude_unset=True)
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a compliance session"""
    if not ComplianceSessionService.delete_session(db, session_id):
        raise HTTPException(status_code=404, detail="Session not found")


# ─── File Upload ───────────────────────────────────────────────────────────

@router.post("/sessions/{session_id}/upload", response_model=FileUploadResponse)
async def upload_files(
    session_id: uuid.UUID,
    financial_statements: UploadFile = File(None),
    notes: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload financial statements and/or notes files"""
    session = ComplianceSessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Ensure upload directory
    session_dir = os.path.join(UPLOAD_DIR, str(session_id))
    os.makedirs(session_dir, exist_ok=True)

    fs_file = None
    fs_filename = None
    notes_file_path = None
    notes_filename = None

    if financial_statements:
        fs_filename = financial_statements.filename
        fs_file = os.path.join(session_dir, f"financial_statements_{fs_filename}")
        with open(fs_file, "wb") as f:
            shutil.copyfileobj(financial_statements.file, f)

    if notes:
        notes_filename = notes.filename
        notes_file_path = os.path.join(session_dir, f"notes_{notes_filename}")
        with open(notes_file_path, "wb") as f:
            shutil.copyfileobj(notes.file, f)

    updated = ComplianceSessionService.update_files(
        db,
        session_id,
        financial_statements_file=fs_file,
        financial_statements_filename=fs_filename,
        notes_file=notes_file_path,
        notes_filename=notes_filename,
    )

    return FileUploadResponse(
        session_id=session_id,
        financial_statements_uploaded=bool(
            updated.financial_statements_file
        ),
        notes_uploaded=bool(updated.notes_file),
        status=updated.status.value
        if hasattr(updated.status, "value")
        else str(updated.status),
        message="Files uploaded successfully"
        if updated.financial_statements_file and updated.notes_file
        else "Partial upload — both files required to proceed",
    )


# ─── Chat Messages ─────────────────────────────────────────────────────────

@router.post("/sessions/{session_id}/messages")
def add_message(
    session_id: uuid.UUID,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add a user message to the session chat"""
    content = body.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="Message content required")

    session = ComplianceSessionService.add_message(
        db, session_id, role="user", content=content
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"status": "ok", "message_count": len(session.messages or [])}


# ─── Decision Tree / Standards ─────────────────────────────────────────────

@router.get("/standards", response_model=StandardsSummary)
def list_standards(
    current_user: User = Depends(get_current_active_user),
):
    """List all available compliance standards with item counts"""
    return DecisionTreeService.get_summary()


@router.get("/standards/{section_key}")
def get_standard_detail(
    section_key: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get full details of a standard including all items and decision trees.
    section_key format: IAS_1, IFRS_9, IFRS_16, etc.
    """
    standard = DecisionTreeService.get_standard(section_key)
    if not standard:
        raise HTTPException(
            status_code=404,
            detail=f"Standard '{section_key}' not found. Use underscore format: IAS_1, IFRS_9",
        )
    return standard


@router.get("/standards-search")
def search_standards(
    q: str = Query(..., min_length=2, description="Search query"),
    current_user: User = Depends(get_current_active_user),
):
    """Search across all standards for matching compliance items"""
    results = DecisionTreeService.search_items(q)
    return {"query": q, "count": len(results), "results": results[:50]}


@router.post("/standards/reload")
def reload_standards(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Force reload of decision tree JSONs from disk"""
    DecisionTreeService.reload()
    summary = DecisionTreeService.get_summary()
    return {
        "status": "reloaded",
        "total_standards": summary["total_standards"],
        "total_questions": summary["total_questions"],
    }


# ─── Processing Pipeline ──────────────────────────────────────────────────

def _get_orchestrator(session, db):
    """
    Build a ComplianceOrchestrator for the given session.

    Priority:
      1. If session has agent_id → use agent's backend_config
      2. Else → use app settings (env vars)
    """
    from app.services.compliance.compliance_orchestrator import ComplianceOrchestrator

    if session.agent_id:
        from app.models.agent.agent import Agent
        agent = db.query(Agent).filter(Agent.id == session.agent_id).first()
        if agent and agent.backend_config:
            return ComplianceOrchestrator.from_agent_config(agent.backend_config)

    from app.core.config import settings
    return ComplianceOrchestrator.from_settings(settings)


@router.post(
    "/sessions/{session_id}/extract-metadata",
    response_model=MetadataExtractionResponse,
)
def extract_metadata(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Extract metadata from uploaded documents using AI.

    Extracts: company_name, reporting_period, currency, industry, auditor, etc.
    Requires documents to be uploaded first.
    """
    session = ComplianceSessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.financial_statements_file:
        raise HTTPException(
            status_code=400,
            detail="Financial statements must be uploaded before metadata extraction",
        )

    orchestrator = _get_orchestrator(session, db)

    # Extract text
    from app.services.compliance.document_extractor import DocumentExtractor
    extractor = orchestrator._extractor

    fs_result = extractor.extract(session.financial_statements_file)

    notes_text = ""
    if session.notes_file:
        notes_result = extractor.extract(session.notes_file)
        notes_text = notes_result.full_text

    combined = fs_result.full_text + "\n\n" + notes_text

    if not combined.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from uploaded documents. Check file format.",
        )

    # Extract metadata via AI
    metadata = orchestrator._engine.extract_metadata(combined)

    # Save to session
    ComplianceSessionService.update_session(
        db, session_id, {
            "extracted_metadata": metadata,
            "status": "metadata_review",
            "current_stage": 2,
        }
    )
    ComplianceSessionService.add_message(
        db, session_id, "system",
        f"Metadata extracted — Company: {metadata.get('company_name', 'Unknown')}, "
        f"Period: {metadata.get('reporting_period', 'Unknown')}.",
    )

    return MetadataExtractionResponse(
        session_id=session_id,
        metadata=metadata,
        status="metadata_review",
    )


@router.post(
    "/sessions/{session_id}/suggest-standards",
    response_model=StandardSuggestionResponse,
)
def suggest_standards(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    AI-powered standard suggestion — reads document and recommends applicable IFRS standards.

    Returns a list of standard section codes (e.g. ["IAS 1", "IFRS 9", "IFRS 15"]).
    """
    session = ComplianceSessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.financial_statements_file:
        raise HTTPException(
            status_code=400,
            detail="Documents must be uploaded before standard suggestion",
        )

    orchestrator = _get_orchestrator(session, db)

    # Extract text
    fs_result = orchestrator._extractor.extract(session.financial_statements_file)
    combined = fs_result.full_text

    # Get available standards
    all_standards = DecisionTreeService.list_standards()

    # AI suggestion
    suggested = orchestrator._engine.suggest_standards(combined, all_standards)

    return StandardSuggestionResponse(
        session_id=session_id,
        suggested_standards=suggested,
        total_suggested=len(suggested),
    )


@router.post(
    "/sessions/{session_id}/analyze",
    response_model=AnalysisResponse,
)
def analyze_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Run full compliance analysis on a session (synchronous).

    Requires:
      - Documents uploaded
      - Standards selected

    This runs the complete pipeline: extract → chunk → index → analyze → results.
    For real-time progress, use the /analyze-stream endpoint instead.
    """
    session = ComplianceSessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.financial_statements_file:
        raise HTTPException(
            status_code=400,
            detail="Documents must be uploaded before analysis",
        )
    if not session.selected_standards:
        raise HTTPException(
            status_code=400,
            detail="Standards must be selected before analysis",
        )

    orchestrator = _get_orchestrator(session, db)

    try:
        result = orchestrator.run(db, session_id)
        return AnalysisResponse(
            session_id=session_id,
            status=result["status"],
            compliance_score=result["compliance_score"],
            summary=result["summary"],
            total_results=result["total_results"],
            analysis_time_seconds=result["analysis_time_seconds"],
        )
    except Exception as e:
        logger.error("Analysis failed for session %s: %s", session_id, e)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/sessions/{session_id}/analyze-stream")
def analyze_session_stream(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Run compliance analysis with NDJSON streaming progress.

    Returns a streaming response where each line is a JSON object:
      {"type": "status", "data": {...}}
      {"type": "progress", "data": {"percentage": 45.2, ...}}
      {"type": "result", "data": {"question_id": "...", "status": "YES", ...}}
      {"type": "complete", "data": {"total": N, "compliant": N, ...}}
      {"type": "error", "data": {"message": "..."}}
    """
    session = ComplianceSessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.financial_statements_file:
        raise HTTPException(status_code=400, detail="Documents must be uploaded")
    if not session.selected_standards:
        raise HTTPException(status_code=400, detail="Standards must be selected")

    orchestrator = _get_orchestrator(session, db)

    def generate():
        for event in orchestrator.run_streaming(db, session_id):
            yield json.dumps(event) + "\n"

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.get("/sessions/{session_id}/results")
def get_results(
    session_id: uuid.UUID,
    standard: str = Query(None, description="Filter by standard (e.g. IAS_1)"),
    status: str = Query(None, description="Filter by status (YES/NO/N/A)"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(0, ge=0, le=500, description="Results per page (0 = all)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get analysis results for a session with optional filtering and pagination.

    Returns the full results array + summary, optionally filtered by standard or status.
    Pagination: ?page=1&page_size=50 (page_size=0 returns all).
    """
    session = ComplianceSessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    analysis = session.analysis_results
    if not analysis or "results" not in analysis:
        return {
            "session_id": str(session_id),
            "status": session.status.value if hasattr(session.status, "value") else str(session.status),
            "results": [],
            "total_filtered": 0,
            "total_results": 0,
            "page": 1,
            "page_size": 0,
            "total_pages": 0,
            "summary": None,
            "message": "Analysis not yet completed",
        }

    results = analysis["results"]

    # Apply filters
    if standard:
        std_normalized = standard.replace("_", " ")
        results = [
            r for r in results
            if r.get("standard", "").replace("_", " ") == std_normalized
            or r.get("standard", "") == standard
        ]

    if status:
        results = [r for r in results if r.get("status", "").upper() == status.upper()]

    total_filtered = len(results)

    # Pagination
    if page_size > 0:
        total_pages = (total_filtered + page_size - 1) // page_size
        start = (page - 1) * page_size
        results = results[start : start + page_size]
    else:
        total_pages = 1

    return {
        "session_id": str(session_id),
        "status": session.status.value if hasattr(session.status, "value") else str(session.status),
        "results": results,
        "total_filtered": total_filtered,
        "total_results": len(analysis["results"]),
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "summary": analysis.get("summary"),
        "compliance_score": session.compliance_score,
    }


@router.post("/sessions/{session_id}/re-analyze")
def re_analyze_questions(
    session_id: uuid.UUID,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Re-analyze specific questions with optional user instructions.

    Body:
      {
        "question_ids": ["q1", "q2"],
        "instructions": "Focus on Note 12 disclosures"
      }

    Overwrites results for specified questions only.
    """
    session = ComplianceSessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    question_ids = body.get("question_ids", [])
    if not question_ids:
        raise HTTPException(status_code=400, detail="question_ids required")

    analysis = session.analysis_results
    if not analysis or "results" not in analysis:
        raise HTTPException(
            status_code=400,
            detail="No existing analysis results to re-analyze from",
        )

    # Get the full questions for the requested IDs
    selected = session.selected_standards or []
    all_questions = DecisionTreeService.get_items_for_standards(selected)
    questions_to_reanalyze = [
        q for q in all_questions if q.get("id") in question_ids
    ]

    if not questions_to_reanalyze:
        raise HTTPException(
            status_code=404,
            detail=f"Questions not found: {question_ids}",
        )

    orchestrator = _get_orchestrator(session, db)
    document_hash = analysis.get("document_hash", "")

    # Re-analyze just these questions
    new_results = orchestrator._engine.analyze(
        questions_to_reanalyze, document_hash, str(session_id),
    )

    # Merge into existing results
    existing_results = analysis["results"]
    new_result_map = {r.to_dict()["question_id"]: r.to_dict() for r in new_results}
    new_result_map_orig = dict(new_result_map)  # Keep copy for ComplianceResult sync

    merged = []
    for r in existing_results:
        q_id = r.get("question_id", "")
        if q_id in new_result_map:
            merged.append(new_result_map[q_id])
            del new_result_map[q_id]
        else:
            merged.append(r)
    # Add any new results not in existing
    merged.extend(new_result_map.values())

    # Re-aggregate
    from app.services.compliance.analysis_engine import ComplianceAnalysisEngine, AnalysisResult, ComplianceStatus
    summary = ComplianceAnalysisEngine.aggregate_results([
        AnalysisResult(
            question_id=r.get("question_id", ""),
            standard=r.get("standard", ""),
            section=r.get("section", ""),
            reference=r.get("reference", ""),
            question=r.get("question", ""),
            status=ComplianceStatus(r.get("status", "N/A")) if r.get("status") in ("YES", "NO", "N/A") else ComplianceStatus.NOT_APPLICABLE,
            confidence=r.get("confidence", 0.0),
        )
        for r in merged
    ])

    analysis["results"] = merged
    analysis["summary"] = summary

    ComplianceSessionService.update_session(
        db, session_id, {
            "analysis_results": analysis,
            "compliance_score": summary["compliance_score"],
            "compliant_count": summary["compliant"],
            "non_compliant_count": summary["non_compliant"],
            "not_applicable_count": summary["not_applicable"],
        }
    )

    # Sync re-analyzed results to ComplianceResult table
    try:
        ComplianceSessionService.persist_results_to_db(
            db, session_id, [new_result_map_orig[q_id] for q_id in new_result_map_orig]
        )
    except Exception as persist_err:
        logger.warning("Failed to sync re-analyzed results to ComplianceResult: %s", persist_err)

    return {
        "session_id": str(session_id),
        "re_analyzed": len(new_results),
        "summary": summary,
        "compliance_score": summary["compliance_score"],
    }


@router.post("/sessions/{session_id}/override")
def override_result(
    session_id: uuid.UUID,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Manually override a compliance result status.

    Body:
      {
        "question_id": "IAS_1_q1",
        "new_status": "YES",
        "reason": "Confirmed compliant per management discussion"
      }
    """
    session = ComplianceSessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    question_id = body.get("question_id")
    new_status = body.get("new_status", "").upper()
    reason = body.get("reason", "")

    if not question_id:
        raise HTTPException(status_code=400, detail="question_id required")
    if new_status not in ("YES", "NO", "N/A"):
        raise HTTPException(status_code=400, detail="new_status must be YES, NO, or N/A")

    analysis = session.analysis_results
    if not analysis or "results" not in analysis:
        raise HTTPException(status_code=400, detail="No analysis results to override")

    # Find and update the result
    found = False
    for r in analysis["results"]:
        if r.get("question_id") == question_id:
            r["original_status"] = r.get("status")
            r["status"] = new_status
            r["override_reason"] = reason
            r["overridden_by"] = str(current_user.id)
            r["confidence"] = 1.0  # Manual override = full confidence
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail=f"Question {question_id} not found in results")

    # Re-aggregate
    compliant = sum(1 for r in analysis["results"] if r.get("status") == "YES")
    non_compliant = sum(1 for r in analysis["results"] if r.get("status") == "NO")
    na = sum(1 for r in analysis["results"] if r.get("status") == "N/A")
    assessed = compliant + non_compliant
    score = round((compliant / assessed) * 100) if assessed > 0 else 0

    if "summary" in analysis:
        analysis["summary"]["compliant"] = compliant
        analysis["summary"]["non_compliant"] = non_compliant
        analysis["summary"]["not_applicable"] = na
        analysis["summary"]["compliance_score"] = score

    ComplianceSessionService.update_session(
        db, session_id, {
            "analysis_results": analysis,
            "compliance_score": score,
            "compliant_count": compliant,
            "non_compliant_count": non_compliant,
            "not_applicable_count": na,
        }
    )

    ComplianceSessionService.add_message(
        db, session_id, "system",
        f"Result overridden: {question_id} → {new_status} by user. Reason: {reason}",
    )

    # Sync override to ComplianceResult table
    try:
        from app.models.compliance import ComplianceResult, ComplianceResultStatus
        from datetime import datetime as dt

        status_map = {
            "YES": ComplianceResultStatus.COMPLIANT,
            "NO": ComplianceResultStatus.NON_COMPLIANT,
            "N/A": ComplianceResultStatus.NOT_APPLICABLE,
        }
        cr = (
            db.query(ComplianceResult)
            .filter(
                ComplianceResult.session_id == session_id,
                ComplianceResult.question_id == question_id,
            )
            .first()
        )
        if cr:
            cr.is_overridden = True
            cr.override_status = status_map.get(new_status, ComplianceResultStatus.COMPLIANT)
            cr.override_reason = reason
            cr.overridden_by = current_user.id
            cr.overridden_at = dt.utcnow()
            cr.status = status_map.get(new_status, ComplianceResultStatus.COMPLIANT)
            cr.confidence = 1.0
            db.commit()
    except Exception as persist_err:
        logger.warning("Failed to sync override to ComplianceResult: %s", persist_err)

    return {
        "session_id": str(session_id),
        "question_id": question_id,
        "new_status": new_status,
        "compliance_score": score,
    }


# ─── Health Check ──────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthCheckResponse)
def compliance_health(
    current_user: User = Depends(get_current_active_user),
):
    """
    Health check for the compliance subsystem.
    Reports availability of Azure services and loaded decision trees.
    """
    from app.core.config import settings
    from app.services.compliance.search_service import SearchService
    from app.services.compliance.azure_openai_client import AzureOpenAIClient
    from app.services.compliance.document_extractor import DocumentExtractor

    openai_status = "configured" if settings.AZURE_OPENAI_ENDPOINTS else "not_configured"
    search_status = "configured" if settings.AZURE_SEARCH_ENDPOINT else "not_configured"
    doc_intel_status = "configured" if settings.AZURE_DOC_INTELLIGENCE_ENDPOINT else "not_configured"

    summary = DecisionTreeService.get_summary()

    return HealthCheckResponse(
        status="healthy",
        azure_openai=openai_status,
        azure_search=search_status,
        azure_doc_intelligence=doc_intel_status,
        decision_trees_loaded=summary["total_standards"],
        total_questions=summary["total_questions"],
    )


# ─── Chunk Management ─────────────────────────────────────────────────────

@router.get(
    "/sessions/{session_id}/chunks",
    response_model=ChunkPreviewResponse,
)
def get_chunk_preview(
    session_id: uuid.UUID,
    taxonomy: str = Query(None, description="Filter by taxonomy category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Preview document chunks for a session.
    Shows all indexed chunks with taxonomy classification and content preview.
    """
    session = ComplianceSessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    orchestrator = _get_orchestrator(session, db)
    sid = str(session_id)

    # Re-extract and chunk to get the chunk data
    chunks = _get_session_chunks(session, orchestrator, sid)

    if taxonomy:
        chunks = [c for c in chunks if c.taxonomy == taxonomy]

    # Build taxonomy summary
    taxonomy_summary = {}
    for c in chunks:
        taxonomy_summary[c.taxonomy] = taxonomy_summary.get(c.taxonomy, 0) + 1

    preview_items = [
        ChunkPreviewItem(
            chunk_id=c.chunk_id,
            chunk_index=c.chunk_index,
            content=c.content[:500],
            taxonomy=c.taxonomy,
            has_table=c.has_table,
            char_count=c.char_count,
        )
        for c in chunks
    ]

    return ChunkPreviewResponse(
        session_id=session_id,
        total_chunks=len(preview_items),
        chunks=preview_items,
        taxonomy_summary=taxonomy_summary,
    )


@router.post(
    "/sessions/{session_id}/chunks/revalidate",
    response_model=ChunkRevalidateResponse,
)
def revalidate_chunks(
    session_id: uuid.UUID,
    body: ChunkRevalidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Re-validate and optionally re-classify document chunks.
    Useful after taxonomy rules are updated.
    """
    session = ComplianceSessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    orchestrator = _get_orchestrator(session, db)
    sid = str(session_id)

    chunks = _get_session_chunks(session, orchestrator, sid)

    taxonomy_changes = 0
    target_chunks = chunks
    if body.chunk_ids:
        target_chunks = [c for c in chunks if c.chunk_id in body.chunk_ids]

    if body.reclassify:
        from app.services.compliance.chunking_service import ChunkingService
        chunking = ChunkingService()
        for chunk in target_chunks:
            old_taxonomy = chunk.taxonomy
            chunk.taxonomy = chunking._classify_taxonomy(chunk.content)
            if chunk.taxonomy != old_taxonomy:
                taxonomy_changes += 1

    # Re-index if search available
    if orchestrator._search.is_available and target_chunks:
        analysis = session.analysis_results or {}
        document_hash = analysis.get("document_hash", "")
        orchestrator._search.index_chunks(
            target_chunks, sid, document_hash,
            source_file=session.financial_statements_filename or "",
        )

    return ChunkRevalidateResponse(
        session_id=session_id,
        revalidated_count=len(target_chunks),
        taxonomy_changes=taxonomy_changes,
        status="revalidated",
    )


# ─── Financial Statement Validation ───────────────────────────────────────

@router.post(
    "/sessions/{session_id}/validate-financials",
    response_model=FinancialValidationResponse,
)
def validate_financial_statements(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Validate that uploaded documents contain expected financial statements.
    Checks for: Balance Sheet, Income Statement, Cash Flow, Equity Changes, Notes.
    """
    session = ComplianceSessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.financial_statements_file:
        raise HTTPException(
            status_code=400,
            detail="Financial statements must be uploaded before validation",
        )

    orchestrator = _get_orchestrator(session, db)
    sid = str(session_id)

    chunks = _get_session_chunks(session, orchestrator, sid)

    expected_statements = [
        "balance_sheet",
        "income_statement",
        "cash_flow",
        "equity_changes",
        "notes",
    ]

    display_names = {
        "balance_sheet": "Balance Sheet / Statement of Financial Position",
        "income_statement": "Income Statement / Statement of Profit or Loss",
        "cash_flow": "Statement of Cash Flows",
        "equity_changes": "Statement of Changes in Equity",
        "notes": "Notes to Financial Statements",
    }

    detected_taxonomies = set(c.taxonomy for c in chunks)
    detected = [s for s in expected_statements if s in detected_taxonomies]
    missing = [s for s in expected_statements if s not in detected_taxonomies]

    warnings = []
    if "general" in detected_taxonomies:
        general_count = sum(1 for c in chunks if c.taxonomy == "general")
        if general_count > len(chunks) * 0.3:
            warnings.append(
                f"{general_count} chunks classified as 'general' — "
                "document structure may be unconventional"
            )

    confidence = len(detected) / len(expected_statements) if expected_statements else 0.0

    validation = FinancialValidationResult(
        is_valid=len(missing) <= 1,
        detected_statements=[display_names.get(s, s) for s in detected],
        missing_statements=[display_names.get(s, s) for s in missing],
        warnings=warnings,
        confidence=round(confidence, 2),
    )

    return FinancialValidationResponse(
        session_id=session_id,
        validation=validation,
        status="validated",
    )


# ─── Question Filter ──────────────────────────────────────────────────────

@router.post(
    "/sessions/{session_id}/filter-questions",
    response_model=QuestionFilterResponse,
)
def filter_questions(
    session_id: uuid.UUID,
    body: QuestionFilterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Filter compliance questions with optional NLP instructions.

    Supports:
      - Standard selection (which standards to include)
      - Exclude specific question IDs
      - Natural language instructions (e.g. 'skip lease-related questions')
    """
    session = ComplianceSessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    all_questions = DecisionTreeService.get_items_for_standards(body.standards)
    total_before = len(all_questions)

    # Apply explicit exclusions
    if body.exclude_question_ids:
        all_questions = [
            q for q in all_questions
            if q.get("id") not in body.exclude_question_ids
        ]

    # Apply NLP instructions via AI
    applied_instructions = None
    if body.instructions and body.instructions.strip():
        applied_instructions = body.instructions
        orchestrator = _get_orchestrator(session, db)
        all_questions = _apply_nlp_filter(
            orchestrator._llm, all_questions, body.instructions,
        )

    from app.schemas.compliance import ComplianceItem
    filtered = [
        ComplianceItem(
            id=q.get("id", ""),
            section=q.get("section", ""),
            reference=q.get("reference", ""),
            question=q.get("question", ""),
            question_type=q.get("question_type"),
            source_question=q.get("source_question"),
            source_trigger=q.get("source_trigger"),
            context_required=q.get("context_required"),
            original_question=q.get("original_question"),
            decision_tree=q.get("decision_tree"),
        )
        for q in all_questions
    ]

    return QuestionFilterResponse(
        session_id=session_id,
        total_before=total_before,
        total_after=len(filtered),
        filtered_questions=filtered,
        applied_instructions=applied_instructions,
    )


# ─── Chatbot / Conversations ──────────────────────────────────────────────

@router.post(
    "/sessions/{session_id}/conversations",
    response_model=ChatConversationResponse,
    status_code=201,
)
def create_conversation(
    session_id: uuid.UUID,
    body: ChatConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new chat conversation within a compliance session."""
    session = ComplianceSessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    from app.models.compliance import ComplianceConversation
    conversation = ComplianceConversation(
        session_id=session_id,
        title=body.title or "New Conversation",
        context_question_id=body.context_question_id,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return ChatConversationResponse(
        id=conversation.id,
        session_id=conversation.session_id,
        title=conversation.title,
        context_question_id=conversation.context_question_id,
        is_active=conversation.is_active,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=0,
    )


@router.get(
    "/sessions/{session_id}/conversations",
    response_model=list[ChatConversationResponse],
)
def list_conversations(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all conversations for a compliance session."""
    session = ComplianceSessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    from app.models.compliance import ComplianceConversation, ComplianceMessage
    from sqlalchemy import func

    conversations = (
        db.query(ComplianceConversation)
        .filter(ComplianceConversation.session_id == session_id)
        .order_by(ComplianceConversation.created_at.desc())
        .all()
    )

    results = []
    for conv in conversations:
        msg_count = (
            db.query(func.count(ComplianceMessage.id))
            .filter(ComplianceMessage.conversation_id == conv.id)
            .scalar()
        )
        results.append(
            ChatConversationResponse(
                id=conv.id,
                session_id=conv.session_id,
                title=conv.title,
                context_question_id=conv.context_question_id,
                is_active=conv.is_active,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=msg_count or 0,
            )
        )

    return results


@router.get(
    "/sessions/{session_id}/conversations/{conversation_id}/messages",
    response_model=list[ChatMessageResponse],
)
def get_conversation_messages(
    session_id: uuid.UUID,
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all messages for a conversation."""
    from app.models.compliance import ComplianceConversation, ComplianceMessage

    conversation = (
        db.query(ComplianceConversation)
        .filter(
            ComplianceConversation.id == conversation_id,
            ComplianceConversation.session_id == session_id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = (
        db.query(ComplianceMessage)
        .filter(ComplianceMessage.conversation_id == conversation_id)
        .order_by(ComplianceMessage.created_at.asc())
        .all()
    )

    return [
        ChatMessageResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role.value if hasattr(m.role, "value") else str(m.role),
            content=m.content,
            citations=m.citations,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.post(
    "/sessions/{session_id}/conversations/{conversation_id}/send",
    response_model=ChatSendResponse,
)
def send_chat_message(
    session_id: uuid.UUID,
    conversation_id: uuid.UUID,
    body: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Send a chat message and get an AI response.
    The AI uses document context and analysis results to answer questions.
    """
    from app.models.compliance import (
        ComplianceConversation,
        ComplianceMessage,
        ChatMessageRole,
    )

    conversation = (
        db.query(ComplianceConversation)
        .filter(
            ComplianceConversation.id == conversation_id,
            ComplianceConversation.session_id == session_id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    session = ComplianceSessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save user message
    user_msg = ComplianceMessage(
        conversation_id=conversation_id,
        role=ChatMessageRole.USER,
        content=body.content,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Build AI context
    orchestrator = _get_orchestrator(session, db)
    sid = str(session_id)

    # Get conversation history
    history = (
        db.query(ComplianceMessage)
        .filter(ComplianceMessage.conversation_id == conversation_id)
        .order_by(ComplianceMessage.created_at.asc())
        .all()
    )

    # Build context from analysis results and document chunks
    analysis = session.analysis_results or {}
    results_context = ""
    if analysis.get("results"):
        # Include relevant results as context
        results_context = _build_results_context(
            analysis["results"],
            conversation.context_question_id,
        )

    # Search document chunks for relevant context
    document_context = ""
    doc_hash = analysis.get("document_hash", "")
    if doc_hash:
        search_results = orchestrator._search.search(
            query=body.content,
            document_hash=doc_hash,
            session_id=sid,
            top=3,
        ) if orchestrator._search.is_available else []

        if search_results:
            document_context = "\n\n---\n\n".join(r.content for r in search_results)

    # Build messages for AI
    system_prompt = (
        "You are a helpful compliance analysis assistant. "
        "Answer questions about the analyzed financial documents and compliance results. "
        "Reference specific evidence when possible. "
        "If you're unsure, say so rather than guessing.\n\n"
    )
    if results_context:
        system_prompt += f"Analysis Results Context:\n{results_context}\n\n"
    if document_context:
        system_prompt += f"Document Context:\n{document_context}\n\n"

    chat_messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
        if role in ("user", "assistant"):
            chat_messages.append({"role": role, "content": msg.content})

    # Get AI response
    try:
        response = orchestrator._llm.chat_completion(
            system_prompt=system_prompt,
            user_prompt=body.content,
        )
        ai_content = response.get("content", "I'm sorry, I couldn't generate a response.")
        citations = _extract_citations(ai_content, document_context)
    except Exception as e:
        logger.error("Chatbot AI call failed: %s", e)
        ai_content = f"I encountered an error processing your question: {str(e)}"
        citations = None

    # Save assistant message
    assistant_msg = ComplianceMessage(
        conversation_id=conversation_id,
        role=ChatMessageRole.ASSISTANT,
        content=ai_content,
        citations=citations,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return ChatSendResponse(
        user_message=ChatMessageResponse(
            id=user_msg.id,
            conversation_id=user_msg.conversation_id,
            role="user",
            content=user_msg.content,
            citations=None,
            created_at=user_msg.created_at,
        ),
        assistant_message=ChatMessageResponse(
            id=assistant_msg.id,
            conversation_id=assistant_msg.conversation_id,
            role="assistant",
            content=assistant_msg.content,
            citations=assistant_msg.citations,
            created_at=assistant_msg.created_at,
        ),
    )


# ─── Saved / Cached Results ───────────────────────────────────────────────

@router.get(
    "/sessions/{session_id}/saved-results",
    response_model=list[SavedResultResponse],
)
def get_saved_results(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get cached analysis results that match the current session's document.
    Useful for displaying previously computed results without re-running analysis.
    """
    session = ComplianceSessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    analysis = session.analysis_results or {}
    doc_hash = analysis.get("document_hash")
    if not doc_hash:
        return []

    from app.models.compliance import CachedAnalysisResult
    cached = (
        db.query(CachedAnalysisResult)
        .filter(CachedAnalysisResult.document_hash == doc_hash)
        .order_by(CachedAnalysisResult.last_accessed_at.desc())
        .all()
    )

    return [
        SavedResultResponse(
            id=c.id,
            document_hash=c.document_hash,
            framework=c.framework,
            questions_hash=c.questions_hash,
            results=c.results,
            metadata=c.metadata,
            access_count=c.access_count,
            last_accessed_at=c.last_accessed_at,
            created_at=c.created_at,
        )
        for c in cached
    ]


@router.post("/sessions/{session_id}/save-results")
def save_results_to_cache(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Cache current analysis results for future re-use.
    Creates a CachedAnalysisResult keyed by document_hash + framework + questions_hash.
    """
    import hashlib

    session = ComplianceSessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    analysis = session.analysis_results or {}
    if not analysis.get("results"):
        raise HTTPException(status_code=400, detail="No analysis results to save")

    doc_hash = analysis.get("document_hash", "")
    if not doc_hash:
        raise HTTPException(status_code=400, detail="No document hash available")

    # Build questions hash from selected standards
    selected = session.selected_standards or []
    questions_hash = hashlib.sha256(
        json.dumps(sorted(selected)).encode()
    ).hexdigest()

    from app.models.compliance import CachedAnalysisResult
    from datetime import datetime as dt

    existing = (
        db.query(CachedAnalysisResult)
        .filter(
            CachedAnalysisResult.document_hash == doc_hash,
            CachedAnalysisResult.framework == session.framework,
            CachedAnalysisResult.questions_hash == questions_hash,
        )
        .first()
    )

    if existing:
        existing.results = analysis
        existing.access_count += 1
        existing.last_accessed_at = dt.utcnow()
        existing.metadata = {
            "session_id": str(session_id),
            "client_name": session.client_name,
            "compliance_score": session.compliance_score,
        }
        db.commit()
        return {"status": "updated", "id": str(existing.id)}
    else:
        cached = CachedAnalysisResult(
            document_hash=doc_hash,
            framework=session.framework,
            questions_hash=questions_hash,
            results=analysis,
            metadata={
                "session_id": str(session_id),
                "client_name": session.client_name,
                "compliance_score": session.compliance_score,
            },
        )
        db.add(cached)
        db.commit()
        db.refresh(cached)
        return {"status": "created", "id": str(cached.id)}


# ─── Analysis Job Tracking ────────────────────────────────────────────────

@router.get(
    "/sessions/{session_id}/job-status",
    response_model=AnalysisJobStatus,
)
def get_job_status(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get per-question progress for the current/latest analysis job.
    Used for resume-from-failure and progress tracking.
    """
    from app.models.compliance import AnalysisProgress as AnalysisProgressModel

    progress_rows = (
        db.query(AnalysisProgressModel)
        .filter(AnalysisProgressModel.session_id == session_id)
        .order_by(AnalysisProgressModel.created_at.desc())
        .all()
    )

    if not progress_rows:
        return AnalysisJobStatus(
            job_id="none",
            session_id=session_id,
            total_questions=0,
            completed=0,
            failed=0,
            in_progress=0,
            pending=0,
            progress_percent=0.0,
        )

    job_id = progress_rows[0].job_id
    job_rows = [r for r in progress_rows if r.job_id == job_id]

    completed = sum(1 for r in job_rows if r.status.value == "completed")
    failed = sum(1 for r in job_rows if r.status.value == "failed")
    in_progress = sum(1 for r in job_rows if r.status.value == "in_progress")
    pending = sum(1 for r in job_rows if r.status.value == "pending")
    total = len(job_rows)

    items = [
        AnalysisProgressItem(
            question_id=r.question_id,
            status=r.status.value if hasattr(r.status, "value") else str(r.status),
            error=r.error,
            started_at=r.started_at,
            completed_at=r.completed_at,
        )
        for r in job_rows
    ]

    return AnalysisJobStatus(
        job_id=job_id,
        session_id=session_id,
        total_questions=total,
        completed=completed,
        failed=failed,
        in_progress=in_progress,
        pending=pending,
        progress_percent=round((completed / max(total, 1)) * 100, 1),
        items=items,
    )


# ─── Helper Functions ─────────────────────────────────────────────────────

def _get_session_chunks(session, orchestrator, sid: str):
    """
    Extract and chunk documents for a session.
    Reusable helper for chunk preview and validation endpoints.
    """
    from app.services.compliance.chunking_service import ChunkingService

    fs_text = ""
    notes_text = ""

    if session.financial_statements_file:
        fs_result = orchestrator._extractor.extract(session.financial_statements_file)
        fs_text = fs_result.full_text

    if session.notes_file:
        notes_result = orchestrator._extractor.extract(session.notes_file)
        notes_text = notes_result.full_text

    chunking = ChunkingService()
    fs_chunks = chunking.chunk_text(fs_text, doc_id=f"{sid}_fs") if fs_text else []
    notes_chunks = chunking.chunk_text(notes_text, doc_id=f"{sid}_notes") if notes_text else []

    return fs_chunks + notes_chunks


def _apply_nlp_filter(llm_client, questions, instructions: str):
    """
    Use AI to filter questions based on natural language instructions.
    Returns filtered list of question dicts.
    """
    question_summaries = "\n".join(
        f"- {q.get('id', '')}: {q.get('question', '')[:100]}"
        for q in questions[:200]
    )

    prompt = (
        f"Given these compliance questions:\n{question_summaries}\n\n"
        f"User instruction: {instructions}\n\n"
        f"Return a JSON object with an 'exclude_ids' array containing "
        f"the IDs of questions that should be EXCLUDED based on the instruction.\n"
        f'Example: {{"exclude_ids": ["IAS_1_q3", "IFRS_16_q7"]}}'
    )

    try:
        result = llm_client.chat_completion_json(
            system_prompt="You are a compliance question filter. Identify questions to exclude based on user instructions.",
            user_prompt=prompt,
            temperature=0.0,
            max_tokens=2048,
        )
        parsed = result.get("parsed", {})
        exclude_ids = set(parsed.get("exclude_ids", []))
        return [q for q in questions if q.get("id") not in exclude_ids]
    except Exception as e:
        logger.warning("NLP filter failed, returning all questions: %s", e)
        return questions


def _build_results_context(results: list, context_question_id: str = None) -> str:
    """Build a summary of analysis results for chatbot context."""
    if context_question_id:
        relevant = [r for r in results if r.get("question_id") == context_question_id]
        if relevant:
            r = relevant[0]
            return (
                f"Question: {r.get('question', '')}\n"
                f"Status: {r.get('status', '')}\n"
                f"Confidence: {r.get('confidence', 0)}\n"
                f"Explanation: {r.get('explanation', '')}\n"
                f"Evidence: {r.get('evidence', '')}\n"
            )

    # Build summary of all results
    compliant = sum(1 for r in results if r.get("status") == "YES")
    non_compliant = sum(1 for r in results if r.get("status") == "NO")
    na = sum(1 for r in results if r.get("status") == "N/A")

    summary = (
        f"Analysis Summary: {compliant} compliant, "
        f"{non_compliant} non-compliant, {na} N/A out of {len(results)} total.\n\n"
    )

    # Include non-compliant items for context
    non_compliant_items = [r for r in results if r.get("status") == "NO"][:5]
    if non_compliant_items:
        summary += "Key non-compliant items:\n"
        for r in non_compliant_items:
            summary += f"- {r.get('question_id', '')}: {r.get('explanation', '')[:150]}\n"

    return summary


def _extract_citations(ai_content: str, document_context: str) -> list:
    """Extract citation references from AI response."""
    if not document_context:
        return []

    citations = []
    # Simple citation detection — look for quoted text that matches context
    quoted_patterns = re.findall(r'"([^"]{20,})"', ai_content)
    for quote in quoted_patterns[:5]:
        if quote.lower() in document_context.lower():
            citations.append({
                "text": quote[:200],
                "source": "document",
            })

    return citations if citations else []
