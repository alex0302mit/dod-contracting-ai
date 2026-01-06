"""
Test script for Pre-Solicitation Pipeline
Demonstrates complete pre-solicitation workflow with ALMS example
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.pre_solicitation_orchestrator import PreSolicitationOrchestrator
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever


def run_pre_solicitation_test():
    """
    Run complete pre-solicitation workflow test
    """
    print("\n" + "="*80)
    print("PRE-SOLICITATION PIPELINE TEST")
    print("="*80)
    print("Testing all 6 pre-solicitation document generators")
    print("="*80 + "\n")
    
    # Get API keys
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it using: export ANTHROPIC_API_KEY='your-api-key'")
        return
    
    tavily_api_key = os.getenv("TAVILY_API_KEY")  # Optional
    
    # Initialize RAG system (optional but recommended for ALMS cost references)
    retriever = None
    try:
        print("Initializing RAG system for ALMS cost/schedule references...")
        vector_store = VectorStore(anthropic_api_key)
        vector_store.load()
        retriever = Retriever(vector_store, top_k=5)
        print("✓ RAG system initialized\n")
    except Exception as e:
        print(f"⚠ RAG system initialization failed: {e}")
        print("Continuing without RAG (cost benchmarking will use defaults)\n")
    
    # Initialize orchestrator
    orchestrator = PreSolicitationOrchestrator(
        api_key=anthropic_api_key,
        retriever=retriever,
        tavily_api_key=tavily_api_key
    )
    
    # Define project information (using ALMS as example)
    project_info = {
        'program_name': 'Advanced Logistics Management System (ALMS)',
        'organization': 'Department of Defense / U.S. Army',
        'estimated_value': '$2.5M - $6.4M (10-year lifecycle)',
        'period_of_performance': '12 months base + 4 option years',
        'contract_type': 'services',  # or 'research_development'
        'contracting_officer': 'Jane Smith',
        'ko_email': 'jane.smith@army.mil',
        'ko_phone': '(703) 555-1234',
        'description': 'Cloud-based logistics inventory management system for 2,800 users across 15 Army installations'
    }
    
    # Optional: Provide requirements content for better context
    requirements_content = """
# ALMS Requirements Summary

## Functional Requirements
- Cloud-based deployment (FedRAMP Moderate)
- Real-time inventory tracking and management
- Mobile application for iOS and Android
- Integration with SAP S/4HANA, DLA DSS, GCSS-Army
- Multi-tenant architecture supporting 2,800 concurrent users

## Performance Requirements
- System Availability: 99.5% threshold, 99.9% objective
- Transaction Performance: <3 seconds threshold, <1 second objective
- Inventory Accuracy: 95% threshold, 98% objective

## Security Requirements
- NIST 800-171 compliance
- CMMC Level 2 certification
- AES-256 encryption for data at rest and in transit
- Multi-factor authentication (MFA)

## Key Deliverables
- Fully functional cloud-based system
- Mobile applications (iOS and Android)
- Integration with 4 external systems
- Technical documentation and training materials
- Operations and maintenance support
"""
    
    # Execute complete pre-solicitation workflow
    print("\n" + "="*80)
    print("EXECUTING COMPLETE PRE-SOLICITATION WORKFLOW")
    print("="*80 + "\n")
    
    results = orchestrator.execute_pre_solicitation_workflow(
        project_info=project_info,
        requirements_content=requirements_content,
        output_dir='outputs/pre-solicitation',
        generate_sources_sought=True,
        generate_rfi=True,
        generate_acquisition_plan=True,
        generate_igce=True,
        generate_pre_solicitation_notice=True,
        generate_industry_day=True,
        # Optional configurations
        sources_sought_config={
            'response_days': 21,
            'office': 'Army Contracting Command'
        },
        rfi_config={
            'response_days': 35,
            'questions_days': 15
        },
        acquisition_plan_config={
            'prepared_by': 'Program Manager - ALMS',
            'pm_name': 'John Doe',
            'co_name': 'Jane Smith'
        },
        igce_config={
            'prepared_by': 'Cost Analyst',
            'contract_type': 'Firm-Fixed-Price (FFP)'
        },
        pre_sol_notice_config={
            'rfp_release_days': 21,
            'proposal_days': 45
        },
        industry_day_config={
            'venue_name': 'Pentagon Conference Center',
            'venue_address': 'Arlington, VA 22202'
        }
    )
    
    # Print summary
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    
    if results['workflow_status'] == 'completed':
        print("✅ PRE-SOLICITATION WORKFLOW: SUCCESSFUL")
        print(f"\nPhases Completed: {len(results['phases_completed'])}/6")
        
        for phase, result in results.items():
            if phase in ['workflow_status', 'phases_completed', 'outputs']:
                continue
            
            print(f"\n{phase.replace('_', ' ').upper()}:")
            print(f"  Status: {result['status']}")
            print(f"  Markdown: {result['output_path']}")
            if result.get('pdf_path'):
                print(f"  PDF: {result['pdf_path']}")
            
            # Print metadata
            if 'metadata' in result:
                print(f"  Metadata:")
                for key, value in result['metadata'].items():
                    print(f"    - {key}: {value}")
    else:
        print("❌ PRE-SOLICITATION WORKFLOW: FAILED")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    
    return results


def test_individual_generators():
    """Test each generator individually (for debugging)"""
    print("\n" + "="*80)
    print("INDIVIDUAL GENERATOR TESTS")
    print("="*80 + "\n")
    
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not set")
        return
    
    # Test configuration
    project_info = {
        'program_name': 'Test Program',
        'organization': 'Department of Defense',
        'estimated_value': '$5M',
        'period_of_performance': '12 months',
        'contract_type': 'services',
        'contracting_officer': 'John Doe',
        'ko_email': 'john.doe@mil.gov',
        'ko_phone': '(703) 555-0000'
    }
    
    # Test each agent
    tests = []
    
    # 1. Test Sources Sought
    print("Testing Sources Sought Generator...")
    try:
        from agents.sources_sought_generator_agent import SourcesSoughtGeneratorAgent
        agent = SourcesSoughtGeneratorAgent(anthropic_api_key)
        result = agent.execute({'project_info': project_info, 'config': {}})
        tests.append(('Sources Sought', result['status'] == 'success'))
        print(f"  ✓ Sources Sought: {result['status']}")
    except Exception as e:
        tests.append(('Sources Sought', False))
        print(f"  ✗ Sources Sought: {e}")
    
    # 2. Test RFI
    print("\nTesting RFI Generator...")
    try:
        from agents.rfi_generator_agent import RFIGeneratorAgent
        agent = RFIGeneratorAgent(anthropic_api_key)
        result = agent.execute({'project_info': project_info, 'config': {}})
        tests.append(('RFI', result['status'] == 'success'))
        print(f"  ✓ RFI: {result['status']}")
    except Exception as e:
        tests.append(('RFI', False))
        print(f"  ✗ RFI: {e}")
    
    # 3. Test Acquisition Plan
    print("\nTesting Acquisition Plan Generator...")
    try:
        from agents.acquisition_plan_generator_agent import AcquisitionPlanGeneratorAgent
        agent = AcquisitionPlanGeneratorAgent(anthropic_api_key)
        result = agent.execute({'project_info': project_info, 'config': {}})
        tests.append(('Acquisition Plan', result['status'] == 'success'))
        print(f"  ✓ Acquisition Plan: {result['status']}")
    except Exception as e:
        tests.append(('Acquisition Plan', False))
        print(f"  ✗ Acquisition Plan: {e}")
    
    # 4. Test IGCE
    print("\nTesting IGCE Generator...")
    try:
        from agents.igce_generator_agent import IGCEGeneratorAgent
        agent = IGCEGeneratorAgent(anthropic_api_key)
        result = agent.execute({'project_info': project_info, 'requirements_content': '', 'config': {}})
        tests.append(('IGCE', result['status'] == 'success'))
        print(f"  ✓ IGCE: {result['status']}")
    except Exception as e:
        tests.append(('IGCE', False))
        print(f"  ✗ IGCE: {e}")
    
    # 5. Test Pre-Solicitation Notice
    print("\nTesting Pre-Solicitation Notice Generator...")
    try:
        from agents.pre_solicitation_notice_generator_agent import PreSolicitationNoticeGeneratorAgent
        agent = PreSolicitationNoticeGeneratorAgent(anthropic_api_key)
        result = agent.execute({'project_info': project_info, 'config': {}})
        tests.append(('Pre-Sol Notice', result['status'] == 'success'))
        print(f"  ✓ Pre-Sol Notice: {result['status']}")
    except Exception as e:
        tests.append(('Pre-Sol Notice', False))
        print(f"  ✗ Pre-Sol Notice: {e}")
    
    # 6. Test Industry Day
    print("\nTesting Industry Day Generator...")
    try:
        from agents.industry_day_generator_agent import IndustryDayGeneratorAgent
        agent = IndustryDayGeneratorAgent(anthropic_api_key)
        result = agent.execute({'project_info': project_info, 'config': {}})
        tests.append(('Industry Day', result['status'] == 'success'))
        print(f"  ✓ Industry Day: {result['status']}")
    except Exception as e:
        tests.append(('Industry Day', False))
        print(f"  ✗ Industry Day: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("INDIVIDUAL TEST SUMMARY")
    print("="*80)
    passed = sum(1 for _, success in tests if success)
    total = len(tests)
    print(f"Tests Passed: {passed}/{total}")
    for name, success in tests:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"  {status}: {name}")
    print("="*80 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Pre-Solicitation Pipeline")
    parser.add_argument('--individual', action='store_true', help='Test individual generators only')
    parser.add_argument('--full', action='store_true', help='Run full workflow (default)')
    
    args = parser.parse_args()
    
    if args.individual:
        test_individual_generators()
    else:
        run_pre_solicitation_test()

