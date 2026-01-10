"""
Test script for PWS Writer Agent - Phase 2 Agent 2
Validates TBD reduction and output quality
"""

import sys
import os
import re
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.pws_writer_agent import PWSWriterAgent
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever
from dotenv import load_dotenv

load_dotenv()

def count_tbds(content: str) -> int:
    """Count TBD occurrences in content"""
    # Count [placeholder] style TBDs
    placeholder_count = len(re.findall(r'\[.*?\]', content))
    # Count {{template_variable}} style placeholders (unique only)
    template_vars = set(re.findall(r'\{\{([^}]+)\}\}', content))
    template_count = len(template_vars)
    # Count explicit TBD markers
    tbd_count = len(re.findall(r'\bTBD\b', content, re.IGNORECASE))

    # Return count (placeholders + template vars + TBD markers)
    return placeholder_count + template_count + tbd_count

def count_template_tbds():
    """Count TBDs in baseline template"""
    template_path = "templates/performance_work_statement_template.md"
    with open(template_path, 'r') as f:
        content = f.read()
    return count_tbds(content)

def main():
    print("=" * 80)
    print("PWS WRITER AGENT - PHASE 2 AGENT 2 TEST")
    print("=" * 80)

    # Count baseline TBDs
    print("\nSTEP 1: Counting baseline TBDs in template...")
    baseline_tbds = count_template_tbds()
    print(f"  ✓ Baseline TBDs found: {baseline_tbds}")

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

    # Initialize PWS agent
    print("\nSTEP 3: Initializing PWS Writer Agent...")
    agent = PWSWriterAgent(api_key=api_key, retriever=retriever)
    print("  ✓ Agent initialized")

    # Create test task
    print("\nSTEP 4: Running PWS generation...")
    test_task = {
        'project_info': {
            'program_name': 'Advanced Logistics Management System (ALMS)',
            'organization': 'U.S. Army',
            'description': 'Cloud-based logistics inventory management system for Army installations',
            'capability_gap': 'Current 15-year-old system lacks real-time tracking and modern cloud capabilities',
            'num_locations': 15,
            'num_users': 2800,
            'estimated_value': '$45M over 5 years'
        },
        'config': {}
    }

    result = agent.execute(test_task)
    content = result['content']

    # Count TBDs in generated document
    print("\nSTEP 5: Counting TBDs in generated document...")
    current_tbds = count_tbds(content)
    reduction = baseline_tbds - current_tbds
    reduction_pct = (reduction / baseline_tbds) * 100 if baseline_tbds > 0 else 0

    print(f"  ✓ TBDs remaining: {current_tbds}")
    print(f"  ✓ TBDs eliminated: {reduction}")
    print(f"  ✓ Reduction: {reduction_pct:.1f}%")

    # Save output
    output_dir = "output/phase2_tests"
    os.makedirs(output_dir, exist_ok=True)

    output_path = f"{output_dir}/pws_generated.md"
    with open(output_path, 'w') as f:
        f.write(content)
    print(f"\n✓ Generated PWS saved to: {output_path}")

    # Results
    print("\n" + "=" * 80)
    print("RESULTS - PWS WRITER AGENT")
    print("=" * 80)
    print(f"Baseline TBDs:      {baseline_tbds}")
    print(f"Current TBDs:       {current_tbds}")
    print(f"Reduction:          {reduction} TBDs eliminated")
    print(f"Reduction %:        {reduction_pct:.1f}%")
    print(f"Target:             {target_reduction*100}% reduction (~{target_tbds} TBDs)")

    if reduction_pct >= target_reduction * 100:
        print(f"✅ SUCCESS: Target achieved! ({reduction_pct:.1f}% >= {target_reduction*100}%)")
    else:
        print(f"❌ BELOW TARGET: {reduction_pct:.1f}% < {target_reduction*100}%")

    print("=" * 80)

    print(f"\nGeneration Stats:")
    print(f"  - Word Count: {result['word_count']}")
    print(f"  - RAG Extracted: {result['rag_extracted_count']} fields")
    print(f"  - LLM Generated: {result['llm_generated_count']} sections")
    print(f"  - Smart Defaults: {result['smart_defaults_count']} values")
    print(f"  - PBSC Compliance: {result['pbsc_compliance']}/100")

    # Save test report
    with open(f"{output_dir}/pws_test_results.txt", 'w') as f:
        f.write(f"PWS Writer Agent - Test Results\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"\n")
        f.write(f"Baseline TBDs: {baseline_tbds}\n")
        f.write(f"Current TBDs: {current_tbds}\n")
        f.write(f"Reduction: {reduction} TBDs\n")
        f.write(f"Reduction %: {reduction_pct:.1f}%\n")
        f.write(f"Target: {target_reduction*100}%\n")
        f.write(f"Status: {'PASS' if reduction_pct >= target_reduction * 100 else 'FAIL'}\n")
        f.write(f"\n")
        f.write(f"Generation Stats:\n")
        f.write(f"  Word Count: {result['word_count']}\n")
        f.write(f"  RAG Extracted: {result['rag_extracted_count']} fields\n")
        f.write(f"  LLM Generated: {result['llm_generated_count']} sections\n")
        f.write(f"  Smart Defaults: {result['smart_defaults_count']} values\n")
        f.write(f"  PBSC Compliance: {result['pbsc_compliance']}/100\n")

    print(f"\n✓ Test report saved to: {output_dir}/pws_test_results.txt")

if __name__ == "__main__":
    main()
