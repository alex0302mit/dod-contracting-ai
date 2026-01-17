#!/usr/bin/env python3
"""
Generate Market Research Report (FIRST DOCUMENT)

This script generates only the Market Research Report for ALMS.
This report should be generated FIRST because it provides foundational
data that reduces TBDs in all downstream documents.

Usage:
    python scripts/generate_market_research_report.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path

from backend.agents.market_research_report_generator_agent import MarketResearchReportGeneratorAgent
from backend.utils.document_processor import DocumentProcessor


def get_alms_requirements():
    """Load ALMS requirements from document files"""
    print("📚 Loading ALMS requirements from documents...")

    alms_docs = [
        'data/documents/alms-kpp-ksa-complete.md',
        'data/documents/13_CDD_ALMS.md',
        'data/documents/9_acquisition_strategy_ALMS.md'
    ]

    all_content = []

    for doc_path in alms_docs:
        try:
            with open(doc_path, 'r') as f:
                content = f.read()
                all_content.append(content[:15000])
                print(f"  ✅ Loaded {Path(doc_path).name}")
        except Exception as e:
            print(f"  ⚠️  Could not load {Path(doc_path).name}: {e}")

    combined = "\n\n===== NEXT DOCUMENT =====\n\n".join(all_content)
    print(f"\n✅ Loaded {len(all_content)} documents ({len(combined):,} characters)\n")
    return combined


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║            MARKET RESEARCH REPORT GENERATOR (Phase 0)                      ║
║                                                                            ║
║  ⚠️  IMPORTANT: This should be the FIRST document generated!              ║
║                                                                            ║
║  Why Generate This First?                                                 ║
║  • Provides vendor landscape and pricing data for IGCE                    ║
║  • Identifies industry standards for PWS/SOW                              ║
║  • Analyzes competition for Acquisition Plan                              ║
║  • Assesses small business opportunities for Sources Sought               ║
║  • Recommends contract types for Section L/M                              ║
║                                                                            ║
║  Reduces TBDs in: IGCE, Acquisition Plan, PWS, SOW, Sources Sought        ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    # Check API keys
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY environment variable not set\n")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    print("✅ Anthropic API Key found")

    # Check for Tavily API key (optional but recommended)
    tavily_api_key = os.environ.get('TAVILY_API_KEY')
    if tavily_api_key:
        print("✅ Tavily API Key found - Web search enabled")
    else:
        print("⚠️  Tavily API Key not found - Web search disabled")
        print("   Set TAVILY_API_KEY to enable real-time market research")
        print("   Get free API key at: https://tavily.com\n")

    # Load ALMS requirements
    print("="*80)
    print("LOADING ALMS REQUIREMENTS")
    print("="*80)
    print()

    try:
        alms_requirements = get_alms_requirements()
    except Exception as e:
        print(f"❌ ERROR loading ALMS requirements: {e}")
        sys.exit(1)

    # Initialize Document Processor
    print("="*80)
    print("INITIALIZING DOCUMENT PROCESSOR")
    print("="*80)
    print()

    processor = DocumentProcessor(api_key=api_key)
    print("✅ Document Processor initialized\n")

    # Create output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path('output') / f'market_research_report_{timestamp}'
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 Output Directory: {output_dir}\n")

    # ALMS program information
    PROGRAM_NAME = "Advanced Logistics Management System (ALMS)"

    project_info = {
        'program_name': PROGRAM_NAME,
        'program_acronym': 'ALMS',
        'solicitation_number': 'W56KGU-25-R-0042',
        'estimated_value': '$2,500,000',
        'lifecycle_cost': '$6,425,000',
        'users': '2,800 users across 15 Army installations',
        'organization': 'U.S. Army',
        'requiring_activity': 'Defense Logistics Agency (DLA)',
        'contracting_office': 'U.S. Army Contracting Command - Rock Island',
        'ioc_date': 'June 2026',
        'foc_date': 'December 2026',
        'research_team': 'U.S. Army Contracting Command - Rock Island',
        'point_of_contact': 'MAJ Sarah Johnson',
        'email': 'sarah.m.johnson.mil@army.mil'
    }

    # Source documents for citations
    alms_source_docs = [
        'alms-kpp-ksa-complete.md',
        '13_CDD_ALMS.md',
        '9_acquisition_strategy_ALMS.md'
    ]

    # Generate Market Research Report
    print("="*80)
    print("GENERATING MARKET RESEARCH REPORT")
    print("="*80)
    print()

    print("  Generating Market Research Report...")
    print("  This may take 1-2 minutes...\n")

    try:
        # Initialize agent with Tavily API key
        agent = MarketResearchReportGeneratorAgent(
            api_key=api_key,
            tavily_api_key=tavily_api_key
        )

        # Generate report
        result = agent.execute({
            'project_info': project_info,
            'requirements_content': alms_requirements,
            'config': {}
        })

        # Process and save with enhancements (PDF, quality, citations)
        from scripts.generate_all_phases_alms import process_and_save_document

        processed = process_and_save_document(
            processor=processor,
            content=result['content'],
            output_path=output_dir / 'market_research_report.md',
            doc_type='market_research_report',
            program_name=PROGRAM_NAME,
            source_docs=alms_source_docs,
            project_info=project_info,
            display_name="Market Research Report"
        )

        print("\n" + "="*80)
        print("MARKET RESEARCH FINDINGS")
        print("="*80)
        print()

        # Display extracted market data
        market_data = result['extracted_data']
        print("📊 Key Market Research Data:")
        print(f"  • Vendor Count Estimate: {market_data.get('vendor_count_estimate', 'TBD')}")
        print(f"  • Small Business Potential: {market_data.get('small_business_potential', 'TBD')}")
        print(f"  • Recommended Contract Type: {market_data.get('recommended_contract_type', 'TBD')}")
        print(f"  • Competition Expected: {market_data.get('competition_expected', 'TBD')}")
        print(f"  • Commercial Items Available: {market_data.get('commercial_items_available', 'TBD')}")

        if market_data.get('labor_rate_ranges'):
            print(f"  • Labor Rate Ranges: {market_data['labor_rate_ranges']}")

        print("\n" + "="*80)
        print("GENERATION COMPLETE")
        print("="*80)
        print()

        print("📄 Generated Files:")
        print(f"  1. Markdown: {output_dir / 'market_research_report.md'}")
        print(f"  2. PDF: {output_dir / 'market_research_report.pdf'}")
        print(f"  3. Evaluation: {output_dir / 'market_research_report_evaluation.md'}")
        print(f"  4. Evaluation PDF: {output_dir / 'market_research_report_evaluation.pdf'}")

        print(f"\n📊 Quality Score: {processed['quality_score']}/100")
        print(f"📚 Citations: {processed['citations_added']} source documents")

        print("\n" + "="*80)
        print("DOWNSTREAM IMPACT")
        print("="*80)
        print()

        print("✅ This Market Research Report will reduce TBDs in:")
        print()
        print("  1. IGCE (Independent Government Cost Estimate)")
        print("     • Vendor pricing data")
        print("     • Labor rate ranges")
        print("     • Industry-standard cost breakdowns")
        print()
        print("  2. Acquisition Plan")
        print("     • Vendor landscape analysis")
        print("     • Competition expectations")
        print("     • Contract type recommendations")
        print()
        print("  3. PWS/SOW (Performance Work Statement / Statement of Work)")
        print("     • Industry capabilities")
        print("     • Technology maturity")
        print("     • Performance standards")
        print()
        print("  4. Sources Sought Notice")
        print("     • Target vendor count")
        print("     • Small business opportunities")
        print("     • Geographic distribution")
        print()
        print("  5. Section L/M (Evaluation Criteria)")
        print("     • Realistic evaluation factors")
        print("     • Market-based scoring criteria")
        print()

        print("="*80)
        print()
        print("🎯 Next Step: Use this market research data when generating other documents")
        print("   to minimize TBDs and improve document quality!")
        print()
        print(f"📁 All files saved to: {output_dir}")
        print()
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ ERROR generating market research report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
