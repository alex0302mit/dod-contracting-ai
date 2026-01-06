#!/usr/bin/env python3
"""
Test script: PWS Orchestrator with QASP Integration
"""

import os
import sys
from pathlib import Path

# Add parent directory to path

from backend.agents.pws_orchestrator import PWSOrchestrator
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever


def main():
    """Test PWS+QASP integration"""

    # Get API keys
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    tavily_api_key = os.environ.get('TAVILY_API_KEY')

    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    # Initialize RAG
    print("Loading vector store...")
    vector_store = VectorStore(api_key)
    if not vector_store.load():
        print("No vector store found")
        sys.exit(1)

    retriever = Retriever(vector_store, top_k=5)

    # Project info
    project_info = {
        "program_name": "Test QASP Integration System",
        "author": "Integration Test",
        "organization": "DOD/ARMY/TEST",
        "date": "10/09/2025",
        "budget": "$1M",
        "period_of_performance": "12 months"
    }

    # PWS sections (minimal for testing)
    sections = [
        {
            "name": "Performance Requirements",
            "guidance": "Define system availability ≥99.9% and response time <2 seconds",
            "focus": "performance"
        },
        {
            "name": "Deliverables",
            "guidance": "Monthly status reports and quarterly reviews",
            "focus": "deliverables"
        }
    ]

    # QASP configuration
    qasp_config = {
        'contracting_officer': 'John Smith',
        'ko_phone': '(410) 555-1234',
        'ko_email': 'john.smith@army.mil',
        'cor_name': 'Jane Doe',
        'cor_phone': '(410) 555-5678',
        'cor_email': 'jane.doe@army.mil',
        'cor_level': 'II'
    }

    # Initialize orchestrator
    print("\nInitializing PWS Orchestrator with QASP integration...")
    orchestrator = PWSOrchestrator(api_key, retriever, tavily_api_key)

    # Execute with QASP generation
    print("\nExecuting PWS workflow with automatic QASP generation...")
    result = orchestrator.execute_pws_workflow(
        project_info=project_info,
        pws_sections_config=sections,
        output_path="outputs/pws/test_integration_pws.md",
        generate_qasp=True,  # Enable QASP generation
        qasp_config=qasp_config
    )

    # Display results
    print("\n" + "="*70)
    print("INTEGRATION TEST RESULTS")
    print("="*70)
    print(f"\n✓ PWS Generated: {result['success']}")
    print(f"  Output: {result['output_path']}")
    print(f"  Time: {result['elapsed_time']:.1f}s")

    if result.get('qasp_result'):
        qasp = result['qasp_result']
        print(f"\n✓ QASP Generated: {qasp.get('success')}")
        print(f"  Output: {qasp.get('output_path')}")
        if qasp.get('pdf_path'):
            print(f"  PDF: {qasp.get('pdf_path')}")
        print(f"  Performance Requirements: {qasp.get('requirements_count')}")
        print(f"  Deliverables: {qasp.get('deliverables_count')}")
    else:
        print("\n⚠ QASP was not generated")

    print("\n" + "="*70)
    print("✅ INTEGRATION TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
