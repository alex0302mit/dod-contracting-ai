"""
Main execution script for generating Market Research Reports
This file contains the project-specific configuration and runs the report generation
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path so we can import from core/
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from backend.core.market_research import MarketResearchFiller

def main():
    """Main execution function"""

    # Your project information - CUSTOMIZE THIS FOR EACH PROJECT
    project_info = {
        "program_name": "Advanced Logistics Management System (ALMS)",
        "author": "John Smith",
        "organization": "DOD/ARMY/LOGISTICS",
        "report_title": "Cloud-Based Inventory Management Services",
        "product_service": "Comprehensive cloud-based inventory management and logistics tracking system",
        "budget": "$2.5 million",
        "period_of_performance": "36 months (3 years)",
        "background_context": "Current inventory system is 15 years old and lacks modern cloud capabilities. Previous contract was $1.8M over 5 years.",
        "critical_requirements": "Real-time tracking, 99.9% uptime, integration with existing ERP systems, mobile access",
        "schedule_constraints": "Must be operational by Q2 FY2026",
        "vendor_research": "Conducted RFI in March 2025 with 12 responses, held industry day in April 2025 with 8 vendors",
        "potential_vendors": "TechLogistics Inc., CloudTrack Systems, MilSpec Software Solutions",
        "small_business_potential": "4 of 12 respondents were small businesses with relevant experience",
    }

    # API Key - REPLACE WITH YOUR ACTUAL API KEY
    # Best practice: Use environment variable instead of hardcoding
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it with: export ANTHROPIC_API_KEY='your-api-key-here'")
        print("Or uncomment the line below and add your key directly (not recommended for production)")
        # api_key = "your-api-key-here"
        return

    # Initialize the market research filler
    print("Initializing Market Research Filler...")
    filler = MarketResearchFiller(api_key)

    # Generate the report
    print(f"\nGenerating report for: {project_info['program_name']}")
    print(f"Author: {project_info['author']}")
    print(f"Organization: {project_info['organization']}\n")

    filled_content = filler.create_filled_document(
        pdf_path="templates/market_research_template.pdf",  # Updated path
        project_info=project_info,
        output_path="outputs/reports/filled_market_research_report.pdf",  # Updated path
        method="markdown"  # Creates markdown first, then PDF
    )

    # Display summary
    print("\n" + "="*60)
    print("GENERATION COMPLETE")
    print("="*60)
    print(f"\nGenerated {len(filled_content)} sections:")
    for section in filled_content.keys():
        print(f"  ✓ {section}")

    print("\n" + "="*60)
    print("FILES CREATED:")
    print("="*60)
    print("  📄 outputs/reports/filled_market_research_report.md")
    print("  📄 outputs/reports/filled_market_research_report.pdf (if conversion succeeded)")
    print("\nYou can now review and edit the files as needed.")

if __name__ == "__main__":
    main()
