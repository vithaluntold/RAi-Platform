# RAI Compliance Analysis Platform — Complete Knowledge Transfer Document

> **Version**: 4.0 | **Updated**: 16 February 2026

---

## Table of Contents

1. [Mission & Why This Exists](#1-mission--why-this-exists)
2. [Complete User Journey (E2E Flow)](#2-complete-user-journey-e2e-flow)
3. [System Architecture](#3-system-architecture)
4. [Frontend State Machine (20 States)](#4-frontend-state-machine-20-states)
5. [Backend API Endpoints (47 Endpoints)](#5-backend-api-endpoints-47-endpoints)
6. [AI/Search Service Layer](#6-aisearch-service-layer)
7. [Checklist & Decision Tree Structure](#7-checklist--decision-tree-structure)
8. [Data Types & Interfaces](#8-data-types--interfaces)
9. [Database Schema & Storage](#9-database-schema--storage)
10. [Results Page & Reporting](#10-results-page--reporting)
11. [Key File Reference](#11-key-file-reference)
12. [Configuration & Environment](#12-configuration--environment)
13. [Deployment & Infrastructure](#13-deployment--infrastructure)

---

## 1. Mission & Why This Exists

**WHAT**: An automated compliance checking platform that analyzes financial statements against accounting standards (IFRS, US GAAP, Ind AS).

**WHY**: Auditors and compliance teams manually check 200+ disclosure requirements per financial report — a process that takes days. This platform:

1. Extracts content from PDF/DOCX financial statements
2. Identifies which accounting standards apply
3. Checks each requirement against the actual document content
4. Produces a detailed compliance report with evidence, confidence, and suggested fix language

**WHO**: Financial auditors, compliance officers, regulatory teams.

**HOW**: Server-side Express API + React frontend using Azure AI services.

- **Azure Document Intelligence**: PDF/DOCX → structured text
- **Azure AI Search**: Semantic search over document chunks
- **Azure OpenAI GPT-5.2/5.1** (6 endpoints, round-robin) with GPT-4o/GPT-4o-mini fallback chain: Tree-driven compliance analysis with chain-of-thought reasoning
- **Neon PostgreSQL**: Sessions, results, progress persistence

---

## 2. Complete User Journey (E2E Flow)

This section traces EVERY step the user takes, what happens behind the scenes, and WHY each step exists.

### Step 1: File Upload

**What the user does:**

Opens the app → sees a chat interface → uploads TWO files:

- **File 1**: Financial Statements (Balance Sheet, P&L, Cash Flow, Equity)
- **File 2**: Notes to the Financial Statements (accounting policies, disclosures)

**Why two files?**

Financial statements and notes are fundamentally different documents:

- FS = numbers, line items, structured tables (needs number extraction)
- Notes = narrative text with disclosures (needs semantic understanding)

Separating them allows:

1. Different indexing strategies per document type
2. Targeted context routing — some questions only need FS numbers, others only need note disclosures, avoiding sending everything to AI every time
3. Smaller, more relevant chunks per question = better AI accuracy

**What happens (Frontend → Backend):**

1. Frontend detects file types (PDF/DOCX/image) via MIME + extension
2. `POST /api/jobs` → Creates a tracking job → returns `jobId`
3. `POST /api/process/extract-azure-dual` → Sends both files as multipart → Azure Document Intelligence extracts:
   - paragraphs (with page numbers, coordinates)
   - tables (as structured markdown)
   - full text content
   - Returns: `{ financialStatements: { content, paragraphs, tables, pageCount }, notesToAccounts: { content, paragraphs, tables, pageCount } }`

**Why Azure Document Intelligence?**

Simple PDF text extraction misses table structures, column layouts, and multi-page spanning content. Azure DI understands document layout and correctly handles:

- Multi-column financial tables
- Headers/footers that should be stripped
- Page-spanning paragraphs
- Image-based PDFs (OCR)

---

### Step 2: Document Indexing & Metadata Extraction

**What happens (automatic, no user action):**

1. `POST /api/process/metadata` → Extracts company metadata via AI
   - First indexes document for search-augmented metadata extraction
   - GPT-4o-mini analyzes content and extracts: `companyName`, `currentReportingYear`, `comparativeYear`, `reportingCurrency`, `basisOfPreparation`, `industry`, `entityType`, `listingStatus`, `consolidation`, `goingConcern`, `companyAddress`, `accountingPolicies`
   - Returns: `{ metadata, documentHash }`

2. `POST /api/process/index-document` → Final full indexing with taxonomy
   - Chunks both documents: 4000-char max chunks with semantic boundary splitting (tables kept atomic, note/section headers as boundaries)
   - Each chunk is tagged with:
     - IFRS taxonomy concepts (from 5,512-concept index)
     - Standard references (e.g., "IAS 7", "IFRS 16")
     - Section type (`financial_statements` | `notes_to_accounts`)
     - Statement type (`balanceSheet`, `incomeStatement`, `cashFlow`, `equity`)
     - Line item categories
     - Page numbers
   - Uploads all chunks to Azure AI Search index
   - Returns: `{ chunksIndexed, fsChunks, noteChunks }`

3. `POST /api/process/validate-financials` → Validates FS completeness
   - Checks: does the FS contain a Balance Sheet? Income Statement? Cash Flow? Statement of Changes in Equity?
   - Warns user if any are missing

4. `POST /api/sessions?action=create` → Saves session to DB for persistence

**Why document hashing?**

`documentHash` = SHA-256 of (FS content + Notes content), truncated to 12 chars.

Purpose:

1. **Document isolation** — search queries ALWAYS filter by `documentHash`, so results from one company's FS can never contaminate another's
2. **Deduplication** — if user uploads the same document twice, we detect it
3. **Caching** — analysis results are cached by `documentHash` + `framework` + `questionsHash`

**Why chunk with taxonomy tags?**

When the AI analyzes "Does the entity disclose cash flow from operations?", we don't send the ENTIRE document. Instead, we search Azure AI Search for chunks tagged with IAS 7 concepts + cash flow taxonomy keywords. This:

1. Reduces token usage by 10-50x (200K chars instead of 1.5M)
2. Gives the AI focused, relevant context instead of noise
3. Enables per-question context routing (`notes_only` vs `FS` vs `full`)

> **NOTE**: Chunking is done by `targetedIndexOrchestrator.js`, NOT `azureSearchService.js`. Tables are kept as atomic chunks regardless of size (preserves numerical integrity). Text is split at semantic boundaries (note headers, section headers) up to 4000 chars.

**Transition**: → `AWAITING_METADATA_CONFIRMATION`

---

### Step 3: Metadata Confirmation

**What the user does:**

Reviews the AI-extracted metadata. Can edit:

- Company name (if AI got it wrong)
- Reporting periods (current year, comparative year)
- Basis of preparation (IFRS, US GAAP, etc.)
- Entity type, listing status, going concern status

**Why?**

Metadata is injected into EVERY AI analysis prompt. If the company name is wrong, the AI might hallucinate references. If the reporting year is wrong, the AI will look for disclosures in the wrong period. This is the user's quality gate for all downstream analysis.

**What happens:**

- `handleMetadataConfirm()` preserves `documentId`/`documentHash`
- `PUT /api/sessions` updates session with confirmed metadata

**Transition**: → `AWAITING_FRAMEWORK_SELECTION`

---

### Step 4: Framework Selection

**What the user does:**

Selects the applicable accounting framework:

- IFRS (International Financial Reporting Standards)
- US GAAP
- Ind AS (Indian standards)
- Custom framework (user-defined taxonomy)

**Why?**

Different frameworks have different disclosure requirements. A company reporting under IFRS needs IAS/IFRS compliance checks; one under US GAAP needs ASC topic checks. The framework determines WHICH checklists to load.

**What happens (for IFRS):**

- `POST /api/process/suggest-standards`
- AI analyzes the document content and suggests which of 44 IFRS standards are applicable (e.g., "This company has leases, so IFRS 16 applies. They have revenue from contracts, so IFRS 15 applies.")
- Returns: `["IAS 1", "IAS 7", "IFRS 15", "IFRS 16", ...]`

**Why AI-suggest standards?**

There are 44 IFRS standards. Most companies need 8-15 of them. Without suggestion, users would have to manually select each one. The AI reads the actual content and identifies which standards are relevant, saving user effort and preventing missed standards.

**Transition**: → `AWAITING_STANDARDS_CONFIRMATION`

---

### Step 5: Standards Confirmation

**What the user does:**

Reviews the AI-suggested standards. Can:

- Add standards the AI missed
- Remove standards that don't apply
- See all 44 available standards

**What happens:**

- `POST /api/process/validation-preview`
- Counts how many indexed chunks map to each selected standard
- Shows: "IAS 7: 23 chunks, IFRS 16: 45 chunks, ..."
- This helps user gauge: "Do we have enough document content for each standard?"

**Why validation preview?**

If a standard shows 0 chunks, it likely means the document doesn't contain relevant disclosures for that standard. The user can deselect it rather than wasting analysis time on questions that will all return N/A.

**Transition**: → `AWAITING_VALIDATION_APPROVAL`

---

### Step 6: Chunk Validation (Optional)

**What the user does:**

Decides whether to run AI revalidation of chunk-to-standard mappings.

- "Approve Revalidation" → AI re-checks each chunk's standard tags
- "Skip" → proceed with existing taxonomy-based tags

**What happens (if approved):**

- `POST /api/process/revalidate-chunks`
- Queries all chunks for selected standards
- AI (GPT-4o-mini) reviews each chunk batch and re-assigns standards
- Returns: `{ revalidatedCount, changedCount }`

**Why?**

Taxonomy-based tagging is rule-based and can miss nuanced associations. For example, a note about "provisions for lease obligations" might be tagged IAS 37 (provisions) but also relates to IFRS 16 (leases). AI revalidation catches these cross-standard connections. However, it costs extra API calls, so it's optional.

**Transition**: → `PREVIEWING_INDEXED_CONTENT`

---

### Step 7: Chunk Preview

**What the user does:**

Reviews the actual document chunks that will be sent to AI for each standard. Can go back to change standards if chunks look wrong.

**Why?**

Transparency — the user sees exactly what the AI will analyze. If chunks are missing or mistagged, they can go back and either revalidate or adjust standard selection. This is the "garbage in, garbage out" safety net.

**Transition**: → `AWAITING_INSTRUCTIONS` (proceed) or → `AWAITING_STANDARDS_CONFIRMATION` (back)

---

### Step 8: Filter Instructions (Optional)

**What the user does:**

Enters optional free-text instructions to narrow the analysis.

Examples:

- "Skip all disclosure questions"
- "Focus only on revenue recognition"
- "Only check presentation requirements"

**What happens:**

- `filterParser.parseFilterFromText()` extracts keywords/phrases
- `POST /api/questions/filter` → semantic search over question index
- Returns `excludedQuestionIds[]` — questions that don't match the filter
- These questions are skipped during analysis (status: "Filtered")

**Why?**

A full IAS 1 checklist has 216 questions. If the user only cares about "statement of financial position" presentation, they can filter down to ~30 relevant questions, saving 80% of analysis time and API cost.

**Transition**: → `ANALYZING_SEQUENCE_1`

---

### Step 9: Compliance Analysis (The Main Event)

**What the user sees:**

Live progress bar + streaming messages in chat:

```text
"Analyzing IAS 7 (batch 1/3)..."
"✓ IAS 7 Q106: YES (confidence: 0.92)"
```

**What happens (the full analysis pipeline):**

#### A. Question Loading

For each selected standard:

- `GET /api/checklist/:standard`
- Tries Enhanced Decision Tree first (`data/checklists/Enhanced Framework/IFRS_decisiontree/<standard>.json`)
- Falls back to base IFRS (`data/checklists/IFRS/<standard>.json`)
- Extracts all `ComplianceQuestion` items from sections

#### B. Two-Phase Analysis

**SEQUENCE 1 — Source + Independent Questions:**

Questions are grouped by: `${standard}|${context_required}` (e.g., `"IAS 7|notes_only"`, `"IAS 7|financial_statements"`, `"IFRS 16|full"`)

**Why group by context?**

Questions needing only notes don't need the Financial Statements text. Questions needing only FS numbers don't need note disclosures. Grouping prevents sending 200K chars of irrelevant content per question.

For each group:

1. Questions split into batches of 5
2. Up to 6 batches run in parallel (6 workers, one per AI endpoint)
3. Workers staggered by 5 seconds (Azure Search rate limit protection)

**Per batch:**

1. **BUILD CONTEXT** (`buildContextWithAzureSearch`):
   - If `context_required = "financial_statements"`: Raw FS text sent directly (no search needed for numbers)
   - If `context_required = "notes_only"`: Azure AI Search: 30 chunks per question, filtered by `documentHash`. Deduplication by 200-char prefix. Minimum relevance score: 0.3. Builds "RELEVANT DISCLOSURE NOTES" text
   - If `context_required = "full"`: Raw FS + Azure Search notes (proportionally allocated within 200K limit)

2. **ANALYZE BATCH** (`analyzeBatch` → GPT-5.2/5.1 with GPT-4o fallback):

   **Prompt Structure:**

   ```text
   ┌─ System: "You are an IFRS compliance expert..."
   ├─ Anti-hallucination protocol (7 rules)
   ├─ User instructions (highest priority override)
   ├─ Company metadata context
   ├─ Document content (FS and/or notes — from context build)
   ├─ Chain of Thought instructions (single tree-driven engine):
   │   Step 1: Identify EXACTLY which standard paragraph applies
   │   Step 2: Search for SPECIFIC evidence in the document
   │   Step 3: TREE WALK — walk through decision tree CHECKPOINTs
   │           (each node answered YES/NO, reach a COMPLIANT: leaf)
   │   Step 4: Plain-language conclusion
   │   STATUS: Must match the COMPLIANT: leaf from Step 3
   │   SELF_CHECK: "Does my STATUS match my STEP_3 tree leaf
   │               AND my STEP_4 conclusion? If NO, fix STATUS."
   ├─ Decision tree for each question (formatted as CHECKPOINTs):
   │   CHECKPOINT 1: [question]
   │       ↳ [guidance]
   │       → IF YES: [next node or COMPLIANT: YES/NO/N/A]
   │       → IF NO: [next node or COMPLIANT: YES/NO/N/A]
   ├─ Perfect/Poor answer examples (STATUS placed AFTER reasoning)
   ├─ Questions block (up to 5 questions)
   └─ Response format: ===RESULT_START=== ... ===RESULT_END===
   ```

   **AI Response Fields:**

   | Field | Description |
   | ----- | ----------- |
   | `ID` | question identifier |
   | `STEP_1_REQUIREMENT` | identify the requirement |
   | `STEP_2_SEARCH` | search for evidence |
   | `STEP_3_TREE_WALK` | walk decision tree checkpoints, reach leaf |
   | `STEP_4_CONCLUSION` | plain language determination |
   | `STATUS` | YES / NO / N/A (must match tree leaf COMPLIANT: value, NOT the factual answer to the screening question) |
   | `SELF_CHECK` | verification that STATUS matches tree walk + conclusion |
   | `CONFIDENCE` | 0.0–1.0 |
   | `EXPLANATION` | detailed analysis text |
   | `EVIDENCE_ITEMS` | structured evidence with page references |
   | `SUGGESTED_DISCLOSURE` | fix language if non-compliant |
   | `DATA_NEEDED` | what additional data would help (for re-search) |

   > **CRITICAL DESIGN**: STATUS is placed AFTER `STEP_4_CONCLUSION` in the template, NOT at the top. This prevents the AI from answering the screening question literally (e.g., "Does entity hold inventories?" → NO) instead of giving the compliance conclusion from the tree leaf. Examples in the prompt also show STATUS after reasoning.

   **Model Parameters:**

   - Temperature: 0.0 (deterministic — no creativity)
   - Max tokens: 16,384
   - Model: GPT-5.2/GPT-5.1 (round-robin across 6 endpoints)
   - Fallback: GPT-4o (6 endpoints) → GPT-4o-mini (6 endpoints) on 429

3. **VALIDATE RESULT** (`validateAnalysisResult`):

   Anti-hallucination validation rules:

   | Rule | Description |
   | ---- | ----------- |
   | Rule 1 | YES without evidence → confidence capped at 0.2 |
   | Rule 1b | YES with empty/placeholder evidence → confidence 0.3 |
   | Rule 2 | Evidence without page references → warning flag |
   | Rule 3 | Short evidence (<50 chars) → critical warning |
   | Rule 3b | Generic/hallucinated phrases detected → confidence cap |
   | Rule 3c | YES + no numbers AND no financial terms → warning |
   | Rule 4 | REMOVED — suspicious number rule caused false positives |
   | Rule 5 | N/A without justification → checks 40+ domain-specific patterns (e.g., "does not hold", "no subsidiaries", "exempt from", "not a financial institution", etc.). Also accepts any explanation ≥100 chars as sufficient. |
   | Rule 6 | SIMPLIFIED — only flags confidence < 0.3 (removed the redundant YES+no-evidence check that conflicted with Rule 1) |
   | Rule 7 | Empty suggested disclosure → auto-populated |

4. **APPLY AUTO-CORRECTION** (`applyAutoCorrectionIfNeeded`):

   If user previously reviewed and corrected this question for a similar document, the correction is applied automatically. Source: `question_learning_data` table.

5. **RE-SEARCH** (if needed):

   If a question set `needsReSearch=true` and provided `dataNeeded`, the system does up to 2 additional search iterations with alternative keywords to find missing evidence.

**SEQUENCE 2 — Followup Questions:**

After all source questions are answered, followups are evaluated.

How followups work:

- Source question "117" asks: "Did entity obtain control of subsidiaries?"
- If source answered YES → followups 118.1, 118.2, 118.3 are TRIGGERED
- If source answered NO → followups get status N/A (skipped)

`source_trigger` field: "Yes" or "No" — the answer value that triggers the followup. Only triggered followups are analyzed with AI.

**Why two sequences?**

Followup questions depend on source answers. You can't ask "What is the acquisition cost?" (followup) without first knowing "Did the entity make an acquisition?" (source). Sequential processing ensures correct conditional logic.

#### C. Results Streaming

During analysis, results stream to the client via NDJSON:

- `{ type: 'heartbeat' }` — every 15s, keeps connection alive
- `{ type: 'progress', phase: 'sequence_1', percentage: 45 }`
- `{ type: 'partial', completed: 23, total: 50 }`
- `{ type: 'complete', data: finalResult }`

Simultaneously, WebSocket broadcasts:

- `{ type: 'partial_results', jobId, data }` — for real-time UI updates

Both channels are used because NDJSON gives guaranteed delivery while WebSocket gives lower latency (but may drop on reconnect).

#### D. Results Persistence

After analysis completes:

- `POST /api/results` → saves to `analysis_results` table → returns `resultId`
- `PUT /api/sessions` → updates session with compliance results
- Results also cached in `cached_analysis_results` for future re-runs
- Per-question progress saved in `analysis_progress` table (for resume)

**Transition**: → `ANALYSIS_COMPLETE`

---

### Step 10: Results & Reporting

**What the user does:**

Clicks "View Results" → sees full compliance report.

**ResultsPage displays:**

```text
┌──────────────────────────────────────────────────────────────────┐
│ TABS: one per selected standard (IAS 1 | IAS 7 | IFRS 16 | ...) │
│ FILTER BAR: All | Compliant | Non-Compliant | N/A | Errors      │
│ STATS: 45 Total | 32 ✓ | 8 ✗ | 5 N/A | 71% compliance rate    │
├──────────────────────────────────────────────────────────────────┤
│ For each question:                                               │
│   Reference: IAS 7.18(b)                                        │
│   Status: [YES] / [NO] / [N/A] with color badge                │
│   Confidence: [████████░░] 82%                                  │
│   Question: "Has the entity presented cash flows from..."       │
│                                                                  │
│   ▼ EXPANDED:                                                   │
│   Analysis: "The entity has presented cash flows from operating  │
│             activities using the indirect method, as evidence..." │
│   Evidence Table:                                                │
│     | Reference | Requirement | Page | Extract | Analysis |     │
│   Suggested Disclosure: "Consider adding a reconciliation of..." │
│   Enhancement Recommendations: "Best practice suggests also..." │
│                                                                  │
│   [Reassess Single] [Manual Override] [View Context]            │
└──────────────────────────────────────────────────────────────────┘
```

**Interactive capabilities:**

1. **Single Reassessment**: User provides instructions ("Look in Note 13") → `POST /api/process/re-analyze` → AI re-checks with focused search → Shows audit trail: original answer vs reassessed answer

2. **Bulk Reassessment**: Select multiple questions via checkboxes → Provide common instructions → batch re-analyze

3. **Manual Override**: Change YES→NO or vice versa → Required: free-text reason explaining why → Tracked as `originalStatus` + `userReason`

4. **Context Viewer**: See exact chunks sent to AI → Tabbed by context type (`notes_only` / `financial_statements` / `full`) → Helps user verify: "Did the AI see the right content?"

5. **Financial Insights Chatbot**: Floating button opens AI chatbot → Can ask any question about the document → Uses same Azure Search index for retrieval → Returns answers with citations `[Page X, Section Y]`

6. **Export**: PDF / DOCX / JSON → Professional formatted compliance report → Includes: company header, standard sections, question details, evidence, recommendations, compliance rate summary

7. **Sharing**: Generates shareable URL via `savedResultId` → `GET /api/results/:id` → anyone with the link can view results

---

### Step 11: Session Persistence & Resume

Every workflow state is auto-saved. Users can:

- Close the browser and return → session restored from DB
- Switch between sessions → left panel session list
- Resume interrupted analysis → `POST /api/jobs/:id/resume` → Uses `analysis_progress` table to find completed questions → Only re-analyzes pending/failed questions → Merges with existing results

**Why?**

A full compliance analysis takes 4-8 minutes. If the browser crashes at minute 6, the user shouldn't lose everything. Per-question progress tracking + session persistence ensures at most one batch (~5 questions) of work is lost.

---

## 3. System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BROWSER (React + Vite)                           │
│                                                                             │
│  App.tsx                                                                    │
│  ├── SessionPanel (left)     — Session list, create/select/delete          │
│  ├── ChatInterface (center)  — Main workflow, file upload, live analysis   │
│  └── AnalysisPanel (right)   — Metadata editor, standards picker, progress │
│                                                                             │
│  useComplianceWorkflow.ts    — State machine (20 states)                   │
│  apiService.ts               — All HTTP calls to backend                   │
│  useWebSocket.ts             — WebSocket connection manager                │
│  filterParser.ts             — NLP instruction → filter criteria           │
└─────────────┬───────────────────────────────────────────────────────────────┘
              │ HTTP + WebSocket
              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     EXPRESS SERVER (dev-server.js / production-server.js)    │
│                                                                             │
│  47 API endpoints                                                           │
│  ├── /api/jobs/*             — Job creation & tracking                      │
│  ├── /api/process/*          — Processing pipeline (extract, metadata,      │
│  │                             index, analyze, re-analyze, validate)        │
│  ├── /api/checklist/*        — Checklist loading (Enhanced DT → base IFRS)  │
│  ├── /api/results/*          — Results persistence                          │
│  ├── /api/sessions           — Session CRUD                                │
│  ├── /api/chat/*             — Financial insights chatbot                   │
│  ├── /api/azure/*            — Azure Search management                      │
│  ├── /api/health             — Service health                              │
│  └── /ws                     — WebSocket for real-time updates             │
│                                                                             │
│  Services:                                                                  │
│  ├── complianceService.js    — Analysis engine (2675 lines)                │
│  ├── azureSearchService.js   — Search + chunk queries (1515 lines)         │
│  ├── targetedIndexOrchestrator.js — Chunking + indexing (941 lines)        │
│  ├── azureOpenAIClient.js    — Multi-region AI client (849 lines)          │
│  ├── documentExtractionService.js — Azure Doc Intelligence wrapper         │
│  ├── metadataService.js      — AI metadata extraction                      │
│  ├── complianceJobService.js — Job orchestration + resume                  │
│  ├── progressTrackingService.js — Per-question progress                    │
│  ├── resultCacheService.js   — Analysis result caching                     │
│  ├── fsValidationService.js  — FS completeness validation                  │
│  └── multiModelClient.js     — AI model abstraction                        │
└──────┬──────────┬──────────┬──────────┬────────────────────────────────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ Azure    │ │ Azure    │ │ Azure    │ │ Neon         │
│ OpenAI   │ │ AI Search│ │ Doc Int  │ │ PostgreSQL   │
│          │ │          │ │          │ │              │
│ GPT-5.2  │ │ Semantic │ │ PDF/DOCX │ │ sessions     │
│ GPT-5.1  │ │ + vector │ │ → text   │ │ results      │
│ GPT-4o   │ │ search   │ │ + tables │ │ progress     │
│ GPT-4o-  │ │          │ │          │ │ cache        │
│ mini     │ │ Index:   │ │ Layout   │ │ learning     │
│          │ │ 500-char │ │ analysis │ │ conversations│
│ 18 endpts│ │ chunks   │ │ OCR      │ │              │
│ 3 tiers  │ │          │ │          │ │              │
└──────────┘ └──────────┘ └──────────┘ └──────────────┘
```

---

## 4. Frontend State Machine (20 States)

20 states defined in `types.ts` `AppState` enum:

| # | State | User Action Required |
| --- | --- | --- |
| 1 | `AWAITING_UPLOAD` | Upload 2 files (FS + Notes) |
| 2 | `PROCESSING_DOCUMENT` | Wait — extracting & indexing |
| 3 | `REVIEWING_EXTRACTION` | Review extraction (legacy single-file) |
| 4 | `AWAITING_METADATA_CONFIRMATION` | Review/edit metadata → Confirm |
| 5 | `AWAITING_FRAMEWORK_SELECTION` | Pick framework (IFRS/US GAAP/etc.) |
| 6 | `AWAITING_CUSTOM_FRAMEWORK_SELECT` | Pick custom framework |
| 7 | `AWAITING_TAXONOMY_UPLOAD` | Upload custom taxonomy (disabled) |
| 8 | `UPLOADING_TAXONOMY` | Wait — processing taxonomy |
| 9 | `SUGGESTING_STANDARDS` | Wait — AI suggesting standards |
| 10 | `AWAITING_STANDARDS_CONFIRMATION` | Review/edit standards → Confirm |
| 11 | `AWAITING_VALIDATION_APPROVAL` | Approve or skip chunk revalidation |
| 12 | `VALIDATION_IN_PROGRESS` | Wait — AI revalidating chunks |
| 13 | `PREVIEWING_INDEXED_CONTENT` | Review chunks → Proceed or Back |
| 14 | `TAGGING_NOTES` | Wait — tagging notes (legacy) |
| 15 | `AWAITING_INSTRUCTIONS` | Enter filter text → Start analysis |
| 16 | `ANALYZING_SEQUENCE_1` | Wait — source questions being analyzed |
| 17 | `ANALYZING_SEQUENCE_2` | Wait — followup questions analyzed |
| 18 | `GENERATING_REPORT` | Wait — finalizing |
| 19 | `ANALYSIS_COMPLETE` | View Results / Add More Standards |
| 20 | `VIEWING_REPORT` | Results page (reassess/override/export) |

**Happy Path (minimum clicks):**

```text
AWAITING_UPLOAD → PROCESSING_DOCUMENT → AWAITING_METADATA_CONFIRMATION
→ AWAITING_FRAMEWORK_SELECTION → SUGGESTING_STANDARDS
→ AWAITING_STANDARDS_CONFIRMATION → AWAITING_VALIDATION_APPROVAL
→ PREVIEWING_INDEXED_CONTENT → AWAITING_INSTRUCTIONS
→ ANALYZING_SEQUENCE_1 → ANALYZING_SEQUENCE_2
→ ANALYSIS_COMPLETE → VIEWING_REPORT
```

**Key functions in `useComplianceWorkflow.ts` (2392 lines):**

| Function | Line | Purpose |
| --- | --- | --- |
| `handleDualFiles()` | ~1321 | File upload → extract → metadata → index |
| `handleMetadataConfirm()` | ~1602 | Confirm metadata |
| `handleFrameworkSelect()` | ~1624 | Select framework → trigger suggestion |
| `handleStandardsConfirm()` | ~1899 | Confirm standards → validation preview |
| `handleValidationApproval()` | ~1956 | Approve/skip chunk revalidation |
| `proceedFromChunkPreview()` | ~1569 | Proceed to instructions |
| `handleInstructionsConfirm()` | ~2001 | Parse filter → start analysis |
| `startComplianceAnalysis()` | ~1696 | Core: load checklists → analyze → save |
| `handleJobUpdate()` | ~873 | WebSocket: process progress updates |
| `handleViewResults()` | ~2077 | Navigate to /results |
| `handleSelectSession()` | ~2189 | Restore session from DB |
| `handleCancelAnalysis()` | ~2309 | Abort running analysis |

---

## 5. Backend API Endpoints (47 Endpoints)

All endpoints defined in `dev-server.js` (1855 lines).

### Job Orchestration

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/jobs` | Create tracking job |
| GET | `/api/jobs/:jobId/status` | Get job status |
| GET | `/api/jobs/:jobId/progress` | Get per-question progress |
| POST | `/api/jobs/:jobId/resume` | Resume failed/interrupted job |

### Processing Pipeline

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/process/extract-azure-dual` | Extract 2 files (FS + Notes) via Azure DI |
| POST | `/api/process/extract-azure` | Extract single file (legacy) |
| POST | `/api/process/ai-pipeline` | REMOVED — returns 410 Gone |
| POST | `/api/process/metadata` | Extract company metadata (AI + search) |
| POST | `/api/process/validate-financials` | Validate FS completeness |
| POST | `/api/process/suggest-standards` | AI suggests applicable standards |
| POST | `/api/process/index-document` | Index chunks to Azure AI Search |
| POST | `/api/process/tag-notes` | DEPRECATED — returns 410 |
| POST | `/api/process/validation-preview` | Preview chunk counts per standard |
| POST | `/api/process/query-chunks` | Query indexed chunks |
| POST | `/api/process/revalidate-chunks` | AI re-validate chunk-standard tags |
| POST | `/api/process/analyze` | MAIN: Full compliance analysis (NDJSON) |
| POST | `/api/process/re-analyze` | Focused re-analysis with keyword extract |

### Chunk Management

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/chunks/preview` | Fetch document chunks with filters |

### Azure Search Management

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/azure/index-document` | DEPRECATED — 410 Gone |
| POST | `/api/azure/tag-notes` | DEPRECATED — 410 Gone |
| POST | `/api/azure/search` | DEPRECATED — 410 Gone |
| POST | `/api/azure/index-questions` | Index checklist questions for filtering |
| POST | `/api/azure/search-questions` | Search question index (for NLP filter) |
| DELETE | `/api/azure/delete-index/:type` | Delete Azure Search index |
| POST | `/api/azure/index-all-questions` | Index all 39 IFRS checklists |

### Data Access

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/checklist/:standard` | Load checklist (Enhanced DT → base IFRS) |
| GET | `/api/taxonomy` | Get IFRS taxonomy concept index |
| GET | `/api/custom-frameworks` | List custom framework directories |
| GET | `/api/custom-framework-standards/:f` | List standards in custom framework |
| GET | `/api/custom-checklist/:f/:s` | Load custom framework checklist |
| POST | `/api/upload-taxonomy` | NOT IMPLEMENTED — 501 |

### Results Persistence

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/results` | Save analysis results to DB |
| GET | `/api/results/:id` | Retrieve saved results |

### Question Filtering

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/questions/index` | Index all questions for semantic filter |
| GET | `/api/questions/status` | Check question index status |
| POST | `/api/questions/filter` | Filter questions by keywords/semantics |

### Financial Insights Chatbot

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/financial-insights` | Query document with AI + citations |
| POST | `/api/chat/conversations` | Create conversation |
| GET | `/api/chat/conversations/:id` | Get conversation history |
| GET | `/api/chat/conversations` | List conversations |
| DELETE | `/api/chat/conversations/:id` | Delete conversation |
| POST | `/api/chat/conversations/:id/msgs` | Send message (SSE streaming) |

### Health

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/health` | Full health check (Azure services + DB) |
| GET | `/health` | Simple "OK" text response |
| GET | `/_health` | JSON health response |
| GET | `/health/providers` | Provider status details |

### Debug

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/debug/search-test` | Test Azure Search connectivity |

### WebSocket

| Method | Endpoint | Description |
| --- | --- | --- |
| WS | `/ws` | Real-time job/session updates |

---

## 6. AI/Search Service Layer

### Azure OpenAI Client (`azureOpenAIClient.js`, 849 lines)

**Deployment Strategy:**

| Stage | Model(s) |
| --- | --- |
| Compliance Analysis | 3x GPT-5.2 + 3x GPT-5.1 (round-robin) |
| Fallback/Tagging | GPT-4o pool (if `ENDPOINT_GPT4O_*` set) |
| Fast Operations | GPT-4o-mini (via `PRIMARY_CONFIG` fallback) |

**Architecture Note:** GPT-5.2 and GPT-5.1 are same-tier substitutes (GPT-5.1 used because Azure quota limits prevented 6x GPT-5.2). Each deployment has its own rate limit quota → 6 truly parallel pipelines. 3 Azure resources × 2 deployments each = 6 independent compliance slots.

**Fallback chain per pipeline on 429:**

Primary (GPT-5.2 or GPT-5.1) → GPT-4o (6 resources) → GPT-4o-mini (6 resources)

**Pool Architecture:**

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ COMPLIANCE POOL (6 endpoints, round-robin)                              │
│                                                                         │
│  Slot 1: GPT-5.2 #1 (AZURE_OPENAI_ENDPOINT_GPT52_1)                   │
│  Slot 2: GPT-5.2 #2 (AZURE_OPENAI_ENDPOINT_GPT52_2)                   │
│  Slot 3: GPT-5.2 #3 (AZURE_OPENAI_ENDPOINT_GPT52_3)                   │
│  Slot 4: GPT-5.1 #1 (AZURE_OPENAI_ENDPOINT_GPT51_1)                   │
│  Slot 5: GPT-5.1 #2 (AZURE_OPENAI_ENDPOINT_GPT51_2)                   │
│  Slot 6: GPT-5.1 #3 (AZURE_OPENAI_ENDPOINT_GPT51_3)                   │
│                                                                         │
│  Merged via getNextComplianceRegion() — round-robin across all 6        │
│  On 429 from any slot → GPT-4o pool → GPT-4o-mini pool                 │
└──────────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────────┐
│ GPT-4o FALLBACK POOL (6 endpoints)                                      │
│  AZURE_OPENAI_ENDPOINT_GPT4O_{1..6}, deployment: gpt-4o                │
│  Used for: 429 fallback from GPT-5.x, tagging, quality operations      │
└──────────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────────┐
│ GPT-4o-MINI FAST POOL (6 endpoints)                                     │
│  AZURE_OPENAI_ENDPOINT_MINI_{1..6}, deployment: gpt-4o-mini            │
│  Used for: final 429 fallback, metadata, sanitize, chat, standards      │
└──────────────────────────────────────────────────────────────────────────┘
```

**Retry/Backoff Config:**

| Parameter | Value |
| --- | --- |
| `maxAttempts` | 3 (initial + 2 retries) |
| `baseDelayMs` | 1000 → exponential ×2 → cap 20000ms |
| Jitter | full random (`Math.random() × exponentialDelay`) |
| Retryable codes | 408, 409, 423, 429, 500, 502, 503, 504 |
| Network errors | ECONNRESET, ETIMEDOUT, ENOTFOUND, ECONNREFUSED |
| Overall timeout | 300000ms (5 minutes) via AbortController |
| Per-request timeout | 120000ms (2 minutes) |

**Model Parameters:**

| Parameter | GPT-5.2/5.1 | GPT-4o/4o-mini |
| --- | --- | --- |
| temperature | 0.0 (compliance) | 0.2 (default) |
| max tokens | `max_completion_tokens`: 16384 | `max_tokens`: 16384 |
| API version | 2024-10-21 | 2024-10-21 |

> **NOTE**: GPT-5.x requires `max_completion_tokens` (NOT `max_tokens`).

**Key functions:**

- `generateCompletionWithGPT5(prompt, options)` — Round-robins across 6 compliance endpoints (3x GPT-5.2 + 3x GPT-5.1). On 429 → falls back to GPT-4o pool → GPT-4o-mini pool. Used ONLY for compliance analysis (`analyzeBatch`).

- `generateCompletionWithAzureOpenAI(prompt, deploymentName, options)` — Generic function with full retry/backoff loop. Used by `multiModelClient.js` for non-compliance operations.

- `generateWithFallback(prompt, options)` [in `multiModelClient.js`, 90 lines] — Thin wrapper routing by operation type:
  - `'fast'`/`'sanitize'`/`'metadata'`/`'standards'`/`'chat'` → gpt-4o-mini
  - `'quality'`/`'tagging'` → gpt-4o
  - `'default'` → gpt-4o-mini
  - Used for ALL non-compliance AI calls
  - Compliance analysis BYPASSES this and calls `generateCompletionWithGPT5()` directly

### Azure Search Service (`azureSearchService.js`, 1515 lines)

**Indexing:**

- `calculateDocumentHash(fs, notes)` → SHA-256, 12-char prefix
- `indexFinancialDocument(fs, notes, metadata)` →
  1. Ensure index exists (25+ fields, semantic config, scoring profiles)
  2. Delete ALL previous chunks for this document
  3. Chunk: 500-char chunks, 100-char overlap
  4. Tag each chunk with: IFRS concepts, standards, `section_type`, `statement_type`, `line_item_category`, `page_number`
  5. Upload to Azure AI Search

**Searching:**

- `searchRelevantContent(query, documentHash, options)` →
  1. Always filter by `documentHash` (document isolation)
  2. Optional: `section_type` filter (notes/FS/both)
  3. Optional: `fiscal_year` filter
  4. Semantic search mode with `financial-semantic-config`
  5. 3 retries with exponential backoff for 503 throttling
  6. Returns: `[{ content, sectionType, pageNumber, score, ... }]`

- `hybridSearchWithRRF(query, documentHash)` →
  - Runs BOTH semantic + keyword searches in parallel
  - Merges via Reciprocal Rank Fusion: `RRF_score = Σ(1/(k+rank))`, k=60

**Scoring Profile:**

| Field | Weight |
| --- | --- |
| `ifrs_concepts` | 12 (highest — exact taxonomy match) |
| `statement_type` | 10 |
| `taxonomy_keywords` | 8 |
| `line_item_category` | 6 |
| `section_name` | 4 |
| `content` | 1 (lowest — full text is baseline) |

### Compliance Service (`complianceService.js`, 2741 lines)

**Constants:**

| Constant | Value |
| --- | --- |
| `BATCH_SIZE` | 5 questions per AI call |
| `MAX_WORKERS` | 6 parallel workers |
| `WORKER_STAGGER_DELAY_MS` | 5000ms between worker starts |
| `MAX_CONTEXT_CHARS` | 200,000 (~50K tokens) |
| `MIN_RELEVANCE_SCORE` | 0.3 |

**Main Function: `analyzeCompliance()`**

1. Filter excluded questions (from semantic filter)
2. Check result cache (`documentHash` + `framework` + `questionsHash`)
3. Clear search cache (prevent cross-job contamination)
4. Build metadata context string
5. Load learning data (from previous user corrections)
6. GROUP questions by `${standard}|${context_required}`

**Context Routing (`context_required` field):**

| Value | Behavior |
| --- | --- |
| `"financial_statements"` | Raw FS text only (no search needed) |
| `"notes_only"` | Azure Search chunks only (30 per Q) |
| `"full"` | Raw FS + Azure Search notes |

**Analysis Prompt (`analyzeBatch`) — Single Tree-Driven Engine:**

- System: IFRS domain expertise + anti-hallucination protocol
- Context: Company metadata + document content
- Method: 4-step Chain of Thought with decision tree CHECKPOINT walk:
  `STEP_1_REQUIREMENT` → `STEP_2_SEARCH` → `STEP_3_TREE_WALK` → `STEP_4_CONCLUSION` → `STATUS` (placed AFTER conclusion, must match tree leaf) → `SELF_CHECK` (verify STATUS matches tree walk + conclusion)
- Decision trees formatted as CHECKPOINTs with → arrows (not nested JSON)
- Examples show STATUS AFTER reasoning (prevents screening-question inversion)
- Format: Structured `===RESULT_START===...===RESULT_END===` blocks
- AI Model: GPT-5.2/5.1 (temp=0.0, `max_completion_tokens`=16384)

**Response Parsing:**

- **STATUS extraction**: Uses `matchAll` + `pop` → takes LAST STATUS match (AI may emit STATUS before and after reasoning; the post-reasoning STATUS is authoritative)
- **Tree walk correction**: Extracts `COMPLIANT: YES/NO/N/A` from `STEP_3_TREE_WALK`. If STATUS disagrees with tree leaf → tree leaf wins. This is a post-parse safety net; tree walk is always authoritative over the STATUS field.
- **Status normalization**: Strips "COMPLIANT:" prefix, handles YES/NO/N/A

**Post-Processing:**

- `validateAnalysisResult()` — anti-hallucination rules (see Step 9 above)
- `applyAutoCorrectionIfNeeded()` — learning data override
- Re-search loop — 2 iterations for missing evidence

**Decision Tree Formatting (`formatDecisionTreeCompact`):**

- Input: Nested JSON tree with `question`/`guidance`/`yes_case`/`no_case`
- Output: Flat CHECKPOINT format with arrows:

```text
CHECKPOINT 1: [question]
    ↳ [guidance]
   → IF YES: [next or COMPLIANT: YES/NO/N/A]
   → IF NO: [next or COMPLIANT: YES/NO/N/A]
CHECKPOINT 2: ...
```

This replaces the old "STEP N" format and makes tree navigation explicit.

---

## 7. Checklist & Decision Tree Structure

### File Structure

**Enhanced Decision Tree checklists:**

```text
data/checklists/Enhanced Framework/IFRS_decisiontree/
  IAS 1.json   (216 questions)
  IAS 7.json   (45 questions)
  IFRS 16.json (48 questions)
  ... (44 files total, 1752 questions combined)
```

**Base IFRS checklists (fallback):**

```text
data/checklists/IFRS/
  IAS 1.json, IAS 7.json, ... (44 files, 1849 questions)
```

Loading: `GET /api/checklist/:standard` tries Enhanced DT first, falls back to base.

### JSON Structure

```json
{
  "title": "International GAAP® Disclosure Checklist",
  "version": "1.0",
  "sections": [{
    "section": "IAS 7",
    "title": "Statement of Cash Flows",
    "description": "Checklist for...",
    "items": [
      {
        "id": "106",
        "section": "IAS 7",
        "reference": "IAS 7.10",
        "question": "Has the entity presented a statement of cash flows?",
        "original_question": "An entity shall prepare a statement of cash flows in accordance with the requirements of this Standard...",
        "question_type": null,
        "source_question": null,
        "source_trigger": null,
        "context_required": "financial_statements",
        "decision_tree": {
          "question": "Is a cash flow statement presented?",
          "guidance": "Look for a statement titled 'Cash Flow Statement' or 'Statement of Cash Flows' in the financial statements.",
          "yes_case": "COMPLIANT: YES",
          "no_case": {
            "question": "Are there specific exemptions that apply?",
            "guidance": "Check if the entity qualifies for exemptions...",
            "yes_case": "COMPLIANT: N/A",
            "no_case": "COMPLIANT: NO"
          }
        }
      },
      {
        "id": "117",
        "question_type": "Source",
        "question": "Did the entity obtain control of any subsidiaries?",
        "...": "..."
      },
      {
        "id": "118.1",
        "question_type": "Followup",
        "source_question": "117",
        "source_trigger": "Yes",
        "question": "Has the entity disclosed the consideration paid?",
        "...": "..."
      }
    ]
  }]
}
```

### Decision Tree Structure

Each question has a nested decision tree the AI traverses:

```text
DecisionTreeNode {
  question: string       — What to evaluate
  guidance: string       — How to evaluate (detailed instructions for AI)
  yes_case: Node|string  — Next node if YES, or terminal outcome
  no_case:  Node|string  — Next node if NO, or terminal outcome
}
```

**Terminal strings (direct compliance mapping):**

| Leaf Value | Maps To |
| --- | --- |
| `"COMPLIANT: YES"` | status = YES (compliant) |
| `"COMPLIANT: NO"` | status = NO (non-compliant) |
| `"COMPLIANT: N/A"` | status = N/A (not applicable) |

> **Historical Note:** Prior to commit `787ed45`, leaf nodes used inverted wording: "Raises compliance issue: YES" → meant NON-compliant (confusing), "Raises compliance issue: NO" → meant COMPLIANT (confusing), "Not Applicable" → meant N/A. All 6,315 leaf nodes across 44 Enhanced Decision Tree JSON files were rewritten to use direct `COMPLIANT:` vocabulary: "Raises compliance issue: YES" → `"COMPLIANT: NO"` (2,312 nodes), "Raises compliance issue: NO" → `"COMPLIANT: YES"` (2,107 nodes), "Not Applicable" → `"COMPLIANT: N/A"` (1,893 nodes).

**Tree depth**: 2–5 levels depending on question complexity. Deepest trees: IAS 7 tax classification questions (5 levels).

### Two-Phase Source/Followup Logic

**SEQUENCE 1**: All questions with `question_type` = `null`, `"Source"`, or `"Independent"` → Processed with full AI analysis

**SEQUENCE 2**: All questions with `question_type` = `"Followup"` → Check: does the source question's final status match `source_trigger`?

- YES → process with full AI analysis
- NO → skip, assign status = N/A, explanation = "Not triggered"

**Example:**

```text
Q117 (Source): "Did entity obtain control of subsidiaries?" → AI says YES
  Q118.1 (Followup, trigger=Yes): "Disclosed consideration?" → TRIGGERED → AI analyzes
  Q118.2 (Followup, trigger=Yes): "Disclosed assets acquired?" → TRIGGERED → AI analyzes

If Q117 had answered NO:
  Q118.1: status=N/A (skipped — trigger not met)
  Q118.2: status=N/A (skipped — trigger not met)
```

---

## 8. Data Types & Interfaces

### ComplianceQuestion (template before analysis)

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Question identifier |
| `section` | string | e.g., "IAS 7" |
| `reference` | string | e.g., "IAS 7.18(b)" |
| `question` | string | Simplified question text |
| `original_question` | string? | Full verbatim requirement from standard |
| `decision_tree` | DecisionTreeNode? | Nested yes/no tree |
| `question_type` | `'Source'`\|`'Followup'`\|`'Independent'`\|`null` | Question classification |
| `source_question` | string\|null | ID of parent source question |
| `source_trigger` | `'Yes'`\|`'No'`\|`null` | What triggers this followup |
| `context_required` | `'full'`\|`'notes_only'`\|`'financial_statements'` | Context routing |
| `applicability_condition` | string? | Pre-condition for applicability |

### ComplianceItem (extends ComplianceQuestion with results)

| Field | Type | Description |
| --- | --- | --- |
| `status` | `'YES'`\|`'NO'`\|`'N/A'`\|`'Error'` | Compliance result |
| `confidence` | number | 0.0–1.0 |
| `explanation` | string | AI analysis text |
| `evidence` | EvidenceItem[] | Structured evidence |
| `suggestedDisclosure` | string | Fix language |
| `recommendations` | string? | Enhancement suggestions |
| `chunksUsed` | string? | Context chunks sent to AI |
| `needsReview` | boolean? | Validation flag |
| `validationIssues` | string[]? | What validation caught |
| `wasReassessed` | boolean? | Re-analysis flag |
| `originalStatus` | string? | Before reassessment/override |
| `originalExplanation` | string? | Before reassessment |
| `originalEvidence` | EvidenceItem[]? | Before reassessment |
| `userReason` | string? | Manual override reason |
| `systemError` | boolean? | Error flag |

### EvidenceItem

| Field | Type | Description |
| --- | --- | --- |
| `reference` | string | Paragraph reference (e.g., "IAS 7.18") |
| `requirement` | string | What the standard requires |
| `description` | string | What was found |
| `pageNumber` | number\|null | Page in source document |
| `extract` | string | Exact quoted text |
| `contentAnalysis` | string | AI's analysis of the evidence |

### Metadata

| Field | Type | Description |
| --- | --- | --- |
| `companyName` | string | Company name |
| `currentReportingYear` | string | e.g., "2024" |
| `comparativeYear` | string | e.g., "2023" |
| `reportingCurrency` | string | e.g., "GBP" |
| `basisOfPreparation` | string | e.g., "IFRS" |
| `industry` | string | Industry sector |
| `entityType` | string | Entity classification |
| `listingStatus` | string | Listed/unlisted |
| `consolidation` | string | Consolidated/standalone |
| `goingConcern` | string | Going concern status |
| `companyAddress` | object | Address details |
| `accountingPolicies` | object | Policy summaries |
| `documentId` | string | Document identifier |
| `documentHash` | string | 12-char SHA-256 prefix |

### Session

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Session ID |
| `sessionName` | string | Display name |
| `documentName` | string | Source document name |
| `documentId` | string | Document identifier |
| `currentState` | AppState | Workflow state |
| `framework` | string | Selected framework |
| `selectedStandards` | string[] | Selected standards |
| `metadata` | Metadata | Confirmed metadata |
| `complianceResults` | ComplianceItem[] | Analysis results |
| `chatMessages` | ChatMessage[] | Conversation history |
| `extractedContent` | object | `{ financialStatements, notesToAccounts }` |
| `createdAt`, `updatedAt` | Date | Timestamps |

---

## 9. Database Schema & Storage

**Database**: Neon PostgreSQL (via Drizzle ORM)
**Schema**: `shared/schema.ts`

### Tables (7 total)

#### 1. `analysis_results`

**Purpose**: Final persisted analysis results (for sharing/retrieval)

**Columns**: `id`, `metadata` (jsonb), `complianceItems` (jsonb), `reportData` (jsonb), `framework`, `documentName`, `createdAt`

#### 2. `cached_analysis_results`

**Purpose**: Speed cache — avoid re-analyzing same document+standards

**Key**: `documentHash` + `framework` + `questionsHash` (composite)

**Columns**: `documentHash`, `framework`, `standards` (jsonb), `questionsHash`, `complianceResults` (jsonb), `metadata` (jsonb), `documentName`, `accessCount`, `lastAccessedAt`, `createdAt`

**Behavior**: Checked before analysis. If hit, results replayed with 15x simulated progress for realistic UX.

#### 3. `sessions`

**Purpose**: Full workflow state persistence (survives browser close)

**Unique**: `sessionName`

**Columns**: `sessionName`, `documentName`, `documentId`, `jobId`, `fileContent`, `metadata` (jsonb), `sanitizedContent` (jsonb), `extractedContent` (jsonb), `framework`, `selectedStandards` (jsonb), `taggedNotes` (jsonb), `complianceResults` (jsonb), `chatMessages` (jsonb), `analysisProgressData` (jsonb), `currentState`, `createdAt`, `updatedAt`

#### 4. `analysis_progress`

**Purpose**: Per-question progress tracking for resume capability

**Key**: `jobId` + `questionId`

**Columns**: `jobId`, `sessionId`, `documentHash`, `framework`, `standard`, `questionId`, `questionData` (jsonb), `result` (jsonb), `status` (`pending`|`in_progress`|`completed`|`failed`), `error`, `completedAt`, `createdAt`

**Indices**: `(jobId)`, `(jobId, status)`, `(jobId, questionId)`

#### 5. `question_learning_data`

**Purpose**: Store user corrections for auto-correction in future analyses

**Columns**: `documentHash`, `framework`, `standards` (jsonb), `questionId`, `originalChunks`, `reassessedChunks`, `userComments`, `approvedAnswer` (jsonb), `wasReassessed`, `createdAt`

#### 6. `conversations`

**Purpose**: Financial insights chatbot threads

**Columns**: `conversationId`, `sessionId`, `documentHash`, `metadata` (jsonb), `createdAt`, `updatedAt`

#### 7. `messages`

**Purpose**: Individual chat messages

**Columns**: `messageId`, `conversationId`, `role` (`user`|`assistant`), `content`, `citations` (jsonb), `suggestedQuestions` (jsonb), `timestamp`

---

## 10. Results Page & Reporting

### Component Files

| File | Purpose |
| --- | --- |
| `components/ResultsPage.tsx` (1105 lines) | Primary results view |
| `components/ResultsPageRoute.tsx` | Route wrapper, connects WorkflowContext |
| `components/ResultsViewerPage.tsx` | Standalone viewer for saved results |
| `components/ChatReanalysis.tsx` | Chat-based re-analysis UI |
| `components/ContextViewerModal.tsx` | Modal for viewing raw AI context |
| `components/TableRenderer.tsx` | Renders tabular data from evidence extracts |
| `utils/reportGenerator.ts` | PDF/DOCX export logic |
| `utils/tableParser.ts` | Detects and parses table structures in text |

### Data Flow: How ResultsPage Gets Its Data

`ResultsPageRoute.tsx` reads from `WorkflowContext` and passes props:

| Prop | Type | Source |
| --- | --- | --- |
| `reportData` | ComplianceItem[] | `workflow.complianceReport` (from `POST /api/process/analyze` response) |
| `metadata` | Metadata | `workflow.metadata` (from `POST /api/process/metadata` response) |
| `framework` | string | `workflow.framework` ("IFRS", "US GAAP", etc.) |
| `userSelectedStds` | string[] | `workflow.standards` (`["IAS 7", "IAS 1", ...]`) |
| `sanitizedContent` | object | `workflow.sanitizedContent` (Azure Doc Intelligence text) |
| `onBackToChat` | () => void | Returns to workflow chat view |
| `onRestart` | () => void | Full session reset |
| `onAddMoreStandards` | () => void | Back to standards selection |
| `onUpdateResults` | (items) => void | Pushes changes to context |

On mount, `reportData` is copied to `localReportData` (useState). All mutations (overrides, reassessments) update `localReportData`. If `onUpdateResults` is provided, changes also propagate back to context.

### Key Computed Values (useMemo)

- **`questionsByStandard`**: Groups `localReportData` by `item.section` matching `userSelectedStandards`. Also applies `statusFilter`. Re-computes on data/filter/tab change.

- **`standardStats`**: Per-standard counts: `{ total, yes, no, na, error }`. Derived from `questionsByStandard`.

- **`standardChunksByContext`**: Groups `currentQuestions` by `context_required` field. Deduplicates — stores one chunk sample per context type. Shows: contextType, chunk text, questionCount.

### UI Sections

#### Section 1: Header Bar (lines ~370-425)

- **Data**: `metadata.companyName`, `framework`
- **Buttons**: "Add More Standards" (conditional), "Download PDF Report", "New Analysis", "Back to Chat"

#### Section 2: Standard Tabs (lines ~427-465)

- One tab per standard from `userSelectedStandards`
- Per tab: standard name, question count, compliance rate (N/A excluded from denominator)

#### Section 3: Stats Overview — 5 boxes (lines ~472-498)

- `[Total] [Compliant/green] [Non-Compliant/red] [N/A/gray] [Errors*]`
- *Errors box only renders if `currentStats.error > 0`

#### Section 4: Chat Re-Analysis (`ChatReanalysis` component)

- User types natural-language instructions → creates job → strips old analysis → `POST /api/process/re-analyze` → updates results

#### Section 5: Context Chunks Sent to AI (lines ~498-530)

- Purple buttons grouped by `context_required`: "Notes Only", "FS Only", "Full Context"
- Per button: context type, question count, size in KB
- Click → opens `ContextViewerModal`

#### Section 6: Status Filter Bar (lines ~530-600)

- Buttons: `[All (N)] [✓ Compliant (N)] [✕ Non-Compliant (N)] [N/A (N)] [⚠ Errors (N)]`
- Bulk reassessment button (if selections exist)

#### Section 7: Bulk Reassessment Panel (lines ~630-680, conditional)

- Textarea for common instructions + "Reassess N Questions" button

#### Section 8: Selection Controls (lines ~690-710)

- "Select All" / "Deselect All" / "N selected"

#### Section 9: Questions List — Per-question cards (lines ~715-1000)

**9a. Question Header (always visible):**

| Element | Data Field |
| --- | --- |
| Checkbox | `selectedQuestions.has(item.id)` |
| Reference badge | `item.reference` (e.g. "IAS 7.18", mono font) |
| Status badge | `item.status` (YES=green, NO=red, N/A=gray) |
| Confidence bar | `item.confidence` (green≥80%, yellow≥60%, red) |
| Confidence % | `Math.round(item.confidence * 100) + "%"` |
| Override badge | `manualOverrides.has(item.id)` (yellow, if any) |
| Question text | `item.original_question \|\| item.question` |
| Save button | `savedQuestions` Set (session-only, not persisted) |
| Edit button | Opens Manual Override panel |
| Reassess button | Opens AI Reassessment panel |
| Chevron | Toggles expanded detail view |

**9b. Reassess Panel** (when `reassessQuestion === item.id`):

Textarea → "Submit for AI Reassessment" → strips old analysis → `POST /api/process/re-analyze` → updates results

**9c. Manual Override Panel** (when `editingQuestion === item.id`):

Radio buttons: YES / NO / N/A + required reason textarea → `handleManualOverride()` → changes `item.status`, prepends `"[MANUAL OVERRIDE] reason"` to `item.explanation`

**9d. Expanded Content** (when question is toggled):

- **Analysis**: `item.explanation` — from AI chain-of-thought
- **Evidence table** (6 columns): Reference, Requirement, Description, Page Number (blue badge), Extract (with table rendering), Content Analysis
- **Suggested Disclosure**: actionable disclosure text per status
- **Enhancement Recommendations** (green box, conditional): from "ENHANCEMENT OPPORTUNITY:" in suggestedDisclosure

#### Section 10: Financial Insights FAB (lines ~1010-1095)

- Blue floating button (bottom-right) → opens `FinancialInsightsChatbot` side drawer
- Only renders when `sanitizedContent` is not null
- Free-form Q&A, toggleable fullscreen

### How Key Parameters Change the Display

| Parameter | What Changes |
| --- | --- |
| `statusFilter` | Filters questionsByStandard → changes stats counts, hides/shows questions |
| `activeTab` | Switches which standard's questions, stats, context chunks, selection state |
| Manual Override | Changes `item.status` + `item.explanation`, adds yellow badge |
| AI Reassessment | Replaces status, confidence, explanation, evidence, suggestedDisclosure |
| `context_required` | Determines context group button assignment (Section 5) |
| `item.confidence` | Controls bar color (green/yellow/red) and % |
| `item.status` | Controls badge color, filter bucket, stats |
| `sanitizedContent` | If null, Financial Insights FAB hidden |
| `onAddMoreStandards` | If null, "Add More Standards" button hidden |

### State Management

| State | Purpose |
| --- | --- |
| `localReportData` | Main data array, initialized from `reportData` prop |
| `activeTab` | Currently selected standard tab |
| `expandedQuestions` | Set of expanded question IDs |
| `statusFilter` | `'all'` \| `'YES'` \| `'NO'` \| `'N/A'` \| `'Error'` |
| `manualOverrides` | Map for audit trail |
| `editingQuestion` | Question ID with open Manual Override panel |
| `reassessQuestion` | Question ID with open Reassess panel |
| `reassessInstructions` | Text for single-question reassess |
| `isReassessing` | Loading state during reassessment |
| `showInsightsChatbot` | Whether Financial Insights drawer is open |
| `isFullscreen` | Whether insights drawer is fullscreen |
| `savedQuestions` | Bookmarked question IDs (session-only) |
| `selectedQuestions` | For bulk reassessment selection |
| `showBulkReassess` | Whether bulk reassess panel is visible |
| `bulkReassessInstructions` | Text for bulk reassessment |
| `viewContextType` | Which context type modal to show |

### Export Formats

- **PDF**: `generateProfessionalPDF(localReportData, metadata, framework, stds)` — in `utils/reportGenerator.ts`
- **DOCX**: `generateProfessionalDOCX(localReportData, metadata, framework, stds)` — in `utils/reportGenerator.ts`

### Persistence

- **Save**: `POST /api/results` → `{ metadata, complianceItems, reportData, framework, documentName }` → returns `{ resultId }`
- **Load**: `GET /api/results/:id` → returns full saved analysis → used by `ResultsViewerPage.tsx` for shareable URLs
- **Database table**: `analysis_results` (see Section 9)

---

## 11. Key File Reference

### Frontend

| File | Purpose |
| --- | --- |
| `App.tsx` | Root component (3-panel layout) |
| `index.tsx` | Vite entry point |
| `index.html` | HTML entry |
| `hooks/useComplianceWorkflow.ts` | STATE MACHINE (2392 lines) |
| `hooks/useWebSocket.ts` | WebSocket connection manager |
| `services/apiService.ts` | All HTTP API calls |
| `src/utils/filterParser.ts` | NLP instruction → filter |
| `constants.ts` | ALL_STANDARDS, frameworks |
| `types.ts` | TypeScript interfaces |

### Frontend Components

| File | Purpose |
| --- | --- |
| `components/ChatInterface.tsx` | Main workflow chat view |
| `components/AnalysisPanel.tsx` | Right panel (metadata/standards/progress) |
| `components/SessionPanel.tsx` | Left panel (session list) |
| `components/ResultsPage.tsx` | Results view (1105 lines) |
| `components/ComplianceReport.tsx` | Report dashboard (287 lines) |
| `components/MetadataDisplay.tsx` | Metadata confirmation card |
| `components/MetadataEditor.tsx` | Metadata editing form |
| `components/StandardsEditor.tsx` | Standards selection UI |
| `components/DualFileUpload.tsx` | Dual file upload component |
| `components/FrameworkSelector.tsx` | Framework selection buttons |
| `components/IndexedContentPreview.tsx` | Chunk preview table |
| `components/InstructionInput.tsx` | Filter instructions input |
| `components/AnalysisProgressCard.tsx` | Real-time progress display |

### Backend Server

| File | Purpose |
| --- | --- |
| `dev-server.js` | Development Express server (1855 lines) |
| `production-server.js` | Production Express server |

### Backend Services

| File | Purpose |
| --- | --- |
| `server/services/complianceService.js` | Analysis engine (2741 lines) |
| `server/services/azureSearchService.js` | Search + chunk queries (1515 lines) |
| `server/services/targetedIndexOrchestrator.js` | Chunking + indexing (941 lines) |
| `server/services/taxonomyTaggingService.js` | IFRS taxonomy concept tagging |
| `server/services/azureOpenAIClient.js` | Multi-region AI client (849 lines) |
| `server/services/multiModelClient.js` | AI model abstraction |
| `server/services/documentExtractionService.js` | Azure Doc Intelligence |
| `server/services/metadataService.js` | AI metadata extraction |
| `server/services/complianceJobService.js` | Job orchestration + resume |
| `server/services/progressTrackingService.js` | Per-question progress |
| `server/services/resultCacheService.js` | Analysis result caching |
| `server/services/fsValidationService.js` | FS completeness validation |
| `server/services/websocketManager.js` | WebSocket server |
| `server/services/suggestStandardsService.js` | AI standard suggestion |
| `server/services/chatService.js` | Financial insights chatbot |

### Backend Utilities

| File | Purpose |
| --- | --- |
| `server/utils/contextReportGenerator.js` | HTML context report |
| `server/utils/jobStore.js` | In-memory job state |

### Data

| Path | Purpose |
| --- | --- |
| `data/checklists/Enhanced Framework/IFRS_decisiontree/` | 44 enhanced checklists |
| `data/checklists/IFRS/` | 44 base checklists |
| `data/taxonomy/ifrs_concept_index.json` | 5,512 IFRS concepts |
| `data/user_taxonomies/` | Custom frameworks |

### Database

| File | Purpose |
| --- | --- |
| `shared/schema.ts` | Drizzle ORM table definitions |
| `drizzle.config.ts` | DB connection config |

### Config

| File | Purpose |
| --- | --- |
| `package.json` | Dependencies + scripts |
| `vite.config.js` | Vite build config |
| `tsconfig.json` | TypeScript config |
| `vitest.config.ts` | Test runner config |
| `.env.example` | Environment template |
| `.gitignore` | Git exclusions |
| `railway.toml` | Railway deployment |
| `render.yaml` | Render deployment |
| `nixpacks.toml` | Nixpacks build config |

---

## 12. Configuration & Environment

### Required Environment Variables

#### Azure OpenAI (legacy primary — fallback if pools not configured)

| Variable | Purpose |
| --- | --- |
| `AZURE_OPENAI_ENDPOINT` | Primary endpoint URL |
| `AZURE_OPENAI_API_KEY` | Primary API key |
| `AZURE_OPENAI_DEPLOYMENT_GPT4O` | Deployment name (default: gpt-4o) |
| `AZURE_OPENAI_DEPLOYMENT_GPT4` | GPT-4 deployment (legacy) |
| `AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI` | GPT-4o-mini deployment (legacy) |
| `AZURE_OPENAI_API_VERSION` | API version (default: 2024-10-21) |

#### Azure OpenAI GPT-5.2 Compliance Pool (3 endpoints)

| Variable Pattern | Purpose |
| --- | --- |
| `AZURE_OPENAI_ENDPOINT_GPT52_{1,2,3}` | GPT-5.2 endpoint URLs |
| `AZURE_OPENAI_API_KEY_GPT52_{1,2,3}` | GPT-5.2 API keys |
| `AZURE_OPENAI_DEPLOYMENT_GPT52_{1,2,3}` | Deployment names (default: gpt-5.2-chat) |

#### Azure OpenAI GPT-5.1 Compliance Pool (3 endpoints)

| Variable Pattern | Purpose |
| --- | --- |
| `AZURE_OPENAI_ENDPOINT_GPT51_{1,2,3}` | GPT-5.1 endpoint URLs |
| `AZURE_OPENAI_API_KEY_GPT51_{1,2,3}` | GPT-5.1 API keys |
| `AZURE_OPENAI_DEPLOYMENT_GPT51_{1,2,3}` | Deployment names (default: gpt-5.1-chat) |

#### Azure OpenAI GPT-4o Fallback Pool (6 endpoints)

| Variable Pattern | Purpose |
| --- | --- |
| `AZURE_OPENAI_ENDPOINT_GPT4O_{1..6}` | GPT-4o endpoint URLs |
| `AZURE_OPENAI_API_KEY_GPT4O_{1..6}` | GPT-4o API keys |
| `AZURE_OPENAI_DEPLOYMENT_GPT4O_{1..6}` | Deployment names (default: gpt-4o) |

#### Azure OpenAI GPT-4o-mini Fast Pool (6 endpoints)

| Variable Pattern | Purpose |
| --- | --- |
| `AZURE_OPENAI_ENDPOINT_MINI_{1..6}` | GPT-4o-mini endpoint URLs |
| `AZURE_OPENAI_API_KEY_MINI_{1..6}` | GPT-4o-mini API keys |
| `AZURE_OPENAI_DEPLOYMENT_MINI_{1..6}` | Deployment names (default: gpt-4o-mini) |

> **TOTAL**: 18 Azure OpenAI resources configured (6 compliance + 6 fallback + 6 fast). `.env.example` only lists legacy vars. Pool vars must be set in Railway/Render.

#### Azure AI Search

| Variable | Purpose |
| --- | --- |
| `AZURE_SEARCH_ENDPOINT` | Search service URL |
| `AZURE_SEARCH_ADMIN_KEY` | Admin API key |

#### Azure Document Intelligence

| Variable | Purpose |
| --- | --- |
| `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` | Doc Intelligence URL |
| `AZURE_DOCUMENT_INTELLIGENCE_KEY` | Doc Intelligence key |

#### Database Connection

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Neon PostgreSQL connection string |

### NPM Scripts

| Script | Purpose |
| --- | --- |
| `npm run dev:full` | Full stack (Express + Vite HMR), port 5000 |
| `npm run build` | Production build → `dist/` |
| `npm start` | Production server (`tsx production-server.js`) |
| `npm test` | Run vitest tests |
| `npm run test:azure` | Run Azure connectivity tests |
| `npm run health-check` | Same as `test:azure` |
| `npm run db:push` | Push schema to database |
| `npm run deploy` | Run deployment script |

---

## 13. Deployment & Infrastructure

### Railway

- **Service**: `rai-compliance-analysis`
- **URL**: `https://rai-compliance-analysis-production.up.railway.app`
- **Build**: Nixpacks (`nixpacks.toml`)
- **Start**: `npm start` → `tsx production-server.js`
- **Config**: `railway.toml`

### Render (alternative)

- **Config**: `render.yaml`
- **Build**: `npm install && npm run build`
- **Start**: `npm start`

### Vercel (alternative)

- **Config**: `vercel.json`

### GitHub

- **Repository**: `vithaluntold/raica1`
- **Branch**: `main`

---

## Changelog (v4.0 — 16 February 2026)

### 1. Decision Tree Leaf Node Rewrite (commit `787ed45`)

- Rewrote ALL 6,315 leaf nodes across 44 Enhanced Decision Tree JSON files
- Old format used inverted, confusing language:
  - "Raises compliance issue: YES" → meant non-compliant (STATUS=NO)
  - "Raises compliance issue: NO" → meant compliant (STATUS=YES)
- New format uses direct compliance vocabulary:
  - `"COMPLIANT: YES"` (2,107 nodes), `"COMPLIANT: NO"` (2,312 nodes), `"COMPLIANT: N/A"` (1,893 nodes)
- This eliminated the semantic inversion that caused AI to mismap statuses

### 2. Prompt Architecture Rewrite (commit `787ed45`)

- Chain of Thought restructured as single tree-driven engine
- Old: `STEP_3_COMPARISON` (compare text against requirement)
- New: `STEP_3_TREE_WALK` (walk through CHECKPOINT nodes, reach leaf)
- `formatDecisionTreeCompact`: "STEP N" → "CHECKPOINT N" with → arrows
- Added `SELF_CHECK` field for AI self-verification

### 3. STATUS Parsing Fix (commit `5a1912d`)

- **Root cause**: After leaf rewrite, 32/44 questions had STATUS contradicting their own tree walk reasoning. AI placed STATUS before reasoning (following old example pattern) and answered screening questions literally instead of compliance conclusions.
- **Fix A — TEMPLATE**: STATUS field moved AFTER `STEP_4_CONCLUSION` with explicit instruction: STATUS = compliance from tree leaf, NOT factual answer to screening question
- **Fix B — EXAMPLES**: All restructured to show STATUS after reasoning
- **Fix C — PARSER**: Uses `matchAll`+`pop` for LAST STATUS match (not first)
- **Fix D — POST-PARSE**: Tree walk correction extracts `COMPLIANT:` from `STEP_3_TREE_WALK` and overrides STATUS when they disagree

### 4. Validation Rules Cleanup (commit `787ed45`)

- Rule 4 REMOVED: Suspicious number detection (`\d{7,}`) caused false positives on legitimate financial figures
- Rule 6 SIMPLIFIED: Removed redundant YES+no-evidence check that conflicted with Rule 1's confidence cap (0.4 vs 0.2)
- Rule 5 EXPANDED: N/A justification patterns expanded from 4 phrases to 40+ domain-specific patterns, plus 100-char length threshold

### 5. AI API Pool Documentation

- Added full Pool Architecture diagrams (Section 6)
- Documented all 18 Azure OpenAI resources across 3 tiers
- Added retry/backoff config, model parameter table
- Added GPT-5.x `max_completion_tokens` vs GPT-4o `max_tokens` distinction
- Expanded Section 12 env vars with all pool variable patterns
- Documented `multiModelClient.js` operation-based routing

---

*Document generated from RAI Compliance Analysis Platform knowledge transfer v4.0*
*Last updated: 16 February 2026*
