# AI Agent Integration Architecture

## Overview

The frontend integrates with AI agents through a **multi-tier architecture** that combines RAG (Retrieval-Augmented Generation), vector search, and Claude Sonnet 4 to generate DoD acquisition documents.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐     ┌──────────────────┐                  │
│  │ GenerationPlan   │────▶│ AIContractingUI  │                  │
│  │                  │     │                  │                  │
│  │ • Document       │     │ • Generation     │                  │
│  │   Selection      │     │   Orchestrator   │                  │
│  │ • Assumption     │     │ • Status Polling │                  │
│  │   Tracing        │     │ • State Mgmt     │                  │
│  └──────────────────┘     └──────────────────┘                  │
│                                    │                             │
│                                    │ POST /api/generate-documents│
│                                    ▼                             │
└─────────────────────────────────────────────────────────────────┘
                                     │
                                     │ HTTP + WebSocket
                                     │
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              /api/generate-documents                      │   │
│  │                                                            │   │
│  │  1. Create Task ID                                        │   │
│  │  2. Initialize task status                                │   │
│  │  3. Start background task: run_document_generation()      │   │
│  │  4. Return task_id to frontend                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                    │                             │
│                                    ▼                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │      run_document_generation() - Background Task         │   │
│  │                                                            │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │ PHASE 1: RAG Context Retrieval                      │ │   │
│  │  │                                                       │ │   │
│  │  │  • Build assumptions_text from user inputs          │ │   │
│  │  │  • For each document:                               │ │   │
│  │  │    - Create search query                            │ │   │
│  │  │    - rag_service.search_documents(query, k=5)       │ │   │
│  │  │    - Retrieve top 5 relevant chunks                 │ │   │
│  │  │  • Aggregate top 20 chunks total                    │ │   │
│  │  │  • Build context_text with sources                  │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                           │                               │   │
│  │                           ▼                               │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │ PHASE 2: AI Agent Document Generation               │ │   │
│  │  │                                                       │ │   │
│  │  │  For each selected document:                        │ │   │
│  │  │    1. Build generation prompt with:                 │ │   │
│  │  │       - Document name/section                       │ │   │
│  │  │       - Assumptions text                            │ │   │
│  │  │       - RAG context text                            │ │   │
│  │  │       - FAR/DFARS compliance instructions           │ │   │
│  │  │                                                       │ │   │
│  │  │    2. Call Claude Sonnet 4:                         │ │   │
│  │  │       client.messages.create(                       │ │   │
│  │  │         model="claude-sonnet-4-20250514",           │ │   │
│  │  │         max_tokens=2000,                            │ │   │
│  │  │         messages=[prompt]                           │ │   │
│  │  │       )                                              │ │   │
│  │  │                                                       │ │   │
│  │  │    3. Extract section_content from response         │ │   │
│  │  │    4. Store in sections dictionary                  │ │   │
│  │  │    5. Update progress (40% → 90%)                   │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                           │                               │   │
│  │                           ▼                               │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │ PHASE 3: Citation Extraction                        │ │   │
│  │  │                                                       │ │   │
│  │  │  • Extract top 5 sources from RAG results           │ │   │
│  │  │  • Create citation objects with:                    │ │   │
│  │  │    - id, source, page, text                         │ │   │
│  │  │  • Attach to generation result                      │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                           │                               │   │
│  │                           ▼                               │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │ PHASE 4: Finalization                               │ │   │
│  │  │                                                       │ │   │
│  │  │  • Set status = "completed"                         │ │   │
│  │  │  • Set progress = 100                               │ │   │
│  │  │  • Store result with sections + citations           │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │      /api/generation-status/{task_id}                    │   │
│  │                                                            │   │
│  │  • Return current task status                            │   │
│  │  • Progress percentage                                    │   │
│  │  • Status: pending → in_progress → completed             │   │
│  │  • Result with sections & citations                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                     │
                                     │
┌─────────────────────────────────────────────────────────────────┐
│                    RAG LAYER (Vector Store)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    RAGService                             │   │
│  │                                                            │   │
│  │  • DoclingProcessor: PDF/DOCX → Text chunks              │   │
│  │  • VectorStore: FAISS index with embeddings              │   │
│  │  • search_documents(query, k) → relevant chunks          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Vector Database (FAISS)                      │   │
│  │                                                            │   │
│  │  • Stores document embeddings (384-dim)                  │   │
│  │  • Similarity search for retrieval                       │   │
│  │  • Metadata: source, page, chunk_index                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                     │
                                     │
┌─────────────────────────────────────────────────────────────────┐
│                  EXTERNAL AI SERVICE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Anthropic Claude API                         │   │
│  │                                                            │   │
│  │  Model: claude-sonnet-4-20250514                         │   │
│  │  Purpose: Generate document sections                     │   │
│  │  Input: Prompt with assumptions + RAG context            │   │
│  │  Output: Professional DoD acquisition text               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Step-by-Step

### 1. **User Initiates Generation** (Frontend)

**Location:** [GenerationPlan.tsx:430-438](dod_contracting_front_end/src/components/GenerationPlan.tsx#L430-L438)

```typescript
<Button onClick={() => {
  const docsToGenerate = documentList.filter(d => selectedDocuments.has(d.name));
  onGenerate(docsToGenerate);  // Calls AIContractingUI.handleGenerateDocuments()
}}>
  Generate Documents ({selectedDocuments.size})
</Button>
```

**What happens:**
- User selects documents to generate (Section L, Section M, etc.)
- Each document is linked to specific assumptions
- Clicks "Generate Documents" button

---

### 2. **Frontend API Call** (AIContractingUI)

**Location:** [AIContractingUI.tsx:50-64](dod_contracting_front_end/src/components/AIContractingUI.tsx#L50-L64)

```typescript
const handleGenerateDocuments = async (selectedDocs: any[]) => {
  setRoute("GENERATING");
  setGenerationProgress(0);

  // POST request to backend
  const response = await ragApi.generateDocuments({
    assumptions: lockedAssumptions,  // User's acquisition assumptions
    documents: selectedDocs.map(doc => ({
      name: doc.name,
      section: doc.section,
      category: doc.category,
      linkedAssumptions: doc.linkedAssumptions,
    })),
  });

  toast.success(`Generating ${response.documents_requested} documents...`);
  // Start polling for status...
}
```

**Request Payload Example:**
```json
{
  "assumptions": [
    { "id": "a1", "text": "BVTO evaluation with weighted factors", "source": "Acq Strategy §3.2" },
    { "id": "a2", "text": "IDIQ base + 4 option years", "source": "Acq Strategy §2.1" }
  ],
  "documents": [
    {
      "name": "Section L - Instructions to Offerors",
      "section": "L",
      "category": "required",
      "linkedAssumptions": ["a1"]
    },
    {
      "name": "Section M - Evaluation Factors",
      "section": "M",
      "category": "required",
      "linkedAssumptions": ["a1"]
    }
  ]
}
```

---

### 3. **Backend Receives Request** (FastAPI Endpoint)

**Location:** [backend/main.py:1400-1441](backend/main.py#L1400-L1441)

```python
@app.post("/api/generate-documents", tags=["Generation"])
async def generate_documents(
    request: GenerateDocumentsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate acquisition documents based on assumptions and selected document types
    """
    task_id = str(uuid.uuid4())

    # Initialize task status
    generation_tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "message": "Initializing document generation...",
        "result": None,
        "documents_requested": len(request.documents)
    }

    # Start generation in background (non-blocking)
    asyncio.create_task(run_document_generation(task_id, request))

    return {
        "message": "Document generation started",
        "task_id": task_id,
        "documents_requested": len(request.documents)
    }
```

**What happens:**
- Creates unique task ID
- Initializes task status in memory dictionary
- Starts background async task
- Returns immediately to frontend (non-blocking)

---

### 4. **Background Task: RAG Context Retrieval**

**Location:** [backend/main.py:1459-1495](backend/main.py#L1459-L1495)

```python
async def run_document_generation(task_id: str, request: GenerateDocumentsRequest):
    """Background task to generate documents using RAG and AI agents"""

    # PHASE 1: Build assumption context
    assumptions_text = "\n".join([
        f"- {a['text']} (Source: {a['source']})"
        for a in request.assumptions
    ])

    generation_tasks[task_id]["progress"] = 20
    generation_tasks[task_id]["message"] = "Gathering relevant document context..."

    # PHASE 2: RAG retrieval for each document
    all_context = []
    for doc in request.documents:
        # Create search query
        search_query = f"{doc.name} {doc.section or ''} DoD acquisition federal requirements"

        # Search vector store (FAISS)
        results = rag_service.search_documents(query=search_query, k=5)
        all_context.extend(results)

    # Build context string from top 20 chunks
    context_text = "\n\n---\n\n".join([
        f"Source: {r['metadata'].get('source', 'Unknown')}\n{r['content']}"
        for r in all_context[:20]
    ])
```

**RAG Service Search:**
```python
# Location: backend/services/rag_service.py
def search_documents(self, query: str, k: int = 5) -> List[Dict]:
    """
    Search for relevant document chunks using vector similarity

    1. Converts query to embedding vector (384-dim)
    2. Performs FAISS similarity search
    3. Returns top-k most relevant chunks with metadata
    """
    return self.vector_store.search(query, k)
```

**Example RAG Results:**
```python
[
  {
    "content": "FAR 15.304 requires evaluation factors to be stated in the solicitation...",
    "metadata": {
      "source": "FAR_Part_15.pdf",
      "page": 12,
      "chunk_index": 45
    },
    "score": 0.89
  },
  {
    "content": "Best Value Tradeoff evaluation approach allows the SSA to consider...",
    "metadata": {
      "source": "Acquisition_Strategy.docx",
      "page": 8,
      "chunk_index": 23
    },
    "score": 0.85
  }
]
```

---

### 5. **AI Agent Document Generation** (Claude Sonnet 4)

**Location:** [backend/main.py:1500-1549](backend/main.py#L1500-L1549)

```python
# PHASE 3: Generate each document section
sections = {}
citations = []
citation_id = 1

for idx, doc in enumerate(request.documents):
    generation_tasks[task_id]["message"] = f"Generating {doc.name}..."

    # Build generation prompt
    prompt = f"""You are a DoD acquisition expert writing {doc.name} for a federal procurement.

ASSUMPTIONS TO INCORPORATE:
{assumptions_text}

RELEVANT SOURCE MATERIAL:
{context_text}

INSTRUCTIONS:
1. Write professional, compliant content for {doc.name}
2. Include proper FAR/DFARS citations where applicable
3. Reference the assumptions provided
4. Use DoD acquisition terminology
5. Keep it concise but comprehensive (2-4 paragraphs)
6. Use inline citations like [1], [2], etc. for source references

Write the section content now:"""

    # Call Claude Sonnet 4 API
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract generated content
    section_content = message.content[0].text.strip()
    sections[doc.name] = section_content

    # Update progress
    generation_tasks[task_id]["progress"] = 40 + (idx + 1) * progress_per_doc
```

**Example Generated Output:**
```
Section M - Evaluation Factors

The Government will conduct a Best Value Tradeoff evaluation [1] in accordance
with FAR 15.304 [2]. Proposals will be evaluated based on three primary factors:

1. **Technical Approach** (Most Important): Offerors must demonstrate capability
to meet all Performance Work Statement requirements, with emphasis on past
performance in similar IDIQ contracts [3].

2. **Past Performance** (Important): Evaluation will consider recent and relevant
contracts of similar scope, value, and complexity.

3. **Price** (Important): The Government will evaluate proposed pricing for
reasonableness and completeness across the base period and four option years [4].

The Source Selection Authority retains tradeoff authority to select other than
the lowest-priced proposal when justified by superior technical merit or past
performance advantages.
```

---

### 6. **Citation Extraction**

**Location:** [backend/main.py:1539-1547](backend/main.py#L1539-L1547)

```python
# Extract citations from RAG context
for r in all_context[:5]:  # Top 5 sources
    citations.append({
        "id": citation_id,
        "source": r['metadata'].get('source', 'Unknown'),
        "page": int(r['metadata'].get('page', 0)),
        "text": r['content'][:200] + "...",
    })
    citation_id += 1
```

**Example Citations:**
```json
[
  {
    "id": 1,
    "source": "Acquisition_Strategy.docx",
    "page": 8,
    "text": "Best Value Tradeoff evaluation approach allows the SSA to consider technical merit..."
  },
  {
    "id": 2,
    "source": "FAR_15.304",
    "page": 12,
    "text": "Evaluation factors must be stated in the solicitation and include technical..."
  }
]
```

---

### 7. **Task Completion**

**Location:** [backend/main.py:1550-1560](backend/main.py#L1550-L1560)

```python
# Mark task as completed
generation_tasks[task_id]["status"] = "completed"
generation_tasks[task_id]["progress"] = 100
generation_tasks[task_id]["message"] = "Document generation complete!"
generation_tasks[task_id]["result"] = {
    "sections": sections,
    "citations": citations
}
```

**Example Task Status:**
```json
{
  "task_id": "abc-123-def-456",
  "status": "completed",
  "progress": 100,
  "message": "Document generation complete!",
  "result": {
    "sections": {
      "Section L - Instructions to Offerors": "The Government requests proposals...",
      "Section M - Evaluation Factors": "The Government will conduct a Best Value..."
    },
    "citations": [
      { "id": 1, "source": "FAR 15.304", "page": 12, "text": "..." }
    ]
  }
}
```

---

### 8. **Frontend Polling** (Status Updates)

**Location:** [AIContractingUI.tsx:69-97](dod_contracting_front_end/src/components/AIContractingUI.tsx#L69-L97)

```typescript
// Poll for status every 2 seconds
const pollInterval = setInterval(async () => {
  const status = await ragApi.getGenerationStatus(response.task_id);
  setGenerationProgress(status.progress);  // Update progress bar

  if (status.status === 'completed' && status.result) {
    clearInterval(pollInterval);

    // Update editor with generated sections
    setEditorSections(status.result.sections);

    // Add citations with bbox for UI compatibility
    const citationsWithBbox = status.result.citations.map(c => ({
      ...c,
      bbox: { x: 30, y: 40 + (c.id * 20), w: 200, h: 16 }
    }));
    setParsed({ ...parsed, citations: citationsWithBbox });

    // Navigate to editor
    setRoute("EDITOR");
    toast.success("Documents generated successfully!");

  } else if (status.status === 'failed') {
    clearInterval(pollInterval);
    toast.error(status.message || "Document generation failed");
  }
}, 2000);
```

---

### 9. **Live Editor Display**

**Location:** [LiveEditor.tsx:382-389](dod_contracting_front_end/src/components/LiveEditor.tsx#L382-L389)

```typescript
<RichTextEditor
  content={text}                      // Generated section text
  onChange={onTextChange}             // User edits
  citations={citations}               // RAG-extracted citations
  qualityIssues={qualityIssues}       // Compliance feedback
  placeholder={`Start writing ${sectionName}...`}
/>
```

**User sees:**
- Generated document sections in rich text editor
- Inline citations as blue chips `[1]` `[2]`
- Quality/compliance feedback with wavy underlines
- Full editing capabilities with formatting toolbar

---

## Key Components

### Frontend Components

| Component | File | Purpose |
|-----------|------|---------|
| **GenerationPlan** | `GenerationPlan.tsx:32` | Document selection and assumption tracing |
| **AIContractingUI** | `AIContractingUI.tsx:22` | Generation orchestration and state management |
| **LiveEditor** | `LiveEditor.tsx:40` | Document editing interface |
| **RichTextEditor** | `RichTextEditor.tsx:34` | TipTap-based WYSIWYG editor |
| **RAG API Client** | `api.ts:587-625` | Backend API communication |

### Backend Components

| Component | File | Purpose |
|-----------|------|---------|
| **Generation Endpoint** | `main.py:1400` | Receives generation requests |
| **Background Task** | `main.py:1459` | Async document generation |
| **RAG Service** | `rag_service.py:20` | Document search and retrieval |
| **Vector Store** | `vector_store.py` | FAISS similarity search |
| **Docling Processor** | `docling_processor.py` | PDF/DOCX parsing |

### AI Integration

| Service | Model | Purpose |
|---------|-------|---------|
| **Anthropic Claude** | `claude-sonnet-4-20250514` | Document text generation |
| **Embeddings** | FAISS (384-dim) | Semantic search for RAG |

---

## RAG Integration Details

### Document Upload Flow

```python
# Location: backend/services/rag_service.py:65-120
def upload_and_process_document(file_content, filename, user_id, metadata):
    """
    1. Save file to disk
    2. Process with DoclingProcessor
       - Extract text, tables, images
       - Split into chunks (1000 chars, 200 overlap)
    3. Generate embeddings
    4. Store in FAISS vector database
    5. Return processing results
    """
```

### Search Query Flow

```python
# Location: backend/services/rag_service.py:150-170
def search_documents(query: str, k: int = 5):
    """
    1. Convert query to embedding vector
    2. Perform FAISS similarity search
    3. Retrieve top-k most similar chunks
    4. Return with metadata (source, page, chunk_index)
    """
```

### Vector Store Structure

```
backend/data/
├── documents/                  # Uploaded PDFs/DOCX
│   ├── 20250101_120000_FAR.pdf
│   └── 20250101_120005_Strategy.docx
└── vector_db/
    └── faiss_index/           # FAISS index files
        ├── index.faiss        # Vector index
        └── metadata.json      # Document metadata
```

---

## Prompt Engineering Strategy

### Generation Prompt Structure

```
ROLE: "You are a DoD acquisition expert"
TASK: "Write [document name] for a federal procurement"

INPUTS:
  1. Assumptions: User-provided acquisition context
  2. RAG Context: Relevant chunks from uploaded documents
  3. Instructions: Formatting, compliance, tone

OUTPUT FORMAT:
  - Professional DoD language
  - FAR/DFARS citations
  - Inline references [1], [2]
  - 2-4 paragraphs per section
```

### Example Prompt

```
You are a DoD acquisition expert writing Section M - Evaluation Factors
for a federal procurement.

ASSUMPTIONS TO INCORPORATE:
- BVTO evaluation with weighted factors (Source: Acq Strategy §3.2)
- IDIQ base + 4 option years (Source: Acq Strategy §2.1)

RELEVANT SOURCE MATERIAL:
Source: FAR_15.304
Evaluation factors must be stated in the solicitation and include technical
approach, past performance, and price considerations...

---

Source: Acquisition_Strategy.docx
Best Value Tradeoff evaluation allows SSA to select other than lowest price
when justified by technical merit...

INSTRUCTIONS:
1. Write professional, compliant content for Section M
2. Include proper FAR/DFARS citations where applicable
3. Reference the assumptions provided
4. Use DoD acquisition terminology
5. Keep it concise but comprehensive (2-4 paragraphs)
6. Use inline citations like [1], [2], etc. for source references

Write the section content now:
```

---

## API Endpoints Summary

### POST `/api/generate-documents`
**Purpose:** Start document generation
**Input:** `{ assumptions, documents }`
**Output:** `{ task_id, message, documents_requested }`
**Auth:** Required (JWT token)

### GET `/api/generation-status/{task_id}`
**Purpose:** Poll generation progress
**Input:** `task_id` (path parameter)
**Output:** `{ status, progress, message, result }`
**Polling:** Every 2 seconds from frontend

### POST `/api/upload-document`
**Purpose:** Upload docs to RAG system
**Input:** File upload (multipart/form-data)
**Output:** `{ chunks_processed, embedding_count }`
**Processing:** Docling → Chunks → Embeddings → FAISS

---

## Performance Characteristics

| Metric | Value |
|--------|-------|
| **Generation Time** | 10-30 seconds (depends on # of documents) |
| **RAG Retrieval** | ~2-5 seconds for 20 chunks |
| **Claude API Call** | ~5-10 seconds per section |
| **Polling Interval** | 2 seconds |
| **Max Tokens** | 2000 per section |
| **Chunk Size** | 1000 characters (200 overlap) |
| **Vector Dimension** | 384 (FAISS embedding) |

---

## Error Handling

### Frontend
```typescript
try {
  const response = await ragApi.generateDocuments({...});
} catch (error: any) {
  toast.error(`Generation error: ${error.message}`);
  setRoute("GEN_PLAN");  // Return to plan view
}
```

### Backend
```python
try:
    # Generation logic...
except Exception as e:
    generation_tasks[task_id]["status"] = "failed"
    generation_tasks[task_id]["message"] = str(e)
```

---

## Future Enhancements

1. **WebSocket Integration** - Real-time progress updates instead of polling
2. **Agent Specialization** - Different prompts/models for different document types
3. **Multi-Agent Orchestration** - Planning agent → Writing agent → Review agent
4. **Streaming Responses** - Show text as it's being generated
5. **Feedback Loop** - User ratings → Fine-tuning → Better outputs
6. **Caching** - Cache RAG results for similar queries

---

## Summary

The AI agent integration follows a **RAG-enhanced generation pipeline**:

1. **Frontend** collects assumptions and document selections
2. **Backend** creates async task and starts RAG retrieval
3. **RAG Service** searches FAISS vector store for relevant context
4. **Claude Sonnet 4** generates document sections using retrieved context
5. **Citations** are extracted from RAG sources
6. **Frontend polls** for status and displays results in LiveEditor
7. **User edits** with compliance feedback and citation management

This architecture provides:
- ✅ **Scalability** - Background tasks don't block API
- ✅ **Accuracy** - RAG grounds generation in real documents
- ✅ **Traceability** - Citations link back to source material
- ✅ **Flexibility** - Easy to add new document types or agents
- ✅ **User Control** - Edit, approve, and refine generated content
