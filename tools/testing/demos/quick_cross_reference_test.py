"""
Quick Cross-Reference System Test
Simplified test to verify cross-reference functionality

Usage:
    python scripts/quick_cross_reference_test.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.utils.document_metadata_store import DocumentMetadataStore


def main():
    """Quick test of cross-reference system"""

    print("\n" + "="*80)
    print("QUICK CROSS-REFERENCE SYSTEM TEST")
    print("="*80)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    # Initialize metadata store
    store = DocumentMetadataStore()

    # Test 1: Check if documents exist
    print("TEST 1: Checking for generated documents...")
    print("-" * 80)

    test_program = "Test_ALMS_CrossRef"
    all_docs = store.list_documents(program=test_program)

    print(f"\nFound {len(all_docs)} documents for '{test_program}':\n")

    if not all_docs:
        print("⚠️  No documents found. Run the full test first.")
        return 1

    # Group by type
    by_type = {}
    for doc in all_docs:
        doc_type = doc['type']
        if doc_type not in by_type:
            by_type[doc_type] = []
        by_type[doc_type].append(doc)

    for doc_type, docs in sorted(by_type.items()):
        print(f"  {doc_type}: {len(docs)} document(s)")
        for doc in docs:
            print(f"    • {doc['id']}")
            if doc.get('references'):
                print(f"      References: {list(doc['references'].keys())}")

    # Test 2: Verify cross-references
    print("\n\nTEST 2: Verifying cross-references...")
    print("-" * 80)

    # Build reference graph
    reference_count = 0
    for doc in all_docs:
        refs = doc.get('references', {})
        if refs:
            print(f"\n{doc['type']} ({doc['id']})")
            for ref_type, ref_id in refs.items():
                # Verify referenced document exists
                ref_doc = next((d for d in all_docs if d['id'] == ref_id), None)
                if ref_doc:
                    print(f"  ✓ → {ref_type}: {ref_id}")
                    reference_count += 1
                else:
                    print(f"  ❌ → {ref_type}: {ref_id} (NOT FOUND)")

    if reference_count == 0:
        print("\n⚠️  No cross-references found")
    else:
        print(f"\n\n✅ Found {reference_count} valid cross-references")

    # Test 3: Test metadata extraction
    print("\n\nTEST 3: Checking extracted data...")
    print("-" * 80)

    for doc in all_docs:
        extracted = doc.get('extracted_data', {})
        print(f"\n{doc['type']}:")
        if extracted:
            print(f"  ✓ Has {len(extracted)} extracted fields")
            # Show first few fields
            for key in list(extracted.keys())[:3]:
                value = extracted[key]
                if isinstance(value, (str, int, float)):
                    print(f"    - {key}: {value}")
                else:
                    print(f"    - {key}: <{type(value).__name__}>")
        else:
            print(f"  ⚠️  No extracted data")

    # Summary
    print("\n\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Documents generated: {len(all_docs)}")
    print(f"Document types: {len(by_type)}")
    print(f"Cross-references: {reference_count}")
    print("="*80 + "\n")

    if len(all_docs) > 0 and reference_count > 0:
        print("✅ Cross-reference system is working!")
        return 0
    else:
        print("⚠️  System needs more testing")
        return 1


if __name__ == "__main__":
    exit(main())
