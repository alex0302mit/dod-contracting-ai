# New Generation Scripts Guide

**All old scripts have been replaced with new phase-based scripts that include full cross-referencing!**

---

## 🎯 Quick Start

### Generate Complete Acquisition Package (All Phases)
```bash
export ANTHROPIC_API_KEY='your-key'
python scripts/generate_all_phases.py
```
**Runtime**: 10-15 minutes
**Output**: 23+ documents across all phases

---

## 📁 New Scripts Overview

### ⭐ **Master Script** (Recommended)

#### `generate_all_phases.py`
Generates complete acquisition package from pre-solicitation through award.

```bash
python scripts/generate_all_phases.py
```

**What it generates:**
- **Phase 1**: 4 Pre-Solicitation documents
- **Phase 2**: 13 Solicitation/RFP documents
- **Phase 3**: 6+ Evaluation & Award documents

**Total**: ~23 documents with full cross-referencing

**Runtime**: 10-15 minutes

---

### 📋 **Individual Phase Scripts**

#### `generate_phase1_presolicitation.py`
Market research and pre-solicitation documents.

```bash
python scripts/generate_phase1_presolicitation.py
```

**Generates:**
1. Sources Sought Notice
2. Request for Information (RFI)
3. Pre-Solicitation Notice
4. Industry Day Materials

**Runtime**: 2-3 minutes

---

#### `generate_phase2_solicitation.py`
Complete RFP/solicitation package.

```bash
python scripts/generate_phase2_solicitation.py
```

**Generates:**
- **Foundation**: IGCE, Acquisition Plan
- **Requirements**: PWS, QASP
- **Sections**: B, H, I, K, L, M
- **Forms**: SF-33, SF-1449, TBS Checklist

**Total**: 13 documents

**Runtime**: 5-7 minutes

**🔗 Cross-references**: Automatically references Phase 1 documents

---

#### `generate_phase3_evaluation.py`
Evaluation and award documents.

```bash
python scripts/generate_phase3_evaluation.py
```

**Generates:**
- Source Selection Plan
- Evaluation Scorecards (per vendor)
- Source Selection Decision Document (SSDD)
- SF-26 (Award/Contract Form)
- Award Notification Letters
- Debriefing Materials

**Total**: 6+ documents (depends on number of vendors)

**Runtime**: 3-5 minutes

**🔗 Cross-references**: Automatically references Phase 1 & 2 documents

---

## 🔄 Migration from Old Scripts

### Old Scripts → New Scripts Mapping

| Old Script | New Replacement | Notes |
|------------|-----------------|-------|
| `run_pre_solicitation_pipeline.py` | `generate_phase1_presolicitation.py` | ✅ Has cross-references |
| `run_rfp_pipeline.py` | `generate_phase2_solicitation.py` | ✅ Has cross-references |
| `run_pws_pipeline.py` | `generate_phase2_solicitation.py` | ✅ PWS included in Phase 2 |
| `run_sow_pipeline.py` | `generate_phase2_solicitation.py` | ✅ Can use SOW instead of PWS |
| `run_soo_pipeline.py` | `generate_phase2_solicitation.py` | ✅ Can use SOO instead of PWS |
| `run_complete_post_solicitation_pipeline.py` | `generate_phase3_evaluation.py` | ✅ Has cross-references |
| `run_agent_pipeline.py` | `generate_all_phases.py` | ✅ Complete package |

### Where Are Old Scripts?

Old scripts have been moved to: `scripts/archived_legacy/`

They still work but **don't have cross-referencing**. Use the new scripts instead!

---

## 📖 Detailed Usage Examples

### Example 1: Generate Complete Package

```bash
# Set API key
export ANTHROPIC_API_KEY='sk-ant-your-key-here'

# Generate everything
python scripts/generate_all_phases.py

# Output will be in: output/complete_acquisition_YYYYMMDD_HHMMSS/
```

**Output structure:**
```
output/complete_acquisition_20251017_100000/
├── phase1_presolicitation/
│   ├── sources_sought.md
│   ├── rfi.md
│   ├── pre_solicitation_notice.md
│   └── industry_day.md
├── phase2_solicitation/
│   ├── igce.md
│   ├── acquisition_plan.md
│   ├── pws.md
│   ├── qasp.md
│   ├── section_b.md
│   ├── section_h.md
│   ├── section_i.md
│   ├── section_k.md
│   ├── section_l.md
│   ├── section_m.md
│   ├── sf33.md
│   ├── sf1449.md
│   └── tbs_checklist.md
└── phase3_evaluation_award/
    ├── source_selection_plan.md
    ├── scorecard_vendor1.md
    ├── scorecard_vendor2.md
    ├── ssdd.md
    ├── sf26.md
    ├── award_notification.md
    └── debriefing_vendor1.md
```

---

### Example 2: Generate One Phase at a Time

```bash
# Phase 1: Pre-Solicitation
python scripts/generate_phase1_presolicitation.py
# Wait 2-3 minutes...

# Phase 2: Solicitation (will cross-reference Phase 1!)
python scripts/generate_phase2_solicitation.py
# Wait 5-7 minutes...

# Phase 3: Evaluation (will cross-reference Phases 1 & 2!)
python scripts/generate_phase3_evaluation.py
# Wait 3-5 minutes...
```

**Why use this approach?**
- Review documents between phases
- Customize configuration for each phase
- Generate only what you need

---

### Example 3: Just Generate RFP Package (Phase 2 Only)

```bash
python scripts/generate_phase2_solicitation.py
```

This generates the complete RFP without pre-solicitation or evaluation docs.

---

## ⚙️ Customization

All scripts have a clearly marked **CUSTOMIZE** section at the top:

### Phase 1 Example:
```python
# In generate_phase1_presolicitation.py
# Line ~45

project_info = {
    'program_name': 'Cloud Infrastructure Modernization',  # ← Change this
    'program_acronym': 'CIM',
    'solicitation_number': 'FA8675-25-R-0001',
    'contracting_office': 'Air Force Materiel Command',
    # ... customize all fields
}

requirements_content = """
    Your requirements here...  # ← Change this
"""
```

### Phase 2 Example:
```python
# In generate_phase2_solicitation.py
# Line ~65

project_info = {
    'program_name': 'Cloud Infrastructure Modernization',  # ← MUST MATCH PHASE 1!
    'solicitation_number': 'FA8675-25-R-0001',
    # ... customize
}

labor_categories = [  # ← Customize for IGCE
    {'category': 'Cloud Architect (Senior)', 'hours': 4160, 'rate': 185},
    # ... add your labor categories
]

materials = [  # ← Customize for IGCE
    {'description': 'AWS GovCloud Services', 'cost': 1500000},
    # ... add your materials
]
```

### Phase 3 Example:
```python
# In generate_phase3_evaluation.py
# Line ~75

vendors = [  # ← Add your actual vendors
    {
        'vendor_name': 'CloudTech Solutions Inc',
        'technical_score': 92,
        'management_score': 88,
        'past_performance': 'Excellent',
        'price': 7200000
    },
    # ... add more vendors
]

winner = {  # ← Specify winner
    'vendor_name': 'CloudTech Solutions Inc',
    'justification': 'Your justification here...'
}
```

---

## 🔗 Cross-Reference System

### How It Works

All scripts use the same **program_name** to enable automatic cross-referencing:

```python
# Phase 1
project_info = {'program_name': 'Cloud Infrastructure Modernization'}

# Phase 2 (same name!)
project_info = {'program_name': 'Cloud Infrastructure Modernization'}

# Phase 3 (same name!)
project_info = {'program_name': 'Cloud Infrastructure Modernization'}
```

When Phase 2 generates the Acquisition Plan, it automatically:
1. Looks up the latest IGCE for "Cloud Infrastructure Modernization"
2. Extracts cost data
3. Uses it in the Acquisition Plan
4. Records the reference in metadata

### Viewing Cross-References

```python
from utils.document_metadata_store import DocumentMetadataStore

store = DocumentMetadataStore()

# List all documents for your program
docs = store.list_documents(program='Cloud Infrastructure Modernization')
print(f"Total documents: {len(docs)}")

# Show cross-references
for doc in docs:
    refs = doc.get('references', {})
    if refs:
        print(f"{doc['type']} references:")
        for ref_type, ref_id in refs.items():
            print(f"  → {ref_type}")
```

---

## 📊 Performance

| Script | Documents | Typical Runtime | API Calls |
|--------|-----------|-----------------|-----------|
| Phase 1 | 4 | 2-3 min | ~12-16 |
| Phase 2 | 13 | 5-7 min | ~40-50 |
| Phase 3 | 6+ | 3-5 min | ~20-30 |
| **All Phases** | **23+** | **10-15 min** | **~70-100** |

*Runtime varies based on document complexity and API response times*

---

## 🐛 Troubleshooting

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY='your-key'
```

### "program_name mismatch - no cross-references found"
Make sure `program_name` is identical across all phases:
```python
# ✅ Correct
Phase 1: 'program_name': 'Cloud Infrastructure Modernization'
Phase 2: 'program_name': 'Cloud Infrastructure Modernization'

# ❌ Wrong
Phase 1: 'program_name': 'Cloud Infrastructure Modernization'
Phase 2: 'program_name': 'Cloud Modernization'  # Different!
```

### "ModuleNotFoundError"
Make sure you're in the correct directory:
```bash
cd "/path/to/Basic use case market research LLM automation"
python scripts/generate_all_phases.py
```

### Scripts running too slow
- Normal: 10-15 minutes for all phases
- Phase 2 is slowest (13 documents)
- You can run individual phases to save time

---

## 📚 Related Documentation

- **[HOW_TO_USE.md](HOW_TO_USE.md)** - Using individual agents directly
- **[START_HERE.md](START_HERE.md)** - Quick start guide
- **[SYSTEM_READY.md](SYSTEM_READY.md)** - System architecture
- **[WHICH_SCRIPTS_TO_USE.md](WHICH_SCRIPTS_TO_USE.md)** - Script comparison

---

## ✅ Summary

### What Changed?

**Old way** (7 separate scripts, no cross-references):
```bash
run_pre_solicitation_pipeline.py
run_rfp_pipeline.py
run_pws_pipeline.py
run_sow_pipeline.py
run_soo_pipeline.py
run_complete_post_solicitation_pipeline.py
run_agent_pipeline.py
```

**New way** (3 phase scripts + 1 master, full cross-references):
```bash
generate_phase1_presolicitation.py    # Pre-Solicitation
generate_phase2_solicitation.py       # RFP Package
generate_phase3_evaluation.py         # Evaluation & Award
generate_all_phases.py                # All at once
```

### Quick Decision Guide

**I want everything**: `generate_all_phases.py`
**I want RFP package**: `generate_phase2_solicitation.py`
**I want market research**: `generate_phase1_presolicitation.py`
**I want evaluation docs**: `generate_phase3_evaluation.py`

---

**Start generating now:**
```bash
export ANTHROPIC_API_KEY='your-key'
python scripts/generate_all_phases.py
```
