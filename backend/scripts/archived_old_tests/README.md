# Archived Old Tests & Superseded Scripts

**Purpose:** Scripts that have been replaced by newer, better versions or are no longer relevant.

**Status:** ⚠️ Superseded - use current alternatives instead

---

## Scripts in This Directory

### Old Generation Scripts

#### `run_full_pipeline.py`
- **Old Purpose:** Market research report generation
- **Status:** ❌ Old market research system (different from current)
- **Replaced By:** `test_full_pipeline.py` (complete acquisition docs)
- **Why Archived:** Different system, not part of acquisition pipeline

#### `run_market_research.py`
- **Old Purpose:** Market research filler
- **Status:** ❌ Old system
- **Replaced By:** Current agents with RAG
- **Why Archived:** Superseded by RAG-enhanced agents

#### `generate_market_research_report.py`
- **Old Purpose:** Generate market research reports
- **Status:** ❌ Old version
- **Replaced By:** `generate_market_research_report_agent.py` in agents/
- **Why Archived:** Old implementation without RAG

#### `generate_all_phases.py`
- **Old Purpose:** Generic phase generation
- **Status:** ❌ Generic version
- **Replaced By:** `generate_all_phases_alms.py` (program-specific)
- **Why Archived:** Too generic, ALMS version is better

#### `document_reference.py`
- **Old Purpose:** Unclear/experimental
- **Status:** ❌ Unclear purpose
- **Replaced By:** `demo_cross_reference_system.py`
- **Why Archived:** Functionality unclear, likely superseded

### Old Test Scripts

#### `test_document_processor.py`
- **Old Purpose:** Test basic document processor
- **Status:** ❌ Tests old PyPDF2 processor
- **Replaced By:** `test_docling_integration.py` (tests Docling)
- **Why Archived:** Old processor, Docling is now standard

#### `test_document_processing.py`
- **Old Purpose:** Document processing tests
- **Status:** ❌ Duplicate/old
- **Replaced By:** `test_docling_integration.py`
- **Why Archived:** Duplicate of above, superseded

#### `test_hybrid_extraction.py`
- **Old Purpose:** Test RAG extraction methods
- **Status:** ❌ Old RAG tests
- **Replaced By:** `test_rag_system.py`
- **Why Archived:** Old RAG implementation

#### `test_integration_workflow.py`
- **Old Purpose:** Integration workflow tests
- **Status:** ❌ Old workflow
- **Replaced By:** `test_complete_system.py`
- **Why Archived:** Old workflow, new orchestrators in place

#### `test_iterative_refinement.py`
- **Old Purpose:** Test iterative refinement
- **Status:** ❌ Old refinement system
- **Replaced By:** Built into current agents
- **Why Archived:** Refinement now integrated into agents

#### `test_citation_detection.py`
- **Old Purpose:** Test citation detection
- **Status:** ❌ Old citation system
- **Replaced By:** Built into document processor
- **Why Archived:** Citation system now automatic

#### `test_citation_injector.py`
- **Old Purpose:** Test citation injection
- **Status:** ❌ Old citation system
- **Replaced By:** Built into document processor
- **Why Archived:** Citation injection now automatic

#### `quick_phase1_validation.py`
- **Old Purpose:** Quick Phase 1 test
- **Status:** ❌ Duplicate
- **Replaced By:** `test_phase1_complete.py`
- **Why Archived:** Duplicate functionality

---

## Migration Guide

### If You Need Functionality From These Scripts

| Old Script | Use This Instead |
|------------|------------------|
| `run_full_pipeline.py` | `test_full_pipeline.py` |
| `run_market_research.py` | Current agents with RAG |
| `generate_market_research_report.py` | Market research agent |
| `generate_all_phases.py` | `generate_all_phases_alms.py` |
| `test_document_processor.py` | `test_docling_integration.py` |
| `test_hybrid_extraction.py` | `test_rag_system.py` |
| `test_integration_workflow.py` | `test_complete_system.py` |
| `quick_phase1_validation.py` | `test_phase1_complete.py` |

---

## Can These Be Restored?

**Generally: No** - They're superseded by better implementations.

**If You Must:**
1. Review the current equivalent first
2. Check if functionality exists in current system
3. Consider updating the old script to use new features (Docling, RAG, cross-references)

---

## Related Current Scripts

**Use these instead:**

### Generation
- `test_full_pipeline.py` - Complete package generation
- `generate_all_phases_alms.py` - ALMS-specific generation
- `generate_phase1_presolicitation.py` - Phase 1 only
- `generate_phase2_solicitation.py` - Phase 2 only
- `generate_phase3_evaluation.py` - Phase 3 only

### Testing
- `test_docling_integration.py` - Document processing
- `test_rag_system.py` - RAG retrieval
- `test_complete_system.py` - Full system
- `test_phase1_complete.py` - Phase 1 validation

### Demonstrations
- `demo_cross_reference_system.py` - Learn cross-references
- `examples/quick_start_example.py` - First document
- `examples/example_usage.py` - Interactive examples

---

**Archived:** October 28, 2025  
**Reason:** Superseded by better implementations  
**Action:** Use current alternatives listed above

