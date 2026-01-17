#!/usr/bin/env python3
"""
Phase 3: Evaluation & Award Document Generation

Generates evaluation and award documents with automatic cross-referencing:
- Source Selection Plan
- Evaluation Scorecards (per vendor)
- Source Selection Decision Document (SSDD)
- SF-26 (Award/Contract Form)
- Award Notification Letters
- Debriefing Materials

All documents automatically cross-reference Phase 1 and Phase 2 documents.

Usage:
    python scripts/generate_phase3_evaluation.py

    Or customize the project_info and vendor data below.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path

from backend.agents.source_selection_plan_generator_agent import SourceSelectionPlanGeneratorAgent
from backend.agents.evaluation_scorecard_generator_agent import EvaluationScorecardGeneratorAgent
from backend.agents.ssdd_generator_agent import SSDDGeneratorAgent
from backend.agents.sf26_generator_agent import SF26GeneratorAgent
from backend.agents.award_notification_generator_agent import AwardNotificationGeneratorAgent
from backend.agents.debriefing_generator_agent import DebriefingGeneratorAgent
from backend.utils.document_metadata_store import DocumentMetadataStore


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  PHASE 3: EVALUATION & AWARD GENERATION                    ║
║                                                                            ║
║  Generates evaluation and award documents with cross-referencing:         ║
║    • Source Selection Plan                                                ║
║    • Evaluation Scorecards (per vendor)                                   ║
║    • Source Selection Decision Document (SSDD)                            ║
║    • SF-26 (Award/Contract Form)                                          ║
║    • Award Notification Letters                                           ║
║    • Debriefing Materials                                                 ║
║                                                                            ║
║  All documents cross-reference Phases 1 & 2 automatically.                ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY environment variable not set\n")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    print("✅ API Key found\n")

    # ============================================================================
    # CUSTOMIZE YOUR PROJECT INFORMATION HERE
    # Must match the program_name from Phases 1 & 2 for cross-referencing!
    # ============================================================================

    project_info = {
        'program_name': 'Cloud Infrastructure Modernization',  # MUST MATCH PHASES 1 & 2!
        'program_acronym': 'CIM',
        'solicitation_number': 'FA8675-25-R-0001',
        'contracting_office': 'Air Force Materiel Command',
        'contracting_officer': 'John Doe',
        'contract_specialist': 'Jane Smith',
        'estimated_value': '$8,000,000',
        'period_of_performance': '60 months (12 base + 4 x 12 option)',
        'organization': 'United States Air Force'
    }

    # Vendor proposals (customize with actual vendor data)
    vendors = [
        {
            'vendor_name': 'CloudTech Solutions Inc',
            'cage_code': '1A2B3',
            'business_size': 'Small Business',
            'technical_score': 92,
            'management_score': 88,
            'past_performance': 'Excellent',
            'price': 7200000,
            'strengths': [
                'Extensive FedRAMP High experience (5 agencies)',
                'Strong AWS GovCloud expertise',
                'Excellent past performance on similar contracts',
                'Innovative automated migration approach'
            ],
            'weaknesses': [
                'Limited experience with classified systems',
                'Smaller team size than competitors'
            ]
        },
        {
            'vendor_name': 'Federal Cloud Services LLC',
            'cage_code': '4C5D6',
            'business_size': 'Small Business',
            'technical_score': 95,
            'management_score': 90,
            'past_performance': 'Excellent',
            'price': 7950000,
            'strengths': [
                'Exceptional technical approach with proven methodology',
                'Deep classified cloud experience (DoD TS/SCI)',
                'Comprehensive security automation capabilities',
                'Strong DevSecOps pipeline design'
            ],
            'weaknesses': [
                'Higher price than government estimate',
                'Aggressive timeline that may pose risk'
            ]
        },
        {
            'vendor_name': 'Enterprise Cloud Partners',
            'cage_code': '7E8F9',
            'business_size': 'Other than Small',
            'technical_score': 85,
            'management_score': 87,
            'past_performance': 'Satisfactory',
            'price': 8400000,
            'strengths': [
                'Large team with deep bench strength',
                'Multi-cloud experience (AWS, Azure, GCP)',
                'Established government cloud practice'
            ],
            'weaknesses': [
                'Highest price among offerors',
                'Generic approach lacking innovation',
                'Past performance had some schedule delays'
            ]
        }
    ]

    # Winner selection (customize based on evaluation)
    winner = {
        'vendor_name': 'Federal Cloud Services LLC',
        'justification': """
        Federal Cloud Services LLC offered the best value to the Government
        based on a comprehensive evaluation of technical, management, past
        performance, and price factors. While their price of $7,950,000 is
        higher than CloudTech Solutions' $7,200,000, the technical superiority
        and exceptional past performance justify the price premium.

        Key differentiators:
        - Superior technical approach (95 vs 92 points)
        - Classified cloud experience critical for mission requirements
        - Advanced security automation exceeds requirements
        - Past performance demonstrates consistent excellence

        The Source Selection Authority determines that the technical advantages
        warrant the additional cost and provide best value to the Government.
        """
    }

    # ============================================================================
    # GENERATE DOCUMENTS
    # ============================================================================

    output_dir = Path(f'output/phase3_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("GENERATING EVALUATION & AWARD DOCUMENTS")
    print("="*80)
    print(f"\nProgram: {project_info['program_name']}")
    print(f"Output Directory: {output_dir}")
    print(f"\n🔗 Will automatically cross-reference Phase 1 & 2 documents")
    print(f"\nEvaluating {len(vendors)} vendor proposals...")
    print(f"This will take approximately 3-5 minutes...\n")

    results = {
        'program': project_info['program_name'],
        'generated_date': datetime.now().isoformat(),
        'output_dir': str(output_dir),
        'documents': []
    }

    # Document 1: Source Selection Plan
    print("="*80)
    print("[1/6+] GENERATING SOURCE SELECTION PLAN")
    print("="*80)
    print("🔗 Will cross-reference Section M and Acquisition Plan\n")

    try:
        agent = SourceSelectionPlanGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'config': {
                'evaluation_method': 'Best Value Trade-Off',
                'source_selection_authority': 'Commander, AFMC'
            }
        })

        filepath = output_dir / 'source_selection_plan.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'source_selection_plan',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id')
        })

        print(f"\n✅ Source Selection Plan saved: {filepath}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")

    # Document 2-4: Evaluation Scorecards (one per vendor)
    print("="*80)
    print(f"[2-{1+len(vendors)}] GENERATING EVALUATION SCORECARDS")
    print("="*80)
    print(f"🔗 Will cross-reference Section M, PWS, and QASP\n")

    for i, vendor in enumerate(vendors, 1):
        print(f"\nGenerating scorecard {i}/{len(vendors)}: {vendor['vendor_name']}...")

        try:
            agent = EvaluationScorecardGeneratorAgent(api_key=api_key)
            result = agent.execute({
                'project_info': project_info,
                'vendor_info': vendor,
                'config': {}
            })

            vendor_slug = vendor['vendor_name'].lower().replace(' ', '_').replace('.', '')
            filepath = output_dir / f'evaluation_scorecard_{vendor_slug}.md'
            with open(filepath, 'w') as f:
                f.write(result['content'])

            results['documents'].append({
                'type': 'evaluation_scorecard',
                'vendor': vendor['vendor_name'],
                'file': str(filepath),
                'metadata_id': result.get('metadata_id')
            })

            print(f"✅ Scorecard saved: {filepath}")

        except Exception as e:
            print(f"❌ Error: {e}")

    print()

    # Document 5: Source Selection Decision Document (SSDD)
    print("="*80)
    print(f"[{2+len(vendors)}] GENERATING SSDD (SOURCE SELECTION DECISION)")
    print("="*80)
    print("🔗 Will cross-reference all scorecards and IGCE\n")

    try:
        agent = SSDDGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'vendors': vendors,
            'winner': winner,
            'config': {}
        })

        filepath = output_dir / 'ssdd.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'ssdd',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id'),
            'winner': winner['vendor_name']
        })

        print(f"\n✅ SSDD saved: {filepath}")
        print(f"   Winner: {winner['vendor_name']}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")

    # Document 6: SF-26 (Award Form)
    print("="*80)
    print(f"[{3+len(vendors)}] GENERATING SF-26 (AWARD/CONTRACT FORM)")
    print("="*80)
    print("🔗 Will cross-reference SSDD and IGCE\n")

    try:
        agent = SF26GeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'winner': winner,
            'config': {}
        })

        filepath = output_dir / 'sf26_award_contract.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'sf26',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id')
        })

        print(f"\n✅ SF-26 saved: {filepath}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")

    # Document 7: Award Notification
    print("="*80)
    print(f"[{4+len(vendors)}] GENERATING AWARD NOTIFICATION LETTER")
    print("="*80)
    print("🔗 Will cross-reference SF-26 and SSDD\n")

    try:
        agent = AwardNotificationGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'winner': winner,
            'config': {}
        })

        filepath = output_dir / 'award_notification_letter.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'award_notification',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id')
        })

        print(f"\n✅ Award Notification saved: {filepath}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")

    # Document 8+: Debriefing Materials (for non-winners)
    print("="*80)
    print(f"[{5+len(vendors)}-{4+2*len(vendors)}] GENERATING DEBRIEFING MATERIALS")
    print("="*80)
    print("🔗 Will cross-reference scorecards and SSDD\n")

    non_winners = [v for v in vendors if v['vendor_name'] != winner['vendor_name']]

    for i, vendor in enumerate(non_winners, 1):
        print(f"\nGenerating debriefing {i}/{len(non_winners)}: {vendor['vendor_name']}...")

        try:
            agent = DebriefingGeneratorAgent(api_key=api_key)
            result = agent.execute({
                'project_info': project_info,
                'vendor_info': vendor,
                'winner_info': winner,
                'config': {}
            })

            vendor_slug = vendor['vendor_name'].lower().replace(' ', '_').replace('.', '')
            filepath = output_dir / f'debriefing_{vendor_slug}.md'
            with open(filepath, 'w') as f:
                f.write(result['content'])

            results['documents'].append({
                'type': 'debriefing',
                'vendor': vendor['vendor_name'],
                'file': str(filepath),
                'metadata_id': result.get('metadata_id')
            })

            print(f"✅ Debriefing saved: {filepath}")

        except Exception as e:
            print(f"❌ Error: {e}")

    print()

    # ============================================================================
    # SUMMARY
    # ============================================================================

    print("\n" + "="*80)
    print("PHASE 3 GENERATION COMPLETE")
    print("="*80)

    print(f"\n📁 Output Directory: {output_dir}")
    print(f"\n✅ Generated {len(results['documents'])} documents:")

    doc_counts = {}
    for doc in results['documents']:
        doc_type = doc['type']
        doc_counts[doc_type] = doc_counts.get(doc_type, 0) + 1

    for doc_type, count in sorted(doc_counts.items()):
        if count == 1:
            print(f"   • {doc_type}: {count} document")
        else:
            print(f"   • {doc_type}: {count} documents")

    print(f"\n🏆 Contract Awarded To: {winner['vendor_name']}")

    # Show cross-reference summary
    print("\n🔗 Cross-Reference Summary:")
    store = DocumentMetadataStore()
    program_docs = [doc for doc in store.metadata['documents'].values()
                   if doc['program'] == project_info['program_name']]

    total_refs = sum(len(doc.get('references', {})) for doc in program_docs)
    print(f"   • Total documents for {project_info['program_name']}: {len(program_docs)}")
    print(f"   • Total cross-references: {total_refs}")

    print("\n" + "="*80)
    print("ACQUISITION PACKAGE COMPLETE")
    print("="*80)
    print("\nYou now have a complete acquisition package:")
    print("   ✅ Phase 1: Pre-Solicitation (4 documents)")
    print("   ✅ Phase 2: Solicitation/RFP (13 documents)")
    print(f"   ✅ Phase 3: Evaluation & Award ({len(results['documents'])} documents)")
    print("\nAll documents are cross-referenced and ready for use!")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
