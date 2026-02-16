"""
Compliance Orchestrator — ties all compliance services together.

This is the entry point called by the AgentExecution framework when
a COMPLIANCE_ANALYSIS agent is triggered. It coordinates:

  1. Document extraction (Azure Document Intelligence)
  2. Chunking (semantic boundary splitting)
  3. Indexing (Azure AI Search)
  4. Metadata extraction (AI-powered)
  5. Compliance analysis (two-phase, batched, validated)
  6. Result persistence (back to ComplianceSession)

Architecture:
  AgentExecution trigger
    → ComplianceOrchestrator.run(session_id, agent_config)
      → DocumentExtractor.extract(files)
      → ChunkingService.chunk_text(text)
      → SearchService.index_chunks(chunks)
      → AnalysisEngine.extract_metadata(text)
      → AnalysisEngine.analyze(questions, hash, session_id)
      → ComplianceSessionService.update_session(results)
"""
import hashlib
import logging
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Generator
from sqlalchemy.orm import Session

from app.models.compliance import (
    ComplianceSession,
    ComplianceSessionStatus,
    AnalysisProgress as AnalysisProgressModel,
    AnalysisProgressStatus,
    CachedAnalysisResult,
)
from app.services.compliance_service import ComplianceSessionService, DecisionTreeService
from app.services.compliance.azure_openai_client import AzureOpenAIClient
from app.services.compliance.document_extractor import DocumentExtractor
from app.services.compliance.chunking_service import ChunkingService
from app.services.compliance.search_service import SearchService
from app.services.compliance.analysis_engine import ComplianceAnalysisEngine

logger = logging.getLogger(__name__)


class ComplianceOrchestrator:
    """
    High-level orchestrator for the full compliance analysis pipeline.

    Can be constructed from:
      - App settings (env vars)
      - Agent backend_config (JSON from Agent model)
    """

    def __init__(
        self,
        llm_client: AzureOpenAIClient,
        doc_extractor: DocumentExtractor,
        chunking_service: ChunkingService,
        search_service: SearchService,
        analysis_engine: ComplianceAnalysisEngine,
    ):
        self._llm = llm_client
        self._extractor = doc_extractor
        self._chunking = chunking_service
        self._search = search_service
        self._engine = analysis_engine

    @classmethod
    def from_settings(cls, settings) -> "ComplianceOrchestrator":
        """Build orchestrator from app settings (env vars)"""
        llm = AzureOpenAIClient.from_settings(settings)
        extractor = DocumentExtractor.from_settings(settings)
        chunking = ChunkingService()
        search = SearchService.from_settings(settings)
        engine = ComplianceAnalysisEngine(llm, search)

        return cls(llm, extractor, chunking, search, engine)

    @classmethod
    def from_agent_config(cls, backend_config: dict) -> "ComplianceOrchestrator":
        """Build orchestrator from Agent.backend_config JSON"""
        llm = AzureOpenAIClient.from_agent_config(backend_config)
        extractor = DocumentExtractor.from_agent_config(backend_config)
        chunking = ChunkingService()
        search = SearchService.from_agent_config(backend_config)
        engine = ComplianceAnalysisEngine(llm, search)

        return cls(llm, extractor, chunking, search, engine)

    # ─── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _compute_questions_hash(question_ids: List[str]) -> str:
        """Deterministic hash of the selected question IDs for cache keying."""
        key = "|".join(sorted(question_ids))
        return hashlib.sha256(key.encode()).hexdigest()

    @staticmethod
    def _lookup_cache(
        db: Session, document_hash: str, framework: str, questions_hash: str
    ) -> Optional[CachedAnalysisResult]:
        """Return cached results if the exact combo was analyzed before."""
        row = (
            db.query(CachedAnalysisResult)
            .filter_by(
                document_hash=document_hash,
                framework=framework,
                questions_hash=questions_hash,
            )
            .first()
        )
        if row:
            row.access_count += 1
            row.last_accessed_at = datetime.utcnow()
            db.commit()
        return row

    @staticmethod
    def _save_cache(
        db: Session,
        document_hash: str,
        framework: str,
        questions_hash: str,
        results: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Upsert analysis results into the cache table."""
        existing = (
            db.query(CachedAnalysisResult)
            .filter_by(
                document_hash=document_hash,
                framework=framework,
                questions_hash=questions_hash,
            )
            .first()
        )
        if existing:
            existing.results = results
            existing.result_metadata = metadata
            existing.access_count += 1
            existing.last_accessed_at = datetime.utcnow()
        else:
            db.add(CachedAnalysisResult(
                document_hash=document_hash,
                framework=framework,
                questions_hash=questions_hash,
                results=results,
                result_metadata=metadata,
            ))
        db.commit()

    @staticmethod
    def _init_progress_rows(
        db: Session, job_id: str, session_id: uuid.UUID, question_ids: List[str]
    ) -> None:
        """Create pending progress rows for every question in the job."""
        for qid in question_ids:
            existing = (
                db.query(AnalysisProgressModel)
                .filter_by(job_id=job_id, question_id=qid)
                .first()
            )
            if not existing:
                db.add(AnalysisProgressModel(
                    job_id=job_id,
                    session_id=session_id,
                    question_id=qid,
                    status=AnalysisProgressStatus.PENDING,
                ))
        db.commit()

    @staticmethod
    def _mark_progress(
        db: Session,
        job_id: str,
        question_id: str,
        status: AnalysisProgressStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update a single question's progress row."""
        row = (
            db.query(AnalysisProgressModel)
            .filter_by(job_id=job_id, question_id=question_id)
            .first()
        )
        if row:
            row.status = status
            row.result = result
            row.error = error
            if status == AnalysisProgressStatus.IN_PROGRESS and not row.started_at:
                row.started_at = datetime.utcnow()
            if status in (AnalysisProgressStatus.COMPLETED, AnalysisProgressStatus.FAILED):
                row.completed_at = datetime.utcnow()
            db.commit()

    @staticmethod
    def _get_completed_question_ids(db: Session, job_id: str) -> set:
        """Return question IDs that are already completed for this job."""
        rows = (
            db.query(AnalysisProgressModel.question_id)
            .filter_by(job_id=job_id, status=AnalysisProgressStatus.COMPLETED)
            .all()
        )
        return {r[0] for r in rows}

    def run(
        self,
        db: Session,
        session_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Run the full compliance analysis pipeline for a session.

        Steps:
          1. Load session from DB
          2. Extract text from uploaded documents
          3. Chunk the text
          4. Index chunks in Azure Search
          5. Extract metadata via AI
          6. Load selected standards & questions
          7. Run compliance analysis
          8. Aggregate results and save to session

        Returns:
            Dict with analysis summary and results
        """
        start_time = time.time()

        # 1. Load session
        session = ComplianceSessionService.get_session(db, session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Update status to ANALYZING
        ComplianceSessionService.update_session(
            db, session_id, {"status": "analyzing", "current_stage": 6}
        )

        try:
            return self._execute_pipeline(db, session, start_time)
        except Exception as e:
            logger.error("Compliance analysis failed for session %s: %s", session_id, e)
            ComplianceSessionService.update_session(
                db, session_id, {"status": "failed"}
            )
            ComplianceSessionService.add_message(
                db, session_id, "system",
                f"Analysis failed: {str(e)}. Please try again or contact support."
            )
            raise

    def _execute_pipeline(
        self,
        db: Session,
        session: ComplianceSession,
        start_time: float,
    ) -> Dict[str, Any]:
        """Execute the analysis pipeline steps"""
        session_id = session.id
        sid = str(session_id)

        # 2. Extract text from uploaded documents
        logger.info("Step 2: Extracting text from documents (session=%s)", sid)
        fs_text = ""
        notes_text = ""

        if session.financial_statements_file:
            fs_result = self._extractor.extract(session.financial_statements_file)
            fs_text = fs_result.full_text
            logger.info(
                "Extracted %d chars from financial statements (%d pages)",
                len(fs_text), fs_result.total_pages,
            )

        if session.notes_file:
            notes_result = self._extractor.extract(session.notes_file)
            notes_text = notes_result.full_text
            logger.info(
                "Extracted %d chars from notes (%d pages)",
                len(notes_text), notes_result.total_pages,
            )

        combined_text = fs_text + "\n\n" + notes_text
        if not combined_text.strip():
            raise ValueError("No text could be extracted from uploaded documents")

        # 3. Chunk the text
        logger.info("Step 3: Chunking text (session=%s)", sid)
        document_hash = self._chunking.generate_document_hash(combined_text)

        fs_chunks = self._chunking.chunk_text(fs_text, doc_id=f"{sid}_fs") if fs_text else []
        notes_chunks = self._chunking.chunk_text(notes_text, doc_id=f"{sid}_notes") if notes_text else []

        total_chunks = len(fs_chunks) + len(notes_chunks)
        logger.info("Created %d chunks (%d from FS, %d from notes)", total_chunks, len(fs_chunks), len(notes_chunks))

        # 4. Index chunks in Azure Search
        logger.info("Step 4: Indexing chunks (session=%s)", sid)
        all_chunks = fs_chunks + notes_chunks
        if self._search.is_available:
            self._search.ensure_index()
            indexed_fs = self._search.index_chunks(
                fs_chunks, sid, document_hash,
                source_file=session.financial_statements_filename or "",
            )
            indexed_notes = self._search.index_chunks(
                notes_chunks, sid, document_hash,
                source_file=session.notes_filename or "",
            )
            logger.info("Indexed %d chunks total", indexed_fs + indexed_notes)
        else:
            logger.warning("Azure Search not available — using local chunk matching fallback")
            self._engine.set_local_chunks(all_chunks)

        # 5. Extract metadata via AI
        logger.info("Step 5: Extracting metadata (session=%s)", sid)
        metadata = self._engine.extract_metadata(combined_text)
        ComplianceSessionService.update_session(
            db, session_id, {
                "extracted_metadata": metadata,
                "status": "analyzing",
            }
        )
        ComplianceSessionService.add_message(
            db, session_id, "system",
            f"Documents processed: {total_chunks} chunks indexed. "
            f"Company: {metadata.get('company_name', 'Unknown')}. "
            f"Starting compliance analysis..."
        )

        # 6. Load selected standards & questions
        logger.info("Step 6: Loading standards and questions (session=%s)", sid)
        selected = session.selected_standards or []
        if not selected:
            raise ValueError("No standards selected for analysis")

        questions = DecisionTreeService.get_items_for_standards(selected)
        if not questions:
            raise ValueError(f"No questions found for selected standards: {selected}")

        logger.info("Loaded %d questions from %d standards", len(questions), len(selected))

        question_ids = [q.get("id", "") for q in questions]
        questions_hash = self._compute_questions_hash(question_ids)

        # ── Cache lookup ──
        cached = self._lookup_cache(db, document_hash, session.framework or "IFRS", questions_hash)
        if cached:
            logger.info("Cache hit for session %s — returning cached results", sid)
            cached_results = cached.results
            if isinstance(cached_results, dict):
                result_list = cached_results.get("results", [])
                summary = cached_results.get("summary", {})
            else:
                result_list = cached_results if isinstance(cached_results, list) else []
                summary = {}

            elapsed = round(time.time() - start_time, 1)
            compliant = summary.get("compliant", sum(1 for r in result_list if r.get("status") == "YES"))
            non_compliant = summary.get("non_compliant", sum(1 for r in result_list if r.get("status") == "NO"))
            na = summary.get("not_applicable", sum(1 for r in result_list if r.get("status") == "N/A"))
            score = round(compliant / max(compliant + non_compliant, 1) * 100)

            ComplianceSessionService.update_session(
                db, session_id, {
                    "status": "completed",
                    "current_stage": 7,
                    "analysis_results": cached_results if isinstance(cached_results, dict) else {"results": result_list},
                    "compliance_score": score,
                    "compliant_count": compliant,
                    "non_compliant_count": non_compliant,
                    "not_applicable_count": na,
                }
            )

            return {
                "session_id": sid,
                "status": "completed",
                "compliance_score": score,
                "summary": summary,
                "total_results": len(result_list),
                "analysis_time_seconds": elapsed,
                "cache_hit": True,
            }

        # ── Initialize progress rows ──
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        self._init_progress_rows(db, job_id, session_id, question_ids)

        # 7. Run compliance analysis
        logger.info("Step 7: Running compliance analysis (session=%s)", sid)
        results = self._engine.analyze(questions, document_hash, sid)

        # Mark all progress rows as completed
        for r in results:
            q_id = r.question_id if hasattr(r, "question_id") else r.get("question_id", "")
            err = r.error if hasattr(r, "error") else r.get("error")
            prog_status = AnalysisProgressStatus.COMPLETED if not err else AnalysisProgressStatus.FAILED
            self._mark_progress(db, job_id, q_id, prog_status, result=r.to_dict() if hasattr(r, "to_dict") else r, error=err)

        # 8. Aggregate and save
        logger.info("Step 8: Aggregating results (session=%s)", sid)
        summary = ComplianceAnalysisEngine.aggregate_results(results)

        elapsed = round(time.time() - start_time, 1)

        analysis_results = {
            "summary": summary,
            "results": [r.to_dict() for r in results],
            "document_hash": document_hash,
            "analysis_time_seconds": elapsed,
        }

        # Persist results
        ComplianceSessionService.update_session(
            db, session_id, {
                "status": "completed",
                "current_stage": 7,
                "analysis_results": analysis_results,
                "compliance_score": summary["compliance_score"],
                "compliant_count": summary["compliant"],
                "non_compliant_count": summary["non_compliant"],
                "not_applicable_count": summary["not_applicable"],
                "total_standards": len(selected),
                "total_questions": len(questions),
            }
        )

        ComplianceSessionService.add_message(
            db, session_id, "system",
            f"Analysis complete! Score: {summary['compliance_score']}% "
            f"({summary['compliant']} compliant, {summary['non_compliant']} non-compliant, "
            f"{summary['not_applicable']} N/A). Time: {elapsed}s."
        )

        # Save to cache for future re-use
        try:
            self._save_cache(
                db, document_hash, session.framework or "IFRS",
                questions_hash, analysis_results, metadata,
            )
            logger.info("Cached analysis results for session %s", sid)
        except Exception as cache_err:
            logger.warning("Failed to cache results: %s (non-blocking)", cache_err)

        # Persist normalized results to ComplianceResult table
        try:
            result_dicts = [r.to_dict() for r in results]
            rows = ComplianceSessionService.persist_results_to_db(
                db, session_id, result_dicts
            )
            logger.info("Persisted %d results to ComplianceResult table", rows)
        except Exception as e:
            logger.warning("Failed to persist normalized results: %s (non-blocking)", e)

        logger.info(
            "Compliance analysis complete: session=%s score=%d%% time=%.1fs",
            sid, summary["compliance_score"], elapsed,
        )

        return {
            "session_id": sid,
            "status": "completed",
            "compliance_score": summary["compliance_score"],
            "summary": summary,
            "total_results": len(results),
            "analysis_time_seconds": elapsed,
        }

    def run_streaming(
        self,
        db: Session,
        session_id: uuid.UUID,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Streaming version of run — yields NDJSON progress dicts.

        Enhancements over basic pipeline:
         - Cache lookup: skips analysis if exact doc+framework+questions combo exists.
         - Per-question progress rows: enables resume-from-failure.
         - Resume: completed questions are skipped on retry after crash.
        """
        session = ComplianceSessionService.get_session(db, session_id)
        if not session:
            yield {"type": "error", "data": {"message": f"Session {session_id} not found"}}
            return

        start_time = time.time()
        job_id = f"job_{uuid.uuid4().hex[:12]}"

        ComplianceSessionService.update_session(
            db, session_id, {"status": "analyzing", "current_stage": 6}
        )

        yield {"type": "status", "data": {"status": "extracting", "message": "Extracting document text...", "job_id": job_id}}

        try:
            # Extract
            fs_text = ""
            notes_text = ""
            if session.financial_statements_file:
                fs_result = self._extractor.extract(session.financial_statements_file)
                fs_text = fs_result.full_text
            if session.notes_file:
                notes_result = self._extractor.extract(session.notes_file)
                notes_text = notes_result.full_text

            combined_text = fs_text + "\n\n" + notes_text
            if not combined_text.strip():
                yield {"type": "error", "data": {"message": "No text extracted from documents"}}
                return

            yield {"type": "status", "data": {"status": "chunking", "message": "Chunking documents..."}}

            # Chunk
            document_hash = self._chunking.generate_document_hash(combined_text)
            sid = str(session_id)
            fs_chunks = self._chunking.chunk_text(fs_text, doc_id=f"{sid}_fs") if fs_text else []
            notes_chunks = self._chunking.chunk_text(notes_text, doc_id=f"{sid}_notes") if notes_text else []

            yield {"type": "status", "data": {"status": "indexing", "message": f"Indexing {len(fs_chunks) + len(notes_chunks)} chunks..."}}

            # Index
            all_chunks = fs_chunks + notes_chunks
            if self._search.is_available:
                self._search.ensure_index()
                self._search.index_chunks(fs_chunks, sid, document_hash)
                self._search.index_chunks(notes_chunks, sid, document_hash)
            else:
                self._engine.set_local_chunks(all_chunks)

            yield {"type": "status", "data": {"status": "metadata", "message": "Extracting metadata..."}}

            # Metadata
            metadata = self._engine.extract_metadata(combined_text)
            ComplianceSessionService.update_session(
                db, session_id, {"extracted_metadata": metadata}
            )

            # Load questions
            selected = session.selected_standards or []
            questions = DecisionTreeService.get_items_for_standards(selected)
            question_ids = [q.get("id", "") for q in questions]
            questions_hash = self._compute_questions_hash(question_ids)

            # ── Cache lookup ──
            cached = self._lookup_cache(db, document_hash, session.framework or "IFRS", questions_hash)
            if cached:
                logger.info("Cache hit for session %s — returning cached results", sid)
                yield {"type": "status", "data": {"status": "cache_hit", "message": "Using cached analysis results..."}}

                cached_results = cached.results
                if isinstance(cached_results, dict):
                    result_list = cached_results.get("results", [])
                    summary = cached_results.get("summary", {})
                else:
                    result_list = cached_results if isinstance(cached_results, list) else []
                    summary = {}

                for r in result_list:
                    yield {"type": "result", "data": r}

                elapsed = round(time.time() - start_time, 1)
                compliant = summary.get("compliant", sum(1 for r in result_list if r.get("status") == "YES"))
                non_compliant = summary.get("non_compliant", sum(1 for r in result_list if r.get("status") == "NO"))
                na = summary.get("not_applicable", sum(1 for r in result_list if r.get("status") == "N/A"))

                ComplianceSessionService.update_session(
                    db, session_id, {
                        "status": "completed",
                        "current_stage": 7,
                        "analysis_results": cached_results if isinstance(cached_results, dict) else {"results": result_list},
                        "compliance_score": round(compliant / max(compliant + non_compliant, 1) * 100),
                        "compliant_count": compliant,
                        "non_compliant_count": non_compliant,
                        "not_applicable_count": na,
                    }
                )

                yield {
                    "type": "complete",
                    "data": {
                        "total": len(result_list),
                        "compliant": compliant,
                        "non_compliant": non_compliant,
                        "not_applicable": na,
                        "errors": 0,
                        "results": result_list,
                        "cache_hit": True,
                    },
                }
                return

            # ── Initialize progress rows ──
            self._init_progress_rows(db, job_id, session_id, question_ids)

            # Check for previously completed questions (resume scenario)
            already_done = self._get_completed_question_ids(db, job_id)
            if already_done:
                logger.info("Resuming: %d questions already completed for job %s", len(already_done), job_id)

            yield {"type": "status", "data": {"status": "analyzing", "message": "Running compliance analysis..."}}

            # Stream analysis
            for event in self._engine.analyze_streaming(questions, document_hash, sid):
                # Track per-question progress
                if event["type"] == "result":
                    q_id = event["data"].get("question_id", "")
                    if q_id in already_done:
                        continue  # Skip already-completed on resume
                    status_val = event["data"].get("status", "")
                    err = event["data"].get("error")
                    prog_status = AnalysisProgressStatus.COMPLETED if not err else AnalysisProgressStatus.FAILED
                    self._mark_progress(db, job_id, q_id, prog_status, result=event["data"], error=err)

                yield event

                # If complete, persist and cache
                if event["type"] == "complete":
                    data = event["data"]
                    elapsed = round(time.time() - start_time, 1)

                    summary_data = {
                        "total": data["total"],
                        "compliant": data["compliant"],
                        "non_compliant": data["non_compliant"],
                        "not_applicable": data["not_applicable"],
                        "compliance_score": round(
                            data["compliant"] / max(data["compliant"] + data["non_compliant"], 1) * 100
                        ),
                    }

                    analysis_results = {
                        "summary": summary_data,
                        "results": data.get("results", []),
                        "document_hash": document_hash,
                        "analysis_time_seconds": elapsed,
                    }

                    ComplianceSessionService.update_session(
                        db, session_id, {
                            "status": "completed",
                            "current_stage": 7,
                            "analysis_results": analysis_results,
                            "compliance_score": summary_data["compliance_score"],
                            "compliant_count": data["compliant"],
                            "non_compliant_count": data["non_compliant"],
                            "not_applicable_count": data["not_applicable"],
                        }
                    )

                    # Save to cache for future re-use
                    try:
                        self._save_cache(
                            db, document_hash, session.framework or "IFRS",
                            questions_hash, analysis_results, metadata,
                        )
                        logger.info("Cached analysis results for session %s", sid)
                    except Exception as cache_err:
                        logger.warning("Failed to cache results: %s (non-blocking)", cache_err)

                    # Persist normalized results to ComplianceResult table
                    try:
                        rows = ComplianceSessionService.persist_results_to_db(
                            db, session_id, data.get("results", [])
                        )
                        logger.info("Persisted %d streaming results to ComplianceResult table", rows)
                    except Exception as persist_err:
                        logger.warning("Failed to persist normalized results: %s (non-blocking)", persist_err)

        except Exception as e:
            logger.error("Streaming analysis failed: %s", e)
            ComplianceSessionService.update_session(
                db, session_id, {"status": "failed"}
            )
            yield {"type": "error", "data": {"message": str(e)}}
