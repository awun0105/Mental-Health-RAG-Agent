# LỊCH SỬ & KẾ HOẠCH DỰ ÁN AI-Mental-Health-Agent (Mental Health AI Platform)

**Ngày bắt đầu:** 19/04/2026
**Cập nhật lần cuối:** 20/04/2026
**Phiên bản SRDS:** 1.0 (19/04/2026)

---

## Tổng quan dự án (Theo SRDS)

**Mental Health AI Platform** là nền tảng AI hỗ trợ lâm sàng, đóng vai trò cầu nối giữa **Bệnh nhân** và **Bác sĩ/Chuyên gia tâm lý**.

Hệ thống sử dụng **LlamaIndex (RAG)** + **LangGraph (Multi-Agent)**, lấy kiến thức cốt lõi từ **DSM-5 bản tiếng Việt**, tuân thủ nghiêm ngặt nguyên tắc **Human-in-the-Loop** và **không chẩn đoán trực tiếp cho bệnh nhân**.

---

## 9 Giai đoạn Dự án (Roadmap)

| STT | Giai đoạn | Trạng thái | Thời gian dự kiến | Hoàn thành |
|-----|-----------|------------|-------------------|------------|
| 1   | Setup & Foundation | ✅ Hoàn thành | 19–20/04/2026 | 20/04/2026 |
| 2   | Data Collection & Ingestion (DSM-5 VN) | ⏳ Chưa bắt đầu | 2 tuần | - |
| 3   | RAG Core (LlamaIndex) + Safety Guardrails | ⏳ Chưa bắt đầu | 2 tuần | - |
| 4   | Multi-Agent System (LangGraph) | ⏳ Chưa bắt đầu | 2.5–3 tuần | - |
| 5   | Backend API + Role-Based Access | ⏳ Chưa bắt đầu | 2 tuần | - |
| 6   | Supabase Integration | ⏳ Chưa bắt đầu | 1.5 tuần | - |
| 7   | Clinical Dashboard & Patient Chat UI | ⏳ Chưa bắt đầu | 2 tuần | - |
| 8   | Testing, Evaluation & Clinical Safety | ⏳ Chưa bắt đầu | 2–3 tuần | - |
| 9   | Deployment, Observability (Langfuse) & Go-Live | ⏳ Chưa bắt đầu | 2 tuần | - |

---

## Chi tiết từng giai đoạn

### Giai đoạn 1: Setup & Foundation ✅ (19–20/04/2026)

**Trạng thái:** Hoàn thành

**Những gì đã làm:**

- Khởi tạo monorepo sử dụng `uv` Workspace
- Cấu hình Ruff, Mypy, Pre-commit hooks, Makefile
- Xây dựng cấu trúc thư mục chuẩn theo SOP
- Viết và hoàn thiện `[11setu_process.md`
- Tạo file **SRDS.md** phiên bản 1.0
- Cấu hình Git và track `_notes/`

**Commit chính:**

- `feat: initialize uv monorepo and enterprise tooling`
- `docs: create detailed SRDS v1.0`
- `docs: add combined project history & roadmap`

**Vấn đề gặp phải:**

- Ban đầu `_notes/` bị ignore trong `.gitignore` nên phải xử lý thủ công `git add` và xóa cache.
- Cần tinh chỉnh nhiều lần cấu hình `pyproject.toml`.

**Bài học rút ra:**

- Viết SRDS sớm giúp định hướng rõ ràng toàn bộ dự án.
- Luôn kiểm tra `.gitignore` ngay từ đầu.

**Next actions:**

- Bắt đầu Giai đoạn 2: Thu thập và Ingestion DSM-5 tiếng Việt.

---

### Giai đoạn 2: Data Collection & Ingestion (DSM-5 VN) ⏳ (Dự kiến: 21/04 – 04/05/2026)

**Trạng thái:** Chưa bắt đầu

**Công việc chính:**

- Thu thập DSM-5 bản tiếng Việt và tài liệu lâm sàng liên quan
- Xây dựng pipeline ingestion (`backend/app/ingestion/`)
- Semantic Chunking + Metadata-rich
- Embedding và upload vào Qdrant (sử dụng LlamaIndex)

**Vấn đề gặp phải:** (Sẽ ghi khi thực hiện)

- ...

**Bài học rút ra:** (Sẽ ghi khi thực hiện)

- ...

**Next actions sau giai đoạn này:** Xây dựng RAG Core với LlamaIndex

---

### Giai đoạn 3: RAG Core (LlamaIndex) + Safety Guardrails ⏳

**Trạng thái:** Chưa bắt đầu

**Công việc chính:**

- Xây dựng RAG pipeline sử dụng **LlamaIndex**
- Hybrid Search, Reranking, Context Compression
- Triển khai Safety Guardrails (suicidal ideation, crisis, nocebo prevention)
- Prompt engineering để tránh chẩn đoán trực tiếp cho bệnh nhân

**Vấn đề gặp phải:** (Sẽ ghi khi thực hiện)

- ...

**Bài học rút ra:** (Sẽ ghi khi thực hiện)

- ...

**Next actions sau giai đoạn này:** Phát triển Multi-Agent với LangGraph

---

### Giai đoạn 4: Multi-Agent System (LangGraph) ⏳

**Trạng thái:** Chưa bắt đầu

**Công việc chính:**

- Thiết kế State và workflow sử dụng **LangGraph**
- Các Agent chính: Empathetic Listener, Silent Analyzer, Safety Guard, Academic Copilot, Router
- Tích hợp LlamaIndex tools vào LangGraph
- State persistence với Supabase

**Vấn đề gặp phải:** (Sẽ ghi khi thực hiện)

- ...

**Bài học rút ra:** (Sẽ ghi khi thực hiện)

- ...

**Next actions sau giai đoạn này:** Xây dựng Backend API + RBAC

---

### Giai đoạn 5: Backend API + Role-Based Access ⏳

**Trạng thái:** Chưa bắt đầu

**Công việc chính:**

- FastAPI routes, authentication, RBAC (Patient/Doctor)
- Tích hợp LlamaIndex và LangGraph vào API

**Vấn đề gặp phải:** (Sẽ ghi khi thực hiện)

- ...

**Bài học rút ra:** (Sẽ ghi khi thực hiện)

- ...

**Next actions sau giai đoạn này:** Tích hợp Supabase

---

### Giai đoạn 6: Supabase Integration ⏳

**Trạng thái:** Chưa bắt đầu

**Công việc chính:**

- User management, Chat history, Clinical Profile, LangGraph checkpointing

**Vấn đề gặp phải:** (Sẽ ghi khi thực hiện)

- ...

**Bài học rút ra:** (Sẽ ghi khi thực hiện)

- ...

**Next actions sau giai đoạn này:** Phát triển UI

---

### Giai đoạn 7: Clinical Dashboard & Patient Chat UI ⏳

**Trạng thái:** Chưa bắt đầu

**Công việc chính:**

- Patient Chat Interface (empathetic + streaming)
- Doctor Clinical Dashboard
- Role-based routing

**Vấn đề gặp phải:** (Sẽ ghi khi thực hiện)

- ...

**Bài học rút ra:** (Sẽ ghi khi thực hiện)

- ...

**Next actions sau giai đoạn này:** Testing & Safety

---

### Giai đoạn 8: Testing, Evaluation & Clinical Safety ⏳

**Trạng thái:** Chưa bắt đầu

**Công việc chính:**

- Unit/Integration/E2E tests
- RAG Evaluation (LlamaIndex) + LangGraph workflow testing
- Safety & Clinical validation

**Vấn đề gặp phải:** (Sẽ ghi khi thực hiện)

- ...

**Bài học rút ra:** (Sẽ ghi khi thực hiện)

- ...

**Next actions sau giai đoạn này:** Deployment

---

### Giai đoạn 9: Deployment, Observability (Langfuse) & Go-Live ⏳

**Trạng thái:** Chưa bắt đầu

**Công việc chính:**

- Docker, CI/CD, Langfuse integration (trace LlamaIndex + LangGraph)

**Vấn đề gặp phải:** (Sẽ ghi khi thực hiện)

- ...

**Bài học rút ra:** (Sẽ ghi khi thực hiện)

- ...

**Next actions sau giai đoạn này:** Triển khai pilot & cải tiến liên tục

---

**Ghi chú chung:**

- Công nghệ cốt lõi: **LlamaIndex (RAG)** + **LangGraph (Agent Orchestration)**.
- Ưu tiên cao nhất: An toàn lâm sàng và Human-in-the-Loop.
