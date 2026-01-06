"""
Progressive Refinement Orchestrator

Implements automatic quality improvement loop:
Generate → Evaluate → Refine → Re-evaluate (repeat until quality threshold met)

Features:
- Automatic iterative refinement
- Quality score tracking
- Convergence detection
- Best version selection
- Detailed improvement metrics

Dependencies:
- agents.quality_agent: Quality evaluation
- agents.refinement_agent: Content refinement
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Import existing agents
from backend.agents.quality_agent import QualityAgent
from backend.agents.refinement_agent import RefinementAgent


class ProgressiveRefinementOrchestrator:
    """
    Orchestrates progressive refinement loop for document quality improvement

    Workflow:
    1. Evaluate initial content with QualityAgent
    2. If score < threshold, refine with RefinementAgent
    3. Re-evaluate refined content
    4. Keep best version (highest score)
    5. Repeat until threshold met or max iterations reached

    Key Features:
    - Automatic convergence detection (stops if no improvement)
    - Detailed iteration tracking
    - Improvement metrics calculation
    - Best version preservation
    """

    def __init__(
        self,
        api_key: str,
        quality_threshold: int = 85,
        max_iterations: int = 2,
        min_improvement: int = 2
    ):
        """
        Initialize progressive refinement orchestrator

        Args:
            api_key: Anthropic API key
            quality_threshold: Target quality score (0-100)
            max_iterations: Maximum refinement iterations
            min_improvement: Minimum score improvement to continue (points)
        """
        self.quality_agent = QualityAgent(api_key=api_key)
        self.refinement_agent = RefinementAgent(api_key=api_key)

        self.quality_threshold = quality_threshold
        self.max_iterations = max_iterations
        self.min_improvement = min_improvement

        print(f"🔄 Progressive Refinement Orchestrator initialized")
        print(f"   Quality threshold: {quality_threshold}/100")
        print(f"   Max iterations: {max_iterations}")
        print(f"   Min improvement: +{min_improvement} points")

    def refine_until_quality_met(
        self,
        content: str,
        section_name: str,
        doc_type: str,
        project_info: Dict,
        research_findings: Optional[Dict] = None
    ) -> Dict:
        """
        Progressively refine content until quality threshold is met

        Args:
            content: Initial content to refine
            section_name: Section name (for logging)
            doc_type: Document type
            project_info: Project information for fact-checking
            research_findings: Research findings for citations

        Returns:
            Dictionary with:
                - final_content: Best version of content
                - initial_score: Starting quality score
                - final_score: Final quality score
                - improvement: Score improvement (delta)
                - iterations_used: Number of iterations performed
                - iteration_history: List of iteration details
                - refinement_applied: Whether refinement was applied
                - quality_evaluation: Final quality evaluation results
        """
        print(f"\n{'='*80}")
        print(f"🔄 PROGRESSIVE REFINEMENT: {section_name}")
        print(f"{'='*80}\n")

        research_findings = research_findings or {}

        # Track iterations
        iteration_history = []

        # Track best version
        best_content = content
        best_score = 0
        best_evaluation = {}

        # Initial evaluation
        print(f"📊 Initial Evaluation...")
        initial_evaluation = self._evaluate_content(
            content,
            section_name,
            project_info,
            research_findings
        )

        initial_score = initial_evaluation['score']
        best_score = initial_score
        best_evaluation = initial_evaluation

        print(f"   Score: {initial_score}/100 ({initial_evaluation['grade']})")
        print(f"   Issues: {len(initial_evaluation['issues'])}")

        # Add to history
        iteration_history.append({
            'iteration': 0,
            'type': 'initial_evaluation',
            'score': initial_score,
            'grade': initial_evaluation['grade'],
            'issues_count': len(initial_evaluation['issues']),
            'hallucination_risk': initial_evaluation['hallucination_risk']
        })

        # Check if refinement needed
        if initial_score >= self.quality_threshold:
            print(f"\n✅ Quality threshold met ({initial_score} >= {self.quality_threshold})")
            print(f"   No refinement needed!\n")

            return {
                'final_content': content,
                'initial_score': initial_score,
                'final_score': initial_score,
                'improvement': 0,
                'iterations_used': 0,
                'iteration_history': iteration_history,
                'refinement_applied': False,
                'quality_evaluation': initial_evaluation
            }

        print(f"\n⚠️  Score below threshold ({initial_score} < {self.quality_threshold})")
        print(f"   Starting refinement loop...\n")

        # Refinement loop
        current_content = content
        current_evaluation = initial_evaluation
        iterations_performed = 0

        for iteration in range(1, self.max_iterations + 1):
            print(f"{'─'*80}")
            print(f"🔄 ITERATION {iteration}/{self.max_iterations}")
            print(f"{'─'*80}\n")

            # Refine content
            print(f"🛠️  Refining content...")
            refinement_result = self._refine_content(
                current_content,
                current_evaluation,
                section_name,
                project_info,
                research_findings,
                iteration
            )

            refined_content = refinement_result['refined_content']
            changes_made = refinement_result['changes_made']

            print(f"   Changes: {', '.join(changes_made)}")

            # Re-evaluate
            print(f"\n📊 Re-evaluating...")
            new_evaluation = self._evaluate_content(
                refined_content,
                section_name,
                project_info,
                research_findings
            )

            new_score = new_evaluation['score']
            improvement = new_score - current_evaluation['score']

            print(f"   Score: {new_score}/100 ({new_evaluation['grade']})")
            print(f"   Improvement: {improvement:+d} points")

            # Track iteration
            iteration_history.append({
                'iteration': iteration,
                'type': 'refinement',
                'score_before': current_evaluation['score'],
                'score_after': new_score,
                'improvement': improvement,
                'grade': new_evaluation['grade'],
                'changes_made': changes_made,
                'issues_count': len(new_evaluation['issues']),
                'hallucination_risk': new_evaluation['hallucination_risk']
            })

            iterations_performed = iteration

            # Check if improved
            if new_score > best_score:
                print(f"   ✅ Improved! New best: {new_score}/100")
                best_content = refined_content
                best_score = new_score
                best_evaluation = new_evaluation
                current_content = refined_content
                current_evaluation = new_evaluation
            else:
                print(f"   ⚠️  No improvement (best remains: {best_score}/100)")
                print(f"   Keeping previous best version")
                # Don't update current_content - stop iterating
                break

            # Check if threshold met
            if new_score >= self.quality_threshold:
                print(f"\n✅ Quality threshold met ({new_score} >= {self.quality_threshold})")
                print(f"   Stopping refinement loop\n")
                break

            # Check if improvement is minimal (convergence)
            if improvement < self.min_improvement:
                print(f"\n⚠️  Minimal improvement (+{improvement} < +{self.min_improvement})")
                print(f"   Convergence detected - stopping refinement\n")
                break

            print()  # Blank line between iterations

        # Final summary
        total_improvement = best_score - initial_score

        print(f"{'='*80}")
        print(f"✅ REFINEMENT COMPLETE")
        print(f"{'='*80}\n")
        print(f"   Initial Score:  {initial_score}/100")
        print(f"   Final Score:    {best_score}/100")
        print(f"   Improvement:    {total_improvement:+d} points")
        print(f"   Iterations:     {iterations_performed}")
        print(f"   Final Grade:    {best_evaluation['grade']}")
        print()

        return {
            'final_content': best_content,
            'initial_score': initial_score,
            'final_score': best_score,
            'improvement': total_improvement,
            'iterations_used': iterations_performed,
            'iteration_history': iteration_history,
            'refinement_applied': iterations_performed > 0,
            'quality_evaluation': best_evaluation
        }

    def _evaluate_content(
        self,
        content: str,
        section_name: str,
        project_info: Dict,
        research_findings: Dict
    ) -> Dict:
        """
        Evaluate content quality

        Args:
            content: Content to evaluate
            section_name: Section name
            project_info: Project information
            research_findings: Research findings

        Returns:
            Quality evaluation results
        """
        evaluation_task = {
            'content': content,
            'section_name': section_name,
            'project_info': project_info,
            'research_findings': research_findings,
            'evaluation_type': 'full'
        }

        return self.quality_agent.execute(evaluation_task)

    def _refine_content(
        self,
        content: str,
        evaluation: Dict,
        section_name: str,
        project_info: Dict,
        research_findings: Dict,
        iteration: int
    ) -> Dict:
        """
        Refine content based on evaluation

        Args:
            content: Content to refine
            evaluation: Quality evaluation results
            section_name: Section name
            project_info: Project information
            research_findings: Research findings
            iteration: Current iteration number

        Returns:
            Refinement results
        """
        refinement_task = {
            'content': content,
            'section_name': section_name,
            'evaluation': evaluation,
            'project_info': project_info,
            'research_findings': research_findings,
            'iteration': iteration
        }

        return self.refinement_agent.execute(refinement_task)

    def generate_refinement_report(
        self,
        result: Dict,
        output_path: str
    ) -> str:
        """
        Generate markdown report of refinement process

        Args:
            result: Refinement result from refine_until_quality_met()
            output_path: Path to save report

        Returns:
            Path to generated report
        """
        report_lines = [
            "# Progressive Refinement Report",
            "",
            f"**Generation Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"- **Initial Score:** {result['initial_score']}/100",
            f"- **Final Score:** {result['final_score']}/100",
            f"- **Improvement:** {result['improvement']:+d} points",
            f"- **Iterations Used:** {result['iterations_used']}",
            f"- **Refinement Applied:** {'Yes' if result['refinement_applied'] else 'No'}",
            "",
            "## Iteration History",
            "",
            "| Iteration | Type | Score Before | Score After | Improvement | Grade | Issues |",
            "|-----------|------|--------------|-------------|-------------|-------|--------|"
        ]

        for iteration_data in result['iteration_history']:
            if iteration_data['type'] == 'initial_evaluation':
                report_lines.append(
                    f"| 0 | Initial | - | {iteration_data['score']} | - | "
                    f"{iteration_data['grade']} | {iteration_data['issues_count']} |"
                )
            else:
                report_lines.append(
                    f"| {iteration_data['iteration']} | Refinement | "
                    f"{iteration_data['score_before']} | {iteration_data['score_after']} | "
                    f"{iteration_data['improvement']:+d} | {iteration_data['grade']} | "
                    f"{iteration_data['issues_count']} |"
                )

        report_lines.extend([
            "",
            "## Final Quality Assessment",
            "",
            f"**Overall Score:** {result['final_score']}/100",
            f"**Grade:** {result['quality_evaluation']['grade']}",
            f"**Hallucination Risk:** {result['quality_evaluation']['hallucination_risk']}",
            "",
            "### Remaining Issues",
            ""
        ])

        if result['quality_evaluation']['issues']:
            for issue in result['quality_evaluation']['issues']:
                report_lines.append(f"- {issue}")
        else:
            report_lines.append("- No major issues detected")

        report_lines.extend([
            "",
            "### Suggestions",
            ""
        ])

        if result['quality_evaluation']['suggestions']:
            for suggestion in result['quality_evaluation']['suggestions'][:5]:
                report_lines.append(f"- {suggestion}")
        else:
            report_lines.append("- No additional suggestions")

        report_lines.append("")

        # Write report
        report_content = '\n'.join(report_lines)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return output_path


# Example usage and testing
if __name__ == '__main__':
    import os
    import sys

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    # Sample content with issues
    sample_content = """
    # IGCE - Sample Program

    The program will cost several million dollars over approximately 3 years.
    Many vendors are interested in this opportunity. The system will provide
    significant improvements to operations.

    ## Cost Estimate

    - Labor: Around $1.5M
    - Hardware: Some amount for servers
    - Software: Various licenses needed

    The timeline is adequate for the requirements.
    """

    project_info = {
        'program_name': 'Sample Acquisition',
        'estimated_value': '$2,500,000',
        'period_of_performance': '36 months'
    }

    # Initialize orchestrator
    orchestrator = ProgressiveRefinementOrchestrator(
        api_key=api_key,
        quality_threshold=85,
        max_iterations=2
    )

    # Run refinement
    result = orchestrator.refine_until_quality_met(
        content=sample_content,
        section_name="IGCE",
        doc_type="igce",
        project_info=project_info
    )

    # Generate report
    report_path = "test_refinement_report.md"
    orchestrator.generate_refinement_report(result, report_path)

    print(f"\n📄 Report saved: {report_path}")
    print(f"\n📝 Final content preview:")
    print(result['final_content'][:500])
