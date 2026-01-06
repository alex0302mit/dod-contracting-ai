# Award Phase Automation Guide

## Overview

This guide documents the **complete Award Phase automation** including all 9 Post-Solicitation tools from Q&A management through contract award.

**What's Included:**
- ✅ Q&A Manager (FAR 15.201(f))
- ✅ Amendment Generator (FAR 15.206)
- ✅ Source Selection Plan (FAR 15.303)
- ✅ Past Performance Questionnaire (FAR 15.305(a)(2))
- ✅ Evaluation Scorecards (FAR 15.305)
- ✅ SSDD - Source Selection Decision (FAR 15.308)
- ✅ SF-26 Contract Award
- ✅ Debriefing Materials (FAR 15.505/15.506)
- ✅ Award Notification Package

---

## System Architecture

### Complete Post-Solicitation Workflow

```
┌─────────────────────────────────────────────────────────────┐
│           Post-Solicitation Orchestrator                    │
├─────────────────────────────────────────────────────────────┤
│  Phase 1: Source Selection Planning                        │
│  Phase 2: Past Performance Questionnaires                  │
│  Phase 3: Evaluation Scorecards (all factors)               │
│  Phase 4: Source Selection Decision (SSDD)                  │
│  Phase 5: Contract Award (SF-26)                            │
│  Phase 6: Award Notifications                               │
│  Phase 7: Debriefing Materials                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Run Complete Award Workflow

```bash
# Set API key
export ANTHROPIC_API_KEY='your-api-key'

# Run complete post-solicitation workflow
python scripts/run_complete_post_solicitation_pipeline.py
```

This generates:
- Source Selection Plan
- 3 PPQs (one per offeror)
- 12 Evaluation Scorecards (3 offerors × 4 factors)
- SSDD (award decision document)
- SF-26 (official contract award)
- Award notification package
- 2 Debriefing documents (for unsuccessful offerors)

---

## Tool Details

### 1. Source Selection Plan (SSP)
**Purpose:** Establish evaluation organization and procedures (FAR 15.303)

**Generates:**
- SSA/SSEB/SSAC organization
- Evaluation schedule
- Consensus procedures

**Output:** `outputs/source-selection/source_selection_plan.md` (+ PDF)

---

### 2. Past Performance Questionnaire (PPQ)
**Purpose:** Standardized reference checks (FAR 15.305(a)(2))

**Generates:**
- Reference check forms
- Performance rating scales
- Email templates

**Output:** `outputs/ppq/ppq_[offeror].md` (+ PDF)

---

### 3. Evaluation Scorecards
**Purpose:** Score proposals per Section M (FAR 15.305)

**Generates:**
- Technical, Management, Past Performance, Cost scorecards
- Strengths/weaknesses/deficiencies
- Risk assessments

**Output:** `outputs/evaluations/scorecard_[factor]_[offeror].md` (+ PDF)

---

### 4. Source Selection Decision Document (SSDD)
**Purpose:** Document award decision (FAR 15.308)

**Generates:**
- Comparative analysis
- Trade-off analysis
- Best value determination
- Award recommendation

**Output:** `outputs/source-selection/ssdd.md` (+ PDF)

---

### 5. SF-26 Contract Award
**Purpose:** Official contract award document

**Generates:**
- Populated SF-26 form
- FPDS-NG data
- SAM.gov posting

**Output:** `outputs/award/sf26_contract_award.md` (+ PDF)

---

### 6. Debriefing Materials
**Purpose:** Offeror feedback (FAR 15.505/15.506)

**Generates:**
- Post-award debriefing documents
- Strengths/weaknesses feedback
- Protest rights information

**Output:** `outputs/debriefing/debriefing_[offeror].md` (+ PDF)

---

### 7. Award Notification Package
**Purpose:** Official award communications

**Generates:**
- Winner notification letter
- Unsuccessful offeror letters
- SAM.gov posting
- Congressional notification (if >$5M)

**Output:** `outputs/award/award_notifications.md` (+ PDF)

---

## Usage Examples

### Example 1: Complete Workflow

```python
from agents import PostSolicitationOrchestrator

# Initialize
orchestrator = PostSolicitationOrchestrator(api_key)

# Define solicitation and offerors
solicitation_info = {
    'solicitation_number': 'W911XX-25-R-1234',
    'program_name': 'ALMS',
    'contracting_officer': 'Jane Smith',
    'co_email': 'jane.smith@army.mil'
}

offerors = [
    {'name': 'Company A', 'cost': '$4.8M'},
    {'name': 'Company B', 'cost': '$5.2M'},
    {'name': 'Company C', 'cost': '$4.5M'}
]

# Execute complete workflow
results = orchestrator.execute_complete_workflow(
    solicitation_info=solicitation_info,
    section_m_content=section_m_content,
    offerors=offerors,
    recommended_awardee='Company A',
    config={'contract_number': 'W911XX-25-C-0001'}
)

print(f"Generated {len(results['phases_completed'])} phases")
```

---

## Complete System Coverage

### You Now Have:

**Pre-Solicitation:** 7/7 (100%) ✅  
**Solicitation:** 8/8 core (100%) ✅  
**Post-Solicitation:** 9/9 (100%) ✅

**TOTAL SYSTEM: 24/28 documents (86%)**

Only missing: Sections B, H, I, K (optional solicitation sections)

---

## FAR Compliance

All tools are FAR-compliant:
- FAR 15.303 - Source Selection Plan
- FAR 15.305 - Proposal Evaluation & Past Performance
- FAR 15.308 - Source Selection Decision
- FAR 15.505/15.506 - Debriefings
- FAR 53.236 - SF-26 Award/Contract

---

## Testing

```bash
# Test complete workflow
python scripts/run_complete_post_solicitation_pipeline.py

# Test individual tools
python scripts/test_post_solicitation_tools.py
```

---

**For complete documentation, see POST_SOLICITATION_TOOLS_GUIDE.md**

**System Status:** ✅ Production Ready - 100% Post-Solicitation Coverage!

