"""
Test script to verify citation detection patterns
"""
import re

# Citation patterns from quality_agent.py
citation_patterns = [
    # Traditional government/academic citations
    r'Per\s+[A-Z]+',
    r'According to\s+[\w\s]+dated',
    r'Reference\s+#?\d+',
    r'Source:\s*',
    r'\(Ref\.',
    r'dated\s+\w+\s+\d+,?\s+\d{4}',
    r'as stated in\s+',
    r'per the\s+[A-Z]+',
    # Parenthetical citations matching SOO writer format
    r'\([A-Z][^)]{3,50},\s*\d{4}\)',  # (Program Objectives, 2025)
    r'\([A-Z][^)]{3,50},\s*\w+\s+\d{4}\)',  # (Performance Standards, March 2025)
    r'\([A-Z][^)]{3,50},\s*\d{1,2}/\d{1,2}/\d{4}\)',  # (Program Objectives, 10/05/2025)
]

# Test content samples from the actual SOO report
test_samples = [
    "The contractor shall achieve cloud-based inventory tracking (Program Objectives, March 2025).",
    "Performance shall meet 99.9% system availability (Performance Standards, 2025).",
    "The system shall be deployed within 36 months (Schedule Requirements, 10/05/2025).",
    "The total program budget is $2.5 million (Program Budget, 10/05/2025).",
    "Integration with existing systems is required (Integration Requirements, 10/05/2025).",
    "Mobile access must be provided (Mobile Requirements, 10/05/2025).",
    "Per FAR 37.602, performance-based acquisition principles apply.",
    "According to DoD guidance dated January 2025, security standards must be met.",
]

print("Testing Citation Detection Patterns")
print("=" * 60)
print()

for i, sample in enumerate(test_samples, 1):
    print(f"Sample {i}: {sample}")
    citations_found = []

    for pattern in citation_patterns:
        matches = re.finditer(pattern, sample, re.IGNORECASE)
        for match in matches:
            citations_found.append(match.group())

    if citations_found:
        print(f"  ✓ Found {len(citations_found)} citation(s): {citations_found}")
    else:
        print(f"  ✗ No citations detected")
    print()

print("=" * 60)
print("Summary: Testing complete")