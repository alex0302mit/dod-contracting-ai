# IGCE Agent Enhancement - Detailed Implementation Plan

**Date:** October 12, 2025
**Status:** Ready for Implementation
**Target:** Reduce TBDs from 120+ to <10

---

## Current Issues

### Problem: Line 412 - Lazy TBD Fallback
```python
# Fill remaining placeholders with TBD
content = re.sub(r'\{\{[^}]+\}\}', 'TBD', content)
```
**Result:** 120+ TBD instances even though data exists in RAG

### Problem: Line 274 - Single Vague RAG Query
```python
query = f"What are typical costs for {program_name}?"
```
**Result:** Generic results, no specific data extraction

### Problem: No Data Extraction from RAG Results
- RAG returns text snippets
- No parsing of costs, schedules, tables
- Retrieved data not used to fill placeholders

---

## Solution: Comprehensive RAG-First Approach

### New Methods to Add

#### 1. `_build_rag_context()` - NEW
**Purpose:** Query RAG with 5 targeted queries and extract structured data

```python
def _build_rag_context(self, project_info: Dict) -> Dict:
    """
    Build comprehensive context from RAG before template population

    Queries:
    1. Budget and development costs
    2. Annual sustainment costs (licenses, training, cloud)
    3. Schedule and milestones (IOC, FOC dates)
    4. Personnel and labor information
    5. Contract structure and details

    Returns:
        Dictionary with extracted data ready for template population
    """
```

#### 2. `_extract_costs_from_rag()` - NEW
**Purpose:** Parse cost data from RAG results

```python
def _extract_costs_from_rag(self, rag_results: List[Dict]) -> Dict:
    """
    Extract structured cost data from RAG text

    Looks for:
    - Dollar amounts ($X, $XM, $XK)
    - Budget tables
    - Development vs lifecycle costs
    - Annual costs

    Returns:
        {
            'development_cost': '$2,500,000',
            'lifecycle_cost': '$6,400,000',
            'annual_sustainment': '$700,000',
            'license_cost': '$320,000',
            ...
        }
    """
```

#### 3. `_extract_schedule_from_rag()` - NEW
**Purpose:** Parse schedule/milestone data

```python
def _extract_schedule_from_rag(self, rag_results: List[Dict]) -> Dict:
    """
    Extract schedule milestones from RAG text

    Looks for:
    - IOC/FOC dates
    - Phase dates
    - Deployment schedules

    Returns:
        {
            'ioc_date': 'June 2026',
            'foc_date': 'December 2026',
            'deployment_phases': [...],
            ...
        }
    """
```

#### 4. `_extract_personnel_from_rag()` - NEW
**Purpose:** Parse personnel and labor data

```python
def _extract_personnel_from_rag(self, rag_results: List[Dict]) -> Dict:
    """
    Extract personnel information from RAG text

    Looks for:
    - Team sizes
    - Labor categories mentioned
    - User counts
    - Training numbers

    Returns:
        {
            'team_size': '15 personnel',
            'users': '2,800',
            'trained_users': '500 initial',
            ...
        }
    """
```

#### 5. `_populate_template_intelligently()` - REPLACE EXISTING
**Purpose:** Replace line 375-414 with smart population logic

```python
def _populate_template_intelligently(
    self,
    template: str,
    project_info: Dict,
    cost_elements: Dict,
    labor_costs: Dict,
    materials_costs: Dict,
    risk_analysis: Dict,
    boe: Dict,
    rag_context: Dict,  # NEW PARAMETER
    config: Dict
) -> str:
    """
    Intelligently populate template with priority system:
    1. Calculated values
    2. RAG-retrieved values
    3. Smart defaults
    4. TBD with explanation (last resort)

    Returns populated template with minimal TBDs
    """
```

---

## Implementation Steps

### Step 1: Add New RAG Queries (Insert after line 116)

```python
# NEW: Step 2a: Build comprehensive RAG context
print("\nSTEP 2a: Building comprehensive RAG context...")
rag_context = self._build_rag_context(project_info)
print(f"  ✓ RAG context built with {len(rag_context)} data points")
```

### Step 2: Implement `_build_rag_context()` (Insert after line 287)

```python
def _build_rag_context(self, project_info: Dict) -> Dict:
    """Build comprehensive context from RAG"""
    if not self.retriever:
        return {}

    program_name = project_info.get('program_name', 'the program')
    rag_context = {}

    try:
        # Query 1: Budget and costs
        print("    - Querying RAG for budget and development costs...")
        results = self.retriever.retrieve(
            f"Total budget development cost lifecycle cost for {program_name} ALMS",
            top_k=5
        )
        costs = self._extract_costs_from_rag(results)
        rag_context.update(costs)

        # Query 2: Annual sustainment costs
        print("    - Querying RAG for sustainment costs...")
        results = self.retriever.retrieve(
            f"Annual sustainment costs software licenses training cloud hosting for {program_name}",
            top_k=5
        )
        sustainment = self._extract_sustainment_from_rag(results)
        rag_context.update(sustainment)

        # Query 3: Schedule and milestones
        print("    - Querying RAG for schedule milestones...")
        results = self.retriever.retrieve(
            f"IOC FOC dates deployment schedule milestones for {program_name}",
            top_k=5
        )
        schedule = self._extract_schedule_from_rag(results)
        rag_context.update(schedule)

        # Query 4: Personnel and labor
        print("    - Querying RAG for personnel information...")
        results = self.retriever.retrieve(
            f"Team size personnel labor categories users training for {program_name}",
            top_k=5
        )
        personnel = self._extract_personnel_from_rag(results)
        rag_context.update(personnel)

        # Query 5: Contract details
        print("    - Querying RAG for contract structure...")
        results = self.retriever.retrieve(
            f"Contract type structure CLIN pricing model for {program_name}",
            top_k=5
        )
        contract_info = self._extract_contract_info_from_rag(results)
        rag_context.update(contract_info)

    except Exception as e:
        self.log(f"RAG context building failed: {e}", level="WARNING")

    return rag_context
```

### Step 3: Implement Data Extraction Methods

All extraction methods follow this pattern:
1. Combine RAG result texts
2. Use regex to find patterns ($XXX, dates, numbers)
3. Use LLM for complex extraction
4. Return structured dictionary

### Step 4: Replace `_populate_igce_template()` (lines 375-414)

Complete rewrite with:
- Priority-based population
- Smart defaults
- Minimal TBDs

---

## Expected Results

### Before Enhancement:
- Total TBDs: 120+
- Filled placeholders: ~20
- Data utilization: 10%

### After Enhancement:
- Total TBDs: <10
- Filled placeholders: ~130
- Data utilization: 90%+

### Specific Improvements:

| Placeholder | Before | After | Source |
|-------------|--------|-------|--------|
| `{{grand_total}}` | TBD | $2.5M - $6.4M | RAG from APB |
| `{{annual_sustainment}}` | TBD | $700,000 | RAG from APB |
| `{{license_cost}}` | TBD | $320,000 | RAG from APB |
| `{{training_cost}}` | TBD | $30,000 | RAG from APB |
| `{{cloud_cost}}` | TBD | $75,000 | RAG from APB |
| `{{ioc_date}}` | TBD | June 2026 | RAG from APB |
| `{{foc_date}}` | TBD | December 2026 | RAG from APB |
| `{{user_count}}` | TBD | 2,800 users | RAG from APB |
| ... | ... | ... | ... |

---

## Testing Plan

1. **Test with ALMS data:**
   - Should extract all costs from APB
   - Should extract all dates
   - Should have <10 TBDs

2. **Test without RAG:**
   - Should fall back to smart defaults
   - Should not crash

3. **Test with unknown program:**
   - Should use calculated values
   - Should have reasonable defaults
   - TBDs should have explanations

---

## Implementation Priority

**HIGH PRIORITY (Do Now):**
1. Add `_build_rag_context()` method
2. Add 5 extraction methods
3. Replace `_populate_igce_template()`
4. Test with existing IGCE generation

**MEDIUM PRIORITY (Next):**
5. Add smart defaults dictionary
6. Add TBD explanation logic
7. Enhance error handling

**LOW PRIORITY (Future):**
8. Cache RAG results for performance
9. Add validation of extracted data
10. Add confidence scores for extracted values

---

## Code Metrics

**Lines to Add:** ~300 lines
**Lines to Replace:** ~40 lines (template population)
**New Methods:** 6
**Enhanced Methods:** 2
**Estimated Time:** 4-6 hours

---

**Ready to implement? This will be a significant improvement to the IGCE agent and serve as a template for enhancing other agents.**
