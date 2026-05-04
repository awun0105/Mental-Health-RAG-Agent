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

- `log_event()`

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

- `accept_consent`
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

- `create_assignment`
- `deactivate_assignment`
- `ensure_doctor_can_access_patient`
- `list_patients_for_doctor`
- `list_doctors_for_patient`

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
- `require_current_doctor_or_admin`

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

- DB-2.25 automated tests
- DB-2.26 frontend auth UI
- DB-2.27 Google OAuth setup

Nếu project muốn giữ Milestone 2 strict theo original plan, nên làm tiếp:

- automated tests
- frontend auth UI
- Google OAuth

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

- DB-2.25 automated tests
- DB-2.26 frontend auth UI
- DB-2.27 Google OAuth

> Phù hợp nếu muốn Milestone 2 thật đầy đủ trước khi chuyển phase.

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
