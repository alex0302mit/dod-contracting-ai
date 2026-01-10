"""
Report Writer Agent: Generates report sections using RAG context
Combines research findings with LLM generation capabilities
"""

from typing import Dict, List
from .base_agent import BaseAgent
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class ReportWriterAgent(BaseAgent):
    """
    Report Writer Agent: Generates high-quality report sections
    
    Responsibilities:
    - Generate report sections using research findings
    - Ensure compliance with government contracting standards
    - Include proper citations and references
    - Maintain professional tone and formatting
    - Follow section-specific guidance
    
    Dependencies:
    - Base agent LLM capabilities
    - Research findings from ResearchAgent
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize report writer agent
        
        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        super().__init__(
            name="ReportWriterAgent",
            api_key=api_key,
            model=model,
            temperature=0.7  # Balanced creativity and consistency
        )
    
    def execute(self, task: Dict) -> Dict:
        """
        Execute a writing task

        Args:
            task: Dictionary with:
                - section_name: Name of the section to write
                - section_guidance: Guidance for the section
                - research_findings: Research findings from ResearchAgent
                - project_info: Project information dictionary
                - previous_sections: Previously written sections (for context)

        Returns:
            Dictionary with:
                - content: Generated section content
                - word_count: Word count
                - citations_used: List of citations included
                - quality_notes: Self-assessment notes
        """
        section_name = task.get('section_name', '')
        section_guidance = task.get('section_guidance', '')
        research_findings = task.get('research_findings', {})
        project_info = task.get('project_info', {})
        previous_sections = task.get('previous_sections', {})
        program_name = project_info.get('program_name', 'Unknown')

        self.log(f"Writing section: {section_name}")

        # STEP 0: Cross-reference lookup for related documents
        self._document_references = []

        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Aggregate all relevant documents for the program
                all_program_docs = [doc for doc in metadata_store._documents.values()
                                   if doc['program'] == program_name]

                if all_program_docs:
                    print(f"✅ Found {len(all_program_docs)} related documents")
                    for doc in all_program_docs[:10]:  # Limit to 10 most relevant
                        doc_type = doc['doc_type']
                        print(f"   - {doc_type}: {doc['id']}")
                        self._document_references.append({
                            'type': doc_type,
                            'id': doc['id'],
                            'data': doc['extracted_data']
                        })

                    # Add document summaries to research findings
                    if not research_findings:
                        research_findings = {}
                    research_findings['cross_referenced_docs'] = self._document_references

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")

        # Generate the section content
        content = self._generate_section(
            section_name,
            section_guidance,
            research_findings,
            project_info,
            previous_sections
        )

        # Analyze the generated content
        analysis = self._analyze_content(content, section_name)

        # Store in memory
        self.add_to_memory(f"section_{section_name}", content)

        # STEP 2: Save metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving Report Section metadata...")
                metadata_store = DocumentMetadataStore()

                # Extract Report Section specific data
                extracted_data = {
                    'section_name': section_name,
                    'word_count': len(content.split()),
                    'citations_count': len(analysis.get('citations', [])),
                    'quality_score': analysis.get('quality_score', 0),
                    'document_references_count': len(self._document_references)
                }

                # Track references
                references = {}
                for i, doc_ref in enumerate(self._document_references[:5]):  # Limit to top 5
                    references[f"{doc_ref['type']}_{i+1}"] = doc_ref['id']

                doc_id = metadata_store.save_document(
                    doc_type='report_section',
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
            'word_count': len(content.split()),
            'citations_used': analysis['citations'],
            'quality_notes': analysis['notes'],
            'section_name': section_name
        }
    
    def _generate_section(
        self,
        section_name: str,
        section_guidance: str,
        research_findings: Dict,
        project_info: Dict,
        previous_sections: Dict
    ) -> str:
        """
        Generate content for a report section
        
        Args:
            section_name: Name of the section
            section_guidance: Guidance text for the section
            research_findings: Research findings dictionary
            project_info: Project information
            previous_sections: Previously written sections
            
        Returns:
            Generated section content
        """
        # Extract research findings
        findings_text = research_findings.get('findings', 'No research findings available.')
        sources = research_findings.get('sources', [])
        recommendations = research_findings.get('recommendations', '')
        confidence = research_findings.get('confidence', 'medium')
        
        # Format sources for reference
        sources_text = "\n".join([f"- {src}" for src in sources[:10]]) if sources else "No specific sources"
        
        # Build comprehensive prompt with ENHANCED anti-hallucination and citation requirements
        prompt = f"""You are writing a section for a government market research report. This is a formal document that must meet FAR (Federal Acquisition Regulation) standards.

SECTION TO WRITE: {section_name}

SECTION GUIDANCE:
{section_guidance}

PROJECT INFORMATION:
{self._format_project_info(project_info)}

RESEARCH FINDINGS:
{findings_text}

AVAILABLE SOURCES:
{sources_text}

RESEARCH CONFIDENCE LEVEL: {confidence.upper()}
{f"RECOMMENDATIONS: {recommendations}" if recommendations else ""}

{self._format_previous_sections(previous_sections)}

═══════════════════════════════════════════════════════════════════
CRITICAL ANTI-HALLUCINATION RULES (MANDATORY):
═══════════════════════════════════════════════════════════════════

**GROUND TRUTH CONSTRAINT**:
✓ ONLY use information explicitly stated in:
  - PROJECT INFORMATION (above)
  - RESEARCH FINDINGS (above)
  - AVAILABLE SOURCES (above)

❌ FORBIDDEN ACTIONS - You MUST NOT:
- Invent vendor names, company names, product names, or brand names
- Create statistics, percentages, counts, or metrics not in sources
- Fabricate dates, timelines, deadlines, or milestones
- Assume technical specifications not explicitly stated
- Infer capabilities, features, or requirements not documented
- Generate budget figures not provided in project info
- Create regulatory references (FAR/DFARS) without source citation

═══════════════════════════════════════════════════════════════════
MANDATORY CITATION REQUIREMENTS:
═══════════════════════════════════════════════════════════════════

**EVERY factual claim MUST include an inline DoD-compliant citation.**

Required Citation Formats:
1. Budget/Cost: "...estimated at $X million (Program Budget Allocation, FY2025)"
2. Timeline: "...period of X months (Schedule Requirements, [date])"
3. Vendor Info: "...X vendors identified (Market Research Report, [date])"
4. Technical Specs: "...requirement for [spec] (Technical Requirements Document, [date])"
5. Regulations: "...per FAR 10.001 (Market Research Requirements)"
6. Quantities: "...X units required (Statement of Need, [date])"
7. Small Business: "...set-aside determination (Small Business Assessment, [date])"

**Minimum Citation Density**: At least 4-6 citations per section (one every 50-75 words)

**Citation Style Examples**:
✓ CORRECT: "Market research identified 12 qualified vendors capable of meeting the technical requirements (Market Research Report, March 2025)."
✓ CORRECT: "The estimated contract value is $2.5 million over a 36-month period of performance (Program Budget, FY2025)."
✓ CORRECT: "Per FAR 10.001, agencies shall conduct market research to determine if commercial sources can meet requirements."

❌ WRONG: "Several vendors were identified through market research."
❌ WRONG: "The contract is expected to cost approximately $2-3 million."
❌ WRONG: "Research shows that many companies provide similar services."

═══════════════════════════════════════════════════════════════════
ELIMINATE VAGUE LANGUAGE:
═══════════════════════════════════════════════════════════════════

**Replace ALL vague terms with specific, cited facts:**

❌ FORBIDDEN WORDS (must replace with specifics):
- "several" / "many" / "some" / "few" / "various" / "numerous"
- "approximately" / "around" / "roughly" (unless citing an estimate)
- "significant" / "substantial" / "considerable" / "adequate"
- "recent" / "upcoming" / "soon" (specify dates)
- "major" / "minor" / "important" / "critical" (without context)
- "may" / "might" / "could" / "possibly" / "potentially" (unless hedging is required)

✓ CORRECT REPLACEMENTS:
- "several vendors" → "5 vendors (Market Research, March 2025)"
- "approximately $2M" → "$2.1 million estimated cost (Budget Document, FY2025)"
- "significant improvements" → "40% reduction in processing time (Performance Requirements, 2025)"
- "recent market analysis" → "market analysis conducted in Q1 FY2025 (Market Research Report, March 15, 2025)"

**If specific data unavailable**, use this format:
- "The number of qualified vendors will be determined during the formal market research phase (Q2 FY2025)."
- "Specific technical requirements are being finalized by the program office (estimated completion: April 2025)."

═══════════════════════════════════════════════════════════════════
ADDITIONAL REQUIREMENTS:
═══════════════════════════════════════════════════════════════════

1. **Neutral Language**: Never favor specific vendors or show bias
2. **Professional Tone**: Government contracting terminology throughout
3. **Substantive Content**: Write 3-5 paragraphs (minimum 250 words)
4. **Verifiable Facts**: Every claim must trace back to provided sources
5. **No Section Headers**: Provide paragraph content only (no title/heading)
6. **FAR Compliance**: Reference applicable FAR/DFARS clauses with citations

═══════════════════════════════════════════════════════════════════
VERIFICATION CHECKLIST (Before finalizing):
═══════════════════════════════════════════════════════════════════
☐ Every number has a citation
☐ Every date has a citation
☐ Every vendor/count reference has a citation
☐ No vague words (several, many, some, approximately, etc.)
☐ No fabricated vendor names or company names
☐ All technical specs traced to source documents
☐ Minimum 4-6 citations included
☐ No unsupported claims

Generate the section content now, adhering strictly to all requirements above:
"""
        
        self.log("Generating section content with LLM...")
        
        # Generate content
        content = self.call_llm(
            prompt,
            max_tokens=3000,
            system_prompt="""You are an expert government contracting professional writing market research reports with extensive FAR/DFARS compliance experience.

CORE PRINCIPLES:
1. **Absolute Accuracy**: Only state facts explicitly provided in source materials
2. **Comprehensive Citations**: Include DoD-compliant inline citations for EVERY factual claim
3. **Zero Hallucination**: Never invent names, numbers, dates, specifications, or capabilities
4. **Eliminate Vagueness**: Replace all imprecise language with specific, quantified facts
5. **Source Traceability**: Every statement must be traceable to provided documents

You are meticulous about citation standards and never make assumptions beyond what sources explicitly state.
You prioritize verifiability and precision over elaboration.
When data is unavailable, you explicitly state what needs to be determined rather than approximating."""
        )
        
        # Clean up the content
        content = self._clean_generated_content(content, section_name)
        
        self.log(f"Generated {len(content.split())} words for {section_name}")
        
        return content
    
    def _clean_generated_content(self, content: str, section_name: str) -> str:
        """
        Clean up generated content to remove unwanted elements
        
        Args:
            content: Raw generated content
            section_name: Name of the section
            
        Returns:
            Cleaned content
        """
        import re
        
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip lines that are just the section title as a header
            if line.strip().startswith('#'):
                # Check if it's the section name
                if section_name.lower() in line.lower():
                    continue
            
            # Skip lines that repeat "SECTION:" labels
            if line.strip().upper().startswith('SECTION:'):
                continue
            
            cleaned_lines.append(line)
        
        content = '\n'.join(cleaned_lines).strip()
        
        # Remove excessive blank lines
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        return content
    
    def _analyze_content(self, content: str, section_name: str) -> Dict:
        """
        Analyze generated content for quality indicators
        
        Args:
            content: Generated content
            section_name: Section name
            
        Returns:
            Analysis dictionary
        """
        import re
        
        # Find citations
        citation_patterns = [
            r'Per\s+[A-Z]+',
            r'According to\s+[\w\s]+dated',
            r'Reference\s+#?\d+',
            r'dated\s+\w+\s+\d+,?\s+\d{4}',
            r'\(Ref\.',
        ]
        
        citations = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            citations.extend(matches)
        
        # Check for vague language (potential issues)
        vague_words = ['several', 'many', 'some', 'various', 'numerous']
        vague_found = []
        for word in vague_words:
            if re.search(rf'\b{word}\b', content, re.IGNORECASE):
                vague_found.append(word)
        
        # Quality notes
        notes = []
        
        word_count = len(content.split())
        if word_count < 200:
            notes.append(f"Section may be too brief ({word_count} words)")
        
        if not citations:
            notes.append("No citations detected - may need more source references")
        
        if vague_found:
            notes.append(f"Contains vague language: {', '.join(vague_found)}")
        
        if not notes:
            notes.append("Content meets quality standards")
        
        return {
            'citations': citations,
            'vague_language': vague_found,
            'word_count': word_count,
            'notes': notes
        }
    
    def _format_project_info(self, project_info: Dict) -> str:
        """Format project information for prompt"""
        lines = []
        for key, value in project_info.items():
            formatted_key = key.replace('_', ' ').title()
            lines.append(f"- {formatted_key}: {value}")
        return "\n".join(lines)
    
    def _format_previous_sections(self, previous_sections: Dict) -> str:
        """Format previously written sections for context"""
        if not previous_sections:
            return ""
        
        formatted = ["PREVIOUSLY WRITTEN SECTIONS (for context and consistency):"]
        for section_name, content in previous_sections.items():
            # Include only first 200 words for context
            words = content.split()[:200]
            preview = " ".join(words) + ("..." if len(content.split()) > 200 else "")
            formatted.append(f"\n## {section_name}\n{preview}\n")
        
        return "\n".join(formatted)
    
    def write_full_report(
        self,
        sections_config: List[Dict],
        research_results: Dict,
        project_info: Dict
    ) -> Dict:
        """
        Write all sections of a report
        
        Args:
            sections_config: List of section configurations with name and guidance
            research_results: Dictionary of research results by section
            project_info: Project information
            
        Returns:
            Dictionary with all generated sections
        """
        self.log("Starting full report generation...")
        
        all_sections = {}
        previous_sections = {}
        
        for section_config in sections_config:
            section_name = section_config['name']
            section_guidance = section_config['guidance']
            
            # Get research findings for this section
            research_findings = research_results.get(section_name, {})
            
            # Write section
            task = {
                'section_name': section_name,
                'section_guidance': section_guidance,
                'research_findings': research_findings,
                'project_info': project_info,
                'previous_sections': previous_sections
            }
            
            result = self.execute(task)
            
            # Store section
            all_sections[section_name] = result
            previous_sections[section_name] = result['content']
            
            self.log(f"✓ Completed: {section_name} ({result['word_count']} words)")
        
        self.log(f"Full report generation complete: {len(all_sections)} sections")
        
        return all_sections
