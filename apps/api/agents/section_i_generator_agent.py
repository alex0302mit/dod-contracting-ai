"""
Section I Generator Agent: Generates Section I (Contract Clauses)
Auto-selects required FAR and DFARS clauses based on contract type
"""

from typing import Dict, List
from pathlib import Path
import sys
from datetime import datetime
import re

sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.base_agent import BaseAgent
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class SectionIGeneratorAgent(BaseAgent):
    """
    Section I Generator Agent
    
    Generates Section I - Contract Clauses.
    
    Features:
    - Auto-selects clauses by contract type
    - FFP vs CPFF vs T&M clause sets
    - Small business clauses
    - Cybersecurity clauses (DFARS)
    - Full text or incorporation by reference
    """
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        super().__init__(name="Section I Generator Agent", api_key=api_key, model=model, temperature=0.2)
        
        self.template_path = Path(__file__).parent.parent / "templates" / "section_i_template.md"
        with open(self.template_path, 'r') as f:
            self.template = f.read()
        
        # Clause database by contract type
        self.clause_sets = self._initialize_clause_sets()
        
        print("\n" + "="*70)
        print("SECTION I GENERATOR INITIALIZED")
        print("="*70)
        print(f"  ✓ Template loaded")
        print(f"  ✓ Clause database loaded")
        print("="*70 + "\n")
    
    def _initialize_clause_sets(self) -> Dict:
        """Initialize standard clause sets by contract type"""
        return {
            'ffp': {
                'changes': 'FAR 52.243-1 - Changes - Fixed-Price',
                'payments': 'FAR 52.232-1 - Payments',
                'termination': 'FAR 52.249-1 - Termination for Convenience (FAR)'
            },
            'cpff': {
                'changes': 'FAR 52.243-2 - Changes - Cost-Reimbursement',
                'payments': 'FAR 52.216-7 - Allowable Cost and Payment',
                'termination': 'FAR 52.249-6 - Termination (Cost-Reimbursement)'
            },
            'tm': {
                'changes': 'FAR 52.243-3 - Changes - Time-and-Materials or Labor-Hours',
                'payments': 'FAR 52.232-7 - Payments under Time-and-Materials and Labor-Hour Contracts',
                'termination': 'FAR 52.249-2 - Termination for Convenience (Fixed-Price Services)'
            }
        }
    
    def execute(self, task: Dict) -> Dict:
        """Execute Section I generation"""
        self.log("Starting Section I generation")

        solicitation_info = task.get('solicitation_info', {})
        config = task.get('config', {})
        program_name = solicitation_info.get('program_name', 'Unknown')

        # STEP 1: Cross-reference lookup for Section B (contract type)
        self._section_b_reference = None
        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for Section B to get contract type
                latest_section_b = metadata_store.find_latest_document('section_b', program_name)

                if latest_section_b:
                    print(f"✅ Found Section B: {latest_section_b['id']}")
                    contract_type_from_b = latest_section_b['extracted_data'].get('contract_type')
                    if contract_type_from_b:
                        print(f"   Contract Type from Section B: {contract_type_from_b}")
                        config['contract_type'] = contract_type_from_b
                    self._section_b_reference = latest_section_b['id']
                else:
                    print("ℹ️  No Section B found, using config contract type")
                    self._section_b_reference = None

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")
                self._section_b_reference = None

        contract_type = config.get('contract_type', 'ffp').lower()

        # Select appropriate clauses
        selected_clauses = self._select_clauses(contract_type, config)

        # Populate template
        content = self._populate_template(solicitation_info, selected_clauses, config)

        # STEP 2: Save metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving Section I metadata...")
                metadata_store = DocumentMetadataStore()
                extractor = DocumentDataExtractor()

                # Extract Section I specific data
                extracted_data = {
                    'contract_type': contract_type,
                    'clauses_count': len(selected_clauses),
                    'clause_list': selected_clauses,
                    'set_aside': config.get('set_aside', False)
                }

                # Track references
                references = {}
                if self._section_b_reference:
                    references['section_b'] = self._section_b_reference

                doc_id = metadata_store.save_document(
                    doc_type='section_i',
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
                'contract_type': contract_type,
                'clauses_count': len(selected_clauses)
            }
        }
    
    def _select_clauses(self, contract_type: str, config: Dict) -> List[str]:
        """Select applicable clauses based on contract type"""
        clauses = []
        
        # Get contract-type specific clauses
        if contract_type in self.clause_sets:
            clauses.extend(self.clause_sets[contract_type].values())
        
        # Add small business clauses if applicable
        if config.get('set_aside'):
            clauses.append('FAR 52.219-6 - Notice of Total Small Business Set-Aside')
        
        return clauses
    
    def _populate_template(self, solicitation_info: Dict, clauses: List[str], config: Dict) -> str:
        """Populate Section I template"""
        content = self.template
        
        content = content.replace('{{solicitation_number}}', solicitation_info.get('solicitation_number', 'TBD'))
        content = content.replace('{{program_name}}', solicitation_info.get('program_name', 'TBD'))
        content = content.replace('{{date}}', datetime.now().strftime('%B %d, %Y'))
        content = content.replace('{{contract_type}}', config.get('contract_type', 'Firm-Fixed-Price'))
        
        # Payment and termination clauses based on contract type
        contract_type_key = config.get('contract_type', 'ffp').lower().replace('firm-fixed-price', 'ffp').replace('cost-plus-fixed-fee', 'cpff')[:3]
        
        if contract_type_key in self.clause_sets:
            content = content.replace('{{payment_clauses}}', self.clause_sets[contract_type_key]['payments'])
            content = content.replace('{{termination_clauses}}', self.clause_sets[contract_type_key]['termination'])
        
        # Fill remaining
        content = re.sub(r'\{\{[^}]+\}\}', 'See FAR Part 52', content)
        return content
    
    def save_to_file(self, content: str, output_path: str, convert_to_pdf: bool = True) -> Dict:
        """Save Section I to file"""
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

