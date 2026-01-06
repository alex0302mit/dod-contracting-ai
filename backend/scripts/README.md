# Scripts Directory

**Last Updated:** October 28, 2025  
**Status:** ✅ Organized and Documented

---

## 📁 Quick Navigation

| Document | Purpose |
|----------|---------|
| **THIS FILE** | Directory overview |
| `SCRIPTS_ORGANIZATION.md` | Complete script catalog and guide |
| `CLEANUP_SUMMARY.md` | What was cleaned up and why |
| `WHICH_SCRIPTS_TO_USE.md` | Decision guide - which script to use |

---

## 🚀 Quick Start

### First Time Users

```bash
# 1. Setup RAG system
python scripts/setup_rag_system.py

# 2. Test Docling integration
python scripts/test_docling_integration.py

# 3. Generate your first document
python examples/quick_start_example.py

# 4. Learn cross-references
python scripts/demo_cross_reference_system.py
```

### Generate Documents

```bash
# Complete package (20+ documents)
python scripts/test_full_pipeline.py

# ALMS-specific package
python scripts/generate_all_phases_alms.py

# Phase 1 only (Pre-Solicitation)
python scripts/generate_phase1_presolicitation.py

# Phase 2 only (Solicitation/RFP)
python scripts/generate_phase2_solicitation.py

# Phase 3 only (Post-Solicitation)
python scripts/generate_phase3_evaluation.py
```

### Test & Validate

```bash
# Quick system validation
python scripts/test_complete_system.py

# Test RAG retrieval
python scripts/test_rag_system.py

# Test Docling processing
python scripts/test_docling_integration.py
```

---

## 📊 Directory Statistics

**Active Scripts:** 30  
**Archived Scripts:** 26  
**Archive Categories:** 4  
**Documentation Files:** 6

---

## 🗂️ Organization

### Active Scripts (In This Directory)

```
scripts/
├── 🚀 Production Scripts (6)
│   ├── setup_rag_system.py              ⭐ Setup RAG with Docling
│   ├── add_documents_to_rag.py          ⭐ Add documents to RAG
│   ├── test_full_pipeline.py            ⭐ Complete generation
│   ├── demo_cross_reference_system.py   ⭐ Learn system
│   ├── test_complete_system.py          ⭐ Quick validation
│   └── quick_cross_reference_test.py    ⭐ 1-min check
│
├── 📊 Generation Scripts (4)
│   ├── generate_all_phases_alms.py
│   ├── generate_phase1_presolicitation.py
│   ├── generate_phase2_solicitation.py
│   └── generate_phase3_evaluation.py
│
├── 🧪 Test Scripts (20+)
│   ├── test_docling_integration.py      NEW - Test Docling
│   ├── test_rag_system.py
│   ├── verify_rag_docs.py
│   ├── test_acquisition_plan_agent.py
│   ├── test_igce_enhancement.py
│   └── ... more agent tests
│
└── 📚 Documentation (2+)
    ├── README.md                        ← This file
    ├── SCRIPTS_ORGANIZATION.md          Complete guide
    ├── CLEANUP_SUMMARY.md               Cleanup details
    └── ... more docs
```

### Archive Directories

```
scripts/
└── 📦 Archives/
    ├── archived_legacy/           [7 scripts + README]
    │   └── Old pipelines (pre-cross-reference system)
    │
    ├── archived_diagnostics/      [3 scripts + README]
    │   └── One-time diagnostic tools
    │
    ├── archived_old_tests/        [13 scripts + README]
    │   └── Superseded test scripts
    │
    └── archived_specialized/      [3 scripts + README]
        └── Specialized/rarely-used scripts
```

---

## 🎯 Decision Guide

### I want to...

| Task | Script | Time |
|------|--------|------|
| **Setup RAG** | `setup_rag_system.py` | 2-5 min |
| **Test Docling** | `test_docling_integration.py` | 2 min |
| **Generate first doc** | `examples/quick_start_example.py` | 30 sec |
| **Learn system** | `demo_cross_reference_system.py` | 5 sec |
| **Validate system** | `test_complete_system.py` | 2-3 min |
| **Generate complete package** | `test_full_pipeline.py` | 15-20 min |
| **Generate ALMS package** | `generate_all_phases_alms.py` | 10-15 min |
| **Test specific agent** | `test_[agent_name]_agent.py` | 1-2 min |
| **Add documents to RAG** | `add_documents_to_rag.py` | Varies |

---

## 📖 Detailed Documentation

### Main Guides

- **`SCRIPTS_ORGANIZATION.md`** - Complete script catalog with descriptions
- **`WHICH_SCRIPTS_TO_USE.md`** - Decision guide for which script to use
- **`CLEANUP_SUMMARY.md`** - What was cleaned up and why

### Archive Documentation

- **`archived_legacy/README.md`** - Old pipeline documentation
- **`archived_diagnostics/README.md`** - Diagnostic scripts guide
- **`archived_old_tests/README.md`** - Old tests migration guide
- **`archived_specialized/README.md`** - Specialized scripts guide

### Project Documentation

- **`../HOW_TO_USE.md`** - Complete usage guide
- **`../START_HERE.md`** - Quick start guide
- **`../GETTING_STARTED.md`** - Getting started reference
- **`../examples/example_usage.py`** - Interactive examples

---

## 🔍 Finding What You Need

### By Purpose

**Setup & Configuration:**
- `setup_rag_system.py` - Initial RAG setup
- `add_documents_to_rag.py` - Add new documents
- `test_docling_integration.py` - Test Docling

**Generation:**
- `test_full_pipeline.py` - Complete package
- `generate_all_phases_alms.py` - ALMS specific
- `generate_phase[1-3]_*.py` - Phase-specific

**Testing:**
- `test_complete_system.py` - Full system test
- `test_*_agent.py` - Individual agent tests
- `test_*_integration.py` - Integration tests

**Learning:**
- `demo_cross_reference_system.py` - Cross-reference demo
- `quick_cross_reference_test.py` - Quick check
- `examples/quick_start_example.py` - First document

### By Category

See `SCRIPTS_ORGANIZATION.md` for complete categorization.

---

## ⚠️ Important Notes

### Don't Use Archived Scripts

Scripts in `archived_*/` directories are **not maintained** and should **not be used**.

**Why?**
- ❌ Missing critical features (cross-references, RAG, Docling)
- ❌ Superseded by better implementations
- ❌ Not tested or maintained

**Instead:**
- ✅ Use current alternatives (see archive README files)
- ✅ Check `SCRIPTS_ORGANIZATION.md` for recommendations

### Before Adding New Scripts

1. Check if functionality already exists
2. Consider if it should be integrated into existing scripts
3. Document the new script in `SCRIPTS_ORGANIZATION.md`
4. Add to appropriate category

---

## 🆘 Need Help?

### Can't find the right script?
→ Read `WHICH_SCRIPTS_TO_USE.md`

### Need complete documentation?
→ Read `SCRIPTS_ORGANIZATION.md`

### Want to use an archived script?
→ Read the archive's `README.md` for alternatives

### General usage questions?
→ Read `../HOW_TO_USE.md`

### First time user?
→ Read `../START_HERE.md`

---

## ✅ Quick Verification

Check that everything is working:

```bash
# Test RAG system
python scripts/test_rag_system.py

# Test Docling
python scripts/test_docling_integration.py

# Test complete system
python scripts/test_complete_system.py
```

All tests should pass! ✅

---

## 📊 Summary

**Status:** ✅ **Well-Organized**

- 30 active, current scripts
- 26 archived scripts (organized in 4 categories)
- Complete documentation for all categories
- Clear migration guides for archived scripts
- Easy navigation and decision guides

**Result:** Clean, organized, and easy to use! 🎉

---

**Last Updated:** October 28, 2025  
**Maintained:** Actively  
**Status:** Production Ready ✅

