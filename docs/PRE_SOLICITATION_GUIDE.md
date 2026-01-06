# Pre-Solicitation Phase Automation Guide

## Overview

This guide documents the **Pre-Solicitation Phase automation system** for DoD contracting. The system automates generation of all 6 critical pre-solicitation documents required before issuing an RFP.

**What It Does:**
- Automates market research and vendor engagement
- Generates FAR-compliant acquisition documents
- Supports both Services and R&D contract types
- Integrates with existing ALMS documents via RAG
- Provides complete pre-solicitation workflow orchestration

---

## System Architecture

### 6 Pre-Solicitation Generators

```
┌─────────────────────────────────────────────────────────────┐
│              Pre-Solicitation Orchestrator                  │
├─────────────────────────────────────────────────────────────┤
│  Phase 1: Market Research (Sources Sought)                 │
│  Phase 2: Technical Deep Dive (RFI)                         │
│  Phase 3: Planning (Acquisition Plan)                       │
│  Phase 4: Cost Estimation (IGCE)                            │
│  Phase 5: Public Announcement (Pre-Sol Notice)              │
│  Phase 6: Vendor Engagement (Industry Day)                  │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              Solicitation Phase (Existing)                  │
├─────────────────────────────────────────────────────────────┤
│  PWS/SOW/SOO → QASP → Section L → Section M → SF-33        │
└─────────────────────────────────────────────────────────────┘
```

### Agent Components

| Agent | Purpose | FAR Reference | Output |
|-------|---------|---------------|--------|
| **IGCE Generator** | Independent Government Cost Estimate | DFARS PGI 215.404-1 | Cost estimate with BOE |
| **Sources Sought Generator** | Market research notice | FAR 5.205 | Vendor capability inquiry |
| **RFI Generator** | Technical information request | FAR 15.201(e) | Detailed technical questions |
| **Acquisition Plan Generator** | Comprehensive acquisition strategy | FAR 7.104-7.105 | 12-element acquisition plan |
| **Pre-Solicitation Notice Generator** | 15-day advance notice | FAR 5.201 | Public solicitation announcement |
| **Industry Day Generator** | Vendor briefing materials | FAR 15.201(c) | Agenda, slides, forms |

---

## Quick Start

### 1. Setup

```bash
# Set API key
export ANTHROPIC_API_KEY='your-api-key'

# Optional: Initialize RAG for ALMS cost references
python scripts/setup_rag_system.py
```

### 2. Run Complete Workflow

```bash
python scripts/run_pre_solicitation_pipeline.py
```

This generates all 6 documents for the ALMS example program.

### 3. Check Outputs

```bash
ls -R outputs/pre-solicitation/
# ├── sources-sought/sources_sought_notice.md (+ PDF)
# ├── rfi/request_for_information.md (+ PDF)
# ├── acquisition-plan/acquisition_plan.md (+ PDF)
# ├── igce/independent_government_cost_estimate.md (+ PDF)
# ├── notices/pre_solicitation_notice.md (+ PDF)
# └── industry-day/industry_day_materials.md (+ PDF)
```

---

## Usage Examples

### Example 1: Complete Pre-Solicitation Workflow

```python
from agents import PreSolicitationOrchestrator
from rag.vector_store import VectorStore
from rag.retriever import Retriever

# Initialize RAG (optional)
vector_store = VectorStore(api_key)
vector_store.load()
retriever = Retriever(vector_store, top_k=5)

# Initialize orchestrator
orchestrator = PreSolicitationOrchestrator(
    api_key=api_key,
    retriever=retriever
)

# Define project information
project_info = {
    'program_name': 'Advanced Cloud System',
    'organization': 'DOD/ARMY',
    'estimated_value': '$5M - $10M',
    'period_of_performance': '36 months',
    'contract_type': 'services',  # or 'research_development'
    'contracting_officer': 'Jane Smith',
    'ko_email': 'jane.smith@army.mil',
    'ko_phone': '(703) 555-1234'
}

# Execute workflow
results = orchestrator.execute_pre_solicitation_workflow(
    project_info=project_info,
    requirements_content='',  # Optional PWS/SOW content
    output_dir='outputs/pre-solicitation',
    generate_sources_sought=True,
    generate_rfi=True,
    generate_acquisition_plan=True,
    generate_igce=True,
    generate_pre_solicitation_notice=True,
    generate_industry_day=True
)

print(f"Workflow Status: {results['workflow_status']}")
print(f"Phases Completed: {len(results['phases_completed'])}/6")
```

### Example 2: Generate Individual Documents

```python
# Generate only IGCE
from agents import IGCEGeneratorAgent
from rag.retriever import Retriever

agent = IGCEGeneratorAgent(api_key, retriever)

task = {
    'project_info': project_info,
    'requirements_content': pws_content,
    'config': {'contract_type': 'services'}
}

result = agent.execute(task)
files = agent.save_to_file(
    result['content'],
    'outputs/pre-solicitation/igce/cost_estimate.md',
    convert_to_pdf=True
)
```

### Example 3: R&D Contract Configuration

```python
# Configure for Research & Development contract
project_info = {
    'program_name': 'Advanced AI Research',
    'organization': 'DARPA',
    'estimated_value': '$15M',
    'period_of_performance': '48 months',
    'contract_type': 'research_development',  # Key difference
    'contracting_officer': 'Dr. Jane Doe',
    'ko_email': 'jane.doe@darpa.mil'
}

# R&D-specific configurations
results = orchestrator.execute_pre_solicitation_workflow(
    project_info=project_info,
    generate_sources_sought=True,
    sources_sought_config={
        'response_days': 30  # More time for R&D
    },
    rfi_config={
        'response_days': 45,  # Longer for technical proposals
        'questions_days': 20
    },
    igce_config={
        'contract_type': 'Cost-Plus-Fixed-Fee (CPFF)'  # Typical for R&D
    }
)
```

---

## Document Details

### 1. Independent Government Cost Estimate (IGCE)

**Purpose:** Government's independent baseline for evaluating contractor proposals.

**Key Features:**
- Labor cost analysis by WBS
- Materials and ODC calculations
- Risk and contingency analysis (10-25%)
- Basis of Estimate (BOE)
- Market cost benchmarking via RAG

**Contract Type Differences:**
- **Services:** Labor-hour focus, 10-15% contingency
- **R&D:** Research phases, equipment costs, 15-25% contingency

**Template Sections:**
- Executive Summary
- Labor Cost Analysis (by CLIN/WBS)
- Materials/ODC Cost Analysis
- Risk and Contingency
- Basis of Estimate
- Market Comparison

**Output:** `outputs/pre-solicitation/igce/independent_government_cost_estimate.md` (+ PDF)

---

### 2. Sources Sought Notice

**Purpose:** Initial market research to identify potential vendors.

**Key Features:**
- FAR 5.205 compliant format
- Vendor capability questionnaire (8-10 questions)
- Small business set-aside determination
- 15-30 day response period
- SAM.gov compatible

**Contract Type Differences:**
- **Services:** Past performance focus
- **R&D:** Technology maturity and innovation questions

**Template Sections:**
- Notice Information
- Program Overview
- Capability Requirements
- Vendor Questionnaire
- Small Business Considerations
- Response Instructions

**Output:** `outputs/pre-solicitation/sources-sought/sources_sought_notice.md` (+ PDF)

---

### 3. Request for Information (RFI)

**Purpose:** Detailed technical and cost information gathering.

**Key Features:**
- More detailed than Sources Sought
- Technical deep-dive questions (40-60 questions)
- Capability matrices
- ROM cost estimates
- 30-45 day response period

**Contract Type Differences:**
- **Services:** Implementation approach focus
- **R&D:** Research methodology and TRL assessment

**Template Sections:**
- General Information
- Technical Requirements
- Technical Questions (by category)
- Management Approach Questions
- Past Performance
- Cost Information
- Capability Matrices

**Output:** `outputs/pre-solicitation/rfi/request_for_information.md` (+ PDF)

---

### 4. Acquisition Plan

**Purpose:** Comprehensive acquisition strategy per FAR 7.105.

**Key Features:**
- 12 required FAR 7.105 elements
- Market research summary integration
- Risk assessment and mitigation
- Source selection methodology
- Small business strategy
- Acquisition schedule

**Contract Type Differences:**
- **Services:** Cost control and performance focus
- **R&D:** Technology maturation and IP rights focus

**Template Sections:**
1. Background
2. Applicable Conditions
3. Cost
4. Capability/Requirement
5. Delivery/Performance Period
6. Trade-offs
7. Acquisition Streamlining
8. Contract Type Determination
9. Source Selection Procedures
10. Acquisition Considerations
11. Market Research
12. Other Considerations

**Output:** `outputs/pre-solicitation/acquisition-plan/acquisition_plan.md` (+ PDF)

---

### 5. Pre-Solicitation Notice

**Purpose:** 15-day minimum advance notice before RFP release (FAR 5.201).

**Key Features:**
- SAM.gov compatible format
- Requirement summary
- Key dates (RFP release, proposal due, award)
- Set-aside determination
- POC information

**Contract Type Differences:**
- **Services:** Straightforward requirements
- **R&D:** Innovation objectives highlighted

**Template Sections:**
- General Information
- Requirement Overview
- Contract Information
- Small Business Information
- Acquisition Approach
- Key Dates and Schedule
- SAM.gov Registration Requirements

**Output:** `outputs/pre-solicitation/notices/pre_solicitation_notice.md` (+ PDF)

---

### 6. Industry Day Materials

**Purpose:** Vendor briefing and engagement event.

**Key Features:**
- Event agenda (2-4 hours typical)
- Presentation slides (14-20 slides)
- Q&A process
- Registration forms
- FAQs (8-10 questions)
- Small business outreach

**Contract Type Differences:**
- **Services:** Requirements and timeline focus
- **R&D:** Technical interchange and innovation discussion

**Template Sections:**
- Event Information and Agenda
- Program Overview Briefing (slides)
- Technical Deep Dive Session
- Acquisition Process Briefing
- Small Business Opportunities
- Q&A Session
- Registration Form
- Question Submission Form

**Output:** `outputs/pre-solicitation/industry-day/industry_day_materials.md` (+ PDF)

---

## Contract Type Support

### Services Contracts (Default)

**Characteristics:**
- IT services, support services, professional services
- Labor-hour/T&M focus
- FFP or T&M contract types
- Cost control emphasis

**Example NAICS:** 541512 (Computer Systems Design Services)

**Configuration:**
```python
project_info = {
    'contract_type': 'services',
    # ...
}
```

### Research & Development Contracts

**Characteristics:**
- Basic research, applied research, advanced development
- Research phases, ODCs, equipment
- CPFF or Cost-Plus-Award-Fee contract types
- Technology maturation and IP focus

**Example NAICS:** 541715 (R&D in Physical, Engineering, and Life Sciences)

**Configuration:**
```python
project_info = {
    'contract_type': 'research_development',
    # ...
}
```

**R&D-Specific Additions:**
- Technology Readiness Level (TRL) assessment
- Innovation approach questions
- Intellectual property considerations
- Research methodology evaluation

---

## RAG Integration

### ALMS Document References

The system uses RAG to retrieve cost and schedule data from ALMS documents:

**Cost Benchmarks:**
- ALMS APB: $2.5M development, $6.4M lifecycle
- ALMS acquisition strategy: FFP + T&M contract mix
- ALMS schedule: IOC Jun 2026, FOC Dec 2026

**Requirements:**
- ALMS CDD: Functional requirements, KPPs
- ALMS ICD: Capability gap, mission need
- ALMS TMRR: Technology risks

**Usage in Agents:**
```python
# IGCE Agent
query = "What are typical labor rates and costs for cloud-based logistics systems?"
results = retriever.retrieve(query, top_k=3)

# Acquisition Plan Agent
query = "What contract types and source selection methods were used for ALMS?"
results = retriever.retrieve(query, top_k=3)
```

---

## Configuration Options

### Global Configuration

```python
orchestrator = PreSolicitationOrchestrator(
    api_key=api_key,
    retriever=retriever,  # Optional RAG
    tavily_api_key=None,  # Not used in pre-solicitation
    model="claude-sonnet-4-20250514"
)
```

### Per-Document Configuration

```python
# Sources Sought Configuration
sources_sought_config = {
    'response_days': 21,  # Days for vendor response
    'office': 'Army Contracting Command',
    'location': 'Fort Belvoir, VA'
}

# RFI Configuration
rfi_config = {
    'response_days': 35,
    'questions_days': 15,  # Days to submit questions
    'technical_page_limit': 25,
    'past_performance_page_limit': 15,
    'cost_page_limit': 10
}

# Acquisition Plan Configuration
acquisition_plan_config = {
    'prepared_by': 'Program Manager',
    'pm_name': 'John Doe',
    'co_name': 'Jane Smith',
    'classification': 'UNCLASSIFIED'
}

# IGCE Configuration
igce_config = {
    'prepared_by': 'Cost Analyst',
    'contract_type': 'Firm-Fixed-Price (FFP)',
    'contingency_percent': 15
}

# Pre-Solicitation Notice Configuration
pre_sol_notice_config = {
    'rfp_release_days': 21,  # Days from notice to RFP
    'proposal_days': 45,  # Days from RFP to proposal due
    'solicitation_number': 'W911XX-25-R-1234'
}

# Industry Day Configuration
industry_day_config = {
    'venue_name': 'Pentagon Conference Center',
    'venue_address': 'Arlington, VA 22202',
    'attendance_type': 'In-person and Virtual'
}
```

---

## Testing

### Run Complete Test Suite

```bash
# Full workflow test
python scripts/run_pre_solicitation_pipeline.py

# Individual generator tests
python scripts/run_pre_solicitation_pipeline.py --individual
```

### Test Results

Expected output:
```
================================================================================
PRE-SOLICITATION WORKFLOW COMPLETE
================================================================================
Phases Completed: 6/6
  ✓ Sources Sought
  ✓ Rfi
  ✓ Acquisition Plan
  ✓ Igce
  ✓ Pre Solicitation Notice
  ✓ Industry Day

Output Directory: outputs/pre-solicitation
================================================================================
```

---

## Troubleshooting

### Issue: RAG retrieval fails

**Solution:** Ensure vector database is initialized:
```bash
python scripts/setup_rag_system.py
```

### Issue: PDF generation fails

**Solution:** Install PDF dependencies:
```bash
pip install markdown2 weasyprint
```

### Issue: Templates not found

**Solution:** Verify template files exist:
```bash
ls templates/*_template.md
```

### Issue: API rate limits

**Solution:** Add delays between agent calls or reduce concurrent operations.

---

## Integration with Solicitation Phase

The Pre-Solicitation phase feeds directly into the existing Solicitation phase:

```python
# 1. Complete Pre-Solicitation Phase
pre_sol_results = pre_sol_orchestrator.execute_pre_solicitation_workflow(...)

# 2. Use outputs for Solicitation Phase
from agents import PWSOrchestrator

pws_orchestrator = PWSOrchestrator(api_key, retriever)

# Use acquisition plan and IGCE as context
pws_result = pws_orchestrator.execute_pws_workflow(
    project_info=project_info,
    pws_sections_config=sections_config,
    generate_qasp=True,
    generate_section_l=True,
    generate_section_m=True
)

# 3. Assemble complete package
from agents import SolicitationPackageOrchestrator

package_orchestrator = SolicitationPackageOrchestrator()
complete_rfp = package_orchestrator.assemble_package(...)
```

---

## FAR Compliance Summary

| Document | FAR Reference | Compliance Notes |
|----------|---------------|------------------|
| IGCE | DFARS PGI 215.404-1 | Required for price reasonableness |
| Sources Sought | FAR 5.205 | Special notices for market research |
| RFI | FAR 15.201(e) | Information exchanges before proposals |
| Acquisition Plan | FAR 7.104-7.105 | Required for >$10M (simplified), >$25M (written) |
| Pre-Sol Notice | FAR 5.201 | Minimum 15-day notice required |
| Industry Day | FAR 15.201(c) | Pre-solicitation conferences |

---

## Best Practices

1. **Start Early:** Begin pre-solicitation 6-9 months before anticipated contract award
2. **Use RAG:** Enable RAG for better cost benchmarking from ALMS documents
3. **Market Research:** Run Sources Sought before RFI to narrow vendor pool
4. **Industry Engagement:** Hold Industry Day after RFI responses to clarify requirements
5. **Iterative Refinement:** Use RFI feedback to refine Acquisition Plan and IGCE
6. **Small Business:** Engage Small Business Specialist early for set-aside determination
7. **Legal Review:** Have legal counsel review Acquisition Plan before approval

---

## Next Steps

After completing pre-solicitation:

1. **Approve Acquisition Plan** - Get stakeholder signatures
2. **Post Sources Sought** - Publish to SAM.gov
3. **Collect RFI Responses** - Analyze vendor capabilities
4. **Hold Industry Day** - Brief industry and answer questions
5. **Refine Requirements** - Update PWS/SOW based on feedback
6. **Validate IGCE** - Adjust cost estimate based on industry feedback
7. **Post Pre-Solicitation Notice** - 15+ days before RFP
8. **Prepare Draft RFP** - Begin solicitation document preparation

---

## Support

For questions or issues:
- Check troubleshooting section above
- Review template files in `templates/`
- Run individual tests: `python scripts/run_pre_solicitation_pipeline.py --individual`
- Check agent logs for detailed error messages

---

**Document Version:** 1.0  
**Last Updated:** January 2025  
**Author:** DoD Contracting Automation Team

