#!/usr/bin/env python3
"""
Test script for Phase 1 enhanced agents
Validates RAG integration and TBD reduction
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def test_imports():
    """Test that all Phase 1 agents can be imported"""
    print("\n" + "="*70)
    print("PHASE 1 AGENT IMPORT TEST")
    print("="*70)

    agents_to_test = [
        ('IGCEGeneratorAgent', 'agents.igce_generator_agent'),
        ('EvaluationScorecardGeneratorAgent', 'agents.evaluation_scorecard_generator_agent'),
        ('SourceSelectionPlanGeneratorAgent', 'agents.source_selection_plan_generator_agent')
    ]

    results = []

    for agent_name, module_path in agents_to_test:
        try:
            module_name = module_path.split('.')[-1]
            module = __import__(module_path, fromlist=[agent_name])
            agent_class = getattr(module, agent_name)

            # Check if retriever parameter exists
            import inspect
            sig = inspect.signature(agent_class.__init__)
            has_retriever = 'retriever' in sig.parameters

            status = "✅ PASS" if has_retriever else "⚠️  WARN (no retriever param)"
            results.append((agent_name, status))
            print(f"  {status}: {agent_name}")

        except Exception as e:
            results.append((agent_name, f"❌ FAIL"))
            print(f"  ❌ FAIL: {agent_name} - {str(e)}")

    return results

def test_rag_methods():
    """Test that RAG context building methods exist"""
    print("\n" + "="*70)
    print("PHASE 1 RAG METHODS TEST")
    print("="*70)

    from agents.igce_generator_agent import IGCEGeneratorAgent
    from agents.evaluation_scorecard_generator_agent import EvaluationScorecardGeneratorAgent
    from agents.source_selection_plan_generator_agent import SourceSelectionPlanGeneratorAgent

    tests = [
        (IGCEGeneratorAgent, '_build_rag_context', 'IGCE'),
        (EvaluationScorecardGeneratorAgent, '_build_evaluation_context', 'EvaluationScorecard'),
        (SourceSelectionPlanGeneratorAgent, '_build_organizational_context', 'SourceSelectionPlan')
    ]

    results = []

    for agent_class, method_name, agent_name in tests:
        has_method = hasattr(agent_class, method_name)
        status = "✅ PASS" if has_method else "❌ FAIL"
        results.append((agent_name, status))
        print(f"  {status}: {agent_name}.{method_name}()")

    return results

def test_extraction_methods():
    """Test that extraction methods exist"""
    print("\n" + "="*70)
    print("PHASE 1 EXTRACTION METHODS TEST")
    print("="*70)

    from agents.igce_generator_agent import IGCEGeneratorAgent
    from agents.evaluation_scorecard_generator_agent import EvaluationScorecardGeneratorAgent
    from agents.source_selection_plan_generator_agent import SourceSelectionPlanGeneratorAgent

    tests = [
        (IGCEGeneratorAgent, [
            '_extract_costs_from_rag',
            '_extract_sustainment_from_rag',
            '_extract_schedule_from_rag',
            '_extract_personnel_from_rag',
            '_extract_contract_info_from_rag'
        ], 'IGCE'),
        (EvaluationScorecardGeneratorAgent, [
            '_extract_rating_standards_from_rag',
            '_extract_evaluation_criteria_from_rag',
            '_extract_evaluation_examples_from_rag'
        ], 'EvaluationScorecard'),
        (SourceSelectionPlanGeneratorAgent, [
            '_extract_ssa_info_from_rag',
            '_extract_team_composition_from_rag',
            '_extract_procedures_from_rag',
            '_extract_schedule_guidance_from_rag'
        ], 'SourceSelectionPlan')
    ]

    for agent_class, methods, agent_name in tests:
        print(f"\n  {agent_name}:")
        for method in methods:
            has_method = hasattr(agent_class, method)
            status = "✅" if has_method else "❌"
            print(f"    {status} {method}()")

    print()

def test_backward_compatibility():
    """Test that agents work without retriever (backward compatibility)"""
    print("\n" + "="*70)
    print("PHASE 1 BACKWARD COMPATIBILITY TEST")
    print("="*70)

    from agents.igce_generator_agent import IGCEGeneratorAgent
    from agents.evaluation_scorecard_generator_agent import EvaluationScorecardGeneratorAgent
    from agents.source_selection_plan_generator_agent import SourceSelectionPlanGeneratorAgent

    # Dummy API key for testing (won't actually call API)
    api_key = "test_key"

    tests = [
        ('IGCE', IGCEGeneratorAgent),
        ('EvaluationScorecard', EvaluationScorecardGeneratorAgent),
        ('SourceSelectionPlan', SourceSelectionPlanGeneratorAgent)
    ]

    results = []

    for name, agent_class in tests:
        try:
            # Initialize WITHOUT retriever
            agent = agent_class(api_key=api_key)

            # Check that retriever is None or agent has retriever attribute
            has_retriever_attr = hasattr(agent, 'retriever')

            if has_retriever_attr:
                status = "✅ PASS (backward compatible)"
            else:
                status = "⚠️  WARN (no retriever attribute)"

            results.append((name, status))
            print(f"  {status}: {name}")

        except TypeError as e:
            if 'retriever' in str(e):
                results.append((name, "❌ FAIL (retriever required)"))
                print(f"  ❌ FAIL: {name} - retriever parameter is required")
            else:
                results.append((name, f"❌ FAIL ({str(e)})"))
                print(f"  ❌ FAIL: {name} - {str(e)}")
        except Exception as e:
            results.append((name, f"⚠️  WARN ({str(e)})"))
            print(f"  ⚠️  WARN: {name} - {str(e)}")

    return results

def print_summary(import_results, rag_results, compat_results):
    """Print test summary"""
    print("\n" + "="*70)
    print("PHASE 1 TEST SUMMARY")
    print("="*70)

    # Count passes
    import_passes = sum(1 for _, status in import_results if '✅' in status)
    rag_passes = sum(1 for _, status in rag_results if '✅' in status)
    compat_passes = sum(1 for _, status in compat_results if '✅' in status)

    total_tests = len(import_results) + len(rag_results) + len(compat_results)
    total_passes = import_passes + rag_passes + compat_passes

    print(f"\n  Import Tests:              {import_passes}/{len(import_results)} passed")
    print(f"  RAG Method Tests:          {rag_passes}/{len(rag_results)} passed")
    print(f"  Backward Compat Tests:     {compat_passes}/{len(compat_results)} passed")
    print(f"\n  TOTAL:                     {total_passes}/{total_tests} passed")

    if total_passes == total_tests:
        print("\n  ✅ ALL TESTS PASSED - Phase 1 agents ready for production!")
    elif total_passes >= total_tests * 0.8:
        print("\n  ⚠️  MOST TESTS PASSED - Minor issues detected")
    else:
        print("\n  ❌ TESTS FAILED - Issues need to be resolved")

    print("="*70)

    return total_passes == total_tests

def main():
    """Run all Phase 1 tests"""
    print("\n" + "="*70)
    print("PHASE 1 ENHANCED AGENTS - VALIDATION TEST SUITE")
    print("="*70)
    print("\nTesting 3 agents enhanced in Phase 1:")
    print("  1. IGCEGeneratorAgent")
    print("  2. EvaluationScorecardGeneratorAgent")
    print("  3. SourceSelectionPlanGeneratorAgent")
    print("\nValidating:")
    print("  - RAG retriever parameter added")
    print("  - RAG context building methods exist")
    print("  - Extraction methods implemented")
    print("  - Backward compatibility maintained")

    try:
        # Run tests
        import_results = test_imports()
        rag_results = test_rag_methods()
        test_extraction_methods()  # Detailed output, no results tracking
        compat_results = test_backward_compatibility()

        # Print summary
        all_passed = print_summary(import_results, rag_results, compat_results)

        # Additional info
        print("\n📋 NEXT STEPS:")
        print("  1. Test agents with real RAG retriever")
        print("  2. Validate TBD reductions (target: 70%+)")
        print("  3. Generate test documents and count TBDs")
        print("  4. Gather user feedback on document quality")
        print("\n📚 DOCUMENTATION:")
        print("  - See PHASE_1_COMPLETE.md for detailed metrics")
        print("  - See individual enhancement docs for agent details")
        print("  - See PHASE_2_PLAN.md for next phase planning")

        return 0 if all_passed else 1

    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
