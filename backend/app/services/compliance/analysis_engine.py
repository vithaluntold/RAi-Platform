"""
Compliance Analysis Engine — the core AI analysis "brain".

Implements the full compliance analysis pipeline from the KT spec:
  1. Decision tree formatting (nested JSON → flat CHECKPOINT prompt format)
  2. Context building (search for relevant chunks per question)
  3. Two-phase analysis (Sequence 1: source+independent → Sequence 2: followups)
  4. Batched AI calls (groups of questions per LLM call for efficiency)
  5. Response parsing (===RESULT_START=== / ===RESULT_END=== blocks)
  6. Anti-hallucination validation (7 rules)
  7. Result aggregation with scoring

This service is called by the ComplianceOrchestrator during AgentExecution.
"""
import json
import logging
import re
import time
from typing import Optional, List, Dict, Any, Generator
from dataclasses import dataclass, field
from enum import Enum

from app.services.compliance.azure_openai_client import AzureOpenAIClient
from app.services.compliance.search_service import SearchService

logger = logging.getLogger(__name__)


# ─── Data Types ────────────────────────────────────────────────────────────

class ComplianceStatus(str, Enum):
    COMPLIANT = "YES"
    NON_COMPLIANT = "NO"
    NOT_APPLICABLE = "N/A"
    PENDING = "PENDING"
    ERROR = "ERROR"


@dataclass
class AnalysisResult:
    """Result of analyzing a single compliance question"""
    question_id: str
    standard: str
    section: str
    reference: str
    question: str
    status: ComplianceStatus = ComplianceStatus.PENDING
    confidence: float = 0.0
    explanation: str = ""
    evidence: str = ""
    suggested_disclosure: str = ""
    decision_tree_path: List[str] = field(default_factory=list)
    context_used: List[str] = field(default_factory=list)
    sequence: int = 1
    analysis_time_ms: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "standard": self.standard,
            "section": self.section,
            "reference": self.reference,
            "question": self.question,
            "status": self.status.value if isinstance(self.status, ComplianceStatus) else self.status,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "evidence": self.evidence,
            "suggested_disclosure": self.suggested_disclosure,
            "decision_tree_path": self.decision_tree_path,
            "context_used": self.context_used,
            "sequence": self.sequence,
            "analysis_time_ms": self.analysis_time_ms,
            "error": self.error,
        }


@dataclass
class AnalysisProgress:
    """Progress tracking for streaming updates"""
    total_questions: int = 0
    completed_questions: int = 0
    current_standard: str = ""
    current_question: str = ""
    phase: str = "preparing"  # preparing, sequence_1, sequence_2, validating, complete
    errors: List[str] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        if self.total_questions == 0:
            return 0.0
        return (self.completed_questions / self.total_questions) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_questions": self.total_questions,
            "completed_questions": self.completed_questions,
            "percentage": round(self.percentage, 1),
            "current_standard": self.current_standard,
            "current_question": self.current_question,
            "phase": self.phase,
            "errors": self.errors,
        }


# ─── Prompt Templates ─────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert IFRS compliance analyst. Your task is to analyze financial documents against specific compliance requirements.

For each question, you MUST:
1. Walk through the decision tree checkpoints step by step
2. Reference specific evidence from the provided document context
3. Arrive at a final compliance status

IMPORTANT RULES:
- Base your analysis ONLY on the provided document context
- If insufficient evidence exists, mark as N/A with explanation
- Never guess or assume information not present in the documents
- Provide specific page/section references when citing evidence
- Be precise about what is disclosed vs what is missing

Output your analysis in the following format for EACH question:

===RESULT_START===
QUESTION_ID: {question_id}
STATUS: {YES|NO|N/A}
CONFIDENCE: {0.0-1.0}
EXPLANATION: {detailed explanation of compliance assessment}
EVIDENCE: {specific text/numbers from the document that support the assessment}
SUGGESTED_DISCLOSURE: {if non-compliant, what should be disclosed}
DECISION_TREE_PATH: {comma-separated list of checkpoint answers taken}
===RESULT_END==="""

QUESTION_PROMPT_TEMPLATE = """
--- QUESTION {index} ---
ID: {question_id}
Standard: {standard}
Reference: {reference}
Question: {question}

Decision Tree:
{decision_tree}

Relevant Document Context:
{context}
---
"""

METADATA_EXTRACTION_PROMPT = """You are a financial document metadata extractor. Analyze the provided document text and extract the following metadata. Return a JSON object with these fields:

{
  "company_name": "Name of the company",
  "reporting_period": "e.g. Year ended December 31, 2025",
  "reporting_year": "e.g. 2025",
  "currency": "e.g. USD, EUR, GBP",
  "industry": "e.g. Manufacturing, Banking, Technology",
  "auditor": "Name of the audit firm",
  "reporting_framework": "e.g. IFRS, US GAAP",
  "consolidated": true/false,
  "interim": true/false,
  "document_type": "e.g. Annual Report, Financial Statements",
  "key_accounting_policies": ["list", "of", "key", "policies"]
}

Only include fields you can confidently extract. Use null for fields you cannot determine."""


# ─── Decision Tree Formatting ─────────────────────────────────────────────

def format_decision_tree_compact(tree: dict, depth: int = 0) -> str:
    """
    Convert nested decision tree JSON into flat CHECKPOINT format for prompts.

    Input:  {"question": "Is X disclosed?", "yes_case": {"question": "..."}, "no_case": "COMPLIANT: NO"}
    Output:
      CHECKPOINT 1: Is X disclosed?
        → YES: proceed to CHECKPOINT 2
        → NO: COMPLIANT: NO
      CHECKPOINT 2: ...
    """
    if isinstance(tree, str):
        return tree

    if not isinstance(tree, dict) or "question" not in tree:
        return str(tree) if tree else ""

    lines = []
    checkpoint_num = depth + 1
    indent = "  " * depth

    lines.append(f"{indent}CHECKPOINT {checkpoint_num}: {tree['question']}")

    yes_case = tree.get("yes_case")
    no_case = tree.get("no_case")

    if isinstance(yes_case, str):
        lines.append(f"{indent}  → YES: {yes_case}")
    elif isinstance(yes_case, dict):
        lines.append(f"{indent}  → YES: proceed to next checkpoint")
        lines.append(format_decision_tree_compact(yes_case, depth + 1))

    if isinstance(no_case, str):
        lines.append(f"{indent}  → NO: {no_case}")
    elif isinstance(no_case, dict):
        lines.append(f"{indent}  → NO: proceed to next checkpoint")
        lines.append(format_decision_tree_compact(no_case, depth + 1))

    return "\n".join(lines)


# ─── Response Parsing ──────────────────────────────────────────────────────

RESULT_BLOCK_RE = re.compile(
    r"===RESULT_START===\s*(.*?)\s*===RESULT_END===",
    re.DOTALL,
)

FIELD_RE = re.compile(
    r"^(QUESTION_ID|STATUS|CONFIDENCE|EXPLANATION|EVIDENCE|SUGGESTED_DISCLOSURE|DECISION_TREE_PATH):\s*(.*)$",
    re.MULTILINE,
)


def parse_analysis_response(response_text: str) -> List[Dict[str, Any]]:
    """
    Parse ===RESULT_START===...===RESULT_END=== blocks from AI response.

    Returns list of dicts with parsed fields.
    """
    results = []
    blocks = RESULT_BLOCK_RE.findall(response_text)

    for block in blocks:
        parsed = {}
        for match in FIELD_RE.finditer(block):
            field_name = match.group(1).lower()
            field_value = match.group(2).strip()
            parsed[field_name] = field_value

        if "question_id" in parsed:
            # Normalize status — take the LAST match if multiple STATUS lines
            status_matches = re.findall(r"^STATUS:\s*(.*)$", block, re.MULTILINE)
            if status_matches:
                parsed["status"] = status_matches[-1].strip()

            # Parse confidence as float
            try:
                parsed["confidence"] = float(parsed.get("confidence", "0.0"))
            except ValueError:
                parsed["confidence"] = 0.0

            # Parse decision tree path
            path_str = parsed.get("decision_tree_path", "")
            if path_str:
                parsed["decision_tree_path"] = [
                    p.strip() for p in path_str.split(",") if p.strip()
                ]
            else:
                parsed["decision_tree_path"] = []

            results.append(parsed)

    return results


# ─── Anti-Hallucination Validation ─────────────────────────────────────────

def validate_result(result: Dict[str, Any], context_available: bool = True) -> Dict[str, Any]:
    """
    Apply 7 anti-hallucination validation rules to an analysis result.

    Rules:
      1. Confidence cap: without strong evidence, cap at 0.7
      2. N/A justification: N/A must have proper explanation pattern
      3. Evidence required: YES/NO must have non-empty evidence
      4. Status normalization: normalize to YES/NO/N/A
      5. Explanation required: must have non-trivial explanation (>20 chars)
      6. Context check: if no context was available, cap confidence at 0.5
      7. Disclosure check: NON_COMPLIANT should have suggested disclosure
    """
    validated = dict(result)

    # Rule 1: Confidence cap without evidence
    evidence = validated.get("evidence", "")
    if len(evidence) < 20:
        validated["confidence"] = min(validated.get("confidence", 0.0), 0.7)

    # Rule 2: N/A justification
    status = str(validated.get("status", "")).upper().strip()
    if status == "N/A":
        explanation = validated.get("explanation", "")
        na_patterns = [
            "not applicable", "does not apply", "not relevant",
            "not required", "outside the scope", "no such",
            "entity does not", "company does not",
        ]
        has_justification = any(p in explanation.lower() for p in na_patterns)
        if not has_justification and len(explanation) < 30:
            validated["confidence"] = min(validated.get("confidence", 0.0), 0.5)

    # Rule 3: Evidence required for YES/NO
    if status in ("YES", "NO") and len(evidence) < 10:
        validated["confidence"] = min(validated.get("confidence", 0.0), 0.6)

    # Rule 4: Status normalization
    status_map = {
        "YES": "YES", "COMPLIANT": "YES", "TRUE": "YES", "PASS": "YES",
        "NO": "NO", "NON-COMPLIANT": "NO", "NON_COMPLIANT": "NO",
        "FALSE": "NO", "FAIL": "NO",
        "N/A": "N/A", "NA": "N/A", "NOT APPLICABLE": "N/A",
        "NOT_APPLICABLE": "N/A",
    }
    validated["status"] = status_map.get(status, status)

    # Rule 5: Explanation required
    explanation = validated.get("explanation", "")
    if len(explanation) < 20:
        validated["confidence"] = min(validated.get("confidence", 0.0), 0.5)

    # Rule 6: Context availability check
    if not context_available:
        validated["confidence"] = min(validated.get("confidence", 0.0), 0.5)
        if validated["status"] not in ("N/A",):
            validated["status"] = "N/A"
            validated["explanation"] = (
                "Insufficient document context available to assess this requirement. "
                + validated.get("explanation", "")
            )

    # Rule 7: Disclosure check for non-compliant
    if validated["status"] == "NO":
        disclosure = validated.get("suggested_disclosure", "")
        if not disclosure or len(disclosure) < 10:
            validated["suggested_disclosure"] = (
                "Review and address the non-compliance identified in the explanation above."
            )

    return validated


# ─── Analysis Engine ───────────────────────────────────────────────────────

class ComplianceAnalysisEngine:
    """
    Core compliance analysis engine.

    Orchestrates:
      - Grouping questions into batches
      - Building context per question (via SearchService)
      - Calling AI (via AzureOpenAIClient)
      - Parsing and validating responses
      - Two-phase analysis (source → followups)

    Usage:
        engine = ComplianceAnalysisEngine(llm_client, search_service)
        results = engine.analyze(questions, document_hash, session_id)
        # or streaming:
        for progress in engine.analyze_streaming(...):
            send_to_client(progress)
    """

    def __init__(
        self,
        llm_client: AzureOpenAIClient,
        search_service: SearchService,
        batch_size: int = 5,
    ):
        self._llm = llm_client
        self._search = search_service
        self._batch_size = batch_size
        self._local_chunks: list = []  # Fallback chunks when Azure Search unavailable

    def set_local_chunks(self, chunks: list):
        """Inject pre-computed chunks for local fallback search"""
        self._local_chunks = chunks

    def extract_metadata(self, document_text: str) -> Dict[str, Any]:
        """
        Use AI to extract structured metadata from document text.
        Returns dict with company_name, reporting_period, currency, etc.
        """
        # Use first ~8000 chars for metadata (covers front matter)
        text_sample = document_text[:8000]

        try:
            result = self._llm.chat_completion_json(
                system_prompt=METADATA_EXTRACTION_PROMPT,
                user_prompt=f"Document text:\n\n{text_sample}",
                temperature=0.0,
                max_tokens=1024,
            )
            return result.get("parsed") or {}
        except Exception as e:
            logger.error("Metadata extraction failed: %s", e)
            return {"error": str(e)}

    def suggest_standards(
        self,
        document_text: str,
        available_standards: List[Dict[str, Any]],
    ) -> List[str]:
        """
        AI-powered standard suggestion — reads document and recommends applicable standards.

        Args:
            document_text: Extracted document text (first ~10000 chars)
            available_standards: List of {section, title, description} dicts

        Returns:
            List of standard section keys that are likely applicable
        """
        text_sample = document_text[:10000]

        standards_list = "\n".join(
            f"- {s['section']}: {s.get('title', '')} — {s.get('description', '')[:100]}"
            for s in available_standards
        )

        prompt = f"""Based on the following financial document excerpt, identify which IFRS standards are applicable.
Return a JSON object with a "standards" array containing the section codes of applicable standards.

Available standards:
{standards_list}

Document excerpt:
{text_sample}

Return JSON: {{"standards": ["IAS 1", "IFRS 9", ...]}}"""

        try:
            result = self._llm.chat_completion_json(
                system_prompt="You are an IFRS expert. Identify applicable standards based on document content.",
                user_prompt=prompt,
                temperature=0.0,
                max_tokens=1024,
            )
            parsed = result.get("parsed", {})
            return parsed.get("standards", [])
        except Exception as e:
            logger.error("Standard suggestion failed: %s", e)
            return []

    def analyze(
        self,
        questions: List[Dict[str, Any]],
        document_hash: str,
        session_id: str,
    ) -> List[AnalysisResult]:
        """
        Run full compliance analysis on all questions.

        Two-phase analysis:
          Phase 1 (Sequence 1): Analyze source and independent questions
          Phase 2 (Sequence 2): Analyze followup questions triggered by Phase 1 results

        Args:
            questions: List of compliance items from decision trees
            document_hash: Document hash for search filtering
            session_id: Session ID for search filtering

        Returns:
            List of AnalysisResult for all questions
        """
        results = []

        # Split into sequences
        seq1_questions = [q for q in questions if q.get("question_type") != "followup"]
        seq2_questions = [q for q in questions if q.get("question_type") == "followup"]

        # Phase 1: Source + Independent questions
        logger.info(
            "Phase 1: Analyzing %d source/independent questions (session=%s)",
            len(seq1_questions), session_id,
        )
        seq1_results = self._analyze_batch(
            seq1_questions, document_hash, session_id, sequence=1,
        )
        results.extend(seq1_results)

        # Phase 2: Followup questions (triggered by source answers)
        if seq2_questions:
            # Filter followups based on source triggers
            seq1_result_map = {r.question_id: r for r in seq1_results}
            triggered = self._filter_triggered_followups(
                seq2_questions, seq1_result_map,
            )

            if triggered:
                logger.info(
                    "Phase 2: Analyzing %d triggered followup questions",
                    len(triggered),
                )
                seq2_results = self._analyze_batch(
                    triggered, document_hash, session_id, sequence=2,
                )
                results.extend(seq2_results)

        return results

    def analyze_streaming(
        self,
        questions: List[Dict[str, Any]],
        document_hash: str,
        session_id: str,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Streaming version of analyze — yields progress updates as NDJSON-compatible dicts.

        Yields:
            {"type": "progress", "data": AnalysisProgress.to_dict()}
            {"type": "result", "data": AnalysisResult.to_dict()}
            {"type": "complete", "data": {"total": N, "compliant": N, ...}}
        """
        progress = AnalysisProgress(
            total_questions=len(questions),
            phase="preparing",
        )
        yield {"type": "progress", "data": progress.to_dict()}

        # Split into sequences
        seq1_questions = [q for q in questions if q.get("question_type") != "followup"]
        seq2_questions = [q for q in questions if q.get("question_type") == "followup"]

        # Phase 1
        progress.phase = "sequence_1"
        yield {"type": "progress", "data": progress.to_dict()}

        all_results = []
        for result in self._analyze_batch_streaming(
            seq1_questions, document_hash, session_id, sequence=1, progress=progress,
        ):
            all_results.append(result)
            progress.completed_questions += 1
            progress.current_question = result.question
            yield {"type": "result", "data": result.to_dict()}
            yield {"type": "progress", "data": progress.to_dict()}

        # Phase 2
        if seq2_questions:
            progress.phase = "sequence_2"
            yield {"type": "progress", "data": progress.to_dict()}

            seq1_map = {r.question_id: r for r in all_results}
            triggered = self._filter_triggered_followups(seq2_questions, seq1_map)

            for result in self._analyze_batch_streaming(
                triggered, document_hash, session_id, sequence=2, progress=progress,
            ):
                all_results.append(result)
                progress.completed_questions += 1
                yield {"type": "result", "data": result.to_dict()}
                yield {"type": "progress", "data": progress.to_dict()}

        # Final summary
        progress.phase = "complete"
        compliant = sum(1 for r in all_results if r.status == ComplianceStatus.COMPLIANT)
        non_compliant = sum(1 for r in all_results if r.status == ComplianceStatus.NON_COMPLIANT)
        na = sum(1 for r in all_results if r.status == ComplianceStatus.NOT_APPLICABLE)

        yield {
            "type": "complete",
            "data": {
                "total": len(all_results),
                "compliant": compliant,
                "non_compliant": non_compliant,
                "not_applicable": na,
                "errors": len(progress.errors),
                "results": [r.to_dict() for r in all_results],
            },
        }

    def _analyze_batch(
        self,
        questions: List[Dict[str, Any]],
        document_hash: str,
        session_id: str,
        sequence: int = 1,
    ) -> List[AnalysisResult]:
        """Analyze questions in batches"""
        results = []
        for i in range(0, len(questions), self._batch_size):
            batch = questions[i : i + self._batch_size]
            batch_results = self._process_single_batch(
                batch, document_hash, session_id, sequence,
            )
            results.extend(batch_results)
        return results

    def _analyze_batch_streaming(
        self,
        questions: List[Dict[str, Any]],
        document_hash: str,
        session_id: str,
        sequence: int = 1,
        progress: Optional[AnalysisProgress] = None,
    ) -> Generator[AnalysisResult, None, None]:
        """Streaming batch analysis — yields individual results"""
        for i in range(0, len(questions), self._batch_size):
            batch = questions[i : i + self._batch_size]
            if progress:
                progress.current_standard = batch[0].get("section", "") if batch else ""
            batch_results = self._process_single_batch(
                batch, document_hash, session_id, sequence,
            )
            for result in batch_results:
                yield result

    def _process_single_batch(
        self,
        questions: List[Dict[str, Any]],
        document_hash: str,
        session_id: str,
        sequence: int,
    ) -> List[AnalysisResult]:
        """Process a single batch of questions through the AI"""
        # Build per-question context
        question_prompts = []
        question_contexts = {}  # q_id → bool (has context)
        question_context_texts = {}  # q_id → list[str] (actual context snippets)

        for idx, q in enumerate(questions, 1):
            q_id = q.get("id", f"q_{idx}")
            question_text = q.get("question", "")
            context_required = q.get("context_required", "full")

            # Search for relevant context
            if self._search.is_available:
                search_results = self._search.search_for_context(
                    question=question_text,
                    context_required=context_required,
                    document_hash=document_hash,
                    session_id=session_id,
                    top=5,
                )
            elif self._local_chunks:
                # Local fallback when Azure Search not configured
                search_results = self._search.search_for_context_local(
                    question=question_text,
                    chunks=self._local_chunks,
                    top=5,
                )
            else:
                search_results = []

            context_texts = [r.content for r in search_results]
            context_str = "\n\n---\n\n".join(context_texts) if context_texts else "No relevant context found in the uploaded documents."
            question_contexts[q_id] = bool(context_texts)
            question_context_texts[q_id] = context_texts

            # Format decision tree
            tree = q.get("decision_tree", {})
            tree_formatted = format_decision_tree_compact(tree) if tree else "No decision tree available."

            question_prompts.append(
                QUESTION_PROMPT_TEMPLATE.format(
                    index=idx,
                    question_id=q_id,
                    standard=q.get("section", ""),
                    reference=q.get("reference", ""),
                    question=question_text,
                    decision_tree=tree_formatted,
                    context=context_str,
                )
            )

        # Combine into single prompt
        full_prompt = (
            f"Analyze the following {len(questions)} compliance questions. "
            f"Provide a ===RESULT_START===...===RESULT_END=== block for each.\n\n"
            + "\n".join(question_prompts)
        )

        # Call AI
        start_time = time.time()
        try:
            response = self._llm.chat_completion(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=full_prompt,
            )
            elapsed_ms = int((time.time() - start_time) * 1000)
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error("AI call failed for batch: %s", e)
            # Return error results for all questions in batch
            return [
                AnalysisResult(
                    question_id=q.get("id", f"q_{i}"),
                    standard=q.get("section", ""),
                    section=q.get("section", ""),
                    reference=q.get("reference", ""),
                    question=q.get("question", ""),
                    status=ComplianceStatus.ERROR,
                    error=str(e),
                    sequence=sequence,
                    analysis_time_ms=elapsed_ms,
                )
                for i, q in enumerate(questions, 1)
            ]

        # Parse response
        parsed_results = parse_analysis_response(response["content"])
        parsed_map = {r["question_id"]: r for r in parsed_results}

        # Build AnalysisResult objects
        results = []
        per_question_time = elapsed_ms // max(len(questions), 1)

        for q in questions:
            q_id = q.get("id", "")
            parsed = parsed_map.get(q_id, {})

            # Validate with anti-hallucination rules
            context_available = question_contexts.get(q_id, False)
            if parsed:
                validated = validate_result(parsed, context_available=context_available)
            else:
                validated = {
                    "status": "N/A",
                    "confidence": 0.3,
                    "explanation": "AI did not return a result for this question.",
                    "evidence": "",
                    "suggested_disclosure": "",
                    "decision_tree_path": [],
                }

            status_str = validated.get("status", "N/A")
            try:
                status = ComplianceStatus(status_str)
            except ValueError:
                status = ComplianceStatus.NOT_APPLICABLE

            results.append(AnalysisResult(
                question_id=q_id,
                standard=q.get("section", ""),
                section=q.get("section", ""),
                reference=q.get("reference", ""),
                question=q.get("question", ""),
                status=status,
                confidence=validated.get("confidence", 0.0),
                explanation=validated.get("explanation", ""),
                evidence=validated.get("evidence", ""),
                suggested_disclosure=validated.get("suggested_disclosure", ""),
                decision_tree_path=validated.get("decision_tree_path", []),
                context_used=question_context_texts.get(q_id, []),
                sequence=sequence,
                analysis_time_ms=per_question_time,
            ))

        return results

    def _filter_triggered_followups(
        self,
        followup_questions: List[Dict[str, Any]],
        source_results: Dict[str, AnalysisResult],
    ) -> List[Dict[str, Any]]:
        """
        Filter followup questions based on source question triggers.

        A followup is triggered when:
          - source_question exists and matches a source result
          - source_trigger matches the source result's status
        """
        triggered = []
        for q in followup_questions:
            source_q_id = q.get("source_question")
            source_trigger = q.get("source_trigger", "").upper()

            if not source_q_id:
                # No source dependency — include by default
                triggered.append(q)
                continue

            source_result = source_results.get(source_q_id)
            if not source_result:
                continue

            # Check trigger match
            source_status = source_result.status.value if isinstance(
                source_result.status, ComplianceStatus
            ) else str(source_result.status)

            if source_trigger in (source_status, ""):
                triggered.append(q)

        return triggered

    @staticmethod
    def aggregate_results(results: List[AnalysisResult]) -> Dict[str, Any]:
        """
        Aggregate analysis results into summary statistics.

        Returns dict with counts, score, and per-standard breakdown.
        """
        total = len(results)
        compliant = sum(1 for r in results if r.status == ComplianceStatus.COMPLIANT)
        non_compliant = sum(1 for r in results if r.status == ComplianceStatus.NON_COMPLIANT)
        na = sum(1 for r in results if r.status == ComplianceStatus.NOT_APPLICABLE)
        errors = sum(1 for r in results if r.status == ComplianceStatus.ERROR)

        # Score: compliant / (compliant + non_compliant) * 100
        assessed = compliant + non_compliant
        score = round((compliant / assessed) * 100) if assessed > 0 else 0

        # Per-standard breakdown
        by_standard = {}
        for r in results:
            std = r.standard or "Unknown"
            if std not in by_standard:
                by_standard[std] = {
                    "total": 0,
                    "compliant": 0,
                    "non_compliant": 0,
                    "not_applicable": 0,
                    "errors": 0,
                    "avg_confidence": 0.0,
                }
            by_standard[std]["total"] += 1
            if r.status == ComplianceStatus.COMPLIANT:
                by_standard[std]["compliant"] += 1
            elif r.status == ComplianceStatus.NON_COMPLIANT:
                by_standard[std]["non_compliant"] += 1
            elif r.status == ComplianceStatus.NOT_APPLICABLE:
                by_standard[std]["not_applicable"] += 1
            elif r.status == ComplianceStatus.ERROR:
                by_standard[std]["errors"] += 1

        # Calculate per-standard avg confidence
        for std, info in by_standard.items():
            std_results = [r for r in results if r.standard == std]
            if std_results:
                info["avg_confidence"] = round(
                    sum(r.confidence for r in std_results) / len(std_results), 2
                )

        return {
            "total": total,
            "compliant": compliant,
            "non_compliant": non_compliant,
            "not_applicable": na,
            "errors": errors,
            "compliance_score": score,
            "by_standard": by_standard,
            "avg_confidence": round(
                sum(r.confidence for r in results) / max(total, 1), 2
            ),
        }
