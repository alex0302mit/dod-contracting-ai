"""
Acquisition Plan Generator Agent: Generates comprehensive Acquisition Plans per FAR 7.105
Leverages ALMS acquisition strategy as reference and includes all 12 required elements
"""

from typing import Dict, List, Optional
from pathlib import Path
import sys
from datetime import datetime, timedelta
import re

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.base_agent import BaseAgent
from backend.rag.retriever import Retriever
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class AcquisitionPlanGeneratorAgent(BaseAgent):
    """
    Acquisition Plan Generator Agent
    
    Generates comprehensive Acquisition Plans per FAR 7.105 (12 required elements).
    
    Features:
    - Leverages ALMS acquisition strategy as reference
    - Sections: Background, Requirements, Market Research, Source Selection, Contract Type, Risk, Schedule
    - Auto-determines thresholds: >$10M requires full written plan
    - Contract type aware: R&D includes tech maturation strategy
    - Integrates market research results
    - Generates risk register and mitigation strategies
    
    Dependencies:
    - BaseAgent: LLM interaction and common utilities
    - Retriever: RAG system for similar acquisition strategies
    """
    
    def __init__(
        self,
        api_key: str,
        retriever: Optional[Retriever] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize Acquisition Plan Generator Agent
        
        Args:
            api_key: Anthropic API key
            retriever: Optional RAG retriever for acquisition strategies
            model: Claude model to use
        """
        super().__init__(
            name="Acquisition Plan Generator Agent",
            api_key=api_key,
            model=model,
            temperature=0.4
        )
        
        self.retriever = retriever
        self.template_path = Path(__file__).parent.parent / "templates" / "acquisition_plan_template.md"
        
        # Load template
        with open(self.template_path, 'r') as f:
            self.template = f.read()
        
        print("\n" + "="*70)
        print("ACQUISITION PLAN GENERATOR AGENT INITIALIZED")
        print("="*70)
        print(f"  ✓ BaseAgent initialized")
        print(f"  ✓ Template loaded: {self.template_path.name}")
        if self.retriever:
            print(f"  ✓ RAG retriever available (ALMS strategy reference)")
        print("="*70 + "\n")
    
    def execute(self, task: Dict) -> Dict:
        """
        Execute Acquisition Plan generation
        
        Args:
            task: Dictionary containing:
                - project_info: Program details
                - requirements_content: Requirements documentation
                - market_research_results: Market research summary (optional)
                - config: Optional configuration
        
        Returns:
            Dictionary with Acquisition Plan content and metadata
        """
        self.log("Starting Acquisition Plan generation")

        project_info = task.get('project_info', {})
        requirements_content = task.get('requirements_content', '')
        market_research = task.get('market_research_results', {})
        config = task.get('config', {})

        contract_type = config.get('contract_type', 'services')

        # NEW: Cross-reference lookup - Find latest IGCE for this program
        program_name = project_info.get('program_name', 'Unknown')
        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()
                latest_igce = metadata_store.find_latest_document('igce', program_name)

                if latest_igce:
                    print(f"✅ Found IGCE: {latest_igce['id']}")
                    print(f"   Total Cost: {latest_igce['extracted_data'].get('total_cost_formatted', 'N/A')}")

                    # Inject IGCE data into project_info for template population
                    extractor = DocumentDataExtractor()
                    igce_summary = extractor.generate_igce_summary(latest_igce['extracted_data'])

                    project_info['igce_summary'] = igce_summary
                    project_info['igce_total_cost'] = latest_igce['extracted_data'].get('total_cost_formatted', 'TBD')
                    project_info['igce_base_year_cost'] = latest_igce['extracted_data'].get('base_year_cost', 0)
                    project_info['igce_option_year_costs'] = latest_igce['extracted_data'].get('option_year_costs', [])
                    project_info['igce_period'] = latest_igce['extracted_data'].get('period_of_performance', 'TBD')

                    # Store IGCE reference for later metadata save
                    self._igce_reference = latest_igce['id']

                    print(f"✅ IGCE data injected into Acquisition Plan context")
                else:
                    print(f"⚠️  No IGCE found for {program_name} - will use estimated values")
                    project_info['igce_summary'] = "TBD - IGCE not yet generated"
                    self._igce_reference = None

            except Exception as e:
                print(f"⚠️  Could not lookup IGCE: {str(e)}")
                project_info['igce_summary'] = "TBD - IGCE lookup failed"
                self._igce_reference = None
        else:
            self._igce_reference = None

        print("\n" + "="*70)
        print("GENERATING ACQUISITION PLAN (FAR 7.105)")
        print("="*70)
        print(f"Program: {program_name}")
        print(f"Estimated Value: {project_info.get('estimated_value', project_info.get('igce_total_cost', 'TBD'))}")
        print(f"Contract Type: {contract_type}")
        print("="*70 + "\n")
        
        # Step 1: Retrieve similar acquisition strategies from RAG
        print("STEP 1: Retrieving similar acquisition strategies...")
        rag_strategies, rag_extracted = self._retrieve_acquisition_strategies(project_info)
        print(f"  ✓ Retrieved {len(rag_strategies)} reference strategies")
        print(f"  ✓ Extracted {len(rag_extracted)} structured data fields from RAG")

        # Step 2: Analyze requirements and capability gap
        print("\nSTEP 2: Analyzing requirements and capability gap...")
        requirements_analysis = self._analyze_requirements(requirements_content)
        print(f"  ✓ Requirements analysis complete")
        
        # Step 3: Determine acquisition strategy
        print("\nSTEP 3: Determining acquisition strategy...")
        strategy = self._determine_acquisition_strategy(project_info, market_research, contract_type)
        print(f"  ✓ Strategy: {strategy['contract_vehicle']}")
        print(f"  ✓ Source Selection: {strategy['source_selection_method']}")
        
        # Step 4: Perform risk assessment
        print("\nSTEP 4: Performing risk assessment...")
        risk_assessment = self._assess_risks(requirements_content, contract_type)
        print(f"  ✓ Identified {len(risk_assessment['risks'])} risks")
        
        # Step 5: Generate acquisition schedule
        print("\nSTEP 5: Generating acquisition schedule...")
        schedule = self._generate_schedule(project_info, config)
        print(f"  ✓ Schedule with {len(schedule)} milestones")
        
        # Step 6: Analyze small business opportunities
        print("\nSTEP 6: Analyzing small business opportunities...")
        small_business = self._analyze_small_business_opportunities(project_info, market_research)
        print(f"  ✓ Set-aside: {small_business['set_aside_type']}")

        # Step 7: Generate narrative sections with LLM
        print("\nSTEP 7: Generating narrative sections with LLM...")
        llm_generated = {}

        # Generate Section 1: Background
        background_data = self._generate_background_from_rag(
            rag_strategies,
            requirements_analysis.get('capability_gap', ''),
            project_info
        )
        llm_generated.update(background_data)

        # Generate Section 2: Applicable Conditions
        conditions_data = self._generate_applicable_conditions_from_rag(project_info, rag_extracted)
        llm_generated.update(conditions_data)

        # Generate Section 6: Trade-offs
        tradeoffs_data = self._generate_tradeoffs_from_strategy(strategy, project_info)
        llm_generated.update(tradeoffs_data)

        # Generate Section 7: Streamlining
        streamlining_data = self._generate_streamlining_from_contract(strategy, project_info)
        llm_generated.update(streamlining_data)

        # Generate Section 10: Acquisition Considerations
        considerations_data = self._generate_acquisition_considerations(strategy, project_info, market_research)
        llm_generated.update(considerations_data)

        # Generate Section 11: Market Research
        market_data = self._generate_market_research_summary(market_research, rag_strategies)
        llm_generated.update(market_data)

        # Generate Section 17: Sustainment
        sustainment_data = self._generate_sustainment_content(project_info, contract_type)
        llm_generated.update(sustainment_data)

        # Generate Section 18: Test & Evaluation
        test_eval_data = self._generate_test_evaluation_content(project_info, requirements_analysis)
        llm_generated.update(test_eval_data)

        print(f"  ✓ Generated {len(llm_generated)} narrative sections")

        # Step 8: Generate smart defaults
        print("\nSTEP 8: Generating smart defaults for personnel, dates, and costs...")
        smart_defaults = self._generate_smart_defaults(project_info, rag_extracted, config)
        print(f"  ✓ Generated {len(smart_defaults)} smart default values")

        # Step 9: Populate acquisition plan template
        print("\nSTEP 9: Populating acquisition plan template...")
        content = self._populate_template(
            project_info,
            requirements_analysis,
            strategy,
            risk_assessment,
            schedule,
            small_business,
            market_research,
            rag_strategies,
            rag_extracted,
            llm_generated,
            smart_defaults,
            config
        )
        print(f"  ✓ Template populated ({len(content)} characters)")
        
        print("\n" + "="*70)
        print("✅ ACQUISITION PLAN GENERATION COMPLETE")
        print("="*70)

        # NEW: Save metadata for cross-referencing
        output_path = task.get('output_path', '')

        if program_name != 'Unknown':
            try:
                print("\n💾 Saving Acquisition Plan metadata for cross-referencing...")
                metadata_store = DocumentMetadataStore()
                extractor = DocumentDataExtractor()

                # Extract structured data from generated Acquisition Plan
                extracted_data = extractor.extract_acquisition_plan_data(content)

                # Prepare references (IGCE if found)
                references = {}
                if hasattr(self, '_igce_reference') and self._igce_reference:
                    references['igce'] = self._igce_reference

                # Save metadata
                doc_id = metadata_store.save_document(
                    doc_type='acquisition_plan',
                    program=program_name,
                    content=content,
                    file_path=output_path,
                    extracted_data=extracted_data,
                    references=references
                )

                print(f"✅ Metadata saved: {doc_id}")
                if references:
                    print(f"   Cross-references: {list(references.keys())}")

            except Exception as e:
                print(f"⚠️  Warning: Could not save metadata: {str(e)}")
                # Continue anyway - metadata is optional

        return {
            'status': 'success',
            'content': content,
            'metadata': {
                'contract_vehicle': strategy['contract_vehicle'],
                'source_selection_method': strategy['source_selection_method'],
                'risks_count': len(risk_assessment['risks']),
                'milestones_count': len(schedule),
                'set_aside_type': small_business['set_aside_type'],
                'contract_type': contract_type
            }
        }
    
    def _retrieve_acquisition_strategies(self, project_info: Dict) -> tuple[List[Dict], Dict]:
        """
        Use RAG to retrieve similar acquisition strategies (e.g., ALMS)

        Returns:
            tuple: (strategies list, extracted_data dict)
        """
        if not self.retriever:
            return [], {}

        strategies = []
        extracted_data = {}

        # Query 1: Acquisition Strategy document
        try:
            query1 = "What is the ALMS acquisition strategy? What contract vehicle and contract type are recommended?"
            results1 = self.retriever.retrieve(query1, k=2)
            for result in results1:
                strategies.append({
                    'source': result.get('metadata', {}).get('source', 'ALMS Acquisition Strategy'),
                    'content': result.content if hasattr(result, 'content') else result.get('content', '')[:800],
                    'type': 'acquisition_strategy'
                })
            self.log(f"RAG retrieved {len(results1)} acquisition strategy documents")

            # Extract structured acquisition strategy data
            strategy_data = self._extract_acquisition_strategy_from_rag(results1)
            extracted_data.update(strategy_data)
            if strategy_data:
                self.log(f"Extracted {len(strategy_data)} acquisition strategy fields from RAG")
        except Exception as e:
            self.log(f"RAG query for acquisition strategy failed: {e}", level="WARNING")

        # Query 2: Cost and schedule information
        try:
            query2 = "What are the ALMS cost estimates and schedule milestones? What is the IOC and FOC?"
            results2 = self.retriever.retrieve(query2, k=2)
            for result in results2:
                strategies.append({
                    'source': result.get('metadata', {}).get('source', 'ALMS Program Baseline'),
                    'content': result.content if hasattr(result, 'content') else result.get('content', '')[:800],
                    'type': 'cost_schedule'
                })
            self.log(f"RAG retrieved {len(results2)} cost/schedule documents")

            # Extract structured cost/schedule data
            cost_schedule_data = self._extract_cost_schedule_from_rag(results2)
            extracted_data.update(cost_schedule_data)
            if cost_schedule_data:
                self.log(f"Extracted {len(cost_schedule_data)} cost/schedule fields from RAG")
        except Exception as e:
            self.log(f"RAG query for cost/schedule failed: {e}", level="WARNING")

        # Query 3: Source selection approach
        try:
            query3 = "What source selection method and evaluation approach was used for ALMS?"
            results3 = self.retriever.retrieve(query3, k=1)
            for result in results3:
                strategies.append({
                    'source': result.get('metadata', {}).get('source', 'ALMS Source Selection'),
                    'content': result.content if hasattr(result, 'content') else result.get('content', '')[:800],
                    'type': 'source_selection'
                })
            self.log(f"RAG retrieved {len(results3)} source selection documents")

            # Extract structured source selection data
            source_selection_data = self._extract_source_selection_from_rag(results3)
            extracted_data.update(source_selection_data)
            if source_selection_data:
                self.log(f"Extracted {len(source_selection_data)} source selection fields from RAG")
        except Exception as e:
            self.log(f"RAG query for source selection failed: {e}", level="WARNING")

        return strategies, extracted_data

    def _extract_acquisition_strategy_from_rag(self, rag_results: List[Dict]) -> Dict:
        """
        Extract structured acquisition strategy data from RAG results

        Extracts: contract vehicle, contract type, acquisition approach
        """
        extracted = {}
        if not rag_results:
            return extracted

        # Combine RAG text using correct field access
        combined_text = "\n".join([
            r.content if hasattr(r, 'content') else r.get('content', '')
            for r in rag_results
        ])

        import re

        # Extract contract type with multiple patterns
        contract_type_patterns = [
            r'contract\s+type[:\s]+([A-Za-z\-\s]+?)(?:\.|,|\n)',
            r'(?:FFP|Firm[- ]Fixed[- ]Price|CPFF|Cost[- ]Plus)',
            r'recommended\s+contract[:\s]+([A-Za-z\-\s]+?)(?:\.|,|\n)',
        ]
        for pattern in contract_type_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                if 'FFP' in match.group(0) or 'Firm' in match.group(0):
                    extracted['contract_type'] = 'Firm-Fixed-Price (FFP)'
                elif 'CPFF' in match.group(0) or 'Cost-Plus' in match.group(0):
                    extracted['contract_type'] = 'Cost-Plus-Fixed-Fee (CPFF)'
                else:
                    extracted['contract_type'] = match.group(1).strip()
                break

        # Extract acquisition approach
        approach_patterns = [
            r'acquisition\s+(?:strategy|approach)[:\s]+([^\.]+)',
            r'(?:commercial|COTS|developmental)',
            r'(?:streamlined|traditional|middle[- ]tier)',
        ]
        for pattern in approach_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                if 'commercial' in match.group(0).lower() or 'COTS' in match.group(0):
                    extracted['acquisition_approach'] = 'Commercial/COTS'
                elif 'middle' in match.group(0).lower():
                    extracted['acquisition_approach'] = 'Middle Tier Acquisition'
                else:
                    extracted['acquisition_approach'] = match.group(1).strip() if match.lastindex else match.group(0)
                break

        return extracted

    def _extract_cost_schedule_from_rag(self, rag_results: List[Dict]) -> Dict:
        """
        Extract cost and schedule data from RAG results

        Extracts: development cost, lifecycle cost, IOC, FOC dates
        """
        extracted = {}
        if not rag_results:
            return extracted

        combined_text = "\n".join([
            r.content if hasattr(r, 'content') else r.get('content', '')
            for r in rag_results
        ])

        import re

        # Extract costs (using Phase 1 patterns)
        dev_patterns = [
            r'\$(\d+\.?\d*[KMB]?)\s*development',
            r'development.*?\$(\d+\.?\d*[KMB]?)',
        ]
        for pattern in dev_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                extracted['development_cost'] = f"${match.group(1)}"
                break

        lifecycle_patterns = [
            r'\$(\d+\.?\d*[KMB]?)\s*life.?cycle',
            r'life.?cycle.*?\$(\d+\.?\d*[KMB]?)',
        ]
        for pattern in lifecycle_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                extracted['lifecycle_cost'] = f"${match.group(1)}"
                break

        # Extract IOC/FOC dates
        ioc_match = re.search(r'IOC[:\s]*(\w+\s+\d{4})', combined_text, re.IGNORECASE)
        if ioc_match:
            extracted['ioc_date'] = ioc_match.group(1)

        foc_match = re.search(r'FOC[:\s]*(\w+\s+\d{4})', combined_text, re.IGNORECASE)
        if foc_match:
            extracted['foc_date'] = foc_match.group(1)

        return extracted

    def _extract_source_selection_from_rag(self, rag_results: List[Dict]) -> Dict:
        """
        Extract source selection information from RAG results

        Extracts: evaluation method, selection approach
        """
        extracted = {}
        if not rag_results:
            return extracted

        combined_text = "\n".join([
            r.content if hasattr(r, 'content') else r.get('content', '')
            for r in rag_results
        ])

        import re

        # Extract evaluation method
        method_patterns = [
            r'(?:Best Value|LPTA|Lowest Price Technically Acceptable|Trade[- ]?Off)',
            r'evaluation\s+(?:method|approach)[:\s]+([^\.]+)',
        ]
        for pattern in method_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                if 'Best Value' in match.group(0):
                    extracted['evaluation_method'] = 'Best Value Trade-Off'
                elif 'LPTA' in match.group(0) or 'Lowest Price' in match.group(0):
                    extracted['evaluation_method'] = 'Lowest Price Technically Acceptable (LPTA)'
                else:
                    extracted['evaluation_method'] = match.group(1).strip() if match.lastindex else match.group(0)
                break

        return extracted

    # ==================== HYBRID EXTRACTION METHODS (Regex + LLM-JSON) ====================

    def _extract_requirements_hybrid(self, rag_results: List[Dict]) -> Dict:
        """
        HYBRID requirements extraction: Regex + LLM-JSON + Metadata
        
        Stage 1: Quick regex for counts and obvious patterns
        Stage 2: LLM-based JSON extraction for structured requirements
        Stage 3: Check metadata for pre-structured JSON
        
        Returns:
            Dictionary with structured requirements data including:
            - functional_requirements: List of functional requirement objects
            - performance_requirements: List of performance requirement objects  
            - key_performance_parameters: List of KPP objects
            - technical_requirements: List of technical requirement objects
            - metadata: Extracted counts and summary info
        """
        if not rag_results:
            return {
                'functional_requirements': [],
                'performance_requirements': [],
                'key_performance_parameters': [],
                'technical_requirements': [],
                'metadata': {}
            }
        
        # Combine all RAG text
        combined_text = "\n\n---CHUNK---\n\n".join([
            r.content if hasattr(r, 'content') else r.get('content', '')
            for r in rag_results
        ])
        
        import re
        import json
        
        # ============ STAGE 1: REGEX QUICK EXTRACTION ============
        metadata = {}
        
        # Extract counts (fast)
        func_count = re.search(r'(\d+)\s+functional\s+requirements?', combined_text, re.IGNORECASE)
        if func_count:
            metadata['functional_count'] = int(func_count.group(1))
        
        perf_count = re.search(r'(\d+)\s+performance\s+requirements?', combined_text, re.IGNORECASE)
        if perf_count:
            metadata['performance_count'] = int(perf_count.group(1))
            
        kpp_count = re.search(r'(\d+)\s+(?:KPP|Key Performance Parameters?)', combined_text, re.IGNORECASE)
        if kpp_count:
            metadata['kpp_count'] = int(kpp_count.group(1))
        
        # Extract user counts
        user_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s+(?:concurrent\s+)?users?', combined_text, re.IGNORECASE)
        if user_match:
            metadata['user_count'] = user_match.group(1)
        
        # ============ STAGE 2: CHECK FOR PRE-STRUCTURED JSON ============
        structured_data = None
        
        for result in rag_results:
            result_metadata = result.get('metadata', {}) if isinstance(result, dict) else getattr(result, 'metadata', {})
            
            # If document already has JSON metadata, use it directly
            if result_metadata.get('format') == 'json' or result_metadata.get('type') == 'structured_requirements':
                try:
                    content = result.content if hasattr(result, 'content') else result.get('content', '')
                    json_content = json.loads(content)
                    if 'requirements' in json_content or 'functional_requirements' in json_content:
                        structured_data = json_content
                        self.log("Found pre-structured JSON requirements in RAG")
                        break
                except json.JSONDecodeError:
                    pass
        
        # If we found structured data, use it
        if structured_data:
            return {
                'functional_requirements': structured_data.get('functional_requirements', structured_data.get('requirements', [])),
                'performance_requirements': structured_data.get('performance_requirements', []),
                'key_performance_parameters': structured_data.get('key_performance_parameters', []),
                'technical_requirements': structured_data.get('technical_requirements', []),
                'metadata': metadata
            }
        
        # ============ STAGE 3: LLM-BASED JSON EXTRACTION ============
        # Only use LLM if we have substantial content and no pre-structured data
        if len(combined_text) > 300:  # Minimum content threshold
            try:
                # Limit text to prevent token overflow
                limited_text = combined_text[:8000]
                
                prompt = f"""Extract system requirements from the following document excerpts and return ONLY valid JSON.

Document Content:
{limited_text}

Extract requirements into this EXACT JSON structure:
{{
  "functional_requirements": [
    {{"id": "FR-001", "description": "full requirement text", "priority": "shall|should|may"}},
    {{"id": "FR-002", "description": "another requirement", "priority": "shall"}}
  ],
  "performance_requirements": [
    {{"id": "PR-001", "description": "performance requirement", "metric": "measurable value", "threshold": "minimum"}},
    {{"id": "PR-002", "description": "another performance req", "metric": "99.5% uptime", "threshold": "99%"}}
  ],
  "key_performance_parameters": [
    {{"name": "System Availability", "threshold": "99%", "objective": "99.9%"}},
    {{"name": "Response Time", "threshold": "2 seconds", "objective": "1 second"}}
  ],
  "technical_requirements": [
    {{"category": "Security", "requirement": "NIST 800-171 compliance"}},
    {{"category": "Integration", "requirement": "RESTful API support"}}
  ]
}}

RULES:
1. Extract actual requirement text word-for-word from the document
2. Preserve requirement IDs if they exist (e.g., REQ-001, FR-1.2.3)
3. Categorize correctly: functional (what it does), performance (how well), technical (how it's built)
4. Include metrics and thresholds where specified
5. Priority: "shall" = mandatory, "should" = desired, "may" = optional
6. If NO requirements found in a category, use empty array []
7. Return ONLY valid JSON, no explanatory text

JSON:"""

                response = self.call_llm(prompt, max_tokens=2500)
                
                # Parse JSON response
                # Try to extract JSON from response (might have extra text)
                json_match = re.search(r'\{[\s\S]*\}', response.strip())
                if json_match:
                    json_text = json_match.group(0)
                    requirements_data = json.loads(json_text)
                    
                    # Validate structure
                    if isinstance(requirements_data, dict):
                        # Add metadata
                        requirements_data['metadata'] = metadata
                        
                        # Count what we extracted
                        total_reqs = (
                            len(requirements_data.get('functional_requirements', [])) +
                            len(requirements_data.get('performance_requirements', [])) +
                            len(requirements_data.get('key_performance_parameters', []))
                        )
                        
                        if total_reqs > 0:
                            self.log(f"LLM extracted {total_reqs} structured requirements from RAG")
                            return requirements_data
                
            except json.JSONDecodeError as e:
                self.log(f"JSON parsing failed in hybrid extraction: {e}", level="WARNING")
            except Exception as e:
                self.log(f"LLM-based extraction failed: {e}", level="WARNING")
        
        # ============ FALLBACK: BASIC REGEX EXTRACTION ============
        # If LLM fails or insufficient content, use enhanced regex
        self.log("Using fallback regex extraction for requirements")
        
        functional_reqs = []
        performance_reqs = []
        
        # Extract functional requirements with simple pattern matching
        func_patterns = [
            r'(?:The system|System)\s+shall\s+([^\.]+\.)',
            r'(?:FR|Functional Requirement)[\s\-:]+\d+[:\s]+([^\.]+\.)',
        ]
        for pattern in func_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            for i, match in enumerate(matches[:10], 1):  # Limit to 10
                functional_reqs.append({
                    'id': f'FR-{i:03d}',
                    'description': match.strip(),
                    'priority': 'shall' if 'shall' in match.lower() else 'should'
                })
        
        # Extract performance requirements
        perf_patterns = [
            r'(?:availability|uptime)[:\s]+(\d+\.?\d*%)',
            r'response\s+time[:\s]+([^\.]+)',
            r'throughput[:\s]+([^\.]+)',
        ]
        for pattern in perf_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            for i, match in enumerate(matches[:5], 1):
                performance_reqs.append({
                    'id': f'PR-{i:03d}',
                    'description': f'Performance metric: {match}',
                    'metric': match.strip()
                })
        
        return {
            'functional_requirements': functional_reqs,
            'performance_requirements': performance_reqs,
            'key_performance_parameters': [],
            'technical_requirements': [],
            'metadata': metadata
        }

    def _extract_requirements_from_rag(self, rag_results: List[Dict]) -> Dict:
        """
        Extract requirements from RAG results (HYBRID ENHANCED)
        
        This is now a wrapper that calls the hybrid extraction method
        """
        # Call the hybrid extraction method
        hybrid_data = self._extract_requirements_hybrid(rag_results)
        
        # For backward compatibility, also include simple counts
        extracted = hybrid_data.get('metadata', {}).copy()
        
        # Add the structured data
        extracted['functional_requirements'] = hybrid_data.get('functional_requirements', [])
        extracted['performance_requirements'] = hybrid_data.get('performance_requirements', [])
        extracted['key_performance_parameters'] = hybrid_data.get('key_performance_parameters', [])
        
        return extracted

    def _extract_kpp_from_rag(self, rag_results: List[Dict]) -> Dict:
        """
        Extract Key Performance Parameters (HYBRID ENHANCED)
        
        Uses hybrid extraction to get structured KPP data
        """
        # Use hybrid extraction
        hybrid_data = self._extract_requirements_hybrid(rag_results)
        
        # Get KPPs from hybrid extraction
        kpps = hybrid_data.get('key_performance_parameters', [])
        
        if kpps:
            # Return structured KPP data
            return {
                'kpps': kpps,
                'kpp_count': len(kpps),
                'kpp_list': [kpp.get('name', 'Unknown KPP') for kpp in kpps]
            }
        
        # Fallback to regex if hybrid didn't find KPPs
        extracted = {}
        combined_text = "\n".join([
            r.content if hasattr(r, 'content') else r.get('content', '')
            for r in rag_results
        ])
        
        import re
        
        # Extract KPP count
        kpp_match = re.search(r'(\d+)\s+(?:KPP|Key Performance Parameter)', combined_text, re.IGNORECASE)
        if kpp_match:
            extracted['kpp_count'] = kpp_match.group(1)
        
        # Look for specific performance metrics
        if 'availability' in combined_text.lower():
            avail_match = re.search(r'availability[:\s]+(\d+\.?\d*%)', combined_text, re.IGNORECASE)
            if avail_match:
                extracted['availability_target'] = avail_match.group(1)
        
        if 'response time' in combined_text.lower():
            response_match = re.search(r'response\s+time[:\s]+([^\n\.]+)', combined_text, re.IGNORECASE)
            if response_match:
                extracted['response_time_target'] = response_match.group(1).strip()
        
        return extracted

    # ==================== LLM GENERATION METHODS ====================
    # These methods use RAG context + LLM to generate narrative sections

    def _generate_background_from_rag(self, rag_strategies: List[Dict], capability_gap: str, project_info: Dict) -> Dict:
        """
        Generate Section 1 (Background) content from RAG

        Generates: current_situation, strategic_alignment, program_history
        """
        generated = {}

        if not rag_strategies:
            return generated

        # Combine RAG content
        rag_text = "\n\n".join([s.get('content', '')[:500] for s in rag_strategies[:3]])

        # Generate current situation
        try:
            prompt = f"""Based on this program information, generate a 2-3 sentence description of the current situation that led to this acquisition need.

Program: {project_info.get('program_name', 'Unknown')}
Capability Gap: {capability_gap}

Context from similar programs:
{rag_text[:800]}

Generate current situation:"""
            current_situation = self.call_llm(prompt, max_tokens=300).strip()
            generated['current_situation'] = current_situation
            self.log("Generated current_situation from RAG")
        except Exception as e:
            self.log(f"Failed to generate current_situation: {e}", level="WARNING")

        # Generate strategic alignment
        try:
            prompt = f"""Based on this program information, generate a 2-3 sentence description of how this acquisition aligns with DoD strategic objectives.

Program: {project_info.get('program_name', 'Unknown')}
Estimated Value: {project_info.get('estimated_value', 'TBD')}

Generate strategic alignment:"""
            strategic_alignment = self.call_llm(prompt, max_tokens=300).strip()
            generated['strategic_alignment'] = strategic_alignment
            self.log("Generated strategic_alignment from RAG")
        except Exception as e:
            self.log(f"Failed to generate strategic_alignment: {e}", level="WARNING")

        # Generate program history
        try:
            prompt = f"""Generate a brief 1-2 sentence program history for this new acquisition program.

Program: {project_info.get('program_name', 'Unknown')}

Context: This is a new program acquisition. Mention if market research was conducted and when planning began.

Generate program history:"""
            program_history = self.call_llm(prompt, max_tokens=250).strip()
            generated['program_history'] = program_history
            self.log("Generated program_history from RAG")
        except Exception as e:
            self.log(f"Failed to generate program_history: {e}", level="WARNING")

        return generated

    def _generate_applicable_conditions_from_rag(self, project_info: Dict, rag_extracted: Dict) -> Dict:
        """
        Generate Section 2 (Applicable Conditions) content

        Generates: acat_level, acat_rationale, applicable_regulations, acquisition_pathway
        """
        generated = {}

        # Determine ACAT level from cost
        estimated_value_str = project_info.get('estimated_value', '$5M')
        try:
            value_millions = float(re.findall(r'[\d\.]+', estimated_value_str)[0])
        except:
            value_millions = 5.0

        if value_millions < 10:
            generated['acat_level'] = "ACAT III"
            generated['acat_rationale'] = f"Program estimated at {estimated_value_str}, below ACAT II threshold of $185M RDT&E or $480M procurement."
        elif value_millions < 100:
            generated['acat_level'] = "ACAT II"
            generated['acat_rationale'] = f"Program estimated at {estimated_value_str}, exceeds ACAT III threshold but below ACAT IC threshold."
        else:
            generated['acat_level'] = "ACAT IC"
            generated['acat_rationale'] = f"Major Defense Acquisition Program estimated at {estimated_value_str}."

        # Generate applicable regulations
        try:
            prompt = f"""List the key DoD and FAR regulations applicable to this acquisition in 2-3 sentences.

Program: {project_info.get('program_name', 'Unknown')}
ACAT Level: {generated.get('acat_level', 'ACAT III')}
Contract Type: {project_info.get('contract_type', 'services')}

Generate applicable regulations:"""
            applicable_regs = self.call_llm(prompt, max_tokens=300).strip()
            generated['applicable_regulations'] = applicable_regs
            self.log("Generated applicable_regulations")
        except Exception as e:
            self.log(f"Failed to generate applicable_regulations: {e}", level="WARNING")

        # Acquisition pathway from RAG or generate
        acquisition_pathway = rag_extracted.get('acquisition_approach', '')
        if not acquisition_pathway:
            acquisition_pathway = "Middle Tier Acquisition (MTA) - Rapid Prototyping pathway per 10 USC 2302" if value_millions < 50 else "Traditional DoD Acquisition Process per DoDI 5000.02"

        generated['acquisition_pathway'] = acquisition_pathway

        return generated

    def _generate_tradeoffs_from_strategy(self, strategy: Dict, project_info: Dict) -> Dict:
        """
        Generate Section 6 (Trade-offs) content from strategy

        Generates: cost_performance_tradeoffs, schedule_performance_tradeoffs, risk_tradeoffs
        """
        generated = {}

        try:
            prompt = f"""Generate a 2-3 sentence description of cost vs. performance trade-offs for this acquisition.

Program: {project_info.get('program_name', 'Unknown')}
Contract Type: {strategy.get('contract_type_recommendation', 'FFP')}
Estimated Value: {project_info.get('estimated_value', 'TBD')}

Generate cost vs. performance trade-offs:"""
            cost_perf = self.call_llm(prompt, max_tokens=300).strip()
            generated['cost_performance_tradeoffs'] = cost_perf
            self.log("Generated cost_performance_tradeoffs")
        except Exception as e:
            self.log(f"Failed to generate cost_performance_tradeoffs: {e}", level="WARNING")

        try:
            prompt = f"""Generate a 2-3 sentence description of schedule vs. performance trade-offs for this acquisition.

Program: {project_info.get('program_name', 'Unknown')}
Period of Performance: {project_info.get('period_of_performance', '12 months base + 4 option years')}

Generate schedule vs. performance trade-offs:"""
            schedule_perf = self.call_llm(prompt, max_tokens=300).strip()
            generated['schedule_performance_tradeoffs'] = schedule_perf
            self.log("Generated schedule_performance_tradeoffs")
        except Exception as e:
            self.log(f"Failed to generate schedule_performance_tradeoffs: {e}", level="WARNING")

        try:
            prompt = f"""Generate a 2-3 sentence description of risk considerations for this acquisition trade-off analysis.

Program: {project_info.get('program_name', 'Unknown')}
Source Selection: {strategy.get('source_selection_method', 'Best Value')}

Generate risk trade-off considerations:"""
            risk_trade = self.call_llm(prompt, max_tokens=300).strip()
            generated['risk_tradeoffs'] = risk_trade
            self.log("Generated risk_tradeoffs")
        except Exception as e:
            self.log(f"Failed to generate risk_tradeoffs: {e}", level="WARNING")

        return generated

    def _generate_streamlining_from_contract(self, strategy: Dict, project_info: Dict) -> Dict:
        """
        Generate Section 7 (Streamlining) content from contract type

        Generates: streamlining_opportunities, commercial_item_determination
        """
        generated = {}

        contract_type = strategy.get('contract_type_recommendation', 'FFP')

        try:
            prompt = f"""Generate 2-3 sentences describing acquisition streamlining opportunities for this program.

Program: {project_info.get('program_name', 'Unknown')}
Contract Type: {contract_type}
Contract Vehicle: {strategy.get('contract_vehicle', 'GSA Schedule')}

Focus on: use of existing contract vehicles, commercial practices, simplified procedures.

Generate streamlining opportunities:"""
            streamlining = self.call_llm(prompt, max_tokens=350).strip()
            generated['streamlining_opportunities'] = streamlining
            self.log("Generated streamlining_opportunities")
        except Exception as e:
            self.log(f"Failed to generate streamlining_opportunities: {e}", level="WARNING")

        try:
            prompt = f"""Generate 1-2 sentences on commercial item determination for this program.

Program: {project_info.get('program_name', 'Unknown')}
Type: {project_info.get('contract_type', 'services')}

Is this a commercial item or service per FAR Part 2? Explain briefly.

Generate commercial item determination:"""
            commercial = self.call_llm(prompt, max_tokens=250).strip()
            generated['commercial_item_determination'] = commercial
            self.log("Generated commercial_item_determination")
        except Exception as e:
            self.log(f"Failed to generate commercial_item_determination: {e}", level="WARNING")

        return generated

    def _generate_acquisition_considerations(self, strategy: Dict, project_info: Dict, market_research: Dict) -> Dict:
        """
        Generate Section 10 (Acquisition Considerations) content

        Generates: budgeting_funding, competition_requirements, security_requirements
        """
        generated = {}

        try:
            prompt = f"""Generate 2-3 sentences on budgeting and funding strategy for this acquisition.

Program: {project_info.get('program_name', 'Unknown')}
Estimated Value: {project_info.get('estimated_value', 'TBD')}
Period: {project_info.get('period_of_performance', '12 months base + 4 option years')}

Include: funding source, appropriation type, funding profile considerations.

Generate budgeting and funding:"""
            budgeting = self.call_llm(prompt, max_tokens=350).strip()
            generated['budgeting_funding'] = budgeting
            self.log("Generated budgeting_funding")
        except Exception as e:
            self.log(f"Failed to generate budgeting_funding: {e}", level="WARNING")

        try:
            prompt = f"""Generate 2-3 sentences on competition requirements for this acquisition.

Program: {project_info.get('program_name', 'Unknown')}
Source Selection: {strategy.get('source_selection_method', 'Best Value')}

Include: full and open competition, exceptions if any, competitive procedures.

Generate competition requirements:"""
            competition = self.call_llm(prompt, max_tokens=300).strip()
            generated['competition_requirements'] = competition
            self.log("Generated competition_requirements")
        except Exception as e:
            self.log(f"Failed to generate competition_requirements: {e}", level="WARNING")

        try:
            prompt = f"""Generate 2-3 sentences on security requirements for this acquisition.

Program: {project_info.get('program_name', 'Unknown')}
Type: {project_info.get('contract_type', 'services')}

Include: NIST 800-171 compliance, FedRAMP requirements, data protection.

Generate security requirements:"""
            security = self.call_llm(prompt, max_tokens=300).strip()
            generated['security_requirements'] = security
            self.log("Generated security_requirements")
        except Exception as e:
            self.log(f"Failed to generate security_requirements: {e}", level="WARNING")

        return generated

    def _generate_market_research_summary(self, market_research: Dict, rag_strategies: List[Dict]) -> Dict:
        """
        Generate Section 11 (Market Research) content

        Generates: market_research_summary, industry_capabilities, competitive_landscape
        """
        generated = {}

        # Use provided market research or generate from RAG
        market_summary = market_research.get('competitive_landscape', '')

        if not market_summary and rag_strategies:
            rag_text = "\n".join([s.get('content', '')[:400] for s in rag_strategies[:2]])
            try:
                prompt = f"""Generate a 2-3 sentence market research summary for this acquisition.

Context from similar programs:
{rag_text[:600]}

Include: market research methods used, number of vendors identified, competition assessment.

Generate market research summary:"""
                market_summary = self.call_llm(prompt, max_tokens=350).strip()
                generated['market_research_summary'] = market_summary
                self.log("Generated market_research_summary")
            except Exception as e:
                self.log(f"Failed to generate market_research_summary: {e}", level="WARNING")
        else:
            generated['market_research_summary'] = market_summary

        try:
            prompt = f"""Generate 2-3 sentences on industry capabilities for this type of acquisition.

Type: Cloud-based IT services / Software as a Service
Market Research: {market_summary[:200] if market_summary else 'Multiple qualified vendors expected'}

Generate industry capabilities:"""
            industry_cap = self.call_llm(prompt, max_tokens=300).strip()
            generated['industry_capabilities'] = industry_cap
            self.log("Generated industry_capabilities")
        except Exception as e:
            self.log(f"Failed to generate industry_capabilities: {e}", level="WARNING")

        try:
            competitive_landscape = market_research.get('competitive_landscape', 'Competitive market with multiple qualified vendors expected.')
            generated['competitive_landscape'] = competitive_landscape
        except Exception as e:
            self.log(f"Failed to set competitive_landscape: {e}", level="WARNING")

        return generated

    def _generate_sustainment_content(self, project_info: Dict, contract_type: str) -> Dict:
        """
        Generate Section 17 (Life Cycle Sustainment) content

        Generates: sustainment_strategy, maintenance_approach, training_requirements
        """
        generated = {}

        try:
            prompt = f"""Generate 2-3 sentences on sustainment strategy for this system.

Program: {project_info.get('program_name', 'Unknown')}
Type: Cloud-based system
Period: {project_info.get('period_of_performance', '5 years')}

Include: sustainment approach, contractor support, lifecycle management.

Generate sustainment strategy:"""
            sustainment = self.call_llm(prompt, max_tokens=350).strip()
            generated['sustainment_strategy'] = sustainment
            self.log("Generated sustainment_strategy")
        except Exception as e:
            self.log(f"Failed to generate sustainment_strategy: {e}", level="WARNING")

        try:
            prompt = f"""Generate 2-3 sentences on maintenance approach for this cloud-based system.

Program: {project_info.get('program_name', 'Unknown')}

Include: maintenance responsibilities, SLA requirements, update procedures.

Generate maintenance approach:"""
            maintenance = self.call_llm(prompt, max_tokens=300).strip()
            generated['maintenance_approach'] = maintenance
            self.log("Generated maintenance_approach")
        except Exception as e:
            self.log(f"Failed to generate maintenance_approach: {e}", level="WARNING")

        try:
            prompt = f"""Generate 2-3 sentences on training requirements for this system.

Program: {project_info.get('program_name', 'Unknown')}
Users: Government personnel and administrators

Include: user training, admin training, training materials.

Generate training requirements:"""
            training = self.call_llm(prompt, max_tokens=300).strip()
            generated['training_requirements'] = training
            self.log("Generated training_requirements")
        except Exception as e:
            self.log(f"Failed to generate training_requirements: {e}", level="WARNING")

        return generated

    def _generate_test_evaluation_content(self, project_info: Dict, requirements_analysis: Dict) -> Dict:
        """
        Generate Section 18 (Test & Evaluation) content

        Generates: te_strategy, dte_approach, acceptance_criteria
        """
        generated = {}

        try:
            prompt = f"""Generate 2-3 sentences on the Test & Evaluation strategy for this system.

Program: {project_info.get('program_name', 'Unknown')}
Type: Cloud-based software system

Include: T&E phases, test environment, evaluation approach.

Generate T&E strategy:"""
            te_strategy = self.call_llm(prompt, max_tokens=350).strip()
            generated['te_strategy'] = te_strategy
            self.log("Generated te_strategy")
        except Exception as e:
            self.log(f"Failed to generate te_strategy: {e}", level="WARNING")

        try:
            prompt = f"""Generate 2-3 sentences on Development Test & Evaluation approach.

Program: {project_info.get('program_name', 'Unknown')}

Include: DT&E objectives, test cases, functional testing.

Generate DT&E approach:"""
            dte = self.call_llm(prompt, max_tokens=300).strip()
            generated['dte_approach'] = dte
            self.log("Generated dte_approach")
        except Exception as e:
            self.log(f"Failed to generate dte_approach: {e}", level="WARNING")

        try:
            kpps = requirements_analysis.get('kpps', [])
            kpp_desc = ", ".join([k.get('name', '') for k in kpps[:2]]) if kpps else "System availability, performance"

            prompt = f"""Generate 2-3 sentences on acceptance criteria for this system.

Program: {project_info.get('program_name', 'Unknown')}
Key Performance Parameters: {kpp_desc}

Include: what must be demonstrated, acceptance testing, criteria for acceptance.

Generate acceptance criteria:"""
            acceptance = self.call_llm(prompt, max_tokens=300).strip()
            generated['acceptance_criteria'] = acceptance
            self.log("Generated acceptance_criteria")
        except Exception as e:
            self.log(f"Failed to generate acceptance_criteria: {e}", level="WARNING")

        return generated

    #  ==================== SMART DEFAULTS ====================
    # Generate intelligent defaults for common fields

    def _generate_smart_defaults(self, project_info: Dict, rag_extracted: Dict, config: Dict) -> Dict:
        """
        Generate intelligent defaults for personnel, dates, costs, and other common fields

        Returns dictionary of smart default values based on context
        """
        defaults = {}

        # ===== Personnel Defaults =====
        # Use descriptive defaults instead of blank TBDs
        defaults['pm_name'] = "TBD - To be assigned"
        defaults['co_name'] = "TBD - To be assigned"
        defaults['cor_name'] = "TBD - To be assigned"
        defaults['legal_name'] = "TBD - To be assigned"
        defaults['sbs_name'] = "TBD - To be assigned"
        defaults['cost_analyst_name'] = "TBD - To be assigned"

        # Organization defaults from RAG or generic
        org = project_info.get('organization', 'Department of Defense')
        defaults['pm_org'] = f"{org} - Program Executive Office"
        defaults['co_org'] = f"{org} - Contracting Office"
        defaults['cor_org'] = f"{org} - Program Office"
        defaults['legal_org'] = f"{org} - Office of General Counsel"
        defaults['sbs_org'] = f"{org} - Small Business Office"
        defaults['cost_analyst_org'] = f"{org} - Cost Analysis Division"

        # Contact placeholders
        defaults['pm_contact'] = "TBD"
        defaults['co_contact'] = "TBD"
        defaults['cor_contact'] = "TBD"
        defaults['legal_contact'] = "TBD"
        defaults['sbs_contact'] = "TBD"
        defaults['cost_analyst_contact'] = "TBD"

        # Titles
        defaults['pm_title'] = "Program Manager"
        defaults['co_title'] = "Contracting Officer"
        defaults['legal_title'] = "Legal Counsel"
        defaults['sbs_title'] = "Small Business Specialist"

        # ===== Date Defaults =====
        # Approval dates - use "Upon plan approval"
        defaults['co_date'] = "Upon plan approval"
        defaults['pm_date'] = "Upon plan approval"
        defaults['legal_date'] = "Upon plan approval"
        defaults['sbs_date'] = "Upon plan approval"

        # Fiscal years - calculate from IOC date if available
        ioc_date_str = rag_extracted.get('ioc_date', '')
        if ioc_date_str and any(char.isdigit() for char in ioc_date_str):
            try:
                # Extract year from "June 2026" format
                import re
                year_match = re.search(r'20\d{2}', ioc_date_str)
                if year_match:
                    base_year = int(year_match.group())
                    defaults['fy_base'] = str(base_year)
                    defaults['fy_opt1'] = str(base_year + 1)
                    defaults['fy_opt2'] = str(base_year + 2)
                    defaults['fy_opt3'] = str(base_year + 3)
                    defaults['fy_opt4'] = str(base_year + 4)
            except:
                pass

        # ===== Cost Breakdown Defaults =====
        # Calculate yearly breakdown from development_cost if available
        dev_cost_str = rag_extracted.get('development_cost', '')
        if dev_cost_str and '$' in dev_cost_str:
            try:
                # Parse cost from "$2.5M" format
                cost_value = self._parse_cost_string(dev_cost_str)
                if cost_value > 0:
                    yearly = self._calculate_yearly_breakdown(cost_value, num_years=5)

                    # Format as currency strings
                    defaults['dev_base'] = f"${yearly['base_year']:,.0f}"
                    defaults['dev_opt1'] = f"${yearly.get('option_year_1', 0):,.0f}"
                    defaults['dev_opt2'] = f"${yearly.get('option_year_2', 0):,.0f}"
                    defaults['dev_opt3'] = f"${yearly.get('option_year_3', 0):,.0f}"
                    defaults['dev_opt4'] = f"${yearly.get('option_year_4', 0):,.0f}"
                    defaults['dev_total'] = dev_cost_str

                    # Calculate total per year (sum across categories)
                    defaults['total_base'] = defaults['dev_base']
                    defaults['total_opt1'] = defaults['dev_opt1']
                    defaults['total_opt2'] = defaults['dev_opt2']
                    defaults['total_opt3'] = defaults['dev_opt3']
                    defaults['total_opt4'] = defaults['dev_opt4']
            except:
                pass

        # Production costs (typically $0 for services/software)
        if 'dev_base' in defaults:
            defaults['prod_base'] = "$0"
            defaults['prod_opt1'] = "$0"
            defaults['prod_opt2'] = "$0"
            defaults['prod_opt3'] = "$0"
            defaults['prod_opt4'] = "$0"
            defaults['prod_total'] = "$0"

        # O&M costs (calculated from lifecycle - development)
        lifecycle_cost_str = rag_extracted.get('lifecycle_cost', '')
        if lifecycle_cost_str and '$' in lifecycle_cost_str and 'dev_base' in defaults:
            try:
                lifecycle_value = self._parse_cost_string(lifecycle_cost_str)
                dev_value = self._parse_cost_string(dev_cost_str)
                om_total = lifecycle_value - dev_value
                if om_total > 0:
                    om_yearly = self._calculate_yearly_breakdown(om_total, num_years=5)
                    defaults['om_base'] = f"${om_yearly['base_year']:,.0f}"
                    defaults['om_opt1'] = f"${om_yearly.get('option_year_1', 0):,.0f}"
                    defaults['om_opt2'] = f"${om_yearly.get('option_year_2', 0):,.0f}"
                    defaults['om_opt3'] = f"${om_yearly.get('option_year_3', 0):,.0f}"
                    defaults['om_opt4'] = f"${om_yearly.get('option_year_4', 0):,.0f}"
                    defaults['om_total'] = f"${om_total:,.0f}"
            except:
                pass

        # ===== Contract Structure Defaults =====
        period_of_performance = project_info.get('period_of_performance', '12 months base + 4 option years')
        defaults['contract_structure'] = f"One base year plus four one-year option periods ({period_of_performance})"
        defaults['option_periods'] = "Four one-year option periods (exercisable at government discretion)"

        # CLIN structure based on contract type
        contract_type = project_info.get('contract_type', 'services')
        if contract_type == 'services':
            defaults['clin_structure'] = "CLIN 0001: Base Year Services\nCLIN 1001-1004: Option Year Services (Years 1-4)"
        else:
            defaults['clin_structure'] = "CLIN 0001: Base Year R&D\nCLIN 0002: Base Year ODCs\nCLIN 1001-1004: Option Year R&D"

        # Incentive structure based on contract type
        defaults['incentive_structure'] = "No incentive fees (FFP contract)" if 'FFP' in str(rag_extracted.get('contract_type', '')) else "Award fee structure (up to 10% of base fee)"

        # ===== Requirements Defaults =====
        defaults['requirements_documents'] = "Capability Development Document (CDD), Initial Capabilities Document (ICD), System Requirements Document (SRD)"

        # ===== Other Common Defaults =====
        defaults['mda_info'] = "Component Acquisition Executive (CAE)" if 'ACAT III' in str(rag_extracted.get('acat_level', '')) else "Milestone Decision Authority (MDA): Program Executive Officer"
        defaults['special_designations'] = "None"
        defaults['version'] = "1.0"
        defaults['last_updated'] = datetime.now().strftime('%B %d, %Y')
        defaults['distribution'] = "Approved for distribution to authorized government personnel only"

        # Additional defaults for simplified sections
        defaults['phase_in_out_plan'] = "Phased deployment across installations over 6-month period post-IOC"
        defaults['performance_milestones'] = "Key milestones: Award, Kickoff, Design Review, Development Complete, Testing Complete, Deployment, IOC, FOC"
        defaults['evaluation_factors'] = "Technical Approach (Most Important), Past Performance, Cost/Price"
        defaults['evaluation_weights'] = "Technical Approach: 50%, Past Performance: 30%, Cost/Price: 20%"
        defaults['overall_strategy'] = "Competitive acquisition using existing contract vehicle with best value trade-off source selection"
        defaults['acquisition_phases'] = "Single-phase acquisition: Requirements → RFP → Source Selection → Award → Development → Deployment → Sustainment"
        defaults['alternative_vehicles'] = "Considered: GSA Schedule 70, SEWP, Direct contract. Selected vehicle provides best mix of speed, competition, and small business access."
        defaults['logistics_support'] = "Contractor logistics support for cloud-based system. Government provides user-side network connectivity and end-user devices."
        defaults['ote_approach'] = "Operational testing conducted in representative user environment with actual end users. Testing validates operational effectiveness and suitability."
        defaults['small_business_goal'] = "Maximize small business participation through set-aside determination and robust subcontracting requirements"

        return defaults

    def _parse_cost_string(self, cost_str: str) -> float:
        """Parse cost string like '$2.5M' or '$6.4M' into float"""
        import re
        try:
            # Extract number
            match = re.search(r'[\d\.]+', cost_str)
            if not match:
                return 0.0

            value = float(match.group())

            # Handle M, K, B suffixes
            cost_upper = cost_str.upper()
            if 'M' in cost_upper:
                value *= 1_000_000
            elif 'K' in cost_upper:
                value *= 1_000
            elif 'B' in cost_upper:
                value *= 1_000_000_000

            return value
        except:
            return 0.0

    def _calculate_yearly_breakdown(
        self,
        total_cost: float,
        num_years: int = 5,
        escalation_rate: float = 0.03,
        base_year_percentage: float = 0.25
    ) -> Dict[str, float]:
        """
        Calculate year-by-year cost breakdown from total cost
        (Copied from IGCE agent - Phase 1 logic)
        """
        base_year_cost = total_cost * base_year_percentage
        remaining_cost = total_cost - base_year_cost
        option_years = num_years - 1

        if option_years > 0:
            base_option_cost = remaining_cost / option_years
            yearly_costs = {'base_year': base_year_cost}

            for year in range(1, num_years):
                if year == 1:
                    option_cost = base_option_cost
                else:
                    option_cost = base_option_cost * (1 + escalation_rate) ** (year - 1)
                yearly_costs[f'option_year_{year}'] = option_cost
        else:
            yearly_costs = {'base_year': total_cost}

        return yearly_costs

    def _analyze_requirements(self, requirements_content: str) -> Dict:
        """Analyze requirements documentation with RAG support"""
        
        # Query RAG for ALMS ICD (Initial Capabilities Document) - capability gap
        capability_gap = "Current systems lack modern cloud-based capabilities and real-time data access"
        if self.retriever:
            try:
                gap_results = self.retriever.retrieve(
                    "What is the ALMS capability gap and current system limitations? What problems need solving?",
                    k=2
                )
                if gap_results and len(gap_results) > 0:
                    # Extract capability gap from top result - use correct field access
                    gap_text = gap_results[0].content if hasattr(gap_results[0], 'content') else gap_results[0].get('content', '')
                    if 'capability gap' in gap_text.lower() or 'current' in gap_text.lower():
                        # Use LLM to extract and summarize capability gap
                        prompt = f"""Extract the capability gap and current system limitations from this text.
                        Provide a 2-3 sentence summary.
                        
                        Text: {gap_text[:1000]}"""
                        capability_gap = self.call_llm(prompt, max_tokens=300).strip()
                        self.log(f"RAG provided capability gap from ALMS documents")
            except Exception as e:
                self.log(f"RAG query for capability gap failed: {e}", level="WARNING")
        
        # Query RAG for ALMS CDD (Capability Development Document) - requirements
        key_requirements = []
        if self.retriever:
            try:
                req_results = self.retriever.retrieve(
                    "What are the ALMS functional requirements and performance requirements? List key system requirements.",
                    k=3
                )
                if req_results and len(req_results) > 0:
                    # Use extraction method for structured requirements data
                    req_extracted = self._extract_requirements_from_rag(req_results)

                    # Combine requirement texts
                    req_text = '\n'.join([r.content if hasattr(r, 'content') else r.get('content', '')[:500] for r in req_results[:2]])

                    # Use LLM to extract requirements
                    prompt = f"""Extract 5-8 key system requirements from this text.
                    Format as a bullet list.
                    
                    Text: {req_text}"""
                    req_response = self.call_llm(prompt, max_tokens=500)
                    
                    # Parse requirements
                    for line in req_response.split('\n'):
                        cleaned = line.strip().lstrip('-•*').strip()
                        if cleaned and len(cleaned) > 20:
                            key_requirements.append(cleaned)
                    
                    self.log(f"RAG provided {len(key_requirements)} requirements from ALMS documents")
            except Exception as e:
                self.log(f"RAG query for requirements failed: {e}", level="WARNING")
        
        # Fallback to defaults if RAG didn't provide requirements
        if not key_requirements:
            key_requirements = [
                "Cloud-based deployment (FedRAMP Moderate)",
                "99.5% system availability",
                "Mobile access capability",
                "Integration with existing enterprise systems",
                "NIST 800-171 compliance"
            ]
        
        # Query RAG for KPPs (Key Performance Parameters)
        kpps = []
        if self.retriever:
            try:
                kpp_results = self.retriever.retrieve(
                    "What are the ALMS Key Performance Parameters (KPPs) and performance thresholds?",
                    k=2
                )
                if kpp_results and len(kpp_results) > 0:
                    kpp_text = kpp_results[0].content if hasattr(kpp_results[0], 'content') else kpp_results[0].get('content', '')

                    # Use extraction method for structured KPP data
                    kpp_extracted = self._extract_kpp_from_rag(kpp_results)

                    # Use LLM to extract KPPs
                    prompt = f"""Extract Key Performance Parameters (KPPs) with thresholds and objectives from this text.
                    Format each as: name, threshold, objective
                    
                    Text: {kpp_text[:800]}"""
                    kpp_response = self.call_llm(prompt, max_tokens=400)
                    
                    # Parse into structured format (simplified parsing)
                    if 'availability' in kpp_response.lower():
                        kpps.append({
                            "name": "System Availability",
                            "threshold": "99.5%",
                            "objective": "99.9%"
                        })
                    if 'performance' in kpp_response.lower() or 'transaction' in kpp_response.lower():
                        kpps.append({
                            "name": "Transaction Performance", 
                            "threshold": "<3 seconds",
                            "objective": "<1 second"
                        })
                    if 'accuracy' in kpp_response.lower():
                        kpps.append({
                            "name": "Inventory Accuracy",
                            "threshold": "95%",
                            "objective": "98%"
                        })
                    
                    self.log(f"RAG provided {len(kpps)} KPPs from ALMS documents")
            except Exception as e:
                self.log(f"RAG query for KPPs failed: {e}", level="WARNING")
        
        # Fallback KPPs
        if not kpps:
            kpps = [
                {"name": "System Availability", "threshold": "99.5%", "objective": "99.9%"},
                {"name": "Transaction Performance", "threshold": "<3 seconds", "objective": "<1 second"}
            ]
        
        return {
            'capability_gap': capability_gap,
            'key_requirements': key_requirements[:8],  # Limit to 8
            'kpps': kpps
        }
    
    def _determine_acquisition_strategy(self, project_info: Dict, market_research: Dict, contract_type: str) -> Dict:
        """Determine overall acquisition strategy"""
        # Parse estimated value
        estimated_value_str = project_info.get('estimated_value', '$5M')
        value_millions = 5.0
        if 'M' in estimated_value_str:
            try:
                value_millions = float(re.findall(r'[\d\.]+', estimated_value_str)[0])
            except:
                pass
        
        # Determine contract vehicle
        if contract_type == 'research_development':
            contract_vehicle = "OASIS+ R&D Pool"
            contract_type_rec = "Cost-Plus-Fixed-Fee (CPFF)"
        else:
            contract_vehicle = "GSA Schedule 70 / OASIS+"
            contract_type_rec = "Firm-Fixed-Price (FFP)"
        
        # Determine source selection
        if value_millions < 5:
            source_selection = "Lowest Price Technically Acceptable (LPTA)"
        else:
            source_selection = "Best Value Trade-Off"
        
        return {
            'contract_vehicle': contract_vehicle,
            'contract_type_recommendation': contract_type_rec,
            'source_selection_method': source_selection,
            'rationale': f"Based on {contract_type} contract requirements and estimated value of {estimated_value_str}"
        }
    
    def _assess_risks(self, requirements_content: str, contract_type: str) -> Dict:
        """Perform comprehensive risk assessment"""
        risks = [
            {
                'id': 'R-001',
                'description': 'Technical complexity may exceed contractor capabilities',
                'probability': 'Medium',
                'impact': 'High',
                'mitigation': 'Require demonstration of similar system development in past performance',
                'owner': 'Program Manager'
            },
            {
                'id': 'R-002',
                'description': 'Integration with legacy systems may encounter unforeseen challenges',
                'probability': 'Medium',
                'impact': 'Medium',
                'mitigation': 'Conduct interface control document (ICD) review and prototyping',
                'owner': 'Technical Lead'
            },
            {
                'id': 'R-003',
                'description': 'Schedule slippage due to security authorization delays',
                'probability': 'High',
                'impact': 'Medium',
                'mitigation': 'Initiate ATO process early, engage ISSO/ISSM from project start',
                'owner': 'Program Manager'
            },
            {
                'id': 'R-004',
                'description': 'Cost growth due to unclear requirements',
                'probability': 'Low',
                'impact': 'High',
                'mitigation': 'Develop detailed PWS with measurable performance standards',
                'owner': 'Contracting Officer'
            }
        ]
        
        if contract_type == 'research_development':
            risks.append({
                'id': 'R-005',
                'description': 'Technology maturation may not achieve target TRL',
                'probability': 'Medium',
                'impact': 'High',
                'mitigation': 'Include technology maturation milestones with go/no-go decision points',
                'owner': 'Program Manager'
            })
        
        return {
            'risks': risks,
            'overall_risk_level': 'Medium'
        }
    
    def _generate_schedule(self, project_info: Dict, config: Dict) -> List[Dict]:
        """Generate acquisition schedule with key milestones"""
        start_date = datetime.now()
        
        milestones = [
            {'event': 'Acquisition Plan Approval', 'date': start_date, 'status': 'In Progress'},
            {'event': 'Sources Sought Notice Posted', 'date': start_date + timedelta(days=7), 'status': 'Planned'},
            {'event': 'Sources Sought Responses Due', 'date': start_date + timedelta(days=28), 'status': 'Planned'},
            {'event': 'RFI Released', 'date': start_date + timedelta(days=35), 'status': 'Planned'},
            {'event': 'RFI Responses Due', 'date': start_date + timedelta(days=70), 'status': 'Planned'},
            {'event': 'Industry Day', 'date': start_date + timedelta(days=77), 'status': 'Planned'},
            {'event': 'Draft RFP Release', 'date': start_date + timedelta(days=90), 'status': 'Planned'},
            {'event': 'Final RFP Release', 'date': start_date + timedelta(days=120), 'status': 'Planned'},
            {'event': 'Proposals Due', 'date': start_date + timedelta(days=165), 'status': 'Planned'},
            {'event': 'Source Selection Complete', 'date': start_date + timedelta(days=210), 'status': 'Planned'},
            {'event': 'Contract Award', 'date': start_date + timedelta(days=240), 'status': 'Planned'}
        ]
        
        return milestones
    
    def _analyze_small_business_opportunities(self, project_info: Dict, market_research: Dict) -> Dict:
        """Analyze small business participation opportunities"""
        # Parse estimated value
        estimated_value_str = project_info.get('estimated_value', '$5M')
        value_millions = 5.0
        if 'M' in estimated_value_str:
            try:
                value_millions = float(re.findall(r'[\d\.]+', estimated_value_str)[0])
            except:
                pass
        
        # Determine set-aside
        if value_millions < 10:
            set_aside_type = "Small Business Set-Aside"
            set_aside_rationale = "Market research indicates adequate small business competition"
        else:
            set_aside_type = "Unrestricted (with subcontracting plan required)"
            set_aside_rationale = "Value exceeds small business threshold but strong subcontracting opportunities exist"
        
        return {
            'set_aside_type': set_aside_type,
            'set_aside_rationale': set_aside_rationale,
            'naics_code': "541512",
            'size_standard': "$34M",
            'subcontracting_goal': "40% small business subcontracting"
        }
    
    # ==================== REQUIREMENTS FORMATTING ====================
    
    def _format_requirements_for_template(self, requirements_data: Dict) -> Dict:
        """
        Format extracted requirements data for template population
        
        Args:
            requirements_data: Output from _extract_requirements_hybrid
            
        Returns:
            Dictionary with formatted strings for template placeholders
        """
        formatted = {}
        
        # Format functional requirements
        func_reqs = requirements_data.get('functional_requirements', [])
        if func_reqs:
            func_list = []
            for req in func_reqs[:15]:  # Top 15
                req_id = req.get('id', 'FR-X')
                desc = req.get('description', 'TBD')
                priority = req.get('priority', 'shall')
                func_list.append(f"- **{req_id}**: {desc} [{priority.upper()}]")
            formatted['functional_requirements_list'] = '\n'.join(func_list)
            formatted['functional_req_count'] = str(len(func_reqs))
        else:
            formatted['functional_requirements_list'] = 'TBD - Define functional requirements'
            formatted['functional_req_count'] = 'TBD'
        
        # Format performance requirements
        perf_reqs = requirements_data.get('performance_requirements', [])
        if perf_reqs:
            perf_list = []
            for req in perf_reqs[:15]:  # Top 15
                req_id = req.get('id', 'PR-X')
                desc = req.get('description', 'TBD')
                metric = req.get('metric', '')
                threshold = req.get('threshold', '')
                
                req_text = f"- **{req_id}**: {desc}"
                if metric:
                    req_text += f" - Metric: {metric}"
                if threshold:
                    req_text += f" (Threshold: {threshold})"
                perf_list.append(req_text)
            formatted['performance_requirements_list'] = '\n'.join(perf_list)
            formatted['performance_req_count'] = str(len(perf_reqs))
        else:
            formatted['performance_requirements_list'] = 'TBD - Define performance requirements'
            formatted['performance_req_count'] = 'TBD'
        
        # Format KPPs as table
        kpps = requirements_data.get('key_performance_parameters', [])
        if kpps:
            kpp_table = "| KPP | Threshold | Objective |\n|-----|-----------|----------|\n"
            for kpp in kpps[:8]:  # Top 8
                name = kpp.get('name', 'TBD')
                threshold = kpp.get('threshold', 'TBD')
                objective = kpp.get('objective', 'TBD')
                kpp_table += f"| {name} | {threshold} | {objective} |\n"
            formatted['kpp_table'] = kpp_table
            formatted['kpp_count'] = str(len(kpps))
        else:
            formatted['kpp_table'] = '| KPP | Threshold | Objective |\n|-----|-----------|----------|\n| TBD | TBD | TBD |'
            formatted['kpp_count'] = 'TBD'
        
        # Format technical requirements
        tech_reqs = requirements_data.get('technical_requirements', [])
        if tech_reqs:
            tech_dict = {}
            for req in tech_reqs:
                category = req.get('category', 'General')
                if category not in tech_dict:
                    tech_dict[category] = []
                tech_dict[category].append(req.get('requirement', ''))
            
            tech_formatted = []
            for category, reqs in tech_dict.items():
                tech_formatted.append(f"**{category}:**")
                for req_text in reqs[:5]:  # Max 5 per category
                    tech_formatted.append(f"  - {req_text}")
            formatted['technical_requirements_list'] = '\n'.join(tech_formatted)
        else:
            formatted['technical_requirements_list'] = 'TBD - Define technical requirements'
        
        # Add metadata
        metadata = requirements_data.get('metadata', {})
        formatted['total_requirements'] = str(
            len(func_reqs) + len(perf_reqs) + len(kpps) + len(tech_reqs)
        )
        if metadata.get('user_count'):
            formatted['user_count'] = metadata['user_count']
        
        return formatted
    
    def _populate_template(
        self,
        project_info: Dict,
        requirements_analysis: Dict,
        strategy: Dict,
        risk_assessment: Dict,
        schedule: List[Dict],
        small_business: Dict,
        market_research: Dict,
        rag_strategies: List[Dict],
        rag_extracted: Dict,
        llm_generated: Dict,
        smart_defaults: Dict,
        config: Dict
    ) -> str:
        """Populate acquisition plan template with RAG-enhanced, LLM-generated, and smart default content"""
        content = self.template

        # Priority-based value selection helper
        def get_value(config_key=None, rag_key=None, generated_key=None, smart_default_key=None, default='TBD'):
            """
            Get value using priority: Config > RAG > Generated > Smart Default > TBD

            Args:
                config_key: Key to check in config dict
                rag_key: Key to check in rag_extracted dict
                generated_key: Key to check in llm_generated dict
                smart_default_key: Key to check in smart_defaults dict
                default: Default value if none found

            Returns:
                The highest priority value found
            """
            # Priority 1: Config (user-specified)
            if config_key and config.get(config_key):
                return config.get(config_key)

            # Priority 2: RAG extracted (from documents)
            if rag_key and rag_key in rag_extracted and rag_extracted[rag_key]:
                return str(rag_extracted[rag_key])

            # Priority 3: LLM generated (synthesized from RAG + context)
            if generated_key and generated_key in llm_generated and llm_generated[generated_key]:
                return str(llm_generated[generated_key])

            # Priority 4: Smart defaults (calculated/inferred)
            if smart_default_key and smart_default_key in smart_defaults and smart_defaults[smart_default_key]:
                return str(smart_defaults[smart_default_key])

            # Priority 5: Default (TBD or fallback)
            return default
        
        # Extract content from RAG strategies
        program_overview = config.get('program_overview', '')
        acquisition_strategy_summary = config.get('acquisition_strategy_summary', '')
        
        # If not in config, try to generate from RAG
        if not program_overview and rag_strategies:
            # Look for acquisition strategy type
            for rag_item in rag_strategies:
                if rag_item.get('type') == 'acquisition_strategy':
                    # Use LLM to extract program overview
                    prompt = f"""Extract a 2-3 sentence program overview from this acquisition strategy:
                    
                    {rag_item['content'][:600]}"""
                    try:
                        program_overview = self.call_llm(prompt, max_tokens=200).strip()
                        self.log("Generated program overview from RAG")
                    except Exception as e:
                        self.log(f"Failed to generate program overview: {e}", level="WARNING")
                    break
        
        if not acquisition_strategy_summary and rag_strategies:
            # Look for acquisition strategy
            for rag_item in rag_strategies:
                if rag_item.get('type') == 'acquisition_strategy':
                    # Use LLM to extract strategy summary
                    prompt = f"""Summarize the acquisition strategy in 2-3 sentences (contract type, vehicle, source selection):
                    
                    {rag_item['content'][:600]}"""
                    try:
                        acquisition_strategy_summary = self.call_llm(prompt, max_tokens=200).strip()
                        self.log("Generated acquisition strategy summary from RAG")
                    except Exception as e:
                        self.log(f"Failed to generate strategy summary: {e}", level="WARNING")
                    break
        
        # Basic information
        content = content.replace('{{program_name}}', project_info.get('program_name', 'TBD'))
        content = content.replace('{{organization}}', project_info.get('organization', 'Department of Defense'))
        content = content.replace('{{prepared_by}}', config.get('prepared_by', 'Program Manager'))
        content = content.replace('{{date}}', datetime.now().strftime('%B %d, %Y'))
        content = content.replace('{{classification}}', config.get('classification', 'UNCLASSIFIED'))
        
        # Use RAG-derived or config content for executive summary
        content = content.replace('{{program_overview}}', program_overview or 'TBD')
        content = content.replace('{{acquisition_strategy_summary}}', acquisition_strategy_summary or 'TBD')
        
        # Requirements from RAG analysis
        content = content.replace('{{capability_gap}}', requirements_analysis.get('capability_gap', 'TBD'))
        content = content.replace('{{mission_need}}', config.get('mission_need', requirements_analysis.get('capability_gap', 'TBD')))
        
        # Executive summary - use RAG extracted costs if available
        total_cost = get_value(
            config_key='total_cost',
            rag_key='development_cost',
            default=project_info.get('estimated_value', project_info.get('igce_total_cost', 'TBD'))
        )
        content = content.replace('{{total_cost}}', total_cost)
        content = content.replace('{{grand_total}}', total_cost)

        # Additional cost fields from RAG
        lifecycle_cost = get_value(rag_key='lifecycle_cost', default='TBD')
        content = content.replace('{{lifecycle_cost}}', lifecycle_cost)
        content = content.replace('{{development_cost}}', get_value(rag_key='development_cost', default='TBD'))

        # NEW: IGCE Summary - use cross-referenced IGCE if available
        igce_summary = project_info.get('igce_summary', 'TBD - IGCE not yet generated')
        content = content.replace('{{igce_summary}}', igce_summary)

        # IOC/FOC dates from RAG
        ioc_date = get_value(config_key='ioc_date', rag_key='ioc_date', default='TBD')
        foc_date = get_value(config_key='foc_date', rag_key='foc_date', default='TBD')
        content = content.replace('{{ioc_date}}', ioc_date)
        content = content.replace('{{foc_date}}', foc_date)
        content = content.replace('{{ioc}}', ioc_date)
        content = content.replace('{{foc}}', foc_date)

        # Milestones table
        milestones_table = '\n'.join([
            f"| {m['event']} | {m['date'].strftime('%B %Y')} |"
            for m in schedule
        ])
        content = content.replace('{{key_milestones_table}}', milestones_table)
        content = content.replace('{{master_schedule_table}}', '\n'.join([
            f"| {m['event']} | {m['date'].strftime('%B %d, %Y')} | | {m['status']} |"
            for m in schedule
        ]))

        # Strategy - use RAG extracted data with priority
        contract_type_value = get_value(
            config_key='contract_type',
            rag_key='contract_type',
            default=strategy['contract_type_recommendation']
        )
        content = content.replace('{{contract_type}}', contract_type_value)
        content = content.replace('{{contract_type_rationale}}', strategy['rationale'])
        content = content.replace('{{contract_vehicle}}', strategy['contract_vehicle'])

        # Source selection method from RAG
        source_selection_value = get_value(
            config_key='source_selection_method',
            rag_key='evaluation_method',
            default=strategy['source_selection_method']
        )
        content = content.replace('{{source_selection_method}}', source_selection_value)
        content = content.replace('{{evaluation_method}}', source_selection_value)
        content = content.replace('{{source_selection_rationale}}', strategy['rationale'])

        # Acquisition approach from RAG
        acquisition_approach = get_value(
            config_key='acquisition_approach',
            rag_key='acquisition_approach',
            default='TBD'
        )
        content = content.replace('{{acquisition_approach}}', acquisition_approach)

        # ========== LLM-Generated Content (Phase 1) ==========

        # Section 1: Background
        content = content.replace('{{current_situation}}',
            get_value(config_key='current_situation', generated_key='current_situation', default='TBD'))
        content = content.replace('{{strategic_alignment}}',
            get_value(config_key='strategic_alignment', generated_key='strategic_alignment', default='TBD'))
        content = content.replace('{{program_history}}',
            get_value(config_key='program_history', generated_key='program_history', default='TBD'))

        # Section 2: Applicable Conditions
        content = content.replace('{{acat_level}}',
            get_value(config_key='acat_level', generated_key='acat_level', default='TBD'))
        content = content.replace('{{acat_rationale}}',
            get_value(config_key='acat_rationale', generated_key='acat_rationale', default='TBD'))
        content = content.replace('{{applicable_regulations}}',
            get_value(config_key='applicable_regulations', generated_key='applicable_regulations', default='TBD'))
        content = content.replace('{{acquisition_pathway}}',
            get_value(config_key='acquisition_pathway', generated_key='acquisition_pathway', default='TBD'))

        # Section 6: Trade-offs
        content = content.replace('{{cost_performance_tradeoffs}}',
            get_value(config_key='cost_performance_tradeoffs', generated_key='cost_performance_tradeoffs', default='TBD'))
        content = content.replace('{{schedule_performance_tradeoffs}}',
            get_value(config_key='schedule_performance_tradeoffs', generated_key='schedule_performance_tradeoffs', default='TBD'))
        content = content.replace('{{risk_tradeoffs}}',
            get_value(config_key='risk_tradeoffs', generated_key='risk_tradeoffs', default='TBD'))

        # Section 7: Streamlining
        content = content.replace('{{streamlining_opportunities}}',
            get_value(config_key='streamlining_opportunities', generated_key='streamlining_opportunities', default='TBD'))
        content = content.replace('{{commercial_item_determination}}',
            get_value(config_key='commercial_item_determination', generated_key='commercial_item_determination', default='TBD'))

        # Section 10: Acquisition Considerations
        content = content.replace('{{budgeting_funding}}',
            get_value(config_key='budgeting_funding', generated_key='budgeting_funding', default='TBD'))
        content = content.replace('{{competition_requirements}}',
            get_value(config_key='competition_requirements', generated_key='competition_requirements', default='TBD'))
        content = content.replace('{{security_requirements}}',
            get_value(config_key='security_requirements', generated_key='security_requirements', default='TBD'))

        # Section 11: Market Research
        content = content.replace('{{market_research_summary}}',
            get_value(config_key='market_research_summary', generated_key='market_research_summary', default='TBD'))
        content = content.replace('{{industry_capabilities}}',
            get_value(config_key='industry_capabilities', generated_key='industry_capabilities', default='TBD'))
        content = content.replace('{{competitive_landscape}}',
            get_value(config_key='competitive_landscape', generated_key='competitive_landscape', default='TBD'))

        # Section 17: Life Cycle Sustainment
        content = content.replace('{{sustainment_strategy}}',
            get_value(config_key='sustainment_strategy', generated_key='sustainment_strategy', default='TBD'))
        content = content.replace('{{maintenance_approach}}',
            get_value(config_key='maintenance_approach', generated_key='maintenance_approach', default='TBD'))
        content = content.replace('{{training_requirements}}',
            get_value(config_key='training_requirements', generated_key='training_requirements', default='TBD'))

        # Section 18: Test & Evaluation
        content = content.replace('{{te_strategy}}',
            get_value(config_key='te_strategy', generated_key='te_strategy', default='TBD'))
        content = content.replace('{{dte_approach}}',
            get_value(config_key='dte_approach', generated_key='dte_approach', default='TBD'))
        content = content.replace('{{acceptance_criteria}}',
            get_value(config_key='acceptance_criteria', generated_key='acceptance_criteria', default='TBD'))

        # ========== Smart Defaults (Phase 2) ==========

        # Personnel
        content = content.replace('{{pm_name}}', get_value(smart_default_key='pm_name', default='TBD'))
        content = content.replace('{{co_name}}', get_value(smart_default_key='co_name', default='TBD'))
        content = content.replace('{{cor_name}}', get_value(smart_default_key='cor_name', default='TBD'))
        content = content.replace('{{legal_name}}', get_value(smart_default_key='legal_name', default='TBD'))
        content = content.replace('{{sbs_name}}', get_value(smart_default_key='sbs_name', default='TBD'))
        content = content.replace('{{cost_analyst_name}}', get_value(smart_default_key='cost_analyst_name', default='TBD'))

        # Organizations
        content = content.replace('{{pm_org}}', get_value(smart_default_key='pm_org', default='TBD'))
        content = content.replace('{{co_org}}', get_value(smart_default_key='co_org', default='TBD'))
        content = content.replace('{{cor_org}}', get_value(smart_default_key='cor_org', default='TBD'))
        content = content.replace('{{legal_org}}', get_value(smart_default_key='legal_org', default='TBD'))
        content = content.replace('{{sbs_org}}', get_value(smart_default_key='sbs_org', default='TBD'))
        content = content.replace('{{cost_analyst_org}}', get_value(smart_default_key='cost_analyst_org', default='TBD'))

        # Contacts & Titles
        content = content.replace('{{pm_contact}}', get_value(smart_default_key='pm_contact', default='TBD'))
        content = content.replace('{{co_contact}}', get_value(smart_default_key='co_contact', default='TBD'))
        content = content.replace('{{pm_title}}', get_value(smart_default_key='pm_title', default='TBD'))
        content = content.replace('{{co_title}}', get_value(smart_default_key='co_title', default='TBD'))
        content = content.replace('{{legal_title}}', get_value(smart_default_key='legal_title', default='TBD'))
        content = content.replace('{{sbs_title}}', get_value(smart_default_key='sbs_title', default='TBD'))

        # Dates
        content = content.replace('{{co_date}}', get_value(smart_default_key='co_date', default='TBD'))
        content = content.replace('{{pm_date}}', get_value(smart_default_key='pm_date', default='TBD'))
        content = content.replace('{{legal_date}}', get_value(smart_default_key='legal_date', default='TBD'))
        content = content.replace('{{sbs_date}}', get_value(smart_default_key='sbs_date', default='TBD'))

        # Fiscal Years
        content = content.replace('{{fy_base}}', get_value(smart_default_key='fy_base', default='TBD'))
        content = content.replace('{{fy_opt1}}', get_value(smart_default_key='fy_opt1', default='TBD'))
        content = content.replace('{{fy_opt2}}', get_value(smart_default_key='fy_opt2', default='TBD'))
        content = content.replace('{{fy_opt3}}', get_value(smart_default_key='fy_opt3', default='TBD'))
        content = content.replace('{{fy_opt4}}', get_value(smart_default_key='fy_opt4', default='TBD'))

        # Cost Breakdown
        content = content.replace('{{dev_base}}', get_value(smart_default_key='dev_base', default='TBD'))
        content = content.replace('{{dev_opt1}}', get_value(smart_default_key='dev_opt1', default='TBD'))
        content = content.replace('{{dev_opt2}}', get_value(smart_default_key='dev_opt2', default='TBD'))
        content = content.replace('{{dev_opt3}}', get_value(smart_default_key='dev_opt3', default='TBD'))
        content = content.replace('{{dev_opt4}}', get_value(smart_default_key='dev_opt4', default='TBD'))
        content = content.replace('{{dev_total}}', get_value(smart_default_key='dev_total', default='TBD'))

        content = content.replace('{{prod_base}}', get_value(smart_default_key='prod_base', default='TBD'))
        content = content.replace('{{prod_opt1}}', get_value(smart_default_key='prod_opt1', default='TBD'))
        content = content.replace('{{prod_opt2}}', get_value(smart_default_key='prod_opt2', default='TBD'))
        content = content.replace('{{prod_opt3}}', get_value(smart_default_key='prod_opt3', default='TBD'))
        content = content.replace('{{prod_opt4}}', get_value(smart_default_key='prod_opt4', default='TBD'))
        content = content.replace('{{prod_total}}', get_value(smart_default_key='prod_total', default='TBD'))

        content = content.replace('{{om_base}}', get_value(smart_default_key='om_base', default='TBD'))
        content = content.replace('{{om_opt1}}', get_value(smart_default_key='om_opt1', default='TBD'))
        content = content.replace('{{om_opt2}}', get_value(smart_default_key='om_opt2', default='TBD'))
        content = content.replace('{{om_opt3}}', get_value(smart_default_key='om_opt3', default='TBD'))
        content = content.replace('{{om_opt4}}', get_value(smart_default_key='om_opt4', default='TBD'))
        content = content.replace('{{om_total}}', get_value(smart_default_key='om_total', default='TBD'))

        content = content.replace('{{total_base}}', get_value(smart_default_key='total_base', default='TBD'))
        content = content.replace('{{total_opt1}}', get_value(smart_default_key='total_opt1', default='TBD'))
        content = content.replace('{{total_opt2}}', get_value(smart_default_key='total_opt2', default='TBD'))
        content = content.replace('{{total_opt3}}', get_value(smart_default_key='total_opt3', default='TBD'))
        content = content.replace('{{total_opt4}}', get_value(smart_default_key='total_opt4', default='TBD'))

        # Contract Structure
        content = content.replace('{{contract_structure}}', get_value(smart_default_key='contract_structure', default='TBD'))
        content = content.replace('{{option_periods}}', get_value(smart_default_key='option_periods', default='TBD'))
        content = content.replace('{{clin_structure}}', get_value(smart_default_key='clin_structure', default='TBD'))
        content = content.replace('{{incentive_structure}}', get_value(smart_default_key='incentive_structure', default='TBD'))

        # Requirements
        content = content.replace('{{requirements_documents}}', get_value(smart_default_key='requirements_documents', default='TBD'))

        # Other
        content = content.replace('{{mda_info}}', get_value(smart_default_key='mda_info', default='TBD'))
        content = content.replace('{{special_designations}}', get_value(smart_default_key='special_designations', default='TBD'))
        content = content.replace('{{version}}', get_value(smart_default_key='version', default='TBD'))
        content = content.replace('{{last_updated}}', get_value(smart_default_key='last_updated', default='TBD'))
        content = content.replace('{{distribution}}', get_value(smart_default_key='distribution', default='TBD'))

        # Additional smart defaults from Phase 3
        content = content.replace('{{phase_in_out_plan}}', get_value(smart_default_key='phase_in_out_plan', default='TBD'))
        content = content.replace('{{performance_milestones}}', get_value(smart_default_key='performance_milestones', default='TBD'))
        content = content.replace('{{evaluation_factors}}', get_value(smart_default_key='evaluation_factors', default='TBD'))
        content = content.replace('{{evaluation_weights}}', get_value(smart_default_key='evaluation_weights', default='TBD'))
        content = content.replace('{{overall_strategy}}', get_value(smart_default_key='overall_strategy', default='TBD'))
        content = content.replace('{{acquisition_phases}}', get_value(smart_default_key='acquisition_phases', default='TBD'))
        content = content.replace('{{alternative_vehicles}}', get_value(smart_default_key='alternative_vehicles', default='TBD'))
        content = content.replace('{{logistics_support}}', get_value(smart_default_key='logistics_support', default='TBD'))
        content = content.replace('{{ote_approach}}', get_value(smart_default_key='ote_approach', default='TBD'))
        content = content.replace('{{small_business_goal}}', get_value(smart_default_key='small_business_goal', default='TBD'))

        # Risk register
        risk_table = '\n'.join([
            f"| {r['id']} | {r['description']} | {r['probability']} | {r['impact']} | {r['mitigation']} | {r['owner']} |"
            for r in risk_assessment['risks']
        ])
        content = content.replace('{{risk_register_table}}', risk_table)
        
        # Small business
        content = content.replace('{{set_aside_type}}', small_business['set_aside_type'])
        content = content.replace('{{set_aside_rationale}}', small_business['set_aside_rationale'])
        content = content.replace('{{naics_code}}', small_business['naics_code'])
        content = content.replace('{{size_standard}}', small_business['size_standard'])
        
        # Period of performance
        content = content.replace('{{period_of_performance}}', project_info.get('period_of_performance', '12 months base + 4 option years'))
        
        # POC information
        content = content.replace('{{pm_name}}', config.get('pm_name', 'TBD'))
        content = content.replace('{{co_name}}', config.get('co_name', project_info.get('contracting_officer', 'TBD')))
        
        # ========== HYBRID REQUIREMENTS EXTRACTION (Phase 2 Enhancement) ==========
        # Extract and format requirements using hybrid method if retriever is available
        if self.retriever:
            try:
                print("  → Extracting requirements with hybrid method...")
                
                # Query RAG for requirements data
                req_query = f"{project_info.get('program_name', '')} functional requirements performance requirements KPP capabilities"
                req_results = self.retriever.retrieve(req_query, k=5)
                
                if req_results:
                    # Use hybrid extraction
                    hybrid_req_data = self._extract_requirements_hybrid(req_results)
                    
                    # Format for template
                    formatted_reqs = self._format_requirements_for_template(hybrid_req_data)
                    
                    # Replace template placeholders with formatted requirements
                    content = content.replace('{{functional_requirements}}', formatted_reqs.get('functional_requirements_list', 'TBD'))
                    content = content.replace('{{functional_requirements_list}}', formatted_reqs.get('functional_requirements_list', 'TBD'))
                    content = content.replace('{{functional_req_count}}', formatted_reqs.get('functional_req_count', 'TBD'))
                    
                    content = content.replace('{{performance_requirements}}', formatted_reqs.get('performance_requirements_list', 'TBD'))
                    content = content.replace('{{performance_requirements_list}}', formatted_reqs.get('performance_requirements_list', 'TBD'))
                    content = content.replace('{{performance_req_count}}', formatted_reqs.get('performance_req_count', 'TBD'))
                    
                    content = content.replace('{{kpp_table}}', formatted_reqs.get('kpp_table', 'TBD'))
                    content = content.replace('{{kpp_count}}', formatted_reqs.get('kpp_count', 'TBD'))
                    
                    content = content.replace('{{technical_requirements}}', formatted_reqs.get('technical_requirements_list', 'TBD'))
                    content = content.replace('{{technical_requirements_list}}', formatted_reqs.get('technical_requirements_list', 'TBD'))
                    
                    content = content.replace('{{total_requirements}}', formatted_reqs.get('total_requirements', 'TBD'))
                    content = content.replace('{{user_count}}', formatted_reqs.get('user_count', 'TBD'))
                    
                    # Log what we extracted
                    extracted_count = int(formatted_reqs.get('total_requirements', '0')) if formatted_reqs.get('total_requirements', 'TBD') != 'TBD' else 0
                    if extracted_count > 0:
                        self.log(f"Hybrid extraction: Populated template with {extracted_count} requirements")
                        print(f"    ✓ Populated {extracted_count} requirements from RAG (functional, performance, KPPs, technical)")
                    
            except Exception as e:
                self.log(f"Hybrid requirements extraction failed: {e}", level="WARNING")
                print(f"    ⚠ Hybrid extraction failed, using defaults")
        
        # Fill remaining placeholders
        content = re.sub(r'\{\{[^}]+\}\}', 'TBD', content)
        
        return content
    
    def save_to_file(self, content: str, output_path: str, convert_to_pdf: bool = True) -> Dict:
        """Save Acquisition Plan to file"""
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

