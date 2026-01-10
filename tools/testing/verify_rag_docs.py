"""
Helper script to verify RAG document setup
Checks that all required documents are present and provides statistics
"""

import os
from pathlib import Path

def check_rag_documents():
    """Check RAG document setup"""
    
    docs_dir = Path("data/documents")
    
    print("="*70)
    print("RAG DOCUMENT VERIFICATION")
    print("="*70)
    print()
    
    # Expected documents
    expected_docs = [
        "1_government_contract_vehicles.md",
        "2_small_business_opportunities.md",
        "3_market_research_methodologies.md",
        "4_far_regulations_market_research.md",
        "5_industry_capabilities_vendor_landscape.md",
        "6_sample_market_research_report.md"
    ]
    
    # Check if directory exists
    if not docs_dir.exists():
        print(f"❌ Directory not found: {docs_dir}")
        print(f"   Create it with: mkdir -p {docs_dir}")
        return False
    
    print(f"✓ Documents directory exists: {docs_dir}")
    print()
    
    # Check each document
    found_docs = []
    missing_docs = []
    total_size = 0
    
    for doc in expected_docs:
        doc_path = docs_dir / doc
        if doc_path.exists():
            size = doc_path.stat().st_size
            total_size += size
            found_docs.append((doc, size))
            print(f"✓ {doc} ({size:,} bytes)")
        else:
            missing_docs.append(doc)
            print(f"❌ {doc} (missing)")
    
    print()
    print("-"*70)
    print(f"Found: {len(found_docs)}/{len(expected_docs)} documents")
    print(f"Total size: {total_size:,} bytes ({total_size/1024:.1f} KB)")
    print()
    
    if missing_docs:
        print("Missing documents:")
        for doc in missing_docs:
            print(f"  - {doc}")
        print()
        print("Action required:")
        print("1. Copy the document content from Claude's artifacts above")
        print("2. Save each as a .md file in data/documents/")
        print("3. Run this script again to verify")
        return False
    else:
        # Check if files are too small (might be empty or incomplete)
        small_files = [(doc, size) for doc, size in found_docs if size < 10000]
        if small_files:
            print("⚠️  Warning: Some files seem incomplete (< 10KB):")
            for doc, size in small_files:
                print(f"  - {doc}: {size:,} bytes (expected ~20-30KB)")
            print()
            print("These files might not have full content from artifacts.")
            print("Expected sizes:")
            print("  - 1_government_contract_vehicles.md: ~25KB")
            print("  - 2_small_business_opportunities.md: ~28KB")  
            print("  - 3_market_research_methodologies.md: ~32KB")
            print("  - 4_far_regulations_market_research.md: ~22KB")
            print("  - 5_industry_capabilities_vendor_landscape.md: ~30KB")
            print("  - 6_sample_market_research_report.md: ~18KB")
            print()
        
        print("✅ All documents present!")
        print()
        print("Next steps:")
        print("1. Run: python scripts/setup_rag_system.py")
        print("2. Test: python rag/retriever.py 'test query'")
        print("3. Generate reports with the agent pipeline")
        return True

if __name__ == "__main__":
    success = check_rag_documents()
    exit(0 if success else 1)
