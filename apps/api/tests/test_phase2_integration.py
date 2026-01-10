"""
Phase 2 Integration Tests

Tests the integration of GenerationCoordinator with agent router and phase detector.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path.parent))

from backend.services.generation_coordinator import GenerationCoordinator


def test_coordinator_initialization():
    """Test that coordinator initializes with specialized agents"""
    coordinator = GenerationCoordinator(
        api_key="test-key",
        use_specialized_agents=True
    )

    assert coordinator.agent_router is not None
    assert coordinator.phase_detector is not None
    assert coordinator.use_specialized_agents is True

    print("✅ Coordinator initialization: PASSED")


def test_phase_analysis():
    """Test phase analysis functionality"""
    coordinator = GenerationCoordinator(
        api_key="test-key",
        use_specialized_agents=True
    )

    # Test solicitation phase detection
    solicitation_docs = [
        "Section L - Instructions to Offerors",
        "Section M - Evaluation Factors",
        "Section B - Supplies/Services and Prices"
    ]

    analysis = coordinator.analyze_generation_plan(solicitation_docs)

    assert analysis["phase_detection_enabled"] is True
    assert analysis["primary_phase"] == "solicitation"
    assert analysis["confidence"] == 1.0  # All docs from same phase
    assert analysis["mixed_phases"] is False

    print("✅ Phase analysis (solicitation): PASSED")
    print(f"   Detected phase: {analysis['primary_phase']}")
    print(f"   Confidence: {analysis['confidence']}")


def test_mixed_phase_detection():
    """Test detection of mixed phases"""
    coordinator = GenerationCoordinator(
        api_key="test-key",
        use_specialized_agents=True
    )

    # Mix of pre-solicitation and solicitation
    mixed_docs = [
        "Market Research Report",  # pre-solicitation
        "Section L - Instructions to Offerors",  # solicitation
        "Section M - Evaluation Factors",  # solicitation
    ]

    analysis = coordinator.analyze_generation_plan(mixed_docs)

    assert analysis["phase_detection_enabled"] is True
    assert analysis["mixed_phases"] is True
    assert len(analysis["warnings"]) > 0
    assert analysis["primary_phase"] == "solicitation"  # 2 solicitation docs

    print("✅ Mixed phase detection: PASSED")
    print(f"   Mixed phases detected: {analysis['mixed_phases']}")
    print(f"   Warnings: {len(analysis['warnings'])}")
    print(f"   Primary phase: {analysis['primary_phase']} (confidence: {analysis['confidence']:.2f})")


def test_phase_recommendations():
    """Test that recommendations are generated"""
    coordinator = GenerationCoordinator(
        api_key="test-key",
        use_specialized_agents=True
    )

    # Incomplete solicitation package
    incomplete_docs = [
        "Section L - Instructions to Offerors",
        "Section M - Evaluation Factors"
    ]

    analysis = coordinator.analyze_generation_plan(incomplete_docs)

    assert analysis["phase_detection_enabled"] is True
    assert len(analysis["recommendations"]) > 0

    print("✅ Phase recommendations: PASSED")
    print(f"   Recommendations provided: {len(analysis['recommendations'])}")
    for rec in analysis["recommendations"][:3]:
        print(f"   - {rec}")


def test_completeness_validation():
    """Test phase completeness validation"""
    coordinator = GenerationCoordinator(
        api_key="test-key",
        use_specialized_agents=True
    )

    # Complete pre-solicitation package
    complete_presol = [
        "Market Research Report",
        "Acquisition Plan",
        "Performance Work Statement (PWS)",
        "Independent Government Cost Estimate (IGCE)"
    ]

    analysis = coordinator.analyze_generation_plan(complete_presol)

    assert analysis["phase_detection_enabled"] is True
    assert analysis["primary_phase"] == "pre_solicitation"
    assert analysis["validation"] is not None
    assert analysis["validation"]["is_complete"] is True
    assert analysis["validation"]["completeness_percentage"] == 100.0

    print("✅ Completeness validation: PASSED")
    print(f"   Phase: {analysis['primary_phase']}")
    print(f"   Complete: {analysis['validation']['is_complete']}")
    print(f"   Completeness: {analysis['validation']['completeness_percentage']:.0f}%")


def test_generic_mode():
    """Test coordinator with generic mode (no specialized agents)"""
    coordinator = GenerationCoordinator(
        api_key="test-key",
        use_specialized_agents=False
    )

    assert coordinator.agent_router is None
    assert coordinator.phase_detector is None

    analysis = coordinator.analyze_generation_plan(["Section L", "Section M"])

    assert analysis["phase_detection_enabled"] is False

    print("✅ Generic mode (no specialized agents): PASSED")


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("PHASE 2 INTEGRATION TESTS")
    print("="*70 + "\n")

    tests = [
        test_coordinator_initialization,
        test_phase_analysis,
        test_mixed_phase_detection,
        test_phase_recommendations,
        test_completeness_validation,
        test_generic_mode
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
            print()
        except AssertionError as e:
            print(f"❌ {test_func.__name__}: FAILED")
            print(f"   Error: {e}")
            print()
            failed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__}: ERROR")
            print(f"   Error: {e}")
            print()
            failed += 1

    print("="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
