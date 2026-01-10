# How to Use the DoD Acquisition Automation System

## Complete User Guide - From Setup to Full RFP

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Option 1: Use the Orchestrators (Recommended)](#option-1-use-the-orchestrators-recommended)
3. [Option 2: Use Individual Agents](#option-2-use-individual-agents)
4. [Option 3: Use the Main Pipeline](#option-3-use-the-main-pipeline)
5. [Understanding Cross-References](#understanding-cross-references)
6. [Common Workflows](#common-workflows)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Set Your API Key
```bash
export ANTHROPIC_API_KEY='your-anthropic-api-key-here'
```

### 2. Verify Installation
```bash
cd "/Users/alejandromaldonado/Desktop/AI_Phantom_Fellow_Course/Basic use case market research LLM automation"

# Test the system
python scripts/test_complete_system.py
```

Expected output: `✅ ALL TESTS PASSED - SYSTEM IS OPERATIONAL`

---

## Option 1: Use the Orchestrators (Recommended)

**Best for**: Generating complete acquisition packages with minimal code

### Phase 1: Pre-Solicitation (Market Research)

Use the **Pre-Solicitation Orchestrator** to generate all market research documents:

```python
import os
from orchestrators.pre_solicitation_orchestrator import PreSolicitationOrchestrator

# Initialize
api_key = os.environ['ANTHROPIC_API_KEY']
orchestrator = PreSolicitationOrchestrator(api_key=api_key)

# Define your program
project_info = {
    'program_name': 'Advanced Logistics Management System',
    'program_acronym': 'ALMS',
    'contracting_office': 'DLA J3',
    'point_of_contact': 'John Smith',
    'email': 'john.smith@dla.mil',
    'phone': '703-555-1234',
    'naics_code': '541512',  # Computer Systems Design Services
    'set_aside': 'Small Business',
    'estimated_value': '$5,000,000',
    'period_of_performance': '36 months'
}

requirements = """
We need a cloud-based logistics management system that:
- Tracks inventory across 50+ DoD warehouses
- Provides real-time visibility of assets
- Integrates with existing ERP systems
- Supports mobile access for field personnel
- Meets NIST 800-171 security requirements
"""

# Generate all pre-solicitation documents
result = orchestrator.execute({
    'project_info': project_info,
    'requirements_content': requirements,
    'config': {
        'include_sources_sought': True,
        'include_rfi': True,
        'include_industry_day': True,
        'include_pre_solicitation': True
    }
})

# Output is saved to output/ folder
print(f"✅ Generated {len(result['documents'])} documents")
print(f"📁 Location: {result['output_path']}")
```

**Generated Documents:**
- Sources Sought Notice
- Request for Information (RFI)
- Pre-Solicitation Notice
- Industry Day Materials

---

### Phase 2: Create the RFP Package

Use the **RFP Orchestrator** to generate complete solicitation:

```python
from orchestrators.rfp_orchestrator import RFPOrchestrator

orchestrator = RFPOrchestrator(api_key=api_key)

# This will automatically cross-reference the pre-solicitation documents
result = orchestrator.execute({
    'project_info': project_info,  # Same as Phase 1!
    'requirements_content': requirements,
    'config': {
        'contract_type': 'Firm Fixed Price',
        'pws_type': 'pws',  # or 'sow' or 'soo'
        'include_qasp': True,
        'include_dd254': False,  # Set True if classified
        'evaluation_approach': 'Best Value Trade-Off'
    }
})

print(f"✅ RFP Package Complete!")
print(f"📁 Location: {result['output_path']}")
```

**Generated Documents:**
- IGCE (Independent Government Cost Estimate)
- Acquisition Plan
- PWS/SOW/SOO
- QASP (Quality Assurance Surveillance Plan)
- Section B (Supplies/Services & Prices)
- Section H (Special Contract Requirements)
- Section I (Contract Clauses)
- Section K (Representations & Certifications)
- Section L (Instructions to Offerors)
- Section M (Evaluation Factors)
- SF-33 (Solicitation Form)
- SF-1449 (Solicitation/Contract Form)
- TBS Checklist

---

### Phase 3: Evaluation & Award

Use the **Evaluation Orchestrator**:

```python
from orchestrators.evaluation_orchestrator import EvaluationOrchestrator

orchestrator = EvaluationOrchestrator(api_key=api_key)

# Evaluate proposals
result = orchestrator.execute({
    'project_info': project_info,
    'proposals': [
        {
            'vendor_name': 'Acme Systems Inc',
            'technical_score': 85,
            'management_score': 90,
            'past_performance': 'Satisfactory',
            'price': 4500000
        },
        {
            'vendor_name': 'Beta Solutions LLC',
            'technical_score': 95,
            'management_score': 85,
            'past_performance': 'Excellent',
            'price': 4800000
        }
    ],
    'config': {
        'evaluation_method': 'Best Value Trade-Off'
    }
})

print(f"✅ Evaluation Complete - Winner: {result['winner']}")
```

**Generated Documents:**
- Source Selection Plan
- Evaluation Scorecards (per vendor)
- Source Selection Decision Document (SSDD)
- SF-26 (Award/Contract)
- Award Notification Letters
- Debriefing Materials

---

## Option 2: Use Individual Agents

**Best for**: Generating specific documents or customizing the workflow

### Example: Generate Just an IGCE

```python
from agents.igce_generator_agent import IGCEGeneratorAgent

agent = IGCEGeneratorAgent(api_key=api_key)

result = agent.execute({
    'project_info': {
        'program_name': 'Advanced Logistics Management System',
        'solicitation_number': 'DLA-25-R-0001',
        'estimated_value': '$5,000,000',
        'period_of_performance': '36 months (12 month base + 2 x 12 month options)',
        'organization': 'Defense Logistics Agency'
    },
    'labor_categories': [
        {'category': 'Program Manager', 'hours': 2080, 'rate': 185},
        {'category': 'Senior Software Engineer', 'hours': 6240, 'rate': 150},
        {'category': 'Software Engineer', 'hours': 12480, 'rate': 110},
        {'category': 'QA Engineer', 'hours': 4160, 'rate': 95},
        {'category': 'Database Administrator', 'hours': 2080, 'rate': 125},
        {'category': 'Technical Writer', 'hours': 1040, 'rate': 85}
    ],
    'materials': [
        {'description': 'Cloud Infrastructure (AWS)', 'cost': 200000},
        {'description': 'Software Licenses', 'cost': 150000},
        {'description': 'Hardware (servers, tablets)', 'cost': 100000}
    ],
    'config': {
        'contract_type': 'Firm Fixed Price',
        'risk_level': 'Medium'
    }
})

# Save to file
with open('output/igce.md', 'w') as f:
    f.write(result['content'])

print(f"✅ IGCE Generated!")
print(f"💰 Total Cost: {result['extracted_data']['total_cost_formatted']}")
print(f"📄 File: output/igce.md")
```

### Example: Generate PWS (References IGCE Automatically)

```python
from agents.pws_writer_agent import PWSWriterAgent

agent = PWSWriterAgent(api_key=api_key)

result = agent.execute({
    'project_info': {
        'program_name': 'Advanced Logistics Management System',  # SAME NAME!
        'solicitation_number': 'DLA-25-R-0001'
    },
    'requirements_content': """
    The contractor shall develop and deploy a cloud-based logistics
    management system with the following capabilities:

    1. Inventory Tracking
       - Real-time tracking of 500,000+ items
       - Barcode/RFID integration
       - Location tracking across 50+ warehouses

    2. Reporting & Analytics
       - Custom dashboard creation
       - Automated reports
       - Predictive analytics for demand forecasting

    3. Integration
       - RESTful API for ERP integration
       - LDAP/CAC authentication
       - NIST 800-171 compliance
    """,
    'config': {
        'contract_type': 'Firm Fixed Price',
        'include_cdrl': True,
        'security_classification': 'Unclassified'
    }
})

# PWS will automatically reference IGCE cost data!
print(f"✅ PWS Generated!")
print(f"📄 File saved to output folder")
```

---

## Option 3: Use the Main Pipeline

**Best for**: Generating everything end-to-end with one command

### Interactive Mode

```bash
python main.py
```

Then follow the prompts:
1. Enter program name
2. Enter requirements
3. Select document types to generate
4. Review and approve

### Automated Mode

```python
from main import AcquisitionPipeline

pipeline = AcquisitionPipeline(api_key=api_key)

result = pipeline.run({
    'program_name': 'Advanced Logistics Management System',
    'program_acronym': 'ALMS',
    'requirements': requirements,
    'contract_type': 'Firm Fixed Price',
    'estimated_value': '$5,000,000',
    'period_of_performance': '36 months',
    'phases': ['pre_solicitation', 'solicitation', 'evaluation']
})

print(f"✅ Complete acquisition package generated!")
print(f"📁 Location: {result['output_path']}")
```

---

## Understanding Cross-References

The system **automatically** cross-references documents when you use the same `program_name`.

### How It Works

```python
# Step 1: Generate IGCE
igce_result = igce_agent.execute({
    'project_info': {'program_name': 'ALMS', ...}
})
# Saved to metadata store with program_name='ALMS'

# Step 2: Generate Acquisition Plan
# Automatically finds and uses IGCE data!
acq_plan_result = acq_plan_agent.execute({
    'project_info': {'program_name': 'ALMS', ...}  # Same name!
})
```

### Viewing Cross-References

```python
from utils.document_metadata_store import DocumentMetadataStore

store = DocumentMetadataStore()

# Find your IGCE
igce = store.find_latest_document('igce', 'ALMS')
print(f"IGCE ID: {igce['id']}")
print(f"Cost: {igce['extracted_data']['total_cost_formatted']}")

# Find Acquisition Plan
acq_plan = store.find_latest_document('acquisition_plan', 'ALMS')
print(f"\nAcquisition Plan references:")
print(acq_plan['references'])  # Will show {'igce': 'igce_ALMS_2025-10-17'}

# See what references the IGCE
referring_docs = store.get_referring_documents(igce['id'])
print(f"\nDocuments that reference this IGCE:")
for doc in referring_docs:
    print(f"  - {doc['type']}")
```

---

## Common Workflows

### Workflow 1: Generate Complete RFP from Scratch

```python
import os
from orchestrators.pre_solicitation_orchestrator import PreSolicitationOrchestrator
from orchestrators.rfp_orchestrator import RFPOrchestrator

api_key = os.environ['ANTHROPIC_API_KEY']

# Your program details
project_info = {
    'program_name': 'My Program',
    'solicitation_number': 'FA1234-25-R-0001',
    'estimated_value': '$10M',
    'period_of_performance': '60 months'
}

requirements = "Your detailed requirements here..."

# Step 1: Market Research
pre_sol = PreSolicitationOrchestrator(api_key=api_key)
pre_sol.execute({
    'project_info': project_info,
    'requirements_content': requirements,
    'config': {'include_sources_sought': True, 'include_rfi': True}
})

# Step 2: RFP Package
rfp = RFPOrchestrator(api_key=api_key)
rfp.execute({
    'project_info': project_info,
    'requirements_content': requirements,
    'config': {'contract_type': 'Cost Plus Fixed Fee', 'pws_type': 'pws'}
})

print("✅ Complete RFP package ready for release!")
```

### Workflow 2: Generate Amendment After Q&A

```python
from agents.amendment_generator_agent import AmendmentGenerator

agent = AmendmentGenerator(api_key=api_key)

result = agent.execute({
    'project_info': {
        'program_name': 'My Program',  # References original RFP
        'solicitation_number': 'FA1234-25-R-0001',
        'amendment_number': '0001'
    },
    'changes': [
        {
            'section': 'Section L',
            'change': 'Extended proposal due date by 14 days',
            'reason': 'Industry request for additional time'
        },
        {
            'section': 'PWS',
            'change': 'Clarified cloud security requirements',
            'reason': 'Response to vendor questions'
        }
    ],
    'qa_responses': [
        {
            'question': 'Is FedRAMP High required?',
            'answer': 'Yes, FedRAMP High authorization is required...'
        }
    ]
})

print(f"✅ Amendment 0001 generated!")
```

### Workflow 3: Generate Just Cost Documents

```python
from agents.igce_generator_agent import IGCEGeneratorAgent
from agents.negotiation_memo_generator_agent import NegotiationMemoGenerator

# Generate IGCE
igce = IGCEGeneratorAgent(api_key=api_key)
igce_result = igce.execute({...})

# After negotiations, document price
nego_memo = NegotiationMemoGenerator(api_key=api_key)
memo_result = nego_memo.execute({
    'project_info': {'program_name': 'My Program'},  # References IGCE
    'vendor_name': 'Acme Systems',
    'initial_price': 5200000,
    'final_price': 4850000,
    'negotiation_summary': 'Reduced scope of Option Year 2...'
})
```

---

## Troubleshooting

### Issue: "No cross-references found"

**Solution**: Make sure you're using the exact same `program_name` across all agents.

```python
# ❌ Wrong - different names
igce.execute({'project_info': {'program_name': 'ALMS'}})
acq_plan.execute({'project_info': {'program_name': 'Advanced Logistics'}})

# ✅ Correct - same name
igce.execute({'project_info': {'program_name': 'ALMS'}})
acq_plan.execute({'project_info': {'program_name': 'ALMS'}})
```

### Issue: "API key not found"

```bash
# Set it in your terminal
export ANTHROPIC_API_KEY='sk-ant-...'

# Or in Python
import os
os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-...'
```

### Issue: "Document not saved to metadata store"

Check that the agent completed successfully:
```python
result = agent.execute({...})
print(result.get('metadata_id'))  # Should print document ID

# Verify in store
from utils.document_metadata_store import DocumentMetadataStore
store = DocumentMetadataStore()
store.print_summary()  # Shows all saved documents
```

### Issue: "Output folder not found"

```bash
# Create it
mkdir -p output
```

---

## Next Steps

1. **Start Small**: Generate one document (try IGCE first)
2. **Test Cross-References**: Generate Acquisition Plan and verify it references IGCE
3. **Try an Orchestrator**: Use PreSolicitationOrchestrator for 4 documents at once
4. **Full Pipeline**: Generate complete RFP package for your program

---

## Quick Reference Card

```python
# Most Common Usage Pattern
from orchestrators.rfp_orchestrator import RFPOrchestrator
import os

orchestrator = RFPOrchestrator(api_key=os.environ['ANTHROPIC_API_KEY'])

result = orchestrator.execute({
    'project_info': {
        'program_name': 'Your Program Name',
        'solicitation_number': 'XXX-25-R-0001',
        'estimated_value': '$XM',
        'period_of_performance': 'XX months'
    },
    'requirements_content': 'Your requirements...',
    'config': {
        'contract_type': 'Firm Fixed Price',
        'pws_type': 'pws'
    }
})

# Done! Check output/ folder
```

---

**For more details:**
- Architecture: See [SYSTEM_READY.md](SYSTEM_READY.md)
- Testing: See [TESTING_GUIDE.md](TESTING_GUIDE.md)
- Quick Start: See [GETTING_STARTED.md](GETTING_STARTED.md)
