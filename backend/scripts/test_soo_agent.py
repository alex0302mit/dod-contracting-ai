"""
Test script for SOO Writer Agent - Phase 2 Agent 4
Validates SMART objectives, citation density, and outcome focus
"""

import sys
import os
import re
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.soo_writer_agent import SOOWriterAgent
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever
from dotenv import load_dotenv

load_dotenv()

# SMART criteria patterns
SMART_PATTERNS = {
    'specific': r'\b(shall|must|will)\b.*\b(deliver|provide|achieve|maintain|develop)\b',
    'measurable': r'\d+\s*(percent|%|users|systems|hours|days|months)',
    'achievable': r'\b(within|by|during|no later than)\b',
    'relevant': r'\b(mission|requirement|objective|goal|capability)\b',
    'timebound': r'\b(by|within|during|until)\s+\w+\s+\d{4}|\d+\s+(day|week|month|year)s?'
}

def count_smart_elements(content: str) -> dict:
    """Count SMART objective elements"""
    smart_counts = {}
    for criterion, pattern in SMART_PATTERNS.items():
        matches = re.findall(pattern, content, re.IGNORECASE)
        smart_counts[criterion] = len(matches) > 0

    smart_score = (sum(smart_counts.values()) / len(smart_counts)) * 100
    return {'score': smart_score, 'elements': smart_counts}

def count_objectives(content: str) -> int:
    """Count number of objectives stated"""
    # Match patterns like "Objective 1:", "1.", numbered lists
    objective_patterns = [
        r'Objective\s+\d+',
        r'^\d+\.\s+[A-Z]',  # Numbered list
        r'^\*\*Objective',   # Bold objective
    ]

    total = 0
    for pattern in objective_patterns:
        matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
        total += len(matches)

    return max(total, 1)  # At least 1 objective

def evaluate_outcome_focus(content: str) -> dict:
    """Evaluate whether content focuses on outcomes vs methods"""
    # Outcome-focused language
    outcome_terms = [
        r'\b(achieve|accomplish|deliver|result|outcome|capability|performance)\b',
        r'\b(meet|exceed|satisfy|fulfill)\s+\w+\s+(requirement|standard|objective)\b',
    ]

    # Method/HOW language (should be minimal in SOO)
    method_terms = [
        r'\b(use|utilize|implement|execute|perform)\s+(the following|these|specific)\b',
        r'\b(step|procedure|process|method|technique)\b',
    ]

    outcome_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) for pattern in outcome_terms)
    method_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) for pattern in method_terms)

    # Good SOO should have high outcome/method ratio
    if method_count == 0:
        ratio = outcome_count
    else:
        ratio = outcome_count / method_count

    outcome_focused = ratio > 2  # At least 2:1 outcome to method ratio

    return {
        'outcome_count': outcome_count,
        'method_count': method_count,
        'ratio': ratio,
        'outcome_focused': outcome_focused
    }

def count_citations(content: str) -> int:
    """Count inline citations in content"""
    citation_pattern = r'\([A-Z][^)]*(?:20\d{2}|v\d+|FY\d{4}|[A-Z][a-z]+ \d{4})[^)]*\)'
    citations = re.findall(citation_pattern, content)
    return len(citations)

def analyze_section(section_name: str, content: str) -> dict:
    """Comprehensive analysis of an SOO section"""
    word_count = len(content.split())
    citation_count = count_citations(content)
    objectives_count = count_objectives(content)
    smart_analysis = count_smart_elements(content)
    outcome_analysis = evaluate_outcome_focus(content)

    # Calculate citation density (citations per 100 words)
    citation_density = (citation_count / word_count * 100) if word_count > 0 else 0

    return {
        'section_name': section_name,
        'word_count': word_count,
        'citation_count': citation_count,
        'citation_density': citation_density,
        'objectives_count': objectives_count,
        'smart_score': smart_analysis['score'],
        'smart_elements': smart_analysis['elements'],
        'outcome_count': outcome_analysis['outcome_count'],
        'method_count': outcome_analysis['method_count'],
        'outcome_ratio': outcome_analysis['ratio'],
        'outcome_focused': outcome_analysis['outcome_focused']
    }

def print_analysis(analysis: dict, label: str = ""):
    """Print analysis results"""
    if label:
        print(f"\n{'='*80}")
        print(f"{label}")
        print('='*80)

    print(f"Section: {analysis['section_name']}")
    print(f"Word Count: {analysis['word_count']}")
    print(f"Objectives: {analysis['objectives_count']}")
    print(f"Citations: {analysis['citation_count']} (density: {analysis['citation_density']:.1f} per 100 words)")
    print(f"SMART Score: {analysis['smart_score']:.1f}%")
    print(f"  Elements present:")
    for element, present in analysis['smart_elements'].items():
        status = '✅' if present else '❌'
        print(f"    {status} {element.title()}")
    print(f"Outcome Focus:")
    print(f"  Outcome terms: {analysis['outcome_count']}")
    print(f"  Method terms: {analysis['method_count']}")
    print(f"  Ratio: {analysis['outcome_ratio']:.1f}:1")
    print(f"  Status: {'✅ Outcome-focused' if analysis['outcome_focused'] else '❌ Too prescriptive'}")

def main():
    print("="*80)
    print("SOO WRITER AGENT - PHASE 2 AGENT 4 BASELINE TEST")
    print("="*80)

    # Initialize RAG system
    print("\nSTEP 1: Initializing RAG system...")
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in environment")
        return

    vector_store = VectorStore(api_key=api_key)
    vector_store.load()
    retriever = Retriever(vector_store, top_k=5)
    print("  ✓ RAG system loaded")

    # Initialize SOO agent
    print("\nSTEP 2: Initializing SOO Writer Agent...")
    agent = SOOWriterAgent(api_key=api_key, retriever=retriever)
    print("  ✓ Agent initialized")

    # Test project info
    project_info = {
        'program_name': 'Advanced Logistics Management System (ALMS)',
        'organization': 'U.S. Army',
        'budget': '$45 million',
        'period_of_performance': '36 months',
        'service_description': 'Cloud-based logistics inventory management system',
        'num_locations': 15,
        'num_users': 2800,
        'date': 'October 2025'
    }

    # Test sections (3 representative sections)
    test_sections = [
        {
            'name': '1. Performance Objectives',
            'guidance': 'State measurable outcomes and performance standards',
            'focus': 'performance'
        },
        {
            'name': '2. Required Capabilities',
            'guidance': 'Define capabilities the solution must provide',
            'focus': 'capabilities'
        },
        {
            'name': '3. Acceptance Criteria',
            'guidance': 'Specify how success will be measured',
            'focus': 'metrics'
        }
    ]

    print("\nSTEP 3: Generating SOO sections (baseline)...")
    results = []

    for i, section_config in enumerate(test_sections, 1):
        print(f"\n  Generating section {i}/3: {section_config['name']}...")

        task = {
            'section_name': section_config['name'],
            'project_info': project_info,
            'guidance': section_config['guidance'],
            'focus': section_config['focus']
        }

        result = agent.execute(task)
        content = result['content']

        # Analyze section
        analysis = analyze_section(section_config['name'], content)
        results.append({
            'config': section_config,
            'result': result,
            'analysis': analysis
        })

        print(f"    ✓ Generated {analysis['word_count']} words")
        print(f"    ✓ Objectives: {analysis['objectives_count']}")
        print(f"    ✓ Citations: {analysis['citation_count']}")
        print(f"    ✓ SMART score: {analysis['smart_score']:.1f}%")
        print(f"    ✓ Outcome-focused: {'Yes' if analysis['outcome_focused'] else 'No'}")

    # Calculate aggregate metrics
    print("\n" + "="*80)
    print("BASELINE RESULTS - AGGREGATE METRICS")
    print("="*80)

    total_words = sum(r['analysis']['word_count'] for r in results)
    total_citations = sum(r['analysis']['citation_count'] for r in results)
    avg_citation_density = sum(r['analysis']['citation_density'] for r in results) / len(results)
    total_objectives = sum(r['analysis']['objectives_count'] for r in results)
    avg_smart_score = sum(r['analysis']['smart_score'] for r in results) / len(results)
    outcome_focused_count = sum(1 for r in results if r['analysis']['outcome_focused'])

    print(f"\nTotal Words: {total_words}")
    print(f"Total Citations: {total_citations}")
    print(f"Average Citations per Section: {total_citations / len(results):.1f}")
    print(f"Average Citation Density: {avg_citation_density:.1f} per 100 words")
    print(f"Total Objectives: {total_objectives}")
    print(f"Average SMART Score: {avg_smart_score:.1f}%")
    print(f"Outcome-Focused Sections: {outcome_focused_count}/{len(results)}")

    # Target metrics
    print("\n" + "="*80)
    print("TARGET METRICS FOR ENHANCEMENT")
    print("="*80)

    target_citations_per_section = 6
    target_smart_score = 80
    target_outcome_focused = 100  # All sections should be outcome-focused

    print(f"\nCitation Target: {target_citations_per_section} per section")
    print(f"  Current: {total_citations / len(results):.1f}")
    print(f"  Gap: {target_citations_per_section - (total_citations / len(results)):.1f}")
    print(f"  Status: {'✅ MET' if total_citations / len(results) >= target_citations_per_section else '❌ BELOW TARGET'}")

    print(f"\nSMART Score Target: {target_smart_score}%")
    print(f"  Current: {avg_smart_score:.1f}%")
    print(f"  Gap: {target_smart_score - avg_smart_score:.1f}%")
    print(f"  Status: {'✅ MET' if avg_smart_score >= target_smart_score else '❌ BELOW TARGET'}")

    outcome_pct = (outcome_focused_count / len(results)) * 100
    print(f"\nOutcome Focus Target: {target_outcome_focused}%")
    print(f"  Current: {outcome_pct:.1f}%")
    print(f"  Gap: {target_outcome_focused - outcome_pct:.1f}%")
    print(f"  Status: {'✅ MET' if outcome_pct >= target_outcome_focused else '❌ BELOW TARGET'}")

    # Detailed section analysis
    print("\n" + "="*80)
    print("DETAILED SECTION ANALYSIS")
    print("="*80)

    for i, r in enumerate(results, 1):
        print_analysis(r['analysis'], f"Section {i}: {r['config']['name']}")

    # Save results
    output_dir = "output/phase2_tests"
    os.makedirs(output_dir, exist_ok=True)

    # Save baseline report
    with open(f"{output_dir}/soo_baseline_report.txt", 'w') as f:
        f.write("SOO Writer Agent - Baseline Analysis\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n")
        f.write("AGGREGATE METRICS:\n")
        f.write(f"  Average Citations per Section: {total_citations / len(results):.1f}\n")
        f.write(f"  Average Citation Density: {avg_citation_density:.1f} per 100 words\n")
        f.write(f"  Average SMART Score: {avg_smart_score:.1f}%\n")
        f.write(f"  Outcome-Focused Sections: {outcome_focused_count}/{len(results)} ({outcome_pct:.1f}%)\n")
        f.write("\n")
        f.write("TARGET GAPS:\n")
        f.write(f"  Citations: {max(0, target_citations_per_section - (total_citations / len(results))):.1f} gap\n")
        f.write(f"  SMART Score: {max(0, target_smart_score - avg_smart_score):.1f}% gap\n")
        f.write(f"  Outcome Focus: {max(0, target_outcome_focused - outcome_pct):.1f}% gap\n")

    # Save generated sections
    for i, r in enumerate(results, 1):
        section_file = f"{output_dir}/soo_baseline_section_{i}.md"
        with open(section_file, 'w') as f:
            f.write(f"# {r['config']['name']}\n\n")
            f.write(r['result']['content'])
            f.write(f"\n\n---\n\n")
            f.write(f"**Analysis:**\n")
            f.write(f"- Word Count: {r['analysis']['word_count']}\n")
            f.write(f"- Objectives: {r['analysis']['objectives_count']}\n")
            f.write(f"- Citations: {r['analysis']['citation_count']}\n")
            f.write(f"- SMART Score: {r['analysis']['smart_score']:.1f}%\n")
            f.write(f"- Outcome-Focused: {'Yes' if r['analysis']['outcome_focused'] else 'No'}\n")

    print(f"\n✓ Baseline report saved to: {output_dir}/soo_baseline_report.txt")
    print(f"✓ Generated sections saved to: {output_dir}/soo_baseline_section_*.md")

if __name__ == "__main__":
    main()
