"""
Consistency Validation Framework

Provides fuzzy matching, format normalization, and intelligent comparison
for cross-document validation in acquisition document generation.

Features:
- Multi-pattern value extraction
- Field-type-aware normalization
- Fuzzy string matching with confidence scores
- Tolerance-based comparison
- Detailed validation reporting

Usage:
    validator = DocumentConsistencyValidator()
    validator.add_field('program_name', FieldType.TEXT, patterns=[...])
    report = validator.validate(doc1_content, doc2_content)
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import re


class FieldType(Enum):
    """Types of fields with specific normalization and comparison rules"""
    TEXT = "text"
    CURRENCY = "currency"
    DATE = "date"
    DURATION = "duration"
    PERCENTAGE = "percentage"
    IDENTIFIER = "identifier"
    ORGANIZATION = "organization"
    NUMBER = "number"


@dataclass
class FieldDefinition:
    """Definition of a field to validate across documents"""
    name: str
    field_type: FieldType
    patterns: List[str]
    required: bool = True
    tolerance: float = 0.85
    description: str = ""


@dataclass
class ValidationResult:
    """Result of validating a single field"""
    field_name: str
    status: str  # PASS, FAIL, NOT_FOUND
    confidence: float
    similarity: float
    doc1_value: Optional[str] = None
    doc2_value: Optional[str] = None
    normalized_v1: Optional[str] = None
    normalized_v2: Optional[str] = None
    method: str = ""
    reason: str = ""
    recommendation: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)


class ValueNormalizer:
    """Normalizes values based on field type for comparison"""

    @staticmethod
    def normalize_currency(value: str) -> float:
        """
        Normalize currency to numeric value in dollars

        Examples:
            "$45M" → 45000000.0
            "$45 million" → 45000000.0
            "$45,000,000" → 45000000.0
            "$2.5M" → 2500000.0
        """
        # Remove currency symbols and spaces
        clean = value.replace('$', '').replace(',', '').replace(' ', '').strip()

        # Handle suffixes
        multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}

        for suffix, multiplier in multipliers.items():
            if suffix in clean.upper():
                num = float(clean.upper().replace(suffix, '').replace('ILLION', ''))
                return num * multiplier

        # Check for "million", "billion" words
        if 'million' in clean.lower():
            num_match = re.search(r'[\d.]+', clean)
            if num_match:
                num = float(num_match.group())
                return num * 1000000

        if 'billion' in clean.lower():
            num_match = re.search(r'[\d.]+', clean)
            if num_match:
                num = float(num_match.group())
                return num * 1000000000

        # Try to parse as plain number
        try:
            return float(clean)
        except ValueError:
            raise ValueError(f"Could not parse currency value: {value}")

    @staticmethod
    def normalize_duration(value: str) -> int:
        """
        Normalize duration to months

        Examples:
            "36 months" → 36
            "3 years" → 36
            "1 Month" → 1
            "24-month" → 24
        """
        # Extract number
        num_match = re.search(r'(\d+)', value)
        if not num_match:
            raise ValueError(f"Could not find number in duration: {value}")

        num = int(num_match.group(1))

        # Determine unit
        if any(word in value.lower() for word in ['year', 'yr']):
            return num * 12  # Convert years to months
        elif any(word in value.lower() for word in ['month', 'mo']):
            return num

        return num  # Assume months if no unit

    @staticmethod
    def normalize_date(value: str) -> Optional[datetime]:
        """
        Normalize dates to datetime objects

        Examples:
            "10/04/2025" → datetime(2025, 10, 4)
            "October 4, 2025" → datetime(2025, 10, 4)
            "Oct 2025" → datetime(2025, 10, 1)
        """
        # Try multiple date formats
        formats = [
            '%m/%d/%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%B %Y',
            '%b %Y',
            '%Y-%m-%d',
        ]

        clean_value = value.strip()

        for fmt in formats:
            try:
                return datetime.strptime(clean_value, fmt)
            except ValueError:
                continue

        return None

    @staticmethod
    def normalize_text(value: str) -> str:
        """
        Normalize text for comparison

        Operations:
            - Remove markdown formatting (**text**, *text*)
            - Standardize whitespace
            - Convert to lowercase
            - Strip extra spaces
        """
        # Remove markdown bold/italic
        clean = re.sub(r'\*\*(.+?)\*\*', r'\1', value)
        clean = re.sub(r'\*(.+?)\*', r'\1', clean)

        # Standardize whitespace
        clean = ' '.join(clean.split())

        # Convert to lowercase for comparison
        clean = clean.lower()

        # Remove trailing punctuation
        clean = clean.rstrip('.,;:')

        return clean.strip()

    @staticmethod
    def normalize_percentage(value: str) -> float:
        """
        Normalize percentage to decimal (0.0 to 1.0)

        Examples:
            "12%" → 0.12
            "0.12" → 0.12
            "12.5%" → 0.125
        """
        clean = value.replace('%', '').replace(' ', '').strip()
        num = float(clean)

        # If greater than 1, assume it's a percentage (12 = 12%)
        if num > 1:
            return num / 100

        return num


class FuzzyMatcher:
    """Provides fuzzy string matching capabilities"""

    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """
        Calculate Levenshtein distance between two strings
        (minimum number of edits to transform s1 into s2)
        """
        if len(s1) < len(s2):
            return FuzzyMatcher.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Cost of insertions, deletions, or substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    @staticmethod
    def similarity_ratio(s1: str, s2: str) -> float:
        """
        Calculate similarity ratio (0.0 to 1.0)
        1.0 = identical, 0.0 = completely different
        """
        distance = FuzzyMatcher.levenshtein_distance(s1, s2)
        max_len = max(len(s1), len(s2))

        if max_len == 0:
            return 1.0

        return 1.0 - (distance / max_len)


class ValueExtractor:
    """Extracts values from document content using multiple patterns"""

    @staticmethod
    def extract_value(content: str, patterns: List[str], context_window: int = 100) -> Optional[Tuple[str, str, int]]:
        """
        Extract value from content using multiple patterns

        Returns:
            Tuple of (value, context, line_number) or None if not found
        """
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    # Try to get capture group
                    value = match.group(1).strip()
                except IndexError:
                    # No capture group, use whole match
                    value = match.group(0).strip()

                # Extract context around match
                start = max(0, match.start() - context_window)
                end = min(len(content), match.end() + context_window)
                context = content[start:end].strip()

                # Calculate line number
                line_num = content[:match.start()].count('\n') + 1

                return (value, context, line_num)

        return None


class ValueComparer:
    """Compares values based on field type with tolerance"""

    def __init__(self, normalizer: ValueNormalizer, fuzzy_matcher: FuzzyMatcher):
        self.normalizer = normalizer
        self.fuzzy_matcher = fuzzy_matcher

    def compare(self, value1: str, value2: str, field_type: FieldType, tolerance: float) -> Dict[str, Any]:
        """
        Compare two values based on field type

        Returns dictionary with:
            - match: bool
            - similarity: float
            - normalized_v1: str
            - normalized_v2: str
            - method: str
            - additional type-specific fields
        """
        if field_type == FieldType.TEXT or field_type == FieldType.ORGANIZATION:
            return self._compare_text(value1, value2, tolerance)
        elif field_type == FieldType.CURRENCY:
            return self._compare_currency(value1, value2, tolerance)
        elif field_type == FieldType.DURATION:
            return self._compare_duration(value1, value2, tolerance)
        elif field_type == FieldType.DATE:
            return self._compare_date(value1, value2, tolerance)
        elif field_type == FieldType.PERCENTAGE:
            return self._compare_percentage(value1, value2, tolerance)
        elif field_type == FieldType.NUMBER:
            return self._compare_number(value1, value2, tolerance)
        else:
            return self._compare_text(value1, value2, tolerance)

    def _compare_text(self, value1: str, value2: str, tolerance: float) -> Dict[str, Any]:
        """Compare text fields with fuzzy matching"""
        norm1 = self.normalizer.normalize_text(value1)
        norm2 = self.normalizer.normalize_text(value2)

        similarity = self.fuzzy_matcher.similarity_ratio(norm1, norm2)

        return {
            'match': similarity >= tolerance,
            'similarity': similarity,
            'normalized_v1': norm1,
            'normalized_v2': norm2,
            'method': 'fuzzy_text_match'
        }

    def _compare_currency(self, value1: str, value2: str, tolerance: float) -> Dict[str, Any]:
        """
        Compare currency values with numeric tolerance

        tolerance: Percentage difference allowed (e.g., 0.10 = 10%)
        """
        try:
            amount1 = self.normalizer.normalize_currency(value1)
            amount2 = self.normalizer.normalize_currency(value2)

            # Calculate percentage difference
            avg = (amount1 + amount2) / 2
            diff = abs(amount1 - amount2)
            pct_diff = diff / avg if avg > 0 else 0

            return {
                'match': pct_diff <= tolerance,
                'similarity': max(0, 1.0 - pct_diff),
                'normalized_v1': f"${amount1:,.2f}",
                'normalized_v2': f"${amount2:,.2f}",
                'difference': f"${diff:,.2f}",
                'pct_difference': f"{pct_diff*100:.1f}%",
                'method': 'currency_numeric_tolerance'
            }
        except Exception as e:
            return {
                'match': False,
                'similarity': 0.0,
                'error': str(e),
                'method': 'currency_numeric_tolerance'
            }

    def _compare_duration(self, value1: str, value2: str, tolerance: float) -> Dict[str, Any]:
        """Compare duration fields (exact match after normalization to months)"""
        try:
            months1 = self.normalizer.normalize_duration(value1)
            months2 = self.normalizer.normalize_duration(value2)

            return {
                'match': months1 == months2,
                'similarity': 1.0 if months1 == months2 else 0.0,
                'normalized_v1': f"{months1} months",
                'normalized_v2': f"{months2} months",
                'method': 'duration_exact_after_norm'
            }
        except Exception as e:
            return {
                'match': False,
                'similarity': 0.0,
                'error': str(e),
                'method': 'duration_exact_after_norm'
            }

    def _compare_date(self, value1: str, value2: str, tolerance: float) -> Dict[str, Any]:
        """Compare date fields (exact match or within tolerance days)"""
        try:
            date1 = self.normalizer.normalize_date(value1)
            date2 = self.normalizer.normalize_date(value2)

            if date1 is None or date2 is None:
                # Fallback to text comparison
                return self._compare_text(value1, value2, 0.90)

            diff_days = abs((date1 - date2).days)
            tolerance_days = 7  # Allow 7-day difference

            return {
                'match': diff_days <= tolerance_days,
                'similarity': 1.0 if diff_days == 0 else max(0, 1.0 - diff_days/30),
                'normalized_v1': date1.strftime('%m/%d/%Y'),
                'normalized_v2': date2.strftime('%m/%d/%Y'),
                'difference_days': diff_days,
                'method': 'date_comparison'
            }
        except Exception as e:
            return {
                'match': False,
                'similarity': 0.0,
                'error': str(e),
                'method': 'date_comparison'
            }

    def _compare_percentage(self, value1: str, value2: str, tolerance: float) -> Dict[str, Any]:
        """Compare percentage values"""
        try:
            pct1 = self.normalizer.normalize_percentage(value1)
            pct2 = self.normalizer.normalize_percentage(value2)

            diff = abs(pct1 - pct2)

            return {
                'match': diff <= tolerance,
                'similarity': max(0, 1.0 - diff),
                'normalized_v1': f"{pct1*100:.1f}%",
                'normalized_v2': f"{pct2*100:.1f}%",
                'difference': f"{diff*100:.1f}%",
                'method': 'percentage_comparison'
            }
        except Exception as e:
            return {
                'match': False,
                'similarity': 0.0,
                'error': str(e),
                'method': 'percentage_comparison'
            }

    def _compare_number(self, value1: str, value2: str, tolerance: float) -> Dict[str, Any]:
        """Compare numeric values with tolerance"""
        try:
            num1 = float(value1.replace(',', ''))
            num2 = float(value2.replace(',', ''))

            diff = abs(num1 - num2)
            avg = (num1 + num2) / 2
            pct_diff = diff / avg if avg > 0 else 0

            return {
                'match': pct_diff <= tolerance,
                'similarity': max(0, 1.0 - pct_diff),
                'normalized_v1': f"{num1:,.2f}",
                'normalized_v2': f"{num2:,.2f}",
                'difference': f"{diff:,.2f}",
                'method': 'numeric_comparison'
            }
        except Exception as e:
            return {
                'match': False,
                'similarity': 0.0,
                'error': str(e),
                'method': 'numeric_comparison'
            }


class DocumentConsistencyValidator:
    """
    Main validator class for cross-document consistency checking

    Usage:
        validator = DocumentConsistencyValidator()
        validator.add_field('program_name', FieldType.TEXT, [...patterns...])
        report = validator.validate(doc1_content, doc2_content)
    """

    def __init__(self):
        self.fields: Dict[str, FieldDefinition] = {}
        self.normalizer = ValueNormalizer()
        self.fuzzy_matcher = FuzzyMatcher()
        self.extractor = ValueExtractor()
        self.comparer = ValueComparer(self.normalizer, self.fuzzy_matcher)

    def add_field(
        self,
        name: str,
        field_type: FieldType,
        patterns: List[str],
        required: bool = True,
        tolerance: float = 0.85,
        description: str = ""
    ):
        """Add a field definition for validation"""
        self.fields[name] = FieldDefinition(
            name=name,
            field_type=field_type,
            patterns=patterns,
            required=required,
            tolerance=tolerance,
            description=description
        )

    def validate(self, doc1_content: str, doc2_content: str, doc1_name: str = "Document 1", doc2_name: str = "Document 2") -> Dict[str, Any]:
        """
        Validate consistency between two documents

        Returns comprehensive report with:
            - overall_score: float
            - passed/failed/not_found counts
            - grade: str
            - fields: dict of ValidationResults
        """
        results = {}
        passed = 0
        failed = 0
        not_found = 0

        for field_name, field_def in self.fields.items():
            result = self._validate_field(doc1_content, doc2_content, field_def, doc1_name, doc2_name)
            results[field_name] = result

            if result.status == 'PASS':
                passed += 1
            elif result.status == 'FAIL':
                failed += 1
            else:
                not_found += 1

        total_checks = passed + failed
        overall_score = passed / total_checks if total_checks > 0 else 0.0

        # Calculate grade
        grade = self._calculate_grade(overall_score)

        return {
            'overall_score': overall_score,
            'passed': passed,
            'failed': failed,
            'not_found': not_found,
            'total_checks': len(self.fields),
            'grade': grade,
            'fields': results,
            'doc1_name': doc1_name,
            'doc2_name': doc2_name
        }

    def _validate_field(
        self,
        doc1_content: str,
        doc2_content: str,
        field_def: FieldDefinition,
        doc1_name: str,
        doc2_name: str
    ) -> ValidationResult:
        """Validate a single field across two documents"""

        # Extract values from both documents
        extract1 = self.extractor.extract_value(doc1_content, field_def.patterns)
        extract2 = self.extractor.extract_value(doc2_content, field_def.patterns)

        # Handle not found cases
        if extract1 is None and extract2 is None:
            return ValidationResult(
                field_name=field_def.name,
                status='NOT_FOUND',
                confidence=0.0,
                similarity=0.0,
                reason=f"Field not found in either {doc1_name} or {doc2_name}",
                recommendation=f"Check if field patterns are correct for '{field_def.name}'"
            )

        if extract1 is None:
            return ValidationResult(
                field_name=field_def.name,
                status='NOT_FOUND',
                confidence=0.0,
                similarity=0.0,
                doc2_value=extract2[0] if extract2 else None,
                reason=f"Field not found in {doc1_name}",
                recommendation=f"Check if '{field_def.name}' exists in {doc1_name}"
            )

        if extract2 is None:
            return ValidationResult(
                field_name=field_def.name,
                status='NOT_FOUND',
                confidence=0.0,
                similarity=0.0,
                doc1_value=extract1[0] if extract1 else None,
                reason=f"Field not found in {doc2_name}",
                recommendation=f"Check if '{field_def.name}' exists in {doc2_name}"
            )

        # Unpack extracted values
        value1, context1, line1 = extract1
        value2, context2, line2 = extract2

        # Compare values
        comparison = self.comparer.compare(value1, value2, field_def.field_type, field_def.tolerance)

        # Build result
        status = 'PASS' if comparison['match'] else 'FAIL'
        confidence = comparison['similarity']

        result = ValidationResult(
            field_name=field_def.name,
            status=status,
            confidence=confidence,
            similarity=comparison['similarity'],
            doc1_value=value1,
            doc2_value=value2,
            normalized_v1=comparison.get('normalized_v1', value1),
            normalized_v2=comparison.get('normalized_v2', value2),
            method=comparison.get('method', 'unknown'),
            evidence={
                'doc1_location': f'Line {line1}',
                'doc2_location': f'Line {line2}',
                'doc1_context': context1[:100] + '...' if len(context1) > 100 else context1,
                'doc2_context': context2[:100] + '...' if len(context2) > 100 else context2,
                **{k: v for k, v in comparison.items() if k not in ['match', 'similarity', 'normalized_v1', 'normalized_v2', 'method']}
            }
        )

        if status == 'FAIL':
            result.reason = f"Values do not match within tolerance ({field_def.tolerance})"
            result.recommendation = f"Review '{field_def.name}' in both documents for consistency"

        return result

    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from score"""
        if score >= 0.95:
            return 'A+'
        elif score >= 0.90:
            return 'A'
        elif score >= 0.85:
            return 'B+'
        elif score >= 0.80:
            return 'B'
        elif score >= 0.75:
            return 'C+'
        elif score >= 0.70:
            return 'C'
        elif score >= 0.60:
            return 'D'
        else:
            return 'F'


# Convenience function for quick validation
def create_standard_validator() -> DocumentConsistencyValidator:
    """
    Create a validator with standard acquisition document fields

    Returns validator pre-configured with common fields:
        - program_name
        - organization
        - budget
        - period_of_performance
        - contract_type
    """
    validator = DocumentConsistencyValidator()

    # Program Name
    validator.add_field(
        'program_name',
        FieldType.TEXT,
        patterns=[
            r'Program Name:\s*\*?\*?(.+?)(?:\*\*|\n|$)',
            r'Program:\s*\*?\*?(.+?)(?:\*\*|\n|$)',
            r'\*\*Program Name:\*\*\s*(.+?)(?:\n|$)',
            r'\*\*Program:\*\*\s*(.+?)(?:\n|$)',
            r'# (.+?)\n',  # Markdown h1
        ],
        required=True,
        tolerance=0.85,
        description='Official program or project name'
    )

    # Organization
    validator.add_field(
        'organization',
        FieldType.ORGANIZATION,
        patterns=[
            r'Organization:\s*\*?\*?(.+?)(?:\*\*|\n|$)',
            r'\*\*Organization:\*\*\s*(.+?)(?:\n|$)',
            r'Contracting Office:\s*(.+?)(?:\n|$)',
            r'Agency:\s*(.+?)(?:\n|$)',
        ],
        required=True,
        tolerance=0.80,
        description='Contracting organization or agency'
    )

    # Budget
    validator.add_field(
        'budget',
        FieldType.CURRENCY,
        patterns=[
            r'Total Budget:\s*(\$[\d.,]+[KMB]?)',
            r'Estimated Value:\s*(\$[\d.,]+[KMB]?)',
            r'Budget:\s*(\$[\d.,]+[KMB]?)',
            r'Total.*?(\$[\d.,]+\s*(?:million|billion|M|B)?)',
            r'(\$\d+(?:\.\d+)?\s*(?:million|M))',
        ],
        required=True,
        tolerance=0.10,  # Within 10% for currency
        description='Total program budget or estimated value'
    )

    # Period of Performance
    validator.add_field(
        'period_of_performance',
        FieldType.DURATION,
        patterns=[
            r'Period of Performance:\s*(.+?)(?:\n|$)',
            r'\*\*Period of Performance:\*\*\s*(.+?)(?:\n|$)',
            r'Contract Period:\s*(.+?)(?:\n|$)',
            r'Duration:\s*(.+?)(?:\n|$)',
            r'(\d+)\s+months?',
            r'(\d+)\s+years?',
        ],
        required=True,
        tolerance=0.0,  # Exact match for duration
        description='Contract period of performance'
    )

    # Contract Type
    validator.add_field(
        'contract_type',
        FieldType.TEXT,
        patterns=[
            r'Contract Type:\s*(.+?)(?:\n|$)',
            r'\*\*Contract Type:\*\*\s*(.+?)(?:\n|$)',
            r'Recommended Contract Type:\s*(.+?)(?:\n|$)',
        ],
        required=False,
        tolerance=0.90,
        description='Type of contract (FFP, CPFF, T&M, etc.)'
    )

    return validator
