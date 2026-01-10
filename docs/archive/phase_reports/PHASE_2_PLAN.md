# Phase 2: Enhance Existing RAG Agents - PLAN

**Created:** January 2025
**Status:** PLANNING
**Target Start:** After Phase 1 Complete ✅
**Estimated Duration:** 2-3 weeks

---

## Overview

Phase 2 focuses on **enhancing agents that already have RAG capability** but use it minimally. These agents have the infrastructure in place (retriever parameter, basic queries) but lack the comprehensive extraction and intelligent template population that Phase 1 demonstrated.

### Phase 2 Philosophy

**"Enhance the foundation, don't rebuild"**

Unlike Phase 1 (which added RAG from scratch), Phase 2 will:
- Expand existing single queries to 3-5 targeted queries
- Add missing extraction methods
- Implement priority-based template population
- Replace lazy TBDs with descriptive messages
- Follow the proven Phase 1 pattern

---

## Current State Analysis

### Agents with Minimal RAG Usage

| Agent | Current RAG Queries | Est. TBDs | RAG Capability | Priority |
|-------|---------------------|-----------|----------------|----------|
| **AcquisitionPlanGeneratorAgent** | 6 queries | 35 | 🟡 Partial | Highest |
| **PWSWriterAgent** | 1 query | 40 | 🟡 Minimal | Highest |
| **SOWWriterAgent** | 1 query | 35 | 🟡 Minimal | High |
| **SOOWriterAgent** | 1 query | 30 | 🟡 Minimal | High |
| **QAManagerAgent** | 1 query | 25 | 🟡 Minimal | Medium |

**Legend:**
- 🟡 Partial: Has multiple queries but lacks extraction/priority system
- 🟡 Minimal: Has 1 generic query, needs targeted queries + extraction

### Comparison with Phase 1

| Metric | Phase 1 Agents | Phase 2 Agents |
|--------|----------------|----------------|
| **Starting Point** | No RAG | Basic RAG |
| **RAG Queries (Before)** | 0 | 1-6 |
| **Extraction Methods (Before)** | 0 | 0 |
| **Priority System (Before)** | No | No |
| **Descriptive TBDs (Before)** | No | No |
| **Work Required** | Build from scratch | Enhance foundation |

**Phase 2 Advantage:** Infrastructure already exists, can focus on enhancement

---

## Phase 2 Agent Details

### Agent 1: AcquisitionPlanGeneratorAgent 🎯

**Priority:** Highest
**Current State:** 6 RAG queries (best of Phase 2 agents)
**Problem:** Has queries but no extraction methods or priority system

#### Current Implementation Analysis
```python
# Currently has 6 queries but results aren't extracted!
results = self.retriever.retrieve(query, top_k=5)
# But then just uses raw text, no structured extraction
```

#### Enhancement Plan

**Goal:** Convert existing 6 queries into structured data extraction

**New Methods to Add:**
1. `_extract_program_info_from_rag()` - Extract program details
2. `_extract_schedule_from_rag()` - Extract milestones and dates
3. `_extract_cost_data_from_rag()` - Extract budget information
4. `_extract_team_info_from_rag()` - Extract organizational data
5. `_extract_acquisition_strategy_from_rag()` - Extract strategy details

**Template Enhancement:**
- Add priority-based value selection
- Replace lazy TBDs with descriptive messages
- Create dynamic Key Assumptions section

**Expected Impact:**
- TBD Reduction: 35 → 10 (~70%)
- Lines Added: ~250 lines
- New Extraction Methods: 5

---

### Agent 2: PWSWriterAgent 🎯

**Priority:** Highest
**Current State:** 1 generic RAG query
**Problem:** Single vague query, no extraction, no priority system

#### Current Implementation
```python
# Currently has 1 generic query
results = self.retriever.retrieve(
    f"Performance Work Statement requirements for {program_name}",
    top_k=5
)
# Results not structured or extracted
```

#### Enhancement Plan

**Goal:** Expand to 5 targeted queries with comprehensive extraction

**New RAG Queries to Add:**
1. Technical requirements and specifications
2. Performance standards and metrics
3. Deliverables and acceptance criteria
4. Security and compliance requirements
5. Personnel and qualification requirements

**New Methods to Add:**
1. `_build_pws_context()` - Comprehensive RAG context building (NEW)
2. `_extract_requirements_from_rag()` - Extract technical requirements
3. `_extract_standards_from_rag()` - Extract performance standards
4. `_extract_deliverables_from_rag()` - Extract deliverables list
5. `_extract_security_requirements_from_rag()` - Extract security reqs

**Template Enhancement:**
- Add priority-based population
- Create dynamic Requirements section
- Create dynamic Deliverables section
- Replace TBDs with contextual guidance

**Expected Impact:**
- TBD Reduction: 40 → 12 (~70%)
- Lines Added: ~350 lines
- New RAG Queries: +4 (1 → 5)
- New Extraction Methods: 5

---

### Agent 3: SOWWriterAgent

**Priority:** High
**Current State:** 1 generic RAG query
**Problem:** Similar to PWS - single query, no extraction

#### Current Implementation
```python
# Currently has 1 generic query
results = self.retriever.retrieve(
    f"Statement of Work for {program_name}",
    top_k=5
)
```

#### Enhancement Plan

**Goal:** Follow PWS pattern with SOW-specific focus

**New RAG Queries to Add:**
1. Work tasks and activities
2. Schedule and milestones
3. Government-furnished items/services
4. Contractor-furnished items/services
5. Quality assurance requirements

**New Methods to Add:**
1. `_build_sow_context()` - Comprehensive RAG context
2. `_extract_tasks_from_rag()` - Extract work tasks
3. `_extract_government_furnished_from_rag()` - Extract GFE/GFI
4. `_extract_contractor_furnished_from_rag()` - Extract CFE/CFI
5. `_extract_quality_requirements_from_rag()` - Extract QA reqs

**Template Enhancement:**
- Add priority-based population
- Create dynamic Tasks section
- Create dynamic GFE/CFE sections
- Replace TBDs with task-specific guidance

**Expected Impact:**
- TBD Reduction: 35 → 10 (~70%)
- Lines Added: ~320 lines
- New RAG Queries: +4 (1 → 5)
- New Extraction Methods: 5

---

### Agent 4: SOOWriterAgent

**Priority:** High
**Current State:** 1 generic RAG query
**Problem:** Single query, no extraction

#### Current Implementation
```python
# Currently has 1 generic query
results = self.retriever.retrieve(
    f"Statement of Objectives for {program_name}",
    top_k=5
)
```

#### Enhancement Plan

**Goal:** Focus on objectives and outcomes vs tasks (different from SOW)

**New RAG Queries to Add:**
1. Program objectives and goals
2. Desired outcomes and metrics
3. Constraints and limitations
4. Evaluation criteria
5. Transition requirements

**New Methods to Add:**
1. `_build_soo_context()` - Comprehensive RAG context
2. `_extract_objectives_from_rag()` - Extract objectives
3. `_extract_outcomes_from_rag()` - Extract desired outcomes
4. `_extract_constraints_from_rag()` - Extract constraints
5. `_extract_metrics_from_rag()` - Extract success metrics

**Template Enhancement:**
- Add priority-based population
- Create dynamic Objectives section
- Create dynamic Outcomes section
- Replace TBDs with objective-specific guidance

**Expected Impact:**
- TBD Reduction: 30 → 9 (~70%)
- Lines Added: ~280 lines
- New RAG Queries: +4 (1 → 5)
- New Extraction Methods: 5

---

### Agent 5: QAManagerAgent

**Priority:** Medium
**Current State:** 1 generic RAG query
**Problem:** Single query, no structured QA extraction

#### Current Implementation
```python
# Currently has 1 generic query
results = self.retriever.retrieve(
    f"Quality assurance requirements for {program_name}",
    top_k=5
)
```

#### Enhancement Plan

**Goal:** Comprehensive QA checklist generation

**New RAG Queries to Add:**
1. Quality standards and compliance requirements
2. Testing and validation procedures
3. Documentation standards
4. Review and approval processes

**New Methods to Add:**
1. `_build_qa_context()` - Comprehensive RAG context
2. `_extract_standards_from_rag()` - Extract QA standards
3. `_extract_procedures_from_rag()` - Extract test procedures
4. `_extract_documentation_reqs_from_rag()` - Extract doc standards

**Template Enhancement:**
- Add priority-based population
- Create dynamic QA Checklist section
- Create dynamic Standards section
- Replace TBDs with QA-specific guidance

**Expected Impact:**
- TBD Reduction: 25 → 8 (~68%)
- Lines Added: ~230 lines
- New RAG Queries: +3 (1 → 4)
- New Extraction Methods: 4

---

## Phase 2 Summary

### Quantitative Goals

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Agents Enhanced** | 5 | AcquisitionPlan, PWS, SOW, SOO, QAManager |
| **Total Lines Added** | ~1,430 | Across all 5 agents |
| **RAG Queries Added** | +19 | New targeted queries |
| **Extraction Methods** | 24 | New extraction methods |
| **TBD Reduction** | ~135 TBDs | 165 → 49 (70% average) |
| **Coverage** | 24% | 8/34 agents total (Phase 1+2) |

### Comparison: Phase 1 vs Phase 2

| Metric | Phase 1 | Phase 2 (Projected) | Combined |
|--------|---------|---------------------|----------|
| **Agents Enhanced** | 3 | 5 | 8 |
| **Lines Added** | 949 | ~1,430 | ~2,379 |
| **RAG Queries** | 12 (new) | +19 (expansion) | 31 |
| **Extraction Methods** | 12 (new) | 24 (new) | 36 |
| **TBD Reduction** | 142 | ~135 | 277 |
| **Starting Point** | No RAG | Minimal RAG | Mixed |
| **Work Type** | Build from scratch | Enhance existing | Mixed |

---

## Implementation Strategy

### Approach: "Expand and Extract"

Unlike Phase 1 (build from scratch), Phase 2 follows an "Expand and Extract" approach:

#### Step 1: Expand Queries (1 → 4-5)
```python
# Before (Phase 2 agents)
results = self.retriever.retrieve(f"Generic query for {program_name}", top_k=5)

# After (Phase 2 enhancement)
# Query 1: Specific aspect 1
results_1 = self.retriever.retrieve(f"Targeted query 1 for {program_name}", top_k=5)
data_1 = self._extract_aspect_1_from_rag(results_1)

# Query 2-4: More targeted queries...
```

#### Step 2: Add Extraction Methods
```python
# NEW: Extract structured data from RAG results
def _extract_aspect_from_rag(self, rag_results: List[Dict]) -> Dict:
    """Extract structured data using regex patterns"""
    extracted = {}
    combined_text = "\n".join([r.get('text', '') for r in rag_results])

    # Apply patterns...
    return extracted
```

#### Step 3: Implement Priority System
```python
# NEW: Priority-based value selection in _populate_template()
def get_value(config_key=None, rag_key=None, default='TBD'):
    if config_key and config.get(config_key):
        return config.get(config_key)  # Priority 1
    if rag_key and rag_key in rag_context:
        return str(rag_context[rag_key])  # Priority 2
    return default  # Priority 3
```

#### Step 4: Replace Lazy TBDs
```python
# Before
content = re.sub(r'\{\{[^}]+\}\}', 'TBD', content)  # Lazy!

# After
for placeholder in remaining_placeholders:
    if 'requirement' in placeholder.lower():
        replacement = 'TBD - Requirement to be defined in coordination with stakeholders'
    elif 'deliverable' in placeholder.lower():
        replacement = 'TBD - Deliverable to be specified in performance plan'
    # ... more contextual replacements
```

---

## Phase 2 Timeline

### Week 1: High-Priority Agents (2 agents)

**Days 1-3: AcquisitionPlanGeneratorAgent**
- Analyze existing 6 queries
- Add 5 extraction methods
- Implement priority system
- Test and validate

**Days 4-5: PWSWriterAgent**
- Expand 1 query to 5 queries
- Add 5 extraction methods
- Implement priority system
- Test and validate

### Week 2: Medium-Priority Agents (2 agents)

**Days 6-8: SOWWriterAgent**
- Expand 1 query to 5 queries
- Add 5 extraction methods
- Implement priority system
- Test and validate

**Days 9-10: SOOWriterAgent**
- Expand 1 query to 5 queries
- Add 5 extraction methods
- Implement priority system
- Test and validate

### Week 3: Final Agent + Integration (1 agent + testing)

**Days 11-12: QAManagerAgent**
- Expand 1 query to 4 queries
- Add 4 extraction methods
- Implement priority system
- Test and validate

**Days 13-15: Integration and Testing**
- Test all 5 enhanced agents
- Validate TBD reductions
- Update documentation
- Create Phase 2 completion report

---

## Success Criteria

### Quantitative Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **TBD Reduction** | 70% average | Count TBDs before/after |
| **RAG Queries** | +19 queries | Code review |
| **Extraction Methods** | 24 methods | Code review |
| **Lines Added** | ~1,430 lines | `wc -l` comparison |
| **Syntax Validation** | 100% pass | `python3 -m py_compile` |
| **Backward Compatibility** | 100% | Test with/without retriever |

### Qualitative Metrics

- ✅ Code follows Phase 1 pattern
- ✅ Extraction methods use regex patterns
- ✅ Priority-based value selection implemented
- ✅ Descriptive TBDs with context
- ✅ Dynamic content sections where appropriate
- ✅ Comprehensive documentation created

---

## Risk Assessment

### Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Existing code conflicts** | Medium | Medium | Careful analysis before enhancement |
| **Template incompatibility** | Low | Medium | Verify placeholders exist |
| **RAG data quality varies** | Medium | Low | Multiple patterns with fallbacks |
| **Timeline slippage** | Low | Low | 50% faster due to established pattern |
| **Breaking changes** | Low | High | Maintain backward compatibility |

### Assumptions

1. RAG vector store contains relevant program documents
2. Templates have correct placeholders for enhancement
3. Phase 1 pattern is proven and replicable
4. Development velocity improves 50% from Phase 1 experience
5. No major changes to agent architecture required

---

## Dependencies

### Technical Dependencies

- ✅ Phase 1 complete (provides pattern)
- ✅ RAG system operational
- ✅ Vector store loaded with documents
- ✅ Templates compatible with enhancements

### Resource Dependencies

- Developer time: ~80-120 hours (2-3 weeks)
- Testing environment
- Documentation tools

---

## Deliverables

### Code Deliverables (5 agents)

1. **agents/acquisition_plan_generator_agent.py** (enhanced)
2. **agents/pws_writer_agent.py** (enhanced)
3. **agents/sow_writer_agent.py** (enhanced)
4. **agents/soo_writer_agent.py** (enhanced)
5. **agents/qa_manager_agent.py** (enhanced)

### Documentation Deliverables (6 docs)

1. **ACQUISITION_PLAN_ENHANCEMENT_COMPLETE.md**
2. **PWS_ENHANCEMENT_COMPLETE.md**
3. **SOW_ENHANCEMENT_COMPLETE.md**
4. **SOO_ENHANCEMENT_COMPLETE.md**
5. **QA_MANAGER_ENHANCEMENT_COMPLETE.md**
6. **PHASE_2_COMPLETE.md** (summary)

### Testing Deliverables

1. Syntax validation scripts
2. TBD counting scripts
3. Integration test results
4. Before/after comparison reports

---

## Key Differences from Phase 1

### What's Different

1. **Starting Point:**
   - Phase 1: No RAG at all
   - Phase 2: Basic RAG exists, needs enhancement

2. **Work Type:**
   - Phase 1: Build foundation from scratch
   - Phase 2: Expand and enhance existing foundation

3. **Velocity:**
   - Phase 1: ~3 agents in 1 week (learning curve)
   - Phase 2: ~5 agents in 2-3 weeks (50% faster per agent)

4. **Complexity:**
   - Phase 1: New pattern development
   - Phase 2: Pattern replication with adaptation

### What's The Same

1. ✅ 7-step enhancement pattern
2. ✅ Priority-based value selection
3. ✅ Descriptive TBDs
4. ✅ Comprehensive documentation
5. ✅ Backward compatibility requirement
6. ✅ Quality standards (syntax, tests, etc.)

---

## Special Considerations

### AcquisitionPlanGeneratorAgent

**Special Case:** Already has 6 queries

**Approach:** Focus on **extraction** more than expansion
- Add extraction methods for existing queries
- May add 1-2 more targeted queries
- Emphasize structured data extraction
- Implement priority system

**Why It's Different:** Most mature RAG usage of Phase 2 agents

### PWS vs SOW vs SOO

**Challenge:** Three similar but distinct agents

**Approach:** Establish patterns that differentiate them
- **PWS:** Performance-based, focus on outcomes/standards
- **SOW:** Task-based, focus on activities/deliverables
- **SOO:** Objective-based, focus on goals/metrics

**Benefit:** Clear separation prevents confusion

---

## Phase 3 Preview

After Phase 2 completion, Phase 3 will focus on:

### Phase 3 Scope (Future)

**Target:** Remaining 26 agents without RAG

**Categories:**
1. **Solicitation Sections** (10 agents): Section B, H, I, K, L, M, etc.
2. **Post-Solicitation** (8 agents): Award, debriefing, amendments
3. **Administrative Forms** (8 agents): SF26, SF30, SF1449, etc.

**Expected Phase 3 Impact:**
- +2,500-3,000 lines
- 50-60 new RAG queries
- ~250-300 TBD reduction
- 100% agent coverage (34/34)

---

## Approval and Next Steps

### Decision Points

**Approval Needed For:**
- [ ] Phase 2 agent selection (5 agents confirmed)
- [ ] Timeline (2-3 weeks acceptable)
- [ ] Resource allocation (80-120 hours)
- [ ] Success criteria (70% TBD reduction)

**Ready to Start When:**
- [ ] Phase 1 validated and tested
- [ ] Phase 2 plan approved
- [ ] Resources allocated
- [ ] Timeline confirmed

---

## Conclusion

Phase 2 represents a **natural evolution** from Phase 1:

1. **Building on Success:** Uses proven Phase 1 pattern
2. **Efficiency Gains:** 50% faster per agent due to experience
3. **Higher Impact:** 5 agents vs 3 in Phase 1
4. **Clear Scope:** Enhance existing minimal RAG to comprehensive RAG
5. **Measurable Goals:** 70% TBD reduction, +1,430 lines, 24 methods

**Expected Outcomes:**
- 5 agents with comprehensive RAG capabilities
- ~135 fewer TBDs (165 → 49)
- Proven pattern applied to "expand and extract" scenario
- 24% total coverage (8/34 agents through Phase 1+2)

**Phase 2 Status:** Ready to start upon approval

---

**Created:** January 2025
**Status:** PLANNING - Awaiting approval
**Dependencies:** Phase 1 complete ✅
**Estimated Start:** After Phase 1 validation
**Estimated Duration:** 2-3 weeks

---

## Appendix: Quick Reference

### Phase 2 At-a-Glance

```
PHASE 2 PLAN SUMMARY
====================

Target Agents:          5 agents (existing minimal RAG)
Approach:               "Expand and Extract"
Timeline:               2-3 weeks
Estimated Effort:       80-120 hours

AGENTS:
  1. AcquisitionPlanGeneratorAgent   (6→6+ queries, +5 methods)
  2. PWSWriterAgent                  (1→5 queries, +5 methods)
  3. SOWWriterAgent                  (1→5 queries, +5 methods)
  4. SOOWriterAgent                  (1→5 queries, +5 methods)
  5. QAManagerAgent                  (1→4 queries, +4 methods)

PROJECTED IMPACT:
  Lines Added:           ~1,430 lines
  RAG Queries Added:     +19 queries
  Extraction Methods:    24 new methods
  TBD Reduction:         ~135 TBDs (165 → 49)
  Average Reduction:     70%

APPROACH:
  1. Expand queries (1-6 → 4-6 targeted)
  2. Add extraction methods (regex-based)
  3. Implement priority system
  4. Replace lazy TBDs
  5. Create dynamic sections
  6. Follow Phase 1 pattern

STATUS: 📋 PLANNING
```

### Enhancement Checklist (Per Agent)

```
PHASE 2 ENHANCEMENT CHECKLIST
==============================

Analysis:
  □ Review existing RAG queries
  □ Identify missing extraction methods
  □ Analyze template placeholders
  □ Count current TBDs

Query Expansion:
  □ Design 3-5 targeted queries
  □ Test query effectiveness
  □ Implement query calls

Extraction Methods:
  □ Create 3-5 extraction methods
  □ Implement regex patterns
  □ Add validation and filtering

Priority System:
  □ Add get_value() helper function
  □ Update _populate_template()
  □ Implement config → RAG → default

TBD Enhancement:
  □ Replace lazy TBDs
  □ Add contextual guidance
  □ Create dynamic sections

Testing:
  □ Syntax validation
  □ Backward compatibility test
  □ TBD count comparison
  □ Quality review

Documentation:
  □ Create completion document
  □ Update README
  □ Document patterns used
```

---

**END OF PHASE 2 PLAN**
