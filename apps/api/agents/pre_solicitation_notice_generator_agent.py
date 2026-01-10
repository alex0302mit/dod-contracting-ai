"""
Pre-Solicitation Notice Generator Agent: Generates Pre-Solicitation Notices per FAR 5.201
Creates 15-day advance notice before solicitation release
"""

from typing import Dict, Optional
from pathlib import Path
import sys
from datetime import datetime, timedelta
import re

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.base_agent import BaseAgent
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class PreSolicitationNoticeGeneratorAgent(BaseAgent):
    """
    Pre-Solicitation Notice Generator Agent
    
    Generates Pre-Solicitation Notices per FAR 5.201 (15-day minimum notice).
    
    Features:
    - Summarizes requirement from PWS
    - Provides solicitation release date (15+ days advance notice)
    - Includes small business set-aside determination
    - SAM.gov compatible format
    - Contract type aware: R&D highlights innovation objectives
    
    Dependencies:
    - BaseAgent: LLM interaction and common utilities
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize Pre-Solicitation Notice Generator Agent
        
        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        super().__init__(
            name="Pre-Solicitation Notice Generator Agent",
            api_key=api_key,
            model=model,
            temperature=0.5
        )
        
        self.template_path = Path(__file__).parent.parent / "templates" / "pre_solicitation_notice_template.md"
        
        # Load template
        with open(self.template_path, 'r') as f:
            self.template = f.read()
        
        print("\n" + "="*70)
        print("PRE-SOLICITATION NOTICE GENERATOR AGENT INITIALIZED")
        print("="*70)
        print(f"  ✓ BaseAgent initialized")
        print(f"  ✓ Template loaded: {self.template_path.name}")
        print("="*70 + "\n")
    
    def execute(self, task: Dict) -> Dict:
        """
        Execute Pre-Solicitation Notice generation
        
        Args:
            task: Dictionary containing:
                - project_info: Program details
                - requirements_content: PWS/SOW/SOO content (optional)
                - config: Optional configuration
        
        Returns:
            Dictionary with Pre-Solicitation Notice content and metadata
        """
        self.log("Starting Pre-Solicitation Notice generation")

        project_info = task.get('project_info', {})
        requirements_content = task.get('requirements_content', '')
        config = task.get('config', {})

        contract_type = config.get('contract_type', 'services')
        program_name = project_info.get('program_name', 'Unknown')

        # NEW: Cross-reference lookup - Find Acquisition Plan and IGCE
        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for Acquisition Plan (timeline, set-aside info)
                latest_acq_plan = metadata_store.find_latest_document('acquisition_plan', program_name)
                # Look for IGCE (estimated value)
                latest_igce = metadata_store.find_latest_document('igce', program_name)

                if latest_acq_plan:
                    print(f"✅ Found Acquisition Plan: {latest_acq_plan['id']}")
                    project_info['acquisition_plan_data'] = latest_acq_plan['extracted_data']
                    self._acq_plan_reference = latest_acq_plan['id']
                else:
                    print(f"⚠️  No Acquisition Plan found for {program_name}")
                    self._acq_plan_reference = None

                if latest_igce:
                    print(f"✅ Found IGCE: {latest_igce['id']}")
                    print(f"   Estimated Value: {latest_igce['extracted_data'].get('total_cost_formatted', 'N/A')}")
                    project_info['estimated_value'] = latest_igce['extracted_data'].get('total_cost_formatted', 'TBD')
                    project_info['igce_data'] = latest_igce['extracted_data']
                    self._igce_reference = latest_igce['id']
                else:
                    print(f"⚠️  No IGCE found for {program_name}")
                    self._igce_reference = None

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")
                self._acq_plan_reference = None
                self._igce_reference = None
        else:
            self._acq_plan_reference = None
            self._igce_reference = None

        print("\n" + "="*70)
        print("GENERATING PRE-SOLICITATION NOTICE (FAR 5.201)")
        print("="*70)
        print(f"Program: {program_name}")
        print(f"Contract Type: {contract_type}")
        print("="*70 + "\n")
        
        # Step 1: Calculate key dates (15+ days advance notice required)
        print("STEP 1: Calculating solicitation dates...")
        dates = self._calculate_solicitation_dates(config)
        print(f"  ✓ RFP Release: {dates['rfp_release_date']}")
        print(f"  ✓ Proposals Due: {dates['proposal_due_date']}")
        print(f"  ✓ Award: {dates['award_date']}")
        
        # Step 2: Determine small business set-aside
        print("\nSTEP 2: Determining small business set-aside...")
        small_business = self._determine_set_aside(project_info)
        print(f"  ✓ Set-aside: {small_business['set_aside_type']}")
        
        # Step 3: Extract requirement summary
        print("\nSTEP 3: Extracting requirement summary...")
        summary = self._extract_requirement_summary(requirements_content, contract_type)
        print(f"  ✓ Summary extracted ({len(summary)} characters)")
        
        # Step 4: Populate template
        print("\nSTEP 4: Populating Pre-Solicitation Notice template...")
        content = self._populate_template(
            project_info,
            dates,
            small_business,
            summary,
            config
        )
        print(f"  ✓ Template populated ({len(content)} characters)")
        
        print("\n" + "="*70)
        print("✅ PRE-SOLICITATION NOTICE GENERATION COMPLETE")
        print("="*70)

        # NEW: Save document metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving document metadata for cross-referencing...")
                metadata_store = DocumentMetadataStore()

                # Extract structured data from generated content
                extracted_data = {
                    'rfp_release_date': dates['rfp_release_date'],
                    'proposal_due_date': dates['proposal_due_date'],
                    'award_date': dates['award_date'],
                    'notice_publication_date': dates.get('notice_date', datetime.now().strftime('%Y-%m-%d')),
                    'set_aside_type': small_business['set_aside_type'],
                    'contract_type': contract_type,
                    'estimated_value': project_info.get('estimated_value', 'TBD'),
                    'requirement_summary': summary
                }

                # Build references dict
                references = {}
                if self._acq_plan_reference:
                    references['acquisition_plan'] = self._acq_plan_reference
                if self._igce_reference:
                    references['igce'] = self._igce_reference

                # Save to metadata store
                doc_id = metadata_store.save_document(
                    doc_type='pre_solicitation_notice',
                    program=program_name,
                    content=content,
                    file_path='',  # Will be set by orchestrator
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
                'rfp_release_date': dates['rfp_release_date'],
                'proposal_due_date': dates['proposal_due_date'],
                'set_aside_type': small_business['set_aside_type'],
                'contract_type': contract_type
            }
        }
    
    def _calculate_solicitation_dates(self, config: Dict) -> Dict:
        """Calculate solicitation timeline dates"""
        # Pre-solicitation notice must be posted at least 15 days before RFP release
        notice_posted = datetime.now()
        
        # RFP release: 15+ days from notice (use config or default to 21 days)
        rfp_days = config.get('rfp_release_days', 21)
        rfp_release = notice_posted + timedelta(days=rfp_days)
        
        # Proposal preparation time: typically 30-45 days
        proposal_days = config.get('proposal_days', 45)
        proposal_due = rfp_release + timedelta(days=proposal_days)
        
        # Questions deadline: typically 14 days before proposal due
        questions_deadline = proposal_due - timedelta(days=14)
        
        # Industry day: typically 1 week after RFP release
        industry_day = rfp_release + timedelta(days=7)
        
        # Draft RFP: typically 2 weeks before final RFP
        draft_rfp = rfp_release - timedelta(days=14)
        
        # Contract award: typically 60-90 days after proposal due
        award_date = proposal_due + timedelta(days=75)
        
        return {
            'notice_posted_date': notice_posted.strftime('%B %d, %Y'),
            'rfp_release_date': rfp_release.strftime('%B %d, %Y'),
            'proposal_due_date': proposal_due.strftime('%B %d, %Y at 2:00 PM EST'),
            'questions_deadline': questions_deadline.strftime('%B %d, %Y'),
            'industry_day_date': industry_day.strftime('%B %d, %Y'),
            'draft_rfp_date': draft_rfp.strftime('%B %d, %Y'),
            'award_date': award_date.strftime('%B %Y'),
            'proposal_prep_days': str(proposal_days)
        }
    
    def _determine_set_aside(self, project_info: Dict) -> Dict:
        """Determine small business set-aside classification"""
        # Parse estimated value
        estimated_value_str = project_info.get('estimated_value', '$5M')
        value_millions = 5.0
        if 'M' in estimated_value_str:
            try:
                value_millions = float(re.findall(r'[\d\.]+', estimated_value_str)[0])
            except:
                pass
        
        # Set-aside determination
        if value_millions < 10:
            set_aside_type = "100% Small Business Set-Aside"
            set_aside_rationale = "Market research indicates adequate small business competition"
            eligible_categories = """
- Small Business (SB)
- Small Disadvantaged Business (SDB)
- Women-Owned Small Business (WOSB)
- HUBZone Small Business
- Service-Disabled Veteran-Owned Small Business (SDVOSB)
- Veteran-Owned Small Business (VOSB)
"""
        else:
            set_aside_type = "Unrestricted"
            set_aside_rationale = "Program exceeds small business threshold; small business subcontracting plan required for awards ≥$750K"
            eligible_categories = """
- All business sizes eligible
- Small business subcontracting plan required if contract value ≥$750K (non-small business prime)
"""
        
        return {
            'set_aside_type': set_aside_type,
            'set_aside_rationale': set_aside_rationale,
            'eligible_categories': eligible_categories,
            'naics_code': "541512",
            'size_standard': "$34M",
            'socioeconomic_applicability': "is set aside for small businesses" if value_millions < 10 else "is unrestricted but encourages small business subcontracting"
        }
    
    def _extract_requirement_summary(self, requirements_content: str, contract_type: str) -> str:
        """Extract high-level requirement summary"""
        if not requirements_content:
            if contract_type == 'research_development':
                return "Research and development of advanced technology solutions to meet mission requirements."
            else:
                return "Cloud-based system development, deployment, and operations and maintenance services."
        
        # Use LLM to summarize requirements
        prompt = f"""Summarize the following requirements in 2-3 paragraphs for a pre-solicitation notice.
Focus on what the Government needs, not how to do it.

Contract Type: {contract_type}

Requirements:
{requirements_content[:5000]}

Write a clear, concise summary suitable for a public notice."""
        
        summary = self.call_llm(prompt, max_tokens=500)
        return summary.strip()
    
    def _populate_template(
        self,
        project_info: Dict,
        dates: Dict,
        small_business: Dict,
        summary: str,
        config: Dict
    ) -> str:
        """Populate pre-solicitation notice template"""
        content = self.template
        
        # Generate solicitation number
        sol_number = config.get('solicitation_number', f"W911XX-25-R-{datetime.now().strftime('%m%d')}")
        
        # Basic information
        content = content.replace('{{solicitation_number}}', sol_number)
        content = content.replace('{{posted_date}}', dates['notice_posted_date'])
        content = content.replace('{{response_date}}', dates['proposal_due_date'])
        content = content.replace('{{classification}}', config.get('classification', 'UNCLASSIFIED'))
        
        # Agency information
        content = content.replace('{{agency}}', project_info.get('organization', 'Department of Defense'))
        content = content.replace('{{office}}', config.get('office', 'Contracting Office'))
        content = content.replace('{{location}}', config.get('location', 'Washington, DC'))
        
        # Program information
        content = content.replace('{{program_name}}', project_info.get('program_name', 'TBD'))
        content = content.replace('{{program_description}}', summary)
        content = content.replace('{{scope_of_work}}', summary)
        content = content.replace('{{estimated_value}}', project_info.get('estimated_value', 'TBD'))
        content = content.replace('{{period_of_performance}}', project_info.get('period_of_performance', '12 months base + 4 option years'))
        
        # Dates
        for key, value in dates.items():
            content = content.replace('{{' + key + '}}', str(value))
        content = content.replace('{{anticipated_release_date}}', dates['rfp_release_date'])
        content = content.replace('{{anticipated_due_date}}', dates['proposal_due_date'])
        
        # Small business
        content = content.replace('{{set_aside_type}}', small_business['set_aside_type'])
        content = content.replace('{{set_aside_rationale}}', small_business['set_aside_rationale'])
        content = content.replace('{{eligible_categories}}', small_business['eligible_categories'])
        content = content.replace('{{naics_code}}', small_business['naics_code'])
        content = content.replace('{{size_standard}}', small_business['size_standard'])
        content = content.replace('{{socioeconomic_applicability}}', small_business['socioeconomic_applicability'])
        
        # Contract information
        contract_type = config.get('contract_type', 'Firm-Fixed-Price (FFP)')
        content = content.replace('{{contract_type}}', contract_type)
        content = content.replace('{{contract_structure}}', '12 month base period + 4 one-year option periods')
        content = content.replace('{{solicitation_type}}', 'Request for Proposal (RFP)')
        content = content.replace('{{source_selection_method}}', 'Best Value Trade-Off')
        
        # POC information
        content = content.replace('{{poc_name}}', config.get('poc_name', project_info.get('contracting_officer', 'John Doe')))
        content = content.replace('{{poc_title}}', config.get('poc_title', 'Contracting Officer'))
        content = content.replace('{{poc_email}}', config.get('poc_email', project_info.get('ko_email', 'contracting@agency.mil')))
        content = content.replace('{{poc_phone}}', config.get('poc_phone', project_info.get('ko_phone', '(703) 555-0000')))
        
        # Notice ID
        content = content.replace('{{notice_id}}', f"PSN-{datetime.now().strftime('%Y%m%d')}-{sol_number}")
        
        # Fill remaining placeholders
        content = re.sub(r'\{\{[^}]+\}\}', 'TBD', content)
        
        return content
    
    def save_to_file(self, content: str, output_path: str, convert_to_pdf: bool = True) -> Dict:
        """Save Pre-Solicitation Notice to file"""
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

