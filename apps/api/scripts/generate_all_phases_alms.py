#!/usr/bin/env python3
"""
MASTER SCRIPT: Generate Complete ALMS Acquisition Package (All Phases)

Loads ALMS program requirements from document files and generates all
acquisition documents from pre-solicitation through award.

**ALMS Program Overview:**
- Program: Advanced Logistics Management System
- Cost: $2.5M development, $6.4M lifecycle
- Users: 2,800 across 15 Army installations
- Contract: FFP (80%) + T&M (20%, NTE $500K)
- Timeline: IOC June 2026, FOC December 2026

Generated Documents:
- Phase 1: Pre-Solicitation (4 documents)
- Phase 2: Solicitation/RFP (11 documents)
- Phase 3: Evaluation & Award (6+ documents)

All documents use actual ALMS requirements from document files.

Usage:
    python scripts/generate_all_phases_alms.py

Estimated Runtime: 10-15 minutes
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import time
import anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path

from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_processor import DocumentProcessor


# ============================================================================
# TOKEN TRACKING FOR COST REPORTING
# ============================================================================
# These classes wrap the Anthropic client to capture token usage for each
# document generation, enabling accurate cost reporting in the final summary.

class TokenTrackingMessages:
    """
    Wrapper around Anthropic messages API that tracks token usage.
    
    Intercepts calls to messages.create() and captures the input_tokens
    and output_tokens from each API response.
    """
    
    def __init__(self, real_messages):
        """
        Initialize with the real Anthropic messages object.
        
        Args:
            real_messages: The actual anthropic.Anthropic().messages object
        """
        self.real_messages = real_messages
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_count = 0
    
    def create(self, **kwargs):
        """
        Wrapper for messages.create() that captures token usage.
        
        Returns the actual API response while accumulating token counts.
        """
        response = self.real_messages.create(**kwargs)
        
        # Capture token usage from response
        if hasattr(response, 'usage'):
            self.total_input_tokens += response.usage.input_tokens
            self.total_output_tokens += response.usage.output_tokens
        
        self.call_count += 1
        return response
    
    def reset(self):
        """Reset token counters for next document."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_count = 0
    
    def get_usage(self):
        """
        Get accumulated token usage.
        
        Returns:
            Tuple of (input_tokens, output_tokens)
        """
        return (self.total_input_tokens, self.total_output_tokens)


class TokenTrackingClient:
    """
    Wrapper around Anthropic client that tracks all token usage.
    
    Drop-in replacement for anthropic.Anthropic() that intercepts
    API calls to capture token metrics for cost reporting.
    """
    
    # Claude Sonnet 4 pricing (per 1 million tokens)
    INPUT_COST_PER_MILLION = 3.00    # $3.00 per 1M input tokens
    OUTPUT_COST_PER_MILLION = 15.00  # $15.00 per 1M output tokens
    
    def __init__(self, api_key: str):
        """
        Initialize with API key.
        
        Args:
            api_key: Anthropic API key
        """
        self.real_client = anthropic.Anthropic(api_key=api_key)
        self.messages = TokenTrackingMessages(self.real_client.messages)
        
        # Cumulative totals across all documents
        self.cumulative_input_tokens = 0
        self.cumulative_output_tokens = 0
    
    def reset_for_document(self):
        """Reset tracking for a new document."""
        self.messages.reset()
    
    def get_document_usage(self):
        """
        Get token usage for current document.
        
        Returns:
            Tuple of (input_tokens, output_tokens)
        """
        return self.messages.get_usage()
    
    def finalize_document(self):
        """
        Finalize document tracking and add to cumulative totals.
        
        Returns:
            Tuple of (input_tokens, output_tokens, cost_usd) for the document
        """
        input_tokens, output_tokens = self.messages.get_usage()
        
        # Add to cumulative totals
        self.cumulative_input_tokens += input_tokens
        self.cumulative_output_tokens += output_tokens
        
        # Calculate cost
        cost = self.calculate_cost(input_tokens, output_tokens)
        
        return (input_tokens, output_tokens, cost)
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost based on token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        input_cost = (input_tokens / 1_000_000) * self.INPUT_COST_PER_MILLION
        output_cost = (output_tokens / 1_000_000) * self.OUTPUT_COST_PER_MILLION
        return round(input_cost + output_cost, 6)
    
    def get_cumulative_totals(self):
        """
        Get cumulative token usage across all documents.
        
        Returns:
            Dict with input_tokens, output_tokens, total_tokens, total_cost_usd
        """
        total_cost = self.calculate_cost(
            self.cumulative_input_tokens, 
            self.cumulative_output_tokens
        )
        return {
            'input_tokens': self.cumulative_input_tokens,
            'output_tokens': self.cumulative_output_tokens,
            'total_tokens': self.cumulative_input_tokens + self.cumulative_output_tokens,
            'total_cost_usd': total_cost
        }


# Global tracking client instance (initialized in main())
tracking_client = None


def patch_agent_for_tracking(agent):
    """
    Replace an agent's Anthropic client with the tracking client.
    
    This allows capturing token usage from all LLM calls made by the agent.
    
    Args:
        agent: Agent instance to patch
    """
    global tracking_client
    if tracking_client and hasattr(agent, 'client'):
        agent.client = tracking_client


# ============================================================================
# CONFIGURATION: Word Document Output
# ============================================================================
# Set to True to generate Microsoft Word (.docx) files alongside PDFs
# Word files include:
# - AI-generated section markers for review
# - Track changes enabled for editing workflow
# - Editable format for recipient approval
ENABLE_WORD_OUTPUT = True  # Set to False to disable Word generation


def print_banner(text, char="="):
    """Print formatted banner"""
    width = 80
    print("\n" + char * width)
    print(text.center(width))
    print(char * width + "\n")


def track_document_metrics(doc_name: str, doc_time: float) -> dict:
    """
    Finalize tracking for a document and return metrics.
    
    Called after each document generation to capture token usage and cost.
    
    Args:
        doc_name: Name of the document generated
        doc_time: Time taken to generate (seconds)
        
    Returns:
        Dict with document metrics (name, time, tokens, cost)
    """
    global tracking_client
    
    if tracking_client:
        input_tokens, output_tokens, cost = tracking_client.finalize_document()
    else:
        input_tokens, output_tokens, cost = 0, 0, 0.0
    
    metrics = {
        'name': doc_name,
        'time_seconds': round(doc_time, 2),
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'total_tokens': input_tokens + output_tokens,
        'cost_usd': cost
    }
    
    # Print inline metrics
    if input_tokens > 0 or output_tokens > 0:
        print(f"         💰 Tokens: {input_tokens + output_tokens:,} | Cost: ${cost:.4f}")
    
    return metrics


def reset_tracking_for_document():
    """Reset token tracking for a new document."""
    global tracking_client
    if tracking_client:
        tracking_client.reset_for_document()


def process_and_save_document(
    processor,
    content,
    output_path,
    doc_type,
    program_name,
    source_docs,
    project_info,
    display_name
):
    """
    Helper function to process and save a document with all enhancements

    Args:
        processor: DocumentProcessor instance
        content: Generated document content
        output_path: Path to save document
        doc_type: Document type identifier
        program_name: Program name
        source_docs: List of source document filenames
        project_info: Project information dict
        display_name: Display name for console output

    Returns:
        Processing result dict
    """
    result = processor.process_document(
        content=content,
        output_path=str(output_path),
        doc_type=doc_type,
        program_name=program_name,
        source_docs=source_docs,
        project_info=project_info,
        generate_pdf=True,
        generate_docx=ENABLE_WORD_OUTPUT,  # NEW: Generate Word documents if enabled
        generate_evaluation=True,
        add_citations=True
    )

    filename = Path(output_path).name
    print(f"      ✅ {display_name}")
    print(f"         📄 MD: {filename}")
    print(f"         📄 PDF: {filename.replace('.md', '.pdf')}")
    
    # NEW: Display Word file if generated
    if result.get('docx_path'):
        print(f"         📄 DOCX: {filename.replace('.md', '.docx')}")
    
    print(f"         📊 Score: {result['quality_score']}/100")

    # Display refinement metrics if applied
    if result.get('refinement_applied', False):
        print(f"         🔄 Refinement: +{result['refinement_improvement']} points ({result['refinement_iterations']} iteration{'s' if result['refinement_iterations'] != 1 else ''})")

    return result


def get_alms_requirements_from_documents():
    """
    Load ALMS requirements directly from document files

    Returns comprehensive requirements text for use in document generation
    """
    print("📚 Loading ALMS requirements from documents...")

    # Use absolute path based on script location to work from any directory
    # __file__ is in scripts/, parent.parent gets us to apps/api/
    script_dir = Path(__file__).resolve().parent.parent
    data_dir = script_dir / 'data' / 'documents'

    alms_docs = [
        data_dir / 'alms-kpp-ksa-complete.md',
        data_dir / '13_CDD_ALMS.md',
        data_dir / '9_acquisition_strategy_ALMS.md'
    ]

    all_content = []

    for doc_path in alms_docs:
        try:
            with open(doc_path, 'r') as f:
                content = f.read()
                all_content.append(content[:15000])  # First 15k chars of each
                print(f"  ✅ Loaded {doc_path.name}")
        except Exception as e:
            print(f"  ⚠️  Could not load {doc_path.name}: {e}")

    # Combine documents
    combined_requirements = "\n\n===== NEXT DOCUMENT =====\n\n".join(all_content)

    print(f"\n✅ Loaded {len(all_content)} ALMS documents")
    print(f"   Combined length: {len(combined_requirements):,} characters\n")

    return combined_requirements


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║            ALMS COMPLETE ACQUISITION PACKAGE GENERATION                    ║
║                                                                            ║
║  Program: Advanced Logistics Management System (ALMS)                     ║
║  Contract Value: $2.5M (Development) / $6.4M (Lifecycle)                  ║
║  Users: 2,800 across 15 Army installations                                ║
║                                                                            ║
║  Generates ALL acquisition documents using actual ALMS requirements       ║
║  from program document files:                                             ║
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
║  All documents use REAL ALMS data and are cross-referenced!               ║
║                                                                            ║
║  Runtime: Approximately 10-15 minutes                                     ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    # Get API keys
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY environment variable not set\n")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    print("✅ Anthropic API Key found")

    # Initialize token tracking client for cost reporting
    global tracking_client
    tracking_client = TokenTrackingClient(api_key)
    print("✅ Token tracking enabled for cost reporting")

    # Check for Tavily API key (optional)
    tavily_api_key = os.environ.get('TAVILY_API_KEY')
    if tavily_api_key:
        print("✅ Tavily API Key found - Web search enabled for market research")
    else:
        print("⚠️  Tavily API Key not found - Market research will use LLM knowledge only")
        print("   (Set TAVILY_API_KEY to enable real-time web search)\n")

    # Initialize Document Processor for PDF generation, quality reports, and citations
    print("="*80)
    print("INITIALIZING DOCUMENT PROCESSOR")
    print("="*80)
    print("\nEnhancements enabled:")
    print("  ✅ PDF generation for all documents")
    
    # NEW: Show Word output status
    if ENABLE_WORD_OUTPUT:
        print("  ✅ Word document (.docx) generation ENABLED")
        print("     • AI-generated section markers included")
        print("     • Track changes enabled for review workflow")
    else:
        print("  ⚠️  Word document generation DISABLED")
    
    print("  ✅ Quality evaluation reports")
    print("  ✅ Source document citations")
    print("  ✅ Progressive refinement loop (threshold: 85/100, max 2 iterations)")
    print()

    processor = DocumentProcessor(
        api_key=api_key,
        enable_progressive_refinement=True,
        quality_threshold=85,
        max_refinement_iterations=2
    )
    print("✅ Document Processor initialized with progressive refinement\n")

    # Source documents for citations
    alms_source_docs = [
        'alms-kpp-ksa-complete.md',
        '13_CDD_ALMS.md',
        '9_acquisition_strategy_ALMS.md'
    ]

    # Load ALMS requirements from documents
    print("="*80)
    print("LOADING ALMS REQUIREMENTS")
    print("="*80)
    print()

    try:
        alms_requirements = get_alms_requirements_from_documents()
    except Exception as e:
        print(f"❌ ERROR loading ALMS requirements: {e}")
        print("\nMake sure ALMS documents are in data/documents/")
        sys.exit(1)

    # ============================================================================
    # ALMS PROGRAM CONFIGURATION (from actual program data)
    # ============================================================================

    PROGRAM_NAME = 'Advanced Logistics Management System'
    PROGRAM_ACRONYM = 'ALMS'
    SOLICITATION_NUMBER = 'W56KGU-25-R-0042'

    # Based on actual ALMS program data
    project_info_base = {
        'program_name': PROGRAM_NAME,
        'program_acronym': PROGRAM_ACRONYM,
        'solicitation_number': SOLICITATION_NUMBER,
        'contracting_office': 'U.S. Army Contracting Command - Rock Island',
        'organization': 'United States Army',
        'command': 'PEO Combat Support & Combat Service Support',
        'estimated_value': '$2,500,000',  # Development cost
        'lifecycle_cost': '$6,425,000',  # Total 10-year lifecycle
        'period_of_performance': '36 months (12 base + 2 x 12 option)',
        'users': '2,800 users across 15 Army installations',
        'ioc_date': 'June 2026',
        'foc_date': 'December 2026',
        'acat_level': 'III',
        'contract_type': 'Firm Fixed Price (primary)',
        'naics_code': '541512',
        'set_aside': 'Small Business',
        'place_of_performance': 'Fort Lee, VA and CONUS installations'
    }

    print("="*80)
    print("ALMS PROGRAM CONFIGURATION")
    print("="*80)
    print(f"\nProgram: {PROGRAM_NAME} ({PROGRAM_ACRONYM})")
    print(f"Solicitation: {SOLICITATION_NUMBER}")
    print(f"Development Cost: $2.5M")
    print(f"Lifecycle Cost: $6.4M (10 years)")
    print(f"Users: 2,800 across 15 installations")
    print(f"Timeline: IOC Jun 2026, FOC Dec 2026")
    print(f"\nUsing REAL ALMS requirements from program documents")
    print("="*80)

    # Create master output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    master_output_dir = Path(f'output/alms_complete_acquisition_{timestamp}')
    master_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📁 Output Directory: {master_output_dir}\n")

    # Confirm before proceeding
    print("This will generate ~22 ALMS acquisition documents using actual ALMS requirements.")
    print("This includes Market Research Report (generated FIRST to reduce TBDs).")
    print("Estimated time: 12-18 minutes.\n")

    # Auto-proceed for automated runs
    import sys
    if sys.stdin.isatty():
        response = input("Proceed? (y/n): ").strip().lower()
        if response != 'y':
            print("\n❌ Generation cancelled by user.")
            sys.exit(0)
    else:
        print("Auto-proceeding (non-interactive mode)...\n")

    start_time = time.time()

    # Track all results
    all_results = {
        'program_name': PROGRAM_NAME,
        'start_time': datetime.now().isoformat(),
        'phases': [],
        'total_documents': 0,
        'total_cross_references': 0,
        'output_dir': str(master_output_dir),
        'uses_alms_documents': True
    }

    # ============================================================================
    # PHASE 0: MARKET RESEARCH REPORT (FOUNDATIONAL DOCUMENT)
    # ============================================================================

    print_banner("PHASE 0: MARKET RESEARCH REPORT (First Document)", "=")
    print("⚠️  IMPORTANT: Generating Market Research Report FIRST")
    print("This provides foundational data that reduces TBDs in all other documents:")
    print("  ✓ Vendor landscape and pricing data for IGCE")
    print("  ✓ Industry standards for PWS/SOW")
    print("  ✓ Competition analysis for Acquisition Plan")
    print("  ✓ Small business opportunities for Sources Sought")
    print("\nEstimated time: 1-2 minutes\n")

    phase0_start = time.time()

    # Import Market Research Report agent
    from agents.market_research_report_generator_agent import MarketResearchReportGeneratorAgent

    phase0_dir = master_output_dir / 'phase0_market_research'
    phase0_dir.mkdir(exist_ok=True)

    project_info_p0 = {**project_info_base}
    project_info_p0.update({
        'research_team': 'U.S. Army Contracting Command - Rock Island',
        'point_of_contact': 'MAJ Sarah Johnson',
        'email': 'sarah.m.johnson.mil@army.mil'
    })

    phase0_docs = []
    phase0_metrics = []  # Track metrics for each document

    # Generate Market Research Report
    print("  Generating Market Research Report...")
    try:
        reset_tracking_for_document()
        doc_start = time.time()
        
        agent = MarketResearchReportGeneratorAgent(
            api_key=api_key,
            tavily_api_key=tavily_api_key
        )
        patch_agent_for_tracking(agent)
        
        result = agent.execute({
            'project_info': project_info_p0,
            'requirements_content': alms_requirements,
            'config': {}
        })
        
        doc_time = time.time() - doc_start

        # Process and save with enhancements
        process_and_save_document(
            processor=processor,
            content=result['content'],
            output_path=phase0_dir / 'market_research_report.md',
            doc_type='market_research_report',
            program_name=PROGRAM_NAME,
            source_docs=alms_source_docs,
            project_info=project_info_p0,
            display_name="Market Research Report"
        )
        
        # Track metrics
        doc_metrics = track_document_metrics("Market Research Report", doc_time)
        phase0_metrics.append(doc_metrics)

        phase0_docs.append('market_research_report')

        # Store market research data for use in downstream documents
        market_research_data = result['extracted_data']
        print(f"\n  📊 Market Research Findings:")
        print(f"      • Vendor Count: {market_research_data.get('vendor_count_estimate', 'TBD')}")
        print(f"      • Small Business: {market_research_data.get('small_business_potential', 'TBD')}")
        print(f"      • Recommended Contract: {market_research_data.get('recommended_contract_type', 'TBD')}")

    except Exception as e:
        print(f"      ❌ Error: {e}")
        market_research_data = {}

    phase0_time = time.time() - phase0_start
    phase0_tokens = sum(m['total_tokens'] for m in phase0_metrics)
    phase0_cost = sum(m['cost_usd'] for m in phase0_metrics)

    all_results['phases'].append({
        'phase': 0,
        'name': 'Market Research',
        'documents': len(phase0_docs),
        'time_seconds': round(phase0_time, 1),
        'total_tokens': phase0_tokens,
        'cost_usd': round(phase0_cost, 4)
    })

    print(f"\n✅ Phase 0 complete: {len(phase0_docs)} document in {phase0_time:.1f}s | {phase0_tokens:,} tokens | ${phase0_cost:.4f}")
    print(f"   Market research data available for downstream documents to reduce TBDs\n")

    # ============================================================================
    # PHASE 1: PRE-SOLICITATION
    # ============================================================================

    print_banner("PHASE 1: PRE-SOLICITATION (Market Research)", "=")
    print("Generating 4 documents using ALMS requirements + market research data...")
    print("Estimated time: 2-3 minutes\n")

    phase1_start = time.time()

    # Import Phase 1 agents
    from agents.sources_sought_generator_agent import SourcesSoughtGeneratorAgent
    from agents.rfi_generator_agent import RFIGeneratorAgent
    from agents.pre_solicitation_notice_generator_agent import PreSolicitationNoticeGeneratorAgent
    from agents.industry_day_generator_agent import IndustryDayGeneratorAgent

    phase1_dir = master_output_dir / 'phase1_presolicitation'
    phase1_dir.mkdir(exist_ok=True)

    project_info_p1 = {**project_info_base}
    project_info_p1.update({
        'point_of_contact': 'MAJ Sarah Johnson',
        'email': 'sarah.m.johnson.mil@army.mil',
        'phone': '309-782-5000',
        'market_research_data': market_research_data  # Add market research data
    })

    phase1_docs = []
    phase1_metrics = []  # Track metrics for each document

    # Generate Phase 1 documents with ALMS requirements
    agents_p1 = [
        ('Sources Sought', SourcesSoughtGeneratorAgent, 'sources_sought.md'),
        ('RFI', RFIGeneratorAgent, 'rfi.md'),
        ('Pre-Solicitation Notice', PreSolicitationNoticeGeneratorAgent, 'pre_solicitation_notice.md'),
        ('Industry Day', IndustryDayGeneratorAgent, 'industry_day.md')
    ]

    for doc_name, AgentClass, filename in agents_p1:
        print(f"  Generating {doc_name}...")
        try:
            reset_tracking_for_document()
            doc_start = time.time()
            
            agent = AgentClass(api_key=api_key)
            patch_agent_for_tracking(agent)
            
            result = agent.execute({
                'project_info': project_info_p1,
                'requirements_content': alms_requirements,  # Using RAG requirements!
                'config': {'contract_type': 'services'}
            })
            
            doc_time = time.time() - doc_start

            filepath = phase1_dir / filename

            # Process document with enhancements (PDF, quality report, citations)
            process_and_save_document(
                processor=processor,
                content=result['content'],
                output_path=filepath,
                doc_type=filename.replace('.md', '').replace('_', ' '),
                program_name=PROGRAM_NAME,
                source_docs=alms_source_docs,
                project_info=project_info_p1,
                display_name=doc_name
            )
            
            # Track metrics
            doc_metrics = track_document_metrics(doc_name, doc_time)
            phase1_metrics.append(doc_metrics)

            phase1_docs.append(doc_name)

        except Exception as e:
            print(f"    ❌ Error: {e}")

    phase1_time = time.time() - phase1_start
    phase1_tokens = sum(m['total_tokens'] for m in phase1_metrics)
    phase1_cost = sum(m['cost_usd'] for m in phase1_metrics)

    all_results['phases'].append({
        'phase': 1,
        'name': 'Pre-Solicitation',
        'documents': len(phase1_docs),
        'time_seconds': round(phase1_time, 1),
        'total_tokens': phase1_tokens,
        'cost_usd': round(phase1_cost, 4)
    })

    print(f"\n✅ Phase 1 complete: {len(phase1_docs)} documents in {phase1_time:.1f}s | {phase1_tokens:,} tokens | ${phase1_cost:.4f}\n")
    time.sleep(1)

    # ============================================================================
    # PHASE 2: SOLICITATION/RFP
    # ============================================================================

    print_banner("PHASE 2: SOLICITATION/RFP", "=")
    print("Generating 11 documents using ALMS RAG requirements...")
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

    project_info_p2 = {**project_info_base}
    project_info_p2.update({
        'contracting_officer': 'LTC Michael Chen',
        'contract_specialist': 'Ms. Jennifer Martinez',
        'issue_date': '2025-09-01',
        'closing_date': '2025-10-15'
    })

    # ALMS-specific labor categories (from KPP document)
    labor_categories = [
        {'category': 'Program Manager (PMP)', 'hours': 2080, 'rate': 175},
        {'category': 'Cloud Solutions Architect (Senior)', 'hours': 2080, 'rate': 185},
        {'category': 'Full Stack Developer (Senior)', 'hours': 6240, 'rate': 155},
        {'category': 'Full Stack Developer (Mid)', 'hours': 8320, 'rate': 125},
        {'category': 'DevSecOps Engineer', 'hours': 4160, 'rate': 145},
        {'category': 'Security Engineer (CISSP)', 'hours': 2080, 'rate': 165},
        {'category': 'QA/Test Engineer', 'hours': 4160, 'rate': 115},
        {'category': 'Business Analyst', 'hours': 2080, 'rate': 125},
        {'category': 'Technical Writer', 'hours': 1040, 'rate': 95},
        {'category': 'Training Specialist', 'hours': 1040, 'rate': 85}
    ]

    # ALMS materials/ODCs
    materials = [
        {'description': 'AWS GovCloud hosting (FedRAMP Moderate)', 'cost': 180000},
        {'description': 'Software licenses (COTS platform)', 'cost': 150000},
        {'description': 'Mobile devices (tablets for warehouse)', 'cost': 85000},
        {'description': 'Barcode/RFID scanners', 'cost': 65000},
        {'description': 'SAP integration licenses', 'cost': 45000},
        {'description': 'Security tools (SIEM, vulnerability scanning)', 'cost': 35000},
        {'description': 'Training materials and courseware', 'cost': 25000}
    ]

    phase2_docs = []
    phase2_metrics = []  # Track metrics for each document

    # Foundation documents
    print("  Foundation Documents:")

    # IGCE
    print("    Generating IGCE...")
    try:
        reset_tracking_for_document()
        doc_start = time.time()
        
        agent = IGCEGeneratorAgent(api_key=api_key)
        patch_agent_for_tracking(agent)
        
        result = agent.execute({
            'project_info': project_info_p2,
            'requirements_content': alms_requirements,
            'labor_categories': labor_categories,
            'materials': materials,
            'config': {'contract_type': 'Firm Fixed Price'}
        })
        
        doc_time = time.time() - doc_start

        process_and_save_document(
            processor=processor,
            content=result['content'],
            output_path=phase2_dir / 'igce.md',
            doc_type='igce',
            program_name=PROGRAM_NAME,
            source_docs=alms_source_docs,
            project_info=project_info_p2,
            display_name=f"IGCE ({result['extracted_data']['total_cost_formatted']})"
        )
        
        doc_metrics = track_document_metrics("IGCE", doc_time)
        phase2_metrics.append(doc_metrics)

        phase2_docs.append('igce')
    except Exception as e:
        print(f"      ❌ Error: {e}")

    # Acquisition Plan
    print("    Generating Acquisition Plan...")
    try:
        reset_tracking_for_document()
        doc_start = time.time()
        
        agent = AcquisitionPlanGeneratorAgent(api_key=api_key)
        patch_agent_for_tracking(agent)
        
        result = agent.execute({
            'project_info': project_info_p2,
            'requirements_content': alms_requirements,
            'config': {'contract_type': 'Firm Fixed Price'}
        })
        
        doc_time = time.time() - doc_start

        process_and_save_document(
            processor=processor,
            content=result['content'],
            output_path=phase2_dir / 'acquisition_plan.md',
            doc_type='acquisition_plan',
            program_name=PROGRAM_NAME,
            source_docs=alms_source_docs,
            project_info=project_info_p2,
            display_name="Acquisition Plan"
        )
        
        doc_metrics = track_document_metrics("Acquisition Plan", doc_time)
        phase2_metrics.append(doc_metrics)

        phase2_docs.append('acquisition_plan')
    except Exception as e:
        print(f"      ❌ Error: {e}")

    # Requirements documents
    print("\n  Requirements Documents:")
    requirements_agents = [
        ('PWS', PWSWriterAgent, 'pws.md'),
        ('QASP', QASPGeneratorAgent, 'qasp.md')
    ]

    for name, AgentClass, filename in requirements_agents:
        print(f"    Generating {name}...")
        try:
            reset_tracking_for_document()
            doc_start = time.time()
            
            agent = AgentClass(api_key=api_key)
            patch_agent_for_tracking(agent)
            
            result = agent.execute({
                'project_info': project_info_p2,
                'requirements_content': alms_requirements,
                'config': {}
            })
            
            doc_time = time.time() - doc_start

            process_and_save_document(
                processor=processor,
                content=result['content'],
                output_path=phase2_dir / filename,
                doc_type=name.lower(),
                program_name=PROGRAM_NAME,
                source_docs=alms_source_docs,
                project_info=project_info_p2,
                display_name=name
            )
            
            doc_metrics = track_document_metrics(name, doc_time)
            phase2_metrics.append(doc_metrics)

            phase2_docs.append(name.lower())
        except Exception as e:
            print(f"      ❌ Error: {e}")

    # Sections
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
            reset_tracking_for_document()
            doc_start = time.time()
            
            agent = AgentClass(api_key=api_key)
            patch_agent_for_tracking(agent)
            
            result = agent.execute({
                'project_info': project_info_p2,
                'requirements_content': alms_requirements,
                'config': {}
            })
            
            doc_time = time.time() - doc_start

            process_and_save_document(
                processor=processor,
                content=result['content'],
                output_path=phase2_dir / filename,
                doc_type=name.lower().replace(' ', '_'),
                program_name=PROGRAM_NAME,
                source_docs=alms_source_docs,
                project_info=project_info_p2,
                display_name=name
            )
            
            doc_metrics = track_document_metrics(name, doc_time)
            phase2_metrics.append(doc_metrics)

            phase2_docs.append(name.lower().replace(' ', '_'))
        except Exception as e:
            print(f"      ❌ Error: {e}")

    # Forms
    print("\n  Forms:")
    print("    Generating SF-33...")
    try:
        reset_tracking_for_document()
        doc_start = time.time()
        
        agent = SF33GeneratorAgent(api_key=api_key)
        patch_agent_for_tracking(agent)
        
        result = agent.execute({
            'project_info': project_info_p2,
            'config': {}
        })
        
        doc_time = time.time() - doc_start

        process_and_save_document(
            processor=processor,
            content=result['content'],
            output_path=phase2_dir / 'sf33.md',
            doc_type='sf33',
            program_name=PROGRAM_NAME,
            source_docs=alms_source_docs,
            project_info=project_info_p2,
            display_name="SF-33"
        )
        
        doc_metrics = track_document_metrics("SF-33", doc_time)
        phase2_metrics.append(doc_metrics)

        phase2_docs.append('sf33')
    except Exception as e:
        print(f"      ❌ Error: {e}")

    phase2_time = time.time() - phase2_start
    phase2_tokens = sum(m['total_tokens'] for m in phase2_metrics)
    phase2_cost = sum(m['cost_usd'] for m in phase2_metrics)

    all_results['phases'].append({
        'phase': 2,
        'name': 'Solicitation/RFP',
        'documents': len(phase2_docs),
        'time_seconds': round(phase2_time, 1),
        'total_tokens': phase2_tokens,
        'cost_usd': round(phase2_cost, 4)
    })

    print(f"\n✅ Phase 2 complete: {len(phase2_docs)} documents in {phase2_time:.1f}s | {phase2_tokens:,} tokens | ${phase2_cost:.4f}\n")
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

    # ALMS-specific vendor data (based on acquisition strategy doc - 12 RFI responses, 4 small businesses)
    vendors = [
        {
            'vendor_name': 'CloudLogix Solutions Inc',
            'cage_code': '7X8Y9',
            'business_size': 'Small Business',
            'technical_score': 94,
            'management_score': 91,
            'past_performance': 'Excellent',
            'price': 2350000,
            'strengths': [
                'Strong Army logistics experience (3 similar contracts)',
                'Proven SAP S/4HANA integration capability',
                'FedRAMP Moderate authorized platform',
                'Excellent mobile app design with offline capability'
            ],
            'weaknesses': [
                'Limited CAC authentication experience',
                'Smaller team may pose risk for 15-site deployment'
            ]
        },
        {
            'vendor_name': 'MilSpec Cloud Technologies LLC',
            'cage_code': '1A2B3',
            'business_size': 'Small Business',
            'technical_score': 97,
            'management_score': 93,
            'past_performance': 'Excellent',
            'price': 2450000,
            'strengths': [
                'Outstanding technical solution with predictive analytics',
                'Deep DoD cloud experience (5 FedRAMP High systems)',
                'Innovative barcode/RFID integration approach',
                'Comprehensive training program'
            ],
            'weaknesses': [
                'Price slightly above government estimate',
                'Aggressive IOC timeline (risk of delay)'
            ]
        },
        {
            'vendor_name': 'Enterprise Logistics Systems Corp',
            'cage_code': '4C5D6',
            'business_size': 'Other than Small',
            'technical_score': 88,
            'management_score': 89,
            'past_performance': 'Satisfactory',
            'price': 2650000,
            'strengths': [
                'Large established company with resources',
                'Existing DLA integration experience',
                'Comprehensive support infrastructure'
            ],
            'weaknesses': [
                'Highest price proposal',
                'Generic solution lacking Army-specific features',
                'Past performance had schedule delays'
            ]
        }
    ]

    winner = {
        'vendor_name': 'MilSpec Cloud Technologies LLC',
        'justification': """
        MilSpec Cloud Technologies LLC provides best value to the Army based on
        comprehensive evaluation of technical merit, management approach, past
        performance, and price. While their price of $2,450,000 is $100K higher
        than CloudLogix Solutions' $2,350,000, the superior technical solution
        and outstanding past performance justify the cost premium.

        Key differentiators:
        - Highest technical score (97 vs 94) with innovative predictive analytics
        - FedRAMP High experience demonstrates security capability beyond requirements
        - Barcode/RFID integration approach reduces training burden
        - Past performance demonstrates consistent excellence on complex DoD projects

        The Source Selection Authority determines that MilSpec's technical
        advantages, particularly the predictive analytics capability supporting
        KPP-2 (Inventory Accuracy ≥95%), warrant the additional cost and provide
        best value to achieve ALMS mission success.
        """
    }

    phase3_docs = []
    phase3_metrics = []  # Track metrics for each document

    # Source Selection Plan
    print("  Generating Source Selection Plan...")
    try:
        reset_tracking_for_document()
        doc_start = time.time()
        
        agent = SourceSelectionPlanGeneratorAgent(api_key=api_key)
        patch_agent_for_tracking(agent)
        
        result = agent.execute({
            'project_info': project_info_p2,
            'config': {'evaluation_method': 'Best Value Trade-Off'}
        })
        
        doc_time = time.time() - doc_start

        process_and_save_document(
            processor=processor,
            content=result['content'],
            output_path=phase3_dir / 'source_selection_plan.md',
            doc_type='source_selection_plan',
            program_name=PROGRAM_NAME,
            source_docs=alms_source_docs,
            project_info=project_info_p2,
            display_name="Source Selection Plan"
        )
        
        doc_metrics = track_document_metrics("Source Selection Plan", doc_time)
        phase3_metrics.append(doc_metrics)

        phase3_docs.append('source_selection_plan')
    except Exception as e:
        print(f"    ❌ Error: {e}")

    # Evaluation Scorecards
    print("\n  Generating Evaluation Scorecards...")
    for vendor in vendors:
        vendor_name = vendor['vendor_name']
        print(f"    {vendor_name}...")
        try:
            reset_tracking_for_document()
            doc_start = time.time()
            
            agent = EvaluationScorecardGeneratorAgent(api_key=api_key)
            patch_agent_for_tracking(agent)
            
            result = agent.execute({
                'project_info': project_info_p2,
                'vendor_info': vendor,
                'config': {}
            })
            
            doc_time = time.time() - doc_start
            vendor_slug = vendor_name.lower().replace(' ', '_').replace('.', '')

            process_and_save_document(
                processor=processor,
                content=result['content'],
                output_path=phase3_dir / f'scorecard_{vendor_slug}.md',
                doc_type=f'scorecard_{vendor_slug}',
                program_name=PROGRAM_NAME,
                source_docs=alms_source_docs,
                project_info=project_info_p2,
                display_name=f"{vendor_name} (Score: {vendor['technical_score']}/100)"
            )
            
            doc_metrics = track_document_metrics(f"Scorecard - {vendor_name}", doc_time)
            phase3_metrics.append(doc_metrics)

            phase3_docs.append(f'scorecard_{vendor_slug}')
        except Exception as e:
            print(f"      ❌ Error: {e}")

    # Award documents
    print("\n  Generating Award Documents...")

    # SSDD
    print("    SSDD...")
    try:
        reset_tracking_for_document()
        doc_start = time.time()
        
        agent = SSDDGeneratorAgent(api_key=api_key)
        patch_agent_for_tracking(agent)
        
        result = agent.execute({
            'project_info': project_info_p2,
            'vendors': vendors,
            'winner': winner,
            'config': {}
        })
        
        doc_time = time.time() - doc_start

        process_and_save_document(
            processor=processor,
            content=result['content'],
            output_path=phase3_dir / 'ssdd.md',
            doc_type='ssdd',
            program_name=PROGRAM_NAME,
            source_docs=alms_source_docs,
            project_info=project_info_p2,
            display_name=f"SSDD (Winner: {winner['vendor_name']})"
        )
        
        doc_metrics = track_document_metrics("SSDD", doc_time)
        phase3_metrics.append(doc_metrics)

        phase3_docs.append('ssdd')
    except Exception as e:
        print(f"      ❌ Error: {e}")

    # SF-26
    print("    SF-26...")
    try:
        reset_tracking_for_document()
        doc_start = time.time()
        
        agent = SF26GeneratorAgent(api_key=api_key)
        patch_agent_for_tracking(agent)
        
        result = agent.execute({
            'project_info': project_info_p2,
            'winner': winner,
            'config': {}
        })
        
        doc_time = time.time() - doc_start

        process_and_save_document(
            processor=processor,
            content=result['content'],
            output_path=phase3_dir / 'sf26.md',
            doc_type='sf26',
            program_name=PROGRAM_NAME,
            source_docs=alms_source_docs,
            project_info=project_info_p2,
            display_name="SF-26"
        )
        
        doc_metrics = track_document_metrics("SF-26", doc_time)
        phase3_metrics.append(doc_metrics)

        phase3_docs.append('sf26')
    except Exception as e:
        print(f"      ❌ Error: {e}")

    # Award Notification
    print("    Award Notification...")
    try:
        reset_tracking_for_document()
        doc_start = time.time()
        
        agent = AwardNotificationGeneratorAgent(api_key=api_key)
        patch_agent_for_tracking(agent)
        
        result = agent.execute({
            'project_info': project_info_p2,
            'winner': winner,
            'config': {}
        })
        
        doc_time = time.time() - doc_start

        process_and_save_document(
            processor=processor,
            content=result['content'],
            output_path=phase3_dir / 'award_notification.md',
            doc_type='award_notification',
            program_name=PROGRAM_NAME,
            source_docs=alms_source_docs,
            project_info=project_info_p2,
            display_name="Award Notification"
        )
        
        doc_metrics = track_document_metrics("Award Notification", doc_time)
        phase3_metrics.append(doc_metrics)

        phase3_docs.append('award_notification')
    except Exception as e:
        print(f"      ❌ Error: {e}")

    phase3_time = time.time() - phase3_start
    phase3_tokens = sum(m['total_tokens'] for m in phase3_metrics)
    phase3_cost = sum(m['cost_usd'] for m in phase3_metrics)

    all_results['phases'].append({
        'phase': 3,
        'name': 'Evaluation & Award',
        'documents': len(phase3_docs),
        'time_seconds': round(phase3_time, 1),
        'total_tokens': phase3_tokens,
        'cost_usd': round(phase3_cost, 4)
    })

    print(f"\n✅ Phase 3 complete: {len(phase3_docs)} documents in {phase3_time:.1f}s | {phase3_tokens:,} tokens | ${phase3_cost:.4f}\n")

    # ============================================================================
    # FINAL SUMMARY
    # ============================================================================

    total_time = time.time() - start_time
    all_results['end_time'] = datetime.now().isoformat()
    all_results['total_time_seconds'] = round(total_time, 1)
    all_results['total_documents'] = len(phase0_docs) + len(phase1_docs) + len(phase2_docs) + len(phase3_docs)

    # Get token and cost totals from tracking client
    if tracking_client:
        token_totals = tracking_client.get_cumulative_totals()
        all_results['total_input_tokens'] = token_totals['input_tokens']
        all_results['total_output_tokens'] = token_totals['output_tokens']
        all_results['total_tokens'] = token_totals['total_tokens']
        all_results['total_cost_usd'] = token_totals['total_cost_usd']
    else:
        all_results['total_input_tokens'] = 0
        all_results['total_output_tokens'] = 0
        all_results['total_tokens'] = 0
        all_results['total_cost_usd'] = 0.0

    # Get cross-reference statistics
    store = DocumentMetadataStore()
    program_docs = [doc for doc in store.metadata['documents'].values()
                   if doc['program'] == PROGRAM_NAME]
    total_refs = sum(len(doc.get('references', {})) for doc in program_docs)
    all_results['total_cross_references'] = total_refs

    print_banner("ALMS COMPLETE ACQUISITION PACKAGE GENERATED", "=")

    print(f"📁 Output Directory: {master_output_dir}\n")

    print("📊 Generation Summary:\n")
    print(f"  {'Phase':<30} {'Docs':>6} {'Time':>10} {'Tokens':>12} {'Cost':>10}")
    print(f"  {'-'*30} {'-'*6} {'-'*10} {'-'*12} {'-'*10}")
    
    for phase in all_results['phases']:
        phase_name = f"Phase {phase['phase']} ({phase['name']})"
        tokens = phase.get('total_tokens', 0)
        cost = phase.get('cost_usd', 0.0)
        print(f"  {phase_name:<30} {phase['documents']:>6} {phase['time_seconds']:>9}s {tokens:>12,} ${cost:>9.4f}")
    
    print(f"  {'-'*30} {'-'*6} {'-'*10} {'-'*12} {'-'*10}")
    print(f"  {'TOTAL':<30} {all_results['total_documents']:>6} {total_time:>9.1f}s {all_results['total_tokens']:>12,} ${all_results['total_cost_usd']:>9.4f}")
    print()

    print(f"✅ Total Documents Generated: {all_results['total_documents']}")
    print(f"🔗 Total Cross-References: {total_refs}")
    print(f"⏱️  Total Time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"📚 ALMS Requirements: YES (from program documents)")
    
    # Token and cost summary
    print(f"\n💰 API Usage Summary:")
    print(f"   Input Tokens: {all_results['total_input_tokens']:,}")
    print(f"   Output Tokens: {all_results['total_output_tokens']:,}")
    print(f"   Total Tokens: {all_results['total_tokens']:,}")
    print(f"   Total Cost: ${all_results['total_cost_usd']:.4f}")
    if all_results['total_documents'] > 0:
        avg_cost = all_results['total_cost_usd'] / all_results['total_documents']
        print(f"   Cost per Document: ${avg_cost:.4f}")

    print("\n" + "="*80)
    print("ALMS COMPLETE ACQUISITION PACKAGE")
    print("="*80)
    print(f"\nPhase 0 (Market Research): {master_output_dir}/phase0_market_research/")
    print(f"Phase 1 (Pre-Solicitation): {master_output_dir}/phase1_presolicitation/")
    print(f"Phase 2 (Solicitation/RFP): {master_output_dir}/phase2_solicitation/")
    print(f"Phase 3 (Evaluation & Award): {master_output_dir}/phase3_evaluation_award/")

    print("\n🎉 All ALMS documents generated with actual requirements from program documents!")
    print("   Documents are cross-referenced and ready for use.")
    print("="*80 + "\n")

    # ============================================================================
    # SAVE GENERATION REPORT TO FILE
    # ============================================================================
    # Write a markdown report file with the complete generation summary
    # for historical tracking and documentation purposes.
    
    report_path = master_output_dir / 'GENERATION_REPORT.md'
    with open(report_path, 'w') as f:
        # Header
        f.write("# ALMS Complete Acquisition Package - Generation Report\n\n")
        f.write(f"**Generated:** {all_results['end_time']}\n\n")
        f.write(f"**Output Directory:** `{master_output_dir}`\n\n")
        
        # Generation Summary Table
        f.write("## Generation Summary\n\n")
        f.write("| Phase | Documents | Time | Tokens | Cost |\n")
        f.write("|-------|-----------|------|--------|------|\n")
        for phase in all_results['phases']:
            phase_name = f"Phase {phase['phase']} ({phase['name']})"
            tokens = phase.get('total_tokens', 0)
            cost = phase.get('cost_usd', 0.0)
            f.write(f"| {phase_name} | {phase['documents']} | {phase['time_seconds']}s | {tokens:,} | ${cost:.4f} |\n")
        f.write(f"| **TOTAL** | **{all_results['total_documents']}** | **{all_results['total_time_seconds']}s** | **{all_results['total_tokens']:,}** | **${all_results['total_cost_usd']:.4f}** |\n\n")
        
        # API Usage Summary
        f.write("## API Usage\n\n")
        f.write(f"- **Input Tokens:** {all_results['total_input_tokens']:,}\n")
        f.write(f"- **Output Tokens:** {all_results['total_output_tokens']:,}\n")
        f.write(f"- **Total Tokens:** {all_results['total_tokens']:,}\n")
        f.write(f"- **Total Cost:** ${all_results['total_cost_usd']:.4f}\n")
        if all_results['total_documents'] > 0:
            avg_cost = all_results['total_cost_usd'] / all_results['total_documents']
            f.write(f"- **Cost per Document:** ${avg_cost:.4f}\n")
        f.write("\n")
        
        # Statistics
        f.write("## Statistics\n\n")
        f.write(f"- **Total Documents:** {all_results['total_documents']}\n")
        f.write(f"- **Cross-References:** {all_results['total_cross_references']}\n")
        f.write(f"- **Total Time:** {all_results['total_time_seconds']}s ({all_results['total_time_seconds']/60:.1f} minutes)\n")
        f.write(f"- **ALMS Requirements:** YES (from program documents)\n\n")
        
        # Output Directories
        f.write("## Output Directories\n\n")
        f.write(f"- **Phase 0 (Market Research):** `{master_output_dir}/phase0_market_research/`\n")
        f.write(f"- **Phase 1 (Pre-Solicitation):** `{master_output_dir}/phase1_presolicitation/`\n")
        f.write(f"- **Phase 2 (Solicitation/RFP):** `{master_output_dir}/phase2_solicitation/`\n")
        f.write(f"- **Phase 3 (Evaluation & Award):** `{master_output_dir}/phase3_evaluation_award/`\n")
    
    print(f"📄 Report saved to: {report_path}")


if __name__ == '__main__':
    main()
