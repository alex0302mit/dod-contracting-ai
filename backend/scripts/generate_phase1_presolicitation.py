#!/usr/bin/env python3
"""
Phase 1: Pre-Solicitation Document Generation

Generates all pre-solicitation/market research documents with automatic cross-referencing:
- Sources Sought Notice
- Request for Information (RFI)
- Pre-Solicitation Notice
- Industry Day Materials

All documents are saved with metadata for cross-referencing by later phases.

Usage:
    python scripts/generate_phase1_presolicitation.py

    Or customize the project_info and requirements below.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path

from backend.agents.sources_sought_generator_agent import SourcesSoughtGeneratorAgent
from backend.agents.rfi_generator_agent import RFIGeneratorAgent
from backend.agents.pre_solicitation_notice_generator_agent import PreSolicitationNoticeGeneratorAgent
from backend.agents.industry_day_generator_agent import IndustryDayGeneratorAgent
from backend.utils.document_metadata_store import DocumentMetadataStore


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  PHASE 1: PRE-SOLICITATION GENERATION                      ║
║                                                                            ║
║  Generates market research and pre-solicitation documents:                ║
║    1. Sources Sought Notice                                               ║
║    2. Request for Information (RFI)                                       ║
║    3. Pre-Solicitation Notice                                             ║
║    4. Industry Day Materials                                              ║
║                                                                            ║
║  All documents saved with metadata for cross-referencing.                 ║
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
    # ============================================================================

    project_info = {
        'program_name': 'Cloud Infrastructure Modernization',
        'program_acronym': 'CIM',
        'solicitation_number': 'FA8675-25-R-0001',
        'contracting_office': 'Air Force Materiel Command',
        'point_of_contact': 'Jane Smith',
        'email': 'jane.smith@us.af.mil',
        'phone': '937-255-1234',
        'naics_code': '518210',  # Data Processing, Hosting, and Related Services
        'set_aside': 'Small Business',
        'estimated_value': '$8,000,000',
        'period_of_performance': '60 months (12 month base + 4 x 12 month options)',
        'organization': 'United States Air Force'
    }

    requirements_content = """
    The Government is conducting market research to identify potential sources
    capable of providing cloud infrastructure modernization services.

    REQUIREMENT OVERVIEW:

    1. Cloud Migration Services
       - Migrate 50+ legacy applications to cloud environment
       - AWS GovCloud or Azure Government Cloud
       - Zero-downtime migration strategy
       - Data migration and validation

    2. Cloud Infrastructure Management
       - Design and implement cloud architecture
       - Infrastructure as Code (Terraform/CloudFormation)
       - Automated deployment pipelines (CI/CD)
       - Container orchestration (Kubernetes)

    3. Security & Compliance
       - FedRAMP High authorization required
       - NIST 800-53 security controls implementation
       - Continuous monitoring and compliance reporting
       - Security Operations Center (SOC) integration

    4. Support & Maintenance
       - 24/7/365 monitoring and support
       - Incident response and troubleshooting
       - Performance optimization
       - Quarterly disaster recovery testing

    5. Training & Documentation
       - Cloud platform training for government personnel
       - Technical documentation and runbooks
       - Knowledge transfer sessions

    TECHNICAL ENVIRONMENT:
    - Current: On-premises VMware infrastructure
    - Target: Cloud-native architecture
    - Users: 5,000+ DoD personnel
    - Data: ~500TB (mix of unclassified and classified)
    - Applications: Mix of COTS and custom-developed

    CONSTRAINTS:
    - Must support Secret-level classified data
    - CONUS and OCONUS deployments
    - Authority to Operate (ATO) required within 6 months
    - Maximum acceptable downtime: 4 hours per year
    """

    # ============================================================================
    # GENERATE DOCUMENTS
    # ============================================================================

    output_dir = Path(f'output/phase1_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("GENERATING PRE-SOLICITATION DOCUMENTS")
    print("="*80)
    print(f"\nProgram: {project_info['program_name']}")
    print(f"Output Directory: {output_dir}")
    print(f"\nThis will take approximately 2-3 minutes...\n")

    results = {
        'program': project_info['program_name'],
        'generated_date': datetime.now().isoformat(),
        'output_dir': str(output_dir),
        'documents': []
    }

    # Document 1: Sources Sought Notice
    print("="*80)
    print("[1/4] GENERATING SOURCES SOUGHT NOTICE")
    print("="*80)

    try:
        agent = SourcesSoughtGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'requirements_content': requirements_content,
            'config': {
                'contract_type': 'services',
                'response_deadline_days': 21
            }
        })

        # Save to file
        filepath = output_dir / 'sources_sought_notice.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'sources_sought',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id')
        })

        print(f"\n✅ Sources Sought Notice saved to: {filepath}\n")

    except Exception as e:
        print(f"\n❌ Error generating Sources Sought: {e}\n")

    # Document 2: Request for Information (RFI)
    print("="*80)
    print("[2/4] GENERATING REQUEST FOR INFORMATION (RFI)")
    print("="*80)
    print("🔗 This will automatically cross-reference the Sources Sought notice\n")

    try:
        agent = RFIGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'requirements_content': requirements_content,
            'config': {
                'contract_type': 'services',
                'response_deadline_days': 35
            }
        })

        # Save to file
        filepath = output_dir / 'rfi.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'rfi',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id')
        })

        print(f"\n✅ RFI saved to: {filepath}\n")

    except Exception as e:
        print(f"\n❌ Error generating RFI: {e}\n")

    # Document 3: Pre-Solicitation Notice
    print("="*80)
    print("[3/4] GENERATING PRE-SOLICITATION NOTICE")
    print("="*80)

    try:
        agent = PreSolicitationNoticeGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'requirements_content': requirements_content,
            'config': {
                'contract_type': 'services',
                'solicitation_release_days': 30
            }
        })

        # Save to file
        filepath = output_dir / 'pre_solicitation_notice.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'pre_solicitation_notice',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id')
        })

        print(f"\n✅ Pre-Solicitation Notice saved to: {filepath}\n")

    except Exception as e:
        print(f"\n❌ Error generating Pre-Solicitation Notice: {e}\n")

    # Document 4: Industry Day Materials
    print("="*80)
    print("[4/4] GENERATING INDUSTRY DAY MATERIALS")
    print("="*80)
    print("🔗 This will automatically cross-reference prior documents\n")

    try:
        agent = IndustryDayGeneratorAgent(api_key=api_key)
        result = agent.execute({
            'project_info': project_info,
            'requirements_content': requirements_content,
            'config': {
                'contract_type': 'services',
                'industry_day_date': '2025-12-15',
                'location': 'Virtual (MS Teams)'
            }
        })

        # Save to file
        filepath = output_dir / 'industry_day_materials.md'
        with open(filepath, 'w') as f:
            f.write(result['content'])

        results['documents'].append({
            'type': 'industry_day',
            'file': str(filepath),
            'metadata_id': result.get('metadata_id')
        })

        print(f"\n✅ Industry Day Materials saved to: {filepath}\n")

    except Exception as e:
        print(f"\n❌ Error generating Industry Day Materials: {e}\n")

    # ============================================================================
    # SUMMARY
    # ============================================================================

    print("\n" + "="*80)
    print("PHASE 1 GENERATION COMPLETE")
    print("="*80)

    print(f"\n📁 Output Directory: {output_dir}")
    print(f"\n✅ Generated {len(results['documents'])} documents:")

    for doc in results['documents']:
        print(f"   • {doc['type']}: {Path(doc['file']).name}")
        if doc.get('metadata_id'):
            print(f"     Metadata ID: {doc['metadata_id']}")

    # Show cross-reference info
    print("\n🔗 Cross-References:")
    store = DocumentMetadataStore()
    program_docs = [doc for doc in store.metadata['documents'].values()
                   if doc['program'] == project_info['program_name']]

    for doc in program_docs:
        refs = doc.get('references', {})
        if refs:
            print(f"   • {doc['type']} references:")
            for ref_type, ref_id in refs.items():
                print(f"     → {ref_type}")

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("\n1. Review generated documents in output folder")
    print("2. Run Phase 2 to generate solicitation documents:")
    print("   python scripts/generate_phase2_solicitation.py")
    print("\n   Phase 2 will automatically cross-reference these Phase 1 documents!")
    print("\n3. Or run all phases at once:")
    print("   python scripts/generate_all_phases.py")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
