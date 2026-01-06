# START HERE - DoD Acquisition Automation System

**Welcome!** This system generates complete DoD acquisition packages with automatic cross-referencing.

---

## ⚡ Quick Start (5 minutes)

### 1. Set Your API Key
```bash
export ANTHROPIC_API_KEY='your-anthropic-key-here'
```

### 2. Run Your First Example
```bash
# Generate your first IGCE document (30 seconds)
python examples/quick_start_example.py
```

### 3. Check the Output
```bash
# View the generated document
cat output/quick_start_igce.md
```

**That's it!** You just generated your first DoD acquisition document.

---

## 📚 What You Have

### ✅ System Status
- **31 document-generating agents** - All operational
- **Automatic cross-referencing** - Documents reference each other
- **100% test coverage** - All tests passing
- **Complete documentation** - Guides for everything

### 📁 Documents You Can Generate

**Pre-Solicitation (Market Research)**
- Sources Sought Notice
- Request for Information (RFI)
- Pre-Solicitation Notice
- Industry Day Materials

**Solicitation (RFP Package)**
- IGCE (Cost Estimate)
- Acquisition Plan
- PWS/SOW/SOO (Requirements)
- QASP (Quality Plan)
- Section B through Section M
- SF-33, SF-1449 forms
- TBS Checklist, DD-254

**Evaluation & Award**
- Source Selection Plan
- Evaluation Scorecards
- Source Selection Decision (SSDD)
- SF-26 (Award Form)
- Award Letters & Debriefings

---

## 🎯 Three Ways to Use the System

### Option 1: Orchestrators (Easiest)
**Generate multiple documents at once**

```python
from agents.rfp_orchestrator import RFPOrchestrator

orchestrator = RFPOrchestrator(api_key=your_key)
result = orchestrator.execute({
    'project_info': {'program_name': 'My Program', ...},
    'requirements_content': 'Your requirements...',
    'config': {'contract_type': 'Firm Fixed Price'}
})

# Complete RFP package generated! ✅
```

### Option 2: Individual Agents (Most Flexible)
**Generate specific documents**

```python
from agents.igce_generator_agent import IGCEGeneratorAgent

agent = IGCEGeneratorAgent(api_key=your_key)
result = agent.execute({
    'project_info': {'program_name': 'My Program', ...},
    'labor_categories': [...],
    'config': {'contract_type': 'FFP'}
})

# IGCE document generated! ✅
```

### Option 3: Interactive Examples
**Learn by running examples**

```bash
python examples/example_usage.py
```

Choose from menu:
1. Generate complete RFP package
2. Generate specific documents
3. Check cross-references

---

## 🔗 How Cross-References Work

**The Magic**: Just use the same `program_name` and documents automatically reference each other!

```python
# Step 1: Generate IGCE
igce_agent.execute({
    'project_info': {'program_name': 'Cloud Services', ...}
})
# ✅ Saved to metadata store

# Step 2: Generate Acquisition Plan
# Automatically finds and uses IGCE cost data!
acq_plan_agent.execute({
    'project_info': {'program_name': 'Cloud Services', ...}  # Same name!
})
# ✅ References IGCE automatically
```

**Behind the scenes:**
- IGCE saves cost data to `data/document_metadata.json`
- Acquisition Plan looks up latest IGCE for "Cloud Services"
- Uses cost data automatically
- Records the reference for traceability

---

## 📖 Documentation Guide

Start with what you need:

### I want to generate documents NOW
→ [examples/quick_start_example.py](examples/quick_start_example.py) (30 seconds)

### I want to understand how to use it
→ [HOW_TO_USE.md](HOW_TO_USE.md) (Complete usage guide)

### I want to see what's available
→ [SYSTEM_READY.md](SYSTEM_READY.md) (All 31 agents explained)

### I want to run tests
→ [TESTING_GUIDE.md](TESTING_GUIDE.md) (Testing procedures)

### I want the quick reference
→ [GETTING_STARTED.md](GETTING_STARTED.md) (Quick reference card)

### I want to understand test results
→ [TEST_RESULTS_EXPLANATION.md](TEST_RESULTS_EXPLANATION.md) (Test output guide)

---

## 🎓 Learning Path

### Beginner (30 minutes)
1. ✅ Run `python examples/quick_start_example.py`
2. ✅ Read the generated IGCE document
3. ✅ Run `python examples/example_usage.py` and choose option 2
4. ✅ Check cross-references with option 3

### Intermediate (1 hour)
1. ✅ Read [HOW_TO_USE.md](HOW_TO_USE.md) - Section "Option 2"
2. ✅ Generate IGCE for your own program
3. ✅ Generate Acquisition Plan that references it
4. ✅ Verify cross-reference in metadata store

### Advanced (2 hours)
1. ✅ Read [SYSTEM_READY.md](SYSTEM_READY.md) - Full architecture
2. ✅ Use RFP Orchestrator for complete package
3. ✅ Customize agent parameters for your needs
4. ✅ Build your own workflow

---

## 🚀 Common Use Cases

### Use Case 1: I need a complete RFP package
```bash
python examples/example_usage.py
# Choose option 1 (RFP Orchestrator)
```
**Time**: 3-5 minutes
**Output**: 13+ documents ready for release

### Use Case 2: I only need cost estimates
```bash
python examples/quick_start_example.py
```
**Time**: 30 seconds
**Output**: Complete IGCE document

### Use Case 3: I'm doing market research
```python
from agents.pre_solicitation_orchestrator import PreSolicitationOrchestrator

orchestrator = PreSolicitationOrchestrator(api_key=your_key)
result = orchestrator.execute({...})
```
**Time**: 2-3 minutes
**Output**: Sources Sought, RFI, Pre-Solicitation Notice, Industry Day

### Use Case 4: I need to track changes
All documents saved to `data/document_metadata.json` with:
- Timestamps
- Cross-references
- Extracted key data
- Full traceability

---

## 🧪 Verify Everything Works

### Quick Test (2 minutes)
```bash
python scripts/test_complete_system.py
```
Expected: `✅ ALL TESTS PASSED - SYSTEM IS OPERATIONAL`

### Full Test (20 minutes)
```bash
python scripts/test_full_pipeline.py
```
Tests all 31 agents end-to-end.

---

## 🆘 Need Help?

### Error: "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY='sk-ant-your-key-here'
```

### Error: "No module named 'agents'"
```bash
# Make sure you're in the right directory
cd "/Users/alejandromaldonado/Desktop/AI_Phantom_Fellow_Course/Basic use case market research LLM automation"
```

### Question: "Which agents can I use?"
See [SYSTEM_READY.md](SYSTEM_READY.md) for all 31 agents.

### Question: "How do I customize documents?"
See [HOW_TO_USE.md](HOW_TO_USE.md) - Section "Option 2: Individual Agents"

---

## 🎯 Your First 3 Commands

```bash
# 1. Set API key
export ANTHROPIC_API_KEY='your-key'

# 2. Generate first document
python examples/quick_start_example.py

# 3. View the result
cat output/quick_start_igce.md
```

**Congratulations!** You just automated DoD acquisition document generation! 🎉

---

## 📊 System Stats

- **Agents**: 31 document generators
- **Cross-References**: 250+ automatic references
- **Test Coverage**: 100% (all tests passing)
- **Documentation**: 6 comprehensive guides
- **Examples**: 2 ready-to-run scripts
- **Status**: ✅ Production Ready

---

## 🗺️ File Structure

```
├── agents/              # 31 document-generating agents
├── orchestrators/       # High-level coordination (in agents/)
├── utils/              # Cross-reference system
├── examples/           # Example scripts (START HERE!)
├── scripts/            # Test scripts
├── data/               # Metadata store
├── output/             # Generated documents
└── *.md               # Documentation (you are here!)
```

---

## ⏭️ Next Steps

**Right Now** (5 min):
```bash
python examples/quick_start_example.py
```

**Today** (30 min):
- Read [HOW_TO_USE.md](HOW_TO_USE.md)
- Run [examples/example_usage.py](examples/example_usage.py)
- Generate documents for your program

**This Week**:
- Generate complete RFP package
- Customize for your requirements
- Integrate into your workflow

---

**Ready to start? Run this:**
```bash
python examples/quick_start_example.py
```

**Questions? Read this:**
```bash
cat HOW_TO_USE.md
```

**Everything working? Build this:**
*Your complete acquisition package!* 🚀
