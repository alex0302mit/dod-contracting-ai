"""
Industry Day Generator Agent: Generates Industry Day briefing materials
Creates agenda, presentation slides, and registration forms for vendor engagement
"""

from typing import Dict, Optional, List
from pathlib import Path
import sys
from datetime import datetime, timedelta
import re

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.base_agent import BaseAgent
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class IndustryDayGeneratorAgent(BaseAgent):
    """
    Industry Day Generator Agent
    
    Generates comprehensive Industry Day briefing materials.
    
    Features:
    - Agenda with timeline (typically 2-4 hours)
    - Program overview briefing slides (8-15 slides)
    - Q&A format and submission process
    - Registration requirements
    - Small business outreach emphasis
    - Contract type aware: R&D includes technical interchange
    
    Dependencies:
    - BaseAgent: LLM interaction and common utilities
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize Industry Day Generator Agent
        
        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        super().__init__(
            name="Industry Day Generator Agent",
            api_key=api_key,
            model=model,
            temperature=0.6  # Slightly higher for creative presentation content
        )
        
        self.template_path = Path(__file__).parent.parent / "templates" / "industry_day_template.md"
        
        # Load template
        with open(self.template_path, 'r') as f:
            self.template = f.read()
        
        print("\n" + "="*70)
        print("INDUSTRY DAY GENERATOR AGENT INITIALIZED")
        print("="*70)
        print(f"  ✓ BaseAgent initialized")
        print(f"  ✓ Template loaded: {self.template_path.name}")
        print("="*70 + "\n")
    
    def execute(self, task: Dict) -> Dict:
        """
        Execute Industry Day materials generation
        
        Args:
            task: Dictionary containing:
                - project_info: Program details
                - requirements_content: PWS/SOW/SOO content (optional)
                - config: Optional configuration
        
        Returns:
            Dictionary with Industry Day content and metadata
        """
        self.log("Starting Industry Day materials generation")

        project_info = task.get('project_info', {})
        requirements_content = task.get('requirements_content', '')
        config = task.get('config', {})

        contract_type = config.get('contract_type', 'services')
        program_name = project_info.get('program_name', 'Unknown')

        # NEW: Cross-reference lookup - Find Sources Sought and Acquisition Plan
        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for Sources Sought (interested vendors list)
                latest_sources_sought = metadata_store.find_latest_document('sources_sought', program_name)
                # Look for Acquisition Plan (program overview)
                latest_acq_plan = metadata_store.find_latest_document('acquisition_plan', program_name)

                if latest_sources_sought:
                    print(f"✅ Found Sources Sought: {latest_sources_sought['id']}")
                    project_info['sources_sought_data'] = latest_sources_sought['extracted_data']
                    self._sources_sought_reference = latest_sources_sought['id']
                else:
                    print(f"⚠️  No Sources Sought found for {program_name}")
                    self._sources_sought_reference = None

                if latest_acq_plan:
                    print(f"✅ Found Acquisition Plan: {latest_acq_plan['id']}")
                    project_info['acquisition_plan_data'] = latest_acq_plan['extracted_data']
                    self._acq_plan_reference = latest_acq_plan['id']
                else:
                    print(f"⚠️  No Acquisition Plan found for {program_name}")
                    self._acq_plan_reference = None

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")
                self._sources_sought_reference = None
                self._acq_plan_reference = None
        else:
            self._sources_sought_reference = None
            self._acq_plan_reference = None

        print("\n" + "="*70)
        print("GENERATING INDUSTRY DAY MATERIALS")
        print("="*70)
        print(f"Program: {program_name}")
        print(f"Contract Type: {contract_type}")
        print("="*70 + "\n")
        
        # Step 1: Create event agenda
        print("STEP 1: Creating Industry Day agenda...")
        agenda = self._create_agenda(contract_type)
        print(f"  ✓ Agenda created ({len(agenda)} sessions)")
        
        # Step 2: Generate presentation slides content
        print("\nSTEP 2: Generating presentation slide content...")
        slides = self._generate_slides_content(project_info, requirements_content, contract_type)
        print(f"  ✓ Generated content for {len(slides)} slides")
        
        # Step 3: Create Q&A process
        print("\nSTEP 3: Creating Q&A process and forms...")
        qa_process = self._create_qa_process()
        print(f"  ✓ Q&A process defined")
        
        # Step 4: Generate FAQs
        print("\nSTEP 4: Generating frequently asked questions...")
        faqs = self._generate_faqs(contract_type)
        print(f"  ✓ Generated {len(faqs)} FAQs")
        
        # Step 5: Populate template
        print("\nSTEP 5: Populating Industry Day template...")
        content = self._populate_template(
            project_info,
            agenda,
            slides,
            qa_process,
            faqs,
            config
        )
        print(f"  ✓ Template populated ({len(content)} characters)")
        
        print("\n" + "="*70)
        print("✅ INDUSTRY DAY MATERIALS GENERATION COMPLETE")
        print("="*70)

        # NEW: Save document metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving document metadata for cross-referencing...")
                metadata_store = DocumentMetadataStore()

                # Extract structured data from generated content
                extracted_data = {
                    'agenda': agenda,
                    'agenda_sessions': len(agenda),
                    'slides': slides,
                    'slides_count': len(slides),
                    'faqs': faqs,
                    'faqs_count': len(faqs),
                    'contract_type': contract_type,
                    'event_date': config.get('industry_day_date', 'TBD')
                }

                # Build references dict
                references = {}
                if self._sources_sought_reference:
                    references['sources_sought'] = self._sources_sought_reference
                if self._acq_plan_reference:
                    references['acquisition_plan'] = self._acq_plan_reference

                # Save to metadata store
                doc_id = metadata_store.save_document(
                    doc_type='industry_day',
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
                'agenda_sessions': len(agenda),
                'slides_count': len(slides),
                'faqs_count': len(faqs),
                'contract_type': contract_type
            }
        }
    
    def _create_agenda(self, contract_type: str) -> List[Dict]:
        """Create Industry Day event agenda"""
        agenda = [
            {'time': '9:00 AM', 'duration': '15 min', 'activity': 'Registration and Check-In', 'presenter': 'Event Staff', 'location': 'Main Lobby'},
            {'time': '9:15 AM', 'duration': '15 min', 'activity': 'Welcome and Introduction', 'presenter': 'Program Manager', 'location': 'Conference Room A'},
            {'time': '9:30 AM', 'duration': '30 min', 'activity': 'Program Overview Briefing', 'presenter': 'Program Manager', 'location': 'Conference Room A'},
            {'time': '10:00 AM', 'duration': '45 min', 'activity': 'Technical Requirements Deep Dive', 'presenter': 'Technical Lead', 'location': 'Conference Room A'},
            {'time': '10:45 AM', 'duration': '15 min', 'activity': 'Break', 'presenter': '-', 'location': 'Main Lobby'},
            {'time': '11:00 AM', 'duration': '30 min', 'activity': 'Acquisition Strategy and Evaluation', 'presenter': 'Contracting Officer', 'location': 'Conference Room A'},
            {'time': '11:30 AM', 'duration': '30 min', 'activity': 'Small Business Opportunities', 'presenter': 'Small Business Specialist', 'location': 'Conference Room A'},
            {'time': '12:00 PM', 'duration': '60 min', 'activity': 'Lunch and Networking', 'presenter': '-', 'location': 'Main Lobby'},
            {'time': '1:00 PM', 'duration': '45 min', 'activity': 'Question and Answer Session', 'presenter': 'Panel', 'location': 'Conference Room A'},
            {'time': '1:45 PM', 'duration': '45 min', 'activity': 'One-on-One Meetings (Optional)', 'presenter': 'By Appointment', 'location': 'Conference Rooms B-D'},
            {'time': '2:30 PM', 'duration': '-', 'activity': 'Adjournment', 'presenter': '-', 'location': '-'}
        ]
        
        # Add R&D-specific session
        if contract_type == 'research_development':
            agenda.insert(4, {
                'time': '10:00 AM',
                'duration': '30 min',
                'activity': 'Technology Innovation and Maturation Strategy',
                'presenter': 'Chief Engineer',
                'location': 'Conference Room A'
            })
        
        return agenda
    
    def _generate_slides_content(self, project_info: Dict, requirements_content: str, contract_type: str) -> List[Dict]:
        """Generate content for presentation slides"""
        slides = [
            {
                'number': 1,
                'title': 'Title Slide',
                'content': f"{project_info.get('program_name', 'Program Name')} Industry Day"
            },
            {
                'number': 2,
                'title': 'Agenda Overview',
                'content': 'Program Background, Technical Requirements, Acquisition Strategy, Q&A'
            },
            {
                'number': 3,
                'title': 'Program Background',
                'content': 'Mission need and capability gap overview'
            },
            {
                'number': 4,
                'title': 'Program Objectives',
                'content': 'Key objectives and success criteria'
            },
            {
                'number': 5,
                'title': 'Scope of Work',
                'content': 'Overview of work to be performed'
            },
            {
                'number': 6,
                'title': 'Key Requirements Summary',
                'content': 'High-level technical and functional requirements'
            },
            {
                'number': 7,
                'title': 'Performance Requirements',
                'content': 'Key Performance Parameters (KPPs) and metrics'
            },
            {
                'number': 8,
                'title': 'Technical Requirements Overview',
                'content': 'System architecture, interfaces, security'
            },
            {
                'number': 9,
                'title': 'Acquisition Strategy',
                'content': f"Contract Type: {contract_type}, Source Selection Method"
            },
            {
                'number': 10,
                'title': 'Evaluation Approach',
                'content': 'Evaluation factors and weights'
            },
            {
                'number': 11,
                'title': 'Acquisition Schedule',
                'content': 'Key milestones and dates'
            },
            {
                'number': 12,
                'title': 'Small Business Opportunities',
                'content': 'Set-aside determination and subcontracting'
            },
            {
                'number': 13,
                'title': 'Next Steps',
                'content': 'Draft RFP, Final RFP, Proposal Timeline'
            },
            {
                'number': 14,
                'title': 'Questions and Contact Information',
                'content': 'POC information and Q&A process'
            }
        ]
        
        # Add R&D-specific slides
        if contract_type == 'research_development':
            slides.insert(8, {
                'number': 9,
                'title': 'Technology Maturation Strategy',
                'content': 'Technology Readiness Levels (TRL) and innovation approach'
            })
        
        return slides
    
    def _create_qa_process(self) -> Dict:
        """Create Q&A process description"""
        return {
            'format': 'Questions may be submitted verbally during the session or in writing via the question submission form',
            'submission': 'Written questions can be submitted until 7 days after Industry Day',
            'response_method': 'Responses will be posted publicly on SAM.gov within 14 days'
        }
    
    def _generate_faqs(self, contract_type: str) -> List[Dict]:
        """Generate frequently asked questions"""
        faqs = [
            {
                'question': 'When will the final RFP be released?',
                'answer': 'The final RFP is anticipated to be released approximately 30 days after Industry Day. The exact date will be announced via SAM.gov.'
            },
            {
                'question': 'What is the anticipated contract value?',
                'answer': 'The estimated contract value will be provided in the RFP. A rough order of magnitude is included in the pre-solicitation notice.'
            },
            {
                'question': 'Is this a small business set-aside?',
                'answer': 'The set-aside determination will be finalized based on market research results. Current indication will be provided during the briefing.'
            },
            {
                'question': 'Will there be a draft RFP?',
                'answer': 'Yes, a draft RFP is planned to be released approximately 2 weeks before the final RFP to allow industry feedback.'
            },
            {
                'question': 'Can we schedule one-on-one meetings?',
                'answer': 'One-on-one meetings may be available on a limited basis. Please indicate your interest on the registration form.'
            },
            {
                'question': 'What security clearance is required?',
                'answer': 'Security clearance requirements, if any, will be specified in the RFP. This Industry Day is unclassified.'
            },
            {
                'question': 'Are teaming arrangements encouraged?',
                'answer': 'Yes, teaming is encouraged to ensure all requirements can be met. A networking session is included in the agenda.'
            },
            {
                'question': 'How will proposals be evaluated?',
                'answer': 'Evaluation factors and their relative importance will be detailed in the RFP Section M. A high-level overview will be provided during the briefing.'
            }
        ]
        
        if contract_type == 'research_development':
            faqs.extend([
                {
                    'question': 'What Technology Readiness Level (TRL) is required?',
                    'answer': 'TRL requirements will be specified in the RFP. The Government is seeking solutions at TRL 6 or higher.'
                },
                {
                    'question': 'How will intellectual property rights be handled?',
                    'answer': 'Data rights and IP considerations will be addressed in the RFP. The Government seeks appropriate rights for its purposes while respecting contractor IP.'
                }
            ])
        
        return faqs
    
    def _populate_template(
        self,
        project_info: Dict,
        agenda: List[Dict],
        slides: List[Dict],
        qa_process: Dict,
        faqs: List[Dict],
        config: Dict
    ) -> str:
        """Populate Industry Day template"""
        content = self.template
        
        # Calculate Industry Day date (typically 7-10 days after RFP release)
        industry_day_date = datetime.now() + timedelta(days=28)
        
        # Basic information
        content = content.replace('{{program_name}}', project_info.get('program_name', 'TBD'))
        content = content.replace('{{industry_day_date}}', industry_day_date.strftime('%B %d, %Y'))
        content = content.replace('{{industry_day_time}}', '9:00 AM - 2:30 PM')
        content = content.replace('{{start_time}}', '9:00 AM')
        content = content.replace('{{end_time}}', '2:30 PM')
        content = content.replace('{{timezone}}', 'Eastern Time')
        content = content.replace('{{location}}', config.get('venue_name', 'Federal Building Conference Center'))
        content = content.replace('{{venue_name}}', config.get('venue_name', 'Federal Building Conference Center'))
        content = content.replace('{{venue_address}}', config.get('venue_address', 'Washington, DC 20001'))
        content = content.replace('{{classification}}', config.get('classification', 'UNCLASSIFIED'))
        
        # Registration information
        registration_deadline = industry_day_date - timedelta(days=7)
        content = content.replace('{{registration_deadline}}', registration_deadline.strftime('%B %d, %Y'))
        content = content.replace('{{registration_email}}', config.get('registration_email', project_info.get('ko_email', 'events@agency.mil')))
        content = content.replace('{{registration_link}}', config.get('registration_link', 'TBD'))
        content = content.replace('{{attendance_type}}', config.get('attendance_type', 'In-person and Virtual (WebEx)'))
        
        # Agenda table
        agenda_table = '\n'.join([
            f"| {item['time']} | {item['duration']} | {item['activity']} | {item['presenter']} | {item['location']} |"
            for item in agenda
        ])
        content = content.replace('{{agenda_table}}', agenda_table)
        
        # FAQs
        faq_section = ''
        for i, faq in enumerate(faqs, 1):
            faq_section += f"\n\n#### Q{i}: {faq['question']}\n**A:** {faq['answer']}"
            # Also fill individual FAQ placeholders
            content = content.replace(f'{{{{faq_{i}_question}}}}', faq['question'])
            content = content.replace(f'{{{{faq_{i}_answer}}}}', faq['answer'])
        content = content.replace('{{additional_faqs}}', faq_section)
        
        # Q&A process
        content = content.replace('{{qa_format}}', qa_process['format'])
        content = content.replace('{{question_submission}}', qa_process['submission'])
        content = content.replace('{{response_method}}', qa_process['response_method'])
        content = content.replace('{{questions_email}}', config.get('questions_email', project_info.get('ko_email', 'contracting@agency.mil')))
        questions_deadline = industry_day_date + timedelta(days=7)
        content = content.replace('{{questions_deadline}}', questions_deadline.strftime('%B %d, %Y'))
        
        # POC information
        content = content.replace('{{poc_name}}', config.get('poc_name', project_info.get('contracting_officer', 'John Doe')))
        content = content.replace('{{poc_email}}', config.get('poc_email', project_info.get('ko_email', 'contracting@agency.mil')))
        content = content.replace('{{poc_phone}}', config.get('poc_phone', project_info.get('ko_phone', '(703) 555-0000')))
        content = content.replace('{{event_contact_name}}', config.get('poc_name', project_info.get('contracting_officer', 'John Doe')))
        content = content.replace('{{event_contact_email}}', config.get('poc_email', project_info.get('ko_email', 'events@agency.mil')))
        content = content.replace('{{event_contact_phone}}', config.get('poc_phone', '(703) 555-0000'))
        
        # Program information for slides
        content = content.replace('{{agency}}', project_info.get('organization', 'Department of Defense'))
        content = content.replace('{{date}}', industry_day_date.strftime('%B %d, %Y'))
        content = content.replace('{{estimated_value}}', project_info.get('estimated_value', 'TBD'))
        content = content.replace('{{period_of_performance}}', project_info.get('period_of_performance', '12 months base + 4 option years'))
        
        # Contract type specific content
        contract_type = config.get('contract_type', 'services')
        if contract_type == 'research_development':
            rd_slides = """
### Slide 9: Technology Maturation Strategy
**Technology Readiness Levels:**
- Current TRL: 4-5 (component validation in lab environment)
- Target TRL: 7-8 (system prototype demonstration)

**Innovation Approach:**
- Encourage innovative solutions and alternative approaches
- Intellectual property considerations
- Technology transition strategy
"""
            content = content.replace('{{contract_type_technical_slides}}', rd_slides)
            content = content.replace('{{contract_type_technical_deep_dive}}', '### Technology Innovation\nDiscussion of technology maturation approach, TRL advancement, and innovation opportunities.')
        else:
            content = content.replace('{{contract_type_technical_slides}}', '')
            content = content.replace('{{contract_type_technical_deep_dive}}', '')
        
        # Max attendees
        content = content.replace('{{max_attendees_per_company}}', '4')
        
        # Fill remaining placeholders
        content = re.sub(r'\{\{[^}]+\}\}', 'TBD', content)
        
        return content
    
    def save_to_file(self, content: str, output_path: str, convert_to_pdf: bool = True) -> Dict:
        """Save Industry Day materials to file"""
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

