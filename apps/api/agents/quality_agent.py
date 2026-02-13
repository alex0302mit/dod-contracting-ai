"""
Quality Agent: Evaluates generated content for quality and compliance
Performs real-time quality checks during generation with DoD citation standards

Dependencies:
- base_agent: Core agent functionality
- utils.dod_citation_validator: DoD citation standards validation
"""

from typing import Dict, List
from .base_agent import BaseAgent
import re
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.utils.dod_citation_validator import DoDCitationValidator, CitationType
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class QualityAgent(BaseAgent):
    """
    Quality Agent: Evaluates content quality and compliance
    
    Responsibilities:
    - Check for hallucinations and fabricated facts
    - Detect vague or unsupported language
    - Verify DoD-compliant citations and sources
    - Assess legal/regulatory compliance
    - Provide improvement recommendations
    - Calculate quality scores
    
    Dependencies:
    - base_agent: Base agent LLM capabilities
    - DoDCitationValidator: DoD citation standards validation
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize quality agent with DoD citation validation
        
        Args:
            api_key: Anthropic API key
            model: Claude model to use
            
        Dependencies:
            - BaseAgent: Core agent functionality
            - DoDCitationValidator: For DoD citation standards
        """
        super().__init__(
            name="QualityAgent",
            api_key=api_key,
            model=model,
            temperature=0.1  # Very low temperature for consistent evaluation
        )
        # Initialize DoD citation validator for comprehensive checking
        self.dod_validator = DoDCitationValidator()
        self.log("Initialized with DoD citation validation")
    
    def execute(self, task: Dict) -> Dict:
        """
        Execute a quality evaluation task

        Args:
            task: Dictionary with:
                - content: Content to evaluate
                - section_name: Section name
                - project_info: Original project information
                - research_findings: Research findings used
                - evaluation_type: Type of evaluation (section/full/quick)
                - reasoning_tracker: Optional ReasoningTracker for token tracking

        Returns:
            Dictionary with:
                - score: Overall quality score (0-100)
                - issues: List of identified issues
                - suggestions: List of improvement suggestions
                - hallucination_risk: Risk level
                - compliance_check: Compliance assessment
                - detailed_checks: Individual check results including DoD citations
        """
        # Extract reasoning tracker from task for token usage tracking
        # Store as instance variable so helper methods can access it
        self._current_tracker = self.get_tracker_from_task(task)
        
        content = task.get('content', '')
        section_name = task.get('section_name', 'Unknown')
        project_info = task.get('project_info', {})
        research_findings = task.get('research_findings', {})
        evaluation_type = task.get('evaluation_type', 'section')
        program_name = project_info.get('program_name', 'Unknown')

        self.log(f"Evaluating: {section_name}")

        # STEP 0: Cross-reference lookup for document consistency validation
        self._document_references = []

        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up documents for consistency validation...")
                metadata_store = DocumentMetadataStore()

                # Get all documents for consistency checking
                all_program_docs = [doc for doc in metadata_store.metadata['documents'].values()
                                   if doc['program'] == program_name]

                if all_program_docs:
                    print(f"✅ Found {len(all_program_docs)} documents for validation")
                    self._document_references = all_program_docs

                    # Add to research findings for cross-validation
                    if not research_findings:
                        research_findings = {}
                    research_findings['existing_documents'] = [
                        {'type': doc['type'], 'id': doc['id'], 'data': doc['extracted_data']}
                        for doc in all_program_docs
                    ]

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")
        
        # Run multiple evaluation checks (now with DoD citation validation)
        checks = {
            'hallucination': self._check_hallucinations(content, project_info, research_findings),
            'vague_language': self._check_vague_language(content),
            'citations': self._check_citations(content),  # Now uses DoD validator
            'compliance': self._check_compliance(content, section_name),
            'completeness': self._check_completeness(content, section_name)
        }
        
        # Calculate overall score
        overall_score = self._calculate_score(checks)
        
        # Compile issues and suggestions
        issues = []
        suggestions = []
        
        for check_name, check_result in checks.items():
            issues.extend(check_result.get('issues', []))
            suggestions.extend(check_result.get('suggestions', []))
        
        result = {
            'score': overall_score,
            'grade': self._score_to_grade(overall_score),
            'issues': issues,
            'suggestions': suggestions,
            'hallucination_risk': checks['hallucination']['risk_level'],
            'compliance_check': checks['compliance'],
            'detailed_checks': checks  # Include all check details
        }

        # STEP 2: Save quality assessment metadata
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving Quality Assessment metadata...")
                metadata_store = DocumentMetadataStore()

                # Extract Quality Assessment specific data
                extracted_data = {
                    'evaluated_section': section_name,
                    'quality_score': overall_score,
                    'grade': self._score_to_grade(overall_score),
                    'issues_count': len(issues),
                    'hallucination_risk': checks['hallucination']['risk_level'],
                    'compliance_status': checks['compliance'].get('status', 'unknown'),
                    'documents_validated': len(self._document_references)
                }

                # Track references (documents that were validated)
                references = {}
                for i, doc in enumerate(self._document_references[:10]):  # Limit to 10
                    references[f"validated_{doc['type']}_{i+1}"] = doc['id']

                doc_id = metadata_store.save_document(
                    doc_type='quality_assessment',
                    program=program_name,
                    content=f"Quality Assessment: {section_name}\nScore: {overall_score}\nGrade: {self._score_to_grade(overall_score)}",
                    file_path=None,
                    extracted_data=extracted_data,
                    references=references
                )

                print(f"✅ Metadata saved: {doc_id}")

            except Exception as e:
                print(f"⚠️  Failed to save metadata: {str(e)}")

        return result
    
    def _check_hallucinations(
        self,
        content: str,
        project_info: Dict,
        research_findings: Dict
    ) -> Dict:
        """
        Check for potential hallucinations or fabricated facts across FULL document
        
        Args:
            content: Content to check
            project_info: Original project information
            research_findings: Research findings used
            
        Returns:
            Dictionary with hallucination check results
            
        Comments:
            Enhanced to analyze full document using chunked analysis
            Chunks document into 3000-char segments with 500-char overlap
        """
        self.log("Checking for hallucinations (full document analysis)...")
        
        # Patterns that indicate LEGITIMATE procurement language (whitelist)
        # These patterns should NOT trigger hallucination warnings
        legitimate_patterns = [
            r'FAR\s+\d+',              # FAR citations (e.g., FAR 15.304)
            r'DFARS\s+\d+',            # DFARS citations
            r'per\s+(?:FAR|DFARS)',    # "per FAR..." references
            r'in accordance with',     # Standard compliance language
            r'pursuant to',            # Legal language
            r'as required by',         # Requirement references
            r'IAW\s+',                 # "In Accordance With" abbreviation
            r'CFR\s+\d+',              # Code of Federal Regulations
            r'USC\s+\d+',              # United States Code
            r'\(Ref:',                 # Inline citations
        ]
        
        # Patterns that suggest fabricated content (narrower scope)
        # More specific to avoid false positives on legitimate market research
        suspicious_patterns = [
            r'according to (?:recent|latest) (?:studies|research)',  # More specific
            r'experts (?:say|agree|believe)',                        # Unattributed expert claims
            r'it is (?:well|widely) known',                          # Unsourced common knowledge claims
            r'studies (?:have )?shown that',                         # Unattributed studies
            r'(?:recent|latest) (?:surveys|polls) (?:indicate|show)', # Unattributed surveys
        ]
        
        # STEP 1: Pattern matching across FULL document (with whitelist filtering)
        findings = []
        for pattern in suspicious_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 100)
                context = content[start:end]
                
                # Skip if context contains legitimate procurement patterns
                is_legitimate = any(
                    re.search(legit_pattern, context, re.IGNORECASE) 
                    for legit_pattern in legitimate_patterns
                )
                if not is_legitimate:
                    findings.append(f"...{context.replace(chr(10), ' ')}...")
        
        # STEP 2: Check citation density across FULL document
        # Lower threshold from 20 to 5 - documents with 5+ citations show effort to source claims
        citation_count = len(re.findall(r'\(Ref:', content))
        has_good_citations = citation_count >= 5  # 5+ citations indicates effort to source claims

        # STEP 3: Chunk document for comprehensive LLM analysis
        chunk_size = 3000  # characters per chunk
        overlap = 500  # overlap between chunks to maintain context
        chunks = []
        
        start = 0
        while start < len(content):
            end = min(start + chunk_size, len(content))
            chunk = content[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap  # Move forward with overlap
        
        total_chunks = len(chunks)
        self.log(f"  Analyzing {total_chunks} chunks ({len(content)} total chars)")
        
        # STEP 4: Analyze each chunk with LLM
        chunk_assessments = []
        high_risk_chunks = 0
        medium_risk_chunks = 0
        low_risk_chunks = 0
        
        citation_note = ""
        if has_good_citations:
            citation_note = f"\n\nNOTE: This document contains {citation_count} inline citations (Ref: Source, Date). Consider this when assessing hallucination risk - cited claims are less likely to be fabricated."

        for i, chunk in enumerate(chunks, 1):
            # Only analyze chunks with substantial content
            if len(chunk.strip()) < 200:
                continue
                
            prompt = f"""You are a fact-checking expert reviewing DoD procurement documentation. Analyze this content segment for potential hallucinations.

CONTENT SEGMENT {i}/{total_chunks}:
{chunk}

PROJECT INFO PROVIDED:
{str(project_info)[:500]}{citation_note}

IMPORTANT CONTEXT - The following are LEGITIMATE and should NOT be flagged:
- FAR/DFARS citations and references (e.g., "FAR 15.304", "DFARS 252.204-7012")
- Standard contract clauses and boilerplate language
- Regulatory compliance statements ("in accordance with", "pursuant to", "as required by")
- Industry-standard procurement terminology
- Claims with inline citations like "(Ref: Source, Date)"

ONLY flag as potential hallucinations:
1. Specific statistics or numbers without any source
2. Claims about specific companies/vendors without verification
3. Fabricated dates, prices, or quantities not in project info
4. Suspiciously specific technical details that weren't provided

Return a brief assessment (2-3 sentences): LOW (standard procurement language), MEDIUM (some unverified claims), or HIGH (likely fabricated content)."""

            try:
                response = self.call_llm(prompt, max_tokens=300, tracker=self._current_tracker)
                assessment = response.strip()
                chunk_assessments.append({
                    'chunk_num': i,
                    'assessment': assessment,
                    'preview': chunk[:100] + "..."
                })
                
                # Count risk levels
                if 'HIGH' in assessment.upper():
                    high_risk_chunks += 1
                elif 'MEDIUM' in assessment.upper():
                    medium_risk_chunks += 1
                else:
                    low_risk_chunks += 1
                    
            except Exception as e:
                self.log(f"  ⚠️  Error analyzing chunk {i}: {str(e)}")
                continue
        
        # STEP 5: Aggregate risk assessment
        total_analyzed = high_risk_chunks + medium_risk_chunks + low_risk_chunks
        
        if total_analyzed == 0:
            # Fallback if all chunks failed
            risk_level = 'MEDIUM'
            llm_assessment = "Unable to analyze chunks; defaulting to MEDIUM risk"
        else:
            # Calculate risk based on chunk distribution
            # Raised thresholds to reduce false positives on DoD procurement documents
            high_ratio = high_risk_chunks / total_analyzed
            medium_ratio = medium_risk_chunks / total_analyzed
            
            if high_ratio > 0.5:  # More than 50% high-risk chunks (was 30%)
                risk_level = 'HIGH'
                llm_assessment = f"HIGH risk detected: {high_risk_chunks}/{total_analyzed} chunks show concerning patterns"
            elif high_ratio > 0.25 or medium_ratio > 0.7:  # 25% high or 70% medium (was 10% / 50%)
                risk_level = 'MEDIUM'
                llm_assessment = f"MEDIUM risk detected: {high_risk_chunks} HIGH, {medium_risk_chunks} MEDIUM, {low_risk_chunks} LOW risk chunks"
            else:
                risk_level = 'LOW'
                llm_assessment = f"LOW risk detected: {low_risk_chunks}/{total_analyzed} chunks are low risk"
        
        # STEP 6: Adjust risk level based on citation density (same as before)
        original_risk = risk_level
        if has_good_citations and risk_level == 'HIGH':
            risk_level = 'MEDIUM'  # Downgrade HIGH to MEDIUM if well-cited
            llm_assessment += f" (Adjusted from HIGH to MEDIUM due to {citation_count} inline citations)"
        elif has_good_citations and risk_level == 'MEDIUM':
            risk_level = 'LOW'  # Downgrade MEDIUM to LOW if well-cited
            llm_assessment += f" (Adjusted from MEDIUM to LOW due to {citation_count} inline citations)"
        
        # STEP 7: Build issues and suggestions
        issues = []
        suggestions = []

        if len(findings) > 0:
            issues.append(f"Found {len(findings)} vague or unsupported references")
            suggestions.append("Replace vague references with specific citations or remove them")

        if risk_level == 'HIGH':
            issues.append("HIGH hallucination risk detected across document")
            suggestions.append("Verify all factual claims against source documents")
        elif risk_level == 'MEDIUM':
            issues.append("MEDIUM hallucination risk detected in some sections")
            suggestions.append("Review and verify key factual claims")
        
        # Add chunk-specific insights if available
        if high_risk_chunks > 0:
            issues.append(f"{high_risk_chunks} section(s) need fact verification")
            high_chunk_nums = [str(c['chunk_num']) for c in chunk_assessments if 'HIGH' in c['assessment'].upper()][:3]
            if high_chunk_nums:
                suggestions.append(f"Focus verification on segments: {', '.join(high_chunk_nums)}")

        # Score based on risk
        risk_scores = {'LOW': 95, 'MEDIUM': 70, 'HIGH': 30}
        score = risk_scores.get(risk_level, 50)
        
        # Log detailed results
        self.log(f"  Analyzed {total_analyzed} chunks: {high_risk_chunks} HIGH, {medium_risk_chunks} MEDIUM, {low_risk_chunks} LOW")
        if original_risk != risk_level:
            self.log(f"  Risk adjusted: {original_risk} → {risk_level} (due to citations)")
        
        return {
            'score': score,
            'risk_level': risk_level,
            'suspicious_patterns': len(findings),
            'llm_assessment': llm_assessment,
            'issues': issues,
            'suggestions': suggestions,
            'examples': findings[:3],
            # Enhanced: Include chunked analysis details
            'chunks_analyzed': total_analyzed,
            'high_risk_chunks': high_risk_chunks,
            'medium_risk_chunks': medium_risk_chunks,
            'low_risk_chunks': low_risk_chunks,
            'chunk_details': chunk_assessments[:5],  # First 5 for debugging
            'full_document_analyzed': True
        }
    
    def _check_vague_language(self, content: str) -> Dict:
        """
        Detect vague or imprecise language
        
        Args:
            content: Content to check
            
        Returns:
            Dictionary with vague language check results
        """
        self.log("Checking for vague language...")
        
        vague_words = [
            'several', 'many', 'some', 'various', 'numerous',
            'significant', 'substantial', 'considerable',
            'appropriate', 'adequate', 'sufficient',
            'relevant', 'important', 'critical',
            'may', 'might', 'could', 'possibly', 'potentially'
        ]
        
        findings = []
        issues = []
        suggestions = []
        
        for word in vague_words:
            pattern = rf'\b{word}\b'
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                start = max(0, match.start() - 30)
                end = min(len(content), match.end() + 30)
                context = content[start:end].replace('\n', ' ')
                findings.append(f"...{context}...")
        
        if len(findings) > 10:
            issues.append(f"High use of vague language: {len(findings)} instances")
            suggestions.append("Replace vague terms with specific quantities and details")
        elif len(findings) > 5:
            issues.append(f"Moderate vague language detected: {len(findings)} instances")
            suggestions.append("Consider being more specific where possible")
        
        # Score: penalize based on vague language density
        vague_ratio = len(findings) / max(1, len(content.split()))
        score = max(0, 100 - (vague_ratio * 10000))
        
        return {
            'score': int(score),
            'count': len(findings),
            'findings': findings,
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _check_citations(self, content: str) -> Dict:
        """
        Check for proper DoD-compliant citations and source attribution
        
        Args:
            content: Content to check
            
        Returns:
            Dictionary with DoD citation check results including:
            - score: Citation quality score (0-100)
            - valid_citations: Count of valid DoD citations
            - invalid_citations: Count of invalid citations
            - claims_needing_citations: Count of uncited claims
            - issues: List of citation issues
            - suggestions: List of improvement suggestions
            - validation_details: Full validation results from DoD validator
            
        Comments:
            Now uses DoDCitationValidator for comprehensive DoD compliance checking
            Replaces generic citation patterns with DoD-specific validation
        """
        self.log("Checking DoD-compliant citations...")
        
        # Use DoD citation validator for comprehensive check
        validation_results = self.dod_validator.validate_content(content)
        
        # Extract key metrics
        score = validation_results['score']
        valid_count = validation_results['valid_citations']
        invalid_count = validation_results['invalid_citations']
        missing_count = validation_results['missing_citation_opportunities']
        
        # Build issues list from validation
        issues = []
        
        if invalid_count > 0:
            issues.append(f"{invalid_count} citation(s) do not follow DoD standards")
        
        if missing_count > 10:
            issues.append(f"{missing_count} factual claims lack proper citations")
        elif missing_count > 5:
            issues.append(f"{missing_count} claims should have citations")
        elif missing_count > 0:
            issues.append(f"{missing_count} claim(s) need citations")
        
        if valid_count == 0 and missing_count > 0:
            issues.append("No DoD-compliant citations detected")
        
        # Add specific issues from validator
        issues.extend(validation_results['issues'][:3])  # Top 3 issues
        
        # Build suggestions from validator
        suggestions = validation_results['suggestions']
        
        # Add DoD-specific suggestions if needed
        if valid_count == 0:
            suggestions.append("Add FAR/DFARS citations for acquisition processes (e.g., FAR 10.001 for market research)")
            suggestions.append("Add program document citations for project specifics (e.g., Budget Specification, FY2025)")
        
        # Log detailed results if score is low
        if score < 70:
            self.log(f"  ⚠️  Low citation score: {score}/100")
            self.log(f"  Valid: {valid_count}, Invalid: {invalid_count}, Missing: {missing_count}")
        
        return {
            'score': int(score),
            'citations_found': valid_count,
            'invalid_citations': invalid_count,
            'claims_needing_citations': missing_count,
            'issues': issues,
            'suggestions': suggestions,
            'validation_details': validation_results['citation_details'],
            'dod_compliant': valid_count > 0 and invalid_count == 0
        }
    
    def _check_compliance(self, content: str, section_name: str) -> Dict:
        """
        Check for legal and regulatory compliance issues
        
        Args:
            content: Content to check
            section_name: Section name
            
        Returns:
            Dictionary with compliance check results
        """
        self.log("Checking compliance...")
        
        prompt = f"""You are a government contracting legal expert reviewing content for compliance issues.

SECTION: {section_name}

CONTENT:
{content}

Analyze for:
1. Anti-competitive language (preferences for specific vendors)
2. Discriminatory or exclusionary language
3. Violations of small business requirements
4. Missing required disclosures or disclaimers
5. Overly restrictive requirements that limit competition

Provide:
- Compliance level: COMPLIANT, MINOR ISSUES, or MAJOR ISSUES
- Brief assessment (2-3 sentences)
- Specific concerns if any"""

        # Pass tracker for token usage tracking
        response = self.call_llm(prompt, max_tokens=500, tracker=self._current_tracker)
        assessment = response.strip()
        
        # Determine compliance level
        if 'MAJOR ISSUES' in assessment.upper():
            level = 'MAJOR ISSUES'
            score = 30
        elif 'MINOR ISSUES' in assessment.upper():
            level = 'MINOR ISSUES'
            score = 70
        else:
            level = 'COMPLIANT'
            score = 95
        
        issues = []
        suggestions = []
        
        if level == 'MAJOR ISSUES':
            issues.append("Major compliance violations detected")
            suggestions.append("Review content with legal counsel before proceeding")
        elif level == 'MINOR ISSUES':
            issues.append("Minor compliance concerns detected")
            suggestions.append("Address compliance issues to avoid procurement challenges")
        
        return {
            'score': score,
            'level': level,
            'assessment': assessment,
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _check_completeness(self, content: str, section_name: str) -> Dict:
        """
        Check if content is complete and substantive
        
        Args:
            content: Content to check
            section_name: Section name
            
        Returns:
            Dictionary with completeness check results
        """
        word_count = len(content.split())
        
        issues = []
        suggestions = []
        
        # Check word count
        min_words = 200
        if word_count < min_words:
            issues.append(f"Section is brief: {word_count} words (recommended: {min_words}+)")
            suggestions.append("Expand section with more detail and examples")
        
        # Check for structure (paragraphs)
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) < 2:
            issues.append("Content lacks paragraph structure")
            suggestions.append("Organize content into multiple paragraphs")
        
        # Score based on completeness
        word_score = min(100, (word_count / min_words) * 100)
        structure_score = min(100, len(paragraphs) * 50)
        score = (word_score + structure_score) / 2
        
        return {
            'score': int(score),
            'word_count': word_count,
            'paragraph_count': len(paragraphs),
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _calculate_score(self, checks: Dict) -> int:
        """
        Calculate overall quality score from individual checks
        
        Args:
            checks: Dictionary of check results
            
        Returns:
            Overall score (0-100)
            
        Comments:
            Citation weight increased to 0.20 to emphasize DoD compliance
        """
        weights = {
            'hallucination': 0.30,  # Most critical for accuracy
            'vague_language': 0.15,
            'citations': 0.20,  # Increased: DoD citation compliance is important
            'compliance': 0.25,  # Increased: Legal compliance is critical
            'completeness': 0.10
        }
        
        weighted_score = sum(
            checks[key]['score'] * weights[key]
            for key in weights.keys()
        )
        
        return int(weighted_score)
    
    def _score_to_grade(self, score: int) -> str:
        """Convert numeric score to letter grade"""
        if score >= 90:
            return 'A (Excellent)'
        elif score >= 80:
            return 'B (Good)'
        elif score >= 70:
            return 'C (Acceptable)'
        elif score >= 60:
            return 'D (Needs Improvement)'
        else:
            return 'F (Major Issues)'
    
    def _format_dict(self, d: Dict) -> str:
        """Format dictionary for display"""
        return '\n'.join([f"- {k}: {v}" for k, v in d.items()])
    
    def evaluate_full_report(
        self,
        sections: Dict,
        project_info: Dict,
        research_results: Dict
    ) -> Dict:
        """
        Evaluate all sections of a report with DoD citation compliance
        
        Args:
            sections: Dictionary of section_name: content
            project_info: Original project information
            research_results: Research results by section
            
        Returns:
            Comprehensive evaluation results including DoD citation analysis
        """
        self.log("Starting full report evaluation with DoD citation validation...")
        
        all_evaluations = {}
        
        for section_name, section_content in sections.items():
            research_findings = research_results.get(section_name, {})
            
            task = {
                'content': section_content,
                'section_name': section_name,
                'project_info': project_info,
                'research_findings': research_findings,
                'evaluation_type': 'section'
            }
            
            evaluation = self.execute(task)
            all_evaluations[section_name] = evaluation
        
        # Calculate overall report score
        section_scores = [eval_result['score'] for eval_result in all_evaluations.values()]
        overall_score = int(sum(section_scores) / len(section_scores)) if section_scores else 0
        
        # Compile all issues and suggestions
        all_issues = []
        all_suggestions = []
        for section_name, eval_result in all_evaluations.items():
            for issue in eval_result['issues']:
                all_issues.append(f"[{section_name}] {issue}")
            for suggestion in eval_result['suggestions']:
                all_suggestions.append(f"[{section_name}] {suggestion}")
        
        # Calculate DoD citation compliance across report
        total_valid_citations = sum(
            eval_result['detailed_checks']['citations']['citations_found']
            for eval_result in all_evaluations.values()
        )
        total_invalid_citations = sum(
            eval_result['detailed_checks']['citations']['invalid_citations']
            for eval_result in all_evaluations.values()
        )
        
        self.log(f"Full report evaluation complete: Overall score {overall_score}/100")
        self.log(f"DoD Citations - Valid: {total_valid_citations}, Invalid: {total_invalid_citations}")
        
        return {
            'overall_score': overall_score,
            'overall_grade': self._score_to_grade(overall_score),
            'section_evaluations': all_evaluations,
            'all_issues': all_issues,
            'all_suggestions': all_suggestions,
            'total_sections': len(all_evaluations),
            'dod_citation_summary': {
                'total_valid': total_valid_citations,
                'total_invalid': total_invalid_citations,
                'compliance_rate': (total_valid_citations / max(1, total_valid_citations + total_invalid_citations)) * 100
            }
        }
