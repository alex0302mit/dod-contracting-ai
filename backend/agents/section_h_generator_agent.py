"""
Section H Generator Agent: Generates Section H (Special Contract Requirements)
Creates special terms, data rights, and cybersecurity requirements
"""

from typing import Dict
from pathlib import Path
import sys
from datetime import datetime
import re

sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.base_agent import BaseAgent
from backend.utils.document_metadata_store import DocumentMetadataStore


class SectionHGeneratorAgent(BaseAgent):
    """
    Section H Generator Agent
    
    Generates Section H - Special Contract Requirements.
    
    Features:
    - Cybersecurity requirements (CMMC, NIST 800-171)
    - Data rights provisions
    - Special contract terms
    - Contract-type aware
    """
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        super().__init__(name="Section H Generator Agent", api_key=api_key, model=model, temperature=0.4)
        
        self.template_path = Path(__file__).parent.parent / "templates" / "section_h_template.md"
        with open(self.template_path, 'r') as f:
            self.template = f.read()
        
        print("\n" + "="*70)
        print("SECTION H GENERATOR INITIALIZED")
        print("="*70)
        print(f"  ✓ Template loaded")
        print("="*70 + "\n")

    async def generate_with_collaboration(
        self,
        requirements: str,
        context: str,
        dependencies: Dict[str, str]
    ) -> Dict:
        """
        Phase 4: Generate Section H with dependency context

        Args:
            requirements: Requirements/assumptions text
            context: RAG context
            dependencies: Dict of dependency_name -> content

        Returns:
            Generation result with content and citations
        """
        self.log("PHASE 4: Generating Section H with collaboration")

        # Parse requirements into solicitation_info
        solicitation_info = self._parse_requirements(requirements)

        # Incorporate PWS content from dependencies if available
        pws_content = ""
        if "Section C - Performance Work Statement" in dependencies:
            pws_content = dependencies["Section C - Performance Work Statement"]
            self.log(f"Using PWS dependency ({len(pws_content)} chars)")

        # Incorporate Section L and M from dependencies for consistency
        if "Section L - Instructions to Offerors" in dependencies:
            section_l = dependencies["Section L - Instructions to Offerors"]
            self.log(f"Using Section L dependency ({len(section_l)} chars)")

        if "Section M - Evaluation Factors" in dependencies:
            section_m = dependencies["Section M - Evaluation Factors"]
            self.log(f"Using Section M dependency ({len(section_m)} chars)")

        # Execute generation with dependency-enriched info
        task = {
            'solicitation_info': solicitation_info,
            'pws_content': pws_content,
            'config': {},
            'dependencies': dependencies  # Pass through for reference
        }

        result = self.execute(task)

        # Add dependency references to content
        if dependencies:
            content = result['content']
            references_section = "\n\n---\n\n## Cross-References\n\n"
            references_section += "This document must be read in conjunction with:\n\n"
            if "Section C - Performance Work Statement" in dependencies:
                references_section += "- **Section C - Performance Work Statement**: Technical requirements\n"
            if "Section L - Instructions to Offerors" in dependencies:
                references_section += "- **Section L - Instructions to Offerors**: Proposal requirements\n"
            if "Section M - Evaluation Factors" in dependencies:
                references_section += "- **Section M - Evaluation Factors**: Evaluation criteria\n"
            result['content'] = content + references_section

        self.log("Section H generated with collaboration")

        return {
            "content": result['content'],
            "citations": [],
            "metadata": {}
        }

    def _parse_requirements(self, requirements: str) -> Dict:
        """Parse requirements text into solicitation_info dictionary"""
        solicitation_info = {}

        # Extract key information from requirements text
        lines = requirements.split('\n')
        for line in lines:
            line = line.strip('- ').strip()
            if not line:
                continue

            # Look for key patterns
            if 'program' in line.lower() or 'project' in line.lower():
                parts = line.split(':')
                if len(parts) > 1:
                    solicitation_info['program_name'] = parts[1].strip()
            elif 'cmmc' in line.lower():
                # Extract CMMC level
                if 'level 1' in line.lower():
                    solicitation_info['cmmc_level'] = '1'
                elif 'level 2' in line.lower():
                    solicitation_info['cmmc_level'] = '2'
                elif 'level 3' in line.lower():
                    solicitation_info['cmmc_level'] = '3'

        # Set defaults if not found
        solicitation_info.setdefault('program_name', 'Acquisition Program')
        solicitation_info.setdefault('cmmc_level', '2')
        solicitation_info.setdefault('solicitation_number', 'TBD')

        return solicitation_info

    def execute(self, task: Dict) -> Dict:
        """Execute Section H generation"""
        self.log("Starting Section H generation")

        solicitation_info = task.get('solicitation_info', {})
        pws_content = task.get('pws_content', '')
        config = task.get('config', {})
        program_name = solicitation_info.get('program_name', 'Unknown')

        # NEW: Cross-reference lookup
        if program_name != 'Unknown':
            try:
                metadata_store = DocumentMetadataStore()
                latest_pws = metadata_store.find_latest_document('pws', program_name)
                self._pws_reference = latest_pws['id'] if latest_pws else None
            except:
                self._pws_reference = None

        content = self._populate_template(solicitation_info, pws_content, config)

        # NEW: Save metadata
        if program_name != 'Unknown':
            try:
                metadata_store = DocumentMetadataStore()
                doc_id = metadata_store.save_document(
                    doc_type='section_h',
                    program=program_name,
                    content=content,
                    file_path='',
                    extracted_data={'cmmc_level': config.get('cmmc_level', '2')},
                    references={'pws': self._pws_reference} if self._pws_reference else {}
                )
            except:
                pass

        return {
            'status': 'success',
            'content': content,
            'metadata': {
                'cmmc_level': config.get('cmmc_level', '2'),
                'contract_type': config.get('contract_type', 'services')
            }
        }
    
    def _populate_template(self, solicitation_info: Dict, pws_content: str, config: Dict) -> str:
        """Populate Section H template"""
        content = self.template
        
        content = content.replace('{{solicitation_number}}', solicitation_info.get('solicitation_number', 'TBD'))
        content = content.replace('{{program_name}}', solicitation_info.get('program_name', 'TBD'))
        content = content.replace('{{date}}', datetime.now().strftime('%B %d, %Y'))
        
        # Cybersecurity
        content = content.replace('{{cmmc_level}}', config.get('cmmc_level', 'Level 2'))
        content = content.replace('{{cmmc_timeframe}}', config.get('cmmc_timeframe', '12 months'))
        content = content.replace('{{incident_reporting_hours}}', config.get('incident_reporting', '72'))
        
        # Fill remaining
        content = re.sub(r'\{\{[^}]+\}\}', 'TBD - To be specified based on contract requirements', content)
        return content
    
    def save_to_file(self, content: str, output_path: str, convert_to_pdf: bool = True) -> Dict:
        """Save Section H to file"""
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

