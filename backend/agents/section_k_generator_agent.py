"""
Section K Generator Agent: Generates Section K (Representations and Certifications)
Creates required offeror certifications per FAR 52.204-8
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


class SectionKGeneratorAgent(BaseAgent):
    """
    Section K Generator Agent
    
    Generates Section K - Representations, Certifications, and Other Statements.
    
    Features:
    - Standard FAR 52.204-8 provisions
    - SAM.gov integration references
    - Small business certifications
    - Contract-type specific reps
    """
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        super().__init__(name="Section K Generator Agent", api_key=api_key, model=model, temperature=0.2)
        
        self.template_path = Path(__file__).parent.parent / "templates" / "section_k_template.md"
        with open(self.template_path, 'r') as f:
            self.template = f.read()
        
        print("\n" + "="*70)
        print("SECTION K GENERATOR INITIALIZED")
        print("="*70)
        print(f"  ✓ Template loaded")
        print("="*70 + "\n")
    
    def execute(self, task: Dict) -> Dict:
        """Execute Section K generation"""
        self.log("Starting Section K generation")

        solicitation_info = task.get('solicitation_info', {})
        config = task.get('config', {})
        program_name = solicitation_info.get('program_name', 'Unknown')

        # Note: Section K typically doesn't need cross-references (representations are standard)
        # But we still save metadata for completeness

        content = self._populate_template(solicitation_info, config)

        # STEP: Save metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving Section K metadata...")
                metadata_store = DocumentMetadataStore()

                # Extract Section K specific data
                extracted_data = {
                    'naics_code': config.get('naics_code', '541512'),
                    'set_aside': config.get('set_aside', 'Small Business'),
                    'size_standard': config.get('size_standard', '$34M'),
                    'representation_types': [
                        'FAR 52.204-8 - Annual Representations',
                        'FAR 52.219-1 - Small Business Program',
                        'FAR 52.219-2 - EEO Certification'
                    ]
                }

                doc_id = metadata_store.save_document(
                    doc_type='section_k',
                    program=program_name,
                    content=content,
                    file_path=None,
                    extracted_data=extracted_data,
                    references={}  # Section K typically has no cross-references
                )

                print(f"✅ Metadata saved: {doc_id}")

            except Exception as e:
                print(f"⚠️  Failed to save metadata: {str(e)}")

        return {
            'status': 'success',
            'content': content,
            'metadata': {
                'naics_code': config.get('naics_code', '541512'),
                'set_aside': config.get('set_aside', 'Small Business')
            }
        }
    
    def _populate_template(self, solicitation_info: Dict, config: Dict) -> str:
        """Populate Section K template"""
        content = self.template
        
        content = content.replace('{{solicitation_number}}', solicitation_info.get('solicitation_number', 'TBD'))
        content = content.replace('{{program_name}}', solicitation_info.get('program_name', 'TBD'))
        content = content.replace('{{date}}', datetime.now().strftime('%B %d, %Y'))
        
        # NAICS and size standard
        content = content.replace('{{naics_code}}', config.get('naics_code', '541512'))
        content = content.replace('{{size_standard}}', config.get('size_standard', '$34M'))
        
        # Fill remaining
        content = re.sub(r'\{\{[^}]+\}\}', '', content)
        return content
    
    def save_to_file(self, content: str, output_path: str, convert_to_pdf: bool = True) -> Dict:
        """Save Section K to file"""
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

