## Phân tích tình trạng hiện tại

### Đã hoàn thành (Phase 1 - Setup & Foundation)
- uv workspace monorepo với `pyproject.toml` ở root, backend, frontend [0-cite-0](#0-cite-0)
- Cấu hình Ruff, Mypy, Pre-commit hooks, Makefile [0-cite-1](#0-cite-1)
- SRDS v2.1 hoàn chỉnh (16 sections, rất chi tiết) [0-cite-2](#0-cite-2)
- Dependencies backend đã khai báo: FastAPI, LangGraph, langchain-openai, qdrant-client, pydantic-settings, uvicorn [0-cite-3](#0-cite-3)

### Chưa có code thực tế
- `backend/` chỉ có `pyproject.toml`, **không có thư mục `app/`**, không có `main.py`, không có bất kỳ file Python nào

- `frontend/` chỉ có `pyproject.toml`, **không có `app.py`**, không có `pages/`, `components/`


### Các vấn đề cần sửa ngay
| Vấn đề | Chi tiết |
|--------|----------|
| Thiếu LlamaIndex | SRDS quy định dùng LlamaIndex cho RAG nhưng chưa có trong `backend/pyproject.toml` |
| README chưa hoàn thiện | Còn nhiều placeholder `[Project Name]`, `[Feature Name 6]`, `[Step 1 Name]`... |
| Thiếu `.env.example` | Được nhắc trong docs nhưng chưa có trong repo |
| Thiếu `docs/DFD.md` | README reference nhưng file không tồn tại |
| Badge sai | README dùng badge của NVIDIA repo thay vì repo hiện tại |

-------------

Đúng, plan 7 milestones mà tôi đã trình bày ở trên chính là plan tổng thể chi tiết của toàn bộ dự án, được xây dựng dựa trên **SRDS Section 14 - Implementation Roadmap**.

Cụ thể, SRDS định nghĩa 7 milestones ở mức high-level:

| Milestone | SRDS (Section 14) | Plan của tôi |
|-----------|-------------------|--------------|
| 1 | Foundation (6 bullet points) | **9 tasks** - breakdown chi tiết với file paths cụ thể |
| 2 | Data and Auth Foundation (4 bullet points) | **8 tasks** - thêm audit service, consent model |
| 3 | RAG Foundation (5 bullet points) | **6 tasks** - thêm CLI, test retrieval |
| 4 | Agent Workflow (6 bullet points) | **10 tasks** - thêm state definition, graph compilation, LLM abstraction |
| 5 | UI Workflows (5 bullet points) | **11 tasks** - tách riêng backend API + frontend pages + components |
| 6 | Safety and Evaluation (5 bullet points) | **6 tasks** - thêm Langfuse integration |
| 7 | Production Readiness (6 bullet points) | **7 tasks** - thêm CI/CD, Docker |

Plan của tôi **mở rộng** từ SRDS bằng cách:
1. **Gán file path cụ thể** cho mỗi task (SRDS chỉ mô tả chức năng, không chỉ file)
2. **Tách nhỏ hơn** - ví dụ Milestone 5 trong SRDS gộp UI, nhưng plan tách riêng backend API endpoints và frontend pages
3. **Bổ sung tasks thiếu** mà SRDS ngầm yêu cầu nhưng không liệt kê rõ (như `state.py`, `graph.py`, `llm_service.py`, `.env.example`, sửa README)

Ngoài ra, SRDS còn có **Deployment Roadmap (Section 13)** với 4 phases dài hạn hơn:
- **Phase 1 (Local MVP)** ≈ Milestone 1-6
- **Phase 2 (Clinical-Grade)** ≈ Milestone 6-7 nâng cao
- **Phase 3 (Production Privacy-First)** ≈ Milestone 7
- **Phase 4 (Sovereign Enterprise)** = ngoài scope MVP (LiteLLM, vLLM, K8s, Keycloak, NATS, Neo4j...)

Phase 4 **không nằm trong plan** vì nó thuộc "Out of Scope for MVP" theo SRDS Section 15.

**Tóm lại:** Plan 7 milestones này cover toàn bộ scope MVP của dự án. Khi hoàn thành cả 7 milestones, project sẽ đạt được **Success Criteria** mà SRDS Section 16 định nghĩa - bao gồm patient chat, safety guardrails, clinical profile generation, doctor copilot, RAG tracing, và basic safety tests.

---

## Plan chi tiết theo 7 Milestones (từ SRDS Section 14)

Dưới đây là breakdown chi tiết từng milestone thành các task cụ thể, kèm file path cần tạo/sửa:

---

### Milestone 1: Foundation (Ưu tiên cao nhất - Làm ngay)

| # | Task | File/Path | Mô tả |
|---|------|-----------|-------|
| 1.1 | Tạo cấu trúc thư mục backend | `backend/app/` + tất cả subdirs | Tạo `api/`, `core/`, `agents/`, `services/`, `schemas/`, `db/`, `ingestion/` với `__init__.py` |
| 1.2 | FastAPI entrypoint | `backend/app/main.py` | App factory, CORS middleware, router include, lifespan events |
| 1.3 | Config loading | `backend/app/core/config.py` | Pydantic Settings class đọc `.env` (OPENAI_API_KEY, QDRANT_URL, SUPABASE_URL, SUPABASE_KEY) |
| 1.4 | Health check endpoint | `backend/app/api/health.py` | `GET /health` trả về status, version, uptime |
| 1.5 | Tạo cấu trúc frontend | `frontend/app.py`, `frontend/pages/`, `frontend/components/` | Streamlit entrypoint cơ bản với navigation |
| 1.6 | Tạo `.env.example` | `.env.example` | Template cho tất cả env vars |
| 1.7 | Thêm LlamaIndex dependency | `backend/pyproject.toml` | `uv add --package backend llama-index llama-index-vector-stores-qdrant llama-index-embeddings-openai` |
| 1.8 | Sửa README.md | `README.md` | Xóa placeholder, sửa badge, điền thông tin thực tế |
| 1.9 | Tạo DFD.md | `docs/DFD.md` | Data Flow Diagram dựa trên SRDS Section 10 |

---

### Milestone 2: Data & Auth Foundation

| # | Task | File/Path | Mô tả |
|---|------|-----------|-------|
| 2.1 | Supabase client setup | `backend/app/db/supabase_client.py` | Singleton Supabase client connection |
| 2.2 | Database schema SQL | `backend/app/db/migrations/` hoặc `docs/schema.sql` | Bảng: `users`, `roles`, `doctor_assignments`, `chat_sessions`, `chat_messages`, `clinical_profiles`, `stress_scores`, `consent_records`, `audit_logs` |
| 2.3 | User & Role models | `backend/app/schemas/user.py` | Pydantic models: UserCreate, UserResponse, Role enum (Patient, Doctor, Admin) |
| 2.4 | Auth endpoints | `backend/app/api/auth.py` | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| 2.5 | RBAC middleware | `backend/app/core/security.py` | JWT verification, role-based dependency injection (`get_current_user`, `require_role`) |
| 2.6 | Doctor assignment CRUD | `backend/app/api/admin.py` | Endpoints quản lý doctor-patient assignment |
| 2.7 | Consent record model | `backend/app/schemas/consent.py` | ConsentRecord schema + endpoint accept consent |
| 2.8 | Audit log service | `backend/app/services/audit_service.py` | Hàm ghi audit log cho mọi sensitive action |

---

### Milestone 3: RAG Foundation (Data Ingestion + Retrieval)

| # | Task | File/Path | Mô tả |
|---|------|-----------|-------|
| 3.1 | Thu thập DSM-5 VN | `backend/data/raw/` | Thu thập tài liệu DSM-5 tiếng Việt, treatment guidelines |
| 3.2 | Ingestion pipeline | `backend/app/ingestion/load_dsm5.py` | LlamaIndex: Load PDF → Semantic Chunking → Metadata enrichment → Embed → Upload Qdrant |
| 3.3 | Qdrant service | `backend/app/services/qdrant_service.py` | Khởi tạo Qdrant client, tạo collections (treatment_knowledge, dsm5_clinical, safety_policy) |
| 3.4 | LlamaIndex RAG service | `backend/app/services/rag_service.py` | Query engine với hybrid search, reranking, metadata filters (patient-safe vs doctor-only) |
| 3.5 | Ingestion CLI | `backend/app/ingestion/cli.py` | Makefile command `make ingest` để chạy pipeline |
| 3.6 | Retrieval tests | `backend/tests/test_retrieval.py` | Test semantic search accuracy, metadata filtering |

---

### Milestone 4: Agent Workflow (LangGraph)

| # | Task | File/Path | Mô tả |
|---|------|-----------|-------|
| 4.1 | Agent State definition | `backend/app/agents/state.py` | TypedDict/Pydantic state: messages, user_role, session_id, safety_flag, clinical_data |
| 4.2 | Router Agent | `backend/app/agents/router.py` | Route theo role (patient/doctor), session state, safety status |
| 4.3 | Safety Guardrail Agent | `backend/app/agents/safety_guard.py` | Detect crisis, self-harm, violence → bypass normal flow → safety response |
| 4.4 | Patient Empathetic Agent | `backend/app/agents/patient_agent.py` | Empathetic response, no diagnosis, coping exercises, grounded in treatment KB |
| 4.5 | Silent Clinical Analyzer | `backend/app/agents/clinical_analyzer.py` | Post-session: extract symptoms, risk markers, generate doctor-facing profile |
| 4.6 | DSM-5 Retrieval Agent | `backend/app/agents/dsm5_agent.py` | Doctor-only: retrieve DSM-5 criteria, differential diagnosis support |
| 4.7 | Doctor Copilot Agent | `backend/app/agents/doctor_copilot.py` | 2 modes: patient-context mode + clinical-knowledge mode, citations |
| 4.8 | Graph compilation | `backend/app/agents/graph.py` | LangGraph StateGraph: compile nodes + edges + conditional routing |
| 4.9 | LLM Provider abstraction | `backend/app/services/llm_service.py` | Abstract LLM calls, configurable provider (OpenAI/Gemini), future LiteLLM |
| 4.10 | Agent tests | `backend/tests/test_agents.py` | Test routing logic, safety detection, response quality |

---

### Milestone 5: Backend API + UI Workflows

| # | Task | File/Path | Mô tả |
|---|------|-----------|-------|
| 5.1 | Chat API | `backend/app/api/chat.py` | `POST /chat` - patient chat endpoint, streaming support |
| 5.2 | Session API | `backend/app/api/sessions.py` | `POST /sessions/end`, `GET /sessions/{id}`, inactivity timeout |
| 5.3 | Clinical profile API | `backend/app/api/clinical.py` | `GET /patients/{id}/profile`, `GET /patients/{id}/scores` |
| 5.4 | Doctor dashboard API | `backend/app/api/dashboard.py` | `GET /doctor/patients` (list, search, filter by risk) |
| 5.5 | Patient Chat UI | `frontend/pages/chat.py` | Streamlit chat interface, streaming, empathetic UX |
| 5.6 | Doctor Patient List | `frontend/pages/doctor_dashboard.py` | Danh sách bệnh nhân, filter, search |
| 5.7 | Clinical Profile View | `frontend/pages/patient_profile.py` | Xem clinical profile, evidence snippets |
| 5.8 | Stress/Risk Trend View | `frontend/pages/risk_trends.py` | Plotly charts cho stress/risk score trends |
| 5.9 | Doctor Copilot Chat UI | `frontend/pages/doctor_copilot.py` | Chat interface cho doctor copilot |
| 5.10 | Auth UI | `frontend/pages/login.py` | Login/Register, role-based routing |
| 5.11 | Reusable components | `frontend/components/` | Chat bubble, metric cards, sidebar navigation |

---

### Milestone 6: Safety & Evaluation

| # | Task | File/Path | Mô tả |
|---|------|-----------|-------|
| 6.1 | Crisis prompt test set | `backend/tests/safety/test_crisis.py` | Test suicidal ideation, self-harm, panic attack |
| 6.2 | No-diagnosis test set | `backend/tests/safety/test_no_diagnosis.py` | Test patient requests for diagnosis → AI refuses |
| 6.3 | RAG faithfulness eval | `backend/tests/evaluation/test_rag_quality.py` | Ragas/DeepEval: faithfulness, hallucination rate |
| 6.4 | Red-team prompts | `backend/tests/safety/test_red_team.py` | Prompt injection, reveal hidden analysis attempts |
| 6.5 | Langfuse integration | `backend/app/services/langfuse_service.py` | Trace prompts, retrieval, latency, cost |
| 6.6 | Langfuse eval workflow | `backend/tests/evaluation/test_langfuse_traces.py` | Regression tracking qua Langfuse datasets |

---

### Milestone 7: Production Readiness

| # | Task | File/Path | Mô tả |
|---|------|-----------|-------|
| 7.1 | Docker Compose | `docker-compose.yml` | Backend, Frontend, Qdrant, Supabase/Postgres |
| 7.2 | Dockerfiles | `backend/Dockerfile`, `frontend/Dockerfile` | Multi-stage builds |
| 7.3 | CI/CD | `.github/workflows/ci.yml` | Lint, type-check, test on PR |
| 7.4 | Secret management docs | `docs/deployment.md` | Hướng dẫn Vault/K8s Secrets |
| 7.5 | Monitoring | Langfuse + OpenTelemetry config | Prometheus metrics, Grafana dashboards |
| 7.6 | Backup & restore | `docs/operations.md` | Supabase backup, Qdrant snapshot |
| 7.7 | Compliance checklist | `docs/compliance.md` | GDPR, HIPAA, VN cybersecurity review |

---

### Thứ tự ưu tiên thực hiện

``` mermaid
graph LR
    M1["Milestone 1: Foundation"] --> M2["Milestone 2: Data & Auth"]
    M1 --> M3["Milestone 3: RAG"]
    M2 --> M4["Milestone 4: Agents"]
    M3 --> M4
    M4 --> M5["Milestone 5: API + UI"]
    M5 --> M6["Milestone 6: Safety & Eval"]
    M6 --> M7["Milestone 7: Production"]
```

**Milestone 2 và 3 có thể làm song song** vì không phụ thuộc lẫn nhau. Milestone 4 cần cả 2 hoàn thành trước (agents cần cả DB lẫn RAG).

---------------
