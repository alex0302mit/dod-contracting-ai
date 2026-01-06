# Phase 2 Quick Start Guide

## What's New in Phase 2?

Phase 2 adds intelligent document generation using 30+ specialized agents:

✅ **Specialized Agents**: Each document type routes to its specialized agent
✅ **Phase Detection**: Automatic detection of procurement phase
✅ **Smart Recommendations**: Suggests missing required documents
✅ **Progress Tracking**: Real-time updates during generation
✅ **Quality Improvements**: Better FAR/DFARS compliance

## New API Endpoints

### 1. Analyze Generation Plan
**Before generating**, call this to get recommendations:

```bash
POST /api/analyze-generation-plan
```

**Request:**
```json
{
  "document_names": [
    "Section L - Instructions to Offerors",
    "Section M - Evaluation Factors"
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "analysis": {
    "primary_phase": "solicitation",
    "confidence": 1.0,
    "mixed_phases": false,
    "recommendations": [
      "Consider adding Section B (required for complete solicitation)",
      "Consider adding Section H (required for complete solicitation)"
    ],
    "validation": {
      "is_complete": false,
      "completeness_percentage": 25.0,
      "missing_required": ["Section B", "Section H", "Section I", "Section K"]
    }
  }
}
```

### 2. Generate Documents (Enhanced)
The existing endpoint now uses specialized agents:

```bash
POST /api/generate-documents
```

**Request:** (same as before)
```json
{
  "assumptions": [
    {"text": "Contract type: Firm Fixed Price (FFP)", "source": "User"},
    {"text": "Evaluation approach: BVTO", "source": "Analysis"}
  ],
  "documents": [
    {
      "name": "Section L - Instructions to Offerors",
      "category": "required",
      "linkedAssumptions": []
    }
  ]
}
```

**Enhanced Response:**
```json
{
  "task_id": "abc-123",
  "message": "Document generation started",
  "documents_requested": 1
}
```

Then poll `/api/generation-status/{task_id}` for results including:
- `agent_metadata`: Which agent generated each document
- `phase_info`: Detected phase and confidence
- `citations`: Deduplicated citations

## Feature Flags

### Enable/Disable Specialized Agents

```bash
# Use specialized agents (default)
export USE_AGENT_BASED_GENERATION=true

# Use generic Claude only
export USE_AGENT_BASED_GENERATION=false
```

## Testing Phase 2

### Run Integration Tests
```bash
cd "/Users/alejandromaldonado/Desktop/AI_Phantom_Fellow_Course/Basic use case market research LLM automation"

# Phase 2 integration tests
python backend/tests/test_phase2_integration.py
```

Expected output:
```
✅ Coordinator initialization: PASSED
✅ Phase analysis (solicitation): PASSED
✅ Mixed phase detection: PASSED
✅ Phase recommendations: PASSED
✅ Completeness validation: PASSED
✅ Generic mode (no specialized agents): PASSED

RESULTS: 6 passed, 0 failed
```

### Run All Tests
```bash
# Phase 1 infrastructure
python backend/tests/run_phase1_tests.py

# Phase 2 integration
python backend/tests/test_phase2_integration.py
```

## Example Usage Scenarios

### Scenario 1: Complete Pre-Solicitation Package
```bash
curl -X POST http://localhost:8000/api/analyze-generation-plan \
  -H "Content-Type: application/json" \
  -d '{
    "document_names": [
      "Market Research Report",
      "Acquisition Plan",
      "Performance Work Statement (PWS)",
      "Independent Government Cost Estimate (IGCE)"
    ]
  }'
```

**Response:**
```json
{
  "primary_phase": "pre_solicitation",
  "confidence": 1.0,
  "validation": {
    "is_complete": true,
    "completeness_percentage": 100.0
  },
  "recommendations": []
}
```

### Scenario 2: Incomplete Solicitation
```bash
curl -X POST http://localhost:8000/api/analyze-generation-plan \
  -H "Content-Type: application/json" \
  -d '{
    "document_names": [
      "Section L - Instructions to Offerors",
      "Section M - Evaluation Factors"
    ]
  }'
```

**Response:**
```json
{
  "primary_phase": "solicitation",
  "confidence": 1.0,
  "validation": {
    "is_complete": false,
    "completeness_percentage": 25.0,
    "missing_required": [
      "SF33 - Solicitation, Offer and Award",
      "Section B - Supplies/Services and Prices",
      "Section C - Performance Work Statement",
      "Section H - Special Contract Requirements",
      "Section I - Contract Clauses",
      "Section K - Representations and Certifications"
    ]
  }
}
```

### Scenario 3: Mixed Phases Warning
```bash
curl -X POST http://localhost:8000/api/analyze-generation-plan \
  -H "Content-Type: application/json" \
  -d '{
    "document_names": [
      "Market Research Report",
      "Section L - Instructions to Offerors",
      "Evaluation Scorecard"
    ]
  }'
```

**Response:**
```json
{
  "primary_phase": "solicitation",
  "mixed_phases": true,
  "warnings": [
    "Mixed phases detected: Documents from pre_solicitation, solicitation, post_solicitation. Consider generating documents in phase-appropriate batches."
  ]
}
```

## Agent Coverage

Phase 2 includes routing for these specialized agents:

**Solicitation Sections:**
- Section L Generator (Instructions to Offerors)
- Section M Generator (Evaluation Factors)
- Section B Generator (Supplies/Services)
- Section H Generator (Special Contract Requirements)
- Section I Generator (Contract Clauses)
- Section K Generator (Representations and Certifications)

**Work Statements:**
- PWS Writer Agent (Performance Work Statement)
- SOW Writer Agent (Statement of Work)
- SOO Writer Agent (Statement of Objectives)

**Supporting Documents:**
- IGCE Generator (Independent Government Cost Estimate)
- Market Research Report Generator
- Acquisition Plan Generator
- Sources Sought Generator
- Pre-Solicitation Notice Generator
- Industry Day Generator
- RFI Generator

**Evaluation Documents:**
- Source Selection Plan Generator
- Evaluation Scorecard Generator
- SSDD Generator (Source Selection Decision Document)
- PPQ Generator (Past Performance Questionnaire)

**Forms:**
- SF26 Generator (Award/Contract)
- Award Notification Generator
- Debriefing Generator

## Fallback Behavior

If a specialized agent:
- Is not available for a document type
- Fails during generation
- Has an incompatible constructor

The system automatically falls back to **generic Claude generation** (same quality as Phase 1).

## Troubleshooting

### Issue: "Phase detection not working"
**Solution:** Ensure `USE_AGENT_BASED_GENERATION=true` in environment

### Issue: "All documents using GenericClaude"
**Solution:** Check that:
1. Agents are being imported correctly
2. Retriever is initialized in RAG service
3. No errors in agent instantiation (check logs)

### Issue: "Mixed phase warnings"
**Solution:** This is expected! The system is helping you:
- Generate documents in phase-appropriate batches
- Understand if you're mixing different procurement stages
- Consider the proper sequencing

## What's Next?

### Phase 3: Frontend Integration
- Display phase information to users
- Show which agents are being used
- Add visual indicators for specialized vs. generic
- Show completeness percentage

### Phase 4: Agent Collaboration
- Cross-reference between documents
- Dependency-based generation ordering
- Shared context between agents

### Phase 5: Quality Assurance
- Automated quality validation
- Iterative refinement
- Quality scoring

## Support

For issues or questions:
1. Check test results: `python backend/tests/test_phase2_integration.py`
2. Review logs in backend console
3. Check API docs: http://localhost:8000/docs
4. Review [PHASE_2_SUMMARY.md](PHASE_2_SUMMARY.md)
