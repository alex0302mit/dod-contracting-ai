#!/usr/bin/env python3
"""
Quick validation script for Phase 1 enhanced agents
Checks code structure without initialization
"""

import sys
from pathlib import Path
import inspect

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def check_agent_structure(agent_class, agent_name, expected_methods):
    """Check if agent has expected RAG methods"""
    print(f"\n{'='*70}")
    print(f"VALIDATING: {agent_name}")
    print('='*70)

    results = []

    # Check for retriever parameter in __init__
    init_sig = inspect.signature(agent_class.__init__)
    has_retriever = 'retriever' in init_sig.parameters
    print(f"  {'✅' if has_retriever else '❌'} Retriever parameter in __init__: {has_retriever}")
    results.append(has_retriever)

    # Check for RAG context building method
    for method_name in expected_methods:
        has_method = hasattr(agent_class, method_name)
        print(f"  {'✅' if has_method else '❌'} Method {method_name}: {has_method}")
        results.append(has_method)

    # Check method count
    all_methods = [m for m in dir(agent_class) if not m.startswith('__')]
    rag_methods = [m for m in all_methods if '_rag' in m.lower() or 'extract' in m.lower()]
    print(f"  ℹ️  Total RAG-related methods: {len(rag_methods)}")

    return all(results), len(rag_methods)

def main():
    """Run quick validation"""
    print("\n" + "="*70)
    print("PHASE 1 QUICK VALIDATION")
    print("="*70)

    try:
        # Import agents
        from agents.igce_generator_agent import IGCEGeneratorAgent
        from agents.evaluation_scorecard_generator_agent import EvaluationScorecardGeneratorAgent
        from agents.source_selection_plan_generator_agent import SourceSelectionPlanGeneratorAgent

        # Test configurations
        tests = [
            (IGCEGeneratorAgent, 'IGCEGeneratorAgent', ['_build_rag_context']),
            (EvaluationScorecardGeneratorAgent, 'EvaluationScorecardGeneratorAgent', ['_build_evaluation_context']),
            (SourceSelectionPlanGeneratorAgent, 'SourceSelectionPlanGeneratorAgent', ['_build_organizational_context'])
        ]

        results = []
        total_rag_methods = 0

        for agent_class, agent_name, expected_methods in tests:
            passed, rag_method_count = check_agent_structure(agent_class, agent_name, expected_methods)
            results.append((agent_name, passed))
            total_rag_methods += rag_method_count

        # Summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print('='*70)

        passed_count = sum(1 for _, passed in results if passed)
        total_count = len(results)

        print(f"\n  Agents validated:          {passed_count}/{total_count}")
        print(f"  Total RAG methods found:   {total_rag_methods}")

        for agent_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"    {status}: {agent_name}")

        if passed_count == total_count:
            print(f"\n  ✅ ALL {total_count} AGENTS VALIDATED SUCCESSFULLY")
            print(f"\n  Expected enhancements:")
            print(f"    • IGCEGeneratorAgent: 5 RAG queries, 5 extraction methods")
            print(f"    • EvaluationScorecardGeneratorAgent: 3 RAG queries, 3 extraction methods")
            print(f"    • SourceSelectionPlanGeneratorAgent: 4 RAG queries, 4 extraction methods")
            print(f"\n  Phase 1 Status: ✅ COMPLETE")
        else:
            print(f"\n  ⚠️  VALIDATION INCOMPLETE: {total_count - passed_count} agent(s) failed")

        print('='*70)

        return 0 if passed_count == total_count else 1

    except ImportError as e:
        print(f"\n❌ IMPORT ERROR: {str(e)}")
        print("  Make sure all Phase 1 agents are in the agents/ directory")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
