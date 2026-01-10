"""
Post-Solicitation Orchestrator: Coordinates complete post-solicitation workflow
Manages all 9 post-solicitation tools from Q&A through award
"""

from typing import Dict, List, Optional
from pathlib import Path
import sys
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.amendment_generator_agent import AmendmentGeneratorAgent
from backend.agents.qa_manager_agent import QAManagerAgent
from backend.agents.evaluation_scorecard_generator_agent import EvaluationScorecardGeneratorAgent
from backend.agents.source_selection_plan_generator_agent import SourceSelectionPlanGeneratorAgent
from backend.agents.ppq_generator_agent import PPQGeneratorAgent
from backend.agents.ssdd_generator_agent import SSDDGeneratorAgent
from backend.agents.debriefing_generator_agent import DebriefingGeneratorAgent
from backend.agents.sf26_generator_agent import SF26GeneratorAgent
from backend.agents.award_notification_generator_agent import AwardNotificationGeneratorAgent
from backend.rag.retriever import Retriever


class PostSolicitationOrchestrator:
    """
    Post-Solicitation Orchestrator
    
    Coordinates the complete post-solicitation workflow.
    
    Workflow:
    1. Q&A Management Phase: Track and answer vendor questions
    2. Amendment Generation Phase: Modify solicitation as needed
    3. Source Selection Planning Phase: Organize evaluation team
    4. Past Performance Phase: Generate PPQs and collect references
    5. Evaluation Phase: Generate scorecards and evaluate proposals
    6. Source Selection Phase: Generate SSDD with award decision
    7. Award Phase: Generate SF-26 and award notifications
    8. Debriefing Phase: Generate debriefing materials
    
    Features:
    - Coordinates all 9 post-solicitation tools
    - Phase dependencies management
    - Comprehensive workflow state tracking
    - RAG integration for Q&A answers
    
    Dependencies:
    - 9 Post-Solicitation Agents
    - Optional: Retriever for RAG-powered Q&A
    """
    
    def __init__(
        self,
        api_key: str,
        retriever: Optional[Retriever] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """Initialize Post-Solicitation Orchestrator"""
        # Initialize all agents
        self.qa_manager = QAManagerAgent(api_key, retriever, model)
        self.amendment_gen = AmendmentGeneratorAgent(api_key, model)
        self.ssp_gen = SourceSelectionPlanGeneratorAgent(api_key, model)
        self.ppq_gen = PPQGeneratorAgent(api_key, model)
        self.eval_scorecard_gen = EvaluationScorecardGeneratorAgent(api_key, model)
        self.ssdd_gen = SSDDGeneratorAgent(api_key, model)
        self.sf26_gen = SF26GeneratorAgent(api_key, model)
        self.debriefing_gen = DebriefingGeneratorAgent(api_key, model)
        self.award_notification_gen = AwardNotificationGeneratorAgent(api_key, model)
        
        self.retriever = retriever
        
        # Workflow state
        self.workflow_state = {
            'phase': 'initialized',
            'qa_results': None,
            'amendments': [],
            'ssp': None,
            'ppqs': [],
            'scorecards': {},
            'ssdd': None,
            'sf26': None,
            'debriefings': [],
            'award_notifications': None
        }
        
        print("\n" + "="*70)
        print("POST-SOLICITATION ORCHESTRATOR INITIALIZED")
        print("="*70)
        print(f"  ✓ Q&A Manager ready")
        print(f"  ✓ Amendment Generator ready")
        print(f"  ✓ Source Selection Plan Generator ready")
        print(f"  ✓ PPQ Generator ready")
        print(f"  ✓ Evaluation Scorecard Generator ready")
        print(f"  ✓ SSDD Generator ready")
        print(f"  ✓ SF-26 Generator ready")
        print(f"  ✓ Debriefing Generator ready")
        print(f"  ✓ Award Notification Generator ready")
        if self.retriever:
            print(f"  ✓ RAG retriever available (Q&A answering enabled)")
        print("="*70 + "\n")
    
    def execute_complete_workflow(
        self,
        solicitation_info: Dict,
        section_m_content: str,
        offerors: List[Dict],
        recommended_awardee: str,
        output_dir: str = 'outputs',
        config: Optional[Dict] = None
    ) -> Dict:
        """
        Execute complete post-solicitation workflow
        
        Args:
            solicitation_info: Solicitation details
            section_m_content: Section M evaluation factors
            offerors: List of offeror dictionaries
            recommended_awardee: Name of winning offeror
            output_dir: Base output directory
            config: Optional configuration
        
        Returns:
            Dictionary with all results
        """
        config = config or {}
        results = {'workflow_status': 'in_progress', 'phases_completed': []}
        
        print("\n" + "="*80)
        print("POST-SOLICITATION COMPLETE WORKFLOW EXECUTION")
        print("="*80)
        print(f"Solicitation: {solicitation_info.get('solicitation_number', 'Unknown')}")
        print(f"Offerors: {len(offerors)}")
        print(f"Recommended Awardee: {recommended_awardee}")
        print("="*80 + "\n")
        
        # Phase 1: Source Selection Plan
        print("PHASE 1: SOURCE SELECTION PLANNING")
        print("-" * 80)
        ssp_result = self.ssp_gen.execute({
            'solicitation_info': solicitation_info,
            'config': config
        })
        ssp_files = self.ssp_gen.save_to_file(ssp_result['content'], f"{output_dir}/source-selection/source_selection_plan.md")
        results['ssp'] = ssp_files
        results['phases_completed'].append('ssp')
        print(f"✓ SSP: {ssp_files['markdown']}\n")
        
        # Phase 2: Past Performance Questionnaires
        print("PHASE 2: PAST PERFORMANCE QUESTIONNAIRES")
        print("-" * 80)
        ppqs = []
        for offeror in offerors:
            ppq_result = self.ppq_gen.execute({
                'solicitation_info': solicitation_info,
                'reference_info': {
                    'offeror_name': offeror.get('name', 'TBD'),
                    'contract_number': offeror.get('reference_contract', 'TBD')
                },
                'config': {}
            })
            ppq_file = self.ppq_gen.save_to_file(ppq_result['content'], f"{output_dir}/ppq/ppq_{offeror.get('name', 'offeror').lower().replace(' ', '_')}.md")
            ppqs.append(ppq_file)
        results['ppqs'] = ppqs
        results['phases_completed'].append('ppq')
        print(f"✓ Generated {len(ppqs)} PPQs\n")
        
        # Phase 3: Evaluation Scorecards
        print("PHASE 3: EVALUATION SCORECARDS")
        print("-" * 80)
        all_scorecards = {}
        for offeror in offerors:
            scorecards = self.eval_scorecard_gen.generate_full_scorecard_set(
                solicitation_info,
                section_m_content,
                {'offeror_name': offeror.get('name', 'TBD'), 'source_selection_method': config.get('source_selection_method', 'Best Value Trade-Off')}
            )
            all_scorecards[offeror.get('name', 'Unknown')] = scorecards
        results['scorecards'] = all_scorecards
        results['phases_completed'].append('evaluation')
        print(f"✓ Generated scorecards for {len(offerors)} offerors\n")
        
        # Phase 4: Source Selection Decision Document
        print("PHASE 4: SOURCE SELECTION DECISION")
        print("-" * 80)
        # Build evaluation results dict
        evaluation_results = {offeror.get('name', 'Unknown'): {
            'technical': 'Good',
            'management': 'Acceptable',
            'past_perf': 'Good',
            'cost': offeror.get('cost', '$5M'),
            'overall': 'Good',
            'risk': 'Moderate'
        } for offeror in offerors}
        
        ssdd_result = self.ssdd_gen.execute({
            'solicitation_info': solicitation_info,
            'evaluation_results': evaluation_results,
            'recommended_awardee': recommended_awardee,
            'config': config
        })
        ssdd_files = self.ssdd_gen.save_to_file(ssdd_result['content'], f"{output_dir}/source-selection/ssdd.md")
        results['ssdd'] = ssdd_files
        results['phases_completed'].append('ssdd')
        print(f"✓ SSDD: {ssdd_files['markdown']}\n")
        
        # Phase 5: SF-26 Contract Award
        print("PHASE 5: CONTRACT AWARD (SF-26)")
        print("-" * 80)
        winner = next((o for o in offerors if o.get('name') == recommended_awardee), offerors[0])
        sf26_result = self.sf26_gen.execute({
            'solicitation_info': solicitation_info,
            'contractor_info': winner,
            'award_info': {
                'contract_number': config.get('contract_number', 'W911XX-25-C-0001'),
                'total_value': winner.get('cost', '$5M'),
                'contract_type': config.get('contract_type', 'FFP')
            },
            'config': config
        })
        sf26_files = self.sf26_gen.save_to_file(sf26_result['content'], f"{output_dir}/award/sf26_contract_award.md")
        results['sf26'] = sf26_files
        results['phases_completed'].append('sf26')
        print(f"✓ SF-26: {sf26_files['markdown']}\n")
        
        # Phase 6: Award Notifications
        print("PHASE 6: AWARD NOTIFICATIONS")
        print("-" * 80)
        notification_result = self.award_notification_gen.execute({
            'solicitation_info': solicitation_info,
            'winner_info': winner,
            'award_info': {
                'contract_number': config.get('contract_number', 'W911XX-25-C-0001'),
                'total_value': winner.get('cost', '$5M')
            },
            'config': config
        })
        notification_files = self.award_notification_gen.save_to_file(notification_result['content'], f"{output_dir}/award/award_notifications.md")
        results['award_notifications'] = notification_files
        results['phases_completed'].append('notifications')
        print(f"✓ Notifications: {notification_files['markdown']}\n")
        
        # Phase 7: Debriefings
        print("PHASE 7: DEBRIEFING MATERIALS")
        print("-" * 80)
        debriefings = []
        for offeror in offerors:
            if offeror.get('name') != recommended_awardee:
                debriefing_result = self.debriefing_gen.execute({
                    'solicitation_info': solicitation_info,
                    'offeror_evaluation': {
                        'name': offeror.get('name', 'TBD'),
                        'overall_rating': 'Good',
                        'cost': offeror.get('cost', '$5M'),
                        'ranking': offerors.index(offeror) + 1
                    },
                    'winner_info': {
                        'name': recommended_awardee,
                        'amount': winner.get('cost', '$5M')
                    },
                    'config': {}
                })
                debriefing_file = self.debriefing_gen.save_to_file(debriefing_result['content'], f"{output_dir}/debriefing/debriefing_{offeror.get('name', 'offeror').lower().replace(' ', '_')}.md")
                debriefings.append(debriefing_file)
        results['debriefings'] = debriefings
        results['phases_completed'].append('debriefing')
        print(f"✓ Generated {len(debriefings)} debriefings\n")
        
        results['workflow_status'] = 'completed'
        
        print("\n" + "="*80)
        print("POST-SOLICITATION WORKFLOW COMPLETE")
        print("="*80)
        print(f"Phases Completed: {len(results['phases_completed'])}/7")
        print("="*80 + "\n")
        
        return results

