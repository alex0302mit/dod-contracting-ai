"""
Vague Language Fixer: Automatically detects and reports vague terms
Helps improve quality scores by identifying imprecise language
"""

import re
from typing import Dict, List, Tuple


class VagueLanguageFixer:
    """
    Detects and reports vague language in DoD acquisition documents

    Usage:
        fixer = VagueLanguageFixer()
        findings = fixer.detect_vague_language(content)
        report = fixer.generate_report(findings)
    """

    # Vague terms mapped to replacement suggestions
    VAGUE_TERMS = {
        # Quantifiers
        'several': 'X [specify number with citation]',
        'many': 'X [specify number with citation]',
        'some': 'X [specify number with citation]',
        'various': 'X [specify number/types]',
        'numerous': 'X [specify count with citation]',
        'multiple': 'X [specify exact number]',
        'few': 'X [specify number]',

        # Approximations
        'approximately': 'estimated at X [cite source]',
        'around': 'approximately X [cite estimate source]',
        'roughly': 'estimated at X [cite source]',
        'about': 'X [provide exact figure or cite estimate]',

        # Qualifiers
        'significant': '[quantify: X% improvement, cite source]',
        'substantial': '[quantify amount with citation]',
        'considerable': '[quantify amount with citation]',
        'major': '[quantify scale/impact with citation]',
        'minor': '[quantify scale/impact with citation]',
        'adequate': '[define standard: X metric, cite requirement]',
        'sufficient': '[define criteria with citation]',
        'appropriate': '[define standard with citation]',
        'reasonable': '[define criteria with citation]',
        'satisfactory': '[define acceptance criteria with citation]',

        # Time references
        'timely': 'within X days/hours [cite SLA/requirement]',
        'prompt': 'within X business days [cite requirement]',
        'soon': '[specify date or timeframe]',
        'recent': '[specify date/quarter/year]',
        'upcoming': '[specify date/quarter]',
        'expeditiously': 'within X days [cite requirement]',

        # Uncertainty
        'may': '[specify probability/conditions]',
        'might': '[specify probability/conditions]',
        'could': '[specify conditions]',
        'possibly': '[specify likelihood percentage]',
        'potentially': '[specify conditions/probability]',

        # Quality descriptors
        'high quality': '[define quality standard: X metric, cite]',
        'low quality': '[define threshold: < X metric, cite]',
        'good': '[define standard with measurable criteria]',
        'better': '[quantify improvement: X → Y, cite baseline]',
        'improved': '[quantify improvement with baseline and target]',
        'enhanced': '[specify enhancement with metrics]',
        'optimized': '[define optimization target/metric]',
    }

    # Additional patterns to check
    VAGUE_PATTERNS = {
        r'\bas\s+needed\b': 'specify frequency/schedule [cite requirement]',
        r'\bas\s+required\b': 'specify exact requirement [cite source]',
        r'\bwhen\s+necessary\b': 'specify conditions/triggers',
        r'\bif\s+possible\b': 'specify conditions or remove qualifier',
        r'\bto\s+the\s+extent\s+practicable\b': 'specify criteria or remove',
    }

    def detect_vague_language(self, content: str) -> List[Dict]:
        """
        Detect all vague terms in content

        Args:
            content: Text to analyze

        Returns:
            List of findings with term, replacement, position, context
        """
        findings = []

        # Check for vague terms
        for vague_term, replacement in self.VAGUE_TERMS.items():
            pattern = rf'\b{re.escape(vague_term)}\b'
            matches = re.finditer(pattern, content, re.IGNORECASE)

            for match in matches:
                finding = self._create_finding(
                    content, match, vague_term, replacement
                )
                findings.append(finding)

        # Check for vague patterns
        for pattern, replacement in self.VAGUE_PATTERNS.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)

            for match in matches:
                finding = self._create_finding(
                    content, match, match.group(0), replacement
                )
                findings.append(finding)

        # Sort by position
        findings.sort(key=lambda x: x['position'])

        return findings

    def _create_finding(
        self,
        content: str,
        match: re.Match,
        term: str,
        replacement: str
    ) -> Dict:
        """Create a finding dictionary from a match"""
        context_start = max(0, match.start() - 60)
        context_end = min(len(content), match.end() + 60)
        context = content[context_start:context_end].replace('\n', ' ')

        line_num = content[:match.start()].count('\n') + 1

        return {
            'term': term,
            'replacement': replacement,
            'position': match.start(),
            'line': line_num,
            'context': f"...{context}...",
            'matched_text': match.group(0)
        }

    def generate_report(self, findings: List[Dict]) -> str:
        """
        Generate human-readable report of vague language issues

        Args:
            findings: List of findings from detect_vague_language

        Returns:
            Formatted report string
        """
        if not findings:
            return "✅ No vague language detected"

        report = []
        report.append("="*70)
        report.append(f"⚠️  VAGUE LANGUAGE DETECTED: {len(findings)} issue(s)")
        report.append("="*70)
        report.append("")

        for i, finding in enumerate(findings[:20], 1):  # Limit to top 20
            report.append(f"{i}. Line {finding['line']}: '{finding['matched_text']}'")
            report.append(f"   Replace with: {finding['replacement']}")
            report.append(f"   Context: {finding['context']}")
            report.append("")

        if len(findings) > 20:
            report.append(f"... and {len(findings) - 20} more issue(s)")
            report.append("")

        report.append("="*70)
        report.append("💡 TIP: Use specific numbers, dates, and inline citations")
        report.append("="*70)

        return "\n".join(report)

    def calculate_vague_score(self, content: str) -> Tuple[int, int]:
        """
        Calculate vague language score

        Args:
            content: Text to analyze

        Returns:
            Tuple of (score, vague_term_count)
        """
        findings = self.detect_vague_language(content)
        word_count = len(content.split())

        # Score based on density of vague terms
        if word_count == 0:
            return 0, 0

        vague_density = len(findings) / word_count * 100

        # Scoring scale
        if vague_density == 0:
            score = 100
        elif vague_density < 1:
            score = 90
        elif vague_density < 2:
            score = 75
        elif vague_density < 3:
            score = 60
        elif vague_density < 5:
            score = 40
        else:
            score = max(0, 20 - int(vague_density * 2))

        return score, len(findings)

    def get_suggestion(self, vague_term: str) -> str:
        """
        Get replacement suggestion for a vague term

        Args:
            vague_term: The vague term to look up

        Returns:
            Replacement suggestion or generic advice
        """
        return self.VAGUE_TERMS.get(
            vague_term.lower(),
            "Replace with specific, quantified language with citation"
        )


# Convenience function for quick analysis
def analyze_vague_language(content: str) -> Dict:
    """
    Quick analysis of vague language in content

    Args:
        content: Text to analyze

    Returns:
        Dictionary with score, findings, and report
    """
    fixer = VagueLanguageFixer()
    findings = fixer.detect_vague_language(content)
    score, count = fixer.calculate_vague_score(content)
    report = fixer.generate_report(findings)

    return {
        'score': score,
        'vague_term_count': count,
        'findings': findings,
        'report': report
    }


if __name__ == "__main__":
    # Test with sample text
    test_text = """
    The contractor should deliver several improvements to the system within a timely manner.
    Approximately 12-15 vendors were identified through market research. Performance will be
    adequate if the system achieves reasonable uptime standards. This represents a significant
    improvement over the legacy system.
    """

    print("Testing Vague Language Detector:\n")
    result = analyze_vague_language(test_text)
    print(result['report'])
    print(f"\nVague Language Score: {result['score']}/100")
    print(f"Vague Terms Found: {result['vague_term_count']}")
