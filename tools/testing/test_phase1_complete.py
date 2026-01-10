#!/usr/bin/env python3
"""
Complete Phase 1 test suite
Validates RAG enhancements and TBD reductions
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def main():
    print("\n" + "="*70)
    print("PHASE 1 COMPLETE TEST SUITE")
    print("="*70)
    print("\nTesting 3 enhanced agents:")
    print("  1. IGCEGeneratorAgent")
    print("  2. EvaluationScorecardGeneratorAgent")
    print("  3. SourceSelectionPlanGeneratorAgent")

    try:
        # Setup
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print("\n❌ ERROR: ANTHROPIC_API_KEY not set")
            print("   Please set your API key:")
            print("   export ANTHROPIC_API_KEY='your-key-here'")
            return 1

        print("\n1. Initializing RAG system...")
        from rag.vector_store import VectorStore
        from rag.retriever import Retriever

        vector_store = VectorStore(api_key=api_key)
        vector_store.load()
        retriever = Retriever(vector_store, top_k=5)
        print(f"   ✓ RAG initialized with {len(vector_store.chunks)} chunks")

        results = []

        # Test 1: IGCE
        print("\n2. Testing IGCEGeneratorAgent...")
        from agents.igce_generator_agent import IGCEGeneratorAgent

        agent = IGCEGeneratorAgent(api_key=api_key, retriever=retriever)
        result = agent.execute({
            'project_info': {
                'program_name': 'Advanced Logistics Management System (ALMS)',
                'solicitation_number': 'W911SC-24-R-0001',
                'estimated_value': '$6.4M',
                'contract_type': 'Firm Fixed Price'
            },
            'config': {
                'classification': 'UNCLASSIFIED'
            }
        })

        # Count TBDs
        igce_tbds = result['content'].count('TBD')
        igce_pass = igce_tbds < 30
        results.append(('IGCE', 120, igce_tbds, 30, igce_pass))
        print(f"   TBDs: {igce_tbds} (target: <30) {'✅' if igce_pass else '⚠️'}")

        # Save output
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        with open(output_dir / 'test_igce_phase1.md', 'w') as f:
            f.write(result['content'])
        print(f"   ✓ Saved to: output/test_igce_phase1.md")

        # Test 2: Evaluation Scorecard
        print("\n3. Testing EvaluationScorecardGeneratorAgent...")
        from agents.evaluation_scorecard_generator_agent import EvaluationScorecardGeneratorAgent

        agent = EvaluationScorecardGeneratorAgent(api_key=api_key, retriever=retriever)
        result = agent.execute({
            'solicitation_info': {
                'program_name': 'Advanced Logistics Management System (ALMS)',
                'solicitation_number': 'W911SC-24-R-0001'
            },
            'section_m_content': 'Technical Approach, Management Approach, Past Performance, Cost/Price evaluation factors',
            'evaluation_factor': 'Technical Approach',
            'config': {
                'source_selection_method': 'Best Value Trade-Off',
                'offeror_name': 'Test Contractor Inc.',
                'classification': 'UNCLASSIFIED'
            }
        })

        scorecard_tbds = result['content'].count('TBD')
        scorecard_pass = scorecard_tbds < 10
        results.append(('Scorecard', 40, scorecard_tbds, 10, scorecard_pass))
        print(f"   TBDs: {scorecard_tbds} (target: <10) {'✅' if scorecard_pass else '⚠️'}")

        # Save output
        with open(output_dir / 'test_scorecard_phase1.md', 'w') as f:
            f.write(result['content'])
        print(f"   ✓ Saved to: output/test_scorecard_phase1.md")

        # Test 3: Source Selection Plan
        print("\n4. Testing SourceSelectionPlanGeneratorAgent...")
        from agents.source_selection_plan_generator_agent import SourceSelectionPlanGeneratorAgent

        agent = SourceSelectionPlanGeneratorAgent(api_key=api_key, retriever=retriever)
        result = agent.execute({
            'solicitation_info': {
                'program_name': 'Advanced Logistics Management System (ALMS)',
                'solicitation_number': 'W911SC-24-R-0001'
            },
            'config': {
                'source_selection_method': 'Best Value Trade-Off',
                'classification': 'UNCLASSIFIED'
            }
        })

        ssp_tbds = result['content'].count('TBD')
        ssp_pass = ssp_tbds < 8
        results.append(('SSP', 30, ssp_tbds, 8, ssp_pass))
        print(f"   TBDs: {ssp_tbds} (target: <8) {'✅' if ssp_pass else '⚠️'}")

        # Save output
        with open(output_dir / 'test_ssp_phase1.md', 'w') as f:
            f.write(result['content'])
        print(f"   ✓ Saved to: output/test_ssp_phase1.md")

        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)

        for name, before, after, target, passed in results:
            reduction = ((before - after) / before) * 100
            status = "✅ PASS" if passed else "⚠️  PARTIAL"
            print(f"\n{name}:")
            print(f"  Before: {before} TBDs")
            print(f"  After:  {after} TBDs")
            print(f"  Target: <{target} TBDs")
            print(f"  Reduction: {reduction:.1f}%")
            print(f"  Status: {status}")

        total_before = sum(r[1] for r in results)
        total_after = sum(r[2] for r in results)
        total_reduction = ((total_before - total_after) / total_before) * 100
        all_passed = all(r[4] for r in results)

        print(f"\nOVERALL:")
        print(f"  Total TBDs Before: {total_before}")
        print(f"  Total TBDs After:  {total_after}")
        print(f"  Total Reduction:   {total_reduction:.1f}%")
        print(f"  Target:            75% average")
        print(f"  Status:            {'✅ ALL PASS' if all_passed else '⚠️  PARTIAL PASS'}")

        print("\n" + "="*70)
        print("📋 NEXT STEPS:")
        print("  1. Review generated documents in output/ directory")
        print("  2. Run TBD analysis: python3 scripts/analyze_tbds.py")
        print("  3. Update PHASE_1_VALIDATION_SUMMARY.md with actual results")
        print("  4. Proceed to user acceptance testing")
        print("="*70)

        return 0 if all_passed else 1

    except ImportError as e:
        print(f"\n❌ IMPORT ERROR: {str(e)}")
        print("\n💡 POSSIBLE FIXES:")
        print("  1. NumPy compatibility: pip install 'numpy<2'")
        print("  2. Missing dependencies: pip install -r requirements.txt")
        print("  3. Check that RAG system is set up correctly")
        return 1

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
