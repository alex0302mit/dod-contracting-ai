# Post-Solicitation Tools Guide

## Overview

This guide documents the **Post-Solicitation Phase tools** for managing the period between RFP release and contract award.

**What These Tools Do:**
- Manage solicitation amendments
- Track and respond to vendor questions
- Generate evaluation scorecards for proposals
- Ensure FAR compliance throughout source selection

---

## System Architecture

### 3 Core Post-Solicitation Tools

```
┌─────────────────────────────────────────────────────────────┐
│              Post-Solicitation Workflow                     │
├─────────────────────────────────────────────────────────────┤
│  1. Q&A Manager           → Track and answer questions      │
│  2. Amendment Generator   → Modify solicitation             │
│  3. Evaluation Scorecards → Score proposals                 │
└─────────────────────────────────────────────────────────────┘
```

### Tool Components

| Tool | Purpose | FAR Reference | Output |
|------|---------|---------------|--------|
| **Q&A Manager** | Track/answer vendor questions | FAR 15.201(f) | Q&A document, database |
| **Amendment Generator** | Modify solicitation | FAR 15.206 | Amendment notices |
| **Evaluation Scorecards** | Score proposals | FAR 15.305 | Evaluation forms |

---

## Quick Start

### 1. Setup

```bash
# Set API key
export ANTHROPIC_API_KEY='your-api-key'

# Install dependencies (already installed)
pip install -r requirements.txt
```

### 2. Run Test Suite

```bash
# Test all three tools
python scripts/test_post_solicitation_tools.py

# Run workflow demonstration
python scripts/test_post_solicitation_tools.py --demo
```

### 3. Check Outputs

```bash
ls -R outputs/amendments/
ls -R outputs/qa/
ls -R outputs/evaluations/
```

---

## Tool 1: Amendment Generator

### Purpose
Generate solicitation amendments per FAR 14.208 and FAR 15.206.

### When to Use
- Incorporating Q&A responses
- Extending proposal due dates
- Correcting errors in solicitation
- Adding/changing requirements
- Revising evaluation factors

### Usage Example

```python
from agents import AmendmentGeneratorAgent

# Initialize
agent = AmendmentGeneratorAgent(api_key)

# Solicitation information
solicitation_info = {
    'solicitation_number': 'W911XX-25-R-1234',
    'program_name': 'ALMS',
    'contracting_officer': 'Jane Smith',
    'co_email': 'jane.smith@army.mil',
    'issue_date': 'September 1, 2025',
    'proposal_due_date': 'October 15, 2025 at 2:00 PM EST'
}

# Define changes
changes = [
    {
        'section': 'Section L',
        'type': 'modify',
        'description': 'Extended Technical Volume page limit from 25 to 30 pages',
        'impact': 'minor'
    },
    {
        'section': 'Section C (PWS)',
        'type': 'modify',
        'description': 'Clarified system availability requirement',
        'impact': 'major'
    }
]

# Q&A to incorporate
qa_responses = [
    {'id': 'Q-001', 'question': 'What cloud provider?', 'answer': 'AWS GovCloud or Azure Gov'}
]

# Generate amendment
task = {
    'solicitation_info': solicitation_info,
    'amendment_number': '0001',
    'changes': changes,
    'qa_responses': qa_responses,
    'config': {'extension_days': 14}
}

result = agent.execute(task)

# Save
files = agent.save_to_file(
    result['content'],
    'outputs/amendments/amendment_0001.md',
    convert_to_pdf=True
)

print(f"Amendment saved: {files['markdown']}")
print(f"PDF: {files['pdf']}")
```

### Output
- **Markdown:** `outputs/amendments/amendment_XXXX.md`
- **PDF:** `outputs/amendments/amendment_XXXX.pdf`

### Key Features
- ✅ Tracks amendment sequence (0001, 0002, etc.)
- ✅ Documents all changes by section
- ✅ Calculates appropriate deadline extensions
- ✅ Incorporates Q&A responses
- ✅ SAM.gov posting format
- ✅ Acknowledgment requirements

---

## Tool 2: Q&A Manager

### Purpose
Track and respond to vendor questions during solicitation period per FAR 15.201(f).

### When to Use
- During solicitation open period
- Managing vendor inquiries
- Ensuring fair disclosure
- Identifying amendment needs

### Usage Example

```python
from agents import QAManagerAgent
from rag.retriever import Retriever

# Initialize with RAG for intelligent answering
agent = QAManagerAgent(api_key, retriever)

# Add questions as they come in
q1 = agent.add_question(
    question_text="What cloud provider should be used?",
    submitter="Anonymous",  # For fair disclosure
    category="Technical Requirements",
    solicitation_section="Section C (PWS)"
)

# Generate answer (uses RAG if available)
agent.generate_answer(
    question_id=q1['id'],
    manual_answer="AWS GovCloud or Azure Government are both acceptable."
)

# Check if amendment needed
amendments_needed = agent.get_questions_requiring_amendment()
print(f"Questions requiring amendment: {len(amendments_needed)}")

# Generate Q&A document
solicitation_info = {
    'solicitation_number': 'W911XX-25-R-1234',
    'program_name': 'ALMS',
    'contracting_officer': 'Jane Smith',
    'co_email': 'jane.smith@army.mil'
}

qa_doc = agent.generate_qa_document(solicitation_info, {})

# Save
files = agent.save_to_file(
    qa_doc['content'],
    'outputs/qa/questions_and_answers_001.md',
    convert_to_pdf=True
)

# Save Q&A database for tracking
agent.save_qa_database('outputs/qa/qa_database.json')

# Export statistics
stats = agent.export_statistics()
print(f"Total questions: {stats['total_questions']}")
print(f"Answered: {stats['answered']}")
```

### Output
- **Q&A Document:** `outputs/qa/questions_and_answers_XXX.md` (+ PDF)
- **Q&A Database:** `outputs/qa/qa_database.json` (tracking)

### Key Features
- ✅ Question tracking with unique IDs
- ✅ RAG-powered answer generation
- ✅ Fair disclosure compliance
- ✅ Amendment requirement detection
- ✅ Category organization
- ✅ Statistics and reporting
- ✅ Database persistence (JSON)

### Question Categories
- General Questions
- Technical Requirements
- Performance Requirements
- Deliverables and Schedule
- Evaluation Factors (Section M)
- Proposal Submission (Section L)
- Contract Type and Pricing
- Small Business and Teaming
- Security and Clearances
- Government-Furnished Property
- Past Performance

---

## Tool 3: Evaluation Scorecard Generator

### Purpose
Generate proposal evaluation scorecards per FAR 15.305.

### When to Use
- After proposal receipt
- During technical evaluation
- For consensus meetings
- Source selection documentation

### Usage Example

```python
from agents import EvaluationScorecardGeneratorAgent

# Initialize
agent = EvaluationScorecardGeneratorAgent(api_key)

# Solicitation information
solicitation_info = {
    'solicitation_number': 'W911XX-25-R-1234',
    'program_name': 'ALMS'
}

# Section M content (evaluation factors)
section_m_content = """
Evaluation Factor 1: Technical Approach (40%)
Subfactors:
- System Architecture
- Development Methodology
- Integration Approach
- Cybersecurity
- Testing
"""

# Evaluator and offeror config
config = {
    'offeror_name': 'ABC Technology Solutions Inc.',
    'offeror_duns': '123456789',
    'business_size': 'Small Business',
    'evaluator_name': 'Dr. John Smith',
    'evaluator_title': 'Technical Evaluator',
    'source_selection_method': 'Best Value Trade-Off',
    'factor_weight': '40%'
}

# Generate scorecard for Technical Approach
task = {
    'solicitation_info': solicitation_info,
    'section_m_content': section_m_content,
    'evaluation_factor': 'Technical Approach',
    'config': config
}

result = agent.execute(task)

# Save
files = agent.save_to_file(
    result['content'],
    'outputs/evaluations/scorecard_technical_abc.md',
    convert_to_pdf=True
)

# Or generate complete set for all factors
full_set = agent.generate_full_scorecard_set(
    solicitation_info,
    section_m_content,
    config
)

# Saves 4 scorecards: Technical, Management, Past Performance, Cost/Price
```

### Output
- **Individual Scorecard:** `outputs/evaluations/scorecard_[factor]_[offeror].md` (+ PDF)
- **Full Set:** 4 scorecards (one per standard evaluation factor)

### Key Features
- ✅ Aligns with Section M factors/subfactors
- ✅ Best Value and LPTA rating scales
- ✅ Strengths/weaknesses/deficiencies format
- ✅ Risk assessment (Low/Medium/High)
- ✅ Numerical scoring (optional)
- ✅ Evaluator certification section
- ✅ Quality review section

### Rating Scales

**Best Value Trade-Off:**
- Outstanding (90-100 points) - Low Risk
- Good (75-89 points) - Low to Moderate Risk
- Acceptable (60-74 points) - Moderate Risk
- Marginal (40-59 points) - Moderate to High Risk
- Unacceptable (0-39 points) - High Risk

**LPTA:**
- Acceptable - Meets all minimum requirements
- Unacceptable - Fails to meet requirements

---

## Workflow Integration

### Complete Post-Solicitation Workflow

```python
# Phase 1: RFP is open
print("="*80)
print("PHASE 1: SOLICITATION OPEN - Q&A PERIOD")
print("="*80)

# Initialize Q&A Manager
qa_manager = QAManagerAgent(api_key, retriever)

# Collect questions (typically 2-4 weeks)
q1 = qa_manager.add_question("What cloud provider?", category="Technical")
q2 = qa_manager.add_question("What is page limit?", category="Proposal Submission")

# Generate answers
qa_manager.generate_answer(q1['id'], manual_answer="AWS GovCloud or Azure Gov")
qa_manager.generate_answer(q2['id'], manual_answer="25 pages per Section L")

# Generate Q&A document
qa_doc = qa_manager.generate_qa_document(solicitation_info, {})
qa_manager.save_to_file(qa_doc['content'], 'outputs/qa/qa_001.md')

# Phase 2: Amendment needed
print("\n="*80)
print("PHASE 2: AMENDMENT GENERATION")
print("="*80)

# Check if amendment needed
amendments_needed = qa_manager.get_questions_requiring_amendment()

if amendments_needed:
    # Generate amendment
    amend_agent = AmendmentGeneratorAgent(api_key)
    
    changes = [
        {
            'section': 'Section L',
            'type': 'modify',
            'description': 'Extended page limit based on Q&A',
            'impact': 'minor'
        }
    ]
    
    amendment = amend_agent.execute({
        'solicitation_info': solicitation_info,
        'amendment_number': '0001',
        'changes': changes,
        'qa_responses': [q for q in qa_manager.qa_database if q['status'] == 'answered']
    })
    
    amend_agent.save_to_file(amendment['content'], 'outputs/amendments/amendment_0001.md')

# Phase 3: Proposals received - evaluate
print("\n="*80)
print("PHASE 3: PROPOSAL EVALUATION")
print("="*80)

# Generate evaluation scorecards
eval_agent = EvaluationScorecardGeneratorAgent(api_key)

# For each offeror and each factor
offerors = ['Company A', 'Company B', 'Company C']
factors = ['Technical Approach', 'Management Approach', 'Past Performance', 'Cost/Price']

for offeror in offerors:
    for factor in factors:
        scorecard = eval_agent.execute({
            'solicitation_info': solicitation_info,
            'section_m_content': section_m_content,
            'evaluation_factor': factor,
            'config': {
                'offeror_name': offeror,
                'evaluator_name': 'Evaluator Name',
                'source_selection_method': 'Best Value Trade-Off'
            }
        })
        
        filename = f"scorecard_{factor.lower().replace(' ', '_')}_{offeror.lower().replace(' ', '_')}.md"
        eval_agent.save_to_file(scorecard['content'], f'outputs/evaluations/{filename}')

print("✅ Evaluation scorecards complete for all offerors")
```

---

## Configuration Options

### Amendment Generator Configuration

```python
amendment_config = {
    'extension_days': 14,              # Days to extend deadline
    'major_extension_days': 14,        # For major changes
    'minor_extension_days': 7,         # For minor changes
    'admin_extension_days': 0,         # For administrative changes
    'reason': 'Incorporate Q&A and industry feedback',
    'classification': 'UNCLASSIFIED'
}
```

### Q&A Manager Configuration

```python
qa_config = {
    'questions_deadline': 'October 1, 2025',
    'response_posting_days': 5,        # Days to post responses after receiving
    'allow_anonymous': True,           # For fair disclosure
    'auto_categorize': True,           # Auto-categorize questions
    'classification': 'UNCLASSIFIED'
}
```

### Evaluation Scorecard Configuration

```python
scorecard_config = {
    # Offeror information
    'offeror_name': 'ABC Technology Solutions Inc.',
    'offeror_duns': '123456789',
    'business_size': 'Small Business',
    'socioeconomic_status': 'SDVOSB',
    
    # Evaluator information
    'evaluator_name': 'Dr. John Smith',
    'evaluator_title': 'Senior Technical Evaluator',
    'evaluator_org': 'SSEB',
    
    # Evaluation settings
    'source_selection_method': 'Best Value Trade-Off',  # or 'LPTA'
    'factor_weight': '40%',
    'page_count': '28',
    'proposal_date': 'October 15, 2025',
    'classification': 'UNCLASSIFIED'
}
```

---

## FAR Compliance

### Amendment Generator Compliance

✅ **FAR 14.208** - Amendment of Solicitations
- Proper amendment numbering
- Acknowledgment requirements
- Distribution to interested parties

✅ **FAR 15.206** - Amending Solicitations
- Amendment procedures for negotiated acquisitions
- Extension of proposal due dates
- Incorporation of changes

### Q&A Manager Compliance

✅ **FAR 15.201(f)** - Exchanges with Industry Before Receipt of Proposals
- Fair disclosure to all interested parties
- Timely responses
- Public posting requirements

✅ **FAR 5.102** - Availability of Solicitation Information
- Equal access to information
- SAM.gov posting

### Evaluation Scorecards Compliance

✅ **FAR 15.305** - Proposal Evaluation
- Evaluation factors from Section M
- Strengths/weaknesses/deficiencies documentation
- Risk assessment
- Adjectival ratings or pass/fail

✅ **FAR 15.308** - Source Selection Decision
- Documented evaluation rationale
- Comparative analysis
- Best value determination

---

## Advanced Features

### Q&A Manager: RAG-Powered Answering

The Q&A Manager can use your RAG system to generate answers based on solicitation content:

```python
# Initialize with RAG
from rag.vector_store import VectorStore
from rag.retriever import Retriever

vector_store = VectorStore(api_key)
vector_store.load()
retriever = Retriever(vector_store, top_k=3)

qa_agent = QAManagerAgent(api_key, retriever)

# Add question
q = qa_agent.add_question("What are the security requirements?")

# Generate answer using RAG (searches solicitation docs)
qa_agent.generate_answer(
    q['id'],
    solicitation_content="PWS and Section M content...",
    manual_answer=None  # Let RAG generate the answer
)
```

The agent will:
1. Query RAG for relevant solicitation content
2. Extract answer from PWS/Section M
3. Generate professional response
4. Flag if amendment needed

### Amendment Generator: Automatic Change Detection

```python
# Compare original vs revised PWS
original_pws = open('outputs/pws/performance_work_statement_v1.md').read()
revised_pws = open('outputs/pws/performance_work_statement_v2.md').read()

# Detect changes (future feature - manual for now)
changes = detect_changes(original_pws, revised_pws)

# Generate amendment automatically
amendment = agent.execute({
    'solicitation_info': solicitation_info,
    'amendment_number': agent.get_next_amendment_number(),
    'changes': changes,
    'config': {'auto_extension': True}
})
```

### Evaluation Scorecards: Batch Generation

```python
# Generate scorecards for multiple offerors
offerors = [
    {'name': 'Company A', 'duns': '111111111', 'size': 'Small'},
    {'name': 'Company B', 'duns': '222222222', 'size': 'Large'},
    {'name': 'Company C', 'duns': '333333333', 'size': 'Small'}
]

for offeror in offerors:
    # Generate all 4 factor scorecards
    full_set = agent.generate_full_scorecard_set(
        solicitation_info,
        section_m_content,
        {
            'offeror_name': offeror['name'],
            'offeror_duns': offeror['duns'],
            'business_size': offeror['size'],
            'evaluator_name': 'Evaluator Name'
        }
    )
    
    # Save each scorecard
    for factor, scorecard in full_set['scorecards'].items():
        filename = f"scorecard_{factor}_{offeror['name']}.md"
        agent.save_to_file(scorecard['content'], f'outputs/evaluations/{filename}')

print(f"Generated {len(offerors) * 4} scorecards")
```

---

## Testing

### Run Individual Tests

```bash
# Test Amendment Generator only
python -c "from scripts.test_post_solicitation_tools import test_amendment_generator; test_amendment_generator()"

# Test Q&A Manager only
python -c "from scripts.test_post_solicitation_tools import test_qa_manager; test_qa_manager()"

# Test Evaluation Scorecards only
python -c "from scripts.test_post_solicitation_tools import test_evaluation_scorecards; test_evaluation_scorecards()"
```

### Run Complete Test Suite

```bash
python scripts/test_post_solicitation_tools.py
```

### Expected Output

```
================================================================================
POST-SOLICITATION TOOLS TEST SUITE
================================================================================

✅ AMENDMENT GENERATOR TEST: PASSED
✅ Q&A MANAGER TEST: PASSED
✅ EVALUATION SCORECARD TEST: PASSED

================================================================================
TEST SUITE SUMMARY
================================================================================
Tests Passed: 3/3

🎉 ALL TESTS PASSED!
================================================================================
```

---

## Troubleshooting

### Issue: Q&A database not persisting

**Solution:** Save database after each session:
```python
agent.save_qa_database('outputs/qa/qa_database.json')
```

Load in next session:
```python
agent.load_qa_database('outputs/qa/qa_database.json')
```

---

### Issue: Amendment numbers not sequential

**Solution:** Use `get_next_amendment_number()`:
```python
next_num = agent.get_next_amendment_number()
# Returns "0001", "0002", etc. based on history
```

---

### Issue: Evaluation scorecards have placeholder text

**Solution:** This is expected! Scorecards are templates for evaluators to complete. Fill in:
- `[Evaluator: Complete this section]`
- Strengths/weaknesses/deficiencies
- Final ratings

---

### Issue: RAG not answering questions correctly

**Solution:** Provide more context:
```python
# Include full PWS/Section M content
qa_agent.generate_answer(
    question_id,
    solicitation_content=pws_content + section_m_content
)
```

---

## Best Practices

### Amendment Management

1. **Number sequentially** - 0001, 0002, 0003...
2. **Extend deadlines appropriately** - 7-14 days for significant changes
3. **Incorporate all Q&A** - Bundle Q&A responses into amendments
4. **Post promptly** - Within 5 business days of Q&A deadline
5. **Track acknowledgments** - Ensure all offerors acknowledge

### Q&A Management

1. **Respond consistently** - Use RAG to maintain consistency with RFP
2. **Maintain anonymity** - Don't reveal submitter identity (fair disclosure)
3. **Categorize questions** - Organize by topic for easy reference
4. **Flag amendment needs** - Identify questions requiring solicitation changes
5. **Post publicly** - All Q&A must be available to all offerors

### Evaluation Scorecards

1. **One scorecard per factor per offeror** - Don't mix factors
2. **Document thoroughly** - Every rating needs supporting rationale
3. **Use consistent criteria** - Follow Section M exactly
4. **Assess risk independently** - For each subfactor
5. **Peer review** - Have another evaluator review scores

---

## Integration with Existing System

The Post-Solicitation tools integrate with your existing workflow:

```
Pre-Solicitation (Existing) → Solicitation (Existing) → Post-Solicitation (NEW!)
├── Sources Sought          ├── PWS/SOW/SOO           ├── Q&A Manager
├── RFI                     ├── QASP                  ├── Amendment Generator
├── Acquisition Plan        ├── Section L             └── Evaluation Scorecards
├── IGCE                    ├── Section M
├── Pre-Sol Notice          ├── SF-33
└── Industry Day            └── Complete Package
```

### Typical Timeline

```
Week 0:  Post RFP to SAM.gov
Week 1:  Vendors submit questions → Use Q&A Manager
Week 2:  Generate Q&A document → Identify amendment needs
Week 3:  Generate Amendment 0001 → Extend deadline 7-14 days
Week 4:  Additional questions → Update Q&A database
Week 5:  Final Q&A document → Amendment 0002 (if needed)
Week 6:  Proposals due
Week 7:  Generate evaluation scorecards → Distribute to SSEB
Week 8-10: Conduct evaluations → Complete scorecards
Week 11: Consensus meeting → Comparative analysis
Week 12: Source selection decision → Prepare award docs
```

---

## Future Enhancements

### Planned Features

1. **Automated Change Detection**
   - Compare document versions
   - Auto-generate change descriptions
   - Redline generation

2. **Q&A Analytics**
   - Question patterns analysis
   - Vendor engagement tracking
   - Amendment impact prediction

3. **Evaluation Consensus Tool**
   - Aggregate individual scores
   - Identify outliers
   - Facilitate consensus meetings

4. **SSDD Generator**
   - Source Selection Decision Document
   - Comparative analysis
   - Trade-off narratives

5. **Debriefing Generator**
   - Post-award debriefing materials
   - Vendor-specific feedback
   - Lessons learned

---

## Summary

The Post-Solicitation tools provide:

✅ **Amendment Management** - Professional solicitation modifications  
✅ **Q&A Tracking** - Comprehensive question/answer system  
✅ **Evaluation Support** - FAR-compliant proposal scoring  
✅ **RAG Integration** - Intelligent answer generation  
✅ **Fair Disclosure** - Equal access to information  
✅ **Complete Documentation** - Audit-ready records  

**Next Steps:**
1. Run test suite: `python scripts/test_post_solicitation_tools.py`
2. Review outputs in `outputs/amendments/`, `outputs/qa/`, `outputs/evaluations/`
3. Integrate into your actual solicitations
4. Customize templates as needed

For questions or issues, refer to the troubleshooting section or review the test script examples.

---

**Document Version:** 1.0  
**Last Updated:** October 2025  
**Author:** DoD Contracting Automation Team

