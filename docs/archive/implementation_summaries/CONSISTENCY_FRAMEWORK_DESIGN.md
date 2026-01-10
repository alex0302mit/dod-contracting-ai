# Consistency Validation Framework - Design

**Date**: October 15, 2025
**Priority**: 2 (Medium Impact, 8-10 hours)
**Goal**: Improve cross-document consistency validation from 25% → 90%+

---

## Problem Statement

### Current Issues

The integration test's consistency validation currently achieves only **25% accuracy** (1/4 checks passing). This is due to:

1. **Rigid Regex Matching**: Patterns require exact string matches
2. **Format Variations**: Same data represented differently ("$45M" vs "$45 million")
3. **Location Variations**: Fields appear in different contexts/formats across documents
4. **No Normalization**: Values not normalized before comparison
5. **No Fuzzy Matching**: Small differences cause false negatives

### Example Failures

**Check 1: Program Name**
- Acquisition Plan: `None` (pattern `r'Program Name:\s*(.+?)'` not found)
- IGCE: `** Advanced Logistics Management System (ALMS)` (extra markdown formatting)
- **Issue**: Pattern assumes exact format "Program Name:" but documents use variations

**Check 2: Organization**
- Acquisition Plan: `** U.S. Army` (markdown bold)
- PWS: `None` (pattern not found due to different heading structure)
- **Issue**: Markdown formatting and heading variations

**Check 3: Budget**
- Acquisition Plan: `$6.4M over 10 years`
- IGCE: `total** | $215,160.40`
- **Issue**: Different contexts (narrative vs table), different formats

**Check 4: Period**
- Acquisition Plan: `36 months`
- PWS: `1 Month` (bug in PWS template)
- **Issue**: Template bug + no normalization

---

## Design Goals

### Functional Requirements

✅ **FR1: Fuzzy Matching** - Match similar values even with small differences
✅ **FR2: Format Normalization** - Convert values to standard format before comparison
✅ **FR3: Multiple Pattern Support** - Try multiple regex patterns per field
✅ **FR4: Confidence Scoring** - Provide confidence scores for matches
✅ **FR5: Semantic Comparison** - Understand meaning, not just text
✅ **FR6: Configurable Tolerance** - Adjust strictness per field type
✅ **FR7: Detailed Reporting** - Show why checks pass/fail with evidence

### Non-Functional Requirements

✅ **NFR1: Performance** - Complete validation in <5 seconds
✅ **NFR2: Extensibility** - Easy to add new field types and validators
✅ **NFR3: Reusability** - Framework works for any document pair
✅ **NFR4: No External Dependencies** - Use built-in Python libraries

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│              CONSISTENCY VALIDATION FRAMEWORK                │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
    ┌───────────────────┐   ┌──────────────────┐
    │  Value Extractor  │   │  Value Comparer  │
    └───────────────────┘   └──────────────────┘
                │                       │
        ┌───────┴────────┐      ┌──────┴──────┐
        ▼                ▼      ▼             ▼
  ┌─────────┐    ┌──────────┐ ┌─────────┐ ┌─────────┐
  │ Pattern │    │  Parser  │ │ Fuzzy   │ │  Norm   │
  │ Matcher │    │  Logic   │ │ Matcher │ │ alizer  │
  └─────────┘    └──────────┘ └─────────┘ └─────────┘
```

### Components

1. **DocumentConsistencyValidator** (Main Class)
   - Orchestrates validation workflow
   - Manages field definitions and rules
   - Generates detailed reports

2. **ValueExtractor** (Extraction Module)
   - Multi-pattern regex matching
   - Context-aware extraction
   - Fallback strategies

3. **ValueNormalizer** (Normalization Module)
   - Format standardization (currency, dates, numbers)
   - Text cleaning (markdown, whitespace)
   - Type conversion

4. **ValueComparer** (Comparison Module)
   - Fuzzy string matching (Levenshtein distance)
   - Semantic similarity
   - Tolerance-based comparison

5. **ValidationReporter** (Reporting Module)
   - Detailed pass/fail results
   - Confidence scores
   - Evidence and explanations

---

## Field Type System

### Field Type Definitions

```python
class FieldType(Enum):
    """Types of fields with specific normalization and comparison rules"""
    TEXT = "text"              # General text (fuzzy match)
    CURRENCY = "currency"      # Money amounts ($X.XM, $X,XXX)
    DATE = "date"              # Dates (MM/DD/YYYY, Month YYYY)
    DURATION = "duration"      # Time periods (36 months, 3 years)
    PERCENTAGE = "percentage"  # Percentages (12%, 0.12)
    IDENTIFIER = "identifier"  # IDs, codes (exact match)
    ORGANIZATION = "organization"  # Org names (fuzzy match)
    NUMBER = "number"          # Numeric values
```

### Field Definitions with Multiple Patterns

```python
FIELD_DEFINITIONS = {
    'program_name': {
        'type': FieldType.TEXT,
        'patterns': [
            r'Program Name:\s*\*?\*?(.+?)(?:\*\*|\n|$)',
            r'Program:\s*\*?\*?(.+?)(?:\*\*|\n|$)',
            r'\*\*Program Name:\*\*\s*(.+?)(?:\n|$)',
            r'\*\*Program:\*\*\s*(.+?)(?:\n|$)',
            r'# (.+?)\n',  # Markdown h1
        ],
        'required': True,
        'tolerance': 0.85,  # 85% similarity required
        'description': 'Official program or project name'
    },
    'organization': {
        'type': FieldType.ORGANIZATION,
        'patterns': [
            r'Organization:\s*\*?\*?(.+?)(?:\*\*|\n|$)',
            r'Contracting Office:\s*(.+?)(?:\n|$)',
            r'Agency:\s*(.+?)(?:\n|$)',
        ],
        'required': True,
        'tolerance': 0.80,
        'description': 'Contracting organization or agency'
    },
    'budget': {
        'type': FieldType.CURRENCY,
        'patterns': [
            r'Total Budget:\s*(\$[\d.,]+[KMB]?)',
            r'Estimated Value:\s*(\$[\d.,]+[KMB]?)',
            r'Budget:\s*(\$[\d.,]+[KMB]?)',
            r'TOTAL ESTIMATE.*?(\$[\d.,]+[KMB]?)',
        ],
        'required': True,
        'tolerance': 0.10,  # Within 10% for currency
        'description': 'Total program budget or estimated value'
    },
    'period_of_performance': {
        'type': FieldType.DURATION,
        'patterns': [
            r'Period of Performance:\s*(.+?)(?:\n|$)',
            r'Contract Period:\s*(.+?)(?:\n|$)',
            r'Duration:\s*(.+?)(?:\n|$)',
            r'(\d+)\s+months?',
            r'(\d+)\s+years?',
        ],
        'required': True,
        'tolerance': 0.0,  # Exact match for duration
        'description': 'Contract period of performance'
    },
    'contract_type': {
        'type': FieldType.TEXT,
        'patterns': [
            r'Contract Type:\s*(.+?)(?:\n|$)',
            r'Recommended Contract Type:\s*(.+?)(?:\n|$)',
        ],
        'required': False,
        'tolerance': 0.90,
        'description': 'Type of contract (FFP, CPFF, T&M, etc.)'
    }
}
```

---

## Normalization Strategies

### Currency Normalization

```python
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
    clean = value.replace('$', '').replace(',', '').strip()

    # Handle suffixes
    multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}

    for suffix, multiplier in multipliers.items():
        if suffix in clean.upper():
            num = float(clean.upper().replace(suffix, ''))
            return num * multiplier

    # Check for "million", "billion" words
    if 'million' in clean.lower():
        num = float(re.search(r'[\d.]+', clean).group())
        return num * 1000000
    if 'billion' in clean.lower():
        num = float(re.search(r'[\d.]+', clean).group())
        return num * 1000000000

    return float(clean)
```

### Duration Normalization

```python
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
        return None

    num = int(num_match.group(1))

    # Determine unit
    if any(word in value.lower() for word in ['year', 'yr']):
        return num * 12  # Convert years to months
    elif any(word in value.lower() for word in ['month', 'mo']):
        return num

    return num  # Assume months if no unit
```

### Date Normalization

```python
def normalize_date(value: str) -> datetime:
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

    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue

    return None
```

### Text Normalization

```python
def normalize_text(value: str) -> str:
    """
    Normalize text for comparison

    Operations:
        - Remove markdown formatting (**text**, *text*)
        - Standardize whitespace
        - Convert to lowercase
        - Remove punctuation (optional)
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
```

---

## Fuzzy Matching Algorithm

### Levenshtein Distance (Edit Distance)

```python
def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings
    (minimum number of edits to transform s1 into s2)
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

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

def similarity_ratio(s1: str, s2: str) -> float:
    """
    Calculate similarity ratio (0.0 to 1.0)
    1.0 = identical, 0.0 = completely different
    """
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))

    if max_len == 0:
        return 1.0

    return 1.0 - (distance / max_len)
```

### Fuzzy Comparison with Tolerance

```python
def fuzzy_compare(value1: str, value2: str, tolerance: float = 0.85) -> dict:
    """
    Compare two values with fuzzy matching

    Returns:
        {
            'match': bool,
            'similarity': float,
            'normalized_v1': str,
            'normalized_v2': str,
            'method': str
        }
    """
    # Normalize both values
    norm1 = normalize_text(value1)
    norm2 = normalize_text(value2)

    # Calculate similarity
    similarity = similarity_ratio(norm1, norm2)

    return {
        'match': similarity >= tolerance,
        'similarity': similarity,
        'normalized_v1': norm1,
        'normalized_v2': norm2,
        'method': 'levenshtein'
    }
```

---

## Comparison Strategies by Field Type

### Strategy 1: Text Fields (Fuzzy Match)

```python
def compare_text(value1: str, value2: str, tolerance: float) -> dict:
    """Compare text fields with fuzzy matching"""
    return fuzzy_compare(value1, value2, tolerance)
```

### Strategy 2: Currency Fields (Numeric Tolerance)

```python
def compare_currency(value1: str, value2: str, tolerance: float) -> dict:
    """
    Compare currency values with numeric tolerance

    tolerance: Percentage difference allowed (e.g., 0.10 = 10%)
    """
    try:
        amount1 = normalize_currency(value1)
        amount2 = normalize_currency(value2)

        # Calculate percentage difference
        avg = (amount1 + amount2) / 2
        diff = abs(amount1 - amount2)
        pct_diff = diff / avg if avg > 0 else 0

        return {
            'match': pct_diff <= tolerance,
            'similarity': 1.0 - pct_diff,
            'normalized_v1': f"${amount1:,.2f}",
            'normalized_v2': f"${amount2:,.2f}",
            'difference': f"${diff:,.2f}",
            'pct_difference': f"{pct_diff*100:.1f}%",
            'method': 'numeric_tolerance'
        }
    except Exception as e:
        return {
            'match': False,
            'similarity': 0.0,
            'error': str(e),
            'method': 'numeric_tolerance'
        }
```

### Strategy 3: Duration Fields (Exact Match after Normalization)

```python
def compare_duration(value1: str, value2: str, tolerance: float) -> dict:
    """Compare duration fields (exact match after normalization to months)"""
    try:
        months1 = normalize_duration(value1)
        months2 = normalize_duration(value2)

        return {
            'match': months1 == months2,
            'similarity': 1.0 if months1 == months2 else 0.0,
            'normalized_v1': f"{months1} months",
            'normalized_v2': f"{months2} months",
            'method': 'exact_after_normalization'
        }
    except Exception as e:
        return {
            'match': False,
            'similarity': 0.0,
            'error': str(e),
            'method': 'exact_after_normalization'
        }
```

### Strategy 4: Date Fields (Exact or Range Match)

```python
def compare_date(value1: str, value2: str, tolerance: float) -> dict:
    """Compare date fields (exact match or within tolerance days)"""
    try:
        date1 = normalize_date(value1)
        date2 = normalize_date(value2)

        if date1 is None or date2 is None:
            # Fallback to text comparison
            return compare_text(value1, value2, 0.90)

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
```

---

## Validation Workflow

### Step-by-Step Process

```
1. EXTRACTION PHASE
   ├─ For each field definition
   │  ├─ Try all patterns in order
   │  ├─ Parse context around match
   │  ├─ Extract candidate values
   │  └─ Select best match (highest confidence)
   └─ Store extracted values per document

2. NORMALIZATION PHASE
   ├─ For each extracted value
   │  ├─ Apply field type normalization
   │  ├─ Clean formatting (markdown, whitespace)
   │  └─ Convert to standard format
   └─ Store normalized values

3. COMPARISON PHASE
   ├─ For each field to validate
   │  ├─ Get normalized values from both docs
   │  ├─ Apply field type comparison strategy
   │  ├─ Calculate similarity score
   │  └─ Determine pass/fail based on tolerance
   └─ Store comparison results

4. REPORTING PHASE
   ├─ Generate detailed report
   │  ├─ Per-field results (pass/fail/not_found)
   │  ├─ Confidence scores
   │  ├─ Evidence (matched text)
   │  ├─ Explanations for failures
   │  └─ Overall consistency score
   └─ Return report object
```

---

## Enhanced Validation Report

### Report Structure

```python
{
    'overall_score': 0.85,  # 85% consistency
    'passed': 5,
    'failed': 1,
    'not_found': 1,
    'total_checks': 7,
    'grade': 'B+',
    'fields': {
        'program_name': {
            'status': 'PASS',
            'confidence': 0.95,
            'similarity': 0.95,
            'doc1_value': 'Advanced Logistics Management System (ALMS)',
            'doc2_value': 'Advanced Logistics Management System (ALMS)',
            'normalized_v1': 'advanced logistics management system (alms)',
            'normalized_v2': 'advanced logistics management system (alms)',
            'method': 'levenshtein',
            'evidence': {
                'doc1_location': 'Line 12',
                'doc2_location': 'Line 3',
                'doc1_context': '**Program Name:** Advanced Logistics...',
                'doc2_context': '**Program:** Advanced Logistics...'
            }
        },
        'budget': {
            'status': 'PASS',
            'confidence': 0.92,
            'similarity': 0.98,
            'doc1_value': '$45 million',
            'doc2_value': '$45M',
            'normalized_v1': '$45,000,000.00',
            'normalized_v2': '$45,000,000.00',
            'difference': '$0.00',
            'pct_difference': '0.0%',
            'method': 'numeric_tolerance'
        },
        'period_of_performance': {
            'status': 'FAIL',
            'confidence': 0.85,
            'similarity': 0.0,
            'doc1_value': '36 months',
            'doc2_value': '1 Month',
            'normalized_v1': '36 months',
            'normalized_v2': '1 months',
            'method': 'exact_after_normalization',
            'reason': 'Values do not match after normalization',
            'recommendation': 'Check PWS period field - appears to be incorrect'
        }
    }
}
```

---

## Implementation Plan

### Phase 1: Core Infrastructure (2-3 hours)

1. **Create base classes** (30 min)
   - `FieldType` enum
   - `FieldDefinition` dataclass
   - `ValidationResult` dataclass

2. **Implement normalizers** (1 hour)
   - Currency normalizer
   - Duration normalizer
   - Date normalizer
   - Text normalizer

3. **Implement fuzzy matching** (1 hour)
   - Levenshtein distance
   - Similarity ratio
   - Comparison strategies

### Phase 2: Validator Implementation (3-4 hours)

1. **ValueExtractor class** (1 hour)
   - Multi-pattern matching
   - Context extraction
   - Best match selection

2. **ValueComparer class** (1 hour)
   - Field type dispatch
   - Tolerance checking
   - Result generation

3. **DocumentConsistencyValidator class** (1.5 hours)
   - Main orchestration logic
   - Field registration
   - Batch validation

4. **ValidationReporter class** (30 min)
   - Report generation
   - Score calculation
   - Grade assignment

### Phase 3: Integration & Testing (2-3 hours)

1. **Integrate with test workflow** (1 hour)
   - Update `test_integration_workflow.py`
   - Replace simple checks with framework

2. **Test with ALMS example** (1 hour)
   - Run integration test
   - Validate improvements
   - Debug issues

3. **Documentation** (1 hour)
   - Usage examples
   - API documentation
   - Results report

---

## Success Criteria

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| **Consistency Score** | 25% | ≥90% | 4/4 → 3.6+/4 checks |
| **False Negatives** | High | Low | Catches valid matches |
| **False Positives** | Low | Low | Rejects invalid matches |
| **Performance** | <1s | <5s | Total validation time |
| **Extensibility** | Hard | Easy | Time to add new field |

### Validation Checks

✅ Program Name: "ALMS" vs "Advanced Logistics Management System (ALMS)" → **PASS** (fuzzy match)
✅ Organization: "U.S. Army" vs "US Army" → **PASS** (fuzzy match)
✅ Budget: "$45M" vs "$45 million" vs "$45,000,000" → **PASS** (normalized)
✅ Period: "36 months" vs "3 years" → **PASS** (normalized to months)

---

## Next Steps

1. ✅ Create design document (this document)
2. ⏳ Implement normalizers and fuzzy matching
3. ⏳ Implement validator classes
4. ⏳ Integrate with test workflow
5. ⏳ Test and validate improvements
6. ⏳ Document results

---

**Design Status**: ✅ COMPLETE
**Next**: Implementation
