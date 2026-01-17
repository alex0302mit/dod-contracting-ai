#!/usr/bin/env python3
"""
Generation Benchmark Test
=========================

Generates all acquisition documents while tracking:
- Generation time per document
- Input/output token counts (from Anthropic API response)
- Cost per document (Claude Sonnet 4: $3/1M input, $15/1M output)

Usage:
    python scripts/test_generation_benchmark.py

Output:
    - Console summary table
    - JSON report: output/benchmark_YYYYMMDD_HHMMSS.json
    - Markdown report: output/benchmark_YYYYMMDD_HHMMSS.md

Dependencies:
    - anthropic (already installed)
    - All existing agents in apps/api/agents/
"""

import os
import sys
import time
import json
import anthropic
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Any

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add project root directory to path for imports (handles 'backend' symlink)
# Project structure: /project_root/apps/api/scripts/this_file.py
# Symlink: /project_root/backend -> /project_root/apps/api
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


# =============================================================================
# MOCK RETRIEVER FOR PWS AGENT
# =============================================================================

class MockRetriever:
    """
    Mock retriever that returns empty results for benchmark testing.
    
    The PWS agent requires a Retriever object, but for benchmarking purposes
    we don't need actual RAG results - we just need the agent to run.
    """
    
    def retrieve(self, query: str, k: int = 5) -> List:
        """Return empty results - PWS agent handles this gracefully."""
        return []


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DocumentMetrics:
    """
    Metrics captured for a single document generation.
    
    Tracks timing, token usage, and cost information for each document
    generated during the benchmark.
    """
    document_name: str          # Human-readable document name
    agent_name: str             # Agent class name
    phase: str                  # Acquisition phase (0-3)
    generation_time_seconds: float = 0.0
    input_tokens: int = 0       # Tokens sent to Claude
    output_tokens: int = 0      # Tokens received from Claude
    total_tokens: int = 0       # input + output
    input_cost_usd: float = 0.0
    output_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    word_count: int = 0         # Words in generated content
    status: str = "pending"     # pending, success, failed, skipped
    error_message: str = ""     # Error details if failed


@dataclass
class PhaseMetrics:
    """
    Aggregated metrics for an acquisition phase.
    """
    phase_name: str
    phase_number: int
    documents: int = 0
    total_time_seconds: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_words: int = 0


@dataclass 
class BenchmarkReport:
    """
    Complete benchmark report with all metrics.
    """
    benchmark_date: str = ""
    benchmark_id: str = ""
    program_name: str = ""
    
    # Summary metrics
    total_documents: int = 0
    successful_documents: int = 0
    failed_documents: int = 0
    total_time_seconds: float = 0.0
    total_time_minutes: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_words: int = 0
    
    # Averages
    avg_time_per_doc_seconds: float = 0.0
    avg_tokens_per_doc: int = 0
    avg_cost_per_doc_usd: float = 0.0
    
    # Pricing info
    model_used: str = "claude-sonnet-4-20250514"
    input_price_per_million: float = 3.00
    output_price_per_million: float = 15.00
    
    # Detailed data
    phases: List[Dict] = field(default_factory=list)
    documents: List[Dict] = field(default_factory=list)


# =============================================================================
# TOKEN TRACKING CLIENT WRAPPER
# =============================================================================

class TokenTrackingMessages:
    """
    Wrapper around Anthropic messages API that tracks token usage.
    
    This intercepts calls to messages.create() and captures the
    input_tokens and output_tokens from each API response.
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
    
    def get_usage(self) -> tuple:
        """
        Get accumulated token usage.
        
        Returns:
            Tuple of (input_tokens, output_tokens, call_count)
        """
        return (self.total_input_tokens, self.total_output_tokens, self.call_count)


class TokenTrackingClient:
    """
    Wrapper around Anthropic client that tracks all token usage.
    
    Drop-in replacement for anthropic.Anthropic() that intercepts
    API calls to capture token metrics.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize with API key.
        
        Args:
            api_key: Anthropic API key
        """
        self.real_client = anthropic.Anthropic(api_key=api_key)
        self.messages = TokenTrackingMessages(self.real_client.messages)
    
    def reset_tracking(self):
        """Reset all token tracking counters."""
        self.messages.reset()
    
    def get_token_usage(self) -> tuple:
        """
        Get current token usage.
        
        Returns:
            Tuple of (input_tokens, output_tokens, call_count)
        """
        return self.messages.get_usage()


# =============================================================================
# GENERATION BENCHMARK CLASS
# =============================================================================

class GenerationBenchmark:
    """
    Main benchmark orchestrator for document generation.
    
    Generates all 18 core acquisition documents while tracking:
    - Time per document
    - Token usage per document  
    - Cost per document
    
    Produces detailed reports in JSON, Markdown, and console formats.
    """
    
    # Claude Sonnet 4 pricing (per 1 million tokens)
    INPUT_COST_PER_MILLION = 3.00    # $3.00 per 1M input tokens
    OUTPUT_COST_PER_MILLION = 15.00  # $15.00 per 1M output tokens
    MODEL = "claude-sonnet-4-20250514"
    
    def __init__(self, api_key: str, program_name: str = "Benchmark Test Program"):
        """
        Initialize the benchmark.
        
        Args:
            api_key: Anthropic API key
            program_name: Name for the test program
        """
        self.api_key = api_key
        self.program_name = program_name
        self.tracking_client = TokenTrackingClient(api_key)
        
        # Results storage
        self.document_metrics: List[DocumentMetrics] = []
        self.phase_metrics: Dict[int, PhaseMetrics] = {}
        
        # Timing
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
        # Output directory
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(f'output/benchmark_{self.timestamp}')
        
        # Project info for agents
        self.project_info = {
            'program_name': program_name,
            'program_acronym': 'BENCH',
            'solicitation_number': 'BENCH-25-R-0001',
            'contracting_office': 'Benchmark Contracting Office',
            'organization': 'Test Organization',
            'estimated_value': '$2,500,000',
            'period_of_performance': '36 months',
            'contract_type': 'Firm Fixed Price',
            'naics_code': '541512',
            'set_aside': 'Small Business',
        }
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> tuple:
        """
        Calculate cost based on token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Tuple of (input_cost, output_cost, total_cost) in USD
        """
        input_cost = (input_tokens / 1_000_000) * self.INPUT_COST_PER_MILLION
        output_cost = (output_tokens / 1_000_000) * self.OUTPUT_COST_PER_MILLION
        total_cost = input_cost + output_cost
        return (round(input_cost, 6), round(output_cost, 6), round(total_cost, 6))
    
    def _patch_agent_client(self, agent):
        """
        Replace agent's Anthropic client with our tracking client.
        
        This allows us to capture token usage from all LLM calls
        made by the agent during document generation.
        
        Args:
            agent: Agent instance to patch
        """
        # Reset tracking for new document
        self.tracking_client.reset_tracking()
        
        # Replace the agent's client with our tracking client
        agent.client = self.tracking_client
    
    def benchmark_single_document(
        self,
        agent_class,
        agent_name: str,
        document_name: str,
        phase: str,
        phase_number: int,
        task: Dict[str, Any],
        agent_kwargs: Optional[Dict[str, Any]] = None
    ) -> DocumentMetrics:
        """
        Benchmark a single document generation.
        
        Args:
            agent_class: The agent class to instantiate
            agent_name: Name of the agent class
            document_name: Human-readable document name
            phase: Phase name (e.g., "Pre-Solicitation")
            phase_number: Phase number (0-3)
            task: Task dictionary to pass to agent.execute()
            agent_kwargs: Optional dict of kwargs for agent constructor.
                          If None, defaults to {'api_key': self.api_key}
                          If empty dict {}, initializes agent with no args.
            
        Returns:
            DocumentMetrics with captured timing and token data
        """
        metrics = DocumentMetrics(
            document_name=document_name,
            agent_name=agent_name,
            phase=phase
        )
        
        print(f"  Generating {document_name}...", end=" ", flush=True)
        
        try:
            # Initialize agent with appropriate kwargs
            # Default: pass api_key. Empty dict {} means no args. Custom dict for special cases.
            if agent_kwargs is None:
                # Default: standard agent with api_key
                agent = agent_class(api_key=self.api_key)
            elif agent_kwargs == {}:
                # No arguments (template-based agents like QASP, SF-33)
                agent = agent_class()
            else:
                # Custom kwargs (e.g., PWS with retriever)
                agent = agent_class(**agent_kwargs)
            
            # Patch client for token tracking
            self._patch_agent_client(agent)
            
            # Time the generation
            start = time.time()
            result = agent.execute(task)
            elapsed = time.time() - start
            
            # Get token usage from tracking client
            input_tokens, output_tokens, call_count = self.tracking_client.get_token_usage()
            
            # Calculate costs
            input_cost, output_cost, total_cost = self.calculate_cost(input_tokens, output_tokens)
            
            # Extract content and word count
            content = result.get('content', '') or result.get('igce_content', '') or ''
            word_count = len(content.split()) if content else 0
            
            # Update metrics
            metrics.generation_time_seconds = round(elapsed, 2)
            metrics.input_tokens = input_tokens
            metrics.output_tokens = output_tokens
            metrics.total_tokens = input_tokens + output_tokens
            metrics.input_cost_usd = input_cost
            metrics.output_cost_usd = output_cost
            metrics.total_cost_usd = total_cost
            metrics.word_count = word_count
            metrics.status = "success"
            
            print(f"✓ {elapsed:.1f}s | {input_tokens + output_tokens:,} tokens | ${total_cost:.4f}")
            
        except Exception as e:
            metrics.status = "failed"
            metrics.error_message = str(e)
            print(f"✗ Error: {str(e)[:50]}")
        
        # Store metrics
        self.document_metrics.append(metrics)
        
        # Update phase metrics
        if phase_number not in self.phase_metrics:
            self.phase_metrics[phase_number] = PhaseMetrics(
                phase_name=phase,
                phase_number=phase_number
            )
        
        pm = self.phase_metrics[phase_number]
        pm.documents += 1
        pm.total_time_seconds += metrics.generation_time_seconds
        pm.total_input_tokens += metrics.input_tokens
        pm.total_output_tokens += metrics.output_tokens
        pm.total_tokens += metrics.total_tokens
        pm.total_cost_usd += metrics.total_cost_usd
        pm.total_words += metrics.word_count
        
        return metrics
    
    def run_full_benchmark(self) -> BenchmarkReport:
        """
        Run the complete benchmark on all 18 core documents.
        
        Generates documents across all 4 phases, tracking metrics
        for each one.
        
        Returns:
            BenchmarkReport with complete results
        """
        print("=" * 70)
        print("DOCUMENT GENERATION BENCHMARK")
        print("=" * 70)
        print(f"Program: {self.program_name}")
        print(f"Model: {self.MODEL}")
        print(f"Pricing: ${self.INPUT_COST_PER_MILLION}/1M input, ${self.OUTPUT_COST_PER_MILLION}/1M output")
        print("=" * 70)
        
        self.start_time = time.time()
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # =================================================================
        # PHASE 0: Market Research (1 document)
        # =================================================================
        print(f"\n{'='*70}")
        print("PHASE 0: MARKET RESEARCH (1 document)")
        print("="*70)
        
        from backend.agents.market_research_report_generator_agent import MarketResearchReportGeneratorAgent
        
        self.benchmark_single_document(
            agent_class=MarketResearchReportGeneratorAgent,
            agent_name="MarketResearchReportGeneratorAgent",
            document_name="Market Research Report",
            phase="Market Research",
            phase_number=0,
            task={
                'project_info': self.project_info,
                'requirements_content': 'Cloud-based logistics management system requirements',
                'config': {}
            }
        )
        
        # =================================================================
        # PHASE 1: Pre-Solicitation (4 documents)
        # =================================================================
        print(f"\n{'='*70}")
        print("PHASE 1: PRE-SOLICITATION (4 documents)")
        print("="*70)
        
        from backend.agents.sources_sought_generator_agent import SourcesSoughtGeneratorAgent
        from backend.agents.rfi_generator_agent import RFIGeneratorAgent
        from backend.agents.pre_solicitation_notice_generator_agent import PreSolicitationNoticeGeneratorAgent
        from backend.agents.industry_day_generator_agent import IndustryDayGeneratorAgent
        
        phase1_agents = [
            (SourcesSoughtGeneratorAgent, "SourcesSoughtGeneratorAgent", "Sources Sought"),
            (RFIGeneratorAgent, "RFIGeneratorAgent", "Request for Information (RFI)"),
            (PreSolicitationNoticeGeneratorAgent, "PreSolicitationNoticeGeneratorAgent", "Pre-Solicitation Notice"),
            (IndustryDayGeneratorAgent, "IndustryDayGeneratorAgent", "Industry Day Notice"),
        ]
        
        for agent_class, agent_name, doc_name in phase1_agents:
            self.benchmark_single_document(
                agent_class=agent_class,
                agent_name=agent_name,
                document_name=doc_name,
                phase="Pre-Solicitation",
                phase_number=1,
                task={
                    'project_info': self.project_info,
                    'requirements_content': 'Cloud-based logistics management system',
                    'config': {'contract_type': 'services'}
                }
            )
        
        # =================================================================
        # PHASE 2: Solicitation/RFP (11 documents)
        # =================================================================
        print(f"\n{'='*70}")
        print("PHASE 2: SOLICITATION/RFP (11 documents)")
        print("="*70)
        
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
        
        # Labor categories for IGCE
        labor_categories = [
            {'category': 'Program Manager', 'hours': 2080, 'rate': 175},
            {'category': 'Senior Developer', 'hours': 4160, 'rate': 155},
            {'category': 'Developer', 'hours': 6240, 'rate': 125},
            {'category': 'QA Engineer', 'hours': 2080, 'rate': 115},
            {'category': 'Technical Writer', 'hours': 1040, 'rate': 95},
        ]
        
        # IGCE
        self.benchmark_single_document(
            agent_class=IGCEGeneratorAgent,
            agent_name="IGCEGeneratorAgent",
            document_name="IGCE",
            phase="Solicitation",
            phase_number=2,
            task={
                'project_info': self.project_info,
                'labor_categories': labor_categories,
                'config': {'contract_type': 'Firm Fixed Price'}
            }
        )
        
        # Acquisition Plan
        self.benchmark_single_document(
            agent_class=AcquisitionPlanGeneratorAgent,
            agent_name="AcquisitionPlanGeneratorAgent",
            document_name="Acquisition Plan",
            phase="Solicitation",
            phase_number=2,
            task={
                'project_info': self.project_info,
                'requirements_content': 'Cloud-based logistics management system',
                'config': {'contract_type': 'Firm Fixed Price'}
            }
        )
        
        # PWS - requires api_key + retriever (using mock retriever for benchmark)
        mock_retriever = MockRetriever()
        self.benchmark_single_document(
            agent_class=PWSWriterAgent,
            agent_name="PWSWriterAgent",
            document_name="Performance Work Statement (PWS)",
            phase="Solicitation",
            phase_number=2,
            task={
                'project_info': self.project_info,
                'requirements_content': 'Cloud-based logistics management system',
                'config': {}
            },
            agent_kwargs={'api_key': self.api_key, 'retriever': mock_retriever}
        )
        
        # QASP - special handling: different execute() signature (requires file paths)
        self._benchmark_qasp()
        
        # RFP Sections B, H, I, K, L, M
        section_agents = [
            (SectionBGeneratorAgent, "SectionBGeneratorAgent", "Section B - Supplies/Services"),
            (SectionHGeneratorAgent, "SectionHGeneratorAgent", "Section H - Special Requirements"),
            (SectionIGeneratorAgent, "SectionIGeneratorAgent", "Section I - Contract Clauses"),
            (SectionKGeneratorAgent, "SectionKGeneratorAgent", "Section K - Representations"),
            (SectionLGeneratorAgent, "SectionLGeneratorAgent", "Section L - Instructions"),
            (SectionMGeneratorAgent, "SectionMGeneratorAgent", "Section M - Evaluation Factors"),
        ]
        
        for agent_class, agent_name, doc_name in section_agents:
            self.benchmark_single_document(
                agent_class=agent_class,
                agent_name=agent_name,
                document_name=doc_name,
                phase="Solicitation",
                phase_number=2,
                task={
                    'project_info': self.project_info,
                    'requirements_content': 'Cloud-based logistics management system',
                    'config': {}
                }
            )
        
        # SF-33 - special handling: different execute() signature
        # SF33GeneratorAgent.execute(work_statement_path, output_path, solicitation_config)
        # We'll benchmark it separately with custom execution logic
        self._benchmark_sf33()
        
        # =================================================================
        # PHASE 3: Evaluation & Award (4 documents)
        # =================================================================
        print(f"\n{'='*70}")
        print("PHASE 3: EVALUATION & AWARD (4 documents)")
        print("="*70)
        
        from backend.agents.source_selection_plan_generator_agent import SourceSelectionPlanGeneratorAgent
        from backend.agents.ssdd_generator_agent import SSDDGeneratorAgent
        from backend.agents.sf26_generator_agent import SF26GeneratorAgent
        from backend.agents.award_notification_generator_agent import AwardNotificationGeneratorAgent
        
        # Source Selection Plan
        self.benchmark_single_document(
            agent_class=SourceSelectionPlanGeneratorAgent,
            agent_name="SourceSelectionPlanGeneratorAgent",
            document_name="Source Selection Plan",
            phase="Evaluation & Award",
            phase_number=3,
            task={
                'project_info': self.project_info,
                'config': {'evaluation_method': 'Best Value Trade-Off'}
            }
        )
        
        # Winner info for award documents
        winner_info = {
            'vendor_name': 'Benchmark Winner Inc.',
            'cage_code': '12345',
            'price': 2500000,
            'justification': 'Best value determination based on technical excellence.'
        }
        
        vendors = [
            {'vendor_name': 'Benchmark Winner Inc.', 'technical_score': 95, 'price': 2500000},
            {'vendor_name': 'Runner Up LLC', 'technical_score': 88, 'price': 2300000},
        ]
        
        # SSDD
        self.benchmark_single_document(
            agent_class=SSDDGeneratorAgent,
            agent_name="SSDDGeneratorAgent",
            document_name="Source Selection Decision Document (SSDD)",
            phase="Evaluation & Award",
            phase_number=3,
            task={
                'project_info': self.project_info,
                'vendors': vendors,
                'winner': winner_info,
                'config': {}
            }
        )
        
        # SF-26
        self.benchmark_single_document(
            agent_class=SF26GeneratorAgent,
            agent_name="SF26GeneratorAgent",
            document_name="SF-26 Award Form",
            phase="Evaluation & Award",
            phase_number=3,
            task={
                'project_info': self.project_info,
                'winner': winner_info,
                'config': {}
            }
        )
        
        # Award Notification
        self.benchmark_single_document(
            agent_class=AwardNotificationGeneratorAgent,
            agent_name="AwardNotificationGeneratorAgent",
            document_name="Award Notification",
            phase="Evaluation & Award",
            phase_number=3,
            task={
                'project_info': self.project_info,
                'winner': winner_info,
                'config': {}
            }
        )
        
        # =================================================================
        # GENERATE REPORT
        # =================================================================
        self.end_time = time.time()
        
        report = self._generate_report()
        self._print_summary(report)
        self._save_reports(report)
        
        return report
        
    def _benchmark_sf33(self):
        """
        Special benchmark for SF-33 which has a different execute() signature.
        
        SF33GeneratorAgent.execute() takes:
        - work_statement_path: Path to PWS/SOO/SOW markdown file
        - output_path: Path to save filled SF33 PDF
        - solicitation_config: Optional configuration overrides
        """
        from backend.agents.sf33_generator_agent import SF33GeneratorAgent
        
        metrics = DocumentMetrics(
            document_name="SF-33 Solicitation Form",
            agent_name="SF33GeneratorAgent",
            phase="Solicitation"
        )
        
        print(f"  Generating SF-33 Solicitation Form...", end=" ", flush=True)
        
        try:
            # Initialize SF33 agent with correct template path
            sf33_template_path = str(project_root / 'apps' / 'api' / 'data' / 'documents' / 'SF33.pdf')
            agent = SF33GeneratorAgent(sf33_template_path=sf33_template_path)
            
            # SF33 needs a work statement file - create a temporary one
            # Using the output directory for temp files
            temp_pws_path = self.output_dir / 'temp_pws.md'
            temp_output_path = self.output_dir / 'sf33_output.pdf'
            
            # Create a minimal PWS content for the SF33 to process
            temp_pws_content = f"""# Performance Work Statement
## {self.project_info['program_name']}

**Solicitation Number:** {self.project_info['solicitation_number']}
**Contracting Office:** {self.project_info['contracting_office']}
**Contract Type:** {self.project_info['contract_type']}
**Period of Performance:** {self.project_info['period_of_performance']}
**Estimated Value:** {self.project_info['estimated_value']}

## 1.0 Background
Cloud-based logistics management system for government operations.

## 2.0 Scope
Development and deployment of a modern logistics platform.

## 3.0 Requirements
- System design and development
- Testing and quality assurance
- Deployment and training
- Ongoing maintenance and support
"""
            with open(temp_pws_path, 'w') as f:
                f.write(temp_pws_content)
            
            # Patch client for token tracking (if SF33 uses LLM)
            self._patch_agent_client(agent)
            
            # Time the generation
            start = time.time()
            result = agent.execute(
                work_statement_path=str(temp_pws_path),
                output_path=str(temp_output_path),
                solicitation_config={
                    'solicitation_number': self.project_info['solicitation_number'],
                    'contract_type': self.project_info['contract_type'],
                },
                verbose=False
            )
            elapsed = time.time() - start
            
            # Get token usage
            input_tokens, output_tokens, call_count = self.tracking_client.get_token_usage()
            
            # Calculate costs
            input_cost, output_cost, total_cost = self.calculate_cost(input_tokens, output_tokens)
            
            # Update metrics
            metrics.generation_time_seconds = round(elapsed, 2)
            metrics.input_tokens = input_tokens
            metrics.output_tokens = output_tokens
            metrics.total_tokens = input_tokens + output_tokens
            metrics.input_cost_usd = input_cost
            metrics.output_cost_usd = output_cost
            metrics.total_cost_usd = total_cost
            metrics.status = "success"
            
            print(f"✓ {elapsed:.1f}s | {input_tokens + output_tokens:,} tokens | ${total_cost:.4f}")
            
        except Exception as e:
            metrics.status = "failed"
            metrics.error_message = str(e)
            print(f"✗ Error: {str(e)[:50]}")
        
        # Store metrics
        self.document_metrics.append(metrics)
        
        # Update phase metrics for Phase 2 (Solicitation)
        phase_number = 2
        if phase_number not in self.phase_metrics:
            self.phase_metrics[phase_number] = PhaseMetrics(
                phase_name="Solicitation",
                phase_number=phase_number
            )
        
        pm = self.phase_metrics[phase_number]
        pm.documents += 1
        pm.total_time_seconds += metrics.generation_time_seconds
        pm.total_input_tokens += metrics.input_tokens
        pm.total_output_tokens += metrics.output_tokens
        pm.total_tokens += metrics.total_tokens
        pm.total_cost_usd += metrics.total_cost_usd
        pm.total_words += metrics.word_count
    
    def _benchmark_qasp(self):
        """
        Special benchmark for QASP which has a different execute() signature.
        
        QASPGeneratorAgent.execute() takes:
        - pws_path: Path to PWS markdown file
        - output_path: Path to save QASP output
        - config: Optional configuration dict
        - verbose: Print progress
        """
        from backend.agents.qasp_generator_agent import QASPGeneratorAgent
        
        metrics = DocumentMetrics(
            document_name="QASP",
            agent_name="QASPGeneratorAgent",
            phase="Solicitation"
        )
        
        print(f"  Generating QASP...", end=" ", flush=True)
        
        try:
            # Initialize QASP agent (no constructor args needed)
            agent = QASPGeneratorAgent()
            
            # QASP needs a PWS file - create a temporary one with performance requirements
            temp_pws_path = self.output_dir / 'temp_pws_for_qasp.md'
            temp_output_path = self.output_dir / 'qasp_output.md'
            
            # Create PWS content with performance requirements for QASP to extract
            temp_pws_content = f"""# Performance Work Statement
## {self.project_info['program_name']}

**Solicitation Number:** {self.project_info['solicitation_number']}
**Contract Type:** {self.project_info['contract_type']}
**Period of Performance:** {self.project_info['period_of_performance']}

## 1.0 Background
Cloud-based logistics management system for government operations.

## 2.0 Scope
Development and deployment of a modern logistics platform.

## 3.0 Performance Requirements

### 3.1 System Availability
The Contractor shall maintain system availability of 99.9% during core business hours.
- Metric: Uptime percentage
- Standard: >= 99.9%
- Surveillance Method: Automated monitoring

### 3.2 Response Time
The system shall respond to user queries within 2 seconds.
- Metric: Average response time
- Standard: <= 2 seconds
- Surveillance Method: Performance testing

### 3.3 Security Compliance
The Contractor shall maintain FedRAMP authorization.
- Metric: Authorization status
- Standard: Active FedRAMP authorization
- Surveillance Method: Annual audit review

### 3.4 Help Desk Support
The Contractor shall provide help desk support with 4-hour response time.
- Metric: Time to first response
- Standard: <= 4 hours
- Surveillance Method: Ticket tracking

### 3.5 Defect Resolution
Critical defects shall be resolved within 24 hours.
- Metric: Mean time to resolution
- Standard: <= 24 hours for critical, <= 72 hours for major
- Surveillance Method: Defect tracking system

## 4.0 Deliverables
- Monthly status reports
- Quarterly performance reviews
- Annual security assessments
"""
            with open(temp_pws_path, 'w') as f:
                f.write(temp_pws_content)
            
            # Time the generation
            start = time.time()
            result = agent.execute(
                pws_path=str(temp_pws_path),
                output_path=str(temp_output_path),
                config={'program_name': self.project_info['program_name']},
                verbose=False
            )
            elapsed = time.time() - start
            
            # QASP agent is template-based and doesn't use LLM tokens
            # But we still capture timing
            metrics.generation_time_seconds = round(elapsed, 2)
            metrics.status = "success"
            
            # Get word count from output if available
            if temp_output_path.exists():
                with open(temp_output_path, 'r') as f:
                    content = f.read()
                    metrics.word_count = len(content.split())
            
            print(f"✓ {elapsed:.1f}s | 0 tokens | $0.0000")
            
        except Exception as e:
            metrics.status = "failed"
            metrics.error_message = str(e)
            print(f"✗ Error: {str(e)[:50]}")
        
        # Store metrics
        self.document_metrics.append(metrics)
        
        # Update phase metrics for Phase 2 (Solicitation)
        phase_number = 2
        if phase_number not in self.phase_metrics:
            self.phase_metrics[phase_number] = PhaseMetrics(
                phase_name="Solicitation",
                phase_number=phase_number
            )
        
        pm = self.phase_metrics[phase_number]
        pm.documents += 1
        pm.total_time_seconds += metrics.generation_time_seconds
        pm.total_input_tokens += metrics.input_tokens
        pm.total_output_tokens += metrics.output_tokens
        pm.total_tokens += metrics.total_tokens
        pm.total_cost_usd += metrics.total_cost_usd
        pm.total_words += metrics.word_count
    
    def _generate_report(self) -> BenchmarkReport:
        """
        Generate the complete benchmark report.
        
        Returns:
            BenchmarkReport with all aggregated metrics
        """
        total_time = self.end_time - self.start_time
        
        # Count successes/failures
        successful = sum(1 for m in self.document_metrics if m.status == "success")
        failed = sum(1 for m in self.document_metrics if m.status == "failed")
        
        # Aggregate totals
        total_input = sum(m.input_tokens for m in self.document_metrics)
        total_output = sum(m.output_tokens for m in self.document_metrics)
        total_tokens = total_input + total_output
        total_cost = sum(m.total_cost_usd for m in self.document_metrics)
        total_words = sum(m.word_count for m in self.document_metrics)
        
        # Calculate averages (avoid division by zero)
        doc_count = len(self.document_metrics)
        avg_time = total_time / doc_count if doc_count > 0 else 0
        avg_tokens = total_tokens // doc_count if doc_count > 0 else 0
        avg_cost = total_cost / doc_count if doc_count > 0 else 0
        
        report = BenchmarkReport(
            benchmark_date=datetime.now().isoformat(),
            benchmark_id=self.timestamp,
            program_name=self.program_name,
            total_documents=doc_count,
            successful_documents=successful,
            failed_documents=failed,
            total_time_seconds=round(total_time, 2),
            total_time_minutes=round(total_time / 60, 2),
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_tokens=total_tokens,
            total_cost_usd=round(total_cost, 4),
            total_words=total_words,
            avg_time_per_doc_seconds=round(avg_time, 2),
            avg_tokens_per_doc=avg_tokens,
            avg_cost_per_doc_usd=round(avg_cost, 4),
            model_used=self.MODEL,
            input_price_per_million=self.INPUT_COST_PER_MILLION,
            output_price_per_million=self.OUTPUT_COST_PER_MILLION,
            phases=[asdict(pm) for pm in sorted(self.phase_metrics.values(), key=lambda x: x.phase_number)],
            documents=[asdict(dm) for dm in self.document_metrics]
        )
        
        return report
    
    def _print_summary(self, report: BenchmarkReport):
        """
        Print formatted summary to console.
        
        Args:
            report: The benchmark report to display
        """
        print("\n" + "=" * 70)
        print("BENCHMARK SUMMARY")
        print("=" * 70)
        
        # Overall metrics
        print(f"\n📊 Overall Metrics:")
        print(f"   Documents Generated: {report.successful_documents}/{report.total_documents}")
        print(f"   Total Time: {report.total_time_minutes:.1f} minutes ({report.total_time_seconds:.1f}s)")
        print(f"   Total Tokens: {report.total_tokens:,}")
        print(f"   Total Cost: ${report.total_cost_usd:.4f}")
        print(f"   Total Words: {report.total_words:,}")
        
        # Averages
        print(f"\n📈 Averages (per document):")
        print(f"   Avg Time: {report.avg_time_per_doc_seconds:.1f}s")
        print(f"   Avg Tokens: {report.avg_tokens_per_doc:,}")
        print(f"   Avg Cost: ${report.avg_cost_per_doc_usd:.4f}")
        
        # By phase
        print(f"\n📋 By Phase:")
        for phase in report.phases:
            print(f"   Phase {phase['phase_number']} ({phase['phase_name']}): "
                  f"{phase['documents']} docs | "
                  f"{phase['total_time_seconds']:.1f}s | "
                  f"{phase['total_tokens']:,} tokens | "
                  f"${phase['total_cost_usd']:.4f}")
        
        # Per document table
        print(f"\n📄 Per Document:")
        print(f"   {'Document':<35} {'Time':>8} {'Input':>10} {'Output':>10} {'Cost':>10}")
        print(f"   {'-'*35} {'-'*8} {'-'*10} {'-'*10} {'-'*10}")
        
        for doc in report.documents:
            status_icon = "✓" if doc['status'] == "success" else "✗"
            name = doc['document_name'][:33]
            print(f"   {status_icon} {name:<33} {doc['generation_time_seconds']:>7.1f}s "
                  f"{doc['input_tokens']:>10,} {doc['output_tokens']:>10,} "
                  f"${doc['total_cost_usd']:>9.4f}")
        
        print(f"   {'-'*35} {'-'*8} {'-'*10} {'-'*10} {'-'*10}")
        print(f"   {'TOTAL':<35} {report.total_time_seconds:>7.1f}s "
              f"{report.total_input_tokens:>10,} {report.total_output_tokens:>10,} "
              f"${report.total_cost_usd:>9.4f}")
        
        print("\n" + "=" * 70)
    
    def _save_reports(self, report: BenchmarkReport):
        """
        Save reports to JSON and Markdown files.
        
        Args:
            report: The benchmark report to save
        """
        # Save JSON
        json_path = self.output_dir / 'benchmark_results.json'
        with open(json_path, 'w') as f:
            json.dump(asdict(report), f, indent=2)
        print(f"\n📁 JSON Report: {json_path}")
        
        # Save Markdown
        md_path = self.output_dir / 'benchmark_report.md'
        md_content = self._generate_markdown_report(report)
        with open(md_path, 'w') as f:
            f.write(md_content)
        print(f"📁 Markdown Report: {md_path}")
    
    def _generate_markdown_report(self, report: BenchmarkReport) -> str:
        """
        Generate a Markdown report.
        
        Args:
            report: The benchmark report data
            
        Returns:
            Markdown formatted string
        """
        md = f"""# Document Generation Benchmark Report

**Date:** {report.benchmark_date}
**Benchmark ID:** {report.benchmark_id}
**Program:** {report.program_name}

---

## Summary

| Metric | Value |
|--------|-------|
| Documents Generated | {report.successful_documents}/{report.total_documents} |
| Total Time | {report.total_time_minutes:.1f} minutes ({report.total_time_seconds:.1f}s) |
| Total Tokens | {report.total_tokens:,} |
| Total Cost | ${report.total_cost_usd:.4f} |
| Total Words | {report.total_words:,} |

### Averages (per document)

| Metric | Value |
|--------|-------|
| Avg Time | {report.avg_time_per_doc_seconds:.1f}s |
| Avg Tokens | {report.avg_tokens_per_doc:,} |
| Avg Cost | ${report.avg_cost_per_doc_usd:.4f} |

---

## Pricing Information

| Model | Input (per 1M) | Output (per 1M) |
|-------|----------------|-----------------|
| {report.model_used} | ${report.input_price_per_million:.2f} | ${report.output_price_per_million:.2f} |

---

## Results by Phase

| Phase | Documents | Time | Tokens | Cost |
|-------|-----------|------|--------|------|
"""
        
        for phase in report.phases:
            md += f"| {phase['phase_name']} | {phase['documents']} | {phase['total_time_seconds']:.1f}s | {phase['total_tokens']:,} | ${phase['total_cost_usd']:.4f} |\n"
        
        md += f"| **TOTAL** | **{report.total_documents}** | **{report.total_time_seconds:.1f}s** | **{report.total_tokens:,}** | **${report.total_cost_usd:.4f}** |\n"
        
        md += """

---

## Results by Document

| Document | Agent | Time | Input Tokens | Output Tokens | Cost | Status |
|----------|-------|------|--------------|---------------|------|--------|
"""
        
        for doc in report.documents:
            status = "✅" if doc['status'] == "success" else "❌"
            md += f"| {doc['document_name']} | {doc['agent_name']} | {doc['generation_time_seconds']:.1f}s | {doc['input_tokens']:,} | {doc['output_tokens']:,} | ${doc['total_cost_usd']:.4f} | {status} |\n"
        
        md += f"""

---

## Cost Analysis

### Total Cost Breakdown

- **Input Tokens:** {report.total_input_tokens:,} × ${report.input_price_per_million}/1M = ${(report.total_input_tokens / 1_000_000) * report.input_price_per_million:.4f}
- **Output Tokens:** {report.total_output_tokens:,} × ${report.output_price_per_million}/1M = ${(report.total_output_tokens / 1_000_000) * report.output_price_per_million:.4f}
- **Total:** ${report.total_cost_usd:.4f}

### Cost Projections

| Packages/Month | Monthly Cost | Annual Cost |
|----------------|--------------|-------------|
| 1 | ${report.total_cost_usd:.2f} | ${report.total_cost_usd * 12:.2f} |
| 5 | ${report.total_cost_usd * 5:.2f} | ${report.total_cost_usd * 60:.2f} |
| 10 | ${report.total_cost_usd * 10:.2f} | ${report.total_cost_usd * 120:.2f} |
| 50 | ${report.total_cost_usd * 50:.2f} | ${report.total_cost_usd * 600:.2f} |

---

*Generated by test_generation_benchmark.py*
"""
        
        return md


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point for the benchmark."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DOCUMENT GENERATION BENCHMARK TEST                         ║
║                                                                              ║
║  Generates all 20 core acquisition documents and tracks:                     ║
║  - Generation time per document                                              ║
║  - Token usage (input/output) from Anthropic API                            ║
║  - Cost per document (Claude Sonnet 4 pricing)                              ║
║                                                                              ║
║  Estimated runtime: 10-15 minutes                                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Check for API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("\nSet it with: export ANTHROPIC_API_KEY='your-key-here'")
        return 1
    
    print("✅ Anthropic API Key found")
    
    # Confirm before proceeding (expensive operation)
    print("\n⚠️  This will make ~100+ API calls to Claude and may cost $2-5.")
    
    if sys.stdin.isatty():
        response = input("Proceed with benchmark? (y/n): ").strip().lower()
        if response != 'y':
            print("\n❌ Benchmark cancelled by user.")
            return 0
    else:
        print("Auto-proceeding (non-interactive mode)...\n")
    
    # Run benchmark
    benchmark = GenerationBenchmark(
        api_key=api_key,
        program_name="Benchmark Test Program"
    )
    
    try:
        report = benchmark.run_full_benchmark()
        
        print(f"\n✅ Benchmark complete!")
        print(f"   Results saved to: {benchmark.output_dir}/")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Benchmark interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
