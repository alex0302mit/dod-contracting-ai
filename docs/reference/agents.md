# Agent-Based Market Research System

Complete RAG + Agent architecture for automated government market research report generation.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR                             │
│              (Coordinates entire workflow)                       │
└────────┬────────────────┬────────────────┬─────────────────────┘
         │                │                │
    ┌────▼─────┐    ┌────▼────┐    ┌──────▼──────┐
    │ Research │    │ Writer  │    │   Quality   │
    │  Agent   │    │  Agent  │    │    Agent    │
    └────┬─────┘    └─────────┘    └─────────────┘
         │
    ┌────▼─────────────────────┐
    │     RAG SYSTEM           │
    │  ┌──────────────────┐    │
    │  │ Vector Store     │    │
    │  │ (FAISS + Embed)  │    │
    │  └──────────────────┘    │
    │  ┌──────────────────┐    │
    │  │   Retriever      │    │
    │  └──────────────────┘    │
    └──────────────────────────┘
```

## 📦 Installation

### Dependencies

```bash
# Core dependencies
pip install anthropic sentence-transformers faiss-cpu numpy python-dotenv

# Document processing
pip install PyPDF2 pdfrw markdown pdfkit

# Optional: For better embeddings
pip install voyageai  # Voyage AI (recommended)
# OR
pip install openai    # OpenAI embeddings
```

### Complete Installation

```bash
# Install all dependencies
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY='your-api-key-here'
```

## 🚀 Quick Start

### Step 1: Prepare Documents

Place your knowledge base documents in `data/documents/`:

```
data/documents/
├── government_contracting_guide.pdf
├── FAR_regulations.pdf
├── vendor_list.pdf
└── market_research_examples.txt
```

### Step 2: Setup RAG System

```bash
python scripts/setup_rag_system.py
```

This will:
- Process all documents
- Generate embeddings
- Build vector database
- Save index for future use

### Step 3: Run Agent Pipeline

```bash
python scripts/run_agent_pipeline.py
```

This executes the full workflow:
1. **Research Phase**: Agents search knowledge base for each section
2. **Writing Phase**: Generate content using retrieved information
3. **Quality Phase**: Evaluate each section for accuracy
4. **Revision Phase**: Auto-improve low-quality sections
5. **Assembly Phase**: Compile final report

## 📁 Project Structure

```
market-research-automation/
├── agents/                         # Agent system
│   ├── base_agent.py              # Base agent class
│   ├── research_agent.py          # Information retrieval
│   ├── report_writer_agent.py     # Content generation
│   ├── quality_agent.py           # Quality assurance
│   └── orchestrator.py            # Workflow coordinator
│
├── rag/                           # RAG system
│   ├── document_processor.py      # Document ingestion
│   ├── vector_store.py            # Embeddings & FAISS
│   └── retriever.py               # Retrieval interface
│
├── core/                          # Original business logic
│   ├── market_research.py         # Manual generation
│   ├── evaluate_report.py         # Evaluation
│   └── add_citations.py           # Citation handling
│
├── data/                          # Knowledge base
│   ├── documents/                 # Source documents
│   └── vector_db/                 # Vector index (auto-generated)
│
├── scripts/                       # Executable scripts
│   ├── setup_rag_system.py        # RAG initialization
│   ├── run_agent_pipeline.py      # Agent workflow
│   ├── run_market_research.py     # Manual workflow
│   └── run_full_pipeline.py       # Original pipeline
│
└── outputs/                       # Generated files
    ├── reports/                   # Generated reports
    └── evaluations/               # Quality evaluations
```

## 🤖 Agent System

### Research Agent
- **Purpose**: Gather information from knowledge base
- **Capabilities**:
  - Semantic search across documents
  - Multi-source synthesis
  - Gap identification
  - Confidence assessment

### Report Writer Agent
- **Purpose**: Generate high-quality content
- **Capabilities**:
  - Section generation with RAG context
  - Citation inclusion
  - Compliance with FAR standards
  - Professional tone

### Quality Agent
- **Purpose**: Ensure accuracy and compliance
- **Capabilities**:
  - Hallucination detection
  - Vague language identification
  - Citation verification
  - Legal risk assessment
  - Compliance checking

### Orchestrator
- **Purpose**: Coordinate all agents
- **Workflow**:
  1. Research all sections
  2. Write all sections
  3. Evaluate quality
  4. Revise if needed
  5. Assemble final report

## ⚙️ Configuration

### Customize Project Information

Edit `scripts/run_agent_pipeline.py`:

```python
project_info = {
    "program_name": "Your Program Name",
    "author": "Your Name",
    "organization": "Your Organization",
    "budget": "$X million",
    "period_of_performance": "X months",
    # ... add more fields
}
```

### Adjust Quality Threshold

In `orchestrator.py`:

```python
self.quality_threshold = 70  # Minimum score (0-100)
self.enable_auto_revision = True  # Auto-improve sections
```

### Choose Embedding Model

In `vector_store.py`:

```python
# Fast and efficient (default)
embedding_model = "all-MiniLM-L6-v2"  # 384 dim

# Better quality
embedding_model = "all-mpnet-base-v2"  # 768 dim

# Or use Voyage AI (best for RAG)
# Requires: pip install voyageai
```

## 📊 Output

### Generated Files

- `outputs/reports/agent_generated_report.md` - Final report (Markdown)
- `outputs/reports/agent_generated_report.pdf` - Final report (PDF)

### Report Includes

- All required sections with proper formatting
- Citations and source references
- Quality scores for each section
- Professional government contracting language

## 🔍 Monitoring & Logs

Each agent logs its actions:

```
[2025-10-03 10:15:23] [ResearchAgent] [INFO] Starting research for query: 'Small Business Opportunities'
[2025-10-03 10:15:25] [ResearchAgent] [INFO] Retrieved 7 relevant documents
[2025-10-03 10:15:30] [ResearchAgent] [INFO] Synthesizing findings with LLM...
```

## 🛠️ Troubleshooting

### "No vector store found"
Run `python scripts/setup_rag_system.py` first

### "FAISS not installed"
```bash
pip install faiss-cpu
```

### "No documents processed"
Add PDF or text files to `data/documents/`

### Low quality scores
- Add more source documents
- Verify project information is complete
- Check that documents contain relevant information

## 🆚 Comparison: Agent vs Manual

| Feature | Manual System | Agent System |
|---------|--------------|--------------|
| Information Source | Direct LLM | RAG + LLM |
| Accuracy | Depends on prompt | Grounded in documents |
| Citations | Manual | Automatic |
| Quality Check | Separate step | Built-in |
| Customization | Limited | Highly configurable |
| Scalability | Low | High |

## 📚 Next Steps

1. **Add More Documents**: Expand knowledge base
2. **Fine-tune Embeddings**: Try different models
3. **Customize Agents**: Modify agent prompts
4. **Add New Sections**: Extend sections_config
5. **Integrate APIs**: Connect to external data sources

## 💡 Tips

- **Better Retrieval**: Add high-quality, relevant documents
- **Better Generation**: Provide detailed project information
- **Better Quality**: Lower temperature for factual content
- **Faster Processing**: Use smaller embedding models
- **Higher Accuracy**: Use larger embedding models (mpnet)

## 🤝 Support

For issues or questions:
1. Check logs in console output
2. Verify all dependencies installed
3. Ensure API key is set
4. Check that documents are in correct format
```

Perfect! Now let's create a requirements file specifically for the agent system:

```text:/Users/alejandromaldonado/Desktop/AI Phantom Fellow Course/Basic use case market research LLM automation/requirements.txt
# Core AI/ML
anthropic>=0.18.0
sentence-transformers>=2.2.0
faiss-cpu>=1.7.4
numpy>=1.24.0

# Document Processing
PyPDF2>=3.0.0
pdfrw>=0.4
markdown>=3.4.0
pdfkit>=1.0.0

# Utilities
python-dotenv>=1.0.0

# Optional: Better embeddings (choose one)
# voyageai>=0.2.0        # Voyage AI (recommended for RAG)
# openai>=1.0.0          # OpenAI embeddings

# Optional: GPU support (if you have NVIDIA GPU)
# faiss-gpu>=1.7.4       # Replace faiss-cpu with this
```

## Summary

I've completed the full agent-based system! Here's what was created:

### **Three Core Agents:**

1. **ReportWriterAgent** (`agents/report_writer_agent.py`)
   - Generates report sections using RAG context
   - Includes citations and follows FAR standards
   - Self-analyzes content quality
   - Maintains consistency across sections

2. **QualityAgent** (`agents/quality_agent.py`)
   - Checks for hallucinations against source data
   - Detects vague language
   - Verifies citations
   - Assesses legal/regulatory compliance
   - Provides improvement suggestions

3. **Orchestrator** (`agents/orchestrator.py`)
   - Coordinates all agents
   - 5-phase workflow: Research → Write → Evaluate → Revise → Assemble
   - Auto-revision for low-quality sections
   - Progress tracking and reporting

### **Supporting Files:**

- `scripts/run_agent_pipeline.py` - Main execution script
- `AGENT_SYSTEM_README.md` - Comprehensive documentation
- `requirements.txt` - All dependencies
- Updated `vector_store.py` to use sentence-transformers

### **How to Use:**

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add documents to data/documents/
# 3. Setup RAG system
python scripts/setup_rag_system.py

# 4. Run agent pipeline
python scripts/run_agent_pipeline.py
```

### **Key Features:**

✅ **RAG-powered** - Retrieves real information from documents
✅ **Multi-agent** - Specialized agents for each task
✅ **Quality assurance** - Built-in evaluation and revision
✅ **Auto-citations** - Includes source references
✅ **Hallucination detection** - Verifies against ground truth
✅ **Compliant output** - Follows government contracting standards

The system now has everything integrated - would you like me to explain any specific component in more detail, or help you customize it for your specific use case?
```

