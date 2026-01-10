"""
Setup Script: Initialize RAG system with documents
Run this first to process documents and create vector store

Dependencies:
- All RAG system components
- Documents in data/documents/ directory
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import enhanced Docling processor for superior document understanding
# Falls back to basic processor if Docling is unavailable
from backend.rag.docling_processor import DoclingProcessor as DocumentProcessor
from backend.rag.vector_store import VectorStore


def main():
    """
    Initialize RAG system:
    1. Process documents
    2. Generate embeddings
    3. Build vector store
    4. Save index
    """
    
    print("="*70)
    print("RAG SYSTEM SETUP")
    print("="*70)
    print()
    
    # Load API key
    load_dotenv()
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        return 1
    
    # Configuration
    documents_dir = "data/documents"
    vector_db_path = "data/vector_db/faiss_index"
    
    # Check if documents directory exists
    if not os.path.exists(documents_dir):
        print(f"Creating documents directory: {documents_dir}")
        Path(documents_dir).mkdir(parents=True, exist_ok=True)
        print()
        print("⚠️  No documents found!")
        print(f"Please add PDF or text files to: {documents_dir}/")
        print("Then run this script again.")
        return 1
    
    # Step 1: Process documents
    print("STEP 1: Processing Documents")
    print("-"*70)
    print()
    
    processor = DocumentProcessor(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    chunks = processor.process_directory(documents_dir)
    
    if not chunks:
        print()
        print("❌ No documents processed!")
        print(f"Please add PDF or text files to: {documents_dir}/")
        return 1
    
    print()
    print(f"✅ Processed {len(chunks)} chunks from documents")
    print()
    
    # Step 2: Create vector store
    print("STEP 2: Creating Vector Store")
    print("-"*70)
    print()
    
    vector_store = VectorStore(
        api_key=api_key,
        embedding_dimension=384,  # Updated to match sentence-transformers all-MiniLM-L6-v2
        index_path=vector_db_path
    )
    
    # Add documents to vector store
    vector_store.add_documents(chunks)
    
    # Save vector store
    vector_store.save()
    
    print()
    print("="*70)
    print("✅ RAG SYSTEM SETUP COMPLETE")
    print("="*70)
    print()
    print("Next steps:")
    print("1. Test retrieval: python scripts/test_rag_system.py")
    print("2. Run agent pipeline: python scripts/run_agent_pipeline.py")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

