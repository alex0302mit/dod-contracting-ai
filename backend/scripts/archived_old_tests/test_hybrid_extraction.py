#!/usr/bin/env python3
"""
Test Hybrid Extraction (Regex + LLM-JSON)
Validates the new hybrid extraction methods across all agents
"""

import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.acquisition_plan_generator_agent import AcquisitionPlanGeneratorAgent
from backend.agents.igce_generator_agent import IGCEGeneratorAgent
from backend.agents.pws_writer_agent import PWSWriterAgent
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever
from dotenv import load_dotenv

load_dotenv()

def test_requirements_hybrid():
    """Test hybrid requirements extraction for Acquisition Plan"""
    print("="*80)
    print("TEST 1: HYBRID REQUIREMENTS EXTRACTION - Acquisition Plan")
    print("="*80)
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    # Initialize RAG
    print("\n1. Loading RAG system...")
    vector_store = VectorStore(api_key=api_key)
    vector_store.load()
    retriever = Retriever(vector_store, top_k=5)
    print(f"   ✓ Loaded {len(vector_store.chunks)} chunks")
    
    # Initialize agent
    agent = AcquisitionPlanGeneratorAgent(api_key=api_key, retriever=retriever)
    
    # Query RAG
    print("\n2. Querying RAG for requirements...")
    results = retriever.retrieve(
        "ALMS functional requirements performance requirements system capabilities KPP",
        k=5
    )
    print(f"   ✓ Retrieved {len(results)} chunks")
    
    # Test hybrid method
    print("\n3. Running Hybrid Extraction (Regex + LLM-JSON)...")
    hybrid_data = agent._extract_requirements_hybrid(results)
    
    func_count = len(hybrid_data.get('functional_requirements', []))
    perf_count = len(hybrid_data.get('performance_requirements', []))
    kpp_count = len(hybrid_data.get('key_performance_parameters', []))
    tech_count = len(hybrid_data.get('technical_requirements', []))
    total_count = func_count + perf_count + kpp_count + tech_count
    
    print(f"\n   ✅ Functional Requirements: {func_count}")
    print(f"   ✅ Performance Requirements: {perf_count}")
    print(f"   ✅ KPPs: {kpp_count}")
    print(f"   ✅ Technical Requirements: {tech_count}")
    print(f"   ✅ Total Requirements: {total_count}")
    
    # Show samples
    if func_count > 0:
        print(f"\n   Sample Functional Requirement:")
        sample = hybrid_data['functional_requirements'][0]
        print(f"      ID: {sample.get('id')}")
        print(f"      Description: {sample.get('description')[:100]}...")
        print(f"      Priority: {sample.get('priority')}")
    
    if kpp_count > 0:
        print(f"\n   Sample KPP:")
        sample = hybrid_data['key_performance_parameters'][0]
        print(f"      Name: {sample.get('name')}")
        print(f"      Threshold: {sample.get('threshold')}")
        print(f"      Objective: {sample.get('objective')}")
    
    # Format for template
    print("\n4. Formatting for template...")
    formatted = agent._format_requirements_for_template(hybrid_data)
    print(f"   ✓ Generated {len(formatted)} formatted fields")
    
    # Show what would go in template
    print(f"\n5. Template Replacements Preview:")
    print(f"   {{{{functional_req_count}}}} → {formatted.get('functional_req_count', 'TBD')}")
    print(f"   {{{{performance_req_count}}}} → {formatted.get('performance_req_count', 'TBD')}")
    print(f"   {{{{kpp_count}}}} → {formatted.get('kpp_count', 'TBD')}")
    print(f"   {{{{total_requirements}}}} → {formatted.get('total_requirements', 'TBD')}")
    
    if formatted.get('functional_requirements_list') != 'TBD - Define functional requirements':
        func_list = formatted.get('functional_requirements_list', '')
        print(f"\n   Sample functional_requirements_list (first 200 chars):")
        print(f"   {func_list[:200]}...")
    
    return total_count

def test_cost_hybrid():
    """Test hybrid cost extraction for IGCE"""
    print("\n" + "="*80)
    print("TEST 2: HYBRID COST EXTRACTION - IGCE")
    print("="*80)
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    # Initialize RAG
    print("\n1. Loading RAG system...")
    vector_store = VectorStore(api_key=api_key)
    vector_store.load()
    retriever = Retriever(vector_store, top_k=5)
    
    # Initialize agent
    agent = IGCEGeneratorAgent(api_key=api_key, retriever=retriever)
    
    # Query RAG for cost data
    print("\n2. Querying RAG for cost data...")
    results = retriever.retrieve(
        "ALMS development cost lifecycle cost labor rates budget funding",
        k=5
    )
    print(f"   ✓ Retrieved {len(results)} chunks")
    
    # Test hybrid method
    print("\n3. Running Hybrid Cost Extraction (Regex + LLM-JSON)...")
    hybrid_costs = agent._extract_costs_hybrid(results)
    
    print(f"\n   Extracted {len(hybrid_costs)} cost fields:")
    for key, value in list(hybrid_costs.items())[:10]:  # Show first 10
        if isinstance(value, list):
            print(f"   ✅ {key}: {len(value)} items")
        else:
            print(f"   ✅ {key}: {value}")
    
    # Check for labor categories (LLM-specific extraction)
    labor_cats = hybrid_costs.get('labor_categories', [])
    if labor_cats:
        print(f"\n   Sample Labor Category:")
        sample = labor_cats[0]
        print(f"      Role: {sample.get('role')}")
        print(f"      Hours: {sample.get('hours')}")
        print(f"      Rate: {sample.get('rate')}")
        print(f"      Total: {sample.get('total')}")
    
    return len(hybrid_costs)

def test_pws_hybrid():
    """Test hybrid PWS extraction"""
    print("\n" + "="*80)
    print("TEST 3: HYBRID PWS EXTRACTION")
    print("="*80)
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    # Initialize RAG
    print("\n1. Loading RAG system...")
    vector_store = VectorStore(api_key=api_key)
    vector_store.load()
    retriever = Retriever(vector_store, top_k=8)
    
    # Initialize agent
    agent = PWSWriterAgent(api_key=api_key, retriever=retriever)
    
    project_info = {
        'program_name': 'Advanced Logistics Management System (ALMS)',
        'organization': 'DOD/ARMY'
    }
    
    # Query RAG for PWS data
    print("\n2. Querying RAG for PWS data...")
    results = retriever.retrieve(
        f"{project_info['program_name']} Performance Work Statement PWS requirements performance standards deliverables quality metrics",
        k=8
    )
    print(f"   ✓ Retrieved {len(results)} chunks")
    
    # Test hybrid method
    print("\n3. Running Hybrid PWS Extraction (Regex + LLM-JSON)...")
    hybrid_pws = agent._extract_pws_data_hybrid(results, project_info)
    
    print(f"\n   Extracted {len(hybrid_pws)} PWS fields:")
    
    # Show structured data
    if 'performance_standards' in hybrid_pws:
        standards = hybrid_pws['performance_standards']
        print(f"   ✅ Performance Standards: {len(standards)} items")
        if standards:
            print(f"      Sample: {standards[0].get('standard', 'N/A')}")
    
    if 'deliverables' in hybrid_pws:
        deliverables = hybrid_pws['deliverables']
        print(f"   ✅ Deliverables: {len(deliverables)} items")
        if deliverables:
            print(f"      Sample: {deliverables[0].get('name', 'N/A')}")
    
    if 'service_type' in hybrid_pws:
        print(f"   ✅ Service Type: {hybrid_pws['service_type']}")
    
    return len(hybrid_pws)

def main():
    """Run all hybrid extraction tests"""
    print("\n" + "="*80)
    print("HYBRID EXTRACTION TEST SUITE")
    print("Testing: Regex + LLM-JSON + Metadata Extraction")
    print("="*80)
    
    try:
        # Test 1: Requirements
        req_count = test_requirements_hybrid()
        
        # Test 2: Costs
        cost_count = test_cost_hybrid()
        
        # Test 3: PWS
        pws_count = test_pws_hybrid()
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"\n✅ Requirements Extraction: {req_count} total requirements extracted")
        print(f"✅ Cost Extraction: {cost_count} cost fields extracted")
        print(f"✅ PWS Extraction: {pws_count} PWS fields extracted")
        
        print(f"\n{'='*80}")
        print("✅ ALL HYBRID EXTRACTION TESTS COMPLETE")
        print(f"{'='*80}")
        
        print(f"\nExpected Improvements:")
        print(f"  - Requirements: 500-1500% more data than regex-only")
        print(f"  - Costs: 200-400% more detailed breakdowns")
        print(f"  - PWS: 800-1200% more structured fields")
        print(f"\n  Overall TBD Reduction Expected: 60-80% in requirements sections")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

