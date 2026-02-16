"""
Compliance Service — business logic for compliance sessions and decision trees.

Handles:
  - Session CRUD with auto-generated session codes
  - Loading IFRS decision tree JSONs from disk
  - File upload tracking
  - Standards listing and filtering
"""
import json
import glob
import os
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.compliance import (
    ComplianceSession,
    ComplianceSessionStatus,
    ComplianceResult,
    ComplianceResultStatus,
)
from app.models.agent import Agent, AgentType, AgentStatus

# Path to IFRS decision tree JSON files
DECISION_TREE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "IFRS_decisiontree",
)


def _generate_session_code(client_name: str) -> str:
    """Generate a session code: RAI-{CLIENT_PREFIX}-{MMDDYYYY}-{SHORT_UUID}"""
    prefix = client_name[:5].upper().replace(" ", "")
    date_str = datetime.utcnow().strftime("%m%d%Y")
    short_id = uuid.uuid4().hex[:4].upper()
    return f"RAI-{prefix}-{date_str}-{short_id}"


class ComplianceSessionService:
    """Handles compliance session CRUD"""

    @staticmethod
    def create_session(
        db: Session, payload: dict, created_by: uuid.UUID
    ) -> ComplianceSession:
        """Create a new compliance analysis session"""
        session_code = _generate_session_code(payload["client_name"])

        # Auto-link to system compliance agent if not explicitly provided
        agent_id = payload.get("agent_id")
        if not agent_id:
            system_agent = db.query(Agent).filter(
                Agent.agent_type == AgentType.COMPLIANCE_ANALYSIS,
                Agent.is_system == True,
                Agent.status == AgentStatus.ACTIVE,
            ).first()
            if system_agent:
                agent_id = system_agent.id

        session = ComplianceSession(
            session_code=session_code,
            client_name=payload["client_name"],
            framework=payload.get("framework", "IFRS"),
            status=ComplianceSessionStatus.AWAITING_UPLOAD,
            current_stage=1,
            agent_id=agent_id,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Welcome to the RAI Compliance Analysis Platform! "
                        "Please upload your document to begin the analysis process."
                    ),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ],
            created_by=created_by,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_session(
        db: Session, session_id: uuid.UUID
    ) -> Optional[ComplianceSession]:
        """Get a single session by ID"""
        return (
            db.query(ComplianceSession)
            .filter(ComplianceSession.id == session_id)
            .first()
        )

    @staticmethod
    def list_sessions(
        db: Session,
        created_by: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        framework: Optional[str] = None,
    ) -> list:
        """List compliance sessions with optional filters"""
        query = db.query(ComplianceSession)
        if created_by:
            query = query.filter(ComplianceSession.created_by == created_by)
        if status:
            try:
                query = query.filter(
                    ComplianceSession.status == ComplianceSessionStatus(status)
                )
            except ValueError:
                pass
        if framework:
            query = query.filter(ComplianceSession.framework == framework)
        return query.order_by(ComplianceSession.created_at.desc()).all()

    @staticmethod
    def update_session(
        db: Session, session_id: uuid.UUID, payload: dict
    ) -> Optional[ComplianceSession]:
        """Update a compliance session"""
        session = (
            db.query(ComplianceSession)
            .filter(ComplianceSession.id == session_id)
            .first()
        )
        if not session:
            return None

        simple_fields = [
            "client_name",
            "framework",
            "current_stage",
            "selected_standards",
            "extracted_metadata",
            "analysis_results",
            "compliance_score",
            "total_standards",
            "total_questions",
            "compliant_count",
            "non_compliant_count",
            "not_applicable_count",
        ]
        # JSON columns need flag_modified to detect in-place mutations
        json_fields = {"selected_standards", "extracted_metadata", "analysis_results"}
        for field in simple_fields:
            if field in payload and payload[field] is not None:
                setattr(session, field, payload[field])
                if field in json_fields:
                    flag_modified(session, field)

        if "status" in payload and payload["status"] is not None:
            try:
                session.status = ComplianceSessionStatus(payload["status"])
            except ValueError:
                pass

        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def update_files(
        db: Session,
        session_id: uuid.UUID,
        financial_statements_file: Optional[str] = None,
        financial_statements_filename: Optional[str] = None,
        notes_file: Optional[str] = None,
        notes_filename: Optional[str] = None,
    ) -> Optional[ComplianceSession]:
        """Update file references on a session"""
        session = (
            db.query(ComplianceSession)
            .filter(ComplianceSession.id == session_id)
            .first()
        )
        if not session:
            return None

        if financial_statements_file:
            session.financial_statements_file = financial_statements_file
            session.financial_statements_filename = financial_statements_filename
        if notes_file:
            session.notes_file = notes_file
            session.notes_filename = notes_filename

        # If both files uploaded, advance status
        if session.financial_statements_file and session.notes_file:
            session.status = ComplianceSessionStatus.PROCESSING
            session.current_stage = 2
            # Add system message — use list() to force new object for SQLAlchemy change detection
            messages = list(session.messages or [])
            messages.append(
                {
                    "role": "system",
                    "content": (
                        f"Files uploaded successfully. "
                        f"Financial Statements: {session.financial_statements_filename}, "
                        f"Notes: {session.notes_filename}. "
                        f"Processing documents..."
                    ),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            session.messages = messages

        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def add_message(
        db: Session,
        session_id: uuid.UUID,
        role: str,
        content: str,
    ) -> Optional[ComplianceSession]:
        """Add a message to the session chat log"""
        session = (
            db.query(ComplianceSession)
            .filter(ComplianceSession.id == session_id)
            .first()
        )
        if not session:
            return None

        # Use list() to force new object — SQLAlchemy skips change detection
        # when re-assigning the same object reference on JSON columns
        messages = list(session.messages or [])
        messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        session.messages = messages
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def delete_session(db: Session, session_id: uuid.UUID) -> bool:
        """Delete a compliance session"""
        session = (
            db.query(ComplianceSession)
            .filter(ComplianceSession.id == session_id)
            .first()
        )
        if not session:
            return False
        db.delete(session)
        db.commit()
        return True


    @staticmethod
    def persist_results_to_db(
        db: Session,
        session_id: uuid.UUID,
        results: list,
    ) -> int:
        """
        Write analysis results to the normalized ComplianceResult table.

        Upserts by (session_id, question_id) — safe to run multiple times.
        results: list of dicts from AnalysisResult.to_dict()
        Returns: number of rows upserted
        """
        # Map AI status strings to DB enum
        status_map = {
            "YES": ComplianceResultStatus.COMPLIANT,
            "NO": ComplianceResultStatus.NON_COMPLIANT,
            "N/A": ComplianceResultStatus.NOT_APPLICABLE,
            "PENDING": ComplianceResultStatus.PENDING,
            "ERROR": ComplianceResultStatus.ERROR,
        }

        count = 0
        for r in results:
            question_id = r.get("question_id", "")
            if not question_id:
                continue

            db_status = status_map.get(
                r.get("status", "PENDING"), ComplianceResultStatus.PENDING
            )

            # Context_used may be a list — join to text
            context_used = r.get("context_used", [])
            if isinstance(context_used, list):
                context_used = "\n---\n".join(context_used)

            existing = (
                db.query(ComplianceResult)
                .filter(
                    ComplianceResult.session_id == session_id,
                    ComplianceResult.question_id == question_id,
                )
                .first()
            )

            if existing:
                existing.status = db_status
                existing.confidence = r.get("confidence", 0.0)
                existing.explanation = r.get("explanation", "")
                existing.evidence = r.get("evidence", "")
                existing.suggested_disclosure = r.get("suggested_disclosure", "")
                existing.decision_tree_path = r.get("decision_tree_path", [])
                existing.context_used = context_used
                existing.analysis_time_ms = r.get("analysis_time_ms", 0)
                existing.error = r.get("error")
                existing.sequence = r.get("sequence", 1)
            else:
                row = ComplianceResult(
                    session_id=session_id,
                    question_id=question_id,
                    standard=r.get("standard", ""),
                    section=r.get("section", ""),
                    reference=r.get("reference", ""),
                    question_text=r.get("question", ""),
                    sequence=r.get("sequence", 1),
                    status=db_status,
                    confidence=r.get("confidence", 0.0),
                    explanation=r.get("explanation", ""),
                    evidence=r.get("evidence", ""),
                    suggested_disclosure=r.get("suggested_disclosure", ""),
                    decision_tree_path=r.get("decision_tree_path", []),
                    context_used=context_used,
                    analysis_time_ms=r.get("analysis_time_ms", 0),
                    error=r.get("error"),
                )
                db.add(row)

            count += 1

        db.commit()
        return count


class DecisionTreeService:
    """Loads and serves IFRS decision tree JSONs"""

    _cache: Optional[dict] = None

    @classmethod
    def _load_all(cls) -> dict:
        """Load all decision tree JSONs into memory (cached)"""
        if cls._cache is not None:
            return cls._cache

        cls._cache = {}
        pattern = os.path.join(DECISION_TREE_DIR, "*.json")
        for filepath in sorted(glob.glob(pattern)):
            filename = os.path.basename(filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for section in data.get("sections", []):
                section_key = section["section"].replace(" ", "_")
                cls._cache[section_key] = {
                    "section": section["section"],
                    "title": section.get("title", ""),
                    "description": section.get("description", ""),
                    "items": section.get("items", []),
                    "file_name": filename,
                }
        return cls._cache

    @classmethod
    def reload(cls):
        """Force reload of decision trees (e.g., after adding new files)"""
        cls._cache = None
        cls._load_all()

    @classmethod
    def list_standards(cls) -> list:
        """List all available standards with item counts"""
        data = cls._load_all()
        standards = []
        for key, info in data.items():
            standards.append(
                {
                    "section": info["section"],
                    "title": info["title"],
                    "description": info["description"],
                    "item_count": len(info["items"]),
                    "file_name": info["file_name"],
                }
            )
        return standards

    @classmethod
    def get_summary(cls) -> dict:
        """Get aggregate summary of all standards"""
        standards = cls.list_standards()
        total_questions = sum(s["item_count"] for s in standards)
        return {
            "total_standards": len(standards),
            "total_questions": total_questions,
            "frameworks": ["IFRS"],
            "standards": standards,
        }

    @classmethod
    def get_standard(cls, section_key: str) -> Optional[dict]:
        """
        Get full details of a specific standard.
        section_key: e.g. "IAS_1", "IFRS_9", "IFRS_16"
        """
        data = cls._load_all()
        return data.get(section_key)

    @classmethod
    def get_items_for_standards(cls, standard_keys: List[str]) -> list:
        """Get all compliance items for a list of standard keys"""
        data = cls._load_all()
        items = []
        for key in standard_keys:
            info = data.get(key)
            if info:
                items.extend(info["items"])
        return items

    @classmethod
    def search_items(cls, query: str) -> list:
        """Search across all standards for items matching a query string"""
        data = cls._load_all()
        query_lower = query.lower()
        results = []
        for key, info in data.items():
            for item in info["items"]:
                if (
                    query_lower in item.get("question", "").lower()
                    or query_lower in item.get("original_question", "").lower()
                    or query_lower in item.get("reference", "").lower()
                ):
                    results.append(
                        {
                            "standard": info["section"],
                            **item,
                        }
                    )
        return results
