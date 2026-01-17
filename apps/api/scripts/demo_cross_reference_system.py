#!/usr/bin/env python3
"""
Demo: Cross-Reference System

Demonstrates how documents can reference each other using the metadata store.

This script shows:
1. Generating an IGCE and saving its metadata
2. Generating an Acquisition Plan that references the IGCE
3. Verifying the cross-reference worked
"""

import os
import sys
from pathlib import Path

# Add parent directory to path

from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


def demo_cross_reference_workflow():
    """Demonstrate complete cross-reference workflow"""

    print("\n" + "="*70)
    print("CROSS-REFERENCE SYSTEM DEMONSTRATION")
    print("="*70)

    # Initialize components
    metadata_store = DocumentMetadataStore('data/document_metadata.json')
    extractor = DocumentDataExtractor()

    # ========== STEP 1: Generate IGCE ==========
    print("\n" + "="*70)
    print("STEP 1: Generate IGCE Document")
    print("="*70)

    # Simulate IGCE generation (in reality, this would come from IGCEGeneratorAgent)
    igce_content = """
# INDEPENDENT GOVERNMENT COST ESTIMATE (IGCE)
## Advanced Logistics Management System (ALMS)

**Classification**: UNCLASSIFIED
**Prepared by**: Government Cost Estimator
**Date**: 2025-10-16

---

## Executive Summary

**Total Program Cost**: $2,847,500
**Period of Performance**: 36 months (Base + 2 Option Years)
**Contract Type**: Firm Fixed Price (FFP)

---

## 8. TOTAL COST SUMMARY

| Category | Base Year (12 months) | Option Year 1 | Option Year 2 | **Total** |
|----------|----------------------|---------------|---------------|-----------|
| Labor | $1,000,000 | $700,000 | $700,000 | **$2,400,000** |
| Hardware | $150,000 | $50,000 | $50,000 | **$250,000** |
| Software | $95,000 | $51,250 | $51,250 | **$197,500** |
| **TOTAL** | **$1,245,000** | **$801,250** | **$801,250** | **$2,847,500** |

---

## 9. LABOR CATEGORIES

| Category | Education | Rate |
|----------|-----------|------|
| Senior Software Engineer | BS + 10 years | $165/hr |
| Project Manager | BS + 8 years | $175/hr |
| DevOps Engineer | BS + 5 years | $145/hr |
| QA Engineer | BS + 3 years | $115/hr |
| Technical Writer | BA + 3 years | $95/hr |
| Database Administrator | BS + 5 years | $135/hr |
| Security Engineer | BS + 7 years | $155/hr |
| Business Analyst | BA + 5 years | $125/hr |
"""

    # Save IGCE content to file
    igce_file_path = 'output/demo_igce_alms.md'
    os.makedirs('output', exist_ok=True)
    with open(igce_file_path, 'w') as f:
        f.write(igce_content)

    print(f"✅ Generated IGCE document: {igce_file_path}")
    print(f"   Word count: {len(igce_content.split())}")

    # Extract structured data from IGCE
    print("\n📊 Extracting structured data from IGCE...")
    igce_data = extractor.extract_igce_data(igce_content)

    print("\nExtracted Data:")
    print(f"  • Total Cost: {igce_data['total_cost_formatted']}")
    print(f"  • Base Year Cost: ${igce_data['base_year_cost']:,.2f}")
    print(f"  • Option Year Costs: {len(igce_data['option_year_costs'])} years")
    for i, cost in enumerate(igce_data['option_year_costs'], 1):
        print(f"    - Option {i}: ${cost:,.2f}")
    print(f"  • Period: {igce_data['period_of_performance']}")
    print(f"  • Labor Categories: {igce_data['labor_categories_count']}")

    # Save metadata
    print("\n💾 Saving IGCE metadata to store...")
    igce_doc_id = metadata_store.save_document(
        doc_type='igce',
        program='ALMS',
        content=igce_content,
        file_path=igce_file_path,
        extracted_data=igce_data
    )

    print(f"✅ Metadata saved with ID: {igce_doc_id}")

    # ========== STEP 2: Generate Acquisition Plan ==========
    print("\n" + "="*70)
    print("STEP 2: Generate Acquisition Plan (with IGCE cross-reference)")
    print("="*70)

    # Find the IGCE we just created
    print("\n🔍 Looking up latest IGCE for ALMS...")
    latest_igce = metadata_store.find_latest_document('igce', 'ALMS')

    if latest_igce:
        print(f"✅ Found IGCE: {latest_igce['id']}")
        print(f"   Generated: {latest_igce['generated_date']}")
        print(f"   Total Cost: {latest_igce['extracted_data']['total_cost_formatted']}")

        # Generate IGCE summary for inclusion in Acquisition Plan
        print("\n📝 Generating IGCE summary...")
        igce_summary = extractor.generate_igce_summary(latest_igce['extracted_data'])
        print(f"\nGenerated Summary:\n{igce_summary}")

        # Safely get option year costs
        option_costs = latest_igce['extracted_data']['option_year_costs']
        opt1_cost = option_costs[0] if len(option_costs) > 0 else 0
        opt2_cost = option_costs[1] if len(option_costs) > 1 else 0

        # Simulate Acquisition Plan generation
        acq_plan_content = f"""
# ACQUISITION PLAN
## Advanced Logistics Management System (ALMS)

**Program**: Advanced Logistics Management System (ALMS)
**Organization**: U.S. Army
**Date**: 2025-10-16

---

## EXECUTIVE SUMMARY

### Total Program Cost
**Estimated Total Cost**: {latest_igce['extracted_data']['total_cost_formatted']}

---

## 3. COST (FAR 7.105(a)(3))

### 3.1 Total Program Cost Estimate

| Cost Category | Base Year | Option Year 1 | Option Year 2 | **Total** |
|---------------|-----------|---------------|---------------|-----------|
| Development | ${latest_igce['extracted_data']['base_year_cost']:,.2f} | ${opt1_cost:,.2f} | ${opt2_cost:,.2f} | **{latest_igce['extracted_data']['total_cost_formatted']}** |

### 3.4 Independent Government Cost Estimate (IGCE)

{igce_summary}

---

## 4. ACQUISITION STRATEGY

The acquisition strategy for ALMS is to use a Firm Fixed Price (FFP) contract
with a total estimated value of {latest_igce['extracted_data']['total_cost_formatted']}
over {latest_igce['extracted_data']['period_of_performance']}.

The IGCE analysis identified {latest_igce['extracted_data']['labor_categories_count']}
labor categories required for successful program execution.
"""

        # Save Acquisition Plan
        acq_plan_file_path = 'output/demo_acquisition_plan_alms.md'
        with open(acq_plan_file_path, 'w') as f:
            f.write(acq_plan_content)

        print(f"\n✅ Generated Acquisition Plan: {acq_plan_file_path}")
        print(f"   Word count: {len(acq_plan_content.split())}")

        # Extract data from Acquisition Plan
        print("\n📊 Extracting structured data from Acquisition Plan...")
        acq_plan_data = extractor.extract_acquisition_plan_data(acq_plan_content)

        print("\nExtracted Data:")
        print(f"  • Total Cost: {acq_plan_data['total_cost_formatted']}")
        print(f"  • Contract Type: {acq_plan_data['contract_type']}")
        print(f"  • Period: {acq_plan_data['period_of_performance']}")

        # Save Acquisition Plan metadata with reference to IGCE
        print("\n💾 Saving Acquisition Plan metadata with IGCE reference...")
        acq_plan_doc_id = metadata_store.save_document(
            doc_type='acquisition_plan',
            program='ALMS',
            content=acq_plan_content,
            file_path=acq_plan_file_path,
            extracted_data=acq_plan_data,
            references={'igce': igce_doc_id}  # ← Cross-reference!
        )

        print(f"✅ Metadata saved with ID: {acq_plan_doc_id}")
        print(f"✅ Cross-reference to IGCE: {igce_doc_id}")

    else:
        print("❌ No IGCE found - cannot generate Acquisition Plan")
        return

    # ========== STEP 3: Verify Cross-References ==========
    print("\n" + "="*70)
    print("STEP 3: Verify Cross-References")
    print("="*70)

    # Get cross-references for Acquisition Plan
    print(f"\n🔗 Getting cross-references for {acq_plan_doc_id}...")
    cross_refs = metadata_store.get_cross_references(acq_plan_doc_id)

    print(f"\nFound {len(cross_refs)} cross-reference(s):")
    for ref_type, ref_doc in cross_refs.items():
        print(f"\n  Reference Type: {ref_type}")
        print(f"  Referenced Document: {ref_doc['id']}")
        print(f"  Document Type: {ref_doc['type']}")
        print(f"  Generated: {ref_doc['generated_date']}")
        if ref_type == 'igce':
            print(f"  IGCE Total Cost: {ref_doc['extracted_data']['total_cost_formatted']}")

    # Get documents that reference the IGCE
    print(f"\n🔗 Finding documents that reference IGCE {igce_doc_id}...")
    referring_docs = metadata_store.get_referring_documents(igce_doc_id)

    print(f"\nFound {len(referring_docs)} document(s) referencing this IGCE:")
    for doc in referring_docs:
        print(f"  • {doc['id']} ({doc['type']})")

    # ========== STEP 4: Verify Consistency ==========
    print("\n" + "="*70)
    print("STEP 4: Verify Data Consistency")
    print("="*70)

    print("\n✓ Checking if cost data is consistent across documents...")

    igce_total = latest_igce['extracted_data']['total_cost']
    acq_plan_total = acq_plan_data['total_cost']

    print(f"\n  IGCE Total Cost:     ${igce_total:,.2f}")
    print(f"  Acq Plan Total Cost: ${acq_plan_total:,.2f}")

    if igce_total == acq_plan_total:
        print(f"\n  ✅ CONSISTENT: Costs match across documents")
    else:
        diff = abs(igce_total - acq_plan_total)
        print(f"\n  ⚠️  INCONSISTENT: ${diff:,.2f} difference")

    # ========== STEP 5: Show Metadata Store Summary ==========
    print("\n" + "="*70)
    print("STEP 5: Metadata Store Summary")
    print("="*70)

    metadata_store.print_summary()

    # ========== STEP 6: Show Generated Files ==========
    print("\n" + "="*70)
    print("GENERATED FILES")
    print("="*70)
    print(f"\n1. IGCE Document:")
    print(f"   📄 {igce_file_path}")
    print(f"\n2. Acquisition Plan Document:")
    print(f"   📄 {acq_plan_file_path}")
    print(f"\n3. Metadata Store:")
    print(f"   📄 data/document_metadata.json")

    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    print("\nKey Achievements:")
    print("  ✅ Generated IGCE with structured data extraction")
    print("  ✅ Generated Acquisition Plan that references IGCE")
    print("  ✅ Verified cross-references are stored and retrievable")
    print("  ✅ Confirmed data consistency across documents")
    print("\nNext Steps:")
    print("  • Integrate this system into actual agents")
    print("  • Add more document types (PWS, QASP, etc.)")
    print("  • Create automated consistency validation")
    print("="*70 + "\n")


if __name__ == '__main__':
    demo_cross_reference_workflow()
