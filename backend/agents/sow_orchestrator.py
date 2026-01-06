"""
SOW Orchestrator: Coordinates SOW generation workflow
Manages SOW Writer Agent and Quality Agent for SOW documents
"""

from typing import Dict, List
from .sow_writer_agent import SOWWriterAgent
from .quality_agent import QualityAgent
from backend.rag.retriever import Retriever
from backend.utils.evaluation_report_generator import EvaluationReportGenerator
import time


class SOWOrchestrator:
    """
    SOW Orchestrator: Coordinates Statement of Work generation

    Workflow:
    1. Planning Phase: Analyze requirements and structure
    2. Writing Phase: Generate each SOW section using RAG
    3. Quality Phase: Evaluate compliance and completeness
    4. Revision Phase: Improve sections if needed
    5. Assembly Phase: Compile final SOW document

    Dependencies:
    - SOWWriterAgent: SOW content generation
    - QualityAgent: Quality evaluation
    - RAG system: SOW manual knowledge base
    """

    def __init__(
        self,
        api_key: str,
        retriever: Retriever,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize SOW orchestrator

        Args:
            api_key: Anthropic API key
            retriever: RAG Retriever with SOW manual indexed
            model: Claude model to use
        """
        # Initialize agents
        self.sow_writer = SOWWriterAgent(api_key, retriever, model)
        self.quality_agent = QualityAgent(api_key, model)

        # Workflow state
        self.workflow_state = {
            'phase': 'initialized',
            'written_sections': {},
            'evaluation_results': {},
            'final_sow': None
        }

        # Configuration
        self.quality_threshold = 75  # Higher threshold for SOW compliance
        self.enable_auto_revision = True

        print("\n" + "="*70)
        print("SOW ORCHESTRATOR INITIALIZED")
        print("="*70)
        print(f"  ✓ SOW Writer Agent ready")
        print(f"  ✓ Quality Agent ready")
        print(f"  Quality threshold: {self.quality_threshold}/100")
        print(f"  Auto-revision: {'Enabled' if self.enable_auto_revision else 'Disabled'}")
        print("="*70 + "\n")

    def execute_sow_workflow(
        self,
        project_info: Dict,
        sow_sections_config: List[Dict],
        output_path: str = "outputs/sow/statement_of_work.md"
    ) -> Dict:
        """
        Execute complete SOW generation workflow

        Args:
            project_info: Project information
            sow_sections_config: List of SOW section configurations
                Each: {name, requirements, context}
            output_path: Path to save SOW

        Returns:
            Dictionary with workflow results
        """
        start_time = time.time()

        print("\n" + "="*70)
        print("STARTING SOW GENERATION WORKFLOW")
        print("="*70)
        print(f"Project: {project_info.get('program_name', 'Unknown')}")
        print(f"SOW Sections: {len(sow_sections_config)}")
        print("="*70 + "\n")

        # Phase 1: Writing
        written_sections = self._phase_writing(sow_sections_config, project_info)
        self.workflow_state['written_sections'] = written_sections
        self.workflow_state['phase'] = 'writing_complete'

        # Phase 2: Quality Check
        evaluation_results = self._phase_quality_check(written_sections, project_info)
        self.workflow_state['evaluation_results'] = evaluation_results
        self.workflow_state['phase'] = 'evaluation_complete'

        # Phase 3: Revision (if needed)
        if self.enable_auto_revision:
            written_sections = self._phase_revision(written_sections, evaluation_results, project_info)
            self.workflow_state['written_sections'] = written_sections
            self.workflow_state['phase'] = 'revision_complete'

        # Phase 4: Assembly
        final_sow = self._phase_assembly(written_sections, project_info, evaluation_results)
        self.workflow_state['final_sow'] = final_sow
        self.workflow_state['phase'] = 'complete'

        # Save SOW
        self._save_sow(final_sow, output_path)

        # Save evaluation report
        self._save_evaluation_report(evaluation_results, project_info, output_path)

        # Summary
        elapsed_time = time.time() - start_time
        summary = self._generate_summary(evaluation_results, elapsed_time)

        print("\n" + "="*70)
        print("SOW GENERATION COMPLETE")
        print("="*70)
        print(summary)
        print(f"\nSOW saved to: {output_path}")
        print("="*70 + "\n")

        return {
            'status': 'success',
            'workflow_state': self.workflow_state,
            'summary': summary,
            'output_path': output_path,
            'elapsed_time': elapsed_time
        }

    def _phase_writing(
        self,
        sow_sections_config: List[Dict],
        project_info: Dict
    ) -> Dict:
        """
        Phase 1: Write all SOW sections

        Args:
            sow_sections_config: Section configurations
            project_info: Project information

        Returns:
            Dictionary of written sections
        """
        print("\n" + "="*70)
        print("PHASE 1: WRITING SOW SECTIONS")
        print("="*70)
        print()

        written_sections = {}

        for i, section_config in enumerate(sow_sections_config, 1):
            section_name = section_config['name']
            print(f"[{i}/{len(sow_sections_config)}] Writing: {section_name}")

            task = {
                'section_name': section_name,
                'project_info': project_info,
                'requirements': section_config.get('requirements', ''),
                'context': section_config.get('context', {})
            }

            result = self.sow_writer.execute(task)
            written_sections[section_name] = result
            print(f"      ✓ Completed ({result['word_count']} words)")

        print()
        print(f"✅ All {len(written_sections)} sections written")
        print("="*70)

        return written_sections

    def _phase_quality_check(
        self,
        written_sections: Dict,
        project_info: Dict
    ) -> Dict:
        """
        Phase 2: Evaluate quality of each section

        Args:
            written_sections: Written sections
            project_info: Project information

        Returns:
            Evaluation results
        """
        print("\n" + "="*70)
        print("PHASE 2: QUALITY EVALUATION")
        print("="*70)
        print()

        evaluation_results = {}

        for i, (section_name, section_data) in enumerate(written_sections.items(), 1):
            print(f"[{i}/{len(written_sections)}] Evaluating: {section_name}")

            task = {
                'section_name': section_name,
                'content': section_data['content'],
                'project_info': project_info,
                'evaluation_type': 'sow_compliance'  # SOW-specific evaluation
            }

            result = self.quality_agent.execute(task)
            evaluation_results[section_name] = result

            score = result.get('score', 0)
            status = "✓" if score >= self.quality_threshold else "⚠"
            print(f"      {status} Score: {score}/100")

        avg_score = sum(r.get('score', 0) for r in evaluation_results.values()) / len(evaluation_results)
        print()
        print(f"Average quality score: {avg_score:.1f}/100")
        print("="*70)

        return evaluation_results

    def _phase_revision(
        self,
        written_sections: Dict,
        evaluation_results: Dict,
        project_info: Dict
    ) -> Dict:
        """
        Phase 3: Revise low-quality sections

        Args:
            written_sections: Written sections
            evaluation_results: Evaluation results
            project_info: Project information

        Returns:
            Revised sections
        """
        sections_to_revise = [
            name for name, eval_result in evaluation_results.items()
            if eval_result.get('score', 0) < self.quality_threshold
        ]

        if not sections_to_revise:
            print("\n✅ All sections meet quality threshold. No revisions needed.")
            return written_sections

        print("\n" + "="*70)
        print(f"PHASE 3: REVISION ({len(sections_to_revise)} sections)")
        print("="*70)
        print()

        for i, section_name in enumerate(sections_to_revise, 1):
            print(f"[{i}/{len(sections_to_revise)}] Revising: {section_name}")

            # Get issues from evaluation
            issues = evaluation_results[section_name].get('issues', [])
            print(f"      Issues: {', '.join(issues[:3])}")

            # Rewrite with feedback
            task = {
                'section_name': section_name,
                'project_info': project_info,
                'requirements': f"Address these issues: {', '.join(issues)}",
                'context': {
                    'revision': True,
                    'previous_version': written_sections[section_name]['content'],
                    'feedback': issues
                }
            }

            result = self.sow_writer.execute(task)
            written_sections[section_name] = result
            print(f"      ✓ Revised")

        print()
        print("="*70)

        return written_sections

    def _phase_assembly(
        self,
        written_sections: Dict,
        project_info: Dict,
        evaluation_results: Dict
    ) -> str:
        """
        Phase 4: Assemble final SOW document

        Args:
            written_sections: All written sections
            project_info: Project information
            evaluation_results: Quality evaluation results

        Returns:
            Final SOW document as string
        """
        print("\n" + "="*70)
        print("PHASE 4: ASSEMBLING FINAL SOW")
        print("="*70)
        print()

        # Build SOW document
        sow_parts = []

        # Header
        sow_parts.append(f"# Statement of Work")
        sow_parts.append(f"\n**Program:** {project_info.get('program_name', '')}")
        sow_parts.append(f"**Date:** {project_info.get('date', '')}")
        sow_parts.append(f"**Prepared by:** {project_info.get('author', '')}")
        sow_parts.append(f"**Organization:** {project_info.get('organization', '')}")
        sow_parts.append("\n---\n")

        # Sections
        for section_name, section_data in written_sections.items():
            sow_parts.append(f"\n## {section_name}\n")
            sow_parts.append(section_data['content'])
            sow_parts.append("\n")

        # Quality summary (optional)
        avg_score = sum(r.get('score', 0) for r in evaluation_results.values()) / len(evaluation_results)
        sow_parts.append("\n---\n")
        sow_parts.append(f"\n*Document Quality Score: {avg_score:.1f}/100*\n")

        final_sow = "\n".join(sow_parts)

        print(f"✓ Assembled {len(written_sections)} sections")
        print(f"✓ Total word count: {len(final_sow.split())} words")
        print("="*70)

        return final_sow

    def _save_sow(self, sow_content: str, output_path: str) -> None:
        """Save SOW to file"""
        import os
        from pathlib import Path

        # Create directory if needed
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Save markdown
        with open(output_path, 'w') as f:
            f.write(sow_content)

        # Convert to PDF if possible
        pdf_path = output_path.replace('.md', '.pdf')
        try:
            from utils.convert_md_to_pdf import convert_markdown_to_pdf
            convert_markdown_to_pdf(output_path, pdf_path)
            print(f"\n✓ PDF saved: {pdf_path}")
        except Exception as e:
            print(f"\n⚠ Could not create PDF: {e}")

    def _generate_summary(self, evaluation_results: Dict, elapsed_time: float) -> str:
        """Generate workflow summary"""
        avg_score = sum(r.get('score', 0) for r in evaluation_results.values()) / len(evaluation_results)

        summary_lines = [
            f"\nWorkflow Statistics:",
            f"  • Total sections: {len(evaluation_results)}",
            f"  • Average quality: {avg_score:.1f}/100",
            f"  • Time elapsed: {elapsed_time:.1f}s",
            f"  • Status: {'✅ SUCCESS' if avg_score >= self.quality_threshold else '⚠ NEEDS REVIEW'}"
        ]

        return "\n".join(summary_lines)

    def _save_evaluation_report(
        self,
        evaluations: Dict,
        project_info: Dict,
        sow_output_path: str
    ) -> None:
        """
        Save evaluation report for SOW document

        Args:
            evaluations: Evaluation results from quality agent
            project_info: Project information
            sow_output_path: Path where SOW was saved
        """
        from pathlib import Path

        # Determine evaluation report path
        eval_path = sow_output_path.replace('.md', '_evaluation_report.md')

        print(f"\nGenerating evaluation report...")

        # Create report generator
        generator = EvaluationReportGenerator(document_type="SOW")

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


# Example usage
def main():
    """Test the SOW orchestrator"""
    import os
    from dotenv import load_dotenv
    from rag.vector_store import VectorStore
    from rag.retriever import Retriever

    load_dotenv()
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        return

    # Initialize RAG
    vector_store = VectorStore(api_key)
    if not vector_store.load():
        print("No vector store found")
        return

    retriever = Retriever(vector_store, top_k=5)

    # Project info
    project_info = {
        "program_name": "Cloud Inventory System",
        "author": "John Smith",
        "organization": "DOD/ARMY",
        "date": "10/04/2025",
        "budget": "$2.5M",
        "period_of_performance": "36 months"
    }

    # SOW sections
    sections = [
        {"name": "Scope", "requirements": "Define boundaries of work"},
        {"name": "Tasks", "requirements": "List specific deliverable tasks"},
        {"name": "Deliverables", "requirements": "Concrete outputs expected"},
        {"name": "Performance Standards", "requirements": "Quality and acceptance criteria"}
    ]

    # Execute
    orchestrator = SOWOrchestrator(api_key, retriever)
    result = orchestrator.execute_sow_workflow(project_info, sections)

    print(f"\n✅ SOW generated: {result['output_path']}")


if __name__ == "__main__":
    main()
