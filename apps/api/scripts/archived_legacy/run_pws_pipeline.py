"""
Run PWS Pipeline: Generate Performance Work Statement documents
Enhanced with web search for performance benchmarks and current standards
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from backend.agents.pws_orchestrator import PWSOrchestrator
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever


def main():
    """
    Execute Performance Work Statement generation pipeline
    """
    
    print("\n" + "="*70)
    print("PERFORMANCE WORK STATEMENT (PWS) GENERATION PIPELINE")
    print("Performance-Based Service Contracting (PBSC)")
    print("="*70)
    print()
    
    # Load environment
    load_dotenv()
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    tavily_key = os.environ.get('TAVILY_API_KEY')
    
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        return 1
    
    if not tavily_key:
        print("⚠️  Warning: TAVILY_API_KEY not set - web search disabled")
        print("   For current performance benchmarks, add to .env: TAVILY_API_KEY='your-key'")
        print("   Continuing with RAG-only mode...\n")
    
    # Configuration
    vector_db_path = "data/vector_db/faiss_index"
    
    # Check vector store
    if not os.path.exists(f"{vector_db_path}.faiss"):
        print("⚠️  No vector store found!")
        print("\nPlease run setup_rag_system.py to index PWS guides")
        print("Recommended documents to index:")
        print("  - Performance-Based Service Contracting guide")
        print("  - Quality Assurance Surveillance Plan (QASP) examples")
        print("  - FAR 37.602 guidance")
        return 1
    
    # Project information - CUSTOMIZE THIS
    project_info = {
        "program_name": "Advanced Logistics Management System (ALMS)",
        "author": "John Smith",
        "organization": "DOD/ARMY/LOGISTICS",
        "date": "10/05/2025",
        "mission": "Modernize inventory tracking to improve operational readiness",
        "budget": "$2.5 million",
        "period_of_performance": "Base: 12 months, Option Year 1: 12 months, Option Year 2: 12 months",
        "current_challenges": "Legacy system causing delays, manual tracking errors, no mobile access",
        "desired_outcomes": "Real-time visibility, 99.9% uptime, ERP integration, mobile access",
        "performance_requirements": "System availability ≥99.9%, data accuracy ≥99.5%, response time <2 seconds",
        "quality_standards": "Customer satisfaction ≥4.5/5, defect rate <0.5%, on-time delivery ≥98%"
    }
    
    # PWS Sections Configuration - BASED ON PBSC PRINCIPLES
    # Follows FAR 37.602 Performance-Based Service Contracting
    pws_sections_config = [
        {
            "name": "1. Introduction",
            "guidance": """Provide overview of the Performance Work Statement (PWS) and its purpose.
Explain that this is a performance-based acquisition focused on outcomes, not methods.
Reference FAR 37.602 Performance-Based Service Contracting principles.
Example: This PWS establishes performance-based requirements for logistics management services, allowing contractor flexibility in methods while ensuring measurable outcomes.""",
            "focus": "general"
        },
        {
            "name": "2. Background",
            "guidance": """Describe the context, current situation, and need for services.
Include relevant history, capability gaps, and strategic importance.
Example: The current inventory system is 15 years old and lacks modern capabilities. Previous assessments identified need for real-time tracking and mobile access to improve operational readiness.""",
            "focus": "general"
        },
        {
            "name": "3. Scope of Work",
            "guidance": """Define the boundaries and extent of work to be performed.
Describe functional areas, systems, locations, and activities (WHAT, not HOW).
Example: The contractor shall provide cloud-based inventory management services including system design, deployment, integration, training, and ongoing support for Army logistics operations across CONUS and OCONUS locations.""",
            "focus": "general"
        },
        {
            "name": "4. Performance Requirements",
            "guidance": """Define measurable outcomes and performance objectives.
Each requirement must be Observable, Measurable, and Achievable.
Include specific metrics, thresholds, and measurement methods.
Examples:
- System Availability: Achieve 99.9% uptime during business hours
- Data Accuracy: Maintain inventory data accuracy ≥99.5%
- Response Time: System response time <2 seconds for 95% of transactions
- User Satisfaction: Achieve customer satisfaction rating ≥4.5/5""",
            "focus": "performance"
        },
        {
            "name": "5. Performance Standards",
            "guidance": """Establish minimum acceptable performance levels and quality thresholds.
Define what constitutes acceptable, marginal, and unacceptable performance.
Include acceptance criteria for each performance requirement.
Example Table:
| Performance Area | Acceptable | Marginal | Unacceptable |
|------------------|------------|----------|--------------|
| System Uptime | ≥99.9% | 99.5-99.8% | <99.5% |
| Response Time | <2 sec | 2-4 sec | >4 sec |""",
            "focus": "standards"
        },
        {
            "name": "6. Quality Assurance Surveillance Plan (QASP)",
            "guidance": """Define how contractor performance will be monitored and assessed.
Specify surveillance methods, frequency, thresholds, and responsible parties.
Include corrective action procedures and consequences.
Methods may include:
- Automated monitoring (24/7 system metrics)
- Periodic inspection (monthly/quarterly reviews)
- Random sampling (percentage-based quality checks)
- Customer feedback (user satisfaction surveys)
Example: System uptime monitored 24/7 via automated tools. Monthly reports showing compliance with 99.9% threshold. COR reviews quarterly.""",
            "focus": "qasp"
        },
        {
            "name": "7. Deliverables and Reporting",
            "guidance": """List all required deliverables, reports, and documentation.
Include format, frequency, submission process, and acceptance criteria.
Examples:
- Monthly Performance Report (due 5th of each month)
- Quarterly Quality Metrics Dashboard
- Annual System Assessment Report
- Incident Reports (within 24 hours of critical events)""",
            "focus": "general"
        },
        {
            "name": "8. Period of Performance",
            "guidance": """Specify contract duration including base and option periods.
Include key milestones and transition periods.
Example: 
- Base Period: 12 months from contract award
- Option Year 1: 12 months (if exercised)
- Option Year 2: 12 months (if exercised)
- Total potential: 36 months""",
            "focus": "general"
        },
        {
            "name": "9. Government-Furnished Resources",
            "guidance": """Identify resources, equipment, data, or access the Government will provide.
Include facilities, systems, security clearances, and information.
Example: Government will provide access to existing ERP systems, network infrastructure, and technical subject matter experts for coordination.""",
            "focus": "general"
        },
        {
            "name": "10. Applicable Standards and Regulations",
            "guidance": """List all applicable laws, regulations, standards, and policies.
Include cybersecurity, accessibility, environmental, and safety requirements.
Examples:
- FAR 37.602 - Performance-Based Service Contracting
- DFARS 252.239-7010 - Cloud Computing Services
- NIST SP 800-171 - Protecting Controlled Unclassified Information
- Section 508 - Accessibility Standards
- DoD Cloud Computing SRG - Security Requirements""",
            "focus": "general"
        },
        {
            "name": "11. Performance Incentives/Disincentives",
            "guidance": """Define any performance-based incentive fees or penalties (if applicable).
Tie incentives to measurable outcomes that exceed standards.
Example: Award fee of up to 5% for exceeding performance standards:
- System uptime ≥99.95%: +2% fee
- Customer satisfaction ≥4.8/5: +2% fee
- Zero critical defects: +1% fee

Disincentives for substandard performance:
- Uptime <99.5%: -1% per occurrence
- Critical defect: -0.5% per incident""",
            "focus": "qasp"
        },
        {
            "name": "12. Transition Requirements",
            "guidance": """Define requirements for contract start-up and eventual transition/closeout.
Include knowledge transfer, documentation, and continuity of services.
Example: Contractor shall provide 90-day transition-in period and 60-day transition-out period with complete knowledge transfer and documentation to successor contractor or Government personnel.""",
            "focus": "general"
        }
    ]
    
    try:
        # Initialize RAG
        print("Initializing RAG system...")
        vector_store = VectorStore(api_key, index_path=vector_db_path)
        
        if not vector_store.load():
            print("❌ Failed to load vector store")
            return 1
        
        retriever = Retriever(vector_store, top_k=5)
        print("✓ RAG system loaded\n")
        
        # Initialize PWS orchestrator with web search
        orchestrator = PWSOrchestrator(
            api_key=api_key,
            retriever=retriever,
            tavily_api_key=tavily_key,  # Enable web search for performance benchmarks
            model="claude-sonnet-4-20250514"
        )
        
        # Execute workflow
        result = orchestrator.execute_pws_workflow(
            project_info=project_info,
            pws_sections_config=pws_sections_config,
            output_path="outputs/pws/performance_work_statement.md"
        )
        
        if result['success']:
            print("\n" + "="*70)
            print("SUCCESS!")
            print("="*70)
            print(f"\nYour Performance Work Statement is ready:")
            print(f"  📄 PWS Document: {result['output_path']}")
            
            # Show evaluation report path
            eval_path = result['output_path'].replace('.md', '_evaluation_report.md')
            print(f"  📊 Evaluation Report: {eval_path}")
            
            print(f"\n⏱️  Time elapsed: {result['elapsed_time']:.1f}s")
            
            # Show quality summary
            workflow_state = result.get('workflow_state', {})
            eval_results = workflow_state.get('evaluation_results', {})
            if eval_results:
                scores = [r['score'] for r in eval_results.values()]
                avg_score = sum(scores) / len(scores)
                print(f"  ✓ Average Quality Score: {avg_score:.1f}/100")
            
            print("\n📋 Next steps:")
            print("  1. Review the PWS document")
            print("  2. Check the evaluation report for quality metrics")
            print("  3. Convert to PDF: python utils/convert_md_to_pdf.py")
            print("  4. Submit for legal/contracting review")
            print()
            return 0
        else:
            print("\n❌ PWS generation failed")
            return 1
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
