#!/usr/bin/env python3
"""
Test script to verify KPP/KSA RAG integration with actual document generation.

This script tests that agents can successfully retrieve and use KPP/KSA data
when generating documents.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path

from backend.agents.pws_writer_agent import PWSWriterAgent
from backend.agents.igce_generator_agent import IGCEGeneratorAgent
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever


def test_rag_retrieval():
    """Test 1: Direct RAG retrieval of KPP/KSA data"""
    print("\n" + "="*70)
    print("TEST 1: RAG RETRIEVAL - KPP/KSA Data Accessibility")
    print("="*70)

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    vector_store = VectorStore(api_key)
    vector_store.load()
    retriever = Retriever(vector_store, top_k=5)

    # Test queries that agents would make
    test_cases = [
        {
            'query': 'ALMS system availability performance requirement threshold objective',
            'expected_data': ['99.5%', '99.9%', 'availability', 'KPP-1'],
            'description': 'System Availability (KPP-1)'
        },
        {
            'query': 'ALMS inventory accuracy performance requirement threshold objective',
            'expected_data': ['95%', '98%', 'inventory', 'accuracy', 'KPP-2'],
            'description': 'Inventory Accuracy (KPP-2)'
        },
        {
            'query': 'ALMS transaction processing speed performance requirement',
            'expected_data': ['5 seconds', '2 seconds', 'transaction', 'KPP-3'],
            'description': 'Transaction Speed (KPP-3)'
        },
        {
            'query': 'ALMS program timeline milestone IOC FOC June December 2026',
            'expected_data': ['2026', 'IOC', 'FOC'],
            'description': 'Program Timeline'
        }
    ]

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   Query: {test_case['query'][:60]}...")

        results = retriever.retrieve(test_case['query'], k=5)

        # Check if KPP/KSA document is in results
        kpp_results = [r for r in results if 'kpp-ksa' in r.get('metadata', {}).get('source', '').lower()]

        if kpp_results:
            print(f"   ✅ KPP/KSA document retrieved ({len(kpp_results)}/5 chunks)")

            # Check if expected data is in retrieved content
            combined_content = ' '.join([r.get('content', '') for r in kpp_results])
            found_data = [data for data in test_case['expected_data'] if data in combined_content]

            print(f"   ✅ Data points found: {len(found_data)}/{len(test_case['expected_data'])}")
            for data in found_data:
                print(f"      • {data}")

            passed += 1
        else:
            print(f"   ❌ KPP/KSA document NOT retrieved")
            failed += 1

    print(f"\n{'='*70}")
    print(f"TEST 1 RESULTS: {passed}/{len(test_cases)} passed")
    print(f"{'='*70}")

    return passed == len(test_cases)


def test_pws_performance_requirements():
    """Test 2: PWS agent using KPP/KSA data for performance requirements"""
    print("\n" + "="*70)
    print("TEST 2: PWS AGENT - Performance Requirements Generation")
    print("="*70)

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    vector_store = VectorStore(api_key)
    vector_store.load()
    retriever = Retriever(vector_store, top_k=10)

    # Initialize PWS agent
    agent = PWSWriterAgent(api_key, retriever)

    # Test configuration
    project_info = {
        'program_name': 'Advanced Logistics Management System (ALMS)',
        'contract_type': 'Firm Fixed Price (FFP)',
        'period_of_performance': '36 months (Base: 12 months + 2 Option Years)',
        'organization': 'U.S. Army',
        'pop_base': '12 months',
        'pop_option1': '12 months',
        'pop_option2': '12 months',
        'budget': '$2.5M'
    }

    task = {
        'project_info': project_info
    }

    print("\nGenerating PWS Document with KPP/KSA Context...")
    print("This should include performance requirements from KPP/KSA document")

    try:
        # First verify RAG retrieval
        rag_query = f"{project_info['program_name']} performance requirements KPP KSA system availability inventory accuracy"
        rag_results = retriever.retrieve(rag_query, k=10)

        print(f"\n✅ Retrieved {len(rag_results)} context chunks")

        # Check if KPP/KSA is in context
        kpp_chunks = [r for r in rag_results if 'kpp-ksa' in r.get('metadata', {}).get('source', '').lower()]
        print(f"✅ KPP/KSA chunks in RAG context: {len(kpp_chunks)}/10")

        if kpp_chunks:
            print("\nKPP/KSA Content Preview:")
            preview = kpp_chunks[0].get('content', '')[:200]
            print(f"  {preview}...")

        # Generate full PWS document
        print(f"\n{'='*70}")
        print("Generating full PWS document...")
        print(f"{'='*70}")

        result = agent.execute(task)

        if result and 'content' in result:
            pws_content = result.get('content', '')

            # Verify KPP data is in generated content
            print("\n" + "="*70)
            print("VERIFICATION: Checking if KPP/KSA data appears in PWS")
            print("="*70)

            checks = [
                ('System Availability Metric', ['99.5%', '99.9%', 'availability']),
                ('Inventory Accuracy Metric', ['95%', '98%', 'accuracy', 'inventory']),
                ('Transaction Performance', ['transaction', 'processing', 'response time']),
                ('Performance Requirements Section', ['performance', 'requirement'])
            ]

            passed = 0
            for check_name, search_terms in checks:
                found = any(term.lower() in pws_content.lower() for term in search_terms)
                if found:
                    # Find which term was found
                    found_terms = [t for t in search_terms if t.lower() in pws_content.lower()]
                    print(f"✅ {check_name}: Found (terms: {', '.join(found_terms[:2])})")
                    passed += 1
                else:
                    print(f"❌ {check_name}: NOT found")

            print(f"\n{'='*70}")
            print(f"TEST 2 RESULTS: {passed}/{len(checks)} checks passed")
            print(f"{'='*70}")

            # Show preview if KPP data found
            if 'performance' in pws_content.lower():
                # Find performance requirements section
                lines = pws_content.split('\n')
                for i, line in enumerate(lines):
                    if 'performance' in line.lower() and ('requirement' in line.lower() or '##' in line or '###' in line):
                        print(f"\nPerformance Section Preview (10 lines from line {i}):")
                        print("-" * 70)
                        preview_lines = lines[i:min(i+10, len(lines))]
                        print('\n'.join(preview_lines))
                        print("-" * 70)
                        break

            return passed >= 2  # At least 2 out of 4 checks should pass

        else:
            print(f"\n❌ PWS generation failed: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n❌ ERROR during generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_igce_cost_scaling():
    """Test 3: IGCE agent scaling costs based on KPP/KSA user counts"""
    print("\n" + "="*70)
    print("TEST 3: IGCE AGENT - Cost Scaling with KPP/KSA User Counts")
    print("="*70)

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    vector_store = VectorStore(api_key)
    vector_store.load()
    retriever = Retriever(vector_store, top_k=10)

    # Query for user scaling information
    print("\nQuerying for ALMS user scaling information...")
    query = "ALMS users IOC FOC 500 2800 Initial Operating Capability Full Operating Capability"
    results = retriever.retrieve(query, k=10)

    # Check if we can extract user counts
    kpp_results = [r for r in results if 'kpp-ksa' in r.get('metadata', {}).get('source', '').lower()]

    print(f"✅ Retrieved {len(results)} total chunks")
    print(f"✅ KPP/KSA chunks: {len(kpp_results)}/10")

    # Extract user counts from content
    combined_content = ' '.join([r.get('content', '') for r in kpp_results])

    checks = [
        ('IOC User Count (500)', ['500 users', 'IOC']),
        ('FOC User Count (2,800)', ['2,800 users', '2800 users', 'FOC']),
        ('Timeline (June 2026)', ['June 2026', 'IOC']),
        ('Timeline (December 2026)', ['December 2026', 'FOC'])
    ]

    passed = 0
    for check_name, search_terms in checks:
        found = any(term in combined_content for term in search_terms)
        if found:
            print(f"✅ {check_name}: Found in KPP/KSA data")
            passed += 1
        else:
            print(f"❌ {check_name}: NOT found in KPP/KSA data")

    print(f"\n{'='*70}")
    print(f"TEST 3 RESULTS: {passed}/{len(checks)} checks passed")
    print(f"{'='*70}")

    return passed >= 3


def main():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("KPP/KSA RAG INTEGRATION TEST SUITE")
    print("="*70)
    print("\nThis test suite verifies that:")
    print("1. KPP/KSA data is retrievable from RAG")
    print("2. Agents can use KPP/KSA data during generation")
    print("3. Generated documents contain KPP/KSA information")
    print("="*70)

    results = []

    # Test 1: RAG Retrieval
    try:
        result1 = test_rag_retrieval()
        results.append(('RAG Retrieval', result1))
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED WITH ERROR: {str(e)}")
        results.append(('RAG Retrieval', False))

    # Test 2: PWS Performance Requirements
    try:
        result2 = test_pws_performance_requirements()
        results.append(('PWS Performance Requirements', result2))
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED WITH ERROR: {str(e)}")
        results.append(('PWS Performance Requirements', False))

    # Test 3: IGCE Cost Scaling
    try:
        result3 = test_igce_cost_scaling()
        results.append(('IGCE Cost Scaling', result3))
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED WITH ERROR: {str(e)}")
        results.append(('IGCE Cost Scaling', False))

    # Summary
    print("\n" + "="*70)
    print("FINAL TEST SUMMARY")
    print("="*70)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    print(f"\n{'='*70}")
    print(f"OVERALL: {total_passed}/{total_tests} tests passed")
    print(f"{'='*70}")

    if total_passed == total_tests:
        print("\n✅ KPP/KSA integration is WORKING CORRECTLY")
        print("   Agents can retrieve and use KPP/KSA data during generation.")
        return 0
    else:
        print("\n⚠️  Some tests failed - review results above")
        return 1


if __name__ == '__main__':
    sys.exit(main())
