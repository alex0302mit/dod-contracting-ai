#!/usr/bin/env python3
"""
MASTER SCRIPT: Generate Complete Acquisition Package (All Phases)

Generates all acquisition documents from pre-solicitation through award:
- Phase 1: Pre-Solicitation (4 documents)
- Phase 2: Solicitation/RFP (13 documents)
- Phase 3: Evaluation & Award (6+ documents)

All documents are automatically cross-referenced for consistency and traceability.

Total: 23+ documents with full cross-referencing

Usage:
    python scripts/generate_all_phases.py

    Or customize the configuration below.

Estimated Runtime: 10-15 minutes
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import time

# Add parent directory to path

from backend.utils.document_metadata_store import DocumentMetadataStore


def print_banner(text, char="="):
    """Print formatted banner"""
    width = 80
    print("\n" + char * width)
    print(text.center(width))
    print(char * width + "\n")


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    COMPLETE ACQUISITION PACKAGE GENERATION                 ║
║                                                                            ║
║  Generates ALL acquisition documents across all phases:                   ║
║                                                                            ║
║  Phase 1: Pre-Solicitation (Market Research)                              ║
║    • Sources Sought, RFI, Pre-Solicitation Notice, Industry Day           ║
║                                                                            ║
║  Phase 2: Solicitation/RFP                                                ║
║    • IGCE, Acquisition Plan, PWS, QASP                                    ║
║    • Sections B, H, I, K, L, M                                            ║
║    • Forms: SF-33                                                         ║
║                                                                            ║
║  Phase 3: Evaluation & Award                                              ║
║    • Source Selection Plan, Evaluation Scorecards                         ║
║    • SSDD, SF-26, Award Letters, Debriefings                              ║
║                                                                            ║
║  All documents are automatically cross-referenced!                        ║
║                                                                            ║
║  Runtime: Approximately 10-15 minutes                                     ║
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
    # SHARED CONFIGURATION
    # IMPORTANT: program_name must be consistent across all phases!
    # ============================================================================

    PROGRAM_NAME = 'Cloud Infrastructure Modernization'
    PROGRAM_ACRONYM = 'CIM'
    SOLICITATION_NUMBER = 'FA8675-25-R-0001'

    print("="*80)
    print("CONFIGURATION")
    print("="*80)
    print(f"\nProgram Name: {PROGRAM_NAME}")
    print(f"Program Acronym: {PROGRAM_ACRONYM}")
    print(f"Solicitation Number: {SOLICITATION_NUMBER}")
    print(f"\nEstimated Runtime: 10-15 minutes")
    print(f"Total Documents: ~23")
    print("\n" + "="*80)

    # Create master output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    master_output_dir = Path(f'output/complete_acquisition_{timestamp}')
    master_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📁 Master Output Directory: {master_output_dir}\n")

    # Confirm before proceeding
    print("This will generate approximately 23 documents and take 10-15 minutes.")
    response = input("\nProceed? (y/n): ").strip().lower()

    if response != 'y':
        print("\n❌ Generation cancelled by user.")
        sys.exit(0)

    start_time = time.time()

    # Track all results
    all_results = {
        'program_name': PROGRAM_NAME,
        'start_time': datetime.now().isoformat(),
        'phases': [],
        'total_documents': 0,
        'total_cross_references': 0,
        'output_dir': str(master_output_dir)
    }

    # ============================================================================
    # PHASE 1: PRE-SOLICITATION
    # ============================================================================

    print_banner("PHASE 1: PRE-SOLICITATION (Market Research)", "=")
    print("Generating 4 documents...")
    print("Estimated time: 2-3 minutes\n")

    phase1_start = time.time()

    # Import and run Phase 1 agents
    from agents.sources_sought_generator_agent import SourcesSoughtGeneratorAgent
    from agents.rfi_generator_agent import RFIGeneratorAgent
    from agents.pre_solicitation_notice_generator_agent import PreSolicitationNoticeGeneratorAgent
    from agents.industry_day_generator_agent import IndustryDayGeneratorAgent

    phase1_dir = master_output_dir / 'phase1_presolicitation'
    phase1_dir.mkdir(exist_ok=True)

    project_info_p1 = {
        'program_name': PROGRAM_NAME,
        'program_acronym': PROGRAM_ACRONYM,
        'solicitation_number': SOLICITATION_NUMBER,
        'contracting_office': 'Air Force Materiel Command',
        'point_of_contact': 'Jane Smith',
        'email': 'jane.smith@us.af.mil',
        'phone': '937-255-1234',
        'naics_code': '518210',
        'set_aside': 'Small Business',
        'estimated_value': '$8,000,000',
        'period_of_performance': '60 months (12 base + 4 x 12 options)',
        'organization': 'United States Air Force'
    }

    requirements = """
    Cloud infrastructure modernization services including migration of 50+ legacy
    applications, AWS GovCloud or Azure Government deployment, FedRAMP High
    authorization, 24/7 operations and support.
    """

    phase1_docs = []

    # Generate Phase 1 documents
    agents_p1 = [
        ('sources_sought', SourcesSoughtGeneratorAgent, 'sources_sought.md'),
        ('rfi', RFIGeneratorAgent, 'rfi.md'),
        ('pre_solicitation_notice', PreSolicitationNoticeGeneratorAgent, 'pre_solicitation_notice.md'),
        ('industry_day', IndustryDayGeneratorAgent, 'industry_day.md')
    ]

    for doc_name, AgentClass, filename in agents_p1:
        print(f"  Generating {doc_name}...")
        try:
            agent = AgentClass(api_key=api_key)
            result = agent.execute({
                'project_info': project_info_p1,
                'requirements_content': requirements,
                'config': {'contract_type': 'services'}
            })

            filepath = phase1_dir / filename
            with open(filepath, 'w') as f:
                f.write(result['content'])

            phase1_docs.append(doc_name)
            print(f"    ✅ Saved to {filename}")

        except Exception as e:
            print(f"    ❌ Error: {e}")

    phase1_time = time.time() - phase1_start

    all_results['phases'].append({
        'phase': 1,
        'name': 'Pre-Solicitation',
        'documents': len(phase1_docs),
        'time_seconds': round(phase1_time, 1)
    })

    print(f"\n✅ Phase 1 complete: {len(phase1_docs)} documents in {phase1_time:.1f}s\n")
    time.sleep(1)

    # ============================================================================
    # PHASE 2: SOLICITATION/RFP
    # ============================================================================

    print_banner("PHASE 2: SOLICITATION/RFP", "=")
    print("Generating 13 documents...")
    print("Estimated time: 5-7 minutes\n")

    phase2_start = time.time()

    # Import Phase 2 agents
    from agents.igce_generator_agent import IGCEGeneratorAgent
    from agents.acquisition_plan_generator_agent import AcquisitionPlanGeneratorAgent
    from agents.pws_writer_agent import PWSWriterAgent
    from agents.qasp_generator_agent import QASPGeneratorAgent
    from agents.section_b_generator_agent import SectionBGeneratorAgent
    from agents.section_h_generator_agent import SectionHGeneratorAgent
    from agents.section_i_generator_agent import SectionIGeneratorAgent
    from agents.section_k_generator_agent import SectionKGeneratorAgent
    from agents.section_l_generator_agent import SectionLGeneratorAgent
    from agents.section_m_generator_agent import SectionMGeneratorAgent
    from agents.sf33_generator_agent import SF33GeneratorAgent

    phase2_dir = master_output_dir / 'phase2_solicitation'
    phase2_dir.mkdir(exist_ok=True)

    project_info_p2 = {
        'program_name': PROGRAM_NAME,  # Same as Phase 1!
        'solicitation_number': SOLICITATION_NUMBER,
        'contracting_officer': 'John Doe',
        'estimated_value': '$8,000,000',
        'period_of_performance': '60 months (12 base + 4 x 12 options)',
        'organization': 'United States Air Force'
    }

    labor_categories = [
        {'category': 'Cloud Architect (Senior)', 'hours': 4160, 'rate': 185},
        {'category': 'Cloud Engineer (Senior)', 'hours': 8320, 'rate': 155},
        {'category': 'DevOps Engineer (Senior)', 'hours': 8320, 'rate': 145},
        {'category': 'Security Engineer (Senior)', 'hours': 6240, 'rate': 165},
    ]

    materials = [
        {'description': 'AWS GovCloud Services', 'cost': 1500000},
        {'description': 'Security Tools', 'cost': 300000},
    ]

    phase2_docs = []

    # Generate Phase 2 foundation documents
    print("  Foundation Documents:")
    try:
        print("    Generating IGCE...")
        agent = IGCEGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info_p2,
            'requirements_content': requirements,
            'labor_categories': labor_categories,
            'materials': materials,
            'config': {'contract_type': 'Firm Fixed Price'}
        })
        with open(phase2_dir / 'igce.md', 'w') as f:
            f.write(result['content'])
        phase2_docs.append('igce')
        print("      ✅ IGCE saved")
    except Exception as e:
        print(f"      ❌ Error: {e}")

    try:
        print("    Generating Acquisition Plan...")
        agent = AcquisitionPlanGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info_p2,
            'requirements_content': requirements,
            'config': {'contract_type': 'Firm Fixed Price'}
        })
        with open(phase2_dir / 'acquisition_plan.md', 'w') as f:
            f.write(result['content'])
        phase2_docs.append('acquisition_plan')
        print("      ✅ Acquisition Plan saved")
    except Exception as e:
        print(f"      ❌ Error: {e}")

    # Generate requirements documents
    print("\n  Requirements Documents:")
    requirements_agents = [
        ('PWS', PWSWriterAgent, 'pws.md'),
        ('QASP', QASPGeneratorAgent, 'qasp.md')
    ]

    for name, AgentClass, filename in requirements_agents:
        print(f"    Generating {name}...")
        try:
            agent = AgentClass(api_key=api_key)
            result = agent.execute({
                'project_info': project_info_p2,
                'requirements_content': requirements,
                'config': {}
            })
            with open(phase2_dir / filename, 'w') as f:
                f.write(result['content'])
            phase2_docs.append(name.lower())
            print(f"      ✅ {name} saved")
        except Exception as e:
            print(f"      ❌ Error: {e}")

    # Generate sections
    print("\n  Solicitation Sections:")
    section_agents = [
        ('Section B', SectionBGeneratorAgent, 'section_b.md'),
        ('Section H', SectionHGeneratorAgent, 'section_h.md'),
        ('Section I', SectionIGeneratorAgent, 'section_i.md'),
        ('Section K', SectionKGeneratorAgent, 'section_k.md'),
        ('Section L', SectionLGeneratorAgent, 'section_l.md'),
        ('Section M', SectionMGeneratorAgent, 'section_m.md')
    ]

    for name, AgentClass, filename in section_agents:
        print(f"    Generating {name}...")
        try:
            agent = AgentClass(api_key=api_key)
            result = agent.execute({
                'project_info': project_info_p2,
                'requirements_content': requirements,
                'config': {}
            })
            with open(phase2_dir / filename, 'w') as f:
                f.write(result['content'])
            phase2_docs.append(name.lower().replace(' ', '_'))
            print(f"      ✅ {name} saved")
        except Exception as e:
            print(f"      ❌ Error: {e}")

    # Generate forms
    print("\n  Forms:")
    form_agents = [
        ('SF-33', SF33GeneratorAgent, 'sf33.md')
    ]

    for name, AgentClass, filename in form_agents:
        print(f"    Generating {name}...")
        try:
            agent = AgentClass(api_key=api_key)
            result = agent.execute({
                'project_info': project_info_p2,
                'config': {}
            })
            with open(phase2_dir / filename, 'w') as f:
                f.write(result['content'])
            phase2_docs.append(name.lower().replace('-', '').replace(' ', '_'))
            print(f"      ✅ {name} saved")
        except Exception as e:
            print(f"      ❌ Error: {e}")

    phase2_time = time.time() - phase2_start

    all_results['phases'].append({
        'phase': 2,
        'name': 'Solicitation/RFP',
        'documents': len(phase2_docs),
        'time_seconds': round(phase2_time, 1)
    })

    print(f"\n✅ Phase 2 complete: {len(phase2_docs)} documents in {phase2_time:.1f}s\n")
    time.sleep(1)

    # ============================================================================
    # PHASE 3: EVALUATION & AWARD
    # ============================================================================

    print_banner("PHASE 3: EVALUATION & AWARD", "=")
    print("Generating 6+ documents...")
    print("Estimated time: 3-5 minutes\n")

    phase3_start = time.time()

    # Import Phase 3 agents
    from agents.source_selection_plan_generator_agent import SourceSelectionPlanGeneratorAgent
    from agents.evaluation_scorecard_generator_agent import EvaluationScorecardGeneratorAgent
    from agents.ssdd_generator_agent import SSDDGeneratorAgent
    from agents.sf26_generator_agent import SF26GeneratorAgent
    from agents.award_notification_generator_agent import AwardNotificationGeneratorAgent
    from agents.debriefing_generator_agent import DebriefingGeneratorAgent

    phase3_dir = master_output_dir / 'phase3_evaluation_award'
    phase3_dir.mkdir(exist_ok=True)

    # Simplified vendor data
    vendors = [
        {
            'vendor_name': 'CloudTech Solutions Inc',
            'technical_score': 92,
            'management_score': 88,
            'past_performance': 'Excellent',
            'price': 7200000
        },
        {
            'vendor_name': 'Federal Cloud Services LLC',
            'technical_score': 95,
            'management_score': 90,
            'past_performance': 'Excellent',
            'price': 7950000
        }
    ]

    winner = {
        'vendor_name': 'Federal Cloud Services LLC',
        'justification': 'Superior technical approach justifies price premium'
    }

    phase3_docs = []

    # Generate evaluation documents
    print("  Generating evaluation documents...")

    try:
        print("    Source Selection Plan...")
        agent = SourceSelectionPlanGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info_p2,
            'config': {'evaluation_method': 'Best Value Trade-Off'}
        })
        with open(phase3_dir / 'source_selection_plan.md', 'w') as f:
            f.write(result['content'])
        phase3_docs.append('source_selection_plan')
        print("      ✅ Saved")
    except Exception as e:
        print(f"      ❌ Error: {e}")

    # Evaluation scorecards
    for vendor in vendors:
        print(f"    Evaluation Scorecard: {vendor['vendor_name']}...")
        try:
            agent = EvaluationScorecardGeneratorAgent(api_key=api_key)
            result = agent.execute({
                'project_info': project_info_p2,
                'vendor_info': vendor,
                'config': {}
            })
            vendor_slug = vendor['vendor_name'].lower().replace(' ', '_')
            with open(phase3_dir / f'scorecard_{vendor_slug}.md', 'w') as f:
                f.write(result['content'])
            phase3_docs.append(f'scorecard_{vendor_slug}')
            print("      ✅ Saved")
        except Exception as e:
            print(f"      ❌ Error: {e}")

    # Award documents
    print("\n  Generating award documents...")

    try:
        print("    SSDD...")
        agent = SSDDGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info_p2,
            'vendors': vendors,
            'winner': winner,
            'config': {}
        })
        with open(phase3_dir / 'ssdd.md', 'w') as f:
            f.write(result['content'])
        phase3_docs.append('ssdd')
        print("      ✅ Saved")
    except Exception as e:
        print(f"      ❌ Error: {e}")

    try:
        print("    SF-26 (Award Form)...")
        agent = SF26GeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info_p2,
            'winner': winner,
            'config': {}
        })
        with open(phase3_dir / 'sf26.md', 'w') as f:
            f.write(result['content'])
        phase3_docs.append('sf26')
        print("      ✅ Saved")
    except Exception as e:
        print(f"      ❌ Error: {e}")

    try:
        print("    Award Notification...")
        agent = AwardNotificationGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info_p2,
            'winner': winner,
            'config': {}
        })
        with open(phase3_dir / 'award_notification.md', 'w') as f:
            f.write(result['content'])
        phase3_docs.append('award_notification')
        print("      ✅ Saved")
    except Exception as e:
        print(f"      ❌ Error: {e}")

    phase3_time = time.time() - phase3_start

    all_results['phases'].append({
        'phase': 3,
        'name': 'Evaluation & Award',
        'documents': len(phase3_docs),
        'time_seconds': round(phase3_time, 1)
    })

    print(f"\n✅ Phase 3 complete: {len(phase3_docs)} documents in {phase3_time:.1f}s\n")

    # ============================================================================
    # FINAL SUMMARY
    # ============================================================================

    total_time = time.time() - start_time
    all_results['end_time'] = datetime.now().isoformat()
    all_results['total_time_seconds'] = round(total_time, 1)
    all_results['total_documents'] = len(phase1_docs) + len(phase2_docs) + len(phase3_docs)

    # Get cross-reference statistics
    store = DocumentMetadataStore()
    program_docs = [doc for doc in store.metadata['documents'].values()
                   if doc['program'] == PROGRAM_NAME]
    total_refs = sum(len(doc.get('references', {})) for doc in program_docs)
    all_results['total_cross_references'] = total_refs

    print_banner("COMPLETE ACQUISITION PACKAGE GENERATED", "=")

    print(f"📁 Output Directory: {master_output_dir}\n")

    print("📊 Generation Summary:\n")
    for phase in all_results['phases']:
        print(f"  Phase {phase['phase']} ({phase['name']}):")
        print(f"    Documents: {phase['documents']}")
        print(f"    Time: {phase['time_seconds']}s")
        print()

    print(f"✅ Total Documents Generated: {all_results['total_documents']}")
    print(f"🔗 Total Cross-References: {total_refs}")
    print(f"⏱️  Total Time: {total_time:.1f}s ({total_time/60:.1f} minutes)")

    print("\n" + "="*80)
    print("YOUR COMPLETE ACQUISITION PACKAGE")
    print("="*80)
    print(f"\nPhase 1 (Pre-Solicitation): {master_output_dir}/phase1_presolicitation/")
    print(f"Phase 2 (Solicitation/RFP): {master_output_dir}/phase2_solicitation/")
    print(f"Phase 3 (Evaluation & Award): {master_output_dir}/phase3_evaluation_award/")

    print("\n🎉 All documents are cross-referenced and ready for use!")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
