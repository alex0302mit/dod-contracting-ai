"""
Test DoD Citation Injector
Quick test to verify citation injection with DoD standards

Dependencies:
- core.add_citations: CitationInjector class
- os: Environment variables
- re: Pattern matching
- dotenv: Load environment variables from .env file
"""

import sys
import os
import re
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load .env file from project root
project_root = Path(__file__).parent.parent
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path=dotenv_path)

from backend.core.add_citations import CitationInjector


def test_dod_citation_injection():
    """
    Test citation injection with DoD standards
    
    Returns:
        bool: True if test passes, False otherwise
        
    Comments:
        Tests end-to-end citation injection flow with sample content
        Validates citation patterns match DoD standards
        Loads API key from .env file in project root
    """
    
    print("="*70)
    print("TEST: DoD Citation Injector")
    print("="*70)
    print()
    
    # Get API key from environment (loaded from .env)
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found")
        print()
        print("Troubleshooting:")
        print(f"1. Check that .env file exists at: {dotenv_path}")
        print("2. Verify .env contains: ANTHROPIC_API_KEY=your-key-here")
        print("3. Or set manually: export ANTHROPIC_API_KEY='your-key-here'")
        return False
    
    print(f"✓ API key loaded from environment")
    print(f"✓ .env file location: {dotenv_path}")
    print()
    
    # Sample content without citations
    test_content = """
# Market Research Report

## Market Research Conducted

Market research was conducted to identify potential sources for cloud-based 
inventory management services. The research included consultation with industry 
experts and review of available solutions.

The estimated budget for this acquisition is $2.5 million with a performance 
period of 36 months. Research activities included:

1. Request for Information (RFI) issued in March 2025
2. Industry Day held in April 2025
3. Analysis of GSA Schedule offerings

A total of 12 vendors responded to the RFI, demonstrating strong market interest.
Four of the respondents were small businesses with relevant experience in 
providing similar services to government agencies.

## Technical Requirements

The system must provide real-time tracking capabilities with 99.9% uptime.
Integration with existing ERP systems is required, along with mobile access
for field personnel. The solution must be operational by Q2 FY2026.

## Conclusions and Recommendations

Based on the market research conducted, there is sufficient competition to 
support a competitive acquisition. Multiple qualified vendors exist that can 
meet the technical requirements within the budget constraints.
"""
    
    # Project info
    project_info = {
        "program_name": "Advanced Logistics Management System (ALMS)",
        "budget": "$2.5 million",
        "period_of_performance": "36 months (3 years)",
        "date": "10/01/2025",
        "critical_requirements": "Real-time tracking, 99.9% uptime, integration with existing ERP systems, mobile access",
        "schedule_constraints": "Must be operational by Q2 FY2026",
        "vendor_research": "Conducted RFI in March 2025 with 12 responses, held industry day in April 2025 with 8 vendors",
        "small_business_potential": "4 of 12 respondents were small businesses with relevant experience",
    }
    
    try:
        # Initialize injector
        print("✓ Initializing CitationInjector with DoD standards...")
        injector = CitationInjector(api_key, document_type="Report")
        print("✓ DoD Citation Validator initialized")
        print()
        
        # Inject citations
        print("Running citation injection...\n")
        cited_content = injector.inject_citations(
            content=test_content,
            project_info=project_info
        )
        
        print("\n" + "="*70)
        print("RESULT: Citation Injection Complete")
        print("="*70)
        print()
        
        # Show sample of cited content
        print("Sample Output (first 800 characters):")
        print("-" * 70)
        print(cited_content[:800] + "...")
        print("-" * 70)
        print()
        
        # Check for DoD citation patterns
        print("="*70)
        print("VALIDATION: Citation Pattern Check")
        print("="*70)
        print()
        
        checks = {
            'FAR citations': r'\bFAR\s+\d+\.\d+',
            'DFARS citations': r'\bDFARS\s+\d+\.\d+',
            'DoDI citations': r'\bDoDI\s+\d+\.\d+',
            'USC citations': r'\d+\s+U\.S\.C\.\s+§\s+\d+',
            'Program documents': r'\([^)]+,\s+(?:FY\d{4}|\w+\s+\d{4}|\d{1,2}/\d{1,2}/\d{4})\)',
            'Any parenthetical': r'\([^)]{15,}\)',
        }
        
        all_passed = False
        patterns_found = 0
        
        for check_name, pattern in checks.items():
            matches = re.findall(pattern, cited_content, re.IGNORECASE)
            if matches:
                patterns_found += 1
                print(f"✅ {check_name}: Found {len(matches)} citation(s)")
                # Show first 3 examples
                for match in matches[:3]:
                    print(f"   - {match}")
            else:
                print(f"⚠️  {check_name}: Not found")
        
        print()
        
        # Determine test result
        if patterns_found >= 2:  # At least 2 types of citations found
            all_passed = True
            print("="*70)
            print("✅ TEST PASSED: DoD citations successfully injected")
            print(f"   Found {patterns_found}/{len(checks)} citation pattern types")
            print("="*70)
        else:
            print("="*70)
            print("⚠️  TEST PARTIAL: Some citation patterns found")
            print(f"   Found {patterns_found}/{len(checks)} citation pattern types")
            print("   Expected at least 2 different types")
            print("="*70)
        
        # Additional checks
        print()
        print("Additional Validation:")
        print("-" * 70)
        
        # Check if content was modified (should have more parentheses)
        original_parens = test_content.count('(')
        cited_parens = cited_content.count('(')
        new_citations = cited_parens - original_parens
        
        print(f"• Original content: {original_parens} parenthetical references")
        print(f"• Cited content: {cited_parens} parenthetical references")
        print(f"• New citations added: {new_citations}")
        
        if new_citations > 0:
            print(f"✅ Citations were added to the content")
        else:
            print(f"⚠️  No new citations detected")
            all_passed = False
        
        print()
        return all_passed
        
    except Exception as e:
        print("\n" + "="*70)
        print("❌ TEST FAILED: Exception occurred")
        print("="*70)
        print(f"\nError: {type(e).__name__}")
        print(f"Message: {str(e)}")
        print()
        
        # Show traceback
        import traceback
        print("Traceback:")
        print("-" * 70)
        traceback.print_exc()
        print()
        
        return False


def main():
    """
    Main test execution
    
    Comments:
        Runs DoD citation injection test and exits with appropriate code
        Loads environment variables from .env file automatically
    """
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " " * 15 + "DoD Citation Injector Test Suite" + " " * 21 + "║")
    print("╚" + "="*68 + "╝")
    print()
    
    success = test_dod_citation_injection()
    
    print("\n")
    print("="*70)
    print("TEST SUITE COMPLETE")
    print("="*70)
    print()
    
    if success:
        print("✅ All tests passed!")
        print("\nNext steps:")
        print("1. Test with real documents: python scripts/run_market_research.py")
        print("2. Proceed to Phase 3: Update Quality Agent")
        print("3. Run full pipeline: python scripts/run_full_pipeline.py")
    else:
        print("⚠️  Tests incomplete or failed")
        print("\nTroubleshooting:")
        print("1. Verify .env file exists in project root")
        print("2. Check .env contains ANTHROPIC_API_KEY=your-key")
        print("3. Ensure utils/dod_citation_validator.py exists")
        print("4. Verify core/add_citations.py has DoD updates")
        print("5. Review error messages above")
    
    print()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
