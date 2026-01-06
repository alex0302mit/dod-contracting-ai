# Phase 4: Agent Collaboration - Detailed Implementation Plan

**Version:** 1.0
**Date:** 2025-11-07
**Status:** 📋 PLANNING - Awaiting Approval
**Estimated Duration:** 2-3 days development + 1 day testing

---

## Executive Summary

Phase 4 introduces **agent collaboration** toto reference each other's work, enable specialized agents  share context, and generate documents in logical dependency order. This transforms the system from parallel independent generation to coordinated sequential generation with cross-document consistency.

### Current State (Phase 3)
```
┌─────────────────────────────────────────────────┐
│         Generation Coordinator                   │
│  ┌──────────────────────────────────────────┐  │
│  │  Parallel Generation (No Dependencies)   │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐       │
│  │Sec L │  │Sec M │  │Sec H │  │ PWS  │       │
│  │Agent │  │Agent │  │Agent │  │Agent │       │
│  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘       │
│     │         │         │         │            │
│     └─────────┴─────────┴─────────┘            │
│             (No coordination)                   │
└─────────────────────────────────────────────────┘
```

### Target State (Phase 4)
```
┌─────────────────────────────────────────────────┐
│    Collaboration-Aware Generation Coordinator    │
│  ┌──────────────────────────────────────────┐  │
│  │   Dependency Graph & Sequential Ordering │  │
│  │   Shared Context Pool                    │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  Step 1: Foundation Documents                   │
│  ┌──────┐  ┌──────┐                             │
│  │ PWS  │  │ Acq  │                             │
│  │Agent │  │Plan  │                             │
│  └──┬───┘  └──┬───┘                             │
│     │         │                                  │
│     └────┬────┘                                  │
│          │ (Output → Context Pool)              │
│          │                                       │
│  Step 2: Dependent Documents                    │
│  ┌──────▼────┐  ┌────▼─────┐                   │
│  │Sec L Agent│  │Sec M Agent│                   │
│  │(reads PWS)│  │(reads PWS)│                   │
│  └──┬────────┘  └──┬────────┘                   │
│     │              │                             │
│     └──────┬───────┘                             │
│            │ (Output → Context Pool)             │
│            │                                      │
│  Step 3: Final Documents                         │
│  ┌─────────▼──────┐                              │
│  │  Sec H Agent   │                              │
│  │ (reads L,M,PWS)│                              │
│  └────────────────┘                              │
└─────────────────────────────────────────────────┘
```

---

## Phase 4 Objectives

### Primary Goals

1. **Cross-Referencing Between Agents**
   - Agents can read and reference previously generated sections
   - Maintain consistency across related documents
   - Prevent contradictions and duplication

2. **Dependency-Based Generation Ordering**
   - Generate foundation documents first (PWS, Acquisition Plan)
   - Generate dependent documents after their dependencies
   - Optimize generation sequence for maximum context sharing

3. **Shared Context Pool**
   - Central repository of generated content
   - Agents contribute to and read from shared pool
   - Track which documents reference which others

4. **Collaboration Indicators in UI**
   - Show dependency relationships visually
   - Display generation order timeline
   - Indicate cross-references between documents

### Success Criteria

- ✅ Section L references PWS content appropriately
- ✅ Section M aligns with Section L evaluation approach
- ✅ Section H includes requirements from PWS, L, and M
- ✅ Documents generated in correct dependency order
- ✅ UI shows collaboration relationships clearly
- ✅ No increase in total generation time (parallel where possible)

---

## Architecture Overview

### New Components

1. **Document Dependency Graph** (`backend/services/dependency_graph.py`)
   - Maps dependencies between document types
   - Determines generation order using topological sort
   - Identifies parallelizable batches

2. **Shared Context Manager** (`backend/services/context_manager.py`)
   - Stores generated sections temporarily
   - Provides retrieval API for agents
   - Tracks cross-references and citations

3. **Enhanced Base Agent** (`backend/agents/base_agent.py`)
   - New `get_related_content()` method
   - New `reference_section()` method
   - Cross-reference formatting utilities

4. **Collaboration Metadata** (extension of existing metadata)
   - Track input dependencies per document
   - Track output references per document
   - Store generation order and timestamps

5. **Dependency Visualization** (`dod_contracting_front_end/src/components/DependencyGraph.tsx`)
   - Visual graph of document relationships
   - Generation timeline view
   - Cross-reference indicators

---

## Detailed Implementation Plan

## Part 1: Backend Infrastructure (Day 1)

### Task 1.1: Document Dependency Configuration

**File:** `backend/config/document_dependencies.json` (NEW)

**Purpose:** Define dependency relationships between document types

**Content Example:**
```json
{
  "dependencies": {
    "Section L - Instructions to Offerors": {
      "depends_on": [
        "Section C - Performance Work Statement",
        "Acquisition Plan"
      ],
      "references": ["evaluation approach", "technical requirements"],
      "priority": 5
    },
    "Section M - Evaluation Factors": {
      "depends_on": [
        "Section C - Performance Work Statement",
        "Acquisition Plan",
        "Section L - Instructions to Offerors"
      ],
      "references": ["evaluation criteria", "proposal instructions"],
      "priority": 6
    },
    "Section H - Special Contract Requirements": {
      "depends_on": [
        "Section C - Performance Work Statement",
        "Section L - Instructions to Offerors",
        "Section M - Evaluation Factors"
      ],
      "references": ["security requirements", "compliance obligations"],
      "priority": 7
    },
    "Section C - Performance Work Statement": {
      "depends_on": [],
      "references": [],
      "priority": 1
    },
    "Acquisition Plan": {
      "depends_on": [],
      "references": [],
      "priority": 1
    }
  },

  "generation_batches": [
    {
      "name": "Foundation Documents",
      "priority": 1,
      "documents": [
        "Section C - Performance Work Statement",
        "Acquisition Plan",
        "Market Research Report"
      ],
      "can_parallelize": true
    },
    {
      "name": "Solicitation Instructions",
      "priority": 2,
      "documents": [
        "Section L - Instructions to Offerors"
      ],
      "can_parallelize": false
    },
    {
      "name": "Evaluation Framework",
      "priority": 3,
      "documents": [
        "Section M - Evaluation Factors",
        "Source Selection Plan"
      ],
      "can_parallelize": true
    },
    {
      "name": "Special Requirements",
      "priority": 4,
      "documents": [
        "Section H - Special Contract Requirements",
        "Section I - Contract Clauses",
        "Section K - Representations and Certifications"
      ],
      "can_parallelize": true
    }
  ]
}
```

**Rationale:** Configuration-driven approach allows easy updates without code changes.

---

### Task 1.2: Dependency Graph Service

**File:** `backend/services/dependency_graph.py` (NEW)

**Purpose:** Load and analyze document dependencies

**Key Classes:**
```python
class DocumentNode:
    """Represents a document in the dependency graph"""
    def __init__(self, name: str, priority: int, depends_on: List[str]):
        self.name = name
        self.priority = priority
        self.depends_on = depends_on
        self.dependents: List[str] = []  # Who depends on this

class DependencyGraph:
    """Manages document dependencies and generation order"""

    def __init__(self, config_path: str):
        """Load dependency configuration"""

    def get_generation_order(self, selected_docs: List[str]) -> List[List[str]]:
        """
        Returns batches of documents in generation order

        Returns:
            List of batches, where each batch can be parallelized
            Example: [["PWS"], ["Section L"], ["Section M", "Section H"]]
        """

    def get_dependencies(self, doc_name: str) -> List[str]:
        """Get list of documents this document depends on"""

    def get_dependents(self, doc_name: str) -> List[str]:
        """Get list of documents that depend on this document"""

    def validate_selection(self, selected_docs: List[str]) -> Dict:
        """
        Validate document selection for missing dependencies

        Returns:
            {
                "valid": bool,
                "missing_dependencies": List[str],
                "warnings": List[str]
            }
        """
```

**Testing:** Unit tests with various document combinations

---

### Task 1.3: Shared Context Manager

**File:** `backend/services/context_manager.py` (NEW)

**Purpose:** Store and retrieve generated content for cross-referencing

**Key Classes:**
```python
class GeneratedContent:
    """Represents generated content with metadata"""
    def __init__(self, doc_name: str, content: str, metadata: Dict):
        self.doc_name = doc_name
        self.content = content
        self.metadata = metadata
        self.generated_at = datetime.now()
        self.word_count = len(content.split())

class ContextManager:
    """Manages shared context across agent generations"""

    def __init__(self):
        self._context_pool: Dict[str, GeneratedContent] = {}
        self._cross_references: Dict[str, List[str]] = {}

    def add_content(self, doc_name: str, content: str, metadata: Dict):
        """Add generated content to shared pool"""

    def get_content(self, doc_name: str) -> Optional[str]:
        """Retrieve previously generated content"""

    def get_related_content(self,
                           doc_name: str,
                           dependency_list: List[str]) -> Dict[str, str]:
        """
        Get all dependent content for a document

        Args:
            doc_name: Name of document being generated
            dependency_list: List of documents to retrieve

        Returns:
            Dictionary mapping doc_name -> content
        """

    def add_cross_reference(self, from_doc: str, to_doc: str, reference_text: str):
        """Track that from_doc references to_doc"""

    def get_cross_references(self, doc_name: str) -> List[Dict]:
        """Get all cross-references involving this document"""

    def clear(self):
        """Clear all context (call between generation tasks)"""
```

**Storage:** In-memory for Phase 4 (can be extended to database in Phase 5)

---

### Task 1.4: Enhanced BaseAgent

**File:** `backend/agents/base_agent.py` (MODIFY)

**Changes:**

1. Add context manager reference:
```python
class BaseAgent:
    def __init__(self, api_key: str, retriever=None, context_manager=None):
        # ... existing code ...
        self.context_manager = context_manager
```

2. Add helper methods:
```python
def get_related_content(self, dependency_list: List[str]) -> Dict[str, str]:
    """
    Retrieve previously generated content for dependencies

    Args:
        dependency_list: List of document names this agent depends on

    Returns:
        Dictionary mapping document name -> content
    """
    if not self.context_manager:
        return {}

    return self.context_manager.get_related_content(
        doc_name=self.__class__.__name__,
        dependency_list=dependency_list
    )

def reference_section(self, target_doc: str, excerpt: str) -> str:
    """
    Format a reference to another document section

    Args:
        target_doc: Name of document being referenced
        excerpt: Brief excerpt or summary

    Returns:
        Formatted reference string
    """
    # Track cross-reference
    if self.context_manager:
        self.context_manager.add_cross_reference(
            from_doc=self.__class__.__name__,
            to_doc=target_doc,
            reference_text=excerpt
        )

    return f"[Ref: {target_doc}] {excerpt}"

def build_collaborative_prompt(self,
                               base_requirements: str,
                               dependencies: Dict[str, str]) -> str:
    """
    Build prompt with context from dependent documents

    Args:
        base_requirements: Core requirements for this document
        dependencies: Dict of doc_name -> content from dependencies

    Returns:
        Enhanced prompt with collaborative context
    """
    if not dependencies:
        return base_requirements

    context_section = "\n\n## PREVIOUSLY GENERATED DOCUMENTS\n"
    context_section += "Use these documents as context and reference them where appropriate:\n\n"

    for doc_name, content in dependencies.items():
        # Truncate long content
        summary = content[:1000] + "..." if len(content) > 1000 else content
        context_section += f"### {doc_name}\n{summary}\n\n"

    return context_section + "\n## YOUR TASK\n" + base_requirements
```

---

### Task 1.5: Update Generation Coordinator

**File:** `backend/services/generation_coordinator.py` (MODIFY)

**Changes:**

1. Add new imports and initialization:
```python
from backend.services.dependency_graph import DependencyGraph
from backend.services.context_manager import ContextManager

class GenerationCoordinator:
    def __init__(self, ...):
        # ... existing code ...

        # Phase 4: Collaboration support
        self.dependency_graph = DependencyGraph(
            "backend/config/document_dependencies.json"
        )
        self.context_manager = ContextManager()
```

2. Modify `generate_documents()` method:
```python
async def generate_documents(self, task: GenerationTask) -> Dict:
    """
    Generate documents with collaboration support

    Phase 4 Enhancement: Generate in dependency order, passing context
    """
    try:
        task.status = "in_progress"
        task.message = "Analyzing dependencies..."
        task.progress = 5

        # Clear previous context
        self.context_manager.clear()

        # Get generation order (batches)
        generation_batches = self.dependency_graph.get_generation_order(
            task.document_names
        )

        task.message = f"Generating {len(task.document_names)} documents in {len(generation_batches)} batches..."
        task.progress = 10

        total_docs = len(task.document_names)
        completed_docs = 0

        # Generate batch by batch
        for batch_index, batch in enumerate(generation_batches):
            task.message = f"Batch {batch_index + 1}/{len(generation_batches)}: {', '.join(batch)}"

            # Generate all documents in batch (parallel if multiple)
            batch_results = await self._generate_batch(
                batch,
                task.assumptions,
                task.linked_assumptions
            )

            # Store results in context pool and task
            for doc_name, result in batch_results.items():
                task.sections[doc_name] = result["content"]
                task.agent_metadata[doc_name] = result["metadata"]

                # Add to context pool for next batch
                self.context_manager.add_content(
                    doc_name=doc_name,
                    content=result["content"],
                    metadata=result["metadata"]
                )

                completed_docs += 1
                task.progress = 10 + (80 * completed_docs / total_docs)

        # Get cross-reference metadata
        collaboration_metadata = self._build_collaboration_metadata(
            task.document_names
        )

        task.status = "completed"
        task.progress = 100
        task.message = "All documents generated successfully"

        return {
            "sections": task.sections,
            "agent_metadata": task.agent_metadata,
            "collaboration_metadata": collaboration_metadata,  # NEW
            "citations": task.citations
        }

    except Exception as e:
        task.status = "failed"
        task.message = f"Generation failed: {str(e)}"
        raise
```

3. Add new helper methods:
```python
async def _generate_batch(self,
                          batch: List[str],
                          assumptions: List[Dict],
                          linked_assumptions: Dict[str, List[str]]) -> Dict[str, Dict]:
    """
    Generate all documents in a batch (parallel if possible)

    Args:
        batch: List of document names to generate
        assumptions: All assumptions
        linked_assumptions: Mapping of doc -> assumption IDs

    Returns:
        Dictionary of doc_name -> {content, metadata}
    """
    results = {}

    # Generate all documents in batch in parallel
    tasks = []
    for doc_name in batch:
        task = self._generate_single_with_context(
            doc_name,
            assumptions,
            linked_assumptions.get(doc_name, [])
        )
        tasks.append((doc_name, task))

    # Await all
    for doc_name, coro in tasks:
        result = await coro
        results[doc_name] = result

    return results

async def _generate_single_with_context(self,
                                       doc_name: str,
                                       assumptions: List[Dict],
                                       linked_assumption_ids: List[str]) -> Dict:
    """
    Generate a single document with collaborative context

    Phase 4 Enhancement: Pass previously generated content to agent
    """
    # Get dependencies for this document
    dependencies = self.dependency_graph.get_dependencies(doc_name)

    # Retrieve content from dependencies
    related_content = self.context_manager.get_related_content(
        doc_name, dependencies
    )

    # Get RAG context (existing Phase 2 logic)
    assumptions_text = self._format_assumptions(assumptions, linked_assumption_ids)
    context = await self._retrieve_context(doc_name, assumptions_text)

    # Route to agent
    agent = self.agent_router.get_agent(doc_name)

    if agent:
        # Pass context manager to agent
        if not hasattr(agent, 'context_manager'):
            agent.context_manager = self.context_manager

        # Build collaborative prompt
        if hasattr(agent, 'build_collaborative_prompt'):
            enhanced_context = agent.build_collaborative_prompt(
                base_requirements=assumptions_text,
                dependencies=related_content
            )
        else:
            enhanced_context = context

        # Generate with agent
        result = await self._call_specialized_agent(
            agent, doc_name, assumptions_text, enhanced_context
        )
    else:
        # Fallback to generic
        result = await self._generate_generic(
            doc_name, assumptions_text, context
        )

    return result

def _build_collaboration_metadata(self, doc_names: List[str]) -> Dict:
    """
    Build metadata about document collaboration

    Returns:
        {
            "generation_order": [...],
            "dependencies": {"Section L": ["PWS"], ...},
            "cross_references": [
                {
                    "from": "Section L",
                    "to": "PWS",
                    "reference": "technical requirements"
                }
            ]
        }
    """
    cross_refs = []
    dependencies_map = {}

    for doc_name in doc_names:
        # Get dependencies
        deps = self.dependency_graph.get_dependencies(doc_name)
        if deps:
            dependencies_map[doc_name] = deps

        # Get cross-references
        refs = self.context_manager.get_cross_references(doc_name)
        cross_refs.extend(refs)

    return {
        "generation_order": self.dependency_graph.get_generation_order(doc_names),
        "dependencies": dependencies_map,
        "cross_references": cross_refs
    }
```

---

### Task 1.6: Update Specific Agents

**Files to Modify:**
- `backend/agents/section_l_generator_agent.py`
- `backend/agents/section_m_generator_agent.py`
- `backend/agents/section_h_generator_agent.py`

**Example for Section L:**

```python
class SectionLGeneratorAgent(BaseAgent):
    """
    Section L Generator - Instructions to Offerors

    Phase 4: References PWS and Acquisition Plan
    """

    def execute(self, task: Dict) -> Dict:
        """Generate Section L with collaborative context"""

        requirements = task.get('requirements', '')
        context = task.get('context', '')

        # Phase 4: Get related content
        dependencies = [
            "Section C - Performance Work Statement",
            "Acquisition Plan"
        ]
        related_content = self.get_related_content(dependencies)

        # Build collaborative prompt
        if related_content:
            enhanced_prompt = self.build_collaborative_prompt(
                base_requirements=requirements,
                dependencies=related_content
            )
        else:
            enhanced_prompt = requirements

        # Generate Section L
        prompt = f"""You are generating Section L - Instructions to Offerors for a DoD acquisition.

{enhanced_prompt}

### REQUIREMENTS
{requirements}

### RAG CONTEXT
{context}

### INSTRUCTIONS
1. If PWS content is provided above, reference specific technical requirements
2. If Acquisition Plan is provided, align proposal structure with evaluation approach
3. Use the reference_section() method to cite other documents

Generate comprehensive Section L content."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text.strip()

        # Track cross-references in content
        if "Section C" in content or "PWS" in content:
            self.reference_section(
                "Section C - Performance Work Statement",
                "Technical requirements and deliverables"
            )

        return {
            "content": content,
            "citations": [],
            "metadata": {
                "agent": self.__class__.__name__,
                "method": "specialized_agent",
                "dependencies_used": list(related_content.keys()) if related_content else []
            }
        }
```

---

## Part 2: Backend API Updates (Day 1, Evening)

### Task 2.1: Update API Response

**File:** `backend/main.py` (MODIFY)

**Changes:**

1. Update `/api/generate-documents` response to include collaboration metadata:
```python
@app.post("/api/generate-documents")
async def generate_documents(request: GenerateDocumentsRequest):
    """Generate documents with agent collaboration"""

    # ... existing generation logic ...

    result = await coordinator.generate_documents(task)

    return {
        "status": "success",
        "task_id": task_id,
        "documents_requested": len(document_names),
        "collaboration_enabled": True,  # NEW
        "generation_batches": len(result.get("collaboration_metadata", {}).get("generation_order", []))  # NEW
    }
```

2. Update `/api/generation-status/{task_id}` to return collaboration metadata:
```python
@app.get("/api/generation-status/{task_id}")
async def get_generation_status(task_id: str):
    """Get generation status with collaboration info"""

    task = generation_tasks.get(task_id)

    # ... existing logic ...

    if task.status == "completed":
        return {
            "status": "completed",
            "progress": 100,
            "result": {
                "sections": task.sections,
                "citations": task.citations,
                "agent_metadata": task.agent_metadata,
                "collaboration_metadata": result.get("collaboration_metadata", {})  # NEW
            }
        }
```

---

## Part 3: Frontend Updates (Day 2)

### Task 3.1: Update API Types

**File:** `dod_contracting_front_end/src/services/api.ts` (MODIFY)

**Changes:**

```typescript
// Add collaboration metadata types
interface CollaborationMetadata {
  generation_order: string[][];
  dependencies: Record<string, string[]>;
  cross_references: Array<{
    from: string;
    to: string;
    reference: string;
  }>;
}

interface GenerationStatusResponse {
  status: string;
  progress: number;
  message?: string;
  result?: {
    sections: Record<string, string>;
    citations: any[];
    agent_metadata: Record<string, any>;
    collaboration_metadata?: CollaborationMetadata;  // NEW
  };
}
```

---

### Task 3.2: Dependency Graph Visualization

**File:** `dod_contracting_front_end/src/components/DependencyGraph.tsx` (NEW)

**Purpose:** Visual display of document dependencies

**Component:**

```typescript
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, GitBranch, Clock } from "lucide-react";

interface DependencyGraphProps {
  collaborationMetadata: CollaborationMetadata;
  agentMetadata: Record<string, any>;
}

export function DependencyGraph({ collaborationMetadata, agentMetadata }: DependencyGraphProps) {
  if (!collaborationMetadata) return null;

  const { generation_order, dependencies, cross_references } = collaborationMetadata;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <GitBranch className="h-5 w-5" />
          Document Dependencies & Generation Order
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Generation Timeline */}
          <div>
            <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Generation Timeline
            </h3>
            <div className="space-y-3">
              {generation_order.map((batch, index) => (
                <div key={index} className="flex items-center gap-3">
                  <Badge variant="outline" className="min-w-[60px] justify-center">
                    Batch {index + 1}
                  </Badge>
                  <div className="flex flex-wrap gap-2">
                    {batch.map((docName) => {
                      const isSpecialized = agentMetadata[docName]?.method === 'specialized_agent';
                      return (
                        <Badge
                          key={docName}
                          variant={isSpecialized ? "default" : "secondary"}
                          className="flex items-center gap-1"
                        >
                          {docName}
                          {isSpecialized && <span className="text-xs">✨</span>}
                        </Badge>
                      );
                    })}
                  </div>
                  {index < generation_order.length - 1 && (
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Dependency Map */}
          {Object.keys(dependencies).length > 0 && (
            <div>
              <h3 className="text-sm font-medium mb-3">Document Dependencies</h3>
              <div className="space-y-2">
                {Object.entries(dependencies).map(([docName, deps]) => (
                  <div key={docName} className="flex items-start gap-2 text-sm">
                    <Badge variant="outline" className="mt-0.5">{docName}</Badge>
                    <span className="text-muted-foreground mt-0.5">depends on</span>
                    <div className="flex flex-wrap gap-1">
                      {deps.map((dep) => (
                        <Badge key={dep} variant="secondary" className="text-xs">
                          {dep}
                        </Badge>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Cross-References */}
          {cross_references.length > 0 && (
            <div>
              <h3 className="text-sm font-medium mb-3">Cross-References</h3>
              <div className="space-y-2">
                {cross_references.map((ref, index) => (
                  <div key={index} className="flex items-center gap-2 text-sm border-l-2 border-blue-500 pl-3 py-1">
                    <span className="font-medium">{ref.from}</span>
                    <ArrowRight className="h-3 w-3 text-muted-foreground" />
                    <span className="font-medium">{ref.to}</span>
                    <span className="text-muted-foreground">- {ref.reference}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

---

### Task 3.3: Update Live Editor

**File:** `dod_contracting_front_end/src/components/LiveEditor.tsx` (MODIFY)

**Changes:**

1. Add import:
```typescript
import { DependencyGraph } from "@/components/DependencyGraph";
```

2. Add prop:
```typescript
interface LiveEditorProps {
  // ... existing props ...
  collaborationMetadata?: CollaborationMetadata;  // NEW
}
```

3. Add display:
```typescript
{/* Header area - after AgentStats */}
{collaborationMetadata && (
  <DependencyGraph
    collaborationMetadata={collaborationMetadata}
    agentMetadata={agentMetadata}
  />
)}
```

---

### Task 3.4: Update AIContractingUI

**File:** `dod_contracting_front_end/src/components/AIContractingUI.tsx` (MODIFY)

**Changes:**

1. Add state:
```typescript
const [collaborationMetadata, setCollaborationMetadata] = useState<CollaborationMetadata | null>(null);
```

2. Update generation handler:
```typescript
if (status.status === 'completed' && status.result) {
  clearInterval(pollInterval);
  setEditorSections(status.result.sections);

  if (status.result.agent_metadata) {
    setAgentMetadata(status.result.agent_metadata);
  }

  // NEW: Store collaboration metadata
  if (status.result.collaboration_metadata) {
    setCollaborationMetadata(status.result.collaboration_metadata);
  }

  // ... rest of code ...
}
```

3. Pass to LiveEditor:
```typescript
<LiveEditor
  // ... existing props ...
  collaborationMetadata={collaborationMetadata}  // NEW
/>
```

---

## Part 4: Testing (Day 3)

### Task 4.1: Unit Tests

**File:** `backend/tests/test_phase4_collaboration.py` (NEW)

**Test Cases:**

1. `test_dependency_graph_loading()` - Load config correctly
2. `test_generation_order_simple()` - Single document, no dependencies
3. `test_generation_order_complex()` - Multiple batches with dependencies
4. `test_generation_order_missing_dependency()` - Handle missing dependency
5. `test_context_manager_add_retrieve()` - Store and retrieve content
6. `test_context_manager_cross_references()` - Track references correctly
7. `test_context_manager_clear()` - Clear between tasks
8. `test_base_agent_get_related_content()` - Agent retrieves dependencies
9. `test_base_agent_reference_section()` - Format references correctly
10. `test_collaborative_generation_order()` - Documents generated in correct order
11. `test_collaborative_generation_content()` - Content includes references
12. `test_collaborative_generation_parallel()` - Batches parallelized correctly

**Command:**
```bash
python backend/tests/test_phase4_collaboration.py
```

**Expected:** 12/12 tests passing

---

### Task 4.2: Integration Tests

**Scenarios:**

1. **Test: Foundation + Dependent Documents**
   - Generate PWS + Section L
   - Verify Section L references PWS
   - Check generation order: [PWS], [Section L]

2. **Test: Full Solicitation Package**
   - Generate PWS, Section L, Section M, Section H
   - Verify dependencies respected
   - Check cross-references exist
   - Verify generation order: [PWS], [L], [M, H]

3. **Test: Missing Dependency Warning**
   - Try to generate Section M without Section L
   - Should still work but log warning
   - Check no cross-references created

4. **Test: Multiple Generations**
   - Generate documents twice
   - Verify context cleared between runs
   - No cross-contamination

---

### Task 4.3: Manual UI Testing

**Test Checklist:**

- [ ] DependencyGraph component appears in Live Editor
- [ ] Generation timeline shows correct batch order
- [ ] Document dependencies listed accurately
- [ ] Cross-references displayed with from/to/reference
- [ ] Specialized agent badges still work
- [ ] AgentStats still accurate
- [ ] No performance degradation
- [ ] No console errors
- [ ] Mobile responsive (optional)

---

## Part 5: Documentation (Day 3, Evening)

### Task 5.1: Update Documentation Files

**Files to Update:**

1. **PROJECT_STATUS.md**
   - Mark Phase 4 as complete
   - Update success metrics
   - Add Phase 4 to changelog

2. **PHASE_4_SUMMARY.md** (NEW)
   - Architecture overview
   - Key features implemented
   - Test results
   - Known limitations

3. **QUICK_START.md**
   - Update "What to Test" section
   - Add Phase 4 test scenarios

4. **API Documentation** (NEW: `backend/docs/api_collaboration.md`)
   - Document new collaboration metadata
   - Example API responses
   - Integration guide for future agents

---

## Implementation Timeline

### Day 1: Backend Core (8 hours)

| Time | Task | Duration |
|------|------|----------|
| 09:00 | Task 1.1: Create document_dependencies.json | 1h |
| 10:00 | Task 1.2: Implement DependencyGraph | 2h |
| 12:00 | Lunch | 1h |
| 13:00 | Task 1.3: Implement ContextManager | 2h |
| 15:00 | Task 1.4: Enhance BaseAgent | 1h |
| 16:00 | Task 1.5: Update GenerationCoordinator | 2h |
| 18:00 | Task 1.6: Update specific agents (L, M, H) | 1h |
| 19:00 | Task 2.1: Update API endpoints | 1h |

### Day 2: Frontend & Integration (6 hours)

| Time | Task | Duration |
|------|------|----------|
| 09:00 | Task 3.1: Update API types | 0.5h |
| 09:30 | Task 3.2: Create DependencyGraph component | 2h |
| 11:30 | Task 3.3: Update LiveEditor | 1h |
| 12:30 | Lunch | 1h |
| 13:30 | Task 3.4: Update AIContractingUI | 0.5h |
| 14:00 | Manual integration testing | 2h |

### Day 3: Testing & Documentation (8 hours)

| Time | Task | Duration |
|------|------|----------|
| 09:00 | Task 4.1: Write unit tests | 3h |
| 12:00 | Lunch | 1h |
| 13:00 | Task 4.2: Integration testing | 2h |
| 15:00 | Task 4.3: Manual UI testing | 1h |
| 16:00 | Task 5.1: Update documentation | 2h |
| 18:00 | Final review & cleanup | 1h |

**Total Estimated Time:** 22 hours (2-3 working days)

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Circular dependencies in config | Low | High | Validation logic in DependencyGraph |
| Context pool memory usage | Medium | Medium | Clear context between tasks; limit content size |
| Generation time increases | Medium | Medium | Parallel batches; monitor performance |
| Agent prompts too long | Low | Medium | Truncate dependency content to 1000 chars |
| Cross-reference tracking fails | Low | Low | Graceful degradation; optional feature |

### Integration Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking existing Phase 3 features | Low | High | Comprehensive testing; backward compatibility |
| Frontend state management complexity | Medium | Medium | Clear prop drilling; consider context if needed |
| API response size increases | Low | Low | Gzip compression; paginate if needed |

### Schedule Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Underestimated complexity | Medium | Medium | Buffer day built into timeline |
| Testing reveals major issues | Low | High | Daily integration tests; catch early |
| Scope creep | Medium | Medium | Stick to defined tasks; defer enhancements |

---

## Success Metrics

### Functional Requirements

- ✅ Documents generated in correct dependency order
- ✅ Agents can access previously generated content
- ✅ Cross-references tracked accurately
- ✅ UI displays collaboration relationships
- ✅ No breaking changes to Phase 3 features

### Performance Requirements

- ✅ Total generation time ≤ 1.2x Phase 3 baseline (20% overhead max)
- ✅ Context pool memory usage < 10MB per task
- ✅ UI remains responsive during generation
- ✅ No degradation in agent quality

### Quality Requirements

- ✅ 12/12 unit tests passing
- ✅ 4/4 integration tests passing
- ✅ Manual UI checklist complete
- ✅ Zero critical bugs
- ✅ Code review approved

---

## Rollback Plan

If Phase 4 encounters critical issues:

1. **Immediate Rollback** (< 5 minutes)
   - Set `USE_COLLABORATION=false` environment variable
   - Coordinator falls back to Phase 3 parallel generation
   - Frontend hides DependencyGraph component

2. **Partial Rollback** (< 1 hour)
   - Keep dependency ordering
   - Disable context sharing
   - Remove cross-reference tracking

3. **Full Rollback** (< 2 hours)
   - Git revert to Phase 3 commit
   - Restore backend/services/generation_coordinator.py
   - Remove new frontend components
   - Run Phase 3 test suite to verify

---

## Post-Phase 4 Enhancements (Future)

### Phase 4.5: Advanced Collaboration (Optional)

- **Iterative Refinement:** Agents re-generate if dependencies change
- **Conflict Detection:** Warn if documents contradict each other
- **Smart Batching:** ML-based optimization of generation order
- **Parallel Dependencies:** Generate multiple dependency chains simultaneously

### Phase 5 Preview: Quality Assurance

- **QualityAgent Integration:** Validate generated content
- **RefinementAgent:** Iteratively improve based on feedback
- **Quality Scoring:** Per-agent and per-document metrics
- **Feedback Loops:** User corrections improve future generations

---

## Approval Checklist

Before proceeding with Phase 4 implementation, please review and approve:

### Architecture

- [ ] Dependency graph approach is appropriate
- [ ] Context manager design is sound
- [ ] Shared context pool strategy is acceptable
- [ ] Generation ordering logic is correct

### Scope

- [ ] Tasks are well-defined and achievable
- [ ] Timeline (2-3 days) is reasonable
- [ ] Risk mitigation strategies are adequate
- [ ] Success criteria are measurable

### Integration

- [ ] Phase 3 features will be preserved
- [ ] API changes are backward-compatible
- [ ] Frontend changes are non-breaking
- [ ] Testing plan is comprehensive

### Resources

- [ ] Required time commitment is available
- [ ] Development environment is ready
- [ ] API keys and credentials are valid
- [ ] Documentation will be maintained

---

## Appendix A: Example Outputs

### Example: Dependency Graph JSON Output

```json
{
  "generation_order": [
    ["Section C - Performance Work Statement"],
    ["Section L - Instructions to Offerors"],
    ["Section M - Evaluation Factors", "Section H - Special Contract Requirements"]
  ],
  "dependencies": {
    "Section L - Instructions to Offerors": [
      "Section C - Performance Work Statement"
    ],
    "Section M - Evaluation Factors": [
      "Section C - Performance Work Statement",
      "Section L - Instructions to Offerors"
    ],
    "Section H - Special Contract Requirements": [
      "Section C - Performance Work Statement",
      "Section L - Instructions to Offerors"
    ]
  },
  "cross_references": [
    {
      "from": "Section L - Instructions to Offerors",
      "to": "Section C - Performance Work Statement",
      "reference": "Technical requirements and deliverables"
    },
    {
      "from": "Section M - Evaluation Factors",
      "to": "Section L - Instructions to Offerors",
      "reference": "Proposal submission requirements"
    },
    {
      "from": "Section H - Special Contract Requirements",
      "to": "Section C - Performance Work Statement",
      "reference": "Security and compliance requirements"
    }
  ]
}
```

### Example: Enhanced Section L Content (with collaboration)

**WITHOUT Phase 4 (Phase 3):**
```
SECTION L - INSTRUCTIONS TO OFFERORS

1. PROPOSAL SUBMISSION
Offerors shall submit proposals in accordance with this section...

2. PROPOSAL CONTENT
Proposals shall include the following:
- Technical approach
- Management plan
- Past performance
```

**WITH Phase 4 (Collaboration):**
```
SECTION L - INSTRUCTIONS TO OFFERORS

1. PROPOSAL SUBMISSION
Offerors shall submit proposals in accordance with this section...

2. PROPOSAL CONTENT
Proposals shall address the technical requirements defined in Section C - Performance Work Statement, specifically:

[Ref: Section C] The technical solution shall demonstrate capabilities for:
- Cloud infrastructure deployment (PWS §3.1)
- Cybersecurity compliance with NIST 800-171 (PWS §4.2)
- 99.9% system availability (PWS §5.1)

Technical proposals shall be organized as follows:
- Volume I: Technical Approach (addressing PWS technical requirements)
- Volume II: Management Plan
- Volume III: Past Performance

3. EVALUATION ALIGNMENT
Proposals will be evaluated in accordance with Section M - Evaluation Factors. Offerors should structure their proposals to directly address each evaluation criterion.
```

---

## Appendix B: Configuration Examples

### Simple Dependency Configuration

```json
{
  "dependencies": {
    "Section L - Instructions to Offerors": {
      "depends_on": ["Section C - Performance Work Statement"],
      "priority": 2
    },
    "Section C - Performance Work Statement": {
      "depends_on": [],
      "priority": 1
    }
  }
}
```

### Complex Multi-Tier Configuration

```json
{
  "dependencies": {
    "Award Notification": {
      "depends_on": [
        "Section M - Evaluation Factors",
        "Evaluation Scorecard",
        "Source Selection Plan"
      ],
      "priority": 10
    },
    "Evaluation Scorecard": {
      "depends_on": [
        "Section M - Evaluation Factors",
        "Section L - Instructions to Offerors"
      ],
      "priority": 8
    },
    "Section M - Evaluation Factors": {
      "depends_on": [
        "Section C - Performance Work Statement",
        "Section L - Instructions to Offerors"
      ],
      "priority": 6
    },
    "Section L - Instructions to Offerors": {
      "depends_on": [
        "Section C - Performance Work Statement"
      ],
      "priority": 5
    },
    "Section C - Performance Work Statement": {
      "depends_on": [],
      "priority": 1
    }
  }
}
```

---

## Questions for Review

1. **Dependency Configuration:** Should dependencies be hard-coded in JSON or configurable per-project?

2. **Context Size:** Is 1000 characters sufficient for dependency content, or should it be adjustable?

3. **Parallelization:** Should we prioritize speed (more parallelization) or quality (more sequential with better context)?

4. **UI Placement:** Should DependencyGraph be in the Editor, or in a dedicated "Generation Report" view?

5. **Backward Compatibility:** Should Phase 4 be opt-in (feature flag) or always enabled?

6. **Performance:** Is 20% generation time overhead acceptable, or should we target lower?

---

**Status:** 📋 AWAITING APPROVAL

**Next Steps:**
1. Review this plan
2. Provide feedback and answer questions
3. Approve to proceed with implementation
4. Begin Day 1 tasks

---

**Document Version:** 1.0
**Last Updated:** 2025-11-07
**Prepared By:** Claude Code
