# Integration Workflow User Guide

## Overview

This guide explains how to run integrated multi-agent workflows that generate complete procurement document packages. The integration system allows Phase 1 and Phase 2 enhanced agents to work together, sharing context and maintaining consistency across documents.

---

## Prerequisites

### 1. Environment Setup
```bash
# Ensure Python environment is active
source venv/bin/activate  # or your virtualenv path

# Verify required packages
pip install anthropic faiss-cpu python-dotenv

# Set API key
export ANTHROPIC_API_KEY="your-api-key"
```

### 2. RAG System Ready
```bash
# Verify vector store is loaded
python scripts/test_rag_system.py "acquisition strategy"

# Expected: Should return relevant chunks from knowledge base
```

### 3. Agent Status
- **Phase 2 Agents** (Template-based, enhanced): Acquisition Plan, PWS, QA Manager
- **Phase 1 Agents** (RAG-only): IGCE, SOO, SOW
- **All agents**: Fully functional and tested

---

## Available Workflows

### Workflow 1: Pre-Solicitation Package
**Agents Used**: Acquisition Plan → IGCE → PWS

**Documents Generated**:
1. **Acquisition Plan** - Strategic planning document (6,000+ words)
2. **IGCE** - Independent Government Cost Estimate (1,200+ words)
3. **PWS** - Performance Work Statement (3,600+ words)

**Use Case**: Complete pre-solicitation documentation for competitive acquisition

**Command**:
```bash
python scripts/test_integration_workflow.py
```

**Expected Runtime**: 3-5 minutes

**Expected Output**:
```
output/integration_tests/
├── 01_acquisition_plan.md
├── 02_igce.md
├── 03_pws.md
├── integration_test_results.json
└── integration_test_report.txt
```

---

## Running Your First Integration

### Step 1: Define Project Information

Edit the project configuration in your workflow script:

```python
project_info = {
    "program_name": "Your Program Name",
    "organization": "Your Organization",
    "author": "Your Name",
    "date": "MM/DD/YYYY",
    "budget": "$X.X million",
    "period_of_performance": "XX months",

    # Additional context
    "scope": "Brief description of what you're acquiring",
    "requirements": "Key requirements or capabilities needed",
    "constraints": "Budget, timeline, or policy constraints"
}
```

### Step 2: Configure Document Sequence

The workflow automatically passes context from one document to the next:

```python
# 1. Acquisition Plan provides strategic context
acq_task = {
    'project_info': project_info,
    'requirements': [],  # Can add specific requirements
}

# 2. IGCE receives acquisition strategy context
igce_task = {
    'project_info': project_info,
    'previous_documents': {
        'acquisition_plan': acq_content  # Automatically includes
    }
}

# 3. PWS receives both acquisition strategy and cost context
pws_task = {
    'project_info': project_info,
    'previous_documents': {
        'acquisition_plan': acq_content,
        'igce': igce_content  # Builds on both previous docs
    }
}
```

### Step 3: Execute Workflow

```bash
# Run the integration test
python scripts/test_integration_workflow.py

# Monitor progress (you'll see):
# - Agent initialization messages
# - Document generation progress
# - Quality validation checks
# - Final statistics
```

### Step 4: Review Output

```bash
# View generated documents
ls -lh output/integration_tests/

# Quick preview
head -n 50 output/integration_tests/01_acquisition_plan.md

# Check quality report
cat output/integration_tests/integration_test_report.txt
```

---

## Understanding the Output

### Document Quality Metrics

Each document includes quality analysis:

**Acquisition Plan**:
- **Word Count**: 6,000-7,000 (comprehensive coverage)
- **TBD Count**: 30-40 (79.5% reduction from baseline)
- **Quality Score**: 85-90% (B+ to A-)

**IGCE**:
- **Word Count**: 1,200-1,500 (detailed cost breakdown)
- **TBD Count**: 60-70 (Phase 1 only, will improve with Phase 2)
- **Quality Score**: 75-80% (C+ to B-)

**PWS**:
- **Word Count**: 3,600-4,000 (detailed performance requirements)
- **TBD Count**: 1-2 (81.8% reduction from baseline)
- **Quality Score**: 90-95% (A- to A)

**Aggregate Package**:
- **Total Words**: 10,000-12,000
- **Average Quality**: 85% (B+)
- **Consistency Score**: 70-80% (needs improvement)

### Quality Grading Scale

| Score | Grade | Meaning |
|-------|-------|---------|
| 95-100% | A | Excellent - Ready for review with minimal edits |
| 90-94% | A- | Very Good - Minor improvements needed |
| 85-89% | B+ | Good - Some sections need attention |
| 80-84% | B | Satisfactory - Several improvements needed |
| 75-79% | C+ | Acceptable - Significant revisions required |
| 70-74% | C | Needs Work - Major improvements needed |
| <70% | F | Unacceptable - Regenerate recommended |

---

## Customizing Workflows

### Create a Custom Workflow

```python
from agents.acquisition_plan_generator_agent import AcquisitionPlanGeneratorAgent
from agents.pws_writer_agent import PWSWriterAgent
from rag.vector_store import VectorStore
from rag.retriever import Retriever
import os

# Initialize RAG
api_key = os.environ.get('ANTHROPIC_API_KEY')
vector_store = VectorStore(api_key)
vector_store.load()
retriever = Retriever(vector_store, top_k=5)

# Your project info
project_info = {
    "program_name": "Custom Acquisition",
    # ... your fields
}

# Step 1: Generate Acquisition Plan
acq_agent = AcquisitionPlanGeneratorAgent(api_key=api_key, retriever=retriever)
acq_result = acq_agent.execute({'project_info': project_info})

# Step 2: Generate PWS using Acquisition Plan context
pws_agent = PWSWriterAgent(api_key=api_key, retriever=retriever)
pws_task = {
    'project_info': project_info,
    'previous_documents': {
        'acquisition_plan': acq_result['content']
    }
}
pws_result = pws_agent.execute(pws_task)

# Save outputs
with open('output/my_acquisition_plan.md', 'w') as f:
    f.write(acq_result['content'])

with open('output/my_pws.md', 'w') as f:
    f.write(pws_result['content'])

print("Workflow complete!")
```

### Add Custom Validation

```python
def validate_consistency(doc1_content, doc2_content, field_name, pattern):
    """Check if a field is consistent across documents"""
    import re

    value1 = re.search(pattern, doc1_content)
    value2 = re.search(pattern, doc2_content)

    if value1 and value2:
        match = value1.group(1).strip() == value2.group(1).strip()
        return {
            'field': field_name,
            'doc1_value': value1.group(1).strip(),
            'doc2_value': value2.group(1).strip(),
            'consistent': match
        }
    return {'field': field_name, 'consistent': False, 'error': 'Pattern not found'}

# Use in workflow
consistency_check = validate_consistency(
    acq_result['content'],
    pws_result['content'],
    'Program Name',
    r'Program Name:\s*(.+?)(?:\n|$)'
)

print(f"Program Name Consistency: {'✓' if consistency_check['consistent'] else '✗'}")
```

---

## Troubleshooting

### Issue: "Vector store not found"

**Symptom**: Error message `FileNotFoundError: data/vector_db/`

**Solution**:
```bash
# Initialize vector store
python scripts/add_documents_to_rag.py data/documents/

# Verify
python scripts/test_rag_system.py "test query"
```

---

### Issue: High TBD Count

**Symptom**: Documents have many `[TBD]` placeholders

**Causes**:
1. **Insufficient RAG context** - Knowledge base doesn't have relevant info
2. **Phase 1 agent** - Agent hasn't received Phase 2 enhancements
3. **Missing project info** - Required fields not provided

**Solutions**:
```python
# 1. Add more detailed project info
project_info = {
    "program_name": "Specific Name",  # Not "TBD Program"
    "budget": "$2.5 million",         # Not "$X million"
    "period_of_performance": "36 months",  # Not "XX months"
    # ... be specific
}

# 2. Check if agent has Phase 2 enhancements
# Phase 2 agents: Acquisition Plan, PWS, QA Manager
# Phase 1 agents: IGCE, SOO, SOW (higher TBD count expected)

# 3. Add relevant documents to RAG
python scripts/add_documents_to_rag.py path/to/relevant/document.pdf
```

---

### Issue: Inconsistent Values Across Documents

**Symptom**: Program name, budget, or dates differ between documents

**Cause**: Pattern matching failures or copy errors

**Solution**:
```python
# Use shared config object
shared_config = {
    'program_name': 'Advanced Logistics Management System',
    'organization': 'U.S. Army',
    'budget': '$45 million',
    'period': '36 months',
    'date': '10/04/2025'
}

# Pass to all agents
acq_task = {'project_info': shared_config, ...}
igce_task = {'project_info': shared_config, ...}
pws_task = {'project_info': shared_config, ...}
```

---

### Issue: Low Quality Scores

**Symptom**: Quality scores below 70%

**Diagnosis**:
```bash
# Check which sections are failing
grep -A 5 "Quality Score" output/integration_tests/integration_test_report.txt

# Common issues:
# - High TBD count (>50 per document)
# - Short documents (<1000 words)
# - Missing required sections
```

**Solutions**:
1. **Improve project info detail**
2. **Add domain-specific docs to RAG**
3. **Use Phase 2 enhanced agents where available**
4. **Review and adjust requirements**

---

### Issue: Workflow Takes Too Long

**Symptom**: Execution time >10 minutes

**Causes**:
1. Large vector store (>50k chunks)
2. Complex documents with many sections
3. Network latency to API

**Solutions**:
```python
# 1. Reduce RAG top_k
retriever = Retriever(vector_store, top_k=3)  # Default: 5

# 2. Adjust agent temperature for faster generation
agent = PWSWriterAgent(api_key=api_key, retriever=retriever, temperature=0.5)

# 3. Use caching (if available)
# Some agents cache RAG queries automatically
```

---

## Performance Benchmarks

Based on test runs with ALMS project:

| Workflow | Agents | Runtime | Total Words | Avg Quality |
|----------|--------|---------|-------------|-------------|
| Pre-Solicitation | 3 agents | 3-5 min | 10,956 | 85.5% (B+) |
| Acquisition Plan Only | 1 agent | 1-2 min | 6,107 | 87% (B+) |
| PWS Only | 1 agent | 1-2 min | 3,685 | 92% (A-) |

**System**:
- Vector Store: 12,806 chunks
- RAG top_k: 5
- Temperature: 0.3-0.7 (varies by agent)
- Model: Claude 3.5 Sonnet

---

## Best Practices

### 1. Always Start with Detailed Project Info
```python
# ❌ Bad - Vague info leads to high TBD counts
project_info = {
    "program_name": "New System",
    "budget": "TBD",
    "organization": "Government"
}

# ✅ Good - Specific info enables quality generation
project_info = {
    "program_name": "Advanced Logistics Management System (ALMS)",
    "budget": "$45 million over 36 months",
    "organization": "U.S. Army Contracting Command",
    "scope": "Cloud-based inventory tracking for 15 installations",
    "users": "2,800 concurrent users",
    "requirements": ["Real-time tracking", "Mobile access", "DoD security compliance"]
}
```

### 2. Build Knowledge Base Before Running Workflows
```bash
# Add all relevant documents first
python scripts/add_documents_to_rag.py data/documents/regulations.pdf
python scripts/add_documents_to_rag.py data/documents/similar_contracts.pdf
python scripts/add_documents_to_rag.py data/documents/technical_standards.pdf

# Then run workflow
python scripts/test_integration_workflow.py
```

### 3. Review Each Document Before Next Step
```python
# Generate first document
acq_result = acq_agent.execute(acq_task)

# Review and save
print(f"Acquisition Plan Quality: {acq_result.get('metadata', {}).get('tbd_count', 'N/A')} TBDs")

# Option: Manual review before proceeding
# input("Review acquisition plan, press Enter to continue...")

# Generate next document with reviewed context
igce_task = {'project_info': project_info, 'previous_documents': {'acquisition_plan': acq_result['content']}}
igce_result = igce_agent.execute(igce_task)
```

### 4. Use Consistent Naming and Structure
```python
# Establish naming convention
OUTPUT_DIR = "output/integration_tests"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Structured file names
files = {
    'acquisition_plan': f"{OUTPUT_DIR}/{TIMESTAMP}_01_acquisition_plan.md",
    'igce': f"{OUTPUT_DIR}/{TIMESTAMP}_02_igce.md",
    'pws': f"{OUTPUT_DIR}/{TIMESTAMP}_03_pws.md",
}
```

### 5. Monitor and Log Execution
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('output/workflow.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Log workflow progress
logger.info(f"Starting workflow for {project_info['program_name']}")
logger.info("Generating Acquisition Plan...")
acq_result = acq_agent.execute(acq_task)
logger.info(f"Acquisition Plan complete: {len(acq_result['content'])} chars, {acq_result.get('metadata', {}).get('tbd_count', 'N/A')} TBDs")
```

---

## Advanced Usage

### Parallel Document Generation

For independent documents that don't require sequential context:

```python
import concurrent.futures

def generate_document(agent, task):
    """Generate a single document"""
    return agent.execute(task)

# For documents that can be generated in parallel
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        'sow': executor.submit(generate_document, sow_agent, sow_task),
        'soo': executor.submit(generate_document, soo_agent, soo_task),
        'qa': executor.submit(generate_document, qa_agent, qa_task),
    }

    results = {name: future.result() for name, future in futures.items()}

# Note: Only works for independent documents
# Sequential workflows (Acq Plan → IGCE → PWS) must run in order
```

### Custom Quality Validation

```python
class CustomQualityValidator:
    """Custom validation rules for your organization"""

    def validate_document(self, content, doc_type):
        """Validate document against custom rules"""
        issues = []

        # Rule 1: Check for required sections
        required_sections = self.get_required_sections(doc_type)
        for section in required_sections:
            if section not in content:
                issues.append(f"Missing required section: {section}")

        # Rule 2: Check word count minimums
        word_count = len(content.split())
        min_words = {'acquisition_plan': 5000, 'pws': 3000, 'igce': 1000}
        if word_count < min_words.get(doc_type, 0):
            issues.append(f"Document too short: {word_count} words (min: {min_words[doc_type]})")

        # Rule 3: Check citation density
        citations = len(re.findall(r'\([^)]*20\d{2}[^)]*\)', content))
        density = citations / (word_count / 1000)
        if density < 5:
            issues.append(f"Low citation density: {density:.1f} per 1000 words (min: 5)")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'score': max(0, 100 - (len(issues) * 10))
        }

# Use in workflow
validator = CustomQualityValidator()
validation = validator.validate_document(acq_result['content'], 'acquisition_plan')
print(f"Validation Score: {validation['score']}%")
if not validation['valid']:
    print("Issues found:")
    for issue in validation['issues']:
        print(f"  - {issue}")
```

---

## Next Steps

After successfully running your first integration:

1. **Apply Phase 2 to IGCE** (recommended)
   - Reduce IGCE TBD count from 62 to ~20
   - Improve overall package quality to 90%+
   - See: [INTEGRATION_TEST_ANALYSIS.md](INTEGRATION_TEST_ANALYSIS.md)

2. **Build More Workflows**
   - Post-Solicitation: Amendment → QA → Evaluation
   - Award Phase: Award Notice → Debriefs
   - Custom sequences for your use cases

3. **Enhance Consistency Validation**
   - Build dedicated validation framework
   - Add fuzzy matching for values
   - Create consistency enforcement rules

4. **Create Workflow Templates**
   - Save successful project_info configs
   - Build reusable workflow scripts
   - Document organization-specific patterns

---

## Support and Resources

**Documentation**:
- [Integration Test Analysis](INTEGRATION_TEST_ANALYSIS.md) - Detailed test results and findings
- [Integration Showcase](INTEGRATION_SHOWCASE.md) - Before/after examples with metrics
- [Phase 2 Complete Report](PHASE_2_COMPLETE_FINAL.md) - All Phase 2 agent enhancements

**Test Scripts**:
- `scripts/test_integration_workflow.py` - Full pre-solicitation workflow
- `scripts/test_acquisition_plan_agent.py` - Individual agent testing
- `scripts/test_pws_agent.py` - PWS agent testing

**Example Output**:
- `output/integration_tests/` - Complete ALMS example package

---

**Questions or Issues?**

Check the troubleshooting section above, review the test scripts for working examples, or examine the output files to see expected formats and quality levels.
