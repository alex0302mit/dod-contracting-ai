"""
Section M Generator Agent: Generates Evaluation Factors for Award (Section M)

Purpose:
- Extracts technical requirements from PWS/SOO/SOW documents
- Determines appropriate evaluation methodology (Best Value vs LPTA)
- Generates evaluation factors, subfactors, and rating scales
- Creates formatted Section M document (markdown and PDF)

FAR Compliance:
- FAR Part 15.304 - Evaluation Factors and Significant Subfactors
- FAR Part 15.305 - Proposal Evaluation
- FAR Part 15.101 - Best Value Continuum
"""

from typing import Dict, Optional, List, Tuple
from pathlib import Path
import re
from datetime import datetime
from anthropic import Anthropic
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class SectionMGeneratorAgent:
    """
    Section M Generator Agent

    Generates Evaluation Factors for Award (Section M) for RFP documents

    Workflow:
    1. Analyze PWS/SOO/SOW for technical complexity and risk
    2. Determine evaluation methodology (Best Value vs LPTA)
    3. Extract technical requirements to create subfactors
    4. Generate factor weights and rating scales
    5. Populate Section M template
    6. Generate formatted document
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize Section M Generator Agent

        Args:
            api_key: Anthropic API key (optional, uses env if not provided)
            model: Claude model to use
        """
        self.api_key = api_key
        self.model = model
        self.client = Anthropic(api_key=api_key) if api_key else None

        # Load Section M template
        self.template_path = Path(__file__).parent.parent / "templates" / "section_m_template.md"
        self.template = self._load_template()

        print("✓ Section M Generator Agent initialized")

    def _load_template(self) -> str:
        """Load Section M template"""
        if not self.template_path.exists():
            raise FileNotFoundError(f"Section M template not found: {self.template_path}")

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
        Phase 4: Generate Section M with dependency context

        Args:
            requirements: Requirements/assumptions text
            context: RAG context
            dependencies: Dict of dependency_name -> content

        Returns:
            Generation result with content and citations
        """
        print("\n" + "="*70)
        print("PHASE 4: GENERATING SECTION M WITH COLLABORATION")
        print("="*70)

        # Parse requirements into project_info
        project_info = self._parse_requirements(requirements)

        # Incorporate PWS content from dependencies if available
        pws_content = ""
        if "Section C - Performance Work Statement" in dependencies:
            pws_content = dependencies["Section C - Performance Work Statement"]
            print(f"✓ Using PWS dependency ({len(pws_content)} chars)")

        # Incorporate Section L from dependencies if available
        if "Section L - Instructions to Offerors" in dependencies:
            section_l = dependencies["Section L - Instructions to Offerors"]
            print(f"✓ Using Section L dependency ({len(section_l)} chars)")
            # Extract evaluation approach mentioned in Section L
            if "best value" in section_l.lower():
                project_info['evaluation_method'] = "Best Value Trade-Off"
            elif "lpta" in section_l.lower() or "lowest price" in section_l.lower():
                project_info['evaluation_method'] = "Lowest Price Technically Acceptable"

        # Incorporate Acquisition Plan from dependencies if available
        if "Acquisition Plan" in dependencies:
            acq_plan = dependencies["Acquisition Plan"]
            print(f"✓ Using Acquisition Plan dependency ({len(acq_plan)} chars)")

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
            references_section += "This document builds upon and references:\n\n"
            if "Section C - Performance Work Statement" in dependencies:
                references_section += "- **Section C - Performance Work Statement**: Technical requirements for evaluation factors\n"
            if "Section L - Instructions to Offerors" in dependencies:
                references_section += "- **Section L - Instructions to Offerors**: Proposal format and submission requirements\n"
            if "Acquisition Plan" in dependencies:
                references_section += "- **Acquisition Plan**: Overall acquisition strategy and approach\n"
            result['content'] = content + references_section

        print("✓ Section M generated with collaboration")
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
                parts = line.split(':')
                if len(parts) > 1:
                    project_info['program_name'] = parts[1].strip()
            elif 'organization' in line.lower():
                parts = line.split(':')
                if len(parts) > 1:
                    project_info['organization'] = parts[1].strip()

        # Set defaults if not found
        project_info.setdefault('program_name', 'Acquisition Program')
        project_info.setdefault('organization', 'Department of Defense')

        return project_info

    def execute(self, task: Dict) -> Dict:
        """
        Execute Section M generation

        Args:
            task: Dictionary containing:
                - project_info: Project metadata
                - pws_content: PWS content for requirement extraction
                - config: Configuration overrides (optional)

        Returns:
            Dictionary with generation results
        """
        print("\n" + "="*70)
        print("GENERATING SECTION M: EVALUATION FACTORS FOR AWARD")
        print("="*70)

        project_info = task.get('project_info', {})
        pws_content = task.get('pws_content', '')
        config = task.get('config', {})
        program_name = project_info.get('program_name', 'Unknown')

        # NEW: Cross-reference lookup - Find PWS and IGCE for evaluation criteria
        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for PWS (technical requirements for evaluation)
                latest_pws = metadata_store.find_latest_document('pws', program_name)
                # Look for IGCE (cost comparison baseline)
                latest_igce = metadata_store.find_latest_document('igce', program_name)

                if latest_pws:
                    print(f"✅ Found PWS: {latest_pws['id']}")
                    print(f"   Performance Metrics: {len(latest_pws['extracted_data'].get('performance_metrics', []))}")
                    project_info['pws_data'] = latest_pws['extracted_data']
                    self._pws_reference = latest_pws['id']
                else:
                    print(f"⚠️  No PWS found for {program_name}")
                    self._pws_reference = None

                if latest_igce:
                    print(f"✅ Found IGCE: {latest_igce['id']}")
                    print(f"   Total Cost: {latest_igce['extracted_data'].get('total_cost_formatted', 'N/A')}")
                    project_info['igce_data'] = latest_igce['extracted_data']
                    self._igce_reference = latest_igce['id']
                else:
                    print(f"⚠️  No IGCE found for {program_name}")
                    self._igce_reference = None

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")
                self._pws_reference = None
                self._igce_reference = None
        else:
            self._pws_reference = None
            self._igce_reference = None

        # Step 1: Analyze PWS complexity
        complexity_analysis = self._analyze_pws_complexity(pws_content)
        print(f"\n  PWS Complexity: {complexity_analysis['complexity_level']}")

        # Step 2: Determine evaluation methodology
        methodology = self._determine_evaluation_methodology(
            complexity_analysis,
            config
        )
        print(f"  Evaluation Method: {methodology['method']}")

        # Step 3: Extract technical subfactors
        technical_subfactors = self._extract_technical_subfactors(pws_content, config)
        print(f"  Technical Subfactors: {len(technical_subfactors)}")

        # Step 4: Extract management subfactors
        management_subfactors = self._extract_management_subfactors(pws_content, config)
        print(f"  Management Subfactors: {len(management_subfactors)}")

        # Step 5: Determine factor weights
        factor_weights = self._calculate_factor_weights(
            complexity_analysis,
            methodology,
            config
        )

        # Step 6: Build enriched project info
        enriched_info = self._enrich_project_info(
            project_info,
            methodology,
            technical_subfactors,
            management_subfactors,
            factor_weights,
            complexity_analysis,
            config
        )

        # Step 7: Populate template
        section_m_content = self._populate_template(enriched_info)

        # Step 8: Generate statistics
        stats = self._generate_statistics(section_m_content)

        print(f"\n✓ Section M generated ({stats['word_count']} words)")
        print("="*70)

        # NEW: Save document metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving document metadata for cross-referencing...")
                metadata_store = DocumentMetadataStore()

                # Extract structured data from generated Section M
                extracted_data = {
                    'methodology': methodology,
                    'complexity_level': complexity_analysis.get('complexity_level', 'Unknown'),
                    'evaluation_factors': enriched_info.get('evaluation_factors', []),
                    'factor_weights': enriched_info.get('factor_weights', {}),
                    'rating_scale': enriched_info.get('rating_scale', 'adjectival'),
                    'word_count': stats['word_count']
                }

                # Build references dict
                references = {}
                if self._pws_reference:
                    references['pws'] = self._pws_reference
                if self._igce_reference:
                    references['igce'] = self._igce_reference

                # Save to metadata store
                doc_id = metadata_store.save_document(
                    doc_type='section_m',
                    program=program_name,
                    content=section_m_content,
                    file_path='',  # Will be set by orchestrator
                    extracted_data=extracted_data,
                    references=references
                )

                print(f"✅ Document metadata saved: {doc_id}")

            except Exception as e:
                print(f"⚠️  Failed to save document metadata: {str(e)}")

        return {
            'content': section_m_content,
            'metadata': enriched_info,
            'methodology': methodology,
            'complexity_analysis': complexity_analysis,
            'statistics': stats,
            'status': 'success'
        }

    def _analyze_pws_complexity(self, pws_content: str) -> Dict:
        """
        Analyze PWS complexity to inform evaluation approach

        Args:
            pws_content: PWS content

        Returns:
            Complexity analysis dictionary
        """
        analysis = {
            'word_count': len(pws_content.split()),
            'technical_indicators': [],
            'risk_indicators': [],
            'complexity_level': 'Moderate'
        }

        content_lower = pws_content.lower()

        # Technical complexity indicators
        technical_keywords = {
            'software development': 'Custom software development',
            'integration': 'System integration',
            'cybersecurity': 'Cybersecurity requirements',
            'cloud': 'Cloud infrastructure',
            'ai': 'Artificial intelligence',
            'machine learning': 'Machine learning',
            'data analytics': 'Data analytics',
            'real-time': 'Real-time processing',
            'scalability': 'Scalability requirements',
            'interoperability': 'Interoperability'
        }

        for keyword, indicator in technical_keywords.items():
            if keyword in content_lower:
                analysis['technical_indicators'].append(indicator)

        # Risk indicators
        risk_keywords = {
            'critical': 'Mission-critical system',
            'classified': 'Classified information',
            'compliance': 'Regulatory compliance',
            '24/7': '24/7 operations',
            'high availability': 'High availability requirements',
            'disaster recovery': 'Disaster recovery',
            'multi-site': 'Multi-site deployment'
        }

        for keyword, indicator in risk_keywords.items():
            if keyword in content_lower:
                analysis['risk_indicators'].append(indicator)

        # Determine complexity level
        complexity_score = (
            len(analysis['technical_indicators']) +
            len(analysis['risk_indicators']) * 2 +
            (1 if analysis['word_count'] > 5000 else 0)
        )

        if complexity_score <= 3:
            analysis['complexity_level'] = 'Low'
        elif complexity_score <= 8:
            analysis['complexity_level'] = 'Moderate'
        else:
            analysis['complexity_level'] = 'High'

        return analysis

    def _determine_evaluation_methodology(
        self,
        complexity_analysis: Dict,
        config: Dict
    ) -> Dict:
        """
        Determine evaluation methodology (Best Value vs LPTA)

        Args:
            complexity_analysis: PWS complexity analysis
            config: Configuration overrides

        Returns:
            Methodology information
        """
        # Check for config override
        if 'evaluation_method' in config:
            method = config['evaluation_method']
        else:
            # Default: Best Value for moderate/high complexity, LPTA for low
            if complexity_analysis['complexity_level'] in ['Moderate', 'High']:
                method = 'Best Value Trade-Off'
            else:
                method = 'Lowest Price Technically Acceptable (LPTA)'

        methodology = {
            'method': method,
            'is_best_value': 'Best Value' in method,
            'is_lpta': 'LPTA' in method,
            'rationale': self._generate_methodology_rationale(
                method,
                complexity_analysis
            )
        }

        return methodology

    def _generate_methodology_rationale(
        self,
        method: str,
        complexity_analysis: Dict
    ) -> str:
        """Generate rationale for evaluation methodology selection"""
        if 'Best Value' in method:
            return (
                f"Given the {complexity_analysis['complexity_level'].lower()} "
                f"technical complexity and the need to assess technical approach quality, "
                f"a Best Value Trade-Off approach is appropriate to ensure the Government "
                f"receives the best overall value rather than simply the lowest price."
            )
        else:
            return (
                f"Given the {complexity_analysis['complexity_level'].lower()} "
                f"technical complexity and well-defined requirements, "
                f"a Lowest Price Technically Acceptable (LPTA) approach is appropriate "
                f"to minimize cost while meeting minimum technical standards."
            )

    def _extract_technical_subfactors(
        self,
        pws_content: str,
        config: Dict
    ) -> List[Dict]:
        """
        Extract technical subfactors from PWS

        Args:
            pws_content: PWS content
            config: Configuration overrides

        Returns:
            List of technical subfactor dictionaries
        """
        # Check for config override
        if 'technical_subfactors' in config:
            return config['technical_subfactors']

        subfactors = []

        content_lower = pws_content.lower()

        # Common technical subfactors based on PWS content
        subfactor_patterns = {
            'Technical Approach and Methodology': ['approach', 'methodology', 'solution'],
            'System Architecture and Design': ['architecture', 'design', 'system'],
            'Development and Implementation': ['development', 'implementation', 'deploy'],
            'Cybersecurity and Information Assurance': ['security', 'cybersecurity', 'IA'],
            'Performance and Scalability': ['performance', 'scalability', 'capacity'],
            'Quality Assurance and Testing': ['quality', 'testing', 'QA'],
            'Innovation and Best Practices': ['innovation', 'best practice', 'modern'],
            'Compliance with Standards': ['compliance', 'standard', 'specification'],
            'Integration and Interoperability': ['integration', 'interoperability', 'interface'],
            'Data Management and Analytics': ['data', 'analytics', 'database']
        }

        # Detect which subfactors are relevant
        for subfactor_name, keywords in subfactor_patterns.items():
            if any(keyword in content_lower for keyword in keywords):
                subfactors.append({
                    'name': subfactor_name,
                    'description': f"Evaluation of the offeror's {subfactor_name.lower()}"
                })

        # If no subfactors detected, use defaults
        if not subfactors:
            subfactors = [
                {'name': 'Technical Approach', 'description': 'Overall technical solution'},
                {'name': 'Technical Capability', 'description': 'Demonstrated technical capability'},
                {'name': 'Risk Management', 'description': 'Technical risk mitigation approach'}
            ]

        # Limit to top 5-7 subfactors
        return subfactors[:7]

    def _extract_management_subfactors(
        self,
        pws_content: str,
        config: Dict
    ) -> List[Dict]:
        """
        Extract management subfactors from PWS

        Args:
            pws_content: PWS content
            config: Configuration overrides

        Returns:
            List of management subfactor dictionaries
        """
        # Check for config override
        if 'management_subfactors' in config:
            return config['management_subfactors']

        subfactors = []

        content_lower = pws_content.lower()

        # Common management subfactors
        subfactor_patterns = {
            'Project Management Plan': ['project management', 'schedule', 'milestone'],
            'Organizational Structure': ['organization', 'team', 'structure'],
            'Quality Management': ['quality', 'QA', 'QC'],
            'Risk Management': ['risk', 'mitigation', 'contingency'],
            'Communication Plan': ['communication', 'reporting', 'status'],
            'Resource Management': ['resource', 'staffing', 'allocation'],
            'Performance Monitoring': ['monitoring', 'tracking', 'metric']
        }

        # Detect which subfactors are relevant
        for subfactor_name, keywords in subfactor_patterns.items():
            if any(keyword in content_lower for keyword in keywords):
                subfactors.append({
                    'name': subfactor_name,
                    'description': f"Evaluation of the offeror's {subfactor_name.lower()}"
                })

        # If no subfactors detected, use defaults
        if not subfactors:
            subfactors = [
                {'name': 'Project Management', 'description': 'Overall project management approach'},
                {'name': 'Organization', 'description': 'Organizational structure and resources'},
                {'name': 'Risk Management', 'description': 'Management risk mitigation'}
            ]

        # Limit to top 4-5 subfactors
        return subfactors[:5]

    def _calculate_factor_weights(
        self,
        complexity_analysis: Dict,
        methodology: Dict,
        config: Dict
    ) -> Dict:
        """
        Calculate factor weights based on complexity and methodology

        Args:
            complexity_analysis: PWS complexity analysis
            methodology: Evaluation methodology
            config: Configuration overrides

        Returns:
            Factor weights dictionary
        """
        # Check for config override
        if 'factor_weights' in config:
            return config['factor_weights']

        weights = {}

        if methodology['is_lpta']:
            # LPTA: All factors equal for minimum threshold
            weights = {
                'technical': 'Pass/Fail',
                'management': 'Pass/Fail',
                'past_performance': 'Pass/Fail',
                'cost': 'Determining Factor',
                'non_cost_comparison': 'All non-cost factors equally weighted'
            }
        else:
            # Best Value: Weight based on complexity
            if complexity_analysis['complexity_level'] == 'High':
                weights = {
                    'technical': '40%',
                    'management': '30%',
                    'past_performance': '20%',
                    'cost': '10%',
                    'non_cost_comparison': 'Non-cost factors, when combined, are significantly more important than cost'
                }
            elif complexity_analysis['complexity_level'] == 'Moderate':
                weights = {
                    'technical': '35%',
                    'management': '25%',
                    'past_performance': '20%',
                    'cost': '20%',
                    'non_cost_comparison': 'Non-cost factors, when combined, are more important than cost'
                }
            else:
                weights = {
                    'technical': '30%',
                    'management': '20%',
                    'past_performance': '20%',
                    'cost': '30%',
                    'non_cost_comparison': 'Non-cost factors and cost are approximately equal in importance'
                }

        return weights

    def _enrich_project_info(
        self,
        project_info: Dict,
        methodology: Dict,
        technical_subfactors: List[Dict],
        management_subfactors: List[Dict],
        factor_weights: Dict,
        complexity_analysis: Dict,
        config: Dict
    ) -> Dict:
        """
        Enrich project information with evaluation-specific data

        Args:
            project_info: Base project information
            methodology: Evaluation methodology
            technical_subfactors: Technical subfactors list
            management_subfactors: Management subfactors list
            factor_weights: Factor weights
            complexity_analysis: Complexity analysis
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

        # Set date issued
        if 'date_issued' not in enriched:
            enriched['date_issued'] = datetime.now().strftime("%B %d, %Y")

        # Evaluation methodology
        enriched['evaluation_method'] = methodology['method']
        enriched['evaluation_methodology_description'] = methodology['rationale']

        # Factor information
        enriched['technical_weight'] = factor_weights['technical']
        enriched['management_weight'] = factor_weights['management']
        enriched['past_performance_weight'] = factor_weights['past_performance']
        enriched['cost_weight'] = factor_weights['cost']
        enriched['non_cost_comparison'] = factor_weights['non_cost_comparison']

        # Technical subfactors
        enriched['technical_subfactors_list'] = self._format_subfactors_list(
            technical_subfactors
        )
        enriched['technical_subfactors_detail'] = self._format_subfactors_detail(
            technical_subfactors,
            methodology['is_best_value']
        )

        # Management subfactors
        enriched['management_subfactors_list'] = self._format_subfactors_list(
            management_subfactors
        )
        enriched['management_subfactors_detail'] = self._format_subfactors_detail(
            management_subfactors,
            methodology['is_best_value']
        )

        # Rating scale
        if methodology['is_best_value']:
            enriched['rating_scale_table'] = self._create_adjectival_rating_table()
            enriched['rating_scale_description'] = "Adjectival ratings (Outstanding to Unacceptable)"
        else:
            enriched['rating_scale_table'] = self._create_lpta_rating_table()
            enriched['rating_scale_description'] = "Pass/Fail for minimum acceptability"

        # Past performance lookback
        enriched['past_performance_lookback'] = config.get('past_performance_lookback', '3')

        # Trade-off statement
        enriched['tradeoff_statement'] = self._generate_tradeoff_statement(
            methodology,
            factor_weights
        )

        # Contracting officer info
        enriched.setdefault('contracting_officer', 'John Smith')
        enriched.setdefault('ko_email', 'john.smith@agency.mil')

        return enriched

    def _format_subfactors_list(self, subfactors: List[Dict]) -> str:
        """Format subfactors as bulleted list"""
        return "\n".join([f"- {sf['name']}" for sf in subfactors])

    def _format_subfactors_detail(
        self,
        subfactors: List[Dict],
        is_best_value: bool
    ) -> str:
        """Format subfactors with detailed descriptions"""
        sections = []

        for i, sf in enumerate(subfactors, 1):
            section = f"**Subfactor {i}: {sf['name']}**\n\n"
            section += f"{sf['description']}.\n\n"

            if is_best_value:
                section += "The Government will evaluate:\n"
                section += f"- The comprehensiveness and feasibility of the proposed {sf['name'].lower()}\n"
                section += f"- The likelihood that the approach will successfully meet requirements\n"
                section += f"- The degree of risk associated with the proposed {sf['name'].lower()}\n"
            else:
                section += "The Government will determine whether the proposal meets the minimum acceptable standard.\n"

            sections.append(section)

        return "\n".join(sections)

    def _create_adjectival_rating_table(self) -> str:
        """Create adjectival rating scale table for Best Value"""
        return """| Rating | Description |
|--------|-------------|
| **Outstanding** | Proposal meets requirements and significantly exceeds in multiple areas with high probability of success and minimal risk |
| **Good** | Proposal meets requirements and exceeds in some areas with high probability of success and low risk |
| **Acceptable** | Proposal meets requirements with acceptable probability of success and acceptable risk |
| **Marginal** | Proposal meets some requirements but has deficiencies requiring clarification or revision; moderate risk |
| **Unacceptable** | Proposal does not meet requirements and/or contains major deficiencies; high risk or infeasible |"""

    def _create_lpta_rating_table(self) -> str:
        """Create Pass/Fail rating table for LPTA"""
        return """| Rating | Description |
|--------|-------------|
| **Acceptable (Pass)** | Proposal meets all minimum technical requirements and demonstrates acceptable capability |
| **Unacceptable (Fail)** | Proposal fails to meet one or more minimum technical requirements |"""

    def _generate_tradeoff_statement(
        self,
        methodology: Dict,
        factor_weights: Dict
    ) -> str:
        """Generate trade-off decision statement"""
        if methodology['is_lpta']:
            return (
                "All technically acceptable proposals will be considered for award. "
                "Award will be made to the offeror whose proposal is technically acceptable "
                "and represents the lowest evaluated price."
            )
        else:
            return (
                f"The Government will make award to the offeror whose proposal provides "
                f"the best value to the Government. {factor_weights['non_cost_comparison']}. "
                f"The Government may award to other than the lowest priced offeror or other than "
                f"the highest technically rated offeror if the Source Selection Authority determines "
                f"that the selected proposal represents the best value to the Government."
            )

    def _populate_template(self, project_info: Dict) -> str:
        """
        Populate Section M template with project information

        Args:
            project_info: Enriched project information

        Returns:
            Populated Section M content
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
        org_code = "W911"
        if "NAVY" in organization.upper():
            org_code = "N000"
        elif "AIR FORCE" in organization.upper():
            org_code = "FA86"
        elif "ARMY" in organization.upper():
            org_code = "W911"

        fiscal_year = datetime.now().year % 100
        import random
        sequence = random.randint(1000, 9999)

        return f"{org_code}XX-{fiscal_year:02d}-R-{sequence:04d}"

    def _generate_statistics(self, content: str) -> Dict:
        """Generate statistics about Section M document"""
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
        Save Section M to file

        Args:
            content: Section M content
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
    """Test Section M Generator Agent"""
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
        'ko_email': 'john.doe@army.mil'
    }

    # Sample PWS content (for analysis)
    pws_content = """
    The contractor shall develop and deploy a cloud-based inventory management system
    with advanced cybersecurity controls, real-time data analytics capabilities,
    system integration with existing DoD systems, and 24/7 support.
    The system must be scalable, highly available, and comply with all applicable
    cybersecurity standards including NIST 800-53 and DFARS requirements.
    """ * 50  # Simulate high complexity

    # Initialize agent
    agent = SectionMGeneratorAgent(api_key=api_key)

    # Execute
    task = {
        'project_info': project_info,
        'pws_content': pws_content,
        'config': {}
    }

    result = agent.execute(task)

    # Save
    output_path = "outputs/section_m/section_m_evaluation_factors.md"
    files = agent.save_to_file(result['content'], output_path)

    print(f"\n✅ Section M generated successfully!")
    print(f"   Markdown: {files['markdown']}")
    if 'pdf' in files:
        print(f"   PDF: {files['pdf']}")


if __name__ == "__main__":
    main()
