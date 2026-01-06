"""
Statement of Objectives (SOO) Writer Agent
Generates outcome-focused SOO documents using RAG
"""

from typing import Dict, List
from .base_agent import BaseAgent
from backend.rag.retriever import Retriever
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class SOOWriterAgent(BaseAgent):
    """
    SOO Writer Agent: Generates Statement of Objectives documents
    
    Responsibilities:
    - Generate outcome-focused objectives (not prescriptive tasks)
    - Focus on measurable results and performance standards
    - Use RAG to reference SOO best practices and examples
    - Ensure objectives are SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
    - Maintain performance-based acquisition principles
    
    Key Differences from SOW Writer:
    - Less prescriptive (WHAT not HOW)
    - More focus on performance metrics
    - Outcome-oriented language
    - Flexibility for contractor methods
    """
    
    def __init__(
        self,
        api_key: str,
        retriever: Retriever,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize SOO writer agent
        
        Args:
            api_key: Anthropic API key
            retriever: RAG Retriever (with SOO guide/examples indexed)
            model: Claude model to use
        """
        super().__init__(
            name="SOOWriterAgent",
            api_key=api_key,
            model=model,
            temperature=0.5  # Balanced for outcomes and compliance
        )
        self.retriever = retriever
    
    def execute(self, task: Dict) -> Dict:
        """
        Execute SOO section generation
        
        Args:
            task: Dictionary with:
                - section_name: SOO section name
                - project_info: Project information
                - guidance: Section guidance
                - focus: Section focus (outcomes, performance, etc.)
                
        Returns:
            Dictionary with:
                - content: Generated SOO section
                - objectives_count: Number of objectives stated
                - performance_metrics: List of metrics identified
        """
        section_name = task.get('section_name', '')
        project_info = task.get('project_info', {})
        guidance = task.get('guidance', '')
        focus = task.get('focus', 'general')
        program_name = project_info.get('program_name', 'Unknown')

        # NEW: Cross-reference lookup (one-time per program)
        if program_name != 'Unknown' and not hasattr(self, '_cross_refs_loaded'):
            try:
                print(f"\n🔍 Looking up cross-referenced documents for {program_name}...")
                metadata_store = DocumentMetadataStore()
                latest_igce = metadata_store.find_latest_document('igce', program_name)
                latest_acq_plan = metadata_store.find_latest_document('acquisition_plan', program_name)

                if latest_igce:
                    project_info['igce_data'] = latest_igce['extracted_data']
                    self._igce_reference = latest_igce['id']
                else:
                    self._igce_reference = None

                if latest_acq_plan:
                    project_info['acquisition_plan_data'] = latest_acq_plan['extracted_data']
                    self._acq_plan_reference = latest_acq_plan['id']
                else:
                    self._acq_plan_reference = None

                self._cross_refs_loaded = True
            except Exception as e:
                self._igce_reference = None
                self._acq_plan_reference = None
                self._cross_refs_loaded = True

        self.log(f"Writing SOO section: {section_name}")
        
        # Step 1: Retrieve SOO guidance from knowledge base
        self.log("Retrieving SOO best practices...")
        soo_guidance = self._retrieve_soo_guidance(section_name, focus)
        
        # Step 2: Generate SOO section
        content = self._generate_soo_section(
            section_name,
            project_info,
            guidance,
            soo_guidance,
            focus
        )
        
        # Step 3: Analyze content
        analysis = self._analyze_soo_content(content, focus)
        
        self.log(f"Generated {len(content.split())} words for {section_name}")
        
        return {
            'content': content,
            'section_name': section_name,
            'word_count': len(content.split()),
            'objectives_count': analysis.get('objectives_count', 0),
            'performance_metrics': analysis.get('metrics', []),
            'smart_compliance': analysis.get('smart_score', 0)
        }
    
    def _retrieve_soo_guidance(self, section_name: str, focus: str) -> str:
        """
        Retrieve relevant SOO guidance from knowledge base
        
        Args:
            section_name: Name of SOO section
            focus: Focus area (outcomes, performance, etc.)
            
        Returns:
            Retrieved guidance text
        """
        # Build retrieval query
        query = f"Statement of Objectives {section_name} {focus} best practices performance-based acquisition"
        
        # Retrieve relevant chunks
        documents = self.retriever.retrieve(query, k=5)
        
        if not documents:
            return "No SOO guidance found. Use performance-based acquisition principles."
        
        # Format guidance
        guidance_parts = []
        for doc in documents:
            guidance_parts.append(f"[{doc['metadata']['source']}]\n{doc['content']}")
        
        return "\n\n---\n\n".join(guidance_parts)
    
    def _generate_soo_section(
        self,
        section_name: str,
        project_info: Dict,
        guidance: str,
        soo_guidance: str,
        focus: str
    ) -> str:
        """
        Generate SOO section content
        
        Args:
            section_name: Section name
            project_info: Project information
            guidance: Section guidance
            soo_guidance: Retrieved SOO best practices
            focus: Section focus
            
        Returns:
            Generated section content
        """
        # Build specialized prompt based on focus
        focus_instructions = {
            'outcomes': """Focus on WHAT needs to be achieved, not HOW.
- State clear, measurable objectives
- Use outcome-oriented language
- Avoid prescriptive methods
- Prioritize objectives (primary, secondary, tertiary)""",
            
            'performance': """Define measurable performance standards:
- Specify Key Performance Indicators (KPIs)
- Define Service Level Agreements (SLAs)
- Include quantitative metrics
- State acceptance criteria""",
            
            'scope': """Define boundaries clearly:
- What IS included
- What IS NOT included
- System/geographic boundaries
- Flexibility for contractor approach""",
            
            'constraints': """Identify limitations without being prescriptive:
- Technical/security requirements
- Regulatory compliance
- Schedule/budget constraints
- Government-mandated standards"""
        }
        
        focus_instruction = focus_instructions.get(focus, "Write clear, outcome-focused content.")

        # Build citation reference guide
        citation_guide = self._build_citation_guide(project_info)

        # Create comprehensive prompt with MANDATORY CITATIONS
        prompt = f"""You are writing a Statement of Objectives (SOO) for a government contract.

**CRITICAL**: SOOs are OUTCOME-FOCUSED, not prescriptive:
- Focus on WHAT results are needed, not HOW to achieve them
- Use performance-based language
- Allow contractor flexibility in methods
- Emphasize measurable outcomes
- **MANDATORY**: Cite ALL factual claims inline

SECTION: {section_name}

SECTION GUIDANCE:
{guidance}

FOCUS FOR THIS SECTION:
{focus_instruction}

PROJECT INFORMATION (Ground Truth - Use ONLY This):
{self._format_project_info(project_info)}

CITATION GUIDE (Use these exact references):
{citation_guide}

SOO BEST PRACTICES (from knowledge base):
{soo_guidance}

**WRITING REQUIREMENTS**:
1. Use SMART objectives (Specific, Measurable, Achievable, Relevant, Time-bound)
2. State performance standards, not procedures
3. Include measurable success criteria
4. Avoid prescriptive "how-to" language
5. Use outcome verbs: "achieve," "deliver," "demonstrate," "improve"
6. NOT task verbs: "perform," "conduct," "execute," "implement"
7. Write 2-4 substantive paragraphs
8. Professional government acquisition tone
9. **MANDATORY**: Include inline citations after EVERY factual statement

**MANDATORY CITATION REQUIREMENTS**:
1. **Every factual claim MUST have a DoD-compliant inline citation**
2. **Target citation density**: Minimum 5-7 citations per section (one every 40-60 words)

Citation formats by information type:
   - Objectives: "...achieve [outcome] (Program Objectives, [date])" or "(Mission Requirements, [date])"
   - Performance Standards: "...meet [metric] standard (Performance Standards, [date])" or "(Service Level Agreement, [date])"
   - KPIs/Metrics: "...measured by [metric] (Key Performance Indicators, [date])"
   - Timeline: "...within X months from award (Schedule Requirements, [date])"
   - Budget: "...estimated at $X million (Program Budget Allocation, FY2025)"
   - Outcomes: "...deliver [result] (Desired Outcomes, [date])"
   - Success Criteria: "...demonstrate [criteria] (Success Metrics, [date])"
   - Constraints: "...comply with [requirement] (Regulatory Requirements, [date])"

3. **Minimum citation requirements per section type**:
   - Outcomes sections: Cite all objectives, outcomes, and success criteria
   - Performance sections: Cite all KPIs, SLAs, metrics, and measurement methods
   - Scope sections: Cite boundaries, inclusions, exclusions, and constraints
   - Constraints sections: Cite all regulatory, technical, and schedule requirements

4. **Enhanced citation examples**:
   ✓ CORRECT: "The contractor shall achieve a cloud-based inventory tracking capability with real-time data synchronization across 15 DoD installations (Program Objectives, March 2025; Technical Requirements, v2.1)."
   ✓ CORRECT: "System availability shall be measured at 99.9% uptime during operational hours, excluding scheduled maintenance windows (Performance Standards, April 2025; Service Level Agreement, Section 3.2)."
   ✓ CORRECT: "The contractor shall demonstrate reduced inventory discrepancies from baseline 8% to target 2% within the 24-month performance period (Success Criteria, FY2025)."
   ✓ CORRECT: "All systems shall comply with NIST SP 800-171 security requirements and achieve Authority to Operate (ATO) within 180 days (Security Requirements, February 2025)."

   ❌ WRONG: "The contractor shall achieve cloud-based inventory tracking."
   ❌ WRONG: "Performance shall meet high availability standards."
   ❌ WRONG: "The system should reduce inventory discrepancies significantly."
   ❌ WRONG: "Compliance with security requirements is expected."

**ELIMINATE VAGUE LANGUAGE**:
Replace ALL imprecise terms with specific, outcome-focused, measurable criteria:

❌ FORBIDDEN VAGUE TERMS:
- "several" / "many" / "some" / "various" / "multiple" (specify exact numbers)
- "high quality" / "best effort" / "world-class" / "optimal" (define measurable standards)
- "approximately" / "around" / "roughly" (use exact numbers or official estimates)
- "significant" / "substantial" / "considerable" (quantify the improvement/change)
- "timely" / "prompt" / "rapid" / "quick" (specify exact timeframes)
- "adequate" / "sufficient" / "appropriate" / "reasonable" (define objective criteria)
- "improve" / "enhance" / "optimize" (specify baseline, target, and metric)

✓ CORRECT OUTCOME-FOCUSED REPLACEMENTS:
- "improve performance" → "achieve 99.5% system availability, up from current 95% baseline (Performance Standards, 2025)"
- "several installations" → "15 DoD installations as listed in Annex A (Site List, March 2025)"
- "high quality data" → "data accuracy rate of 99.8% or higher (Quality Standards, v1.2)"
- "timely response" → "response time under 500ms for 95% of queries (Performance Requirements, 2025)"
- "significant cost savings" → "achieve 20% reduction in operational costs from FY2024 baseline (Cost Objectives, FY2025)"
- "adequate security" → "comply with NIST SP 800-171 and maintain continuous ATO (Security Requirements, 2025)"

**If specific data is unavailable**, use outcome-focused placeholder language:
- "The specific performance thresholds will be finalized during the Source Selection process (completion: Q2 FY2025)."
- "Success metrics are under development by the program office in coordination with end users (draft: April 2025)."
- "Objective measures for user satisfaction will be defined in the Quality Assurance Surveillance Plan (QASP)."

**CRITICAL ANTI-HALLUCINATION RULES FOR SOO**:
❌ Do NOT invent:
- Objectives or outcomes not stated in program documentation
- Performance metrics, KPIs, or SLAs not specified in sources
- Success criteria or acceptance thresholds not documented
- Baseline measurements or target improvements without data
- Compliance requirements beyond what sources specify
- Timelines or milestones not provided in schedule documents

✓ DO use:
- Only objectives explicitly stated in program/mission documents
- Exact performance standards and metrics from specifications
- Measurable outcomes with quantified targets from sources
- Outcome-focused language (achieve, deliver, demonstrate)
- Flexible language that allows contractor innovation in methods

**OUTCOME-FOCUSED LANGUAGE GUIDE**:
Use these outcome verbs (WHAT to achieve):
✓ "achieve" / "deliver" / "demonstrate" / "attain" / "produce" / "result in" / "enable"

Avoid these task verbs (HOW to do it):
❌ "perform" / "conduct" / "execute" / "implement" / "create" / "develop" / "establish"

**VERIFICATION CHECKLIST**:
☐ 5-7+ citations included (check density)
☐ All objectives cited with measurable outcomes
☐ All performance metrics cited with specific thresholds
☐ No vague terms (several, high quality, timely, etc.)
☐ All improvements quantified (baseline → target)
☐ No prescriptive "how-to" language (outcome-focused only)
☐ No fabricated metrics or objectives
☐ SMART criteria met (Specific, Measurable, Achievable, Relevant, Time-bound)

Generate the {section_name} content WITH MANDATORY INLINE CITATIONS using outcome-focused language:
"""
        
        self.log("Generating SOO content with LLM...")
        
        content = self.call_llm(
            prompt,
            max_tokens=3000,
            system_prompt="""You are a senior acquisition specialist with extensive experience in performance-based acquisition (PBA) and Statement of Objectives (SOO) development for DoD programs.

EXPERTISE AREAS:
- Performance-based acquisition per FAR Part 37.6
- Outcome-focused requirement definition vs. task-based specifications
- SMART objectives development (Specific, Measurable, Achievable, Relevant, Time-bound)
- Key Performance Indicators (KPIs) and Service Level Agreements (SLAs)
- Quality Assurance Surveillance Plans (QASP)
- Measurable performance standards and acceptance criteria

CORE SOO PHILOSOPHY:
SOOs define WHAT outcomes are needed, NOT HOW to achieve them:
- Focus on desired results and performance standards
- Allow contractor flexibility and innovation in methods
- Emphasize measurable outcomes over prescriptive tasks
- Enable best-value source selection based on proposed approaches

CORE OPERATING PRINCIPLES:
1. **Comprehensive Citations**: Include DoD-compliant inline citations for EVERY objective, metric, outcome, and requirement (minimum 5-7 per section)
2. **Measurable Outcomes**: Define all objectives with quantifiable success criteria (baseline → target)
3. **Outcome Language**: Use "achieve/deliver/demonstrate" not "perform/conduct/execute"
4. **Zero Ambiguity**: Replace ALL vague terms (several, timely, adequate) with specific, measurable criteria
5. **Source Fidelity**: Only include objectives, KPIs, and outcomes explicitly stated in program documents
6. **SMART Compliance**: Every objective must be Specific, Measurable, Achievable, Relevant, and Time-bound

MANDATORY STANDARDS:
- Use outcome-focused verbs (achieve, deliver, demonstrate, attain, enable)
- Cite every objective, performance standard, metric, and timeline
- Quantify all improvements with baseline and target metrics
- Never prescribe methods or technical approaches (unless mandatory constraints)
- Never fabricate objectives, KPIs, baselines, or targets not in sources
- Replace vague language with specific, measurable, outcome-focused criteria

You prioritize measurability, outcome focus, and contractor flexibility while maintaining clear accountability.
When information is incomplete, you explicitly state what metrics need to be defined rather than using vague placeholders."""
        )
        
        # Clean content
        content = self._clean_content(content, section_name)
        
        return content
    
    def _analyze_soo_content(self, content: str, focus: str) -> Dict:
        """
        Analyze SOO content for compliance and quality
        
        Args:
            content: Generated content
            focus: Section focus
            
        Returns:
            Analysis dictionary
        """
        import re
        
        analysis = {}
        
        # Count objectives (look for numbered lists or bullet points)
        objectives = re.findall(r'(?:^|\n)\s*[-•\d]+\.?\s+[A-Z]', content)
        analysis['objectives_count'] = len(objectives)
        
        # Find performance metrics
        metric_patterns = [
            r'\d+%',  # Percentages
            r'\d+\s*hours?',  # Time
            r'within\s+\d+\s+\w+',  # Timeframes
            r'(?:SLA|KPI|metric)',  # Direct mentions
        ]
        metrics = []
        for pattern in metric_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            metrics.extend(matches)
        analysis['metrics'] = list(set(metrics))
        
        # Check SMART compliance (simple heuristic)
        smart_score = 0
        if re.search(r'\d+', content):  # Specific numbers
            smart_score += 20
        if analysis['metrics']:  # Measurable
            smart_score += 20
        if len(content.split()) > 150:  # Sufficient detail (Achievable)
            smart_score += 20
        if any(word in content.lower() for word in ['mission', 'objective', 'goal', 'outcome']):  # Relevant
            smart_score += 20
        if any(word in content.lower() for word in ['month', 'year', 'quarter', 'date', 'deadline']):  # Time-bound
            smart_score += 20
        
        analysis['smart_score'] = smart_score
        
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
            'program_name': ('Program Objectives', 'Program Charter'),
            'objectives': ('Program Objectives', 'Mission Requirements'),
            'performance_standards': ('Performance Standards', 'Service Level Agreements'),
            'kpis': ('Key Performance Indicators', 'Metrics Framework'),
            'budget': ('Program Budget', 'Budget Allocation'),
            'period_of_performance': ('Schedule Requirements', 'Timeline Specification'),
            'technical_requirements': ('Technical Requirements', 'Performance Specifications'),
            'outcomes': ('Desired Outcomes', 'Program Goals'),
            'constraints': ('Constraints Documentation', 'Regulatory Requirements'),
            'success_criteria': ('Success Criteria', 'Acceptance Standards'),
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
            lines.append("- Objectives: (Program Objectives, 2025)")
            lines.append("- Performance standards: (Performance Standards, 2025)")
            lines.append("- Budget/cost: (Program Budget, 2025)")
            lines.append("- Timeline: (Schedule Requirements, 2025)")

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
