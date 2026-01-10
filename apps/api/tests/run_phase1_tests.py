"""
Phase 1 Test Runner

Executes all Phase 1 unit tests and generates comprehensive report.
Tests the core infrastructure: AgentRouter and PhaseDetector.
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


def run_phase1_tests():
    """Run all Phase 1 tests and report results"""

    print("\n" + "="*80)
    print(" PHASE 1 INFRASTRUCTURE TESTS")
    print("="*80)
    print("\nTesting:")
    print("  1. AgentRouter (41-agent mapping)")
    print("  2. PhaseDetector (phase analysis)")
    print("\n" + "="*80)

    # Run agent router tests
    print("\n>>> RUNNING AGENT ROUTER TESTS...")
    print("-"*80)
    result1 = pytest.main([
        "tests/services/test_agent_router.py",
        "-v",
        "--tb=short",
        "--color=yes"
    ])

    # Run phase detector tests
    print("\n" + "="*80)
    print("\n>>> RUNNING PHASE DETECTOR TESTS...")
    print("-"*80)
    result2 = pytest.main([
        "tests/services/test_phase_detector.py",
        "-v",
        "--tb=short",
        "--color=yes"
    ])

    # Generate summary report
    print("\n" + "="*80)
    print(" PHASE 1 TEST RESULTS SUMMARY")
    print("="*80)

    router_status = "✅ PASSED" if result1 == 0 else "❌ FAILED"
    detector_status = "✅ PASSED" if result2 == 0 else "❌ FAILED"

    print(f"\nAgent Router Tests:     {router_status}")
    print(f"Phase Detector Tests:   {detector_status}")

    overall_status = "✅ ALL TESTS PASSED" if (result1 == 0 and result2 == 0) else "❌ SOME TESTS FAILED"
    print(f"\nOverall Status:         {overall_status}")

    print("\n" + "="*80)

    if result1 == 0 and result2 == 0:
        print("\n✅ Phase 1 infrastructure is validated and ready!")
        print("   You can proceed to Phase 2: API Layer Integration")
    else:
        print("\n⚠️  Please review and fix failing tests before proceeding to Phase 2")

    print("="*80 + "\n")

    # Return non-zero exit code if any tests failed
    return max(result1, result2)


if __name__ == "__main__":
    exit_code = run_phase1_tests()
    sys.exit(exit_code)
