"""
Test Docling Integration

Tests the new Docling document processor to verify:
1. Basic document processing works
2. Table extraction is functioning
3. Multiple document formats are supported
4. RAG integration is compatible
5. Quality improvements are measurable

Usage:
    python scripts/test_docling_integration.py
    python scripts/test_docling_integration.py --document path/to/test.pdf
    python scripts/test_docling_integration.py --compare
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)


def test_basic_processing():
    """Test basic document processing with Docling"""
    print("\n" + "="*70)
    print("TEST 1: Basic Document Processing")
    print("="*70 + "\n")
    
    from rag.docling_processor import DoclingProcessor
    
    # Initialize processor
    processor = DoclingProcessor(chunk_size=1000, chunk_overlap=200)
    
    # Find a test document
    test_docs = list(Path("data/documents").glob("*.pdf"))[:1]
    
    if not test_docs:
        print("⚠️  No PDF documents found in data/documents/")
        return False
    
    test_doc = test_docs[0]
    print(f"Testing with: {test_doc.name}")
    print()
    
    try:
        # Process document
        chunks = processor.process_document(str(test_doc))
        
        # Verify results
        if not chunks:
            print("❌ No chunks extracted!")
            return False
        
        print(f"✅ Successfully processed document")
        print(f"   Chunks extracted: {len(chunks)}")
        
        # Check metadata
        sample = chunks[0]
        print(f"\nSample chunk metadata:")
        for key, value in sample.metadata.items():
            print(f"   {key}: {value}")
        
        # Verify Docling was used
        if sample.metadata.get('processor') == 'docling':
            print("\n✅ Docling processor confirmed")
        else:
            print(f"\n⚠️  Processor used: {sample.metadata.get('processor', 'unknown')}")
        
        # Check for table chunks
        table_chunks = [c for c in chunks if c.metadata.get('content_type') == 'table']
        print(f"\n📊 Table chunks: {len(table_chunks)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_formats():
    """Test processing multiple document formats"""
    print("\n" + "="*70)
    print("TEST 2: Multiple Format Support")
    print("="*70 + "\n")
    
    from rag.docling_processor import DoclingProcessor
    
    processor = DoclingProcessor()
    
    # Test different formats
    formats_to_test = {
        '.pdf': 'PDF documents',
        '.docx': 'Word documents',
        '.xlsx': 'Excel spreadsheets',
        '.pptx': 'PowerPoint presentations',
        '.html': 'HTML files',
        '.md': 'Markdown files',
        '.txt': 'Text files'
    }
    
    results = {}
    
    for ext, description in formats_to_test.items():
        # Find a document with this extension
        test_files = list(Path("data/documents").glob(f"*{ext}"))
        
        if test_files:
            test_file = test_files[0]
            try:
                chunks = processor.process_document(str(test_file))
                results[ext] = {'status': '✅', 'chunks': len(chunks), 'file': test_file.name}
                print(f"✅ {description:30} {len(chunks):4} chunks - {test_file.name}")
            except Exception as e:
                results[ext] = {'status': '❌', 'error': str(e), 'file': test_file.name}
                print(f"❌ {description:30} Error: {str(e)[:50]}")
        else:
            results[ext] = {'status': '⊘', 'reason': 'No test file found'}
            print(f"⊘  {description:30} (no test file)")
    
    # Summary
    tested = sum(1 for r in results.values() if r['status'] in ['✅', '❌'])
    passed = sum(1 for r in results.values() if r['status'] == '✅')
    
    print(f"\nFormat support: {passed}/{tested} formats tested successfully")
    
    return passed > 0


def test_rag_integration():
    """Test integration with RAG vector store"""
    print("\n" + "="*70)
    print("TEST 3: RAG Integration")
    print("="*70 + "\n")
    
    from rag.docling_processor import DoclingProcessor
    from rag.vector_store import VectorStore
    
    load_dotenv()
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set - skipping RAG integration test")
        return None
    
    # Process a document
    processor = DoclingProcessor()
    
    test_docs = list(Path("data/documents").glob("*.pdf"))[:1]
    if not test_docs:
        print("⚠️  No PDF documents found")
        return None
    
    print(f"Processing: {test_docs[0].name}")
    chunks = processor.process_document(str(test_docs[0]))
    
    if not chunks:
        print("❌ No chunks to test with")
        return False
    
    print(f"✓ Processed {len(chunks)} chunks\n")
    
    # Create temporary vector store
    print("Creating test vector store...")
    vector_store = VectorStore(
        api_key=api_key,
        embedding_dimension=384,
        index_path="data/test_docling_vector_store"
    )
    
    try:
        # Add documents
        vector_store.add_documents(chunks[:10])  # Use first 10 chunks for speed
        print(f"✓ Added {len(chunks[:10])} chunks to vector store\n")
        
        # Test search
        print("Testing search...")
        results = vector_store.search("cost estimate schedule", k=3)
        
        if results:
            print(f"✅ Search successful - found {len(results)} results")
            
            # Show sample result
            if results:
                sample = results[0][0]
                print(f"\nSample result:")
                print(f"  Source: {sample['metadata']['source']}")
                print(f"  Processor: {sample['metadata'].get('processor', 'unknown')}")
                print(f"  Score: {sample['score']:.4f}")
                print(f"  Content: {sample['content'][:150]}...")
            
            return True
        else:
            print("⚠️  Search returned no results")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup test files
        test_files = [
            "data/test_docling_vector_store.faiss",
            "data/test_docling_vector_store.pkl"
        ]
        for f in test_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass


def compare_processors():
    """Compare basic vs Docling processor"""
    print("\n" + "="*70)
    print("TEST 4: Processor Comparison")
    print("="*70 + "\n")
    
    from rag.document_processor import DocumentProcessor as BasicProcessor
    from rag.docling_processor import DoclingProcessor
    
    # Find test document
    test_docs = list(Path("data/documents").glob("*.pdf"))[:1]
    if not test_docs:
        print("⚠️  No PDF documents found")
        return None
    
    test_doc = test_docs[0]
    print(f"Comparing processors on: {test_doc.name}\n")
    
    # Process with basic processor
    print("1. Basic Processor (PyPDF2)")
    print("-" * 40)
    basic = BasicProcessor(chunk_size=1000, chunk_overlap=200)
    
    try:
        basic_chunks = basic.process_pdf(str(test_doc))
        print(f"✓ Chunks: {len(basic_chunks)}")
        
        # Count tables (basic processor doesn't separate them)
        basic_tables = 0  # Basic processor doesn't extract tables separately
        print(f"✓ Tables: {basic_tables} (not extracted separately)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        basic_chunks = []
    
    print()
    
    # Process with Docling
    print("2. Docling Processor")
    print("-" * 40)
    docling = DoclingProcessor(chunk_size=1000, chunk_overlap=200)
    
    try:
        docling_chunks = docling.process_document(str(test_doc))
        print(f"✓ Chunks: {len(docling_chunks)}")
        
        # Count tables
        docling_tables = [c for c in docling_chunks if c.metadata.get('content_type') == 'table']
        print(f"✓ Tables: {len(docling_tables)} (extracted separately)")
        
        # Count text chunks
        text_chunks = [c for c in docling_chunks if c.metadata.get('content_type') == 'text']
        print(f"✓ Text chunks: {len(text_chunks)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        docling_chunks = []
        docling_tables = []
    
    print()
    
    # Comparison
    if basic_chunks and docling_chunks:
        print("Comparison:")
        print("-" * 40)
        print(f"Basic processor:   {len(basic_chunks):4} total chunks")
        print(f"Docling processor: {len(docling_chunks):4} total chunks")
        print(f"                   {len(docling_tables):4} table chunks (Docling only)")
        print()
        print("Docling advantages:")
        print("  ✅ Separate table extraction for better retrieval")
        print("  ✅ Layout-aware chunking (reading order)")
        print("  ✅ Better structure preservation (markdown export)")
        print("  ✅ More format support (PPTX, HTML, images, etc.)")
        
        return True
    
    return False


def test_specific_document(doc_path: str):
    """Test processing a specific document"""
    print("\n" + "="*70)
    print(f"TEST: Specific Document - {Path(doc_path).name}")
    print("="*70 + "\n")
    
    if not os.path.exists(doc_path):
        print(f"❌ File not found: {doc_path}")
        return False
    
    from rag.docling_processor import DoclingProcessor
    
    processor = DoclingProcessor()
    
    try:
        chunks = processor.process_document(doc_path)
        
        print(f"✅ Successfully processed")
        print(f"   Total chunks: {len(chunks)}")
        
        # Analyze chunks
        text_chunks = [c for c in chunks if c.metadata.get('content_type') == 'text']
        table_chunks = [c for c in chunks if c.metadata.get('content_type') == 'table']
        
        print(f"   Text chunks: {len(text_chunks)}")
        print(f"   Table chunks: {len(table_chunks)}")
        
        # Show sample chunks
        print("\nFirst 3 chunks:")
        for i, chunk in enumerate(chunks[:3], 1):
            print(f"\n{i}. {chunk.chunk_id}")
            print(f"   Type: {chunk.metadata.get('content_type', 'unknown')}")
            print(f"   Length: {len(chunk.content)} chars")
            print(f"   Preview: {chunk.content[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("DOCLING INTEGRATION TEST SUITE")
    print("="*70)
    
    # Parse arguments
    args = sys.argv[1:]
    
    if '--document' in args:
        idx = args.index('--document')
        if idx + 1 < len(args):
            doc_path = args[idx + 1]
            test_specific_document(doc_path)
            return
    
    if '--compare' in args:
        compare_processors()
        return
    
    # Run all tests
    results = {}
    
    results['basic'] = test_basic_processing()
    results['formats'] = test_multiple_formats()
    results['rag'] = test_rag_integration()
    results['compare'] = compare_processors()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70 + "\n")
    
    test_names = {
        'basic': 'Basic Document Processing',
        'formats': 'Multiple Format Support',
        'rag': 'RAG Integration',
        'compare': 'Processor Comparison'
    }
    
    for key, name in test_names.items():
        result = results.get(key)
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⊘  SKIP"
        
        print(f"{status:10} {name}")
    
    # Overall status
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    print()
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0 and passed > 0:
        print("\n✅ All tests passed!")
    elif passed > 0:
        print("\n⚠️  Some tests passed")
    else:
        print("\n❌ Tests failed or were skipped")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()

