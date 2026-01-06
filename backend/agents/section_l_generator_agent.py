"""
Section L Generator Agent: Generates Instructions to Offerors (Section L)

Purpose:
- Extracts project metadata from PWS/SOO/SOW documents
- Populates Section L template with project-specific instructions
- Generates proposal submission requirements, format guidelines, and evaluation instructions
- Creates formatted Section L document (markdown and PDF)

FAR Compliance:
- FAR Part 15 - Contracting by Negotiation
- FAR 52.215-1 - Instructions to Offerors - Competitive Acquisition
"""

from typing import Dict, Optional, List
from pathlib import Path
import re
from datetime import datetime, timedelta
from anthropic import Anthropic
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class SectionLGeneratorAgent:
    """
    Section L Generator Agent

    Generates Instructions to Offerors (Section L) for RFP documents

    Workflow:
    1. Extract project information from source documents
    2. Calculate proposal timelines and deadlines
    3. Determine page limits based on complexity
    4. Populate Section L template
    5. Generate formatted document
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize Section L Generator Agent

        Args:
            api_key: Anthropic API key (optional, uses env if not provided)
            model: Claude model to use
        """
        self.api_key = api_key
        self.model = model
        self.client = Anthropic(api_key=api_key) if api_key else None

        # Load Section L template
        self.template_path = Path(__file__).parent.parent / "templates" / "section_l_template.md"
        self.template = self._load_template()

        print("✓ Section L Generator Agent initialized")

    def _load_template(self) -> str:
        """Load Section L template"""
        if not self.template_path.exists():
            raise FileNotFoundError(f"Section L template not found: {self.template_path}")

        with open(self.template_path, 'r') as f:
            return f.read()

    def has_collaboration_enabled(self) -> bool:
        """
        Phase 4: Check if collaboration is enabled

        Returns:
            True (this agent supports collaboration)
        """
        return True

    async def generate_with_collaboration(
        self,
        requirements: str,
        context: str,
        dependencies: Dict[str, str]
    ) -> Dict:
        """
        Phase 4: Generate Section L with dependency context

        Args:
            requirements: Requirements/assumptions text
            context: RAG context
            dependencies: Dict of dependency_name -> content

        Returns:
            Generation result with content and citations
        """
        print("\n" + "="*70)
        print("PHASE 4: GENERATING SECTION L WITH COLLABORATION")
        print("="*70)

        # Parse requirements into project_info
        project_info = self._parse_requirements(requirements)

        # Incorporate PWS content from dependencies if available
        pws_content = ""
        if "Section C - Performance Work Statement" in dependencies:
            pws_content = dependencies["Section C - Performance Work Statement"]
            print(f"✓ Using PWS dependency ({len(pws_content)} chars)")

        # Incorporate Acquisition Plan from dependencies if available
        if "Acquisition Plan" in dependencies:
            acq_plan = dependencies["Acquisition Plan"]
            print(f"✓ Using Acquisition Plan dependency ({len(acq_plan)} chars)")
            # Extract evaluation approach from Acquisition Plan
            if "best value" in acq_plan.lower():
                project_info['evaluation_approach'] = "Best Value Trade-Off (see Section M)"
            elif "lpta" in acq_plan.lower() or "lowest price" in acq_plan.lower():
                project_info['evaluation_approach'] = "Lowest Price Technically Acceptable (LPTA)"

        # Execute generation with dependency-enriched info
        task = {
            'project_info': project_info,
            'pws_content': pws_content,
            'config': {},
            'dependencies': dependencies  # Pass through for reference
        }

        result = self.execute(task)

        # Add dependency references to content
        if dependencies:
            content = result['content']
            references_section = "\n\n---\n\n## Cross-References\n\n"
            references_section += "This document references the following previously generated documents:\n\n"
            for dep_name in dependencies.keys():
                references_section += f"- {dep_name}\n"
            result['content'] = content + references_section

        print("✓ Section L generated with collaboration")
        print("="*70)

        return {
            "content": result['content'],
            "citations": [],
            "metadata": result.get('metadata', {})
        }

    def _parse_requirements(self, requirements: str) -> Dict:
        """Parse requirements text into project_info dictionary"""
        project_info = {}

        # Extract key information from requirements text
        lines = requirements.split('\n')
        for line in lines:
            line = line.strip('- ').strip()
            if not line:
                continue

            # Look for key patterns
            if 'program' in line.lower() or 'project' in line.lower():
                # Extract program name
                parts = line.split(':')
                if len(parts) > 1:
                    project_info['program_name'] = parts[1].strip()
            elif 'organization' in line.lower():
                parts = line.split(':')
                if len(parts) > 1:
                    project_info['organization'] = parts[1].strip()
            elif 'value' in line.lower() or 'budget' in line.lower():
                parts = line.split(':')
                if len(parts) > 1:
                    project_info['estimated_value'] = parts[1].strip()

        # Set defaults if not found
        project_info.setdefault('program_name', 'Acquisition Program')
        project_info.setdefault('organization', 'Department of Defense')
        project_info.setdefault('estimated_value', 'TBD')

        return project_info

    def execute(self, task: Dict) -> Dict:
        """
        Execute Section L generation

        Args:
            task: Dictionary containing:
                - project_info: Project metadata
                - pws_content: PWS content (optional, for complexity analysis)
                - config: Configuration overrides (optional)

        Returns:
            Dictionary with generation results
        """
        print("\n" + "="*70)
        print("GENERATING SECTION L: INSTRUCTIONS TO OFFERORS")
        print("="*70)

        project_info = task.get('project_info', {})
        pws_content = task.get('pws_content', '')
        config = task.get('config', {})
        program_name = project_info.get('program_name', 'Unknown')

        # NEW: Cross-reference lookup - Find PWS for proposal requirements
        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for PWS (to extract deliverables and requirements for proposal instructions)
                latest_pws = metadata_store.find_latest_document('pws', program_name)

                if latest_pws:
                    print(f"✅ Found PWS: {latest_pws['id']}")
                    project_info['pws_data'] = latest_pws['extracted_data']
                    self._pws_reference = latest_pws['id']
                else:
                    print(f"⚠️  No PWS found for {program_name}")
                    self._pws_reference = None

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")
                self._pws_reference = None
        else:
            self._pws_reference = None

        # Step 1: Extract and enrich project information
        enriched_info = self._enrich_project_info(project_info, pws_content, config)

        # Step 2: Calculate timelines
        timeline_info = self._calculate_timelines(enriched_info, config)
        enriched_info.update(timeline_info)

        # Step 3: Determine page limits
        page_limits = self._calculate_page_limits(pws_content, config)
        enriched_info.update(page_limits)

        # Step 4: Populate template
        section_l_content = self._populate_template(enriched_info)

        # Step 5: Generate statistics
        stats = self._generate_statistics(section_l_content)

        print(f"\n✓ Section L generated ({stats['word_count']} words)")
        print("="*70)

        # NEW: Save document metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving document metadata for cross-referencing...")
                metadata_store = DocumentMetadataStore()

                # Extract structured data from generated Section L
                extracted_data = {
                    'proposal_due_date': enriched_info.get('proposal_due_date', 'TBD'),
                    'questions_due_date': enriched_info.get('questions_due_date', 'TBD'),
                    'page_limits': {
                        'technical': enriched_info.get('technical_page_limit', 0),
                        'management': enriched_info.get('management_page_limit', 0),
                        'cost': enriched_info.get('cost_page_limit', 0)
                    },
                    'submission_format': enriched_info.get('submission_format', 'electronic'),
                    'word_count': stats['word_count']
                }

                # Build references dict
                references = {}
                if self._pws_reference:
                    references['pws'] = self._pws_reference

                # Save to metadata store
                doc_id = metadata_store.save_document(
                    doc_type='section_l',
                    program=program_name,
                    content=section_l_content,
                    file_path='',  # Will be set by orchestrator
                    extracted_data=extracted_data,
                    references=references
                )

                print(f"✅ Document metadata saved: {doc_id}")

            except Exception as e:
                print(f"⚠️  Failed to save document metadata: {str(e)}")

        return {
            'content': section_l_content,
            'metadata': enriched_info,
            'statistics': stats,
            'status': 'success'
        }

    def _enrich_project_info(
        self,
        project_info: Dict,
        pws_content: str,
        config: Dict
    ) -> Dict:
        """
        Enrich project information with derived and default values

        Args:
            project_info: Base project information
            pws_content: PWS content for analysis
            config: Configuration overrides

        Returns:
            Enriched project information dictionary
        """
        enriched = project_info.copy()

        # Generate solicitation number if not provided
        if 'solicitation_number' not in enriched:
            enriched['solicitation_number'] = self._generate_solicitation_number(
                enriched.get('organization', 'DOD')
            )

        # Set date issued to today if not provided
        if 'date_issued' not in enriched:
            enriched['date_issued'] = datetime.now().strftime("%B %d, %Y")

        # Determine contract type
        if 'contract_type' not in enriched:
            enriched['contract_type'] = config.get('contract_type', 'Firm-Fixed-Price (FFP)')

        # Set submission method
        enriched['submission_method'] = config.get(
            'submission_method',
            'Electronic Submission via Email'
        )
        enriched['submission_address'] = config.get(
            'submission_address',
            enriched.get('ko_email', 'contracting@agency.mil')
        )

        # File size limits
        enriched['max_file_size'] = config.get('max_file_size', '50')

        # Number of copies
        enriched['electronic_copies'] = config.get('electronic_copies', '1')
        enriched['hard_copies'] = config.get('hard_copies', '0 (electronic only)')

        # Proposal volumes
        enriched['proposal_volumes'] = config.get('proposal_volumes', 'three (3)')

        # Validity period
        enriched['validity_period'] = config.get('validity_period', '180')

        # Number of required references
        enriched['required_references'] = config.get('required_references', '3-5')
        enriched['reference_timeframe'] = config.get('reference_timeframe', '3')

        # Relevance criteria
        if 'relevance_criteria' not in enriched:
            enriched['relevance_criteria'] = self._determine_relevance_criteria(pws_content)

        # Key personnel positions
        if 'key_personnel_positions' not in enriched:
            enriched['key_personnel_positions'] = self._extract_key_personnel_positions(pws_content)

        # Evaluation approach
        enriched['evaluation_approach'] = config.get(
            'evaluation_approach',
            'Best Value Trade-Off (see Section M)'
        )

        # Timezone
        enriched['timezone'] = config.get('timezone', 'Eastern Time')

        # Physical delivery address
        if 'physical_delivery_address' not in enriched:
            org = enriched.get('organization', 'Department of Defense')
            enriched['physical_delivery_address'] = (
                f"{org}\n"
                f"ATTN: {enriched.get('contracting_officer', 'Contracting Officer')}\n"
                f"Address Line 1\n"
                f"Address Line 2\n"
                f"City, State ZIP"
            )

        # Contracting officer information
        enriched.setdefault('contracting_officer', 'John Smith')
        enriched.setdefault('ko_title', 'Contracting Officer')
        enriched.setdefault('ko_email', 'john.smith@agency.mil')
        enriched.setdefault('ko_phone', '(555) 123-4567')

        return enriched

    def _calculate_timelines(self, project_info: Dict, config: Dict) -> Dict:
        """
        Calculate proposal submission timelines

        Args:
            project_info: Project information
            config: Configuration overrides

        Returns:
            Timeline information dictionary
        """
        # Parse or use today as start date
        if 'date_issued' in project_info:
            try:
                start_date = datetime.strptime(project_info['date_issued'], "%B %d, %Y")
            except:
                start_date = datetime.now()
        else:
            start_date = datetime.now()

        # Questions due date (typically 10-14 days after issue)
        questions_days = config.get('questions_days', 14)
        questions_due = start_date + timedelta(days=questions_days)

        # Proposal due date (typically 30-45 days after issue)
        proposal_days = config.get('proposal_days', 45)
        proposal_due = start_date + timedelta(days=proposal_days)

        return {
            'questions_due_date': questions_due.strftime("%B %d, %Y at 12:00 PM"),
            'proposal_due_date': proposal_due.strftime("%B %d, %Y"),
            'proposal_due_time': config.get('proposal_due_time', '2:00 PM'),
        }

    def _calculate_page_limits(self, pws_content: str, config: Dict) -> Dict:
        """
        Calculate page limits based on PWS complexity

        Args:
            pws_content: PWS content for complexity analysis
            config: Configuration overrides

        Returns:
            Page limit information
        """
        # If overrides provided, use them
        if 'technical_approach_pages' in config:
            return {
                'technical_approach_pages': config['technical_approach_pages'],
                'management_approach_pages': config['management_approach_pages'],
                'past_performance_pages': config['past_performance_pages'],
                'key_personnel_pages': config['key_personnel_pages'],
                'technical_page_limits_table': self._create_page_limits_table(config)
            }

        # Otherwise, calculate based on complexity
        word_count = len(pws_content.split())

        # Simple heuristic: more complex PWS = more pages allowed
        if word_count < 3000:
            # Simple acquisition
            limits = {
                'technical_approach_pages': 15,
                'management_approach_pages': 10,
                'past_performance_pages': 10,
                'key_personnel_pages': 10
            }
        elif word_count < 7000:
            # Moderate acquisition
            limits = {
                'technical_approach_pages': 25,
                'management_approach_pages': 15,
                'past_performance_pages': 15,
                'key_personnel_pages': 15
            }
        else:
            # Complex acquisition
            limits = {
                'technical_approach_pages': 40,
                'management_approach_pages': 20,
                'past_performance_pages': 20,
                'key_personnel_pages': 20
            }

        limits['technical_page_limits_table'] = self._create_page_limits_table(limits)

        return limits

    def _create_page_limits_table(self, limits: Dict) -> str:
        """Create formatted page limits table"""
        return f"""| Section | Page Limit |
|---------|-----------|
| Executive Summary | No Limit |
| Technical Approach | {limits.get('technical_approach_pages', 25)} pages |
| Management Approach | {limits.get('management_approach_pages', 15)} pages |
| Past Performance | {limits.get('past_performance_pages', 15)} pages |
| Key Personnel | {limits.get('key_personnel_pages', 15)} pages |"""

    def _determine_relevance_criteria(self, pws_content: str) -> str:
        """Determine past performance relevance criteria from PWS"""
        criteria = []

        # Check for common keywords
        content_lower = pws_content.lower()

        if 'software' in content_lower or 'application' in content_lower:
            criteria.append("Software development or systems engineering")
        if 'cloud' in content_lower or 'saas' in content_lower:
            criteria.append("Cloud computing services")
        if 'cybersecurity' in content_lower or 'security' in content_lower:
            criteria.append("Cybersecurity and information assurance")
        if 'maintenance' in content_lower or 'support' in content_lower:
            criteria.append("Operations and maintenance support")
        if 'data' in content_lower and 'analysis' in content_lower:
            criteria.append("Data analytics and business intelligence")

        if not criteria:
            criteria.append("Similar scope, complexity, and dollar value")
            criteria.append("Similar technical domain")

        return "\n- ".join([""] + criteria)

    def _extract_key_personnel_positions(self, pws_content: str) -> str:
        """Extract key personnel positions from PWS"""
        positions = []

        # Common patterns
        common_positions = [
            "Program Manager",
            "Technical Lead",
            "Deputy Program Manager"
        ]

        # Check for specific mentions in PWS
        content_lower = pws_content.lower()

        if 'program manager' in content_lower:
            positions.append("- Program Manager")
        if 'technical lead' in content_lower or 'chief engineer' in content_lower:
            positions.append("- Technical Lead / Chief Engineer")
        if 'deputy' in content_lower:
            positions.append("- Deputy Program Manager")
        if 'security' in content_lower:
            positions.append("- Information Security Manager (if applicable)")
        if 'quality' in content_lower or 'qa' in content_lower:
            positions.append("- Quality Assurance Manager (if applicable)")

        # Default if nothing found
        if not positions:
            positions = [f"- {pos}" for pos in common_positions]

        return "\n".join(positions)

    def _populate_template(self, project_info: Dict) -> str:
        """
        Populate Section L template with project information

        Args:
            project_info: Enriched project information

        Returns:
            Populated Section L content
        """
        content = self.template

        # Replace all template variables
        for key, value in project_info.items():
            placeholder = f"{{{{{key}}}}}"
            content = content.replace(placeholder, str(value))

        # Handle any remaining placeholders with defaults
        remaining_placeholders = re.findall(r'\{\{(\w+)\}\}', content)
        for placeholder in remaining_placeholders:
            content = content.replace(f"{{{{{placeholder}}}}}", "[TO BE DETERMINED]")

        return content

    def _generate_solicitation_number(self, organization: str) -> str:
        """Generate DoD-style solicitation number"""
        # Extract org code
        org_code = "W911"
        if "NAVY" in organization.upper():
            org_code = "N000"
        elif "AIR FORCE" in organization.upper():
            org_code = "FA86"
        elif "ARMY" in organization.upper():
            org_code = "W911"

        # Fiscal year
        fiscal_year = datetime.now().year % 100

        # Random sequence
        import random
        sequence = random.randint(1000, 9999)

        return f"{org_code}XX-{fiscal_year:02d}-R-{sequence:04d}"

    def _generate_statistics(self, content: str) -> Dict:
        """Generate statistics about Section L document"""
        lines = content.split('\n')
        words = content.split()

        return {
            'line_count': len(lines),
            'word_count': len(words),
            'char_count': len(content),
            'section_count': content.count('\n## ')
        }

    def save_to_file(
        self,
        content: str,
        output_path: str,
        convert_to_pdf: bool = True
    ) -> Dict:
        """
        Save Section L to file

        Args:
            content: Section L content
            output_path: Output path (markdown)
            convert_to_pdf: Whether to convert to PDF

        Returns:
            Dictionary with file paths
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save markdown
        with open(output_path, 'w') as f:
            f.write(content)

        result = {'markdown': str(output_path)}

        # Convert to PDF if requested
        if convert_to_pdf:
            pdf_path = output_path.with_suffix('.pdf')
            try:
                from utils.convert_md_to_pdf import convert_markdown_to_pdf
                convert_markdown_to_pdf(str(output_path), str(pdf_path))
                result['pdf'] = str(pdf_path)
                print(f"✓ PDF created: {pdf_path}")
            except Exception as e:
                print(f"⚠ Could not create PDF: {e}")

        return result


# Example usage
def main():
    """Test Section L Generator Agent"""
    import os
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    # Sample project info
    project_info = {
        'program_name': 'Advanced Cloud Inventory Management System',
        'organization': 'Department of Defense / U.S. Army',
        'author': 'Jane Smith',
        'contracting_officer': 'John Doe',
        'ko_email': 'john.doe@army.mil',
        'ko_phone': '(703) 555-1234',
        'estimated_value': '$5,000,000 - $10,000,000',
        'period_of_performance': 'Base Period (12 months) + Four Option Periods (12 months each)'
    }

    # Sample PWS content (for analysis)
    pws_content = """
    The contractor shall develop and deploy a cloud-based inventory management system
    with cybersecurity controls, data analytics capabilities, and 24/7 support.
    """ * 100  # Simulate moderate complexity

    # Configuration
    config = {
        'contract_type': 'Firm-Fixed-Price (FFP)',
        'proposal_days': 45,
        'questions_days': 14
    }

    # Initialize agent
    agent = SectionLGeneratorAgent(api_key=api_key)

    # Execute
    task = {
        'project_info': project_info,
        'pws_content': pws_content,
        'config': config
    }

    result = agent.execute(task)

    # Save
    output_path = "outputs/section_l/section_l_instructions_to_offerors.md"
    files = agent.save_to_file(result['content'], output_path)

    print(f"\n✅ Section L generated successfully!")
    print(f"   Markdown: {files['markdown']}")
    if 'pdf' in files:
        print(f"   PDF: {files['pdf']}")


if __name__ == "__main__":
    main()
