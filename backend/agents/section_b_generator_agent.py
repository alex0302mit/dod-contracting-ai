"""
Section B Generator Agent: Generates Section B (Supplies or Services and Prices)
Creates CLIN structure and pricing schedule
"""

from typing import Dict, List, Optional
from pathlib import Path
import sys
from datetime import datetime
import re

sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.base_agent import BaseAgent
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class SectionBGeneratorAgent(BaseAgent):
    """
    Section B Generator Agent
    
    Generates Section B - Supplies or Services and Prices (CLIN Structure).
    
    Features:
    - Auto-generates CLIN structure from deliverables
    - Calculates pricing from IGCE
    - Option year pricing
    - FFP vs T&M vs CPFF handling
    - Payment schedule generation
    """
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        super().__init__(name="Section B Generator Agent", api_key=api_key, model=model, temperature=0.3)
        
        self.template_path = Path(__file__).parent.parent / "templates" / "section_b_template.md"
        with open(self.template_path, 'r') as f:
            self.template = f.read()
        
        print("\n" + "="*70)
        print("SECTION B GENERATOR INITIALIZED")
        print("="*70)
        print(f"  ✓ Template loaded")
        print("="*70 + "\n")
    
    def execute(self, task: Dict) -> Dict:
        """Execute Section B generation"""
        self.log("Starting Section B generation")

        solicitation_info = task.get('solicitation_info', {})
        pws_content = task.get('pws_content', '')
        igce_data = task.get('igce_data', {})
        config = task.get('config', {})
        program_name = solicitation_info.get('program_name', 'Unknown')

        # NEW: Cross-reference lookup - Find PWS and IGCE
        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for PWS (deliverables for CLIN structure)
                latest_pws = metadata_store.find_latest_document('pws', program_name)
                # Look for IGCE (pricing data)
                latest_igce = metadata_store.find_latest_document('igce', program_name)

                if latest_pws:
                    print(f"✅ Found PWS: {latest_pws['id']}")
                    solicitation_info['pws_data'] = latest_pws['extracted_data']
                    self._pws_reference = latest_pws['id']
                else:
                    self._pws_reference = None

                if latest_igce:
                    print(f"✅ Found IGCE: {latest_igce['id']}")
                    print(f"   Total Cost: {latest_igce['extracted_data'].get('total_cost_formatted', 'N/A')}")
                    # Override igce_data with actual data from store
                    igce_data = latest_igce['extracted_data']
                    self._igce_reference = latest_igce['id']
                else:
                    self._igce_reference = None

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")
                self._pws_reference = None
                self._igce_reference = None
        else:
            self._pws_reference = None
            self._igce_reference = None
        
        # Generate CLIN structure
        clin_structure = self._generate_clin_structure(pws_content, igce_data, config)
        
        # Populate template
        content = self._populate_template(solicitation_info, clin_structure, config)

        # NEW: Save document metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving document metadata for cross-referencing...")
                metadata_store = DocumentMetadataStore()

                extracted_data = {
                    'clins': clin_structure['clins'],
                    'clins_count': len(clin_structure['clins']),
                    'total_value': clin_structure['total_value'],
                    'contract_type': config.get('contract_type', 'FFP')
                }

                references = {}
                if hasattr(self, '_pws_reference') and self._pws_reference:
                    references['pws'] = self._pws_reference
                if hasattr(self, '_igce_reference') and self._igce_reference:
                    references['igce'] = self._igce_reference

                doc_id = metadata_store.save_document(
                    doc_type='section_b',
                    program=program_name,
                    content=content,
                    file_path='',
                    extracted_data=extracted_data,
                    references=references
                )

                print(f"✅ Document metadata saved: {doc_id}")

            except Exception as e:
                print(f"⚠️  Failed to save document metadata: {str(e)}")

        return {
            'status': 'success',
            'content': content,
            'metadata': {
                'clins_count': len(clin_structure['clins']),
                'total_value': clin_structure['total_value']
            }
        }
    
    def _generate_clin_structure(self, pws_content: str, igce_data: Dict, config: Dict) -> Dict:
        """Generate CLIN structure from deliverables"""
        # Default CLIN structure
        clins = [
            {
                'number': '0001',
                'description': 'Base Period Services',
                'quantity': '1',
                'unit': 'LOT',
                'unit_price': igce_data.get('base_year_cost', '$1,200,000'),
                'extended': igce_data.get('base_year_cost', '$1,200,000')
            },
            {
                'number': '0002',
                'description': 'Option Year 1 Services',
                'quantity': '1',
                'unit': 'LOT',
                'unit_price': igce_data.get('option_1_cost', '$1,200,000'),
                'extended': igce_data.get('option_1_cost', '$1,200,000')
            },
            {
                'number': '0003',
                'description': 'Option Year 2 Services',
                'quantity': '1',
                'unit': 'LOT',
                'unit_price': igce_data.get('option_2_cost', '$1,200,000'),
                'extended': igce_data.get('option_2_cost', '$1,200,000')
            },
            {
                'number': '0004',
                'description': 'Option Year 3 Services',
                'quantity': '1',
                'unit': 'LOT',
                'unit_price': igce_data.get('option_3_cost', '$1,200,000'),
                'extended': igce_data.get('option_3_cost', '$1,200,000')
            },
            {
                'number': '0005',
                'description': 'Option Year 4 Services',
                'quantity': '1',
                'unit': 'LOT',
                'unit_price': igce_data.get('option_4_cost', '$1,200,000'),
                'extended': igce_data.get('option_4_cost', '$1,200,000')
            }
        ]
        
        return {
            'clins': clins,
            'total_value': config.get('total_value', '$6,000,000')
        }
    
    def _populate_template(self, solicitation_info: Dict, clin_structure: Dict, config: Dict) -> str:
        """
        Populate Section B template with CLIN data
        
        IMPORTANT: CLIN placeholder replacements must use proper table row format
        to maintain markdown table structure. Plain 'TBD' breaks table parsing.
        """
        content = self.template
        
        # Basic info replacements
        content = content.replace('{{solicitation_number}}', solicitation_info.get('solicitation_number', 'TBD'))
        content = content.replace('{{program_name}}', solicitation_info.get('program_name', 'TBD'))
        content = content.replace('{{date}}', datetime.now().strftime('%B %d, %Y'))
        
        # Get CLINs from structure (use defaults if not available)
        clins = clin_structure.get('clins', [])
        
        # Base period CLIN table row
        if len(clins) > 0:
            base_clin = clins[0]
            base_clins = f"| {base_clin['number']} | {base_clin['description']} | {base_clin['quantity']} | {base_clin['unit']} | {base_clin['unit_price']} | {base_clin['extended']} |"
            base_total = base_clin['extended']
        else:
            base_clins = '| 0001 | Base Period Services | 1 | LOT | $1,200,000 | $1,200,000 |'
            base_total = '$1,200,000'
        
        content = content.replace('{{base_period_clins}}', base_clins)
        content = content.replace('{{base_period_total}}', base_total)
        content = content.replace('{{base_period}}', 'Year 1')
        
        # Option period CLIN table rows - MUST be proper table row format, not plain 'TBD'
        # This is critical for proper markdown table rendering
        option_periods = [
            ('option_1_clins', 'option_1_total', 'option_period_1', 1),
            ('option_2_clins', 'option_2_total', 'option_period_2', 2),
            ('option_3_clins', 'option_3_total', 'option_period_3', 3),
            ('option_4_clins', 'option_4_total', 'option_period_4', 4),
        ]
        
        for clin_key, total_key, period_key, idx in option_periods:
            if len(clins) > idx:
                opt_clin = clins[idx]
                opt_row = f"| {opt_clin['number']} | {opt_clin['description']} | {opt_clin['quantity']} | {opt_clin['unit']} | {opt_clin['unit_price']} | {opt_clin['extended']} |"
                opt_total = opt_clin['extended']
            else:
                # Use TBD but in proper table row format to maintain table structure
                opt_row = '| TBD | TBD | TBD | TBD | TBD | TBD |'
                opt_total = 'TBD'
            
            content = content.replace('{{' + clin_key + '}}', opt_row)
            content = content.replace('{{' + total_key + '}}', opt_total)
            content = content.replace('{{' + period_key + '}}', f'Year {idx + 1}')
        
        # Contract type and total value
        content = content.replace('{{contract_type}}', config.get('contract_type', 'Firm-Fixed-Price'))
        content = content.replace('{{total_contract_value}}', clin_structure['total_value'])
        
        # Fill any remaining placeholders with TBD
        # Note: At this point, no table row placeholders should remain
        content = re.sub(r'\{\{[^}]+\}\}', 'TBD', content)
        return content
    
    def save_to_file(self, content: str, output_path: str, convert_to_pdf: bool = True) -> Dict:
        """Save Section B to file"""
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

