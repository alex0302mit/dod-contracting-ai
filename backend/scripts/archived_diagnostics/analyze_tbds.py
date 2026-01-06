#!/usr/bin/env python3
"""
Analyze TBDs in generated documents
Shows TBD categories and whether they're descriptive (Phase 1 enhancement)
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

def analyze_tbds(content: str, agent_name: str):
    """Analyze TBD patterns in content"""
    print(f"\n{'='*70}")
    print(f"TBD ANALYSIS: {agent_name}")
    print('='*70)

    # Count total TBDs
    total_tbds = content.count('TBD')
    print(f"\nTotal TBD count: {total_tbds}")

    if total_tbds == 0:
        print("  ✅ No TBDs found - perfect!")
        return

    # Check for descriptive TBDs (Phase 1 enhancement)
    descriptive_pattern = r'TBD\s*-\s*\w+'
    descriptive_tbds = re.findall(descriptive_pattern, content)
    descriptive_count = len(descriptive_tbds)
    descriptive_pct = (descriptive_count / total_tbds * 100) if total_tbds > 0 else 0

    print(f"\nDescriptive TBDs: {descriptive_count}/{total_tbds} ({descriptive_pct:.1f}%)")
    if descriptive_pct > 80:
        print("  ✅ Excellent: Most TBDs are descriptive (Phase 1 enhancement working!)")
    elif descriptive_pct > 50:
        print("  ✅ Good: Majority of TBDs are descriptive")
    elif descriptive_pct > 0:
        print("  ⚠️  Some TBDs are descriptive, but could be better")
    else:
        print("  ❌ No descriptive TBDs found - using lazy 'TBD'")

    # Show sample descriptive TBDs
    if descriptive_tbds:
        print(f"\nSample descriptive TBDs:")
        for i, tbd in enumerate(descriptive_tbds[:5], 1):
            print(f"  {i}. {tbd[:80]}...")

    # Find TBD contexts and categorize
    print(f"\nTBD Categories:")
    tbd_pattern = r'([^\n]*TBD[^\n]*)'
    matches = re.findall(tbd_pattern, content, re.IGNORECASE)

    categories = defaultdict(list)
    for match in matches:
        # Clean up match
        match = match.strip()
        if not match or len(match) < 5:
            continue

        # Categorize by keywords
        match_lower = match.lower()
        if 'cost' in match_lower or 'price' in match_lower or 'budget' in match_lower:
            categories['Cost/Budget'].append(match)
        elif 'schedule' in match_lower or 'date' in match_lower or 'timeline' in match_lower:
            categories['Schedule/Timeline'].append(match)
        elif 'team' in match_lower or 'personnel' in match_lower or 'staff' in match_lower:
            categories['Personnel/Team'].append(match)
        elif 'requirement' in match_lower or 'specification' in match_lower:
            categories['Requirements'].append(match)
        elif 'evaluator' in match_lower or 'evaluation' in match_lower:
            categories['Evaluation Instructions'].append(match)
        elif 'contract' in match_lower:
            categories['Contract'].append(match)
        else:
            categories['Other'].append(match)

    for category, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"\n  {category} ({len(items)}):")
        for item in items[:3]:  # Show first 3 per category
            display = item[:100] + '...' if len(item) > 100 else item
            print(f"    • {display}")

def main():
    """Analyze TBDs in test outputs"""
    print("\n" + "="*70)
    print("PHASE 1 TBD ANALYSIS TOOL")
    print("="*70)

    output_dir = Path(__file__).parent.parent / 'output'

    test_files = [
        ('test_igce_phase1.md', 'IGCE Generator', 30),
        ('test_scorecard_phase1.md', 'Evaluation Scorecard', 10),
        ('test_ssp_phase1.md', 'Source Selection Plan', 8)
    ]

    all_results = []

    for filename, agent_name, target in test_files:
        filepath = output_dir / filename

        if not filepath.exists():
            print(f"\n⚠️  File not found: {filepath}")
            print(f"   Run test suite first: python3 scripts/test_phase1_complete.py")
            continue

        with open(filepath, 'r') as f:
            content = f.read()

        analyze_tbds(content, agent_name)

        # Check target
        tbd_count = content.count('TBD')
        if tbd_count <= target:
            status = "✅ PASS"
            print(f"\n{status}: Target met ({tbd_count} ≤ {target})")
        else:
            status = "⚠️  TARGET NOT MET"
            print(f"\n{status}: {tbd_count} > {target}")

        all_results.append((agent_name, tbd_count, target, tbd_count <= target))

    # Overall summary
    if all_results:
        print("\n" + "="*70)
        print("OVERALL SUMMARY")
        print("="*70)

        total_tbds = sum(r[1] for r in all_results)
        total_target = sum(r[2] for r in all_results)
        all_passed = all(r[3] for r in all_results)

        print(f"\nTotal TBDs found: {total_tbds}")
        print(f"Total target: <{total_target}")
        print(f"\nResults:")
        for agent, count, target, passed in all_results:
            status = "✅" if passed else "⚠️ "
            print(f"  {status} {agent}: {count} TBDs (target: <{target})")

        if all_passed:
            print(f"\n✅ ALL TARGETS MET!")
            print(f"   Phase 1 TBD reduction goal achieved: {total_tbds}/{total_target}")
        else:
            failed = sum(1 for r in all_results if not r[3])
            print(f"\n⚠️  {failed} agent(s) did not meet target")

        print("="*70)
    else:
        print("\n⚠️  No test files found. Run tests first:")
        print("   python3 scripts/test_phase1_complete.py")

if __name__ == "__main__":
    main()
