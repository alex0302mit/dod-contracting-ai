"""
Source Selection Plan Generator Agent: Generates Source Selection Plans
Creates SSP per FAR 15.303 with SSA/SSEB/SSAC organization
"""

from typing import Dict, List, Optional
from pathlib import Path
import sys
from datetime import datetime, timedelta
import re

sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.base_agent import BaseAgent
from backend.rag.retriever import Retriever
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class SourceSelectionPlanGeneratorAgent(BaseAgent):
    """
    Source Selection Plan Generator Agent
    
    Generates Source Selection Plan per FAR 15.303.
    
    Features:
    - SSA/SSEB/SSAC organization
    - Evaluation procedures
    - Consensus methodology
    - Schedule generation
    """
    
    def __init__(
        self,
        api_key: str,
        retriever: Optional[Retriever] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize Source Selection Plan Generator Agent

        Args:
            api_key: Anthropic API key
            retriever: Optional RAG retriever for organizational guidance
            model: Claude model to use
        """
        super().__init__(name="Source Selection Plan Generator Agent", api_key=api_key, model=model, temperature=0.4)

        self.retriever = retriever
        self.template_path = Path(__file__).parent.parent / "templates" / "source_selection_plan_template.md"
        with open(self.template_path, 'r') as f:
            self.template = f.read()

        print("\n" + "="*70)
        print("SOURCE SELECTION PLAN GENERATOR INITIALIZED")
        print("="*70)
        print(f"  ✓ Template loaded: {self.template_path.name}")
        if self.retriever:
            print(f"  ✓ RAG retriever available (organizational guidance enhancement enabled)")
        else:
            print(f"  ℹ RAG retriever not available (using standard guidance only)")
        print("="*70 + "\n")
    
    def execute(self, task: Dict) -> Dict:
        """Execute SSP generation"""
        self.log("Starting Source Selection Plan generation")

        solicitation_info = task.get('solicitation_info', {})
        config = task.get('config', {})
        program_name = solicitation_info.get('program_name', 'Unknown')

        # STEP 0: Cross-reference lookup for Section M and Acquisition Plan
        self._section_m_reference = None
        self._acquisition_plan_reference = None

        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for Section M (evaluation factors)
                latest_m = metadata_store.find_latest_document('section_m', program_name)
                if latest_m:
                    print(f"✅ Found Section M: {latest_m['id']}")
                    print(f"   Evaluation Factors: {latest_m['extracted_data'].get('factor_count', 0)}")
                    config['evaluation_factors'] = latest_m['extracted_data'].get('evaluation_factors', [])
                    config['evaluation_weights'] = latest_m['extracted_data'].get('evaluation_weights', {})
                    self._section_m_reference = latest_m['id']
                else:
                    print("ℹ️  No Section M found")

                # Look for Acquisition Plan (timeline and strategy)
                latest_acq = metadata_store.find_latest_document('acquisition_plan', program_name)
                if latest_acq:
                    print(f"✅ Found Acquisition Plan: {latest_acq['id']}")
                    print(f"   Timeline: {latest_acq['extracted_data'].get('period_of_performance', 'TBD')}")
                    config['acquisition_timeline'] = latest_acq['extracted_data'].get('milestones_count', 0)
                    solicitation_info['acquisition_strategy'] = latest_acq['extracted_data'].get('acquisition_strategy', '')
                    self._acquisition_plan_reference = latest_acq['id']
                else:
                    print("ℹ️  No Acquisition Plan found")

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")

        print("\n" + "="*70)
        print("GENERATING SOURCE SELECTION PLAN")
        print("="*70)
        print(f"Solicitation: {solicitation_info.get('solicitation_number', 'Unknown')}")
        print(f"Program: {program_name}")
        print("="*70 + "\n")

        # Step 1: Build organizational context from RAG
        print("STEP 1: Building organizational context from RAG...")
        rag_context = self._build_organizational_context(solicitation_info, config)
        print(f"  ✓ RAG context built with {len(rag_context)} organizational elements extracted")

        # Step 2: Generate evaluation schedule
        print("\nSTEP 2: Generating evaluation schedule...")
        schedule = self._generate_evaluation_schedule(solicitation_info, rag_context)
        print(f"  ✓ Schedule generated with {len(schedule)} events")

        # Step 3: Populate template
        print("\nSTEP 3: Populating source selection plan template...")
        content = self._populate_template(solicitation_info, schedule, rag_context, config)
        print(f"  ✓ Template populated ({len(content)} characters)")

        # STEP 4: Save metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving Source Selection Plan metadata...")
                metadata_store = DocumentMetadataStore()

                # Extract SSP specific data
                extracted_data = {
                    'source_selection_method': config.get('source_selection_method', 'Best Value'),
                    'schedule_events_count': len(schedule),
                    'schedule': schedule,
                    'evaluation_team_size': rag_context.get('team_size', 0),
                    'evaluation_factors': config.get('evaluation_factors', []),
                    'ssa_authority': rag_context.get('ssa_authority', 'TBD'),
                    'sseb_chair': rag_context.get('sseb_chair', 'TBD'),
                    'consensus_required': rag_context.get('consensus_required', True)
                }

                # Track references
                references = {}
                if self._section_m_reference:
                    references['section_m'] = self._section_m_reference
                if self._acquisition_plan_reference:
                    references['acquisition_plan'] = self._acquisition_plan_reference

                doc_id = metadata_store.save_document(
                    doc_type='source_selection_plan',
                    program=program_name,
                    content=content,
                    file_path=None,
                    extracted_data=extracted_data,
                    references=references
                )

                print(f"✅ Metadata saved: {doc_id}")

            except Exception as e:
                print(f"⚠️  Failed to save metadata: {str(e)}")

        print("\n" + "="*70)
        print("✅ SOURCE SELECTION PLAN GENERATION COMPLETE")
        print("="*70)

        return {
            'status': 'success',
            'content': content,
            'metadata': {
                'schedule_events': len(schedule),
                'source_selection_method': config.get('source_selection_method', 'Best Value'),
                'rag_data_points': len(rag_context)
            }
        }

    def _build_organizational_context(self, solicitation_info: Dict, config: Dict) -> Dict:
        """
        Build comprehensive organizational context from RAG documents

        Performs 4 targeted RAG queries:
        1. Source Selection Authority and organizational structure
        2. SSEB/SSAC team composition and roles
        3. Evaluation procedures and methodology
        4. Schedule guidance and timeline best practices

        Returns:
            Dictionary with extracted organizational data
        """
        if not self.retriever:
            return {}

        program_name = solicitation_info.get('program_name', 'the program')
        rag_context = {}

        print(f"    → Querying RAG for source selection organizational guidance...")

        # Query 1: Source Selection Authority and organization
        print(f"    → Query 1: SSA and organizational structure...")
        results = self.retriever.retrieve(
            f"Source Selection Authority SSA organization structure for {program_name} acquisition",
            k=5
        )
        ssa_info = self._extract_ssa_info_from_rag(results)
        rag_context.update(ssa_info)
        print(f"      ✓ Extracted {len(ssa_info)} SSA organizational elements")

        # Query 2: SSEB and SSAC composition
        print(f"    → Query 2: SSEB and SSAC team composition...")
        results = self.retriever.retrieve(
            f"Source Selection Evaluation Board SSEB SSAC team composition roles responsibilities for {program_name}",
            k=5
        )
        team_info = self._extract_team_composition_from_rag(results)
        rag_context.update(team_info)
        print(f"      ✓ Extracted {len(team_info)} team composition elements")

        # Query 3: Evaluation procedures and methodology
        print(f"    → Query 3: Evaluation procedures and methodology...")
        results = self.retriever.retrieve(
            f"Evaluation procedures methodology consensus process for {program_name} source selection",
            k=5
        )
        procedures = self._extract_procedures_from_rag(results)
        rag_context.update(procedures)
        print(f"      ✓ Extracted {len(procedures)} procedure elements")

        # Query 4: Schedule and timeline guidance
        print(f"    → Query 4: Schedule and timeline guidance...")
        results = self.retriever.retrieve(
            f"Evaluation schedule timeline duration for {program_name} proposal evaluation",
            k=5
        )
        schedule_guidance = self._extract_schedule_guidance_from_rag(results)
        rag_context.update(schedule_guidance)
        print(f"      ✓ Extracted {len(schedule_guidance)} schedule elements")

        return rag_context

    def _extract_ssa_info_from_rag(self, rag_results: List[Dict]) -> Dict:
        """Extract Source Selection Authority information from RAG results"""
        ssa_info = {}
        combined_text = "\n".join([r.content if hasattr(r, 'content') else r.get('content', '') for r in rag_results])

        import re

        # Look for SSA role guidance (not specific names)
        if 'SSA' in combined_text or 'Source Selection Authority' in combined_text:
            # Extract role description
            ssa_role_patterns = [
                r'SSA.*?(?:will|shall|is|serves as).*?([^\.]+)',
                r'Source Selection Authority.*?(?:will|shall|is).*?([^\.]+)',
                r'(?:Contracting Officer|PCO).*?designated.*?([^\.]+)',
            ]
            for pattern in ssa_role_patterns:
                match = re.search(pattern, combined_text, re.IGNORECASE | re.DOTALL)
                if match:
                    role_desc = match.group(1).strip()[:200]  # Limit length
                    if len(role_desc) > 10:
                        ssa_info['ssa_role_guidance'] = role_desc
                        break

        # Look for PCO information
        if 'PCO' in combined_text:
            pco_patterns = [
                r'PCO.*?(?:will|shall).*?([^\.]+)',
                r'Procuring Contracting Officer.*?(?:will|shall).*?([^\.]+)',
            ]
            for pattern in pco_patterns:
                match = re.search(pattern, combined_text, re.IGNORECASE)
                if match:
                    pco_desc = match.group(1).strip()[:200]
                    if len(pco_desc) > 10:
                        ssa_info['pco_role_guidance'] = pco_desc
                        break

        # Extract FAR references
        far_match = re.search(r'FAR\s+([\d\.]+)', combined_text)
        if far_match:
            ssa_info['far_reference'] = f"FAR {far_match.group(1)}"

        # Extract authority/responsibilities as general guidance
        if 'responsibilit' in combined_text.lower():
            resp_match = re.search(
                r'responsibilit(?:y|ies).*?([^\.]{20,150})',
                combined_text,
                re.IGNORECASE
            )
            if resp_match:
                ssa_info['general_responsibilities'] = resp_match.group(1).strip()

        return ssa_info

    def _extract_team_composition_from_rag(self, rag_results: List[Dict]) -> Dict:
        """Extract SSEB and SSAC team composition from RAG results"""
        team_info = {}
        combined_text = "\n".join([r.content if hasattr(r, 'content') else r.get('content', '') for r in rag_results])

        import re

        # Extract SSEB role guidance (not specific names)
        if 'SSEB' in combined_text:
            sseb_role_patterns = [
                r'SSEB.*?(?:shall|will|is responsible for).*?([^\.]+)',
                r'SSEB Chairperson.*?(?:shall|will).*?([^\.]+)',
                r'Evaluation Board.*?(?:shall|will).*?([^\.]+)',
            ]
            for pattern in sseb_role_patterns:
                match = re.search(pattern, combined_text, re.IGNORECASE)
                if match:
                    role_desc = match.group(1).strip()[:200]
                    if len(role_desc) > 10:
                        team_info['sseb_role_guidance'] = role_desc
                        break

        # Extract SSAC role guidance
        if 'SSAC' in combined_text:
            ssac_patterns = [
                r'SSAC.*?(?:shall|will|is responsible for).*?([^\.]+)',
                r'Advisory Council.*?(?:shall|will).*?([^\.]+)',
            ]
            for pattern in ssac_patterns:
                match = re.search(pattern, combined_text, re.IGNORECASE)
                if match:
                    role_desc = match.group(1).strip()[:200]
                    if len(role_desc) > 10:
                        team_info['ssac_role_guidance'] = role_desc
                        break

        # Extract general team composition patterns
        sseb_composition_patterns = [
            r'SSAC\s+(?:composition|members)[:\s]+([^\.]+)',
            r'Advisory\s+Council\s+(?:includes|consists)[:\s]+([^\.]+)',
            r'SSAC\s+team[:\s]+([^\.]+)'
        ]

        for pattern in ssac_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                team_info['ssac_composition'] = match.group(1).strip()
                break

        # Extract team sizes
        sseb_size_match = re.search(r'SSEB.*?(\d+)\s+(?:member|evaluator)', combined_text, re.IGNORECASE)
        if sseb_size_match:
            team_info['sseb_size'] = sseb_size_match.group(1)

        ssac_size_match = re.search(r'SSAC.*?(\d+)\s+(?:member|advisor)', combined_text, re.IGNORECASE)
        if ssac_size_match:
            team_info['ssac_size'] = ssac_size_match.group(1)

        # Extract key roles
        if 'chair' in combined_text.lower():
            chair_match = re.search(r'SSEB\s+Chair[:\s]+([^,\n\.]+)', combined_text, re.IGNORECASE)
            if chair_match:
                team_info['sseb_chair'] = chair_match.group(1).strip()

        return team_info

    def _extract_procedures_from_rag(self, rag_results: List[Dict]) -> Dict:
        """Extract evaluation procedures and methodology from RAG results"""
        procedures = {}
        combined_text = "\n".join([r.content if hasattr(r, 'content') else r.get('content', '') for r in rag_results])

        # Extract consensus methodology
        consensus_patterns = [
            r'consensus\s+(?:method|process|approach)[:\s]+([^\.]+)',
            r'consensus.*?(\w+\s+\w+\s+\w+)',
            r'SSEB\s+consensus[:\s]+([^\.]+)'
        ]

        for pattern in consensus_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match and len(match.group(1).strip()) > 10:
                procedures['consensus_methodology'] = match.group(1).strip()
                break

        # Extract evaluation phases
        if 'phase' in combined_text.lower():
            phase_matches = re.findall(
                r'(?:Phase\s+\d+|Stage\s+\d+)[:\s]+([^\.]+)',
                combined_text,
                re.IGNORECASE
            )
            if phase_matches:
                procedures['evaluation_phases'] = phase_matches[:3]  # Top 3 phases

        # Extract documentation requirements
        if 'document' in combined_text.lower():
            doc_match = re.search(
                r'documentation\s+(?:requirement|required)[:\s]+([^\.]+)',
                combined_text,
                re.IGNORECASE
            )
            if doc_match:
                procedures['documentation_requirements'] = doc_match.group(1).strip()

        return procedures

    def _extract_schedule_guidance_from_rag(self, rag_results: List[Dict]) -> Dict:
        """Extract schedule and timeline guidance from RAG results"""
        schedule_info = {}
        combined_text = "\n".join([r.content if hasattr(r, 'content') else r.get('content', '') for r in rag_results])

        # Extract evaluation duration
        duration_patterns = [
            r'evaluation.*?(\d+)\s+(?:day|week)',
            r'(\d+)\s+(?:day|week).*?evaluation',
            r'duration[:\s]+(\d+)\s+(?:day|week)'
        ]

        for pattern in duration_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                schedule_info['evaluation_duration'] = match.group(1)
                break

        # Extract individual evaluation period
        indiv_match = re.search(
            r'individual\s+evaluation.*?(\d+)\s+(?:day|week)',
            combined_text,
            re.IGNORECASE
        )
        if indiv_match:
            schedule_info['individual_eval_days'] = indiv_match.group(1)

        # Extract consensus meeting duration
        consensus_match = re.search(
            r'consensus.*?(\d+)\s+(?:day|hour)',
            combined_text,
            re.IGNORECASE
        )
        if consensus_match:
            schedule_info['consensus_duration'] = consensus_match.group(1)

        # Extract total timeline
        timeline_match = re.search(
            r'(?:total|overall).*?(\d+)\s+(?:day|week)',
            combined_text,
            re.IGNORECASE
        )
        if timeline_match:
            schedule_info['total_timeline_days'] = timeline_match.group(1)

        return schedule_info

    def _generate_evaluation_schedule(self, solicitation_info: Dict, rag_context: Dict = None) -> List[Dict]:
        """
        Generate evaluation schedule with RAG-informed durations

        Uses RAG context to adjust schedule durations based on similar programs
        """
        if rag_context is None:
            rag_context = {}

        proposal_due = datetime.now()

        # Use RAG-informed durations if available, otherwise use defaults
        individual_eval_days = int(rag_context.get('individual_eval_days', 14))
        consensus_days = int(rag_context.get('consensus_duration', 2))

        # Adjust if RAG provided total timeline
        if 'total_timeline_days' in rag_context:
            total_days = int(rag_context['total_timeline_days'])
        else:
            total_days = 30  # Default

        schedule = [
            {'event': 'Proposals Due', 'date': proposal_due, 'duration': '1 day', 'responsible': 'CO'},
            {'event': 'Administrative Review', 'date': proposal_due + timedelta(days=1), 'duration': '2 days', 'responsible': 'CO'},
            {'event': 'Distribute to SSEB', 'date': proposal_due + timedelta(days=3), 'duration': '1 day', 'responsible': 'SSEB Chair'},
            {'event': 'Individual Evaluations', 'date': proposal_due + timedelta(days=4), 'duration': f'{individual_eval_days} days', 'responsible': 'SSEB Members'},
            {'event': 'SSEB Consensus Meeting', 'date': proposal_due + timedelta(days=4+individual_eval_days), 'duration': f'{consensus_days} days', 'responsible': 'SSEB'},
            {'event': 'SSAC Review', 'date': proposal_due + timedelta(days=4+individual_eval_days+consensus_days), 'duration': '3 days', 'responsible': 'SSAC'},
            {'event': 'SSA Decision Briefing', 'date': proposal_due + timedelta(days=4+individual_eval_days+consensus_days+3), 'duration': '1 day', 'responsible': 'SSA'},
            {'event': 'Award Decision', 'date': proposal_due + timedelta(days=total_days), 'duration': '1 day', 'responsible': 'SSA'}
        ]

        return schedule
    
    def _populate_template(
        self,
        solicitation_info: Dict,
        schedule: List[Dict],
        rag_context: Dict,
        config: Dict
    ) -> str:
        """
        Populate SSP template with intelligent priority system

        Priority order:
        1. Config values (explicitly provided)
        2. RAG-retrieved values (from documents)
        3. Descriptive TBDs with context
        """
        content = self.template

        # Helper function for priority-based value selection
        def get_value(config_key=None, rag_key=None, default='TBD'):
            if config_key and config.get(config_key):
                return config.get(config_key)
            if rag_key and rag_key in rag_context:
                return str(rag_context[rag_key])
            return default

        # Basic information
        content = content.replace('{{solicitation_number}}', solicitation_info.get('solicitation_number', 'TBD'))
        content = content.replace('{{program_name}}', solicitation_info.get('program_name', 'TBD'))
        content = content.replace('{{plan_date}}', datetime.now().strftime('%B %d, %Y'))
        content = content.replace('{{classification}}', config.get('classification', 'UNCLASSIFIED'))

        # SSA information with RAG enhancement
        ssa_name = get_value('ssa_name', default='TBD - SSA to be designated')
        content = content.replace('{{ssa_name}}', ssa_name)

        ssa_title = get_value('ssa_title', 'ssa_title_found', 'Program Executive Officer')
        content = content.replace('{{ssa_title}}', ssa_title)

        # Source selection method
        content = content.replace('{{source_selection_method}}', config.get('source_selection_method', 'Best Value Trade-Off'))

        # SSA responsibilities with RAG enhancement
        if 'ssa_responsibilities' in rag_context:
            ssa_resp = f"The SSA is responsible for: {rag_context['ssa_responsibilities']}"
            content = content.replace('{{ssa_responsibilities}}', ssa_resp)
        else:
            content = content.replace('{{ssa_responsibilities}}', 'TBD - SSA responsibilities per FAR 15.303')

        # Organizational structure with RAG enhancement
        if 'org_structure' in rag_context:
            org_text = f"**Organizational Structure:** {rag_context['org_structure']}"
            content = content.replace('{{org_structure}}', org_text)
        else:
            content = content.replace('{{org_structure}}', 'TBD - Organizational structure to be documented')

        # SSEB composition with RAG enhancement
        sseb_comp = get_value('sseb_composition', 'sseb_composition', 'TBD - SSEB composition to be determined')
        if 'sseb_size' in rag_context:
            sseb_comp += f" (approximately {rag_context['sseb_size']} members)"
        content = content.replace('{{sseb_composition}}', sseb_comp)

        # SSEB Chair with RAG enhancement
        sseb_chair = get_value('sseb_chair', 'sseb_chair', 'TBD - SSEB Chair to be designated')
        content = content.replace('{{sseb_chair}}', sseb_chair)

        # SSAC composition with RAG enhancement
        ssac_comp = get_value('ssac_composition', 'ssac_composition', 'TBD - SSAC composition to be determined')
        if 'ssac_size' in rag_context:
            ssac_comp += f" (approximately {rag_context['ssac_size']} members)"
        content = content.replace('{{ssac_composition}}', ssac_comp)

        # Consensus methodology with RAG enhancement
        consensus = get_value('consensus_method', 'consensus_methodology', 'TBD - Consensus methodology per FAR 15.305')
        content = content.replace('{{consensus_methodology}}', consensus)

        # Evaluation phases with RAG enhancement
        if 'evaluation_phases' in rag_context and rag_context['evaluation_phases']:
            phases_text = "**Evaluation Phases:**\n"
            for i, phase in enumerate(rag_context['evaluation_phases'], 1):
                phases_text += f"{i}. {phase}\n"
            content = content.replace('{{evaluation_phases}}', phases_text)
        else:
            content = content.replace('{{evaluation_phases}}', 'TBD - Evaluation phases to be defined')

        # Documentation requirements with RAG enhancement
        doc_req = get_value('documentation_requirements', 'documentation_requirements', 'TBD - Documentation requirements per FAR')
        content = content.replace('{{documentation_requirements}}', doc_req)

        # Schedule table
        schedule_table = '\n'.join([
            f"| {item['event']} | {item['date'].strftime('%B %d, %Y')} | {item['duration']} | {item['responsible']} |"
            for item in schedule
        ])
        content = content.replace('{{evaluation_schedule_table}}', schedule_table)

        # Fill remaining placeholders with contextual TBDs
        remaining_placeholders = re.findall(r'\{\{([^}]+)\}\}', content)
        for placeholder in remaining_placeholders:
            placeholder_lower = placeholder.lower()
            if 'sseb' in placeholder_lower:
                replacement = 'TBD - SSEB details to be determined'
            elif 'ssac' in placeholder_lower:
                replacement = 'TBD - SSAC details to be determined'
            elif 'ssa' in placeholder_lower:
                replacement = 'TBD - SSA information to be provided'
            elif 'evaluation' in placeholder_lower:
                replacement = 'TBD - Evaluation details per Section M'
            elif 'schedule' in placeholder_lower:
                replacement = 'TBD - Schedule to be finalized'
            elif 'team' in placeholder_lower or 'member' in placeholder_lower:
                replacement = 'TBD - Team member to be assigned'
            else:
                replacement = 'TBD - Information to be determined'

            content = content.replace(f'{{{{{placeholder}}}}}', replacement)

        return content
    
    def save_to_file(self, content: str, output_path: str, convert_to_pdf: bool = True) -> Dict:
        """Save SSP to file"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(content)
        
        result = {'markdown': output_path}
        
        if convert_to_pdf:
            pdf_path = output_path.replace('.md', '.pdf')
            try:
                from utils.convert_md_to_pdf import convert_markdown_to_pdf
                convert_markdown_to_pdf(output_path, pdf_path)
                result['pdf'] = pdf_path
            except:
                result['pdf'] = None
        
        return result

