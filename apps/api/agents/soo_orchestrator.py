"""
SOO Orchestrator: Coordinates SOO generation workflow with web search
Enhanced with ResearchAgent for current market intelligence
"""

from typing import Dict, List, Optional
from .soo_writer_agent import SOOWriterAgent
from .quality_agent import QualityAgent
from .research_agent import ResearchAgent
from .refinement_agent import RefinementAgent
from backend.rag.retriever import Retriever
from backend.utils.evaluation_report_generator import EvaluationReportGenerator
import time


class SOOOrchestrator:
    """
    SOO Orchestrator: Coordinates Statement of Objectives generation

    Workflow:
    1. Research Phase: Gather current market data and regulatory info (NEW)
    2. Writing Phase: Generate each SOO section with research findings
    3. Quality Phase: Evaluate outcome-focus and measurability
    4. Revision Phase: Improve sections if needed
    5. Assembly Phase: Compile final SOO document

    Dependencies:
    - ResearchAgent: Current market data + regulatory info (RAG + Web)
    - SOOWriterAgent: SOO content generation
    - QualityAgent: Quality evaluation
    - RAG system: SOO guide knowledge base
    """

    def __init__(
        self,
        api_key: str,
        retriever: Retriever,
        tavily_api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize SOO orchestrator with web search support

        Args:
            api_key: Anthropic API key
            retriever: RAG Retriever with SOO guide indexed
            tavily_api_key: Tavily API key for web search (optional)
            model: Claude model to use
        """
        # Initialize agents
        self.research_agent = ResearchAgent(api_key, retriever, tavily_api_key, model)
        self.soo_writer = SOOWriterAgent(api_key, retriever, model)
        self.quality_agent = QualityAgent(api_key, model)
        self.refinement_agent = RefinementAgent(api_key, model)

        # Workflow state
        self.workflow_state = {
            'phase': 'initialized',
            'research_results': {},
            'written_sections': {},
            'evaluation_results': {},
            'refinement_history': {},  # Track refinement iterations
            'final_soo': None
        }

        # Configuration
        self.quality_threshold = 90
        self.enable_auto_revision = True
        self.max_refinement_iterations = 10  # Max iterations per section
        self.min_score_improvement = 5  # Minimum score improvement to continue

        print("\n" + "="*70)
        print("SOO ORCHESTRATOR INITIALIZED")
        print("="*70)
        print(f"  ✓ Research Agent ready")
        if self.research_agent.web_search_enabled:
            print(f"    └─ Web search enabled")
        else:
            print(f"    └─ Web search disabled (RAG only)")
        print(f"  ✓ SOO Writer Agent ready")
        print(f"  ✓ Quality Agent ready")
        print(f"  ✓ Refinement Agent ready (iterative improvement)")
        print(f"  Quality threshold: {self.quality_threshold}/100")
        print(f"  Max refinement iterations: {self.max_refinement_iterations}")
        print("="*70 + "\n")
    
    def execute_soo_workflow(
        self,
        project_info: Dict,
        soo_sections_config: List[Dict],
        output_path: str = "outputs/soo/statement_of_objectives.md"
    ) -> Dict:
        """
        Execute complete SOO generation workflow
        
        Args:
            project_info: Project information
            soo_sections_config: List of SOO section configurations
            output_path: Path to save SOO
            
        Returns:
            Dictionary with workflow results
        """
        start_time = time.time()
        
        print("\n" + "="*70)
        print("STARTING SOO GENERATION WORKFLOW")
        print("="*70)
        print(f"Project: {project_info.get('program_name', 'Unknown')}")
        print(f"SOO Sections: {len(soo_sections_config)}")
        print("="*70 + "\n")

        # Phase 1: Research (gather current market data)
        research_results = self._phase_research(soo_sections_config, project_info)
        self.workflow_state['research_results'] = research_results

        # Phase 2: Writing (using research findings)
        written_sections = self._phase_writing(soo_sections_config, project_info, research_results)
        self.workflow_state['written_sections'] = written_sections

        # Phase 3: Quality Check
        evaluation_results = self._phase_quality(written_sections, project_info)
        self.workflow_state['evaluation_results'] = evaluation_results

        # Phase 4: Revision (if needed)
        if self.enable_auto_revision:
            written_sections = self._phase_revision(
                written_sections,
                evaluation_results,
                soo_sections_config,
                project_info
            )

        # Phase 5: Assembly
        final_soo = self._phase_assembly(written_sections, project_info, evaluation_results)
        self.workflow_state['final_soo'] = final_soo

        # Save
        self._save_soo(final_soo, output_path)

        # Save evaluation report
        self._save_evaluation_report(evaluation_results, project_info, output_path)

        elapsed_time = time.time() - start_time
        
        print("\n" + "="*70)
        print("✅ SOO GENERATION COMPLETE")
        print("="*70)
        print(f"Time elapsed: {elapsed_time:.1f}s")
        print(f"Output: {output_path}")
        print("="*70 + "\n")
        
        return {
            'status': 'success',
            'output_path': output_path,
            'elapsed_time': elapsed_time,
            'workflow_state': self.workflow_state
        }

    def _phase_research(self, sections_config: List[Dict], project_info: Dict) -> Dict:
        """
        Research phase: Gather current market data and regulatory info

        Args:
            sections_config: List of section configurations
            project_info: Project information

        Returns:
            Dictionary of research results by section
        """
        print("\n" + "="*70)
        print("PHASE 1: RESEARCH & DATA GATHERING")
        print("="*70 + "\n")

        research_results = {}

        for i, section_config in enumerate(sections_config, 1):
            section_name = section_config['name']
            print(f"[{i}/{len(sections_config)}] Researching: {section_name}...")

            # Build research query based on section focus
            section_guidance = section_config.get('guidance', '')
            section_focus = section_config.get('focus', 'general')

            query = f"SOO {section_name}: {section_guidance[:200]}"

            # Determine search type based on section focus
            search_type = 'general'
            if 'performance' in section_name.lower() or section_focus == 'performance':
                search_type = 'general'  # Performance standards
            elif 'objective' in section_name.lower() or section_focus == 'outcomes':
                search_type = 'general'  # Desired outcomes

            research_task = {
                'query': query,
                'section': section_name,
                'context': project_info,
                'use_web_search': True,
                'search_type': search_type
            }

            result = self.research_agent.execute(research_task)
            research_results[section_name] = result

            # Show what was found
            confidence = result.get('confidence', 'unknown')
            sources_count = len(result.get('sources', []))
            web_count = len(result.get('web_results', []))

            print(f"  ✓ Found {sources_count} internal docs, {web_count} web sources")
            print(f"  Confidence: {confidence}")
            print()

        print(f"✅ Research phase complete: {len(research_results)} sections researched\n")
        return research_results

    def _phase_writing(self, sections_config: List[Dict], project_info: Dict, research_results: Dict = None) -> Dict:
        """Generate all SOO sections using research findings"""
        print("\n" + "="*70)
        print("PHASE 2: WRITING SOO SECTIONS")
        print("="*70 + "\n")

        if research_results:
            print("Using research findings from Phase 1\n")

        written_sections = {}

        for i, section_config in enumerate(sections_config, 1):
            section_name = section_config['name']
            print(f"[{i}/{len(sections_config)}] Writing: {section_name}...")

            # Get research findings for this section
            research_findings = {}
            if research_results and section_name in research_results:
                research_findings = research_results[section_name]

            task = {
                'section_name': section_name,
                'project_info': project_info,
                'guidance': section_config.get('guidance', ''),
                'focus': section_config.get('focus', 'general'),
                'research_findings': research_findings  # Pass research to writer
            }

            result = self.soo_writer.execute(task)
            written_sections[section_name] = result['content']
            
            print(f"  ✓ Complete ({result['word_count']} words, "
                  f"{result['objectives_count']} objectives, "
                  f"SMART score: {result['smart_compliance']}/100)")
            print()
        
        print(f"✅ Writing phase complete: {len(written_sections)} sections\n")
        return written_sections
    
    def _phase_quality(self, sections: Dict, project_info: Dict) -> Dict:
        """Evaluate SOO quality"""
        print("\n" + "="*70)
        print("PHASE 3: QUALITY EVALUATION")
        print("="*70 + "\n")
        
        evaluations = {}
        
        for section_name, content in sections.items():
            print(f"Evaluating: {section_name}...")
            
            task = {
                'content': content,
                'section_name': section_name,
                'project_info': project_info,
                'evaluation_type': 'soo'  # SOO-specific evaluation
            }
            
            result = self.quality_agent.execute(task)
            evaluations[section_name] = result
            
            print(f"  Score: {result['score']}/100 ({result['grade']})")
            print()
        
        avg_score = sum(e['score'] for e in evaluations.values()) / len(evaluations)
        print(f"✅ Quality evaluation complete: Average score {avg_score:.1f}/100\n")
        
        return evaluations
    
    def _phase_revision(
        self,
        sections: Dict,
        evaluations: Dict,
        sections_config: List[Dict],
        project_info: Dict
    ) -> Dict:
        """
        Iterative refinement: Generate → Evaluate → Fix → Re-evaluate
        Uses RefinementAgent with quality feedback loop
        """
        print("\n" + "="*70)
        print("PHASE 4: ITERATIVE REFINEMENT")
        print("="*70 + "\n")

        sections_to_refine = [
            name for name, eval_result in evaluations.items()
            if eval_result['score'] < self.quality_threshold
        ]

        if not sections_to_refine:
            print("✓ All sections meet quality threshold\n")
            return sections

        print(f"Refining {len(sections_to_refine)} section(s) with iterative feedback loop...\n")

        refined_sections = sections.copy()

        for section_name in sections_to_refine:
            print(f"{'─'*70}")
            print(f"Refining: {section_name}")
            print(f"{'─'*70}")

            # Get research findings for this section
            research_findings = self.workflow_state['research_results'].get(section_name, {})

            # Iteratively refine until threshold met or max iterations reached
            refined_content, refinement_history = self._iterative_refine_section(
                section_name=section_name,
                initial_content=sections[section_name],
                initial_evaluation=evaluations[section_name],
                project_info=project_info,
                research_findings=research_findings
            )

            # Store refined content and history
            refined_sections[section_name] = refined_content
            self.workflow_state['refinement_history'][section_name] = refinement_history

            # Show improvement
            initial_score = evaluations[section_name]['score']
            final_score = refinement_history[-1]['score']
            improvement = final_score - initial_score

            print(f"\n  📊 Improvement: {initial_score}/100 → {final_score}/100 ({improvement:+d} points)")
            print(f"  🔄 Iterations: {len(refinement_history)}")
            print(f"  {'✅' if final_score >= self.quality_threshold else '⚠️ '} Final Status: {refinement_history[-1]['grade']}\n")

        print(f"✅ Iterative refinement complete\n")
        return refined_sections

    def _iterative_refine_section(
        self,
        section_name: str,
        initial_content: str,
        initial_evaluation: Dict,
        project_info: Dict,
        research_findings: Dict
    ) -> tuple[str, List[Dict]]:
        """
        Iteratively refine a single section until quality threshold met

        Returns:
            Tuple of (final_content, refinement_history)
        """
        current_content = initial_content
        current_evaluation = initial_evaluation
        refinement_history = []

        for iteration in range(1, self.max_refinement_iterations + 1):
            print(f"\n  Iteration {iteration}/{self.max_refinement_iterations}:")
            print(f"    Current score: {current_evaluation['score']}/100")

            # Check if we've met the threshold
            if current_evaluation['score'] >= self.quality_threshold:
                print(f"    ✅ Quality threshold met!")
                break

            # Apply refinement
            refinement_task = {
                'content': current_content,
                'section_name': section_name,
                'evaluation': current_evaluation,
                'project_info': project_info,
                'research_findings': research_findings,
                'iteration': iteration
            }

            refinement_result = self.refinement_agent.execute(refinement_task)
            refined_content = refinement_result['refined_content']

            print(f"    Changes: {', '.join(refinement_result['changes_made'])}")

            # Re-evaluate
            eval_task = {
                'content': refined_content,
                'section_name': section_name,
                'project_info': project_info,
                'research_findings': research_findings,
                'evaluation_type': 'soo'
            }

            new_evaluation = self.quality_agent.execute(eval_task)
            new_score = new_evaluation['score']

            print(f"    New score: {new_score}/100", end="")

            # Check for improvement
            score_improvement = new_score - current_evaluation['score']

            if score_improvement >= self.min_score_improvement:
                print(f" ({score_improvement:+d}) ✅")
                # Accept improvement
                current_content = refined_content
                current_evaluation = new_evaluation

                # Track history
                refinement_history.append({
                    'iteration': iteration,
                    'score': new_score,
                    'grade': new_evaluation['grade'],
                    'improvement': score_improvement,
                    'changes': refinement_result['changes_made']
                })

            elif score_improvement > 0:
                print(f" ({score_improvement:+d}) ⚠️  (below minimum)")
                # Small improvement - accept but warn
                current_content = refined_content
                current_evaluation = new_evaluation

                refinement_history.append({
                    'iteration': iteration,
                    'score': new_score,
                    'grade': new_evaluation['grade'],
                    'improvement': score_improvement,
                    'changes': refinement_result['changes_made']
                })

            else:
                print(f" ({score_improvement:+d}) ❌ No improvement")
                # No improvement - stop iterating
                refinement_history.append({
                    'iteration': iteration,
                    'score': current_evaluation['score'],
                    'grade': current_evaluation['grade'],
                    'improvement': 0,
                    'changes': ['No improvement - stopped']
                })
                break

            # Check convergence
            if iteration > 1 and abs(score_improvement) < 2:
                print(f"    ⚠️  Converged (minimal improvement)")
                break

        return current_content, refinement_history
    
    def _phase_assembly(
        self,
        sections: Dict,
        project_info: Dict,
        evaluations: Dict
    ) -> str:
        """Assemble final SOO document"""
        print("\n" + "="*70)
        print("PHASE 4: ASSEMBLY")
        print("="*70 + "\n")
        
        soo_parts = []
        
        # Header
        soo_parts.append("# Statement of Objectives (SOO)")
        soo_parts.append("")
        soo_parts.append(f"**Program:** {project_info.get('program_name', '')}")
        soo_parts.append(f"**Date:** {project_info.get('date', '')}")
        soo_parts.append(f"**Prepared by:** {project_info.get('author', '')}")
        soo_parts.append(f"**Organization:** {project_info.get('organization', '')}")
        soo_parts.append("")
        soo_parts.append("---")
        soo_parts.append("")
        
        # Sections
        for section_name, content in sections.items():
            soo_parts.append(f"## {section_name}")
            soo_parts.append("")
            soo_parts.append(content)
            soo_parts.append("")
            soo_parts.append("---")
            soo_parts.append("")
        
        soo = "\n".join(soo_parts)
        
        print(f"✅ SOO assembled: {len(soo.split())} total words\n")
        
        return soo
    
    def _save_soo(self, soo_content: str, output_path: str) -> None:
        """Save SOO to file (markdown and PDF)"""
        from pathlib import Path

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Save markdown
        with open(output_path, 'w') as f:
            f.write(soo_content)

        print(f"Saved: {output_path}")

        # Convert to PDF
        pdf_path = output_path.replace('.md', '.pdf')
        try:
            from utils.convert_md_to_pdf import convert_markdown_to_pdf
            convert_markdown_to_pdf(output_path, pdf_path)
            print(f"PDF saved: {pdf_path}")
        except Exception as e:
            print(f"Warning: Could not create PDF: {e}")

    def _save_evaluation_report(
        self,
        evaluations: Dict,
        project_info: Dict,
        soo_output_path: str
    ) -> None:
        """
        Save evaluation report for SOO document

        Args:
            evaluations: Evaluation results from quality agent
            project_info: Project information
            soo_output_path: Path where SOO was saved
        """
        from pathlib import Path

        # Determine evaluation report path
        eval_path = soo_output_path.replace('.md', '_evaluation_report.md')

        print(f"\nGenerating evaluation report...")

        # Create report generator
        generator = EvaluationReportGenerator(document_type="SOO")

        # Generate and save report
        generator.generate_full_report(
            evaluation_results=evaluations,
            project_info=project_info,
            output_path=eval_path
        )

        print(f"Evaluation report saved: {eval_path}")

        # Convert to PDF
        pdf_eval_path = eval_path.replace('.md', '.pdf')
        try:
            from utils.convert_md_to_pdf import convert_markdown_to_pdf
            convert_markdown_to_pdf(eval_path, pdf_eval_path)
            print(f"PDF evaluation report: {pdf_eval_path}")
        except Exception as e:
            print(f"Warning: Could not create PDF evaluation report: {e}")
