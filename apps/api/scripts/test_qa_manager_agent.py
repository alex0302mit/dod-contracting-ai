"""
Test script for QA Manager Agent - Phase 2 Agent 5
Validates TBD reduction in Q&A response generation
"""

import sys
import os
import re
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.qa_manager_agent import QAManagerAgent
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever
from dotenv import load_dotenv

load_dotenv()

def count_tbds_in_template() -> int:
    """Count TBD placeholders in template"""
    template_path = "templates/qa_response_template.md"
    with open(template_path, 'r') as f:
        content = f.read()

    # Count unique {{template_variables}}
    template_vars = set(re.findall(r'\{\{([^}]+)\}\}', content))
    return len(template_vars)

def count_tbds_in_content(content: str) -> int:
    """Count remaining TBDs in generated content"""
    # Count {{template_variables}} that weren't replaced
    template_vars = set(re.findall(r'\{\{([^}]+)\}\}', content))
    # Count explicit TBD markers
    tbd_markers = len(re.findall(r'\bTBD\b', content, re.IGNORECASE))

    return len(template_vars) + tbd_markers

def main():
    print("="*80)
    print("QA MANAGER AGENT - PHASE 2 AGENT 5 BASELINE TEST")
    print("="*80)

    # Count baseline TBDs in template
    print("\nSTEP 1: Counting baseline TBDs in template...")
    baseline_tbds = count_tbds_in_template()
    print(f"  ✓ Baseline template variables: {baseline_tbds}")

    # Calculate target
    target_reduction = 0.70  # 70%
    target_tbds = int(baseline_tbds * (1 - target_reduction))
    target_eliminated = baseline_tbds - target_tbds

    print(f"\n  Target: {target_reduction*100}% reduction")
    print(f"  Target TBDs remaining: ≤{target_tbds}")
    print(f"  Must eliminate: ≥{target_eliminated} TBDs")

    # Initialize RAG system
    print("\nSTEP 2: Initializing RAG system...")
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in environment")
        return

    vector_store = VectorStore(api_key=api_key)
    vector_store.load()
    retriever = Retriever(vector_store, top_k=5)
    print("  ✓ RAG system loaded")

    # Initialize QA Manager agent
    print("\nSTEP 3: Initializing QA Manager Agent...")
    agent = QAManagerAgent(api_key=api_key, retriever=retriever)
    print("  ✓ Agent initialized")

    # Add test questions
    print("\nSTEP 4: Adding test questions...")

    test_questions = [
        {
            'question': 'What is the contract type for this acquisition?',
            'vendor': 'ABC Corporation',
            'category': 'Contract Type and Pricing'
        },
        {
            'question': 'Can you clarify the system availability requirements in Section C?',
            'vendor': 'XYZ Solutions',
            'category': 'Technical Requirements'
        },
        {
            'question': 'What is the deadline for proposal submission?',
            'vendor': 'Anonymous',
            'category': 'Proposal Submission'
        }
    ]

    for q in test_questions:
        agent.add_question(
            question_text=q['question'],
            submitter=q['vendor'],
            category=q['category']
        )
        print(f"  ✓ Added question from {q['vendor']}")

    # Generate answers
    print("\nSTEP 5: Generating answers using RAG...")

    solicitation_context = {
        'solicitation_number': 'W911S0-25-R-0001',
        'program_name': 'Advanced Logistics Management System (ALMS)',
        'contract_type': 'Firm-Fixed-Price with Option Years',
        'availability_requirement': '99.9% uptime during business hours',
        'proposal_due_date': 'January 15, 2026'
    }

    for q_id in [1, 2, 3]:
        answer = agent.generate_answer(q_id, solicitation_context)
        print(f"  ✓ Generated answer for Q-{q_id:03d}")

    # Generate Q&A document
    print("\nSTEP 6: Generating Q&A document...")

    project_info = {
        'solicitation_number': 'W911S0-25-R-0001',
        'program_name': 'Advanced Logistics Management System (ALMS)',
        'issuing_office': 'U.S. Army Contracting Command - Rock Island',
        'poc_name': 'Jane Smith',
        'poc_title': 'Contract Specialist',
        'poc_email': 'jane.smith@army.mil',
        'poc_phone': '(309) 782-1234',
        'original_issue_date': 'October 1, 2025',
        'proposal_due_date': 'January 15, 2026',
        'questions_deadline': 'December 1, 2025'
    }

    config = {
        'classification': 'UNCLASSIFIED'
    }

    result = agent.generate_qa_document(project_info, config)
    content = result['content']

    # Count TBDs in generated document
    print("\nSTEP 7: Analyzing generated document...")
    current_tbds = count_tbds_in_content(content)
    reduction = baseline_tbds - current_tbds
    reduction_pct = (reduction / baseline_tbds) * 100 if baseline_tbds > 0 else 0

    print(f"  ✓ TBDs remaining: {current_tbds}")
    print(f"  ✓ TBDs eliminated: {reduction}")
    print(f"  ✓ Reduction: {reduction_pct:.1f}%")

    # Word count
    word_count = len(content.split())
    print(f"  ✓ Generated document: {word_count} words")

    # Save output
    output_dir = "output/phase2_tests"
    os.makedirs(output_dir, exist_ok=True)

    output_path = f"{output_dir}/qa_document_baseline.md"
    with open(output_path, 'w') as f:
        f.write(content)
    print(f"\n✓ Generated Q&A document saved to: {output_path}")

    # Results
    print("\n" + "="*80)
    print("RESULTS - QA MANAGER AGENT")
    print("="*80)
    print(f"Baseline TBDs:      {baseline_tbds}")
    print(f"Current TBDs:       {current_tbds}")
    print(f"Reduction:          {reduction} TBDs eliminated")
    print(f"Reduction %:        {reduction_pct:.1f}%")
    print(f"Target:             {target_reduction*100}% reduction (~{target_tbds} TBDs)")

    if reduction_pct >= target_reduction * 100:
        print(f"✅ SUCCESS: Target achieved! ({reduction_pct:.1f}% >= {target_reduction*100}%)")
    else:
        print(f"❌ BELOW TARGET: {reduction_pct:.1f}% < {target_reduction*100}%")

    print("="*80)

    print(f"\nDocument Stats:")
    print(f"  - Word Count: {word_count}")
    print(f"  - Questions Answered: {len(test_questions)}")
    print(f"  - Template Variables Populated: {baseline_tbds - current_tbds}")

    # Identify remaining TBDs
    if current_tbds > 0:
        print(f"\nRemaining TBDs ({current_tbds}):")
        remaining_vars = re.findall(r'\{\{([^}]+)\}\}', content)
        remaining_unique = set(remaining_vars)
        for var in sorted(remaining_unique):
            count = remaining_vars.count(var)
            print(f"  - {{{{{var}}}}} ({count} occurrence{'s' if count > 1 else ''})")

    # Save test report
    with open(f"{output_dir}/qa_manager_test_results.txt", 'w') as f:
        f.write(f"QA Manager Agent - Test Results\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"\n")
        f.write(f"Baseline TBDs: {baseline_tbds}\n")
        f.write(f"Current TBDs: {current_tbds}\n")
        f.write(f"Reduction: {reduction} TBDs\n")
        f.write(f"Reduction %: {reduction_pct:.1f}%\n")
        f.write(f"Target: {target_reduction*100}%\n")
        f.write(f"Status: {'PASS' if reduction_pct >= target_reduction * 100 else 'FAIL'}\n")
        f.write(f"\n")
        f.write(f"Document Stats:\n")
        f.write(f"  Word Count: {word_count}\n")
        f.write(f"  Questions Answered: {len(test_questions)}\n")

    print(f"\n✓ Test report saved to: {output_dir}/qa_manager_test_results.txt")

if __name__ == "__main__":
    main()
