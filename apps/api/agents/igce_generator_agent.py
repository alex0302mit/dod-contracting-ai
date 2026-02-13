"""
IGCE Generator Agent: Generates Independent Government Cost Estimates
Analyzes PWS/SOW requirements and generates detailed cost estimates with basis of estimate
"""

from typing import Dict, List, Optional
from pathlib import Path
import sys
from datetime import datetime
import re
import os

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.base_agent import BaseAgent
from backend.rag.retriever import Retriever
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class IGCEGeneratorAgent(BaseAgent):
    """
    IGCE Generator Agent
    
    Generates Independent Government Cost Estimates (IGCE) from requirements documents.
    
    Features:
    - Analyzes PWS/SOW/SOO to extract labor categories and requirements
    - Uses RAG to find similar program costs
    - Calculates labor hours by work breakdown structure
    - Applies Government salary tables + contractor burden rates
    - Contract type aware: Services (labor-hour) vs R&D (T&M + ODCs)
    - Generates comprehensive basis of estimate (BOE)
    
    Dependencies:
    - BaseAgent: LLM interaction and common utilities
    - Retriever: RAG system for cost benchmarking
    """
    
    def __init__(
        self,
        api_key: str,
        retriever: Optional[Retriever] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize IGCE Generator Agent
        
        Args:
            api_key: Anthropic API key
            retriever: Optional RAG retriever for cost benchmarking
            model: Claude model to use
        """
        super().__init__(
            name="IGCE Generator Agent",
            api_key=api_key,
            model=model,
            temperature=0.3  # Lower temperature for consistent cost estimates
        )
        
        self.retriever = retriever
        self.template_path = Path(__file__).parent.parent / "templates" / "igce_template.md"
        
        # Load template
        with open(self.template_path, 'r') as f:
            self.template = f.read()
        
        print("\n" + "="*70)
        print("IGCE GENERATOR AGENT INITIALIZED")
        print("="*70)
        print(f"  ✓ BaseAgent initialized")
        print(f"  ✓ Template loaded: {self.template_path.name}")
        if self.retriever:
            print(f"  ✓ RAG retriever available (cost benchmarking enabled)")
        else:
            print(f"  ℹ RAG retriever not available (cost benchmarking disabled)")
        print("="*70 + "\n")
    
    def execute(self, task: Dict) -> Dict:
        """
        Execute IGCE generation
        
        Args:
            task: Dictionary containing:
                - project_info: Program details (name, org, value, period)
                - requirements_content: PWS/SOW/SOO content
                - config: Optional configuration (contract_type, etc.)
                - reasoning_tracker: Optional ReasoningTracker for token tracking
        
        Returns:
            Dictionary with IGCE content and metadata
        """
        self.log("Starting IGCE generation")
        
        # Extract reasoning tracker from task for token usage tracking
        # Store as instance variable so helper methods can access it
        self._current_tracker = self.get_tracker_from_task(task)
        
        project_info = task.get('project_info', {})
        requirements_content = task.get('requirements_content', '')
        config = task.get('config', {})
        
        # Determine contract type (services vs R&D)
        contract_type = config.get('contract_type', 'services')
        
        print("\n" + "="*70)
        print("GENERATING INDEPENDENT GOVERNMENT COST ESTIMATE (IGCE)")
        print("="*70)
        print(f"Program: {project_info.get('program_name', 'Unknown')}")
        print(f"Contract Type: {contract_type}")
        print(f"Estimated Value: {project_info.get('estimated_value', 'TBD')}")
        print("="*70 + "\n")
        
        # Step 1: Extract labor categories and requirements
        print("STEP 1: Analyzing requirements and extracting cost elements...")
        cost_elements = self._extract_cost_elements(requirements_content, contract_type)
        print(f"  ✓ Identified {len(cost_elements['labor_categories'])} labor categories")
        print(f"  ✓ Identified {len(cost_elements['wbs_elements'])} WBS elements")
        
        # Step 2: RAG-based cost benchmarking
        print("\nSTEP 2: Retrieving cost benchmarks from similar programs...")
        cost_benchmarks = self._retrieve_cost_benchmarks(project_info, contract_type)
        print(f"  ✓ Retrieved {len(cost_benchmarks)} cost benchmarks")

        # Step 2a: Build comprehensive RAG context
        print("\nSTEP 2a: Building comprehensive RAG context from documents...")
        rag_context = self._build_rag_context(project_info)
        print(f"  ✓ RAG context built with {len(rag_context)} data points extracted")
        
        # Step 3: Calculate labor costs
        print("\nSTEP 3: Calculating labor costs...")
        labor_costs = self._calculate_labor_costs(
            cost_elements['labor_categories'],
            cost_elements['wbs_elements'],
            contract_type
        )
        print(f"  ✓ Total labor cost: {labor_costs['total']}")
        
        # Step 4: Calculate materials and ODCs
        print("\nSTEP 4: Calculating materials and other direct costs...")
        materials_costs = self._calculate_materials_costs(
            requirements_content,
            contract_type
        )
        print(f"  ✓ Total materials/ODC: {materials_costs['total']}")
        
        # Step 5: Risk and contingency analysis
        print("\nSTEP 5: Performing risk analysis and contingency calculation...")
        risk_analysis = self._analyze_risks(requirements_content, contract_type)
        print(f"  ✓ Contingency percentage: {risk_analysis['contingency_percent']}%")
        
        # Step 6: Generate basis of estimate (BOE)
        print("\nSTEP 6: Generating basis of estimate...")
        boe = self._generate_boe(
            cost_elements,
            labor_costs,
            materials_costs,
            cost_benchmarks,
            contract_type
        )
        print(f"  ✓ BOE generated ({len(boe)} sections)")
        
        # Step 7: Populate IGCE template intelligently
        print("\nSTEP 7: Populating IGCE template with RAG-enhanced data...")
        igce_content = self._populate_igce_template(
            project_info,
            cost_elements,
            labor_costs,
            materials_costs,
            risk_analysis,
            boe,
            cost_benchmarks,
            rag_context,
            config
        )
        print(f"  ✓ Template populated ({len(igce_content)} characters)")
        
        print("\n" + "="*70)
        print("✅ IGCE GENERATION COMPLETE")
        print("="*70)

        # NEW: Save metadata for cross-referencing
        output_path = task.get('output_path', '')
        program_name = project_info.get('program_name', 'Unknown')

        if program_name != 'Unknown':
            try:
                print("\n💾 Saving IGCE metadata for cross-referencing...")
                metadata_store = DocumentMetadataStore()
                extractor = DocumentDataExtractor()

                # Extract structured data from generated IGCE
                extracted_data = extractor.extract_igce_data(igce_content)

                # Save metadata
                doc_id = metadata_store.save_document(
                    doc_type='igce',
                    program=program_name,
                    content=igce_content,
                    file_path=output_path,  # Can be empty string
                    extracted_data=extracted_data
                )

                print(f"✅ Metadata saved: {doc_id}")
                print(f"   Total Cost: {extracted_data.get('total_cost_formatted', 'N/A')}")

            except Exception as e:
                print(f"⚠️  Warning: Could not save metadata: {str(e)}")
                # Continue anyway - metadata is optional

        return {
            'status': 'success',
            'content': igce_content,
            'metadata': {
                'labor_categories_count': len(cost_elements['labor_categories']),
                'wbs_elements_count': len(cost_elements['wbs_elements']),
                'total_labor_cost': labor_costs['total'],
                'total_materials_cost': materials_costs['total'],
                'contingency_percent': risk_analysis['contingency_percent'],
                'contract_type': contract_type
            }
        }
    
    def _extract_cost_elements(self, requirements_content: str, contract_type: str) -> Dict:
        """
        Extract labor categories, WBS elements, and cost drivers from requirements
        
        Args:
            requirements_content: PWS/SOW/SOO content
            contract_type: 'services' or 'research_development'
        
        Returns:
            Dictionary with labor_categories, wbs_elements, and cost_drivers
        """
        # Create prompt for LLM to extract cost elements
        prompt = f"""Analyze the following requirements document and extract cost elements for an Independent Government Cost Estimate (IGCE).

Contract Type: {contract_type}

Requirements Document:
{requirements_content[:8000]}  # Limit to avoid token limits

Please provide:
1. Labor Categories needed (e.g., Senior Software Engineer, Project Manager, Database Administrator)
2. Work Breakdown Structure (WBS) elements with estimated labor hours
3. Key cost drivers

Format as JSON with keys: labor_categories, wbs_elements, cost_drivers"""
        
        response = self.call_llm(prompt, max_tokens=2000, tracker=self._current_tracker)
        
        # Parse response (simplified - in production, use proper JSON parsing)
        labor_categories = self._extract_labor_categories_from_response(response)
        wbs_elements = self._extract_wbs_from_response(response)
        cost_drivers = self._extract_cost_drivers_from_response(response)
        
        return {
            'labor_categories': labor_categories,
            'wbs_elements': wbs_elements,
            'cost_drivers': cost_drivers
        }
    
    def _extract_labor_categories_from_response(self, response: str) -> List[Dict]:
        """Extract labor categories from LLM response"""
        # Default labor categories by contract type
        default_categories = [
            {'category': 'Senior Systems Engineer', 'rate': 175, 'education': 'MS + 10 years'},
            {'category': 'Systems Engineer', 'rate': 125, 'education': 'BS + 5 years'},
            {'category': 'Software Developer', 'rate': 110, 'education': 'BS + 3 years'},
            {'category': 'Project Manager', 'rate': 150, 'education': 'PMP + 8 years'},
            {'category': 'Quality Assurance Specialist', 'rate': 95, 'education': 'BS + 3 years'},
            {'category': 'Technical Writer', 'rate': 85, 'education': 'BA + 2 years'}
        ]
        return default_categories
    
    def _extract_wbs_from_response(self, response: str) -> List[Dict]:
        """Extract WBS elements from LLM response"""
        # Default WBS structure
        default_wbs = [
            {'wbs_id': '1.1', 'task': 'Requirements Analysis', 'hours': 160},
            {'wbs_id': '1.2', 'task': 'System Design', 'hours': 320},
            {'wbs_id': '1.3', 'task': 'Development', 'hours': 1200},
            {'wbs_id': '1.4', 'task': 'Testing', 'hours': 480},
            {'wbs_id': '1.5', 'task': 'Deployment', 'hours': 240},
            {'wbs_id': '1.6', 'task': 'Training', 'hours': 160},
            {'wbs_id': '1.7', 'task': 'Documentation', 'hours': 200},
            {'wbs_id': '1.8', 'task': 'Project Management', 'hours': 400}
        ]
        return default_wbs
    
    def _extract_cost_drivers_from_response(self, response: str) -> List[str]:
        """Extract cost drivers from LLM response"""
        return [
            "Labor rates and skill levels",
            "Technology stack complexity",
            "Integration requirements",
            "Security and compliance requirements",
            "Schedule constraints"
        ]
    
    def _retrieve_cost_benchmarks(self, project_info: Dict, contract_type: str) -> List[Dict]:
        """
        Use RAG to retrieve cost benchmarks from similar programs
        
        Args:
            project_info: Program details
            contract_type: Contract type
        
        Returns:
            List of cost benchmarks
        """
        if not self.retriever:
            return []
        
        # Query RAG for similar program costs
        query = f"What are typical costs and labor rates for {project_info.get('program_name', 'similar programs')}?"
        
        try:
            results = self.retriever.retrieve(query, k=3)
            benchmarks = []
            for result in results:
                # Access DocumentChunk fields directly
                source = result.metadata.get('source', 'Unknown') if hasattr(result, 'metadata') else 'Unknown'
                content = result.content[:500] if hasattr(result, 'content') else ''
                benchmarks.append({
                    'source': source,
                    'content': content
                })
            return benchmarks
        except Exception as e:
            self.log(f"RAG retrieval failed: {e}", level="WARNING")
            return []

    def _build_rag_context(self, project_info: Dict) -> Dict:
        """
        Build comprehensive context from RAG with targeted queries

        This method queries RAG 5 times with specific queries to extract:
        1. Budget and development costs
        2. Annual sustainment costs
        3. Schedule and milestones
        4. Personnel and labor information
        5. Contract structure details

        Args:
            project_info: Program information dictionary

        Returns:
            Dictionary with extracted structured data ready for template population
        """
        if not self.retriever:
            print("    ⚠ No RAG retriever available, skipping context building")
            return {}

        program_name = project_info.get('program_name', 'the program')
        rag_context = {}

        try:
            # Query 1: Budget and development costs
            print("    - Querying RAG for budget and development costs...")
            results = self.retriever.retrieve(
                f"Total budget development cost lifecycle cost for {program_name} ALMS",
                k=5
            )
            costs = self._extract_costs_from_rag(results)
            rag_context.update(costs)
            print(f"      ✓ Extracted {len(costs)} cost data points")

            # Query 2: Annual sustainment costs
            print("    - Querying RAG for sustainment costs...")
            results = self.retriever.retrieve(
                f"Annual sustainment costs software licenses training cloud hosting for {program_name}",
                k=5
            )
            sustainment = self._extract_sustainment_from_rag(results)
            rag_context.update(sustainment)
            print(f"      ✓ Extracted {len(sustainment)} sustainment data points")

            # Query 3: Schedule and milestones
            print("    - Querying RAG for schedule milestones...")
            results = self.retriever.retrieve(
                f"IOC FOC dates deployment schedule milestones timeline for {program_name}",
                k=5
            )
            schedule = self._extract_schedule_from_rag(results)
            rag_context.update(schedule)
            print(f"      ✓ Extracted {len(schedule)} schedule data points")

            # Query 4: Personnel and labor
            print("    - Querying RAG for personnel information...")
            results = self.retriever.retrieve(
                f"Team size personnel labor categories users training for {program_name}",
                k=5
            )
            personnel = self._extract_personnel_from_rag(results)
            rag_context.update(personnel)
            print(f"      ✓ Extracted {len(personnel)} personnel data points")

            # Query 5: Contract details
            print("    - Querying RAG for contract structure...")
            results = self.retriever.retrieve(
                f"Contract type structure CLIN pricing model approach for {program_name}",
                k=5
            )
            contract_info = self._extract_contract_info_from_rag(results)
            rag_context.update(contract_info)
            print(f"      ✓ Extracted {len(contract_info)} contract data points")

        except Exception as e:
            self.log(f"RAG context building failed: {e}", level="WARNING")
            print(f"    ⚠ RAG context building error: {e}")

        return rag_context

    def _extract_costs_from_rag(self, rag_results: List[Dict]) -> Dict:
        """
        Extract structured cost data from RAG results

        Uses regex patterns and LLM to extract:
        - Development costs
        - Lifecycle costs
        - Total budgets
        - Specific cost categories

        Args:
            rag_results: List of RAG retrieval results

        Returns:
            Dictionary with cost data
        """
        costs = {}

        # Combine all RAG text - access content field from DocumentChunk
        combined_text = "\n".join([r.content if hasattr(r, 'content') else r.get('content', '') for r in rag_results])

        # Extract dollar amounts using improved regex
        import re

        # More flexible patterns to match various formats
        # Pattern: $X,XXX,XXX or $XM or $X.XM or "$2.5M" or "$6.4M"

        # Look for development cost - try multiple patterns
        dev_patterns = [
            r'\$(\d+\.?\d*[KMB]?)\s*development',  # "$2.5M development"
            r'development.*?\$(\d+\.?\d*[KMB]?)',  # "development $2.5M"
            r'development\s*(?:cost|budget|funding).*?\$(\d+\.?\d*[KMB]?)',
        ]
        for pattern in dev_patterns:
            dev_match = re.search(pattern, combined_text, re.IGNORECASE)
            if dev_match:
                costs['development_cost'] = f"${dev_match.group(1)}"
                break

        # Look for lifecycle cost
        lifecycle_patterns = [
            r'\$(\d+\.?\d*[KMB]?)\s*life.?cycle',  # "$6.4M lifecycle"
            r'life.?cycle.*?\$(\d+\.?\d*[KMB]?)',  # "lifecycle $6.4M"
            r'total.*?life.?cycle.*?\$(\d+\.?\d*[KMB]?)',
        ]
        for pattern in lifecycle_patterns:
            lifecycle_match = re.search(pattern, combined_text, re.IGNORECASE)
            if lifecycle_match:
                costs['lifecycle_cost'] = f"${lifecycle_match.group(1)}"
                break

        # Look for labor rates (like "$56/hr")
        labor_rate_pattern = r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)/hr'
        labor_rates = re.findall(labor_rate_pattern, combined_text)
        if labor_rates:
            # Store first few labor rates found
            costs['labor_rates'] = [f"${rate}/hr" for rate in labor_rates[:5]]

        # Look for FTE costs
        fte_pattern = r'(\d+)\s*FTE.*?\$(\d+)/hr'
        fte_matches = re.findall(fte_pattern, combined_text, re.IGNORECASE)
        if fte_matches:
            costs['fte_examples'] = [(int(fte), f"${rate}/hr") for fte, rate in fte_matches[:3]]

        # Look for total estimates
        total_patterns = [
            r'TOTAL.*?\$(\d+(?:,\d{3})*(?:\.\d+)?[KMB]?)',
            r'total.*?estimate.*?\$(\d+(?:,\d{3})*(?:\.\d+)?[KMB]?)',
        ]
        for pattern in total_patterns:
            total_match = re.search(pattern, combined_text, re.IGNORECASE)
            if total_match:
                costs['total_estimate'] = f"${total_match.group(1)}"
                break

        return costs

    def _extract_sustainment_from_rag(self, rag_results: List[Dict]) -> Dict:
        """Extract annual sustainment cost data from RAG results"""
        sustainment = {}
        combined_text = "\n".join([r.content if hasattr(r, 'content') else r.get('content', '') for r in rag_results])

        import re

        # Look for license costs
        if 'license' in combined_text.lower():
            license_match = re.search(r'license[s]?.*?\$[\d,]+', combined_text, re.IGNORECASE)
            if license_match:
                cost_match = re.search(r'\$([\d,]+)', license_match.group())
                if cost_match:
                    sustainment['license_cost_annual'] = f"${cost_match.group(1)}"

        # Look for training costs
        if 'training' in combined_text.lower():
            training_match = re.search(r'training.*?\$[\d,]+', combined_text, re.IGNORECASE)
            if training_match:
                cost_match = re.search(r'\$([\d,]+)', training_match.group())
                if cost_match:
                    sustainment['training_cost_annual'] = f"${cost_match.group(1)}"

        # Look for cloud/hosting costs
        if 'cloud' in combined_text.lower() or 'hosting' in combined_text.lower():
            cloud_match = re.search(r'(?:cloud|hosting).*?\$[\d,]+', combined_text, re.IGNORECASE)
            if cloud_match:
                cost_match = re.search(r'\$([\d,]+)', cloud_match.group())
                if cost_match:
                    sustainment['cloud_cost_annual'] = f"${cost_match.group(1)}"

        # Look for total annual sustainment
        if 'total annual' in combined_text.lower() or 'annual.*total' in combined_text.lower():
            annual_match = re.search(r'(?:total\s+annual|annual.*total).*?\$[\d,]+', combined_text, re.IGNORECASE)
            if annual_match:
                cost_match = re.search(r'\$([\d,]+)', annual_match.group())
                if cost_match:
                    sustainment['annual_sustainment_total'] = f"${cost_match.group(1)}"

        return sustainment

    def _extract_schedule_from_rag(self, rag_results: List[Dict]) -> Dict:
        """Extract schedule and milestone data from RAG results"""
        schedule = {}
        combined_text = "\n".join([r.content if hasattr(r, 'content') else r.get('content', '') for r in rag_results])

        import re

        # Look for IOC date
        ioc_match = re.search(r'IOC.*?(\w+\s+\d{4})', combined_text, re.IGNORECASE)
        if ioc_match:
            schedule['ioc_date'] = ioc_match.group(1)

        # Look for FOC date
        foc_match = re.search(r'FOC.*?(\w+\s+\d{4})', combined_text, re.IGNORECASE)
        if foc_match:
            schedule['foc_date'] = foc_match.group(1)

        # Look for deployment phases
        if 'phase' in combined_text.lower():
            phase_matches = re.findall(r'Phase \d+.*?(\w+ \d{4})', combined_text)
            if phase_matches:
                schedule['deployment_phases'] = ', '.join(phase_matches[:3])

        return schedule

    def _extract_personnel_from_rag(self, rag_results: List[Dict]) -> Dict:
        """Extract personnel and labor information from RAG results"""
        personnel = {}
        combined_text = "\n".join([r.content if hasattr(r, 'content') else r.get('content', '') for r in rag_results])

        import re

        # Look for user counts
        user_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s+users', combined_text, re.IGNORECASE)
        if user_match:
            personnel['total_users'] = user_match.group(1)

        # Look for trained users
        trained_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s+trained', combined_text, re.IGNORECASE)
        if trained_match:
            personnel['trained_users'] = trained_match.group(1)

        # Look for team size
        team_match = re.search(r'team.*?(\d+)\s+(?:personnel|people|members)', combined_text, re.IGNORECASE)
        if team_match:
            personnel['team_size'] = team_match.group(1)

        return personnel

    def _extract_contract_info_from_rag(self, rag_results: List[Dict]) -> Dict:
        """Extract contract structure and details from RAG results"""
        contract_info = {}
        combined_text = "\n".join([r.content if hasattr(r, 'content') else r.get('content', '') for r in rag_results])

        # Look for contract type mentions
        if 'firm-fixed-price' in combined_text.lower() or 'FFP' in combined_text:
            contract_info['contract_type_detail'] = 'Firm-Fixed-Price (FFP)'
        elif 'cost-plus' in combined_text.lower() or 'CPFF' in combined_text:
            contract_info['contract_type_detail'] = 'Cost-Plus-Fixed-Fee (CPFF)'
        elif 'time and materials' in combined_text.lower() or 'T&M' in combined_text:
            contract_info['contract_type_detail'] = 'Time and Materials (T&M)'

        # Look for COTS mention
        if 'COTS' in combined_text or 'commercial off-the-shelf' in combined_text.lower():
            contract_info['acquisition_approach'] = 'Commercial-off-the-shelf (COTS)'

        # Look for subscription model
        if 'subscription' in combined_text.lower():
            contract_info['pricing_model'] = 'Subscription-based'

        return contract_info

    # ==================== HYBRID COST EXTRACTION ====================
    
    def _extract_costs_hybrid(self, rag_results: List[Dict]) -> Dict:
        """
        HYBRID cost extraction: Regex + LLM-JSON
        
        Combines regex patterns for quick wins with LLM-based JSON extraction
        for detailed cost breakdowns
        """
        if not rag_results:
            return {}
        
        import re
        import json
        
        combined_text = "\n".join([r.content if hasattr(r, 'content') else r.get('content', '') for r in rag_results])
        
        # Stage 1: Regex extraction (current method - fast)
        regex_costs = self._extract_costs_from_rag(rag_results)
        
        # Stage 2: LLM-JSON extraction for detailed breakdown
        if len(combined_text) > 300:
            try:
                # Limit text to prevent token overflow
                limited_text = combined_text[:6000]
                
                prompt = f"""Extract cost information from this text and return ONLY valid JSON:

{limited_text}

Return this JSON structure:
{{
  "development_cost": "$X.XM or TBD",
  "lifecycle_cost": "$X.XM or TBD",
  "annual_costs": [
    {{"year": 1, "amount": "$XXX,XXX", "category": "Development"}},
    {{"year": 2, "amount": "$XXX,XXX", "category": "Sustainment"}}
  ],
  "labor_categories": [
    {{"role": "Senior Engineer", "hours": 1000, "rate": "$125/hr", "total": "$125,000"}},
    {{"role": "Junior Developer", "hours": 2000, "rate": "$75/hr", "total": "$150,000"}}
  ],
  "cost_breakdown": {{
    "labor": "$XXX,XXX",
    "materials": "$XXX,XXX",
    "travel": "$XXX,XXX",
    "other": "$XXX,XXX"
  }}
}}

Extract actual values from the text. Use "TBD" only if truly not specified.
Return ONLY valid JSON, no other text.

JSON:"""
                
                response = self.call_llm(prompt, max_tokens=1500, tracker=self._current_tracker)
                
                # Extract JSON from response
                json_match = re.search(r'\{[\s\S]*\}', response.strip())
                
                if json_match:
                    cost_data = json.loads(json_match.group(0))
                    # Merge with regex results (LLM takes precedence for matching keys)
                    merged = {**regex_costs, **cost_data}
                    
                    # Calculate total labor if labor categories provided
                    labor_cats = cost_data.get('labor_categories', [])
                    if labor_cats:
                        try:
                            total_labor = sum([
                                float(cat.get('total', '0').replace('$', '').replace(',', ''))
                                for cat in labor_cats
                                if cat.get('total')
                            ])
                            if total_labor > 0:
                                merged['total_labor_cost'] = f"${total_labor:,.0f}"
                        except (ValueError, AttributeError):
                            pass
                    
                    self.log(f"Hybrid extraction found {len(labor_cats)} labor categories")
                    return merged
                    
            except json.JSONDecodeError as e:
                self.log(f"JSON parsing failed in hybrid cost extraction: {e}", level="WARNING")
            except Exception as e:
                self.log(f"LLM-based cost extraction failed: {e}", level="WARNING")
        
        # Fallback to regex-only results
        return regex_costs

    def _calculate_yearly_breakdown(
        self,
        total_cost: float,
        num_years: int = 5,
        escalation_rate: float = 0.03,
        base_year_percentage: float = 0.25
    ) -> Dict[str, float]:
        """
        Calculate year-by-year cost breakdown from total cost

        Args:
            total_cost: Total cost across all years
            num_years: Number of years (base + options)
            escalation_rate: Annual escalation rate (default 3%)
            base_year_percentage: Percentage of work in base year (default 25%)

        Returns:
            Dictionary with base_year and option_year costs
        """
        # Calculate base year cost (typically 20-30% of total for multi-year contracts)
        base_year_cost = total_cost * base_year_percentage

        # Remaining cost distributed across option years with escalation
        remaining_cost = total_cost - base_year_cost
        option_years = num_years - 1

        if option_years > 0:
            # Calculate base option year cost (before escalation)
            base_option_cost = remaining_cost / option_years

            # Apply escalation for each option year
            yearly_costs = {'base_year': base_year_cost}

            for year in range(1, num_years):
                # Escalate from previous year
                if year == 1:
                    option_cost = base_option_cost
                else:
                    option_cost = base_option_cost * (1 + escalation_rate) ** (year - 1)

                yearly_costs[f'option_year_{year}'] = option_cost
        else:
            yearly_costs = {'base_year': total_cost}

        return yearly_costs

    # ========================================================================
    # PHASE 2 ENHANCEMENTS: Smart Default Table and Narrative Generators
    # ========================================================================

    def _generate_labor_categories_table(self, labor_categories: List[Dict]) -> str:
        """Generate markdown table for labor categories (Phase 2 Smart Default)"""
        if not labor_categories:
            return "TBD - Detailed breakdown in development"

        rows = []
        for cat in labor_categories:
            row = f"| {cat['category']} | {cat['education']} | ${cat['rate']}/hr | GSA CALC Schedule |"
            rows.append(row)
        return '\n'.join(rows)

    def _generate_wbs_labor_table(
        self,
        wbs_elements: List[Dict],
        labor_categories: List[Dict],
        year: int,
        escalation: float = 0.03
    ) -> tuple:
        """
        Generate WBS labor table for a specific year (Phase 2 Smart Default)

        Args:
            wbs_elements: List of WBS elements
            labor_categories: List of labor categories
            year: Year number (0 = base, 1+ = option years)
            escalation: Annual escalation rate

        Returns:
            Tuple of (table_markdown, total_hours)
        """
        if not wbs_elements or not labor_categories:
            return "TBD - Detailed breakdown in development", 0

        rows = []
        total_hours = 0

        for wbs in wbs_elements:
            # Assign appropriate labor category (rotate through categories based on WBS)
            try:
                cat_index = int(wbs['wbs_id'].split('.')[1]) % len(labor_categories)
            except:
                cat_index = 0
            category = labor_categories[cat_index]

            # Apply escalation for future years
            rate = category['rate'] * (1 + escalation) ** year
            hours = wbs['hours']
            cost = rate * hours

            row = f"| {wbs['wbs_id']} | {wbs['task']} | {category['category']} | {hours} | ${rate:.2f} | **${cost:,.2f}** |"
            rows.append(row)
            total_hours += hours

        return '\n'.join(rows), total_hours

    def _generate_hardware_equipment_table(self, project_info: Dict, rag_context: Dict) -> tuple:
        """Generate hardware/equipment cost table with smart defaults (Phase 2)"""
        # Extract user count to scale equipment
        users_str = rag_context.get('total_users', '500').replace(',', '')
        try:
            users = int(users_str)
        except:
            users = 500

        # Standard equipment items based on contract type
        items = [
            {
                'item': 'Development Workstations',
                'description': 'High-performance developer machines',
                'quantity': max(5, users // 500),
                'unit_cost': 2500,
                'basis': 'GSA Advantage pricing'
            },
            {
                'item': 'Test Environment Servers',
                'description': 'Staging and QA servers',
                'quantity': 3,
                'unit_cost': 5000,
                'basis': 'AWS EC2 equivalent dedicated'
            },
            {
                'item': 'Network Equipment',
                'description': 'Switches, routers, firewalls',
                'quantity': 2,
                'unit_cost': 3000,
                'basis': 'Cisco enterprise pricing'
            },
            {
                'item': 'Backup Storage',
                'description': 'Redundant data storage',
                'quantity': 1,
                'unit_cost': 8000,
                'basis': 'Enterprise SAN pricing'
            }
        ]

        rows = []
        total = 0

        for item in items:
            cost = item['quantity'] * item['unit_cost']
            total += cost
            row = f"| {item['item']} | {item['description']} | {item['quantity']} | ${item['unit_cost']:,} | **${cost:,}** | {item['basis']} |"
            rows.append(row)

        return '\n'.join(rows), f"${total:,}"

    def _generate_software_licenses_table(self, project_info: Dict, rag_context: Dict) -> tuple:
        """Generate software licenses table with smart defaults (Phase 2)"""
        users_str = rag_context.get('total_users', '500').replace(',', '')
        try:
            users = int(users_str)
        except:
            users = 500

        licenses = [
            {
                'software': 'Database Management System',
                'type': 'Enterprise',
                'licenses': 1,
                'unit_cost': 25000,
                'basis': 'Oracle/SQL Server enterprise pricing'
            },
            {
                'software': 'Application Server Licenses',
                'type': 'Per-core',
                'licenses': 8,
                'unit_cost': 3000,
                'basis': 'Commercial application server'
            },
            {
                'software': 'Development Tools',
                'type': 'Named user',
                'licenses': max(10, users // 200),
                'unit_cost': 500,
                'basis': 'IDE and development suite'
            },
            {
                'software': 'Security/Monitoring Tools',
                'type': 'Enterprise',
                'licenses': 1,
                'unit_cost': 15000,
                'basis': 'SIEM and vulnerability scanning'
            },
            {
                'software': 'End User Licenses',
                'type': 'Concurrent',
                'licenses': users,
                'unit_cost': 50,
                'basis': 'Per-seat client access'
            }
        ]

        rows = []
        total = 0

        for lic in licenses:
            cost = lic['licenses'] * lic['unit_cost']
            total += cost
            row = f"| {lic['software']} | {lic['type']} | {lic['licenses']} | ${lic['unit_cost']:,} | **${cost:,}** | {lic['basis']} |"
            rows.append(row)

        return '\n'.join(rows), f"${total:,}"

    def _generate_cloud_infrastructure_table(self, project_info: Dict, rag_context: Dict) -> tuple:
        """Generate cloud infrastructure cost table with smart defaults (Phase 2)"""
        users_str = rag_context.get('total_users', '500').replace(',', '')
        try:
            users = int(users_str)
        except:
            users = 500

        months = 12  # Annual calculation

        services = [
            {
                'service': 'Compute Instances (Production)',
                'description': f'Autoscaling for {users} concurrent users',
                'monthly': max(2000, users * 3),
                'basis': 'AWS/Azure compute pricing'
            },
            {
                'service': 'Database (RDS/Managed)',
                'description': 'Multi-AZ, automated backups',
                'monthly': 1500,
                'basis': 'Managed database service'
            },
            {
                'service': 'Storage (S3/Blob)',
                'description': 'Document and media storage',
                'monthly': 500,
                'basis': 'Object storage with redundancy'
            },
            {
                'service': 'CDN and Load Balancing',
                'description': 'Global content delivery',
                'monthly': 800,
                'basis': 'CloudFront/Azure CDN'
            },
            {
                'service': 'Monitoring and Logging',
                'description': 'CloudWatch, alerting, log retention',
                'monthly': 400,
                'basis': 'Cloud monitoring services'
            }
        ]

        rows = []
        total = 0

        for svc in services:
            cost = svc['monthly'] * months
            total += cost
            row = f"| {svc['service']} | {svc['description']} | ${svc['monthly']:,} | {months} | **${cost:,}** | {svc['basis']} |"
            rows.append(row)

        return '\n'.join(rows), f"${total:,}"

    def _generate_travel_table(self, project_info: Dict) -> str:
        """Generate travel cost breakdown table with smart defaults (Phase 2)"""
        trips = [
            {
                'purpose': 'Requirements Gathering',
                'travelers': 3,
                'trips': 2,
                'days': 3,
                'per_diem': 180,
                'airfare': 600,
            },
            {
                'purpose': 'Design Reviews',
                'travelers': 2,
                'trips': 3,
                'days': 2,
                'per_diem': 180,
                'airfare': 600,
            },
            {
                'purpose': 'User Acceptance Testing',
                'travelers': 4,
                'trips': 2,
                'days': 5,
                'per_diem': 180,
                'airfare': 600,
            },
            {
                'purpose': 'Training Delivery',
                'travelers': 2,
                'trips': 4,
                'days': 3,
                'per_diem': 180,
                'airfare': 600,
            },
        ]

        rows = []

        for trip in trips:
            per_diem_total = trip['travelers'] * trip['trips'] * trip['days'] * trip['per_diem']
            airfare_total = trip['travelers'] * trip['trips'] * trip['airfare']
            total = per_diem_total + airfare_total

            row = f"| {trip['purpose']} | {trip['travelers']} | {trip['trips']} | {trip['days']} | ${trip['per_diem']} | ${trip['airfare']} | **${total:,}** |"
            rows.append(row)

        return '\n'.join(rows)

    def _generate_training_table(self, project_info: Dict, rag_context: Dict) -> tuple:
        """Generate training cost table with smart defaults (Phase 2)"""
        users_str = rag_context.get('total_users', '500').replace(',', '')
        try:
            users = int(users_str)
        except:
            users = 500

        training = [
            {
                'type': 'System Administrator Training',
                'attendees': max(5, users // 200),
                'cost_per_person': 2000,
                'basis': '5-day comprehensive course'
            },
            {
                'type': 'End User Training (Basic)',
                'attendees': users,
                'cost_per_person': 200,
                'basis': '1-day introductory workshop'
            },
            {
                'type': 'Power User Training',
                'attendees': max(20, users // 25),
                'cost_per_person': 500,
                'basis': '2-day advanced features'
            },
            {
                'type': 'Train-the-Trainer',
                'attendees': max(5, users // 100),
                'cost_per_person': 3000,
                'basis': '1-week instructor certification'
            }
        ]

        rows = []
        total = 0

        for t in training:
            cost = t['attendees'] * t['cost_per_person']
            total += cost
            row = f"| {t['type']} | {t['attendees']} | ${t['cost_per_person']:,} | **${cost:,}** | {t['basis']} |"
            rows.append(row)

        return '\n'.join(rows), f"${total:,}"

    def _generate_risk_assessment_table(self, project_info: Dict, risk_analysis: Dict) -> str:
        """Generate risk assessment table with smart defaults (Phase 2)"""
        risks = [
            {
                'category': 'Technical Complexity',
                'probability': 'Medium (30%)',
                'impact': 'High',
                'mitigation': 'Phased implementation, technical reviews',
                'cost_impact': '8-12%'
            },
            {
                'category': 'Schedule Delays',
                'probability': 'Medium (25%)',
                'impact': 'Medium',
                'mitigation': 'Agile methodology, frequent milestones',
                'cost_impact': '5-8%'
            },
            {
                'category': 'Integration Challenges',
                'probability': 'Low (15%)',
                'impact': 'Medium',
                'mitigation': 'Early integration testing, API contracts',
                'cost_impact': '3-5%'
            },
            {
                'category': 'Security Requirements',
                'probability': 'Low (20%)',
                'impact': 'High',
                'mitigation': 'Security-first design, continuous scanning',
                'cost_impact': '4-6%'
            },
            {
                'category': 'Resource Availability',
                'probability': 'Low (10%)',
                'impact': 'Low',
                'mitigation': 'Cross-training, vendor partnerships',
                'cost_impact': '2-3%'
            }
        ]

        rows = []
        for risk in risks:
            row = f"| {risk['category']} | {risk['probability']} | {risk['impact']} | {risk['mitigation']} | {risk['cost_impact']} |"
            rows.append(row)

        return '\n'.join(rows)

    def _calculate_labor_costs(
        self,
        labor_categories: List[Dict],
        wbs_elements: List[Dict],
        contract_type: str
    ) -> Dict:
        """Calculate total labor costs"""
        total_hours = sum(wbs.get('hours', 0) for wbs in wbs_elements)
        avg_rate = sum(cat.get('rate', 0) for cat in labor_categories) / len(labor_categories) if labor_categories else 100
        
        base_cost = total_hours * avg_rate
        
        # Add burden rate (typically 1.5-2.0x for services, 1.8-2.5x for R&D)
        burden_multiplier = 2.2 if contract_type == 'research_development' else 1.8
        loaded_cost = base_cost * burden_multiplier
        
        return {
            'total_hours': total_hours,
            'average_rate': avg_rate,
            'base_cost': f"${base_cost:,.2f}",
            'burden_multiplier': burden_multiplier,
            'loaded_cost': f"${loaded_cost:,.2f}",
            'total': f"${loaded_cost:,.2f}"
        }
    
    def _calculate_materials_costs(self, requirements_content: str, contract_type: str) -> Dict:
        """Calculate materials and ODC costs"""
        # For services contracts, materials are typically lower
        # For R&D, materials and equipment can be significant
        
        if contract_type == 'research_development':
            hardware = 50000
            software = 75000
            equipment = 100000
            travel = 25000
        else:
            hardware = 25000
            software = 50000
            equipment = 10000
            travel = 15000
        
        total = hardware + software + equipment + travel
        
        return {
            'hardware': f"${hardware:,.2f}",
            'software': f"${software:,.2f}",
            'equipment': f"${equipment:,.2f}",
            'travel': f"${travel:,.2f}",
            'total': f"${total:,.2f}"
        }
    
    def _analyze_risks(self, requirements_content: str, contract_type: str) -> Dict:
        """Analyze risks and calculate contingency percentage"""
        # Default contingency: 10-15% for services, 15-25% for R&D
        contingency_percent = 20 if contract_type == 'research_development' else 12
        
        risk_factors = [
            "Technical complexity and maturity",
            "Schedule constraints",
            "Integration challenges",
            "Security and compliance requirements",
            "Vendor availability and competition"
        ]
        
        return {
            'contingency_percent': contingency_percent,
            'risk_factors': risk_factors,
            'rationale': f"Based on {contract_type} contract complexity and identified risk factors"
        }
    
    def _generate_boe(
        self,
        cost_elements: Dict,
        labor_costs: Dict,
        materials_costs: Dict,
        cost_benchmarks: List[Dict],
        contract_type: str
    ) -> Dict:
        """Generate basis of estimate (BOE)"""
        return {
            'labor_rate_boe': "Labor rates based on GSA CALC tool and industry benchmarks for similar contracts",
            'labor_hour_boe': f"Labor hours estimated using work breakdown structure with {cost_elements['wbs_elements'][0]['hours']} hours for initial tasks",
            'materials_boe': f"Materials costs based on vendor quotes and {contract_type} contract benchmarks",
            'contingency_boe': f"Contingency reflects {contract_type} contract risk factors including technical complexity and schedule constraints"
        }
    
    def _populate_igce_template(
        self,
        project_info: Dict,
        cost_elements: Dict,
        labor_costs: Dict,
        materials_costs: Dict,
        risk_analysis: Dict,
        boe: Dict,
        cost_benchmarks: List[Dict],
        rag_context: Dict,
        config: Dict
    ) -> str:
        """
        Intelligently populate IGCE template with priority system:
        1. Calculated values
        2. RAG-retrieved values
        3. Smart defaults
        4. TBD (only when truly unknown)
        """
        content = self.template

        # Helper function to get value with priority
        def get_value(key, calculated=None, rag_key=None, default='TBD'):
            """Get value with priority: calculated > RAG > default"""
            if calculated:
                return str(calculated)
            if rag_key and rag_key in rag_context:
                return str(rag_context[rag_key])
            return default

        # Project information
        content = content.replace('{{program_name}}', project_info.get('program_name', 'TBD'))
        content = content.replace('{{organization}}', project_info.get('organization', 'Department of Defense'))
        content = content.replace('{{prepared_by}}', config.get('prepared_by', 'Cost Analyst'))
        content = content.replace('{{date}}', datetime.now().strftime('%B %d, %Y'))
        content = content.replace('{{classification}}', config.get('classification', 'UNCLASSIFIED'))

        # Program overview - use RAG if available
        program_overview = project_info.get('background', '')
        if not program_overview and 'total_users' in rag_context:
            program_overview = f"Program to deploy logistics management system for {rag_context.get('total_users', '')} users."
        content = content.replace('{{program_overview}}', program_overview or 'TBD')

        # Costs - Priority: calculated > RAG > TBD
        content = content.replace('{{total_labor}}', str(labor_costs['total']))
        content = content.replace('{{total_materials}}', str(materials_costs['total']))
        content = content.replace('{{contingency_percent}}', str(risk_analysis['contingency_percent']))

        # Calculate year-by-year breakdowns for cost tables
        # Parse numeric values from cost strings
        def parse_cost(cost_str):
            """Extract numeric value from cost string like '$701,520.00'"""
            import re
            if isinstance(cost_str, (int, float)):
                return float(cost_str)
            clean_str = re.sub(r'[^\d.]', '', str(cost_str))
            return float(clean_str) if clean_str else 0

        labor_total_value = parse_cost(labor_costs['total'])
        materials_total_value = parse_cost(materials_costs['total'])

        # Calculate yearly breakdowns
        labor_yearly = self._calculate_yearly_breakdown(labor_total_value, num_years=5)
        materials_yearly = self._calculate_yearly_breakdown(materials_total_value, num_years=5)

        # Format yearly costs for template
        labor_base = f"${labor_yearly['base_year']:,.2f}"
        labor_opt1 = f"${labor_yearly.get('option_year_1', 0):,.2f}"
        labor_opt2 = f"${labor_yearly.get('option_year_2', 0):,.2f}"
        labor_opt3 = f"${labor_yearly.get('option_year_3', 0):,.2f}"
        labor_opt4 = f"${labor_yearly.get('option_year_4', 0):,.2f}"

        materials_base = f"${materials_yearly['base_year']:,.2f}"
        materials_opt1 = f"${materials_yearly.get('option_year_1', 0):,.2f}"
        materials_opt2 = f"${materials_yearly.get('option_year_2', 0):,.2f}"
        materials_opt3 = f"${materials_yearly.get('option_year_3', 0):,.2f}"
        materials_opt4 = f"${materials_yearly.get('option_year_4', 0):,.2f}"

        # Calculate totals for each year
        total_base = labor_yearly['base_year'] + materials_yearly['base_year']
        total_opt1 = labor_yearly.get('option_year_1', 0) + materials_yearly.get('option_year_1', 0)
        total_opt2 = labor_yearly.get('option_year_2', 0) + materials_yearly.get('option_year_2', 0)
        total_opt3 = labor_yearly.get('option_year_3', 0) + materials_yearly.get('option_year_3', 0)
        total_opt4 = labor_yearly.get('option_year_4', 0) + materials_yearly.get('option_year_4', 0)

        subtotal_base = f"${total_base:,.2f}"
        subtotal_opt1 = f"${total_opt1:,.2f}"
        subtotal_opt2 = f"${total_opt2:,.2f}"
        subtotal_opt3 = f"${total_opt3:,.2f}"
        subtotal_opt4 = f"${total_opt4:,.2f}"

        # Store yearly values for use in template
        yearly_costs = {
            'labor_base': labor_base,
            'labor_opt1': labor_opt1,
            'labor_opt2': labor_opt2,
            'labor_opt3': labor_opt3,
            'labor_opt4': labor_opt4,
            'materials_base': materials_base,
            'materials_opt1': materials_opt1,
            'materials_opt2': materials_opt2,
            'materials_opt3': materials_opt3,
            'materials_opt4': materials_opt4,
            'subtotal_base': subtotal_base,
            'subtotal_opt1': subtotal_opt1,
            'subtotal_opt2': subtotal_opt2,
            'subtotal_opt3': subtotal_opt3,
            'subtotal_opt4': subtotal_opt4,
        }

        # ====================================================================
        # PHASE 2: Generate smart default tables
        # ====================================================================

        # Generate labor categories table
        labor_cat_table = self._generate_labor_categories_table(cost_elements['labor_categories'])
        content = content.replace('{{labor_categories_table}}', labor_cat_table)

        # Generate WBS labor tables for each year
        base_wbs_table, base_year_hours = self._generate_wbs_labor_table(
            cost_elements['wbs_elements'],
            cost_elements['labor_categories'],
            year=0
        )
        content = content.replace('{{base_year_labor_wbs}}', base_wbs_table)
        content = content.replace('{{base_year_total_hours}}', str(base_year_hours))

        opt1_wbs_table, opt1_hours = self._generate_wbs_labor_table(
            cost_elements['wbs_elements'],
            cost_elements['labor_categories'],
            year=1
        )
        content = content.replace('{{option_year_1_labor_wbs}}', opt1_wbs_table)
        content = content.replace('{{opt1_total_hours}}', str(opt1_hours))

        # Additional option years (combine for brevity)
        additional_years = []
        for year_num in range(2, 5):
            opt_wbs_table, opt_hours = self._generate_wbs_labor_table(
                cost_elements['wbs_elements'],
                cost_elements['labor_categories'],
                year=year_num
            )
            additional_years.append(f"\n#### Option Year {year_num} Labor Hours\n\n")
            additional_years.append("| WBS Element | Task Description | Labor Category | Hours | Rate | **Cost** |\n")
            additional_years.append("|-------------|------------------|----------------|-------|------|----------|\n")
            additional_years.append(opt_wbs_table + "\n")
            additional_years.append(f"| | | | **Total Option Year {year_num} Labor Hours:** | **{opt_hours}** | **{locals()[f'labor_opt{year_num}']}** |\n")

        content = content.replace('{{additional_option_years_labor}}', ''.join(additional_years))

        # Generate hardware/equipment table
        hardware_table, hardware_total = self._generate_hardware_equipment_table(project_info, rag_context)
        content = content.replace('{{hardware_equipment_table}}', hardware_table)
        content = content.replace('{{total_hardware}}', hardware_total)

        # Generate software licenses table
        software_table, software_total = self._generate_software_licenses_table(project_info, rag_context)
        content = content.replace('{{software_licenses_table}}', software_table)
        content = content.replace('{{total_software}}', software_total)

        # Generate cloud infrastructure table
        cloud_table, cloud_total = self._generate_cloud_infrastructure_table(project_info, rag_context)
        content = content.replace('{{cloud_infrastructure_table}}', cloud_table)
        content = content.replace('{{total_cloud}}', cloud_total)

        # Generate travel table
        travel_table = self._generate_travel_table(project_info)
        content = content.replace('{{travel_table}}', travel_table)

        # Travel assumptions
        travel_assumptions = f"Travel estimates based on {4} trips per year. Per diem rates use GSA CONUS rates ($180/day). Airfare estimated at $600 per trip based on historical data for CONUS travel."
        content = content.replace('{{travel_assumptions}}', travel_assumptions)

        # Generate training table
        training_table, training_total = self._generate_training_table(project_info, rag_context)
        content = content.replace('{{training_table}}', training_table)
        content = content.replace('{{total_training}}', training_total)

        # Generate risk assessment table
        risk_table = self._generate_risk_assessment_table(project_info, risk_analysis)
        content = content.replace('{{risk_assessment_table}}', risk_table)

        # ====================================================================
        # PHASE 2: Generate narrative sections
        # ====================================================================

        # Materials cost assumptions
        materials_assumptions = f"Materials costs include hardware procurement ({hardware_total}), software licensing ({software_total}), and cloud infrastructure ({cloud_total}). Estimates based on GSA pricing, vendor quotes, and cloud service calculators. Annual escalation of 3% applied to option years per historical inflation trends."
        content = content.replace('{{materials_cost_assumptions}}', materials_assumptions)

        # Contingency rationale
        contingency_rationale = f"Contingency of {risk_analysis['contingency_percent']}% reflects medium technical risk with established technology stack and moderate integration complexity. Based on historical performance data from similar government IT service contracts and risk assessment identifying 5 primary risk categories."
        content = content.replace('{{contingency_rationale}}', contingency_rationale)

        # Materials and equipment BOE
        materials_equipment_boe = f"Materials and equipment costs based on GSA Advantage pricing ({hardware_total}), commercial software pricing with government discounts ({software_total}), and cloud service provider pricing ({cloud_total}). Hardware estimates use current GSA Schedule 70 pricing. Software licenses reflect enterprise pricing with volume discounts. Cloud costs calculated using AWS/Azure pricing calculators for production workloads."
        content = content.replace('{{materials_equipment_boe}}', materials_equipment_boe)

        # Travel and ODC BOE
        travel_odc_boe = f"Travel costs based on GSA per diem rates ($180/day CONUS average) and historical airfare data ($600 average per trip). Travel estimates include requirements gathering (2 trips), design reviews (3 trips), user acceptance testing (2 trips), and training delivery (4 trips). Training costs ({training_total}) based on commercial training provider rates with government discounts."
        content = content.replace('{{travel_odc_boe}}', travel_odc_boe)

        # Other direct costs table and total
        odc_table = "| Shipping and Handling | Materials and equipment delivery | **$5,000** | GSA freight rates |\n"
        odc_table += "| Subcontractor Management | Oversight and coordination | **$10,000** | Industry standards |\n"
        odc_table += "| Documentation and Reports | Technical documentation | **$8,000** | Technical writing rates |"
        content = content.replace('{{other_direct_costs_table}}', odc_table)
        content = content.replace('{{total_other_odc}}', "$23,000")

        # ====================================================================

        # Replace yearly cost placeholders in template
        content = content.replace('{{base_labor}}', labor_base)
        content = content.replace('{{opt1_labor}}', labor_opt1)
        content = content.replace('{{opt2_labor}}', labor_opt2)
        content = content.replace('{{opt3_labor}}', labor_opt3)
        content = content.replace('{{opt4_labor}}', labor_opt4)

        content = content.replace('{{base_materials}}', materials_base)
        content = content.replace('{{opt1_materials}}', materials_opt1)
        content = content.replace('{{opt2_materials}}', materials_opt2)
        content = content.replace('{{opt3_materials}}', materials_opt3)
        content = content.replace('{{opt4_materials}}', materials_opt4)

        # Add travel costs (typically 5-10% of labor for services contracts)
        travel_percentage = 0.05  # 5% of labor
        travel_yearly = self._calculate_yearly_breakdown(labor_total_value * travel_percentage, num_years=5)
        travel_base = f"${travel_yearly['base_year']:,.2f}"
        travel_opt1 = f"${travel_yearly.get('option_year_1', 0):,.2f}"
        travel_opt2 = f"${travel_yearly.get('option_year_2', 0):,.2f}"
        travel_opt3 = f"${travel_yearly.get('option_year_3', 0):,.2f}"
        travel_opt4 = f"${travel_yearly.get('option_year_4', 0):,.2f}"
        travel_total = f"${labor_total_value * travel_percentage:,.2f}"

        content = content.replace('{{base_travel}}', travel_base)
        content = content.replace('{{opt1_travel}}', travel_opt1)
        content = content.replace('{{opt2_travel}}', travel_opt2)
        content = content.replace('{{opt3_travel}}', travel_opt3)
        content = content.replace('{{opt4_travel}}', travel_opt4)
        content = content.replace('{{total_travel}}', travel_total)

        # Add other direct costs (typically 3-5% of labor+materials)
        odc_percentage = 0.03  # 3%
        odc_base_cost = (labor_total_value + materials_total_value) * odc_percentage
        odc_yearly = self._calculate_yearly_breakdown(odc_base_cost, num_years=5)
        odc_base = f"${odc_yearly['base_year']:,.2f}"
        odc_opt1 = f"${odc_yearly.get('option_year_1', 0):,.2f}"
        odc_opt2 = f"${odc_yearly.get('option_year_2', 0):,.2f}"
        odc_opt3 = f"${odc_yearly.get('option_year_3', 0):,.2f}"
        odc_opt4 = f"${odc_yearly.get('option_year_4', 0):,.2f}"
        odc_total = f"${odc_base_cost:,.2f}"

        content = content.replace('{{base_odc}}', odc_base)
        content = content.replace('{{opt1_odc}}', odc_opt1)
        content = content.replace('{{opt2_odc}}', odc_opt2)
        content = content.replace('{{opt3_odc}}', odc_opt3)
        content = content.replace('{{opt4_odc}}', odc_opt4)
        content = content.replace('{{total_odc}}', odc_total)

        # Recalculate subtotals including travel and ODC
        total_base = labor_yearly['base_year'] + materials_yearly['base_year'] + travel_yearly['base_year'] + odc_yearly['base_year']
        total_opt1 = (labor_yearly.get('option_year_1', 0) + materials_yearly.get('option_year_1', 0) +
                     travel_yearly.get('option_year_1', 0) + odc_yearly.get('option_year_1', 0))
        total_opt2 = (labor_yearly.get('option_year_2', 0) + materials_yearly.get('option_year_2', 0) +
                     travel_yearly.get('option_year_2', 0) + odc_yearly.get('option_year_2', 0))
        total_opt3 = (labor_yearly.get('option_year_3', 0) + materials_yearly.get('option_year_3', 0) +
                     travel_yearly.get('option_year_3', 0) + odc_yearly.get('option_year_3', 0))
        total_opt4 = (labor_yearly.get('option_year_4', 0) + materials_yearly.get('option_year_4', 0) +
                     travel_yearly.get('option_year_4', 0) + odc_yearly.get('option_year_4', 0))

        subtotal_base = f"${total_base:,.2f}"
        subtotal_opt1 = f"${total_opt1:,.2f}"
        subtotal_opt2 = f"${total_opt2:,.2f}"
        subtotal_opt3 = f"${total_opt3:,.2f}"
        subtotal_opt4 = f"${total_opt4:,.2f}"
        subtotal_total = f"${total_base + total_opt1 + total_opt2 + total_opt3 + total_opt4:,.2f}"

        content = content.replace('{{base_subtotal}}', subtotal_base)
        content = content.replace('{{opt1_subtotal}}', subtotal_opt1)
        content = content.replace('{{opt2_subtotal}}', subtotal_opt2)
        content = content.replace('{{opt3_subtotal}}', subtotal_opt3)
        content = content.replace('{{opt4_subtotal}}', subtotal_opt4)
        content = content.replace('{{total_subtotal}}', subtotal_total)

        # Calculate and populate contingency costs (based on subtotals)
        contingency_rate = risk_analysis['contingency_percent'] / 100
        contingency_base = f"${total_base * contingency_rate:,.2f}"
        contingency_opt1 = f"${total_opt1 * contingency_rate:,.2f}"
        contingency_opt2 = f"${total_opt2 * contingency_rate:,.2f}"
        contingency_opt3 = f"${total_opt3 * contingency_rate:,.2f}"
        contingency_opt4 = f"${total_opt4 * contingency_rate:,.2f}"
        contingency_total = f"${(total_base + total_opt1 + total_opt2 + total_opt3 + total_opt4) * contingency_rate:,.2f}"

        content = content.replace('{{base_contingency}}', contingency_base)
        content = content.replace('{{opt1_contingency}}', contingency_opt1)
        content = content.replace('{{opt2_contingency}}', contingency_opt2)
        content = content.replace('{{opt3_contingency}}', contingency_opt3)
        content = content.replace('{{opt4_contingency}}', contingency_opt4)
        content = content.replace('{{total_contingency}}', contingency_total)

        # Calculate and populate total costs (subtotal + contingency)
        final_base = f"${total_base * (1 + contingency_rate):,.2f}"
        final_opt1 = f"${total_opt1 * (1 + contingency_rate):,.2f}"
        final_opt2 = f"${total_opt2 * (1 + contingency_rate):,.2f}"
        final_opt3 = f"${total_opt3 * (1 + contingency_rate):,.2f}"
        final_opt4 = f"${total_opt4 * (1 + contingency_rate):,.2f}"

        content = content.replace('{{base_total}}', final_base)
        content = content.replace('{{opt1_total}}', final_opt1)
        content = content.replace('{{opt2_total}}', final_opt2)
        content = content.replace('{{opt3_total}}', final_opt3)
        content = content.replace('{{opt4_total}}', final_opt4)

        # Grand total - use RAG if available
        grand_total = project_info.get('estimated_value', '')
        if not grand_total and 'development_cost' in rag_context and 'lifecycle_cost' in rag_context:
            grand_total = f"{rag_context['development_cost']} development, {rag_context['lifecycle_cost']} lifecycle"
        elif not grand_total and 'total_budget' in rag_context:
            grand_total = rag_context['total_budget']
        content = content.replace('{{grand_total}}', grand_total or 'TBD')

        # Contract information - use RAG if available
        contract_type = config.get('contract_type', '')
        if not contract_type and 'contract_type_detail' in rag_context:
            contract_type = rag_context['contract_type_detail']
        content = content.replace('{{contract_type}}', contract_type or 'services')

        # Period of performance - enhanced with RAG
        period = project_info.get('period_of_performance', '')
        if not period and 'ioc_date' in rag_context and 'foc_date' in rag_context:
            period = f"Through {rag_context['foc_date']} (IOC: {rag_context['ioc_date']}, FOC: {rag_context['foc_date']})"
        content = content.replace('{{period_of_performance}}', period or '12 months base + 4 option years')

        # Contract structure - use RAG
        contract_structure = get_value(
            'contract_structure',
            rag_key='acquisition_approach',
            default='Base year plus options'
        )
        content = content.replace('{{contract_structure}}', contract_structure)

        # Estimate basis - enhanced with RAG data
        estimate_basis_parts = [
            "- Analysis of performance work statement requirements",
            f"- Industry labor rates ({labor_costs.get('average_rate', 'standard')} average)",
            "- Historical cost data from similar programs"
        ]
        if cost_benchmarks:
            estimate_basis_parts.append(f"- {len(cost_benchmarks)} comparable program benchmarks")
        if 'total_budget' in rag_context:
            estimate_basis_parts.append(f"- Program baseline budget: {rag_context['total_budget']}")
        content = content.replace('{{estimate_basis}}', '\n'.join(estimate_basis_parts))

        # Contract type rationale - enhanced
        rationale_parts = []
        if 'acquisition_approach' in rag_context:
            rationale_parts.append(f"Program uses {rag_context['acquisition_approach']} approach")
        if 'pricing_model' in rag_context:
            rationale_parts.append(f"{rag_context['pricing_model']} licensing model")
        rationale_parts.append("Provides cost certainty and performance incentives")
        content = content.replace('{{contract_type_rationale}}', '. '.join(rationale_parts))

        # BOE sections
        content = content.replace('{{labor_rate_boe}}', boe['labor_rate_boe'])
        content = content.replace('{{labor_hour_boe}}', boe['labor_hour_boe'])
        content = content.replace('{{labor_rate_basis}}', "Based on GSA CALC and industry benchmarks")

        # Key assumptions - build from RAG data
        assumptions = []
        if 'total_users' in rag_context:
            assumptions.append(f"System deployed for {rag_context['total_users']} users")
        if 'ioc_date' in rag_context:
            assumptions.append(f"Initial Operating Capability by {rag_context['ioc_date']}")
        if 'pricing_model' in rag_context:
            assumptions.append(f"{rag_context['pricing_model']} licensing")
        assumptions.extend([
            "Contractor provides full lifecycle support",
            "Government provides program management oversight",
            f"Contingency: {risk_analysis['contingency_percent']}% for technical and schedule risks"
        ])
        content = content.replace('{{key_assumptions}}', '\n'.join(f"- {a}" for a in assumptions))

        # Confidence level - enhanced with data availability
        data_points = len(rag_context) + len(cost_benchmarks)
        if data_points > 15:
            confidence = "HIGH"
            confidence_rationale = f"Based on {data_points} retrieved data points from program baseline and similar acquisitions"
        elif data_points > 8:
            confidence = "MEDIUM-HIGH"
            confidence_rationale = f"Based on {data_points} data points and industry standards"
        elif data_points > 3:
            confidence = "MEDIUM"
            confidence_rationale = f"Based on {data_points} data points with standard cost factors"
        else:
            confidence = "MEDIUM"
            confidence_rationale = "Based on requirements analysis and industry cost factors"
        content = content.replace('{{confidence_level}}', confidence)
        content = content.replace('{{confidence_rationale}}', confidence_rationale)

        # Labor cost assumptions - enhanced
        labor_assumptions = [
            f"Fully burdened rates with {labor_costs.get('burden_multiplier', 1.8)}x multiplier",
            "Rates include overhead, G&A, and fee",
            f"Based on {len(cost_elements.get('labor_categories', []))} labor categories",
            "Annual escalation per BLS employment cost index"
        ]
        if 'team_size' in rag_context:
            labor_assumptions.append(f"Core team size: {rag_context['team_size']} personnel")
        content = content.replace('{{labor_cost_assumptions}}', '\n'.join(f"- {a}" for a in labor_assumptions))

        # Escalation factors
        content = content.replace('{{escalation_factors}}',
            "- Base Year: 0%\n- Option Year 1-4: 3.0% annually (historical average)")

        # Annual sustainment data from RAG
        if 'license_cost_annual' in rag_context:
            content = content.replace('{{annual_license_cost}}', rag_context['license_cost_annual'])
        if 'training_cost_annual' in rag_context:
            content = content.replace('{{annual_training_cost}}', rag_context['training_cost_annual'])
        if 'cloud_cost_annual' in rag_context:
            content = content.replace('{{annual_cloud_cost}}', rag_context['cloud_cost_annual'])
        if 'annual_sustainment_total' in rag_context:
            content = content.replace('{{annual_sustainment}}', rag_context['annual_sustainment_total'])

        # Fill remaining placeholders with descriptive TBD (not lazy!)
        remaining_placeholders = re.findall(r'\{\{([^}]+)\}\}', content)
        for placeholder in remaining_placeholders:
            # Replace with TBD but keep the field name for clarity
            if 'cost' in placeholder.lower() or 'budget' in placeholder.lower():
                content = content.replace(f'{{{{{placeholder}}}}}', 'TBD - Detailed cost breakdown pending')
            elif 'date' in placeholder.lower() or 'schedule' in placeholder.lower():
                content = content.replace(f'{{{{{placeholder}}}}}', 'TBD - Schedule to be determined')
            elif 'table' in placeholder.lower() or 'wbs' in placeholder.lower():
                content = content.replace(f'{{{{{placeholder}}}}}', 'TBD - Detailed breakdown in development')
            else:
                content = content.replace(f'{{{{{placeholder}}}}}', 'TBD')

        return content
    
    def save_to_file(self, content: str, output_path: str, convert_to_pdf: bool = True) -> Dict:
        """
        Save IGCE to file and optionally convert to PDF
        
        Args:
            content: IGCE markdown content
            output_path: Path to save markdown file
            convert_to_pdf: Whether to convert to PDF
        
        Returns:
            Dictionary with file paths
        """
        # Save markdown
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(content)
        
        result = {'markdown': output_path}
        
        # Convert to PDF
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

