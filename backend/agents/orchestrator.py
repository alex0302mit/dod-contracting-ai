"""
Orchestrator: Coordinates all agents to execute the full workflow
Main entry point for the agent-based system with optional web search
"""

from typing import Dict, List, Optional
from .research_agent import ResearchAgent
from .report_writer_agent import ReportWriterAgent
from .quality_agent import QualityAgent
from backend.rag.retriever import Retriever
import time


class Orchestrator:
    """
    Orchestrator: Coordinates the entire market research workflow

    Workflow:
    1. Research Phase: Gather information for each section (RAG + Web Search)
    2. Writing Phase: Generate content for each section
    3. Quality Phase: Evaluate each section
    4. Revision Phase: Improve sections with issues (optional)
    5. Assembly Phase: Compile final report

    Dependencies:
    - ResearchAgent: Information gathering (RAG + Web)
    - ReportWriterAgent: Content generation
    - QualityAgent: Quality evaluation
    - RAG system: Knowledge base access
    """

    def __init__(
        self,
        api_key: str,
        retriever: Retriever,
        tavily_api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize orchestrator with all agents

        Args:
            api_key: Anthropic API key
            retriever: RAG Retriever instance
            tavily_api_key: Tavily API key for web search (optional)
            model: Claude model to use
        """
        # Initialize agents
        self.research_agent = ResearchAgent(
            api_key=api_key,
            retriever=retriever,
            tavily_api_key=tavily_api_key,  # Pass web search key
            model=model
        )
        self.writer_agent = ReportWriterAgent(api_key, model)
        self.quality_agent = QualityAgent(api_key, model)

        # Workflow state
        self.workflow_state = {
            'phase': 'initialized',
            'research_results': {},
            'written_sections': {},
            'evaluation_results': {},
            'final_report': None
        }

        # Configuration
        self.quality_threshold = 70  # Minimum acceptable quality score
        self.enable_auto_revision = True  # Auto-improve low-quality sections

        print("\n" + "="*70)
        print("AGENT ORCHESTRATOR INITIALIZED")
        print("="*70)
        print(f"  ✓ Research Agent ready")
        if self.research_agent.web_search_enabled:
            print(f"    └─ Web search enabled")
        else:
            print(f"    └─ Web search disabled (RAG only)")
        print(f"  ✓ Report Writer Agent ready")
        print(f"  ✓ Quality Agent ready")
        print(f"  Quality threshold: {self.quality_threshold}/100")
        print(f"  Auto-revision: {'Enabled' if self.enable_auto_revision else 'Disabled'}")
        print("="*70 + "\n")
    
    def execute_full_workflow(
        self,
        project_info: Dict,
        sections_config: List[Dict],
        output_path: str = "outputs/reports/agent_generated_report.md"
    ) -> Dict:
        """
        Execute the complete market research report workflow
        
        Args:
            project_info: Project information dictionary
            sections_config: List of section configurations
            output_path: Path to save final report
            
        Returns:
            Dictionary with workflow results
        """
        start_time = time.time()
        
        print("\n" + "="*70)
        print("STARTING AGENT-BASED WORKFLOW")
        print("="*70)
        print(f"Project: {project_info.get('program_name', 'Unknown')}")
        print(f"Sections to generate: {len(sections_config)}")
        print("="*70 + "\n")
        
        # Phase 1: Research
        research_results = self._phase_research(sections_config, project_info)
        self.workflow_state['research_results'] = research_results
        self.workflow_state['phase'] = 'research_complete'
        
        # Phase 2: Writing
        written_sections = self._phase_writing(sections_config, research_results, project_info)
        self.workflow_state['written_sections'] = written_sections
        self.workflow_state['phase'] = 'writing_complete'
        
        # Phase 3: Quality Evaluation
        evaluation_results = self._phase_quality_check(written_sections, project_info, research_results)
        self.workflow_state['evaluation_results'] = evaluation_results
        self.workflow_state['phase'] = 'evaluation_complete'
        
        # Phase 4: Revision (if needed)
        if self.enable_auto_revision:
            written_sections = self._phase_revision(written_sections, evaluation_results, research_results, project_info)
            self.workflow_state['written_sections'] = written_sections
            self.workflow_state['phase'] = 'revision_complete'
        
        # Phase 5: Assembly
        final_report = self._phase_assembly(written_sections, project_info, evaluation_results)
        self.workflow_state['final_report'] = final_report
        self.workflow_state['phase'] = 'complete'
        
        # Save report
        self._save_report(final_report, output_path)
        
        # Generate summary
        elapsed_time = time.time() - start_time
        summary = self._generate_summary(evaluation_results, elapsed_time)
        
        print("\n" + "="*70)
        print("WORKFLOW COMPLETE")
        print("="*70)
        print(summary)
        print(f"\nReport saved to: {output_path}")
        print("="*70 + "\n")
        
        return {
            'status': 'success',
            'workflow_state': self.workflow_state,
            'summary': summary,
            'output_path': output_path,
            'elapsed_time': elapsed_time
        }
    
    def _phase_research(self, sections_config: List[Dict], project_info: Dict) -> Dict:
        """
        Phase 1: Research information for each section
        
        Args:
            sections_config: Section configurations
            project_info: Project information
            
        Returns:
            Dictionary of research results by section
        """
        print("\n" + "="*70)
        print("PHASE 1: RESEARCH")
        print("="*70 + "\n")
        
        research_results = {}
        
        for section_config in sections_config:
            section_name = section_config['name']
            section_guidance = section_config['guidance']
            
            print(f"Researching: {section_name}...")
            
            # Research for this section
            result = self.research_agent.research_for_section(
                section_name,
                section_guidance,
                project_info
            )
            
            research_results[section_name] = result
            
            # Show confidence
            confidence = result.get('confidence', 'unknown')
            print(f"  ✓ Research complete (Confidence: {confidence.upper()})")
            
            # Show any gaps
            gaps = result.get('gaps', [])
            if gaps:
                print(f"  ⚠️  Information gaps: {len(gaps)}")
            
            print()
        
        print(f"✅ Research phase complete: {len(research_results)} sections researched\n")
        
        return research_results
    
    def _phase_writing(
        self,
        sections_config: List[Dict],
        research_results: Dict,
        project_info: Dict
    ) -> Dict:
        """
        Phase 2: Write content for each section
        
        Args:
            sections_config: Section configurations
            research_results: Research results from Phase 1
            project_info: Project information
            
        Returns:
            Dictionary of written content by section
        """
        print("\n" + "="*70)
        print("PHASE 2: WRITING")
        print("="*70 + "\n")
        
        written_sections = {}
        previous_sections = {}
        
        for section_config in sections_config:
            section_name = section_config['name']
            section_guidance = section_config['guidance']
            
            print(f"Writing: {section_name}...")
            
            # Get research findings
            research_findings = research_results.get(section_name, {})
            
            # Write section
            task = {
                'section_name': section_name,
                'section_guidance': section_guidance,
                'research_findings': research_findings,
                'project_info': project_info,
                'previous_sections': previous_sections
            }
            
            result = self.writer_agent.execute(task)
            
            written_sections[section_name] = result['content']
            previous_sections[section_name] = result['content']
            
            # Show stats
            word_count = result['word_count']
            citations = len(result['citations_used'])
            print(f"  ✓ Section complete ({word_count} words, {citations} citations)")
            
            # Show quality notes
            for note in result['quality_notes']:
                if 'may' in note.lower() or 'need' in note.lower():
                    print(f"  ⚠️  {note}")
            
            print()
        
        print(f"✅ Writing phase complete: {len(written_sections)} sections written\n")
        
        return written_sections
    
    def _phase_quality_check(
        self,
        written_sections: Dict,
        project_info: Dict,
        research_results: Dict
    ) -> Dict:
        """
        Phase 3: Evaluate quality of written sections
        
        Args:
            written_sections: Written content by section
            project_info: Project information
            research_results: Research results
            
        Returns:
            Dictionary of evaluation results by section
        """
        print("\n" + "="*70)
        print("PHASE 3: QUALITY EVALUATION")
        print("="*70 + "\n")
        
        evaluation_results = {}
        
        for section_name, content in written_sections.items():
            print(f"Evaluating: {section_name}...")
            
            research_findings = research_results.get(section_name, {})
            
            task = {
                'content': content,
                'section_name': section_name,
                'project_info': project_info,
                'research_findings': research_findings,
                'evaluation_type': 'section'
            }
            
            result = self.quality_agent.execute(task)
            
            evaluation_results[section_name] = result
            
            # Show score
            score = result['score']
            grade = result['grade']
            risk = result['hallucination_risk']
            
            score_symbol = "✓" if score >= self.quality_threshold else "⚠️"
            print(f"  {score_symbol} Score: {score}/100 ({grade})")
            print(f"  Hallucination risk: {risk}")
            
            # Show critical issues
            if result['issues']:
                print(f"  Issues: {len(result['issues'])}")
                for issue in result['issues'][:2]:  # Show first 2 issues
                    print(f"    - {issue[:80]}...")
            
            print()
        
        # Calculate overall score
        scores = [r['score'] for r in evaluation_results.values()]
        overall_score = sum(scores) / len(scores) if scores else 0
        
        print(f"✅ Quality evaluation complete: Overall score {overall_score:.1f}/100\n")
        
        return evaluation_results
    
    def _phase_revision(
        self,
        written_sections: Dict,
        evaluation_results: Dict,
        research_results: Dict,
        project_info: Dict
    ) -> Dict:
        """
        Phase 4: Revise sections with quality issues
        
        Args:
            written_sections: Current written content
            evaluation_results: Evaluation results
            research_results: Research results
            project_info: Project information
            
        Returns:
            Revised sections dictionary
        """
        print("\n" + "="*70)
        print("PHASE 4: REVISION")
        print("="*70 + "\n")
        
        sections_to_revise = []
        
        for section_name, eval_result in evaluation_results.items():
            if eval_result['score'] < self.quality_threshold:
                sections_to_revise.append(section_name)
        
        if not sections_to_revise:
            print("✓ All sections meet quality threshold. No revisions needed.\n")
            return written_sections
        
        print(f"Revising {len(sections_to_revise)} section(s) that scored below threshold...\n")
        
        revised_sections = written_sections.copy()
        
        for section_name in sections_to_revise:
            print(f"Revising: {section_name}...")
            
            eval_result = evaluation_results[section_name]
            current_content = written_sections[section_name]
            research_findings = research_results.get(section_name, {})
            
            # Create revision prompt with feedback
            revision_guidance = self._create_revision_guidance(eval_result)
            
            # Revise using writer agent with additional feedback
            task = {
                'section_name': section_name,
                'section_guidance': revision_guidance,
                'research_findings': research_findings,
                'project_info': project_info,
                'previous_sections': {}
            }
            
            result = self.writer_agent.execute(task)
            revised_sections[section_name] = result['content']
            
            print(f"  ✓ Revision complete")
            print()
        
        print(f"✅ Revision phase complete: {len(sections_to_revise)} section(s) revised\n")
        
        return revised_sections
    
    def _create_revision_guidance(self, eval_result: Dict) -> str:
        """
        Create revision guidance based on evaluation results
        
        Args:
            eval_result: Evaluation result for a section
            
        Returns:
            Revision guidance text
        """
        guidance_parts = ["This section needs revision to address the following issues:\n"]
        
        # Add issues
        if eval_result['issues']:
            guidance_parts.append("ISSUES TO FIX:")
            for issue in eval_result['issues'][:5]:
                guidance_parts.append(f"- {issue}")
            guidance_parts.append("")
        
        # Add suggestions
        if eval_result['suggestions']:
            guidance_parts.append("IMPROVEMENT SUGGESTIONS:")
            for suggestion in eval_result['suggestions'][:5]:
                guidance_parts.append(f"- {suggestion}")
            guidance_parts.append("")
        
        guidance_parts.append("Please rewrite this section addressing all issues above while maintaining professional quality.")
        
        return "\n".join(guidance_parts)
    
    def _phase_assembly(
        self,
        written_sections: Dict,
        project_info: Dict,
        evaluation_results: Dict
    ) -> str:
        """
        Phase 5: Assemble final report
        
        Args:
            written_sections: Final written content
            project_info: Project information
            evaluation_results: Evaluation results
            
        Returns:
            Complete report as markdown string
        """
        print("\n" + "="*70)
        print("PHASE 5: ASSEMBLY")
        print("="*70 + "\n")
        
        print("Assembling final report...\n")
        
        # Build report
        report_parts = []
        
        # Header
        report_parts.append("# Market Research Report")
        report_parts.append("")
        report_parts.append(f"**Program Name:** {project_info.get('program_name', '')}")
        report_parts.append(f"**Date:** {project_info.get('date', '')}")
        report_parts.append(f"**Prepared by:** {project_info.get('author', '')}")
        report_parts.append(f"**Organization:** {project_info.get('organization', '')}")
        report_parts.append("")
        report_parts.append("---")
        report_parts.append("")
        
        # Add each section
        for section_name, content in written_sections.items():
            report_parts.append(f"## {section_name}")
            report_parts.append("")
            report_parts.append(content)
            report_parts.append("")
            report_parts.append("---")
            report_parts.append("")
        
        # Add quality assessment footer
        report_parts.append("## Quality Assessment")
        report_parts.append("")
        report_parts.append("This report was generated using an AI-assisted workflow with quality assurance.")
        report_parts.append("")
        
        for section_name, eval_result in evaluation_results.items():
            score = eval_result['score']
            report_parts.append(f"- **{section_name}**: Quality Score {score}/100")
        
        report = "\n".join(report_parts)
        
        print(f"✅ Report assembled: {len(report.split())} total words\n")
        
        return report
    
    def _save_report(self, report: str, output_path: str) -> None:
        """
        Save report to file
        
        Args:
            report: Report content
            output_path: Output file path
        """
        import os
        from pathlib import Path
        
        # Create directory if needed
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save markdown
        with open(output_path, 'w') as f:
            f.write(report)
        
        print(f"Saved: {output_path}")
        
        # Also try to save PDF if possible
        try:
            from utils.convert_md_to_pdf import convert_markdown_to_pdf
            pdf_path = output_path.replace('.md', '.pdf')
            convert_markdown_to_pdf(output_path, pdf_path)
            print(f"Saved: {pdf_path}")
        except Exception as e:
            print(f"Note: Could not generate PDF: {e}")
    
    def _generate_summary(self, evaluation_results: Dict, elapsed_time: float) -> str:
        """
        Generate workflow summary
        
        Args:
            evaluation_results: Evaluation results
            elapsed_time: Total elapsed time
            
        Returns:
            Summary text
        """
        scores = [r['score'] for r in evaluation_results.values()]
        overall_score = sum(scores) / len(scores) if scores else 0
        
        high_risk_sections = [
            name for name, result in evaluation_results.items()
            if result['hallucination_risk'] == 'HIGH'
        ]
        
        low_score_sections = [
            name for name, result in evaluation_results.items()
            if result['score'] < self.quality_threshold
        ]
        
        summary_parts = []
        summary_parts.append(f"Overall Quality Score: {overall_score:.1f}/100")
        summary_parts.append(f"Sections Generated: {len(evaluation_results)}")
        summary_parts.append(f"Elapsed Time: {elapsed_time:.1f} seconds")
        
        if high_risk_sections:
            summary_parts.append(f"\n⚠️  High Hallucination Risk: {', '.join(high_risk_sections)}")
        
        if low_score_sections:
            summary_parts.append(f"\n⚠️  Below Threshold: {', '.join(low_score_sections)}")
        
        if not high_risk_sections and not low_score_sections:
            summary_parts.append("\n✅ All sections meet quality standards")
        
        return "\n".join(summary_parts)
    
    def get_workflow_state(self) -> Dict:
        """Get current workflow state"""
        return self.workflow_state
