"""
Award Notification Generator Agent: Generates award notification packages
Creates winner/loser notifications, SAM.gov posting, FPDS-NG data
"""

from typing import Dict
from pathlib import Path
import sys
from datetime import datetime
import re

sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.base_agent import BaseAgent
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class AwardNotificationGeneratorAgent(BaseAgent):
    """
    Award Notification Generator Agent
    
    Generates complete award notification package:
    - Winner notification letter
    - Unsuccessful offeror notifications
    - SAM.gov posting
    - FPDS-NG data
    """
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        super().__init__(name="Award Notification Generator Agent", api_key=api_key, model=model, temperature=0.4)
        
        self.template_path = Path(__file__).parent.parent / "templates" / "award_notification_template.md"
        with open(self.template_path, 'r') as f:
            self.template = f.read()
        
        print("\n" + "="*70)
        print("AWARD NOTIFICATION GENERATOR INITIALIZED")
        print("="*70)
        print(f"  ✓ Template loaded")
        print("="*70 + "\n")
    
    def execute(self, task: Dict) -> Dict:
        """Execute award notification generation"""
        self.log("Starting award notification generation")

        solicitation_info = task.get('solicitation_info', {})
        winner_info = task.get('winner_info', {})
        award_info = task.get('award_info', {})
        config = task.get('config', {})
        program_name = solicitation_info.get('program_name', 'Unknown')

        # STEP 0: Cross-reference lookup for SF-26 and SSDD
        self._sf26_reference = None
        self._ssdd_reference = None

        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for SF-26 (contract award document)
                latest_sf26 = metadata_store.find_latest_document('sf26', program_name)
                if latest_sf26:
                    print(f"✅ Found SF-26: {latest_sf26['id']}")
                    print(f"   Contract Number: {latest_sf26['extracted_data'].get('contract_number', 'TBD')}")
                    print(f"   Awardee: {latest_sf26['extracted_data'].get('contractor_name', 'TBD')}")

                    # Use SF-26 data if not provided
                    if not award_info.get('contract_number'):
                        award_info['contract_number'] = latest_sf26['extracted_data'].get('contract_number', 'TBD')
                    if not winner_info.get('name'):
                        winner_info['name'] = latest_sf26['extracted_data'].get('contractor_name', 'TBD')
                    if not award_info.get('total_value'):
                        award_info['total_value'] = latest_sf26['extracted_data'].get('award_amount', 'TBD')
                    award_info['contract_type'] = latest_sf26['extracted_data'].get('contract_type', 'FFP')
                    award_info['period'] = latest_sf26['extracted_data'].get('period_of_performance', 'TBD')

                    self._sf26_reference = latest_sf26['id']
                else:
                    print("ℹ️  No SF-26 found")

                # Look for SSDD (award decision documentation)
                latest_ssdd = metadata_store.find_latest_document('ssdd', program_name)
                if latest_ssdd:
                    print(f"✅ Found SSDD: {latest_ssdd['id']}")
                    award_info['award_justification'] = latest_ssdd['extracted_data'].get('award_justification', '')
                    self._ssdd_reference = latest_ssdd['id']

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")

        print(f"\n📢 Generating award notification for: {winner_info.get('name', 'Unknown Contractor')}")

        content = self._populate_template(solicitation_info, winner_info, award_info, config)

        # STEP 2: Save metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving Award Notification metadata...")
                metadata_store = DocumentMetadataStore()

                # Extract Award Notification specific data
                extracted_data = {
                    'contract_number': award_info.get('contract_number', 'TBD'),
                    'contractor_name': winner_info.get('name', 'TBD'),
                    'award_amount': award_info.get('total_value', 'TBD'),
                    'notification_date': datetime.now().strftime('%Y-%m-%d'),
                    'contract_type': award_info.get('contract_type', 'FFP'),
                    'period_of_performance': award_info.get('period', 'TBD')
                }

                # Track references
                references = {}
                if self._sf26_reference:
                    references['sf26'] = self._sf26_reference
                if self._ssdd_reference:
                    references['ssdd'] = self._ssdd_reference

                doc_id = metadata_store.save_document(
                    doc_type='award_notification',
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
                'contract_number': award_info.get('contract_number', 'TBD'),
                'winner': winner_info.get('name', 'TBD'),
                'award_amount': award_info.get('total_value', 'TBD')
            }
        }
    
    def _populate_template(self, solicitation_info: Dict, winner: Dict, award: Dict, config: Dict) -> str:
        """Populate award notification template"""
        content = self.template
        
        content = content.replace('{{contract_number}}', award.get('contract_number', 'TBD'))
        content = content.replace('{{program_name}}', solicitation_info.get('program_name', 'TBD'))
        content = content.replace('{{award_date}}', datetime.now().strftime('%B %d, %Y'))
        content = content.replace('{{classification}}', config.get('classification', 'UNCLASSIFIED'))
        
        # Contractor information
        content = content.replace('{{contractor_name}}', winner.get('name', 'TBD'))
        content = content.replace('{{contractor_address}}', winner.get('address', 'TBD'))
        content = content.replace('{{contractor_poc_name}}', winner.get('poc_name', 'TBD'))
        content = content.replace('{{contractor_duns}}', winner.get('duns', 'TBD'))
        
        # Award details
        content = content.replace('{{contract_value}}', award.get('total_value', 'TBD'))
        content = content.replace('{{total_contract_value}}', award.get('total_value', 'TBD'))
        content = content.replace('{{contract_type}}', award.get('contract_type', 'FFP'))
        content = content.replace('{{period_of_performance}}', award.get('period', '12 months base + 4 option years'))
        
        # CO information
        content = content.replace('{{co_name}}', solicitation_info.get('contracting_officer', 'TBD'))
        content = content.replace('{{co_email}}', solicitation_info.get('co_email', 'TBD'))
        content = content.replace('{{co_phone}}', solicitation_info.get('co_phone', 'TBD'))
        
        content = re.sub(r'\{\{[^}]+\}\}', 'TBD', content)
        return content
    
    def save_to_file(self, content: str, output_path: str, convert_to_pdf: bool = True) -> Dict:
        """Save award notification to file"""
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

