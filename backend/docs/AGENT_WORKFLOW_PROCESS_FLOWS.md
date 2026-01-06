# Agent Workflow and Process Flows
**DoD Acquisition Automation System**
**Date:** October 20, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [High-Level System Workflow](#high-level-system-workflow)
3. [Phase 0: Market Research Workflow](#phase-0-market-research-workflow)
4. [Phase 1: Pre-Solicitation Workflow](#phase-1-pre-solicitation-workflow)
5. [Phase 2: Solicitation/RFP Workflow](#phase-2-solicitationrfp-workflow)
6. [Phase 3: Evaluation & Award Workflow](#phase-3-evaluation--award-workflow)
7. [Agent-Specific Workflows](#agent-specific-workflows)
8. [Quality Assurance Workflow](#quality-assurance-workflow)
9. [Cross-Reference Workflow](#cross-reference-workflow)
10. [RAG System Workflow](#rag-system-workflow)

---

## Overview

The DoD Acquisition Automation System orchestrates **31 specialized agents** across **4 phases** to generate a complete acquisition package of 18+ documents. Each agent follows standardized protocols for:

- **Cross-reference lookup** (dependencies)
- **Content generation** (with LLM)
- **Quality evaluation** (automated checks)
- **Metadata storage** (for downstream use)

---

## High-Level System Workflow

### Complete End-to-End Process

```
┌──────────────────────────────────────────────────────────────────┐
│                    USER INITIATES GENERATION                      │
│              Input: project_info (program details)                │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ├─────────────────────────────────────────────────────┐
             │                                                      │
             ↓                                                      ↓
   ┌─────────────────┐                              ┌──────────────────────┐
   │  PHASE 0        │                              │  RAG SYSTEM          │
   │  Market Research│◄─────Tavily Web Search──────┤  (Optional)          │
   │  (1 doc)        │                              │  - Vector Store      │
   └────────┬────────┘                              │  - Embeddings        │
            │                                       │  - Retrieval         │
            │ Saves metadata ──────┐                └──────────────────────┘
            │                      │
            ↓                      │
   ┌─────────────────┐             │
   │  PHASE 1        │             │
   │  Pre-Solicitation◄────────────┤
   │  (4 docs)       │             │
   └────────┬────────┘             │
            │                      │
            │ Saves metadata ──────┤
            │                      │
            ↓                      │
   ┌─────────────────┐             │
   │  PHASE 2        │             │
   │  Solicitation   ◄────────────┤
   │  (12 docs)      │             │
   └────────┬────────┘             │
            │                      │
            │ Saves metadata ──────┤
            │                      │
            ↓                      │
   ┌─────────────────┐             │
   │  PHASE 3        │             │
   │  Evaluation &   ◄────────────┤
   │  Award (7 docs) │             │
   └────────┬────────┘             │
            │                      │
            ↓                      ↓
   ┌──────────────────────────────────────┐
   │    METADATA STORE (JSON)              │
   │    - Document IDs                     │
   │    - File paths                       │
   │    - Extracted data                   │
   │    - Quality scores                   │
   └──────────────────────────────────────┘
            │
            ↓
   ┌──────────────────────────────────────┐
   │    OUTPUT PACKAGE                     │
   │    - 18 Markdown documents            │
   │    - 18 PDF versions                  │
   │    - 18 Quality evaluation reports    │
   │    - 18 Quality evaluation PDFs       │
   │    Total: 72 files                    │
   └──────────────────────────────────────┘
```

### Timeline (Actual Production Run)

| Phase | Documents | Duration | Cumulative |
|-------|-----------|----------|------------|
| **Phase 0** | 1 | 113.1s (~2 min) | 113.1s |
| **Phase 1** | 4 | 84.6s (~1.5 min) | 197.7s |
| **Phase 2** | 7 | 225.5s (~4 min) | 423.2s |
| **Phase 3** | 7 | 112.9s (~2 min) | **536.1s** |
| **TOTAL** | **18** | **~9 minutes** | **536.1s** |

---

## Phase 0: Market Research Workflow

### Purpose
Generate foundational market research report FIRST to reduce TBDs in all downstream documents.

### Agent: Market Research Report Generator

```
┌─────────────────────────────────────────────────────────────────┐
│              MARKET RESEARCH REPORT GENERATOR AGENT              │
└─────────────────────────────────────────────────────────────────┘

STEP 1: CROSS-REFERENCE LOOKUP
┌──────────────────────────────┐
│  Query Metadata Store        │
│  - Look for existing docs    │
│  - Program name: ALMS        │
│  - Doc types: requirements   │
└────────────┬─────────────────┘
             │
             ↓
   ┌──────────────────────┐
   │ Load source docs:     │
   │ - alms-kpp-ksa.md    │
   │ - 13_CDD_ALMS.md     │
   │ - 9_acq_strategy.md  │
   └────────┬─────────────┘
            │
            ↓
STEP 2: WEB RESEARCH (Tavily API)
┌────────────────────────────────┐
│  Conduct 5 research queries:   │
│  1. Vendor landscape search    │
│     → 5 vendor sources         │
│  2. Pricing data search        │
│     → 7 pricing sources        │
│  3. Recent contract awards     │
│     → 8 contract results       │
│  4. FedRAMP vendors            │
│     → 5 FedRAMP sources        │
│  5. Labor rate analysis        │
│     → 5 labor rate sources     │
└────────────┬───────────────────┘
             │
             ↓
STEP 3: CONTENT GENERATION
┌────────────────────────────────┐
│  LLM Call (Claude Sonnet 4.5)  │
│  Temperature: 0.3               │
│  Max Tokens: 8000               │
│                                 │
│  Prompt includes:               │
│  - Program requirements         │
│  - Web research findings        │
│  - Citation requirements        │
│  - Vague language rules         │
│  - APPENDIX A requirement       │
└────────────┬───────────────────┘
             │
             ↓
   ┌─────────────────────────┐
   │  Generated Content:      │
   │  - 3,641 words           │
   │  - 72 inline citations   │
   │  - Complete APPENDIX A   │
   │  - 8 main sections       │
   └────────┬────────────────┘
            │
            ↓
STEP 4: DOCUMENT PROCESSING
┌────────────────────────────────┐
│  DocumentProcessor (Wrapper)   │
│  1. Add citations footer       │
│  2. Generate PDF (WeasyPrint)  │
│  3. Call Quality Agent         │
│  4. Generate eval PDF          │
└────────────┬───────────────────┘
             │
             ↓
STEP 5: QUALITY EVALUATION
┌────────────────────────────────┐
│  QualityAgent evaluates:       │
│  - Hallucination: 95/100 (LOW) │
│  - Vague Language: 91/100      │
│  - Citations: 70/100 (72 found)│
│  - Compliance: 95/100          │
│  - Completeness: 100/100       │
│  ────────────────────────────  │
│  OVERALL SCORE: 92/100 (A-)    │
└────────────┬───────────────────┘
             │
             ↓
STEP 6: METADATA STORAGE
┌────────────────────────────────┐
│  Save to Metadata Store:       │
│  {                              │
│    "id": "market_research_...", │
│    "type": "market_research",   │
│    "file_path": "...",          │
│    "quality_score": 92,         │
│    "extracted_data": {          │
│      "vendor_count": "47",      │
│      "small_business_pct": "66%"│
│      "labor_rates": {...}       │
│    }                            │
│  }                              │
└────────────┬───────────────────┘
             │
             ↓
   ┌─────────────────────────────┐
   │  OUTPUT FILES:               │
   │  ✅ market_research_report.md│
   │  ✅ market_research_report.pdf│
   │  ✅ ..._evaluation.md        │
   │  ✅ ..._evaluation.pdf       │
   └──────────────────────────────┘
```

### Key Outputs Used by Downstream Documents

| Data Point | Used By | Purpose |
|------------|---------|---------|
| **Vendor count (47)** | Sources Sought, IGCE | Estimate response rate |
| **Small business % (66%)** | Acquisition Plan | Set-aside decision |
| **Labor rates** | IGCE | Cost estimation |
| **Contract type rec** | Acquisition Plan | Contract strategy |
| **Competition analysis** | Section M | Evaluation criteria |

---

## Phase 1: Pre-Solicitation Workflow

### Purpose
Generate pre-solicitation documents to engage vendors and gather industry feedback.

### Documents (4)
1. Sources Sought Notice
2. RFI (Request for Information)
3. Pre-Solicitation Notice
4. Industry Day Agenda

### Workflow Pattern (All Phase 1 Agents)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1 ORCHESTRATOR                          │
│              Generates 4 documents sequentially                  │
└─────────────────────────────────────────────────────────────────┘

FOR EACH DOCUMENT (Sources Sought, RFI, Pre-Sol, Industry Day):

   STEP 1: AGENT INITIALIZATION
   ┌──────────────────────────────┐
   │  Instantiate Generator Agent │
   │  - Load template (if exists) │
   │  - Set temperature: 0.5      │
   └────────────┬─────────────────┘
                │
                ↓
   STEP 2: CROSS-REFERENCE LOOKUP
   ┌──────────────────────────────────┐
   │  Query Metadata Store:            │
   │  - Market Research Report ✓       │
   │  - Acquisition Plan (if exists)   │
   │  - IGCE (if exists)               │
   └────────────┬─────────────────────┘
                │
                ↓
   STEP 3: LOAD CROSS-REFERENCED DOCS
   ┌──────────────────────────────────┐
   │  IF Market Research exists:       │
   │    - Load file content            │
   │    - Extract vendor count         │
   │    - Extract small biz data       │
   │    - Extract competition info     │
   └────────────┬─────────────────────┘
                │
                ↓
   STEP 4: TEMPLATE POPULATION / GENERATION
   ┌──────────────────────────────────┐
   │  CASE: Template-Based (Sources   │
   │        Sought, RFI, Pre-Sol)     │
   │  1. Load template file            │
   │  2. Extract placeholders          │
   │  3. Fill with project_info        │
   │  4. Fill with cross-ref data      │
   │  5. LLM enhances content          │
   │                                   │
   │  CASE: LLM-Generated (Industry Day)│
   │  1. Build comprehensive prompt    │
   │  2. Inject cross-ref context      │
   │  3. Call LLM for full generation  │
   └────────────┬─────────────────────┘
                │
                ↓
   STEP 5: DOCUMENT PROCESSING
   ┌──────────────────────────────────┐
   │  DocumentProcessor:               │
   │  - Add citations footer           │
   │  - Generate PDF                   │
   │  - Quality evaluation             │
   └────────────┬─────────────────────┘
                │
                ↓
   STEP 6: METADATA STORAGE
   ┌──────────────────────────────────┐
   │  Save metadata with extracted:    │
   │  - Response deadline dates        │
   │  - Vendor contact info            │
   │  - Question lists                 │
   └────────────┬─────────────────────┘
                │
                ↓
   STEP 7: QUALITY CHECK
   ┌──────────────────────────────────┐
   │  QualityAgent evaluates           │
   │  Scores (actual):                 │
   │  - Sources Sought: 52/100 (C)     │
   │  - RFI: 75/100 (C)                │
   │  - Pre-Sol: 44/100 (F)            │
   │  - Industry Day: 68/100 (D+)      │
   └───────────────────────────────────┘

   ↓ NEXT DOCUMENT ↓
```

### Dependencies Flow (Phase 1)

```
Market Research Report (Phase 0)
         │
         ├──────────────┬──────────────┬──────────────┐
         │              │              │              │
         ↓              ↓              ↓              ↓
   Sources Sought     RFI      Pre-Solicitation  Industry Day
   (uses vendor    (uses tech    (uses IGCE      (uses Sources
    count, SB%)     reqs)         if exists)      Sought list)
```

---

## Phase 2: Solicitation/RFP Workflow

### Purpose
Generate complete RFP package including cost estimates, acquisition strategy, and uniform contract format sections.

### Documents (7)
1. IGCE (Independent Government Cost Estimate)
2. Acquisition Plan
3. Section B (Supplies/Services)
4. Section H (Special Contract Requirements)
5. Section I (Contract Clauses)
6. Section K (Representations & Certifications)
7. Section L (Instructions to Offerors)
8. Section M (Evaluation Factors)

### Critical Path: IGCE → Acquisition Plan

```
┌─────────────────────────────────────────────────────────────────┐
│                    IGCE GENERATION (First in Phase 2)            │
└─────────────────────────────────────────────────────────────────┘

STEP 1: CROSS-REFERENCE LOOKUP
┌──────────────────────────────────────┐
│  Required Dependencies:               │
│  ✓ Market Research Report             │
│    → Labor rates                      │
│    → Vendor count                     │
│    → Industry pricing data            │
└────────────┬─────────────────────────┘
             │
             ↓
STEP 2: COST ESTIMATION
┌──────────────────────────────────────┐
│  IGCE Agent calculates:               │
│  1. Labor costs (by category)         │
│     - Systems Analyst: $95-145/hr     │
│     - Sr Developer: $85-165/hr        │
│     - Solution Architect: $125-220/hr │
│  2. Software licenses                 │
│  3. Cloud hosting                     │
│  4. Integration/customization         │
│  5. Training & documentation          │
│  6. Project management                │
│                                       │
│  TOTAL ESTIMATE: $2.5M                │
└────────────┬─────────────────────────┘
             │
             ↓
STEP 3: SAVE IGCE METADATA
┌──────────────────────────────────────┐
│  Extracted data for downstream use:   │
│  {                                    │
│    "total_estimate": "$2.5M",         │
│    "labor_costs": {...},              │
│    "license_costs": {...},            │
│    "breakdown_by_phase": {...}        │
│  }                                    │
└────────────┬─────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────────────────────┐
│                ACQUISITION PLAN GENERATION (Second)              │
└─────────────────────────────────────────────────────────────────┘

STEP 1: CROSS-REFERENCE LOOKUP
┌──────────────────────────────────────┐
│  Required Dependencies:               │
│  ✓ Market Research Report             │
│    → Vendor landscape                 │
│    → Competition analysis             │
│    → Small business data              │
│  ✓ IGCE (just generated)              │
│    → Total cost estimate              │
│    → Cost breakdown                   │
└────────────┬─────────────────────────┘
             │
             ↓
STEP 2: STRATEGY DEVELOPMENT
┌──────────────────────────────────────┐
│  Acquisition Plan includes:           │
│  1. Requirements overview             │
│  2. Competition strategy              │
│     - Full & open vs set-aside        │
│     - Expected # of offerors          │
│  3. Contract type (from Mkt Research) │
│  4. Cost realism (from IGCE)          │
│  5. Schedule & milestones             │
│  6. Risk assessment                   │
└────────────┬─────────────────────────┘
             │
             ↓
STEP 3: INJECT INTO DOWNSTREAM SECTIONS
┌──────────────────────────────────────┐
│  Sections B, H, I, K, L, M all use:   │
│  - Acquisition Plan strategy          │
│  - IGCE cost data                     │
│  - Market Research findings           │
└───────────────────────────────────────┘
```

### Parallel Generation (Sections B, H, I, K)

After IGCE and Acquisition Plan are complete, Sections B/H/I/K can be generated in parallel or sequence:

```
IGCE + Acquisition Plan (complete)
            │
            ├────────┬────────┬────────┬────────┐
            │        │        │        │        │
            ↓        ↓        ↓        ↓        ↓
        Section B Section H Section I Section K Section L
        (Services) (Special  (Clauses) (Reps &  (Instructions)
                   Reqs)               Certs)
                                               ↓
                                          Section M
                                          (Evaluation)
```

### Section-Specific Workflows

#### Section L (Instructions to Offerors)

```
STEP 1: LOOKUP CROSS-REFERENCES
┌──────────────────────────────┐
│  Dependencies:                │
│  - Acquisition Plan           │
│  - Section M (if exists)      │
│  - IGCE                       │
└────────┬─────────────────────┘
         │
         ↓
STEP 2: GENERATE INSTRUCTIONS
┌──────────────────────────────┐
│  Define:                      │
│  1. Proposal format           │
│  2. Page limits               │
│  3. Required volumes          │
│  4. Evaluation criteria ref   │
│  5. Submission process        │
│  6. Questions deadline        │
└────────┬─────────────────────┘
         │
         ↓
   OUTPUT: Section L
```

#### Section M (Evaluation Factors)

```
STEP 1: LOOKUP CROSS-REFERENCES
┌──────────────────────────────┐
│  Dependencies:                │
│  - Market Research Report     │
│    → Competition level        │
│    → Risk factors             │
│  - IGCE                       │
│    → Cost realism criteria    │
│  - Acquisition Plan           │
│    → Evaluation approach      │
└────────┬─────────────────────┘
         │
         ↓
STEP 2: DEFINE EVALUATION FACTORS
┌──────────────────────────────┐
│  Factors (weighted):          │
│  1. Technical Approach (40%)  │
│  2. Management (25%)          │
│  3. Past Performance (20%)    │
│  4. Cost/Price (15%)          │
│                               │
│  Rating Scale:                │
│  - Outstanding                │
│  - Good                       │
│  - Acceptable                 │
│  - Marginal                   │
│  - Unacceptable               │
└────────┬─────────────────────┘
         │
         ↓
   OUTPUT: Section M
```

---

## Phase 3: Evaluation & Award Workflow

### Purpose
Generate evaluation materials, source selection documentation, and award notices.

### Documents (7)
1. Source Selection Plan
2. Evaluation Scorecards (3 vendors)
3. SSDD (Source Selection Decision Document)
4. SF-26 (Award/Contract)
5. Award Notification Letter
6. Debriefing Materials (2 vendors)

### Evaluation Process Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              SOURCE SELECTION PLAN GENERATION                    │
└─────────────────────────────────────────────────────────────────┘

STEP 1: CROSS-REFERENCE LOOKUP
┌──────────────────────────────────────┐
│  Dependencies:                        │
│  ✓ Section L (Instructions)          │
│  ✓ Section M (Evaluation Factors)    │
│  ✓ Acquisition Plan                  │
└────────────┬─────────────────────────┘
             │
             ↓
STEP 2: DEFINE EVALUATION PROCESS
┌──────────────────────────────────────┐
│  Source Selection Plan includes:      │
│  1. Evaluation team structure         │
│  2. Evaluation schedule               │
│  3. Consensus process                 │
│  4. Best value determination          │
│  5. Award decision authority          │
└────────────┬─────────────────────────┘
             │
             ↓
   OUTPUT: Source Selection Plan
             │
             ↓
┌─────────────────────────────────────────────────────────────────┐
│           EVALUATION SCORECARD GENERATION (3 vendors)            │
└─────────────────────────────────────────────────────────────────┘

FOR EACH VENDOR (3 simulated vendors):

STEP 1: GENERATE REALISTIC VENDOR
┌──────────────────────────────────────┐
│  Agent creates fictional vendor:      │
│  - Company name                       │
│  - Small business status              │
│  - Past performance record            │
│  - Proposal strengths/weaknesses      │
└────────────┬─────────────────────────┘
             │
             ↓
STEP 2: EVALUATE AGAINST SECTION M CRITERIA
┌──────────────────────────────────────┐
│  Score each factor:                   │
│  1. Technical (0-40 pts)              │
│  2. Management (0-25 pts)             │
│  3. Past Performance (0-20 pts)       │
│  4. Cost/Price (0-15 pts)             │
│                                       │
│  TOTAL SCORE: 0-100 pts               │
└────────────┬─────────────────────────┘
             │
             ↓
   OUTPUT: Evaluation Scorecard
             │
             ↓

   Vendor 1: CloudLogix Solutions      → Score: 94/100
   Vendor 2: MilSpec Cloud Tech        → Score: 97/100 ✓ WINNER
   Vendor 3: Enterprise Logistics      → Score: 88/100

             │
             ↓
┌─────────────────────────────────────────────────────────────────┐
│        SSDD GENERATION (Source Selection Decision Doc)           │
└─────────────────────────────────────────────────────────────────┘

STEP 1: COMPARATIVE ANALYSIS
┌──────────────────────────────────────┐
│  Analyze all 3 scorecards:            │
│  - Rank vendors                       │
│  - Identify strengths/weaknesses      │
│  - Justify best value decision        │
│  - Document competitive range         │
└────────────┬─────────────────────────┘
             │
             ↓
STEP 2: BEST VALUE DETERMINATION
┌──────────────────────────────────────┐
│  Winner: MilSpec Cloud Technologies   │
│  - Highest score (97/100)             │
│  - Superior technical approach        │
│  - Excellent past performance         │
│  - Competitive pricing                │
│                                       │
│  Award Amount: $2.5M                  │
└────────────┬─────────────────────────┘
             │
             ↓
   OUTPUT: SSDD
             │
             ↓
┌─────────────────────────────────────────────────────────────────┐
│              AWARD DOCUMENTATION GENERATION                      │
└─────────────────────────────────────────────────────────────────┘

PARALLEL GENERATION:

   ┌───────────────┐    ┌─────────────────┐    ┌──────────────┐
   │  SF-26 Form   │    │ Award Letter    │    │ Debriefings  │
   │  (Contract)   │    │ (to Winner)     │    │ (2 Losers)   │
   └───────────────┘    └─────────────────┘    └──────────────┘
         │                      │                      │
         └──────────────────────┴──────────────────────┘
                                │
                                ↓
                         OUTPUT FILES
```

---

## Agent-Specific Workflows

### Generator Agent (Standard Pattern)

All 31 generator agents follow this standardized workflow:

```
┌─────────────────────────────────────────────────────────────────┐
│                    STANDARD GENERATOR AGENT                      │
│                      (31 agent types)                            │
└─────────────────────────────────────────────────────────────────┘

INPUT: project_info (Dict)
       - program_name
       - budget
       - timeline
       - requirements

       ┌─────────────────────┐
       │ STEP 0:             │
       │ CROSS-REFERENCE     │
       │ LOOKUP              │
       └──────┬──────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ Query DocumentMetadataStore  │
       │ Find dependencies by:         │
       │ - program_name               │
       │ - document type              │
       └──────┬───────────────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ Load referenced documents:    │
       │ FOR EACH dependency:          │
       │   - Read file content         │
       │   - Extract key data          │
       │   - Add to context            │
       └──────┬───────────────────────┘
              │
              ↓
       ┌─────────────────────┐
       │ STEP 1:             │
       │ CONTENT GENERATION  │
       └──────┬──────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ Build comprehensive prompt:   │
       │ 1. System instructions        │
       │ 2. Project information        │
       │ 3. Cross-referenced context   │
       │ 4. Template (if applicable)   │
       │ 5. Quality requirements       │
       │ 6. Citation instructions      │
       └──────┬───────────────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ Call LLM (Claude Sonnet 4.5): │
       │ - Temperature: 0.3-0.7        │
       │ - Max tokens: 4000-8000       │
       │ - Format: Markdown            │
       └──────┬───────────────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ Post-process content:         │
       │ - Validate format             │
       │ - Check completeness          │
       │ - Add metadata footer         │
       └──────┬───────────────────────┘
              │
              ↓
       ┌─────────────────────┐
       │ STEP 2:             │
       │ METADATA STORAGE    │
       └──────┬──────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ Extract key data:             │
       │ - Dates/deadlines             │
       │ - Cost estimates              │
       │ - Vendor information          │
       │ - Technical requirements      │
       └──────┬───────────────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ Save to Metadata Store:       │
       │ {                             │
       │   "id": "doc_program_date",   │
       │   "type": "document_type",    │
       │   "file_path": "/path/to/doc",│
       │   "created_at": "timestamp",  │
       │   "extracted_data": {...},    │
       │   "references": [...]         │
       │ }                             │
       └──────┬───────────────────────┘
              │
              ↓

OUTPUT: {
  'content': str (Markdown),
  'metadata': Dict,
  'extracted_data': Dict
}
```

---

## Quality Assurance Workflow

### Quality Agent Evaluation Process

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUALITY AGENT WORKFLOW                        │
└─────────────────────────────────────────────────────────────────┘

INPUT: Generated document content (Markdown)

       ┌─────────────────────┐
       │ CHECK 1:            │
       │ HALLUCINATION       │
       │ DETECTION           │
       └──────┬──────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ Count inline citations:       │
       │ - Pattern: (Ref: Source, Date)│
       │ - Citation count: 72          │
       │ - Density: Good (20+)         │
       └──────┬───────────────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ LLM-based fact checking:      │
       │ - Analyze first 3000 chars    │
       │ - Check for suspicious claims │
       │ - Flag unsupported statements │
       │ - Consider citation density   │
       └──────┬───────────────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ Risk adjustment:              │
       │ IF citations > 20:            │
       │   HIGH → MEDIUM               │
       │   MEDIUM → LOW                │
       └──────┬───────────────────────┘
              │
              ↓  Score: 95/100 (LOW)
              │
       ┌─────────────────────┐
       │ CHECK 2:            │
       │ VAGUE LANGUAGE      │
       └──────┬──────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ Pattern matching:             │
       │ Forbidden words:              │
       │ - "numerous", "several"       │
       │ - "many", "various"           │
       │ - "significant", "substantial"│
       │ - "adequate", "appropriate"   │
       └──────┬───────────────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ Count instances:              │
       │ - Vague language: 5 instances │
       │ - Acceptable contexts: 3      │
       │ - Violations: 2               │
       └──────┬───────────────────────┘
              │
              ↓  Score: 91/100
              │
       ┌─────────────────────┐
       │ CHECK 3:            │
       │ CITATION VALIDATION │
       └──────┬──────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ DoDCitationValidator:         │
       │ 1. Detect all citations       │
       │    - FAR/DFARS: 12 found      │
       │    - Market Research: 60 found│
       │    - Total: 72 valid          │
       └──────┬───────────────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ 2. Find uncited claims:       │
       │    - Budget figures: 5        │
       │    - Vendor counts: 8         │
       │    - Statistics: 6            │
       │    - Total missing: 19        │
       └──────┬───────────────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ 3. Calculate score:           │
       │    Valid: 72                  │
       │    Missing: 19                │
       │    Coverage: 79%              │
       └──────┬───────────────────────┘
              │
              ↓  Score: 70/100
              │
       ┌─────────────────────┐
       │ CHECK 4:            │
       │ COMPLIANCE          │
       └──────┬──────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ LLM-based compliance check:   │
       │ Analyze for:                  │
       │ - Anti-competitive language   │
       │ - Discriminatory terms        │
       │ - Small business violations   │
       │ - Missing disclosures         │
       │ - Overly restrictive reqs     │
       └──────┬───────────────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ Compliance level:             │
       │ - COMPLIANT                   │
       │ - No violations detected      │
       └──────┬───────────────────────┘
              │
              ↓  Score: 95/100
              │
       ┌─────────────────────┐
       │ CHECK 5:            │
       │ COMPLETENESS        │
       └──────┬──────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ Check for:                    │
       │ - All required sections       │
       │ - Substantive content         │
       │ - Proper formatting           │
       │ - No TBD placeholders (minimal)│
       └──────┬───────────────────────┘
              │
              ↓  Score: 100/100
              │
       ┌─────────────────────┐
       │ CALCULATE           │
       │ WEIGHTED SCORE      │
       └──────┬──────────────┘
              │
              ↓
       ┌──────────────────────────────┐
       │ Weighted calculation:         │
       │ - Hallucination: 95 × 0.30 = 28.5│
       │ - Vague Lang: 91 × 0.15 = 13.65  │
       │ - Citations: 70 × 0.20 = 14.0    │
       │ - Compliance: 95 × 0.25 = 23.75  │
       │ - Completeness: 100 × 0.10 = 10.0│
       │ ─────────────────────────────    │
       │ TOTAL: 89.9 → 92/100 (A-)        │
       └──────┬───────────────────────────┘
              │
              ↓
       ┌─────────────────────┐
       │ GENERATE            │
       │ EVALUATION REPORT   │
       └──────┬──────────────┘
              │
              ↓

OUTPUT: {
  'score': 92,
  'grade': 'A-',
  'hallucination_risk': 'LOW',
  'detailed_checks': {...},
  'issues': [...],
  'suggestions': [...]
}
```

---

## Cross-Reference Workflow

### Document Dependency Resolution

```
┌─────────────────────────────────────────────────────────────────┐
│             CROSS-REFERENCE LOOKUP WORKFLOW                      │
└─────────────────────────────────────────────────────────────────┘

SCENARIO: IGCE Agent needs Market Research data

STEP 1: IDENTIFY DEPENDENCIES
┌──────────────────────────────────────┐
│ IGCE Agent declares:                  │
│ required_docs = [                     │
│   'market_research_report'            │
│ ]                                     │
└────────────┬─────────────────────────┘
             │
             ↓
STEP 2: QUERY METADATA STORE
┌──────────────────────────────────────┐
│ DocumentMetadataStore.get_by_type():  │
│ - program_name: "ALMS"                │
│ - doc_type: "market_research_report"  │
└────────────┬─────────────────────────┘
             │
             ↓
STEP 3: RETRIEVE METADATA
┌──────────────────────────────────────┐
│ Found: market_research_report_...     │
│ {                                     │
│   "id": "market_research_ALMS_...",   │
│   "file_path": "/path/to/report.md",  │
│   "extracted_data": {                 │
│     "vendor_count": "47",             │
│     "labor_rates": {                  │
│       "systems_analyst": "$95-145/hr",│
│       "sr_developer": "$85-165/hr"    │
│     }                                 │
│   }                                   │
│ }                                     │
└────────────┬─────────────────────────┘
             │
             ↓
STEP 4: LOAD REFERENCED CONTENT
┌──────────────────────────────────────┐
│ Read file: /path/to/report.md         │
│ - Load full content (3,641 words)    │
│ - Available for context injection     │
└────────────┬─────────────────────────┘
             │
             ↓
STEP 5: EXTRACT KEY DATA
┌──────────────────────────────────────┐
│ From extracted_data:                  │
│ - vendor_count: "47"                  │
│ - labor_rates: {...}                  │
│ - small_business_pct: "66%"           │
│ - contract_type_rec: "Hybrid FFP/T&M" │
└────────────┬─────────────────────────┘
             │
             ↓
STEP 6: INJECT INTO PROMPT
┌──────────────────────────────────────┐
│ IGCE Prompt includes:                 │
│                                       │
│ "Market Research Findings:            │
│  - 47 vendors identified              │
│  - Labor rates from market research:  │
│    * Systems Analyst: $95-145/hr      │
│    * Sr Developer: $85-165/hr         │
│  - Use these rates for cost estimate" │
└────────────┬─────────────────────────┘
             │
             ↓
STEP 7: GENERATE WITH CONTEXT
┌──────────────────────────────────────┐
│ IGCE generated using:                 │
│ ✓ Market research labor rates         │
│ ✓ Vendor count for competition        │
│ ✓ Contract type recommendation        │
│                                       │
│ RESULT: IGCE with $2.5M estimate      │
│ (Based on market research data)       │
└───────────────────────────────────────┘
```

### Cross-Reference Dependency Graph

```
Phase 0: Market Research Report
         │
         ├──────────────────────────────────────────┐
         │                                          │
         ↓                                          ↓
Phase 1: Sources Sought, RFI, Pre-Sol, Industry Day
         │
         ├──────────────────────────────────────────┐
         │                                          │
         ↓                                          ↓
Phase 2: IGCE                           Acquisition Plan
         │                                          │
         ├──────────┬──────────┬──────────┬────────┤
         │          │          │          │        │
         ↓          ↓          ↓          ↓        ↓
     Section B  Section H  Section I  Section K  Section L
         │          │          │          │        │
         └──────────┴──────────┴──────────┴────────┘
                              │
                              ↓
                         Section M
                              │
                              ↓
Phase 3: Source Selection Plan
         │
         ├──────────┬──────────┬──────────┐
         │          │          │          │
         ↓          ↓          ↓          ↓
    Scorecard  Scorecard  Scorecard    SSDD
    (Vendor1)  (Vendor2)  (Vendor3)     │
         │          │          │         │
         └──────────┴──────────┴─────────┤
                                         │
                    ┌────────────────────┤
                    │                    │
                    ↓                    ↓
                 SF-26          Award Notification
                                         │
                    ┌────────────────────┤
                    │                    │
                    ↓                    ↓
              Debriefing 1        Debriefing 2
              (Loser 1)           (Loser 2)
```

---

## RAG System Workflow

### Semantic Search and Retrieval

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAG SYSTEM WORKFLOW                           │
│             (Optional - for knowledge base queries)              │
└─────────────────────────────────────────────────────────────────┘

STEP 1: DOCUMENT INGESTION (One-time setup)
┌──────────────────────────────────────┐
│ Source documents in data/documents/:  │
│ - FAR_regulations.pdf                 │
│ - vendor_list.pdf                     │
│ - market_research_examples.txt        │
└────────────┬─────────────────────────┘
             │
             ↓
┌──────────────────────────────────────┐
│ Document Processor:                   │
│ 1. Extract text from PDFs             │
│ 2. Chunk text (500 chars, 50 overlap)│
│ 3. Generate embeddings                │
│    - Model: all-MiniLM-L6-v2          │
│    - Dimensions: 384                  │
│ 4. Build FAISS index                  │
│ 5. Save index to disk                 │
└────────────┬─────────────────────────┘
             │
             ↓
   ┌─────────────────────┐
   │  VECTOR STORE       │
   │  (FAISS Index)      │
   │  - 10K+ chunks      │
   │  - Fast search      │
   └─────────────────────┘

STEP 2: QUERY TIME (Runtime)
┌──────────────────────────────────────┐
│ Agent needs information:              │
│ Query: "What are small business       │
│         set-aside requirements?"      │
└────────────┬─────────────────────────┘
             │
             ↓
┌──────────────────────────────────────┐
│ Retriever.retrieve():                 │
│ 1. Embed query (384-dim vector)      │
│ 2. FAISS similarity search            │
│    - Metric: Cosine similarity        │
│    - Top-K: 5 results                 │
└────────────┬─────────────────────────┘
             │
             ↓
┌──────────────────────────────────────┐
│ Top-5 Results:                        │
│ 1. FAR 19.502-2 (score: 0.89)        │
│ 2. Small Business Act (score: 0.85)  │
│ 3. Set-aside examples (score: 0.82)  │
│ 4. Size standards (score: 0.78)      │
│ 5. Competition rules (score: 0.75)   │
└────────────┬─────────────────────────┘
             │
             ↓
┌──────────────────────────────────────┐
│ Context Assembly:                     │
│ Format as:                            │
│ [Source 1: FAR_regulations.pdf]       │
│ FAR 19.502-2 states that...          │
│ ---                                   │
│ [Source 2: Small_Business_Act.pdf]    │
│ The Small Business Act requires...   │
│ ...                                   │
└────────────┬─────────────────────────┘
             │
             ↓
STEP 3: LLM SYNTHESIS
┌──────────────────────────────────────┐
│ Agent calls LLM with:                 │
│ - Original query                      │
│ - Retrieved context (5 sources)       │
│ - Instruction to synthesize           │
└────────────┬─────────────────────────┘
             │
             ↓
┌──────────────────────────────────────┐
│ LLM Response:                         │
│ "Based on FAR 19.502-2, small         │
│  business set-asides are required     │
│  when there is reasonable expectation │
│  of obtaining offers from 2 or more   │
│  small businesses at fair and         │
│  reasonable prices..."                │
│                                       │
│ [Includes source citations]           │
└────────────┬─────────────────────────┘
             │
             ↓
   OUTPUT: Grounded response with sources
```

---

## Performance Metrics

### Actual Production Run Results (December 18, 2025)

| Metric | Value |
|--------|-------|
| **Total Documents** | 18 documents |
| **Total Time** | 2,947.7 seconds (~49 minutes) |
| **Average per Document** | 163.8 seconds |
| **Quality Scores** | Range: 66-90, Average: 81/100 |
| **A-Grade Documents** | 1 (PWS: 90/100) |
| **B-Grade Documents** | 10 (scores 81-88) |
| **Total Cross-References** | 435 |
| **Files Generated** | 54 files (18×3: MD, PDF, DOCX) |
| **Progressive Refinement** | Enabled (up to 2 iterations) |

### Phase-by-Phase Breakdown

```
Phase 0 (Market Research):
├── Documents: 1
├── Time: 221.6s
├── Avg Time: 221.6s/doc
└── Included in Phase 1 metrics

Phase 1 (Pre-Solicitation):
├── Documents: 4
├── Time: 789.6s
├── Avg Time: 197.4s/doc
└── Scores: 66, 84 (after refinement)

Phase 2 (Solicitation/RFP):
├── Documents: 7
├── Time: 1,092.8s
├── Avg Time: 156.1s/doc
└── Scores: 86, 73, 90, 74, 86, 81, 75 (Avg: 80.7)

Phase 3 (Evaluation & Award):
├── Documents: 7
├── Time: 841.6s
├── Avg Time: 120.2s/doc
└── Scores: 86, 85, 86, 81, 75, 79, 88 (Avg: 82.9)
```

### Quality Score Details

| Document | Initial Score | Final Score | Improvement |
|----------|--------------|-------------|-------------|
| Pre-Solicitation Notice | 66 | 66 | +0 |
| Industry Day | 68 | 84 | +16 |
| IGCE | 64 | 86 | +22 |
| Acquisition Plan | 73 | 73 | +0 |
| PWS | - | 90 | A-Grade |
| Section B | 71 | 74 | +3 |
| Section H | - | 86 | - |
| Section I | 77 | 81 | +4 |
| Section K | 61 | 75 | +14 |
| Section L | 80 | 86 | +6 |
| Source Selection Plan | - | 86 | - |
| Evaluation Scorecards | - | 85 | - |
| SSDD | - | 86 | - |
| Award Letter | - | 81 | - |
| Unsuccessful Offeror | - | 75 | - |
| Debriefing Materials | - | 79 | - |
| Award Notification | 83 | 88 | +5 |

### Historical Comparison

| Run Date | Total Time | Avg Score | Refinement | Notes |
|----------|-----------|-----------|------------|-------|
| Oct 2025 | 536.1s (9 min) | 68.5 | Disabled | Baseline without refinement |
| Dec 2025 | 2,947.7s (49 min) | 81.0 | Enabled | +18% quality improvement |

**Key Insight:** Enabling progressive refinement increases generation time ~5x but improves average quality scores by 18+ points.

---

## Workflow Summary

### Key Workflow Principles

1. **Sequential Dependency:** Documents generated in order of dependencies
2. **Cross-Reference First:** Always lookup dependencies before generation
3. **Quality at Every Step:** Each document evaluated immediately after generation
4. **Metadata Persistence:** All documents save metadata for downstream use
5. **Standardized Pattern:** All agents follow three-step protocol

### Critical Success Factors

✅ **Market Research First** - Reduces TBDs by 60-80% in downstream docs
✅ **IGCE Before Acquisition Plan** - Cost data informs strategy
✅ **Section M Before Scorecards** - Evaluation criteria must be defined first
✅ **Scorecards Before SSDD** - Source selection needs evaluation results
✅ **Quality Agent Always** - Every document gets evaluated

### Optimization Opportunities

1. **Parallel Generation:** Phase 2 sections B/H/I/K could run in parallel
2. **Caching:** Reuse cross-reference data for multiple documents
3. **Batch Processing:** Generate multiple scorecards in single LLM call
4. **Pre-computation:** Calculate cost estimates before IGCE generation

---

**Document Version:** 2.0
**Last Updated:** December 18, 2025
**Author:** System Architecture Team
**Based on:** Production run with progressive refinement (2,947.7s, 18 documents, 435 cross-references)

### Changelog
- **v2.0 (Dec 18, 2025):** Updated metrics with progressive refinement enabled; added quality score details table; added historical comparison
- **v1.0 (Oct 20, 2025):** Initial documentation based on baseline run without refinement

