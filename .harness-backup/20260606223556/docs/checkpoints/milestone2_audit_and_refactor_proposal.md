# Milestone 2 — Audit + Đề xuất Refactor `[3]database_auth_implementation_process.md`

> **Lưu ý:** Tài liệu này CHỈ là proposal. Chưa có file code/docs nào trong repo bị sửa.
> Tôi sẽ chỉ tiến hành refactor file `docs/_notes/[3]database_auth_implementation_process.md`
> sau khi nhận được **xác nhận rõ ràng** từ bạn.

---

## 1. Phạm vi đã rà soát

| Nguồn | Mục đích đọc |
|------|--------------|
| `docs/.plan/MASTER_PLAN.md` | Hiểu 7 milestones tổng thể, mức độ chi tiết của Milestone 2 |
| `docs/.plan/MILESTONE1.md` / `MILESTONE2.md` | Lấy danh sách task gốc 2.1 → 2.27, mock test/frontend/Google OAuth |
| `docs/AGENT.md` | Reference architecture principles (Layered, SOLID, Repository/Service/Strategy) |
| `docs/schema.sql` | Đối chiếu cột thực tế của các bảng với code repository |
| `docs/_notes/[2]E2E_database_design_and_development.md` | Hiểu strategy database, role separation, audit-ready |
| `docs/_notes/[3]database_auth_implementation_process.md` | **File sẽ refactor** — đọc full 2037 dòng |
| `backend/app/**` (35 file Python) | Audit code Milestone 2 |
| `frontend/main.py`, `Makefile`, `.env.example`, `pre-commit-config` | Verify môi trường + frontend status |
| `make check` (`ruff` + `mypy strict`) | Confirm lint/type clean |

---

## 2. Đánh giá hoàn thành Milestone 2

### 2.1 Đã hoàn thành (xác nhận bằng code + manual smoke test)

| # | Task | Trạng thái | Bằng chứng |
|---|------|------------|------------|
| 2.1 | Dependencies (supabase, passlib, python-jose, pin bcrypt 4.3.0) | ✅ | `backend/pyproject.toml`, `uv.lock` |
| 2.2 | `core/config.py` đọc root `.env` cố định bằng `Path` | ✅ | Patch `PROJECT_ROOT = Path(...).parents[3]` |
| 2.3 | `docs/schema.sql` đầy đủ 8 bảng + `GRANT ... TO service_role` | ✅ | `docs/schema.sql:437-445` |
| 2.4 | `core/constants.py` (UserRole, AuthProvider, AuditAction…) | ✅ | 7 enum, đủ vocabulary |
| 2.5 | `core/exceptions.py` (App/Not/Already/Unauth/Forbidden/Invalid/Consent/DatabaseError) | ✅ | Handler đã đổi sang `exc: Exception` |
| 2.6 | `db/supabase_client.py` singleton manager | ✅ | OK |
| 2.7 | `db/repositories/base.py` Generic `BaseRepository[ModelT]` | ✅ | JSONValue/JSONRow type alias |
| 2.8 | Pydantic schemas (user/consent/audit/assignment/session) | ✅ | All `from_attributes=True` |
| 2.9 → 2.12 | UserRepository / ConsentRepository / AuditRepository / AssignmentRepository | ✅ | 4 file đầy đủ |
| 2.13 → 2.16 | AuthService / AuditService / ConsentService / AssignmentService | ✅ | Constructor injection sạch |
| 2.17 | `core/security.py` decode JWT + role helpers | ✅ | Validate sub/email/role nghiêm ngặt |
| 2.18 | `api/dependencies.py` DI wiring | ✅ | Repos + services + RBAC guards |
| 2.19 | `api/auth.py` (register/login/me) | ✅ | Local email/password OK |
| 2.20 | `api/consent.py` (accept/status) | ✅ | OK |
| 2.21 | `api/admin.py` (assignments + my-patients) | ✅ | OK |
| 2.22 | `main.py` wire routers + exception handler | ✅ | `prefix="/api/v1"` |
| 2.23 | `.env.example` mẫu cho Supabase/JWT/Google/URLs/consent | ✅ | OK |
| 2.25 | Manual smoke test register/login/me/consent (theo `[3]` §10) | ✅ | Đã verify trong runtime thực |

`make check` (ruff + mypy strict) hiện đang **PASS** trên 35 source file.

### 2.2 Chưa hoàn thành (cần đặc biệt lưu ý)

| # | Task | Trạng thái | Vấn đề |
|---|------|------------|--------|
| **2.24** | Automated tests (auth, RBAC, consent, audit) | ❌ | `backend/tests/` chỉ có `__init__.py`. Không có pytest case nào. MILESTONE2 §2.24 cung cấp full skeleton (`test_auth.py`, `test_consent.py`, `test_assignment.py`) nhưng **chưa được tạo file thực**. |
| **2.26** | Frontend Email/Password + Google OAuth UI | ❌ | `frontend/main.py` hiện tại CHỈ có demo "Check Backend Health". Chưa có form login/đăng ký/Google. **Có thêm syntax error** (xem §3.2 bên dưới). |
| **2.27** | Google OAuth setup (Google Cloud + Supabase Dashboard) | ⛔ | Không thể verify từ ngoài code. NHƯNG **toàn bộ phần Google OAuth ở backend cũng chưa được implement** — không có route `GET /auth/google`, không có `POST /auth/google/exchange`, không có method `AuthService.exchange_google_auth_code()`. Frontend snippet trong MILESTONE2 §2.26 đang reference các endpoint chưa tồn tại. |

> **Kết luận:** Milestone 2 là **complete cho local email/password authentication, RBAC, consent, doctor-assignment, audit** — đủ để mở khóa Milestone 3 (chat/session). Tuy nhiên, **chưa hoàn thành đầy đủ theo định nghĩa của plan** (Google OAuth + Frontend Auth UI + Tests). Có 2 bug runtime cần fix trước khi tin cậy production-readiness.

---

## 3. Code Quality Audit

Đánh giá theo 4 tiêu chí bạn yêu cầu.

### 3.1 Code cleanliness và readability — **Tốt**

- Type hint đầy đủ; `mypy --strict` pass trên toàn bộ backend.
- Docstring ngắn gọn, đúng phong cách Pydantic/FastAPI.
- Naming convention nhất quán (`_` prefix cho private, `Repo`/`Service`/`Response` suffix).
- Mỗi file có single responsibility rõ ràng (no mega-module).

**Hạn chế nhỏ:**
- Helper `_rows(data)` được copy-paste 4 lần vào `user_repo.py`, `consent_repo.py`, `audit_repo.py`, `assignment_repo.py` thay vì đẩy lên `BaseRepository`. → DRY violation.
- `auth_service._row_to_user_response` viết tay 4 helper parse JSONRow trong khi `UserResponse.model_validate(dict(row))` (đã dùng ở `UserRepository._to_model`) sẽ làm gọn. → Coupling không cần thiết với cấu trúc raw row.
- Một số string trong handler error trộn tiếng Anh/Việt; với code chuẩn hoá nên giữ tiếng Anh ở exception message để OpenAPI docs đồng bộ.

### 3.2 Bug runtime đã phát hiện

> Đây là 2 issue khá nghiêm trọng, nên flag riêng — không phải thuộc phạm vi refactor docs nhưng cần bạn biết.

**B1. `assignment_repo` dùng cột `assigned_at` không tồn tại trong schema**
- File: `backend/app/db/repositories/assignment_repo.py:81` và `:100`.
- Schema thực tế (`docs/schema.sql:134`): `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`.
- Hậu quả: `GET /api/v1/doctor/my-patients` và bất kỳ call nào tới `list_doctors_for_patient` sẽ **lỗi runtime** từ PostgREST (`column doctor_assignments.assigned_at does not exist`).
- Mypy không bắt được vì column name là string runtime.
- Note `[3]` §5.6 đã đề cập điều này nhưng code chưa được sửa.

**B2. `frontend/main.py` lỗi syntax**
- Line 5: `page_icon="🧠,` — thiếu dấu nháy đóng → file không parse được.
- Hậu quả: `make dev-fe` sẽ crash ngay khi load.

### 3.3 Appropriate use of design patterns — **Tốt, đúng hướng AGENT.md §5**

| Pattern | Áp dụng ở | Đánh giá |
|---------|-----------|----------|
| **Repository** | `db/repositories/base.py` Generic `BaseRepository[ModelT]` + abstract `_to_model` | ✅ chuẩn |
| **Service** | 4 service nhận repo qua constructor injection | ✅ chuẩn |
| **Singleton** | `SupabaseClientManager` cache `Client` | ✅ chuẩn |
| **Dependency Injection** | `api/dependencies.py` với FastAPI `Depends` | ✅ chuẩn |
| **Strategy** | (Sẽ cần cho LLMProvider — Milestone 4) | ⏳ chưa scope |
| **Factory** | (Sẽ cần cho LangGraph `build_agent_graph` — Milestone 4) | ⏳ chưa scope |

**Hạn chế nhỏ:**
- `dependencies.require_current_doctor_or_admin` viết tay logic + import `ForbiddenError` *bên trong hàm* thay vì gọi lại `require_roles({DOCTOR, ADMIN})` đã có ở `core/security.py`. Vi phạm "imports at top" và DRY.

### 3.4 Loose coupling và modularity — **Tốt**

Layer dependency flow đúng theo AGENT.md §4.1:
```
api ──▶ services ──▶ repositories ──▶ supabase_client
                 ╲▶ exceptions / constants / schemas
```
- API không query Supabase trực tiếp.
- Service không import từ `api/`.
- Repository không import từ `services/` hay `api/`.
- Không có circular import.

**Hạn chế nhỏ:**
- `AuthService._get_required_string/_bool/_datetime` raise `UnauthorizedError` cho lỗi thiếu cột DB — đây là `DatabaseError` về bản chất. Coupling sai về domain.
- `auth_service` import trực tiếp `passlib.context.CryptContext` ở module-level. Để testable hơn, có thể wrap qua `PasswordHasher` interface (giống `LLMProvider` Strategy ở Milestone 4). MVP hiện tại OK.
- `audit_service.log_event` chưa nhận `role` mặc dù schema `audit_logs.role` có sẵn. Khi sang Milestone 3+ (clinical access), sẽ cần audit theo role để filter dashboard.

### 3.5 Scalability và maintainability — **Tốt cho MVP, có debt cần dọn**

**Điểm mạnh:**
- Schema có index hợp lý (partial index trên `is_active=TRUE`, composite index `(user_id, accepted_at DESC)`).
- JSONB cho metadata/flexible field, normal column cho authorization data — đúng strategy.
- `audit_logs` append-only, có index `created_at DESC`.
- Generic `BaseRepository[ModelT]` → mở rộng table mới chỉ cần `_to_model`.
- DI qua `Depends` → mock hoá dễ trong test sau này.

**Debt cần xử lý trước khi sang Milestone 3:**
1. Hoàn thiện task 2.24 (automated tests) — giờ đang chỉ có manual smoke test.
2. Fix B1 (`assigned_at` → `created_at`) ở `assignment_repo`.
3. Fix B2 (`frontend/main.py` syntax) hoặc rewrite theo §2.26.
4. Hoàn thiện Google OAuth backend (`/auth/google`, `/auth/google/exchange`) hoặc khai báo rõ là "deferred to later milestone".

---

## 4. Đề xuất chi tiết: Refactor `docs/_notes/[3]database_auth_implementation_process.md`

### 4.1 Nguyên tắc bất di bất dịch (theo yêu cầu của bạn)

- **Giữ nguyên ngôn ngữ:** Tiếng Việt, đúng cách bạn viết.
- **Giữ nguyên phong cách:** terse, narrative, có "Mục đích / Vì sao / Lỗi đã gặp / Flow / Bài học".
- **Giữ nguyên purpose:** đây là tài liệu *process* để đọc lại sau, không phải tài liệu API hay tutorial.
- **Không thêm content kỹ thuật mới** ngoài những gì bạn đã nêu trong file gốc. Tôi chỉ:
  - Sửa formatting (Markdown lỗi/thiếu).
  - Tách lại heading levels theo chuẩn `#`/`##`/`###`.
  - Đóng khung code/SQL/shell/flow trong fenced code block đúng ngôn ngữ.
  - Bổ sung table tóm tắt (file → mục đích, lỗi → cách fix) **chỉ khi nội dung đã có sẵn** trong văn bản gốc.
  - Bổ sung Table of Contents.
  - Detail-hóa các đoạn paragraph dày đặc bằng bullet list — **giữ nguyên câu chữ gốc**, chỉ tách dòng.

### 4.2 Vấn đề Markdown của bản hiện tại

Sau khi đọc full 2037 dòng, tôi thấy các vấn đề chính:

1. **Heading không nhất quán:** `# PHẦN 1: ...` có `#`, nhưng `PHẦN 2: ...` (line 120), `PHẦN 3: ...` (line 251), `PHẦN 4` … `PHẦN 18` đều **không có `#`** → render thành plain text.
2. **Sub-heading dạng `1.1`, `1.2`, `4.3`, `5.4` …** không được render đậm; viết flat trong văn bản.
3. **Code/SQL/Shell/Flow không được fenced:**
   - SQL grants ở §3.5 trộn với prose
   - Flow ASCII (`POST /api/v1/auth/register ↓ ...`) không có ``` nên Markdown ăn mất khoảng trắng.
   - Bash command ở §10.4 và §11.6 không có \`\`\`bash.
   - Python schema/JSON examples không có \`\`\`python / \`\`\`json.
4. **Bullet list vỡ:** ví dụ §1.2 (line 51-66) — các điểm "user là ai", "user thuộc role nào", "patient đã consent chưa" lẽ ra là `-` bullet nhưng đang là paragraph rỗng dòng.
5. **Inline code không backtick:** tên file (`backend/app/main.py`), tên hàm (`AuthService.register()`), tên cột DB (`auth_user_id`) không được \` … \`.
6. **Bảng có thể chèn:** một số đoạn dài liệt kê file → mục đích, lỗi → fix, đang ở dạng đoạn văn — nên thành bảng để dễ tra cứu.
7. **Section numbering trộn ASCII và Markdown:** dùng `1.`, `1.1`, `(1)` không nhất quán.
8. **Trống section divider:** không có `---` giữa các PHẦN, làm văn bản dày liền tù tì.

### 4.3 Cấu trúc Markdown đề xuất (skeleton — không thêm content mới)

```
# Milestone 2 — Database & Auth Implementation Process

> Project: Mental Health Sovereign Agentic AI Platform
> Giai đoạn: Milestone 2 — Data & Auth Foundation
> Mục đích: ... (giữ nguyên đoạn mở đầu)

## Mục lục
- [Phần 1. Bối cảnh và mục tiêu](#phần-1-bối-cảnh-và-mục-tiêu)
- [Phần 2. Kiến trúc tổng thể sau Milestone 2](#phần-2-kiến-trúc-tổng-thể-sau-milestone-2)
- [Phần 3. Database modeling và schema](#phần-3-database-modeling-và-schema)
- [Phần 4. Core: config, constants, exceptions, security](#phần-4-core)
- [Phần 5. Supabase client và Repository layer](#phần-5-supabase-client-và-repository-layer)
- [Phần 6. Pydantic schemas — API contracts](#phần-6-pydantic-schemas)
- [Phần 7. Service layer — Business logic](#phần-7-service-layer)
- [Phần 8. API dependency injection và routers](#phần-8-api-dependency-injection-và-routers)
- [Phần 9. Supabase setup và runtime integration](#phần-9-supabase-setup)
- [Phần 10. Smoke test end-to-end](#phần-10-smoke-test-end-to-end)
- [Phần 11. Các lỗi đã gặp và bài học](#phần-11-các-lỗi-đã-gặp-và-bài-học)
- [Phần 12. Architecture flow theo từng workflow](#phần-12-architecture-flow)
- [Phần 13. Files implemented trong Milestone 2](#phần-13-files-implemented)
- [Phần 14. Current status sau DB-2.24](#phần-14-current-status)
- [Phần 15. Commit strategy và safety rules](#phần-15-commit-strategy)
- [Phần 16. Bài học kiến trúc](#phần-16-bài-học-kiến-trúc)
- [Phần 17. Checklist trước khi tiếp tục](#phần-17-checklist)
- [Phần 18. Next implementation direction](#phần-18-next-implementation-direction)

---

## Phần 1. Bối cảnh và mục tiêu

### 1.1 Milestone này đang giải quyết vấn đề gì?
... (giữ nguyên content)

### 1.2 Tại sao chưa làm LangGraph/RAG ở giai đoạn này?
... (giữ nguyên)

### 1.3 Nguyên tắc thiết kế áp dụng trong milestone này
... (giữ nguyên — chỉ tách bullet đúng định dạng)

---

## Phần 2. Kiến trúc tổng thể sau Milestone 2

### 2.1 Layer architecture
\`\`\`text
FastAPI route
    ↓
api/dependencies.py
    ↓
Service layer
    ↓
Repository layer
    ↓
Supabase client
    ↓
Supabase / PostgreSQL
\`\`\`
... (giữ nguyên)

### 2.2 Các folder liên quan trong milestone này
| Folder | File | Vai trò |
|--------|------|---------|
| `backend/app/core/` | `config.py` | settings/env |
| `backend/app/core/` | `constants.py` | enums |
| ... | ... | ... |

(Giữ nguyên các điểm bạn đã liệt kê — chỉ chuyển từ paragraph sang bảng)

---

## Phần 3. Database modeling và schema

### 3.1 Mục tiêu của database model
### 3.2 Vì sao cần `users` riêng thay vì chỉ dùng Supabase Auth?
### 3.3 Vì sao dùng `auth_user_id` nullable?
### 3.4 Vì sao dùng `JSONB` cho một số field?
### 3.5 File `docs/schema.sql`
\`\`\`sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;
\`\`\`
\`\`\`sql
GRANT USAGE ON SCHEMA public TO service_role;

GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA public
TO service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLES TO service_role;
\`\`\`
(Tách nguyên đoạn SQL hiện đang trộn với prose ra fenced block)

---

## Phần 4. Core: config, constants, exceptions, security

### 4.1 `backend/app/core/config.py`
**Mục đích:** ...
**Vì sao cần file này?** ...
**Vấn đề runtime đã gặp:** ...
**Quyết định fix:** ...
**Flow sử dụng:**
\`\`\`text
config.py
    ↓
supabase_client.py reads settings.supabase_url/settings.supabase_key
    ↓
auth_service.py reads JWT settings
    ↓
consent_service.py reads current policy version
\`\`\`

### 4.2 ... (giữ pattern Mục đích / Vì sao / Lỗi / Flow cho tất cả phần)

```

(Skeleton tương tự cho Phần 5 → Phần 18.)

### 4.4 Các phép biến đổi cụ thể tôi sẽ làm

| Loại transform | Ví dụ chỗ áp dụng | Thay đổi nội dung? |
|-----------------|-------------------|--------------------|
| Sửa heading level | `PHẦN 2:` (line 120) → `## Phần 2.` | KHÔNG |
| Wrap fenced code (`text`/`sql`/`bash`/`python`/`json`) | Mọi flow ASCII, mọi SQL grants, mọi `curl`/`uv add`/`TOKEN=...` | KHÔNG |
| Inline code backtick | `users`, `auth_user_id`, `AuthService.register()`, `make dev-be` | KHÔNG |
| Tách paragraph thành bullet | §1.2, §1.3, §3.3, §6.2 v.v. | KHÔNG (giữ y câu) |
| Bảng tóm tắt | §13 (file → mục đích), §11 (lỗi → fix), §14 (task → status) | KHÔNG (chỉ chuyển hình thức) |
| Section divider `---` | Giữa mỗi `## Phần` | KHÔNG |
| Mục lục clickable | Đầu file | KHÔNG (chỉ navigation) |
| Sửa lỗi chính tả/typo nhỏ rõ ràng | "ban đầu BaseSettings đọc:\n\n.env" → wrap thành code | KHÔNG (chỉ formatting) |
| Đồng nhất ngôn ngữ Vietnamese | Giữ y nguyên | KHÔNG |

### 4.5 Việc tôi sẽ KHÔNG làm

- ❌ Không thêm bất kỳ kết luận, bài học, opinion mới nào của tôi.
- ❌ Không sửa nội dung kỹ thuật (ví dụ không "fix" ghi chú "60 phút" thành "60 phút (configurable)").
- ❌ Không dịch tiếng Anh.
- ❌ Không xóa section nào — kể cả Phần 18 (Next direction).
- ❌ Không gộp/tách lại flow của bạn.
- ❌ Không touch file code nào (audit chỉ là báo cáo).

### 4.6 Diff dự kiến

- File duy nhất bị sửa: `docs/_notes/[3]database_auth_implementation_process.md`.
- Số dòng dự kiến tăng: ~+400 → +600 (do thêm fenced block, table, ToC, divider). Word count thay đổi: ~+5% (chỉ thêm anchor + table header + bullet markers).
- Không tạo file mới.
- Không sửa file code.

---

## 5. Câu hỏi xin xác nhận

1. **Bạn có đồng ý refactor file `docs/_notes/[3]database_auth_implementation_process.md`** theo skeleton ở §4.3 và transform ở §4.4 không?
2. **Có muốn tôi mở thêm một PR riêng** để fix 2 bug nghiêm trọng (B1 `assigned_at` ở `assignment_repo`, B2 syntax error `frontend/main.py`) không? (Đây không thuộc scope task hiện tại, sẽ không làm trừ khi bạn yêu cầu.)
3. **Có muốn tôi audit thêm** phần Google OAuth backend (file/route/service cần thêm để hoàn thành 2.27) thành một file `MILESTONE2_GAP_REPORT.md` riêng không?

> Tôi sẽ chờ phản hồi rõ ràng trước khi đụng vào file `[3]`.
