"""
Amendment Generator Agent: Generates solicitation amendments per FAR 15.206
Tracks changes, Q&A responses, and deadline extensions
"""

from typing import Dict, List, Optional
from pathlib import Path
import sys
from datetime import datetime, timedelta
import re

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.base_agent import BaseAgent
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class AmendmentGeneratorAgent(BaseAgent):
    """
    Amendment Generator Agent
    
    Generates solicitation amendments per FAR 14.208 and FAR 15.206.
    
    Features:
    - Tracks amendment sequence (0001, 0002, etc.)
    - Documents changes to solicitation sections
    - Incorporates Q&A responses
    - Manages deadline extensions
    - Generates SAM.gov-compatible notices
    - Creates redline comparisons
    
    Dependencies:
    - BaseAgent: LLM interaction and common utilities
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize Amendment Generator Agent
        
        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        super().__init__(
            name="Amendment Generator Agent",
            api_key=api_key,
            model=model,
            temperature=0.4
        )
        
        self.template_path = Path(__file__).parent.parent / "templates" / "amendment_template.md"
        
        # Load template
        with open(self.template_path, 'r') as f:
            self.template = f.read()
        
        # Amendment tracking
        self.amendment_history = []
        
        print("\n" + "="*70)
        print("AMENDMENT GENERATOR AGENT INITIALIZED")
        print("="*70)
        print(f"  ✓ BaseAgent initialized")
        print(f"  ✓ Template loaded: {self.template_path.name}")
        print("="*70 + "\n")
    
    def execute(self, task: Dict) -> Dict:
        """
        Execute amendment generation

        Args:
            task: Dictionary containing:
                - solicitation_info: Solicitation details
                - amendment_number: Amendment sequence (e.g., "0001")
                - changes: List of changes to document
                - qa_responses: Optional Q&A to incorporate
                - config: Optional configuration

        Returns:
            Dictionary with amendment content and metadata
        """
        self.log("Starting amendment generation")

        solicitation_info = task.get('solicitation_info', {})
        amendment_number = task.get('amendment_number', '0001')
        changes = task.get('changes', [])
        qa_responses = task.get('qa_responses', [])
        config = task.get('config', {})
        program_name = solicitation_info.get('program_name', 'Unknown')

        # STEP 0: Cross-reference lookup for original documents
        self._pws_reference = None
        self._sow_reference = None
        self._soo_reference = None
        self._qa_reference = None
        self._section_l_reference = None
        self._section_m_reference = None

        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for original work statement (PWS, SOW, or SOO)
                latest_pws = metadata_store.find_latest_document('pws', program_name)
                latest_sow = metadata_store.find_latest_document('sow', program_name)
                latest_soo = metadata_store.find_latest_document('soo', program_name)

                if latest_pws:
                    print(f"✅ Found PWS: {latest_pws['id']}")
                    self._pws_reference = latest_pws['id']
                    solicitation_info['original_pws_id'] = latest_pws['id']

                if latest_sow:
                    print(f"✅ Found SOW: {latest_sow['id']}")
                    self._sow_reference = latest_sow['id']
                    solicitation_info['original_sow_id'] = latest_sow['id']

                if latest_soo:
                    print(f"✅ Found SOO: {latest_soo['id']}")
                    self._soo_reference = latest_soo['id']
                    solicitation_info['original_soo_id'] = latest_soo['id']

                # Look for Q&A document
                latest_qa = metadata_store.find_latest_document('qa', program_name)
                if latest_qa:
                    print(f"✅ Found Q&A: {latest_qa['id']}")
                    print(f"   Questions Answered: {latest_qa['extracted_data'].get('total_questions', 0)}")
                    self._qa_reference = latest_qa['id']
                    # Use Q&A data if qa_responses not provided
                    if not qa_responses:
                        qa_responses = latest_qa['extracted_data'].get('questions', [])

                # Look for Section L and M (if dates are changing)
                if any(c.get('section') in ['Section L', 'Section M'] for c in changes):
                    latest_l = metadata_store.find_latest_document('section_l', program_name)
                    latest_m = metadata_store.find_latest_document('section_m', program_name)

                    if latest_l:
                        print(f"✅ Found Section L: {latest_l['id']}")
                        self._section_l_reference = latest_l['id']

                    if latest_m:
                        print(f"✅ Found Section M: {latest_m['id']}")
                        self._section_m_reference = latest_m['id']

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")
                # Continue with generation even if cross-reference fails
        
        print("\n" + "="*70)
        print(f"GENERATING AMENDMENT {amendment_number}")
        print("="*70)
        print(f"Solicitation: {solicitation_info.get('solicitation_number', 'Unknown')}")
        print(f"Changes: {len(changes)}")
        print(f"Q&A Responses: {len(qa_responses)}")
        print("="*70 + "\n")
        
        # Step 1: Analyze changes
        print("STEP 1: Analyzing changes...")
        change_analysis = self._analyze_changes(changes)
        print(f"  ✓ {change_analysis['section_count']} sections affected")
        print(f"  ✓ Impact level: {change_analysis['impact_level']}")
        
        # Step 2: Determine deadline extension
        print("\nSTEP 2: Calculating deadline extension...")
        deadline_info = self._calculate_deadline_extension(change_analysis, solicitation_info, config)
        print(f"  ✓ Extension: {deadline_info['extension_days']} days")
        print(f"  ✓ New due date: {deadline_info['revised_due_date']}")
        
        # Step 3: Generate change descriptions
        print("\nSTEP 3: Generating change descriptions...")
        change_descriptions = self._generate_change_descriptions(changes)
        print(f"  ✓ Generated {len(change_descriptions)} change descriptions")
        
        # Step 4: Process Q&A responses
        print("\nSTEP 4: Processing Q&A responses...")
        qa_summary = self._process_qa_responses(qa_responses)
        print(f"  ✓ Processed {len(qa_responses)} Q&A responses")
        
        # Step 5: Populate template
        print("\nSTEP 5: Populating amendment template...")
        content = self._populate_template(
            solicitation_info,
            amendment_number,
            change_analysis,
            change_descriptions,
            deadline_info,
            qa_summary,
            config
        )
        print(f"  ✓ Template populated ({len(content)} characters)")
        
        # Track amendment in history
        self.amendment_history.append({
            'number': amendment_number,
            'date': datetime.now().isoformat(),
            'changes_count': len(changes),
            'qa_count': len(qa_responses)
        })

        # STEP 6: Save metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving Amendment metadata...")
                metadata_store = DocumentMetadataStore()

                # Extract Amendment specific data
                extracted_data = {
                    'amendment_number': amendment_number,
                    'issue_date': datetime.now().strftime('%Y-%m-%d'),
                    'changes_count': len(changes),
                    'changes_list': changes,
                    'sections_affected': change_analysis['sections_affected'],
                    'impact_level': change_analysis['impact_level'],
                    'extension_days': deadline_info['extension_days'],
                    'original_due_date': deadline_info['original_due_date'],
                    'revised_due_date': deadline_info['revised_due_date'],
                    'qa_responses_count': len(qa_responses)
                }

                # Track references
                references = {}
                if self._pws_reference:
                    references['pws'] = self._pws_reference
                if self._sow_reference:
                    references['sow'] = self._sow_reference
                if self._soo_reference:
                    references['soo'] = self._soo_reference
                if self._qa_reference:
                    references['qa'] = self._qa_reference
                if self._section_l_reference:
                    references['section_l'] = self._section_l_reference
                if self._section_m_reference:
                    references['section_m'] = self._section_m_reference

                doc_id = metadata_store.save_document(
                    doc_type='amendment',
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
        print("✅ AMENDMENT GENERATION COMPLETE")
        print("="*70)

        return {
            'status': 'success',
            'content': content,
            'metadata': {
                'amendment_number': amendment_number,
                'changes_count': len(changes),
                'sections_affected': change_analysis['section_count'],
                'qa_responses_count': len(qa_responses),
                'extension_days': deadline_info['extension_days'],
                'revised_due_date': deadline_info['revised_due_date'],
                'impact_level': change_analysis['impact_level']
            }
        }
    
    def _analyze_changes(self, changes: List[Dict]) -> Dict:
        """
        Analyze the scope and impact of changes
        
        Args:
            changes: List of change dictionaries with keys:
                - section: Section ID (e.g., "Section L")
                - type: "add", "delete", "modify"
                - description: Change description
                - impact: "major", "minor", "administrative"
        
        Returns:
            Analysis of changes
        """
        sections_affected = set()
        impact_levels = []
        
        for change in changes:
            sections_affected.add(change.get('section', 'Unknown'))
            impact_levels.append(change.get('impact', 'minor'))
        
        # Determine overall impact
        if 'major' in impact_levels:
            overall_impact = 'Major'
        elif 'minor' in impact_levels:
            overall_impact = 'Minor'
        else:
            overall_impact = 'Administrative'
        
        return {
            'section_count': len(sections_affected),
            'sections_affected': list(sections_affected),
            'impact_level': overall_impact,
            'requires_extension': 'major' in impact_levels or len(changes) > 5
        }
    
    def _calculate_deadline_extension(
        self,
        change_analysis: Dict,
        solicitation_info: Dict,
        config: Dict
    ) -> Dict:
        """Calculate appropriate deadline extension"""
        # Parse original due date
        original_due_str = solicitation_info.get('proposal_due_date', '')
        try:
            original_due = datetime.strptime(original_due_str, '%B %d, %Y')
        except:
            original_due = datetime.now() + timedelta(days=30)
        
        # Determine extension based on impact
        if change_analysis['impact_level'] == 'Major':
            extension_days = config.get('major_extension_days', 14)
        elif change_analysis['impact_level'] == 'Minor':
            extension_days = config.get('minor_extension_days', 7)
        else:
            extension_days = config.get('admin_extension_days', 0)
        
        # Override with config if provided
        extension_days = config.get('extension_days', extension_days)
        
        revised_due = original_due + timedelta(days=extension_days)
        
        return {
            'original_due_date': original_due.strftime('%B %d, %Y at 2:00 PM EST'),
            'revised_due_date': revised_due.strftime('%B %d, %Y at 2:00 PM EST'),
            'extension_days': extension_days,
            'extension_rationale': f"Extension granted due to {change_analysis['impact_level'].lower()} changes to solicitation"
        }
    
    def _generate_change_descriptions(self, changes: List[Dict]) -> List[Dict]:
        """Generate detailed descriptions for each change"""
        descriptions = []
        
        for i, change in enumerate(changes, 1):
            descriptions.append({
                'item': str(i),
                'section': change.get('section', 'Unknown'),
                'change_type': change.get('type', 'modify'),
                'description': change.get('description', 'No description provided'),
                'impact': change.get('impact', 'minor')
            })
        
        return descriptions
    
    def _process_qa_responses(self, qa_responses: List[Dict]) -> Dict:
        """Process Q&A responses for incorporation"""
        if not qa_responses:
            return {
                'questions_count': 0,
                'qa_summary': 'No Q&A responses incorporated in this amendment.',
                'qa_attachment': 'N/A'
            }
        
        return {
            'questions_count': len(qa_responses),
            'qa_summary': f"This amendment incorporates responses to {len(qa_responses)} questions received from potential offerors. See Q&A document for details.",
            'qa_attachment': 'Attachment A'
        }
    
    def _populate_template(
        self,
        solicitation_info: Dict,
        amendment_number: str,
        change_analysis: Dict,
        change_descriptions: List[Dict],
        deadline_info: Dict,
        qa_summary: Dict,
        config: Dict
    ) -> str:
        """Populate amendment template"""
        content = self.template
        
        # Basic information
        content = content.replace('{{solicitation_number}}', solicitation_info.get('solicitation_number', 'TBD'))
        content = content.replace('{{amendment_number}}', amendment_number)
        content = content.replace('{{issue_date}}', datetime.now().strftime('%B %d, %Y'))
        content = content.replace('{{classification}}', config.get('classification', 'UNCLASSIFIED'))
        
        # Office information
        content = content.replace('{{issuing_office}}', solicitation_info.get('office', 'Contracting Office'))
        content = content.replace('{{contracting_officer}}', solicitation_info.get('contracting_officer', 'John Doe'))
        content = content.replace('{{co_email}}', solicitation_info.get('co_email', 'contracting@agency.mil'))
        content = content.replace('{{co_phone}}', solicitation_info.get('co_phone', '(703) 555-0000'))
        
        # Dates
        content = content.replace('{{original_issue_date}}', solicitation_info.get('issue_date', 'TBD'))
        content = content.replace('{{original_due_date}}', deadline_info['original_due_date'])
        content = content.replace('{{revised_due_date}}', deadline_info['revised_due_date'])
        content = content.replace('{{extension_days}}', str(deadline_info['extension_days']))
        content = content.replace('{{extension_rationale}}', deadline_info['extension_rationale'])
        
        # Amendment details
        content = content.replace('{{amendment_type}}', change_analysis['impact_level'])
        content = content.replace('{{amendment_reason}}', config.get('reason', 'Incorporate Q&A responses and clarify requirements'))
        
        # Changes summary table
        changes_table = '\n'.join([
            f"| {c['item']} | {c['section']} | {c['change_type'].title()} | {c['description'][:100]} |"
            for c in change_descriptions
        ])
        content = content.replace('{{changes_summary_table}}', changes_table)
        
        # Detailed changes
        detailed_changes = '\n\n'.join([
            f"**Change {c['item']}:** {c['section']}\n\n*Type:* {c['change_type'].title()}\n\n*Description:* {c['description']}\n\n*Impact:* {c['impact'].title()}"
            for c in change_descriptions
        ])
        content = content.replace('{{detailed_changes}}', detailed_changes)
        
        # Q&A information
        content = content.replace('{{questions_count}}', str(qa_summary['questions_count']))
        content = content.replace('{{qa_attachment_number}}', qa_summary['qa_attachment'])
        content = content.replace('{{key_clarifications}}', qa_summary['qa_summary'])
        
        # Acknowledgment
        acknowledgment_deadline = datetime.now() + timedelta(days=deadline_info['extension_days'])
        content = content.replace('{{acknowledgment_deadline}}', acknowledgment_deadline.strftime('%B %d, %Y at 2:00 PM EST'))
        content = content.replace('{{acknowledgment_submission_method}}', f"Email to {solicitation_info.get('co_email', 'contracting@agency.mil')}")
        
        # Fill remaining placeholders
        content = re.sub(r'\{\{[^}]+\}\}', 'None', content)
        
        return content
    
    def save_to_file(self, content: str, output_path: str, convert_to_pdf: bool = True) -> Dict:
        """Save amendment to file"""
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
    
    def get_next_amendment_number(self) -> str:
        """Get next amendment number in sequence"""
        if not self.amendment_history:
            return "0001"
        
        last_number = int(self.amendment_history[-1]['number'])
        return f"{last_number + 1:04d}"

