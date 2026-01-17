"""
Document Content Reference
This file lists what each artifact contains for easy copying
"""

DOCUMENTS = {
    "1_government_contract_vehicles.md": {
        "artifact_name": "1_government_contract_vehicles.md",
        "size_kb": 25,
        "sections": [
            "GSA Multiple Award Schedule (MAS)",
            "Government-Wide Acquisition Contracts (GWACs)",
            "Blanket Purchase Agreements (BPAs)",
            "Best-in-Class (BIC) Contract Vehicles",
            "Quick Reference Matrix"
        ],
        "key_data": [
            "GSA MAS: $31B annual obligations",
            "SEWP VI: $50B ceiling, 148 contractors",
            "OASIS+: $75B ceiling, launched Sept 2024",
            "Processing times: 1-6 weeks"
        ]
    },
    
    "2_small_business_opportunities.md": {
        "artifact_name": "small_business_doc",
        "size_kb": 28,
        "sections": [
            "Small Business Size Standards",
            "8(a) Business Development Program",
            "HUBZone Program",
            "SDVOSB Program",
            "WOSB Program",
            "Market Research Resources"
        ],
        "key_data": [
            "FY 2024: $167.2B small business (24.1%)",
            "8(a) threshold: $4.5M services, $7M mfg",
            "9,247 active 8(a) participants",
            "11,432 verified SDVOSB firms"
        ]
    },
    
    "3_market_research_methodologies.md": {
        "artifact_name": "market_research_methods",
        "size_kb": 32,
        "sections": [
            "Legal Requirements (FAR 10)",
            "Research Techniques",
            "Market Research Phases",
            "Small Business Market Research",
            "Commercial Item Determination",
            "Price Analysis and IGCE"
        ],
        "key_data": [
            "Industry day avg: 78 attendees, $12.5K cost",
            "RFI responses: 14-31 average",
            "Sources sought: 11.3 responses avg",
            "Timeline: 90 days typical"
        ]
    },
    
    "4_far_regulations_market_research.md": {
        "artifact_name": "far_regulations_doc",
        "size_kb": 22,
        "sections": [
            "FAR Part 10 - Market Research",
            "FAR Part 7 - Acquisition Planning",
            "FAR Part 12 - Commercial Items",
            "FAR Part 13 - Simplified Acquisition",
            "FAR Part 19 - Small Business Programs",
            "Key Definitions (FAR 2.101)"
        ],
        "key_data": [
            "SAT: $250,000",
            "FAR 19.502-2: Rule of Two",
            "Plans required: >$10M",
            "Subcontracting plans: $750K/$1.5M"
        ]
    },
    
    "5_industry_capabilities_vendor_landscape.md": {
        "artifact_name": "vendor_capabilities_doc",
        "size_kb": 30,
        "sections": [
            "IT Services Sector",
            "Professional Services Sector",
            "Construction Services Sector",
            "Capability Assessment Criteria",
            "Emerging Vendor Trends",
            "Geographic Market Analysis"
        ],
        "key_data": [
            "IT services: $87.3B market",
            "Senior developer: $118/hour avg",
            "3,847 certified IT 8(a) firms",
            "CMMC: 4,200 firms pursuing"
        ]
    },
    
    "6_sample_market_research_report.md": {
        "artifact_name": "sample_market_research",
        "size_kb": 18,
        "sections": [
            "Executive Summary",
            "Requirement Overview",
            "Research Methodology",
            "Commercial Item Determination",
            "Competitive Assessment",
            "Pricing Analysis"
        ],
        "key_data": [
            "Example: $8.5M IT helpdesk",
            "31 sources sought responses",
            "23 small businesses (74%)",
            "Tier 1: $45-$68/hour"
        ]
    }
}

def print_extraction_guide():
    """Print guide for extracting documents from artifacts"""
    
    print("="*70)
    print("DOCUMENT EXTRACTION GUIDE")
    print("="*70)
    print()
    print("To extract documents from Claude's artifacts:")
    print()
    
    for filename, info in DOCUMENTS.items():
        print(f"📄 {filename}")
        print(f"   Artifact: {info['artifact_name']}")
        print(f"   Size: ~{info['size_kb']}KB")
        print(f"   Key sections: {len(info['sections'])}")
        print()
        print("   How to extract:")
        print("   1. Scroll up in conversation")
        print(f"   2. Find artifact titled: {info['artifact_name']}")
        print("   3. Click to expand")
        print("   4. Copy all content")
        print(f"   5. Save as: data/documents/{filename}")
        print()
    
    print("-"*70)
    print("After saving all 6 files:")
    print("  python scripts/verify_rag_docs.py")
    print()

def print_content_summary():
    """Print summary of what each document contains"""
    
    print("="*70)
    print("DOCUMENT CONTENT SUMMARY")
    print("="*70)
    print()
    
    for filename, info in DOCUMENTS.items():
        print(f"\n{filename}")
        print("-" * len(filename))
        print("\nMain Sections:")
        for section in info['sections']:
            print(f"  • {section}")
        print("\nKey Data Points:")
        for data in info['key_data']:
            print(f"  • {data}")
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        print_content_summary()
    else:
        print_extraction_guide()
