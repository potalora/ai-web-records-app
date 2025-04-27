# The AI Health Records Application

## Overview

An AI health web app to ingest arbitrary medical data (text, PDF, images, EHR exports, DICOM), summarize records, support diagnostics, suggest treatments, and locate specialists—all via cloud LLM APIs and locally in a Mac environment using Git (no GitHub).

## Key Features

- **Data Ingestion & Parsing**
  - Feed raw files (PDF, text, image, EHR exports) directly to cloud LLM document-understanding endpoints (e.g., OpenAI’s Document API, Anthropic’s DocReader) for entity extraction and chunked summarization.
  
- **Structured Data Handling**
  - Parse FHIR/HL7/C-CDA exports using lightweight Python libraries, then pass JSON to LLMs for normalization.

- **Medical Imaging**
  - DICOM files loaded via `pydicom`; extracted metadata and image series sent to LLM vision endpoints (OpenAI vision, Claude multimodal) for analysis prompts.

- **LLM-Driven Modules**
  - **Summarization & Extraction**: OpenAI GPT-4 Turbo, Anthropic Claude 3.7, Google Gemini Advanced for clinician-level summaries.
  - **Diagnostics & Treatment Planning**: Use same cloud LLMs with SMART-structured prompts for differential diagnoses and next-step recommendations.
  - **Semantic Search (RAG)**: Embed record chunks with Chroma/Weaviate; retrieve top-k relevant contexts for question answering.

- **Specialist Finder**
  - Integrate third-party medical directory APIs; map case profiles to provider network.

- **UI/UX**
  - Next.js + React + Tailwind CSS single-page dashboard; global search bar; patient timeline viewer.

- **Guidelines & Evidence Module**
  - Automatically search PubMed, ClinicalTrials.gov, and relevant medical guidelines (e.g., NICE, WHO, AHA) based on patient profile.
  - Allow user to upload or link specific studies, clinical trials, or guidelines to steer LLM responses.
  - Maintain an evidence cache with periodic refreshing to self-improve recommendations.

## Enhanced PDF Processing Strategy

To handle diverse PDF document types effectively (digitally native text, scanned images, mixed content), the application will implement a hybrid processing strategy:

1. **Initial Analysis:**
    - Upon receiving a PDF upload, the backend will first attempt to extract text content using the `PyPDF2` library.
    - A heuristic check (e.g., amount of coherent text extracted) will classify the PDF as primarily "text-based" or "image-based".

2. **Provider-Specific Handling:**
    - **If "text-based":** The extracted text will be sent directly to the selected LLM provider's API (OpenAI, Gemini, Anthropic) using their standard text input methods.
    - **If "image-based" (or text extraction fails):**
        - The PDF pages will be converted into images using the `pdf2image` library (which requires the `poppler` system dependency).
        - These images will be sent to the selected LLM provider's *vision-capable* API endpoint (e.g., GPT-4o, Gemini 1.5 Pro/Flash, Claude 3 Sonnet/Opus) in the appropriate format (e.g., base64 encoding).

3. **Goal:** Provide accurate summaries regardless of the PDF's internal structure (text vs. image-based).

4. **Dependencies:**
    - `PyPDF2`: For initial text extraction attempts.
    - `pdf2image`: For converting image-based PDFs to processable images.
        - Requires system dependency: `poppler`.

## Current Status (as of 2025-04-27)

- **Core Backend:** FastAPI application structure established.
- **Project Structure:** Refactored backend directory structure for clarity (services, ingestion, tests aligned).
- **Version Control:** Git repository initialized with appropriate `.gitignore`.
- **EHR Ingestion (TSV):**
  - Implemented `ehr_parser.py` in `backend/src/services/ingestion/`.
  - Handles batch processing of TSV files from a directory.
  - Supports multiple file encodings.
  - Integrates optional schema data from a JSON file.
  - Utilizes parallel processing (`concurrent.futures`) for performance.
  - Outputs Markdown files to a configurable directory (defaults to adjacent directory).
  - **Integrated into backend via `/ingest/ehr` POST endpoint using BackgroundTasks.**
- **PDF Ingestion:**
  - Basic PDF upload endpoint (`/summarize-pdf/`) implemented.
  - Hybrid PDF processing strategy implemented (`pdf_utils.py`):
    - Text extraction using `PyPDF2`.
    - Image conversion using `pdf2image` for scanned/image-based PDFs.
    - Heuristic (`TEXT_EXTRACTION_THRESHOLD_PER_PAGE`) to differentiate text vs. image PDFs.
- **LLM Integration (`llm_service.py`):**
  - Integration with OpenAI, Google Gemini, and Anthropic Claude APIs for summarization.
  - Handles both text and image inputs based on PDF analysis.
  - Dynamic model fetching implemented for OpenAI and Google (`model_registry.py`).
  - Static list for Anthropic models with an update script (`scripts/update_anthropic_models.py`).
  - `/models/` endpoint to expose available models to the frontend.
- **Rudimentary Evidence Module:**
  - Placeholder functionality exists for searching external sources (PubMed, etc.), but not yet integrated into summarization/diagnostic flows or RAG.

## Development Plan

Based on the current status and project goals, the following development phases are planned:

### Phase 1: Foundational Enhancements & Core Features

1. **Frontend Development:**
     - Build a clean, modern UI using Next.js, React, and Tailwind CSS.
     - Implement file upload component.
     - Display model selection options fetched from the `/models/` endpoint.
     - Display summarization results.
     - Basic patient context management (e.g., selecting a patient case).
2. **Expanded Data Ingestion:**
     - Add support for raw `.txt` file ingestion.
     - Implement DICOM file ingestion using `pydicom` (metadata extraction, passing image data to vision models).
     - **Completed:** Initial EHR TSV file parsing and Markdown conversion (`ehr_parser.py`).
     - **Completed:** Integrated `ehr_parser.py` into the backend service via the `/ingest/ehr` API endpoint.
     - **Next Steps:** Explore parsing other EHR formats (C-CDA, FHIR JSON/XML). Add more robust error handling and status tracking for background ingestion tasks.
3. **Prompt Engineering & Core LLM Functions:**
     - Develop and refine prompts for high-quality **Summarization** across different record types.
     - Develop initial prompts for **Diagnostic Support** (e.g., differential diagnoses based on summary).
     - Develop initial prompts for **Treatment Suggestions** (e.g., next steps, relevant guidelines).
4. **Security & Guardrails:**
     - Implement input/output sanitization and validation.
     - Add basic content moderation/safety checks suitable for a medical context (e.g., detecting harmful suggestions, ensuring factual grounding when possible).
     - Review and implement security best practices for local data handling (API key management, secure file storage/processing).

### Phase 2: RAG Integration & Evidence Grounding

1. **Vector Database Integration:**
     - Set up Chroma or Weaviate.
     - Implement document chunking strategies suitable for medical text.
     - Create embedding pipeline for ingested records (patient history).
2. **RAG Implementation:**
     - Integrate vector search results into Summarization, Diagnostics, and Treatment prompts to provide context.
     - Enhance the Evidence Module to ingest and index specific studies/guidelines provided by the user into the vector DB.
     - Allow LLM prompts to leverage both patient history and curated evidence from the RAG system.

### Phase 3: Advanced Features & Agentic Capabilities

1. **Specialist Finder:** Integrate with a medical directory API.
2. **Refined EHR Handling:** More robust parsing and integration of structured EHR data.
3. **User Feedback Loop:** Implement mechanisms for users to rate/correct LLM outputs.
4. **Agentic System Exploration:**
     - Define tools for the agent (e.g., `search_pubmed`, `retrieve_patient_history`, `analyze_dicom_image`).
     - Integrate with an agent framework or build custom orchestration logic.
     - Explore using MCP (Multi-Cog Proc) for more complex, multi-step reasoning tasks.

### Ongoing

- Testing (unit, integration, E2E).
- Documentation updates.
- Dependency management.
- Code formatting and linting.

## Architecture

```mermaid
digraph LR
  Frontend[Next.js Frontend] --> BackendAPI[FastAPI Backend]

  subgraph Backend
    direction TB
    BackendAPI --> Auth[Auth Service]
    BackendAPI --> RecordProcessing[Record Processing Service]
    BackendAPI --> LLMService[LLM Service]
    BackendAPI --> Storage[Data Storage Interface]

    RecordProcessing --> LocalTools[Local Tools: Tesseract, pydicom, PyPDF2]
    LLMService --> CloudLLMs[Cloud LLMs: OpenAI, Anthropic, Google]
    Storage --> PostgreSQL[PostgreSQL]
    Storage --> VectorDB[Vector DB: Chroma/Weaviate]
    Storage --> Neo4j[Neo4j Graph DB]
  end

  CloudLLMs --> ExternalAPIs[External APIs: PubMed, Specialist DBs]
```

## Tech Stack

- **Frontend**: Next.js, React, TypeScript 5.2, Tailwind CSS, Zustand, Axios
- **Backend**: Python 3.11, FastAPI, Uvicorn
- **Databases**: PostgreSQL (Prisma ORM), Neo4j
- **LLM APIs**: OpenAI, Google Gemini, Anthropic Claude (Latest Models)
- **Indexing**: Chroma / Weaviate
- **Testing**: Jest, Pytest, Playwright
- **Formatting**: Prettier, Black, Ruff
- **Environment**: Local Mac, Git

## Setup

1. Clone the repository.
2. Install backend dependencies: `pip install -r backend/requirements.txt`
3. Install frontend dependencies: `cd frontend && npm install`
4. Set up environment variables (`backend/.env`)
5. Run backend: `uvicorn backend.main:app --reload`
6. Run frontend: `cd frontend && npm run dev`

## Future Enhancements

- Integrate local LLM options (e.g., Ollama) for offline/private processing.
- Add support for more medical data types (DICOM, EHR formats like HL7/FHIR).
- Implement a more sophisticated RAG pipeline with advanced chunking and embedding strategies.
- Develop a user feedback mechanism for improving LLM responses.
- Add user authentication and RBAC.
- Implement robust audit trails.
