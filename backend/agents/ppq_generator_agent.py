"""
PPQ Generator Agent: Generates Past Performance Questionnaires
Creates standardized reference check forms per FAR 15.305(a)(2)
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


class PPQGeneratorAgent(BaseAgent):
    """PPQ Generator Agent - Generates Past Performance Questionnaires"""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        super().__init__(name="PPQ Generator Agent", api_key=api_key, model=model, temperature=0.3)
        
        self.template_path = Path(__file__).parent.parent / "templates" / "ppq_template.md"
        with open(self.template_path, 'r') as f:
            self.template = f.read()
        
        print("\n" + "="*70)
        print("PPQ GENERATOR INITIALIZED")
        print("="*70)
        print(f"  ✓ Template loaded")
        print("="*70 + "\n")
    
    def execute(self, task: Dict) -> Dict:
        """Execute PPQ generation"""
        self.log("Starting PPQ generation")

        solicitation_info = task.get('solicitation_info', {})
        reference_info = task.get('reference_info', {})
        config = task.get('config', {})
        program_name = solicitation_info.get('program_name', 'Unknown')

        # STEP 0: Cross-reference lookup for PWS/SOW and QASP
        self._pws_reference = None
        self._sow_reference = None
        self._qasp_reference = None

        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for PWS/SOW (performance requirements)
                latest_pws = metadata_store.find_latest_document('pws', program_name)
                latest_sow = metadata_store.find_latest_document('sow', program_name)

                if latest_pws:
                    print(f"✅ Found PWS: {latest_pws['id']}")
                    print(f"   Performance Requirements: {len(latest_pws['extracted_data'].get('performance_requirements', []))}")
                    config['performance_requirements'] = latest_pws['extracted_data'].get('performance_requirements', [])
                    self._pws_reference = latest_pws['id']
                elif latest_sow:
                    print(f"✅ Found SOW: {latest_sow['id']}")
                    self._sow_reference = latest_sow['id']

                # Look for QASP (quality metrics)
                latest_qasp = metadata_store.find_latest_document('qasp', program_name)
                if latest_qasp:
                    print(f"✅ Found QASP: {latest_qasp['id']}")
                    config['quality_metrics'] = latest_qasp['extracted_data'].get('performance_standards', [])
                    self._qasp_reference = latest_qasp['id']

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")

        print(f"\n📋 Generating PPQ for: {reference_info.get('offeror_name', 'Unknown Offeror')}")

        content = self._populate_template(solicitation_info, reference_info, config)

        # STEP 2: Save metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving PPQ metadata...")
                metadata_store = DocumentMetadataStore()

                # Extract PPQ specific data
                extracted_data = {
                    'offeror_name': reference_info.get('offeror_name', 'TBD'),
                    'reference_contract': reference_info.get('contract_number', 'TBD'),
                    'issue_date': datetime.now().strftime('%Y-%m-%d'),
                    'return_deadline': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'),
                    'performance_areas': config.get('performance_requirements', [])[:5] if config.get('performance_requirements') else []
                }

                # Track references
                references = {}
                if self._pws_reference:
                    references['pws'] = self._pws_reference
                if self._sow_reference:
                    references['sow'] = self._sow_reference
                if self._qasp_reference:
                    references['qasp'] = self._qasp_reference

                doc_id = metadata_store.save_document(
                    doc_type='ppq',
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
                'offeror': reference_info.get('offeror_name', 'TBD'),
                'reference': reference_info.get('reference_contract', 'TBD')
            }
        }
    
    def _populate_template(self, solicitation_info: Dict, reference_info: Dict, config: Dict) -> str:
        """Populate PPQ template"""
        content = self.template
        
        content = content.replace('{{solicitation_number}}', solicitation_info.get('solicitation_number', 'TBD'))
        content = content.replace('{{program_name}}', solicitation_info.get('program_name', 'TBD'))
        content = content.replace('{{offeror_name}}', reference_info.get('offeror_name', 'TBD'))
        content = content.replace('{{reference_contract}}', reference_info.get('contract_number', 'TBD'))
        content = content.replace('{{issue_date}}', datetime.now().strftime('%B %d, %Y'))
        
        return_deadline = datetime.now() + timedelta(days=10)
        content = content.replace('{{return_deadline}}', return_deadline.strftime('%B %d, %Y'))
        
        content = re.sub(r'\{\{[^}]+\}\}', 'TBD', content)
        return content
    
    def save_to_file(self, content: str, output_path: str, convert_to_pdf: bool = True) -> Dict:
        """Save PPQ to file"""
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

