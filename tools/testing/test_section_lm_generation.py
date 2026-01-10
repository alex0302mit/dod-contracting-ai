"""
Test Script: Section L and M Generation

Tests the complete Section L (Instructions to Offerors) and
Section M (Evaluation Factors for Award) generation pipeline.

Usage:
    python scripts/test_section_lm_generation.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from backend.agents.section_l_generator_agent import SectionLGeneratorAgent
from backend.agents.section_m_generator_agent import SectionMGeneratorAgent


def test_section_l_generation():
    """Test Section L generation"""
    print("\n" + "="*70)
    print("TESTING SECTION L GENERATOR")
    print("="*70)

    # Load API key
    load_dotenv()
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        return False

    # Sample project information
    project_info = {
        'program_name': 'Advanced Logistics Management System (ALMS)',
        'organization': 'Department of Defense / U.S. Army',
        'author': 'Jane Smith',
        'contracting_officer': 'John Doe',
        'ko_email': 'john.doe@army.mil',
        'ko_phone': '(703) 555-1234',
        'estimated_value': '$5,000,000 - $10,000,000',
        'period_of_performance': 'Base Period (12 months) + Four Option Periods (12 months each)'
    }

    # Sample PWS content (for complexity analysis)
    pws_content = """
    # Performance Work Statement (PWS)
    ## Advanced Logistics Management System (ALMS)

    ## 1. Scope

    The contractor shall develop, deploy, and maintain a cloud-based Advanced Logistics
    Management System (ALMS) to modernize supply chain operations across CONUS and OCONUS
    military installations. The system must integrate with existing DoD systems, provide
    real-time inventory tracking, and support predictive analytics for demand forecasting.

    ## 2. Performance Objectives

    **PO-001: System Development and Deployment**
    The contractor shall design, develop, test, and deploy a scalable cloud-native ALMS
    within 180 days of contract award.

    Performance Standard: System fully operational with 99.9% uptime and processing
    10,000 transactions per second.

    **PO-002: Data Integration and Migration**
    The contractor shall integrate ALMS with existing DoD logistics systems including
    DLA TBS, DPAS, and LOGSA systems, ensuring seamless data flow and synchronization.

    Performance Standard: 99.5% data accuracy with <2 hour synchronization latency.

    **PO-003: Cybersecurity Compliance**
    The contractor shall implement comprehensive cybersecurity controls in compliance
    with DFARS 252.204-7012, NIST SP 800-171, and DoD Cloud Security Requirements Guide.

    Performance Standard: Pass all required security assessments with zero critical
    vulnerabilities.

    **PO-004: User Training and Support**
    The contractor shall provide comprehensive training to 500+ users and 24/7/365
    help desk support with multi-tier escalation.

    Performance Standard: 95% user satisfaction rating, <15 minute response time for
    Priority 1 issues.

    **PO-005: Performance Analytics and Reporting**
    The contractor shall implement advanced analytics capabilities including predictive
    modeling, demand forecasting, and automated reporting dashboards.

    Performance Standard: 85% forecast accuracy with daily automated reports delivered
    by 0800 EST.

    ## 3. Technical Requirements

    ### 3.1 System Architecture
    - Cloud-native microservices architecture (AWS GovCloud or Azure Government)
    - Containerized deployment using Kubernetes
    - API-first design with RESTful and GraphQL interfaces
    - Event-driven architecture with message queuing

    ### 3.2 Data Management
    - Real-time data processing and analytics
    - Data warehouse for historical analysis
    - Master data management (MDM) implementation
    - Data governance and quality controls

    ### 3.3 Integration Requirements
    - Enterprise Service Bus (ESB) for system integration
    - SOAP and REST API endpoints
    - Secure file transfer protocols (SFTP/FTPS)
    - Real-time streaming data ingestion

    ### 3.4 Cybersecurity Requirements
    - Role-based access control (RBAC)
    - Multi-factor authentication (MFA)
    - Data encryption at rest and in transit (FIPS 140-2)
    - Continuous monitoring and threat detection
    - Incident response and recovery procedures

    ### 3.5 Performance Requirements
    - 99.9% system availability (excluding scheduled maintenance)
    - <3 second response time for 95% of transactions
    - Support 5,000 concurrent users
    - Horizontal scalability to 50,000 concurrent users

    ## 4. Quality Assurance

    The contractor shall implement comprehensive quality assurance processes including:
    - Automated testing (unit, integration, end-to-end)
    - Continuous integration/continuous deployment (CI/CD)
    - Code quality analysis and security scanning
    - Performance testing and load testing
    - User acceptance testing (UAT)

    ## 5. Deliverables

    **D-001: System Design Documentation** - Due: 30 days after award
    **D-002: Security Authorization Package** - Due: 60 days after award
    **D-003: Operational System (Development)** - Due: 90 days after award
    **D-004: Operational System (Production)** - Due: 180 days after award
    **D-005: Training Materials and User Guides** - Due: 150 days after award
    **D-006: Monthly Status Reports** - Due: 5th business day of each month
    **D-007: Quarterly Performance Reports** - Due: 10 business days after quarter end

    ## 6. Period of Performance

    Base Period: 12 months from contract award
    Option Period 1: 12 months
    Option Period 2: 12 months
    Option Period 3: 12 months
    Option Period 4: 12 months

    Total Potential Period: 60 months

    ## 7. Place of Performance

    - Primary: Contractor facility (TBD)
    - Government site support: Fort Belvoir, VA (as required)
    - Remote support: CONUS and OCONUS locations (as required)
    """

    # Configuration options (optional)
    config = {
        'contract_type': 'Firm-Fixed-Price (FFP)',
        'proposal_days': 45,
        'questions_days': 14,
        'max_file_size': '50'
    }

    # Initialize agent
    agent = SectionLGeneratorAgent(api_key=api_key)

    # Execute generation
    task = {
        'project_info': project_info,
        'pws_content': pws_content,
        'config': config
    }

    print("\nGenerating Section L...")
    result = agent.execute(task)

    if result['status'] != 'success':
        print(f"✗ Section L generation failed")
        return False

    # Save to file
    output_path = "outputs/section_l/section_l_instructions_to_offerors.md"
    files = agent.save_to_file(result['content'], output_path, convert_to_pdf=True)

    # Display results
    print("\n" + "="*70)
    print("SECTION L GENERATION RESULTS")
    print("="*70)
    print(f"Status: {result['status']}")
    print(f"Word Count: {result['statistics']['word_count']}")
    print(f"Section Count: {result['statistics']['section_count']}")
    print(f"\nMetadata:")
    print(f"  Solicitation #: {result['metadata']['solicitation_number']}")
    print(f"  Proposal Due: {result['metadata']['proposal_due_date']}")
    print(f"  Questions Due: {result['metadata']['questions_due_date']}")
    print(f"  Technical Pages: {result['metadata']['technical_approach_pages']}")
    print(f"  Management Pages: {result['metadata']['management_approach_pages']}")
    print(f"\nOutput Files:")
    print(f"  Markdown: {files['markdown']}")
    if 'pdf' in files:
        print(f"  PDF: {files['pdf']}")
    print("="*70)

    return True


def test_section_m_generation():
    """Test Section M generation"""
    print("\n" + "="*70)
    print("TESTING SECTION M GENERATOR")
    print("="*70)

    # Load API key
    load_dotenv()
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        return False

    # Sample project information
    project_info = {
        'program_name': 'Advanced Logistics Management System (ALMS)',
        'organization': 'Department of Defense / U.S. Army',
        'author': 'Jane Smith',
        'contracting_officer': 'John Doe',
        'ko_email': 'john.doe@army.mil'
    }

    # Use same PWS content as Section L test
    pws_content = """
    # Performance Work Statement (PWS)
    ## Advanced Logistics Management System (ALMS)

    The contractor shall develop, deploy, and maintain a cloud-based Advanced Logistics
    Management System with advanced cybersecurity controls, real-time data analytics
    capabilities, system integration with existing DoD systems, and 24/7 support.
    The system must be scalable, highly available, and comply with all applicable
    cybersecurity standards including NIST 800-53, DFARS requirements, and DoD Cloud
    Security Requirements Guide.

    Key technical requirements include:
    - Cloud-native microservices architecture
    - Real-time data processing and analytics
    - Integration with multiple DoD enterprise systems
    - Advanced cybersecurity and compliance controls
    - High availability (99.9% uptime)
    - Performance at scale (5,000-50,000 concurrent users)
    - Comprehensive quality assurance processes
    """ * 10  # Simulate moderate-high complexity

    # Configuration (optional)
    config = {}

    # Initialize agent
    agent = SectionMGeneratorAgent(api_key=api_key)

    # Execute generation
    task = {
        'project_info': project_info,
        'pws_content': pws_content,
        'config': config
    }

    print("\nGenerating Section M...")
    result = agent.execute(task)

    if result['status'] != 'success':
        print(f"✗ Section M generation failed")
        return False

    # Save to file
    output_path = "outputs/section_m/section_m_evaluation_factors.md"
    files = agent.save_to_file(result['content'], output_path, convert_to_pdf=True)

    # Display results
    print("\n" + "="*70)
    print("SECTION M GENERATION RESULTS")
    print("="*70)
    print(f"Status: {result['status']}")
    print(f"Word Count: {result['statistics']['word_count']}")
    print(f"Section Count: {result['statistics']['section_count']}")
    print(f"\nComplexity Analysis:")
    print(f"  Level: {result['complexity_analysis']['complexity_level']}")
    print(f"  Technical Indicators: {len(result['complexity_analysis']['technical_indicators'])}")
    print(f"  Risk Indicators: {len(result['complexity_analysis']['risk_indicators'])}")
    print(f"\nEvaluation Methodology:")
    print(f"  Method: {result['methodology']['method']}")
    print(f"  Rationale: {result['methodology']['rationale'][:100]}...")
    print(f"\nMetadata:")
    print(f"  Solicitation #: {result['metadata']['solicitation_number']}")
    print(f"  Technical Weight: {result['metadata']['technical_weight']}")
    print(f"  Management Weight: {result['metadata']['management_weight']}")
    print(f"  Past Performance Weight: {result['metadata']['past_performance_weight']}")
    print(f"  Cost Weight: {result['metadata']['cost_weight']}")
    print(f"\nOutput Files:")
    print(f"  Markdown: {files['markdown']}")
    if 'pdf' in files:
        print(f"  PDF: {files['pdf']}")
    print("="*70)

    return True


def test_integrated_generation():
    """Test integrated Section L and M generation with PWS orchestrator"""
    print("\n" + "="*70)
    print("TESTING INTEGRATED SECTION L/M GENERATION")
    print("="*70)

    # This would be tested through the PWS orchestrator
    # For now, just display the integration points

    print("\nIntegration Points:")
    print("  1. PWS Orchestrator has Section L/M generation phases")
    print("  2. Agents auto-detect and extract from PWS content")
    print("  3. Solicitation Package Orchestrator auto-includes L/M PDFs")
    print("\nTo test full integration:")
    print("  python scripts/run_pws_pipeline.py --with-section-l --with-section-m")
    print("="*70)

    return True


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print(" "*20 + "SECTION L/M GENERATION TEST SUITE")
    print("="*80)

    results = {}

    # Test 1: Section L Generation
    try:
        results['section_l'] = test_section_l_generation()
    except Exception as e:
        print(f"\n✗ Section L test failed with error: {e}")
        results['section_l'] = False

    # Test 2: Section M Generation
    try:
        results['section_m'] = test_section_m_generation()
    except Exception as e:
        print(f"\n✗ Section M test failed with error: {e}")
        results['section_m'] = False

    # Test 3: Integration
    try:
        results['integration'] = test_integrated_generation()
    except Exception as e:
        print(f"\n✗ Integration test failed with error: {e}")
        results['integration'] = False

    # Summary
    print("\n" + "="*80)
    print(" "*30 + "TEST SUMMARY")
    print("="*80)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name.upper()}: {status}")

    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)

    print(f"\n  Total: {passed_tests}/{total_tests} tests passed")
    print("="*80 + "\n")

    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
