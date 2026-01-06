# Scripts Directory Organization

**Last Updated:** October 28, 2025

---

## 📁 Directory Structure

```
scripts/
├── SCRIPTS_ORGANIZATION.md        ← This file (index)
│
├── 🚀 PRODUCTION SCRIPTS (Use These)
│   ├── setup_rag_system.py             ✅ Setup RAG with Docling
│   ├── add_documents_to_rag.py         ✅ Add documents to RAG
│   ├── test_full_pipeline.py           ⭐ Complete 20+ doc generation
│   ├── demo_cross_reference_system.py  ⭐ Learn cross-references
│   ├── test_complete_system.py         ⭐ Quick validation
│   └── quick_cross_reference_test.py   ⭐ 1-min check
│
├── 📊 GENERATION SCRIPTS (Current)
│   ├── generate_all_phases_alms.py     ALMS complete package
│   ├── generate_phase1_presolicitation.py
│   ├── generate_phase2_solicitation.py
│   └── generate_phase3_evaluation.py
│
├── 🧪 TESTING SCRIPTS (Active)
│   ├── test_docling_integration.py     NEW - Test Docling
│   ├── test_rag_system.py              Test RAG retrieval
│   ├── verify_rag_docs.py              Validate RAG setup
│   │
│   ├── Agent Tests/
│   │   ├── test_acquisition_plan_agent.py
│   │   ├── test_igce_enhancement.py
│   │   ├── test_pws_agent.py
│   │   ├── test_soo_agent.py
│   │   ├── test_sow_agent.py
│   │   ├── test_qa_manager_agent.py
│   │   ├── test_quality_agent.py
│   │   └── ...more agent tests
│   │
│   └── Integration Tests/
│       ├── test_cross_reference_system.py
│       ├── test_cross_reference_integration.py
│       ├── test_kpp_ksa_integration.py
│       ├── test_qasp_integration.py
│       └── test_section_lm_generation.py
│
└── 📦 ARCHIVED (Old/Deprecated)
    ├── archived_legacy/              Already archived pipelines
    ├── archived_diagnostics/         One-time diagnostic scripts
    └── archived_old_tests/           Superseded test scripts
```

---

## 🚀 RECOMMENDED SCRIPTS (Start Here)

### For First-Time Users

| Script | Purpose | Runtime | When to Use |
|--------|---------|---------|-------------|
| `examples/quick_start_example.py` | Your first document | 30s | First time |
| `demo_cross_reference_system.py` | Learn cross-refs | 5s | Learning |
| `test_complete_system.py` | Quick validation | 2-3m | Verify setup |

### For Production Use

| Script | Purpose | Runtime | When to Use |
|--------|---------|---------|-------------|
| `test_full_pipeline.py` | Generate 20+ docs | 15-20m | Complete package |
| `generate_all_phases_alms.py` | ALMS package | 10-15m | ALMS specific |
| `generate_phase1_presolicitation.py` | Phase 1 only | 3-5m | Pre-solicitation |
| `generate_phase2_solicitation.py` | Phase 2 only | 5-8m | RFP/solicitation |
| `generate_phase3_evaluation.py` | Phase 3 only | 2-4m | Post-solicitation |

### For RAG Management

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `setup_rag_system.py` | Initial RAG setup | First time / rebuild |
| `add_documents_to_rag.py` | Add new documents | Adding to existing RAG |
| `test_rag_system.py` | Test RAG retrieval | Verify RAG quality |
| `verify_rag_docs.py` | Validate RAG setup | Check document count |
| `test_docling_integration.py` | Test Docling | After installing Docling |

---

## 📦 ARCHIVED SCRIPTS

### Already Archived (in `archived_legacy/`)

- ❌ `run_agent_pipeline.py` - Generic old pipeline
- ❌ `run_complete_post_solicitation_pipeline.py` - Old version
- ❌ `run_pre_solicitation_pipeline.py` - Old version
- ❌ `run_pws_pipeline.py` - Old PWS pipeline
- ❌ `run_rfp_pipeline.py` - Old RFP pipeline
- ❌ `run_soo_pipeline.py` - Old SOO pipeline
- ❌ `run_sow_pipeline.py` - Old SOW pipeline

**Reason:** Replaced by `test_full_pipeline.py` and new orchestrators

### Should Archive (Next Cleanup)

**One-Time Diagnostics:**
- `analyze_tbds.py` - TBD analysis (one-time)
- `benchmark_system.py` - Performance benchmark (one-time)
- `diagnose_rag_extraction.py` - RAG diagnostic (one-time)

**Old/Superseded Scripts:**
- `run_full_pipeline.py` - Old market research (different system)
- `run_market_research.py` - Old market research filler
- `generate_market_research_report.py` - Old market research
- `generate_all_phases.py` - Generic (replaced by ALMS version)
- `document_reference.py` - Unclear purpose
- `test_document_processor.py` - Old (replaced by test_docling_integration.py)
- `test_document_processing.py` - Duplicate/old
- `test_hybrid_extraction.py` - Old RAG test
- `test_integration_workflow.py` - Old workflow test
- `test_iterative_refinement.py` - Old refinement test
- `test_citation_detection.py` - Old citation test
- `test_citation_injector.py` - Old citation test
- `quick_phase1_validation.py` - Duplicate test

**Specialized Tests (Keep but rarely used):**
- `test_web_search.py` - Tavily integration test
- `test_xlsx_processing.py` - Excel processing test
- `generate_sf33.py` - Specific form test

---

## 🗂️ SCRIPTS BY CATEGORY

### RAG & Document Processing

| Script | Status | Purpose |
|--------|--------|---------|
| `setup_rag_system.py` | ✅ CURRENT | Setup RAG with Docling |
| `add_documents_to_rag.py` | ✅ CURRENT | Add documents to RAG |
| `test_rag_system.py` | ✅ CURRENT | Test RAG retrieval |
| `verify_rag_docs.py` | ✅ CURRENT | Validate RAG documents |
| `test_docling_integration.py` | ✅ NEW | Test Docling processor |
| `test_document_processor.py` | ⚠️ OLD | Old processor test |
| `test_document_processing.py` | ⚠️ OLD | Duplicate/old |
| `test_xlsx_processing.py` | 🔧 SPECIFIC | Excel test only |

### Complete Pipeline Generation

| Script | Status | Purpose |
|--------|--------|---------|
| `test_full_pipeline.py` | ✅ CURRENT | Complete 20+ docs |
| `generate_all_phases_alms.py` | ✅ CURRENT | ALMS complete |
| `generate_all_phases.py` | ⚠️ OLD | Generic version |
| `run_full_pipeline.py` | ❌ ARCHIVED | Old market research |

### Phase-Specific Generation

| Script | Status | Purpose |
|--------|--------|---------|
| `generate_phase1_presolicitation.py` | ✅ CURRENT | Phase 1 only |
| `generate_phase2_solicitation.py` | ✅ CURRENT | Phase 2 only |
| `generate_phase3_evaluation.py` | ✅ CURRENT | Phase 3 only |

### Cross-Reference System

| Script | Status | Purpose |
|--------|--------|---------|
| `demo_cross_reference_system.py` | ⭐ RECOMMENDED | Learn system |
| `test_complete_system.py` | ⭐ RECOMMENDED | Quick validation |
| `quick_cross_reference_test.py` | ⭐ RECOMMENDED | 1-min check |
| `test_cross_reference_system.py` | ✅ CURRENT | Unit tests |
| `test_cross_reference_integration.py` | ✅ CURRENT | Integration tests |

### Agent-Specific Tests

| Script | Status | Purpose |
|--------|--------|---------|
| `test_acquisition_plan_agent.py` | ✅ CURRENT | Test Acq Plan agent |
| `test_igce_enhancement.py` | ✅ CURRENT | Test IGCE RAG |
| `test_pws_agent.py` | ✅ CURRENT | Test PWS agent |
| `test_soo_agent.py` | ✅ CURRENT | Test SOO agent |
| `test_sow_agent.py` | ✅ CURRENT | Test SOW agent |
| `test_qa_manager_agent.py` | ✅ CURRENT | Test QA agent |
| `test_quality_agent.py` | ✅ CURRENT | Test quality agent |
| `test_phase1_agents.py` | ✅ CURRENT | Test Phase 1 agents |
| `test_phase1_complete.py` | ✅ CURRENT | Complete Phase 1 test |

### Integration Tests

| Script | Status | Purpose |
|--------|--------|---------|
| `test_kpp_ksa_integration.py` | ✅ CURRENT | KPP/KSA integration |
| `test_qasp_integration.py` | ✅ CURRENT | QASP integration |
| `test_section_i_k.py` | ✅ CURRENT | Sections I & K |
| `test_section_lm_generation.py` | ✅ CURRENT | Sections L & M |
| `test_optional_sections.py` | ✅ CURRENT | Optional sections |
| `test_post_solicitation_tools.py` | ✅ CURRENT | Post-solicitation |

### Diagnostics & Analysis

| Script | Status | Purpose |
|--------|--------|---------|
| `analyze_tbds.py` | 🔧 ONE-TIME | TBD analysis |
| `benchmark_system.py` | 🔧 ONE-TIME | Performance benchmark |
| `diagnose_rag_extraction.py` | 🔧 ONE-TIME | RAG diagnostic |
| `test_web_search.py` | 🔧 SPECIFIC | Tavily test |

### Legacy/Archived

| Script | Status | Reason |
|--------|--------|--------|
| `run_agent_pipeline.py` | ❌ ARCHIVED | Replaced by orchestrators |
| `run_rfp_pipeline.py` | ❌ ARCHIVED | Old pipeline |
| `run_pws_pipeline.py` | ❌ ARCHIVED | Old pipeline |
| `run_soo_pipeline.py` | ❌ ARCHIVED | Old pipeline |
| `run_sow_pipeline.py` | ❌ ARCHIVED | Old pipeline |
| `run_pre_solicitation_pipeline.py` | ❌ ARCHIVED | Old pipeline |
| `run_complete_post_solicitation_pipeline.py` | ❌ ARCHIVED | Old pipeline |

---

## 🎯 Quick Decision Guide

### I want to...

**Setup RAG for the first time:**
```bash
python scripts/setup_rag_system.py
```

**Test that Docling integration works:**
```bash
python scripts/test_docling_integration.py
```

**Generate my first document:**
```bash
python examples/quick_start_example.py
```

**Learn how cross-references work:**
```bash
python scripts/demo_cross_reference_system.py
```

**Validate the system is working:**
```bash
python scripts/test_complete_system.py
```

**Generate a complete acquisition package:**
```bash
python scripts/test_full_pipeline.py
```

**Generate ALMS-specific package:**
```bash
python scripts/generate_all_phases_alms.py
```

**Test a specific agent:**
```bash
python scripts/test_[agent_name]_agent.py
```

**Add new documents to RAG:**
```bash
python scripts/add_documents_to_rag.py path/to/document.pdf
```

---

## 🧹 Cleanup Recommendations

### Scripts to Archive (Proposed)

Move to `archived_diagnostics/`:
- `analyze_tbds.py`
- `benchmark_system.py`
- `diagnose_rag_extraction.py`

Move to `archived_old_tests/`:
- `run_full_pipeline.py`
- `run_market_research.py`
- `generate_market_research_report.py`
- `generate_all_phases.py`
- `document_reference.py`
- `test_document_processor.py`
- `test_document_processing.py`
- `test_hybrid_extraction.py`
- `test_integration_workflow.py`
- `test_iterative_refinement.py`
- `test_citation_detection.py`
- `test_citation_injector.py`
- `quick_phase1_validation.py`

Keep but mark as specialized:
- `test_web_search.py`
- `test_xlsx_processing.py`
- `generate_sf33.py`

---

## 📊 Statistics

**Total Scripts:** 55
- ✅ **Production/Current:** 18 (33%)
- 🧪 **Active Tests:** 20 (36%)
- ❌ **Already Archived:** 7 (13%)
- 🔧 **Should Archive:** 10 (18%)

---

## 🔄 Migration Guide

If you need an archived script:

1. Check `archived_legacy/` or `archived_old_tests/`
2. Copy back to `scripts/` if needed
3. Review for compatibility with current system
4. Consider updating to use new features (Docling, cross-references)

---

**Last Updated:** October 28, 2025  
**Maintained By:** Auto-organization system  
**Next Review:** When adding new scripts

