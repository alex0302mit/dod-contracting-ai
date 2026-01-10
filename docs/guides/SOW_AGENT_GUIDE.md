# Statement of Work (SOW) Agent System Guide

## Overview

This guide explains how to use the SOW Agent System to generate Statement of Work documents using your SOW manual as a knowledge base.

---

## 🏗️ Architecture

The SOW system follows the same pattern as the Market Research system:

```
SOW Manual (PDF/Text)
    ↓
RAG System (Vector DB)
    ↓
SOW Writer Agent → Quality Agent
    ↓
Final SOW Document
```

### Components

| Component | Purpose |
|-----------|---------|
| **SOWWriterAgent** | Generates SOW sections using RAG |
| **SOWOrchestrator** | Coordinates workflow (Writing → Quality → Revision → Assembly) |
| **QualityAgent** | Evaluates compliance and completeness |
| **RAG System** | Retrieves relevant SOW manual guidance |

---

## 📋 Step-by-Step Usage

### Step 1: Add Your SOW Manual to RAG

```bash
# 1. Place your SOW manual in data/documents/
cp ~/Documents/SOW_Manual.pdf data/documents/

# 2. Add to RAG system
python scripts/add_documents_to_rag.py data/documents/SOW_Manual.pdf

# 3. Verify it's indexed
python scripts/test_rag_system.py "statement of work scope requirements"
```

**Expected Output:**
```
✓ Loaded existing store with 142 chunks
✓ Processed 45 new chunks
✅ Total chunks now: 187
```

---

### Step 2: Configure Your Project

Edit `scripts/run_sow_pipeline.py` and customize the project information:

```python
project_info = {
    "program_name": "Your Project Name",
    "author": "Your Name",
    "organization": "Your Organization",
    "date": "10/04/2025",
    "budget": "$X.X million",
    "period_of_performance": "XX months",
    # Add more fields as needed
}
```

---

### Step 3: Define SOW Sections

Customize the sections based on your SOW manual structure:

```python
sow_sections_config = [
    {
        "name": "1. Scope of Work",
        "requirements": "Define boundaries and extent of services",
        "context": {"be_specific": True}
    },
    {
        "name": "2. Tasks",
        "requirements": "List all deliverable tasks",
        "context": {"use_numbered_list": True}
    },
    # Add more sections...
]
```

---

### Step 4: Generate SOW

```bash
python scripts/run_sow_pipeline.py
```

**Output:**
- **Markdown:** `outputs/sow/statement_of_work.md`
- **PDF:** `outputs/sow/statement_of_work.pdf` (auto-generated)

---

## 🔄 How It Works

### Workflow Phases

#### **Phase 1: Writing** ✍️
For each SOW section:
1. Query RAG system for relevant SOW manual guidance
2. Retrieve top 5 most relevant chunks from manual
3. Synthesize guidance (requirements, structure, examples)
4. Generate section content using LLM + guidance
5. Return section with references

**Example Flow:**
```
Section: "Scope of Work"
    ↓
Query RAG: "statement of work scope section requirements"
    ↓
Retrieved: [SOW Manual p.12, p.45, p.67, Guide p.3, Examples p.2]
    ↓
Synthesize: "Scope must include: boundaries, inclusions, exclusions..."
    ↓
Generate: "The scope of this contract encompasses..."
```

#### **Phase 2: Quality Check** ✅
- Evaluate each section for compliance
- Check completeness against requirements
- Assign quality score (0-100)
- Identify issues

#### **Phase 3: Revision** 🔄 (if needed)
- Sections scoring < 75 are automatically revised
- Uses quality feedback to improve
- Re-evaluates revised sections

#### **Phase 4: Assembly** 📦
- Combines all sections into final SOW
- Adds header with project info
- Generates PDF version
- Creates quality summary

---

## 🎯 Key Features

### 1. **RAG-Powered Compliance**
Every section references your actual SOW manual, ensuring:
- ✅ Compliance with your standards
- ✅ Consistent terminology
- ✅ Proper structure
- ✅ Example language from manual

### 2. **Automatic Quality Control**
- Evaluates completeness
- Checks compliance requirements
- Auto-revises low-quality sections
- Provides quality scores

### 3. **Customizable Sections**
Easily adapt to different SOW formats:
```python
# Government contract SOW
sections = ["Scope", "Tasks", "Deliverables", "Performance Standards"]

# Commercial SOW
sections = ["Objectives", "Services", "Timeline", "Success Criteria"]

# Technical SOW
sections = ["Requirements", "Architecture", "Implementation", "Testing"]
```

### 4. **Context Awareness**
Sections reference each other for consistency:
- Later sections reference earlier ones
- Maintains document coherence
- Avoids contradictions

---

## 🧪 Testing Individual Agent

Test the SOW Writer Agent directly:

```bash
python -c "
from agents.sow_writer_agent import SOWWriterAgent
from rag.vector_store import VectorStore
from rag.retriever import Retriever
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get('ANTHROPIC_API_KEY')

# Initialize RAG
vector_store = VectorStore(api_key)
vector_store.load()
retriever = Retriever(vector_store, top_k=5)

# Initialize agent
agent = SOWWriterAgent(api_key, retriever)

# Test task
task = {
    'section_name': 'Scope of Work',
    'project_info': {'program_name': 'Test Project'},
    'requirements': 'Define the scope clearly',
    'context': {}
}

result = agent.execute(task)
print(result['content'])
"
```

---

## 📊 Comparison: Market Research vs SOW

| Feature | Market Research | SOW Agent |
|---------|----------------|-----------|
| **Agent** | ResearchAgent + ReportWriterAgent | SOWWriterAgent |
| **Knowledge Base** | Regulations, vendor info, contracts | SOW manual, templates |
| **Output** | Market research report | Statement of Work |
| **Sections** | 8-9 analytical sections | 10+ task-oriented sections |
| **Temperature** | 0.7 (creative analysis) | 0.5 (compliance-focused) |
| **Quality Threshold** | 70/100 | 75/100 (stricter) |

---

## 🔧 Advanced Usage

### Combine Market Research + SOW

Generate both documents for a complete procurement package:

```python
# 1. Generate Market Research
from agents.orchestrator import Orchestrator
mr_orchestrator = Orchestrator(api_key, retriever)
mr_result = mr_orchestrator.execute_full_workflow(...)

# 2. Generate SOW (using market research findings)
from agents.sow_orchestrator import SOWOrchestrator
sow_orchestrator = SOWOrchestrator(api_key, retriever)

# Pass market research context to SOW
project_info['market_research'] = mr_result['workflow_state']['written_sections']
sow_result = sow_orchestrator.execute_sow_workflow(project_info, ...)
```

### Create Multi-Agent Workflow

```python
# Master orchestrator that runs both
class ProcurementOrchestrator:
    def __init__(self, api_key, retriever):
        self.mr_orchestrator = Orchestrator(api_key, retriever)
        self.sow_orchestrator = SOWOrchestrator(api_key, retriever)

    def execute_full_procurement(self, project_info):
        # 1. Market Research
        mr_result = self.mr_orchestrator.execute_full_workflow(...)

        # 2. SOW (informed by MR)
        sow_result = self.sow_orchestrator.execute_sow_workflow(...)

        return {
            'market_research': mr_result,
            'statement_of_work': sow_result
        }
```

---

## 🐛 Troubleshooting

### Issue: "No SOW guidance found in knowledge base"

**Solution:**
```bash
# Verify SOW manual is indexed
python scripts/test_rag_system.py "statement of work"

# If nothing found, re-add manual
python scripts/add_documents_to_rag.py data/documents/SOW_Manual.pdf
```

### Issue: Low quality scores

**Causes:**
1. SOW manual not detailed enough
2. Section requirements too vague
3. Project info incomplete

**Solution:**
```python
# Add more detailed requirements
{
    "name": "Scope",
    "requirements": """Define scope with:
        - Clear boundaries
        - Specific inclusions
        - Explicit exclusions
        - Dependencies
        - Assumptions""",
    "context": {"detail_level": "high"}
}
```

### Issue: Sections don't match SOW manual format

**Solution:**
Ensure your section names match terminology in the SOW manual:
```python
# ❌ Generic names
"Requirements", "Work Description"

# ✅ Matches SOW manual
"Technical Requirements per Section 3.2", "Performance Work Statement (PWS)"
```

---

## 📚 File Structure

```
agents/
├── sow_writer_agent.py      # SOW content generation
├── sow_orchestrator.py       # SOW workflow coordination
└── __init__.py               # Exports SOW agents

scripts/
└── run_sow_pipeline.py       # Main SOW generation script

outputs/
└── sow/
    ├── statement_of_work.md
    └── statement_of_work.pdf

data/
└── documents/
    └── SOW_Manual.pdf        # Your SOW manual
```

---

## 🎓 Best Practices

### 1. **High-Quality SOW Manual**
- Use detailed, well-structured SOW manual
- Include examples and templates
- Cover all section types you need

### 2. **Specific Section Requirements**
```python
# ❌ Vague
"requirements": "Write the scope"

# ✅ Specific
"requirements": """Define scope including:
    1. Service boundaries
    2. Technical specifications
    3. Geographical limitations
    4. Exclusions and out-of-scope items
    5. Assumptions and dependencies"""
```

### 3. **Iterative Refinement**
1. Generate initial SOW
2. Review quality scores
3. Adjust section requirements
4. Regenerate low-scoring sections

### 4. **Maintain Knowledge Base**
```bash
# Regularly update SOW manual
cp ~/Documents/SOW_Manual_v2.pdf data/documents/
python scripts/add_documents_to_rag.py data/documents/SOW_Manual_v2.pdf
```

---

## 🚀 Quick Start Checklist

- [ ] Add SOW manual to `data/documents/`
- [ ] Index manual: `python scripts/add_documents_to_rag.py data/documents/SOW_Manual.pdf`
- [ ] Verify indexing: `python scripts/test_rag_system.py "scope of work"`
- [ ] Edit `scripts/run_sow_pipeline.py` with your project info
- [ ] Customize SOW sections configuration
- [ ] Run: `python scripts/run_sow_pipeline.py`
- [ ] Review output in `outputs/sow/statement_of_work.md`
- [ ] Revise and regenerate as needed

---

## 💡 Tips

1. **Use Multiple SOW Examples**: Add several SOW examples to knowledge base for better guidance
2. **Section-Specific Manuals**: If you have section-specific guides, add them all
3. **Quality Threshold**: Adjust `quality_threshold` in SOWOrchestrator based on your needs
4. **Temperature**: Lower temperature (0.3-0.5) for compliance, higher (0.7) for creative descriptions

---

## 📞 Support

For issues or questions:
1. Check logs in terminal output
2. Review `data/vector_db/` to ensure manual is indexed
3. Test RAG retrieval with `scripts/test_rag_system.py`
4. Adjust section requirements for better results
