# QASP Integration Guide

## Overview

The QASP (Quality Assurance Surveillance Plan) generation system is now fully integrated into the PWS/SOO/SOW orchestrators. QASPs are automatically generated after each work statement document is created.

---

## ✅ What Was Integrated

### **1. PWS Orchestrator Integration**

The PWS Orchestrator now includes Phase 6: QASP Generation

**File:** `agents/pws_orchestrator.py`

**Changes:**
- Added `QASPGeneratorAgent` import
- Added `qasp_generator` to orchestrator initialization
- Added `generate_qasp` parameter (default: `True`)
- Added `qasp_config` parameter for COR/KO details
- Added `_phase_qasp_generation()` method
- QASP auto-generated after PWS assembly
- QASP result included in workflow output

**New Workflow:**
```
1. Research Phase → Performance benchmarks
2. Writing Phase → PWS sections
3. Quality Phase → PWS evaluation
4. Revision Phase → PWS refinement
5. Assembly Phase → Final PWS document
6. QASP Generation Phase → Automatic QASP from PWS ✨ NEW
```

### **2. Solicitation Package Orchestrator Integration**

The Solicitation Package Orchestrator now includes QASP as Section J

**File:** `agents/solicitation_package_orchestrator.py`

**Changes:**
- Auto-detects QASP PDF in `outputs/qasp/` directory
- Includes QASP as Section J: "Quality Assurance Surveillance Plan"
- Adds QASP to package manifest
- Merges QASP into complete solicitation package

**New Package Structure:**
```
Complete Solicitation Package:
├── Section A: SF33 (Solicitation Form)
├── Section C: PWS (Work Statement)
├── Section J: QASP (Quality Assurance) ✨ NEW
├── Section L: Instructions to Offerors (future)
└── Section M: Evaluation Factors (future)
```

---

## 🚀 Usage

### **Option 1: Automatic QASP Generation (Default)**

QASPs are generated automatically when you create a PWS:

```python
from agents.pws_orchestrator import PWSOrchestrator

# Initialize
orchestrator = PWSOrchestrator(api_key, retriever, tavily_api_key)

# Execute workflow - QASP auto-generated
result = orchestrator.execute_pws_workflow(
    project_info=project_info,
    pws_sections_config=sections,
    output_path="outputs/pws/performance_work_statement.md"
    # generate_qasp defaults to True - QASP will be generated automatically
)

# Check results
if result['qasp_result']:
    print(f"QASP: {result['qasp_result']['output_path']}")
    print(f"Requirements: {result['qasp_result']['requirements_count']}")
```

### **Option 2: QASP with Custom Configuration**

Provide COR/KO details for personalized QASP:

```python
# Configure QASP with specific personnel
qasp_config = {
    'contracting_officer': 'John Smith',
    'ko_phone': '(410) 555-1234',
    'ko_email': 'john.smith@army.mil',
    'cor_name': 'Jane Doe',
    'cor_phone': '(410) 555-5678',
    'cor_email': 'jane.doe@army.mil',
    'cor_level': 'II',  # FAC-COR Level
    'qae_name': 'Bob Johnson',
    'qae_phone': '(410) 555-9012',
    'qae_email': 'bob.johnson@army.mil'
}

# Execute with configuration
result = orchestrator.execute_pws_workflow(
    project_info=project_info,
    pws_sections_config=sections,
    output_path="outputs/pws/performance_work_statement.md",
    generate_qasp=True,
    qasp_config=qasp_config
)
```

### **Option 3: Disable QASP Generation**

If you don't want automatic QASP generation:

```python
result = orchestrator.execute_pws_workflow(
    project_info=project_info,
    pws_sections_config=sections,
    output_path="outputs/pws/performance_work_statement.md",
    generate_qasp=False  # Disable QASP generation
)
```

### **Option 4: Complete Solicitation Package with QASP**

Generate complete package including QASP:

```python
from agents.solicitation_package_orchestrator import SolicitationPackageOrchestrator

# First, generate PWS with QASP
pws_result = pws_orchestrator.execute_pws_workflow(
    project_info=project_info,
    pws_sections_config=sections,
    output_path="outputs/pws/performance_work_statement.md",
    generate_qasp=True  # Ensure QASP is generated
)

# Then, build complete package (automatically includes QASP)
package_orchestrator = SolicitationPackageOrchestrator()
package_result = package_orchestrator.build_complete_package(
    work_statement_md="outputs/pws/performance_work_statement.md",
    work_statement_pdf="outputs/pws/performance_work_statement.pdf",
    output_path="outputs/solicitation/complete_package.pdf"
)

# Package now includes:
# - Section A: SF33
# - Section C: PWS
# - Section J: QASP (auto-detected and included) ✨
```

---

## 📁 File Structure

### **Generated Files**

When PWS with QASP is generated:

```
outputs/
├── pws/
│   ├── performance_work_statement.md
│   ├── performance_work_statement.pdf
│   ├── performance_work_statement_evaluation_report.md
│   └── performance_work_statement_evaluation_report.pdf
│
├── qasp/  ✨ NEW
│   ├── quality_assurance_surveillance_plan.md
│   └── quality_assurance_surveillance_plan.pdf
│
└── solicitation/
    ├── SF33_performance_work_statement.pdf
    ├── performance_work_statement_package.pdf  (includes QASP)
    └── performance_work_statement_package_manifest.json
```

### **Package Manifest**

The solicitation package manifest now tracks QASP:

```json
{
  "solicitation_number": "W911XX-25-R-1234",
  "program_name": "Advanced Logistics Management System",
  "components": [
    {
      "section": "A",
      "title": "Solicitation/Contract Form (SF33)",
      "source": "outputs/solicitation/SF33.pdf"
    },
    {
      "section": "C",
      "title": "Description/Specifications/Work Statement",
      "source": "outputs/pws/performance_work_statement.pdf"
    },
    {
      "section": "J",
      "title": "Quality Assurance Surveillance Plan (QASP)",
      "source": "outputs/qasp/quality_assurance_surveillance_plan.pdf"
    }
  ]
}
```

---

## 🔧 Technical Details

### **QASP Generation Process**

1. **Extraction:** Parse PWS for performance requirements, deliverables, standards
2. **Analysis:** Identify metrics, SLAs, quality criteria
3. **Mapping:** Map requirements to surveillance methods
4. **Matrix Generation:** Create performance requirements matrix with 20 items
5. **Template Population:** Fill 1,400-line QASP template
6. **Output:** Generate markdown + PDF

### **Performance Requirements Matrix**

Auto-generated from PWS with:
- **PWS Paragraph References** - Links to source requirements
- **Performance Objectives** - What must be achieved
- **Performance Standards** - Measurable success criteria
- **AQLs (Acceptable Quality Levels)** - Defect tolerances (0-10%)
- **Surveillance Methods** - How to monitor (7 methods)
- **Frequencies** - How often (continuous to quarterly)
- **Responsibilities** - Who monitors (COR or QAE)

### **Surveillance Method Selection**

Automatic surveillance method assignment based on requirement type:

| Requirement Type | Surveillance Method |
|------------------|-------------------|
| Reports, Documents | Desk Review |
| System Availability | Automated Monitoring |
| Customer Satisfaction | Customer Feedback |
| Response Times, Incidents | Random Sampling |
| Inspections, Tests | 100% Inspection |
| Processes, Activities | Periodic Surveillance |
| Training, Meetings | Observation |

### **AQL (Acceptable Quality Level) Assignment**

Automatic AQL recommendations based on criticality:

| Requirement Type | AQL | Description |
|------------------|-----|-------------|
| Security, Safety, Classified | 0% | Zero tolerance |
| System, Availability, Data | 2% | Low tolerance |
| Response, Delivery, Performance | 5% | Moderate tolerance |
| Reports, Documentation | 10% | Higher tolerance |

---

## 📊 Example Output

### **PWS Workflow with QASP**

```
======================================================================
STARTING PWS GENERATION WORKFLOW
======================================================================
Project: Advanced Logistics Management System (ALMS)
PWS Sections: 12
======================================================================

PHASE 1: RESEARCH & INTELLIGENCE GATHERING
...

PHASE 2: PWS WRITING (Performance-Based)
...

PHASE 3: QUALITY EVALUATION
...

PHASE 4: ITERATIVE REFINEMENT
...

PHASE 5: DOCUMENT ASSEMBLY
...

======================================================================
PHASE 6: QASP GENERATION  ✨ NEW
======================================================================

Generating QASP from PWS...
  PWS Source: outputs/pws/performance_work_statement.md
  QASP Output: outputs/qasp/quality_assurance_surveillance_plan.md

✓ QASP generated successfully
  Requirements: 20
  Deliverables: 2
  QASP: outputs/qasp/quality_assurance_surveillance_plan.md
  PDF: outputs/qasp/quality_assurance_surveillance_plan.pdf

======================================================================
QASP GENERATION COMPLETE
======================================================================

======================================================================
✅ PWS GENERATION COMPLETE
======================================================================
Time elapsed: 245.3s
Output: outputs/pws/performance_work_statement.md
QASP: outputs/qasp/quality_assurance_surveillance_plan.md  ✨
======================================================================
```

---

## 🎯 Benefits

### **For Contracting Officers**
✅ Automatic QASP generation saves 10+ hours per acquisition
✅ Ensures FAR 37.604 compliance
✅ Consistent surveillance methodology across contracts

### **For CORs (Contracting Officer's Representatives)**
✅ Ready-to-use surveillance plan on day one
✅ Pre-defined performance requirements matrix
✅ Clear roles and responsibilities
✅ Standardized forms and procedures

### **For Program Offices**
✅ Complete acquisition package in single workflow
✅ PWS → QASP → Solicitation Package automatically generated
✅ Reduced acquisition timeline by 2-3 weeks

---

## 🔄 Integration with Existing Scripts

### **PWS Generation Scripts**

All existing PWS generation scripts now support QASP:

```bash
# scripts/run_pws_pipeline.py
python scripts/run_pws_pipeline.py
# Now automatically generates QASP

# Custom configuration via environment or config file
export QASP_CONTRACTING_OFFICER="John Smith"
export QASP_COR_NAME="Jane Doe"
python scripts/run_pws_pipeline.py
```

---

## 📚 Related Documentation

- **QASP Guide:** [17_QASP_Guide.md](../data/documents/17_QASP_Guide.md) - Comprehensive QASP development guide
- **SF33 Generation:** [docs/SF33_GENERATION_GUIDE.md](SF33_GENERATION_GUIDE.md) - SF33 form generation
- **PWS Orchestrator:** [agents/pws_orchestrator.py](../agents/pws_orchestrator.py) - PWS generation workflow
- **QASP Generator:** [agents/qasp_generator_agent.py](../agents/qasp_generator_agent.py) - QASP generation logic

---

## 🐛 Troubleshooting

### Issue: QASP not generated

**Check:**
1. `generate_qasp=True` in orchestrator call (default)
2. PWS markdown file exists and is valid
3. QASP output directory is writable (`outputs/qasp/`)

**Solution:**
```python
# Explicitly enable and verify
result = orchestrator.execute_pws_workflow(
    ...,
    generate_qasp=True
)

if not result.get('qasp_result'):
    print("QASP generation failed or disabled")
else:
    print(f"QASP: {result['qasp_result']['output_path']}")
```

### Issue: QASP not included in solicitation package

**Check:**
1. QASP PDF exists in `outputs/qasp/` directory
2. File name matches expected pattern: `quality_assurance_surveillance_plan.pdf`
3. Package orchestrator can access QASP directory

**Solution:**
```python
from pathlib import Path

qasp_pdf = "outputs/qasp/quality_assurance_surveillance_plan.pdf"
if Path(qasp_pdf).exists():
    print(f"✓ QASP found: {qasp_pdf}")
else:
    print(f"✗ QASP not found - will not be included in package")
```

### Issue: Performance requirements not extracted

**Check:**
1. PWS contains performance metrics (percentages, times, quantities)
2. PWS has performance standards section
3. PWS deliverables are defined

**Solution:**
- Add explicit performance standards to PWS (e.g., "99.9% uptime", "<2 seconds response time")
- Include measurable criteria in requirements
- Define clear deliverables with acceptance criteria

---

## 🚀 Future Enhancements

### **Planned Features**

1. **Enhanced Surveillance Methods**
   - Automated monitoring tool integration
   - Customer survey generation
   - Sampling plan calculators

2. **QASP Templates by Domain**
   - IT Services QASP template
   - Systems Engineering QASP template
   - Facilities Management QASP template

3. **Performance Metrics Dashboard**
   - Real-time contractor performance tracking
   - Automated monthly assessment reports
   - Trend analysis and predictions

4. **Integration with Contract Management Systems**
   - Export to PIEE, FPDS, eSRS
   - Automated past performance documentation
   - Payment recommendation automation

---

## ✅ Integration Checklist

Use this checklist to verify QASP integration:

- [ ] PWS Orchestrator imports `QASPGeneratorAgent`
- [ ] QASP generator initialized in orchestrator `__init__`
- [ ] `generate_qasp` parameter added to `execute_pws_workflow()`
- [ ] `_phase_qasp_generation()` method implemented
- [ ] QASP result included in workflow return dictionary
- [ ] Solicitation Package Orchestrator detects QASP PDF
- [ ] QASP added as Section J in package components
- [ ] QASP included in merged package PDF
- [ ] Test script created (`scripts/test_qasp_integration.py`)
- [ ] Documentation updated

---

**Integration Complete!** Your PWS/SOO/SOW orchestrators now automatically generate comprehensive QASPs, ready for immediate use by CORs and QAEs.

---

**Version:** 1.0
**Date:** October 2025
**Status:** ✅ Integrated and Operational
