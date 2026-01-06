"""
Refinement Agent: Iteratively improves content based on Quality Agent feedback
Implements Generate → Evaluate → Fix → Re-evaluate loop
"""

from typing import Dict, List, Optional
from .base_agent import BaseAgent
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class RefinementAgent(BaseAgent):
    """
    Refinement Agent: Improves content based on quality feedback

    Responsibilities:
    - Analyze quality evaluation results
    - Generate targeted improvements based on specific issues
    - Apply fixes for vague language, missing citations, and hallucinations
    - Preserve good content while fixing issues
    - Track improvement metrics across iterations

    Key Features:
    - Issue-specific refinement strategies
    - Iterative improvement with convergence detection
    - Preserves document structure and context
    - Targeted fixes rather than complete regeneration
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize refinement agent

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        super().__init__(
            name="RefinementAgent",
            api_key=api_key,
            model=model,
            temperature=0.3  # Low temperature for precise fixes
        )

    def execute(self, task: Dict) -> Dict:
        """
        Execute refinement task based on quality feedback

        Args:
            task: Dictionary with:
                - content: Original content to refine
                - section_name: Section name
                - evaluation: Quality evaluation results
                - project_info: Project information (for fact checking)
                - research_findings: Research findings (for citations)
                - iteration: Current iteration number

        Returns:
            Dictionary with:
                - refined_content: Improved content
                - changes_made: List of changes applied
                - improvement_summary: Description of improvements
                - confidence: Confidence in improvements (0-100)
        """
        content = task.get('content', '')
        section_name = task.get('section_name', 'Unknown')
        evaluation = task.get('evaluation', {})
        project_info = task.get('project_info', {})
        research_findings = task.get('research_findings', {})
        iteration = task.get('iteration', 1)
        program_name = project_info.get('program_name', 'Unknown')

        self.log(f"Refining: {section_name} (Iteration {iteration})")
        self.log(f"Current score: {evaluation.get('score', 0)}/100")

        # STEP 0: Cross-reference lookup for context and fact-checking
        self._document_references = []
        self._quality_assessment_reference = None

        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up documents for refinement context...")
                metadata_store = DocumentMetadataStore()

                # Get all program documents for fact-checking
                all_program_docs = [doc for doc in metadata_store._documents.values()
                                   if doc['program'] == program_name]

                if all_program_docs:
                    print(f"✅ Found {len(all_program_docs)} documents for context")
                    self._document_references = all_program_docs

                    # Add to research findings for accurate refinements
                    if not research_findings:
                        research_findings = {}
                    research_findings['reference_documents'] = [
                        {'type': doc['doc_type'], 'id': doc['id'], 'data': doc['extracted_data']}
                        for doc in all_program_docs
                    ]

                # Look for related quality assessment
                quality_assessments = [doc for doc in metadata_store._documents.values()
                                      if doc['program'] == program_name and doc['doc_type'] == 'quality_assessment']
                if quality_assessments:
                    latest_qa = max(quality_assessments, key=lambda x: x['timestamp'])
                    print(f"✅ Found Quality Assessment: {latest_qa['id']}")
                    self._quality_assessment_reference = latest_qa['id']

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")

        # Analyze issues
        issues = evaluation.get('issues', [])
        suggestions = evaluation.get('suggestions', [])
        detailed_checks = evaluation.get('detailed_checks', {})

        # Build targeted refinement strategy
        refinement_strategy = self._build_refinement_strategy(
            evaluation,
            detailed_checks
        )

        # Apply refinements
        refined_content = self._apply_refinements(
            content,
            refinement_strategy,
            issues,
            suggestions,
            project_info,
            research_findings,
            section_name
        )

        # Analyze changes
        changes_made = self._analyze_changes(content, refined_content)

        result = {
            'refined_content': refined_content,
            'changes_made': changes_made,
            'improvement_summary': self._summarize_improvements(refinement_strategy),
            'confidence': self._calculate_confidence(refinement_strategy, changes_made)
        }

        self.log(f"Refinement complete: {len(changes_made)} changes made")

        # STEP 2: Save refinement metadata
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving Refinement metadata...")
                metadata_store = DocumentMetadataStore()

                # Extract Refinement specific data
                extracted_data = {
                    'refined_section': section_name,
                    'iteration': iteration,
                    'changes_count': len(changes_made),
                    'original_score': evaluation.get('score', 0),
                    'confidence': self._calculate_confidence(refinement_strategy, changes_made),
                    'issues_addressed': len(issues),
                    'documents_referenced': len(self._document_references)
                }

                # Track references
                references = {}
                if self._quality_assessment_reference:
                    references['quality_assessment'] = self._quality_assessment_reference
                for i, doc in enumerate(self._document_references[:5]):  # Limit to top 5
                    references[f"reference_{doc['doc_type']}_{i+1}"] = doc['id']

                doc_id = metadata_store.save_document(
                    doc_type='refinement',
                    program=program_name,
                    content=refined_content,
                    file_path=None,
                    extracted_data=extracted_data,
                    references=references
                )

                print(f"✅ Metadata saved: {doc_id}")

            except Exception as e:
                print(f"⚠️  Failed to save metadata: {str(e)}")

        return result

    def _build_refinement_strategy(
        self,
        evaluation: Dict,
        detailed_checks: Dict
    ) -> Dict:
        """
        Build targeted refinement strategy based on evaluation

        Args:
            evaluation: Overall evaluation results
            detailed_checks: Detailed check results by category

        Returns:
            Dictionary with refinement priorities and actions
        """
        strategy = {
            'priorities': [],
            'actions': [],
            'focus_areas': []
        }

        # Analyze each check category
        if 'hallucination' in detailed_checks:
            hallucination_check = detailed_checks['hallucination']
            if hallucination_check['score'] < 70:
                strategy['priorities'].append('hallucination')
                strategy['actions'].append('verify_facts')
                strategy['focus_areas'].append('Ground all claims in source documents')

        if 'vague_language' in detailed_checks:
            vague_check = detailed_checks['vague_language']
            if vague_check['score'] < 70:
                strategy['priorities'].append('vague_language')
                strategy['actions'].append('specify_details')
                strategy['focus_areas'].append('Replace vague terms with specific, quantified language')

        if 'citations' in detailed_checks:
            citation_check = detailed_checks['citations']
            if citation_check['score'] < 80:
                strategy['priorities'].append('citations')
                strategy['actions'].append('add_citations')
                strategy['focus_areas'].append('Add inline citations for all factual claims')

        if 'completeness' in detailed_checks:
            completeness_check = detailed_checks['completeness']
            if completeness_check['score'] < 70:
                strategy['priorities'].append('completeness')
                strategy['actions'].append('expand_content')
                strategy['focus_areas'].append('Add more detail and substance')

        return strategy

    def _apply_refinements(
        self,
        content: str,
        strategy: Dict,
        issues: List[str],
        suggestions: List[str],
        project_info: Dict,
        research_findings: Dict,
        section_name: str
    ) -> str:
        """
        Apply refinements to content based on strategy

        Args:
            content: Original content
            strategy: Refinement strategy
            issues: List of issues from evaluation
            suggestions: List of suggestions from evaluation
            project_info: Project information
            research_findings: Research findings
            section_name: Section name

        Returns:
            Refined content
        """
        # Build comprehensive refinement prompt
        prompt = self._build_refinement_prompt(
            content,
            strategy,
            issues,
            suggestions,
            project_info,
            research_findings,
            section_name
        )

        # Generate refined content
        refined_content = self.call_llm(
            prompt,
            max_tokens=4000,
            system_prompt=self._get_refinement_system_prompt()
        )

        return refined_content.strip()

    def _build_refinement_prompt(
        self,
        content: str,
        strategy: Dict,
        issues: List[str],
        suggestions: List[str],
        project_info: Dict,
        research_findings: Dict,
        section_name: str
    ) -> str:
        """Build the refinement prompt"""

        priorities = ", ".join(strategy['priorities']) if strategy['priorities'] else "general quality"
        focus_areas = "\n".join([f"- {area}" for area in strategy['focus_areas']])

        issues_text = "\n".join([f"- {issue}" for issue in issues[:10]]) if issues else "None"
        suggestions_text = "\n".join([f"- {suggestion}" for suggestion in suggestions[:10]]) if suggestions else "None"

        project_info_text = "\n".join([f"- {k}: {v}" for k, v in project_info.items()])

        research_text = research_findings.get('findings', 'No research findings available')
        sources_text = "\n".join([f"- {src}" for src in research_findings.get('sources', [])[:10]])

        prompt = f"""You are refining a section of a DoD acquisition document based on quality evaluation feedback.

**SECTION**: {section_name}

**CURRENT CONTENT TO REFINE**:
```
{content}
```

**QUALITY ISSUES IDENTIFIED**:
{issues_text}

**IMPROVEMENT SUGGESTIONS**:
{suggestions_text}

**REFINEMENT PRIORITIES**: {priorities}

**FOCUS AREAS**:
{focus_areas}

**GROUND TRUTH - PROJECT INFORMATION**:
{project_info_text}

**RESEARCH FINDINGS (for citations)**:
{research_text}

**AVAILABLE SOURCES**:
{sources_text}

═══════════════════════════════════════════════════════════════════
REFINEMENT INSTRUCTIONS:
═══════════════════════════════════════════════════════════════════

**PRIMARY OBJECTIVE**: Fix the identified issues while preserving good content.

**SPECIFIC FIXES REQUIRED**:

1. **Fix Vague Language**:
   - Replace ALL vague terms: several → X (specific number with citation)
   - Replace: many → X vendors (cite source)
   - Replace: approximately → exact figure (cite source) or "estimated at X (Source)"
   - Replace: timely → within X days (cite requirement)
   - Replace: adequate → specific metric (cite standard)

2. **Add Missing Citations**:
   - Every factual claim MUST have inline citation: (Source Name, Date)
   - Budget amounts: (Program Budget, FY2025)
   - Timeline: (Schedule Requirements, Date)
   - Requirements: (Technical Requirements Document, Date)
   - Objectives: (Program Objectives, Date)
   - Standards: (Performance Standards, Date)
   - **Target**: 5-7 citations per section minimum

3. **Eliminate Hallucinations**:
   - ONLY use facts from Project Information and Research Findings above
   - Remove any claims not traceable to sources
   - If uncertain, remove the claim or add "to be determined"
   - Do NOT invent vendor names, statistics, or specifications

4. **Maintain Document Quality**:
   - Keep good structure and flow
   - Preserve accurate statements
   - Maintain professional tone
   - Keep appropriate length (250+ words)
   - Use outcome-focused language (achieve, deliver, demonstrate)

═══════════════════════════════════════════════════════════════════
OUTPUT REQUIREMENTS:
═══════════════════════════════════════════════════════════════════

Return the REFINED VERSION of the content with:
✓ All vague terms replaced with specifics + citations
✓ All factual claims cited inline
✓ No unverifiable claims
✓ Same structure and tone
✓ Professional DoD acquisition language

Do NOT include explanations, comments, or meta-text. Return ONLY the refined content.

Generate the refined content now:
"""
        return prompt

    def _get_refinement_system_prompt(self) -> str:
        """Get system prompt for refinement"""
        return """You are an expert DoD acquisition document editor specializing in quality refinement.

CORE COMPETENCIES:
- Precise fact-checking and source verification
- DoD citation standards (inline document citations)
- Elimination of vague, imprecise language
- Preservation of document structure and flow
- Surgical improvements without unnecessary changes

REFINEMENT PRINCIPLES:
1. **Precision**: Replace every vague term with specific, quantified language
2. **Traceability**: Add inline citations for every factual claim
3. **Accuracy**: Only state facts from provided sources
4. **Preservation**: Keep good content, fix only what needs fixing
5. **Efficiency**: Make targeted improvements, not wholesale rewrites

You never add information not in sources. You always cite claims. You eliminate vagueness ruthlessly."""

    def _analyze_changes(self, original: str, refined: str) -> List[str]:
        """Analyze what changed between original and refined"""
        changes = []

        # Simple heuristic-based change detection
        import re

        # Check for added citations
        orig_citations = len(re.findall(r'\([A-Z][A-Za-z\s,/\-]+,\s*[A-Za-z0-9/\s,]+\)', original))
        new_citations = len(re.findall(r'\([A-Z][A-Za-z\s,/\-]+,\s*[A-Za-z0-9/\s,]+\)', refined))

        if new_citations > orig_citations:
            changes.append(f"Added {new_citations - orig_citations} citation(s)")

        # Check for removed vague words
        vague_words = ['several', 'many', 'some', 'various', 'approximately', 'around', 'significant']
        orig_vague = sum(len(re.findall(rf'\b{word}\b', original, re.IGNORECASE)) for word in vague_words)
        new_vague = sum(len(re.findall(rf'\b{word}\b', refined, re.IGNORECASE)) for word in vague_words)

        if new_vague < orig_vague:
            changes.append(f"Removed {orig_vague - new_vague} vague term(s)")

        # Check for length changes
        orig_words = len(original.split())
        new_words = len(refined.split())

        if abs(new_words - orig_words) > 20:
            if new_words > orig_words:
                changes.append(f"Expanded content (+{new_words - orig_words} words)")
            else:
                changes.append(f"Condensed content (-{orig_words - new_words} words)")

        return changes if changes else ["Minor text refinements"]

    def _summarize_improvements(self, strategy: Dict) -> str:
        """Summarize improvements made"""
        if not strategy['focus_areas']:
            return "General quality improvements applied"

        return "; ".join(strategy['focus_areas'])

    def _calculate_confidence(self, strategy: Dict, changes: List[str]) -> int:
        """Calculate confidence in improvements"""
        base_confidence = 70

        # Higher confidence if we addressed specific issues
        if len(strategy['priorities']) > 0:
            base_confidence += 10

        # Higher confidence if we made substantive changes
        if len(changes) > 2:
            base_confidence += 10

        # Cap at 90
        return min(90, base_confidence)

    def _format_dict(self, d: Dict) -> str:
        """Format dictionary for display"""
        return '\n'.join([f"- {k}: {v}" for k, v in d.items()])
