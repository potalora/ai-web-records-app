# product_spec.md

## Purpose & Scope
An AI health web app to ingest arbitrary medical data (text, PDF, images, EHR exports, DICOM), summarize records, support diagnostics, suggest treatments, and locate specialists—all via cloud LLM APIs and locally in a Mac environment using Git (no GitHub).

## Key Features
1. **Data Ingestion & Parsing**  
   - Feed raw files (PDF, text, image, EHR exports) directly to cloud LLM document-understanding endpoints (e.g., OpenAI’s Document API, Anthropic’s DocReader) for entity extraction and chunked summarization.  
   - Minimal local preprocessing: OCR with Tesseract for images; metadata extraction via Python libraries when needed.
2. **Structured Data Handling**  
   - Parse FHIR/HL7/C-CDA exports using lightweight Python libraries, then pass JSON to LLMs for normalization.
3. **Medical Imaging**  
   - DICOM files loaded via `pydicom`; extracted metadata and image series sent to LLM vision endpoints (OpenAI vision, Claude multimodal) for analysis prompts.
4. **LLM-Driven Modules**  
   - **Summarization & Extraction**: OpenAI GPT-4 Turbo, Anthropic Claude 3.7, Google Gemini Advanced for clinician-level summaries.  
   - **Diagnostics & Treatment Planning**: Use same cloud LLMs with SMART-structured prompts for differential diagnoses and next-step recommendations.  
   - **Semantic Search (RAG)**: Embed record chunks with Chroma/Weaviate; retrieve top-k relevant contexts for question answering.
5. **Specialist Finder**  
   - Integrate third-party medical directory APIs; map case profiles to provider network.
6. **UI/UX**  
   - Next.js + React + Tailwind CSS single-page dashboard; global search bar; patient timeline viewer.
7. **Guidelines & Evidence Module**  
   - Automatically search PubMed, ClinicalTrials.gov, and relevant medical guidelines (e.g., NICE, WHO, AHA) based on patient profile.  
   - Allow user to upload or link specific studies, clinical trials, or guidelines to steer LLM responses.  
   - Maintain an evidence cache with periodic refreshing to self-improve recommendations.

## Architecture
```mermaid
digraph LR
  subgraph Ingestion
    PF[PDF/Text/Image/EHR] --> LLMDoc[LLM Document API]
    IM[DICOM] --> PD[pydicom] --> CL[LLM Vision API]
  end
  subgraph Processing
    LLMDoc & CL --> Norm[Data Normalizer]
    Norm --> Index[Vector Index]
    Norm --> LLM[LLM Orchestrator]
  end
  subgraph Backend
    API[FastAPI] --> Norm
    API --> LLM
    API --> Search[Search Endpoint]
    DB[(PostgreSQL/Neo4j)] --> Norm
    Index --> Search
  end
  subgraph Frontend
    UI[Next.js UI] --> API
  end
```  

## Tech Stack
- **Frontend:** Next.js, React, Tailwind CSS  
- **Backend:** Python 3.11, FastAPI, Uvicorn  
- **Database:** PostgreSQL (relational), Neo4j (knowledge graph)  
- **LLM APIs:** OpenAI GPT-4 Turbo, Anthropic Claude 3.7, Google Gemini Advanced  
- **Indexing:** Chroma or Weaviate embeddings store

## Security & Compliance
- **OWASP Top 10** safeguards: input validation, auth controls, rate limiting.  
- **Encryption:** TLS for in transit; AES-256 for at rest.  
- **Auth:** OAuth2 + JWT with least privilege.  
- **Audit Logging:** Record all record views/queries with user ID & timestamp.  
- **HIPAA‑style Dev Mode:** Pseudonymize PHI; real data behind opt‑in flags.

## System Prompts & RAG Workflow
- **Document Summarization Prompt:**
  ```
  You are a clinical summarization assistant. Given a medical record document (PDF/text), extract demographics, labs, diagnoses, medications, and procedures. Output CSV then narrative summary.
  ```
- **Diagnostic Prompt:**
  ```
  Role: Expert diagnostician. Input: patient summary + current labs/imaging. Output: top 3 differential diagnoses with rationale, next steps, and specialist suggestions.
  ```
- **RAG:** Chunk ingestion → embed → retrieve top-5 → combine with `Context` + `Question` in LLM call.

## Next Steps
1. Initialize local Git repo; commit `rules.md` & updated `product_spec.md`.  
2. Complete Phase 1: environment setup and sample PDF-to-summary slice.  
3. Design & build Phase 2: Evidence Retrieval & Guidelines Module (PubMed, trials, guideline ingestion).  
4. Iterate on ingestion and LLM prompt tuning.  
5. Conduct clinician review & refine evidence caching strategy.