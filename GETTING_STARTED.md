# Getting Started - DoD Acquisition Automation System

## System Status
✅ **OPERATIONAL** - All 31 agents with cross-reference capability

---

## Run Tests

### Quick Test (2-3 min)
```bash
python scripts/test_complete_system.py
```
Expected: `6/6 passed (100.0%)`

### Full Test (15-20 min)
```bash
python scripts/test_full_pipeline.py
```

---

## Generate Your First Document

### Step 1: Set API Key
```bash
export ANTHROPIC_API_KEY='your-key-here'
```

### Step 2: Generate IGCE
```python
from agents.igce_generator_agent import IGCEGeneratorAgent

agent = IGCEGeneratorAgent(api_key=your_api_key)
result = agent.execute({
    'project_info': {
        'program_name': 'Your Program',
        'solicitation_number': 'FA1234-25-R-0001',
        'estimated_value': '$5M',
        'period_of_performance': '36 months'
    },
    'labor_categories': [
        {'category': 'Senior Engineer', 'hours': 4000, 'rate': 150},
        {'category': 'Engineer', 'hours': 8000, 'rate': 100}
    ],
    'config': {'contract_type': 'Firm Fixed Price'}
})

print(result['content'])  # Full IGCE document
```

### Step 3: Generate Acquisition Plan (Cross-References IGCE)
```python
from agents.acquisition_plan_generator_agent import AcquisitionPlanGeneratorAgent

agent = AcquisitionPlanGeneratorAgent(api_key=your_api_key)
result = agent.execute({
    'project_info': {
        'program_name': 'Your Program',  # Same name!
        'solicitation_number': 'FA1234-25-R-0001',
        'description': 'Software development services',
        'estimated_value': '$5M'
    },
    'requirements_content': 'Your requirements...',
    'config': {'contract_type': 'Firm Fixed Price'}
})

# Automatically references IGCE from Step 2!
print(result['content'])
```

---

## Available Agents (31 Total)

### Phase 1: Pre-Solicitation (4 agents)
- `sources_sought_generator_agent` - Market research
- `rfi_generator_agent` - Request for Information
- `pre_solicitation_notice_generator_agent` - Pre-RFP notice
- `industry_day_generator_agent` - Vendor engagement

### Phase 2: Solicitation (17 agents)
**Foundation:**
- `igce_generator_agent` - Cost estimate
- `acquisition_plan_generator_agent` - FAR 7.105 plan

**Requirements:**
- `pws_writer_agent` - Performance Work Statement
- `sow_generator_agent` - Statement of Work
- `soo_generator_agent` - Statement of Objectives
- `qasp_generator_agent` - Quality Assurance Plan

**Solicitation Sections:**
- `section_b_generator_agent` - Supplies/Services & Prices
- `section_h_generator_agent` - Special Contract Requirements
- `section_i_generator_agent` - Contract Clauses
- `section_k_generator_agent` - Representations & Certifications
- `section_l_generator_agent` - Instructions to Offerors
- `section_m_generator_agent` - Evaluation Factors

**Forms & Documents:**
- `sf33_generator_agent` - Solicitation form
- `sf1449_generator_agent` - Solicitation/Contract form
- `tbs_checklist_generator_agent` - TBS approval checklist
- `negotiation_memo_generator_agent` - Price negotiation memo
- `dd254_generator_agent` - Security requirements

### Phase 3: Evaluation & Award (7 agents)
- `amendment_generator_agent` - Solicitation amendments
- `source_selection_plan_generator_agent` - SSP
- `evaluation_scorecard_generator_agent` - Vendor scores
- `ssdd_generator_agent` - Source Selection Decision
- `sf26_generator_agent` - Award/Contract form
- `debriefing_generator_agent` - Vendor debriefing
- `award_notification_generator_agent` - Award letters

### Support Agents (3 agents)
- `research_agent` - RAG + web search
- `report_writer_agent` - Custom reports
- `quality_agent` - Document validation
- `refinement_agent` - Document improvement

---

## Cross-Reference Flow

```
Market Research
    ↓
Sources Sought ──→ RFI ──→ Pre-Solicitation Notice
    ↓                ↓
Industry Day    Acquisition Plan
                     ↓
                   IGCE ──→ PWS/SOW/SOO
                     ↓         ↓
                Section B   QASP
                     ↓         ↓
              Section L/M ←───┘
                     ↓
                  SF-33 ──→ Amendment
                     ↓         ↓
           Source Selection ──→ Evaluation
                     ↓
                  SSDD ──→ SF-26
                     ↓
            Award Notification
```

All references are **automatic** - just use the same `program_name`!

---

## Metadata Store

All documents saved to: `data/document_metadata.json`

```python
from utils.document_metadata_store import DocumentMetadataStore

store = DocumentMetadataStore()

# Find latest IGCE for your program
igce = store.find_latest_document('igce', 'Your Program')
print(igce['extracted_data']['total_cost_formatted'])

# List all documents for program
docs = store.list_documents(program='Your Program')
print(f"Generated {len(docs)} documents")

# Get statistics
stats = store.get_statistics()
print(f"Total docs: {stats['total_documents']}")
```

---

## Documentation

- `SYSTEM_READY.md` - Complete system overview
- `TESTING_GUIDE.md` - Testing procedures
- `TEST_RESULTS_EXPLANATION.md` - Understanding test output
- `FINAL_TEST_STATUS.md` - Current system status
- `GETTING_STARTED.md` - This file

---

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY='your-key'
# Or create .env file:
echo "ANTHROPIC_API_KEY=your-key" > .env
```

### "ModuleNotFoundError"
```bash
# Make sure you're in the correct directory
cd "/path/to/Basic use case market research LLM automation"
# Should see agents/ folder
ls agents/
```

### Tests failing
```bash
# Run quick test to diagnose
python scripts/test_complete_system.py

# Check metadata store
python -c "from utils.document_metadata_store import DocumentMetadataStore; DocumentMetadataStore().print_summary()"
```

---

## Need Help?

1. Read [TESTING_GUIDE.md](TESTING_GUIDE.md) for detailed examples
2. Check [TEST_RESULTS_EXPLANATION.md](TEST_RESULTS_EXPLANATION.md) for test output interpretation
3. Review [SYSTEM_READY.md](SYSTEM_READY.md) for architecture details

---

## Summary

- ✅ 31 agents ready
- ✅ Cross-references automatic
- ✅ Metadata tracking operational
- ✅ Tests passing (100%)
- ✅ Production ready

**Generate your first acquisition document in under 5 minutes!**
