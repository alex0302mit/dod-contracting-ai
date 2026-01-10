# 🎉 NEW: Phase-Based Generation Scripts

**All scripts have been updated with full cross-referencing!**

---

## 🚀 Quick Start (30 seconds)

```bash
# Set your API key
export ANTHROPIC_API_KEY='your-anthropic-key-here'

# Generate complete acquisition package (23+ documents)
python scripts/generate_all_phases.py
```

**That's it!** You'll get 23+ cross-referenced documents in 10-15 minutes.

---

## 📋 New Scripts

### 1. **Complete Package** (Recommended)
```bash
python scripts/generate_all_phases.py
```
- Generates ALL 23+ documents across all phases
- Runtime: 10-15 minutes
- Output: Complete acquisition package

### 2. **Phase 1: Pre-Solicitation**
```bash
python scripts/generate_phase1_presolicitation.py
```
- 4 market research documents
- Runtime: 2-3 minutes

### 3. **Phase 2: Solicitation/RFP**
```bash
python scripts/generate_phase2_solicitation.py
```
- 13 RFP documents (IGCE, Acquisition Plan, PWS, Sections, Forms)
- Runtime: 5-7 minutes
- **Automatically cross-references Phase 1**

### 4. **Phase 3: Evaluation & Award**
```bash
python scripts/generate_phase3_evaluation.py
```
- 6+ evaluation and award documents
- Runtime: 3-5 minutes
- **Automatically cross-references Phases 1 & 2**

---

## 📖 Complete Guide

See **[NEW_SCRIPTS_GUIDE.md](NEW_SCRIPTS_GUIDE.md)** for:
- Detailed usage examples
- Customization instructions
- Cross-reference system explanation
- Troubleshooting

---

## ✨ What's New?

### ✅ Full Cross-Referencing
All documents automatically reference each other:
- Acquisition Plan references IGCE
- PWS references IGCE and Acquisition Plan
- Section M references PWS and QASP
- SSDD references all evaluation scorecards
- And much more!

### ✅ Phase-Based Organization
Documents organized by acquisition lifecycle phase:
1. Phase 1: Pre-Solicitation (Market Research)
2. Phase 2: Solicitation/RFP
3. Phase 3: Evaluation & Award

### ✅ Easy Customization
Each script has a clearly marked section for customizing:
- Program information
- Requirements
- Labor categories (IGCE)
- Vendor data (evaluation)

### ✅ Clean Output Structure
```
output/complete_acquisition_YYYYMMDD_HHMMSS/
├── phase1_presolicitation/
├── phase2_solicitation/
└── phase3_evaluation_award/
```

---

## 🔄 Migration from Old Scripts

| Old Script | New Script |
|------------|------------|
| `run_pre_solicitation_pipeline.py` | `generate_phase1_presolicitation.py` |
| `run_rfp_pipeline.py` | `generate_phase2_solicitation.py` |
| `run_pws_pipeline.py` | `generate_phase2_solicitation.py` |
| All others | `generate_all_phases.py` |

Old scripts are in: `scripts/archived_legacy/`

---

## 📚 Documentation

- **[NEW_SCRIPTS_GUIDE.md](NEW_SCRIPTS_GUIDE.md)** - Complete usage guide
- **[HOW_TO_USE.md](HOW_TO_USE.md)** - Using agents directly
- **[START_HERE.md](START_HERE.md)** - Quick start
- **[SYSTEM_READY.md](SYSTEM_READY.md)** - System architecture

---

## 🎯 Examples

### Generate Complete Package
```bash
python scripts/generate_all_phases.py
```

### Generate Just RFP
```bash
python scripts/generate_phase2_solicitation.py
```

### Generate One Phase at a Time
```bash
python scripts/generate_phase1_presolicitation.py
python scripts/generate_phase2_solicitation.py  # Auto cross-references Phase 1!
python scripts/generate_phase3_evaluation.py     # Auto cross-references Phases 1 & 2!
```

---

**Start now:**
```bash
export ANTHROPIC_API_KEY='your-key'
python scripts/generate_all_phases.py
```

**Happy automating!** 🚀
