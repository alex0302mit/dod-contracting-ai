"""
RFI Generator Agent: Generates Request for Information documents
More detailed than Sources Sought - includes technical deep-dive questions
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


class RFIGeneratorAgent(BaseAgent):
    """
    RFI Generator Agent
    
    Generates comprehensive Request for Information (RFI) documents.
    
    Features:
    - More detailed than Sources Sought (technical deep-dive)
    - Extracts technical questions from requirements
    - Creates capability matrices for vendor responses
    - Includes cost range questions (rough order of magnitude)
    - Contract type aware: R&D focuses on innovation approach
    - Sets Q&A period and response format
    
    Dependencies:
    - BaseAgent: LLM interaction and common utilities
    - Retriever: Optional RAG system for technical requirements
    """
    
    def __init__(
        self,
        api_key: str,
        retriever: Optional[Retriever] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize RFI Generator Agent
        
        Args:
            api_key: Anthropic API key
            retriever: Optional RAG retriever
            model: Claude model to use
        """
        super().__init__(
            name="RFI Generator Agent",
            api_key=api_key,
            model=model,
            temperature=0.5
        )
        
        self.retriever = retriever
        self.template_path = Path(__file__).parent.parent / "templates" / "rfi_template.md"
        
        # Load template
        with open(self.template_path, 'r') as f:
            self.template = f.read()
        
        print("\n" + "="*70)
        print("RFI GENERATOR AGENT INITIALIZED")
        print("="*70)
        print(f"  ✓ BaseAgent initialized")
        print(f"  ✓ Template loaded: {self.template_path.name}")
        print("="*70 + "\n")
    
    def execute(self, task: Dict) -> Dict:
        """
        Execute RFI generation
        
        Args:
            task: Dictionary containing:
                - project_info: Program details
                - requirements_content: PWS/SOO/SOW content
                - config: Optional configuration
                - reasoning_tracker: Optional ReasoningTracker for token tracking
        
        Returns:
            Dictionary with RFI content and metadata
        """
        self.log("Starting RFI generation")
        
        # Extract reasoning tracker for token usage tracking
        self._current_tracker = self.get_tracker_from_task(task)

        project_info = task.get('project_info', {})
        requirements_content = task.get('requirements_content', '')
        config = task.get('config', {})

        contract_type = config.get('contract_type', 'services')
        program_name = project_info.get('program_name', 'Unknown')

        # NEW: Cross-reference lookup - Find Sources Sought and Market Research
        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for Sources Sought (vendor responses would inform RFI questions)
                latest_sources_sought = metadata_store.find_latest_document('sources_sought', program_name)
                # Look for market research
                latest_market_research = metadata_store.find_latest_document('market_research', program_name)

                if latest_sources_sought:
                    print(f"✅ Found Sources Sought: {latest_sources_sought['id']}")
                    project_info['sources_sought_data'] = latest_sources_sought['extracted_data']
                    self._sources_sought_reference = latest_sources_sought['id']
                else:
                    print(f"⚠️  No Sources Sought found for {program_name}")
                    self._sources_sought_reference = None

                if latest_market_research:
                    print(f"✅ Found Market Research: {latest_market_research['id']}")
                    project_info['market_research_insights'] = latest_market_research['extracted_data']
                    self._market_research_reference = latest_market_research['id']
                else:
                    print(f"⚠️  No Market Research found for {program_name}")
                    self._market_research_reference = None

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")
                self._sources_sought_reference = None
                self._market_research_reference = None
        else:
            self._sources_sought_reference = None
            self._market_research_reference = None

        print("\n" + "="*70)
        print("GENERATING REQUEST FOR INFORMATION (RFI)")
        print("="*70)
        print(f"Program: {program_name}")
        print(f"Contract Type: {contract_type}")
        print("="*70 + "\n")
        
        # Step 1: Extract technical requirements
        print("STEP 1: Extracting technical requirements...")
        technical_reqs = self._extract_technical_requirements(requirements_content, contract_type)
        print(f"  ✓ Identified {len(technical_reqs)} technical requirement areas")
        
        # Step 2: Generate technical questions
        print("\nSTEP 2: Generating technical questions...")
        technical_questions = self._generate_technical_questions(technical_reqs, contract_type)
        print(f"  ✓ Generated {sum(len(q) for q in technical_questions.values())} questions across {len(technical_questions)} categories")
        
        # Step 3: Create capability matrices
        print("\nSTEP 3: Creating capability matrices...")
        matrices = self._create_capability_matrices(technical_reqs, contract_type)
        print(f"  ✓ Created {len(matrices)} capability matrices")
        
        # Step 4: Calculate deadlines
        print("\nSTEP 4: Calculating response deadlines...")
        deadlines = self._calculate_deadlines(config)
        print(f"  ✓ Response deadline: {deadlines['response_deadline']}")
        
        # Step 5: Populate template
        print("\nSTEP 5: Populating RFI template...")
        content = self._populate_template(
            project_info,
            technical_reqs,
            technical_questions,
            matrices,
            deadlines,
            config
        )
        print(f"  ✓ Template populated ({len(content)} characters)")
        
        print("\n" + "="*70)
        print("✅ RFI GENERATION COMPLETE")
        print("="*70)

        # NEW: Save document metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving document metadata for cross-referencing...")
                metadata_store = DocumentMetadataStore()

                # Extract structured data from generated content
                extracted_data = {
                    'technical_areas': technical_reqs,
                    'questions_count': sum(len(q) for q in technical_questions.values()),
                    'technical_questions': technical_questions,
                    'capability_matrices': matrices,
                    'response_deadline': deadlines['response_deadline'],
                    'contract_type': contract_type,
                    'publication_date': deadlines.get('publication_date', datetime.now().strftime('%Y-%m-%d'))
                }

                # Build references dict
                references = {}
                if self._sources_sought_reference:
                    references['sources_sought'] = self._sources_sought_reference
                if self._market_research_reference:
                    references['market_research'] = self._market_research_reference

                # Save to metadata store
                doc_id = metadata_store.save_document(
                    doc_type='rfi',
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
                'technical_areas': len(technical_reqs),
                'questions_count': sum(len(q) for q in technical_questions.values()),
                'matrices_count': len(matrices),
                'response_deadline': deadlines['response_deadline'],
                'contract_type': contract_type
            }
        }
    
    def _extract_technical_requirements(self, requirements_content: str, contract_type: str) -> List[str]:
        """Extract technical requirement areas"""
        default_areas = [
            "System Architecture and Design",
            "Development and Implementation",
            "Integration and Interoperability",
            "Cybersecurity and Compliance",
            "Testing and Quality Assurance",
            "Performance and Scalability",
            "Data Management",
            "User Experience and Interface Design"
        ]
        
        if contract_type == 'research_development':
            default_areas.extend([
                "Technology Maturation and Innovation",
                "Research Methodology",
                "Intellectual Property Management"
            ])
        
        return default_areas
    
    def _generate_technical_questions(self, technical_reqs: List[str], contract_type: str) -> Dict[str, List[str]]:
        """Generate detailed technical questions for each requirement area"""
        questions = {}
        
        # Architecture questions
        questions['Architecture and Design'] = [
            "Describe your proposed system architecture at a high level.",
            "What design patterns and architectural principles will you employ?",
            "How will you ensure scalability and maintainability?",
            "What technology stack do you recommend and why?"
        ]
        
        # Development questions
        questions['Development Methodology'] = [
            "What software development methodology do you propose (Agile, DevOps, etc.)?",
            "How will you manage version control and code quality?",
            "Describe your continuous integration/continuous deployment (CI/CD) approach.",
            "What development tools and environments do you use?"
        ]
        
        # Integration questions
        questions['Integration Approach'] = [
            "How will you approach integration with existing systems?",
            "What integration technologies and protocols do you recommend?",
            "Describe your approach to API development and management.",
            "How will you handle data migration from legacy systems?"
        ]
        
        # Cybersecurity questions
        questions['Cybersecurity'] = [
            "How will you implement security controls to meet NIST 800-171 requirements?",
            "Describe your approach to vulnerability management and patching.",
            "What encryption methods will you use for data at rest and in transit?",
            "How will you implement identity and access management (IAM)?",
            "Describe your incident response and monitoring capabilities."
        ]
        
        # Testing questions
        questions['Testing and Quality Assurance'] = [
            "Describe your testing strategy (unit, integration, system, acceptance).",
            "What testing tools and frameworks do you use?",
            "How will you perform security testing and penetration testing?",
            "Describe your quality assurance processes and metrics."
        ]
        
        # Performance questions
        questions['Performance and Scalability'] = [
            "How will you ensure the system meets performance requirements?",
            "Describe your approach to load testing and performance optimization.",
            "What scalability mechanisms will you implement?",
            "How will you monitor system performance in production?"
        ]
        
        # Management questions
        questions['Project Management'] = [
            "Describe your project management approach and methodology.",
            "How will you track progress and manage schedule/cost/performance?",
            "What collaboration tools will you use with the Government team?",
            "How will you manage risks and issues?"
        ]
        
        # Contract-type-specific questions
        if contract_type == 'research_development':
            questions['Technology Maturation'] = [
                "What is the current Technology Readiness Level (TRL) of your proposed solution?",
                "Describe your approach to advancing the technology to higher TRL levels.",
                "What are the key technical risks and how will you mitigate them?",
                "Describe your innovation approach and relevant intellectual property."
            ]
        
        return questions
    
    def _create_capability_matrices(self, technical_reqs: List[str], contract_type: str) -> Dict:
        """Create capability assessment matrices"""
        # Technical Capability Matrix
        technical_matrix = []
        for req in technical_reqs[:8]:  # Limit to first 8
            technical_matrix.append(f"| {req} | ☐ | ☐ | ☐ | ☐ | |")
        
        technical_matrix_text = '\n'.join(technical_matrix)
        
        # Compliance Matrix
        compliance_items = [
            "NIST 800-171 Compliance",
            "Section 508 Accessibility",
            "FedRAMP Authorization",
            "CMMC Level 2 Certification",
            "Cloud-based deployment capability",
            "24/7 operations and maintenance",
            "Continuous monitoring capability",
            "Data backup and recovery"
        ]
        
        compliance_matrix = []
        for item in compliance_items:
            compliance_matrix.append(f"| {item} | ☐ | ☐ | ☐ | |")
        
        compliance_matrix_text = '\n'.join(compliance_matrix)
        
        return {
            'technical_capability_matrix': technical_matrix_text,
            'compliance_matrix': compliance_matrix_text
        }
    
    def _calculate_deadlines(self, config: Dict) -> Dict:
        """Calculate RFI response and questions deadlines"""
        issue_date = datetime.now()
        
        # RFI typically allows 30-45 days for response
        response_days = config.get('response_days', 35)
        response_deadline = issue_date + timedelta(days=response_days)
        
        # Questions deadline: typically 15-20 days after issue
        questions_days = config.get('questions_days', 15)
        questions_deadline = issue_date + timedelta(days=questions_days)
        
        # Government responses to questions: 5-7 days after questions deadline
        questions_response_date = questions_deadline + timedelta(days=5)
        
        return {
            'issue_date': issue_date.strftime('%B %d, %Y'),
            'response_deadline': response_deadline.strftime('%B %d, %Y at 2:00 PM EST'),
            'response_deadline_detailed': response_deadline.strftime('%B %d, %Y at 2:00 PM Eastern Time'),
            'questions_deadline': questions_deadline.strftime('%B %d, %Y at 2:00 PM EST'),
            'questions_response_date': questions_response_date.strftime('%B %d, %Y')
        }
    
    def _populate_template(
        self,
        project_info: Dict,
        technical_reqs: List[str],
        technical_questions: Dict[str, List[str]],
        matrices: Dict,
        deadlines: Dict,
        config: Dict
    ) -> str:
        """Populate RFI template"""
        content = self.template
        
        # Basic information
        content = content.replace('{{rfi_number}}', f"RFI-{datetime.now().strftime('%Y%m%d')}-{project_info.get('program_name', 'PRG')[:3].upper()}")
        content = content.replace('{{program_name}}', project_info.get('program_name', 'TBD'))
        content = content.replace('{{issue_date}}', deadlines['issue_date'])
        content = content.replace('{{response_deadline}}', deadlines['response_deadline'])
        content = content.replace('{{response_deadline_detailed}}', deadlines['response_deadline_detailed'])
        content = content.replace('{{questions_deadline}}', deadlines['questions_deadline'])
        content = content.replace('{{questions_response_date}}', deadlines['questions_response_date'])
        content = content.replace('{{classification}}', config.get('classification', 'UNCLASSIFIED'))
        
        # Agency and POC information
        content = content.replace('{{agency}}', project_info.get('organization', 'Department of Defense'))
        content = content.replace('{{office}}', config.get('office', 'Contracting Office'))
        content = content.replace('{{poc_name}}', config.get('poc_name', project_info.get('contracting_officer', 'John Doe')))
        content = content.replace('{{poc_title}}', config.get('poc_title', 'Contracting Officer'))
        content = content.replace('{{poc_email}}', config.get('poc_email', project_info.get('ko_email', 'contracting@agency.mil')))
        content = content.replace('{{poc_phone}}', config.get('poc_phone', project_info.get('ko_phone', '(703) 555-0000')))
        content = content.replace('{{questions_email}}', config.get('poc_email', project_info.get('ko_email', 'contracting@agency.mil')))
        
        # Program information
        content = content.replace('{{program_description}}', project_info.get('description', 'Cloud-based system development'))
        content = content.replace('{{estimated_funding}}', project_info.get('estimated_value', '$5M - $10M'))
        content = content.replace('{{period_of_performance}}', project_info.get('period_of_performance', '12 months base + 4 option years'))
        
        # Technical questions - populate each section
        for category, questions in technical_questions.items():
            questions_text = '\n\n'.join([f"**Question:** {q}" for q in questions])
            # Use a placeholder that matches the category
            placeholder_key = category.lower().replace(' ', '_').replace('and', '')
            content = content.replace(f'{{{{{placeholder_key}_questions}}}}', questions_text)
        
        # Matrices
        content = content.replace('{{technical_capability_matrix}}', matrices['technical_capability_matrix'])
        content = content.replace('{{compliance_matrix}}', matrices['compliance_matrix'])
        
        # Page limits
        content = content.replace('{{technical_page_limit}}', str(config.get('technical_page_limit', 25)))
        content = content.replace('{{past_performance_page_limit}}', str(config.get('past_performance_page_limit', 15)))
        content = content.replace('{{cost_page_limit}}', str(config.get('cost_page_limit', 10)))
        
        # Submission method
        submission_method = config.get('submission_method', f"Email to {config.get('poc_email', 'contracting@agency.mil')}")
        content = content.replace('{{submission_method}}', submission_method)
        
        # Contract type specific questions
        contract_type = config.get('contract_type', 'services')
        if contract_type == 'research_development':
            rd_questions = """
### 5.9 Research and Development Approach

**Question:** What is your proposed research methodology and approach to technology development?

**Question:** Describe your experience with similar R&D efforts and relevant technical breakthroughs.

**Question:** What is the current Technology Readiness Level (TRL) of your proposed solution?

**Question:** How will you approach intellectual property development and data rights?
"""
            content = content.replace('{{contract_type_specific_technical_questions}}', rd_questions)
        else:
            content = content.replace('{{contract_type_specific_technical_questions}}', '')
        
        # Fill remaining placeholders
        content = re.sub(r'\{\{[^}]+\}\}', 'TBD', content)
        
        return content
    
    def save_to_file(self, content: str, output_path: str, convert_to_pdf: bool = True) -> Dict:
        """Save RFI to file"""
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

