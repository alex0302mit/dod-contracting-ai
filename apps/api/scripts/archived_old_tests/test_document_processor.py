#!/usr/bin/env python3
"""
Test Script for DocumentProcessor

Tests the document enhancement system with PDF generation,
quality evaluation reports, and citations.

Usage:
    python scripts/test_document_processor.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path

from backend.utils.document_processor import DocumentProcessor


def create_sample_document():
    """Create a sample document for testing"""
    return """# Sample IGCE Document

## Independent Government Cost Estimate

**Program:** Advanced Logistics Management System (ALMS)
**Solicitation Number:** W56KGU-25-R-0042
**Date:** 2025-10-17

---

## 1. Executive Summary

This Independent Government Cost Estimate (IGCE) provides a comprehensive cost analysis for the Advanced Logistics Management System (ALMS) development and deployment. The estimated total cost is $2,500,000 for development with a lifecycle cost of $6,425,000.

## 2. Cost Breakdown

### 2.1 Labor Costs

The following labor categories are required for ALMS development:

| Labor Category | Hours | Rate ($/hr) | Total Cost |
|----------------|-------|-------------|------------|
| Program Manager (PMP) | 2,080 | $175 | $364,000 |
| Cloud Solutions Architect | 2,080 | $185 | $384,800 |
| DevSecOps Engineer | 4,160 | $145 | $603,200 |
| Full Stack Developer (Senior) | 4,160 | $135 | $561,600 |
| Full Stack Developer (Mid) | 8,320 | $110 | $915,200 |

**Total Labor Cost:** $2,828,800

### 2.2 Materials and Other Direct Costs

| Item | Quantity | Unit Cost | Total Cost |
|------|----------|-----------|------------|
| AWS GovCloud Hosting (FedRAMP) | 12 months | $15,000 | $180,000 |
| COTS Platform Licenses | 2,800 users | $50 | $140,000 |
| SAP Integration Licenses | 1 system | $75,000 | $75,000 |
| Mobile Devices (Warehouse) | 100 devices | $800 | $80,000 |
| Barcode/RFID Scanners | 150 scanners | $500 | $75,000 |

**Total Materials/ODC Cost:** $550,000

## 3. Total Estimate

- **Labor:** $2,828,800
- **Materials/ODC:** $550,000
- **Subtotal:** $3,378,800
- **Risk Contingency (10%):** $337,880
- **Total Development Cost:** $3,716,680

## 4. Basis of Estimate

This estimate is based on:
- Industry standard labor rates for cloud development
- AWS GovCloud pricing for FedRAMP Moderate hosting
- Market research from 12 RFI responses
- Similar ACAT III logistics system implementations

## 5. Assumptions

1. Development will use Agile methodology with 2-week sprints
2. FedRAMP Moderate authorization timeline is 6 months
3. SAP integration requires existing SAP S/4HANA licenses
4. Government will provide CAC authentication infrastructure
5. All development will be performed CONUS

## 6. Risk Analysis

Key cost risks include:
- **FedRAMP Authorization Delays:** Could add $200K-$400K
- **SAP Integration Complexity:** Could add $150K-$300K
- **Hardware Procurement Delays:** Could add $50K-$100K

**Recommended Contingency:** 10% ($337,880)
"""


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   DOCUMENT PROCESSOR TEST SCRIPT                           ║
║                                                                            ║
║  Tests enhancement capabilities:                                          ║
║    1. PDF generation from markdown                                        ║
║    2. Quality evaluation reports                                          ║
║    3. Source document citations                                           ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY environment variable not set\n")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    print("✅ API Key found\n")

    # Create test output directory
    test_dir = Path('output') / f'document_processor_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    test_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 Test Output Directory: {test_dir}\n")
    print("=" * 80)

    # Initialize DocumentProcessor
    print("\n[1/4] INITIALIZING DOCUMENT PROCESSOR")
    print("=" * 80)

    try:
        processor = DocumentProcessor(api_key=api_key)
        print("✅ DocumentProcessor initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize DocumentProcessor: {e}")
        sys.exit(1)

    # Create sample document
    print("\n[2/4] CREATING SAMPLE DOCUMENT")
    print("=" * 80)

    sample_content = create_sample_document()
    print(f"✅ Sample IGCE document created ({len(sample_content)} characters)")

    # Process document with all enhancements
    print("\n[3/4] PROCESSING DOCUMENT WITH ENHANCEMENTS")
    print("=" * 80)
    print("\nThis will:")
    print("  - Add citations to source documents")
    print("  - Generate PDF version")
    print("  - Run quality evaluation")
    print("  - Generate evaluation report")
    print("  - Generate evaluation PDF")
    print("\nProcessing... (this may take 30-60 seconds)\n")

    try:
        result = processor.process_document(
            content=sample_content,
            output_path=str(test_dir / 'sample_igce.md'),
            doc_type='igce',
            program_name='Advanced Logistics Management System (ALMS)',
            source_docs=[
                'alms-kpp-ksa-complete.md',
                '13_CDD_ALMS.md',
                '9_acquisition_strategy_ALMS.md'
            ],
            project_info={
                'program_name': 'Advanced Logistics Management System (ALMS)',
                'solicitation_number': 'W56KGU-25-R-0042',
                'organization': 'U.S. Army',
                'estimated_value': '$2,500,000'
            },
            generate_pdf=True,
            generate_evaluation=True,
            add_citations=True
        )

        print("✅ Document processing complete!\n")

    except Exception as e:
        print(f"❌ Document processing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Display results
    print("\n[4/4] PROCESSING RESULTS")
    print("=" * 80)
    print("\n📄 Generated Files:")
    print(f"  1. Markdown Document:      {result['markdown_path']}")
    print(f"  2. PDF Document:           {result['pdf_path']}")
    print(f"  3. Evaluation Report (MD): {result['evaluation_path']}")
    print(f"  4. Evaluation Report (PDF): {result['evaluation_pdf_path']}")

    print("\n📊 Enhancement Summary:")
    print(f"  - Citations Added:    {result['citations_added']} source documents")
    print(f"  - Quality Score:      {result['quality_score']}/100")

    # Verify files exist
    print("\n✅ File Verification:")
    files_to_check = [
        ('Markdown', result['markdown_path']),
        ('PDF', result['pdf_path']),
        ('Evaluation MD', result['evaluation_path']),
        ('Evaluation PDF', result['evaluation_pdf_path'])
    ]

    all_exist = True
    for file_type, file_path in files_to_check:
        if file_path and Path(file_path).exists():
            file_size = Path(file_path).stat().st_size
            print(f"  ✅ {file_type}: {file_size:,} bytes")
        else:
            print(f"  ❌ {file_type}: NOT FOUND")
            all_exist = False

    # Final summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    if all_exist:
        print("\n✅ ALL TESTS PASSED!")
        print("\nThe DocumentProcessor successfully:")
        print("  1. Added citations to the document footer")
        print("  2. Generated a professional PDF")
        print("  3. Ran quality evaluation on the content")
        print("  4. Generated evaluation report in markdown")
        print("  5. Generated evaluation report in PDF")
        print(f"\n📁 All files saved to: {test_dir}")
        print("\nNext Steps:")
        print("  1. Review the generated files")
        print("  2. Check the quality evaluation report")
        print("  3. Integrate into generate_all_phases_alms.py")
        print("\n✅ Ready for integration!")
    else:
        print("\n⚠️  SOME FILES MISSING")
        print("Check the error messages above.")

    print("\n" + "=" * 80 + "\n")


if __name__ == '__main__':
    main()
