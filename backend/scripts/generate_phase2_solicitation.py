#!/usr/bin/env python3
"""
Phase 2: Solicitation/RFP Document Generation

Generates all solicitation documents with automatic cross-referencing:
- IGCE (Independent Government Cost Estimate)
- Acquisition Plan
- PWS (Performance Work Statement)
- QASP (Quality Assurance Surveillance Plan)
- Section B: Supplies/Services and Prices
- Section H: Special Contract Requirements
- Section I: Contract Clauses
- Section K: Representations and Certifications
- Section L: Instructions to Offerors
- Section M: Evaluation Factors
- SF-33: Solicitation Form

All documents automatically cross-reference Phase 1 documents and each other.

Usage:
    python scripts/generate_phase2_solicitation.py

    Or customize the project_info and requirements below.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path

from backend.agents.igce_generator_agent import IGCEGeneratorAgent
from backend.agents.acquisition_plan_generator_agent import AcquisitionPlanGeneratorAgent
from backend.agents.pws_writer_agent import PWSWriterAgent
from backend.agents.qasp_generator_agent import QASPGeneratorAgent
from backend.agents.section_b_generator_agent import SectionBGeneratorAgent
from backend.agents.section_h_generator_agent import SectionHGeneratorAgent
from backend.agents.section_i_generator_agent import SectionIGeneratorAgent
from backend.agents.section_k_generator_agent import SectionKGeneratorAgent
from backend.agents.section_l_generator_agent import SectionLGeneratorAgent
from backend.agents.section_m_generator_agent import SectionMGeneratorAgent
from backend.agents.sf33_generator_agent import SF33GeneratorAgent
from backend.utils.document_metadata_store import DocumentMetadataStore


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    PHASE 2: SOLICITATION/RFP GENERATION                    ║
║                                                                            ║
║  Generates complete RFP package with cross-referencing:                   ║
║    • Foundation: IGCE, Acquisition Plan                                   ║
║    • Requirements: PWS, QASP                                              ║
║    • Sections: B, H, I, K, L, M                                           ║
║    • Forms: SF-33                                                         ║
║                                                                            ║
║  All documents cross-reference Phase 1 and each other automatically.      ║
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
    # Must match the program_name from Phase 1 for cross-referencing!
    # ============================================================================

    project_info = {
        'program_name': 'Cloud Infrastructure Modernization',  # MUST MATCH PHASE 1!
        'program_acronym': 'CIM',
        'solicitation_number': 'FA8675-25-R-0001',
        'contracting_office': 'Air Force Materiel Command',
        'contracting_officer': 'John Doe',
        'contract_specialist': 'Jane Smith',
        'estimated_value': '$8,000,000',
        'period_of_performance': '60 months (12 base + 4 x 12 option)',
        'organization': 'United States Air Force',
        'issue_date': '2026-01-15',
        'closing_date': '2026-03-01',
        'place_of_performance': 'Wright-Patterson AFB, OH'
    }

    requirements_content = """
    PERFORMANCE WORK STATEMENT

    1. SCOPE
    The contractor shall provide comprehensive cloud infrastructure modernization
    services to migrate and manage the Air Force's enterprise applications.

    2. BACKGROUND
    Current infrastructure consists of on-premises VMware environment supporting
    50+ mission-critical applications serving 5,000+ DoD personnel. The system
    requires modernization to cloud-native architecture.

    3. PERFORMANCE REQUIREMENTS

    3.1 Cloud Migration (Base Period)
       - Assess all 50+ applications for cloud readiness
       - Develop migration strategy and roadmap
       - Migrate applications with zero-downtime approach
       - Validate data integrity post-migration
       - Performance: 99.9% migration success rate

    3.2 Cloud Infrastructure (All Periods)
       - Design and implement cloud architecture (AWS GovCloud or Azure Gov)
       - Implement Infrastructure as Code (Terraform/CloudFormation)
       - Container orchestration using Kubernetes
       - Automated CI/CD pipelines
       - Performance: 99.95% uptime SLA

    3.3 Security & Compliance (All Periods)
       - Achieve FedRAMP High authorization within 6 months
       - Implement NIST 800-53 security controls
       - Continuous monitoring and compliance reporting
       - SOC integration for incident response
       - Performance: Zero security breaches, continuous compliance

    3.4 Operations & Support (All Periods)
       - 24/7/365 monitoring and support
       - Incident response within 15 minutes (critical), 2 hours (standard)
       - Monthly performance reports
       - Quarterly DR testing
       - Performance: 95% first-call resolution

    3.5 Training & Knowledge Transfer (Base + Option 1)
       - Cloud platform training for 20+ government personnel
       - Technical documentation and runbooks
       - Monthly knowledge transfer sessions
       - Performance: 90% training satisfaction score

    4. DELIVERABLES
       - Migration plan and schedules
       - Architecture design documents
       - Security compliance packages
       - Monthly status reports
       - Training materials and documentation
    """

    # Labor categories for IGCE
    labor_categories = [
        {'category': 'Cloud Architect (Senior)', 'hours': 4160, 'rate': 185},
        {'category': 'Cloud Engineer (Senior)', 'hours': 8320, 'rate': 155},
        {'category': 'Cloud Engineer (Mid)', 'hours': 12480, 'rate': 125},
        {'category': 'DevOps Engineer (Senior)', 'hours': 8320, 'rate': 145},
        {'category': 'Security Engineer (Senior)', 'hours': 6240, 'rate': 165},
        {'category': 'System Administrator', 'hours': 10400, 'rate': 105},
        {'category': 'Program Manager', 'hours': 2080, 'rate': 175},
        {'category': 'Technical Writer', 'hours': 2080, 'rate': 95},
    ]

    materials = [
        {'description': 'AWS GovCloud Services (compute, storage, networking)', 'cost': 1500000},
        {'description': 'Monitoring and Security Tools (Splunk, Tenable)', 'cost': 300000},
        {'description': 'Development Tools and Licenses', 'cost': 200000},
        {'description': 'Training Materials and Lab Environment', 'cost': 100000},
    ]

    # ============================================================================
    # GENERATE DOCUMENTS
    # ============================================================================

    output_dir = Path(f'output/phase2_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("GENERATING SOLICITATION DOCUMENTS")
    print("="*80)
    print(f"\nProgram: {project_info['program_name']}")
    print(f"Output Directory: {output_dir}")
    print(f"\n🔗 Will automatically cross-reference Phase 1 documents")
    print(f"\nThis will take approximately 5-7 minutes...\n")

    results = {
        'program': project_info['program_name'],
        'generated_date': datetime.now().isoformat(),
        'output_dir': str(output_dir),
        'documents': []
    }

    # Document 1: IGCE
    print("="*80)
    print("[1/13] GENERATING IGCE (COST ESTIMATE)")
    print("="*80)

    try:
        agent = IGCEGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'requirements_content': requirements_content,
            'labor_categories': labor_categories,
            'materials': materials,
            'config': {'contract_type': 'Firm Fixed Price'}
        })

        filepath = output_dir / 'igce.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'igce',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id'),
            'cost': result['extracted_data']['total_cost_formatted']
        })

        print(f"\n✅ IGCE saved: {filepath}")
        print(f"   Total Cost: {result['extracted_data']['total_cost_formatted']}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")

    # Document 2: Acquisition Plan
    print("="*80)
    print("[2/13] GENERATING ACQUISITION PLAN")
    print("="*80)
    print("🔗 Will cross-reference IGCE\n")

    try:
        agent = AcquisitionPlanGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'requirements_content': requirements_content,
            'config': {'contract_type': 'Firm Fixed Price'}
        })

        filepath = output_dir / 'acquisition_plan.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'acquisition_plan',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id')
        })

        print(f"\n✅ Acquisition Plan saved: {filepath}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")

    # Document 3: PWS
    print("="*80)
    print("[3/13] GENERATING PWS (PERFORMANCE WORK STATEMENT)")
    print("="*80)
    print("🔗 Will cross-reference IGCE and Acquisition Plan\n")

    try:
        agent = PWSWriterAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'requirements_content': requirements_content,
            'config': {
                'contract_type': 'Firm Fixed Price',
                'include_cdrl': True
            }
        })

        filepath = output_dir / 'pws.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'pws',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id')
        })

        print(f"\n✅ PWS saved: {filepath}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")

    # Document 4: QASP
    print("="*80)
    print("[4/13] GENERATING QASP (QUALITY ASSURANCE PLAN)")
    print("="*80)
    print("🔗 Will cross-reference PWS\n")

    try:
        agent = QASPGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'requirements_content': requirements_content,
            'config': {}
        })

        filepath = output_dir / 'qasp.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'qasp',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id')
        })

        print(f"\n✅ QASP saved: {filepath}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")

    # Document 5: Section B
    print("="*80)
    print("[5/13] GENERATING SECTION B (SUPPLIES/SERVICES & PRICES)")
    print("="*80)
    print("🔗 Will cross-reference IGCE and PWS\n")

    try:
        agent = SectionBGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'requirements_content': requirements_content,
            'config': {'contract_type': 'Firm Fixed Price'}
        })

        filepath = output_dir / 'section_b.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'section_b',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id')
        })

        print(f"\n✅ Section B saved: {filepath}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")

    # Document 6: Section H
    print("="*80)
    print("[6/13] GENERATING SECTION H (SPECIAL CONTRACT REQUIREMENTS)")
    print("="*80)

    try:
        agent = SectionHGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'requirements_content': requirements_content,
            'config': {}
        })

        filepath = output_dir / 'section_h.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'section_h',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id')
        })

        print(f"\n✅ Section H saved: {filepath}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")

    # Document 7: Section I
    print("="*80)
    print("[7/13] GENERATING SECTION I (CONTRACT CLAUSES)")
    print("="*80)
    print("🔗 Will cross-reference Section B\n")

    try:
        agent = SectionIGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'config': {'contract_type': 'Firm Fixed Price'}
        })

        filepath = output_dir / 'section_i.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'section_i',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id')
        })

        print(f"\n✅ Section I saved: {filepath}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")

    # Document 8: Section K
    print("="*80)
    print("[8/13] GENERATING SECTION K (REPRESENTATIONS & CERTIFICATIONS)")
    print("="*80)

    try:
        agent = SectionKGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'config': {}
        })

        filepath = output_dir / 'section_k.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'section_k',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id')
        })

        print(f"\n✅ Section K saved: {filepath}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")

    # Document 9: Section L
    print("="*80)
    print("[9/13] GENERATING SECTION L (INSTRUCTIONS TO OFFERORS)")
    print("="*80)
    print("🔗 Will cross-reference PWS and Section M\n")

    try:
        agent = SectionLGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'requirements_content': requirements_content,
            'config': {}
        })

        filepath = output_dir / 'section_l.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'section_l',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id')
        })

        print(f"\n✅ Section L saved: {filepath}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")

    # Document 10: Section M
    print("="*80)
    print("[10/13] GENERATING SECTION M (EVALUATION FACTORS)")
    print("="*80)
    print("🔗 Will cross-reference PWS and QASP\n")

    try:
        agent = SectionMGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'requirements_content': requirements_content,
            'config': {'evaluation_method': 'Best Value Trade-Off'}
        })

        filepath = output_dir / 'section_m.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'section_m',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id')
        })

        print(f"\n✅ Section M saved: {filepath}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")

    # Document 11: SF-33
    print("="*80)
    print("[11/11] GENERATING SF-33 (SOLICITATION FORM)")
    print("="*80)

    try:
        agent = SF33GeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'config': {}
        })

        filepath = output_dir / 'sf33_solicitation_form.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'sf33',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id')
        })

        print(f"\n✅ SF-33 saved: {filepath}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")

    # ============================================================================
    # SUMMARY
    # ============================================================================

    print("\n" + "="*80)
    print("PHASE 2 GENERATION COMPLETE")
    print("="*80)

    print(f"\n📁 Output Directory: {output_dir}")
    print(f"\n✅ Generated {len(results['documents'])} documents:")

    for doc in results['documents']:
        print(f"   • {doc['type']}: {Path(doc['file']).name}")
        if doc.get('cost'):
            print(f"     Total Cost: {doc['cost']}")

    # Show cross-reference summary
    print("\n🔗 Cross-Reference Summary:")
    store = DocumentMetadataStore()
    program_docs = [doc for doc in store.metadata['documents'].values()
                   if doc['program'] == project_info['program_name']]

    total_refs = sum(len(doc.get('references', {})) for doc in program_docs)
    print(f"   • Total documents for {project_info['program_name']}: {len(program_docs)}")
    print(f"   • Total cross-references: {total_refs}")

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("\n1. Review generated RFP package in output folder")
    print("2. Run Phase 3 to generate evaluation/award documents:")
    print("   python scripts/generate_phase3_evaluation.py")
    print("\n3. Or run all phases at once:")
    print("   python scripts/generate_all_phases.py")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
