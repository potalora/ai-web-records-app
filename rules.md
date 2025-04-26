# rules.md

## 1. Core Objective
The primary goal of this project is to build an AI-driven health web application that ingests diverse medical records and leverages LLMs to summarize, diagnose, recommend treatments, and locate specialists. Keep this objective front and center when generating or reviewing code.

## 2. Language & Style Conventions

* **Languages:**
  * Frontend: TypeScript 5.2 (Next.js, React)
  * Backend: Python 3.11 (FastAPI)
* **Formatting:** Strictly follow `.prettierrc`, `.eslintrc.js`, and `pyproject.toml` (Black/Ruff). Auto‑format all generated and modified code.
* **Naming Conventions:**  
  * JS/TS variables & functions: `camelCase`  
  * Python variables & functions: `snake_case`  
  * Classes & React components: `PascalCase`  
  * Constants: `UPPER_SNAKE_CASE`  
  * File names match exported components/classes (e.g., `PatientDashboard.tsx`).
* **Comments & Documentation:**  
  * Use JSDoc/TSDoc for JS/TS public APIs.  
  * Use Python docstrings for modules and functions.  
  * Document all complex logic, especially prompt-engineering or security-related code.
* **Imports:**  
  * Group in order: standard library, third‑party, then project‑local.  
  * Prefer absolute imports from `src/`; avoid deep relative paths (`../../../`).

## 3. Architecture & Design Patterns

* **Overall Structure:** Layered architecture:
  * `src/routes/`: API endpoint definitions  
  * `src/services/`: Business/domain logic  
  * `src/db/` or `src/models/`: Database models/repositories  
  * `src/components/`: React UI components, organized by feature
* **State Management:** Zustand for global state; React Context for localized state.  
* **Error Handling:**  
  * Custom error classes in `src/errors/`.  
  * API endpoints return `{ error: { code: string; message: string } }`.  
  * Log errors via `src/logger.ts` central logger.
* **Database:** PostgreSQL with Prisma ORM.  
  * Avoid N+1 queries; prefer joins or Prisma’s `include`.  
  * Manage schema changes via Prisma Migrate; do not suggest manual SQL edits.

## 4. Key Libraries & Frameworks

* **Primary Frameworks:** Next.js (frontend), FastAPI (backend)  
* **UI Library:** React with Tailwind CSS  
* **Testing:**  
  * Unit & integration tests: Jest (TS), Pytest (Python)  
  * E2E tests: Playwright  
  * Place test files alongside code (e.g., `service.test.ts`).
* **API Client:** Use the shared Axios instance in `src/apiClient.ts` for external calls.

## 5. Domain-Specific Knowledge

* A `PatientRecord` must include: `id`, `patientId`, `timestamp`, `type`, and `content`.  
* Standard processing statuses: `INGESTED`, `NORMALIZED`, `SUMMARIZED`.  
* Specialist matching logic defined in `src/services/specialistFinder.ts`.

## 6. Constraints & Things to Avoid

* **DO NOT:** Use `any` in TypeScript without a clear comment and justification.  
* **DO NOT:** Introduce new dependencies without team discussion.  
* **DO NOT:** Hardcode secrets, PHI, or API keys—use environment variables (`process.env` or `.env`).  
* **DO NOT:** Commit directly to `main`; use feature branches and PR reviews.  
* **AVOID:** Monolithic functions—break logic into small, composable units.  
* **AVOID:** Deprecated code (tagged `@deprecated`) or unmaintained libraries.

## 7. Task-Specific Instructions

* **Adding a New Ingestion Pipeline:**  
  1. Implement parser under `src/services/ingestion/`.  
  2. Define validation schemas in `src/schemas/` (Zod/Pydantic).  
  3. Write unit tests for parsing logic.  
  4. Register the pipeline in the ingestion orchestrator.
* **Integrating a New LLM Model:**  
  1. Create a client in `src/services/llm/`.  
  2. Update model configs in `src/config/models.ts`.  
  3. Define TypeScript/Python interfaces in `src/models/llm.ts`.  
  4. Add tests for prompt formatting and response validation.
* **Refactoring Code:**  
  * Ensure all existing tests pass.  
  * Update relevant docs in `docs/`.  
  * Perform prompt-hallucination audit on related LLM code.