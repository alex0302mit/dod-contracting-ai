"""
Evaluation Scorecard Generator Agent: Generates proposal evaluation scorecards
Creates scorecards aligned with Section M evaluation factors per FAR 15.305
"""

from typing import Dict, List, Optional
from pathlib import Path
import sys
from datetime import datetime
import re

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.base_agent import BaseAgent
from backend.rag.retriever import Retriever
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class EvaluationScorecardGeneratorAgent(BaseAgent):
    """
    Evaluation Scorecard Generator Agent
    
    Generates proposal evaluation scorecards per FAR 15.305.
    
    Features:
    - Aligns with Section M factors/subfactors
    - Adjectival rating scales (Outstanding, Good, Acceptable, Marginal, Unacceptable)
    - Numerical scoring (if applicable)
    - Strengths/weaknesses/deficiencies format per FAR
    - Risk assessment (Low/Medium/High)
    - Supports Best Value Trade-Off and LPTA
    
    Dependencies:
    - BaseAgent: LLM interaction and common utilities
    """
    
    def __init__(
        self,
        api_key: str,
        retriever: Optional[Retriever] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize Evaluation Scorecard Generator Agent

        Args:
            api_key: Anthropic API key
            retriever: Optional RAG retriever for evaluation criteria
            model: Claude model to use
        """
        super().__init__(
            name="Evaluation Scorecard Generator Agent",
            api_key=api_key,
            model=model,
            temperature=0.3  # Low temperature for objective evaluation
        )

        self.retriever = retriever
        self.template_path = Path(__file__).parent.parent / "templates" / "evaluation_scorecard_template.md"
        
        # Load template
        with open(self.template_path, 'r') as f:
            self.template = f.read()
        
        # Rating scales
        self.rating_scales = {
            'best_value': {
                'Outstanding': {
                    'description': 'Proposal meets requirements and exceeds in all significant aspects. Exceptional merit with multiple strengths and no weaknesses.',
                    'risk': 'Low',
                    'score_range': '90-100'
                },
                'Good': {
                    'description': 'Proposal meets requirements and exceeds in some significant aspects. Above average merit with strengths outweighing weaknesses.',
                    'risk': 'Low to Moderate',
                    'score_range': '75-89'
                },
                'Acceptable': {
                    'description': 'Proposal meets requirements with no significant weaknesses. Adequate proposal with minimal risk.',
                    'risk': 'Moderate',
                    'score_range': '60-74'
                },
                'Marginal': {
                    'description': 'Proposal meets minimum requirements but has significant weaknesses. Weaknesses increase performance risk.',
                    'risk': 'Moderate to High',
                    'score_range': '40-59'
                },
                'Unacceptable': {
                    'description': 'Proposal fails to meet minimum requirements or has deficiencies. Unacceptable risk of unsuccessful performance.',
                    'risk': 'High',
                    'score_range': '0-39'
                }
            },
            'lpta': {
                'Acceptable': 'Meets all minimum requirements',
                'Unacceptable': 'Fails to meet one or more minimum requirements'
            }
        }
        
        print("\n" + "="*70)
        print("EVALUATION SCORECARD GENERATOR AGENT INITIALIZED")
        print("="*70)
        print(f"  ✓ BaseAgent initialized")
        print(f"  ✓ Template loaded: {self.template_path.name}")
        if self.retriever:
            print(f"  ✓ RAG retriever available (evaluation criteria enhancement enabled)")
        else:
            print(f"  ℹ RAG retriever not available (using standard criteria only)")
        print(f"  ✓ Rating scales loaded (Best Value + LPTA)")
        print("="*70 + "\n")
    
    def execute(self, task: Dict) -> Dict:
        """
        Execute evaluation scorecard generation

        Args:
            task: Dictionary containing:
                - solicitation_info: Solicitation details
                - section_m_content: Section M evaluation factors content
                - evaluation_factor: Factor being evaluated (Technical, Management, etc.)
                - config: Configuration (evaluator info, methodology)

        Returns:
            Dictionary with scorecard content and metadata
        """
        self.log("Starting evaluation scorecard generation")

        solicitation_info = task.get('solicitation_info', {})
        section_m_content = task.get('section_m_content', '')
        evaluation_factor = task.get('evaluation_factor', 'Technical Approach')
        config = task.get('config', {})
        program_name = solicitation_info.get('program_name', 'Unknown')

        source_selection_method = config.get('source_selection_method', 'Best Value Trade-Off')

        # STEP 0: Cross-reference lookup for Section M, PWS/SOW/SOO
        self._section_m_reference = None
        self._pws_reference = None
        self._sow_reference = None
        self._soo_reference = None

        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for Section M (evaluation criteria)
                latest_m = metadata_store.find_latest_document('section_m', program_name)
                if latest_m:
                    print(f"✅ Found Section M: {latest_m['id']}")
                    print(f"   Evaluation Factors: {latest_m['extracted_data'].get('factor_count', 0)}")
                    # Use Section M content if not provided
                    if not section_m_content:
                        section_m_content = latest_m['content']
                    config['evaluation_factors'] = latest_m['extracted_data'].get('evaluation_factors', [])
                    self._section_m_reference = latest_m['id']
                else:
                    print("ℹ️  No Section M found")

                # Look for work statement (PWS, SOW, or SOO) for performance requirements
                latest_pws = metadata_store.find_latest_document('pws', program_name)
                latest_sow = metadata_store.find_latest_document('sow', program_name)
                latest_soo = metadata_store.find_latest_document('soo', program_name)

                if latest_pws:
                    print(f"✅ Found PWS: {latest_pws['id']}")
                    print(f"   Performance Requirements: {len(latest_pws['extracted_data'].get('performance_requirements', []))}")
                    config['performance_requirements'] = latest_pws['extracted_data'].get('performance_requirements', [])
                    self._pws_reference = latest_pws['id']

                if latest_sow:
                    print(f"✅ Found SOW: {latest_sow['id']}")
                    self._sow_reference = latest_sow['id']

                if latest_soo:
                    print(f"✅ Found SOO: {latest_soo['id']}")
                    self._soo_reference = latest_soo['id']

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")

        print("\n" + "="*70)
        print("GENERATING EVALUATION SCORECARD")
        print("="*70)
        print(f"Solicitation: {solicitation_info.get('solicitation_number', 'Unknown')}")
        print(f"Factor: {evaluation_factor}")
        print(f"Method: {source_selection_method}")
        print("="*70 + "\n")
        
        # Step 1: Extract evaluation criteria from Section M
        print("STEP 1: Extracting evaluation criteria from Section M...")
        criteria = self._extract_evaluation_criteria(section_m_content, evaluation_factor)
        print(f"  ✓ Extracted {len(criteria['subfactors'])} subfactors")

        # Step 1a: Build evaluation context from RAG
        print("\nSTEP 1a: Building evaluation criteria context from RAG...")
        rag_context = self._build_evaluation_context(solicitation_info, section_m_content, evaluation_factor)
        print(f"  ✓ RAG context built with {len(rag_context)} criteria points extracted")

        # Step 2: Generate rating scale
        print("\nSTEP 2: Generating rating scale...")
        rating_scale = self._generate_rating_scale(source_selection_method)
        print(f"  ✓ Rating scale: {source_selection_method}")
        
        # Step 3: Create subfactor evaluation sections
        print("\nSTEP 3: Creating subfactor evaluation sections...")
        subfactor_sections = self._create_subfactor_sections(criteria['subfactors'])
        print(f"  ✓ Created {len(subfactor_sections)} subfactor sections")
        
        # Step 4: Populate template
        print("\nSTEP 4: Populating evaluation scorecard template...")
        content = self._populate_template(
            solicitation_info,
            evaluation_factor,
            criteria,
            rating_scale,
            subfactor_sections,
            rag_context,
            config
        )
        print(f"  ✓ Template populated ({len(content)} characters)")
        
        # STEP 5: Save metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving Evaluation Scorecard metadata...")
                metadata_store = DocumentMetadataStore()

                # Extract scorecard specific data
                extracted_data = {
                    'evaluation_factor': evaluation_factor,
                    'subfactors_count': len(criteria['subfactors']),
                    'subfactors': criteria['subfactors'],
                    'source_selection_method': source_selection_method,
                    'rating_scale_type': 'Best Value' if source_selection_method == 'Best Value Trade-Off' else 'LPTA',
                    'rating_levels': list(rating_scale.keys()) if isinstance(rating_scale, dict) else ['Acceptable', 'Unacceptable'],
                    'criteria_count': len(criteria['subfactors'])
                }

                # Track references
                references = {}
                if self._section_m_reference:
                    references['section_m'] = self._section_m_reference
                if self._pws_reference:
                    references['pws'] = self._pws_reference
                if self._sow_reference:
                    references['sow'] = self._sow_reference
                if self._soo_reference:
                    references['soo'] = self._soo_reference

                doc_id = metadata_store.save_document(
                    doc_type='evaluation_scorecard',
                    program=program_name,
                    content=content,
                    file_path=None,
                    extracted_data=extracted_data,
                    references=references
                )

                print(f"✅ Metadata saved: {doc_id}")

            except Exception as e:
                print(f"⚠️  Failed to save metadata: {str(e)}")

        print("\n" + "="*70)
        print("✅ EVALUATION SCORECARD GENERATION COMPLETE")
        print("="*70)

        return {
            'status': 'success',
            'content': content,
            'metadata': {
                'evaluation_factor': evaluation_factor,
                'subfactors_count': len(criteria['subfactors']),
                'source_selection_method': source_selection_method,
                'rating_scale_type': 'Best Value' if source_selection_method == 'Best Value Trade-Off' else 'LPTA'
            }
        }
    
    def _extract_evaluation_criteria(self, section_m_content: str, evaluation_factor: str) -> Dict:
        """Extract evaluation criteria for specified factor from Section M"""
        # Default subfactors by factor type
        default_subfactors = {
            'Technical Approach': [
                {'name': 'System Architecture and Design', 'weight': '25%'},
                {'name': 'Development Methodology', 'weight': '20%'},
                {'name': 'Integration Approach', 'weight': '20%'},
                {'name': 'Cybersecurity Implementation', 'weight': '20%'},
                {'name': 'Testing and Quality Assurance', 'weight': '15%'}
            ],
            'Management Approach': [
                {'name': 'Project Management', 'weight': '30%'},
                {'name': 'Team Organization and Key Personnel', 'weight': '25%'},
                {'name': 'Risk Management', 'weight': '20%'},
                {'name': 'Quality Management', 'weight': '15%'},
                {'name': 'Transition Planning', 'weight': '10%'}
            ],
            'Past Performance': [
                {'name': 'Relevance of Past Performance', 'weight': '40%'},
                {'name': 'Quality of Past Performance', 'weight': '40%'},
                {'name': 'Recency of Past Performance', 'weight': '20%'}
            ],
            'Cost/Price': [
                {'name': 'Price Reasonableness', 'weight': '50%'},
                {'name': 'Cost Realism', 'weight': '30%'},
                {'name': 'Cost Completeness', 'weight': '20%'}
            ]
        }
        
        subfactors = default_subfactors.get(evaluation_factor, [])
        
        return {
            'factor': evaluation_factor,
            'subfactors': subfactors,
            'description': f"Evaluation of {evaluation_factor} as specified in Section M"
        }

    def _build_evaluation_context(
        self,
        solicitation_info: Dict,
        section_m_content: str,
        evaluation_factor: str
    ) -> Dict:
        """
        Build comprehensive evaluation context from RAG documents

        Performs 3 targeted RAG queries:
        1. Rating standards and definitions from similar RFPs
        2. Evaluation criteria examples for the specific factor
        3. Strengths/weaknesses examples and past performance criteria

        Returns:
            Dictionary with extracted evaluation context data
        """
        if not self.retriever:
            return {}

        program_name = solicitation_info.get('program_name', 'the program')
        rag_context = {}

        print(f"    → Querying RAG for {evaluation_factor} evaluation criteria...")

        # Query 1: Rating standards and definitions
        print(f"    → Query 1: Rating standards and definitions...")
        results = self.retriever.retrieve(
            f"Rating scale definitions adjectival ratings outstanding good acceptable for {program_name} evaluation",
            k=5
        )
        rating_standards = self._extract_rating_standards_from_rag(results)
        rag_context.update(rating_standards)
        print(f"      ✓ Extracted {len(rating_standards)} rating standards")

        # Query 2: Evaluation criteria for specific factor
        print(f"    → Query 2: {evaluation_factor} evaluation criteria...")
        results = self.retriever.retrieve(
            f"{evaluation_factor} evaluation criteria subfactors for {program_name} RFP Section M",
            k=5
        )
        criteria_examples = self._extract_evaluation_criteria_from_rag(results, evaluation_factor)
        rag_context.update(criteria_examples)
        print(f"      ✓ Extracted {len(criteria_examples)} criteria examples")

        # Query 3: Evaluation examples and guidance
        print(f"    → Query 3: Evaluation examples and guidance...")
        results = self.retriever.retrieve(
            f"Strengths weaknesses deficiencies examples evaluation guidance for {evaluation_factor}",
            k=5
        )
        eval_examples = self._extract_evaluation_examples_from_rag(results)
        rag_context.update(eval_examples)
        print(f"      ✓ Extracted {len(eval_examples)} evaluation examples")

        return rag_context

    def _extract_rating_standards_from_rag(self, rag_results: List[Dict]) -> Dict:
        """Extract rating standards and definitions from RAG results"""
        standards = {}
        combined_text = "\n".join([r.content if hasattr(r, 'content') else r.get('content', '') for r in rag_results])

        # Extract rating thresholds
        if 'outstanding' in combined_text.lower():
            # Look for outstanding criteria
            outstanding_match = re.search(
                r'outstanding[:\s]+([^\.]+(?:\.[^\.]+)?)',
                combined_text,
                re.IGNORECASE
            )
            if outstanding_match:
                standards['outstanding_criteria'] = outstanding_match.group(1).strip()

        # Extract acceptable criteria
        if 'acceptable' in combined_text.lower():
            acceptable_match = re.search(
                r'acceptable[:\s]+([^\.]+(?:\.[^\.]+)?)',
                combined_text,
                re.IGNORECASE
            )
            if acceptable_match:
                standards['acceptable_criteria'] = acceptable_match.group(1).strip()

        # Extract risk assessment guidance
        if 'risk' in combined_text.lower():
            risk_match = re.search(
                r'risk\s+(?:assessment|level)[:\s]+([^\.]+)',
                combined_text,
                re.IGNORECASE
            )
            if risk_match:
                standards['risk_guidance'] = risk_match.group(1).strip()

        return standards

    def _extract_evaluation_criteria_from_rag(self, rag_results: List[Dict], evaluation_factor: str) -> Dict:
        """Extract specific evaluation criteria for the given factor"""
        criteria = {}
        combined_text = "\n".join([r.content if hasattr(r, 'content') else r.get('content', '') for r in rag_results])

        # Look for factor-specific criteria
        factor_keywords = {
            'Technical Approach': ['architecture', 'design', 'development', 'testing', 'integration', 'cybersecurity'],
            'Management Approach': ['project management', 'team', 'personnel', 'risk management', 'quality'],
            'Past Performance': ['relevance', 'quality', 'recency', 'contract performance', 'similar work'],
            'Cost/Price': ['reasonable', 'realistic', 'complete', 'competitive', 'cost breakdown']
        }

        keywords = factor_keywords.get(evaluation_factor, [])
        found_criteria = []

        for keyword in keywords:
            if keyword.lower() in combined_text.lower():
                # Extract sentence containing keyword
                pattern = r'([^\.]*' + re.escape(keyword) + r'[^\.]*\.)'
                matches = re.findall(pattern, combined_text, re.IGNORECASE)
                if matches:
                    found_criteria.extend(matches[:2])  # Limit to 2 examples per keyword

        if found_criteria:
            criteria['factor_criteria_examples'] = found_criteria[:5]  # Max 5 examples

        # Extract weighting guidance if available
        weight_match = re.search(r'weight(?:ing)?[:\s]+(\d+%)', combined_text, re.IGNORECASE)
        if weight_match:
            criteria['weighting_guidance'] = weight_match.group(1)

        return criteria

    def _extract_evaluation_examples_from_rag(self, rag_results: List[Dict]) -> Dict:
        """Extract example strengths, weaknesses, and evaluation guidance"""
        examples = {}
        combined_text = "\n".join([r.content if hasattr(r, 'content') else r.get('content', '') for r in rag_results])

        # Extract strength examples
        strength_patterns = [
            r'strength[s]?[:\s]+([^\.]+)',
            r'exceeds[:\s]+([^\.]+)',
            r'exceptional[:\s]+([^\.]+)'
        ]

        strengths = []
        for pattern in strength_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            strengths.extend([m.strip() for m in matches if len(m.strip()) > 10])

        if strengths:
            examples['strength_examples'] = strengths[:3]  # Top 3

        # Extract weakness examples
        weakness_patterns = [
            r'weakness[es]*[:\s]+([^\.]+)',
            r'deficiency[ies]*[:\s]+([^\.]+)',
            r'concern[s]?[:\s]+([^\.]+)'
        ]

        weaknesses = []
        for pattern in weakness_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            weaknesses.extend([m.strip() for m in matches if len(m.strip()) > 10])

        if weaknesses:
            examples['weakness_examples'] = weaknesses[:3]  # Top 3

        # Extract evaluation best practices
        if 'evaluator' in combined_text.lower() or 'evaluation' in combined_text.lower():
            guidance_match = re.search(
                r'(?:evaluator|evaluation)\s+(?:should|must|shall)[:\s]+([^\.]+)',
                combined_text,
                re.IGNORECASE
            )
            if guidance_match:
                examples['evaluation_guidance'] = guidance_match.group(1).strip()

        return examples

    def _generate_rating_scale(self, source_selection_method: str) -> str:
        """Generate appropriate rating scale"""
        if 'LPTA' in source_selection_method or 'Lowest Price' in source_selection_method:
            # LPTA rating scale
            return """
**LPTA Rating Scale:**

| Rating | Definition |
|--------|------------|
| **Acceptable** | Meets all minimum technical requirements |
| **Unacceptable** | Fails to meet one or more minimum technical requirements |

**Note:** Under LPTA, only technically acceptable proposals are considered for award. Award is made to the lowest priced, technically acceptable offeror.
"""
        else:
            # Best Value rating scale
            scale_text = "**Best Value Trade-Off Rating Scale:**\n\n| Rating | Definition | Risk Level | Score Range |\n|--------|------------|------------|-------------|\n"
            
            for rating, details in self.rating_scales['best_value'].items():
                scale_text += f"| **{rating}** | {details['description']} | {details['risk']} | {details['score_range']} |\n"
            
            return scale_text
    
    def _create_subfactor_sections(self, subfactors: List[Dict]) -> str:
        """Create evaluation sections for each subfactor"""
        sections = []
        
        for i, subfactor in enumerate(subfactors, 1):
            section = f"""
### 3.{i} Subfactor: {subfactor['name']}

**Weight:** {subfactor['weight']}

**Evaluation Criteria:**
[Evaluator: Insert specific criteria for this subfactor from Section M]

**Offeror's Approach:**
[Evaluator: Summarize offeror's proposed approach for this subfactor]

**Assessment:**
[Evaluator: Provide detailed assessment]

**Strengths:**
[Evaluator: List any strengths identified]

**Weaknesses:**
[Evaluator: List any weaknesses identified]

**Deficiencies:**
[Evaluator: List any deficiencies identified]

**Subfactor Rating:** [Outstanding / Good / Acceptable / Marginal / Unacceptable]

**Risk Level:** [Low / Moderate / High]

---
"""
            sections.append(section)
        
        return '\n'.join(sections)
    
    def _populate_template(
        self,
        solicitation_info: Dict,
        evaluation_factor: str,
        criteria: Dict,
        rating_scale: str,
        subfactor_sections: str,
        rag_context: Dict,
        config: Dict
    ) -> str:
        """
        Populate evaluation scorecard template with intelligent priority system

        Priority order:
        1. Config values (explicitly provided)
        2. RAG-retrieved values (from documents)
        3. Descriptive TBDs with context
        """
        content = self.template

        # Helper function for priority-based value selection
        def get_value(config_key=None, rag_key=None, default='TBD'):
            if config_key and config.get(config_key):
                return config.get(config_key)
            if rag_key and rag_key in rag_context:
                return str(rag_context[rag_key])
            return default

        # Basic information
        content = content.replace('{{solicitation_number}}', solicitation_info.get('solicitation_number', 'TBD'))
        content = content.replace('{{program_name}}', solicitation_info.get('program_name', 'TBD'))
        content = content.replace('{{offeror_name}}', config.get('offeror_name', '[Offeror Name]'))
        content = content.replace('{{evaluation_factor}}', evaluation_factor)
        content = content.replace('{{evaluator_name}}', config.get('evaluator_name', '[Evaluator Name]'))
        content = content.replace('{{evaluation_date}}', datetime.now().strftime('%B %d, %Y'))
        content = content.replace('{{classification}}', config.get('classification', 'UNCLASSIFIED'))

        # Source selection method
        content = content.replace('{{source_selection_method}}', config.get('source_selection_method', 'Best Value Trade-Off'))

        # Rating scale
        content = content.replace('{{rating_scale}}', rating_scale)

        # Factor details with RAG enhancement
        factor_description = criteria['description']
        if 'factor_criteria_examples' in rag_context and rag_context['factor_criteria_examples']:
            # Enhance description with RAG examples
            examples = rag_context['factor_criteria_examples'][:2]  # Top 2
            factor_description += f"\n\n**Key Criteria:** {'; '.join(examples[:100] for examples in examples)}"

        content = content.replace('{{factor_description}}', factor_description)
        content = content.replace('{{factor_weight}}', get_value('factor_weight', 'weighting_guidance', 'TBD - Weight specified in Section M'))

        # Evaluation criteria with RAG enhancement
        eval_criteria = 'Per Section M of the solicitation'
        if 'evaluation_guidance' in rag_context:
            eval_criteria += f"\n\n**Evaluation Guidance:** {rag_context['evaluation_guidance']}"
        content = content.replace('{{evaluation_criteria}}', eval_criteria)

        # Subfactor evaluations
        content = content.replace('{{subfactor_evaluations}}', subfactor_sections)

        # Evaluator information
        content = content.replace('{{evaluator_title}}', config.get('evaluator_title', 'Technical Evaluator'))
        content = content.replace('{{evaluator_org}}', config.get('evaluator_org', 'Evaluation Team'))

        # Offeror information with descriptive TBDs
        content = content.replace('{{offeror_duns}}', get_value('offeror_duns', default='TBD - Offeror DUNS to be provided'))
        content = content.replace('{{business_size}}', get_value('business_size', default='TBD - Business size per SAM.gov'))
        content = content.replace('{{socioeconomic_status}}', get_value('socioeconomic_status', default='TBD - Socioeconomic status per SAM.gov'))
        content = content.replace('{{volume_name}}', f"{evaluation_factor} Volume")
        content = content.replace('{{page_count}}', get_value('page_count', default='TBD - Page count from proposal'))
        content = content.replace('{{proposal_date}}', get_value('proposal_date', default='TBD - Date from proposal submission'))

        # Rating definitions - enhance with RAG if available
        rating_defs = """
- **Outstanding:** Exceeds requirements in all significant aspects, exceptional merit
- **Good:** Meets requirements and exceeds in some aspects, above average merit
- **Acceptable:** Meets requirements, adequate with minimal risk
- **Marginal:** Meets minimum requirements but has significant weaknesses
- **Unacceptable:** Fails to meet requirements or has deficiencies
"""

        # Add RAG-derived rating guidance if available
        if 'outstanding_criteria' in rag_context:
            rating_defs += f"\n**Outstanding Criteria:** {rag_context['outstanding_criteria']}"
        if 'acceptable_criteria' in rag_context:
            rating_defs += f"\n**Acceptable Criteria:** {rag_context['acceptable_criteria']}"
        if 'risk_guidance' in rag_context:
            rating_defs += f"\n**Risk Assessment Guidance:** {rag_context['risk_guidance']}"

        content = content.replace('{{rating_definitions}}', rating_defs)

        # Add evaluation examples section if available
        if 'strength_examples' in rag_context or 'weakness_examples' in rag_context:
            examples_section = "\n\n## Evaluation Examples\n\n"

            if 'strength_examples' in rag_context:
                examples_section += "**Example Strengths:**\n"
                for strength in rag_context['strength_examples']:
                    examples_section += f"- {strength}\n"
                examples_section += "\n"

            if 'weakness_examples' in rag_context:
                examples_section += "**Example Weaknesses:**\n"
                for weakness in rag_context['weakness_examples']:
                    examples_section += f"- {weakness}\n"

            # Insert before final sections
            content = content.replace('---\n\n## Evaluator Certification', examples_section + '\n---\n\n## Evaluator Certification')

        # Fill remaining placeholders with contextual instructions
        remaining_placeholders = re.findall(r'\{\{([^}]+)\}\}', content)
        for placeholder in remaining_placeholders:
            placeholder_lower = placeholder.lower()
            if 'criteria' in placeholder_lower:
                replacement = '[Evaluator: Insert specific evaluation criteria from Section M]'
            elif 'approach' in placeholder_lower:
                replacement = '[Evaluator: Summarize offeror\'s proposed approach]'
            elif 'assessment' in placeholder_lower:
                replacement = '[Evaluator: Provide detailed technical assessment]'
            elif 'strength' in placeholder_lower:
                replacement = '[Evaluator: Document specific strengths with rationale]'
            elif 'weakness' in placeholder_lower:
                replacement = '[Evaluator: Document specific weaknesses with impact analysis]'
            elif 'deficiency' in placeholder_lower:
                replacement = '[Evaluator: Document any deficiencies requiring correction]'
            elif 'rating' in placeholder_lower:
                replacement = '[Evaluator: Assign rating: Outstanding/Good/Acceptable/Marginal/Unacceptable]'
            elif 'risk' in placeholder_lower:
                replacement = '[Evaluator: Assess risk level: Low/Moderate/High]'
            else:
                replacement = '[Evaluator: Complete this section per evaluation guidelines]'

            content = content.replace(f'{{{{{placeholder}}}}}', replacement)

        return content
    
    def generate_full_scorecard_set(
        self,
        solicitation_info: Dict,
        section_m_content: str,
        config: Dict
    ) -> Dict:
        """
        Generate complete set of scorecards for all evaluation factors
        
        Args:
            solicitation_info: Solicitation details
            section_m_content: Section M content
            config: Configuration
        
        Returns:
            Dictionary with scorecards for each factor
        """
        print("\n" + "="*70)
        print("GENERATING COMPLETE EVALUATION SCORECARD SET")
        print("="*70)
        
        # Standard evaluation factors
        factors = [
            'Technical Approach',
            'Management Approach',
            'Past Performance',
            'Cost/Price'
        ]
        
        scorecards = {}
        
        for factor in factors:
            print(f"\nGenerating scorecard for: {factor}")
            
            task = {
                'solicitation_info': solicitation_info,
                'section_m_content': section_m_content,
                'evaluation_factor': factor,
                'config': config
            }
            
            result = self.execute(task)
            scorecards[factor] = result
            
            print(f"  ✓ {factor} scorecard complete")
        
        print("\n" + "="*70)
        print(f"✅ GENERATED {len(scorecards)} SCORECARDS")
        print("="*70)
        
        return {
            'status': 'success',
            'scorecards': scorecards,
            'metadata': {
                'factors_count': len(factors),
                'solicitation_number': solicitation_info.get('solicitation_number', 'TBD')
            }
        }
    
    def save_to_file(self, content: str, output_path: str, convert_to_pdf: bool = True) -> Dict:
        """Save evaluation scorecard to file"""
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

