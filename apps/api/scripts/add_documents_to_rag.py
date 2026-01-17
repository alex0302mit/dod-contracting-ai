"""
Add Documents to Existing RAG System
Use this to add new documents without rebuilding the entire vector database

Usage:
    # Add all new documents from data/documents/
    python scripts/add_documents_to_rag.py

    # Add specific file
    python scripts/add_documents_to_rag.py path/to/new_document.pdf

    # Add all files from a specific directory
    python scripts/add_documents_to_rag.py path/to/new_docs/
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


def add_documents(file_or_dir_path: str = None, vector_db_path: str = "data/vector_db/faiss_index"):
    """
    Add new documents to existing RAG system

    Args:
        file_or_dir_path: Path to file or directory to add. If None, scans data/documents/
        vector_db_path: Path to vector database
    """

    print("\n" + "="*70)
    print("ADD DOCUMENTS TO RAG SYSTEM")
    print("="*70)
    print()

    # Load API key
    load_dotenv()
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        return 1

    # Check if vector store exists
    if not os.path.exists(f"{vector_db_path}.faiss"):
        print("❌ No existing vector store found!")
        print("\nPlease run setup first: python scripts/setup_rag_system.py")
        return 1

    # Determine what to process
    if file_or_dir_path:
        target_path = file_or_dir_path
    else:
        target_path = "data/documents"
        print("⚠️  No specific path provided. Scanning data/documents/")
        print("   This will re-index ALL documents (may create duplicates)")
        print()
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return 0

    if not os.path.exists(target_path):
        print(f"❌ Path does not exist: {target_path}")
        return 1

    # Load existing vector store
    print(f"Loading existing vector store from: {vector_db_path}")
    vector_store = VectorStore(
        api_key=api_key,
        embedding_dimension=384,  # Must match existing store
        index_path=vector_db_path
    )

    if not vector_store.load():
        print("❌ Failed to load existing vector store")
        return 1

    existing_count = len(vector_store.chunks)
    print(f"✓ Loaded existing store with {existing_count} chunks")
    print()

    # Process new documents
    print("Processing new documents...")
    print("-"*70)
    print()

    processor = DocumentProcessor(
        chunk_size=1000,
        chunk_overlap=200
    )

    # Process based on path type
    path_obj = Path(target_path)
    if path_obj.is_file():
        # Single file
        if path_obj.suffix.lower() == '.pdf':
            chunks = processor.process_pdf(str(path_obj))
        elif path_obj.suffix.lower() in ['.txt', '.md']:
            chunks = processor.process_text_file(str(path_obj))
        elif path_obj.suffix.lower() == '.docx':
            chunks = processor.process_docx(str(path_obj))
        else:
            print(f"❌ Unsupported file type: {path_obj.suffix}")
            return 1
    else:
        # Directory
        chunks = processor.process_directory(target_path)

    if not chunks:
        print()
        print("⚠️  No new documents processed!")
        return 0

    print()
    print(f"✓ Processed {len(chunks)} new chunks")
    print()

    # Add to existing vector store
    print("Adding to vector store...")
    print("-"*70)
    print()

    vector_store.add_documents(chunks)

    # Save updated vector store
    print("\nSaving updated vector store...")
    vector_store.save()

    new_total = len(vector_store.chunks)
    print()
    print("="*70)
    print("✅ DOCUMENTS ADDED SUCCESSFULLY")
    print("="*70)
    print(f"  Previous chunks: {existing_count}")
    print(f"  New chunks added: {len(chunks)}")
    print(f"  Total chunks now: {new_total}")
    print()
    print("The RAG system is ready to use with the new documents!")
    print()

    return 0


def main():
    """Main entry point"""

    # Check for command line argument
    file_or_dir = None
    if len(sys.argv) > 1:
        file_or_dir = sys.argv[1]

    return add_documents(file_or_dir)


if __name__ == "__main__":
    sys.exit(main())
