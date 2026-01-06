"""
Full Pipeline Script - Generate and Evaluate Market Research Report
This script runs both the generation and evaluation in sequence
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path so we can import from core/
# This allows: from core.market_research import MarketResearchFiller
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from backend.core.market_research import MarketResearchFiller
from backend.core.evaluate_report import ReportEvaluator

def main():
    """
    Execute the full pipeline:
    1. Generate market research report
    2. Evaluate the generated report
    """
    
    print("="*70)
    print("MARKET RESEARCH REPORT - FULL PIPELINE")
    print("="*70)
    print()
    
    # Get API key from environment
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("\nPlease set it with: export ANTHROPIC_API_KEY='your-api-key-here'")
        return 1
    
    # Project information - CUSTOMIZE THIS FOR EACH PROJECT
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
    
    # =========================================================================
    # STEP 1: GENERATE MARKET RESEARCH REPORT
    # =========================================================================
    print("STEP 1: GENERATING MARKET RESEARCH REPORT")
    print("="*70)
    print()
    
    try:
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
        
        # Display generation summary
        print("\n" + "="*70)
        print("✅ GENERATION COMPLETE")
        print("="*70)
        print(f"\nGenerated {len(filled_content)} sections:")
        for section in filled_content.keys():
            print(f"  ✓ {section}")
        
        print("\n" + "="*70)
        print("FILES CREATED:")
        print("="*70)
        print("  📄 outputs/reports/filled_market_research_report.md")
        print("  📄 outputs/reports/filled_market_research_report.pdf (if conversion succeeded)")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during report generation: {e}")
        import traceback
        traceback.print_exc()
        print("\nAborting pipeline...")
        return 1
    
    # =========================================================================
    # STEP 2: EVALUATE GENERATED REPORT
    # =========================================================================
    print("\n" + "="*70)
    print("STEP 2: EVALUATING GENERATED REPORT")
    print("="*70)
    print()
    
    try:
        # Check if markdown file was created
        markdown_file = 'outputs/reports/filled_market_research_report.md'
        if not os.path.exists(markdown_file):
            print(f"❌ Error: Generated report file '{markdown_file}' not found")
            return 1
        
        # Initialize evaluator
        print("Initializing Report Evaluator...")
        evaluator = ReportEvaluator(api_key)
        
        # Run evaluation
        results = evaluator.evaluate_report(
            markdown_file,
            project_info
        )
        
        # Print summary
        print("\n" + "="*70)
        print("✅ EVALUATION COMPLETE")
        print("="*70)
        print(f"\nOverall Score: {results['overall_score']['score']}/100")
        print(f"Grade: {results['overall_score']['grade']}")
        print("\nBreakdown:")
        for category, score in results['overall_score']['breakdown'].items():
            print(f"  {category.replace('_', ' ').title()}: {score:.1f}/100")
        
        # Generate detailed evaluation report
        eval_output = "outputs/evaluations/evaluation_report.md"
        evaluator.generate_report(results, eval_output)
        
        # Convert evaluation to PDF
        print("\nConverting evaluation report to PDF...")
        try:
            from utils.convert_md_to_pdf import convert_markdown_to_pdf
            convert_markdown_to_pdf(
                'outputs/evaluations/evaluation_report.md', 
                'outputs/evaluations/evaluation_report.pdf'
            )
            print("✅ PDF evaluation report created: outputs/evaluations/evaluation_report.pdf")
        except Exception as e:
            print(f"⚠️  Could not convert evaluation to PDF: {e}")
            print("You can manually convert evaluation_report.md to PDF if needed.")
        
    except Exception as e:
        print(f"\n❌ Error during report evaluation: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "="*70)
    print("🎉 PIPELINE COMPLETE")
    print("="*70)
    print("\nGenerated Files:")
    print("  📄 outputs/reports/filled_market_research_report.md - Generated report (Markdown)")
    print("  📄 outputs/reports/filled_market_research_report.pdf - Generated report (PDF)")
    print("  📄 outputs/evaluations/evaluation_report.md - Quality evaluation (Markdown)")
    print("  📄 outputs/evaluations/evaluation_report.pdf - Quality evaluation (PDF)")
    print("\nNext Steps:")
    print("  1. Review the evaluation report for quality issues")
    print("  2. Address any high-priority legal risks")
    print("  3. Fix vague language and add missing citations")
    print("  4. Verify all facts match your project information")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
