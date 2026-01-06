# Phase 6: Advanced Agent Comparison & Selection - Implementation Complete

**Version:** 1.0
**Date:** 2025-11-19
**Status:** ✅ IMPLEMENTED - Ready for Integration Testing

---

## Executive Summary

Phase 6 introduces **advanced agent comparison and selection** capabilities, enabling users to:
- Generate the same document with multiple AI agents/models
- Compare results side-by-side with detailed metrics
- Select optimal agent configurations based on quality, speed, or other criteria
- A/B test different model parameters (temperature, etc.)

This transforms the system from single-path generation to **intelligent multi-variant testing**, allowing users to find the best AI configuration for each document type.

---

## What Was Built

### 1. Backend Infrastructure

#### Agent Comparison Service
**File:** `backend/services/agent_comparison_service.py`

**Key Classes:**
- `AgentVariant` - Configuration for a specific agent/model combination
- `ComparisonResult` - Stores results for a single variant
- `ComparisonTask` - Manages multi-variant comparison
- `AgentComparisonService` - Main service for running comparisons

**Features:**
- Parallel generation of multiple variants
- Quality scoring and metrics calculation
- Winner selection by multiple criteria
- Automatic cleanup of old comparisons

#### API Endpoints
**File:** `backend/main.py` (lines 1566-1739)

**Endpoints:**
1. `POST /api/comparison/start` - Start a new comparison
2. `GET /api/comparison/status/{task_id}` - Check comparison progress
3. `GET /api/comparison/results/{task_id}` - Get full results
4. `GET /api/comparison/winner/{task_id}` - Get winning variant

### 2. Frontend Components

#### ComparisonViewer
**File:** `dod_contracting_front_end/src/components/comparison/ComparisonViewer.tsx`

**Features:**
- **3 View Modes:**
  - Side-by-side: Compare top 2 variants
  - Stacked: View all variants vertically
  - Metrics Only: Focus on statistics

- **Winners Dashboard:**
  - Best Quality (trophy icon)
  - Fastest Generation (zap icon)
  - Most Detailed (file icon)
  - Best Citations (quote icon)

- **Sorting Options:**
  - Quality Score
  - Generation Speed
  - Word Count
  - Citations Count

- **Variant Cards:**
  - Content preview with scrolling
  - Detailed metrics display
  - Model badge with color coding
  - Select winner button

#### Agent Selector
**File:** `dod_contracting_front_end/src/components/comparison/AgentSelector.tsx`

**Features:**
- **Model Selection:**
  - Claude Opus 4 (most capable, $$$)
  - Claude Sonnet 4 (balanced, $$)
  - Claude Haiku 4 (fastest, $)

- **Comparison Modes:**
  - Compare different models
  - Compare temperature variations
  - Use specialized vs generic agents

- **Temperature Presets:**
  - Focused (0.3) - Deterministic output
  - Balanced (0.7) - Default creativity
  - Creative (1.0) - Varied output

- **Preview:**
  - Estimated costs
  - Variant count
  - Configuration summary

---

## Architecture

### Comparison Flow

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                       │
│  ┌───────────────────────────────────────────────────┐ │
│  │            Agent Selector Dialog                  │ │
│  │  • Select models to compare                       │ │
│  │  • Choose temperature settings                    │ │
│  │  • Configure comparison mode                      │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│             POST /api/comparison/start                  │
│  {                                                      │
│    documentName: "Section L",                          │
│    requirements: "...",                                │
│    variants: [                                         │
│      { model: "claude-opus-4", temp: 0.7 },           │
│      { model: "claude-sonnet-4", temp: 0.7 },         │
│      { model: "claude-haiku-4", temp: 0.7 }           │
│    ]                                                   │
│  }                                                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│          Agent Comparison Service                       │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Parallel Generation (asyncio)                    │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │ │
│  │  │ Variant 1│  │ Variant 2│  │ Variant 3│       │ │
│  │  │  Opus    │  │  Sonnet  │  │  Haiku   │       │ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘       │ │
│  │       │             │             │              │ │
│  │       └─────────────┴─────────────┘              │ │
│  │                     │                            │ │
│  │            Quality Scoring Engine                │ │
│  │  • Word count • Citations • Compliance           │ │
│  │  • Readability • FAR references                  │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│          GET /api/comparison/results/{id}               │
│  {                                                      │
│    results: [                                          │
│      {                                                 │
│        variant_name: "Claude Opus 4",                 │
│        quality_score: 92,                             │
│        generation_time: 14.3s,                        │
│        word_count: 1847,                              │
│        citations_count: 8,                            │
│        content: "..."                                 │
│      },                                               │
│      ...                                              │
│    ]                                                  │
│  }                                                    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Comparison Viewer                      │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Winners Dashboard                                │ │
│  │  🏆 Best Quality: Opus (92)                      │ │
│  │  ⚡ Fastest: Haiku (8.7s)                        │ │
│  │  📝 Most Detailed: Opus (1847 words)            │ │
│  │  💬 Best Citations: Sonnet (9 citations)        │ │
│  └───────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Side-by-Side View                               │ │
│  │  ┌────────────────┐  ┌────────────────┐         │ │
│  │  │ Variant 1      │  │ Variant 2      │         │ │
│  │  │ Quality: 92    │  │ Quality: 88    │         │ │
│  │  │ Speed: 14.3s   │  │ Speed: 10.1s   │         │ │
│  │  │ [Content...]   │  │ [Content...]   │         │ │
│  │  │ [Select]       │  │ [Select]       │         │ │
│  │  └────────────────┘  └────────────────┘         │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. Multi-Model Comparison
Compare output from different Claude models:
- **Opus 4**: Highest quality, best for complex documents
- **Sonnet 4**: Balanced performance and cost
- **Haiku 4**: Fastest and most cost-effective

### 2. Temperature Variation Testing
Test same model with different creativity levels:
- **0.3 (Focused)**: Deterministic, consistent output
- **0.7 (Balanced)**: Default creativity level
- **1.0 (Creative)**: More varied, creative responses

### 3. Quality Metrics
Each variant is scored on:
- **Quality Score (0-100)**: Overall quality rating
- **Generation Time**: Speed in seconds
- **Word Count**: Length/detail level
- **Citations Count**: Number of regulatory references

### 4. Winner Selection
Automatically identify best variant by:
- Highest quality score
- Fastest generation
- Most detailed (word count)
- Best citations

### 5. Visual Comparison
Three view modes for different analysis needs:
- **Side-by-Side**: Quick comparison of top 2
- **Stacked**: Detailed review of all variants
- **Metrics Only**: Focus on statistics

---

## Integration Points

### With Existing Systems

1. **Agent Router** (`backend/services/agent_router.py`)
   - Comparison service uses existing agent routing
   - Leverages specialized agents when configured

2. **RAG Service** (`backend/services/rag_service.py`)
   - Each variant gets same RAG context
   - Ensures fair comparison

3. **Quality Agent** (`backend/agents/quality_agent.py`)
   - Can be integrated for more sophisticated scoring
   - Currently uses simplified quality calculation

4. **Generation Coordinator** (`backend/services/generation_coordinator.py`)
   - Comparison runs independently
   - Can compare coordinator vs direct agent calls

---

## Usage Example

### Starting a Comparison

```typescript
// Frontend Code
const handleStartComparison = async () => {
  const response = await fetch('/api/comparison/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      documentName: 'Section L - Instructions to Offerors',
      requirements: 'Generate comprehensive Section L...',
      variants: [
        {
          id: 'opus-variant',
          name: 'Claude Opus 4',
          model: 'claude-opus-4',
          temperature: 0.7,
          description: 'Most capable model'
        },
        {
          id: 'sonnet-variant',
          name: 'Claude Sonnet 4',
          model: 'claude-sonnet-4',
          temperature: 0.7,
          description: 'Balanced performance'
        },
        {
          id: 'haiku-variant',
          name: 'Claude Haiku 4',
          model: 'claude-haiku-4',
          temperature: 0.7,
          description: 'Fastest model'
        }
      ]
    })
  });

  const { task_id } = await response.json();
  pollComparisonStatus(task_id);
};
```

### Viewing Results

```typescript
// Poll for completion
const results = await fetch(`/api/comparison/results/${task_id}`).then(r => r.json());

// Display in ComparisonViewer
<ComparisonViewer
  comparisonData={results}
  onSelectWinner={(variantId) => {
    // Use winning variant's content
    applySelectedVariant(variantId);
  }}
/>
```

---

## Performance Considerations

### Parallel Generation
- All variants generated simultaneously using `asyncio.gather()`
- Total time ≈ slowest variant (not sum of all)
- Example: 3 variants @ 10s each = ~10s total (not 30s)

### Cost Implications
- Each variant = 1 API call
- Opus costs more than Sonnet/Haiku
- Users can see estimated costs before starting

### Memory Usage
- Comparison results stored in-memory
- Auto-cleanup after 24 hours
- Manual cleanup available via service method

---

## Testing Scenarios

### Scenario 1: Model Comparison
**Goal:** Find best model for Section L generation

**Setup:**
- Document: Section L - Instructions to Offerors
- Variants: Opus, Sonnet, Haiku (all at temp 0.7)
- Requirements: Standard Section L with evaluation criteria

**Expected Results:**
- Opus: Highest quality (90-95), slowest (12-15s)
- Sonnet: Good quality (85-90), medium speed (8-12s)
- Haiku: Lower quality (75-85), fastest (5-8s)

### Scenario 2: Temperature Testing
**Goal:** Find optimal temperature for consistency

**Setup:**
- Document: Section M - Evaluation Factors
- Variants: Sonnet at 0.3, 0.7, 1.0
- Requirements: Evaluation framework aligned with Section L

**Expected Results:**
- 0.3: Most consistent, formal language
- 0.7: Balanced creativity and consistency
- 1.0: Most varied, potentially creative solutions

### Scenario 3: Specialized vs Generic
**Goal:** Validate specialized agent value

**Setup:**
- Document: Section H - Special Contract Requirements
- Variants: Specialized H agent vs Generic generation
- Model: Same (Sonnet) for both

**Expected Results:**
- Specialized: Higher quality, better citations
- Generic: Faster, less detailed

---

## Future Enhancements

### Phase 6.5: Advanced Comparison
1. **Quality Agent Integration**
   - Use full quality_agent.py for scoring
   - Compliance checking per variant
   - FAR/DFARS validation

2. **Historical Tracking**
   - Save comparison results to database
   - Track winning configurations per document type
   - Recommend best agents based on history

3. **Cost Tracking**
   - Real API cost calculation
   - Budget limits and warnings
   - Cost vs quality optimization

4. **A/B Testing Dashboard**
   - Aggregate statistics across comparisons
   - Model performance trends
   - Document type recommendations

5. **Custom Variants**
   - User-defined agent configurations
   - Custom prompts per variant
   - Fine-tuned model integration

---

## Files Created

### Backend
1. `backend/services/agent_comparison_service.py` (407 lines)
   - Core comparison service
   - Variant management
   - Quality scoring

2. `backend/main.py` (modified)
   - Added 4 comparison endpoints
   - Request/response models
   - Error handling

### Frontend
1. `dod_contracting_front_end/src/components/comparison/ComparisonViewer.tsx` (432 lines)
   - Main comparison UI
   - 3 view modes
   - Winners dashboard
   - Variant cards

2. `dod_contracting_front_end/src/components/comparison/AgentSelector.tsx` (362 lines)
   - Configuration dialog
   - Model selection
   - Temperature presets
   - Preview panel

### Documentation
1. `PHASE_6_SUMMARY.md` (this file)
   - Complete feature documentation
   - Integration guide
   - Usage examples

---

## Success Criteria

- ✅ Backend service implemented with parallel generation
- ✅ API endpoints created and tested
- ✅ Frontend components built with rich UI
- ✅ Multiple comparison modes supported
- ✅ Quality metrics calculated
- ✅ Winner selection by criteria
- ⏳ Integration with LiveEditor (pending)
- ⏳ End-to-end testing (pending)

---

## Next Steps

### Integration with LiveEditor

To complete Phase 6, integrate comparison features into the main editor:

1. Add "Compare Agents" button to LiveEditor toolbar
2. Open AgentSelector dialog on click
3. Run comparison in background
4. Show ComparisonViewer in modal or new tab
5. Allow user to select winner and replace content

**Example Integration:**

```typescript
// In LiveEditor.tsx
const [showComparison, setShowComparison] = useState(false);
const [comparisonResults, setComparisonResults] = useState(null);

// Add to toolbar
<Button onClick={() => setShowComparison(true)}>
  <GitCompare className="h-4 w-4 mr-2" />
  Compare Agents
</Button>

// Dialogs
{showComparison && (
  <AgentSelector
    documentName={activeSection}
    isOpen={showComparison}
    onClose={() => setShowComparison(false)}
    onStartComparison={(variants) => {
      // Start comparison
      startComparison(activeSection, currentText, variants);
    }}
  />
)}

{comparisonResults && (
  <ComparisonViewer
    comparisonData={comparisonResults}
    onSelectWinner={(variantId) => {
      // Apply winner's content
      const winner = comparisonResults.results.find(r => r.variant_id === variantId);
      handleTextChange(winner.content);
      setComparisonResults(null);
    }}
  />
)}
```

---

## Conclusion

Phase 6 successfully implements **advanced agent comparison and selection**, providing users with powerful tools to:
- Test different AI models side-by-side
- Optimize agent configurations for specific documents
- Make data-driven decisions about model selection
- Balance quality, speed, and cost

The system is now ready for integration testing and can be easily connected to the existing LiveEditor interface.

**Status:** ✅ **Implementation Complete - Ready for Integration**

---

**Document Version:** 1.0
**Last Updated:** 2025-11-19
**Prepared By:** Claude Code
