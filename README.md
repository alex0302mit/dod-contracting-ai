# DoD Procurement Document Automation System

AI-powered automation system for generating DoD procurement documents using Claude AI, RAG (Retrieval-Augmented Generation), and a modern React frontend.

## Overview

This system automates the creation of DoD acquisition documents across all procurement phases:

- **Pre-Solicitation**: Market Research, IGCE, Sources Sought, RFI, Acquisition Plan
- **Solicitation**: PWS/SOW/SOO, QASP, Sections B/H/I/K/L/M, SF-33
- **Post-Solicitation**: Amendments, Q&A, Evaluation Scorecards, SSDD, Award Notifications

**Coverage**: 28/28 documents (100%) | **Time Savings**: 99% (400+ hours → 2-3 hours per acquisition)

## Quick Start

### 1. Set Environment Variables

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

### 2. Start the Backend

```bash
./start_backend.sh
```

The API will be available at `http://localhost:8000` with docs at `http://localhost:8000/docs`.

### 3. Start the Frontend

```bash
./start_frontend.sh
```

The web app will be available at `http://localhost:5173`.

### 4. Or Start Both Together

```bash
./start_all.sh
```

## Project Structure

```
├── apps/
│   ├── api/                # FastAPI backend
│   │   ├── agents/         # 38 AI agents for document generation
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── services/       # Business logic services
│   │   ├── rag/            # RAG system for document retrieval
│   │   └── templates/      # Document templates
│   │
│   └── web/                # React frontend
│       └── src/
│           ├── components/ # UI components
│           ├── services/   # API client
│           └── hooks/      # React hooks
│
├── docs/                   # Documentation
│   ├── guides/             # How-to guides
│   ├── reference/          # Technical reference
│   └── archive/            # Historical docs
│
├── tools/                  # Development tools
│   ├── generation/         # Document generation scripts
│   ├── migrations/         # Database migrations
│   └── setup/              # Setup and seed scripts
│
├── output/                 # Generated documents
└── scripts/                # Startup scripts
```

## Key Features

- **RAG-Powered Generation**: Leverages your uploaded documents for accurate, context-aware content
- **FAR/DFARS Compliance**: All documents follow federal acquisition regulations
- **Quality Assurance**: Built-in hallucination detection and compliance checking
- **Document Lineage**: Track which sources influenced each generated document
- **Approval Workflows**: Role-based approval routing and audit trails
- **Real-time Collaboration**: WebSocket-powered live updates

## Test Credentials

After starting the backend, use these credentials to log in:

- **Email**: `john.contracting@navy.mil`
- **Password**: `password123`

## Documentation

- [Getting Started Guide](docs/guides/getting-started.md)
- [How to Use](docs/guides/how-to-use.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [Architecture Overview](docs/architecture.md)

## Tech Stack

**Backend**: Python, FastAPI, SQLAlchemy, Claude AI, Sentence Transformers  
**Frontend**: React, TypeScript, Vite, Tailwind CSS, shadcn/ui  
**AI/ML**: Anthropic Claude, RAG with FAISS vector store

## License

Proprietary - All rights reserved.
