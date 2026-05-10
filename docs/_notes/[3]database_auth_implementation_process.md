# Milestone 2 — Database & Auth Implementation Process

> **Project:** Mental Health Sovereign Agentic AI Platform
> **Giai đoạn:** Milestone 2 — Data & Auth Foundation
> **Mục đích tài liệu:** Ghi lại toàn bộ quá trình implement phần database/auth foundation đã làm trong project, theo dạng process document để sau này đọc lại có thể hiểu rõ:
>
> - đã làm những bước nào;
> - vì sao làm theo thứ tự đó;
> - mỗi file được tạo ra để làm gì;
> - các lớp architecture liên kết với nhau như thế nào;
> - flow hoạt động thực tế khi register/login/consent/assignment;
> - các lỗi đã gặp khi tích hợp Supabase thật và cách xử lý;
> - các decision quan trọng đã chốt trong quá trình implement.

---

## Mục lục

- [Phần 1. Bối cảnh và mục tiêu của giai đoạn database implementation](#phần-1-bối-cảnh-và-mục-tiêu-của-giai-đoạn-database-implementation)
- [Phần 2. Kiến trúc tổng thể sau khi implement Milestone 2](#phần-2-kiến-trúc-tổng-thể-sau-khi-implement-milestone-2)
- [Phần 3. Database modeling và schema implementation](#phần-3-database-modeling-và-schema-implementation)
- [Phần 4. Core: config, constants, exceptions, security](#phần-4-core-config-constants-exceptions-security)
- [Phần 5. Supabase client và repository layer](#phần-5-supabase-client-và-repository-layer)
- [Phần 6. Pydantic schemas — API contracts](#phần-6-pydantic-schemas--api-contracts)
- [Phần 7. Service layer — business logic](#phần-7-service-layer--business-logic)
- [Phần 8. API dependency injection và routers](#phần-8-api-dependency-injection-và-routers)
- [Phần 9. Supabase setup và runtime integration](#phần-9-supabase-setup-và-runtime-integration)
- [Phần 10. Smoke test end-to-end](#phần-10-smoke-test-end-to-end)
- [Phần 11. Các lỗi đã gặp và bài học](#phần-11-các-lỗi-đã-gặp-và-bài-học)
- [Phần 12. Architecture flow theo từng workflow](#phần-12-architecture-flow-theo-từng-workflow)
- [Phần 13. Files implemented trong Milestone 2 và mục đích](#phần-13-files-implemented-trong-milestone-2-và-mục-đích)
- [Phần 14. Current status sau DB-2.24](#phần-14-current-status-sau-db-224)
- [Phần 15. Commit strategy và safety rules](#phần-15-commit-strategy-và-safety-rules)
- [Phần 16. Bài học kiến trúc sau giai đoạn này](#phần-16-bài-học-kiến-trúc-sau-giai-đoạn-này)
- [Phần 17. Checklist đọc lại trước khi tiếp tục](#phần-17-checklist-đọc-lại-trước-khi-tiếp-tục)
- [Phần 18. Next implementation direction](#phần-18-next-implementation-direction)
- [Phần 19. Code-quality refactor và automated tests phase 1 (PR #9 + PR #10)](#phần-19-code-quality-refactor-và-automated-tests-phase-1-pr-9--pr-10)
- [Phần 20. Đóng Milestone 2 — tests phase 2, frontend UI, Google OAuth, Sessions CRUD (PRs #12–#18)](#phần-20-đóng-milestone-2--tests-phase-2-frontend-ui-google-oauth-sessions-crud-prs-12-18)

---

## Phần 1. Bối cảnh và mục tiêu của giai đoạn database implementation

### 1.1 Milestone này đang giải quyết vấn đề gì?

Project là một nền tảng AI hỗ trợ sức khỏe tinh thần, có hai nhóm user chính:

1. **Patient**
   - dùng AI companion để trò chuyện;
   - nhận hỗ trợ cảm xúc, coping exercises, journaling, grounding;
   - không được AI trả về diagnosis trực tiếp.

2. **Doctor / Counselor**
   - xem danh sách patient được assign;
   - review clinical profile do AI tạo;
   - xem risk/stress score và evidence snippets;
   - dùng doctor-facing decision support về sau.

Vì vậy, trước khi làm chat agent, LangGraph, RAG hoặc clinical profile, hệ thống cần một nền móng dữ liệu và phân quyền thật chắc.

Milestone 2 tập trung vào phần này:

```text
Database schema
→ Supabase client
→ Repository layer
→ Service layer
→ Security/JWT/RBAC
→ API routes
→ Supabase cloud setup
→ Smoke test end-to-end
```

Nói ngắn gọn:

> Milestone 2 là phần dựng "xương sống identity + database + authorization" cho toàn bộ platform.

### 1.2 Tại sao chưa làm LangGraph/RAG ở giai đoạn này?

LangGraph agent và RAG cần dựa trên các dữ liệu sau:

- user là ai;
- user thuộc role nào;
- patient đã consent chưa;
- doctor có được assign cho patient đó không;
- message/session lưu ở đâu;
- clinical profile sẽ gắn với patient/session nào;
- audit log ghi event như thế nào.

Nếu chưa có database/auth foundation, agent dù chạy được cũng sẽ không có ranh giới an toàn về privacy, role và audit.

Vì vậy thứ tự đúng là:

1. **Milestone 1:** Project foundation
2. **Milestone 2:** Data/Auth foundation
3. **Milestone 3+:** Chat/session/agent/RAG

### 1.3 Nguyên tắc thiết kế áp dụng trong milestone này

Các nguyên tắc xuyên suốt:

- **Backend-enforced authorization**
  - frontend không được tự quyết định quyền;
  - FastAPI backend phải kiểm tra JWT, role và assignment.

- **Doctor assignment enforcement**
  - doctor chỉ được xem patient được assign;
  - logic này nằm ở backend service, không nằm ở Streamlit.

- **Consent-first**
  - user phải accept policy version hiện tại;
  - consent được lưu lại bằng database record.

- **Audit-ready**
  - các action nhạy cảm phải có audit log;
  - audit log là application audit, không thay thế bởi Langfuse.

- **Strict typing**
  - code phải pass mypy strict;
  - không dùng `Any` nếu có thể tránh;
  - raw Supabase rows được type bằng JSON aliases.

- **Repository-Service-API layering**
  - API route không query Supabase trực tiếp;
  - repository chỉ làm data access;
  - service chứa business rules;
  - dependency layer wire các object lại với nhau.

---

## Phần 2. Kiến trúc tổng thể sau khi implement Milestone 2

### 2.1 Layer architecture

Sau khi implement, backend có kiến trúc theo lớp:

```text
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
```

**Ví dụ flow register:**

```text
POST /api/v1/auth/register
    ↓
backend/app/api/auth.py
    ↓
AuthService.register()
    ↓
UserRepository.email_exists()
UserRepository.create()
    ↓
BaseRepository / Supabase client
    ↓
public.users table
```

**Ví dụ flow consent:**

```text
POST /api/v1/consent/accept
    ↓
backend/app/api/consent.py
    ↓
get_current_user() decode JWT
    ↓
ConsentService.accept_consent()
    ↓
ConsentRepository.create()
AuditService.log_event()
    ↓
consent_records table
audit_logs table
```

**Ví dụ flow doctor assignment:**

```text
POST /api/v1/admin/assignments
    ↓
require_current_admin()
    ↓
AssignmentService.create_assignment()
    ↓
UserRepository.get_by_id(doctor_id)
UserRepository.get_by_id(patient_id)
AssignmentRepository.get_active_assignment()
AssignmentRepository.create()
AuditService.log_event()
    ↓
doctor_assignments table
audit_logs table
```

### 2.2 Các folder liên quan trong milestone này

| Folder | File | Vai trò |
|--------|------|---------|
| `backend/app/core/` | `config.py` | settings/env |
| `backend/app/core/` | `constants.py` | enums |
| `backend/app/core/` | `exceptions.py` | exception hierarchy |
| `backend/app/core/` | `security.py` | JWT decode + role helpers |
| `backend/app/db/` | `supabase_client.py` | Supabase connection |
| `backend/app/db/repositories/` | `base.py` | base repository |
| `backend/app/db/repositories/` | `user_repo.py` | data access cho users |
| `backend/app/db/repositories/` | `consent_repo.py` | data access cho consent |
| `backend/app/db/repositories/` | `audit_repo.py` | data access cho audit logs |
| `backend/app/db/repositories/` | `assignment_repo.py` | data access cho doctor assignment |
| `backend/app/schemas/` | `user.py` | auth/user request-response |
| `backend/app/schemas/` | `consent.py` | consent request-response |
| `backend/app/schemas/` | `audit.py` | audit log models |
| `backend/app/schemas/` | `assignment.py` | assignment models |
| `backend/app/schemas/` | `session.py` | future session/message models |
| `backend/app/services/` | `auth_service.py` | register/login/JWT |
| `backend/app/services/` | `audit_service.py` | centralized audit logging |
| `backend/app/services/` | `consent_service.py` | consent business logic |
| `backend/app/services/` | `assignment_service.py` | doctor-patient assignment |
| `backend/app/api/` | `dependencies.py` | FastAPI DI |
| `backend/app/api/` | `auth.py` | auth endpoints |
| `backend/app/api/` | `consent.py` | consent endpoints |
| `backend/app/api/` | `admin.py` | admin assignment endpoints |
| `backend/app/api/` | `health.py` | health check |
| `docs/` | `DATABASE_MODEL.md` | data modeling reference |
| `docs/` | `schema.sql` | reference SQL schema |

---

## Phần 3. Database modeling và schema implementation

### 3.1 Mục tiêu của database model

Application DB dùng Supabase/PostgreSQL để lưu dữ liệu nghiệp vụ chính:

- `users`
- `doctor_assignments`
- `consent_records`
- `chat_sessions`
- `chat_messages`
- `clinical_profiles`
- `stress_risk_scores`
- `audit_logs`

Trong milestone này, không phải bảng nào cũng đã có repository/API ngay. Một số bảng được model sẵn để chuẩn bị cho milestone sau.

Ví dụ:

- `chat_sessions`
- `chat_messages`
- `clinical_profiles`
- `stress_risk_scores`

đã nằm trong schema vì thuộc data model tổng thể, nhưng chưa implement repository/service trong Milestone 2 vì chat/clinical workflow thuộc milestone sau.

### 3.2 Vì sao cần `users` riêng thay vì chỉ dùng Supabase Auth?

Supabase có `auth.users`, nhưng project cần application-level user vì cần lưu:

- `role`: patient / doctor / admin;
- `provider`: local / google;
- active status;
- doctor-patient assignment;
- consent record;
- audit log reference;
- app JWT subject.

Do đó, bảng `public.users` là source chính cho application authorization.

**Cột quan trọng:**

```text
id
auth_user_id
email
password_hash
full_name
role
auth_provider
provider_user_id
avatar_url
is_active
created_at
updated_at
```

**Ý nghĩa:**

- `id`: application user id, dùng trong app JWT;
- `auth_user_id`: mapping Supabase Auth user nếu dùng OAuth;
- `password_hash`: chỉ có local user;
- `role`: quyết định quyền trong backend;
- `auth_provider`: local/google;
- `is_active`: soft deactivate.

### 3.3 Vì sao dùng `auth_user_id` nullable?

Cột này được thêm để chuẩn bị cho Google OAuth/Supabase Auth mapping.

- Local email/password user có thể chưa có Supabase Auth user, nên nullable.
- Google OAuth user về sau có thể map:

```sql
users.auth_user_id = auth.users.id
```

**Index khuyến nghị:**

```sql
CREATE UNIQUE INDEX IF NOT EXISTS unique_users_auth_user_id
ON users(auth_user_id)
WHERE auth_user_id IS NOT NULL;
```

### 3.4 Vì sao dùng `JSONB` cho một số field?

Các field AI/clinical còn thay đổi nhiều:

- clinical symptoms;
- risk markers;
- evidence snippets;
- risk score evidence;
- audit metadata;
- session metadata.

Do đó, dùng `JSONB` cho MVP giúp iterate nhanh.

Nhưng không dùng `JSONB` cho các quan hệ chính như user, role, assignment, session ID. Các field đó vẫn là cột rõ ràng để enforce FK, index và access rule.

**Nguyên tắc:**

```text
Structured authorization data → normal columns
Flexible AI/metadata data     → JSONB
```

### 3.5 File `docs/schema.sql`

**Vai trò:**

- là SQL reference schema cho application DB;
- dùng để apply vào Supabase project;
- chứa extensions, table definitions, constraints, indexes;
- sau smoke test đã bổ sung grant privileges cho `service_role`.

**Các extension cần có:**

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;
```

**Ý nghĩa:**

- `pgcrypto`: dùng `gen_random_uuid()`;
- `citext`: email case-insensitive.

Sau khi tích hợp Supabase thật, phát hiện backend dùng secret/service role key nhưng chưa có quyền trên table custom. Vì vậy thêm grant:

```sql
GRANT USAGE ON SCHEMA public TO service_role;

GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA public
TO service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLES TO service_role;
```

**Ý nghĩa:**

- cho backend service role query các bảng application;
- tránh lỗi `permission denied for table users`;
- đảm bảo bảng tạo mới sau này cũng có quyền cho service role.

---

## Phần 4. Core: config, constants, exceptions, security

### 4.1 `backend/app/core/config.py`

#### Mục đích

File này quản lý toàn bộ environment settings của backend.

**Các nhóm config:**

- App metadata
- External services
- Supabase
- JWT
- Google OAuth
- Backend/frontend URLs
- Consent policy version

#### Vì sao cần file này?

Nếu code đọc env trực tiếp ở nhiều nơi, project sẽ khó maintain.

Vì vậy ta gom toàn bộ vào:

```python
settings = Settings()
```

Các service/repository khác chỉ import `settings`.

#### Vấn đề runtime đã gặp

Ban đầu `BaseSettings` đọc:

```text
.env
```

theo current working directory. Nhưng `make dev-be` chạy:

```bash
cd backend && uv run uvicorn app.main:app --reload
```

nên backend tìm `.env` trong `backend/.env`, không phải root `.env`.

Điều này gây lỗi:

```text
Supabase URL and KEY must be set in environment variables
```

#### Quyết định fix

Sửa `config.py` để đọc root `.env` cố định bằng `Path`.

**Architecture decision:**

> 1 source of truth = root `.env`

Không copy `.env` vào `backend/` vì sẽ tạo duplicate config.

#### Flow sử dụng

```text
config.py
    ↓
supabase_client.py reads settings.supabase_url/settings.supabase_key
    ↓
auth_service.py reads JWT settings
    ↓
consent_service.py reads current policy version
```

### 4.2 `backend/app/core/constants.py`

#### Mục đích

Định nghĩa enum vocabulary dùng toàn hệ thống.

**Các nhóm enum:**

- `AuthProvider`
- `UserRole`
- `SessionStatus`
- `MessageRole`
- `SafetySeverity`
- `RiskSeverity`
- `AuditAction`

#### Vì sao cần file này?

Không để code rải rác string như:

```text
"patient"
"doctor"
"user_login"
"consent_accepted"
```

Nếu viết string tay nhiều nơi sẽ dễ typo.

Dùng enum giúp:

- code rõ hơn;
- mypy hỗ trợ tốt hơn;
- schema/API nhất quán;
- database value thống nhất.

#### File nào sử dụng?

- `schemas/user.py` dùng `UserRole`, `AuthProvider`;
- `auth_service.py` dùng `AuthProvider`, `UserRole`;
- `audit_repo.py` dùng `AuditAction`;
- `audit_service.py` dùng `AuditAction`;
- `consent_service.py` dùng `AuditAction.CONSENT_ACCEPTED`;
- `assignment_service.py` dùng `UserRole`, `AuditAction`.

### 4.3 `backend/app/core/exceptions.py`

#### Mục đích

Tạo exception hierarchy chung cho application.

**Các exception chính:**

- `AppException`
- `NotFoundError`
- `AlreadyExistsError`
- `UnauthorizedError`
- `ForbiddenError`
- `InvalidCredentialsError`
- `ConsentRequiredError`
- `DatabaseError`

#### Vì sao cần file này?

Service layer không nên throw trực tiếp `HTTPException`, vì service layer không nên biết quá nhiều về HTTP.

Thay vào đó:

```text
Service raises AppException subclass
FastAPI exception handler converts to JSON response
```

**Ví dụ:**

| Exception | HTTP status |
|-----------|-------------|
| `InvalidCredentialsError` | 401 |
| `ForbiddenError` | 403 |
| `AlreadyExistsError` | 409 |
| `DatabaseError` | 500 |

#### Lỗi đã gặp

Khi wire vào `main.py`, mypy báo:

```text
Argument 2 to add_exception_handler has incompatible type
```

**Nguyên nhân:**

```python
app_exception_handler(request: Request, exc: AppException)
```

trong khi FastAPI/Starlette muốn handler nhận:

```python
exc: Exception
```

#### Cách fix

Đổi handler signature:

```python
exc: Exception
```

và bên trong check:

```python
if isinstance(exc, AppException)
```

**Kết quả:**

- type-check pass;
- vẫn giữ JSON response format cho custom exceptions.

### 4.4 `backend/app/core/security.py`

#### Mục đích

Xử lý JWT decoding và role-based access helper.

**Nội dung chính:**

- `CurrentUserClaims`
- `decode_access_token`
- `require_roles`
- `require_admin`
- `require_doctor`
- `require_patient`

#### Vì sao cần file này?

`AuthService` tạo token, nhưng API cần decode token.

Tách `security.py` giúp:

- không trộn token decode vào route;
- role check dùng thống nhất;
- dependency layer có thể gọi lại;
- tests sau này dễ hơn.

#### Flow hoạt động

```text
Request with Authorization: Bearer <JWT>
    ↓
api/dependencies.py get_current_user()
    ↓
security.decode_access_token()
    ↓
CurrentUserClaims(user_id, email, role)
    ↓
route/service dùng current_user
```

#### Token chứa gì?

JWT payload:

```text
sub   = user id
email = email
role  = patient/doctor/admin
exp   = expiration timestamp
```

Trong config hiện tại token sống 60 phút:

```bash
JWT_EXPIRATION_MINUTES=60
```

---

## Phần 5. Supabase client và repository layer

### 5.1 `backend/app/db/supabase_client.py`

#### Mục đích

Tạo Supabase client dùng chung cho backend.

#### Vì sao cần file này?

Không muốn mỗi repository tự gọi:

```python
create_client(...)
```

Vì như vậy:

- config bị lặp;
- khó test;
- khó đổi Supabase client;
- dễ tạo nhiều client không cần thiết.

#### Cách hoạt động

```text
get_supabase_client()
    ↓
SupabaseClientManager.get_client()
    ↓
nếu chưa có client:
    đọc settings.supabase_url/settings.supabase_key
    create_client()
    cache lại
    return client
```

#### Lỗi đã gặp liên quan env

Khi settings chưa đọc được `.env`, file này raise:

```text
ValueError: Supabase URL and KEY must be set in environment variables
```

Sau khi fix `config.py`, Supabase client hoạt động đúng.

### 5.2 `backend/app/db/repositories/base.py`

#### Mục đích

Tạo `BaseRepository` dùng chung cho các bảng Supabase.

**Cung cấp CRUD chung:**

- `get_by_id`
- `create`
- `update`
- `delete`
- `_first_row`
- `_rows` *(lift từ 4 repo con vào base ở [PR #9](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/9) — xem Phần 19)*
- `_to_model`

#### Vì sao cần `BaseRepository`?

Các repository đều có pattern giống nhau:

- select by id
- insert row
- update row
- delete row
- convert row → Pydantic model
- catch DB error

Nếu viết lặp ở từng repo, code dài và dễ lệch style.

#### Vấn đề typing đã gặp

Supabase Python SDK có typing không dễ khớp với:

```python
dict[str, object]
```

Khi dùng mypy strict, `.insert()` / `.update()` có thể báo lỗi.

#### Cách fix

Tạo JSON type aliases:

```python
JSONValue
JSONRow
```

**Ý nghĩa:**

```python
JSONValue = str | int | float | bool | None | list[JSONValue] | dict[str, JSONValue]
JSONRow   = dict[str, JSONValue]
```

**Lợi ích:**

- tránh dùng `Any`;
- thể hiện đúng dữ liệu Supabase trả về;
- giúp repository strict typing ổn định.

### 5.3 `backend/app/db/repositories/user_repo.py`

#### Mục đích

Repository cho bảng `users`.

**Method quan trọng:**

- `get_by_email`
- `email_exists`
- `get_by_auth_user_id`
- `get_by_provider_identity`
- `list_by_role`
- `deactivate`

#### Vì sao `get_by_email` trả raw row?

Login cần đọc:

```text
password_hash
```

Nhưng `UserResponse` không được expose `password_hash`.

Vì vậy:

- `get_by_email()` trả `JSONRow | None`;
- `AuthService.login()` đọc `password_hash` từ raw row;
- response ra client vẫn dùng `UserResponse`.

#### Flow sử dụng

**Register:**

```text
AuthService.register()
    ↓
UserRepository.email_exists()
    ↓
UserRepository.create()
```

**Login:**

```text
AuthService.login()
    ↓
UserRepository.get_by_email()
    ↓
verify password hash
```

**Admin/assignment:**

```text
AssignmentService.create_assignment()
    ↓
UserRepository.get_by_id(doctor_id)
UserRepository.get_by_id(patient_id)
```

### 5.4 `backend/app/db/repositories/consent_repo.py`

#### Mục đích

Repository cho bảng `consent_records`.

**Method quan trọng:**

- `get_latest_by_user`
- `has_accepted_version`
- `list_by_user`

#### Vì sao cần riêng repository này?

Consent logic có query đặc thù:

- lấy consent mới nhất;
- kiểm tra user đã accept policy version hiện tại chưa;
- list lịch sử consent.

Không nên để các query này nằm trong service hoặc route.

#### Flow sử dụng

```text
ConsentService.get_status()
    ↓
ConsentRepository.has_accepted_version()
ConsentRepository.get_latest_by_user()
```

### 5.5 `backend/app/db/repositories/audit_repo.py`

#### Mục đích

Repository cho bảng `audit_logs`.

**Method quan trọng:**

- `list_by_user`
- `list_by_action`
- `list_by_resource`

#### Vì sao cần audit repository?

Audit log là dữ liệu nhạy cảm và cần query theo nhiều góc:

- user nào thực hiện action;
- action loại gì;
- resource nào bị tác động.

Repository giúp các query này tập trung một nơi.

#### Flow sử dụng

```text
AuditService.log_event()
    ↓
AuditRepository.create()
```

Query review sau này:

```text
AuditRepository.list_by_user()
AuditRepository.list_by_action()
AuditRepository.list_by_resource()
```

### 5.6 `backend/app/db/repositories/assignment_repo.py`

#### Mục đích

Repository cho bảng `doctor_assignments`.

**Method quan trọng:**

- `get_active_assignment`
- `is_assigned`
- `list_patients_for_doctor`
- `list_doctors_for_patient`
- `deactivate`

#### Vì sao file này rất quan trọng?

Doctor assignment là security boundary chính của doctor-facing workflow.

> Doctor không được xem patient chỉ vì có role doctor. Doctor phải có active assignment.

#### Flow sử dụng

```text
AssignmentService.ensure_doctor_can_access_patient()
    ↓
AssignmentRepository.is_assigned()
```

**Doctor dashboard:**

```text
GET /doctor/my-patients
    ↓
AssignmentService.list_patients_for_doctor()
    ↓
AssignmentRepository.list_patients_for_doctor()
```

**Future clinical access:**

```text
Doctor requests patient clinical profile
    ↓
AssignmentService.ensure_doctor_can_access_patient()
    ↓
only then return doctor-facing data
```

#### Note về field thời gian

Schema hiện tại `AssignmentResponse` dùng:

```text
created_at
```

Do đó các repository query order nên dùng:

```text
created_at
```

Không nên dùng `assigned_at` nếu bảng không có field này.

---

## Phần 6. Pydantic schemas — API contracts

### 6.1 Vì sao cần schemas?

Schemas là ranh giới giữa:

```text
external API request/response
và
internal database/service logic
```

**Lợi ích:**

- validate input;
- chuẩn hóa output;
- không expose sensitive fields;
- OpenAPI docs rõ ràng;
- mypy type-check tốt hơn.

### 6.2 `backend/app/schemas/user.py`

#### Mục đích

Định nghĩa request/response cho user/auth.

**Classes:**

- `UserCreate`
- `UserLogin`
- `GoogleExchangeRequest`
- `UserResponse`
- `TokenResponse`

#### Điểm quan trọng

`UserResponse` không có:

```text
password_hash
```

Đây là intentional.

`TokenResponse` gồm:

```text
access_token
token_type
user
```

**Lỗi đã gặp:**

> `AuthService.login()` ban đầu chỉ trả token, thiếu `user`, dẫn tới mypy lỗi. Sau đó service được sửa để trả đủ `TokenResponse`.

### 6.3 `backend/app/schemas/consent.py`

#### Mục đích

Định nghĩa contract cho consent.

**Classes:**

- `ConsentAcceptRequest`
- `ConsentResponse`
- `ConsentStatusResponse`

#### Điểm quan trọng

`ConsentAcceptRequest` chỉ có:

```text
policy_version
```

không có `accepted`.

**Ý nghĩa:**

> Client gọi `/consent/accept` nghĩa là `accepted = true`

Do đó `ConsentService` tự set:

```python
accepted=True
```

**Lỗi đã gặp:**

> Service ban đầu giả định `payload.accepted`, nhưng schema không có field này. Sau đó service được sửa để dùng `payload.policy_version`.

`ConsentStatusResponse` có:

```text
has_valid_consent
current_policy_version
latest_accepted_policy_version
```

không có `accepted` hoặc `latest_consent`.

### 6.4 `backend/app/schemas/audit.py`

#### Mục đích

Định nghĩa audit log request/response.

**Dùng cho:**

- `AuditRepository`;
- `AuditService`;
- future admin audit views.

#### Audit response chứa các thông tin như:

```text
id
user_id
action
resource_type
resource_id
metadata
ip_address
created_at
```

#### Nguyên tắc metadata

Audit metadata không nên chứa raw sensitive content nếu không cần.

**Ví dụ nên ghi:**

```text
policy_version
doctor_id
patient_id
method
```

Không nên ghi toàn bộ raw chat message vào audit metadata.

### 6.5 `backend/app/schemas/assignment.py`

#### Mục đích

Định nghĩa contract cho doctor-patient assignment.

**Classes:**

- `AssignmentCreateRequest`
- `AssignmentResponse`

**Field chính:**

```text
doctor_id
patient_id
assigned_by
is_active
created_at
```

Service đã được kiểm tra khớp với schema này.

### 6.6 `backend/app/schemas/session.py`

#### Vì sao có schema session nhưng chưa có repository?

File này chuẩn bị cho milestone sau.

Milestone 2 chưa implement:

- `SessionRepository`
- `MessageRepository`
- `ChatService`

vì chat workflow thuộc milestone tiếp theo.

**Quyết định:**

> Schema có thể tồn tại trước để chuẩn hóa response model tương lai.
> Repository chỉ tạo khi có use-case trong milestone hiện tại.

---

## Phần 7. Service layer — business logic

### 7.1 Vì sao cần service layer?

Repository chỉ biết đọc/ghi DB. API route chỉ nhận request/trả response.

> Business rules phải nằm ở service.

**Ví dụ:**

- email đã tồn tại chưa;
- password hash/verify;
- user active không;
- `doctor_id` có thật sự là doctor không;
- `patient_id` có thật sự là patient không;
- consent policy hiện tại là gì;
- ghi audit log sau action.

Nếu không có service layer, logic sẽ rải rác trong route, khó test và dễ leak authorization.

### 7.2 `backend/app/services/auth_service.py`

#### Mục đích

Xử lý local authentication:

- register
- login
- hash password
- verify password
- create JWT
- convert raw user row → `UserResponse`

#### Register flow

```text
UserCreate payload
    ↓
email_exists(payload.email)
    ↓
hash_password(payload.password)
    ↓
create users row
    ↓
return UserResponse
```

#### Login flow

```text
UserLogin payload
    ↓
get_by_email(email)
    ↓
read password_hash from raw JSONRow
    ↓
verify_password()
    ↓
check is_active
    ↓
row_to_user_response()
    ↓
create_access_token()
    ↓
return TokenResponse(access_token, token_type, user)
```

#### JWT flow

Token payload chứa:

```text
sub   = user.id
email = user.email
role  = user.role
exp   = expiration timestamp
```

#### Refactor (PR #9)

4 helper viết tay `_get_required_string/_bool/_datetime` đã bị thay bằng:

```python
UserResponse.model_validate(dict(row))
```

**Lý do:**

- `UserRepository._to_model` đã làm đúng pattern này → service nên reuse;
- giảm coupling với raw row shape;
- malformed row (thiếu cột) sẽ raise `DatabaseError` (500), không leak `ValidationError`.

Login cũng được sửa để đọc `password_hash` / `is_active` qua dict access + raise `DatabaseError` nếu cột thiếu (vì đó là vấn đề schema, không phải vấn đề auth). Chi tiết ở Phần 19.

#### Lỗi đã gặp

**Lỗi 1: Exception constructor mismatch**

`AlreadyExistsError` cần:

```text
resource
identifier
```

`InvalidCredentialsError` không nhận message.

> Service được sửa để dùng đúng constructor.

**Lỗi 2: `TokenResponse` thiếu `user`**

Schema yêu cầu:

```python
user: UserResponse
```

> Service được sửa để convert raw row sang `UserResponse`.

**Lỗi 3: bcrypt/passlib runtime**

Khi register, passlib báo lỗi liên quan bcrypt version:

```text
module 'bcrypt' has no attribute '__about__'
ValueError: password cannot be longer than 72 bytes
```

Dù password không dài, lỗi đến từ incompatibility giữa passlib và bcrypt version mới.

**Fix:**

```bash
uv add --package backend "bcrypt==4.3.0"
```

hoặc pin `<5`.

**Mục tiêu:**

> stable password hashing

### 7.3 `backend/app/services/audit_service.py`

#### Mục đích

Tạo một nơi duy nhất để ghi audit log.

**Method chính:**

- `log_event()` *(thêm param `role: str | None = None` ở [PR #9](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/9) để khớp cột `audit_logs.role` — xem Phần 19)*

#### Vì sao không ghi audit trực tiếp từ từng service?

Nếu từng service tự gọi repository với payload riêng:

- format audit dễ lệch;
- metadata không được sanitize;
- khó thêm policy sau này;
- khó test.

Do đó mọi sensitive action nên gọi:

```python
AuditService.log_event()
```

#### Metadata sanitization

Service sanitize metadata để đảm bảo JSON-safe.

**Nguyên tắc:**

- scalar values giữ nguyên;
- object phức tạp convert string;
- không nên đưa raw sensitive text nếu không cần.

#### Flow sử dụng

**Consent:**

```text
ConsentService.accept_consent()
    ↓
AuditService.log_event(action=CONSENT_ACCEPTED)
```

**Assignment:**

```text
AssignmentService.create_assignment()
    ↓
AuditService.log_event(action=DOCTOR_ASSIGNMENT_CREATED)
```

### 7.4 `backend/app/services/consent_service.py`

#### Mục đích

Xử lý consent business logic.

**Method:**

- `accept_consent` *(thêm param `role: str` ở [PR #9](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/9) để propagate xuống `AuditService.log_event` — xem Phần 19)*
- `get_status`

#### Accept flow

```text
current user id
ConsentAcceptRequest(policy_version)
    ↓
create consent_records row with accepted=True
    ↓
log audit event consent_accepted
    ↓
return ConsentResponse
```

#### Status flow

```text
current policy version from settings
    ↓
ConsentRepository.has_accepted_version(user_id, version)
    ↓
ConsentRepository.get_latest_by_user(user_id)
    ↓
ConsentStatusResponse
```

#### Lỗi đã gặp

Schema thật không có `accepted` trong request.

**Fix:**

```text
Client gửi policy_version
Service tự set accepted=True
```

Schema thật trả:

```text
has_valid_consent
current_policy_version
latest_accepted_policy_version
```

> Service được sửa theo đúng schema.

### 7.5 `backend/app/services/assignment_service.py`

#### Mục đích

Xử lý doctor-patient assignment business logic.

**Method:**

- `create_assignment` *(thêm param `assigned_by_role: str` ở [PR #9](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/9))*
- `deactivate_assignment` *(thêm param `deactivated_by_role: str` ở PR #9)*
- `ensure_doctor_can_access_patient`
- `list_patients_for_doctor`
- `list_doctors_for_patient`

> Cả 2 method create/deactivate đều propagate role xuống `AuditService.log_event`. Xem Phần 19.

#### Create assignment flow

```text
AssignmentCreateRequest(doctor_id, patient_id)
    ↓
UserRepository.get_by_id(doctor_id)
    ↓
verify role == doctor
    ↓
UserRepository.get_by_id(patient_id)
    ↓
verify role == patient
    ↓
AssignmentRepository.get_active_assignment()
    ↓
if exists: return existing
else create assignment
    ↓
AuditService.log_event(DOCTOR_ASSIGNMENT_CREATED)
```

#### Vì sao check role ở service?

Database FK chỉ biết user tồn tại, không biết user đó có role doctor/patient đúng với business rule không.

Service phải enforce:

```text
doctor_id must belong to doctor
patient_id must belong to patient
```

#### Deactivate flow

Không hard delete assignment.

```text
deactivate assignment
    ↓
set is_active=false
    ↓
audit log assignment_deactivated
```

**Lý do:**

- giữ history;
- audit được;
- không phá trace.

#### Authorization method

```python
ensure_doctor_can_access_patient()
```

Đây là method cực quan trọng cho milestone sau:

- doctor dashboard
- clinical profile access
- doctor copilot

---

## Phần 8. API dependency injection và routers

### 8.1 `backend/app/api/dependencies.py`

#### Mục đích

Wire toàn bộ dependencies cho FastAPI.

**Bao gồm:**

- `get_supabase`
- `get_user_repo`
- `get_consent_repo`
- `get_audit_repo`
- `get_assignment_repo`
- `get_audit_service`
- `get_auth_service`
- `get_consent_service`
- `get_assignment_service`
- `get_current_user`
- `require_current_admin`
- `require_current_doctor`
- `require_current_patient`
- `require_current_doctor_or_admin` *(refactor ở [PR #9](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/9) để gọi lại `require_roles({DOCTOR, ADMIN})` thay vì viết tay logic — xem Phần 19)*

#### Vì sao cần file này?

Không muốn routes tự tạo repository/service.

Ví dụ không nên viết trong route:

```python
db = get_supabase_client()
repo = UserRepository(db)
service = AuthService(repo)
```

Thay vào đó dùng:

```python
Depends(get_auth_service)
```

**Lợi ích:**

- route sạch;
- dependency graph rõ;
- dễ mock trong tests;
- tránh duplicate construction logic;
- không có circular import.

#### Flow protected route

```text
Authorization header
    ↓
HTTPBearer
    ↓
get_current_user()
    ↓
decode_access_token()
    ↓
CurrentUserClaims
    ↓
require_current_admin/doctor/patient
```

### 8.2 `backend/app/api/auth.py`

#### Mục đích

Expose auth endpoints.

**Routes:**

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

#### Flow register

```text
HTTP request
    ↓
UserCreate validation
    ↓
AuthService.register()
    ↓
UserResponse
```

#### Flow login

```text
HTTP request
    ↓
UserLogin validation
    ↓
AuthService.login()
    ↓
TokenResponse
```

#### Flow me

```text
Bearer token
    ↓
get_current_user()
    ↓
CurrentUserClaims
```

### 8.3 `backend/app/api/consent.py`

#### Mục đích

Expose consent endpoints.

**Routes:**

```text
POST /api/v1/consent/accept
GET  /api/v1/consent/status
```

#### Flow accept

```text
Bearer token
    ↓
current_user
    ↓
ConsentAcceptRequest(policy_version)
    ↓
ConsentService.accept_consent(user_id, payload, ip_address)
    ↓
ConsentResponse
```

#### Flow status

```text
Bearer token
    ↓
current_user
    ↓
ConsentService.get_status(user_id)
    ↓
ConsentStatusResponse
```

### 8.4 `backend/app/api/admin.py`

#### Mục đích

Expose admin/doctor assignment endpoints.

**Routes implemented:**

```text
POST  /api/v1/admin/assignments
PATCH /api/v1/admin/assignments/{assignment_id}/deactivate
GET   /api/v1/doctor/my-patients
```

#### Create assignment route

**Requires:**

```text
admin role
```

**Flow:**

```text
Bearer token
    ↓
require_current_admin
    ↓
AssignmentService.create_assignment()
```

#### Doctor my patients route

**Requires:**

```text
doctor role
```

**Flow:**

```text
Bearer token
    ↓
require_current_doctor
    ↓
AssignmentService.list_patients_for_doctor()
```

#### Vì sao `/doctor/my-patients` không nằm dưới `/admin`?

Domain rõ hơn:

```text
admin routes  = quản trị
doctor routes = doctor tự xem dữ liệu của mình
```

### 8.5 `backend/app/main.py`

#### Mục đích

FastAPI application entrypoint.

**Nội dung đã wire:**

- CORS middleware
- `AppException` handler
- health router
- auth router
- consent router
- admin router

#### Lỗi đã xử lý

Ban đầu có import duplicate:

```python
from app.api.health import router as health_router
from app.api import admin, auth, consent, health
```

Đã sửa về style thống nhất:

```python
from app.api import admin, auth, consent, health
```

và include:

```text
health.router
auth.router
consent.router
admin.router
```

#### Verify

Mở:

```text
http://localhost:8000/docs
```

**Kết quả cần thấy route groups:**

- health
- auth
- consent
- admin

---

## Phần 9. Supabase setup và runtime integration

### 9.1 Tạo Supabase project

Đã tạo Supabase Cloud dev project.

**Lưu ý:**

> - Chỉ dùng fake/dev data
> - Không dùng real patient data

### 9.2 `SUPABASE_URL` đúng là gì?

Đã xác định:

```bash
SUPABASE_URL=https://<project-ref>.supabase.co
```

Không dùng:

```text
/rest/v1
/dashboard
project URL trong dashboard UI
```

Vì `supabase-py` tự thêm path REST API khi cần.

**Sai nếu dùng:**

```text
https://<project-ref>.supabase.co/rest/v1/
```

### 9.3 `SUPABASE_KEY` dùng key nào?

Backend dùng secret/service role key:

```text
sb_secret_...
```

Không dùng publishable key cho backend.

**Lý do:**

- backend cần full quyền CRUD cho application tables;
- publishable/anon key phù hợp frontend khi có RLS;
- service role key chỉ dùng server-side.

**Không bao giờ:**

- paste key vào chat
- commit `.env`
- expose service role key ra frontend

### 9.4 Apply schema

Dùng Supabase Dashboard:

```text
SQL Editor
→ paste docs/schema.sql
→ Run
```

**Sau đó verify tables:**

- `users`
- `doctor_assignments`
- `consent_records`
- `chat_sessions`
- `chat_messages`
- `clinical_profiles`
- `stress_risk_scores`
- `audit_logs`

### 9.5 Permission issue đã gặp

Khi chạy query Supabase trực tiếp:

```text
permission denied for table users
```

**Supabase gợi ý:**

```sql
GRANT SELECT ON public.users TO service_role
```

**Nguyên nhân:**

- bảng custom được tạo trong public schema;
- `service_role` chưa có explicit table privileges;
- backend dùng secret key nhưng PostgREST role vẫn cần quyền table.

Fix bằng SQL grant ở Supabase SQL Editor và thêm vào `docs/schema.sql`.

Sau khi fix, Python direct query pass:

```text
data=[] count=None
```

**Điều này chứng minh:**

- Supabase URL đúng
- Supabase key đúng
- table tồn tại
- permission đã ổn

---

## Phần 10. Smoke test end-to-end

### 10.1 Mục tiêu smoke test

Kiểm tra runtime thật:

```text
FastAPI
→ service layer
→ repository layer
→ Supabase
→ response
```

> Không chỉ kiểm tra type/lint.

### 10.2 Test register

**Request:**

```text
POST /api/v1/auth/register
```

**Payload:**

```text
email
password
full_name
role
```

**Kết quả pass:**

- 200 OK
- `UserResponse` returned
- `password_hash` not exposed

> Record được tạo trong `users`.

### 10.3 Test login

**Request:**

```text
POST /api/v1/auth/login
```

**Kết quả pass:**

- `access_token`
- `token_type=bearer`
- `user`

### 10.4 Token handling lesson

Khi lấy token trong terminal, không nên copy thủ công từ JSON dài vì terminal có thể wrap line.

**Cách tốt:**

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"patient.dev@example.com","password":"Password123!"}' \
  | jq -r .access_token)
```

Sau đó:

```bash
echo $TOKEN
```

**Dùng token:**

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

#### Ghi chú

> Người dùng ban đầu dùng `ACCESS_TOKEN`, sau đó lấy `TOKEN`. Cả hai đều là biến shell tạm, miễn là header dùng đúng biến có token.

### 10.5 Test `/auth/me`

**Kết quả pass:**

```json
{
  "user_id": "...",
  "email": "patient.dev@example.com",
  "role": "patient"
}
```

**Điều này xác nhận:**

- JWT creation OK
- JWT decoding OK
- Authorization header OK
- `CurrentUserClaims` OK

### 10.6 Test consent accept

**Request:**

```text
POST /api/v1/consent/accept
```

**Payload:**

```json
{"policy_version": "v1"}
```

**Kết quả pass:**

- `ConsentResponse` returned
- `accepted=true`

**Điều này xác nhận:**

- `ConsentService`
- `ConsentRepository`
- `AuditService`
- `AuditRepository`
- Supabase insert

đều chạy được.

### 10.7 Test consent status

**Request:**

```text
GET /api/v1/consent/status
```

**Kết quả pass:**

```json
{
  "has_valid_consent": true,
  "current_policy_version": "v1",
  "latest_accepted_policy_version": "v1"
}
```

**Điều này xác nhận:**

- `ConsentRepository.has_accepted_version()`
- `ConsentRepository.get_latest_by_user()`
- `settings.current_consent_policy_version`

đều khớp.

---

## Phần 11. Các lỗi đã gặp và bài học

### 11.1 `git add .` lỡ stage quá nhiều

**Nguy cơ:**

- `.env`
- `backend/.env`
- `__pycache__`
- `*.pyc`

**Cách xử lý nếu chưa commit:**

```bash
git reset
```

Sau đó add đúng file cần commit.

**Cần đảm bảo `.gitignore` có:**

```text
.env
backend/.env
__pycache__/
*.pyc
.venv/
```

### 11.2 `.env` không được backend đọc

**Nguyên nhân:**

```text
make dev-be chạy từ backend/
BaseSettings env_file=".env" tìm backend/.env
```

**Fix:**

```text
config.py đọc root .env bằng Path
```

**Architecture principle:**

> - Root `.env` là source of truth
> - Không duplicate `backend/.env`

### 11.3 Supabase permission denied

**Lỗi:**

```text
permission denied for table users
```

**Fix:**

```text
grant privileges to service_role
```

**Bài học:**

- tạo bảng custom trong Supabase không đủ;
- backend key/role cần table privileges;
- grant phải nằm trong `schema.sql` để tái tạo DB không lỗi.

### 11.4 Supabase URL sai format

**Lỗi có thể gặp:**

```text
Invalid path specified in request URL
```

Nguyên nhân thường là URL sai, ví dụ có `/rest/v1`.

**Correct:**

```text
https://<project-ref>.supabase.co
```

### 11.5 passlib/bcrypt version issue

**Lỗi:**

```text
(trapped) error reading bcrypt version
ValueError: password cannot be longer than 72 bytes
```

**Nguyên nhân:**

```text
passlib incompatible với bcrypt version mới
```

**Fix:**

```bash
uv add --package backend "bcrypt==4.3.0"
```

**Commit khuyến nghị:**

```text
fix(auth): pin bcrypt to a passlib-compatible version for stable password hashing
```

### 11.6 Token copy thủ công bị hiểu nhầm

Terminal wrap làm token nhìn như xuống dòng, nhưng token thật có thể vẫn là một dòng.

**Cách tránh:**

```text
jq extract token tự động
```

**Command:**

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"patient.dev@example.com","password":"Password123!"}' \
  | jq -r .access_token)
```

### 11.7 Curl command bị paste trùng

**Lỗi:**

```text
curl -X POST http://localhostcurl -X POST ...
```

**Kết quả:**

```text
Not authenticated
```

**Bài học:**

- khi smoke test, copy command nguyên khối;
- nếu lỗi auth, test `/auth/me` trước để xác định token có đúng không.

---

## Phần 12. Architecture flow theo từng workflow

### 12.1 Register user flow

```text
Client
  ↓ POST /api/v1/auth/register
api/auth.py
  ↓ payload validated by UserCreate
AuthService.register()
  ↓ UserRepository.email_exists()
Supabase users select
  ↓ if email not exists
AuthService.hash_password()
  ↓ bcrypt/passlib
UserRepository.create()
  ↓ BaseRepository.create()
Supabase users insert
  ↓
UserResponse
```

**Security notes:**

- password không bao giờ trả ra response;
- password lưu DB dạng hash;
- duplicate email trả `AlreadyExistsError`.

### 12.2 Login flow

```text
Client
  ↓ POST /api/v1/auth/login
api/auth.py
  ↓ UserLogin
AuthService.login()
  ↓ UserRepository.get_by_email()
Supabase users select
  ↓ raw JSONRow includes password_hash
AuthService.verify_password()
  ↓
AuthService.create_access_token()
  ↓
TokenResponse(access_token, user)
```

**JWT notes:**

- token sống 60 phút;
- mỗi lần login cấp token mới;
- token cũ vẫn dùng được nếu chưa expired;
- logout hiện tại là frontend xóa token, chưa có server-side revocation.

### 12.3 Protected route flow

```text
Client
  ↓ Authorization: Bearer <token>
FastAPI dependency
  ↓ HTTPBearer
get_current_user()
  ↓ decode_access_token()
security.py
  ↓ JWT validation
CurrentUserClaims
  ↓ route receives current_user
```

Nếu token invalid/expired:

```text
UnauthorizedError → 401 JSON response
```

### 12.4 Consent flow

```text
Client
  ↓ POST /api/v1/consent/accept
get_current_user()
  ↓
ConsentService.accept_consent()
  ↓ ConsentRepository.create()
Supabase consent_records insert
  ↓
AuditService.log_event()
  ↓ AuditRepository.create()
Supabase audit_logs insert
  ↓
ConsentResponse
```

**Status:**

```text
Client
  ↓ GET /api/v1/consent/status
ConsentService.get_status()
  ↓ has_accepted_version()
  ↓ get_latest_by_user()
ConsentStatusResponse
```

### 12.5 Assignment flow

```text
Admin
  ↓ POST /api/v1/admin/assignments
require_current_admin()
  ↓
AssignmentService.create_assignment()
  ↓ validate doctor user exists and role=doctor
  ↓ validate patient user exists and role=patient
  ↓ check active assignment duplicate
  ↓ create assignment
  ↓ audit log
AssignmentResponse
```

**Doctor:**

```text
Doctor
  ↓ GET /api/v1/doctor/my-patients
require_current_doctor()
  ↓
AssignmentService.list_patients_for_doctor()
  ↓
AssignmentRepository.list_patients_for_doctor()
```

**Future clinical access:**

```text
Doctor requests patient clinical profile
  ↓
AssignmentService.ensure_doctor_can_access_patient()
  ↓
only then return doctor-facing data
```

---

## Phần 13. Files implemented trong Milestone 2 và mục đích

### Core files

| File | Mục đích |
|------|----------|
| `backend/app/core/config.py` | Quản lý settings/env. Sau fix, đọc root `.env`. |
| `backend/app/core/constants.py` | Định nghĩa enums domain-wide. |
| `backend/app/core/exceptions.py` | Định nghĩa custom exception hierarchy và JSON exception handler. |
| `backend/app/core/security.py` | Decode JWT và role check helpers. |

### Database client

| File | Mục đích |
|------|----------|
| `backend/app/db/supabase_client.py` | Tạo/cached Supabase client dùng chung. |

### Repository files

| File | Mục đích |
|------|----------|
| `backend/app/db/repositories/base.py` | Base CRUD repository + JSON typing. |
| `backend/app/db/repositories/user_repo.py` | Data access cho `users`. |
| `backend/app/db/repositories/consent_repo.py` | Data access cho `consent_records`. |
| `backend/app/db/repositories/audit_repo.py` | Data access cho `audit_logs`. |
| `backend/app/db/repositories/assignment_repo.py` | Data access cho `doctor_assignments`. |

### Schema files

| File | Mục đích |
|------|----------|
| `backend/app/schemas/user.py` | Auth/user request-response models. |
| `backend/app/schemas/consent.py` | Consent accept/status models. |
| `backend/app/schemas/audit.py` | Audit log models. |
| `backend/app/schemas/assignment.py` | Assignment models. |
| `backend/app/schemas/session.py` | Future session/message response models. |

### Service files

| File | Mục đích |
|------|----------|
| `backend/app/services/auth_service.py` | Register/login/password/JWT logic. |
| `backend/app/services/audit_service.py` | Centralized audit logging. |
| `backend/app/services/consent_service.py` | Consent accept/status business logic. |
| `backend/app/services/assignment_service.py` | Doctor-patient assignment validation, access check, audit logging. |

### API files

| File | Mục đích |
|------|----------|
| `backend/app/api/dependencies.py` | FastAPI DI for repos/services/current user/role guards. |
| `backend/app/api/auth.py` | Auth endpoints. |
| `backend/app/api/consent.py` | Consent endpoints. |
| `backend/app/api/admin.py` | Admin assignment and doctor my-patients endpoints. |
| `backend/app/main.py` | FastAPI app wiring: routers, CORS, exception handler. |

### Docs/config files

| File | Mục đích |
|------|----------|
| `docs/schema.sql` | Reference SQL schema + grants. |
| `docs/DATABASE_MODEL.md` | Data modeling reference. |
| `.env.example` | Environment variable template. |
| `backend/pyproject.toml` + `uv.lock` | Backend dependencies and locked versions, including Supabase/JWT/password hashing/bcrypt pin. |

---

## Phần 14. Current status sau DB-2.24

### Completed

| Task | Description |
|------|-------------|
| DB-2.1 | `schema.sql` |
| DB-2.2 | backend dependencies |
| DB-2.3 | config |
| DB-2.4 | Supabase client |
| DB-2.5 | constants |
| DB-2.6 | exceptions |
| DB-2.7 | Pydantic schemas |
| DB-2.8 | `BaseRepository` |
| DB-2.9 | `UserRepository` |
| DB-2.10 | `ConsentRepository` |
| DB-2.11 | `AuditRepository` |
| DB-2.12 | `AssignmentRepository` |
| DB-2.13 | `AuthService` |
| DB-2.14 | `AuditService` |
| DB-2.15 | `ConsentService` |
| DB-2.16 | `AssignmentService` |
| DB-2.17 | `security.py` |
| DB-2.18 | `dependencies.py` |
| DB-2.19 | auth routes |
| DB-2.20 | consent routes |
| DB-2.21 | admin/doctor assignment routes |
| DB-2.22 | `main.py` router + exception wiring |
| DB-2.23 | Supabase setup + schema apply |
| DB-2.24 | smoke test register/login/me/consent |
| DB-2.25 | automated tests phase 1 ([PR #10](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/10), 16 tests trên FakeSupabase — xem Phần 19) |

### Verified runtime flows

| Flow | Status |
|------|--------|
| Supabase direct query | pass |
| Register | pass |
| Login | pass |
| `/auth/me` | pass |
| Consent accept | pass |
| Consent status | pass |
| Backend docs visible | pass |

### Important unresolved / future tasks

- DB-2.26 frontend auth UI
- DB-2.27 Google OAuth setup
- automated tests phase 2 (FastAPI `TestClient` + httpx, RBAC API-layer, Google OAuth tests — extend từ phase 1 ở PR #10)

Nếu project muốn giữ Milestone 2 strict theo original plan, nên làm tiếp:

- frontend auth UI
- Google OAuth
- mở rộng test suite phase 2

Nếu muốn chuyển sớm sang chat/session foundation, có thể bắt đầu Phase 3 nhưng nên ghi rõ test/frontend/OAuth còn pending.

---

## Phần 15. Commit strategy và safety rules

### 15.1 Không dùng `git add .` bừa bãi

Trước commit nên chạy:

```bash
git status
```

Nếu lỡ:

```bash
git add .
```

mà chưa commit:

```bash
git reset
```

Sau đó add đúng file.

### 15.2 Không commit secrets

**Không commit:**

- `.env`
- `backend/.env`
- Supabase service role key
- JWT secret
- Google OAuth secret
- access token

### 15.3 Commit messages nên rõ ràng

**Ví dụ tốt:**

```text
fix(config,database,auth): stabilize Supabase environment loading, backend table privileges, and bcrypt password hashing
```

**Không nên:**

```text
fix stuff
update
add files
```

---

## Phần 16. Bài học kiến trúc sau giai đoạn này

### 16.1 Database không chỉ là schema

Trong project này, database foundation gồm:

- schema
- permissions
- repository layer
- service layer
- API layer
- security checks
- runtime smoke tests

> Chỉ tạo bảng chưa đủ.

### 16.2 Service role key không phải là magic key

Dù dùng `sb_secret_...`, table privileges vẫn cần được grant đúng cho PostgREST role.

### 16.3 Type strict giúp phát hiện mismatch sớm

Các lỗi như:

- `TokenResponse` missing `user`
- `ConsentAcceptRequest` has no `accepted`
- `ConsentStatusResponse` unexpected fields

được mypy bắt trước khi runtime.

> Điều này chứng minh strict typing có giá trị thật.

### 16.4 Architecture layering giúp debug nhanh

Khi lỗi xảy ra, ta tách được:

- env config issue
- Supabase permission issue
- schema mismatch
- dependency issue
- JWT copy issue
- curl command issue

> Vì mỗi layer có trách nhiệm rõ.

### 16.5 Manual smoke test vẫn cần thiết

`make check` pass không đảm bảo app chạy thật.

**Smoke test đã phát hiện:**

- env path issue;
- Supabase grant issue;
- bcrypt runtime issue;
- token handling issue.

---

## Phần 17. Checklist đọc lại trước khi tiếp tục

Trước khi sang phase tiếp theo, kiểm tra:

```bash
git status
make check
```

**Kiểm tra `.gitignore` có:**

```text
.env
.env.*
!.env.example
backend/.env
__pycache__/
*.pyc
.venv/
```

**Kiểm tra Supabase:**

- `users` row created
- `consent_records` row created
- `audit_logs` row created

**Kiểm tra docs:**

- `docs/schema.sql` có grant `service_role`
- `docs/DATABASE_MODEL.md` khớp schema

---

## Phần 18. Next implementation direction

Có hai hướng tiếp theo.

### Hướng A — Hoàn thiện phần còn lại của Milestone 2

- DB-2.26 frontend auth UI
- DB-2.27 Google OAuth
- automated tests phase 2 (mở rộng từ phase 1 ở [PR #10](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/10))

> Phù hợp nếu muốn Milestone 2 thật đầy đủ trước khi chuyển phase.
> Phase 1 tests đã đóng gap DB-2.25; chi tiết ở Phần 19.

### Hướng B — Sang Phase 3: Session & Chat Foundation

- `SessionRepository`
- `MessageRepository`
- `SessionService`
- `ChatService`
- Chat API routes
- patient chat flow

> Phù hợp nếu muốn bắt đầu core AI interaction layer.

### Khuyến nghị kỹ thuật

> Nếu mục tiêu là foundation chắc, làm DB-2.25 tests trước. Nếu mục tiêu là prototype nhanh, sang Phase 3 nhưng vẫn ghi test debt lại.

> Cập nhật: phase 1 tests đã có sẵn ở [PR #10](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/10). Foundation hiện đủ chắc để sang Phase 3, miễn ghi nợ phase 2 (API-layer + OAuth tests).

> **Cập nhật 2 (Hướng A đã đóng):** sau §19, Hướng A được làm tuần tự **C → B → A → D**: tests phase 2 ([PR #12](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/12)) → frontend auth UI ([PR #13](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/13)) → RBAC register fix ([PR #14](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/14)) → Google OAuth ([PR #15](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/15) + 2 follow-up bugfix [PR #17](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/17), [PR #18](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/18)) → Sessions CRUD foundation cho Milestone 5 ([PR #16](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/16)). Chi tiết ở [Phần 20](#phần-20-đóng-milestone-2--tests-phase-2-frontend-ui-google-oauth-sessions-crud-prs-12-18). Sau §20, Milestone 2 chính thức đóng và bước tiếp theo là Hướng A→B của Milestone 3 (RAG foundation + LangGraph agents).

---

## Phần 19. Code-quality refactor và automated tests phase 1 (PR #9 + PR #10)

### 19.1 Bối cảnh — code-quality audit sau smoke test

Sau khi DB-2.24 (manual smoke test register/login/consent) pass, một code-quality audit Milestone 2 phát hiện 6 hạn chế trong code đã merge:

| # | Hạn chế | Ảnh hưởng |
|---|---------|-----------|
| 1 | `_rows(data)` copy-paste 4 lần ở `user_repo.py`, `consent_repo.py`, `audit_repo.py`, `assignment_repo.py` | DRY violation, dễ lệch khi sửa |
| 2 | `auth_service._row_to_user_response` viết tay 4 helper parse `JSONRow` | Coupling không cần thiết với raw row, đã có `UserResponse.model_validate(dict(row))` ở `UserRepository._to_model` |
| 3 | `dependencies.require_current_doctor_or_admin` viết tay logic + `import ForbiddenError` bên trong hàm | Vi phạm "imports at top" và DRY (đã có `require_roles` ở `core/security.py`) |
| 4 | `AuthService._get_required_string/_bool/_datetime` raise `UnauthorizedError` cho lỗi thiếu cột DB | Domain coupling sai — đây là `DatabaseError` về bản chất, không phải auth error |
| 5 | `audit_service.log_event` chưa nhận `role` mặc dù schema `audit_logs.role` đã có sẵn | Milestone 3+ (clinical access) sẽ cần audit theo role để filter dashboard |
| 6 | `backend/tests/` chỉ có `__init__.py` — không có test tự động | DB-2.25 chưa được đóng |

Kết quả: 2 PR sequential.

- [PR #9](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/9) — refactor 5 hạn chế đầu (1–5).
- [PR #10](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/10) — đóng hạn chế 6 (automated tests phase 1).

### 19.2 PR #9 — code-quality refactor

#### 19.2.1 Lift `_rows()` lên `BaseRepository`

**Trước:** mỗi repo con có:

```python
def _rows(self, data: object) -> list[JSONRow]:
    if not isinstance(data, list):
        return []
    rows: list[JSONRow] = []
    for item in data:
        if isinstance(item, dict):
            rows.append(cast(JSONRow, item))
    return rows
```

Giống nhau từng dòng × 4 file.

**Sau:** chỉ còn ở `BaseRepository` (đã sẵn `cast` import). 4 repo con xoá luôn `_rows()` + xoá `from typing import cast` không còn dùng nữa (nếu có).

**Lợi ích:**

- DRY — sửa 1 chỗ duy nhất khi cần đổi behavior;
- Liskov substitution clean — base xử lý format Supabase response, child chỉ lo `_to_model`.

#### 19.2.2 Đơn giản hoá `AuthService._row_to_user_response`

**Trước:** 4 helper viết tay:

```python
self._get_required_string(row, "id")
self._get_required_string(row, "email")
self._get_required_bool(row, "is_active")
self._get_required_datetime(row, "created_at")
# … (lặp ~30 dòng)
```

Mỗi helper raise `UnauthorizedError` cho missing column → domain mismatch.

**Sau:**

```python
def _row_to_user_response(self, row: JSONRow) -> UserResponse:
    try:
        return UserResponse.model_validate(dict(row))
    except ValidationError as exc:
        raise DatabaseError("Invalid user row shape") from exc
```

**Lý do wrap try/except:**

- malformed row (cột thiếu / type sai) là vấn đề schema, không phải vấn đề auth;
- `DatabaseError` (500) đúng domain, không leak raw `ValidationError` traceback ra client;
- `UserRepository._to_model` đã dùng pattern này, service giờ đồng bộ.

`AuthService.login` cũng được sửa: đọc `password_hash` / `is_active` qua dict access + `DatabaseError` nếu cột thiếu, thay vì 3 helper riêng:

```python
password_hash = user_row.get("password_hash")
if not isinstance(password_hash, str) or not password_hash:
    raise DatabaseError("User row missing password_hash")

is_active = user_row.get("is_active")
if not isinstance(is_active, bool):
    raise DatabaseError("User row missing is_active")
if not is_active:
    raise UnauthorizedError("User account is inactive")
```

> `UnauthorizedError("User account is inactive")` được giữ — vì đây mới là business rule (user tồn tại nhưng bị deactivate), không phải lỗi schema.

#### 19.2.3 RBAC dependency reuse `require_roles`

**Trước:**

```python
def require_current_doctor_or_admin(
    current_user: Annotated[CurrentUserClaims, Depends(get_current_user)],
) -> CurrentUserClaims:
    from app.core.exceptions import ForbiddenError  # import inline → vi phạm style
    if current_user.role not in {UserRole.DOCTOR, UserRole.ADMIN}:
        raise ForbiddenError("…")
    return current_user
```

**Sau:**

```python
from app.core.security import require_roles  # import top

def require_current_doctor_or_admin(
    current_user: Annotated[CurrentUserClaims, Depends(get_current_user)],
) -> CurrentUserClaims:
    require_roles(current_user, {UserRole.DOCTOR, UserRole.ADMIN})
    return current_user
```

**Lợi ích:**

- imports at top — đúng project style;
- tái sử dụng `require_roles` đã có sẵn ở `core/security.py`;
- error message format đồng bộ với 3 dependency `require_current_admin/doctor/patient`.

#### 19.2.4 Audit role propagation

Schema `audit_logs.role` đã có sẵn (verify bằng SQL `information_schema.columns` trên Supabase thật trước khi sửa code), nhưng `log_event()` chưa nhận. Giờ thêm:

```python
async def log_event(
    self,
    *,
    user_id: str | None,
    action: AuditAction,
    role: str | None = None,                  # NEW
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> None: ...
```

**Cascade tới các caller:**

- `ConsentService.accept_consent(user_id, payload, role, ip_address)` — route `api/consent.py` truyền `role=current_user.role.value`.
- `AssignmentService.create_assignment(payload, assigned_by, assigned_by_role, ip_address)` — route `api/admin.py` truyền `assigned_by_role=current_user.role.value`.
- `AssignmentService.deactivate_assignment(assignment_id, deactivated_by, deactivated_by_role, ip_address)` — route `api/admin.py` truyền `deactivated_by_role=current_user.role.value`.

**Lý do `role: str | None = None` (không phải `UserRole | str | None`):**

- khớp DB column type (`text NULL`);
- khớp `AuditLogCreate.role: str | None`;
- caller gọi `current_user.role.value` ngay tại route → service không phải lo enum coercion.

#### 19.2.5 Real Supabase smoke test

Sau refactor, chạy verification trên Supabase thật (không phải FakeSupabase):

```text
1. Insert audit log với role='system' + metadata={'origin':'PR4_smoke','safe':True}
2. SELECT lại, đối chiếu role + metadata
3. DELETE row test, verify không sót
4. Import smoke: app.main load, 13 route đăng ký OK, không signature mismatch
```

**Kết quả:** all pass. `make check` (ruff + mypy strict) cũng pass trên 35 file.

### 19.3 PR #10 — automated tests phase 1

#### 19.3.1 Mục tiêu

Đóng DB-2.25 với một test foundation **chắc và nhỏ**, không phải nhồi 30 test một lần. Lý do: `FakeSupabase` là phần dễ tạo bug nhất (mock không khớp Supabase thật → test pass giả). Phase 1 tập trung 12-15 test cốt lõi đã prove FakeSupabase đúng + service layer hoạt động; phase 2 (sau) sẽ mở rộng API-layer với `TestClient` + `httpx`.

#### 19.3.2 Layout

```text
backend/tests/
├── __init__.py
├── conftest.py                  ← per-test fixtures + make_user_row helper
├── fakes/
│   ├── __init__.py
│   └── fake_supabase.py         ← chain stub mimic supabase Client
├── test_health.py               (1)
├── test_security.py             (4)
├── test_auth_service.py         (6)
├── test_consent_service.py      (2)
├── test_audit_service.py        (1)
└── test_assignment_service.py   (2)
```

Total: **16 tests** (target 12–15, vừa overshoot 1 cho regression guard `missing password_hash`).

#### 19.3.3 FakeSupabase design

Mimic **đúng và chỉ** chain API mà các repo trong codebase này dùng:

```python
client.table(name).select("*").eq(...).order(...).limit(...).execute()
client.table(name).insert(payload).execute()
client.table(name).update(payload).eq(...).execute()
client.table(name).delete().eq(...).execute()
```

**Quy tắc:**

- in-memory `dict[str, list[dict]]`, isolated mỗi test (fixture `fake_db`);
- auto-gen `id`, `created_at`, `updated_at` (cho `users`), `accepted_at` (cho `consent_records`) khi insert nếu chưa có;
- op không support → `raise NotImplementedError(...)` để khi codebase thêm method mới (vd `.in_()`, `.range()`), test fail loud thay vì pass giả.

**Helper test:**

```python
make_user_row(role=UserRole.DOCTOR, email="d@x.com", is_active=True, ...)
→ dict đầy đủ shape mà UserResponse.model_validate cần (id, auth_user_id, email,
  full_name, role, auth_provider, provider_user_id, avatar_url, is_active,
  password_hash, created_at, updated_at)
```

#### 19.3.4 Test coverage matrix

| File | Test | Cover gì |
|------|------|----------|
| `test_health.py` | health returns healthy status | api/health endpoint |
| `test_security.py` | decode valid token | JWT decode happy path |
|  | decode expired token raises Unauthorized | JWT exp validation |
|  | require_roles allows member | RBAC happy path |
|  | require_roles rejects non-member | RBAC reject + ForbiddenError message format |
| `test_auth_service.py` | register creates user | local provider, hashed password |
|  | register dup email raises AlreadyExists | email_exists branch |
|  | login returns token | TokenResponse with embedded user |
|  | login wrong password raises InvalidCredentials | verify_password branch |
|  | login inactive user raises Unauthorized | is_active business rule |
|  | **login missing password_hash raises DatabaseError** | regression guard cho PR #9 §19.2.2 |
| `test_consent_service.py` | accept_consent writes record + audit with role | role propagation §19.2.4 |
|  | get_status flips after accept | has_valid_consent logic |
| `test_audit_service.py` | **log_event persists role + sanitizes metadata** | regression guard cho PR #9 §19.2.4 |
| `test_assignment_service.py` | create_assignment is idempotent | no duplicate row + no double audit log |
|  | ensure_doctor_can_access_patient blocks unassigned | RBAC business logic |

**Regression guards quan trọng** (in đậm) đảm bảo nếu tương lai có ai revert PR #9 hoặc đổi behavior, test sẽ fail.

#### 19.3.5 Verification

```bash
cd backend && uv run pytest -v
# → 16 passed in 2.59s

make check
# uv run ruff check . → All checks passed!
# uv run mypy .       → Success: no issues found in 35 source files
```

> `tests/` đã được exclude khỏi mypy theo config sẵn có (`pyproject.toml` root) nên không bị type-strict, nhưng vẫn bị ruff lint (E + F + I).

### 19.4 Bài học mới

#### 19.4.1 Refactor có audit thường tốt hơn refactor không có audit

Cả 6 hạn chế ở §19.1 đều là **chi tiết nhỏ** — code vẫn chạy đúng smoke test. Nhưng tích lũy lại:

- DRY violation gốc khiến mỗi lần đổi format Supabase response phải sửa 4 chỗ;
- `UnauthorizedError` cho lỗi DB column khiến error message ngoài API gây hiểu nhầm;
- thiếu role ở audit khiến milestone sau (clinical dashboard) phải làm migration ngược.

Việc audit trước khi sang phase mới giúp xác định **debt là gì** thay vì để nó nổi lên ở Milestone 4 lúc đang vội.

#### 19.4.2 FakeSupabase là một interface contract — không phải mock toàn bộ

Không cố mimic toàn bộ supabase-py. Chỉ mimic **đúng các method codebase dùng**, và **fail loud** khi gặp method chưa support. Khi codebase thêm method mới (`.in_()`, `.range()`, RPC, …), test sẽ fail rõ ràng → buộc phải bổ sung fake hoặc dùng integration test.

#### 19.4.3 Regression guard quan trọng hơn coverage number

Trong 16 test, 2 test in đậm ở §19.3.4 (`login missing password_hash → DatabaseError`, `log_event persists role`) là **regression guard** trực tiếp cho PR #9. Coverage có thể chỉ ~70% nhưng giá trị thật của test suite nằm ở mỗi test có 1 lý do tồn tại rõ ràng — không phải con số.

#### 19.4.4 Sequential PR strategy giúp review dễ hơn

Thay vì gộp refactor + tests vào 1 PR khổng lồ (~700 dòng test + ~200 dòng refactor), tách:

- PR #9: chỉ refactor (~12 file, +57/-135 dòng) — review focus vào logic change.
- PR #10: chỉ tests (~9 file, +702 dòng) — review focus vào test design + FakeSupabase contract.

Khi PR #9 merge trước, test trong PR #10 mới có lý do tồn tại (regression guard cho refactor đã land). Ngược lại sẽ confusing.

---

## Phần 20. Đóng Milestone 2 — tests phase 2, frontend UI, Google OAuth, Sessions CRUD (PRs #12–#18)

### 20.1 Bối cảnh — đóng nốt Hướng A của Phần 18

Sau §19, ba việc còn nợ Milestone 2 đã được liệt kê ở [`MILESTONE2_GAP_REPORT.md`](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/blob/master/docs/_notes/MILESTONE2_GAP_REPORT.md):

- DB-2.25 tests phase 2 (mở rộng từ 16 unit/service tests sang FastAPI `TestClient` + RBAC API-layer + OAuth tests).
- DB-2.26 frontend auth UI (Streamlit pages thật, không còn demo "Check Backend Health").
- DB-2.27 Google OAuth backend.

Đồng thời, Sessions CRUD foundation (sub-scope của Milestone 5) được kéo về Milestone 2 vì không cần infra mới (Qdrant, RAG, LangGraph) — đủ điều kiện đóng gói cùng đợt với Hướng A.

Thứ tự thực hiện được chốt với người dùng là **C → B → A → D**:

| # | PR | Phase | Scope |
|---|----|-------|-------|
| 1 | [PR #12](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/12) | C | Tests phase 2 — 16 → 32 tests |
| 2 | [PR #13](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/13) | B | Frontend Streamlit auth UI |
| 3 | [PR #14](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/14) | (insert) | RBAC register fix — vá lỗ hổng escalation phát hiện qua Devin Review trên PR #13 |
| 4 | [PR #15](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/15) | A | Google OAuth backend (Verify-first) |
| 5 | [PR #16](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/16) | D | Sessions CRUD foundation (Milestone 5 sub-scope) |
| 6 | [PR #17](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/17) | A bugfix #1 | Ephemeral Supabase client (lỗi sai hướng — broke PKCE) |
| 7 | [PR #18](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/18) | A bugfix #2 | Reset auth-state về service_role (đúng hướng) |

PRs #17–#18 không nằm trong plan ban đầu — chúng là post-mortem của một runtime bug chỉ xuất hiện khi smoke test PR #15 trên Supabase thật. Chi tiết ở §20.7.

### 20.2 PR #12 — Tests phase 2 (16 → 32 tests)

#### Mục tiêu

Đóng nốt DB-2.25 bằng API-layer tests, không phải nhồi thêm unit test. Phase 1 đã prove `FakeSupabase` đúng (§19.3); phase 2 mở rộng lên FastAPI `TestClient` để cover full DI chain (route → dependency → service → repo → fake DB).

#### Layout

```text
backend/tests/
├── conftest.py                       # +client fixture, +token helper
├── test_auth_api.py                  # 6 API-layer tests (NEW)
├── test_consent_api.py               # 4 API-layer tests (NEW)
├── test_admin_api.py                 # 6 API-layer tests (NEW)
└── (existing service-layer tests)    # giữ nguyên 16 từ phase 1
```

Total: **32 tests** (16 service-layer giữ nguyên + 16 API-layer mới).

#### Fixtures bổ sung

`conftest.py` thêm:

- `client` — `TestClient(app)` với `app.dependency_overrides[get_supabase] = lambda: fake_db` để mọi route đều đi qua FakeSupabase chung.
- `auth_headers(role: UserRole, ...)` — helper sinh JWT thật bằng `core.security.create_access_token` thay vì mock JWT decode (test stronger contract: route + dependency + decode đều chạy thật, chỉ DB là fake).

#### Test coverage matrix mới

| File | Test | Cover gì |
|------|------|----------|
| `test_auth_api.py` | POST /auth/register success | api/auth route + AuthService.register full DI chain |
|  | POST /auth/register dup email → 409 | error mapping `AlreadyExistsError → 409` ở `core/exceptions.py` |
|  | POST /auth/login success → JWT + user | TokenResponse shape qua wire |
|  | POST /auth/login wrong password → 401 | error mapping `InvalidCredentialsError → 401` |
|  | GET /auth/me requires Bearer | `get_current_user` dependency reject anonymous |
|  | GET /auth/me with valid Bearer | full claims roundtrip |
| `test_consent_api.py` | POST /consent/accept persists row + audit role | role propagation §19.2.4 qua HTTP |
|  | GET /consent/status reflects current version | version coherence với `CURRENT_CONSENT_POLICY_VERSION` |
|  | POST /consent/accept stale version → 400 | version validation |
|  | POST /consent/accept anonymous → 401 | `get_current_user` reject |
| `test_admin_api.py` | POST /admin/assignments admin-only → patient gets 403 | RBAC dependency `require_current_admin` |
|  | POST /admin/assignments admin-only → doctor gets 403 | RBAC reject doctor |
|  | POST /admin/assignments admin success | happy path + audit `assigned_by_role='admin'` |
|  | POST /admin/assignments idempotent | giữ idempotency của §19 qua API |
|  | DELETE /admin/assignments/{id} admin-only | RBAC reject + happy path |
|  | DELETE /admin/assignments/{id} writes audit role | `deactivated_by_role` cascade từ §19.2.4 |

#### Verification

```bash
cd backend && uv run pytest -v
# → 32 passed in ~3s

make check
# uv run ruff check . → All checks passed!
# uv run mypy .       → Success: no issues found in 40 source files
```

Diff: chỉ thêm test files + `httpx>=0.28.1` dev dep (yêu cầu của FastAPI `TestClient`); không đụng production code.

### 20.3 PR #13 — Frontend Streamlit auth UI

#### Mục tiêu

Thay 1 trang demo `main.py` (chỉ có 1 nút "Check Backend Health") bằng multi-page Streamlit app thực sự cho user.

#### Layout

```text
frontend/
├── main.py                  ← landing page + sidebar nav
├── api_client.py            ← shared httpx client (reads BACKEND_URL)
├── pages/
│   ├── 1_Register.py        ← email + password (KHÔNG có role selector — fix ở §20.4)
│   ├── 2_Login.py           ← email + password
│   ├── 3_Consent.py         ← display current policy version + Accept button
│   └── 4_Profile.py         ← /auth/me claims viewer
```

`api_client.py` quy ước:

- `BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")`;
- token persist trong `st.session_state["jwt"]` (TUYỆT ĐỐI không lưu vào cookies/local storage để giảm risk XSS — cùng logic [Phần 11.3 SRDS](../SRDS.md));
- mọi call gắn `Authorization: Bearer <jwt>` từ session state;
- 401 từ backend → clear session_state + redirect Login page.

#### Tại sao chưa thêm Google login button

Phase B này đi trước phase A. Nếu thêm button Google ở UI bây giờ, sẽ là dead-link cho đến khi A xong. Để tránh ship code stub, button được defer sang follow-up sau khi PR #15 merge. Trong scope D thì cũng không cần (Sessions CRUD là pure backend).

#### Verification

```bash
cd frontend && uv run streamlit run main.py
# → boot OK, 4 page load OK, register/login/consent/profile click qua được manual
```

Backend tests (32) vẫn pass; `make check` pass (40 source files).

### 20.4 PR #14 — RBAC register fix (Devin Review finding)

#### Bối cảnh — bug an ninh sót lại từ phase B

Devin Review chạy tự động trên PR #13 đã flag 1 finding **đỏ**:

> 🔴 **Register page allows self-registration as admin/doctor, enabling privilege escalation.** Backend `/auth/register` không restrict role → bất kỳ ai cũng có thể POST `{"email":"...","password":"...","role":"admin"}` rồi nhận admin JWT. Vi phạm AGENT.md §11.3 RBAC matrix.

Đây là bug **thật**, không phải false positive. Cả frontend (selectbox role ở Register page) và backend (`AuthService.register` accept role tự do) đều có lỗ hổng.

#### Fix — chặn ở backend làm gốc, cập nhật frontend cho nhất quán

**Backend:** thêm schema mới `PublicUserRegister`:

```python
class PublicUserRegister(BaseModel):
    """Public-facing register payload. Always patient — no role field exposed."""
    email: EmailStr
    password: str
    full_name: str | None = None
```

`/auth/register` route đổi sang `PublicUserRegister`. Bên trong `AuthService.register`, nếu input là `PublicUserRegister` thì hard-code `role=UserRole.PATIENT`; admin/doctor vẫn có thể tạo qua `/admin/users` (admin-only) bằng schema cũ `UserRegisterRequest` để giữ flexibility.

**Frontend:** xoá selectbox role ở `pages/1_Register.py`. Form chỉ còn email + password + full_name.

#### Regression test

Hai test mới ở `test_auth_api.py`:

```python
async def test_register_ignores_admin_role_in_payload(client, fake_db):
    # POST với role=admin trong body → 200 nhưng user.role == 'patient'
    resp = client.post("/api/v1/auth/register", json={..., "role": "admin"})
    assert resp.status_code == 200
    assert resp.json()["user"]["role"] == "patient"

async def test_register_ignores_doctor_role_in_payload(client, fake_db):
    # tương tự cho doctor
    ...
```

`role=admin` / `role=doctor` trong body bị Pydantic ignore (extra field) → backend tự gán `patient`. **Regression guard này đảm bảo nếu tương lai ai unstrict schema, test sẽ fail.**

#### Verification

32 → **34 tests** pass; `make check` pass; tổng diff +98/-21 dòng (5 file: 3 backend + 2 frontend).

### 20.5 PR #15 — Google OAuth backend với Verify-first policy

#### Quyết định kiến trúc — Supabase làm OAuth proxy

Backend KHÔNG gọi Google API trực tiếp. Mọi OAuth flow đi qua `supabase.auth.sign_in_with_oauth()` + `supabase.auth.exchange_code_for_session()`. Lý do:

- Google credentials (Client ID + Secret) lưu trong **Supabase Dashboard → Authentication → Providers → Google**, KHÔNG nằm trong `.env` của backend → ít chỗ leak hơn.
- Supabase tự handle PKCE, callback validation, token refresh.
- Backend chỉ cần: gọi 2 method, lấy `supabase_user`, dispatch sang business logic riêng (verify-first, audit, JWT mint).

Trade-off: phụ thuộc cứng vào Supabase (không thể plug provider khác mà không refactor). Chấp nhận vì project đã commit dùng Supabase ở §3.

#### 3 routes + 3 service methods

```text
GET  /api/v1/auth/google              → AuthService.get_google_oauth_url() → URL Supabase
GET  /api/v1/auth/google/callback     → AuthService.handle_google_callback(code) → redirect FE với one-time auth_code
POST /api/v1/auth/google/exchange     → AuthService.exchange_auth_code(auth_code) → TokenResponse JWT
```

Verify-first policy ở `handle_google_callback`:

```python
existing = await self._user_repo.get_by_email(google_user.email)
if existing and existing.auth_provider == AuthProvider.LOCAL:
    # Email đã đăng ký password trước → từ chối Google login
    raise UnauthorizedError(
        "Email đã đăng ký bằng password. Hãy login bằng password rồi link Google từ Profile."
    )
if existing and existing.auth_provider == AuthProvider.GOOGLE:
    # User Google quay lại — login lần thứ N
    if not existing.is_active:
        raise UnauthorizedError("User account is inactive")
    user = existing
else:
    # User mới — tạo với auth_provider=google, password_hash=NULL, role=patient
    user = await self._user_repo.create_google_user(google_user, role=UserRole.PATIENT)
```

#### Tránh leak JWT vào URL — `_pending_tokens`

Một bug điển hình của OAuth callback là set `Location: /?access_token=eyJ...` trong redirect → JWT lộ trong browser history, server log, referer header. Để tránh:

1. `handle_google_callback` mint JWT NGAY, lưu trong dict `_pending_tokens: dict[str, tuple[TokenResponse, datetime]]` (in-memory, key là một `auth_code` random base64).
2. Redirect FE với chỉ `?auth_code=<one-time>&user_name=<name>` — KHÔNG có JWT.
3. FE gọi `POST /auth/google/exchange` với `auth_code` → backend pop entry khỏi `_pending_tokens` (single-use), trả `TokenResponse`.
4. TTL 60 giây cho mỗi entry (`exchange_auth_code` reject 401 nếu hết hạn).
5. Replay cùng `auth_code` → 401 (đã pop).

Trade-off: `_pending_tokens` là in-memory class-level dict → KHÔNG horizontal-scale OK. Production cần thay bằng Redis. Acceptable cho MVP single-instance; debt ghi nợ ở [`MILESTONE2_GAP_REPORT.md`](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/blob/master/docs/_notes/MILESTONE2_GAP_REPORT.md).

#### Audit ghi đầy đủ

`AuditAction.USER_REGISTERED` và `AuditAction.USER_LOGIN` đều được log với `metadata={"method": "google"}` và `role=user.role.value` (cascade từ §19.2.4 PR #9). Cho phép Milestone 4 dashboard filter login theo provider.

#### Frontend integration

`pages/2_Login.py` thêm button "Login with Google":

```python
if st.button("Login with Google"):
    resp = httpx.get(f"{BACKEND_URL}/api/v1/auth/google")
    st.markdown(f"[Continue to Google]({resp.json()['url']})")
```

Sau khi user authorize ở Google + Supabase, callback redirect về `localhost:8501/?auth_code=...&user_name=...`. `main.py` detect query param này → call `/auth/google/exchange` → store JWT vào `st.session_state["jwt"]` → redirect Profile.

#### Verification

Unit tests + API tests: 34 → **52 tests** (PR #15 gốc) pass với FakeSupabase mock OAuth response.

Live smoke test trên Devin VM PHẢI có: Google Cloud Console OAuth client + Supabase Dashboard Provider = Google enabled + redirect URI `https://<project>.supabase.co/auth/v1/callback` thêm vào Google allow-list.

> Smoke test gốc fail → PRs #17–#18 follow-up. Chi tiết ở §20.7.

### 20.6 PR #16 — Sessions CRUD foundation (sub-scope Milestone 5)

#### Mục tiêu

Đóng gói "session lifecycle" (start / close / get / list) như một foundation cho Milestone 5. Không có chat / AI / RAG / LangGraph trong scope này — chỉ CRUD thuần.

Lý do tách: Milestone 3 (RAG) và Milestone 4 (LangGraph agents) cần infra mới (Qdrant, OpenAI embeddings, DSM-5 ingestion). Sessions CRUD không cần gì ngoài Supabase đã có. Tách trước giúp khi M3+M4 vào sau, M5 chỉ phải gắn AI vào lifecycle đã sẵn — không tạo throwaway code.

#### 4 routes

| Method | Path | Auth | Behavior |
|--------|------|------|----------|
| POST | `/api/v1/sessions` | Patient (JWT) | Start session — consent gate + one-active gate |
| POST | `/api/v1/sessions/{id}/close` | Owner | Close session — idempotent |
| GET | `/api/v1/sessions/{id}` | Owner / assigned doctor | Read 1 session |
| GET | `/api/v1/sessions/me` | Patient | List own sessions với pagination |

#### 5 design decisions chốt với user (default được chọn cho cả 5)

1. **`close_reason` enum default `user_end`** — schema thêm enum `SessionCloseReason` (`user_end | system_timeout | doctor_intervention`) thay vì free text → query analytics dễ.
2. **One-active policy: 409 Conflict** nếu patient đã có session `status=active` khi gọi POST. Giảm noise data + buộc client phải close session cũ trước.
3. **Consent gate: 403 Forbidden** nếu user chưa accept `CURRENT_CONSENT_POLICY_VERSION` (`v1`) trước khi start. Không silent-skip — user phải qua trang Consent (PR #13) trước.
4. **Defer M5 chat features** — không xử lý message AI / streaming / pagination message ở PR này. PR sau ở Milestone 5 sẽ thêm.
5. **Pure backend D3** — không có frontend chat page mới. Test = service tests + API tests (RBAC + lifecycle), không có Streamlit UI cho sessions.

#### Idempotent close

`POST /sessions/{id}/close` được gọi 2 lần liên tiếp:

- lần 1: status `active → ended`, audit `session_closed` với `metadata.reason='user_end'`.
- lần 2: status đã `ended` → no-op, KHÔNG audit duplicate row, return 200 (giống behavior `AssignmentService.create_assignment` từ §19).

#### RBAC matrix cho session

```text
patient(self):  POST /sessions, POST close own, GET own, GET /sessions/me
patient(other): 403 hết
doctor:         GET /sessions/{id} CHỈ KHI có active assignment với patient owner;
                KHÔNG được POST/close (chỉ patient close session của họ)
admin:          giống doctor — read-only
```

`api/sessions.py` dependency: tái sử dụng `require_current_patient` (cho start/close/list) và viết mới `require_session_reader` (cho GET single — check ownership hoặc assignment).

#### Test coverage

23 test mới (12 service + 3 repo + 8 API):

| Layer | Cover gì |
|-------|----------|
| service | start consent gate, start one-active reject, close idempotent, RBAC patient owns close, RBAC doctor blocked from close, list pagination, close audit metadata, ... |
| repo | `get_active_for_patient` returns active only; `list_for_patient` orders desc + paginates; idempotent ops |
| api | full DI: 200 happy path, 403 consent, 409 one-active, 403 wrong patient, 200 doctor reads assigned, 403 doctor reads unassigned, ... |

50 → **73 tests** pass; `make check` pass (45 source files).

### 20.7 PRs #17 + #18 — Google OAuth runtime bug saga (postgrest 42501 + PKCE)

#### Bug #1 — postgrest 42501 sau smoke test PR #15

Khi smoke test PR #15 trên Devin VM (Supabase + Google thật), backend log show:

```text
postgrest.exceptions.APIError: {
  'message': 'permission denied for table users',
  'code': '42501',
  'hint': 'Grant the required privileges to the current role with: GRANT SELECT ON public.users TO authenticated;',
}
```

User thấy: `localhost:8501/?google_error=Failed+to+fetch+user+by+provider+identity` thay vì JWT.

**Root cause:** `supabase-py` `Client` maintain 1 auth state duy nhất. Khi `auth.exchange_code_for_session(code)` chạy, nó internal dispatch event `SIGNED_IN` → swap `Authorization` header của PostgREST từ `Bearer <service_role_key>` sang `Bearer <user_jwt>`. Câu query ngay sau đó (`get_by_provider_identity` trong `handle_google_callback`) giờ đi dưới role `authenticated` → RLS reject → 42501.

Đây không phải lỗi config Supabase (không thể GRANT SELECT cho `authenticated` được vì thế là tự bypass RLS). Đây là **bug hành vi không tài liệu** của supabase-py.

#### Attempt sai hướng — PR #17 Ephemeral client

PR #17 thử: tạo 1 `Client` mới mỗi khi gọi OAuth method:

```python
def _ephemeral_supabase_client(self) -> Client:
    return create_client(settings.supabase_url, settings.supabase_key)

# In get_google_oauth_url + _exchange_supabase_code:
response = self._ephemeral_supabase_client().auth.sign_in_with_oauth(...)
session = self._ephemeral_supabase_client().auth.exchange_code_for_session(...)
```

Logic: client A handle request 1 (sign_in_with_oauth) → client A bị GC → request 2 dùng client B mới (exchange_code_for_session) → client B bị mutate state nhưng KHÔNG chia sẻ với `self._supabase` (cái dùng cho repo) → repo vẫn `service_role` OK.

Tests (FakeSupabase) đều pass; `make check` pass; merged.

**Smoke test thất bại lần 2:** `localhost:8501/?google_error=Google+login+failed` (khác lần trước, không còn 42501).

**Root cause của fix sai:** PKCE flow yêu cầu `code_verifier` được generate ở request 1 (lúc redirect đi Google) phải được persist để request 2 (lúc exchange code) đọc lại. supabase-py persist verifier vào **storage của Client instance** (mặc định in-memory). PR #17 tạo 2 instance khác nhau → instance A có verifier nhưng đã GC; instance B mới tinh không có verifier → Supabase reject exchange với "Google login failed".

→ Ephemeral client phá PKCE. Sai hướng. Cần revert.

#### Fix đúng — PR #18 Reset auth-state

Quay lại dùng `self._supabase` singleton cho cả 2 OAuth call (verifier survive OK), nhưng thêm 1 hook reset auth state về `service_role` SAU khi exchange:

```python
def _reset_supabase_to_service_role(self) -> None:
    """Restore the shared Supabase client's auth state to service_role.

    Re-emits SIGNED_OUT(None) — the same hook supabase-py uses on logout —
    which nulls cached PostgREST/storage/functions clients (so they lazy-
    re-init with refreshed headers) and rewrites
    options.headers["Authorization"] back to Bearer <supabase_key>.
    No network call, deterministic, idempotent.
    """
    listen = getattr(self._supabase, "_listen_to_auth_events", None)
    if callable(listen):
        listen("SIGNED_OUT", None)

def _exchange_supabase_code(self, code: str) -> Any:
    callback_url = f"{settings.backend_url}/api/v1/auth/google/callback"
    try:
        try:
            session_response = self._supabase.auth.exchange_code_for_session(
                {"auth_code": code, "code_verifier": "", "redirect_to": callback_url}
            )
        except Exception as exc:
            raise UnauthorizedError("Google login failed") from exc
    finally:
        # Always reset, including on exchange failure — partial mutation possible.
        self._reset_supabase_to_service_role()
    ...
```

**Vì sao dispatch `SIGNED_OUT` thay vì `auth.sign_out({"scope":"local"})`:** sign_out gọi network HTTP DELETE tới Supabase Auth endpoint (revoke session bên server) — không cần thiết vì JWT user đã được mint thành app JWT, mục đích duy nhất ở đây là reset client-side header. Dispatch event là pure client-side, deterministic, không network.

#### Tests update cho PR #18

```python
# Removed (assertion sai, dựa trên ephemeral approach của PR #17):
test_oauth_uses_ephemeral_client_so_db_state_is_isolated

# Added:
async def test_handle_google_callback_resets_auth_state_after_exchange(...):
    # Sau exchange thành công, expect ("SIGNED_OUT", None) đã được dispatch
    auth_code, _ = await auth_service.handle_google_callback("any-code")
    assert fake_db.auth_events_received[-1] == ("SIGNED_OUT", None)

async def test_handle_google_callback_resets_auth_state_even_on_exchange_failure(...):
    # Khi exchange raise (Supabase reject), state vẫn được reset
    fake_db.auth.exchange_should_fail = True
    with pytest.raises(UnauthorizedError):
        await auth_service.handle_google_callback("any-code")
    assert fake_db.auth_events_received[-1] == ("SIGNED_OUT", None)
```

`FakeSupabase` thêm `auth_events_received: list[tuple[str, Any]]` + `_listen_to_auth_events(event, session)` recorder để service test có thể assert hành vi reset mà không cần Supabase thật.

`make check` pass; **75 tests** pass.

### 20.8 Smoke test trên Devin VM — kết quả 5/5 PASS sau PR #18

Plan: 5 adversarial assertions, mỗi cái thiết kế để fail nếu fix sai.

| # | Assertion | Adversarial framing | Result |
|---|-----------|--------------------|--------|
| 1 | `GET /auth/google` trả URL Supabase với `provider=google` + PKCE challenge | Naive impl gọi Google trực tiếp hoặc trả URL rỗng | PASS |
| 2 | Final callback URL có `auth_code=` + `user_name=` và NONE của `access_token`/`Bearer`/`eyJ` | Naive impl đặt `access_token=` trong URL → AGENT.md §11 violation | PASS |
| 3 | `POST /google/exchange` trả 200 với `email == GOOGLE_TEST_EMAIL` + JWT `role == "patient"` | Naive impl dùng Supabase JWT thay vì app JWT (RBAC mismatch); hoặc JWT có `role=admin` (PR #14 broken) | PASS |
| 4 | Replay cùng `auth_code` → 401 | Weak impl quên pop khỏi `_pending_tokens` → vô hạn replay | PASS |
| 5 | `users` row: `auth_provider='google'`, `password_hash IS NULL`, `role='patient'`; `audit_logs.user_login` row có `metadata.method='google'` và `role='patient'` | Buggy impl ghi `auth_provider='local'` hoặc hash empty password; `role` NULL trong audit | PASS |

Live data verified bằng Python supabase client:

```text
users[f4bf737c-c808-4a06-bceb-8f43e723e41c]:
  email='devinaitesting@gmail.com', role='patient', auth_provider='google',
  password_hash=None, is_active=True

audit_logs (newest first):
  user_login      role='patient'  metadata={'method':'google'}
  user_registered role='patient'  metadata={'method':'google'}
```

Smoke test report đính kèm trong [comment trên PR #18](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/18). Recording bị mất khi shell restart giữa execution; evidence dùng raw text output + 1 screenshot Streamlit page sau callback.

### 20.9 Bài học mới

#### 20.9.1 Test coverage giả khi mock không khớp library behavior

PR #17 có 100% test pass với FakeSupabase (FakeSupabase không simulate auth state mutation của `exchange_code_for_session`), `make check` xanh, mypy strict pass. Smoke test thật MỚI lộ ra fix sai hướng. Bài học:

- **Mock chỉ chứng minh logic của TA đúng, không chứng minh assumption về library đúng.** Khi assumption về library sai (ephemeral client lưu PKCE verifier ở storage chia sẻ), mock cũng sai theo → test pass giả.
- **Smoke test thật trên infra production-like là không thể skip cho integration với external service** — kể cả khi 100 test mock pass.
- Sau PR #18, FakeSupabase được mở rộng để **record auth event dispatch** (`auth_events_received`) — biến contract "reset state" thành thứ test được. Đây là pattern: nếu bug runtime đã từng trượt qua mock, sau khi fix phải mở rộng mock contract để bug tương tự không trượt lại.

#### 20.9.2 PR sequential thắng PR khổng lồ — đã prove qua C → B → A → D

Phase này có 7 PR (#12, #13, #14, #15, #16, #17, #18) thay vì 1 PR khổng lồ. Lợi ích thấy rõ:

- **PR #14 vá lỗ hổng escalation** chỉ +98/-21 dòng, review trong 5 phút. Nếu gộp với PR #13 frontend (~500 dòng), reviewer rất dễ miss.
- **PRs #17–#18 bugfix** không phải cần revert toàn bộ phase A. Chỉ cần thêm 2 PR follow-up nhỏ.
- **PR #16 Sessions CRUD** không bị ảnh hưởng bởi bug Google OAuth — vì code không đụng vào nhau, có thể merge song song nếu cần (thực tế làm tuần tự).

Trade-off: 7 PR review effort > 1 PR review effort. Nhưng cost-of-bug khi miss escalation finding ở 1 PR khổng lồ >> overhead review 7 PR nhỏ.

#### 20.9.3 Devin Review = 1 cặp mắt extra, đáng tin cho finding security

Devin Review tự chạy trên PR #13 và bắt được lỗ hổng escalation trước khi user thấy. Đây không phải false positive — là bug thật, vi phạm AGENT.md §11.3 RBAC matrix. Bài học:

- **Auto code review tool nên được treat as input vào checklist trước khi merge,** không phải background noise.
- Khi tool flag finding đỏ về security, dừng phase đang làm và fix immediate (PR #14 chen ngang giữa B → A) thay vì defer. Chi phí defer thường > chi phí fix ngay.

#### 20.9.4 Verify-first chặn được account takeover qua provider mới

Nếu auto-link Google account theo email (lax policy):

> Attacker biết email victim đã đăng ký password ở app này → attacker tạo Google account với cùng email đó (Google không yêu cầu chứng minh ownership email cho gmail.com — bất kỳ ai có thể sign up với bất kỳ chuỗi nào trước @gmail.com) → attacker login Google → app auto-link → attacker vào account victim.

Verify-first đóng đường này:

- Nếu email Google trùng account local-password → reject Google login, redirect "Vui lòng login bằng password trước rồi link Google từ Profile."
- Linking thật sự yêu cầu user authenticate ownership email qua password trước.

Trade-off: UX kém hơn (user phải login local → link manual). Acceptable vì đây là health app — security >> convenience. Documented ở [`MILESTONE2_GAP_REPORT.md`](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/blob/master/docs/_notes/MILESTONE2_GAP_REPORT.md) §8 risk #3.

#### 20.9.5 One-time auth code thay vì JWT trong URL

Tính toán cụ thể: nếu redirect là `?access_token=eyJ...`, JWT sẽ xuất hiện trong:

- browser history (persist disk-based);
- referer header gửi tới external resources nếu page có image/script bên thứ 3;
- server access log (nginx, CloudFlare default log full URL);
- bookmarks nếu user accidental save.

`?auth_code=<random>&user_name=<urlencoded>` chỉ leak auth_code (single-use, TTL 60s, KHÔNG decode được — chỉ là key vào in-memory dict). Mất auth_code = mất nothing nếu đã expire / đã exchange.

Pattern này cũng dùng được cho phase Linking sau (provide auth_code thay vì gắn provider_user_id trực tiếp vào URL).

---

## Phụ lục — Chuỗi PR Milestone 2 đầy đủ

| # | PR | Title | Phần |
|---|----|-------|------|
| 1 | [#6](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/6) | Refactor docs Markdown | (audit) |
| 2 | [#7](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/7) | Fix `assigned_at` → `created_at` ordering | (audit) |
| 3 | [#8](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/8) | Add `MILESTONE2_GAP_REPORT.md` | (audit) |
| 4 | [#9](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/9) | Code-quality refactor (DRY + audit role) | §19.2 |
| 5 | [#10](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/10) | Automated tests phase 1 (16 tests) | §19.3 |
| 6 | [#11](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/11) | Sync notes với PR #9 + PR #10 | (docs) |
| 7 | [#12](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/12) | Tests phase 2 (16 → 32 tests) | §20.2 |
| 8 | [#13](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/13) | Frontend Streamlit auth UI | §20.3 |
| 9 | [#14](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/14) | RBAC register fix (privilege escalation) | §20.4 |
| 10 | [#15](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/15) | Google OAuth backend (Verify-first) | §20.5 |
| 11 | [#16](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/16) | Sessions CRUD foundation | §20.6 |
| 12 | [#17](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/17) | Ephemeral client (sai hướng — broke PKCE) | §20.7 |
| 13 | [#18](https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform/pull/18) | Reset auth-state về service_role (đúng hướng) | §20.7 |

Total: 13 PR cho Milestone 2 (gồm cả audit/refactor/docs ở §19 + đóng nốt ở §20). 75 tests pass; `make check` pass (45 source files); 1 live smoke test pass 5/5 trên Supabase + Google thật.
