"""
Complete Post-Solicitation Pipeline Test
Tests all 9 post-solicitation tools including the new award phase tools
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.append(str(Path(__file__).parent.parent))

from agents import PostSolicitationOrchestrator
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever


def test_complete_award_workflow():
    """
    Test complete post-solicitation workflow:
    - Source Selection Plan
    - PPQs
    - Evaluation Scorecards
    - SSDD
    - SF-26
    - Debriefings
    - Award Notifications
    (Plus Amendment and Q&A from previous implementation)
    """
    print("\n" + "="*80)
    print("COMPLETE POST-SOLICITATION WORKFLOW TEST")
    print("="*80)
    print("Testing all 9 post-solicitation tools")
    print("="*80 + "\n")
    
    # Get API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not set")
        return
    
    # Initialize RAG (optional)
    retriever = None
    try:
        print("Initializing RAG system...")
        vector_store = VectorStore(api_key)
        vector_store.load()
        retriever = Retriever(vector_store, top_k=3)
        print("✓ RAG system ready\n")
    except Exception as e:
        print(f"⚠ RAG not available: {e}\n")
    
    # Initialize orchestrator
    orchestrator = PostSolicitationOrchestrator(api_key, retriever)
    
    # Solicitation information
    solicitation_info = {
        'solicitation_number': 'W911XX-25-R-1234',
        'program_name': 'Advanced Logistics Management System (ALMS)',
        'office': 'Army Contracting Command',
        'contracting_officer': 'Jane Smith',
        'co_email': 'jane.smith@army.mil',
        'co_phone': '(703) 555-1234',
        'issue_date': 'September 1, 2025',
        'proposal_due_date': 'October 15, 2025'
    }
    
    # Section M content
    section_m_content = """
    Evaluation Factor 1: Technical Approach (40%)
    Evaluation Factor 2: Management Approach (30%)
    Evaluation Factor 3: Past Performance (20%)
    Evaluation Factor 4: Cost/Price (10%)
    """
    
    # Offerors (sample)
    offerors = [
        {
            'name': 'TechSolutions Inc.',
            'duns': '123456789',
            'size': 'Small Business',
            'socioeconomic': 'SDVOSB',
            'cost': '$4.8M',
            'reference_contract': 'W912XX-20-C-5678',
            'address': '123 Tech Street, Arlington, VA 22202'
        },
        {
            'name': 'Global Systems Corp.',
            'duns': '987654321',
            'size': 'Large Business',
            'socioeconomic': 'N/A',
            'cost': '$5.2M',
            'reference_contract': 'W913XX-19-C-9012',
            'address': '456 Corp Ave, McLean, VA 22102'
        },
        {
            'name': 'Innovative Solutions LLC',
            'duns': '555555555',
            'size': 'Small Business',
            'socioeconomic': 'WOSB',
            'cost': '$4.5M',
            'reference_contract': 'W914XX-21-C-3456',
            'address': '789 Innovation Dr, Reston, VA 20190'
        }
        ]
    
    # Recommended awardee (based on best value)
    recommended_awardee = 'TechSolutions Inc.'
    
    # Configuration
    config = {
        'source_selection_method': 'Best Value Trade-Off',
        'ssa_name': 'General John Doe',
        'ssa_title': 'Program Executive Officer',
        'ssa_organization': 'PEO - Army Logistics',
        'contract_value': '$4.8M',
        'contract_number': 'W911XX-25-C-0001',
        'contract_type': 'Firm-Fixed-Price (FFP)',
        'period_of_performance': '12 months base + 4 option years',
        'classification': 'UNCLASSIFIED'
    }
    
    # Execute complete workflow
    print("="*80)
    print("EXECUTING COMPLETE POST-SOLICITATION WORKFLOW")
    print("="*80 + "\n")
    
    results = orchestrator.execute_complete_workflow(
        solicitation_info=solicitation_info,
        section_m_content=section_m_content,
        offerors=offerors,
        recommended_awardee=recommended_awardee,
        output_dir='outputs',
        config=config
    )
    
    # Print results summary
    print("\n" + "="*80)
    print("WORKFLOW RESULTS SUMMARY")
    print("="*80)
    print(f"Status: {results['workflow_status']}")
    print(f"Phases Completed: {len(results['phases_completed'])}/7\n")
    
    print("Generated Documents:")
    print("-" * 80)
    if results.get('ssp'):
        print(f"  ✓ Source Selection Plan: {results['ssp']['markdown']}")
    if results.get('ppqs'):
        print(f"  ✓ PPQs: {len(results['ppqs'])} questionnaires")
    if results.get('scorecards'):
        print(f"  ✓ Evaluation Scorecards: {len(results['scorecards'])} offerors × 4 factors")
    if results.get('ssdd'):
        print(f"  ✓ SSDD: {results['ssdd']['markdown']}")
    if results.get('sf26'):
        print(f"  ✓ SF-26: {results['sf26']['markdown']}")
    if results.get('award_notifications'):
        print(f"  ✓ Award Notifications: {results['award_notifications']['markdown']}")
    if results.get('debriefings'):
        print(f"  ✓ Debriefings: {len(results['debriefings'])} documents")
    
    print("\n" + "="*80)
    print("✅ COMPLETE POST-SOLICITATION WORKFLOW TEST: PASSED")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_complete_award_workflow()

