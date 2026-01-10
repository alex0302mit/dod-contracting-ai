"""
Quick test script for RAG system
Tests retrieval with sample queries
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever

def test_rag_system():
    """Test RAG retrieval with sample queries"""
    
    load_dotenv()
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not set")
        return False
    
    print("="*70)
    print("RAG SYSTEM TEST")
    print("="*70)
    print()
    
    # Initialize vector store
    print("Loading vector store...")
    vector_store = VectorStore(api_key=api_key)
    
    if not vector_store.load():
        print("❌ No vector store found. Run setup_rag_system.py first.")
        return False
    
    print(f"✓ Loaded vector store with {len(vector_store.chunks)} chunks")
    print()
    
    # Initialize retriever
    retriever = Retriever(vector_store, top_k=3)
    
    # Test queries
    test_queries = [
        "small business set-aside requirements",
        "GSA schedule contract vehicles",
        "market research methods",
        "FAR regulations"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {query}")
        print('='*70)
        
        results = retriever.retrieve(query, k=3)
        
        if not results:
            print("⚠️  No results found")
            continue
        
        print(f"\nFound {len(results)} results:")
        for j, doc in enumerate(results, 1):
            print(f"\n{j}. Source: {doc['metadata']['source']}")
            print(f"   Score: {doc.get('score', 'N/A')}")
            print(f"   Preview: {doc['content'][:200]}...")
    
    print("\n" + "="*70)
    print("✅ RAG SYSTEM TEST COMPLETE")
    print("="*70)
    print()
    print("System is working! You can now:")
    print("1. Test more queries with: python rag/retriever.py 'your query'")
    print("2. Run agent pipeline (if agents are set up)")
    print("3. Add more comprehensive documents for better coverage")
    print()
    
    return True

if __name__ == "__main__":
    success = test_rag_system()
    sys.exit(0 if success else 1)
