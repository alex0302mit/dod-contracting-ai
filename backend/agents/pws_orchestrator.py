"""
PWS Orchestrator: Coordinates Performance Work Statement generation workflow
Enhanced with ResearchAgent for current market intelligence and performance benchmarks
"""

from typing import Dict, List, Optional
from .pws_writer_agent import PWSWriterAgent
from .quality_agent import QualityAgent
from .research_agent import ResearchAgent
from .refinement_agent import RefinementAgent
from .qasp_generator_agent import QASPGeneratorAgent
from .section_l_generator_agent import SectionLGeneratorAgent
from .section_m_generator_agent import SectionMGeneratorAgent
from backend.rag.retriever import Retriever
from backend.utils.evaluation_report_generator import EvaluationReportGenerator
import time


class PWSOrchestrator:
    """
    PWS Orchestrator: Coordinates Performance Work Statement generation
    
    Workflow:
    1. Research Phase: Gather performance benchmarks and best practices
    2. Writing Phase: Generate each PWS section with performance focus
    3. Quality Phase: Evaluate performance-based elements and measurability
    4. Revision Phase: Improve sections if needed (iterative refinement)
    5. Assembly Phase: Compile final PWS document
    6. QASP Generation Phase: Automatically generate Quality Assurance Surveillance Plan
    7. Section L Generation Phase: Generate Instructions to Offerors (optional)
    8. Section M Generation Phase: Generate Evaluation Factors for Award (optional)

    Dependencies:
    - ResearchAgent: Market intelligence + performance benchmarks
    - PWSWriterAgent: PWS content generation (performance-based)
    - QualityAgent: Quality evaluation with DoD citation standards
    - RefinementAgent: Iterative improvement
    - QASPGeneratorAgent: QASP generation from PWS
    - SectionLGeneratorAgent: Section L generation (NEW)
    - SectionMGeneratorAgent: Section M generation (NEW)
    - RAG system: PWS guide knowledge base
    """
    
    def __init__(
        self,
        api_key: str,
        retriever: Retriever,
        tavily_api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize PWS orchestrator with research capabilities
        
        Args:
            api_key: Anthropic API key
            retriever: RAG Retriever with PWS guide indexed
            tavily_api_key: Tavily API key for web search (optional)
            model: Claude model to use
        """
        # Initialize agents
        self.research_agent = ResearchAgent(api_key, retriever, tavily_api_key, model)
        self.pws_writer = PWSWriterAgent(api_key, retriever, model)
        self.quality_agent = QualityAgent(api_key, model)
        self.refinement_agent = RefinementAgent(api_key, model)
        self.qasp_generator = QASPGeneratorAgent()  # QASP generation
        self.section_l_generator = SectionLGeneratorAgent(api_key, model)  # NEW: Section L
        self.section_m_generator = SectionMGeneratorAgent(api_key, model)  # NEW: Section M
        
        # Workflow state
        self.workflow_state = {
            'phase': 'initialized',
            'research_results': {},
            'written_sections': {},
            'evaluation_results': {},
            'refinement_history': {},
            'final_pws': None
        }
        
        # Configuration
        self.quality_threshold = 90
        self.enable_auto_revision = True
        self.max_refinement_iterations = 10
        self.min_score_improvement = 5
        
        print("\n" + "="*70)
        print("PWS ORCHESTRATOR INITIALIZED")
        print("="*70)
        print(f"  ✓ Research Agent ready")
        if self.research_agent.web_search_enabled:
            print(f"    └─ Web search enabled (performance benchmarks)")
        else:
            print(f"    └─ Web search disabled (RAG only)")
        print(f"  ✓ PWS Writer Agent ready")
        print(f"  ✓ Quality Agent ready (DoD citations)")
        print(f"  ✓ Refinement Agent ready (iterative improvement)")
        print(f"  ✓ QASP Generator Agent ready (automatic QASP generation)")
        print(f"  ✓ Section L Generator Agent ready (instructions to offerors)")
        print(f"  ✓ Section M Generator Agent ready (evaluation factors)")
        print(f"  Quality threshold: {self.quality_threshold}/100")
        print(f"  Max refinement iterations: {self.max_refinement_iterations}")
        print("="*70 + "\n")
    
    def execute_pws_workflow(
        self,
        project_info: Dict,
        pws_sections_config: List[Dict],
        output_path: str = "outputs/pws/performance_work_statement.md",
        generate_qasp: bool = True,
        qasp_config: Optional[Dict] = None,
        generate_section_l: bool = False,
        section_l_config: Optional[Dict] = None,
        generate_section_m: bool = False,
        section_m_config: Optional[Dict] = None
    ) -> Dict:
        """
        Execute complete PWS generation workflow

        Args:
            project_info: Project information
            pws_sections_config: List of PWS section configurations
            output_path: Path to save PWS
            generate_qasp: Whether to automatically generate QASP (default: True)
            qasp_config: Optional QASP configuration (COR info, KO details)
            generate_section_l: Whether to generate Section L (default: False)
            section_l_config: Optional Section L configuration
            generate_section_m: Whether to generate Section M (default: False)
            section_m_config: Optional Section M configuration

        Returns:
            Dictionary with workflow results including QASP, Section L, Section M if generated
        """
        start_time = time.time()
        
        print("\n" + "="*70)
        print("STARTING PWS GENERATION WORKFLOW")
        print("="*70)
        print(f"Project: {project_info.get('program_name', 'Unknown')}")
        print(f"PWS Sections: {len(pws_sections_config)}")
        print("="*70 + "\n")
        
        # Phase 1: Research (gather performance benchmarks)
        research_results = self._phase_research(pws_sections_config, project_info)
        self.workflow_state['research_results'] = research_results
        
        # Phase 2: Writing (performance-based requirements)
        written_sections = self._phase_writing(pws_sections_config, project_info, research_results)
        self.workflow_state['written_sections'] = written_sections
        
        # Phase 3: Quality Check (with DoD citations)
        evaluation_results = self._phase_quality(written_sections, project_info)
        self.workflow_state['evaluation_results'] = evaluation_results
        
        # Phase 4: Revision (iterative improvement)
        if self.enable_auto_revision:
            written_sections = self._phase_revision(
                written_sections,
                evaluation_results,
                pws_sections_config,
                project_info
            )
        
        # Phase 5: Assembly
        final_pws = self._phase_assembly(written_sections, project_info, evaluation_results)
        self.workflow_state['final_pws'] = final_pws
        
        # Save
        self._save_pws(final_pws, output_path)
        
        # Save evaluation report
        self._save_evaluation_report(evaluation_results, project_info, output_path)

        # Phase 6: QASP Generation
        qasp_result = None
        if generate_qasp:
            qasp_result = self._phase_qasp_generation(output_path, project_info, qasp_config)
            self.workflow_state['qasp_result'] = qasp_result

        # Phase 7: Section L Generation (NEW)
        section_l_result = None
        if generate_section_l:
            # Read PWS content for analysis
            with open(output_path, 'r') as f:
                pws_content = f.read()
            section_l_result = self._phase_section_l_generation(
                project_info,
                pws_content,
                output_path,
                section_l_config
            )
            self.workflow_state['section_l_result'] = section_l_result

        # Phase 8: Section M Generation (NEW)
        section_m_result = None
        if generate_section_m:
            # Read PWS content for analysis
            with open(output_path, 'r') as f:
                pws_content = f.read()
            section_m_result = self._phase_section_m_generation(
                project_info,
                pws_content,
                output_path,
                section_m_config
            )
            self.workflow_state['section_m_result'] = section_m_result

        elapsed_time = time.time() - start_time

        print("\n" + "="*70)
        print("✅ PWS GENERATION COMPLETE")
        print("="*70)
        print(f"Time elapsed: {elapsed_time:.1f}s")
        print(f"Output: {output_path}")
        if qasp_result and qasp_result.get('success'):
            print(f"QASP: {qasp_result['output_path']}")
        if section_l_result and section_l_result.get('status') == 'success':
            print(f"Section L: {section_l_result['output_path']}")
        if section_m_result and section_m_result.get('status') == 'success':
            print(f"Section M: {section_m_result['output_path']}")
        print("="*70 + "\n")

        return {
            'success': True,
            'output_path': output_path,
            'elapsed_time': elapsed_time,
            'workflow_state': self.workflow_state,
            'qasp_result': qasp_result,
            'section_l_result': section_l_result,
            'section_m_result': section_m_result
        }
    
    def _phase_research(self, sections_config: List[Dict], project_info: Dict) -> Dict:
        """Phase 1: Research performance benchmarks and best practices"""
        
        print("\n" + "="*70)
        print("PHASE 1: RESEARCH & INTELLIGENCE GATHERING")
        print("="*70 + "\n")
        
        research_results = {}
        
        for section_config in sections_config:
            section_name = section_config['name']
            focus = section_config.get('focus', 'general')
            
            print(f"Researching: {section_name}")
            
            # Build research query focusing on performance metrics
            query = f"{section_name} performance metrics benchmarks standards {focus}"
            
            task = {
                'query': query,
                'section_name': section_name,
                'project_info': project_info,
                'use_web_search': True,  # Get current benchmarks
                'search_focus': 'performance metrics and standards'
            }
            
            result = self.research_agent.execute(task)
            research_results[section_name] = result
            
            print(f"  ✓ Found {len(result.get('rag_results', []))} RAG sources")
            if result.get('web_results'):
                print(f"  ✓ Found {len(result.get('web_results', []))} web sources")
            print()
        
        print("="*70)
        print(f"RESEARCH COMPLETE: {len(research_results)} sections researched")
        print("="*70 + "\n")
        
        return research_results
    
    def _phase_writing(
        self,
        sections_config: List[Dict],
        project_info: Dict,
        research_results: Dict
    ) -> Dict:
        """Phase 2: Write PWS sections with performance focus"""
        
        print("\n" + "="*70)
        print("PHASE 2: PWS WRITING (Performance-Based)")
        print("="*70 + "\n")
        
        written_sections = {}
        
        for section_config in sections_config:
            section_name = section_config['name']
            guidance = section_config.get('guidance', '')
            focus = section_config.get('focus', 'general')
            
            print(f"Writing: {section_name}")
            
            # Include research findings in guidance
            research_data = research_results.get(section_name, {})
            enhanced_guidance = f"{guidance}\n\nResearch Findings:\n{self._format_research_summary(research_data)}"
            
            task = {
                'section_name': section_name,
                'project_info': project_info,
                'guidance': enhanced_guidance,
                'focus': focus
            }
            
            result = self.pws_writer.execute(task)
            written_sections[section_name] = result['content']
            
            print(f"  ✓ Generated {result['word_count']} words")
            print(f"  ✓ Performance metrics: {len(result['performance_metrics'])}")
            print(f"  ✓ QASP elements: {len(result['qasp_elements'])}")
            print(f"  ✓ PBSC compliance: {result['pbsc_compliance']}/100")
            print()
        
        print("="*70)
        print(f"WRITING COMPLETE: {len(written_sections)} sections written")
        print("="*70 + "\n")
        
        return written_sections
    
    def _phase_quality(self, written_sections: Dict, project_info: Dict) -> Dict:
        """Phase 3: Quality evaluation with DoD citation standards"""
        
        print("\n" + "="*70)
        print("PHASE 3: QUALITY EVALUATION")
        print("="*70 + "\n")
        
        evaluation_results = {}
        
        for section_name, content in written_sections.items():
            print(f"Evaluating: {section_name}")
            
            task = {
                'content': content,
                'section_name': section_name,
                'project_info': project_info,
                'research_findings': {},
                'evaluation_type': 'section'
            }
            
            result = self.quality_agent.execute(task)
            evaluation_results[section_name] = result
            
            score = result['score']
            grade = result['grade']
            risk = result['hallucination_risk']
            
            # Check DoD citation compliance
            citation_check = result['detailed_checks']['citations']
            dod_compliant = citation_check.get('dod_compliant', False)
            
            score_symbol = "✓" if score >= self.quality_threshold else "⚠️"
            citation_symbol = "✓" if dod_compliant else "⚠️"
            
            print(f"  {score_symbol} Score: {score}/100 ({grade})")
            print(f"  Hallucination risk: {risk}")
            print(f"  {citation_symbol} DoD Citations: {citation_check['citations_found']} valid, {citation_check['invalid_citations']} invalid")
            
            if result['issues']:
                print(f"  Issues: {len(result['issues'])}")
                for issue in result['issues'][:2]:
                    print(f"    - {issue[:80]}...")
            print()
        
        # Calculate overall score
        scores = [r['score'] for r in evaluation_results.values()]
        overall_score = sum(scores) / len(scores) if scores else 0
        
        print("="*70)
        print(f"QUALITY EVALUATION COMPLETE: Overall Score {overall_score:.1f}/100")
        print("="*70 + "\n")
        
        return evaluation_results
    
    def _phase_revision(
        self,
        written_sections: Dict,
        evaluation_results: Dict,
        sections_config: List[Dict],
        project_info: Dict
    ) -> Dict:
        """Phase 4: Iterative refinement"""
        
        print("\n" + "="*70)
        print("PHASE 4: ITERATIVE REFINEMENT")
        print("="*70 + "\n")
        
        sections_needing_revision = []
        
        for section_name, evaluation in evaluation_results.items():
            if evaluation['score'] < self.quality_threshold:
                sections_needing_revision.append(section_name)
        
        if not sections_needing_revision:
            print("✓ All sections meet quality threshold - no revision needed")
            print("="*70 + "\n")
            return written_sections
        
        print(f"Sections needing revision: {len(sections_needing_revision)}")
        for section in sections_needing_revision:
            score = evaluation_results[section]['score']
            print(f"  - {section}: {score}/100")
        print()
        
        # Refine each section
        for section_name in sections_needing_revision:
            written_sections[section_name] = self._refine_section_iteratively(
                section_name,
                written_sections[section_name],
                evaluation_results[section_name],
                project_info
            )
        
        print("="*70)
        print("REFINEMENT COMPLETE")
        print("="*70 + "\n")
        
        return written_sections
    
    def _refine_section_iteratively(
        self,
        section_name: str,
        content: str,
        evaluation: Dict,
        project_info: Dict
    ) -> str:
        """Iteratively refine a section until quality threshold met"""
        
        print(f"\n{'─'*70}")
        print(f"Refining: {section_name}")
        print(f"{'─'*70}")
        
        current_content = content
        current_score = evaluation['score']
        iteration = 0
        
        refinement_history = []
        
        while current_score < self.quality_threshold and iteration < self.max_refinement_iterations:
            iteration += 1
            
            print(f"\n  Iteration {iteration}")
            print(f"  Current score: {current_score}/100")
            
            # Prepare refinement task
            task = {
                'content': current_content,
                'issues': evaluation['issues'],
                'suggestions': evaluation['suggestions'],
                'section_name': section_name,
                'project_info': project_info,
                'target_score': self.quality_threshold
            }
            
            # Refine
            refined_result = self.refinement_agent.execute(task)
            refined_content = refined_result['refined_content']
            
            # Re-evaluate
            eval_task = {
                'content': refined_content,
                'section_name': section_name,
                'project_info': project_info,
                'research_findings': {},
                'evaluation_type': 'section'
            }
            
            new_evaluation = self.quality_agent.execute(eval_task)
            new_score = new_evaluation['score']
            
            improvement = new_score - current_score
            
            print(f"  New score: {new_score}/100 (Δ {improvement:+.1f})")
            
            # Track history
            refinement_history.append({
                'iteration': iteration,
                'score': new_score,
                'improvement': improvement
            })
            
            # Check if improvement is sufficient
            if improvement < self.min_score_improvement and iteration > 2:
                print(f"  ⚠️  Minimal improvement - stopping refinement")
                break
            
            # Update for next iteration
            current_content = refined_content
            current_score = new_score
            evaluation = new_evaluation
            
            if current_score >= self.quality_threshold:
                print(f"  ✓ Quality threshold reached!")
                break
        
        # Store refinement history
        self.workflow_state['refinement_history'][section_name] = refinement_history
        
        print(f"\n  Final score: {current_score}/100 after {iteration} iteration(s)")
        print(f"{'─'*70}\n")
        
        return current_content
    
    def _phase_assembly(
        self,
        written_sections: Dict,
        project_info: Dict,
        evaluation_results: Dict
    ) -> str:
        """Phase 5: Assemble final PWS document"""
        
        print("\n" + "="*70)
        print("PHASE 5: DOCUMENT ASSEMBLY")
        print("="*70 + "\n")
        
        # Calculate overall quality score
        scores = [r['score'] for r in evaluation_results.values()]
        overall_score = sum(scores) / len(scores) if scores else 0
        overall_grade = self._score_to_grade(overall_score)
        
        # Build PWS document
        pws_parts = []
        
        # Header
        pws_parts.append(f"# Performance Work Statement (PWS)")
        pws_parts.append(f"## {project_info.get('program_name', 'Program Name')}")
        pws_parts.append("")
        pws_parts.append("**Document Information**")
        pws_parts.append(f"- **Organization**: {project_info.get('organization', 'N/A')}")
        pws_parts.append(f"- **Date**: {project_info.get('date', 'N/A')}")
        pws_parts.append(f"- **Author**: {project_info.get('author', 'N/A')}")
        pws_parts.append(f"- **Document Type**: Performance Work Statement (PWS)")
        pws_parts.append("")
        pws_parts.append("---")
        pws_parts.append("")

        # Sections (Quality scores removed - see evaluation report)
        for section_name, content in written_sections.items():
            pws_parts.append(f"## {section_name}")
            pws_parts.append("")
            pws_parts.append(content)
            pws_parts.append("")
            pws_parts.append("---")
            pws_parts.append("")
        
        pws_document = '\n'.join(pws_parts)
        
        print("✓ PWS document assembled")
        print(f"  Total sections: {len(written_sections)}")
        print(f"  Total words: {len(pws_document.split())}")
        print(f"  Overall quality: {overall_score:.1f}/100 ({overall_grade})")
        print()
        
        return pws_document
    
    def _save_pws(self, pws_content: str, output_path: str):
        """Save PWS document as markdown and PDF"""
        import os

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save markdown
        with open(output_path, 'w') as f:
            f.write(pws_content)

        print(f"✓ PWS saved to: {output_path}")

        # Convert to PDF
        pdf_path = output_path.replace('.md', '.pdf')
        try:
            from utils.convert_md_to_pdf import convert_markdown_to_pdf
            convert_markdown_to_pdf(output_path, pdf_path)
            print(f"✓ PDF saved to: {pdf_path}")
        except Exception as e:
            print(f"⚠️  Warning: Could not create PDF: {e}")
    
    def _save_evaluation_report(
        self,
        evaluation_results: Dict,
        project_info: Dict,
        pws_path: str
    ):
        """Save evaluation report as markdown and PDF"""

        report_path = pws_path.replace('.md', '_evaluation_report.md')

        generator = EvaluationReportGenerator(document_type="PWS")
        generator.generate_full_report(
            evaluation_results,
            project_info,
            report_path
        )

        print(f"✓ Evaluation report saved to: {report_path}")

        # Convert evaluation report to PDF
        pdf_report_path = report_path.replace('.md', '.pdf')
        try:
            from utils.convert_md_to_pdf import convert_markdown_to_pdf
            convert_markdown_to_pdf(report_path, pdf_report_path)
            print(f"✓ Evaluation PDF saved to: {pdf_report_path}")
        except Exception as e:
            print(f"⚠️  Warning: Could not create evaluation PDF: {e}")
    
    def _format_research_summary(self, research_data: Dict) -> str:
        """Format research findings summary"""
        if not research_data:
            return "No research data available."
        
        summary_parts = []
        
        # RAG results
        rag_results = research_data.get('rag_results', [])
        if rag_results:
            summary_parts.append(f"Knowledge Base: {len(rag_results)} relevant documents")
        
        # Web results
        web_results = research_data.get('web_results', [])
        if web_results:
            summary_parts.append(f"Web Research: {len(web_results)} current sources")
        
        return ', '.join(summary_parts) if summary_parts else "No specific research findings"
    
    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade"""
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

    def _phase_qasp_generation(
        self,
        pws_path: str,
        project_info: Dict,
        qasp_config: Optional[Dict] = None
    ) -> Dict:
        """
        Phase 6: Generate Quality Assurance Surveillance Plan from PWS

        Args:
            pws_path: Path to generated PWS markdown
            project_info: Project information
            qasp_config: Optional QASP configuration (COR, KO details)

        Returns:
            QASP generation results
        """
        print("\n" + "="*70)
        print("PHASE 6: QASP GENERATION")
        print("="*70 + "\n")

        # Determine QASP output path
        qasp_output_path = pws_path.replace('performance_work_statement.md', 'quality_assurance_surveillance_plan.md')
        qasp_output_path = qasp_output_path.replace('/pws/', '/qasp/')

        # Build QASP config with project info defaults
        if qasp_config is None:
            qasp_config = {}

        # Merge project info into QASP config
        qasp_config.setdefault('contracting_officer', project_info.get('author', 'TBD'))
        qasp_config.setdefault('cor_name', project_info.get('author', 'TBD'))
        qasp_config.setdefault('pws_reference', f"PWS dated {project_info.get('date', 'TBD')}")

        print(f"Generating QASP from PWS...")
        print(f"  PWS Source: {pws_path}")
        print(f"  QASP Output: {qasp_output_path}")

        try:
            # Generate QASP
            qasp_result = self.qasp_generator.execute(
                pws_path=pws_path,
                output_path=qasp_output_path,
                config=qasp_config,
                verbose=False  # Less verbose since we're in orchestrator
            )

            if qasp_result['success']:
                print(f"\n✓ QASP generated successfully")
                print(f"  Requirements: {qasp_result['requirements_count']}")
                print(f"  Deliverables: {qasp_result['deliverables_count']}")
                print(f"  QASP: {qasp_result['output_path']}")
                if qasp_result.get('pdf_path'):
                    print(f"  PDF: {qasp_result['pdf_path']}")
            else:
                print(f"\n⚠ QASP generation completed with warnings")

            print("\n" + "="*70)
            print("QASP GENERATION COMPLETE")
            print("="*70 + "\n")

            return qasp_result

        except Exception as e:
            print(f"\n✗ QASP generation failed: {e}")
            print("="*70 + "\n")
            return {
                'success': False,
                'error': str(e)
            }

    def _phase_section_l_generation(
        self,
        project_info: Dict,
        pws_content: str,
        pws_path: str,
        section_l_config: Optional[Dict] = None
    ) -> Dict:
        """
        Phase 7: Generate Section L (Instructions to Offerors)

        Args:
            project_info: Project information
            pws_content: PWS content for analysis
            pws_path: Path to PWS file
            section_l_config: Optional Section L configuration

        Returns:
            Section L generation results
        """
        print("\n" + "="*70)
        print("PHASE 7: SECTION L GENERATION (INSTRUCTIONS TO OFFERORS)")
        print("="*70 + "\n")

        # Determine Section L output path
        section_l_output_path = pws_path.replace('performance_work_statement.md', 'section_l_instructions_to_offerors.md')
        section_l_output_path = section_l_output_path.replace('/pws/', '/section_l/')

        if section_l_config is None:
            section_l_config = {}

        print(f"Generating Section L from PWS...")
        print(f"  PWS Source: {pws_path}")
        print(f"  Section L Output: {section_l_output_path}")

        try:
            # Generate Section L
            task = {
                'project_info': project_info,
                'pws_content': pws_content,
                'config': section_l_config
            }

            result = self.section_l_generator.execute(task)

            # Save to file
            files = self.section_l_generator.save_to_file(
                result['content'],
                section_l_output_path,
                convert_to_pdf=True
            )

            result['output_path'] = files['markdown']
            if 'pdf' in files:
                result['pdf_path'] = files['pdf']

            print(f"\n✓ Section L generated successfully")
            print(f"  Word count: {result['statistics']['word_count']}")
            print(f"  Markdown: {result['output_path']}")
            if 'pdf_path' in result:
                print(f"  PDF: {result['pdf_path']}")

            print("\n" + "="*70)
            print("SECTION L GENERATION COMPLETE")
            print("="*70 + "\n")

            return result

        except Exception as e:
            print(f"\n✗ Section L generation failed: {e}")
            print("="*70 + "\n")
            return {
                'status': 'failed',
                'error': str(e)
            }

    def _phase_section_m_generation(
        self,
        project_info: Dict,
        pws_content: str,
        pws_path: str,
        section_m_config: Optional[Dict] = None
    ) -> Dict:
        """
        Phase 8: Generate Section M (Evaluation Factors for Award)

        Args:
            project_info: Project information
            pws_content: PWS content for analysis
            pws_path: Path to PWS file
            section_m_config: Optional Section M configuration

        Returns:
            Section M generation results
        """
        print("\n" + "="*70)
        print("PHASE 8: SECTION M GENERATION (EVALUATION FACTORS)")
        print("="*70 + "\n")

        # Determine Section M output path
        section_m_output_path = pws_path.replace('performance_work_statement.md', 'section_m_evaluation_factors.md')
        section_m_output_path = section_m_output_path.replace('/pws/', '/section_m/')

        if section_m_config is None:
            section_m_config = {}

        print(f"Generating Section M from PWS...")
        print(f"  PWS Source: {pws_path}")
        print(f"  Section M Output: {section_m_output_path}")

        try:
            # Generate Section M
            task = {
                'project_info': project_info,
                'pws_content': pws_content,
                'config': section_m_config
            }

            result = self.section_m_generator.execute(task)

            # Save to file
            files = self.section_m_generator.save_to_file(
                result['content'],
                section_m_output_path,
                convert_to_pdf=True
            )

            result['output_path'] = files['markdown']
            if 'pdf' in files:
                result['pdf_path'] = files['pdf']

            print(f"\n✓ Section M generated successfully")
            print(f"  Evaluation Method: {result['methodology']['method']}")
            print(f"  Complexity Level: {result['complexity_analysis']['complexity_level']}")
            print(f"  Word count: {result['statistics']['word_count']}")
            print(f"  Markdown: {result['output_path']}")
            if 'pdf_path' in result:
                print(f"  PDF: {result['pdf_path']}")

            print("\n" + "="*70)
            print("SECTION M GENERATION COMPLETE")
            print("="*70 + "\n")

            return result

        except Exception as e:
            print(f"\n✗ Section M generation failed: {e}")
            print("="*70 + "\n")
            return {
                'status': 'failed',
                'error': str(e)
            }
