# Which Scripts to Use - Cross-Reference System Guide

## ✅ Scripts That USE the Cross-Reference System (Updated)

These scripts use the **DocumentMetadataStore** and generate documents with automatic cross-referencing:

---

### 🎯 **RECOMMENDED: Production-Ready Scripts**

#### 1. **`demo_cross_reference_system.py`** ⭐ BEST FOR LEARNING
**Purpose**: Simple demonstration of cross-reference workflow
**What it does**: Generates IGCE → Acquisition Plan with cross-references
**Runtime**: 5 seconds
**Use when**: Learning how the system works

```bash
python scripts/demo_cross_reference_system.py
```

**Output:**
- `output/demo_igce_alms.md`
- `output/demo_acquisition_plan_alms.md`
- `data/document_metadata.json` (updated)

---

#### 2. **`test_full_pipeline.py`** ⭐ BEST FOR COMPLETE GENERATION
**Purpose**: Generate ALL 31 document types end-to-end
**What it does**: Complete acquisition lifecycle with full cross-referencing
**Runtime**: 15-20 minutes
**Use when**: Generating complete acquisition package

```bash
python scripts/test_full_pipeline.py
```

**Generates:**
- 6 Pre-Solicitation documents
- 9 Solicitation documents (including IGCE, Acq Plan, PWS, Sections L/M, etc.)
- 3 Post-Solicitation documents
- 3 Award documents
- Full cross-reference chain with validation

**Output folder:** `output/full_pipeline_test_YYYYMMDD_HHMMSS/`

---

#### 3. **`test_complete_system.py`** ⭐ BEST FOR QUICK VALIDATION
**Purpose**: Quick test of core 6 agents
**What it does**: Tests Phase 1 + Phase 2 agents with cross-references
**Runtime**: 2-3 minutes
**Use when**: Verifying system works before full generation

```bash
python scripts/test_complete_system.py
```

**Tests:**
- Sources Sought, RFI, Pre-Solicitation, Industry Day
- IGCE, Acquisition Plan
- Cross-reference validation (100% integrity check)

---

#### 4. **`quick_cross_reference_test.py`**
**Purpose**: Minimal cross-reference test
**What it does**: Quick IGCE → Acquisition Plan test
**Runtime**: 1 minute
**Use when**: Quick system check

```bash
python scripts/quick_cross_reference_test.py
```

---

#### 5. **`examples/quick_start_example.py`** ⭐ EASIEST START
**Purpose**: Generate your first document
**What it does**: Generates one IGCE with metadata
**Runtime**: 30 seconds
**Use when**: First time using the system

```bash
python examples/quick_start_example.py
```

**Output:** `output/quick_start_igce.md`

---

#### 6. **`examples/example_usage.py`** ⭐ INTERACTIVE LEARNING
**Purpose**: Interactive examples menu
**What it does**: Choose from 3 different usage patterns
**Runtime**: Varies (2-5 minutes)
**Use when**: Learning different ways to use the system

```bash
python examples/example_usage.py
```

**Menu options:**
1. Generate complete RFP package (orchestrator)
2. Generate specific documents (individual agents)
3. Check cross-references in metadata store

---

### 📊 **Test & Validation Scripts**

#### 7. **`test_section_i_k.py`**
**Purpose**: Test Section I & K generators
**What it does**: Tests contract clauses and representations
**Uses cross-references**: Yes (Section I references Section B)

```bash
python scripts/test_section_i_k.py
```

---

#### 8. **`test_cross_reference_system.py`**
**Purpose**: Test cross-reference infrastructure
**What it does**: Unit tests for DocumentMetadataStore

```bash
python scripts/test_cross_reference_system.py
```

---

#### 9. **`test_cross_reference_integration.py`**
**Purpose**: Integration tests for cross-references
**What it does**: Tests multiple agents working together

```bash
python scripts/test_cross_reference_integration.py
```

---

## ❌ Scripts That DON'T Use Cross-Reference System (Legacy)

These scripts are older and **don't use the DocumentMetadataStore**. They still work but won't have automatic cross-referencing:

### Legacy Scripts (Not Recommended)

#### `run_rfp_pipeline.py`
- **Status**: Old version
- **Issue**: Doesn't use DocumentMetadataStore
- **Alternative**: Use `test_full_pipeline.py` or `examples/example_usage.py` instead

#### `run_pws_pipeline.py`
- **Status**: Old version
- **Alternative**: Use individual PWS agent with cross-references (see HOW_TO_USE.md)

#### `run_sow_pipeline.py`
- **Status**: Old version
- **Alternative**: Use individual SOW agent

#### `run_soo_pipeline.py`
- **Status**: Old version
- **Alternative**: Use individual SOO agent

#### `run_pre_solicitation_pipeline.py`
- **Status**: Old version
- **Alternative**: Use `test_full_pipeline.py` or Pre-Solicitation Orchestrator

#### `run_complete_post_solicitation_pipeline.py`
- **Status**: Old version
- **Alternative**: Use `test_full_pipeline.py`

#### `run_agent_pipeline.py`
- **Status**: Generic old pipeline
- **Alternative**: Use `examples/example_usage.py`

#### `run_full_pipeline.py`
- **Status**: Market research only (different system)
- **Purpose**: Original market research filler (not part of acquisition docs)

#### `run_market_research.py`
- **Status**: Market research only (different system)

---

## 🎯 Quick Decision Guide

### I want to...

**Generate my first document (30 seconds)**
```bash
python examples/quick_start_example.py
```

**Learn how the system works (5 min)**
```bash
python scripts/demo_cross_reference_system.py
```

**Test that everything works (2 min)**
```bash
python scripts/test_complete_system.py
```

**Generate a complete RFP package (5 min)**
```bash
python examples/example_usage.py
# Choose option 1
```

**Generate ALL acquisition documents (20 min)**
```bash
python scripts/test_full_pipeline.py
```

**Generate specific documents with code (flexible)**
See [HOW_TO_USE.md](HOW_TO_USE.md) - Option 2: Individual Agents

---

## 📋 Comparison Table

| Script | Runtime | Documents | Cross-Refs | Best For |
|--------|---------|-----------|------------|----------|
| `quick_start_example.py` | 30s | 1 | ✅ | First time users |
| `demo_cross_reference_system.py` | 5s | 2 | ✅ | Learning |
| `test_complete_system.py` | 2-3m | 6 | ✅ | Validation |
| `example_usage.py` | 2-5m | Varies | ✅ | Interactive learning |
| `test_full_pipeline.py` | 15-20m | 20+ | ✅ | Complete package |
| Legacy scripts | Varies | Varies | ❌ | Not recommended |

---

## 🚀 Recommended Workflow

### For First-Time Users:
```bash
# 1. Quick start (30 seconds)
python examples/quick_start_example.py

# 2. See how cross-references work (5 seconds)
python scripts/demo_cross_reference_system.py

# 3. Interactive examples (2-5 minutes)
python examples/example_usage.py
```

### For Production Use:
```bash
# Option A: Generate specific documents
# Use individual agents (see HOW_TO_USE.md)

# Option B: Generate complete package
python scripts/test_full_pipeline.py

# Option C: Use orchestrators in your code
# See examples/example_usage.py - Option 1
```

---

## 📖 Related Documentation

- **[HOW_TO_USE.md](HOW_TO_USE.md)** - Complete usage guide with code examples
- **[START_HERE.md](START_HERE.md)** - Quick start for new users
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Quick reference card
- **[SYSTEM_READY.md](SYSTEM_READY.md)** - Full system architecture
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing procedures

---

## ✅ Summary

**Use these scripts (they have cross-references):**
1. ✅ `examples/quick_start_example.py` - Your first document
2. ✅ `scripts/demo_cross_reference_system.py` - Learn the system
3. ✅ `scripts/test_complete_system.py` - Quick validation
4. ✅ `examples/example_usage.py` - Interactive examples
5. ✅ `scripts/test_full_pipeline.py` - Complete generation

**Avoid these scripts (they're old):**
- ❌ `run_rfp_pipeline.py`
- ❌ `run_pws_pipeline.py`
- ❌ `run_sow_pipeline.py`
- ❌ `run_soo_pipeline.py`
- ❌ `run_pre_solicitation_pipeline.py`
- ❌ `run_complete_post_solicitation_pipeline.py`
- ❌ `run_agent_pipeline.py`

---

**Start now:**
```bash
export ANTHROPIC_API_KEY='your-key'
python examples/quick_start_example.py
```
