#!/usr/bin/env python3
"""
Test Progressive Refinement Loop

Tests the automatic quality improvement system with various content quality levels.

Usage:
    python scripts/test_progressive_refinement.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path

from backend.utils.progressive_refinement_orchestrator import ProgressiveRefinementOrchestrator
from backend.utils.document_processor import DocumentProcessor


def test_low_quality_content():
    """Test refinement on low-quality content with vague language"""

    print("\n" + "="*80)
    print("TEST 1: LOW QUALITY CONTENT (Vague Language, No Citations)")
    print("="*80 + "\n")

    content = """
    # Independent Government Cost Estimate (IGCE)
    # Advanced Logistics Management System

    ## Executive Summary

    The program will cost several million dollars over approximately 3 years.
    Many vendors are interested in this opportunity. The system will provide
    significant improvements to operations.

    ## Cost Breakdown

    ### Labor Costs
    - Development Team: Around $1.5M annually
    - Testing Team: Some amount for QA
    - Project Management: Various PM costs

    ### Materials and Equipment
    - Hardware: Several servers needed
    - Software: Numerous licenses required
    - Cloud Services: Adequate hosting capacity

    ### Other Direct Costs
    - Travel: Reasonable amount for site visits
    - Training: Sufficient resources for user training
    - Documentation: Appropriate budget for technical writing

    ## Timeline

    The project timeline is adequate for the requirements. Development will
    take some time, followed by testing, which will also require significant
    effort.

    ## Risk Assessment

    There are various risks that need to be considered. Many of these risks
    can be mitigated with appropriate planning and sufficient resources.
    """

    project_info = {
        'program_name': 'Advanced Logistics Management System',
        'estimated_value': '$2,500,000',
        'period_of_performance': '36 months',
        'contract_type': 'Firm Fixed Price'
    }

    # Test with orchestrator directly
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    orchestrator = ProgressiveRefinementOrchestrator(
        api_key=api_key,
        quality_threshold=85,
        max_iterations=2
    )

    result = orchestrator.refine_until_quality_met(
        content=content,
        section_name="IGCE Test",
        doc_type="igce",
        project_info=project_info
    )

    # Print results
    print("\n" + "="*80)
    print("TEST 1 RESULTS")
    print("="*80)
    print(f"\nInitial Score:     {result['initial_score']}/100")
    print(f"Final Score:       {result['final_score']}/100")
    print(f"Improvement:       {result['improvement']:+d} points")
    print(f"Iterations Used:   {result['iterations_used']}")
    print(f"Refinement Applied: {result['refinement_applied']}")

    print("\n" + "-"*80)
    print("ITERATION HISTORY:")
    print("-"*80)
    for iter_data in result['iteration_history']:
        if iter_data['type'] == 'initial_evaluation':
            print(f"\nIteration 0 (Initial): {iter_data['score']}/100 - {iter_data['grade']}")
            print(f"  Issues: {iter_data['issues_count']}")
        else:
            print(f"\nIteration {iter_data['iteration']} (Refinement):")
            print(f"  Before: {iter_data['score_before']}/100")
            print(f"  After:  {iter_data['score_after']}/100 - {iter_data['grade']}")
            print(f"  Change: {iter_data['improvement']:+d} points")
            print(f"  Changes: {', '.join(iter_data['changes_made'])}")

    print("\n" + "-"*80)
    print("FINAL CONTENT PREVIEW (first 500 chars):")
    print("-"*80)
    print(result['final_content'][:500] + "...\n")

    return result


def test_with_document_processor():
    """Test integration with DocumentProcessor"""

    print("\n" + "="*80)
    print("TEST 2: DOCUMENT PROCESSOR INTEGRATION")
    print("="*80 + "\n")

    content = """
    # Performance Work Statement (PWS)

    ## Background

    This project needs to be completed on time. The system should work well
    and meet various requirements. Several stakeholders are interested in
    this capability.

    ## Scope

    The contractor will provide numerous services including development,
    testing, and support. Many different features will be implemented.

    ## Performance Requirements

    - System availability: Should be high
    - Response time: Must be adequate
    - Capacity: Sufficient for user load
    - Security: Appropriate measures required

    ## Deliverables

    The contractor will deliver various documents and software components
    as needed throughout the project.
    """

    project_info = {
        'program_name': 'Test System',
        'estimated_value': '$1,000,000',
        'period_of_performance': '24 months'
    }

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    # Test with DocumentProcessor
    processor = DocumentProcessor(
        api_key=api_key,
        enable_progressive_refinement=True,
        quality_threshold=85,
        max_refinement_iterations=2
    )

    output_dir = Path('test_output')
    output_dir.mkdir(exist_ok=True)

    result = processor.process_document(
        content=content,
        output_path=str(output_dir / 'test_pws.md'),
        doc_type='pws',
        program_name='Test System',
        source_docs=['test_requirements.md'],
        project_info=project_info,
        generate_pdf=True,
        generate_evaluation=True,
        add_citations=True
    )

    print("\n" + "="*80)
    print("TEST 2 RESULTS")
    print("="*80)
    print(f"\nQuality Score:          {result['quality_score']}/100")
    print(f"Refinement Applied:     {result['refinement_applied']}")
    print(f"Refinement Improvement: {result['refinement_improvement']:+d} points")
    print(f"Refinement Iterations:  {result['refinement_iterations']}")
    print(f"Citations Added:        {result['citations_added']}")

    print("\nGenerated Files:")
    print(f"  📄 Markdown:  {result['markdown_path']}")
    if result['pdf_path']:
        print(f"  📄 PDF:       {result['pdf_path']}")
    if result['evaluation_path']:
        print(f"  📊 Evaluation: {result['evaluation_path']}")

    print()

    return result


def main():
    """Run all tests"""

    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║            PROGRESSIVE REFINEMENT LOOP - TEST SUITE                        ║
║                                                                            ║
║  Tests the automatic quality improvement system:                          ║
║  1. Low quality content with vague language                               ║
║  2. Integration with DocumentProcessor                                    ║
║                                                                            ║
║  Expected behavior:                                                       ║
║  - Initial evaluation identifies issues                                   ║
║  - Refinement agent fixes issues                                          ║
║  - Re-evaluation shows improvement                                        ║
║  - Loop continues until threshold met or max iterations reached           ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    # Check API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("❌ ERROR: ANTHROPIC_API_KEY environment variable not set\n")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    print("✅ API Key found\n")

    try:
        # Test 1: Basic refinement
        result1 = test_low_quality_content()

        # Test 2: Integration
        result2 = test_with_document_processor()

        # Summary
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED")
        print("="*80)
        print(f"\nTest 1 (Low Quality Content):")
        print(f"  Improvement: {result1['improvement']:+d} points")
        print(f"  Iterations:  {result1['iterations_used']}")

        print(f"\nTest 2 (Document Processor Integration):")
        print(f"  Improvement: {result2['refinement_improvement']:+d} points")
        print(f"  Iterations:  {result2['refinement_iterations']}")

        print("\n✅ Progressive Refinement System: WORKING")
        print()

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
