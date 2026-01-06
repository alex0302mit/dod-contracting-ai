"""
Sources Sought Generator Agent: Generates Sources Sought Notices for market research
Creates FAR 5.205 compliant market research notices
"""

from typing import Dict, List, Optional
from pathlib import Path
import sys
from datetime import datetime, timedelta
import re

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.base_agent import BaseAgent
from backend.rag.retriever import Retriever
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class SourcesSoughtGeneratorAgent(BaseAgent):
    """
    Sources Sought Generator Agent
    
    Generates Sources Sought Notices per FAR 5.205 for market research.
    
    Features:
    - Extracts capability requirements from PWS/requirements docs
    - Generates vendor questionnaire
    - Sets appropriate response deadlines (15-30 days)
    - Includes small business considerations
    - Contract type aware: R&D includes technical maturity questions
    - Creates SAM.gov-compatible format
    
    Dependencies:
    - BaseAgent: LLM interaction and common utilities
    - Retriever: Optional RAG system for similar notices
    """
    
    def __init__(
        self,
        api_key: str,
        retriever: Optional[Retriever] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize Sources Sought Generator Agent
        
        Args:
            api_key: Anthropic API key
            retriever: Optional RAG retriever
            model: Claude model to use
        """
        super().__init__(
            name="Sources Sought Generator Agent",
            api_key=api_key,
            model=model,
            temperature=0.5
        )
        
        self.retriever = retriever
        self.template_path = Path(__file__).parent.parent / "templates" / "sources_sought_template.md"
        
        # Load template
        with open(self.template_path, 'r') as f:
            self.template = f.read()
        
        print("\n" + "="*70)
        print("SOURCES SOUGHT GENERATOR AGENT INITIALIZED")
        print("="*70)
        print(f"  ✓ BaseAgent initialized")
        print(f"  ✓ Template loaded: {self.template_path.name}")
        print("="*70 + "\n")
    
    def execute(self, task: Dict) -> Dict:
        """
        Execute Sources Sought notice generation
        
        Args:
            task: Dictionary containing:
                - project_info: Program details
                - requirements_content: PWS/SOO/SOW content (optional)
                - config: Optional configuration
        
        Returns:
            Dictionary with Sources Sought content and metadata
        """
        self.log("Starting Sources Sought generation")

        project_info = task.get('project_info', {})
        requirements_content = task.get('requirements_content', '')
        config = task.get('config', {})

        contract_type = config.get('contract_type', 'services')
        program_name = project_info.get('program_name', 'Unknown')

        # NEW: Cross-reference lookup - Find related documents
        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for market research report (if available)
                latest_market_research = metadata_store.find_latest_document('market_research', program_name)

                if latest_market_research:
                    print(f"✅ Found Market Research Report: {latest_market_research['id']}")
                    # Inject market research insights into project_info
                    project_info['market_research_insights'] = latest_market_research['extracted_data']
                    self._market_research_reference = latest_market_research['id']
                else:
                    print(f"⚠️  No market research report found for {program_name}")
                    self._market_research_reference = None

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")
                self._market_research_reference = None
        else:
            self._market_research_reference = None

        print("\n" + "="*70)
        print("GENERATING SOURCES SOUGHT NOTICE")
        print("="*70)
        print(f"Program: {program_name}")
        print(f"Contract Type: {contract_type}")
        print("="*70 + "\n")
        
        # Step 1: Extract capability requirements
        print("STEP 1: Extracting capability requirements...")
        capabilities = self._extract_capabilities(requirements_content, contract_type)
        print(f"  ✓ Identified {len(capabilities)} capability requirements")
        
        # Step 2: Generate questionnaire
        print("\nSTEP 2: Generating vendor questionnaire...")
        questionnaire = self._generate_questionnaire(capabilities, contract_type)
        print(f"  ✓ Generated {len(questionnaire)} questions")
        
        # Step 3: Determine response deadline
        print("\nSTEP 3: Calculating response deadline...")
        deadlines = self._calculate_deadlines(config)
        print(f"  ✓ Response deadline: {deadlines['response_deadline']}")
        
        # Step 4: Small business analysis
        print("\nSTEP 4: Analyzing small business opportunities...")
        small_business_info = self._analyze_small_business(project_info, contract_type)
        print(f"  ✓ Set-aside determination: {small_business_info['set_aside_type']}")
        
        # Step 5: Populate template
        print("\nSTEP 5: Populating Sources Sought template...")
        content = self._populate_template(
            project_info,
            capabilities,
            questionnaire,
            deadlines,
            small_business_info,
            config
        )
        print(f"  ✓ Template populated ({len(content)} characters)")
        
        print("\n" + "="*70)
        print("✅ SOURCES SOUGHT GENERATION COMPLETE")
        print("="*70)

        # NEW: Save document metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving document metadata for cross-referencing...")
                metadata_store = DocumentMetadataStore()
                extractor = DocumentDataExtractor()

                # Extract structured data from generated content
                extracted_data = {
                    'capabilities': capabilities,
                    'questions_count': len(questionnaire),
                    'questionnaire': questionnaire,
                    'response_deadline': deadlines['response_deadline'],
                    'set_aside_type': small_business_info['set_aside_type'],
                    'contract_type': contract_type,
                    'publication_date': deadlines.get('publication_date', datetime.now().strftime('%Y-%m-%d'))
                }

                # Build references dict
                references = {}
                if self._market_research_reference:
                    references['market_research'] = self._market_research_reference

                # Save to metadata store
                doc_id = metadata_store.save_document(
                    doc_type='sources_sought',
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
                'capabilities_count': len(capabilities),
                'questions_count': len(questionnaire),
                'response_deadline': deadlines['response_deadline'],
                'set_aside_type': small_business_info['set_aside_type'],
                'contract_type': contract_type
            }
        }
    
    def _extract_capabilities(self, requirements_content: str, contract_type: str) -> List[str]:
        """
        Extract capability requirements from requirements document
        
        Args:
            requirements_content: Requirements text
            contract_type: Contract type
        
        Returns:
            List of capability requirements
        """
        if not requirements_content:
            # Default capabilities
            return [
                "Cloud-based system development and deployment",
                "Enterprise system integration",
                "Cybersecurity implementation and compliance",
                "User interface/user experience design",
                "Data migration and management",
                "Technical documentation and training"
            ]
        
        # Use LLM to extract capabilities
        prompt = f"""Analyze the following requirements and extract 5-8 key capability requirements for a Sources Sought notice.

Contract Type: {contract_type}

Requirements:
{requirements_content[:6000]}

List the key capabilities vendors should have to perform this work. Be specific and measurable."""
        
        response = self.call_llm(prompt, max_tokens=1000)
        
        # Parse capabilities from response
        capabilities = []
        lines = response.split('\n')
        for line in lines:
            # Remove numbering, bullets, etc.
            cleaned = re.sub(r'^[\d\.\-\*\s]+', '', line).strip()
            if cleaned and len(cleaned) > 20:
                capabilities.append(cleaned)
        
        return capabilities[:8]  # Limit to 8 capabilities
    
    def _generate_questionnaire(self, capabilities: List[str], contract_type: str) -> List[Dict]:
        """
        Generate vendor questionnaire based on capabilities
        
        Args:
            capabilities: List of capability requirements
            contract_type: Contract type
        
        Returns:
            List of questions with expected response formats
        """
        questions = [
            {
                'number': '1',
                'question': 'Company name, address, DUNS/UEI number, and SAM.gov registration status?',
                'format': 'Provide complete contact information'
            },
            {
                'number': '2',
                'question': 'Business size classification (large or small business) and any applicable socioeconomic designations (SDB, WOSB, SDVOSB, HUBZone)?',
                'format': 'Check all that apply'
            },
            {
                'number': '3',
                'question': 'Do you have experience with similar projects? If yes, provide 2-3 brief examples including customer, contract value, and period of performance.',
                'format': '1-2 pages maximum'
            },
            {
                'number': '4',
                'question': 'What are your company\'s core technical capabilities relevant to this requirement?',
                'format': 'Bullet list of capabilities'
            },
            {
                'number': '5',
                'question': 'Do you have existing contracts or contract vehicles that could be leveraged for this requirement (GSA Schedule, OASIS, etc.)?',
                'format': 'Yes/No with details if yes'
            },
            {
                'number': '6',
                'question': 'Would you pursue this requirement as a prime contractor or subcontractor?',
                'format': 'Prime / Subcontractor / Either'
            },
            {
                'number': '7',
                'question': 'Are you interested in teaming arrangements? If yes, what capabilities are you seeking in a team?',
                'format': 'Yes/No with details'
            },
            {
                'number': '8',
                'question': 'What is your rough order of magnitude (ROM) cost estimate for this requirement?',
                'format': 'Cost range (optional)'
            }
        ]
        
        # Add contract-type-specific questions
        if contract_type == 'research_development':
            questions.extend([
                {
                    'number': '9',
                    'question': 'What is the Technology Readiness Level (TRL) of your proposed solution?',
                    'format': 'TRL 1-9 with brief explanation'
                },
                {
                    'number': '10',
                    'question': 'Do you have relevant intellectual property or patents that would support this effort?',
                    'format': 'Yes/No with details'
                }
            ])
        
        return questions
    
    def _calculate_deadlines(self, config: Dict) -> Dict:
        """
        Calculate response and questions deadlines
        
        Args:
            config: Configuration dictionary
        
        Returns:
            Dictionary with formatted deadlines
        """
        posted_date = datetime.now()
        
        # Response deadline: typically 15-30 days for Sources Sought
        response_days = config.get('response_days', 21)
        response_deadline = posted_date + timedelta(days=response_days)
        
        # Questions deadline: typically 7-10 days before response
        questions_deadline = response_deadline - timedelta(days=7)
        
        return {
            'posted_date': posted_date.strftime('%B %d, %Y'),
            'response_deadline': response_deadline.strftime('%B %d, %Y at 2:00 PM EST'),
            'response_deadline_detailed': response_deadline.strftime('%B %d, %Y at 2:00 PM Eastern Time'),
            'questions_deadline': questions_deadline.strftime('%B %d, %Y at 2:00 PM EST')
        }
    
    def _analyze_small_business(self, project_info: Dict, contract_type: str) -> Dict:
        """
        Analyze small business set-aside opportunities
        
        Args:
            project_info: Project information
            contract_type: Contract type
        
        Returns:
            Dictionary with small business determination
        """
        # Extract estimated value
        estimated_value_str = project_info.get('estimated_value', '$5M')
        
        # Simple parsing of dollar amounts
        value_millions = 5.0  # Default
        if 'M' in estimated_value_str:
            try:
                value_millions = float(re.findall(r'[\d\.]+', estimated_value_str)[0])
            except:
                pass
        
        # Determine set-aside
        if value_millions < 10:
            set_aside_type = "Small Business Set-Aside (anticipated)"
            set_aside_rationale = "Market research indicates adequate small business competition"
        else:
            set_aside_type = "To Be Determined"
            set_aside_rationale = "Set-aside determination pending market research results"
        
        # NAICS code determination
        if contract_type == 'research_development':
            naics_code = "541715"
            naics_description = "Research and Development in the Physical, Engineering, and Life Sciences"
            size_standard = "$47.5M"
        else:
            naics_code = "541512"
            naics_description = "Computer Systems Design Services"
            size_standard = "$34M"
        
        return {
            'set_aside_type': set_aside_type,
            'set_aside_rationale': set_aside_rationale,
            'naics_code': naics_code,
            'naics_description': naics_description,
            'size_standard': size_standard
        }
    
    def _populate_template(
        self,
        project_info: Dict,
        capabilities: List[str],
        questionnaire: List[Dict],
        deadlines: Dict,
        small_business_info: Dict,
        config: Dict
    ) -> str:
        """Populate Sources Sought template"""
        content = self.template
        
        # Basic information
        content = content.replace('{{notice_id}}', f"SS-{datetime.now().strftime('%Y%m%d')}-{project_info.get('program_name', 'PRG')[:3].upper()}")
        content = content.replace('{{posted_date}}', deadlines['posted_date'])
        content = content.replace('{{response_deadline}}', deadlines['response_deadline'])
        content = content.replace('{{response_deadline_detailed}}', deadlines['response_deadline_detailed'])
        content = content.replace('{{questions_deadline}}', deadlines['questions_deadline'])
        content = content.replace('{{classification}}', config.get('classification', 'UNCLASSIFIED'))
        
        # Agency information
        content = content.replace('{{agency}}', project_info.get('organization', 'Department of Defense'))
        content = content.replace('{{office}}', config.get('office', 'Contracting Office'))
        content = content.replace('{{location}}', config.get('location', 'Washington, DC'))
        
        # POC information
        content = content.replace('{{poc_name}}', config.get('poc_name', project_info.get('contracting_officer', 'John Doe')))
        content = content.replace('{{poc_title}}', config.get('poc_title', 'Contracting Officer'))
        content = content.replace('{{poc_email}}', config.get('poc_email', project_info.get('ko_email', 'contracting@agency.mil')))
        content = content.replace('{{poc_phone}}', config.get('poc_phone', project_info.get('ko_phone', '(703) 555-0000')))
        
        # Program information
        content = content.replace('{{program_name}}', project_info.get('program_name', 'TBD'))
        content = content.replace('{{program_description}}', project_info.get('description', 'Cloud-based system development and implementation'))
        content = content.replace('{{estimated_value}}', project_info.get('estimated_value', '$5M - $10M'))
        content = content.replace('{{period_of_performance}}', project_info.get('period_of_performance', '12 months base + 4 option years'))
        
        # Capabilities
        capabilities_text = '\n'.join([f"- {cap}" for cap in capabilities])
        content = content.replace('{{key_requirements_summary}}', capabilities_text)
        content = content.replace('{{technical_capabilities}}', capabilities_text)
        
        # Questionnaire
        questionnaire_text = '\n\n'.join([
            f"**Question {q['number']}:** {q['question']}\n\n*Response Format:* {q['format']}"
            for q in questionnaire
        ])
        content = content.replace('{{questionnaire}}', questionnaire_text)
        
        # Small business information
        content = content.replace('{{small_business_set_aside}}', small_business_info['set_aside_type'])
        content = content.replace('{{naics_code}}', small_business_info['naics_code'])
        content = content.replace('{{size_standard}}', small_business_info['size_standard'])
        
        # Contract type specific content
        contract_type = config.get('contract_type', 'services')
        if contract_type == 'research_development':
            contract_questions = """
**Additional Questions for R&D Contracts:**

**Question 9:** What is the Technology Readiness Level (TRL) of your proposed solution?

**Question 10:** Do you have relevant intellectual property or patents that would support this effort?

**Question 11:** Describe your approach to innovation and technology maturation.
"""
            content = content.replace('{{contract_type_questions}}', contract_questions)
        else:
            content = content.replace('{{contract_type_questions}}', '')
        
        # Fill remaining placeholders
        content = re.sub(r'\{\{[^}]+\}\}', 'TBD', content)
        
        return content
    
    def save_to_file(self, content: str, output_path: str, convert_to_pdf: bool = True) -> Dict:
        """Save Sources Sought notice to file"""
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

