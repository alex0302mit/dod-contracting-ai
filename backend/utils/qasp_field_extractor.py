"""
QASP Field Extractor: Extract performance requirements from PWS for QASP generation
"""

import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime


class QASPFieldExtractor:
    """
    Extract performance requirements from PWS documents for QASP generation

    Extracts:
    - Performance objectives and standards
    - Performance metrics and KPIs
    - Deliverables and acceptance criteria
    - Quality requirements
    - Service level agreements (SLAs)
    """

    def __init__(self):
        self.surveillance_methods = [
            "100% Inspection",
            "Random Sampling",
            "Periodic Surveillance",
            "Observation",
            "Customer Feedback",
            "Automated Monitoring",
            "Desk Review"
        ]

    def extract_from_pws(self, pws_path: str) -> Dict:
        """
        Extract QASP-relevant data from PWS markdown file

        Args:
            pws_path: Path to PWS markdown file

        Returns:
            Dictionary with extracted QASP data
        """
        with open(pws_path, 'r', encoding='utf-8') as f:
            content = f.read()

        qasp_data = {
            'contract_info': self._extract_contract_info(content),
            'performance_requirements': self._extract_performance_requirements(content),
            'deliverables': self._extract_deliverables(content),
            'performance_standards': self._extract_performance_standards(content),
            'quality_metrics': self._extract_quality_metrics(content),
            'sla_requirements': self._extract_sla_requirements(content),
            'government_roles': self._extract_government_roles(content)
        }

        return qasp_data

    def _extract_contract_info(self, content: str) -> Dict:
        """Extract basic contract information"""
        info = {}

        # Program name
        match = re.search(r'##\s*(.+?)(?:\n|$)', content)
        if match:
            info['program_name'] = match.group(1).strip()

        # Organization
        match = re.search(r'\*\*Organization:\*\*\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        if match:
            info['organization'] = match.group(1).strip()

        # Date
        match = re.search(r'\*\*Date:\*\*\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        if match:
            info['date'] = match.group(1).strip()

        # Author (potential COR)
        match = re.search(r'\*\*Author:\*\*\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        if match:
            info['author'] = match.group(1).strip()

        # Period of performance
        match = re.search(r'(\d+)\s*months?', content, re.IGNORECASE)
        if match:
            info['period_of_performance'] = f"{match.group(1)} months"

        return info

    def _extract_performance_requirements(self, content: str) -> List[Dict]:
        """
        Extract performance requirements from PWS

        Returns list of requirements with:
        - Section/paragraph reference
        - Performance objective
        - Performance standard
        - Measurable criteria
        """
        requirements = []

        # Look for sections with performance language
        performance_patterns = [
            r'##\s*\d+\.?\s*(.+?Performance.+?)(?:\n\n|\n###)',
            r'##\s*\d+\.?\s*(.+?Requirements?.+?)(?:\n\n|\n###)',
            r'##\s*\d+\.?\s*(.+?Standards?.+?)(?:\n\n|\n###)'
        ]

        section_num = 1
        for pattern in performance_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                section_content = match.group(0)

                # Extract metrics from this section
                metrics = self._find_metrics_in_text(section_content)

                if metrics:
                    for metric in metrics:
                        requirements.append({
                            'pws_paragraph': f"{section_num}.{len(requirements)+1}",
                            'performance_objective': self._extract_objective(section_content),
                            'performance_standard': metric['standard'],
                            'measurable_criteria': metric['value'],
                            'section_text': section_content[:200]
                        })

                section_num += 1

        # If no specific performance sections found, create generic ones
        if not requirements:
            requirements = self._create_default_requirements(content)

        return requirements

    def _extract_performance_standards(self, content: str) -> List[Dict]:
        """Extract performance standards with specific metrics"""
        standards = []

        # Pattern: "X% of Y" or "≥X%" or ">X seconds"
        metric_patterns = [
            r'(\d+\.?\d*)\s*%\s*(?:of|or\s+(?:higher|greater))',
            r'[≥>]\s*(\d+\.?\d*)\s*%',
            r'<\s*(\d+\.?\d*)\s*(?:seconds?|hours?|days?)',
            r'(\d+\.?\d*)\s*(?:hours?|days?|months?)',
            r'within\s+(\d+)\s+(?:business\s+)?(?:hours?|days?)'
        ]

        for pattern in metric_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                context = self._get_context(content, match.start(), 100)
                standards.append({
                    'value': match.group(1),
                    'metric': match.group(0),
                    'context': context
                })

        return standards

    def _extract_deliverables(self, content: str) -> List[Dict]:
        """Extract deliverables that require QASP surveillance"""
        deliverables = []

        # Look for deliverables section
        deliverable_section = re.search(
            r'##\s*.*?Deliverables?.*?\n(.+?)(?:\n##|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if deliverable_section:
            section_text = deliverable_section.group(1)

            # Find bulleted or numbered items
            items = re.findall(
                r'[-•*]\s*(.+?)(?:\n(?:[-•*]|\n|$))',
                section_text,
                re.DOTALL
            )

            for item in items:
                deliverable = {
                    'title': item.strip()[:100],
                    'full_text': item.strip(),
                    'surveillance_method': self._recommend_surveillance_method(item)
                }
                deliverables.append(deliverable)

        return deliverables

    def _extract_quality_metrics(self, content: str) -> List[Dict]:
        """Extract quality and acceptance criteria"""
        metrics = []

        # Look for quality-related language
        quality_patterns = [
            r'quality\s+(?:score|rating|level).*?(\d+\.?\d*)',
            r'accuracy.*?(\d+\.?\d*)\s*%',
            r'defect\s+rate.*?(\d+\.?\d*)\s*%',
            r'customer\s+satisfaction.*?(\d+\.?\d*)',
            r'acceptable\s+quality\s+level.*?(\d+\.?\d*)'
        ]

        for pattern in quality_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                metrics.append({
                    'type': 'quality',
                    'metric': match.group(0),
                    'value': match.group(1),
                    'context': self._get_context(content, match.start(), 80)
                })

        return metrics

    def _extract_sla_requirements(self, content: str) -> List[Dict]:
        """Extract Service Level Agreement requirements"""
        slas = []

        # Common SLA patterns
        sla_patterns = [
            r'(\d+\.?\d*)\s*%\s*(?:uptime|availability)',
            r'response\s+time.*?(\d+)\s*(?:seconds?|minutes?|hours?)',
            r'resolution\s+time.*?(\d+)\s*(?:hours?|days?)',
            r'system\s+availability.*?(\d+\.?\d*)\s*%'
        ]

        for pattern in sla_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                slas.append({
                    'requirement': match.group(0),
                    'value': match.group(1),
                    'context': self._get_context(content, match.start(), 100)
                })

        return slas

    def _extract_government_roles(self, content: str) -> Dict:
        """Extract government personnel information for QASP roles"""
        roles = {}

        # Look for government-furnished resources or points of contact
        gov_section = re.search(
            r'##\s*.*?(?:Government|Point of Contact).*?\n(.+?)(?:\n##|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if gov_section:
            section_text = gov_section.group(1)

            # Extract names and roles
            name_matches = re.findall(
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)',
                section_text
            )

            roles['potential_cor'] = name_matches[0] if name_matches else None

        return roles

    def _find_metrics_in_text(self, text: str) -> List[Dict]:
        """Find quantifiable metrics in text"""
        metrics = []

        # Look for tables or structured metrics
        table_pattern = r'\|(.+?)\|(.+?)\|'
        matches = re.finditer(table_pattern, text)

        for match in matches:
            if any(word in match.group(0).lower() for word in ['metric', 'standard', 'requirement']):
                metrics.append({
                    'standard': match.group(1).strip(),
                    'value': match.group(2).strip()
                })

        # Look for percentage-based metrics
        percent_pattern = r'(\d+\.?\d*)\s*%'
        for match in re.finditer(percent_pattern, text):
            context = self._get_context(text, match.start(), 50)
            metrics.append({
                'standard': context,
                'value': f"{match.group(1)}%"
            })

        return metrics[:10]  # Limit to top 10 metrics per section

    def _create_default_requirements(self, content: str) -> List[Dict]:
        """Create default requirements if none found"""
        requirements = []

        # Extract all performance standards found
        standards = self._extract_performance_standards(content)

        for i, std in enumerate(standards[:10], 1):
            requirements.append({
                'pws_paragraph': f"PWS {i}",
                'performance_objective': std['context'][:80],
                'performance_standard': std['metric'],
                'measurable_criteria': std['value'],
                'section_text': std['context']
            })

        return requirements

    def _extract_objective(self, text: str) -> str:
        """Extract the performance objective from section text"""
        # Take first sentence or first 150 characters
        sentences = re.split(r'[.!?]\s+', text)
        if sentences:
            objective = sentences[0].strip()
            # Clean up markdown
            objective = re.sub(r'[#*_]', '', objective)
            return objective[:150]
        return text[:150]

    def _recommend_surveillance_method(self, deliverable_text: str) -> str:
        """
        Recommend appropriate surveillance method based on deliverable type

        Returns:
            One of the standard surveillance methods
        """
        text_lower = deliverable_text.lower()

        if 'report' in text_lower or 'document' in text_lower:
            return "Desk Review"
        elif 'system' in text_lower or 'software' in text_lower:
            return "Automated Monitoring"
        elif 'training' in text_lower or 'meeting' in text_lower:
            return "Observation"
        elif 'satisfaction' in text_lower or 'feedback' in text_lower:
            return "Customer Feedback"
        elif 'test' in text_lower or 'inspection' in text_lower:
            return "100% Inspection"
        else:
            return "Periodic Surveillance"

    def _get_context(self, text: str, position: int, chars: int = 100) -> str:
        """Get surrounding context for a match"""
        start = max(0, position - chars // 2)
        end = min(len(text), position + chars // 2)
        context = text[start:end].strip()
        # Clean up markdown
        context = re.sub(r'[#*_]', '', context)
        return context

    def generate_aql_recommendation(self, requirement: Dict) -> Tuple[str, str]:
        """
        Generate Acceptable Quality Level (AQL) recommendation

        Args:
            requirement: Performance requirement dictionary

        Returns:
            Tuple of (AQL percentage, AQL description)
        """
        # Critical requirements (zero tolerance)
        if any(word in str(requirement).lower() for word in ['security', 'safety', 'classified']):
            return ("0%", "Zero tolerance - any deficiency is unacceptable")

        # High importance (low tolerance)
        elif any(word in str(requirement).lower() for word in ['system', 'availability', 'data']):
            return ("2%", "No more than 2% defect rate per measurement period")

        # Medium importance (moderate tolerance)
        elif any(word in str(requirement).lower() for word in ['response', 'delivery', 'performance']):
            return ("5%", "No more than 5% defect rate per measurement period")

        # Lower importance (higher tolerance)
        else:
            return ("10%", "No more than 10% defect rate per measurement period")

    def generate_surveillance_frequency(self, requirement: Dict) -> str:
        """
        Recommend surveillance frequency based on requirement type

        Args:
            requirement: Performance requirement dictionary

        Returns:
            Recommended frequency (e.g., "Daily", "Weekly", "Monthly")
        """
        text = str(requirement).lower()

        if any(word in text for word in ['critical', 'security', 'safety']):
            return "Continuous"
        elif any(word in text for word in ['daily', 'real-time', 'availability']):
            return "Daily"
        elif any(word in text for word in ['weekly', 'incident', 'ticket']):
            return "Weekly"
        elif any(word in text for word in ['report', 'monthly', 'assessment']):
            return "Monthly"
        elif any(word in text for word in ['quarterly', 'survey', 'satisfaction']):
            return "Quarterly"
        else:
            return "Monthly"


# Example usage
if __name__ == "__main__":
    extractor = QASPFieldExtractor()

    pws_path = "outputs/pws/performance_work_statement.md"

    if Path(pws_path).exists():
        print("Extracting QASP data from PWS...\n")
        print("="*70)

        qasp_data = extractor.extract_from_pws(pws_path)

        print("\n1. Contract Information:")
        for key, value in qasp_data['contract_info'].items():
            print(f"   {key}: {value}")

        print(f"\n2. Performance Requirements: {len(qasp_data['performance_requirements'])}")
        for i, req in enumerate(qasp_data['performance_requirements'][:3], 1):
            print(f"   {i}. {req['performance_objective'][:80]}...")

        print(f"\n3. Deliverables: {len(qasp_data['deliverables'])}")
        for i, deliv in enumerate(qasp_data['deliverables'][:3], 1):
            print(f"   {i}. {deliv['title'][:60]}...")
            print(f"      Surveillance: {deliv['surveillance_method']}")

        print(f"\n4. Performance Standards: {len(qasp_data['performance_standards'])}")
        for i, std in enumerate(qasp_data['performance_standards'][:3], 1):
            print(f"   {i}. {std['metric']}")

        print(f"\n5. Quality Metrics: {len(qasp_data['quality_metrics'])}")
        print(f"6. SLA Requirements: {len(qasp_data['sla_requirements'])}")

        print("\n" + "="*70)
        print("✓ Extraction complete\n")

    else:
        print(f"PWS file not found: {pws_path}")
