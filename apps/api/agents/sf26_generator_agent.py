"""
SF-26 Generator Agent: Generates Standard Form 26 (Award/Contract)
Creates official contract award document per FAR requirements
"""

from typing import Dict, Optional
from pathlib import Path
import sys
from datetime import datetime
import re

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.base_agent import BaseAgent
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class SF26GeneratorAgent(BaseAgent):
    """
    SF-26 Generator Agent
    
    Generates Standard Form 26 - Award/Contract.
    
    Features:
    - Populates SF-26 standard form
    - Contract award notice
    - FPDS-NG reporting data
    - SAM.gov award posting format
    - Contractor information extraction
    
    Dependencies:
    - BaseAgent: LLM interaction and common utilities
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514"
    ):
        """Initialize SF-26 Generator Agent"""
        super().__init__(
            name="SF-26 Generator Agent",
            api_key=api_key,
            model=model,
            temperature=0.2
        )
        
        self.template_path = Path(__file__).parent.parent / "templates" / "sf26_template.md"
        
        with open(self.template_path, 'r') as f:
            self.template = f.read()
        
        print("\n" + "="*70)
        print("SF-26 GENERATOR AGENT INITIALIZED")
        print("="*70)
        print(f"  ✓ BaseAgent initialized")
        print(f"  ✓ Template loaded: {self.template_path.name}")
        print("="*70 + "\n")
    
    def execute(self, task: Dict) -> Dict:
        """Execute SF-26 generation"""
        self.log("Starting SF-26 generation")

        solicitation_info = task.get('solicitation_info', {})
        contractor_info = task.get('contractor_info', {})
        award_info = task.get('award_info', {})
        config = task.get('config', {})
        program_name = solicitation_info.get('program_name', 'Unknown')

        # STEP 0: Cross-reference lookup for SSDD, IGCE, PWS, and all solicitation docs
        self._ssdd_reference = None
        self._igce_reference = None
        self._pws_reference = None
        self._acquisition_plan_reference = None

        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for SSDD (award decision)
                latest_ssdd = metadata_store.find_latest_document('ssdd', program_name)
                if latest_ssdd:
                    print(f"✅ Found SSDD: {latest_ssdd['id']}")
                    print(f"   Awardee: {latest_ssdd['extracted_data'].get('recommended_awardee', 'Unknown')}")
                    if not contractor_info.get('name'):
                        contractor_info['name'] = latest_ssdd['extracted_data'].get('recommended_awardee', 'TBD')
                    self._ssdd_reference = latest_ssdd['id']

                # Look for IGCE (contract value baseline)
                latest_igce = metadata_store.find_latest_document('igce', program_name)
                if latest_igce:
                    print(f"✅ Found IGCE: {latest_igce['id']}")
                    print(f"   Government Estimate: {latest_igce['extracted_data'].get('total_cost_formatted', 'N/A')}")
                    if not award_info.get('government_estimate'):
                        award_info['government_estimate'] = latest_igce['extracted_data'].get('total_cost_formatted', 'TBD')
                    self._igce_reference = latest_igce['id']

                # Look for PWS (scope of work)
                latest_pws = metadata_store.find_latest_document('pws', program_name)
                if latest_pws:
                    print(f"✅ Found PWS: {latest_pws['id']}")
                    award_info['period_of_performance'] = latest_pws['extracted_data'].get('period_of_performance', 'TBD')
                    self._pws_reference = latest_pws['id']

                # Look for Acquisition Plan (contract type and strategy)
                latest_acq = metadata_store.find_latest_document('acquisition_plan', program_name)
                if latest_acq:
                    print(f"✅ Found Acquisition Plan: {latest_acq['id']}")
                    award_info['contract_type'] = latest_acq['extracted_data'].get('contract_type', 'Firm Fixed Price (FFP)')
                    self._acquisition_plan_reference = latest_acq['id']

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")

        print("\n" + "="*70)
        print("GENERATING SF-26 AWARD/CONTRACT")
        print("="*70)
        print(f"Contractor: {contractor_info.get('name', 'Unknown')}")
        print(f"Award Amount: {award_info.get('total_value', 'TBD')}")
        print("="*70 + "\n")
        
        # Populate template
        content = self._populate_sf26_template(
            solicitation_info,
            contractor_info,
            award_info,
            config
        )
        
        # STEP 2: Save metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving SF-26 metadata...")
                metadata_store = DocumentMetadataStore()

                # Extract SF-26 specific data
                extracted_data = {
                    'contract_number': award_info.get('contract_number', 'TBD'),
                    'contractor_name': contractor_info.get('name', 'TBD'),
                    'contractor_duns': contractor_info.get('duns', 'TBD'),
                    'award_amount': award_info.get('total_value', 'TBD'),
                    'government_estimate': award_info.get('government_estimate', 'TBD'),
                    'contract_type': award_info.get('contract_type', 'Firm Fixed Price (FFP)'),
                    'effective_date': award_info.get('effective_date', datetime.now().strftime('%Y-%m-%d')),
                    'period_of_performance': award_info.get('period_of_performance', 'TBD'),
                    'business_size': contractor_info.get('size', 'Small Business')
                }

                # Track references
                references = {}
                if self._ssdd_reference:
                    references['ssdd'] = self._ssdd_reference
                if self._igce_reference:
                    references['igce'] = self._igce_reference
                if self._pws_reference:
                    references['pws'] = self._pws_reference
                if self._acquisition_plan_reference:
                    references['acquisition_plan'] = self._acquisition_plan_reference

                doc_id = metadata_store.save_document(
                    doc_type='sf26',
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
        print("✅ SF-26 GENERATION COMPLETE")
        print("="*70)

        return {
            'status': 'success',
            'content': content,
            'metadata': {
                'contract_number': award_info.get('contract_number', 'TBD'),
                'contractor': contractor_info.get('name', 'TBD'),
                'award_amount': award_info.get('total_value', 'TBD')
            }
        }
    
    def _populate_sf26_template(
        self,
        solicitation_info: Dict,
        contractor_info: Dict,
        award_info: Dict,
        config: Dict
    ) -> str:
        """Populate SF-26 template"""
        content = self.template
        
        # Contract number
        content = content.replace('{{contract_number}}', award_info.get('contract_number', 'TBD'))
        content = content.replace('{{effective_date}}', award_info.get('effective_date', datetime.now().strftime('%B %d, %Y')))
        content = content.replace('{{solicitation_number}}', solicitation_info.get('solicitation_number', 'TBD'))
        content = content.replace('{{solicitation_issue_date}}', solicitation_info.get('issue_date', 'TBD'))
        
        # Contractor information
        content = content.replace('{{contractor_name}}', contractor_info.get('name', 'TBD'))
        content = content.replace('{{contractor_duns}}', contractor_info.get('duns', 'TBD'))
        content = content.replace('{{contractor_address}}', contractor_info.get('address', 'TBD'))
        content = content.replace('{{business_size}}', contractor_info.get('size', 'Small Business'))
        content = content.replace('{{socioeconomic_status}}', contractor_info.get('socioeconomic', 'N/A'))
        
        # Award amount
        content = content.replace('{{total_contract_value}}', award_info.get('total_value', 'TBD'))
        content = content.replace('{{contract_value}}', award_info.get('total_value', 'TBD'))
        content = content.replace('{{base_period_value}}', award_info.get('base_value', 'TBD'))
        
        # Period of performance
        content = content.replace('{{period_of_performance}}', award_info.get('period', '12 months base + 4 option years'))
        content = content.replace('{{total_period}}', award_info.get('period', '60 months'))
        
        # Contract type
        content = content.replace('{{contract_type}}', award_info.get('contract_type', 'Firm-Fixed-Price'))
        
        # Set-aside
        content = content.replace('{{set_aside_type}}', contractor_info.get('set_aside', 'Small Business'))
        content = content.replace('{{naics_code}}', contractor_info.get('naics', '541512'))
        
        # Award date
        content = content.replace('{{award_date}}', datetime.now().strftime('%B %d, %Y'))
        
        # Fill remaining
        content = re.sub(r'\{\{[^}]+\}\}', 'TBD', content)
        
        return content
    
    def save_to_file(self, content: str, output_path: str, convert_to_pdf: bool = True) -> Dict:
        """Save SF-26 to file"""
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
                print(f"  ✓ PDF saved: {pdf_path}")
            except Exception as e:
                print(f"  ⚠ PDF generation failed: {e}")
                result['pdf'] = None
        
        return result

