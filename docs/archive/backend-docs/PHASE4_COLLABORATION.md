# Phase 4: Agent Collaboration

## Overview

Phase 4 implements agent collaboration capabilities that enable specialized agents to reference each other's work, share context, and generate documents in logical dependency order for improved cross-document consistency.

## Architecture

### Key Components

#### 1. ContextManager (`backend/services/context_manager.py`)

Manages shared context across agent generations for cross-referencing and collaboration.

**Features:**
- Stores generated content temporarily with metadata
- Provides retrieval API for dependent documents
- Tracks cross-references between documents
- Manages memory usage (configurable content length limit)
- Thread-safe singleton pattern for global access

**Key Classes:**
- `GeneratedContent`: Represents generated content with metadata, word count, character count
- `CrossReference`: Represents a reference from one document to another
- `ContextManager`: Main service managing the context pool

**API:**
```python
# Add content to pool
cm.add_content(doc_name="Section L", content="...", metadata={})

# Retrieve content
content = cm.get_content("Section L")

# Get related content for dependencies
related = cm.get_related_content(
    doc_name="Section M",
    dependency_list=["Section L", "PWS"],
    max_summary_length=1000
)

# Track cross-references
cm.add_cross_reference(
    from_doc="Section M",
    to_doc="Section L",
    reference_text="Evaluation procedures"
)

# Get statistics
stats = cm.get_statistics()

# Clear for next task
cm.clear()
```

#### 2. DependencyGraph (`backend/services/dependency_graph.py`)

Manages document dependencies and determines optimal generation order using topological sorting and batch parallelization.

**Features:**
- Loads dependency configuration from JSON
- Performs topological sort for generation order
- Identifies batches of independent documents for parallel generation
- Validates document selection for missing dependencies
- Detects circular dependencies
- Suggests additional related documents

**Key Classes:**
- `DocumentNode`: Represents a document with dependencies and priority
- `DependencyGraph`: Main service managing the dependency graph

**API:**
```python
# Get generation order (returns list of batches)
batches = dg.get_generation_order(["Section L", "Section M", "Section H"])
# Example output: [["PWS"], ["Section L"], ["Section M", "Section H"]]

# Get direct dependencies
deps = dg.get_dependencies("Section M")

# Get dependents
dependents = dg.get_dependents("PWS")

# Validate selection
result = dg.validate_selection(["Section L", "Section M"])

# Get document info
info = dg.get_document_info("Section M")
```

#### 3. BaseAgent Collaboration Methods (`backend/agents/base_agent.py`)

Provides collaboration methods for all agents that inherit from BaseAgent.

**New Methods:**
```python
# Check if collaboration is enabled
has_collab = agent.has_collaboration_enabled()

# Get related content from dependencies
related = agent.get_related_content(
    dependency_list=["PWS", "Acq Plan"],
    max_length=1000
)

# Create formatted reference
ref = agent.reference_section(
    target_doc="Section L",
    reference_text="Evaluation procedures"
)
# Returns: "[See Section L: Evaluation procedures]"

# Build enhanced prompt with dependency context
prompt = agent.build_collaborative_prompt(
    base_requirements="Generate Section M...",
    dependencies={"Section L": "...", "PWS": "..."},
    context="FAR 15.304 content..."
)
```

#### 4. GenerationCoordinator Updates (`backend/services/generation_coordinator.py`)

Enhanced to support batch-based generation with collaboration.

**Features:**
- Conditional collaboration mode (enabled/disabled)
- Batch-by-batch generation respecting dependencies
- Progress tracking across batches
- Parallel generation within batches
- Collaboration metadata collection

**Batch Generation Flow:**
1. Clear context manager for new task
2. Get generation batches from DependencyGraph
3. For each batch:
   - Generate all documents in batch (parallel if multiple)
   - Call specialized agents with `generate_with_collaboration()`
   - Add generated content to context manager
   - Track progress
4. Collect collaboration metadata
5. Return results with metadata

#### 5. Enhanced Specialized Agents

**Section L Generator** (`backend/agents/section_l_generator_agent.py`):
- Added `generate_with_collaboration()` method
- Extracts PWS and Acquisition Plan dependencies
- Incorporates evaluation approach from dependencies

**Section M Generator** (`backend/agents/section_m_generator_agent.py`):
- Added `generate_with_collaboration()` method
- Extracts PWS, Section L, and Acquisition Plan dependencies
- Derives evaluation method from Section L
- Adds detailed cross-reference section

**Section H Generator** (`backend/agents/section_h_generator_agent.py`):
- Added `generate_with_collaboration()` method
- References PWS, Section L, and Section M for consistency
- Adds cross-reference section

## Configuration

### Document Dependencies (`backend/config/document_dependencies.json`)

Defines the dependency graph structure:

```json
{
  "dependencies": {
    "Section C - Performance Work Statement": {
      "priority": 1,
      "depends_on": ["Acquisition Plan"],
      "description": "Technical requirements"
    },
    "Section L - Instructions to Offerors": {
      "priority": 2,
      "depends_on": ["Section C - Performance Work Statement", "Acquisition Plan"],
      "references": ["PWS requirements", "Acquisition approach"]
    },
    "Section M - Evaluation Factors": {
      "priority": 3,
      "depends_on": [
        "Section C - Performance Work Statement",
        "Section L - Instructions to Offerors",
        "Acquisition Plan"
      ],
      "references": ["Technical requirements", "Proposal format", "Evaluation approach"]
    }
  },
  "validation_rules": {
    "warn_if_missing": {
      "Section L - Instructions to Offerors": ["Section M - Evaluation Factors"],
      "Section M - Evaluation Factors": ["Section H - Special Contract Requirements"]
    }
  },
  "cross_reference_patterns": {
    "section_l_to_pws": "Technical requirements defined in Section C",
    "section_m_to_section_l": "Proposal format per Section L"
  }
}
```

**Configuration Fields:**
- `priority`: Lower numbers generate first (within dependency constraints)
- `depends_on`: List of documents this document depends on
- `references`: Types of references this document makes
- `description`: Brief description of document purpose
- `validation_rules`: Rules for warning about missing related documents
- `cross_reference_patterns`: Common reference patterns for agents

## Frontend Integration

### DependencyGraph Component (`dod_contracting_front_end/src/components/DependencyGraph.tsx`)

React component visualizing collaboration metadata.

**Features:**
- Overview statistics (batches, documents, cross-references, total time)
- Generation flow visualization with batch indicators
- Cross-reference listings
- Context pool statistics
- Responsive design

**Props:**
```typescript
interface CollaborationMetadata {
  enabled: boolean;
  generation_order: string[];
  batch_count: number;
  batches: Array<{
    batch_number: number;
    documents: string[];
    generation_time_seconds: number;
  }>;
  cross_references: Array<{
    from: string;
    to: string;
    reference: string;
    created_at: string;
  }>;
  context_pool_stats: {
    document_count: number;
    total_words: number;
    total_characters: number;
    cross_reference_count: number;
    documents: string[];
  };
}
```

### LiveEditor Integration

**Updates:**
- Added `collaborationMetadata` prop
- New "Dependencies" tab (conditionally shown when collaboration enabled)
- DependenciesView component displays the DependencyGraph

### AIContractingUI Integration

**Updates:**
- Added `collaborationMetadata` state
- Stores collaboration metadata from API response
- Passes metadata to LiveEditor component

## API Updates

### Generate Documents Endpoint (`POST /api/generate-documents`)

**Response includes collaboration metadata:**
```json
{
  "sections": {
    "Section L": "...",
    "Section M": "..."
  },
  "citations": [...],
  "agent_metadata": {...},
  "collaboration_metadata": {
    "enabled": true,
    "generation_order": ["PWS", "Section L", "Section M"],
    "batch_count": 3,
    "batches": [
      {
        "batch_number": 1,
        "documents": ["PWS"],
        "generation_time_seconds": 12.5
      },
      {
        "batch_number": 2,
        "documents": ["Section L"],
        "generation_time_seconds": 10.3
      },
      {
        "batch_number": 3,
        "documents": ["Section M"],
        "generation_time_seconds": 11.8
      }
    ],
    "cross_references": [
      {
        "from": "Section L",
        "to": "PWS",
        "reference": "Technical requirements",
        "created_at": "2025-01-15T10:30:00"
      }
    ],
    "context_pool_stats": {
      "document_count": 3,
      "total_words": 5432,
      "total_characters": 28156,
      "cross_reference_count": 2,
      "documents": ["PWS", "Section L", "Section M"]
    }
  }
}
```

## Usage

### Enabling Collaboration

Collaboration is enabled in the GenerationCoordinator when:
1. `enable_collaboration=True` flag is set
2. `dependency_graph` is provided
3. `context_manager` is provided

```python
from backend.services.generation_coordinator import GenerationCoordinator
from backend.services.dependency_graph import get_dependency_graph
from backend.services.context_manager import get_context_manager

coordinator = GenerationCoordinator(
    api_key=api_key,
    retriever=retriever,
    enable_collaboration=True,
    dependency_graph=get_dependency_graph(),
    context_manager=get_context_manager()
)
```

### Generation Flow

**With Collaboration:**
1. User selects documents to generate
2. DependencyGraph calculates generation order and batches
3. GenerationCoordinator generates batch by batch:
   - Batch 1: Documents with no dependencies (can run in parallel)
   - Batch 2: Documents depending only on Batch 1 (can run in parallel)
   - Batch 3: Documents depending on Batch 1 or 2 (can run in parallel)
   - etc.
4. Each document can access previously generated content via ContextManager
5. Agents create cross-references to related documents
6. Frontend displays collaboration metadata in Dependencies tab

**Without Collaboration (Legacy):**
1. Documents generated sequentially in user-selected order
2. No cross-referencing
3. No dependency resolution

## Testing

### Unit Tests (`backend/tests/test_phase4_collaboration.py`)

Comprehensive test suite covering:
- **ContextManager** (11 tests)
  - Initialization, content storage, truncation
  - Related content retrieval with missing dependencies
  - Cross-reference tracking and filtering
  - Statistics and clearing

- **DependencyGraph** (10 tests)
  - Configuration loading
  - Dependency and dependent retrieval
  - Generation order with simple and complex dependencies
  - Parallel batch identification
  - Validation and circular dependency detection
  - Document suggestions

- **BaseAgent Collaboration** (5 tests)
  - Collaboration enablement check
  - Reference formatting and tracking
  - Related content retrieval
  - Collaborative prompt building

- **Collaborative Flow** (1 integration test)
  - Complete flow: add content → retrieve → reference → stats

**Run tests:**
```bash
cd backend
pytest tests/test_phase4_collaboration.py -v
```

**Test Results:** ✅ 27/27 passed

## Benefits

### Improved Quality
- Documents reference each other consistently
- No conflicting information across documents
- Proper citation of dependencies

### Better Traceability
- Clear dependency relationships
- Cross-reference tracking
- Generation order visibility

### Performance Optimization
- Parallel generation of independent documents
- Batch processing reduces total time
- Efficient context sharing

### User Experience
- Visual dependency graph
- Generation flow transparency
- Cross-reference navigation

## Backward Compatibility

Phase 4 maintains full backward compatibility:
- Legacy sequential generation still works when `enable_collaboration=False`
- Frontend gracefully handles missing collaboration metadata
- Dependencies tab only shown when collaboration is enabled
- Existing agents continue to work without collaboration methods

## Future Enhancements

Potential improvements:
1. **Dynamic Dependency Detection**: Analyze content to detect missing dependencies
2. **Smart Summarization**: Use LLM to create better summaries of dependent content
3. **Dependency Visualization**: Interactive graph showing document relationships
4. **Version Control**: Track how changes in one document affect dependents
5. **Circular Dependency Resolution**: Strategies for handling circular references
6. **Partial Regeneration**: Regenerate only documents affected by changes

## Troubleshooting

### Issue: Documents generated in wrong order
**Solution:** Check `document_dependencies.json` for correct `depends_on` relationships

### Issue: Missing cross-references
**Solution:** Ensure agents call `reference_section()` when referencing other documents

### Issue: Content truncation warnings
**Solution:** Adjust `max_content_length` in ContextManager (default: 10000 characters)

### Issue: Circular dependency error
**Solution:** Review dependency graph - no document should depend on itself directly or indirectly

## Performance Considerations

- **Memory Usage**: ContextManager stores up to `max_content_length` per document
- **Parallel Limits**: Limited by asyncio concurrency (typically 5-10 simultaneous)
- **Network**: Each document requires LLM API call (can be expensive for large batches)
- **Caching**: Context pool cleared between generation tasks to prevent memory leaks

## Configuration Best Practices

1. **Set Priorities Wisely**: Lower priority = earlier generation
2. **Minimize Dependencies**: Only declare true dependencies
3. **Group Related Docs**: Documents with similar dependencies batch together
4. **Validate Config**: Use `validate_selection()` before generation
5. **Document Patterns**: Define common cross-reference patterns for consistency

## Migration from Phase 3

No migration required - Phase 4 is additive:
1. Phase 3 code continues to work unchanged
2. Enable collaboration by setting flags in GenerationCoordinator
3. Add dependency configuration to `document_dependencies.json`
4. Specialized agents automatically use collaboration when available
5. Frontend displays Dependencies tab when metadata is present

## Summary

Phase 4 Agent Collaboration transforms the system from independent document generation to an intelligent, context-aware generation pipeline. Documents now "know" about each other, reference correctly, and generate in optimal order for maximum consistency and quality.
