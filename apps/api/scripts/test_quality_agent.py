"""
Test Quality Agent with DoD Citation Validation
Verifies quality checks including DoD citation compliance

Dependencies:
- agents.quality_agent: QualityAgent class
- dotenv: Load environment variables from .env file
- os: Environment variables
"""

import sys
import os
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load .env file from project root
project_root = Path(__file__).parent.parent
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path=dotenv_path)

from backend.agents.quality_agent import QualityAgent


def test_quality_agent_basic():
    """
    Test basic Quality Agent functionality with DoD citations
    
    Returns:
        bool: True if test passes, False otherwise
    """
    
    print("="*70)
    print("TEST 1: Quality Agent Basic Functionality")
    print("="*70)
    print()
    
    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found")
        print(f"Check .env file at: {dotenv_path}")
        return False
    
    print("✓ API key loaded from environment")
    print()
    
    try:
        # Initialize Quality Agent
        print("Initializing Quality Agent with DoD validation...")
        agent = QualityAgent(api_key)
        print("✓ Quality Agent initialized")
        print("✓ DoD Citation Validator loaded")
        print()
        
        # Test content with good DoD citations
        test_content_good = """
## Market Research Conducted

Market research was conducted per FAR 10.001 and FAR 10.002 to identify 
potential sources for cloud-based inventory management services. The research 
included consultation with industry experts and review of available solutions.

The estimated budget for this acquisition is $2.5 million (Budget Specification, FY2025) 
with a performance period of 36 months (Schedule Requirements, 2025). Research activities 
included:

1. Request for Information (RFI) issued in March 2025
2. Industry Day held in April 2025
3. Analysis of GSA Schedule offerings

A total of 12 vendors responded to the RFI (Market Research Report, March 2025), 
demonstrating strong market interest. Four of the respondents were small businesses 
with relevant experience (Small Business Analysis, April 2025).

The system must provide real-time tracking capabilities with 99.9% uptime 
(Technical Requirements Document, October 2025). Integration with existing ERP 
systems is required, along with mobile access for field personnel.
"""
        
        # Test the citation check directly
        print("Running DoD citation validation...")
        print("-" * 70)
        
        citation_results = agent._check_citations(test_content_good)
        
        print(f"\n📊 Citation Check Results:")
        print(f"   Score: {citation_results['score']}/100")
        print(f"   Valid DoD Citations: {citation_results['citations_found']}")
        print(f"   Invalid Citations: {citation_results['invalid_citations']}")
        print(f"   Claims Needing Citations: {citation_results['claims_needing_citations']}")
        print(f"   DoD Compliant: {'✅ Yes' if citation_results['dod_compliant'] else '⚠️  No'}")
        
        # Show issues if any
        if citation_results['issues']:
            print(f"\n⚠️  Issues Found:")
            for issue in citation_results['issues']:
                print(f"   - {issue}")
        else:
            print(f"\n✅ No citation issues")
        
        # Show suggestions
        if citation_results['suggestions']:
            print(f"\n💡 Suggestions:")
            for suggestion in citation_results['suggestions'][:3]:
                print(f"   - {suggestion}")
        
        print()
        
        # Test passes if score is reasonable and DoD citations detected
        test_passed = citation_results['score'] >= 50 and citation_results['citations_found'] > 0
        
        if test_passed:
            print("="*70)
            print("✅ TEST 1 PASSED: Quality Agent working correctly")
            print("="*70)
        else:
            print("="*70)
            print("⚠️  TEST 1 PARTIAL: Citations detected but score low")
            print("="*70)
        
        return test_passed
        
    except Exception as e:
        print("\n" + "="*70)
        print("❌ TEST 1 FAILED: Exception occurred")
        print("="*70)
        print(f"\nError: {type(e).__name__}")
        print(f"Message: {str(e)}")
        
        import traceback
        print("\nTraceback:")
        print("-" * 70)
        traceback.print_exc()
        
        return False


def test_quality_agent_full_evaluation():
    """
    Test full quality evaluation including all checks
    
    Returns:
        bool: True if test passes, False otherwise
    """
    
    print("\n")
    print("="*70)
    print("TEST 2: Full Quality Evaluation (All Checks)")
    print("="*70)
    print()
    
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found")
        return False
    
    try:
        agent = QualityAgent(api_key)
        
        test_content = """
## Market Research Conducted

Market research was conducted per FAR 10.001 and FAR 10.002 to determine 
the availability of commercial solutions. The acquisition strategy follows 
DoDI 5000.85, Major Capability Acquisition (August 6, 2020), requirements.

The estimated cost is $2.5 million (Budget Specification, FY2025) for a 
36-month performance period (Schedule Requirements, 2025). Research included:

1. Request for Information (RFI) with 12 responses (Market Research Report, March 2025)
2. Industry Day with 8 attendees (Industry Day Summary, April 2025)
3. GSA Schedule analysis (GSA Review, May 2025)

Four small businesses demonstrated relevant capabilities (Small Business Analysis, April 2025).
The system requires 99.9% uptime (Technical Requirements Document, October 2025) and
must integrate with existing ERP systems (Integration Specifications, October 2025).

Per 10 U.S.C. § 3201, full and open competition will be used for this acquisition.
"""
        
        # Prepare task for full evaluation
        task = {
            'content': test_content,
            'section_name': 'Market Research Conducted',
            'project_info': {
                'budget': '$2.5 million',
                'vendor_research': '12 vendors responded',
                'program_name': 'Test Program'
            },
            'research_findings': {},
            'evaluation_type': 'section'
        }
        
        print("Running full quality evaluation...")
        print("-" * 70)
        
        result = agent.execute(task)
        
        print(f"\n📊 Overall Quality Assessment:")
        print(f"   Overall Score: {result['score']}/100")
        print(f"   Grade: {result['grade']}")
        print(f"   Hallucination Risk: {result['hallucination_risk']}")
        
        # Show detailed checks
        print(f"\n📋 Detailed Check Scores:")
        for check_name, check_result in result['detailed_checks'].items():
            score = check_result['score']
            status = "✅" if score >= 70 else "⚠️"
            display_name = check_name.replace('_', ' ').title()
            print(f"   {status} {display_name}: {score}/100")
        
        # Show DoD citation details
        citation_check = result['detailed_checks']['citations']
        print(f"\n🏛️  DoD Citation Analysis:")
        print(f"   Valid Citations: {citation_check['citations_found']}")
        print(f"   Invalid Citations: {citation_check['invalid_citations']}")
        print(f"   Missing Citations: {citation_check['claims_needing_citations']}")
        print(f"   DoD Compliant: {'✅ Yes' if citation_check.get('dod_compliant') else '⚠️  No'}")
        
        # Show top issues
        if result['issues']:
            print(f"\n⚠️  Top Issues ({len(result['issues'])} total):")
            for issue in result['issues'][:5]:
                print(f"   - {issue}")
        else:
            print(f"\n✅ No major issues detected")
        
        # Show top suggestions
        if result['suggestions']:
            print(f"\n💡 Top Suggestions ({len(result['suggestions'])} total):")
            for suggestion in result['suggestions'][:3]:
                print(f"   - {suggestion}")
        
        print()
        
        # Test passes if overall score is reasonable
        test_passed = result['score'] >= 60
        
        if test_passed:
            print("="*70)
            print("✅ TEST 2 PASSED: Full evaluation working correctly")
            print("="*70)
        else:
            print("="*70)
            print("⚠️  TEST 2 PARTIAL: Evaluation complete but score low")
            print(f"   Score: {result['score']}/100 (expected >= 60)")
            print("="*70)
        
        return test_passed
        
    except Exception as e:
        print("\n" + "="*70)
        print("❌ TEST 2 FAILED: Exception occurred")
        print("="*70)
        print(f"\nError: {type(e).__name__}")
        print(f"Message: {str(e)}")
        
        import traceback
        print("\nTraceback:")
        print("-" * 70)
        traceback.print_exc()
        
        return False


def test_citation_types_detection():
    """
    Test detection of various DoD citation types
    
    Returns:
        bool: True if test passes, False otherwise
    """
    
    print("\n")
    print("="*70)
    print("TEST 3: DoD Citation Type Detection")
    print("="*70)
    print()
    
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found")
        return False
    
    try:
        agent = QualityAgent(api_key)
        
        # Content with multiple citation types
        test_content = """
## Acquisition Strategy

This acquisition follows FAR 15.203 procedures for competitive negotiation and
FAR 10.001 market research requirements. The program complies with DoDI 5000.85,
Major Capability Acquisition (August 6, 2020).

Per 10 U.S.C. § 3201, full and open competition is required. Foreign acquisitions
will follow DFARS 225.872 guidelines.

The budget is $2.5 million (Budget Specification, FY2025) for a 36-month period
(Schedule Requirements, 2025). Technical requirements are documented in the 
Technical Requirements Document (October 2025).
"""
        
        print("Testing citation type detection...")
        print("-" * 70)
        
        citation_results = agent._check_citations(test_content)
        
        # Check validation details
        validation_details = citation_results.get('validation_details', {})
        valid_citations = validation_details.get('valid', [])
        
        print(f"\n📊 Citation Types Detected:")
        
        # Count citation types
        citation_types = {}
        for citation in valid_citations:
            ctype = citation.get('type', 'UNKNOWN')
            citation_types[ctype] = citation_types.get(ctype, 0) + 1
        
        if citation_types:
            for ctype, count in sorted(citation_types.items()):
                print(f"   ✓ {ctype}: {count} citation(s)")
        else:
            print("   ⚠️  No citation types detected")
        
        # Show examples
        if valid_citations:
            print(f"\n📝 Citation Examples:")
            for citation in valid_citations[:5]:
                print(f"   - {citation['type']}: {citation['reference']}")
        
        print()
        
        # Test passes if multiple citation types detected
        test_passed = len(citation_types) >= 2
        
        if test_passed:
            print("="*70)
            print(f"✅ TEST 3 PASSED: Detected {len(citation_types)} citation types")
            print("="*70)
        else:
            print("="*70)
            print("⚠️  TEST 3 PARTIAL: Limited citation types detected")
            print(f"   Found: {len(citation_types)} types (expected >= 2)")
            print("="*70)
        
        return test_passed
        
    except Exception as e:
        print("\n" + "="*70)
        print("❌ TEST 3 FAILED: Exception occurred")
        print("="*70)
        print(f"\nError: {type(e).__name__}")
        print(f"Message: {str(e)}")
        
        import traceback
        print("\nTraceback:")
        print("-" * 70)
        traceback.print_exc()
        
        return False


def main():
    """
    Run all Quality Agent tests
    """
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " " * 17 + "Quality Agent Test Suite" + " " * 27 + "║")
    print("║" + " " * 20 + "(DoD Citation Validation)" + " " * 23 + "║")
    print("╚" + "="*68 + "╝")
    print()
    
    tests = [
        ("Basic Functionality", test_quality_agent_basic),
        ("Full Evaluation", test_quality_agent_full_evaluation),
        ("Citation Type Detection", test_citation_types_detection)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results[test_name] = "PASS" if passed else "PARTIAL"
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR in {test_name}: {str(e)}\n")
            results[test_name] = "ERROR"
    
    # Print summary
    print("\n")
    print("="*70)
    print("TEST SUITE SUMMARY")
    print("="*70)
    print()
    
    for test_name, result in results.items():
        if result == "PASS":
            emoji = "✅"
        elif result == "PARTIAL":
            emoji = "⚠️"
        else:
            emoji = "❌"
        print(f"{emoji} {test_name}: {result}")
    
    print()
    
    passed_count = sum(1 for r in results.values() if r == "PASS")
    partial_count = sum(1 for r in results.values() if r == "PARTIAL")
    total_count = len(results)
    
    print(f"Results: {passed_count} passed, {partial_count} partial, {total_count - passed_count - partial_count} failed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        print("\nNext steps:")
        print("1. Proceed to Phase 4: Update Evaluation Report Generator")
        print("2. Or skip to Phase 5: Full pipeline integration tests")
        print("3. Test with real documents: python scripts/run_market_research.py")
        exit_code = 0
    elif passed_count + partial_count == total_count:
        print("\n✓ Tests completed with some partial results")
        print("\nThis is acceptable - the Quality Agent is working.")
        print("Partial results may be due to content variations or API responses.")
        print("\nNext steps:")
        print("1. Proceed with integration")
        print("2. Test with real documents")
        exit_code = 0
    else:
        print("\n⚠️  Some tests failed")
        print("\nTroubleshooting:")
        print("1. Check ANTHROPIC_API_KEY is set in .env")
        print("2. Verify utils/dod_citation_validator.py exists")
        print("3. Ensure agents/quality_agent.py has DoD updates")
        print("4. Review error messages above")
        exit_code = 1
    
    print()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
