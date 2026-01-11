"""
Performance Work Statement (PWS) Writer Agent
Generates performance-based PWS documents with quality assurance surveillance plans
"""

from pathlib import Path
from typing import Dict, List
from .base_agent import BaseAgent
from backend.rag.retriever import Retriever
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class PWSWriterAgent(BaseAgent):
    """
    PWS Writer Agent: Generates Performance Work Statement documents
    
    Responsibilities:
    - Generate performance-based requirements (measurable outcomes)
    - Define quality assurance surveillance methods
    - Establish performance standards and acceptance criteria
    - Include performance incentives/disincentives where appropriate
    - Focus on WHAT is required, not HOW to do it
    - Ensure alignment with Performance-Based Service Contracting (PBSC) principles
    
    Key Differences from SOO/SOW:
    - PWS = Performance-based (outcomes + quality surveillance)
    - SOO = Outcome-focused (broader objectives)
    - SOW = Task-based (prescriptive methods)
    
    PWS Structure:
    1. Background/Introduction
    2. Scope of Work
    3. Performance Requirements (measurable outcomes)
    4. Performance Standards (quality levels)
    5. Quality Assurance Surveillance Plan (QASP)
    6. Deliverables and Reporting
    7. Period of Performance
    
    Dependencies:
    - RAG system with PWS guidelines and examples
    - Base agent LLM capabilities
    """
    
    def __init__(
        self,
        api_key: str,
        retriever: Retriever,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize PWS writer agent
        
        Args:
            api_key: Anthropic API key
            retriever: RAG Retriever (with PWS guide/examples indexed)
            model: Claude model to use
        """
        super().__init__(
            name="PWSWriterAgent",
            api_key=api_key,
            model=model,
            temperature=0.5  # Balanced for performance standards and compliance
        )
        self.retriever = retriever
    
    def execute(self, task: Dict) -> Dict:
        """
        Execute complete PWS document generation

        Args:
            task: Dictionary with:
                - project_info: Project information
                - config: Optional configuration overrides

        Returns:
            Dictionary with:
                - content: Complete PWS document
                - metadata: Document metadata
                - word_count: Total word count
        """
        project_info = task.get('project_info', {})
        config = task.get('config', {})
        program_name = project_info.get('program_name', 'Unknown')

        # NEW: Cross-reference lookup - Find IGCE and Acquisition Plan
        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for IGCE (budget constraints, labor categories)
                latest_igce = metadata_store.find_latest_document('igce', program_name)
                # Look for Acquisition Plan (timeline, deliverables)
                latest_acq_plan = metadata_store.find_latest_document('acquisition_plan', program_name)

                if latest_igce:
                    print(f"✅ Found IGCE: {latest_igce['id']}")
                    print(f"   Budget: {latest_igce['extracted_data'].get('total_cost_formatted', 'N/A')}")
                    project_info['igce_data'] = latest_igce['extracted_data']
                    project_info['budget_constraint'] = latest_igce['extracted_data'].get('total_cost_formatted', 'TBD')
                    self._igce_reference = latest_igce['id']
                else:
                    print(f"⚠️  No IGCE found for {program_name}")
                    self._igce_reference = None

                if latest_acq_plan:
                    print(f"✅ Found Acquisition Plan: {latest_acq_plan['id']}")
                    project_info['acquisition_plan_data'] = latest_acq_plan['extracted_data']
                    self._acq_plan_reference = latest_acq_plan['id']
                else:
                    print(f"⚠️  No Acquisition Plan found for {program_name}")
                    self._acq_plan_reference = None

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")
                self._igce_reference = None
                self._acq_plan_reference = None
        else:
            self._igce_reference = None
            self._acq_plan_reference = None

        self.log("=" * 80)
        self.log("GENERATING PERFORMANCE WORK STATEMENT (PWS)")
        self.log("=" * 80)

        # Step 1: Extract data from RAG
        print("\nSTEP 1: Extracting PWS data from knowledge base...")
        rag_extracted = self._extract_from_rag(project_info)
        print(f"  ✓ Extracted {len(rag_extracted)} fields from documents")

        # Step 2: Generate narrative sections with LLM
        print("\nSTEP 2: Generating narrative sections with LLM...")
        llm_generated = self._generate_narrative_sections(project_info, rag_extracted)
        print(f"  ✓ Generated {len(llm_generated)} narrative sections")

        # Step 3: Generate smart defaults
        print("\nSTEP 3: Generating smart defaults...")
        smart_defaults = self._generate_smart_defaults(project_info, rag_extracted, config)
        print(f"  ✓ Generated {len(smart_defaults)} smart default values")

        # Step 4: Populate template
        print("\nSTEP 4: Populating PWS template...")
        content = self._populate_template(project_info, rag_extracted, llm_generated, smart_defaults, config)
        word_count = len(content.split())
        print(f"  ✓ Generated {word_count} words")

        # Step 5: Analyze PBSC compliance
        print("\nSTEP 5: Analyzing performance-based compliance...")
        analysis = self._analyze_pws_content(content, 'full_document')
        print(f"  ✓ PBSC Compliance Score: {analysis.get('pbsc_score', 0)}/100")

        self.log("=" * 80)
        self.log("PWS GENERATION COMPLETE")
        self.log("=" * 80)

        # NEW: Save document metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving document metadata for cross-referencing...")
                metadata_store = DocumentMetadataStore()
                extractor = DocumentDataExtractor()

                # Extract structured data from generated PWS
                extracted_data = extractor.extract_pws_data(content)
                extracted_data.update({
                    'performance_metrics': analysis.get('metrics', []),
                    'qasp_elements': analysis.get('qasp_elements', []),
                    'pbsc_compliance': analysis.get('pbsc_score', 0),
                    'service_type': smart_defaults.get('service_type', 'services'),
                    'word_count': word_count
                })

                # Build references dict
                references = {}
                if self._igce_reference:
                    references['igce'] = self._igce_reference
                if self._acq_plan_reference:
                    references['acquisition_plan'] = self._acq_plan_reference

                # Save to metadata store
                doc_id = metadata_store.save_document(
                    doc_type='pws',
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
            'content': content,
            'word_count': word_count,
            'metadata': {
                'program_name': project_info.get('program_name', 'Unknown'),
                'organization': project_info.get('organization', 'DoD'),
                'service_type': smart_defaults.get('service_type', 'services'),
            },
            'performance_metrics': analysis.get('metrics', []),
            'qasp_elements': analysis.get('qasp_elements', []),
            'pbsc_compliance': analysis.get('pbsc_score', 0),
            'rag_extracted_count': len(rag_extracted),
            'llm_generated_count': len(llm_generated),
            'smart_defaults_count': len(smart_defaults)
        }
    
    def _retrieve_pws_guidance(self, section_name: str, focus: str) -> Dict:
        """
        Retrieve PWS guidance from knowledge base
        
        Args:
            section_name: Section name
            focus: Section focus area
            
        Returns:
            Dictionary with PWS guidance and examples
        """
        # Build query for PWS-specific guidance
        query_elements = [
            f"Performance Work Statement {section_name}",
            f"PWS {focus}",
            "performance-based service contracting",
            "quality assurance surveillance",
            "measurable performance standards",
            "acceptance criteria"
        ]
        
        query = " ".join(query_elements)
        
        # Retrieve from RAG
        results = self.retriever.retrieve(
            query=query,
            k=5  # Fixed: use 'k' parameter instead of 'top_k'
        )
        
        return {
            'guidance': results,
            'sources': [r.get('source', 'Unknown') for r in results],
            'focus': focus
        }
    
    def _generate_pws_section(
        self,
        section_name: str,
        project_info: Dict,
        guidance: str,
        pws_guidance: Dict,
        focus: str
    ) -> str:
        """
        Generate PWS section content
        
        Args:
            section_name: Section name
            project_info: Project information
            guidance: User-provided guidance
            pws_guidance: Retrieved PWS guidance
            focus: Section focus
            
        Returns:
            Generated PWS section content
        """
        # Build context from retrieved guidance
        rag_context = self._format_rag_context(pws_guidance['guidance'])
        
        # Build prompt based on section type
        if 'Performance Requirements' in section_name or 'performance' in focus.lower():
            prompt = self._build_performance_requirements_prompt(
                section_name, project_info, guidance, rag_context
            )
        elif 'QASP' in section_name or 'quality' in focus.lower() or 'surveillance' in focus.lower():
            prompt = self._build_qasp_prompt(
                section_name, project_info, guidance, rag_context
            )
        elif 'Standard' in section_name or 'standards' in focus.lower():
            prompt = self._build_standards_prompt(
                section_name, project_info, guidance, rag_context
            )
        else:
            prompt = self._build_general_pws_prompt(
                section_name, project_info, guidance, rag_context
            )
        
        # Generate content
        content = self.call_llm(prompt, max_tokens=2000)
        
        return content.strip()
    
    def _build_performance_requirements_prompt(
        self,
        section_name: str,
        project_info: Dict,
        guidance: str,
        rag_context: str
    ) -> str:
        """Build prompt for Performance Requirements section"""
        
        return f"""You are a government contracting expert writing a Performance Work Statement (PWS) Performance Requirements section.

PROJECT INFORMATION:
{self._format_project_info(project_info)}

USER GUIDANCE:
{guidance}

PWS BEST PRACTICES (from knowledge base):
{rag_context}

SECTION TO WRITE: {section_name}

TASK:
Write the Performance Requirements section following Performance-Based Service Contracting (PBSC) principles.

REQUIREMENTS:
1. Focus on WHAT outcomes are required, not HOW to achieve them
2. Each requirement must be:
   - Measurable (quantifiable metrics)
   - Observable (can be verified)
   - Achievable (realistic given resources)
   - Relevant (tied to mission objectives)
   - Time-bound (specific timeframes)

3. Use this structure for each requirement:
   **Requirement [Number]**: [Clear statement of what is required]
   - **Performance Metric**: [How it will be measured]
   - **Performance Standard**: [Acceptable quality level, e.g., "99.9% uptime"]
   - **Measurement Method**: [How compliance will be verified]
   - **Timeframe**: [When measured, e.g., "monthly", "quarterly"]

4. Include quantifiable metrics such as:
   - Timeliness (response times, delivery schedules)
   - Quality (defect rates, accuracy percentages)
   - Quantity (volume, throughput)
   - Customer satisfaction (survey scores, complaint rates)

5. Avoid prescriptive HOW language like:
   ❌ "The contractor shall use X software"
   ✅ "The contractor shall achieve data accuracy of 99.5%"

EXAMPLE FORMAT:
**Requirement 1: Service Availability**
- **Performance Metric**: System uptime percentage
- **Performance Standard**: 99.9% availability during business hours
- **Measurement Method**: Automated monitoring logs
- **Timeframe**: Measured monthly

LIST FORMATTING (MANDATORY):
- Do NOT include blank lines between bullet list items
- Keep all list items in a continuous block with single newlines
- CORRECT: "- item1\\n- item2\\n- item3"
- WRONG: "- item1\\n\\n- item2\\n\\n- item3"

Write professional, measurable performance requirements. Use markdown formatting."""
    
    def _build_qasp_prompt(
        self,
        section_name: str,
        project_info: Dict,
        guidance: str,
        rag_context: str
    ) -> str:
        """Build prompt for Quality Assurance Surveillance Plan section"""
        
        return f"""You are a government contracting expert writing a Performance Work Statement (PWS) Quality Assurance Surveillance Plan (QASP) section.

PROJECT INFORMATION:
{self._format_project_info(project_info)}

USER GUIDANCE:
{guidance}

PWS BEST PRACTICES (from knowledge base):
{rag_context}

SECTION TO WRITE: {section_name}

TASK:
Write the Quality Assurance Surveillance Plan (QASP) section that defines how performance will be monitored and verified.

QASP REQUIREMENTS:
1. Surveillance Methods:
   - 100% Inspection: All deliverables/services reviewed
   - Random Sampling: Percentage-based sampling
   - Periodic Inspection: Scheduled reviews
   - Customer Feedback: User satisfaction surveys
   - Automated Monitoring: System-generated metrics

2. For each performance requirement, specify:
   - **Surveillance Method**: How performance will be monitored
   - **Frequency**: How often (daily, weekly, monthly, quarterly)
   - **Performance Threshold**: Acceptable quality level
   - **Responsible Party**: Who conducts surveillance (COR, contractor, automated)
   - **Corrective Actions**: What happens if standards not met

3. Include a surveillance table:
   | Performance Requirement | Method | Frequency | Threshold | Responsible |
   |------------------------|--------|-----------|-----------|-------------|
   | [Requirement] | [Method] | [Frequency] | [%/metric] | [Party] |

4. Define corrective action process:
   - Notification procedures
   - Timeframes for correction
   - Escalation process
   - Potential consequences (warnings, deductions, termination)

5. Address performance incentives/disincentives (if applicable):
   - Award fees for exceeding standards
   - Penalties for failing to meet standards

EXAMPLE:
**Surveillance Method 1: Automated Performance Monitoring**
- System uptime will be monitored 24/7 via automated tools
- Monthly reports generated showing availability percentages
- Threshold: 99.9% uptime required
- If uptime falls below 99.5%, contractor must submit root cause analysis within 48 hours

LIST FORMATTING (MANDATORY):
- Do NOT include blank lines between bullet list items
- Keep all list items in a continuous block with single newlines
- CORRECT: "- item1\\n- item2\\n- item3"
- WRONG: "- item1\\n\\n- item2\\n\\n- item3"

Write a comprehensive QASP that ensures effective quality assurance. Use markdown formatting."""
    
    def _build_standards_prompt(
        self,
        section_name: str,
        project_info: Dict,
        guidance: str,
        rag_context: str
    ) -> str:
        """Build prompt for Performance Standards section"""
        
        return f"""You are a government contracting expert writing a Performance Work Statement (PWS) Performance Standards section.

PROJECT INFORMATION:
{self._format_project_info(project_info)}

USER GUIDANCE:
{guidance}

PWS BEST PRACTICES (from knowledge base):
{rag_context}

SECTION TO WRITE: {section_name}

TASK:
Write the Performance Standards section that defines acceptable quality levels and acceptance criteria.

PERFORMANCE STANDARDS REQUIREMENTS:
1. For each performance area, define:
   - **Standard**: Minimum acceptable performance level
   - **Measurement**: How it will be quantified
   - **Acceptance Criteria**: What constitutes acceptable performance
   - **Incentive Level**: (Optional) Exceeds expectations
   - **Unacceptable Level**: Below minimum, triggers corrective action

2. Use quantifiable standards such as:
   - Percentages: "99.9% accuracy", "95% on-time delivery"
   - Time metrics: "Response within 2 hours", "Resolution within 24 hours"
   - Quality metrics: "Zero critical defects", "Customer satisfaction score ≥ 4.5/5"
   - Compliance metrics: "100% regulatory compliance"

3. Structure as a table:
   | Performance Area | Standard | Measurement | Acceptance Criteria |
   |------------------|----------|-------------|---------------------|
   | [Area] | [Threshold] | [Method] | [Criteria] |

4. Define quality levels:
   - **Exceptional**: [Criteria] - Eligible for award fee
   - **Satisfactory**: [Criteria] - Meets all requirements
   - **Marginal**: [Criteria] - Requires improvement plan
   - **Unsatisfactory**: [Criteria] - Subject to remediation/termination

5. Include acceptance procedures:
   - Inspection and acceptance process
   - Government acceptance authority (COR)
   - Timeframe for acceptance/rejection
   - Re-work procedures for rejected deliverables

EXAMPLE:
**Performance Standard 1: Service Response Time**
- **Standard**: 95% of service requests resolved within 4 hours
- **Measurement**: Tracked via ticketing system
- **Acceptance Criteria**: Monthly average ≥ 95%
- **Incentive Level**: ≥ 98% (eligible for performance bonus)
- **Unacceptable**: < 90% (requires corrective action plan)

LIST FORMATTING (MANDATORY):
- Do NOT include blank lines between bullet list items
- Keep all list items in a continuous block with single newlines
- CORRECT: "- item1\\n- item2\\n- item3"
- WRONG: "- item1\\n\\n- item2\\n\\n- item3"

Write clear, measurable performance standards with acceptance criteria. Use markdown formatting."""
    
    def _build_general_pws_prompt(
        self,
        section_name: str,
        project_info: Dict,
        guidance: str,
        rag_context: str
    ) -> str:
        """Build prompt for general PWS sections"""
        
        return f"""You are a government contracting expert writing a Performance Work Statement (PWS) section.

PROJECT INFORMATION:
{self._format_project_info(project_info)}

USER GUIDANCE:
{guidance}

PWS BEST PRACTICES (from knowledge base):
{rag_context}

SECTION TO WRITE: {section_name}

TASK:
Write the {section_name} section following Performance-Based Service Contracting (PBSC) principles.

KEY PWS PRINCIPLES:
1. **Performance-Based**: Focus on measurable outcomes, not methods
2. **Outcome-Oriented**: Define desired results, not processes
3. **Measurable**: Include quantifiable metrics and standards
4. **Flexible**: Allow contractor innovation in approach
5. **Quality-Focused**: Emphasize quality assurance and surveillance

SECTION GUIDELINES:
1. Use clear, professional government contracting language
2. Be specific and measurable where possible
3. Include relevant regulations/standards (FAR, agency-specific)
4. Define roles and responsibilities clearly
5. Specify deliverables, timelines, and acceptance criteria
6. Focus on WHAT is required, not HOW to do it

FORMATTING:
- Use markdown formatting (headers, bullets, tables)
- Use numbered lists for sequential items
- Include subsections where appropriate
- Bold key terms and requirements
- Use tables for structured data

LIST FORMATTING (MANDATORY):
- Do NOT include blank lines between bullet list items
- Keep all list items in a continuous block with single newlines
- CORRECT: "- item1\\n- item2\\n- item3"
- WRONG: "- item1\\n\\n- item2\\n\\n- item3"

Write a comprehensive, performance-based {section_name} section. Use markdown formatting."""
    
    def _format_project_info(self, project_info: Dict) -> str:
        """Format project info for prompt"""
        info_lines = []
        for key, value in project_info.items():
            label = key.replace('_', ' ').title()
            info_lines.append(f"- {label}: {value}")
        return '\n'.join(info_lines)
    
    def _format_rag_context(self, rag_results: List) -> str:
        """Format RAG results for prompt"""
        if not rag_results:
            return "No specific guidance found in knowledge base."
        
        context_parts = []
        for i, result in enumerate(rag_results[:3], 1):
            text = result.get('text', '')
            source = result.get('source', 'Unknown')
            context_parts.append(f"{i}. {text[:500]}... (Source: {source})")
        
        return '\n\n'.join(context_parts)
    
    def _analyze_pws_content(self, content: str, focus: str) -> Dict:
        """
        Analyze PWS content for performance-based elements
        
        Args:
            content: Generated content
            focus: Section focus
            
        Returns:
            Analysis dictionary
        """
        import re
        
        # Extract performance metrics
        metrics = []
        metric_patterns = [
            r'(\d+(?:\.\d+)?%)',  # Percentages
            r'within\s+(\d+)\s+(hours?|days?|weeks?)',  # Time metrics
            r'(?:≥|>=)\s*(\d+(?:\.\d+)?)',  # Greater than thresholds
            r'(?:≤|<=)\s*(\d+(?:\.\d+)?)',  # Less than thresholds
        ]
        for pattern in metric_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            metrics.extend([m if isinstance(m, str) else m[0] for m in matches])
        
        # Extract QASP elements
        qasp_keywords = ['surveillance', 'monitoring', 'inspection', 'verification', 'audit']
        qasp_elements = [kw for kw in qasp_keywords if kw in content.lower()]
        
        # Extract acceptance criteria
        acceptance_patterns = [
            r'Acceptance Criteria:?\s*([^\n]+)',
            r'acceptable\s+(?:if|when)\s+([^\n]+)',
        ]
        acceptance_criteria = []
        for pattern in acceptance_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            acceptance_criteria.extend(matches)
        
        # Calculate PBSC compliance score (basic heuristic)
        pbsc_score = 0
        if len(metrics) > 0:
            pbsc_score += 30
        if len(qasp_elements) > 0:
            pbsc_score += 25
        if len(acceptance_criteria) > 0:
            pbsc_score += 25
        if 'performance' in content.lower():
            pbsc_score += 20
        
        return {
            'metrics': list(set(metrics))[:10],  # Top 10 unique metrics
            'qasp_elements': qasp_elements,
            'acceptance_criteria': acceptance_criteria[:5],
            'pbsc_score': min(100, pbsc_score)
        }

    # ========== Phase 1: RAG Extraction Methods ==========

    def _extract_from_rag(self, project_info: Dict) -> Dict:
        """
        Extract PWS-relevant data from RAG knowledge base

        Args:
            project_info: Project information

        Returns:
            Dictionary of extracted fields
        """
        extracted = {}

        # Build comprehensive query for PWS information
        program_name = project_info.get('program_name', '')
        query = f"{program_name} Performance Work Statement PWS requirements performance standards deliverables quality metrics"

        # Retrieve relevant chunks
        results = self.retriever.retrieve(query=query, k=8)  # Increased from 5 to 8

        if not results:
            return extracted

        # Combine all RAG text - handle both dict and object formats
        import re
        combined_text = "\n".join([
            r.content if hasattr(r, 'content') else r.get('content', '')
            for r in results
        ])

        # 1. Extract service type (ENHANCED)
        service_patterns = [
            (r'IT\s+services?|information technology services?', 'IT services'),
            (r'engineering\s+services?', 'engineering services'),
            (r'logistics\s+(?:support\s+)?services?', 'logistics support services'),
            (r'software\s+development', 'software development services'),
            (r'system\s+(?:integration|development)', 'systems integration services'),
            (r'maintenance\s+(?:and\s+support|services?)', 'maintenance and support services'),
            (r'professional\s+services?', 'professional services'),
        ]
        for pattern, service_name in service_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                extracted['service_type'] = service_name
                break

        # 2. Extract performance metrics/standards
        metric_patterns = [
            r'(\d+(?:\.\d+)?%)\s*(?:availability|uptime|reliability)',  # "99.5% availability"
            r'within\s+(\d+)\s+(hours?|days?|weeks?)\s+(?:of|for)',  # "within 24 hours of"
            r'response\s+time[:\s]+(\d+)\s+(hours?|minutes?)',  # "response time: 2 hours"
            r'(\d+)\s+(?:business|calendar)\s+days?',  # "5 business days"
        ]
        metrics_found = []
        for pattern in metric_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            metrics_found.extend([m if isinstance(m, str) else ' '.join(m) for m in matches])
        
        if metrics_found:
            extracted['performance_metrics'] = metrics_found[:5]  # Top 5 metrics

        # 3. Extract deliverables
        deliverable_patterns = [
            r'deliverable[s]?[:\s]+([^\.]+)',
            r'shall\s+(?:deliver|provide)[:\s]+([^\.]+)',
            r'(?:report|document|plan|specification)[s]?\s+(?:shall|will)',
        ]
        deliverables_found = []
        for pattern in deliverable_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            deliverables_found.extend([m.strip()[:100] for m in matches if len(m.strip()) > 10])
        
        if deliverables_found:
            extracted['deliverables'] = deliverables_found[:5]  # Top 5 deliverables

        # 4. Extract quality standards
        quality_patterns = [
            r'quality\s+(?:standard|requirement|criteria)[:\s]+([^\.]+)',
            r'acceptable\s+(?:if|when)[:\s]+([^\.]+)',
            r'(?:ISO|CMMI|NIST)\s+[\d\.\-]+',  # Standards references
            r'compliance\s+with[:\s]+([^\.]+)',
        ]
        quality_standards = []
        for pattern in quality_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            quality_standards.extend([m if isinstance(m, str) else m.strip()[:100] for m in matches])
        
        if quality_standards:
            extracted['quality_standards'] = quality_standards[:3]  # Top 3 standards

        # 5. Extract performance periods/schedules
        schedule_patterns = [
            r'(\d+)\s*(?:month|year)[s]?\s+(?:period|duration)',  # "36 months period"
            r'period\s+of\s+performance[:\s]+(\d+\s+\w+)',  # "period of performance: 12 months"
            r'base\s+period[:\s]+(\d+\s+\w+)',  # "base period: 12 months"
            r'option\s+period[s]?[:\s]+(\d+\s+\w+)',  # "option periods: 12 months"
        ]
        for pattern in schedule_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                extracted['performance_period'] = match.group(1).strip()
                break

        # 6. Extract personnel/qualification requirements
        personnel_patterns = [
            r'(?:key\s+personnel|KP)[:\s]+([^\.]+)',
            r'(?:clearance|security)[:\s]+([^\.]+)',
            r'(?:certification|qualified|experienced)[:\s]+([^\.]+)',
            r'(?:degree|bachelor|master|PhD)\s+in\s+([^\.]+)',
        ]
        personnel_reqs = []
        for pattern in personnel_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            personnel_reqs.extend([m.strip()[:100] for m in matches if len(str(m).strip()) > 5])
        
        if personnel_reqs:
            extracted['personnel_requirements'] = personnel_reqs[:3]  # Top 3 requirements

        # 7. Extract acceptance criteria
        acceptance_patterns = [
            r'acceptance\s+criteria[:\s]+([^\.]+)',
            r'acceptable\s+(?:when|if)[:\s]+([^\.]+)',
            r'shall\s+be\s+accepted\s+(?:when|if)[:\s]+([^\.]+)',
        ]
        acceptance_criteria = []
        for pattern in acceptance_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            acceptance_criteria.extend([m.strip()[:100] for m in matches if len(m.strip()) > 10])
        
        if acceptance_criteria:
            extracted['acceptance_criteria'] = acceptance_criteria[:3]  # Top 3 criteria

        # 8. Extract surveillance methods (QASP-related)
        surveillance_patterns = [
            r'surveillance\s+method[s]?[:\s]+([^\.]+)',
            r'monitoring[:\s]+([^\.]+)',
            r'inspection\s+(?:method|procedure)[s]?[:\s]+([^\.]+)',
        ]
        surveillance_methods = []
        for pattern in surveillance_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            surveillance_methods.extend([m.strip()[:100] for m in matches if len(m.strip()) > 10])
        
        if surveillance_methods:
            extracted['surveillance_methods'] = surveillance_methods[:3]  # Top 3 methods

        # 9. Extract performance incentives/disincentives
        incentive_patterns = [
            r'incentive[s]?[:\s]+([^\.]+)',
            r'disincentive[s]?[:\s]+([^\.]+)',
            r'(?:bonus|award)\s+fee[:\s]+([^\.]+)',
            r'penalty[:\s]+([^\.]+)',
        ]
        for pattern in incentive_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                extracted['performance_incentives'] = match.group(1).strip()[:100]
                break

        # 10. Extract reporting requirements
        reporting_patterns = [
            r'report(?:ing)?\s+(?:requirement|frequency)[s]?[:\s]+([^\.]+)',
            r'(?:monthly|weekly|quarterly|annual)\s+report[s]?',
            r'shall\s+report[:\s]+([^\.]+)',
        ]
        reporting_reqs = []
        for pattern in reporting_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            reporting_reqs.extend([m if isinstance(m, str) else m.strip()[:100] for m in matches])
        
        if reporting_reqs:
            extracted['reporting_requirements'] = reporting_reqs[:3]  # Top 3 requirements

        return extracted

    def _extract_pws_data_hybrid(self, rag_results: List[Dict], project_info: Dict) -> Dict:
        """
        HYBRID PWS extraction: Enhanced regex + LLM-JSON
        
        Combines your existing enhanced regex patterns with LLM-JSON for complex requirements
        """
        # First run existing enhanced extraction
        regex_data = self._extract_from_rag(project_info) if rag_results else {}
        
        # Then add LLM-JSON for complex requirements
        if len(rag_results) > 0:
            combined_text = "\n".join([
                r.content if hasattr(r, 'content') else r.get('content', '')
                for r in rag_results[:5]
            ])[:7000]  # Limit to prevent token overflow
            
            try:
                prompt = f"""Extract PWS performance requirements from this text and return ONLY valid JSON:

{combined_text}

Return this JSON structure:
{{
  "service_type": "IT services|engineering services|logistics|etc",
  "performance_standards": [
    {{"standard": "99.5% availability", "measurement": "monthly monitoring", "consequence": "service credit"}},
    {{"standard": "2-hour response time", "measurement": "ticket timestamp", "consequence": "escalation"}}
  ],
  "deliverables": [
    {{"name": "Monthly Status Report", "frequency": "monthly", "format": "PDF", "recipients": "CO, COR"}},
    {{"name": "System Documentation", "frequency": "at completion", "format": "electronic", "recipients": "Government"}}
  ],
  "quality_levels": [
    {{"element": "availability", "acceptable": "99%", "target": "99.9%"}},
    {{"element": "defect rate", "acceptable": "5%", "target": "2%"}}
  ],
  "reporting_requirements": [
    {{"report": "Status Report", "frequency": "monthly", "content": "progress and issues"}},
    {{"report": "Metrics Dashboard", "frequency": "weekly", "content": "performance metrics"}}
  ]
}}

Extract actual values from the text. Use empty arrays [] if no data found in a category.
Return ONLY valid JSON, no other text.

JSON:"""
                
                response = self.call_llm(prompt, max_tokens=1500)
                
                # Extract JSON from response
                import json
                import re
                json_match = re.search(r'\{[\s\S]*\}', response.strip())
                
                if json_match:
                    pws_json = json.loads(json_match.group(0))
                    # Merge with regex data (LLM takes precedence)
                    merged = {**regex_data, **pws_json}
                    
                    deliverable_count = len(pws_json.get('deliverables', []))
                    standard_count = len(pws_json.get('performance_standards', []))
                    
                    self.log(f"Hybrid PWS extraction found {deliverable_count} deliverables, {standard_count} performance standards")
                    return merged
                    
            except json.JSONDecodeError as e:
                self.log(f"JSON parsing failed in hybrid PWS extraction: {e}", level="WARNING")
            except Exception as e:
                self.log(f"LLM-based PWS extraction failed: {e}", level="WARNING")
        
        # Fallback to regex-only results
        return regex_data

    # ========== Phase 1: LLM Generation Methods ==========

    def _generate_narrative_sections(self, project_info: Dict, rag_extracted: Dict) -> Dict:
        """
        Generate narrative sections using LLM

        Args:
            project_info: Project information
            rag_extracted: RAG-extracted data

        Returns:
            Dictionary of generated sections
        """
        generated = {}

        # Generate background section
        background = self._generate_background_from_rag(project_info, rag_extracted)
        if background:
            generated['background'] = background

        # Generate scope elements
        scope_elements = self._generate_scope_from_project_info(project_info)
        generated.update(scope_elements)

        return generated

    def _generate_background_from_rag(self, project_info: Dict, rag_extracted: Dict) -> str:
        """
        Generate consolidated background section from RAG context

        Args:
            project_info: Project information
            rag_extracted: RAG-extracted data

        Returns:
            Generated background text
        """
        program_name = project_info.get('program_name', 'the system')
        description = project_info.get('description', '')
        capability_gap = project_info.get('capability_gap', '')

        # Retrieve background context
        query = f"{program_name} background current situation capability gaps strategic importance mission"
        results = self.retriever.retrieve(query=query, k=3)

        # Build RAG context
        rag_text = ""
        for result in results:
            text = result.get('text', '') if isinstance(result, dict) else getattr(result, 'content', '')
            rag_text += text[:400] + " "

        prompt = f"""Based on the program information and context provided, generate a comprehensive background section for a Performance Work Statement (PWS).

Program Name: {program_name}
Description: {description}
Capability Gap: {capability_gap}

Context from similar programs:
{rag_text[:800]}

Generate a 2-3 paragraph background that covers:
1. Current Situation: Describe the existing state, systems, or capabilities
2. Capability Gaps: Identify specific gaps, challenges, or deficiencies
3. Strategic Importance: Explain how this aligns with organizational mission
4. Prior Efforts: Mention any previous contracts or initiatives (if known)

Write in professional government contracting language. Be specific to {program_name}."""

        background = self.call_llm(prompt, max_tokens=500).strip()
        return background

    def _generate_scope_from_project_info(self, project_info: Dict) -> Dict:
        """
        Generate scope section elements from project information

        Args:
            project_info: Project information

        Returns:
            Dictionary with functional_areas, geographic_scope, system_interfaces
        """
        generated = {}

        program_name = project_info.get('program_name', 'the system')
        description = project_info.get('description', '')
        num_locations = project_info.get('num_locations', 0)
        num_users = project_info.get('num_users', 0)

        # Generate functional areas
        prompt_functional = f"""Based on the program information, list 3-5 functional areas for this Performance Work Statement.

Program: {program_name}
Description: {description}

Provide the functional areas as a numbered list in this format:
1. **[Functional Area Name]**: [Brief description]
2. **[Functional Area Name]**: [Brief description]
etc.

Focus on specific service areas relevant to this type of system."""

        functional_areas = self.call_llm(prompt_functional, max_tokens=300).strip()
        generated['functional_areas'] = functional_areas

        # Generate geographic scope
        if num_locations > 0:
            geographic = f"""- {num_locations} installations across CONUS (Continental United States)
- Remote/virtual support as required
- OCONUS (Outside Continental United States) support if mission requirements dictate"""
        else:
            geographic = """- Government facilities as specified in task orders
- Remote/virtual support as required
- CONUS and OCONUS locations as mission requirements dictate"""

        generated['geographic_scope'] = geographic

        # Generate system interfaces
        prompt_systems = f"""Based on the program, list 2-3 key systems that this solution will integrate with.

Program: {program_name}
Description: {description}

Provide as a bulleted list:
- **[System Name]**: [Integration description]
- **[System Name]**: [Integration description]

Use realistic Government/DoD systems relevant to this type of acquisition."""

        system_interfaces = self.call_llm(prompt_systems, max_tokens=200).strip()
        generated['system_interfaces'] = system_interfaces

        return generated

    # ========== Phase 2: Smart Defaults Methods ==========

    def _generate_smart_defaults(self, project_info: Dict, rag_extracted: Dict, config: Dict) -> Dict:
        """
        Generate smart defaults for metadata and structured fields

        Args:
            project_info: Project information
            rag_extracted: RAG-extracted data
            config: Configuration overrides

        Returns:
            Dictionary of smart default values
        """
        from datetime import datetime
        defaults = {}

        # Metadata defaults
        defaults['program_name'] = project_info.get('program_name', 'TBD - Program Name')
        defaults['organization'] = project_info.get('organization', 'Department of Defense')
        defaults['date'] = datetime.now().strftime('%B %d, %Y')
        defaults['author'] = f"Contract Specialist, {defaults['organization']}"
        defaults['approved_by'] = "TBD - To be assigned upon contract award"

        # Service type inference
        defaults['service_type'] = self._infer_service_type(project_info, rag_extracted)

        return defaults

    def _infer_service_type(self, project_info: Dict, rag_extracted: Dict) -> str:
        """
        Infer service type from project information

        Args:
            project_info: Project information
            rag_extracted: RAG-extracted data

        Returns:
            Service type string
        """
        # Check RAG extracted first
        if 'service_type' in rag_extracted:
            return rag_extracted['service_type']

        # Infer from project info
        program_name = project_info.get('program_name', '').lower()
        description = project_info.get('description', '').lower()
        combined = program_name + " " + description

        if any(kw in combined for kw in ['software', 'it', 'information technology', 'system', 'cloud', 'cyber']):
            return 'information technology (IT) services'
        elif any(kw in combined for kw in ['engineering', 'technical', 'design', 'development']):
            return 'engineering and technical services'
        elif any(kw in combined for kw in ['logistics', 'supply', 'inventory', 'maintenance']):
            return 'logistics support services'
        elif any(kw in combined for kw in ['training', 'education', 'instruction']):
            return 'training and education services'
        elif any(kw in combined for kw in ['research', 'analysis', 'study']):
            return 'research and analysis services'
        else:
            return 'professional services'

    # ========== Template Population Method ==========

    def _populate_template(self, project_info: Dict, rag_extracted: Dict,
                          llm_generated: Dict, smart_defaults: Dict, config: Dict) -> str:
        """
        Populate PWS template with priority: config > RAG > LLM > smart defaults

        Args:
            project_info: Project information
            rag_extracted: RAG-extracted data
            llm_generated: LLM-generated content
            smart_defaults: Smart default values
            config: Configuration overrides

        Returns:
            Populated PWS content
        """
        import os

        # Load template
        template_path = Path(__file__).parent.parent / "templates" / "performance_work_statement_template.md"
        with open(template_path, 'r') as f:
            content = f.read()

        def get_value(config_key=None, rag_key=None, llm_key=None, default_key=None, fallback='TBD'):
            """Priority: config > RAG > LLM > smart defaults > fallback"""
            if config_key and config.get(config_key):
                return config.get(config_key)
            if rag_key and rag_extracted.get(rag_key):
                value = rag_extracted.get(rag_key)
                # Handle lists - join or return first item
                if isinstance(value, list):
                    return ', '.join(value) if value else fallback
                return value
            if llm_key and llm_generated.get(llm_key):
                return llm_generated.get(llm_key)
            if default_key and smart_defaults.get(default_key):
                return smart_defaults.get(default_key)
            return fallback

        # Populate template variables (10 total)
        content = content.replace('{{program_name}}',
            get_value(config_key='program_name', default_key='program_name', fallback='TBD'))

        content = content.replace('{{organization}}',
            get_value(config_key='organization', default_key='organization', fallback='TBD'))

        content = content.replace('{{date}}',
            get_value(config_key='date', default_key='date', fallback='TBD'))

        content = content.replace('{{author}}',
            get_value(config_key='author', default_key='author', fallback='TBD'))

        content = content.replace('{{service_type}}',
            get_value(config_key='service_type', rag_key='service_type',
                     default_key='service_type', fallback='professional services'))

        # Scope section placeholders - these are generated by _generate_narrative_sections()
        # and stored in llm_generated dict
        content = content.replace('{{background}}',
            get_value(llm_key='background', fallback='TBD - Background information to be provided'))

        content = content.replace('{{functional_areas}}',
            get_value(llm_key='functional_areas', fallback='TBD - Functional areas to be defined'))

        content = content.replace('{{geographic_scope}}',
            get_value(llm_key='geographic_scope', fallback='TBD - Geographic scope to be defined'))

        content = content.replace('{{system_interfaces}}',
            get_value(llm_key='system_interfaces', fallback='TBD - System interfaces to be defined'))

        content = content.replace('{{performance_metrics}}',
            get_value(rag_key='performance_metrics', fallback='TBD - Define specific performance metrics'))

        content = content.replace('{{deliverables}}',
            get_value(rag_key='deliverables', llm_key='deliverables', fallback='TBD - Define specific deliverables'))

        content = content.replace('{{quality_standards}}',
            get_value(rag_key='quality_standards', fallback='TBD - Define quality standards'))

        content = content.replace('{{acceptance_criteria}}',
            get_value(rag_key='acceptance_criteria', fallback='TBD - Define acceptance criteria'))

        content = content.replace('{{surveillance_methods}}',
            get_value(rag_key='surveillance_methods', fallback='TBD - Define surveillance methods'))

        content = content.replace('{{reporting_requirements}}',
            get_value(rag_key='reporting_requirements', fallback='TBD - Define reporting requirements'))

        content = content.replace('{{approved_by}}',
            get_value(config_key='approved_by', default_key='approved_by', fallback='TBD'))

        return content
