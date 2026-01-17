#!/usr/bin/env python3
"""
Diagnostic script to examine what RAG retrieval returns.
This will help us understand the actual format of retrieved chunks.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever

def main():
    print("="*70)
    print("RAG EXTRACTION DIAGNOSTIC TOOL")
    print("="*70)
    print()

    # Initialize RAG
    print("1. Initializing RAG system...")
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not set")
        return 1

    vector_store = VectorStore(api_key=api_key)
    vector_store.load()
    retriever = Retriever(vector_store, top_k=5)
    print(f"   ✓ Loaded {len(vector_store.chunks)} chunks")
    print()

    # Test queries from IGCE agent
    print("2. Testing IGCE cost extraction queries...")
    print()

    queries = [
        ("Budget and Development Costs",
         "ALMS Advanced Logistics Management System budget development costs estimated total cost contract value"),
        ("Labor Rates",
         "ALMS labor rates hourly rates contractor rates FTE costs personnel costs"),
        ("Sustainment Costs",
         "ALMS sustainment costs operations maintenance O&M annual costs recurring costs"),
        ("Schedule Milestones",
         "ALMS schedule timeline milestones phases contract period base period option years"),
    ]

    for query_name, query_text in queries:
        print(f"{'='*70}")
        print(f"Query: {query_name}")
        print(f"{'='*70}")
        print()

        # Retrieve chunks
        results = retriever.retrieve(query_text, k=3)

        if not results:
            print("❌ No results returned")
            print()
            continue

        print(f"✓ Retrieved {len(results)} chunks")
        print()

        # Display each chunk
        for i, result in enumerate(results, 1):
            print(f"--- Chunk {i} (score: {result.get('score', 'N/A'):.4f}) ---")
            print()

            # Show metadata
            metadata = result.get('metadata', {})
            if metadata:
                print(f"Source: {metadata.get('source', 'Unknown')}")
                print(f"Section: {metadata.get('section', 'Unknown')}")
                print()

            # Show content (first 500 chars)
            content = result.get('content', '')
            if len(content) > 500:
                print(content[:500] + "...")
            else:
                print(content)
            print()

        print()

    # Test queries from SSP agent
    print()
    print("="*70)
    print("3. Testing SSP organizational queries...")
    print("="*70)
    print()

    ssp_queries = [
        ("SSA and Organizational Structure",
         "Source Selection Authority SSA contracting officer PCO designation roles responsibilities organizational structure"),
        ("Team Composition",
         "SSEB Source Selection Evaluation Board SSAC committee team members composition technical evaluator cost analyst"),
    ]

    for query_name, query_text in ssp_queries:
        print(f"{'='*70}")
        print(f"Query: {query_name}")
        print(f"{'='*70}")
        print()

        results = retriever.retrieve(query_text, k=3)

        if not results:
            print("❌ No results returned")
            print()
            continue

        print(f"✓ Retrieved {len(results)} chunks")
        print()

        for i, result in enumerate(results, 1):
            print(f"--- Chunk {i} (score: {result.get('score', 'N/A'):.4f}) ---")
            print()

            metadata = result.get('metadata', {})
            if metadata:
                print(f"Source: {metadata.get('source', 'Unknown')}")
                print()

            content = result.get('content', '')
            if len(content) > 500:
                print(content[:500] + "...")
            else:
                print(content)
            print()

        print()

    print("="*70)
    print("DIAGNOSTIC COMPLETE")
    print("="*70)
    print()
    print("Use this output to understand:")
    print("1. What format the data is in (narrative vs. structured)")
    print("2. Whether specific values exist or just guidance")
    print("3. How to write extraction patterns that will match")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
