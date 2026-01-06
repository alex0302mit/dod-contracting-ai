#!/usr/bin/env python3
"""
Test script for Phase 2 Agent 1: AcquisitionPlanGeneratorAgent
Tests RAG enhancement and TBD reduction

Baseline: 176 TBDs
Target: ~53 TBDs (70% reduction)
"""

import sys
import os
import re
from pathlib import Path

# Add parent directory to path

from backend.agents.acquisition_plan_generator_agent import AcquisitionPlanGeneratorAgent
from backend.rag.retriever import Retriever
from backend.rag.vector_store import VectorStore

def count_tbds(content: str) -> int:
    """Count TBD occurrences in content"""
    return len(re.findall(r'\bTBD\b', content, re.IGNORECASE))

def main():
    print("="*80)
    print("PHASE 2 AGENT 1: ACQUISITION PLAN GENERATOR - RAG ENHANCEMENT TEST")
    print("="*80)
    print()

    # Get API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("\n❌ ERROR: ANTHROPIC_API_KEY not set")
        print("   Set it with:")
        print("   export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    # Initialize RAG system
    print("Initializing RAG system...")
    vector_store = VectorStore(api_key=api_key)
    vector_store.load()
    retriever = Retriever(vector_store, top_k=5)

    # Get vector store stats
    num_chunks = len(vector_store.chunks) if hasattr(vector_store, 'chunks') else 0
    print(f"  ✓ RAG initialized with {num_chunks} chunks")
    print()

    # Test configuration
    test_task = {
        'project_info': {
            'program_name': 'Advanced Logistics Management System (ALMS)',
            'organization': 'Department of Defense',
            'estimated_value': '$45M',
            'period_of_performance': '12 months base + 4 option years'
        },
        'requirements_content': 'Modern cloud-based logistics system with mobile access',
        'market_research_results': {
            'competitive_landscape': 'Multiple qualified vendors identified',
            'pricing_analysis': 'Market rates established'
        },
        'config': {
            'contract_type': 'services',
            'classification': 'UNCLASSIFIED'
        }
    }

    # Test Agent 1: AcquisitionPlanGeneratorAgent
    print("Testing Agent 1: AcquisitionPlanGeneratorAgent")
    print("-" * 80)

    agent = AcquisitionPlanGeneratorAgent(api_key=api_key, retriever=retriever)

    print("\nGenerating acquisition plan with RAG enhancement...")
    result = agent.execute(test_task)

    # Count TBDs
    tbd_count = count_tbds(result['content'])
    baseline = 176
    reduction_pct = ((baseline - tbd_count) / baseline) * 100

    print("\n" + "="*80)
    print("RESULTS - ACQUISITION PLAN GENERATOR AGENT")
    print("="*80)
    print(f"Baseline TBDs:      {baseline}")
    print(f"Current TBDs:       {tbd_count}")
    print(f"Reduction:          {baseline - tbd_count} TBDs eliminated")
    print(f"Reduction %:        {reduction_pct:.1f}%")
    print(f"Target:             70% reduction (~53 TBDs)")

    if reduction_pct >= 70:
        print(f"✅ SUCCESS: Target achieved! ({reduction_pct:.1f}% >= 70%)")
    elif reduction_pct >= 60:
        print(f"⚠️  CLOSE: Near target ({reduction_pct:.1f}% >= 60%)")
    else:
        print(f"❌ NEEDS WORK: Below target ({reduction_pct:.1f}% < 60%)")

    print("="*80)
    print()

    # Save test output
    output_dir = Path("./output/phase2_tests")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "acquisition_plan_test.md"
    with open(output_path, 'w') as f:
        f.write(result['content'])

    print(f"Test output saved: {output_path}")
    print()

    return {
        'agent': 'AcquisitionPlanGeneratorAgent',
        'baseline': baseline,
        'current': tbd_count,
        'reduction_pct': reduction_pct,
        'target_met': reduction_pct >= 70
    }

if __name__ == '__main__':
    try:
        result = main()
        sys.exit(0 if result['target_met'] else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
