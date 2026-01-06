"""
Debriefing Generator Agent: Generates post-award debriefing materials
Creates offeror-specific debriefings per FAR 15.505/15.506
"""

from typing import Dict
from pathlib import Path
import sys
from datetime import datetime, timedelta
import re

sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.base_agent import BaseAgent
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class DebriefingGeneratorAgent(BaseAgent):
    """
    Debriefing Generator Agent
    
    Generates post-award or pre-award debriefing materials per FAR 15.505/15.506.
    
    Features:
    - Offeror-specific feedback
    - Strengths/weaknesses from scorecards
    - General comparison with winner
    - Protest rights information
    """
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        super().__init__(name="Debriefing Generator Agent", api_key=api_key, model=model, temperature=0.4)
        
        self.template_path = Path(__file__).parent.parent / "templates" / "debriefing_template.md"
        with open(self.template_path, 'r') as f:
            self.template = f.read()
        
        print("\n" + "="*70)
        print("DEBRIEFING GENERATOR INITIALIZED")
        print("="*70)
        print(f"  ✓ Template loaded")
        print("="*70 + "\n")
    
    def execute(self, task: Dict) -> Dict:
        """Execute debriefing generation"""
        self.log("Starting debriefing generation")

        solicitation_info = task.get('solicitation_info', {})
        offeror_evaluation = task.get('offeror_evaluation', {})
        winner_info = task.get('winner_info', {})
        config = task.get('config', {})
        program_name = solicitation_info.get('program_name', 'Unknown')

        # STEP 0: Cross-reference lookup for Scorecards and SSDD
        self._scorecard_references = []
        self._ssdd_reference = None

        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for Evaluation Scorecards (for strengths/weaknesses)
                all_scorecards = [doc for doc in metadata_store._documents.values()
                                 if doc['program'] == program_name and doc['doc_type'] == 'evaluation_scorecard']

                if all_scorecards:
                    print(f"✅ Found {len(all_scorecards)} Evaluation Scorecard(s)")
                    for scorecard in all_scorecards:
                        self._scorecard_references.append(scorecard['id'])
                        # Could extract strengths/weaknesses from scorecards if needed

                # Look for SSDD (award decision and winner info)
                latest_ssdd = metadata_store.find_latest_document('ssdd', program_name)
                if latest_ssdd:
                    print(f"✅ Found SSDD: {latest_ssdd['id']}")
                    print(f"   Awardee: {latest_ssdd['extracted_data'].get('recommended_awardee', 'Unknown')}")
                    if not winner_info.get('name'):
                        winner_info['name'] = latest_ssdd['extracted_data'].get('recommended_awardee', 'TBD')
                    winner_info['decision_date'] = latest_ssdd['extracted_data'].get('decision_date', datetime.now().strftime('%Y-%m-%d'))
                    self._ssdd_reference = latest_ssdd['id']
                else:
                    print("ℹ️  No SSDD found")

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")

        print(f"\n📋 Generating debriefing for: {offeror_evaluation.get('name', 'Unknown Offeror')}")

        content = self._populate_template(solicitation_info, offeror_evaluation, winner_info, config)

        # STEP 2: Save metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving Debriefing metadata...")
                metadata_store = DocumentMetadataStore()

                # Extract Debriefing specific data
                extracted_data = {
                    'offeror_name': offeror_evaluation.get('name', 'TBD'),
                    'debriefing_type': config.get('debriefing_type', 'Post-Award'),
                    'debriefing_date': datetime.now().strftime('%Y-%m-%d'),
                    'offeror_rating': offeror_evaluation.get('overall_rating', 'TBD'),
                    'offeror_ranking': offeror_evaluation.get('ranking', 'TBD'),
                    'awardee_name': winner_info.get('name', 'TBD'),
                    'protest_deadline': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
                }

                # Track references
                references = {}
                if self._scorecard_references:
                    for i, scorecard_id in enumerate(self._scorecard_references):
                        references[f'scorecard_{i+1}'] = scorecard_id
                if self._ssdd_reference:
                    references['ssdd'] = self._ssdd_reference

                doc_id = metadata_store.save_document(
                    doc_type='debriefing',
                    program=program_name,
                    content=content,
                    file_path=None,
                    extracted_data=extracted_data,
                    references=references
                )

                print(f"✅ Metadata saved: {doc_id}")

            except Exception as e:
                print(f"⚠️  Failed to save metadata: {str(e)}")

        return {
            'status': 'success',
            'content': content,
            'metadata': {
                'offeror': offeror_evaluation.get('name', 'TBD'),
                'debriefing_type': config.get('debriefing_type', 'Post-Award')
            }
        }
    
    def _populate_template(self, solicitation_info: Dict, offeror_eval: Dict, winner: Dict, config: Dict) -> str:
        """Populate debriefing template"""
        content = self.template
        
        content = content.replace('{{solicitation_number}}', solicitation_info.get('solicitation_number', 'TBD'))
        content = content.replace('{{program_name}}', solicitation_info.get('program_name', 'TBD'))
        content = content.replace('{{offeror_name}}', offeror_eval.get('name', 'TBD'))
        content = content.replace('{{debriefing_date}}', datetime.now().strftime('%B %d, %Y'))
        content = content.replace('{{classification}}', config.get('classification', 'UNCLASSIFIED'))
        
        # Award information
        content = content.replace('{{awardee_name}}', winner.get('name', 'TBD'))
        content = content.replace('{{award_amount}}', winner.get('amount', 'TBD'))
        content = content.replace('{{award_date}}', winner.get('date', datetime.now().strftime('%B %d, %Y')))
        
        # Evaluation results
        content = content.replace('{{offeror_overall_rating}}', offeror_eval.get('overall_rating', 'TBD'))
        content = content.replace('{{offeror_overall_risk}}', offeror_eval.get('overall_risk', 'Moderate'))
        content = content.replace('{{your_technical_rating}}', offeror_eval.get('technical_rating', 'TBD'))
        content = content.replace('{{your_management_rating}}', offeror_eval.get('management_rating', 'TBD'))
        content = content.replace('{{your_proposed_cost}}', offeror_eval.get('cost', 'TBD'))
        content = content.replace('{{your_ranking}}', str(offeror_eval.get('ranking', 'TBD')))
        
        # Protest deadline (10 days after debriefing)
        protest_deadline = datetime.now() + timedelta(days=10)
        content = content.replace('{{protest_deadline}}', protest_deadline.strftime('%B %d, %Y'))
        
        content = re.sub(r'\{\{[^}]+\}\}', 'TBD', content)
        return content
    
    def save_to_file(self, content: str, output_path: str, convert_to_pdf: bool = True) -> Dict:
        """Save debriefing to file"""
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

