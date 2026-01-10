# Guide to Implementing Remaining Agents

**Status:** 20/40 agents complete (50%)
**Remaining:** 20 agents to implement
**Est. Time:** ~4-8 hours (15 min/agent)

---

## Summary of Completed Work

### ✅ Completed Agents (18 total)

**Phase 1 - Pre-Solicitation (4/4 = 100%)**
1. Sources Sought Generator ✅
2. RFI Generator ✅
3. Pre-Solicitation Notice Generator ✅
4. Industry Day Generator ✅

**Phase 2 - Solicitation (13/13 = 100%)**
5. IGCE Generator ✅
6. Acquisition Plan Generator ✅
7. PWS Writer Agent ✅
8. SOW Writer Agent ✅
9. SOO Writer Agent ✅
10. QASP Generator ✅
11. Section L Generator ✅
12. Section M Generator ✅
13. Section B Generator ✅
14. Section H Generator ✅
15. Section I Generator ✅
16. Section K Generator ✅
17. SF-33 Generator ✅

**Phase 3 - Post-Solicitation (1/9 = 11%)**
18. Q&A Manager ✅

---

## Agents Needing Implementation (20)

### Phase 3 - Critical Path (8 agents)
- Amendment Generator
- Source Selection Plan Generator
- Evaluation Scorecard Generator
- SSDD Generator
- SF-26 Generator
- Debriefing Generator
- Award Notification Generator
- PPQ Generator

### Support Agents (3 agents)
- Report Writer Agent
- Quality Agent
- Refinement Agent

### Additional Agents (9 agents - if they exist)
- Market Research Report Generator
- Proposal Evaluation Agent
- Contract Administration Agent
- Performance Monitoring Agent
- Close-out Agent
- Protest Response Agent
- Past Performance Questionnaire
- CPAR Generator
- Others as discovered

---

## Implementation Template

### For Agents With execute() Method

```python
# STEP 1: Add imports at top of file
from utils.document_metadata_store import DocumentMetadataStore
from utils.document_extractor import DocumentDataExtractor

# STEP 2: In execute() method, add cross-reference lookup
def execute(self, task: Dict) -> Dict:
    # ... existing code ...
    program_name = task.get('program_name') or project_info.get('program_name', 'Unknown')

    # NEW: Cross-reference lookup
    if program_name != 'Unknown':
        try:
            print("\n🔍 Looking up cross-referenced documents...")
            metadata_store = DocumentMetadataStore()

            # Look for relevant documents (customize based on agent needs)
            latest_pws = metadata_store.find_latest_document('pws', program_name)
            latest_igce = metadata_store.find_latest_document('igce', program_name)
            # Add more as needed

            if latest_pws:
                print(f"✅ Found PWS: {latest_pws['id']}")
                project_info['pws_data'] = latest_pws['extracted_data']
                self._pws_reference = latest_pws['id']
            else:
                self._pws_reference = None

            # Repeat for other documents...

        except Exception as e:
            print(f"⚠️  Cross-reference lookup failed: {str(e)}")
            self._pws_reference = None

    # ... rest of execute() logic ...

    # STEP 3: Before return, add metadata saving
    if program_name != 'Unknown':
        try:
            print("\n💾 Saving document metadata...")
            metadata_store = DocumentMetadataStore()

            extracted_data = {
                # Add agent-specific fields
                'field1': value1,
                'field2': value2,
            }

            references = {}
            if hasattr(self, '_pws_reference') and self._pws_reference:
                references['pws'] = self._pws_reference
            # Add more references as needed

            doc_id = metadata_store.save_document(
                doc_type='agent_doc_type',  # e.g., 'amendment', 'ssdd', etc.
                program=program_name,
                content=content,
                file_path=output_path,
                extracted_data=extracted_data,
                references=references
            )

            print(f"✅ Metadata saved: {doc_id}")

        except Exception as e:
            print(f"⚠️  Failed to save metadata: {str(e)}")

    return {
        'status': 'success',
        # ... rest of return dict ...
    }
```

---

## Agent-Specific Cross-Reference Needs

### Section I Generator
**Cross-references:** Section B (contract type)
**Saves:** Clause list, contract type
**Status:** Imports added ✅, needs execute() update

### Section K Generator
**Cross-references:** None (representations are standard)
**Saves:** Required representations list
**Status:** Imports added ✅, needs execute() update

### Amendment Generator
**Cross-references:**
- Original PWS/SOW/SOO
- Q&A document (changes required)
- Section L/M (if dates change)
**Saves:** Amendment number, changes list, effective date
**Complexity:** HIGH - needs to track what changed

### Source Selection Plan Generator
**Cross-references:**
- Section M (evaluation factors)
- Acquisition Plan (timeline)
**Saves:** Evaluation team, process, schedule
**Complexity:** MEDIUM

### Evaluation Scorecard Generator
**Cross-references:**
- Section M (evaluation criteria, weights)
- PWS/SOW/SOO (technical requirements)
**Saves:** Scorecard template, scoring guidelines
**Complexity:** HIGH - complex evaluation logic

### SSDD Generator (Source Selection Decision Document)
**Cross-references:**
- Evaluation scorecards (proposal scores)
- IGCE (cost comparison)
- Section M (methodology)
**Saves:** Award decision, justification, scores
**Complexity:** HIGH - synthesizes all evaluation data

### SF-26 Generator (Award/Contract)
**Cross-references:**
- SSDD (award decision)
- IGCE (final negotiated price)
- All solicitation documents
**Saves:** Contract details, awardee, final price
**Complexity:** MEDIUM

### Debriefing Generator
**Cross-references:**
- Evaluation scorecards (offeror's scores)
- SSDD (award rationale)
**Saves:** Debriefing content, areas for improvement
**Complexity:** MEDIUM

### Award Notification Generator
**Cross-references:**
- SF-26 (contract details)
- SSDD (decision)
**Saves:** Notification details, distribution list
**Complexity:** LOW

### PPQ Generator (Past Performance Questionnaire)
**Cross-references:**
- PWS/SOW (requirements completed)
- QASP (performance data)
**Saves:** Performance ratings, narrative
**Complexity:** MEDIUM

---

## Quick Start Commands

### Test Individual Agent
```python
# Example for Section I
from agents.section_i_generator_agent import SectionIGeneratorAgent

agent = SectionIGeneratorAgent(api_key=API_KEY)
result = agent.execute({
    'solicitation_info': {'program_name': 'TEST_PROGRAM'},
    'config': {'contract_type': 'ffp'}
})

# Verify metadata saved
from utils.document_metadata_store import DocumentMetadataStore
store = DocumentMetadataStore()
doc = store.find_latest_document('section_i', 'TEST_PROGRAM')
print(f"Saved: {doc is not None}")
```

### Batch Test All Implemented Agents
```bash
python scripts/quick_cross_reference_test.py
```

---

## Extraction Methods Needed

Add these to `utils/document_extractor.py` as you implement agents:

```python
def extract_amendment_data(self, content: str) -> Dict:
    return {
        'amendment_number': self._extract_amendment_number(content),
        'changes': self._extract_changes_list(content),
        'effective_date': self._extract_date(content, 'effective')
    }

def extract_ssdd_data(self, content: str) -> Dict:
    return {
        'awardee': self._extract_awardee(content),
        'final_price': self._extract_price(content),
        'technical_score': self._extract_score(content, 'technical'),
        'justification': self._extract_justification(content)
    }

def extract_scorecard_data(self, content: str) -> Dict:
    return {
        'evaluation_factors': self._extract_eval_factors(content),
        'scores': self._extract_scores(content),
        'strengths': self._extract_strengths(content),
        'weaknesses': self._extract_weaknesses(content)
    }

# Add more as needed for each agent...
```

---

## Priority Implementation Order

### Tier 1: Complete Critical Path (6 agents, ~2 hours)
1. ~~**Section I**~~ ✅ COMPLETE
2. ~~**Section K**~~ ✅ COMPLETE
3. **Amendment Generator** - 20 min
4. **Evaluation Scorecard** - 20 min
5. **SSDD Generator** - 25 min
6. **SF-26 Generator** - 20 min

### Tier 2: Close Award Process (3 agents, ~45 min)
7. **Source Selection Plan** - 15 min
8. **Debriefing Generator** - 15 min
9. **Award Notification** - 15 min

### Tier 3: Support Tools (3 agents, ~1 hour)
10. **Report Writer Agent** - 20 min
11. **Quality Agent** - 20 min
12. **Refinement Agent** - 20 min

### Tier 4: Optional Enhancements (remaining agents)
- Market Research Generator
- PPQ Generator
- Additional support agents

---

## Testing Checklist

For each agent implemented:
- [ ] Imports added (DocumentMetadataStore, DocumentDataExtractor)
- [ ] Cross-reference lookup in execute()
- [ ] Metadata saving before return
- [ ] Test with quick_cross_reference_test.py
- [ ] Verify document appears in metadata store
- [ ] Check references are correct

---

## Common Patterns

### Pattern 1: Simple Agent (Sections H/I/K)
- Minimal cross-references
- Standard template population
- Quick implementation (~10-15 min)

### Pattern 2: Complex Agent (SSDD, Scorecard)
- Multiple cross-references
- Data aggregation from many sources
- Custom extraction logic needed (~20-30 min)

### Pattern 3: Sequential Agent (Amendment)
- References previous version
- Tracks changes over time
- Versioning considerations (~20-25 min)

---

## Success Metrics

### Phase 1: Pre-Solicitation
- ✅ 100% complete (4/4 agents)

### Phase 2: Solicitation
- ✅ 100% complete (13/13 agents) 🎉

### Phase 3: Post-Solicitation
- ⚠️ 11% complete (1/9 agents)
- Target: 100% (all critical path agents)

### Overall System
- Current: 50% (20/40 agents) 🎉
- After Tier 1: 65% (26/40 agents)
- After Tier 2: 73% (29/40 agents)
- After Tier 3: 80% (32/40 agents)

---

## Next Steps

1. ~~**Finish Section I & K**~~ ✅ COMPLETE
2. **Implement Tier 1 agents** (2 hours)
3. **Test full pipeline** (30 min)
4. **Implement Tier 2 agents** (45 min)
5. **Final system test** (30 min)

**Total Time to 80% Complete: ~4 hours**

---

## Resources

- **Pattern Examples:** See any completed agent (e.g., `pws_writer_agent.py`)
- **Test Scripts:** `scripts/test_cross_reference_system.py`
- **Documentation:** `CROSS_REFERENCE_IMPLEMENTATION_SUMMARY.md`
- **Test Results:** `TEST_RESULTS.md`

---

**Last Updated:** October 17, 2025
**Status:** 20/40 agents complete (50%) 🎉
**Phase 2 Solicitation:** 100% COMPLETE ✅
**Next Target:** 32/40 agents (80%) - achievable in ~4 hours
