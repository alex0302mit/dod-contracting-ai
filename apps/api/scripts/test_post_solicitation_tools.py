"""
Test script for Post-Solicitation tools
Demonstrates Amendment Generator, Q&A Manager, and Evaluation Scorecards
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.amendment_generator_agent import AmendmentGeneratorAgent
from backend.agents.qa_manager_agent import QAManagerAgent
from backend.agents.evaluation_scorecard_generator_agent import EvaluationScorecardGeneratorAgent
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever


def test_amendment_generator():
    """Test Amendment Generator"""
    print("\n" + "="*80)
    print("TEST 1: AMENDMENT GENERATOR")
    print("="*80 + "\n")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return False
    
    # Initialize agent
    agent = AmendmentGeneratorAgent(api_key)
    
    # Solicitation information
    solicitation_info = {
        'solicitation_number': 'W911XX-25-R-1234',
        'program_name': 'Advanced Logistics Management System (ALMS)',
        'office': 'Army Contracting Command',
        'contracting_officer': 'Jane Smith',
        'co_email': 'jane.smith@army.mil',
        'co_phone': '(703) 555-1234',
        'issue_date': 'September 1, 2025',
        'proposal_due_date': 'October 15, 2025 at 2:00 PM EST'
    }
    
    # Changes to incorporate
    changes = [
        {
            'section': 'Section C (PWS)',
            'type': 'modify',
            'description': 'Clarified performance standard for system availability from 99.5% to 99.7% based on industry feedback',
            'impact': 'major'
        },
        {
            'section': 'Section L',
            'type': 'modify',
            'description': 'Extended page limit for Technical Volume from 25 to 30 pages',
            'impact': 'minor'
        },
        {
            'section': 'Attachment J-1',
            'type': 'add',
            'description': 'Added Interface Control Document (ICD) for SAP integration',
            'impact': 'major'
        }
    ]
    
    # Q&A responses (if any)
    qa_responses = [
        {'id': 'Q-001', 'question': 'What cloud provider is required?', 'answer': 'AWS GovCloud or Azure Government'},
        {'id': 'Q-002', 'question': 'Is CMMC Level 2 required?', 'answer': 'Yes, per PWS Section 3.4'}
    ]
    
    # Generate amendment
    task = {
        'solicitation_info': solicitation_info,
        'amendment_number': '0001',
        'changes': changes,
        'qa_responses': qa_responses,
        'config': {
            'extension_days': 14,
            'reason': 'Incorporate industry feedback and Q&A responses'
        }
    }
    
    result = agent.execute(task)
    
    # Save to file
    output_path = 'outputs/amendments/amendment_0001.md'
    files = agent.save_to_file(result['content'], output_path, convert_to_pdf=True)
    
    print("\n" + "="*80)
    print("✅ AMENDMENT GENERATOR TEST: PASSED")
    print("="*80)
    print(f"Amendment saved: {files['markdown']}")
    if files.get('pdf'):
        print(f"PDF saved: {files['pdf']}")
    print(f"\nMetadata:")
    for key, value in result['metadata'].items():
        print(f"  - {key}: {value}")
    print("="*80 + "\n")
    
    return True


def test_qa_manager():
    """Test Q&A Manager"""
    print("\n" + "="*80)
    print("TEST 2: Q&A MANAGER")
    print("="*80 + "\n")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return False
    
    # Initialize RAG (optional)
    retriever = None
    try:
        print("Loading RAG system for Q&A answering...")
        vector_store = VectorStore(api_key)
        vector_store.load()
        retriever = Retriever(vector_store, top_k=3)
        print("✓ RAG system loaded\n")
    except Exception as e:
        print(f"⚠ RAG not available: {e}\n")
    
    # Initialize agent
    agent = QAManagerAgent(api_key, retriever)
    
    # Add sample questions
    print("Adding sample questions...")
    
    q1 = agent.add_question(
        "What cloud provider should be used for deployment?",
        submitter="Company A",
        category="Technical Requirements",
        solicitation_section="Section C (PWS)"
    )
    print(f"  ✓ Added {q1['id']}")
    
    q2 = agent.add_question(
        "What is the page limit for the Technical Volume?",
        submitter="Company B",
        category="Proposal Submission",
        solicitation_section="Section L"
    )
    print(f"  ✓ Added {q2['id']}")
    
    q3 = agent.add_question(
        "Is CMMC Level 2 certification required prior to contract award?",
        submitter="Company C",
        category="Security and Clearances",
        solicitation_section="Section C (PWS)"
    )
    print(f"  ✓ Added {q3['id']}")
    
    q4 = agent.add_question(
        "Can the performance period include option years beyond the stated 4 years?",
        submitter="Company D",
        category="Contract Type and Pricing",
        solicitation_section="Section B"
    )
    print(f"  ✓ Added {q4['id']}")
    
    # Generate answers
    print("\nGenerating answers...")
    
    # Answer with manual response
    agent.generate_answer(q1['id'], manual_answer="AWS GovCloud or Azure Government are both acceptable. The contractor may propose either platform as long as FedRAMP Moderate certification is maintained.")
    print(f"  ✓ Answered {q1['id']}")
    
    agent.generate_answer(q2['id'], manual_answer="The Technical Volume page limit is 25 pages as specified in Section L.4.1.")
    print(f"  ✓ Answered {q2['id']}")
    
    agent.generate_answer(q3['id'], manual_answer="CMMC Level 2 certification is required within 12 months of contract award, not prior to award. Offerors must demonstrate a plan to achieve certification.")
    print(f"  ✓ Answered {q3['id']}")
    
    agent.generate_answer(q4['id'], manual_answer="No, the maximum period of performance is 12 months base + 4 option years as stated in the solicitation. No additional option years will be considered.")
    print(f"  ✓ Answered {q4['id']}")
    
    # Save Q&A database
    db_path = 'outputs/qa/qa_database.json'
    agent.save_qa_database(db_path)
    print(f"\n✓ Q&A database saved: {db_path}")
    
    # Generate Q&A document
    print("\nGenerating Q&A document...")
    
    solicitation_info = {
        'solicitation_number': 'W911XX-25-R-1234',
        'program_name': 'Advanced Logistics Management System (ALMS)',
        'office': 'Army Contracting Command',
        'contracting_officer': 'Jane Smith',
        'co_email': 'jane.smith@army.mil',
        'co_phone': '(703) 555-1234',
        'issue_date': 'September 1, 2025',
        'proposal_due_date': 'October 15, 2025',
        'questions_deadline': 'October 1, 2025'
    }
    
    qa_doc_result = agent.generate_qa_document(solicitation_info, {})
    
    # Save Q&A document
    output_path = 'outputs/qa/questions_and_answers_001.md'
    files = agent.save_to_file(qa_doc_result['content'], output_path, convert_to_pdf=True)
    
    # Export statistics
    stats = agent.export_statistics()
    
    print("\n" + "="*80)
    print("✅ Q&A MANAGER TEST: PASSED")
    print("="*80)
    print(f"Q&A document saved: {files['markdown']}")
    if files.get('pdf'):
        print(f"PDF saved: {files['pdf']}")
    print(f"\nStatistics:")
    print(f"  - Total questions: {stats['total_questions']}")
    print(f"  - Answered: {stats['answered']}")
    print(f"  - Requires amendment: {stats['requires_amendment']}")
    print(f"  - Categories: {len(stats['by_category'])}")
    print("="*80 + "\n")
    
    return True


def test_evaluation_scorecards():
    """Test Evaluation Scorecard Generator"""
    print("\n" + "="*80)
    print("TEST 3: EVALUATION SCORECARD GENERATOR")
    print("="*80 + "\n")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return False
    
    # Initialize agent
    agent = EvaluationScorecardGeneratorAgent(api_key)
    
    # Solicitation information
    solicitation_info = {
        'solicitation_number': 'W911XX-25-R-1234',
        'program_name': 'Advanced Logistics Management System (ALMS)'
    }
    
    # Section M content (simplified)
    section_m_content = """
    Evaluation Factor 1: Technical Approach (40%)
    - System Architecture and Design
    - Development Methodology
    - Integration Approach
    - Cybersecurity Implementation
    - Testing and Quality Assurance
    """
    
    # Configuration for scorecard
    scorecard_config = {
        'offeror_name': 'ABC Technology Solutions Inc.',
        'offeror_duns': '123456789',
        'business_size': 'Small Business',
        'socioeconomic_status': 'SDVOSB',
        'evaluator_name': 'Dr. John Smith',
        'evaluator_title': 'Senior Technical Evaluator',
        'evaluator_org': 'Source Selection Evaluation Board (SSEB)',
        'source_selection_method': 'Best Value Trade-Off',
        'factor_weight': '40%',
        'page_count': '28',
        'proposal_date': 'October 15, 2025',
        'classification': 'UNCLASSIFIED'
    }
    
    # Generate Technical Approach scorecard
    task = {
        'solicitation_info': solicitation_info,
        'section_m_content': section_m_content,
        'evaluation_factor': 'Technical Approach',
        'config': scorecard_config
    }
    
    result = agent.execute(task)
    
    # Save to file
    output_path = 'outputs/evaluations/scorecard_technical_approach_offeror_abc.md'
    files = agent.save_to_file(result['content'], output_path, convert_to_pdf=True)
    
    print("\n" + "="*80)
    print("✅ EVALUATION SCORECARD TEST: PASSED")
    print("="*80)
    print(f"Scorecard saved: {files['markdown']}")
    if files.get('pdf'):
        print(f"PDF saved: {files['pdf']}")
    print(f"\nMetadata:")
    for key, value in result['metadata'].items():
        print(f"  - {key}: {value}")
    print("="*80 + "\n")
    
    # Test full scorecard set generation
    print("Generating complete scorecard set (all factors)...\n")
    
    full_set = agent.generate_full_scorecard_set(
        solicitation_info,
        section_m_content,
        scorecard_config
    )
    
    # Save each scorecard
    for factor, scorecard_result in full_set['scorecards'].items():
        factor_filename = factor.lower().replace(' ', '_').replace('/', '_')
        output_path = f'outputs/evaluations/scorecard_{factor_filename}_offeror_abc.md'
        files = agent.save_to_file(scorecard_result['content'], output_path, convert_to_pdf=False)
        print(f"  ✓ Saved: {files['markdown']}")
    
    print("\n✅ Generated complete scorecard set (4 factors)")
    
    return True


def run_all_tests():
    """Run all post-solicitation tool tests"""
    print("\n" + "="*80)
    print("POST-SOLICITATION TOOLS TEST SUITE")
    print("="*80)
    print("Testing: Amendment Generator, Q&A Manager, Evaluation Scorecards")
    print("="*80 + "\n")
    
    results = {
        'Amendment Generator': False,
        'Q&A Manager': False,
        'Evaluation Scorecards': False
    }
    
    # Test 1: Amendment Generator
    try:
        results['Amendment Generator'] = test_amendment_generator()
    except Exception as e:
        print(f"❌ Amendment Generator test failed: {e}\n")
    
    # Test 2: Q&A Manager
    try:
        results['Q&A Manager'] = test_qa_manager()
    except Exception as e:
        print(f"❌ Q&A Manager test failed: {e}\n")
    
    # Test 3: Evaluation Scorecards
    try:
        results['Evaluation Scorecards'] = test_evaluation_scorecards()
    except Exception as e:
        print(f"❌ Evaluation Scorecards test failed: {e}\n")
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUITE SUMMARY")
    print("="*80)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}\n")
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status}: {test_name}")
    
    print("\n" + "="*80)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
    
    print("="*80 + "\n")
    
    return passed == total


def demo_workflow():
    """Demonstrate complete post-solicitation workflow"""
    print("\n" + "="*80)
    print("POST-SOLICITATION WORKFLOW DEMONSTRATION")
    print("="*80 + "\n")
    
    print("SCENARIO: RFP is open, vendors are asking questions")
    print("-" * 80)
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    # Step 1: Manage Q&A
    print("\n📝 STEP 1: Managing vendor questions...")
    qa_agent = QAManagerAgent(api_key)
    
    q1 = qa_agent.add_question(
        "The PWS states 99.5% availability but industry standard for critical systems is 99.9%. Can we propose 99.9%?",
        category="Technical Requirements"
    )
    
    qa_agent.generate_answer(
        q1['id'],
        manual_answer="Offerors may propose solutions that exceed the minimum 99.5% availability threshold. Proposals exceeding requirements may be evaluated as strengths."
    )
    
    print(f"  ✓ {q1['id']}: Question answered")
    
    # Step 2: Identify need for amendment
    print("\n📋 STEP 2: Identifying questions requiring amendment...")
    
    q2 = qa_agent.add_question(
        "Section L specifies 25 pages for Technical Volume, but the complexity requires more detail. Can the page limit be extended?",
        category="Proposal Submission"
    )
    
    qa_agent.generate_answer(
        q2['id'],
        manual_answer="The Government will extend the Technical Volume page limit to 30 pages. This change will be incorporated via Amendment 0001."
    )
    
    amendment_required = qa_agent.get_questions_requiring_amendment()
    print(f"  ⚠️  {len(amendment_required)} question(s) require amendment")
    
    # Step 3: Generate Q&A document
    print("\n📄 STEP 3: Generating Q&A document...")
    
    solicitation_info = {
        'solicitation_number': 'W911XX-25-R-1234',
        'program_name': 'ALMS',
        'contracting_officer': 'Jane Smith',
        'co_email': 'jane.smith@army.mil'
    }
    
    qa_doc = qa_agent.generate_qa_document(solicitation_info, {})
    qa_agent.save_to_file(qa_doc['content'], 'outputs/qa/qa_demo.md')
    print(f"  ✓ Q&A document generated")
    
    # Step 4: Generate amendment incorporating changes
    print("\n📋 STEP 4: Generating amendment...")
    
    amend_agent = AmendmentGeneratorAgent(api_key)
    
    changes = [
        {
            'section': 'Section L',
            'type': 'modify',
            'description': 'Extended Technical Volume page limit from 25 to 30 pages',
            'impact': 'minor'
        }
    ]
    
    amendment_task = {
        'solicitation_info': solicitation_info,
        'amendment_number': '0001',
        'changes': changes,
        'qa_responses': [{'id': q['id'], 'question': q['question'], 'answer': q['answer']} for q in qa_agent.qa_database if q['status'] == 'answered'],
        'config': {'extension_days': 7}
    }
    
    amendment = amend_agent.execute(amendment_task)
    amend_agent.save_to_file(amendment['content'], 'outputs/amendments/amendment_demo.md')
    print(f"  ✓ Amendment 0001 generated")
    
    # Step 5: After proposals received - prepare evaluation scorecards
    print("\n📊 STEP 5: Preparing evaluation scorecards...")
    
    eval_agent = EvaluationScorecardGeneratorAgent(api_key)
    
    scorecard_task = {
        'solicitation_info': solicitation_info,
        'section_m_content': 'Technical Approach (40%), Management Approach (30%), Past Performance (20%), Cost (10%)',
        'evaluation_factor': 'Technical Approach',
        'config': {
            'offeror_name': 'Company A',
            'evaluator_name': 'Dr. Smith',
            'source_selection_method': 'Best Value Trade-Off'
        }
    }
    
    scorecard = eval_agent.execute(scorecard_task)
    eval_agent.save_to_file(scorecard['content'], 'outputs/evaluations/scorecard_demo.md')
    print(f"  ✓ Evaluation scorecard prepared")
    
    print("\n" + "="*80)
    print("✅ WORKFLOW DEMONSTRATION COMPLETE")
    print("="*80)
    print("\nGenerated:")
    print("  ✓ Q&A Document: outputs/qa/qa_demo.md")
    print("  ✓ Amendment: outputs/amendments/amendment_demo.md")
    print("  ✓ Evaluation Scorecard: outputs/evaluations/scorecard_demo.md")
    print("="*80 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Post-Solicitation Tools")
    parser.add_argument('--demo', action='store_true', help='Run workflow demonstration')
    parser.add_argument('--full', action='store_true', help='Run full test suite (default)')
    
    args = parser.parse_args()
    
    if args.demo:
        demo_workflow()
    else:
        run_all_tests()

