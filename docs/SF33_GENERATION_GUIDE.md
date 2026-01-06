# SF33 Solicitation Form Generation Guide

## Overview

This system automatically generates SF33 (Solicitation, Offer, and Award) forms from PWS/SOO/SOW documents and assembles complete Federal acquisition solicitation packages.

**SF33 Form:** Standard Form 33 is the official solicitation/contract form used by the Federal government, prescribed by FAR (48 CFR) 53.214(c).

## Features

✅ **Automatic Data Extraction** - Extracts project metadata from PWS/SOO/SOW documents
✅ **PDF Form Filling** - Populates interactive SF33 PDF form fields
✅ **Solicitation Number Generation** - Generates DoD-style solicitation numbers
✅ **Package Assembly** - Combines SF33 + work statements into complete packages
✅ **Multi-Document Support** - Works with PWS, SOO, and SOW documents
✅ **Manifest Generation** - Creates JSON metadata for each package

## System Architecture

### Components

1. **SF33 Field Extractor** (`utils/sf33_field_extractor.py`)
   - Extracts metadata from markdown documents
   - Generates solicitation numbers
   - Maps data to SF33 form fields

2. **PDF Form Filler** (`utils/pdf_form_filler.py`)
   - Fills interactive PDF form fields
   - Validates field mappings
   - Saves filled PDFs

3. **SF33 Generator Agent** (`agents/sf33_generator_agent.py`)
   - Orchestrates extraction and filling
   - Validates required fields
   - Generates filled SF33 forms

4. **Solicitation Package Orchestrator** (`agents/solicitation_package_orchestrator.py`)
   - Assembles complete solicitation packages
   - Merges multiple PDFs
   - Generates package manifests

5. **CLI Script** (`scripts/generate_sf33.py`)
   - Command-line interface
   - Batch processing support

## Installation

### Prerequisites

```bash
# Required Python packages
pip install pypdf PyPDF2
```

### Verify Installation

```bash
python -c "import pypdf; print('pypdf version:', pypdf.__version__)"
```

## Usage

### Basic Usage: Generate SF33 Only

Generate SF33 for a single document:

```bash
python scripts/generate_sf33.py \
  --work-statement outputs/pws/performance_work_statement.md
```

Output:
- `outputs/solicitation/SF33_performance_work_statement.pdf`

### Generate Complete Solicitation Package

Generate SF33 + work statement in single package:

```bash
python scripts/generate_sf33.py \
  --package \
  --work-statement outputs/pws/performance_work_statement.md
```

Output:
- `outputs/solicitation/performance_work_statement_package.pdf` (SF33 + PWS merged)
- `outputs/solicitation/performance_work_statement_package_manifest.json` (metadata)

### Generate for All Document Types

Generate SF33 for all available PWS/SOO/SOW documents:

```bash
python scripts/generate_sf33.py --all
```

Output:
- `outputs/solicitation/SF33_performance_work_statement.pdf`
- `outputs/solicitation/SF33_statement_of_objectives.pdf`
- `outputs/solicitation/SF33_statement_of_work.pdf`

### Advanced Options

```bash
# Custom output directory
python scripts/generate_sf33.py \
  --work-statement outputs/pws/performance_work_statement.md \
  --output-dir outputs/solicitation/custom

# Custom SF33 template
python scripts/generate_sf33.py \
  --work-statement outputs/pws/performance_work_statement.md \
  --sf33-template data/templates/SF33_custom.pdf

# Quiet mode (less output)
python scripts/generate_sf33.py \
  --work-statement outputs/pws/performance_work_statement.md \
  --quiet
```

## SF33 Form Field Mapping

### Extracted from Documents

| Metadata Field | SF33 Field | Source |
|----------------|------------|--------|
| Program Name | Section C title | `**Program:** Advanced Logistics...` |
| Organization | Block 7 (Issued By) | `**Organization:** DOD/ARMY/LOGISTICS` |
| Date | Block 5 (Date Issued) | `**Date:** 10/05/2025` |
| Author | Block 10A (Contact Name) | `**Author:** John Smith` |
| Budget | Referenced in description | `$2.5 million` |
| Period | Referenced in description | `36 months` |

### Auto-Generated Fields

| Field | Format | Example |
|-------|--------|---------|
| Solicitation Number | W911XX-YY-R-XXXX | W911XX-25-R-7768 |
| Contract Number | TBD (assigned at award) | TBD |
| Type | RFP (Request for Proposal) | Negotiated (RFP) |
| Page Numbers | Section-based | A:1, C:2, L:48, M:49 |

### SF33 Form Sections

**Completed by System:**
- Block 1: Rating (DPAS code)
- Block 2: Contract Number (TBD)
- Block 3: Solicitation Number (auto-generated)
- Block 4: Type (RFP checkbox)
- Block 5: Date Issued
- Block 6: Requisition Number
- Block 7: Issued By (organization)
- Block 10: Contact Information
- Block 11: Table of Contents (section page numbers)

**Completed by Offeror:**
- Block 12-18: Offer details, signature, dates

**Completed by Government (Award):**
- Block 19-28: Award details, contracting officer signature

## Output Structure

### Individual SF33

```
outputs/solicitation/
├── SF33_performance_work_statement.pdf   (SF33 only)
├── SF33_statement_of_objectives.pdf      (SF33 only)
└── SF33_statement_of_work.pdf            (SF33 only)
```

### Complete Package

```
outputs/solicitation/
├── performance_work_statement_package.pdf           (SF33 + PWS merged - 47 pages)
├── performance_work_statement_package_manifest.json (metadata)
└── performance_work_statement_package_SF33.pdf      (SF33 component)
```

### Package Manifest

```json
{
  "solicitation_number": "W911XX-25-R-5137",
  "program_name": "Advanced Logistics Management System (ALMS)",
  "organization": "DOD/ARMY/LOGISTICS",
  "generated_date": "2025-10-09T11:13:35.188727",
  "package_path": "outputs/solicitation/performance_work_statement_package.pdf",
  "components": [
    {
      "section": "A",
      "title": "Solicitation/Contract Form (SF33)",
      "source": "outputs/solicitation/performance_work_statement_package_SF33.pdf"
    },
    {
      "section": "C",
      "title": "Description/Specifications/Work Statement",
      "source": "outputs/pws/performance_work_statement.pdf"
    }
  ],
  "metadata": {
    "document_type": "PWS",
    "program_name": "Advanced Logistics Management System (ALMS)",
    "organization": "DOD/ARMY/LOGISTICS",
    "date": "10/05/2025",
    "author": "John Smith",
    "budget": "$2.5 million",
    "period_of_performance": "12 months"
  }
}
```

## Integration with Existing Workflows

### With PWS/SOO/SOW Orchestrators

The SF33 generation can be integrated into existing document generation workflows:

```python
from agents.pws_orchestrator import PWSOrchestrator
from agents.sf33_generator_agent import SF33GeneratorAgent
from agents.solicitation_package_orchestrator import SolicitationPackageOrchestrator

# 1. Generate PWS
pws_orchestrator = PWSOrchestrator(api_key, retriever)
pws_result = pws_orchestrator.execute_pws_workflow(
    project_info=project_info,
    pws_sections_config=sections,
    output_path="outputs/pws/performance_work_statement.md"
)

# 2. Generate SF33 and complete package
package_orchestrator = SolicitationPackageOrchestrator()
package_result = package_orchestrator.build_complete_package(
    work_statement_md="outputs/pws/performance_work_statement.md",
    work_statement_pdf="outputs/pws/performance_work_statement.pdf",
    output_path="outputs/solicitation/ALMS_Solicitation_Package.pdf"
)

print(f"Solicitation Package: {package_result['output_path']}")
print(f"Solicitation Number: {package_result['solicitation_number']}")
```

### Standalone Usage

```python
from agents.sf33_generator_agent import SF33GeneratorAgent

# Generate SF33 only
agent = SF33GeneratorAgent()
result = agent.execute(
    work_statement_path="outputs/pws/performance_work_statement.md",
    output_path="outputs/solicitation/SF33_ALMS.pdf"
)

if result['success']:
    print(f"SF33 generated: {result['output_path']}")
    print(f"Solicitation #: {result['solicitation_number']}")
    print(f"Fields filled: {result['fields_filled']}")
```

## Troubleshooting

### Issue: No form fields found in PDF

**Problem:** SF33.pdf doesn't have fillable form fields

**Solution:**
- Verify SF33.pdf is the correct fillable form version
- Download official SF33 from GSA.gov: https://www.gsa.gov/reference/forms/solicitation-offer-and-award
- Ensure PDF has interactive form fields (not just a flat image)

### Issue: Fields not filling correctly

**Problem:** PDF form fields have unexpected names

**Solution:**
- Run field analysis: `python utils/pdf_form_filler.py`
- Update field mappings in `utils/sf33_field_extractor.py`
- Check SF33 template version matches (REV. 12/2022)

### Issue: Missing metadata from documents

**Problem:** Extracted metadata is incomplete

**Solution:**
- Ensure documents have metadata in standard format:
  ```markdown
  **Program:** Program Name
  **Organization:** DOD/ARMY
  **Date:** MM/DD/YYYY
  **Author:** Author Name
  ```
- Update regex patterns in `SF33FieldExtractor._extract_*()` methods

## Future Enhancements

### Planned Features

1. **Section L/M Templates**
   - Instructions to Offerors template generation
   - Evaluation Factors template generation

2. **Enhanced Form Support**
   - SF1449 (Solicitation/Contract/Order)
   - SF30 (Amendment of Solicitation/Modification)
   - SF1442 (Solicitation, Offer and Award - Construction)

3. **Additional Data Extraction**
   - NAICS codes from documents
   - Contract clauses and provisions
   - Security requirements

4. **Validation & Compliance**
   - FAR compliance checking
   - Required clause verification
   - Field completeness validation

5. **Batch Processing**
   - Process multiple projects at once
   - Template-based generation
   - Automated quality checks

## References

- **FAR 53.214**: Solicitation provisions and contract clauses (SF 33)
- **GSA SF33 Form**: https://www.gsa.gov/reference/forms/solicitation-offer-and-award
- **DAU SF33 Guide**: https://www.dau.edu/cop/Contingency/documents/sf-form-33-solicitation-offer-and-award
- **FAR Part 15**: Contracting by Negotiation

## Support

For issues or questions:
1. Check this guide and troubleshooting section
2. Review generated manifest JSON for metadata
3. Test with sample documents in `outputs/` directory
4. Check PDF form field names with `pdf_form_filler.py`

---

**Generated:** October 2025
**Version:** 1.0
**System:** DoD Acquisition Document Generation Framework
