# AI Health Records Application - CLAUDE.md

## Overview

The AI Health Records Application is an ambitious AI-driven health web application designed to ingest, process, and analyze diverse medical records. It leverages multiple cloud LLM APIs (OpenAI, Google Gemini, Anthropic Claude) to provide medical summarization, diagnostic support, treatment recommendations, and specialist finding capabilities.

## Development Conventions

### Language & Style Conventions

* **Languages:**
  * Frontend: TypeScript 5.x (Next.js, React)
  * Backend: Python 3.11 (FastAPI)
* **Formatting:** 
  * Frontend: Follow `.prettierrc` and `.eslintrc.js` configurations
  * Backend: Use Black and Ruff formatters per `pyproject.toml`
  * Auto-format all generated and modified code
* **Naming Conventions:**  
  * JS/TS variables & functions: `camelCase`  
  * Python variables & functions: `snake_case`  
  * Classes & React components: `PascalCase`  
  * Constants: `UPPER_SNAKE_CASE`  
  * File names match exported components/classes (e.g., `PatientDashboard.tsx`)
* **Comments & Documentation:**  
  * Use JSDoc/TSDoc for JS/TS public APIs  
  * Use Python docstrings for modules and functions  
  * Document all complex logic, especially prompt-engineering or security-related code
* **Imports:**  
  * Group in order: standard library, third-party, then project-local  
  * Prefer absolute imports from `src/`; avoid deep relative paths (`../../../`)

### Architecture & Design Patterns

* **Layered Architecture:**
  * `src/routes/`: API endpoint definitions  
  * `src/services/`: Business/domain logic  
  * `src/models/` or `src/database/`: Database models/repositories  
  * `src/components/`: React UI components, organized by feature
* **State Management:** 
  * Zustand for global state (planned)
  * React Context for localized state (auth implemented)
* **Error Handling:**  
  * Custom error classes in `src/errors/` (planned) 
  * API endpoints return `{ error: { code: string; message: string } }`  
  * Central logging via dedicated logger service
* **Database:** PostgreSQL with Prisma ORM  
  * Avoid N+1 queries; prefer joins or Prisma's `include`  
  * Manage schema changes via Prisma Migrate; do not use manual SQL edits

### Task-Specific Instructions

* **Converting Ingested Files:** All ingested source files (e.g., TSV, RTF, TXT) must be parsed and converted into Markdown (.md) format before being passed to LLMs for summarization, analysis, or other processing steps. This ensures a consistent input format for the language models.
* **Model Selection Based on API Results:** Always determine LLM availability and capabilities based strictly on the results returned by the relevant provider's API call (e.g., `list_models`). Never use assumptions about which models should be available or should have certain features.
* **Adding a New Ingestion Pipeline:**  
  1. Implement parser under `src/services/ingestion/`  
  2. Define validation schemas (Zod/Pydantic)  
  3. Write unit tests for parsing logic  
  4. Register the pipeline in the ingestion orchestrator
* **Integrating a New LLM Model:**  
  1. Create a client in `src/services/llm/`  
  2. Update model configs  
  3. Define TypeScript/Python interfaces  
  4. Add tests for prompt formatting and response validation

### Development Workflow

* **Milestone Completion:** After implementing significant features:
  1. **Refactor:** Review code for clarity, efficiency, and adherence to standards
  2. **Commit:** Use conventional commit messages (e.g., `feat:`, `fix:`, `refactor:`, `docs:`)
  3. **Document:** Update relevant documentation (README.md, CLAUDE.md, docstrings)
  4. **Sync Documentation:** Keep README.md and CLAUDE.md updated

### Constraints & Things to Avoid

* **DO NOT:** Use `any` in TypeScript without clear justification  
* **DO NOT:** Introduce new dependencies without discussion  
* **DO NOT:** Hardcode secrets, PHI, or API keys—use environment variables  
* **DO NOT:** Commit directly to `main`; use feature branches and PR reviews  
* **AVOID:** Monolithic functions—break logic into small, composable units  
* **AVOID:** Deprecated code or unmaintained libraries

## Technology Stack

### Backend
- **Framework**: Python 3.11 with FastAPI
- **Server**: Uvicorn with hot reload
- **LLM Integration**: OpenAI, Google Gemini, Anthropic Claude APIs
- **Document Processing**: 
  - PyPDF2, pdf2image, PyMuPDF (fitz) for PDF handling
  - pydicom for DICOM medical imaging (planned)
  - fhir.resources for FHIR/HL7 data parsing
  - striprtf for RTF document processing
- **Web Processing**: BeautifulSoup4, lxml for HTML/XML parsing
- **External APIs**: PubMed integration for medical evidence retrieval
- **Environment**: python-dotenv for configuration management
- **File Handling**: python-multipart for upload processing

### Frontend
- **Framework**: Next.js 15.2.4 with React 19
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS with shadcn/ui component library
- **UI Components**: 25+ Radix UI components (dialogs, forms, navigation, etc.)
- **Forms**: React Hook Form with Zod validation
- **Charts**: Recharts for data visualization
- **Icons**: Lucide React icon library

### Infrastructure
- **Database**: PostgreSQL with Prisma ORM (✅ Implemented)
  - Complete schema with 10+ tables for users, health records, documents, summaries
  - HIPAA-compliant with encryption, audit trails, and soft deletes
  - Session-based authentication with bcrypt password hashing
- **Vector Database**: Chroma/Weaviate for RAG functionality (Phase 2)
- **Graph Database**: Neo4j for relationship modeling (Phase 2)

## Project Architecture

### Directory Structure
```
ai_web_records_app/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── requirements.txt        # Python dependencies
│   ├── src/
│   │   ├── models/            # Data models and schemas
│   │   ├── routes/            # API route definitions
│   │   └── services/          # Business logic layer
│   │       ├── llm_service.py       # LLM API integrations
│   │       ├── model_registry.py    # Dynamic model discovery
│   │       ├── pdf_utils.py         # PDF processing utilities
│   │       ├── evidence_retriever.py # PubMed search integration
│   │       └── ingestion/           # Data ingestion pipelines
│   │           ├── ehr_parser.py    # EHR/TSV file processing
│   │           ├── rtf_processor.py # RTF document handling
│   │           └── media_processor.py # Media file processing
│   ├── tests/                 # Test suites
│   ├── scripts/               # Utility scripts
│   └── data/                  # Data storage (local development)
├── frontend/
│   ├── app/                   # Next.js App Router structure
│   │   ├── dashboard/         # Main application pages
│   │   ├── upload/            # File upload interfaces
│   │   └── layout.tsx         # Root layout component
│   ├── components/            # Reusable React components
│   └── lib/                   # Utility functions and configurations
└── docs/                      # Project documentation
```

### API Endpoints

#### Core Endpoints
- `GET /` - Health check
- `GET /health` - Comprehensive health check with database status
- `GET /models/` - List available LLM models by provider
- `POST /summarize-pdf/` - PDF summarization with provider/model selection
- `POST /upload/` - General file upload (FHIR JSON/XML, PDF)

#### Authentication Endpoints
- `POST /auth/register` - User registration with encrypted profile data
- `POST /auth/login` - User login with session token
- `POST /auth/logout` - User logout
- `GET /auth/session/validate` - Validate session token
- `POST /auth/password/change` - Change user password

#### Dashboard Endpoints
- `GET /dashboard/stats` - User statistics and metrics
- `GET /dashboard/recent-uploads` - Recent file uploads
- `GET /dashboard/health-summary` - Latest AI health summary
- `GET /dashboard/medical-records` - User's medical records list

#### Ingestion Endpoints
- `POST /ingest/ehr` - EHR directory ingestion (background processing)
- `POST /ingest/text` - Plain text file ingestion  
- `POST /ingest/files` - Multi-file upload with directory support

#### Evidence Retrieval (Phase 2)
- `POST /retrieve-evidence/pubmed` - PubMed medical evidence search

### Key Features Implemented

#### Backend Services
1. **LLM Service Integration** (`llm_service.py`)
   - Unified interface for OpenAI, Google Gemini, and Anthropic Claude
   - Lazy client initialization with error handling
   - Support for both text and multimodal (vision) capabilities

2. **Model Registry** (`model_registry.py`)
   - Dynamic model fetching for OpenAI and Google APIs
   - Static model lists with update scripts for Anthropic
   - Model capability detection (vision support, token limits)

3. **PDF Processing** (`pdf_utils.py`)
   - Hybrid processing strategy for text-based and image-based PDFs
   - Automatic detection and routing to appropriate LLM endpoints
   - Support for scanned documents via pdf2image conversion

4. **EHR Data Processing** (`ehr_parser.py`)
   - TSV file parsing with multiple encoding support
   - Parallel processing for large datasets
   - Markdown conversion for LLM consumption
   - Schema-aware parsing with JSON metadata integration

5. **Evidence Retrieval** (`evidence_retriever.py`)
   - PubMed API integration for medical literature search
   - Structured search results with abstracts and URLs

6. **Database Layer** (`src/database/`)
   - Prisma ORM with PostgreSQL integration
   - Complete schema with users, health records, documents, summaries
   - Singleton database client with connection pooling
   - Audit logging and access control

7. **Authentication System** (`src/services/auth/`)
   - Session-based authentication with secure tokens
   - Password hashing with bcrypt
   - User registration with encrypted profile data
   - Session validation and management

8. **Security Services** (`src/services/security/`)
   - AES-256-GCM encryption for sensitive data
   - Field-level encryption for PII
   - Master key management
   - HIPAA-compliant data handling

#### Frontend Components
- **Complete Dashboard Layout**: Real-time data from backend APIs
- **Authentication UI**: Login, registration, and protected routes
- **Multi-tab Upload Interface**: File upload, EHR import, text input
- **Navigation System**: Dashboard, records, summaries, settings
- **UI Component Library**: 25+ shadcn/ui components integrated
- **Real Data Integration**: Live health summaries and medical records
- **TypeScript API Client**: Type-safe backend communication
- **React Context**: Authentication state management

## Development Commands

### Backend Development
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload

# Run tests
pytest

# Update Anthropic models
python scripts/update_anthropic_models.py
```

### Frontend Development
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
# or
pnpm install

# Run development server
npm run dev

# Build for production
npm run build

# Run linting
npm run lint
```

### Environment Setup
Create a `.env` file in the backend directory with:
```env
# LLM API Keys
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Database
DATABASE_URL=postgresql://healthapp:password@localhost:5432/health_records_dev?schema=public

# Security
MASTER_KEY=your-32-byte-hex-master-key  # Generate with: openssl rand -hex 32
SESSION_SECRET=your-session-secret

# Server
PORT=8000
```

## Current Development Status

### ✅ Phase 1 Completed Features
- **Backend Infrastructure**
  - FastAPI backend with CORS middleware
  - PostgreSQL database with Prisma ORM
  - Complete authentication system with session management
  - HIPAA-compliant data encryption and audit logging
  
- **LLM Integration**
  - Complete integration for OpenAI, Google Gemini, and Anthropic Claude
  - Dynamic model selection and capability detection
  - PDF processing with hybrid text/image handling
  - Medical record summarization

- **Data Processing**
  - Multi-format file ingestion (PDF, FHIR, EHR, plain text)
  - EHR file parsing and conversion to Markdown
  - Background processing for large file batches
  - Document storage with encryption

- **Frontend Application**  
  - Next.js frontend with TypeScript
  - Complete authentication UI (login/register)
  - Real-time dashboard with user statistics
  - Medical records management interface
  - File upload with progress tracking
  - AI summary generation and display

### 🚀 Phase 1 Focus Areas
1. **Overview Dashboard**: Real-time health metrics and statistics
2. **Records Management**: Upload, view, and organize medical documents
3. **AI Summaries**: Generate and view AI-powered health summaries

### 📋 Phase 2 Planned Features
- **Evidence Search**: PubMed integration for medical literature
- **Specialist Finder**: Connect patients with appropriate specialists
- **Treatment Recommendations**: AI-powered treatment suggestions
- **Advanced Analytics**: Trends, predictions, and insights
- **DICOM Support**: Medical imaging file processing
- **Vector Database**: RAG for improved context understanding

## Key Development Patterns

### Backend Patterns
- **Layered Architecture**: Routes → Services → Models
- **Async/Await**: Throughout for non-blocking operations
- **Error Handling**: Custom exceptions with detailed logging
- **Lazy Initialization**: LLM clients created on first use
- **Background Processing**: For long-running ingestion tasks

### Frontend Patterns
- **App Router**: Next.js 13+ file-based routing
- **Component Composition**: shadcn/ui + custom components
- **TypeScript First**: Strict typing throughout
- **Server Components**: React Server Components where applicable

### Code Quality
- **Python**: Black formatting, Ruff linting
- **TypeScript**: ESLint, Prettier formatting
- **Testing**: pytest (backend), planned Jest (frontend)
- **Documentation**: Docstrings, JSDoc comments

## Security Considerations

### ✅ Implemented Security Features
- **Authentication**: Session-based auth with secure tokens
- **Password Security**: bcrypt hashing with salt
- **Data Encryption**: AES-256-GCM for sensitive fields
- **Audit Logging**: All data access tracked
- **Environment Variables**: Secure storage of API keys and secrets
- **CORS Configuration**: Restricted to allowed origins
- **File Validation**: Type and size restrictions

### 🔒 HIPAA Compliance Features
- **Encryption at Rest**: All PII encrypted in database
- **Access Controls**: Role-based permissions (PATIENT, PROVIDER, ADMIN)
- **Audit Trail**: Complete logging of PHI access
- **Data Isolation**: Row-level security for multi-tenancy
- **Soft Deletes**: Data retention for compliance

### 📋 Additional Production Requirements
- Rate limiting on API endpoints
- API security headers (CSP, HSTS, etc.)
- HTTPS enforcement
- Penetration testing
- Security monitoring and alerts
- Regular security audits

## Medical Domain Specifics

### Data Types Supported
- **PDF Documents**: Medical reports, lab results, prescriptions
- **EHR Exports**: TSV, HTM files from various systems
- **FHIR Resources**: JSON/XML format healthcare data
- **DICOM Images**: Medical imaging (planned)
- **Plain Text**: Clinical notes, reports

### Processing Pipeline
1. **Ingestion**: File upload and validation
2. **Parsing**: Format-specific data extraction
3. **Normalization**: Conversion to Markdown for LLM processing
4. **Analysis**: LLM-powered summarization and insights
5. **Storage**: Encrypted persistence in PostgreSQL database

### Compliance Considerations
- Local processing to maintain data privacy
- Encrypted storage of all sensitive data
- Complete audit trails for medical data access
- HIPAA-compliant data handling practices
- Role-based access control (RBAC)
- Data retention and soft delete policies

## Development Workflow

### Git Workflow
- Main branch: `master`
- Feature branches with descriptive names
- Conventional commit messages (`feat:`, `fix:`, `refactor:`, etc.)
- No direct commits to main branch

### Testing Strategy
- Unit tests for core services
- Integration tests for API endpoints
- E2E tests with Playwright (planned)
- Medical data validation tests

### Deployment
- Local development with hot reload
- Production deployment with Docker (planned)
- Environment-specific configuration
- Health checks and monitoring (planned)

## Roadmap

### Phase 1: Core Health Records Platform (✅ Complete)
**Focus**: Build a secure, HIPAA-compliant platform for managing medical records with AI summarization

1. **Records Management**
   - Multi-format file upload (PDF, FHIR, EHR)
   - Secure document storage with encryption
   - Medical record organization and viewing
   
2. **AI Summaries**
   - LLM-powered health summaries
   - Multi-provider support (OpenAI, Google, Anthropic)
   - Summary history and management
   
3. **Overview Dashboard**
   - Real-time health metrics
   - Recent uploads tracking
   - Activity monitoring

### Phase 2: Evidence & Insights (Planned)
**Focus**: Enhance the platform with medical evidence search and advanced analytics

1. **Evidence Search**
   - PubMed integration
   - Medical literature recommendations
   - Evidence-based insights
   
2. **Advanced Analytics**
   - Health trends visualization
   - Predictive insights
   - Risk assessment
   
3. **Specialist Finder**
   - Provider matching based on conditions
   - Referral management
   - Communication tools

### Phase 3: Clinical Integration (Future)
**Focus**: Enterprise features and healthcare system integration

1. **EHR Integration**
   - HL7 FHIR connectivity
   - Real-time data sync
   - Bidirectional updates
   
2. **DICOM Support**
   - Medical imaging processing
   - AI-powered image analysis
   - Radiology report generation
   
3. **Treatment Recommendations**
   - Personalized treatment plans
   - Drug interaction checking
   - Clinical decision support

## Resources and References

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Next.js Documentation**: https://nextjs.org/docs
- **shadcn/ui Components**: https://ui.shadcn.com/
- **OpenAI API**: https://platform.openai.com/docs
- **Google AI Studio**: https://aistudio.google.com/
- **Anthropic Claude**: https://docs.anthropic.com/
- **FHIR Standard**: https://www.hl7.org/fhir/
- **PubMed API**: https://www.ncbi.nlm.nih.gov/books/NBK25501/

This codebase represents a sophisticated foundation for AI-driven healthcare applications, with strong architectural patterns and comprehensive LLM integration ready for production development.