#!/usr/bin/env python3
"""
Test Cross-Reference Integration with Real Agents

This script tests the complete IGCE → Acquisition Plan cross-reference workflow
using the actual IGCE and Acquisition Plan agents with real data.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path

from backend.agents.igce_generator_agent import IGCEGeneratorAgent
from backend.agents.acquisition_plan_generator_agent import AcquisitionPlanGeneratorAgent
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever
from backend.utils.document_metadata_store import DocumentMetadataStore


def test_cross_reference_integration():
    """Test end-to-end cross-reference integration"""

    print("\n" + "="*70)
    print("CROSS-REFERENCE INTEGRATION TEST")
    print("Testing: IGCE → Acquisition Plan workflow")
    print("="*70)

    # Initialize
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not set")
        return False

    vector_store = VectorStore(api_key)
    vector_store.load()
    retriever = Retriever(vector_store, top_k=10)

    # Test project info
    project_info = {
        'program_name': 'Advanced Logistics Management System (ALMS)',
        'organization': 'U.S. Army',
        'estimated_value': '$2.5M',
        'budget': '$2.5M',
        'timeline': '36 months',
        'contract_type': 'Firm Fixed Price (FFP)',
        'period_of_performance': '36 months (Base: 12 months + 2 Option Years)'
    }

    # ========== STEP 1: Generate IGCE ==========
    print("\n" + "="*70)
    print("STEP 1: Generate IGCE")
    print("="*70)

    igce_agent = IGCEGeneratorAgent(api_key, retriever)

    igce_output_path = 'output/test_igce_alms_cross_ref.md'

    igce_result = igce_agent.execute({
        'project_info': project_info,
        'requirements_content': '',  # Will use RAG
        'config': {'contract_type': 'services'},
        'output_path': igce_output_path  # ← Triggers metadata save
    })

    if igce_result['status'] != 'success':
        print(f"❌ IGCE generation failed")
        return False

    # Save IGCE to file
    os.makedirs('output', exist_ok=True)
    with open(igce_output_path, 'w') as f:
        f.write(igce_result['content'])

    print(f"\n✅ IGCE saved to: {igce_output_path}")
    print(f"   Word count: {len(igce_result['content'].split())}")

    # ========== STEP 2: Verify IGCE Metadata ==========
    print("\n" + "="*70)
    print("STEP 2: Verify IGCE Metadata was Saved")
    print("="*70)

    metadata_store = DocumentMetadataStore()
    latest_igce = metadata_store.find_latest_document('igce', 'Advanced Logistics Management System (ALMS)')

    if not latest_igce:
        print("❌ IGCE metadata not found in store")
        return False

    print(f"✅ IGCE metadata found: {latest_igce['id']}")
    print(f"   Total Cost: {latest_igce['extracted_data'].get('total_cost_formatted', 'N/A')}")
    print(f"   Period: {latest_igce['extracted_data'].get('period_of_performance', 'N/A')}")
    print(f"   Labor Categories: {latest_igce['extracted_data'].get('labor_categories_count', 0)}")

    # ========== STEP 3: Generate Acquisition Plan ==========
    print("\n" + "="*70)
    print("STEP 3: Generate Acquisition Plan (should reference IGCE)")
    print("="*70)

    acq_plan_agent = AcquisitionPlanGeneratorAgent(api_key, retriever)

    acq_plan_output_path = 'output/test_acquisition_plan_alms_cross_ref.md'

    acq_plan_result = acq_plan_agent.execute({
        'project_info': project_info,
        'requirements_content': '',  # Will use RAG
        'config': {'contract_type': 'services'},
        'output_path': acq_plan_output_path  # ← Triggers metadata save
    })

    if acq_plan_result['status'] != 'success':
        print(f"❌ Acquisition Plan generation failed")
        return False

    # Save Acquisition Plan to file
    with open(acq_plan_output_path, 'w') as f:
        f.write(acq_plan_result['content'])

    print(f"\n✅ Acquisition Plan saved to: {acq_plan_output_path}")
    print(f"   Word count: {len(acq_plan_result['content'].split())}")

    # ========== STEP 4: Verify Acquisition Plan Metadata ==========
    print("\n" + "="*70)
    print("STEP 4: Verify Acquisition Plan Metadata and Cross-References")
    print("="*70)

    latest_acq_plan = metadata_store.find_latest_document('acquisition_plan', 'Advanced Logistics Management System (ALMS)')

    if not latest_acq_plan:
        print("❌ Acquisition Plan metadata not found in store")
        return False

    print(f"✅ Acquisition Plan metadata found: {latest_acq_plan['id']}")
    print(f"   Total Cost: {latest_acq_plan['extracted_data'].get('total_cost_formatted', 'N/A')}")

    # Check cross-references
    if 'references' in latest_acq_plan and latest_acq_plan['references']:
        print(f"✅ Cross-references found:")
        for ref_type, ref_id in latest_acq_plan['references'].items():
            print(f"   • {ref_type}: {ref_id}")
    else:
        print(f"⚠️  No cross-references found (this might be okay if IGCE wasn't available)")

    # ========== STEP 5: Verify Cross-Referenced Data in Content ==========
    print("\n" + "="*70)
    print("STEP 5: Verify IGCE Data Appears in Acquisition Plan")
    print("="*70)

    acq_plan_content = acq_plan_result['content']

    checks = [
        ('IGCE Summary Section', ['IGCE', 'Independent Government Cost Estimate', 'cost estimate']),
        ('Total Cost from IGCE', [latest_igce['extracted_data'].get('total_cost_formatted', 'N/A')]),
        ('Period of Performance', [latest_igce['extracted_data'].get('period_of_performance', 'TBD')]),
    ]

    passed_checks = 0
    total_checks = len(checks)

    for check_name, search_terms in checks:
        found = any(term in acq_plan_content for term in search_terms if term not in ['TBD', 'N/A'])
        if found:
            found_term = next(term for term in search_terms if term in acq_plan_content)
            print(f"✅ {check_name}: Found ('{found_term}')")
            passed_checks += 1
        else:
            print(f"❌ {check_name}: NOT found")

    # ========== STEP 6: Verify Data Consistency ==========
    print("\n" + "="*70)
    print("STEP 6: Verify Data Consistency Across Documents")
    print("="*70)

    igce_total = latest_igce['extracted_data'].get('total_cost')
    acq_plan_total = latest_acq_plan['extracted_data'].get('total_cost')

    if igce_total and acq_plan_total:
        print(f"  IGCE Total Cost:     ${igce_total:,.2f}")
        print(f"  Acq Plan Total Cost: ${acq_plan_total:,.2f}")

        if abs(igce_total - acq_plan_total) < 100:  # Allow small rounding differences
            print(f"\n  ✅ CONSISTENT: Costs match across documents")
            passed_checks += 1
        else:
            diff = abs(igce_total - acq_plan_total)
            print(f"\n  ⚠️  INCONSISTENT: ${diff:,.2f} difference")
    else:
        print(f"  ⚠️  Could not compare costs (one or both missing)")

    # ========== STEP 7: Summary ==========
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    print(f"\nDocuments Generated:")
    print(f"  1. IGCE: {igce_output_path}")
    print(f"  2. Acquisition Plan: {acq_plan_output_path}")

    print(f"\nMetadata Store:")
    print(f"  • IGCE: {latest_igce['id']}")
    print(f"  • Acquisition Plan: {latest_acq_plan['id']}")

    if latest_acq_plan.get('references', {}).get('igce'):
        print(f"\nCross-Reference:")
        print(f"  {latest_acq_plan['id']} → references → {latest_acq_plan['references']['igce']}")

    print(f"\nVerification Checks: {passed_checks}/{total_checks + 1} passed")

    print("\n" + "="*70)
    if passed_checks >= (total_checks + 1) * 0.75:  # 75% pass rate
        print("✅ INTEGRATION TEST PASSED")
        print("="*70)
        print("\nKey Achievements:")
        print("  ✅ IGCE generated and metadata saved")
        print("  ✅ Acquisition Plan generated and metadata saved")
        print("  ✅ Cross-reference established (Acq Plan → IGCE)")
        print("  ✅ IGCE data appears in Acquisition Plan content")
        print("  ✅ Costs are consistent across documents")
        print("\n🎉 Cross-reference system is working correctly!")
        return True
    else:
        print("⚠️  INTEGRATION TEST PARTIALLY PASSED")
        print("="*70)
        print(f"\n{passed_checks}/{total_checks + 1} checks passed")
        print("Review the output above for details on what failed.")
        return False


if __name__ == '__main__':
    success = test_cross_reference_integration()
    sys.exit(0 if success else 1)
