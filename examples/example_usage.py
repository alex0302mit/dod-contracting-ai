#!/usr/bin/env python3
"""
Example: How to Use the DoD Acquisition Automation System

This script demonstrates three different ways to use the system:
1. Using orchestrators (easiest - generates multiple documents)
2. Using individual agents (most flexible)
3. Checking cross-references (understanding the system)
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def example_1_using_orchestrators():
    """
    EASIEST METHOD: Use orchestrators to generate multiple documents at once
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Using RFP Orchestrator (Generates Complete RFP Package)")
    print("="*80 + "\n")

    from agents.rfp_orchestrator import RFPOrchestrator

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("   Set it with: export ANTHROPIC_API_KEY='your-key'")
        return

    # Initialize orchestrator
    orchestrator = RFPOrchestrator(api_key=api_key)

    # Define your program
    project_info = {
        'program_name': 'Example Cloud Platform',
        'program_acronym': 'ECP',
        'solicitation_number': 'EXAMPLE-25-R-0001',
        'contracting_office': 'Example Contracting Office',
        'estimated_value': '$3,000,000',
        'period_of_performance': '24 months (12 month base + 1 x 12 month option)',
        'organization': 'Example Organization'
    }

    requirements = """
    The contractor shall provide cloud platform services including:

    1. Cloud Infrastructure
       - Deploy and manage cloud infrastructure on AWS GovCloud
       - Provide 99.9% uptime SLA
       - Implement auto-scaling and load balancing

    2. Security & Compliance
       - Achieve and maintain FedRAMP Moderate authorization
       - Implement NIST 800-53 security controls
       - Provide continuous monitoring

    3. Support Services
       - 24/7 technical support
       - Monthly security patches
       - Quarterly system upgrades
    """

    print("📋 Generating RFP package for: Example Cloud Platform")
    print("⏳ This may take a few minutes...\n")

    # Generate complete RFP package
    result = orchestrator.execute({
        'project_info': project_info,
        'requirements_content': requirements,
        'config': {
            'contract_type': 'Firm Fixed Price',
            'pws_type': 'pws',
            'include_qasp': True,
            'include_dd254': False
        }
    })

    print(f"\n✅ RFP Package Generated!")
    print(f"📁 Output folder: {result.get('output_path', 'output/')}")
    print(f"📄 Documents generated: {len(result.get('documents', []))}")
    print("\nDocuments include:")
    print("  - IGCE (Cost Estimate)")
    print("  - Acquisition Plan")
    print("  - PWS (Performance Work Statement)")
    print("  - QASP (Quality Assurance Plan)")
    print("  - Section L (Instructions to Offerors)")
    print("  - Section M (Evaluation Factors)")
    print("  - And more...")


def example_2_using_individual_agents():
    """
    MOST FLEXIBLE: Use individual agents for specific documents
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: Using Individual Agents (Generate Specific Documents)")
    print("="*80 + "\n")

    from agents.igce_generator_agent import IGCEGeneratorAgent
    from agents.pws_writer_agent import PWSWriterAgent

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not set")
        return

    # Step 1: Generate IGCE
    print("Step 1: Generating IGCE (Cost Estimate)...")
    igce_agent = IGCEGeneratorAgent(api_key=api_key)

    igce_result = igce_agent.execute({
        'project_info': {
            'program_name': 'Example Cybersecurity System',
            'solicitation_number': 'CYBER-25-R-0001',
            'estimated_value': '$2,000,000',
            'period_of_performance': '36 months',
            'organization': 'Example Cyber Command'
        },
        'labor_categories': [
            {'category': 'Cybersecurity Architect', 'hours': 2080, 'rate': 175},
            {'category': 'Senior Security Engineer', 'hours': 4160, 'rate': 140},
            {'category': 'Security Engineer', 'hours': 8320, 'rate': 110},
            {'category': 'Security Analyst', 'hours': 4160, 'rate': 95}
        ],
        'materials': [
            {'description': 'SIEM Software Licenses', 'cost': 150000},
            {'description': 'Security Appliances', 'cost': 100000}
        ],
        'config': {
            'contract_type': 'Firm Fixed Price'
        }
    })

    print(f"   ✅ IGCE Generated!")
    print(f"   💰 Total Cost: {igce_result['extracted_data']['total_cost_formatted']}")
    print(f"   📄 Saved to: output/")

    # Step 2: Generate PWS (automatically references IGCE)
    print("\nStep 2: Generating PWS (Performance Work Statement)...")
    print("   🔗 This will automatically cross-reference the IGCE!")

    pws_agent = PWSWriterAgent(api_key=api_key)

    pws_result = pws_agent.execute({
        'project_info': {
            'program_name': 'Example Cybersecurity System',  # SAME NAME!
            'solicitation_number': 'CYBER-25-R-0001'
        },
        'requirements_content': """
        The contractor shall provide cybersecurity services including:

        1. Security Operations Center (SOC)
           - 24/7/365 monitoring
           - Threat detection and response
           - Incident management

        2. Vulnerability Management
           - Weekly vulnerability scans
           - Quarterly penetration testing
           - Remediation support

        3. Compliance Support
           - NIST 800-171 compliance
           - RMF package development
           - ATO support
        """,
        'config': {
            'contract_type': 'Firm Fixed Price',
            'include_cdrl': True
        }
    })

    print(f"   ✅ PWS Generated!")
    print(f"   📄 Saved to: output/")
    print(f"   🔗 Cross-referenced: IGCE")


def example_3_checking_cross_references():
    """
    UNDERSTANDING: View cross-references between documents
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: Checking Cross-References")
    print("="*80 + "\n")

    from utils.document_metadata_store import DocumentMetadataStore

    store = DocumentMetadataStore()

    # Show overall statistics
    print("📊 Document Metadata Store Statistics:\n")
    stats = store.get_statistics()

    print(f"Total Documents: {stats['total_documents']}")
    print(f"Total Words: {stats['total_words']:,}")

    if stats['total_documents'] == 0:
        print("\n⚠️  No documents generated yet. Run Example 1 or 2 first!")
        return

    print(f"\nDocuments by Type:")
    for doc_type, count in sorted(stats['by_type'].items()):
        print(f"  • {doc_type}: {count}")

    print(f"\nDocuments by Program:")
    for program, count in sorted(stats['by_program'].items()):
        print(f"  • {program}: {count}")

    # Show cross-reference example
    print("\n🔗 Cross-Reference Example:")

    # Find an IGCE
    all_docs = store.list_documents(doc_type='igce')
    if all_docs:
        igce = all_docs[0]
        program_name = igce['program']

        print(f"\n📄 Document: {igce['type']} for '{program_name}'")
        print(f"   ID: {igce['id']}")
        print(f"   Generated: {igce['generated_date'][:10]}")

        # Find what references this IGCE
        referring_docs = store.get_referring_documents(igce['id'])
        if referring_docs:
            print(f"\n   Referenced by {len(referring_docs)} document(s):")
            for doc in referring_docs:
                print(f"     → {doc['type']}")
        else:
            print(f"\n   No documents reference this IGCE yet")

        # Find what this IGCE references
        refs = igce.get('references', {})
        if refs:
            print(f"\n   This IGCE references:")
            for ref_type, ref_id in refs.items():
                print(f"     ← {ref_type}: {ref_id}")


def main():
    """Main menu for examples"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║              DoD Acquisition Automation System - Examples                 ║
║                                                                            ║
║  This script demonstrates how to use the system to generate acquisition   ║
║  documents with automatic cross-referencing.                              ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    print("\nAvailable Examples:")
    print("  1. Generate complete RFP package (using orchestrator)")
    print("  2. Generate specific documents (using individual agents)")
    print("  3. Check cross-references in metadata store")
    print("  4. Run all examples")
    print("  0. Exit")

    choice = input("\nSelect an example (0-4): ").strip()

    if choice == '1':
        example_1_using_orchestrators()
    elif choice == '2':
        example_2_using_individual_agents()
    elif choice == '3':
        example_3_checking_cross_references()
    elif choice == '4':
        example_1_using_orchestrators()
        example_2_using_individual_agents()
        example_3_checking_cross_references()
    elif choice == '0':
        print("\n👋 Goodbye!")
        return
    else:
        print("\n❌ Invalid choice")
        return

    print("\n" + "="*80)
    print("✅ Example Complete!")
    print("="*80)
    print("\n📖 For more information:")
    print("   - Read HOW_TO_USE.md for detailed usage guide")
    print("   - Read SYSTEM_READY.md for system architecture")
    print("   - Read GETTING_STARTED.md for quick start")
    print("\n")


if __name__ == '__main__':
    main()
