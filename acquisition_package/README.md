# DoD Acquisition Contract Package Automation — Agent Architecture

## Overview

This package provides a complete, machine-readable architecture for automating the generation of all **28 required documents** in a DoD acquisition contract package (USMC & Space Force). It replaces the single .docx template approach with a structured, agent-optimized system designed for multi-agent orchestration.

**Target**: 38+ specialized AI agents generating a complete contract package, reducing processing time from 400-800 hours to 2-3 hours.

---

## Package Structure

```
acquisition_package/
├── manifest.json                    # Master index: all 28 documents, dependencies, phases, cross-references
├── dependency_graph.json            # DAG with topological sort, execution tiers, conditional logic, human gates
├── cross_reference_validation.json  # 30+ validation rules for data consistency across documents
├── orchestrator_config.json         # Orchestrator agent config: shared data store, agent registry, execution protocol
├── schemas/                         # 28 individual JSON schemas (one per document)
│   ├── DOC-001_acquisition_strategy.json
│   ├── DOC-002_market_research.json
│   ├── DOC-003_igce.json
│   ├── DOC-004_justification_approval.json
│   ├── DOC-005_determination_findings.json
│   ├── DOC-006_pws_sow_soo.json
│   ├── DOC-007_source_selection_plan.json
│   ├── DOC-008_solicitation.json
│   ├── DOC-009_evaluation_criteria.json
│   ├── DOC-010_sseb_report.json
│   ├── DOC-011_ssdd.json
│   ├── DOC-012_pnm_bcm.json
│   ├── DOC-013_dd2579.json
│   ├── DOC-014_dd254.json
│   ├── DOC-015_dd1547.json
│   ├── DOC-016_legal_review.json
│   ├── DOC-017_purchase_request.json
│   ├── DOC-018_contract_ucf.json
│   ├── DOC-019_qasp.json
│   ├── DOC-020_cor_appointment.json
│   ├── DOC-021_cpars_evaluation.json
│   ├── DOC-022_responsibility_determination.json
│   ├── DOC-023_oci_determination.json
│   ├── DOC-024_sb_subcontracting_plan.json
│   ├── DOC-025_distribution_list.json
│   ├── DOC-026_debriefing.json
│   ├── DOC-027_award_notice.json
│   └── DOC-028_admin_plan.json
├── prompts/                         # 28 agent prompt templates (one per document)
│   ├── DOC-001_acquisition_strategy.md
│   ├── DOC-002_market_research.md
│   ├── ... (28 total)
│   └── DOC-028_contract_administration_plan.md
└── README.md                        # This file
```

---

## How It Works

### 1. Manifest (`manifest.json`)
The central index that maps all 28 documents with:
- Regulatory references (FAR/DFARS/NMCARS/AFFARS)
- Dependencies (`depends_on` array)
- Downstream consumers (`feeds_into` array)
- Specific field-level data mappings (`data_sources` object)
- Conditional requirements (`trigger_condition`)
- Dollar thresholds for approval routing

### 2. Schemas (`schemas/`)
Each document has a standalone JSON schema defining:
- **Every field** with type, required/optional, validation rules
- **Cross-references** showing where data flows to/from other documents
- **Enum options** with regulatory basis
- **Computed fields** with formulas
- **Approval chains** with threshold-based routing
- **Validation rules** specific to that document

### 3. Prompts (`prompts/`)
Each agent gets a Markdown prompt template containing:
- Role definition and regulatory authority
- Input requirements (which schemas to load)
- Step-by-step generation instructions
- Decision logic (e.g., "If only 1 capable source → flag DOC-004 as required")
- Cross-reference validation checklist
- Common pitfalls to avoid
- Tone and style guidance

### 4. Dependency Graph (`dependency_graph.json`)
- **12 execution tiers** with topological ordering
- **Parallel groups** (documents within a tier can run simultaneously)
- **3 human gates** where automation must pause for human input
- **8 conditional document rules** with trigger conditions

### 5. Cross-Reference Validation (`cross_reference_validation.json`)
- **7 exact-match rules** (e.g., total cost must be identical everywhere)
- **8 consistency rules** (e.g., competition strategy must be coherent across documents)
- **7 conditional existence rules** (e.g., J&A must exist if sole source)
- **5 mathematical rules** (e.g., IGCE totals must sum correctly)

### 6. Orchestrator Config (`orchestrator_config.json`)
- **Minimum user inputs** needed to bootstrap the entire package
- **Shared data store schema** — central key-value store all agents read/write
- **Agent registry** mapping each document to its agent with read/write permissions
- **10-step execution protocol**

---

## Execution Flow

```
User Input → Orchestrator
    │
    ├── Tier 1:  DOC-006 (PWS/SOW) ──────────────────────────────────────┐
    │                                                                      │
    ├── Tier 2:  DOC-002 (Market Research) ┬── DOC-014 (DD 254) ──── DOC-019 (QASP)
    │                                      │
    ├── Tier 3:  DOC-003 (IGCE) ── DOC-001 (Strategy) ── DOC-013 ── DOC-017 (PR)
    │                                      │
    ├── Tier 4:  DOC-004 (J&A)* ── DOC-005 (D&F)* ── DOC-007 (SSP)* ── DOC-023 (OCI)
    │                                      │
    ├── Tier 5:  DOC-009 (Eval Criteria)   │
    │                                      │
    ├── Tier 6:  DOC-008 (Solicitation) ◄──┘
    │
    ║  ═══ HUMAN GATE 1: Issue solicitation, receive & evaluate proposals ═══
    │
    ├── Tier 7:  DOC-010 (SSEB Report)** ── DOC-016 (Legal Review)
    │
    ║  ═══ HUMAN GATE 2: SSA makes award decision ═══
    │
    ├── Tier 8:  DOC-011 (SSDD)** ── DOC-012 (PNM) ── DOC-022 (Responsibility)
    │
    ├── Tier 9:  DOC-018 (Contract) ── DOC-026 (Debriefing)*
    │
    ├── Tier 10: DOC-020 (COR) ── DOC-024 (SB Sub Plan)* ── DOC-027 (Award Notice)
    │
    ├── Tier 11: DOC-025 (Distribution) ── DOC-028 (Admin Plan)
    │
    └── Tier 12: DOC-021 (CPARS)** [ongoing during performance]

    * = Conditional (may be skipped based on acquisition parameters)
    ** = Requires human input
```

---

## Integration with RAG / ALMS

Each schema's `data_sources` and `cross_reference` fields are designed to map to:
- **ALMS historical data**: Prior contract pricing, past performance, vendor databases
- **Regulatory databases**: FAR/DFARS clause matrices, NAICS lookups, SAM.gov data
- **Organizational data**: Contracting office codes, fund cites, personnel directories

To integrate with your RAG pipeline:
1. Load the relevant schema for the document being generated
2. For each field with a `source` attribute, query the shared data store first, then fall back to RAG
3. For fields requiring external validation (NAICS, SAM.gov), implement API calls or cached lookups
4. Store all generated outputs in the shared data store for downstream agents

---

## Service-Specific Notes

| Feature | USMC | Space Force |
|---------|------|-------------|
| Regulation Supplement | NMCARS | AFFARS |
| Contract System | MOCAS / SPS | CON-IT |
| Payment System | WAWF/iRAPT | WAWF/iRAPT |
| Acquisition Command | MARCORSYSCOM | SSC / SpRCO |
| SB Office | OSBP HQMC | SAF/SB |
| Legal Review | SJA/OGC | SAF/GC |

---

## Versioning

- **v1.0**: Single .docx template (human-readable, not agent-optimized)
- **v2.0**: This package — full JSON schema architecture with dependency graph, validation, and orchestrator config
- **Planned v3.0**: Integration with Docling for enhanced document processing and output rendering
