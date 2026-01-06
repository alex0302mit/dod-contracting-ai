"""
Request for Proposal (RFP) Writer Agent
Generates comprehensive RFP documents using RAG
"""

from typing import Dict, List
from .base_agent import BaseAgent
from backend.rag.retriever import Retriever
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class RFPWriterAgent(BaseAgent):
    """
    RFP Writer Agent: Generates Request for Proposal documents
    
    Responsibilities:
    - Generate complete RFP sections (Sections A-M per FAR)
    - Include evaluation criteria and submission requirements
    - Use RAG to reference RFP best practices and FAR regulations
    - Ensure compliance with DoD acquisition requirements
    - Create clear instructions for offerors
    
    Key Focus Areas:
    - Clarity and completeness
    - Fair and transparent evaluation criteria
    - Compliance with FAR/DFARS
    - Small business considerations
    - Realistic timelines
    
    Dependencies:
    - BaseAgent: Core LLM functionality
    - Retriever: RAG system for RFP guidance
    """
    
    def __init__(
        self,
        api_key: str,
        retriever: Retriever,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize RFP writer agent
        
        Args:
            api_key: Anthropic API key
            retriever: RAG Retriever (with RFP guide indexed)
            model: Claude model to use
        """
        super().__init__(
            name="RFPWriterAgent",
            api_key=api_key,
            model=model,
            temperature=0.4  # Lower temperature for compliance/accuracy
        )
        self.retriever = retriever
    
    def execute(self, task: Dict) -> Dict:
        """
        Execute RFP section generation
        
        Args:
            task: Dictionary with:
                - section_name: RFP section name (e.g., "Section A", "Section L")
                - project_info: Project information
                - guidance: Section guidance
                - section_type: Type of section (solicitation, contract, instructions, evaluation)
                
        Returns:
            Dictionary with:
                - content: Generated RFP section
                - word_count: Number of words
                - compliance_items: List of compliance requirements mentioned
                - evaluation_factors: List of evaluation factors (if applicable)
        """
        section_name = task.get('section_name', '')
        project_info = task.get('project_info', {})
        guidance = task.get('guidance', '')
        section_type = task.get('section_type', 'general')
        program_name = project_info.get('program_name', 'Unknown')

        self.log(f"Writing RFP section: {section_name}")

        # STEP 0: Cross-reference lookup for all solicitation documents
        self._document_references = []

        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up solicitation documents for RFP compilation...")
                metadata_store = DocumentMetadataStore()

                # Get all solicitation documents for comprehensive RFP
                solicitation_docs = [doc for doc in metadata_store._documents.values()
                                    if doc['program'] == program_name and
                                    doc['doc_type'] in ['igce', 'acquisition_plan', 'pws', 'sow', 'soo',
                                                       'qasp', 'section_l', 'section_m', 'section_b',
                                                       'section_h', 'section_i', 'section_k', 'sf33']]

                if solicitation_docs:
                    print(f"✅ Found {len(solicitation_docs)} solicitation documents")
                    self._document_references = solicitation_docs

                    # Add comprehensive data to project_info for RFP compilation
                    for doc in solicitation_docs:
                        doc_type = doc['doc_type']
                        project_info[f'{doc_type}_data'] = doc['extracted_data']
                        print(f"   - {doc_type}: {doc['id']}")

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")
        
        # Step 1: Retrieve RFP guidance from knowledge base
        self.log("Retrieving RFP best practices...")
        rfp_guidance = self._retrieve_rfp_guidance(section_name, section_type)
        
        # Step 2: Generate RFP section
        content = self._generate_rfp_section(
            section_name,
            project_info,
            guidance,
            rfp_guidance,
            section_type
        )
        
        # Step 3: Analyze content
        analysis = self._analyze_rfp_content(content, section_type)
        
        self.log(f"Generated {len(content.split())} words for {section_name}")

        # STEP 2: Save RFP metadata
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving RFP Section metadata...")
                metadata_store = DocumentMetadataStore()

                # Extract RFP Section specific data
                extracted_data = {
                    'section_name': section_name,
                    'section_type': section_type,
                    'word_count': len(content.split()),
                    'compliance_items_count': len(analysis.get('compliance_items', [])),
                    'evaluation_factors_count': len(analysis.get('evaluation_factors', [])),
                    'solicitation_docs_referenced': len(self._document_references)
                }

                # Track references (all solicitation documents used)
                references = {}
                for doc in self._document_references:
                    references[doc['doc_type']] = doc['id']

                doc_id = metadata_store.save_document(
                    doc_type='rfp_section',
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
            'content': content,
            'section_name': section_name,
            'word_count': len(content.split()),
            'compliance_items': analysis.get('compliance_items', []),
            'evaluation_factors': analysis.get('evaluation_factors', []),
            'clarity_score': analysis.get('clarity_score', 0)
        }
    
    def _retrieve_rfp_guidance(self, section_name: str, section_type: str) -> str:
        """
        Retrieve relevant RFP guidance from knowledge base
        
        Args:
            section_name: Name of RFP section
            section_type: Type of section
            
        Returns:
            Retrieved guidance text
        """
        # Build retrieval query focused on RFP requirements
        query = f"Request for Proposal {section_name} {section_type} FAR requirements DoD best practices"
        
        # Retrieve relevant chunks
        documents = self.retriever.retrieve(query, k=5)
        
        if not documents:
            return "No RFP guidance found. Follow FAR Part 15 requirements."
        
        # Format guidance
        guidance_parts = []
        for doc in documents:
            guidance_parts.append(f"[{doc['metadata']['source']}]\n{doc['content']}")
        
        return "\n\n---\n\n".join(guidance_parts)
    
    def _generate_rfp_section(
        self,
        section_name: str,
        project_info: Dict,
        guidance: str,
        rfp_guidance: str,
        section_type: str
    ) -> str:
        """
        Generate RFP section content
        
        Args:
            section_name: Section name
            project_info: Project information
            guidance: Section guidance
            rfp_guidance: Retrieved RFP best practices
            section_type: Section type
            
        Returns:
            Generated section content
        """
        # Build specialized prompt based on section type
        section_instructions = {
            'solicitation': """Generate clear solicitation provisions:
- Include all required FAR clauses
- Define scope clearly
- Specify deliverables
- State period of performance
- Include place of performance""",
            
            'contract': """Generate contract terms and clauses:
- Reference applicable FAR/DFARS clauses
- Include payment terms
- Define inspection/acceptance criteria
- Specify warranty requirements
- Include data rights provisions""",
            
            'instructions': """Provide clear instructions to offerors:
- Proposal format and structure
- Page limits and formatting requirements
- Submission methods and deadlines
- Question/answer process
- Required certifications and representations""",
            
            'evaluation': """Define fair evaluation criteria:
- Evaluation factors in order of importance
- Relative weights or importance ratings
- Subfactors with clear descriptions
- Past performance evaluation approach
- Price evaluation methodology
- Trade-off process explanation"""
        }
        
        section_instruction = section_instructions.get(
            section_type, 
            "Generate clear, comprehensive content."
        )
        
        # Build citation reference guide
        citation_guide = self._build_citation_guide(project_info)

        # Create comprehensive prompt with STRICT GROUNDING and MANDATORY CITATIONS
        prompt = f"""You are writing a Request for Proposal (RFP) for a government acquisition.

**CRITICAL CONSTRAINT - ANTI-HALLUCINATION RULES**:
1. ONLY use information from:
   - Project Information (below)
   - RFP Best Practices (below)
2. Do NOT invent specific details, numbers, or capabilities not mentioned
3. Do NOT assume technical specifications beyond what's stated
4. If information is missing, write in general terms or state "To Be Determined"
5. **MANDATORY**: Cite ALL factual claims inline

**FORBIDDEN ACTIONS**:
❌ Do NOT invent vendor names, company names, or product names
❌ Do NOT specify technical details not in source material
❌ Do NOT create specific metrics without source data
❌ Do NOT elaborate beyond the scope of provided information
❌ Do NOT write ANY factual statement without a citation

SECTION: {section_name}

PROJECT INFORMATION (Ground Truth - Use ONLY This):
{self._format_project_info(project_info)}

CITATION GUIDE (Use these exact references):
{citation_guide}

RFP BEST PRACTICES (from knowledge base):
{rfp_guidance}

SECTION GUIDANCE:
{guidance}

**SECTION-SPECIFIC INSTRUCTIONS**:
{section_instruction}

**MANDATORY CITATION REQUIREMENTS**:
1. **Every factual claim MUST have a DoD-compliant inline citation**
2. **Target citation density**: Minimum 5-7 citations per section (one every 40-60 words)

Citation formats by type:
   - Budget/Cost: "...estimated at $X million (Program Budget Allocation, FY2025)"
   - Timeline: "...period of X months from award date (Performance Schedule, [date])"
   - Requirements: "...requirement for [spec] (Technical Requirements Document, [date])"
   - FAR/DFARS: "...per FAR 15.204 (Solicitation Requirements)" or "...per DFARS 225.872"
   - Vendor Info: "...X qualified vendors identified (Market Research Report, [date])"
   - Small Business: "...set-aside for small business (Small Business Determination, [date])"
   - Deliverables: "...deliverable [X] (Statement of Work, [date])"
   - Evaluation: "...evaluation factor (Source Selection Plan, [date])"

3. **Minimum citation requirements per section type**:
   - Solicitation sections: Cite scope, deliverables, period, place of performance
   - Contract sections: Cite all FAR/DFARS clauses, payment terms, acceptance criteria
   - Instructions sections: Cite submission requirements, deadlines, page limits
   - Evaluation sections: Cite all factors, weights, methodology

4. **Enhanced citation examples**:
   ✓ CORRECT: "The Government requires a cloud-based inventory tracking system with 99.9% uptime and real-time synchronization capabilities (Technical Requirements Document, March 2025)."
   ✓ CORRECT: "The estimated contract value is $2.5 million over a base period of 36 months with two optional 12-month extension periods (Program Budget Allocation, FY2025)."
   ✓ CORRECT: "Per FAR 15.204-5, agencies must include the provision at FAR 52.215-1 (Instructions to Offerors) in all competitive proposals."
   ✓ CORRECT: "Offerors shall submit proposals by 3:00 PM Eastern Time on June 15, 2025 (Solicitation Schedule, April 2025)."

   ❌ WRONG: "The Government requires a cloud-based system with high uptime."
   ❌ WRONG: "The contract value is approximately $2-3 million."
   ❌ WRONG: "Proposals must be submitted by the deadline."

**ELIMINATE VAGUE LANGUAGE**:
Replace ALL imprecise terms with specific, cited facts:

❌ FORBIDDEN VAGUE TERMS:
- "several" / "many" / "some" / "various" / "numerous"
- "approximately" / "around" / "about" (unless in official estimate)
- "significant" / "substantial" / "adequate" / "sufficient"
- "timely" / "prompt" / "soon" / "recent" (specify actual timeframes)
- "appropriate" / "reasonable" / "as needed"

✓ CORRECT REPLACEMENTS:
- "several vendors" → "8 vendors identified (Market Research, March 2025)"
- "adequate performance" → "99.5% uptime requirement (Performance Standards, 2025)"
- "timely delivery" → "delivery within 45 calendar days of order (Delivery Schedule)"
- "reasonable price" → "fair and reasonable pricing per FAR 15.404-1 (Price Analysis)"

**If specific data is unavailable**, use precise language:
- "The number of evaluation factors will be specified in Section M of the final RFP."
- "Delivery timelines are under development by the program office (estimated finalization: April 2025)."

**OUTPUT REQUIREMENTS**:
1. Write 3-6 substantive paragraphs (minimum 300 words)
2. Professional government acquisition tone per FAR standards
3. Follow FAR Part 15 requirements strictly
4. Use ONLY facts from above sources - zero fabrication
5. **Include inline citations after EVERY factual statement**
6. Eliminate all vague/imprecise language
7. Every number, date, requirement, and specification MUST be cited
8. No vendor bias or anti-competitive language

**VERIFICATION CHECKLIST**:
☐ 5-7+ citations included (check density)
☐ No vague terms (several, many, approximately, etc.)
☐ All numbers/dates/specs cited
☐ No fabricated information
☐ FAR/DFARS references cited correctly
☐ No vendor preferences or bias

Generate the {section_name} content now WITH MANDATORY INLINE CITATIONS:
"""
        
        self.log("Generating RFP content with LLM...")
        
        # System prompt emphasizes accuracy and compliance
        system_prompt = """You are a senior government acquisition specialist with extensive experience writing compliant RFP documents for DoD programs.

EXPERTISE AREAS:
- FAR/DFARS regulations and clause selection
- DoD acquisition policy and source selection
- Competitive procurement procedures
- Small business program requirements
- Contract formation and compliance

CORE OPERATING PRINCIPLES:
1. **Citation Rigor**: Include DoD-compliant inline citations for every factual statement
2. **Zero Fabrication**: Only use information explicitly provided in source documents
3. **Precision Over Vagueness**: Replace all imprecise language with specific, measurable terms
4. **Competition Integrity**: Ensure fair, unbiased language that promotes maximum competition
5. **FAR Compliance**: Reference appropriate FAR/DFARS clauses with accurate citations

You prioritize clarity, completeness, and legal defensibility in all solicitation documents.
You never make assumptions about requirements, budgets, timelines, or evaluation criteria not explicitly stated in sources.
When information is incomplete, you state what needs to be determined rather than approximating."""
        
        content = self.call_llm(
            prompt,
            max_tokens=4000,
            system_prompt=system_prompt
        )
        
        # Clean content
        content = self._clean_content(content, section_name)
        
        return content
    
    def _analyze_rfp_content(self, content: str, section_type: str) -> Dict:
        """
        Analyze RFP content for compliance and quality
        
        Args:
            content: Generated content
            section_type: Section type
            
        Returns:
            Analysis dictionary
        """
        import re
        
        analysis = {}
        
        # Find compliance items (FAR/DFARS references)
        compliance_patterns = [
            r'FAR\s+\d+\.\d+',  # FAR clauses
            r'DFARS\s+\d+\.\d+',  # DFARS clauses
            r'52\.\d+-\d+',  # FAR clause numbers
            r'252\.\d+-\d+',  # DFARS clause numbers
        ]
        compliance_items = []
        for pattern in compliance_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            compliance_items.extend(matches)
        analysis['compliance_items'] = list(set(compliance_items))
        
        # Find evaluation factors (for Section M)
        if section_type == 'evaluation':
            evaluation_patterns = [
                r'factor',
                r'criterion',
                r'criteria',
                r'weight',
                r'rating',
                r'score'
            ]
            evaluation_factors = []
            for pattern in evaluation_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    evaluation_factors.append(pattern)
            analysis['evaluation_factors'] = evaluation_factors
        else:
            analysis['evaluation_factors'] = []
        
        # Assess clarity (simple heuristic)
        clarity_score = 0
        
        # Check for clear structure
        if re.search(r'\d+\.', content):  # Numbered lists
            clarity_score += 25
        
        # Check for specificity
        if re.search(r'\d+\s+(days?|weeks?|months?|hours?)', content):
            clarity_score += 25
        
        # Check for completeness (reasonable length)
        if len(content.split()) > 200:
            clarity_score += 25
        
        # Check for professionalism (no casual language)
        casual_words = ['pretty', 'kinda', 'gonna', 'wanna']
        if not any(word in content.lower() for word in casual_words):
            clarity_score += 25
        
        analysis['clarity_score'] = clarity_score
        
        return analysis
    
    def _format_project_info(self, project_info: Dict) -> str:
        """Format project info for prompt"""
        lines = []
        for key, value in project_info.items():
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
            'budget': ('Program Budget', 'Budget Allocation'),
            'period_of_performance': ('Performance Period Specification', 'Schedule Requirements'),
            'program_name': ('Program Documentation', 'Program Charter'),
            'solicitation_number': ('Solicitation Documentation', 'RFP Package'),
            'issue_date': ('Schedule', 'Timeline Documentation'),
            'closing_date': ('Schedule', 'Timeline Documentation'),
            'contracting_officer': ('Contracting Authority', 'Point of Contact'),
            'issuing_office': ('Issuing Authority', 'Government Office'),
            'technical_requirements': ('Technical Requirements Document', 'Performance Specifications'),
            'evaluation_criteria': ('Evaluation Plan', 'Source Selection Plan'),
            'small_business_set_aside': ('Small Business Assessment', 'Set-Aside Determination'),
            'place_of_performance': ('Performance Location', 'Site Specification'),
            'security_requirements': ('Security Requirements Document', 'Classification Guide'),
        }

        lines = []
        lines.append("Use these citation formats based on the information type:")
        lines.append("")

        for key, value in project_info.items():
            if key in citation_mapping:
                source_names = citation_mapping[key]
                source_name = source_names[0]  # Use primary name

                # Add date if available
                date_info = project_info.get('issue_date', project_info.get('date', '2025'))

                lines.append(f"- For '{key.replace('_', ' ')}' information: Cite as ({source_name}, {date_info})")

        if not lines:
            lines.append("- General factual claims: (Project Documentation)")
            lines.append("- Budget/cost information: (Program Budget Allocation)")
            lines.append("- Timeline information: (Schedule Requirements)")
            lines.append("- Technical requirements: (Technical Requirements Document)")

        return "\n".join(lines)
    
    def _clean_content(self, content: str, section_name: str) -> str:
        """Remove unwanted headers or formatting"""
        import re
        
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip if it's just the section name as header
            if line.strip().startswith('#') and section_name.lower() in line.lower():
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
