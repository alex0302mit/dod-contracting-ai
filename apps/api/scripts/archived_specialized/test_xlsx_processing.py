"""
Test XLSX processing in RAG system
Demonstrates how to add and query tabular data
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from backend.rag.document_processor import DocumentProcessor
from backend.rag.vector_store import VectorStore
from backend.rag.table_aware_retriever import TableAwareRetriever
from backend.rag.retriever import Retriever
from dotenv import load_dotenv


def main():
    """Test XLSX processing"""
    
    print("\n" + "="*70)
    print("XLSX PROCESSING TEST")
    print("="*70 + "\n")
    
    # Load environment
    load_dotenv()
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not set")
        return 1
    
    # Step 1: Process XLSX files
    print("Step 1: Processing XLSX files...")
    processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
    
    # Process a specific directory with XLSX files
    xlsx_dir = "data/documents"  # Your XLSX files location
    chunks = processor.process_directory(xlsx_dir)
    
    print(f"\n✅ Processed {len(chunks)} chunks\n")
    
    # Show sample table chunks
    table_chunks = [c for c in chunks if c.metadata.get('file_type') in ['excel', 'csv']]
    if table_chunks:
        print(f"Found {len(table_chunks)} table chunks\n")
        print("Sample table chunk:")
        sample = table_chunks[0]
        print(f"  Source: {sample.metadata['source']}")
        print(f"  Sheet: {sample.metadata.get('sheet_name', 'N/A')}")
        print(f"  Columns: {sample.metadata.get('columns', 'N/A')}")
        print(f"  Content preview:\n{sample.content[:300]}...\n")
    
    # Step 2: Add to vector store
    print("\nStep 2: Adding to vector store...")
    vector_store = VectorStore(api_key, index_path="data/vector_db/faiss_index")
    
    # Load existing or create new
    if not vector_store.load():
        print("Creating new vector store...")
        vector_store.create_index(chunks)
    else:
        print("Adding to existing vector store...")
        vector_store.add_documents(chunks)
    
    vector_store.save()
    print("✅ Vector store updated\n")
    
    # Step 3: Test retrieval
    print("\nStep 3: Testing table-aware retrieval...")
    base_retriever = Retriever(vector_store, top_k=5)
    table_retriever = TableAwareRetriever(base_retriever)
    
    # Test query
    test_query = "What vendors are available for logistics systems?"
    print(f"\nQuery: {test_query}")
    
    results = table_retriever.retrieve_table_data(test_query, k=3)
    
    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n[Result {i}]")
        print(f"Source: {result['metadata']['source']}")
        if result['metadata'].get('file_type') == 'excel':
            print(f"Sheet: {result['metadata'].get('sheet_name')}")
            print(f"Columns: {result['metadata'].get('columns')}")
        print(f"Content preview: {result['content'][:200]}...")
    
    print("\n" + "="*70)
    print("✅ XLSX PROCESSING TEST COMPLETE")
    print("="*70 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
