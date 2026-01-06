"""
Evaluation tool for Market Research Reports
Checks for accuracy, hallucinations, vague language, citations, and legal risks
"""

import re
import anthropic
import os
from typing import Dict, List, Tuple


class ReportEvaluator:
    def __init__(self, api_key: str):
        """Initialize with Anthropic API key for advanced analysis"""
        self.client = anthropic.Anthropic(api_key=api_key)

    def evaluate_report(self, markdown_file: str, project_info: Dict) -> Dict:
        """
        Comprehensive evaluation of generated report

        Args:
            markdown_file: Path to generated markdown report
            project_info: Original project information dictionary

        Returns:
            Dictionary with evaluation results and scores
        """

        # Read the generated report
        with open(markdown_file, 'r') as f:
            report_content = f.read()

        print("="*70)
        print("MARKET RESEARCH REPORT EVALUATION")
        print("="*70)
        print()

        results = {}

        # 1. Accuracy Check
        print("1. Checking Accuracy & Factual Correctness...")
        results['accuracy'] = self.check_accuracy(report_content, project_info)

        # 2. Hallucination Detection
        print("\n2. Detecting Hallucinations...")
        results['hallucinations'] = self.detect_hallucinations(report_content, project_info)

        # 3. Vague Language Detection
        print("\n3. Checking for Vague Language...")
        results['vague_language'] = self.detect_vague_language(report_content)

        # 4. Citation Check
        print("\n4. Checking Citations & Sources...")
        results['citations'] = self.check_citations(report_content)

        # 5. Legal Risk Analysis
        print("\n5. Analyzing Legal & Regulatory Risks...")
        results['legal_risks'] = self.analyze_legal_risks(report_content)

        # 6. Completeness Check
        print("\n6. Checking Completeness...")
        results['completeness'] = self.check_completeness(report_content)

        # Calculate overall score
        results['overall_score'] = self.calculate_score(results)

        return results

    def check_accuracy(self, report: str, project_info: Dict) -> Dict:
        """Verify all input data appears correctly in output"""

        issues = []
        found_items = []
        missing_items = []

        # Key items to verify
        key_fields = [
            'program_name', 'author', 'organization', 'report_title',
            'budget', 'period_of_performance'
        ]

        for field in key_fields:
            if field in project_info:
                value = str(project_info[field])
                if value in report:
                    found_items.append(f"✓ {field}: '{value}'")
                else:
                    missing_items.append(f"✗ {field}: '{value}' NOT FOUND")
                    issues.append(f"Missing or incorrect {field}")

        # Display results
        for item in found_items:
            print(f"  {item}")

        if missing_items:
            print("\n  ⚠️  ISSUES FOUND:")
            for item in missing_items:
                print(f"  {item}")

        accuracy_score = (len(found_items) / len(key_fields)) * 100 if key_fields else 100

        return {
            'score': accuracy_score,
            'found': found_items,
            'missing': missing_items,
            'issues': issues
        }

    def detect_hallucinations(self, report: str, project_info: Dict) -> Dict:
        """Use Claude to detect potential hallucinations"""

        prompt = f"""You are evaluating a government market research report for factual accuracy.

PROJECT INFORMATION PROVIDED (Ground Truth):
{self._format_dict(project_info)}

GENERATED REPORT:
{report}

Analyze the report and identify:
1. Any specific facts, names, dates, or numbers that appear in the report but were NOT in the project information
2. Vendor names that were not mentioned in the project info
3. Specific statistics or data points that seem made up
4. Any technical claims not supported by the input

Format your response as:
HALLUCINATIONS FOUND:
- [List each potential hallucination with the specific text]

CONFIDENCE LEVEL: [High/Medium/Low] that hallucinations exist

If no hallucinations found, state: "No clear hallucinations detected."
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        analysis = response.content[0].text
        print(f"\n{analysis}")

        # Parse for hallucination count
        hallucination_lines = [line for line in analysis.split('\n') if line.strip().startswith('-')]
        hallucination_count = len(hallucination_lines)

        # Score: fewer hallucinations = higher score
        score = max(0, 100 - (hallucination_count * 10))

        return {
            'score': score,
            'count': hallucination_count,
            'analysis': analysis
        }

    def detect_vague_language(self, report: str) -> Dict:
        """Detect vague, non-specific language"""

        vague_patterns = [
            r'\bseveral\b',
            r'\bmany\b',
            r'\bsome\b',
            r'\ba few\b',
            r'\bnumerous\b',
            r'\bvarious\b',
            r'\bmultiple\b',
            r'\bsignificant\b',
            r'\bsubstantial\b',
            r'\bconsiderable\b',
            r'\bapproximately\b',
            r'\baround\b',
            r'\broughly\b',
        ]

        findings = []

        for pattern in vague_patterns:
            matches = re.finditer(pattern, report, re.IGNORECASE)
            for match in matches:
                # Get context (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(report), match.end() + 50)
                context = report[start:end].replace('\n', ' ')
                findings.append({
                    'word': match.group(),
                    'context': f"...{context}..."
                })

        print(f"  Found {len(findings)} instances of vague language")
        if findings:
            print("\n  Examples:")
            for i, finding in enumerate(findings[:5]):  # Show first 5
                print(f"    {i+1}. '{finding['word']}' in: {finding['context']}")
            if len(findings) > 5:
                print(f"    ... and {len(findings) - 5} more")

        # Score: fewer vague terms = higher score
        vague_ratio = len(findings) / max(1, len(report.split()))
        score = max(0, 100 - (vague_ratio * 10000))

        return {
            'score': score,
            'count': len(findings),
            'findings': findings
        }

    def check_citations(self, report: str) -> Dict:
        """Check for proper citations and source attribution"""

        # Look for citation patterns
        citation_patterns = [
            r'Per\s+[A-Z]+\s+#?\d+',  # Per RFI #123
            r'According to\s+[\w\s]+dated',  # According to ... dated
            r'Reference\s+#?\d+',  # Reference #123
            r'Source:\s*',  # Source:
            r'\(Ref\.',  # (Ref. ...)
            r'dated\s+\w+\s+\d+,?\s+\d{4}',  # dated March 15, 2025
        ]

        citations_found = []
        for pattern in citation_patterns:
            matches = re.finditer(pattern, report, re.IGNORECASE)
            for match in matches:
                start = max(0, match.start() - 30)
                end = min(len(report), match.end() + 50)
                context = report[start:end].replace('\n', ' ')
                citations_found.append(f"...{context}...")

        print(f"  Found {len(citations_found)} citation-like references")
        if citations_found:
            print("\n  Examples:")
            for i, citation in enumerate(citations_found[:3]):
                print(f"    {i+1}. {citation}")

        # Check for sections that should have citations
        sections_needing_citations = [
            'Market Research Conducted',
            'Industry Capabilities',
            'Commercial Opportunities'
        ]

        missing_citations = []
        for section in sections_needing_citations:
            if section in report:
                section_start = report.find(section)
                section_end = report.find('##', section_start + len(section))
                if section_end == -1:
                    section_end = len(report)
                section_text = report[section_start:section_end]

                has_citation = any(re.search(pattern, section_text, re.IGNORECASE)
                                 for pattern in citation_patterns)
                if not has_citation:
                    missing_citations.append(section)

        if missing_citations:
            print(f"\n  ⚠️  Sections missing citations: {', '.join(missing_citations)}")

        # Score based on citation presence
        score = (len(citations_found) / max(1, len(sections_needing_citations))) * 50
        score = min(100, score)  # Cap at 100

        return {
            'score': score,
            'citations_found': len(citations_found),
            'missing_in_sections': missing_citations,
            'examples': citations_found[:5]
        }

    def analyze_legal_risks(self, report: str) -> Dict:
        """Analyze for legal and regulatory risks"""

        prompt = f"""You are a government contracting legal expert reviewing a market research report for potential legal issues.

REPORT:
{report}

Analyze for these specific risks:
1. **Anti-competitive language** - Preferences for specific vendors, requirements that favor one company
2. **Unsupported claims** - Definitive statements without evidence ("only one vendor can...")
3. **Small business compliance** - Missing or inadequate small business analysis (required by FAR)
4. **Biased language** - Overly favorable descriptions of specific vendors
5. **Contract type justification** - Claims about contract type without proper basis
6. **FAR compliance** - Missing required elements per FAR Part 10

For each risk found, provide:
- **Risk Level**: HIGH/MEDIUM/LOW
- **Location**: Which section
- **Issue**: Specific problematic text
- **Recommendation**: How to fix

Format as:
RISK 1: [Risk Level]
Section: [section name]
Issue: [specific text]
Recommendation: [how to fix]

If no major risks found, state: "No significant legal risks detected."
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )

        analysis = response.content[0].text
        print(f"\n{analysis}")

        # Count risks by severity
        high_risks = len(re.findall(r'HIGH', analysis, re.IGNORECASE))
        medium_risks = len(re.findall(r'MEDIUM', analysis, re.IGNORECASE))
        low_risks = len(re.findall(r'LOW', analysis, re.IGNORECASE))

        # Score: penalize based on risk severity
        score = 100 - (high_risks * 30) - (medium_risks * 15) - (low_risks * 5)
        score = max(0, score)

        return {
            'score': score,
            'high_risks': high_risks,
            'medium_risks': medium_risks,
            'low_risks': low_risks,
            'analysis': analysis
        }

    def check_completeness(self, report: str) -> Dict:
        """Check if all required sections are present and substantive"""

        required_sections = [
            'Product/Service Description',
            'Background',
            'Performance Requirements',
            'Market Research Conducted',
            'Industry Capabilities',
            'Small Business Opportunities',
            'Commercial Opportunities',
            'Conclusions and Recommendations'
        ]

        found_sections = []
        missing_sections = []
        thin_sections = []

        for section in required_sections:
            if section in report:
                found_sections.append(section)

                # Check if section is substantive (more than 200 words)
                section_start = report.find(section)
                section_end = report.find('##', section_start + len(section))
                if section_end == -1:
                    section_end = len(report)
                section_text = report[section_start:section_end]
                word_count = len(section_text.split())

                if word_count < 200:
                    thin_sections.append(f"{section} ({word_count} words)")
                    print(f"  ⚠️  {section}: Only {word_count} words (recommend 200+)")
                else:
                    print(f"  ✓ {section}: {word_count} words")
            else:
                missing_sections.append(section)
                print(f"  ✗ {section}: MISSING")

        score = (len(found_sections) / len(required_sections)) * 100
        score = score - (len(thin_sections) * 5)  # Penalize thin sections
        score = max(0, score)

        return {
            'score': score,
            'found': found_sections,
            'missing': missing_sections,
            'thin': thin_sections
        }

    def calculate_score(self, results: Dict) -> Dict:
        """Calculate overall quality score"""

        weights = {
            'accuracy': 0.25,
            'hallucinations': 0.20,
            'vague_language': 0.15,
            'citations': 0.15,
            'legal_risks': 0.15,
            'completeness': 0.10
        }

        weighted_score = sum(
            results[key]['score'] * weights[key]
            for key in weights.keys()
        )

        # Grade
        if weighted_score >= 90:
            grade = 'A (Excellent)'
        elif weighted_score >= 80:
            grade = 'B (Good)'
        elif weighted_score >= 70:
            grade = 'C (Acceptable)'
        elif weighted_score >= 60:
            grade = 'D (Needs Improvement)'
        else:
            grade = 'F (Major Issues)'

        return {
            'score': round(weighted_score, 1),
            'grade': grade,
            'breakdown': {key: results[key]['score'] for key in weights.keys()}
        }

    def _format_dict(self, d: Dict) -> str:
        """Format dictionary for display"""
        return '\n'.join([f"- {k}: {v}" for k, v in d.items()])

    def generate_report(self, results: Dict, output_file: str = "evaluation_report.md"):
        """Generate a detailed evaluation report in markdown format"""

        with open(output_file, 'w') as f:
            f.write("# Market Research Report - Quality Evaluation\n\n")

            f.write(f"## Overall Score: {results['overall_score']['score']}/100\n")
            f.write(f"**Grade: {results['overall_score']['grade']}**\n\n")

            f.write("---\n\n")
            f.write("## Score Breakdown\n\n")
            for category, score in results['overall_score']['breakdown'].items():
                f.write(f"- **{category.replace('_', ' ').title()}**: {score:.1f}/100\n")

            f.write("\n---\n\n")
            f.write("## Detailed Findings\n\n")

            # Accuracy
            f.write("### 1. Accuracy & Factual Correctness\n\n")
            f.write(f"**Score**: {results['accuracy']['score']:.1f}/100\n\n")
            if results['accuracy']['issues']:
                f.write("**Issues Found**:\n")
                for issue in results['accuracy']['issues']:
                    f.write(f"- {issue}\n")
                f.write("\n")

            # Hallucinations
            f.write("### 2. Hallucination Detection\n\n")
            f.write(f"**Score**: {results['hallucinations']['score']:.1f}/100\n\n")
            f.write(f"**Potential hallucinations**: {results['hallucinations']['count']}\n\n")
            f.write(f"**Analysis**:\n\n{results['hallucinations']['analysis']}\n\n")

            # Vague Language
            f.write("### 3. Vague Language\n\n")
            f.write(f"**Score**: {results['vague_language']['score']:.1f}/100\n\n")
            f.write(f"**Instances found**: {results['vague_language']['count']}\n\n")

            # Citations
            f.write("### 4. Citations & Sources\n\n")
            f.write(f"**Score**: {results['citations']['score']:.1f}/100\n\n")
            f.write(f"**Citations found**: {results['citations']['citations_found']}\n\n")
            if results['citations']['missing_in_sections']:
                f.write(f"**Missing in sections**: {', '.join(results['citations']['missing_in_sections'])}\n\n")

            # Legal Risks
            f.write("### 5. Legal & Regulatory Risks\n\n")
            f.write(f"**Score**: {results['legal_risks']['score']:.1f}/100\n\n")
            f.write(f"- **High risks**: {results['legal_risks']['high_risks']}\n")
            f.write(f"- **Medium risks**: {results['legal_risks']['medium_risks']}\n")
            f.write(f"- **Low risks**: {results['legal_risks']['low_risks']}\n\n")
            f.write(f"**Analysis**:\n\n{results['legal_risks']['analysis']}\n\n")

            # Completeness
            f.write("### 6. Completeness\n\n")
            f.write(f"**Score**: {results['completeness']['score']:.1f}/100\n\n")
            f.write(f"**Sections found**: {len(results['completeness']['found'])}/8\n\n")
            if results['completeness']['missing']:
                f.write(f"**Missing sections**: {', '.join(results['completeness']['missing'])}\n\n")
            if results['completeness']['thin']:
                f.write(f"**Thin sections** (need more content):\n")
                for section in results['completeness']['thin']:
                    f.write(f"- {section}\n")
                f.write("\n")

            f.write("---\n\n")
            f.write("## Recommendations\n\n")

            recommendations = []

            if results['accuracy']['score'] < 80:
                recommendations.append("Review and correct factual inaccuracies")

            if results['hallucinations']['count'] > 0:
                recommendations.append("Remove or verify hallucinated facts")

            if results['vague_language']['count'] > 10:
                recommendations.append("Replace vague language with specific numbers and facts")

            if results['citations']['score'] < 50:
                recommendations.append("Add proper citations and source references")

            if results['legal_risks']['high_risks'] > 0:
                recommendations.append("⚠️ **ADDRESS HIGH-PRIORITY legal risks immediately**")

            if results['completeness']['missing']:
                recommendations.append("Add missing required sections")

            if recommendations:
                for i, rec in enumerate(recommendations, 1):
                    f.write(f"{i}. {rec}\n")
            else:
                f.write("✅ No major issues found. Document is ready for review.\n")

        print(f"\n\nDetailed evaluation report saved to: {output_file}")


def main():
    """Main execution"""
    import sys

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        return

    # Get markdown file path from command line or use default
    if len(sys.argv) > 1:
        markdown_file = sys.argv[1]
    else:
        markdown_file = 'filled_market_research_report.md'

    # Check if file exists
    if not os.path.exists(markdown_file):
        print(f"Error: File '{markdown_file}' not found")
        print("\nUsage: python evaluate_report.py [markdown_file]")
        print("Example: python evaluate_report.py filled_market_research_report.md")
        print("\nMake sure to run 'python run_market_research.py' first to generate the report.")
        return

    # Project info (should match what was used to generate report)
    project_info = {
        "program_name": "Advanced Logistics Management System (ALMS)",
        "author": "John Smith",
        "organization": "DOD/ARMY/LOGISTICS",
        "report_title": "Cloud-Based Inventory Management Services",
        "budget": "$2.5 million",
        "period_of_performance": "36 months (3 years)",
    }

    # Run evaluation
    evaluator = ReportEvaluator(api_key)
    results = evaluator.evaluate_report(
        markdown_file,
        project_info
    )

    # Print summary
    print("\n" + "="*70)
    print("FINAL SCORE")
    print("="*70)
    print(f"\nOverall Score: {results['overall_score']['score']}/100")
    print(f"Grade: {results['overall_score']['grade']}")
    print("\nBreakdown:")
    for category, score in results['overall_score']['breakdown'].items():
        print(f"  {category.replace('_', ' ').title()}: {score:.1f}/100")

    # Generate detailed report
    evaluator.generate_report(results)

    # Convert markdown to PDF
    print("\nConverting evaluation report to PDF...")
    try:
        from utils.convert_md_to_pdf import convert_markdown_to_pdf
        convert_markdown_to_pdf('evaluation_report.md', 'evaluation_report.pdf')
        print("✅ PDF evaluation report created: evaluation_report.pdf")
    except Exception as e:
        print(f"⚠️  Could not convert to PDF: {e}")
        print("You can manually convert evaluation_report.md to PDF if needed.")


if __name__ == "__main__":
    main()
