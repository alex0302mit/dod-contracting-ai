"""
Test Enhanced Hallucination Detection - Full Document Analysis

This script tests the new chunked hallucination detection that analyzes
the entire document instead of just the first 3,000 characters.

Dependencies:
- agents.quality_agent: Enhanced QualityAgent with full document analysis
- anthropic: Claude API for LLM calls
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from backend.agents.quality_agent import QualityAgent


def test_enhanced_hallucination_detection():
    """
    Test the enhanced hallucination detection with a large document
    
    This test demonstrates:
    1. Full document chunking (3000 chars with 500 char overlap)
    2. Per-chunk risk assessment
    3. Aggregate risk calculation
    4. Enhanced reporting with chunk-level details
    """
    
    print("="*80)
    print("TESTING ENHANCED HALLUCINATION DETECTION - FULL DOCUMENT ANALYSIS")
    print("="*80)
    print()
    
    # Get API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        return
    
    # Initialize Quality Agent
    print("1. Initializing Quality Agent...")
    agent = QualityAgent(api_key=api_key)
    print("   ✓ Agent initialized with enhanced hallucination detection\n")
    
    # Create a large test document (>10,000 characters)
    # This simulates a typical Market Research Report or Acquisition Plan
    test_document = """
# Market Research Report - Advanced Logistics Management System (ALMS)

## Executive Summary

The Advanced Logistics Management System (ALMS) represents a critical modernization initiative 
for the Department of Defense's supply chain operations. This market research identifies 47 qualified 
vendors with relevant cloud-based logistics capabilities (Ref: SAM.gov Vendor Search, 2025-10-18).

Based on comprehensive market analysis, 66% of identified vendors qualify as small businesses under 
NAICS code 541512 (Ref: SBA Size Standards, FY2025). The competitive landscape demonstrates sufficient 
depth for full and open competition under FAR 6.102 (Ref: FAR 6.102, Competition Requirements).

## Industry Landscape Analysis

### Vendor Capability Assessment

Recent contract awards in the logistics automation space show significant industry maturity. 
The General Services Administration awarded three major LCAT contracts totaling $8.2M in FY2024 
(Ref: USA Spending Contract Awards Database, 2024-Q4). These awards demonstrate proven capability 
delivery in similar DoD environments.

Labor rate analysis indicates commercial cloud developers command $95-145/hr for systems analysts 
and $85-165/hr for senior developers in the DC metro area (Ref: GSA Professional Services Schedule, 
2025-10-15). Solution architects with federal experience range from $125-220/hr based on clearance 
level and specialization (Ref: Defense Contractor Labor Market Survey, 2025-09-30).

### Technology Maturity

Cloud-native logistics platforms have achieved production maturity with multiple vendors offering 
FedRAMP Moderate authorized solutions (Ref: FedRAMP.gov Marketplace, 2025-10-10). Key capabilities 
include real-time tracking, predictive analytics, and automated workflow orchestration.

According to recent studies, AI-driven logistics optimization can reduce operational costs by 25-35%. 
This represents a significant opportunity for the ALMS program, though specific vendor claims require 
validation during the technical evaluation phase.

### Small Business Participation

The small business industrial base demonstrates robust capability in cloud logistics. Analysis of 
GSA Schedule 70 holders shows 156 small businesses offer relevant logistics software services 
(Ref: GSA eBuy Market Research, 2025-10-12). Of these, 31 vendors hold active DoD contracts worth 
$500K+ annually (Ref: FPDS-NG Contract Database, 2025-10-18).

Many industry experts believe that small business innovation will drive the next generation of 
logistics capabilities. The Small Business Administration has prioritized logistics technology 
in their FY2025 investment priorities (Ref: SBA Technology Investment Report, FY2025).

## Pricing Analysis

### Cost Structure Assessment

Market research indicates typical cloud logistics implementations range from $2M-$4M for initial 
deployment, with annual operating costs of $300K-$600K (Ref: Gartner Cloud Logistics Market Analysis, 
2025-06-15). These estimates align with DoD historical spending patterns for similar enterprise systems.

License costs vary significantly by deployment model. Software-as-a-Service (SaaS) offerings typically 
charge $150-$300 per user per month for enterprise features (Ref: Vendor Price Lists, Multiple Sources, 
2025-Q3). On-premise licensing follows traditional perpetual models with 15-20% annual maintenance.

Research shows that hybrid cloud deployments can reduce costs by up to 40% compared to fully on-premise 
solutions. However, this data comes from commercial sector studies and may not directly apply to 
federal security requirements.

### Labor Rate Benchmarking

Government contract labor rates show consistency across major metropolitan areas. The Washington DC 
region commands premium rates due to clearance requirements and high demand (Ref: OPM Locality Pay Tables, 
2025). Rates for equivalent positions in secondary markets like San Antonio or Colorado Springs run 
15-20% lower (Ref: GSA Contract Labor Market Analysis, 2025-Q2).

Project management oversight typically adds 8-12% to total labor costs based on industry standards. 
Quality assurance and testing represent an additional 10-15% of development labor (Ref: DoD Software 
Development Cost Guide, Version 3.2, 2024).

## Competition Analysis

### Market Concentration

The logistics software market exhibits moderate concentration with three major vendors holding 
approximately 45% market share (Ref: IDC Software Market Rankings, 2024-Q4). However, the DoD-specific 
segment shows greater fragmentation with no single vendor exceeding 15% of federal contract value 
(Ref: Bloomberg Government Federal IT Market Report, 2025).

Various analysts have noted increasing small business participation in federal logistics contracts. 
The GSA reports small business awards in IT services grew 12% year-over-year in FY2024 
(Ref: GSA Small Business Report, FY2024).

### Technical Differentiation

Vendors differentiate primarily on integration capabilities, security certifications, and logistics-specific 
features. FedRAMP authorization serves as a minimum threshold for cloud deployment, with 23 vendors 
holding relevant authorizations (Ref: FedRAMP Marketplace Search, 2025-10-10).

Studies have shown that API integration capability correlates strongly with implementation success rates. 
Modern microservices architectures enable 3-5x faster deployment than monolithic legacy systems, though 
specific timelines depend on organizational readiness.

## Risk Assessment

### Vendor Viability

Financial analysis of identified vendors shows strong stability. Dun & Bradstreet ratings for the 
top 20 vendors average 3A2 or higher, indicating low financial risk (Ref: D&B Vendor Financial Analysis, 
2025-09-15). No vendors in the competitive range show elevated business risk indicators.

Some industry observers worry about over-concentration in cloud infrastructure providers. The 
majority of logistics SaaS vendors rely on AWS or Azure infrastructure, creating potential supply 
chain dependencies (Ref: Cloud Infrastructure Market Analysis, 2025-Q2).

### Technical Risk Mitigation

Migration from legacy systems represents the primary technical risk. According to recent surveys, 
60-70% of federal IT modernization projects encounter integration challenges. The ALMS program 
should plan for comprehensive testing and phased deployment to mitigate these risks.

## Recommendations

### Acquisition Strategy

Market conditions support full and open competition under FAR Part 6. The depth of qualified vendors 
(47 identified) exceeds the threshold for competitive acquisition (Ref: FAR 6.102). A small business 
set-aside is not recommended given the technical complexity and integration requirements, though 
small business subcontracting goals should be emphasized.

Contract type recommendation is Hybrid Fixed-Price/Time-and-Materials structure. Initial deployment 
should use Firm-Fixed-Price for defined deliverables, with T&M provisions for integration support and 
sustainment activities (Ref: FAR 16.2, Contract Types).

### Evaluation Approach

Technical capability should receive highest weighting (40-45%) given system complexity. Past performance 
in DoD logistics environments warrants 25-30% weight to ensure proven delivery capability. Cost/price 
should not exceed 20-25% to avoid sacrificing technical quality for price savings.

Numerous procurement experts emphasize the importance of thorough technical evaluation in cloud 
acquisitions. The Office of Management and Budget recommends comprehensive technical demonstrations 
as part of the evaluation process (Ref: OMB Memorandum M-25-07, Cloud Acquisition Best Practices, 2025).

## Appendix A: Sources

All market research conducted in accordance with FAR 10.001 and DFARS 210.001 requirements. Research 
sources include government databases, industry publications, vendor documentation, and subject matter 
expert interviews. Pricing data represents market averages as of October 2025 and should be validated 
during cost analysis.

Total vendor outreach included 47 responses to preliminary market inquiries. Of these, 31 vendors 
provided detailed capability statements and pricing information. Response rate of 66% exceeds typical 
DoD market research response rates of 40-50% (Ref: Defense Acquisition University Market Research Guide, 2024).
""" 
    
    print(f"2. Test Document Created:")
    print(f"   - Length: {len(test_document):,} characters")
    print(f"   - Word Count: {len(test_document.split()):,} words")
    print(f"   - Citations: {len([c for c in test_document.split() if 'Ref:' in c])} inline citations")
    print()
    
    # Prepare test task
    project_info = {
        'program_name': 'ALMS',
        'budget': '$3.5M',
        'timeline': '18 months'
    }
    
    task = {
        'content': test_document,
        'section_name': 'Market Research Report',
        'project_info': project_info,
        'research_findings': {},
        'evaluation_type': 'section'
    }
    
    # Run enhanced hallucination detection
    print("3. Running Enhanced Hallucination Detection...")
    print("   (This will take 8-15 seconds to analyze all chunks)")
    print()
    
    try:
        # Call the quality agent - it will use the new enhanced method
        result = agent._check_hallucinations(
            content=test_document,
            project_info=project_info,
            research_findings={}
        )
        
        print("="*80)
        print("RESULTS: ENHANCED HALLUCINATION DETECTION")
        print("="*80)
        print()
        
        print(f"✓ Overall Risk Level: {result['risk_level']}")
        print(f"✓ Score: {result['score']}/100")
        print(f"✓ Full Document Analyzed: {result.get('full_document_analyzed', False)}")
        print()
        
        print(f"📊 Chunk Analysis:")
        print(f"   - Total Chunks Analyzed: {result.get('chunks_analyzed', 0)}")
        print(f"   - High Risk Chunks: {result.get('high_risk_chunks', 0)}")
        print(f"   - Medium Risk Chunks: {result.get('medium_risk_chunks', 0)}")
        print(f"   - Low Risk Chunks: {result.get('low_risk_chunks', 0)}")
        print()
        
        print(f"📝 LLM Assessment:")
        print(f"   {result['llm_assessment']}")
        print()
        
        if result.get('issues'):
            print(f"⚠️  Issues Found ({len(result['issues'])}):")
            for issue in result['issues']:
                print(f"   - {issue}")
            print()
        
        if result.get('suggestions'):
            print(f"💡 Suggestions ({len(result['suggestions'])}):")
            for suggestion in result['suggestions']:
                print(f"   - {suggestion}")
            print()
        
        # Show chunk details if available
        if result.get('chunk_details'):
            print(f"🔍 Sample Chunk Assessments:")
            for detail in result['chunk_details'][:3]:
                print(f"\n   Chunk {detail['chunk_num']}:")
                print(f"   Preview: {detail['preview'][:80]}...")
                print(f"   Assessment: {detail['assessment'][:150]}...")
            print()
        
        print("="*80)
        print("TEST COMPLETED SUCCESSFULLY")
        print("="*80)
        print()
        print("COMPARISON TO OLD METHOD:")
        print(f"  Old Method: Analyzed first 3,000 chars (~{min(3000, len(test_document)):,} chars)")
        print(f"  New Method: Analyzed ALL {len(test_document):,} characters in chunks")
        print(f"  Coverage Increase: {(len(test_document)/min(3000, len(test_document)))*100:.0f}%")
        print()
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_enhanced_hallucination_detection()

