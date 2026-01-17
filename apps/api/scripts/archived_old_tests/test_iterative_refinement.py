"""
Test Iterative Refinement: Generate → Evaluate → Fix → Re-evaluate
Demonstrates the quality feedback loop with a single section
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from backend.agents.refinement_agent import RefinementAgent
from backend.agents.quality_agent import QualityAgent


def main():
    """Test iterative refinement with a sample section"""

    print("\n" + "="*70)
    print("ITERATIVE REFINEMENT TEST")
    print("Generate → Evaluate → Fix → Re-evaluate Loop")
    print("="*70 + "\n")

    # Load environment
    load_dotenv()
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not set")
        return 1

    # Sample content with quality issues (vague language, missing citations)
    test_content = """
The Advanced Logistics Management System will improve inventory tracking
capabilities across several DoD installations. The contractor should deliver
a comprehensive solution that provides significant improvements in system
availability and operational efficiency.

The system must integrate with existing ERP systems and provide mobile
access for personnel. Performance should meet high availability standards
with minimal downtime. The contractor will achieve these modernization
outcomes within the allocated budget and timeframe.

Success will be measured through various performance metrics and user
satisfaction surveys conducted during the implementation period.
"""

    project_info = {
        "program_name": "Advanced Logistics Management System (ALMS)",
        "budget": "$2.5 million",
        "period_of_performance": "36 months",
        "installations": "15 DoD installations",
        "uptime_requirement": "99.9%",
        "date": "10/05/2025"
    }

    research_findings = {
        "findings": "System requirements include 99.9% uptime, ERP integration, and mobile access.",
        "sources": [
            "Performance Standards, 10/05/2025",
            "Technical Requirements, 10/05/2025",
            "Program Objectives, 10/05/2025"
        ]
    }

    # Initialize agents
    print("Initializing agents...")
    quality_agent = QualityAgent(api_key)
    refinement_agent = RefinementAgent(api_key)
    print("✓ Agents ready\n")

    # Phase 1: Initial Evaluation
    print("="*70)
    print("ITERATION 0: Initial Evaluation")
    print("="*70 + "\n")

    eval_task = {
        'content': test_content,
        'section_name': 'Purpose',
        'project_info': project_info,
        'research_findings': research_findings,
        'evaluation_type': 'soo'
    }

    evaluation = quality_agent.execute(eval_task)

    print(f"Initial Score: {evaluation['score']}/100")
    print(f"Grade: {evaluation['grade']}")
    print(f"Hallucination Risk: {evaluation['hallucination_risk']}")
    print()

    print("Detailed Scores:")
    for check_name, check_result in evaluation['detailed_checks'].items():
        score = check_result['score']
        status = "✅" if score >= 70 else "⚠️ "
        print(f"  {status} {check_name.replace('_', ' ').title()}: {score}/100")
    print()

    if evaluation['issues']:
        print(f"Issues ({len(evaluation['issues'])}):")
        for issue in evaluation['issues'][:5]:
            print(f"  - {issue}")
        print()

    # Iterative Refinement Loop
    max_iterations = 5
    quality_threshold = 90
    current_content = test_content
    current_evaluation = evaluation

    for iteration in range(1, max_iterations + 1):
        print("\n" + "="*70)
        print(f"ITERATION {iteration}: Refinement")
        print("="*70 + "\n")

        # Check if threshold met
        if current_evaluation['score'] >= quality_threshold:
            print(f"✅ Quality threshold ({quality_threshold}/100) met!")
            break

        print(f"Current score: {current_evaluation['score']}/100")
        print("Applying refinements based on quality feedback...\n")

        # Refine content
        refinement_task = {
            'content': current_content,
            'section_name': 'Purpose',
            'evaluation': current_evaluation,
            'project_info': project_info,
            'research_findings': research_findings,
            'iteration': iteration
        }

        refinement_result = refinement_agent.execute(refinement_task)
        refined_content = refinement_result['refined_content']

        print(f"Changes Made:")
        for change in refinement_result['changes_made']:
            print(f"  ✓ {change}")
        print()

        # Re-evaluate
        print("Re-evaluating refined content...\n")

        eval_task['content'] = refined_content
        new_evaluation = quality_agent.execute(eval_task)

        print(f"New Score: {new_evaluation['score']}/100 (was {current_evaluation['score']}/100)")
        improvement = new_evaluation['score'] - current_evaluation['score']
        print(f"Improvement: {improvement:+d} points")
        print(f"Grade: {new_evaluation['grade']}")
        print()

        print("Updated Detailed Scores:")
        for check_name, check_result in new_evaluation['detailed_checks'].items():
            old_score = current_evaluation['detailed_checks'][check_name]['score']
            new_score = check_result['score']
            delta = new_score - old_score
            status = "✅" if new_score >= 70 else "⚠️ "
            print(f"  {status} {check_name.replace('_', ' ').title()}: {new_score}/100 ({delta:+d})")
        print()

        # Check for improvement
        if improvement >= 5:
            print(f"✅ Significant improvement - continuing")
            current_content = refined_content
            current_evaluation = new_evaluation
        elif improvement > 0:
            print(f"⚠️  Minor improvement - continuing")
            current_content = refined_content
            current_evaluation = new_evaluation
        else:
            print(f"❌ No improvement - stopping")
            break

    # Final Summary
    print("\n" + "="*70)
    print("REFINEMENT SUMMARY")
    print("="*70 + "\n")

    initial_score = evaluation['score']
    final_score = current_evaluation['score']
    total_improvement = final_score - initial_score

    print(f"Initial Score:  {initial_score}/100 ({evaluation['grade']})")
    print(f"Final Score:    {final_score}/100 ({current_evaluation['grade']})")
    print(f"Improvement:    {total_improvement:+d} points")
    print(f"Iterations:     {iteration}")
    print(f"Status:         {'✅ Success' if final_score >= quality_threshold else '⚠️  Partial'}")
    print()

    print("Score Breakdown:")
    print(f"  Initial → Final")
    for check_name in evaluation['detailed_checks'].keys():
        initial = evaluation['detailed_checks'][check_name]['score']
        final = current_evaluation['detailed_checks'][check_name]['score']
        delta = final - initial
        print(f"  {check_name.replace('_', ' ').title()}: {initial}/100 → {final}/100 ({delta:+d})")
    print()

    if final_score >= quality_threshold:
        print("="*70)
        print("✅ SUCCESS: Content meets quality standards!")
        print("="*70)
        return 0
    else:
        print("="*70)
        print("⚠️  PARTIAL: Content improved but below threshold")
        print("="*70)
        return 0


if __name__ == "__main__":
    sys.exit(main())
