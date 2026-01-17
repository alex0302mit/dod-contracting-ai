"""
Test script for SOW Writer Agent - Phase 2 Agent 3
Validates citation density, completeness, and vague language reduction
"""

import sys
import os
import re
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.sow_writer_agent import SOWWriterAgent
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever
from dotenv import load_dotenv

load_dotenv()

# Vague language patterns to detect
VAGUE_TERMS = [
    r'\bseveral\b', r'\bmany\b', r'\bsome\b', r'\bvarious\b',
    r'\bas needed\b', r'\bas required\b', r'\bapproximately\b',
    r'\baround\b', r'\babout\b', r'\badequate\b', r'\bsufficient\b',
    r'\bappropriate\b', r'\breasonable\b', r'\bsatisfactory\b',
    r'\btimely\b', r'\bprompt\b', r'\bexpeditiously\b', r'\bsoon\b',
    r'\bASAP\b', r'\bhigh quality\b', r'\bbest effort\b',
    r'\bindustry standard\b', r'\bcoordinate with\b', r'\bwork with\b',
    r'\bassist\b'
]

def count_citations(content: str) -> int:
    """Count inline citations in content"""
    # Match patterns like (Source, Date) or (Source, Version)
    citation_pattern = r'\([A-Z][^)]*(?:20\d{2}|v\d+|FY\d{4}|[A-Z][a-z]+ \d{4})[^)]*\)'
    citations = re.findall(citation_pattern, content)
    return len(citations)

def count_vague_language(content: str) -> dict:
    """Count instances of vague language"""
    vague_counts = {}
    total = 0

    for pattern in VAGUE_TERMS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            count = len(matches)
            vague_counts[pattern.replace('\\b', '')] = count
            total += count

    return {'total': total, 'by_term': vague_counts}

def evaluate_completeness(content: str, section_name: str) -> dict:
    """Evaluate section completeness based on required elements"""
    checklist = {
        'has_citations': count_citations(content) > 0,
        'has_specific_metrics': bool(re.search(r'\d+', content)),
        'uses_shall_language': bool(re.search(r'\bshall\b', content, re.IGNORECASE)),
        'no_excessive_vague': count_vague_language(content)['total'] <= 5,
        'sufficient_length': len(content.split()) >= 100,
    }

    # Section-specific checks
    if 'scope' in section_name.lower():
        checklist['defines_boundaries'] = bool(re.search(r'\b(includ|exclud|bound|limit)', content, re.IGNORECASE))

    if 'task' in section_name.lower():
        checklist['enumerates_tasks'] = bool(re.search(r'(shall perform|shall deliver|shall provide)', content, re.IGNORECASE))

    if 'deliverable' in section_name.lower():
        checklist['specifies_format'] = bool(re.search(r'\b(format|document|report)', content, re.IGNORECASE))
        checklist['specifies_schedule'] = bool(re.search(r'\b(day|week|month|deadline)', content, re.IGNORECASE))

    score = (sum(checklist.values()) / len(checklist)) * 100

    return {
        'score': score,
        'checklist': checklist,
        'passed': score >= 70
    }

def analyze_section(section_name: str, content: str) -> dict:
    """Comprehensive analysis of a section"""
    word_count = len(content.split())
    citation_count = count_citations(content)
    vague_analysis = count_vague_language(content)
    completeness = evaluate_completeness(content, section_name)

    # Calculate citation density (citations per 100 words)
    citation_density = (citation_count / word_count * 100) if word_count > 0 else 0

    return {
        'section_name': section_name,
        'word_count': word_count,
        'citation_count': citation_count,
        'citation_density': citation_density,
        'vague_language_total': vague_analysis['total'],
        'vague_language_by_term': vague_analysis['by_term'],
        'completeness_score': completeness['score'],
        'completeness_checklist': completeness['checklist'],
        'completeness_passed': completeness['passed']
    }

def print_analysis(analysis: dict, label: str = ""):
    """Print analysis results"""
    if label:
        print(f"\n{'='*80}")
        print(f"{label}")
        print('='*80)

    print(f"Section: {analysis['section_name']}")
    print(f"Word Count: {analysis['word_count']}")
    print(f"Citations: {analysis['citation_count']} (density: {analysis['citation_density']:.1f} per 100 words)")
    print(f"Vague Language: {analysis['vague_language_total']} instances")

    if analysis['vague_language_by_term']:
        print("  Breakdown:")
        for term, count in analysis['vague_language_by_term'].items():
            print(f"    - {term}: {count}")

    print(f"Completeness: {analysis['completeness_score']:.1f}% {'✅ PASS' if analysis['completeness_passed'] else '❌ FAIL'}")
    print(f"  Checklist:")
    for item, passed in analysis['completeness_checklist'].items():
        status = '✅' if passed else '❌'
        print(f"    {status} {item.replace('_', ' ').title()}")

def main():
    print("="*80)
    print("SOW WRITER AGENT - PHASE 2 AGENT 3 BASELINE TEST")
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

    # Initialize SOW agent
    print("\nSTEP 2: Initializing SOW Writer Agent...")
    agent = SOWWriterAgent(api_key=api_key, retriever=retriever)
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
            'name': '1. Scope of Work',
            'requirements': 'Define the boundaries and extent of services to be provided, including inclusions and exclusions',
            'context': {}
        },
        {
            'name': '2. Tasks and Responsibilities',
            'requirements': 'List all tasks the contractor shall perform, with specific deliverables and timelines',
            'context': {}
        },
        {
            'name': '3. Deliverables',
            'requirements': 'Specify all deliverables including format, schedule, and acceptance criteria',
            'context': {}
        }
    ]

    print("\nSTEP 3: Generating SOW sections (baseline)...")
    results = []

    for i, section_config in enumerate(test_sections, 1):
        print(f"\n  Generating section {i}/3: {section_config['name']}...")

        task = {
            'section_name': section_config['name'],
            'project_info': project_info,
            'requirements': section_config['requirements'],
            'context': section_config['context']
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
        print(f"    ✓ Citations: {analysis['citation_count']}")
        print(f"    ✓ Vague language: {analysis['vague_language_total']} instances")
        print(f"    ✓ Completeness: {analysis['completeness_score']:.1f}%")

    # Calculate aggregate metrics
    print("\n" + "="*80)
    print("BASELINE RESULTS - AGGREGATE METRICS")
    print("="*80)

    total_words = sum(r['analysis']['word_count'] for r in results)
    total_citations = sum(r['analysis']['citation_count'] for r in results)
    avg_citation_density = sum(r['analysis']['citation_density'] for r in results) / len(results)
    total_vague = sum(r['analysis']['vague_language_total'] for r in results)
    avg_vague_per_section = total_vague / len(results)
    avg_completeness = sum(r['analysis']['completeness_score'] for r in results) / len(results)

    print(f"\nTotal Words: {total_words}")
    print(f"Total Citations: {total_citations}")
    print(f"Average Citations per Section: {total_citations / len(results):.1f}")
    print(f"Average Citation Density: {avg_citation_density:.1f} per 100 words")
    print(f"Total Vague Language: {total_vague} instances")
    print(f"Average Vague Language per Section: {avg_vague_per_section:.1f}")
    print(f"Average Completeness Score: {avg_completeness:.1f}%")

    # Target metrics
    print("\n" + "="*80)
    print("TARGET METRICS FOR ENHANCEMENT")
    print("="*80)

    target_citations_per_section = 6
    target_completeness = 95
    target_vague_per_section = 2

    print(f"\nCitation Target: {target_citations_per_section} per section")
    print(f"  Current: {total_citations / len(results):.1f}")
    print(f"  Gap: {target_citations_per_section - (total_citations / len(results)):.1f}")
    print(f"  Status: {'✅ MET' if total_citations / len(results) >= target_citations_per_section else '❌ BELOW TARGET'}")

    print(f"\nCompleteness Target: {target_completeness}%")
    print(f"  Current: {avg_completeness:.1f}%")
    print(f"  Gap: {target_completeness - avg_completeness:.1f}%")
    print(f"  Status: {'✅ MET' if avg_completeness >= target_completeness else '❌ BELOW TARGET'}")

    print(f"\nVague Language Target: ≤{target_vague_per_section} per section")
    print(f"  Current: {avg_vague_per_section:.1f}")
    print(f"  Gap: {avg_vague_per_section - target_vague_per_section:.1f} (reduce by this amount)")
    print(f"  Status: {'✅ MET' if avg_vague_per_section <= target_vague_per_section else '❌ ABOVE TARGET'}")

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
    with open(f"{output_dir}/sow_baseline_report.txt", 'w') as f:
        f.write("SOW Writer Agent - Baseline Analysis\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n")
        f.write("AGGREGATE METRICS:\n")
        f.write(f"  Average Citations per Section: {total_citations / len(results):.1f}\n")
        f.write(f"  Average Citation Density: {avg_citation_density:.1f} per 100 words\n")
        f.write(f"  Average Vague Language: {avg_vague_per_section:.1f} per section\n")
        f.write(f"  Average Completeness: {avg_completeness:.1f}%\n")
        f.write("\n")
        f.write("TARGET GAPS:\n")
        f.write(f"  Citations: Need +{target_citations_per_section - (total_citations / len(results)):.1f} per section\n")
        f.write(f"  Completeness: Need +{target_completeness - avg_completeness:.1f}%\n")
        f.write(f"  Vague Language: Need -{avg_vague_per_section - target_vague_per_section:.1f} per section\n")

    # Save generated sections
    for i, r in enumerate(results, 1):
        section_file = f"{output_dir}/sow_baseline_section_{i}.md"
        with open(section_file, 'w') as f:
            f.write(f"# {r['config']['name']}\n\n")
            f.write(r['result']['content'])
            f.write(f"\n\n---\n\n")
            f.write(f"**Analysis:**\n")
            f.write(f"- Word Count: {r['analysis']['word_count']}\n")
            f.write(f"- Citations: {r['analysis']['citation_count']}\n")
            f.write(f"- Vague Language: {r['analysis']['vague_language_total']}\n")
            f.write(f"- Completeness: {r['analysis']['completeness_score']:.1f}%\n")

    print(f"\n✓ Baseline report saved to: {output_dir}/sow_baseline_report.txt")
    print(f"✓ Generated sections saved to: {output_dir}/sow_baseline_section_*.md")

if __name__ == "__main__":
    main()
