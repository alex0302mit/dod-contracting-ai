# Archived Legacy Pipelines

**Location:** `scripts/archived_legacy/`  
**Status:** ❌ Deprecated - Do Not Use

---

## Scripts in This Directory

These are the original pipeline scripts that have been replaced by better implementations with cross-reference support and modern orchestrators.

### `run_agent_pipeline.py`
- **Old Purpose:** Generic agent pipeline runner
- **Replaced By:** `examples/example_usage.py` and orchestrators
- **Why Deprecated:** No cross-reference support, replaced by orchestrator pattern

### `run_complete_post_solicitation_pipeline.py`
- **Old Purpose:** Post-solicitation document generation
- **Replaced By:** `test_full_pipeline.py` (Phase 3)
- **Why Deprecated:** Old workflow, no cross-references

### `run_pre_solicitation_pipeline.py`
- **Old Purpose:** Pre-solicitation document generation
- **Replaced By:** `generate_phase1_presolicitation.py`
- **Why Deprecated:** Old workflow, no DocumentMetadataStore

### `run_pws_pipeline.py`
- **Old Purpose:** Performance Work Statement pipeline
- **Replaced By:** PWS agent with orchestrators
- **Why Deprecated:** No cross-references, old template system

### `run_rfp_pipeline.py`
- **Old Purpose:** RFP package generation
- **Replaced By:** `test_full_pipeline.py` or `generate_phase2_solicitation.py`
- **Why Deprecated:** No cross-reference system, old orchestrator

### `run_soo_pipeline.py`
- **Old Purpose:** Statement of Objectives pipeline
- **Replaced By:** SOO agent with orchestrators
- **Why Deprecated:** No cross-references

### `run_sow_pipeline.py`
- **Old Purpose:** Statement of Work pipeline
- **Replaced By:** SOW agent with orchestrators
- **Why Deprecated:** No cross-references

---

## Why These Were Deprecated

**Key Issues with Legacy Pipelines:**

1. ❌ **No Cross-Reference System**
   - Documents generated independently
   - No automatic data propagation
   - Manual data entry required

2. ❌ **No DocumentMetadataStore**
   - Can't track generated documents
   - Can't reference data from previous docs
   - No validation of document relationships

3. ❌ **Old Template System**
   - Basic placeholder replacement
   - No RAG integration
   - High TBD count (100-200+ per doc)

4. ❌ **Outdated Orchestration**
   - Hardcoded workflows
   - Limited flexibility
   - Difficult to maintain

---

## Current Alternatives

### For Complete Package Generation

**Use:** `test_full_pipeline.py`
```bash
python scripts/test_full_pipeline.py
```

**Generates:** 20+ documents with full cross-references
- Pre-Solicitation (6 docs)
- Solicitation (9 docs)
- Post-Solicitation (3 docs)
- Award (3 docs)

### For Phase-Specific Generation

**Phase 1 (Pre-Solicitation):**
```bash
python scripts/generate_phase1_presolicitation.py
```

**Phase 2 (Solicitation/RFP):**
```bash
python scripts/generate_phase2_solicitation.py
```

**Phase 3 (Post-Solicitation):**
```bash
python scripts/generate_phase3_evaluation.py
```

### For Individual Documents

**Use:** Individual agents with orchestrators
```python
from agents.pws_writer_agent import PWSWriterAgent
from rag.retriever import Retriever

agent = PWSWriterAgent(api_key=api_key, retriever=retriever)
result = agent.execute(task)
```

See `examples/example_usage.py` for complete examples.

---

## Migration Path

If you were using legacy pipelines:

### From `run_rfp_pipeline.py`
**→ Use:** `test_full_pipeline.py` or `generate_phase2_solicitation.py`

**Benefits:**
- ✅ Full cross-references
- ✅ RAG-enhanced (75% fewer TBDs)
- ✅ Metadata tracking
- ✅ Document validation

### From `run_pre_solicitation_pipeline.py`
**→ Use:** `generate_phase1_presolicitation.py`

**Benefits:**
- ✅ Cross-reference support
- ✅ DocumentMetadataStore integration
- ✅ Modern orchestrators

### From Individual Pipelines (PWS, SOW, SOO)
**→ Use:** Individual agents with orchestrators

**Benefits:**
- ✅ RAG integration
- ✅ Cross-references
- ✅ Better templates
- ✅ Quality improvements

---

## Can These Be Restored?

**No - Should Not Be Used**

**Reasons:**
1. Lack critical features (cross-references, metadata tracking)
2. Superseded by better implementations
3. Not maintained or tested
4. Missing RAG enhancements

**If you need old functionality:**
- Current scripts provide all features and more
- Use current alternatives listed above
- See `SCRIPTS_ORGANIZATION.md` for guidance

---

## Documentation

**See Also:**
- `SCRIPTS_ORGANIZATION.md` - Complete script organization
- `WHICH_SCRIPTS_TO_USE.md` - Which scripts to use guide
- `HOW_TO_USE.md` - Complete usage guide
- `examples/example_usage.py` - Interactive examples

---

**Archived:** Pre-October 2025  
**Reason:** Replaced by modern cross-reference system  
**Status:** Deprecated - Do not use  
**Alternative:** See current scripts listed above

---

**⚠️ IMPORTANT:** Do not use these scripts. They are kept only for historical reference.

