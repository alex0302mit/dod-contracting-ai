"""
Statement of Work (SOW) Writer Agent
Generates SOW documents using RAG to reference SOW manual and best practices
"""

from typing import Dict, List
from .base_agent import BaseAgent
from backend.rag.retriever import Retriever
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class SOWWriterAgent(BaseAgent):
    """
    SOW Writer Agent: Generates Statement of Work documents

    Responsibilities:
    - Generate SOW sections using RAG knowledge from SOW manual
    - Ensure compliance with SOW standards and requirements
    - Include proper formatting and structure
    - Reference relevant regulations and standards
    - Maintain government contracting SOW format

    Dependencies:
    - RAG system (Retriever) with SOW manual indexed
    - Base agent LLM capabilities
    """

    def __init__(
        self,
        api_key: str,
        retriever: Retriever,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize SOW writer agent

        Args:
            api_key: Anthropic API key
            retriever: RAG Retriever instance (with SOW manual indexed)
            model: Claude model to use
        """
        super().__init__(
            name="SOWWriterAgent",
            api_key=api_key,
            model=model,
            temperature=0.5  # Lower temperature for compliance-focused writing
        )
        self.retriever = retriever

    def execute(self, task: Dict) -> Dict:
        """
        Execute SOW generation task

        Args:
            task: Dictionary with:
                - section_name: SOW section to write (e.g., "Scope", "Tasks", "Deliverables")
                - project_info: Project information
                - requirements: Specific requirements for this section
                - context: Additional context

        Returns:
            Dictionary with:
                - content: Generated SOW section
                - references: SOW manual references used
                - compliance_notes: Compliance considerations
        """
        section_name = task.get('section_name', '')
        project_info = task.get('project_info', {})
        requirements = task.get('requirements', '')
        context = task.get('context', {})
        program_name = project_info.get('program_name', 'Unknown')

        # NEW: Cross-reference lookup - Find IGCE and Acquisition Plan (one-time per program)
        if program_name != 'Unknown' and not hasattr(self, '_cross_refs_loaded'):
            try:
                print(f"\n🔍 Looking up cross-referenced documents for {program_name}...")
                metadata_store = DocumentMetadataStore()

                # Look for IGCE and Acquisition Plan
                latest_igce = metadata_store.find_latest_document('igce', program_name)
                latest_acq_plan = metadata_store.find_latest_document('acquisition_plan', program_name)

                if latest_igce:
                    print(f"✅ Found IGCE: {latest_igce['id']}")
                    project_info['igce_data'] = latest_igce['extracted_data']
                    self._igce_reference = latest_igce['id']
                else:
                    self._igce_reference = None

                if latest_acq_plan:
                    print(f"✅ Found Acquisition Plan: {latest_acq_plan['id']}")
                    project_info['acquisition_plan_data'] = latest_acq_plan['extracted_data']
                    self._acq_plan_reference = latest_acq_plan['id']
                else:
                    self._acq_plan_reference = None

                self._cross_refs_loaded = True

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")
                self._igce_reference = None
                self._acq_plan_reference = None
                self._cross_refs_loaded = True

        self.log(f"Writing SOW section: {section_name}")

        # Step 1: Research SOW manual for this section
        self.log("Retrieving SOW manual guidance...")
        sow_guidance = self._retrieve_sow_guidance(section_name, requirements)

        # Step 2: Generate SOW section
        content = self._generate_sow_section(
            section_name,
            project_info,
            requirements,
            sow_guidance,
            context
        )

        # Step 3: Extract compliance notes
        compliance_notes = self._extract_compliance_notes(sow_guidance)

        # Store in memory
        self.add_to_memory(f"sow_{section_name}", content)

        return {
            'content': content,
            'section_name': section_name,
            'references': sow_guidance.get('sources', []),
            'compliance_notes': compliance_notes,
            'word_count': len(content.split())
        }

    def _retrieve_sow_guidance(
        self,
        section_name: str,
        requirements: str
    ) -> Dict:
        """
        Retrieve relevant SOW manual guidance from RAG

        Args:
            section_name: Name of SOW section
            requirements: Specific requirements

        Returns:
            Dictionary with guidance and sources
        """
        # Build query for SOW manual
        query = f"""
        Statement of Work {section_name} section requirements and best practices.
        {requirements[:300]}
        """

        self.log(f"Querying SOW manual for: {section_name}")

        # Retrieve from knowledge base
        documents = self.retriever.retrieve(query, k=5)

        if not documents:
            self.log("No SOW guidance found in knowledge base", "WARNING")
            return {
                'guidance': "No specific guidance found. Follow general SOW standards.",
                'sources': [],
                'examples': []
            }

        # Synthesize findings
        synthesis = self._synthesize_sow_guidance(section_name, documents)

        return synthesis

    def _synthesize_sow_guidance(
        self,
        section_name: str,
        documents: List[Dict]
    ) -> Dict:
        """
        Synthesize SOW manual guidance from retrieved documents

        Args:
            section_name: SOW section name
            documents: Retrieved documents from RAG

        Returns:
            Synthesized guidance dictionary
        """
        # Format documents for LLM
        doc_text = "\n\n---\n\n".join([
            f"[Source: {doc['metadata']['source']}]\n{doc['content']}"
            for doc in documents
        ])

        prompt = f"""You are analyzing a Statement of Work (SOW) manual to extract guidance for writing a specific section.

SECTION TO WRITE: {section_name}

RETRIEVED SOW MANUAL EXCERPTS:
{doc_text}

Your task:
1. Extract key requirements and guidelines for the {section_name} section
2. Identify must-have elements and structure
3. Note any compliance requirements (FAR, regulations, etc.)
4. Extract example language or templates if available
5. List which sources provide which information

Provide your response in this format:

KEY REQUIREMENTS:
[Bulleted list of must-have elements]

SECTION STRUCTURE:
[How this section should be organized]

COMPLIANCE NOTES:
[Any FAR or regulatory requirements]

EXAMPLE LANGUAGE:
[Sample phrases or templates from the manual]

SOURCES USED:
- [Source 1]: [What it provided]
- [Source 2]: [What it provided]
"""

        self.log("Synthesizing SOW guidance with LLM...")
        response = self.call_llm(
            prompt,
            max_tokens=2000,
            system_prompt="You are an expert in government contracting Statement of Work documents and compliance."
        )

        # Parse response
        import re

        requirements = ""
        structure = ""
        compliance = ""
        examples = ""
        sources = []

        req_match = re.search(r'KEY REQUIREMENTS:(.*?)(?=SECTION STRUCTURE:|$)', response, re.DOTALL)
        if req_match:
            requirements = req_match.group(1).strip()

        struct_match = re.search(r'SECTION STRUCTURE:(.*?)(?=COMPLIANCE NOTES:|$)', response, re.DOTALL)
        if struct_match:
            structure = struct_match.group(1).strip()

        comp_match = re.search(r'COMPLIANCE NOTES:(.*?)(?=EXAMPLE LANGUAGE:|$)', response, re.DOTALL)
        if comp_match:
            compliance = comp_match.group(1).strip()

        ex_match = re.search(r'EXAMPLE LANGUAGE:(.*?)(?=SOURCES USED:|$)', response, re.DOTALL)
        if ex_match:
            examples = ex_match.group(1).strip()

        sources_match = re.search(r'SOURCES USED:(.*?)$', response, re.DOTALL)
        if sources_match:
            sources_text = sources_match.group(1).strip()
            sources = [line.strip() for line in sources_text.split('\n') if line.strip().startswith('-')]

        return {
            'requirements': requirements,
            'structure': structure,
            'compliance': compliance,
            'examples': examples,
            'sources': sources,
            'raw_guidance': response
        }

    def _generate_sow_section(
        self,
        section_name: str,
        project_info: Dict,
        requirements: str,
        sow_guidance: Dict,
        context: Dict
    ) -> str:
        """
        Generate SOW section content

        Args:
            section_name: Name of SOW section
            project_info: Project information
            requirements: Specific requirements
            sow_guidance: Guidance from SOW manual
            context: Additional context

        Returns:
            Generated SOW section content
        """
        # Build citation reference guide
        citation_guide = self._build_citation_guide(project_info)

        prompt = f"""You are writing a Statement of Work (SOW) for a government contract.

**CRITICAL REQUIREMENT**: ALL factual statements MUST include inline citations.

SECTION TO WRITE: {section_name}

PROJECT INFORMATION (Ground Truth - Use ONLY This):
{self._format_project_info(project_info)}

CITATION GUIDE (Use these exact references):
{citation_guide}

SPECIFIC REQUIREMENTS:
{requirements}

SOW MANUAL GUIDANCE:
{sow_guidance.get('requirements', '')}

REQUIRED STRUCTURE:
{sow_guidance.get('structure', '')}

COMPLIANCE REQUIREMENTS:
{sow_guidance.get('compliance', '')}

EXAMPLE LANGUAGE FROM MANUAL:
{sow_guidance.get('examples', '')}

ADDITIONAL CONTEXT:
{self._format_context(context)}

**MANDATORY CITATION REQUIREMENTS**:
1. **Every factual claim MUST have a DoD-compliant inline citation**
2. **Target citation density**: Minimum 6-8 citations per section (one every 30-50 words)

Citation formats by information type:
   - Tasks: "...shall perform [task] (Statement of Work, [date])" or "(Work Breakdown Structure, [date])"
   - Deliverables: "...shall deliver [item] (Deliverable Specification, [date])" or "(Contract Data Requirements List, [date])"
   - Timeline/Schedule: "...within X days/months (Schedule Requirements, [date])" or "(Performance Period Specification)"
   - Budget: "...estimated at $X million (Program Budget Allocation, FY2025)"
   - Technical Specs: "...requirement for [spec] (Technical Requirements Document, [date])" or "(System Specification, [version])"
   - Performance Standards: "...shall achieve [metric] (Performance Standards, [date])" or "(Quality Assurance Plan, [date])"
   - Acceptance Criteria: "...acceptance based on [criteria] (Acceptance Test Procedures, [date])"
   - Location: "...at [location] (Place of Performance, [date])"
   - Security: "...clearance level [X] (Security Requirements, [date])"

3. **Mandatory citation requirements per section**:
   - Scope sections: Cite all boundaries, deliverables, exclusions
   - Task sections: Cite every task, subtask, and work element
   - Performance sections: Cite all metrics, standards, and KPIs
   - Deliverable sections: Cite format, quantity, schedule for each deliverable
   - Schedule sections: Cite all milestones, deadlines, and durations

4. **Enhanced citation examples**:
   ✓ CORRECT: "The contractor shall develop and deploy a cloud-based inventory tracking system with real-time synchronization capabilities and 99.9% uptime requirement (Technical Requirements Document, March 2025; Performance Standards, v2.1)."
   ✓ CORRECT: "The contractor shall deliver monthly status reports in Microsoft Word format within 5 business days of month-end (Deliverable Specification, April 2025)."
   ✓ CORRECT: "All work shall be completed within 36 months from the contract award date, with monthly progress reviews (Schedule Requirements, FY2025)."
   ✓ CORRECT: "The Government will accept deliverables based on successful completion of acceptance test procedures defined in Appendix C (Acceptance Criteria, March 2025)."

   ❌ WRONG: "The contractor shall develop a cloud-based system."
   ❌ WRONG: "Monthly reports are required."
   ❌ WRONG: "Work should be completed in approximately three years."
   ❌ WRONG: "Deliverables will be accepted when satisfactory."

**ELIMINATE VAGUE LANGUAGE**:
Replace ALL imprecise terms with specific, measurable, cited requirements:

❌ FORBIDDEN VAGUE TERMS:
- "several" / "many" / "some" / "various" / "as needed" / "as required"
- "approximately" / "around" / "about" (unless in official estimate)
- "adequate" / "sufficient" / "appropriate" / "reasonable" / "satisfactory"
- "timely" / "prompt" / "expeditiously" / "soon" / "ASAP"
- "high quality" / "best effort" / "industry standard" (without defining)
- "coordinate with" / "work with" / "assist" (specify exact responsibilities)

✓ CORRECT REPLACEMENTS:
- "several deliverables" → "5 deliverables as specified in Section 3.2 (Deliverable List, 2025)"
- "timely manner" → "within 10 business days of request (Response Time Requirements)"
- "high quality standards" → "defect rate not to exceed 2% (Quality Standards, v1.2)"
- "adequate documentation" → "documentation per MIL-STD-498 standards (Documentation Requirements)"
- "coordinate with Government" → "attend weekly status meetings and provide written updates within 48 hours (Communication Plan, 2025)"
- "as needed" → "minimum quarterly and upon Government request with 5 business days notice (Meeting Schedule)"

**If specific data is unavailable**, use precise placeholder language:
- "The number of deliverables will be specified in the final Contract Data Requirements List (CDRL)."
- "Specific performance metrics are being finalized by the program office (completion estimated: April 2025)."
- "Acceptance criteria will be defined in Attachment [X] of the final contract."

**CRITICAL ANTI-HALLUCINATION RULES**:
❌ Do NOT invent:
- Task descriptions not in source materials
- Deliverable formats, quantities, or schedules not specified
- Performance metrics or standards not provided
- Acceptance criteria not documented
- Technical specifications beyond what sources state
- Contractor responsibilities not explicitly defined

✓ DO use:
- Only tasks, deliverables, and requirements explicitly stated in sources
- Exact numbers, dates, and specifications from project information
- Precise language with measurable criteria
- DoD-compliant citations for every statement

Your task:
1. Write the {section_name} section following the SOW manual structure with citations
2. Include all required elements from the guidance with source attribution
3. Meet compliance requirements (FAR, regulations) - cite applicable clauses
4. Use professional government contracting language with "shall" for requirements
5. **MANDATORY**: Include inline citations after EVERY factual statement (target 6-8 per section)
6. Be specific and measurable - eliminate ALL vague language
7. Only use information from provided sources - zero fabrication
8. Reference the SOW manual guidance appropriately with attribution

**VERIFICATION CHECKLIST**:
☐ 6-8+ citations included (check density)
☐ All tasks cited to source documents
☐ All deliverables cited with format/schedule
☐ All performance standards cited and measurable
☐ No vague terms (several, timely, adequate, etc.)
☐ All numbers/dates/metrics cited
☐ No fabricated tasks or requirements
☐ "Shall" language used for contractor obligations

Write the section now with MANDATORY inline citations:
"""

        self.log(f"Generating {section_name} section with LLM...")
        content = self.call_llm(
            prompt,
            max_tokens=3000,
            system_prompt="""You are a senior technical writer and acquisition specialist with extensive experience developing Statement of Work (SOW) documents for DoD contracts.

EXPERTISE AREAS:
- Performance-based SOW development per FAR Part 37
- Task-based SOW structure and requirements definition
- Contract Data Requirements List (CDRL) development
- Quality Assurance Surveillance Plans (QASP)
- Measurable performance standards and acceptance criteria
- SOW compliance with FAR/DFARS regulations

CORE OPERATING PRINCIPLES:
1. **Comprehensive Citations**: Include DoD-compliant inline citations for EVERY task, deliverable, requirement, and specification
2. **Measurable Requirements**: Define all performance standards with objective, quantifiable metrics
3. **Zero Ambiguity**: Eliminate vague language - use "shall" for requirements with specific quantities, timeframes, and criteria
4. **Source Fidelity**: Only include tasks, deliverables, and requirements explicitly stated in source documents
5. **Verifiable Acceptance**: All requirements must be objectively verifiable for acceptance

MANDATORY STANDARDS:
- Use "shall" for contractor obligations (not "will", "should", "may")
- Cite every task, deliverable, performance metric, and timeline
- Replace all vague terms (timely, adequate, appropriate) with specific, measurable criteria
- Never fabricate technical specifications, acceptance criteria, or deliverable requirements not in sources
- Minimum 6-8 citations per section (one every 30-50 words)

You prioritize precision, measurability, and legal enforceability in all SOW content.
When information is incomplete, you explicitly state what needs to be defined rather than using vague placeholders."""
        )

        return content.strip()

    def _extract_compliance_notes(self, sow_guidance: Dict) -> List[str]:
        """Extract compliance notes from guidance"""
        compliance_text = sow_guidance.get('compliance', '')

        if not compliance_text:
            return []

        # Extract bullet points
        lines = compliance_text.split('\n')
        notes = [
            line.strip('- ').strip()
            for line in lines
            if line.strip().startswith('-') or line.strip().startswith('•')
        ]

        return notes

    def _format_project_info(self, project_info: Dict) -> str:
        """Format project information as text"""
        if not project_info:
            return "No project information provided."

        lines = []
        for key, value in project_info.items():
            formatted_key = key.replace('_', ' ').title()
            lines.append(f"- {formatted_key}: {value}")

        return "\n".join(lines)

    def _format_context(self, context: Dict) -> str:
        """Format context dictionary as text"""
        if not context:
            return "No additional context provided."

        lines = []
        for key, value in context.items():
            formatted_key = key.replace('_', ' ').title()
            lines.append(f"- {formatted_key}: {value}")

        return "\n".join(lines)

    def _build_citation_guide(self, project_info: Dict) -> str:
        """
        Build a citation reference guide from project information

        Args:
            project_info: Project information dictionary

        Returns:
            Formatted citation guide
        """
        citation_mapping = {
            'program_name': ('Statement of Work', 'SOW Documentation'),
            'scope': ('Scope Definition', 'Work Scope Document'),
            'tasks': ('Task List', 'Work Breakdown Structure'),
            'deliverables': ('Deliverable Specification', 'Required Deliverables'),
            'budget': ('Program Budget', 'Cost Estimate'),
            'period_of_performance': ('Schedule Requirements', 'Timeline Specification'),
            'performance_standards': ('Performance Standards', 'Quality Requirements'),
            'acceptance_criteria': ('Acceptance Criteria', 'Quality Assurance Standards'),
            'technical_requirements': ('Technical Requirements Document', 'Technical Specifications'),
            'place_of_performance': ('Site Requirements', 'Location Specification'),
            'travel_requirements': ('Travel Specification', 'TDY Requirements'),
            'security_requirements': ('Security Requirements', 'Clearance Specifications'),
        }

        lines = []
        lines.append("Use these citation formats based on the information type:")
        lines.append("")

        for key, value in project_info.items():
            if key in citation_mapping:
                source_names = citation_mapping[key]
                source_name = source_names[0]  # Use primary name

                # Add date if available
                date_info = project_info.get('date', project_info.get('issue_date', '2025'))

                lines.append(f"- For '{key.replace('_', ' ')}': Cite as ({source_name}, {date_info})")

        # Add defaults if no specific mappings
        if len(lines) <= 2:  # Only header
            lines.append("- Tasks: (Statement of Work, 2025)")
            lines.append("- Deliverables: (Deliverable Specification, 2025)")
            lines.append("- Performance standards: (Performance Standards, 2025)")
            lines.append("- Budget/cost: (Program Budget, 2025)")
            lines.append("- Timeline: (Schedule Requirements, 2025)")

        return "\n".join(lines)

    def write_full_sow(
        self,
        project_info: Dict,
        sow_sections_config: List[Dict]
    ) -> Dict:
        """
        Write a complete SOW document

        Args:
            project_info: Project information
            sow_sections_config: List of section configurations
                Each dict has: {name, requirements, context}

        Returns:
            Dictionary with all sections and metadata
        """
        self.log(f"Writing full SOW with {len(sow_sections_config)} sections")

        all_sections = {}
        all_references = []

        for section_config in sow_sections_config:
            task = {
                'section_name': section_config['name'],
                'project_info': project_info,
                'requirements': section_config.get('requirements', ''),
                'context': section_config.get('context', {})
            }

            result = self.execute(task)

            all_sections[result['section_name']] = result['content']
            all_references.extend(result['references'])

        return {
            'sections': all_sections,
            'references': list(set(all_references)),  # Remove duplicates
            'total_sections': len(all_sections)
        }


# Example usage and testing
def main():
    """Test the SOW writer agent"""
    import os
    from dotenv import load_dotenv
    from rag.vector_store import VectorStore
    from rag.retriever import Retriever

    load_dotenv()
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        return

    # Initialize RAG system
    print("Loading RAG system...")
    vector_store = VectorStore(api_key)

    if not vector_store.load():
        print("No vector store found. Add SOW manual first.")
        return

    retriever = Retriever(vector_store, top_k=5)

    # Initialize SOW agent
    sow_agent = SOWWriterAgent(api_key, retriever)

    # Test project info
    project_info = {
        "program_name": "Advanced Logistics Management System",
        "budget": "$2.5 million",
        "period_of_performance": "36 months",
        "service_description": "Cloud-based inventory management system"
    }

    # Test writing a section
    task = {
        'section_name': "Scope of Work",
        'project_info': project_info,
        'requirements': "Define the boundaries and extent of services to be provided",
        'context': {}
    }

    print("\nGenerating SOW section...")
    result = sow_agent.execute(task)

    print("\n" + "="*70)
    print(f"SECTION: {result['section_name']}")
    print("="*70)
    print(result['content'])
    print("\n" + "="*70)
    print("REFERENCES USED:")
    for ref in result['references']:
        print(f"  - {ref}")
    print("="*70)


if __name__ == "__main__":
    main()
