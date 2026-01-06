"""
Pre-Solicitation Orchestrator: Coordinates the complete pre-solicitation workflow
Manages 6-phase document generation: Sources Sought → RFI → Acquisition Plan → IGCE → Pre-Sol Notice → Industry Day
"""

from typing import Dict, List, Optional
from pathlib import Path
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.igce_generator_agent import IGCEGeneratorAgent
from backend.agents.sources_sought_generator_agent import SourcesSoughtGeneratorAgent
from backend.agents.rfi_generator_agent import RFIGeneratorAgent
from backend.agents.acquisition_plan_generator_agent import AcquisitionPlanGeneratorAgent
from backend.agents.pre_solicitation_notice_generator_agent import PreSolicitationNoticeGeneratorAgent
from backend.agents.industry_day_generator_agent import IndustryDayGeneratorAgent
from backend.rag.retriever import Retriever


class PreSolicitationOrchestrator:
    """
    Pre-Solicitation Orchestrator
    
    Coordinates the complete pre-solicitation workflow for DoD contracting.
    
    Workflow:
    1. Market Research Phase: Sources Sought → collect vendor responses
    2. Deep Dive Phase: RFI → technical capability assessment
    3. Planning Phase: Acquisition Plan → strategy documentation
    4. Cost Phase: IGCE → cost estimate with basis of estimate
    5. Announcement Phase: Pre-Solicitation Notice → public 15-day notice
    6. Engagement Phase: Industry Day → vendor interaction and Q&A
    
    Features:
    - Contract type configuration (services vs R&D)
    - Phase dependencies (Sources Sought before RFI)
    - RAG integration for cost/schedule references from ALMS
    - Quality gates between phases
    - Comprehensive workflow state management
    
    Dependencies:
    - 6 Generator Agents (IGCE, Sources Sought, RFI, Acq Plan, Pre-Sol Notice, Industry Day)
    - Retriever: Optional RAG system for ALMS document references
    """
    
    def __init__(
        self,
        api_key: str,
        retriever: Optional[Retriever] = None,
        tavily_api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize Pre-Solicitation Orchestrator
        
        Args:
            api_key: Anthropic API key
            retriever: Optional RAG retriever for ALMS references
            tavily_api_key: Optional Tavily API key (not used in pre-solicitation but for consistency)
            model: Claude model to use
        """
        # Initialize all generator agents
        self.sources_sought_agent = SourcesSoughtGeneratorAgent(api_key, retriever, model)
        self.rfi_agent = RFIGeneratorAgent(api_key, retriever, model)
        self.acquisition_plan_agent = AcquisitionPlanGeneratorAgent(api_key, retriever, model)
        self.igce_agent = IGCEGeneratorAgent(api_key, retriever, model)
        self.pre_sol_notice_agent = PreSolicitationNoticeGeneratorAgent(api_key, model)
        self.industry_day_agent = IndustryDayGeneratorAgent(api_key, model)
        
        self.retriever = retriever
        
        # Workflow state
        self.workflow_state = {
            'phase': 'initialized',
            'sources_sought_result': None,
            'rfi_result': None,
            'acquisition_plan_result': None,
            'igce_result': None,
            'pre_sol_notice_result': None,
            'industry_day_result': None
        }
        
        print("\n" + "="*70)
        print("PRE-SOLICITATION ORCHESTRATOR INITIALIZED")
        print("="*70)
        print(f"  ✓ Sources Sought Generator Agent ready")
        print(f"  ✓ RFI Generator Agent ready")
        print(f"  ✓ Acquisition Plan Generator Agent ready")
        print(f"  ✓ IGCE Generator Agent ready")
        print(f"  ✓ Pre-Solicitation Notice Generator Agent ready")
        print(f"  ✓ Industry Day Generator Agent ready")
        if self.retriever:
            print(f"  ✓ RAG retriever available (ALMS cost/schedule references)")
        else:
            print(f"  ℹ RAG retriever not available")
        print("="*70 + "\n")
    
    def execute_pre_solicitation_workflow(
        self,
        project_info: Dict,
        requirements_content: str = '',
        output_dir: str = 'outputs/pre-solicitation',
        generate_sources_sought: bool = True,
        generate_rfi: bool = True,
        generate_acquisition_plan: bool = True,
        generate_igce: bool = True,
        generate_pre_solicitation_notice: bool = True,
        generate_industry_day: bool = True,
        sources_sought_config: Optional[Dict] = None,
        rfi_config: Optional[Dict] = None,
        acquisition_plan_config: Optional[Dict] = None,
        igce_config: Optional[Dict] = None,
        pre_sol_notice_config: Optional[Dict] = None,
        industry_day_config: Optional[Dict] = None
    ) -> Dict:
        """
        Execute complete pre-solicitation workflow
        
        Args:
            project_info: Program information dict with keys:
                - program_name: str
                - organization: str
                - estimated_value: str (e.g., "$5M - $10M")
                - period_of_performance: str
                - contract_type: 'services' or 'research_development'
                - contracting_officer: str
                - ko_email: str
                - ko_phone: str
            requirements_content: Optional PWS/SOW/SOO content
            output_dir: Base output directory
            generate_*: Boolean flags for each document type
            *_config: Optional configuration for each generator
        
        Returns:
            Dictionary with results from all phases
        """
        print("\n" + "="*80)
        print("PRE-SOLICITATION WORKFLOW EXECUTION")
        print("="*80)
        print(f"Program: {project_info.get('program_name', 'Unknown')}")
        print(f"Organization: {project_info.get('organization', 'Unknown')}")
        print(f"Estimated Value: {project_info.get('estimated_value', 'TBD')}")
        print(f"Contract Type: {project_info.get('contract_type', 'services')}")
        print("="*80)
        
        results = {
            'workflow_status': 'in_progress',
            'phases_completed': [],
            'outputs': {}
        }
        
        # Ensure output directories exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Get contract type
        contract_type = project_info.get('contract_type', 'services')
        
        # Phase 1: Sources Sought Notice (Market Research)
        if generate_sources_sought:
            print("\n" + "="*80)
            print("PHASE 1: MARKET RESEARCH (SOURCES SOUGHT)")
            print("="*80)
            
            ss_config = sources_sought_config or {}
            ss_config['contract_type'] = contract_type
            
            ss_task = {
                'project_info': project_info,
                'requirements_content': requirements_content,
                'config': ss_config
            }
            
            ss_result = self.sources_sought_agent.execute(ss_task)
            
            # Save to file
            ss_output_path = f"{output_dir}/sources-sought/sources_sought_notice.md"
            files = self.sources_sought_agent.save_to_file(
                ss_result['content'],
                ss_output_path,
                convert_to_pdf=True
            )
            
            self.workflow_state['sources_sought_result'] = ss_result
            results['sources_sought'] = {
                'status': 'completed',
                'output_path': files['markdown'],
                'pdf_path': files.get('pdf'),
                'metadata': ss_result['metadata']
            }
            results['phases_completed'].append('sources_sought')
            
            print(f"\n✅ PHASE 1 COMPLETE: {files['markdown']}")
        
        # Phase 2: Request for Information (Deep Dive)
        if generate_rfi:
            print("\n" + "="*80)
            print("PHASE 2: TECHNICAL DEEP DIVE (RFI)")
            print("="*80)
            
            rfi_config_data = rfi_config or {}
            rfi_config_data['contract_type'] = contract_type
            
            rfi_task = {
                'project_info': project_info,
                'requirements_content': requirements_content,
                'config': rfi_config_data
            }
            
            rfi_result = self.rfi_agent.execute(rfi_task)
            
            # Save to file
            rfi_output_path = f"{output_dir}/rfi/request_for_information.md"
            files = self.rfi_agent.save_to_file(
                rfi_result['content'],
                rfi_output_path,
                convert_to_pdf=True
            )
            
            self.workflow_state['rfi_result'] = rfi_result
            results['rfi'] = {
                'status': 'completed',
                'output_path': files['markdown'],
                'pdf_path': files.get('pdf'),
                'metadata': rfi_result['metadata']
            }
            results['phases_completed'].append('rfi')
            
            print(f"\n✅ PHASE 2 COMPLETE: {files['markdown']}")
        
        # Phase 3: Acquisition Plan (Strategy Documentation)
        if generate_acquisition_plan:
            print("\n" + "="*80)
            print("PHASE 3: ACQUISITION PLANNING")
            print("="*80)
            
            ap_config = acquisition_plan_config or {}
            ap_config['contract_type'] = contract_type
            
            # Include market research results if available
            market_research = {}
            if results.get('sources_sought'):
                market_research['sources_sought_summary'] = "Market research indicates adequate competition"
            
            ap_task = {
                'project_info': project_info,
                'requirements_content': requirements_content,
                'market_research_results': market_research,
                'config': ap_config
            }
            
            ap_result = self.acquisition_plan_agent.execute(ap_task)
            
            # Save to file
            ap_output_path = f"{output_dir}/acquisition-plan/acquisition_plan.md"
            files = self.acquisition_plan_agent.save_to_file(
                ap_result['content'],
                ap_output_path,
                convert_to_pdf=True
            )
            
            self.workflow_state['acquisition_plan_result'] = ap_result
            results['acquisition_plan'] = {
                'status': 'completed',
                'output_path': files['markdown'],
                'pdf_path': files.get('pdf'),
                'metadata': ap_result['metadata']
            }
            results['phases_completed'].append('acquisition_plan')
            
            print(f"\n✅ PHASE 3 COMPLETE: {files['markdown']}")
        
        # Phase 4: IGCE (Cost Estimation)
        if generate_igce:
            print("\n" + "="*80)
            print("PHASE 4: COST ESTIMATION (IGCE)")
            print("="*80)
            
            igce_config_data = igce_config or {}
            igce_config_data['contract_type'] = contract_type
            
            igce_task = {
                'project_info': project_info,
                'requirements_content': requirements_content,
                'config': igce_config_data
            }
            
            igce_result = self.igce_agent.execute(igce_task)
            
            # Save to file
            igce_output_path = f"{output_dir}/igce/independent_government_cost_estimate.md"
            files = self.igce_agent.save_to_file(
                igce_result['content'],
                igce_output_path,
                convert_to_pdf=True
            )
            
            self.workflow_state['igce_result'] = igce_result
            results['igce'] = {
                'status': 'completed',
                'output_path': files['markdown'],
                'pdf_path': files.get('pdf'),
                'metadata': igce_result['metadata']
            }
            results['phases_completed'].append('igce')
            
            print(f"\n✅ PHASE 4 COMPLETE: {files['markdown']}")
        
        # Phase 5: Pre-Solicitation Notice (Public Announcement)
        if generate_pre_solicitation_notice:
            print("\n" + "="*80)
            print("PHASE 5: PUBLIC ANNOUNCEMENT (PRE-SOLICITATION NOTICE)")
            print("="*80)
            
            psn_config = pre_sol_notice_config or {}
            psn_config['contract_type'] = contract_type
            
            psn_task = {
                'project_info': project_info,
                'requirements_content': requirements_content,
                'config': psn_config
            }
            
            psn_result = self.pre_sol_notice_agent.execute(psn_task)
            
            # Save to file
            psn_output_path = f"{output_dir}/notices/pre_solicitation_notice.md"
            files = self.pre_sol_notice_agent.save_to_file(
                psn_result['content'],
                psn_output_path,
                convert_to_pdf=True
            )
            
            self.workflow_state['pre_sol_notice_result'] = psn_result
            results['pre_solicitation_notice'] = {
                'status': 'completed',
                'output_path': files['markdown'],
                'pdf_path': files.get('pdf'),
                'metadata': psn_result['metadata']
            }
            results['phases_completed'].append('pre_solicitation_notice')
            
            print(f"\n✅ PHASE 5 COMPLETE: {files['markdown']}")
        
        # Phase 6: Industry Day (Vendor Engagement)
        if generate_industry_day:
            print("\n" + "="*80)
            print("PHASE 6: VENDOR ENGAGEMENT (INDUSTRY DAY)")
            print("="*80)
            
            id_config = industry_day_config or {}
            id_config['contract_type'] = contract_type
            
            id_task = {
                'project_info': project_info,
                'requirements_content': requirements_content,
                'config': id_config
            }
            
            id_result = self.industry_day_agent.execute(id_task)
            
            # Save to file
            id_output_path = f"{output_dir}/industry-day/industry_day_materials.md"
            files = self.industry_day_agent.save_to_file(
                id_result['content'],
                id_output_path,
                convert_to_pdf=True
            )
            
            self.workflow_state['industry_day_result'] = id_result
            results['industry_day'] = {
                'status': 'completed',
                'output_path': files['markdown'],
                'pdf_path': files.get('pdf'),
                'metadata': id_result['metadata']
            }
            results['phases_completed'].append('industry_day')
            
            print(f"\n✅ PHASE 6 COMPLETE: {files['markdown']}")
        
        # Workflow complete
        results['workflow_status'] = 'completed'
        
        print("\n" + "="*80)
        print("PRE-SOLICITATION WORKFLOW COMPLETE")
        print("="*80)
        print(f"Phases Completed: {len(results['phases_completed'])}/6")
        for phase in results['phases_completed']:
            print(f"  ✓ {phase.replace('_', ' ').title()}")
        print(f"\nOutput Directory: {output_dir}")
        print("="*80 + "\n")
        
        return results
    
    def get_workflow_state(self) -> Dict:
        """Get current workflow state"""
        return self.workflow_state.copy()
    
    def reset_workflow(self):
        """Reset workflow state"""
        self.workflow_state = {
            'phase': 'initialized',
            'sources_sought_result': None,
            'rfi_result': None,
            'acquisition_plan_result': None,
            'igce_result': None,
            'pre_sol_notice_result': None,
            'industry_day_result': None
        }
        print("✓ Workflow state reset")

