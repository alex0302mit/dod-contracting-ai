#!/usr/bin/env python3
"""
Quick test for Section I and K generators with cross-reference system
"""

import sys
import os
from pathlib import Path
import time

# Add parent directory to path

from backend.agents.section_i_generator_agent import SectionIGeneratorAgent
from backend.agents.section_k_generator_agent import SectionKGeneratorAgent
from backend.utils.document_metadata_store import DocumentMetadataStore
from dotenv import load_dotenv

load_dotenv()

def test_section_i():
    """Test Section I Generator"""
    print("\n" + "="*70)
    print("TEST: Section I Generator with Cross-Reference")
    print("="*70)

    try:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            print("❌ ANTHROPIC_API_KEY not set")
            return False

        # Create agent
        agent = SectionIGeneratorAgent(api_key=api_key)

        # Execute
        result = agent.execute({
            'solicitation_info': {
                'program_name': 'TEST_SECTION_I',
                'solicitation_number': 'TEST-001'
            },
            'config': {
                'contract_type': 'ffp',
                'set_aside': True
            }
        })

        print(f"\n✅ Section I generated successfully")
        print(f"   Status: {result['status']}")
        print(f"   Contract Type: {result['metadata']['contract_type']}")
        print(f"   Clauses Count: {result['metadata']['clauses_count']}")

        # Wait for file I/O
        time.sleep(0.5)

        # Verify metadata saved
        store = DocumentMetadataStore()
        saved_doc = store.find_latest_document('section_i', 'TEST_SECTION_I')

        if saved_doc:
            print(f"\n✅ Metadata saved successfully: {saved_doc['id']}")
            print(f"   Contract Type: {saved_doc['extracted_data']['contract_type']}")
            print(f"   Clauses: {saved_doc['extracted_data']['clauses_count']}")
            return True
        else:
            print(f"\n❌ Metadata NOT saved")
            return False

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_section_k():
    """Test Section K Generator"""
    print("\n" + "="*70)
    print("TEST: Section K Generator with Cross-Reference")
    print("="*70)

    try:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            print("❌ ANTHROPIC_API_KEY not set")
            return False

        # Create agent
        agent = SectionKGeneratorAgent(api_key=api_key)

        # Execute
        result = agent.execute({
            'solicitation_info': {
                'program_name': 'TEST_SECTION_K',
                'solicitation_number': 'TEST-002'
            },
            'config': {
                'naics_code': '541512',
                'set_aside': 'Small Business',
                'size_standard': '$34M'
            }
        })

        print(f"\n✅ Section K generated successfully")
        print(f"   Status: {result['status']}")
        print(f"   NAICS: {result['metadata']['naics_code']}")
        print(f"   Set Aside: {result['metadata']['set_aside']}")

        # Wait for file I/O
        time.sleep(0.5)

        # Verify metadata saved
        store = DocumentMetadataStore()
        saved_doc = store.find_latest_document('section_k', 'TEST_SECTION_K')

        if saved_doc:
            print(f"\n✅ Metadata saved successfully: {saved_doc['id']}")
            print(f"   NAICS: {saved_doc['extracted_data']['naics_code']}")
            print(f"   Set Aside: {saved_doc['extracted_data']['set_aside']}")
            print(f"   Representation Types: {len(saved_doc['extracted_data']['representation_types'])}")
            return True
        else:
            print(f"\n❌ Metadata NOT saved")
            return False

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def cleanup():
    """Clean up test data"""
    print("\n" + "="*70)
    print("CLEANUP")
    print("="*70)

    try:
        store = DocumentMetadataStore()

        # Remove test documents
        test_programs = ['TEST_SECTION_I', 'TEST_SECTION_K']
        removed_count = 0

        for program in test_programs:
            for doc_type in ['section_i', 'section_k']:
                docs = [doc for doc in store.documents.values()
                       if doc['program'] == program and doc['doc_type'] == doc_type]

                for doc in docs:
                    del store.documents[doc['id']]
                    removed_count += 1
                    print(f"   Removed: {doc['id']}")

        store._save_to_file()
        print(f"\n✅ Cleanup complete: {removed_count} test documents removed")

    except Exception as e:
        print(f"⚠️  Cleanup warning: {str(e)}")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("SECTION I & K GENERATOR TESTS")
    print("="*70)

    results = []

    # Run tests
    results.append(("Section I Generator", test_section_i()))
    results.append(("Section K Generator", test_section_k()))

    # Cleanup
    cleanup()

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*70)

    sys.exit(0 if passed == total else 1)
