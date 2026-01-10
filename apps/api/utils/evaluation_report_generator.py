"""
Evaluation Report Generator
Generates detailed quality evaluation reports from QualityAgent results
"""

from typing import Dict, List
from datetime import datetime


class EvaluationReportGenerator:
    """
    Generates formatted evaluation reports for document quality assessments

    Takes evaluation results from QualityAgent and produces comprehensive
    markdown reports with scores, issues, suggestions, and detailed findings.
    """

    def __init__(self, document_type: str = "Document"):
        """
        Initialize evaluation report generator

        Args:
            document_type: Type of document (e.g., "RFP", "SOO", "SOW")
        """
        self.document_type = document_type

    def generate_full_report(
        self,
        evaluation_results: Dict,
        project_info: Dict,
        output_path: str
    ) -> str:
        """
        Generate and save complete evaluation report

        Args:
            evaluation_results: Dictionary of section_name: evaluation_result
            project_info: Project information dictionary
            output_path: Path to save markdown report

        Returns:
            Path to saved report
        """
        # Calculate overall statistics
        overall_stats = self._calculate_overall_stats(evaluation_results)

        # Build report
        report_lines = []

        # Header
        report_lines.extend(self._generate_header(project_info, overall_stats))

        # Executive Summary
        report_lines.extend(self._generate_executive_summary(overall_stats))

        # Overall Score Breakdown
        report_lines.extend(self._generate_score_breakdown(overall_stats))

        # Section-by-Section Evaluation
        report_lines.extend(self._generate_section_evaluations(evaluation_results))

        # Issues Summary
        report_lines.extend(self._generate_issues_summary(evaluation_results))

        # Recommendations
        report_lines.extend(self._generate_recommendations(evaluation_results, overall_stats))

        # Footer
        report_lines.extend(self._generate_footer())

        # Join and save
        report_content = '\n'.join(report_lines)

        with open(output_path, 'w') as f:
            f.write(report_content)

        return output_path

    def _calculate_overall_stats(self, evaluation_results: Dict) -> Dict:
        """Calculate overall statistics from all section evaluations"""
        if not evaluation_results:
            return {
                'overall_score': 0,
                'overall_grade': 'N/A',
                'section_count': 0,
                'avg_hallucination_risk': 'N/A',
                'total_issues': 0,
                'total_suggestions': 0,
                'sections_below_threshold': []
            }

        scores = [result['score'] for result in evaluation_results.values()]
        overall_score = sum(scores) / len(scores)

        # Count issues and suggestions
        total_issues = sum(len(result.get('issues', [])) for result in evaluation_results.values())
        total_suggestions = sum(len(result.get('suggestions', [])) for result in evaluation_results.values())

        # Check hallucination risks
        risk_levels = [result.get('hallucination_risk', 'UNKNOWN') for result in evaluation_results.values()]
        high_risk_count = sum(1 for risk in risk_levels if risk == 'HIGH')
        medium_risk_count = sum(1 for risk in risk_levels if risk == 'MEDIUM')

        if high_risk_count > 0:
            avg_risk = 'HIGH'
        elif medium_risk_count > len(risk_levels) / 2:
            avg_risk = 'MEDIUM'
        else:
            avg_risk = 'LOW'

        # Sections below 75
        sections_below = [
            name for name, result in evaluation_results.items()
            if result['score'] < 75
        ]

        return {
            'overall_score': round(overall_score, 1),
            'overall_grade': self._score_to_grade(overall_score),
            'section_count': len(evaluation_results),
            'avg_hallucination_risk': avg_risk,
            'total_issues': total_issues,
            'total_suggestions': total_suggestions,
            'sections_below_threshold': sections_below
        }

    def _score_to_grade(self, score: float) -> str:
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

    def _generate_header(self, project_info: Dict, overall_stats: Dict) -> List[str]:
        """Generate report header"""
        lines = [
            f"# {self.document_type} Quality Evaluation Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Document Information",
            "",
            f"- **Program:** {project_info.get('program_name', 'N/A')}",
            f"- **Organization:** {project_info.get('organization', 'N/A')}",
            f"- **Author:** {project_info.get('author', 'N/A')}",
            "",
            "---",
            ""
        ]
        return lines

    def _generate_executive_summary(self, overall_stats: Dict) -> List[str]:
        """Generate executive summary section"""
        score = overall_stats['overall_score']
        grade = overall_stats['overall_grade']

        # Determine status emoji
        if score >= 80:
            status = "✅ PASS"
        elif score >= 70:
            status = "⚠️ ACCEPTABLE"
        else:
            status = "❌ NEEDS IMPROVEMENT"

        lines = [
            "## Executive Summary",
            "",
            f"### Overall Quality Score: **{score}/100** ({grade})",
            "",
            f"**Status:** {status}",
            "",
            f"- Total Sections Evaluated: {overall_stats['section_count']}",
            f"- Sections Below Threshold (75): {len(overall_stats['sections_below_threshold'])}",
            f"- Average Hallucination Risk: {overall_stats['avg_hallucination_risk']}",
            f"- Total Issues Identified: {overall_stats['total_issues']}",
            f"- Total Recommendations: {overall_stats['total_suggestions']}",
            "",
            "---",
            ""
        ]
        return lines

    def _generate_score_breakdown(self, overall_stats: Dict) -> List[str]:
        """Generate score breakdown section"""
        lines = [
            "## Quality Metrics Overview",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Overall Score | {overall_stats['overall_score']}/100 |",
            f"| Grade | {overall_stats['overall_grade']} |",
            f"| Hallucination Risk | {overall_stats['avg_hallucination_risk']} |",
            f"| Issues Found | {overall_stats['total_issues']} |",
            f"| Recommendations | {overall_stats['total_suggestions']} |",
            "",
            "---",
            ""
        ]
        return lines

    def _generate_section_evaluations(self, evaluation_results: Dict) -> List[str]:
        """Generate detailed section-by-section evaluations"""
        lines = [
            "## Section-by-Section Evaluation",
            ""
        ]

        for section_name, result in evaluation_results.items():
            score = result.get('score', 0)
            grade = result.get('grade', 'N/A')
            hallucination_risk = result.get('hallucination_risk', 'UNKNOWN')

            # Section header
            lines.extend([
                f"### {section_name}",
                "",
                f"**Score:** {score}/100 ({grade})  ",
                f"**Hallucination Risk:** {hallucination_risk}",
                ""
            ])

            # Detailed checks (if available)
            detailed_checks = result.get('detailed_checks', {})
            if detailed_checks:
                lines.append("**Quality Checks:**")
                lines.append("")
                lines.append("| Check | Score | Status |")
                lines.append("|-------|-------|--------|")

                for check_name, check_result in detailed_checks.items():
                    check_score = check_result.get('score', 0)
                    status = "✓" if check_score >= 75 else "⚠"
                    display_name = check_name.replace('_', ' ').title()
                    lines.append(f"| {display_name} | {check_score}/100 | {status} |")

                lines.append("")

            # Issues
            issues = result.get('issues', [])
            if issues:
                lines.append("**Issues:**")
                lines.append("")
                for issue in issues[:5]:  # Limit to 5 issues per section
                    lines.append(f"- ⚠️ {issue}")
                if len(issues) > 5:
                    lines.append(f"- *...and {len(issues) - 5} more issues*")
                lines.append("")

            # Suggestions
            suggestions = result.get('suggestions', [])
            if suggestions:
                lines.append("**Recommendations:**")
                lines.append("")
                for suggestion in suggestions[:5]:  # Limit to 5 suggestions
                    lines.append(f"- 💡 {suggestion}")
                if len(suggestions) > 5:
                    lines.append(f"- *...and {len(suggestions) - 5} more recommendations*")
                lines.append("")

            # Compliance check (if available)
            compliance = result.get('compliance_check', {})
            if compliance:
                compliance_level = compliance.get('level', 'UNKNOWN')
                lines.append(f"**Compliance Level:** {compliance_level}")
                lines.append("")

            lines.extend(["---", ""])

        return lines

    def _generate_issues_summary(self, evaluation_results: Dict) -> List[str]:
        """Generate summary of all critical issues"""
        lines = [
            "## Critical Issues Summary",
            ""
        ]

        # Collect high-priority issues
        high_priority_issues = []

        for section_name, result in evaluation_results.items():
            # High hallucination risk
            if result.get('hallucination_risk') == 'HIGH':
                high_priority_issues.append(f"**[{section_name}]** HIGH hallucination risk detected")

            # Low score
            if result.get('score', 0) < 60:
                high_priority_issues.append(f"**[{section_name}]** Low quality score ({result.get('score', 0)}/100)")

            # Major compliance issues
            compliance = result.get('compliance_check', {})
            if compliance.get('level') == 'MAJOR ISSUES':
                high_priority_issues.append(f"**[{section_name}]** Major compliance issues detected")

        if high_priority_issues:
            lines.append("**High Priority Issues Requiring Immediate Attention:**")
            lines.append("")
            for issue in high_priority_issues:
                lines.append(f"- 🚨 {issue}")
            lines.append("")
        else:
            lines.append("✅ No critical issues detected.")
            lines.append("")

        lines.extend(["---", ""])
        return lines

    def _generate_recommendations(self, evaluation_results: Dict, overall_stats: Dict) -> List[str]:
        """Generate prioritized recommendations"""
        lines = [
            "## Recommended Actions",
            ""
        ]

        recommendations = []

        # Based on overall score
        if overall_stats['overall_score'] < 70:
            recommendations.append(("HIGH", "Document requires significant revision before use"))
        elif overall_stats['overall_score'] < 80:
            recommendations.append(("MEDIUM", "Address identified issues to improve document quality"))

        # Based on hallucination risk
        if overall_stats['avg_hallucination_risk'] == 'HIGH':
            recommendations.append(("HIGH", "Review and verify all factual claims against source documents"))

        # Based on sections below threshold
        if len(overall_stats['sections_below_threshold']) > 0:
            sections_list = ', '.join(overall_stats['sections_below_threshold'])
            recommendations.append(("MEDIUM", f"Revise sections: {sections_list}"))

        # Compliance issues
        for section_name, result in evaluation_results.items():
            compliance = result.get('compliance_check', {})
            if compliance.get('level') == 'MAJOR ISSUES':
                recommendations.append(("HIGH", f"Address compliance violations in {section_name}"))

        # Add default if none
        if not recommendations:
            recommendations.append(("LOW", "Document meets quality standards - proceed with final review"))

        # Format recommendations by priority
        for priority in ['HIGH', 'MEDIUM', 'LOW']:
            priority_recs = [rec for p, rec in recommendations if p == priority]
            if priority_recs:
                priority_emoji = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}[priority]
                lines.append(f"### {priority_emoji} {priority} Priority")
                lines.append("")
                for rec in priority_recs:
                    lines.append(f"- {rec}")
                lines.append("")

        lines.extend(["---", ""])
        return lines

    def _generate_footer(self) -> List[str]:
        """Generate report footer"""
        lines = [
            "",
            "---",
            "",
            "*This evaluation report was generated automatically by the Quality Agent.*",
            "*Scores are based on: hallucination detection, vague language, citations, compliance, and completeness.*",
            ""
        ]
        return lines
