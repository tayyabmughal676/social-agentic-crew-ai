# Production Readiness & Security Checklist (fresh-todo.md)

This list outlines the security and production-readiness issues identified in the project, along with action items to address them before deploying to a production environment.

---

## 🔒 1. API Security & Authentication
- [x] **Implement API Key Authentication**: Add a security dependency (e.g., `APIKeyHeader` in FastAPI) to secure all endpoints (`/create-post`, `/workflow/*`, `/workflows`).
- [x] **Secure Workflow Modification/Deletion**: Restrict the `/workflow/{workflow_id}/approve` and `DELETE /workflow/{workflow_id}` routes so only authorized API clients can execute them.
- [ ] **Add Rate Limiting to Endpoints**: Prevent abuse/DoS attacks on resource-heavy LLM endpoints by implementing a rate limiter (e.g., `slowapi` or custom token-bucket middleware) on FastAPI routes.

---

## ⚙️ 2. Environment Variables & Secret Management
- [x] **Externalize LLM Configurations**: Move hardcoded values in `utils/llm_setup.py` (like model name, base URL, and API key) to environment variables in `.env`.
- [x] **Remove Hardcoded Placeholder Keys**: Remove statements setting `os.environ["OPENAI_API_KEY"]` to static dummy strings in `main.py` and `linkedin_workflow.py`. Use environment variables with sensible production defaults.
- [x] **Production CORS Policy**: Replace `allow_origins=["*"]` in `main.py` with a list loaded from an `ALLOWED_ORIGINS` environment variable.

---

## 💾 3. Database & Storage Safety
- [x] **Database Path Configuration**: Allow custom SQLite database path via environment variables instead of hardcoding `storage/db/workflows.db`.
- [ ] **Implement Database Backups / Migration Strategy**: Ensure a production-ready approach for backing up `workflows.db` or migrating to a managed DBMS (like PostgreSQL) for multi-worker environments.
- [ ] **Strict File Permissions**: Restrict read/write permissions on the `storage/` directory to prevent unauthorized process access.

---

## 🛠️ 4. Robust Validation & Error Handling
- [x] **Tighten Request Schema Limits**: Add constraints (`max_length`, `regex` patterns) for fields like `target_audience`, `tone`, and `urgency` in `models/schemas.py` to prevent excessively large payload injections.
- [ ] **Graceful Exception Exposure**: Sanitize error messages returned from the API to avoid exposing full stack traces or internal server details to users when LLMs or SQLite queries fail.
