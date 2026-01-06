#!/usr/bin/env python3
"""
QUICKEST START: Generate Your First Acquisition Document

This is the simplest possible example - generates one IGCE document.
Runtime: ~30 seconds
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.igce_generator_agent import IGCEGeneratorAgent


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    Generate Your First IGCE Document                       ║
║                                                                            ║
║  This will generate an Independent Government Cost Estimate (IGCE) for    ║
║  a sample cloud computing project.                                        ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    # Check for API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY environment variable not set\n")
        print("To fix this:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        print("\nOr add it to your .env file")
        sys.exit(1)

    print("✅ API Key found\n")
    print("📋 Generating IGCE for: Cloud Infrastructure Services")
    print("⏳ Please wait 20-30 seconds...\n")

    # Initialize agent
    agent = IGCEGeneratorAgent(api_key=api_key)

    # Generate IGCE
    result = agent.execute({
        'project_info': {
            'program_name': 'Cloud Infrastructure Services',
            'solicitation_number': 'QUICK-START-001',
            'estimated_value': '$1,500,000',
            'period_of_performance': '24 months (12 base + 12 option)',
            'organization': 'Example Agency'
        },
        'labor_categories': [
            {'category': 'Cloud Architect', 'hours': 2080, 'rate': 165},
            {'category': 'DevOps Engineer', 'hours': 4160, 'rate': 125},
            {'category': 'System Administrator', 'hours': 4160, 'rate': 95}
        ],
        'materials': [
            {'description': 'AWS GovCloud Services', 'cost': 200000},
            {'description': 'Monitoring Tools', 'cost': 50000}
        ],
        'config': {
            'contract_type': 'Firm Fixed Price'
        }
    })

    # Display results
    print("\n" + "="*80)
    print("✅ SUCCESS! IGCE Generated")
    print("="*80 + "\n")

    print(f"💰 Total Cost: {result['extracted_data']['total_cost_formatted']}")
    print(f"📊 Labor Cost: ${result['extracted_data']['labor_cost']:,.2f}")
    print(f"📦 Materials: ${result['extracted_data']['materials_cost']:,.2f}")
    print(f"📅 Period: {result['extracted_data']['period_of_performance']}")

    # Save to file
    output_file = 'output/quick_start_igce.md'
    os.makedirs('output', exist_ok=True)

    with open(output_file, 'w') as f:
        f.write(result['content'])

    print(f"\n📄 Document saved to: {output_file}")
    print(f"   Open it to see the complete IGCE!")

    # Show metadata info
    print(f"\n🔗 Document ID: {result.get('metadata_id', 'N/A')}")
    print(f"   This ID allows other documents to cross-reference this IGCE")

    print("\n" + "="*80)
    print("Next Steps:")
    print("="*80)
    print("\n1. Open the generated file:")
    print(f"   cat {output_file}")
    print("\n2. Generate more documents that reference this IGCE:")
    print("   python examples/example_usage.py")
    print("\n3. Learn about the complete system:")
    print("   cat HOW_TO_USE.md")
    print("\n")


if __name__ == '__main__':
    main()
