"""Quick test of document processing"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.rag.document_processor import DocumentProcessor

# Test with a single file
processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)

test_file = "data/documents/1_government_contract_vehicles.md"
print(f"Testing with: {test_file}")

# Get file size
import os
size = os.path.getsize(test_file)
print(f"File size: {size:,} bytes ({size/1024:.1f} KB)")

print("\n1. Reading file...")
try:
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"   ✓ Read {len(content)} characters")
except Exception as e:
    print(f"   ✗ Error reading: {e}")
    sys.exit(1)

print("\n2. Cleaning text...")
try:
    cleaned = processor._clean_text(content)
    print(f"   ✓ Cleaned to {len(cleaned)} characters")
except Exception as e:
    print(f"   ✗ Error cleaning: {e}")
    sys.exit(1)

print("\n3. Chunking text...")
try:
    chunks_list = processor._chunk_text(content)
    print(f"   ✓ Created {len(chunks_list)} text chunks")
except Exception as e:
    print(f"   ✗ Error chunking: {e}")
    sys.exit(1)

print("\n4. Full processing...")
try:
    chunks = processor.process_text_file(test_file)
    print(f"   ✓ Created {len(chunks)} DocumentChunk objects")
    if chunks:
        print(f"\nFirst chunk preview: {chunks[0].content[:100]}...")
except Exception as e:
    print(f"   ✗ Error in full processing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ All tests passed!")
