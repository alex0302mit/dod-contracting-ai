"""
Document Data Extractor

Extract structured data from generated acquisition documents.
"""

import re
from typing import Dict, List, Optional, Any


class DocumentDataExtractor:
    """Extract key data from generated documents for cross-referencing"""

    def extract_igce_data(self, content: str) -> Dict[str, Any]:
        """
        Extract key data from IGCE document

        Returns dict with:
            - total_cost: float
            - total_cost_formatted: str
            - base_year_cost: float
            - option_year_costs: List[float]
            - period_of_performance: str
            - labor_categories: List[Dict]
            - cost_breakdown: Dict
        """
        return {
            'total_cost': self._extract_total_cost(content),
            'total_cost_formatted': self._extract_total_cost_formatted(content),
            'base_year_cost': self._extract_base_year_cost(content),
            'option_year_costs': self._extract_option_year_costs(content),
            'period_of_performance': self._extract_period(content),
            'labor_categories_count': self._count_labor_categories(content),
            'cost_breakdown': self._extract_cost_breakdown(content)
        }

    def extract_pws_data(self, content: str) -> Dict[str, Any]:
        """
        Extract key data from PWS document

        Returns dict with:
            - performance_requirements: List[Dict]
            - deliverables: List[str]
            - period_of_performance: str
            - acceptance_criteria: List[str]
        """
        return {
            'performance_requirements': self._extract_performance_requirements(content),
            'deliverables': self._extract_deliverables(content),
            'period_of_performance': self._extract_period(content),
            'acceptance_criteria': self._extract_acceptance_criteria(content)
        }

    def extract_acquisition_plan_data(self, content: str) -> Dict[str, Any]:
        """
        Extract key data from Acquisition Plan

        Returns dict with:
            - total_cost: float
            - total_cost_formatted: str
            - contract_type: str
            - milestones: List[Dict]
            - acquisition_strategy: str
        """
        return {
            'total_cost': self._extract_total_cost(content),
            'total_cost_formatted': self._extract_total_cost_formatted(content),
            'contract_type': self._extract_contract_type(content),
            'period_of_performance': self._extract_period(content),
            'milestones_count': self._count_milestones(content),
            'acquisition_strategy': self._extract_acquisition_strategy(content)
        }

    # ========== Private Extraction Methods ==========

    def _extract_total_cost(self, content: str) -> Optional[float]:
        """Extract total cost as a number"""
        patterns = [
            r'Total Program Cost\*\*:\s*\$\s?([\d,]+(?:\.\d{2})?)',
            r'\*\*Total Program Cost\*\*:\s*\$\s?([\d,]+(?:\.\d{2})?)',
            r'Estimated Total Cost\*\*:\s*\$\s?([\d,]+(?:\.\d{2})?)',
            r'\| \*\*TOTAL\*\* \|[^|]*\|[^|]*\|[^|]*\| \*\*\$\s?([\d,]+)\*\*',
            r'(?:Total.*Cost|Grand Total).*?\$\s?([\d,]+(?:\.\d{2})?)',
            r'\*\*Total\*\*.*?\$\s?([\d,]+(?:\.\d{2})?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                cost_str = match.group(1).replace(',', '')
                try:
                    return float(cost_str)
                except ValueError:
                    continue

        return None

    def _extract_total_cost_formatted(self, content: str) -> Optional[str]:
        """Extract total cost as formatted string"""
        total_cost = self._extract_total_cost(content)
        if total_cost:
            return f"${total_cost:,.2f}"
        return None

    def _extract_base_year_cost(self, content: str) -> Optional[float]:
        """Extract base year cost"""
        patterns = [
            r'Base Year.*?\$?([\d,]+(?:\.\d{2})?)',
            r'FY\d{4}.*?Base.*?\$?([\d,]+(?:\.\d{2})?)',
            r'\| Base \|.*?\$?([\d,]+(?:\.\d{2})?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                cost_str = match.group(1).replace(',', '')
                try:
                    return float(cost_str)
                except ValueError:
                    continue

        return None

    def _extract_option_year_costs(self, content: str) -> List[float]:
        """Extract all option year costs"""
        costs = []

        # Look for Option Year 1, Option Year 2, etc.
        for i in range(1, 6):  # Check up to 5 option years
            patterns = [
                rf'Option.*?{i}.*?\$?([\d,]+(?:\.\d{{2}})?)',
                rf'FY\d{{4}}.*?Opt.*?{i}.*?\$?([\d,]+(?:\.\d{{2}})?)',
                rf'\| Opt {i} \|.*?\$?([\d,]+(?:\.\d{{2}})?)',
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    cost_str = match.group(1).replace(',', '')
                    try:
                        costs.append(float(cost_str))
                        break  # Found this option year, move to next
                    except ValueError:
                        continue

        return costs

    def _extract_period(self, content: str) -> Optional[str]:
        """Extract period of performance"""
        patterns = [
            r'Period of Performance.*?[:\-]\s*([^\n]+)',
            r'PoP.*?[:\-]\s*([^\n]+)',
            r'Duration.*?[:\-]\s*([^\n]+)',
            r'(\d+)\s*months?',
            r'(\d+)\s*years?',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                period = match.group(1).strip()
                # Clean up common formatting
                period = period.replace('**', '').replace('*', '')
                return period

        return None

    def _extract_contract_type(self, content: str) -> Optional[str]:
        """Extract contract type"""
        patterns = [
            r'Contract Type.*?[:\-]\s*([^\n]+)',
            r'Type of Contract.*?[:\-]\s*([^\n]+)',
            r'\*\*Contract Type\*\*.*?[:\-]?\s*([^\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                contract_type = match.group(1).strip()
                # Clean up
                contract_type = contract_type.replace('**', '').replace('*', '')
                # Common contract types
                if 'FFP' in contract_type or 'Firm Fixed Price' in contract_type:
                    return 'Firm Fixed Price (FFP)'
                elif 'CPFF' in contract_type:
                    return 'Cost Plus Fixed Fee (CPFF)'
                elif 'T&M' in contract_type or 'Time and Material' in contract_type:
                    return 'Time and Materials (T&M)'
                return contract_type

        return None

    def _count_labor_categories(self, content: str) -> int:
        """Count number of labor categories in IGCE"""
        # Look for labor category tables
        labor_section_match = re.search(
            r'Labor Categories.*?\n(.*?)(?:\n\n|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )

        if labor_section_match:
            section = labor_section_match.group(1)
            # Count table rows (lines starting with |)
            rows = [line for line in section.split('\n') if line.strip().startswith('|')]
            # Subtract header rows (usually 2)
            return max(0, len(rows) - 2)

        return 0

    def _extract_cost_breakdown(self, content: str) -> Dict[str, float]:
        """Extract cost breakdown by category"""
        breakdown = {}

        categories = [
            'Labor',
            'Hardware',
            'Software',
            'Cloud',
            'Travel',
            'Training',
            'ODCs',
            'Other Direct Costs'
        ]

        for category in categories:
            pattern = rf'{category}.*?\$?([\d,]+(?:\.\d{{2}})?)'
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                cost_str = match.group(1).replace(',', '')
                try:
                    breakdown[category] = float(cost_str)
                except ValueError:
                    continue

        return breakdown

    def _extract_performance_requirements(self, content: str) -> List[Dict[str, str]]:
        """Extract performance requirements from PWS"""
        requirements = []

        # Look for performance requirements section
        perf_section_match = re.search(
            r'Performance Requirements.*?\n(.*?)(?:\n##|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )

        if perf_section_match:
            section = perf_section_match.group(1)

            # Look for patterns like "System Availability: 99.5%"
            # or "- **Availability**: ≥99.5%"
            patterns = [
                r'\*\*([^:]+)\*\*[:\-]\s*([^\n]+)',
                r'-\s*([^:]+):\s*([^\n]+)',
                r'([^:]+):\s*≥?([\d.]+%)',
            ]

            for pattern in patterns:
                matches = re.finditer(pattern, section)
                for match in matches:
                    name = match.group(1).strip()
                    value = match.group(2).strip()
                    requirements.append({
                        'name': name,
                        'requirement': value
                    })

        return requirements

    def _extract_deliverables(self, content: str) -> List[str]:
        """Extract deliverables list"""
        deliverables = []

        # Look for deliverables section
        deliv_section_match = re.search(
            r'Deliverables.*?\n(.*?)(?:\n##|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )

        if deliv_section_match:
            section = deliv_section_match.group(1)

            # Extract list items
            list_items = re.findall(r'[-•]\s*([^\n]+)', section)
            deliverables.extend([item.strip() for item in list_items])

        return deliverables

    def _extract_acceptance_criteria(self, content: str) -> List[str]:
        """Extract acceptance criteria"""
        criteria = []

        # Look for acceptance criteria section
        accept_section_match = re.search(
            r'Acceptance Criteria.*?\n(.*?)(?:\n##|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )

        if accept_section_match:
            section = accept_section_match.group(1)

            # Extract list items
            list_items = re.findall(r'[-•]\s*([^\n]+)', section)
            criteria.extend([item.strip() for item in list_items])

        return criteria

    def _count_milestones(self, content: str) -> int:
        """Count number of milestones in acquisition plan"""
        # Look for milestone table
        milestone_section_match = re.search(
            r'Milestones.*?\n(.*?)(?:\n\n|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )

        if milestone_section_match:
            section = milestone_section_match.group(1)
            # Count table rows
            rows = [line for line in section.split('\n') if line.strip().startswith('|')]
            return max(0, len(rows) - 2)

        return 0

    def _extract_acquisition_strategy(self, content: str) -> Optional[str]:
        """Extract acquisition strategy summary"""
        patterns = [
            r'Acquisition Strategy.*?[:\-]\s*([^\n]+)',
            r'Strategy.*?[:\-]\s*([^\n]+)',
            r'\*\*Acquisition Strategy\*\*.*?\n\n(.*?)(?:\n\n|\Z)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                strategy = match.group(1).strip()
                # Limit to first 200 characters
                if len(strategy) > 200:
                    strategy = strategy[:200] + '...'
                return strategy

        return None

    def generate_igce_summary(self, igce_data: Dict) -> str:
        """
        Generate a human-readable summary of IGCE for inclusion in other documents

        Args:
            igce_data: Extracted IGCE data dict

        Returns:
            Formatted summary paragraph
        """
        total_cost = igce_data.get('total_cost_formatted', 'TBD')
        pop = igce_data.get('period_of_performance', 'TBD')
        base_cost = igce_data.get('base_year_cost')
        option_costs = igce_data.get('option_year_costs', [])
        labor_count = igce_data.get('labor_categories_count', 0)

        summary_parts = [
            f"The Independent Government Cost Estimate (IGCE) projects a total program cost of {total_cost}"
        ]

        if pop and pop != 'TBD':
            summary_parts.append(f"over {pop}")

        summary = ' '.join(summary_parts) + '.'

        # Add cost breakdown if available
        if base_cost and option_costs:
            summary += f" This includes a base year cost of ${base_cost:,.2f}"
            if len(option_costs) > 0:
                summary += f" and {len(option_costs)} option year(s)"
            summary += '.'

        # Add labor categories if available
        if labor_count > 0:
            summary += f" The estimate is based on {labor_count} labor categories and includes hardware, software, and operations costs."

        # Add reference
        summary += " See Attachment A for complete IGCE documentation."

        return summary


if __name__ == '__main__':
    # Example usage
    extractor = DocumentDataExtractor()

    # Test IGCE extraction
    sample_igce = """
    # IGCE - ALMS

    **Total Program Cost**: $2,847,500

    ## Cost Breakdown
    | Year | Labor | Hardware | Software | Total |
    |------|-------|----------|----------|-------|
    | Base Year | $1,000,000 | $150,000 | $95,000 | $1,245,000 |
    | Option Year 1 | $700,000 | $50,000 | $51,250 | $801,250 |
    | Option Year 2 | $700,000 | $50,000 | $51,250 | $801,250 |

    **Period of Performance**: 36 months
    """

    igce_data = extractor.extract_igce_data(sample_igce)
    print("IGCE Data Extracted:")
    print(f"  Total Cost: {igce_data['total_cost_formatted']}")
    print(f"  Base Year: ${igce_data['base_year_cost']:,.2f}")
    print(f"  Option Years: {len(igce_data['option_year_costs'])}")
    print(f"  Period: {igce_data['period_of_performance']}")

    print("\nIGCE Summary:")
    summary = extractor.generate_igce_summary(igce_data)
    print(summary)
