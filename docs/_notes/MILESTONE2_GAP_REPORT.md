# Milestone 2 — Gap Report

> **Phạm vi:** Báo cáo gap giữa hiện trạng repo và yêu cầu hoàn thành Milestone 2 (Data & Auth Foundation), tập trung vào **Google OAuth (task 2.27)** + frontend auth UI (task 2.26) + automated tests (task 2.24).
>
> **Nguồn đối chiếu:**
>
> - `docs/.plan/MILESTONE2.md` — kế hoạch chi tiết task 2.1 → 2.27.
> - `docs/_notes/[2]E2E_database_design_and_development.md` — note E2E thiết kế DB.
> - `docs/_notes/[3]database_auth_implementation_process.md` — note quá trình implement.
> - Code thực tế tại `backend/app/`, `frontend/main.py`, `docs/schema.sql`, `.env.example`.
>
> **Quy ước báo cáo:**
>
> - ✅ Done — đã có code và `make check` pass.
> - 🟡 Partial — có một phần (schema/setting/comment) nhưng chưa wire-up runtime.
> - ❌ Missing — chưa tồn tại trong code base.

---

## Mục lục

- [1. Tổng quan tiến độ Milestone 2](#1-tổng-quan-tiến-độ-milestone-2)
- [2. Gap chi tiết — Google OAuth (task 2.27)](#2-gap-chi-tiết--google-oauth-task-227)
  - [2.1 Backend Settings và environment](#21-backend-settings-và-environment)
  - [2.2 Schema và Repository](#22-schema-và-repository)
  - [2.3 Service layer (`AuthService`)](#23-service-layer-authservice)
  - [2.4 API layer (`api/auth.py`)](#24-api-layer-apiauthpy)
  - [2.5 Dependency injection (`api/dependencies.py`)](#25-dependency-injection-apidependenciespy)
- [3. Gap — Frontend auth UI (task 2.26)](#3-gap--frontend-auth-ui-task-226)
- [4. Gap — Automated tests (task 2.24)](#4-gap--automated-tests-task-224)
- [5. Setup ngoài code (task 2.27 manual)](#5-setup-ngoài-code-task-227-manual)
- [6. Đề xuất thứ tự implement](#6-đề-xuất-thứ-tự-implement)
- [7. Definition of Done](#7-definition-of-done)
- [8. Rủi ro và nợ kỹ thuật cần lưu ý](#8-rủi-ro-và-nợ-kỹ-thuật-cần-lưu-ý)

---

## 1. Tổng quan tiến độ Milestone 2

| # | Task | Status | Ghi chú |
|---|------|--------|---------|
| 2.1 | Thêm dependencies (`supabase`, `passlib`, `python-jose`) | ✅ | `backend/pyproject.toml` đã có. |
| 2.2 | Cập nhật `core/config.py` — JWT + Supabase + Google + URL settings | ✅ | Có đủ `google_client_id`, `google_client_secret`, `backend_url`, `frontend_url`. |
| 2.3 | Tạo Database Schema SQL | ✅ | `docs/schema.sql` (8 bảng + extensions + GRANT). |
| 2.4 | Tạo `core/constants.py` — Enums | ✅ | `UserRole`, `AuthProvider`, `AuditAction`, ... |
| 2.5 | Tạo `core/exceptions.py` | ✅ | Exception hierarchy + handler. |
| 2.6 | Tạo `db/supabase_client.py` | ✅ | Singleton `SupabaseClientManager`. |
| 2.7 | Tạo `db/repositories/base.py` | ✅ | Generic `BaseRepository[ModelT]` với CRUD chung. |
| 2.8 | Tạo Pydantic schemas | ✅ | `user`, `consent`, `audit`, `assignment`, `session`. |
| 2.9 | Tạo `db/repositories/user_repo.py` | ✅ | Có `get_by_email`, `get_by_provider_identity`, ... |
| 2.10 | Tạo `db/repositories/consent_repo.py` | ✅ | |
| 2.11 | Tạo `db/repositories/audit_repo.py` | ✅ | |
| 2.12 | Tạo `db/repositories/assignment_repo.py` | ✅ | (Bug ordering theo `assigned_at` đã fix ở PR riêng — xem PR#7.) |
| 2.13 | Tạo `services/auth_service.py` — Register, Login, JWT | 🟡 | Local register/login/JWT đủ. **Google OAuth methods còn thiếu** (xem §2.3). |
| 2.14 | Tạo `services/audit_service.py` | ✅ | |
| 2.15 | Tạo `services/consent_service.py` | ✅ | |
| 2.16 | Tạo `services/assignment_service.py` | ✅ | |
| 2.17 | Tạo `core/security.py` — JWT decode + RBAC deps | ✅ | |
| 2.18 | Tạo `api/dependencies.py` — DI wiring | 🟡 | Đủ cho local auth. **Chưa inject `Client` + `AuditService` vào `AuthService`** (cần cho Google OAuth). |
| 2.19 | Tạo `api/auth.py` — Auth endpoints | 🟡 | Có `register`, `login`, `me`. **Thiếu 3 route Google OAuth** (xem §2.4). |
| 2.20 | Tạo `api/consent.py` | ✅ | |
| 2.21 | Tạo `api/admin.py` | ✅ | |
| 2.22 | Cập nhật `main.py` — register routers | ✅ | |
| 2.23 | Cập nhật `.env.example` | ✅ | Có Google + URL keys. |
| 2.24 | Tạo tests cho auth, RBAC, consent, audit | ❌ | `backend/tests/` chỉ có `__init__.py`. |
| 2.25 | Verify — server + tests + `make check` | 🟡 | `make check` PASS (ruff + mypy strict). Server smoke test đã chạy thủ công (xem note `[3]` Phần 9). Automated test chưa có. |
| 2.26 | Cập nhật `frontend/main.py` — Google + Email/Password UI | ❌ | File hiện tại vẫn là demo "Check Backend Health" (28 dòng). |
| 2.27 | Setup Google OAuth bên ngoài code (Console + Supabase Dashboard) | ❌ | Chưa setup; không thể verify runtime của Google flow. |

**Tóm tắt:** 21/27 task **Done** + 4 task **Partial** + 3 task **Missing** (`2.24`, `2.26`, một phần của `2.13/2.18/2.19/2.27`).

---

## 2. Gap chi tiết — Google OAuth (task 2.27)

Tính năng Google OAuth được spec trong `MILESTONE2.md` xuyên suốt task 2.2, 2.4, 2.8, 2.9, 2.13, 2.18, 2.19, 2.23, 2.26, 2.27. Phần lớn **plumbing** (settings, schema, repository) đã sẵn sàng; nhưng **service + API + frontend UI** chưa được wire-up.

### 2.1 Backend Settings và environment

| Item | Status | File / dòng | Ghi chú |
|------|--------|-------------|---------|
| `settings.google_client_id` | ✅ | `backend/app/core/config.py:38` | Default `""`. |
| `settings.google_client_secret` | ✅ | `backend/app/core/config.py:39` | Default `""`. |
| `settings.backend_url` | ✅ | `backend/app/core/config.py:44` | `http://localhost:8000`. |
| `settings.frontend_url` | ✅ | `backend/app/core/config.py:45` | `http://localhost:8501`. |
| `.env.example` keys | ✅ | `.env.example:14-24` | Có đủ `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `BACKEND_URL`, `FRONTEND_URL`. |
| `.env` thực tế (root) | ❓ | Không nằm trong repo | Cần setup ngoài code (§5). |

**Kết luận §2.1:** Settings layer **đã sẵn sàng** — không cần thêm gì. Chỉ cần điền giá trị thực vào `.env` sau khi setup Google Cloud Console + Supabase Dashboard (§5).

### 2.2 Schema và Repository

| Item | Status | File / dòng | Ghi chú |
|------|--------|-------------|---------|
| Cột `auth_provider` (enum local/google) | ✅ | `docs/schema.sql` | |
| Cột `provider_user_id` | ✅ | `docs/schema.sql` | |
| Cột `avatar_url` | ✅ | `docs/schema.sql` | |
| Cột `password_hash` nullable (Google user không có password) | ✅ | `docs/schema.sql:133` | |
| Constant `AuthProvider.GOOGLE` | ✅ | `backend/app/core/constants.py` | |
| Schema `GoogleExchangeRequest` | 🟡 | `backend/app/schemas/user.py:24-27` | **Định nghĩa nhưng chưa được endpoint nào sử dụng.** |
| `UserRepository.get_by_provider_identity()` | ✅ | `backend/app/db/repositories/user_repo.py:75-92` | Đã hỗ trợ tra cứu user theo `(auth_provider, provider_user_id)`. |
| `UserRepository.create()` chấp nhận user không password | ✅ | `backend/app/db/repositories/base.py` (qua generic `BaseRepository.create`) | |
| `UserRepository.update()` để link Google account vào user local có sẵn | ✅ | `BaseRepository.update` | |

**Kết luận §2.2:** Data layer **đã sẵn sàng**. Service chỉ cần gọi `get_by_provider_identity` → `get_by_email` → `create`/`update` theo flow trong `MILESTONE2.md` Phần 2.13.

### 2.3 Service layer (`AuthService`)

**Hiện trạng** (`backend/app/services/auth_service.py:20-170`):

```text
AuthService
├── __init__(user_repo)           ✅
├── register(payload)             ✅
├── login(payload)                ✅
├── hash_password(password)       ✅
├── verify_password(plain, hash)  ✅
├── create_access_token(...)      ✅
└── _row_to_user_response(row)    ✅
```

**Thiếu (theo `MILESTONE2.md` §2.13 lines 994-1187):**

| Method | Mục đích | Phụ thuộc mới |
|--------|----------|---------------|
| `get_google_oauth_url() -> str` | Gọi `supabase.auth.sign_in_with_oauth({"provider":"google", "options":{"redirect_to": ...}})`, trả URL Google login. | Cần inject `supabase: Client` vào constructor. |
| `async handle_google_callback(code: str) -> tuple[str, str]` | (1) `supabase.auth.exchange_code_for_session({"auth_code": code})` → lấy Supabase user; (2) `get_by_provider_identity` → nếu có thì dùng; (3) `get_by_email` → nếu có thì update link Google; (4) `create` user mới với `auth_provider=google`; (5) issue app JWT; (6) audit log `USER_LOGIN` với metadata `{"method":"google"}`; (7) lưu JWT vào in-memory store với `auth_code` short-lived; (8) trả `(auth_code, user_name)`. | Cần `supabase: Client`, `audit_service: AuditService`. |
| `exchange_auth_code(auth_code: str) -> TokenResponse` | Tra `_pending_tokens[auth_code]`, pop ra (one-time), trả `TokenResponse`. Raise `UnauthorizedError` nếu code không hợp lệ hoặc đã dùng. | Class-level dict `_pending_tokens: dict[str, TokenResponse] = {}`. |

**Constructor mới cần đổi từ:**

```python
def __init__(self, user_repo: UserRepository) -> None: ...
```

**sang:**

```python
def __init__(
    self,
    user_repo: UserRepository,
    supabase: Client,
    audit_service: AuditService,
) -> None: ...
```

**Lưu ý kỹ thuật:**

- `_pending_tokens` lưu in-memory → **không scale được multi-process/multi-replica**. Đây là limitation đã được note `[3]` đề cập. Khi triển khai production cần thay bằng Redis hoặc bảng riêng `auth_codes (code, token, expires_at)` với TTL ngắn (60s).
- `secrets.token_urlsafe(32)` → đủ entropy cho one-time code.
- Mọi exception từ Supabase OAuth call cần wrap thành `InvalidCredentialsError`/`UnauthorizedError` để tránh leak provider error message ra client.
- Khi link account theo email (3b), **bắt buộc audit log** action mới `USER_ACCOUNT_LINKED` (cần thêm vào `AuditAction` enum) — note `[3]` chưa cover điểm này nhưng đáng làm.

### 2.4 API layer (`api/auth.py`)

**Hiện trạng** (`backend/app/api/auth.py:1-36`):

```text
POST /auth/register      ✅
POST /auth/login         ✅
GET  /auth/me            ✅
```

**Thiếu (theo `MILESTONE2.md` §2.19 lines 1707-1804):**

| Route | Method | Trả về | Mục đích |
|-------|--------|--------|----------|
| `/auth/google` | `GET` | `{"url": str}` | Frontend gọi để lấy Google OAuth URL, rồi redirect user. |
| `/auth/google/callback` | `GET` (query `code`) | `RedirectResponse` đến `frontend_url?auth_code=...&user_name=...` | Supabase redirect về đây sau khi user đăng nhập Google. Endpoint exchange code → JWT, lưu in-memory, redirect frontend với one-time auth_code. |
| `/auth/google/exchange` | `POST` (query hoặc body `auth_code`) | `TokenResponse` | Frontend gọi để đổi auth_code lấy JWT thật. |

**Note:** plan gốc dùng `auth_code: str = Query(...)`, nhưng schema `GoogleExchangeRequest` đã có sẵn (`backend/app/schemas/user.py:24-27`). Nên dùng body JSON (`POST` body với `GoogleExchangeRequest`) thay vì query param để đồng nhất với phong cách RESTful + tránh log auth_code vào access log của reverse proxy.

**Imports cần thêm:**

```python
from urllib.parse import urlencode
from fastapi import Query
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.schemas.user import GoogleExchangeRequest  # nếu chuyển sang body
```

### 2.5 Dependency injection (`api/dependencies.py`)

**Hiện trạng** (`backend/app/api/dependencies.py:68-72`):

```python
def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
) -> AuthService:
    return AuthService(user_repo=user_repo)
```

**Cần đổi thành:**

```python
def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    supabase: Annotated[Client, Depends(get_supabase)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> AuthService:
    return AuthService(
        user_repo=user_repo,
        supabase=supabase,
        audit_service=audit_service,
    )
```

**Lưu ý:** Tất cả test/code đang gọi `AuthService(user_repo=...)` sẽ phải update — hiện chỉ có 1 chỗ là `get_auth_service`, không có tests nên impact thấp.

---

## 3. Gap — Frontend auth UI (task 2.26)

**Hiện trạng** (`frontend/main.py`, 28 dòng):

- Chỉ có demo "Check Backend Health" (gọi `GET /api/v1/health`).
- Không có form login, không có session_state cho `access_token`, không có nút Google.

**Cần thay thế bằng** (theo `MILESTONE2.md` §2.26 lines 3109-3221, ~110 dòng):

- Block xử lý OAuth callback ở đầu file: nếu URL có `?auth_code=...` → `POST /auth/google/exchange` lấy JWT → lưu `st.session_state["access_token"]` → `st.query_params.clear()`.
- Block "Đã đăng nhập" với sidebar hiển thị tên user và nút "Đăng xuất".
- Block "Chưa đăng nhập" với 2 cột:
  - **Cột trái:** Form Email/Password → `POST /api/v1/auth/login`.
  - **Cột phải:** Nút "Đăng nhập với Google" → `GET /api/v1/auth/google` → meta-refresh redirect đến URL Google trả về.

**Lưu ý:**

- Plan gốc import `from config import settings`, nhưng repo chưa có `frontend/config.py`. Cần tạo file này hoặc đọc trực tiếp `os.environ["BACKEND_URL"]`.
- `st.query_params` (mới) thay cho `st.experimental_get_query_params` (deprecated). Cần Streamlit ≥ 1.30.
- Streamlit không tự động refresh khi session_state thay đổi → dùng `st.rerun()` sau khi set token (đã có trong plan).
- Cần handle case `BACKEND_URL` chưa chạy → hiện thông báo Vietnamese friendly thay vì crash.

---

## 4. Gap — Automated tests (task 2.24)

**Hiện trạng:**

```text
backend/tests/
└── __init__.py    # rỗng
```

**Test cần viết** (theo `MILESTONE2.md` §2.24, không trích trong file này vì plan đã chi tiết):

- `tests/conftest.py` — fixture `client` (TestClient), `db_session`, `mock_supabase` (dùng `pytest-mock` hoặc `unittest.mock`), `auth_token_factory` cho 3 role.
- `tests/test_auth.py` — register success, register duplicate email (409), login wrong password (401), `/me` không token (401), JWT expired.
- `tests/test_rbac.py` — patient không gọi được endpoint admin (403), doctor có thể gọi `/doctor/my-patients`.
- `tests/test_consent.py` — accept consent, status before/after, version mới invalidate version cũ.
- `tests/test_audit.py` — `USER_LOGIN`/`CONSENT_ACCEPTED` được ghi đúng metadata.
- `tests/test_assignment.py` — admin tạo assignment, doctor list patient của mình, patient không truy cập được assignment.

**Khuyến nghị:**

- Setup `pytest`, `pytest-asyncio`, `httpx` (async client) trong `[project.optional-dependencies] dev` của `backend/pyproject.toml`.
- Dùng Supabase **mock** ở unit test layer (mock `Client.table().select().execute()` tự build chain). Integration test thật chỉ chạy trong CI optional với `SUPABASE_TEST_URL`.
- Coverage target ban đầu: ≥ 70% với services + repositories.

---

## 5. Setup ngoài code (task 2.27 manual)

Sau khi backend code đã có 3 endpoint `/auth/google*` và frontend đã có nút Google, vẫn cần các bước manual sau **trước** khi test runtime (nguồn: `MILESTONE2.md` §2.27 lines 3233-3272):

### 5.1 Google Cloud Console

- Truy cập [Google Cloud Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials).
- Tạo (hoặc chọn) project.
- **Create Credentials → OAuth Client ID → Application type: Web application**.
- **Authorized redirect URIs**: thêm `https://<SUPABASE_PROJECT_REF>.supabase.co/auth/v1/callback`.
- Lưu Client ID + Client Secret.

### 5.2 Supabase Dashboard

- Truy cập [Supabase Dashboard → Authentication → Providers](https://supabase.com/dashboard).
- Tìm **Google** → Enable.
- Paste Client ID + Client Secret từ §5.1.
- Save.

### 5.3 Cập nhật root `.env`

```env
GOOGLE_CLIENT_ID=<paste_from_5.1>
GOOGLE_CLIENT_SECRET=<paste_from_5.1>
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:8501
```

### 5.4 Verify end-to-end

```bash
make dev-be    # terminal 1
make dev-fe    # terminal 2
```

- Mở `http://localhost:8501` → "Đăng nhập với Google" → Google login → redirect về frontend → `st.session_state["access_token"]` có giá trị.
- Trong Supabase: bảng `users` có row mới với `auth_provider='google'`, `provider_user_id` = Supabase user UUID, `password_hash IS NULL`.
- Trong bảng `audit_logs`: row mới với `action='USER_LOGIN'`, `metadata->>'method'='google'`.

---

## 6. Đề xuất thứ tự implement

Để tránh vỡ flow đang chạy (local register/login đã pass smoke test), implement theo thứ tự sau, mỗi bước là 1 PR riêng:

| Bước | Phạm vi | Estimate | Ghi chú |
|------|---------|----------|---------|
| **A** | `AuthService` thêm 3 method Google + đổi constructor; `dependencies.py` inject thêm `supabase` + `audit_service`. | 0.5 ngày | Không touch route — backend cũ vẫn pass smoke test. |
| **B** | `api/auth.py` thêm 3 route `/google`, `/google/callback`, `/google/exchange`; thêm action mới `USER_ACCOUNT_LINKED` vào `AuditAction`. | 0.5 ngày | Sau bước này, có thể test bằng `curl` (kèm fake Supabase response). |
| **C** | Setup §5 (Google Cloud + Supabase Dashboard + `.env`). | 0.5 ngày | Manual — cần account quyền admin. |
| **D** | Frontend `frontend/main.py` UI Email/Password + Google. | 0.5 ngày | Test `make dev-fe` end-to-end. |
| **E** | `tests/` — pytest fixtures + test cases cho `register`, `login`, `me`, `accept_consent`, RBAC, assignment, **không test Google call thật** (mock Supabase). | 1.5 ngày | Bắt buộc trước khi sang Milestone 3. |

**Total estimate:** ~3.5 ngày người + setup manual.

---

## 7. Definition of Done

Milestone 2 chỉ được coi là **fully done** khi tất cả check sau đây pass:

- [ ] `make check` PASS (ruff + mypy strict).
- [ ] `pytest backend/tests/ -v` PASS với coverage ≥ 70% trên `backend/app/services/` + `backend/app/db/repositories/`.
- [ ] Smoke test bằng `curl` cho 6 flow:
  - [ ] `POST /auth/register` → 201 + `UserResponse`.
  - [ ] `POST /auth/login` → 200 + `TokenResponse`.
  - [ ] `GET /auth/me` (Bearer JWT) → 200 + `CurrentUserClaims`.
  - [ ] `GET /auth/google` → 200 + `{"url": "https://..."}`.
  - [ ] `GET /auth/google/callback?code=<from_supabase>` → 302 redirect đến `frontend_url?auth_code=...&user_name=...`.
  - [ ] `POST /auth/google/exchange` (auth_code từ callback) → 200 + `TokenResponse`.
- [ ] Manual end-to-end qua frontend Streamlit:
  - [ ] Login bằng Email/Password thành công, sidebar hiện tên user.
  - [ ] Login bằng Google thành công, user mới được tạo trong `users` với `auth_provider='google'`.
  - [ ] Logout → quay lại form login.
- [ ] Tất cả 27 task trong `MILESTONE2.md` đã chuyển từ ⬜ → ✅.
- [ ] Cập nhật note `[3]database_auth_implementation_process.md` Phần 18 (Next implementation direction) với kết quả thực tế của Google OAuth.

---

## 8. Rủi ro và nợ kỹ thuật cần lưu ý

| Rủi ro | Mức độ | Giảm thiểu |
|--------|--------|------------|
| `_pending_tokens` in-memory không scale multi-process | Trung bình | Khi deploy production: thay bằng Redis (TTL 60s) hoặc bảng `auth_codes`. Document trong note `[3]`. |
| Auth code lộ qua URL query string `?auth_code=...&user_name=...` | Thấp | Đã được mitigate bằng one-time code (vs. JWT trực tiếp). Vẫn cần HTTPS cho `frontend_url` trong production. |
| Link account theo email mở cửa cho **account takeover** nếu Google trả email mà attacker đã register local | Cao | Hiện plan link luôn nếu trùng email → **không an toàn**. Nên thêm bước **xác thực sở hữu email** (gửi confirmation hoặc bắt user login local trước khi link). Đây là gap an ninh đáng cảnh báo. |
| Supabase `service_role` key được dùng cho tất cả query → bypass RLS | Trung bình | RBAC enforcement nằm ở application layer (RBAC dependencies). Cần test kỹ ở task 2.24 và bổ sung RLS policy ở Milestone sau. |
| Không có test nào cho path Google OAuth thật (chỉ test logic xử lý callback với mock) | Trung bình | Chấp nhận giới hạn. End-to-end Google flow chỉ test thủ công. Có thể add Playwright e2e ở Milestone sau. |
| Frontend dùng `st.session_state` → token mất khi refresh tab | Thấp | Acceptable cho MVP. Nâng cấp lưu vào browser storage ở milestone UI/UX sau. |
| `AuditAction` chưa có `USER_ACCOUNT_LINKED` | Thấp | Thêm khi implement bước A (cần thiết cho audit khi link Google vào local account). |

---

## Phụ lục — Các file dự kiến đụng đến

### Sẽ sửa

```text
backend/app/core/constants.py                # thêm AuditAction.USER_ACCOUNT_LINKED
backend/app/services/auth_service.py         # thêm 3 method + đổi __init__
backend/app/api/auth.py                      # thêm 3 route google
backend/app/api/dependencies.py              # inject supabase + audit_service vào get_auth_service
frontend/main.py                             # thay thế bằng UI Email/Password + Google
backend/pyproject.toml                       # thêm dev deps: pytest, pytest-asyncio, httpx
docs/.plan/MILESTONE2.md                     # cập nhật progress tracker ⬜ → ✅
```

### Sẽ thêm mới

```text
backend/tests/conftest.py
backend/tests/test_auth.py
backend/tests/test_rbac.py
backend/tests/test_consent.py
backend/tests/test_audit.py
backend/tests/test_assignment.py
frontend/config.py                           # nếu chọn dùng pydantic-settings ở frontend
```

### Không đụng (đã sẵn sàng)

```text
backend/app/core/config.py                   # đã có Google + URL settings
backend/app/db/repositories/user_repo.py     # đã có get_by_provider_identity
backend/app/schemas/user.py                  # đã có GoogleExchangeRequest
docs/schema.sql                              # đã có cột auth_provider, provider_user_id, avatar_url
.env.example                                 # đã có Google + URL keys
```
