# Plan: Hoàn thiện hạn chế code-quality + automated tests + sync note [3]

> **Phạm vi:** Vá các điểm trong audit code quality + viết test suite cho task 2.24, sau đó cập nhật `[3]database_auth_implementation_process.md` cho đồng bộ.
>
> **Cam kết:**
>
> - Không thay đổi behavior của API hiện tại (register/login/me/consent/admin) — mọi route + payload giữ nguyên.
> - Không touch Google OAuth implementation (đã tách thành plan riêng trong gap report PR3).
> - Không sửa `docs/schema.sql` (các cột đã đủ — đặc biệt `audit_logs.role` đã sẵn sàng cho thay đổi).
> - Không sửa `[2]E2E_database_design_and_development.md` (note thiết kế DB không liên quan).

---

## 0. Tóm tắt 3 PR sẽ tạo

| # | Title | Phạm vi | Risk |
|---|-------|---------|------|
| **PR4** | `refactor(milestone2): code quality fixes — DRY + decoupling + audit role` | 7 file `backend/app` | 🟡 yellow (đụng layer DB + auth) |
| **PR5** | `test(milestone2): add pytest suite for auth, RBAC, consent, audit, assignment` | `backend/tests/*`, `backend/pyproject.toml` | 🟢 green (chỉ thêm test) |
| **PR6** | `docs(notes): sync [3] implementation notes with code-quality refactor` | `docs/_notes/[3]database_auth_implementation_process.md` | 🟢 green (docs only) |

Thứ tự thực thi tuần tự (PR5 cần PR4 merged để test code mới; PR6 cần PR4+PR5 merged để note ghi đúng hiện trạng).

---

## 1. PR4 — Code-quality refactor

### 1.1 Symbols sẽ thay đổi

| File | Symbol | Action | Lý do |
|------|--------|--------|-------|
| `backend/app/db/repositories/base.py` | `BaseRepository._rows(self, data: object) -> list[JSONRow]` | **THÊM MỚI** | Đẩy helper chung lên base, fix DRY violation. |
| `backend/app/db/repositories/user_repo.py` | `UserRepository._rows` | **XÓA** | Đã có ở base. |
| `backend/app/db/repositories/consent_repo.py` | `ConsentRepository._rows` | **XÓA** | Đã có ở base. |
| `backend/app/db/repositories/audit_repo.py` | `AuditRepository._rows` | **XÓA** | Đã có ở base. |
| `backend/app/db/repositories/assignment_repo.py` | `AssignmentRepository._rows` | **XÓA** | Đã có ở base. |
| `backend/app/services/auth_service.py` | `AuthService._row_to_user_response` | **REWRITE** | Dùng `UserResponse.model_validate(dict(row))` thay vì 4 helper tay. |
| `backend/app/services/auth_service.py` | `AuthService._get_required_string/_optional_string/_required_bool/_required_datetime` | **XÓA** | Không còn cần — Pydantic validate row trực tiếp. |
| `backend/app/services/auth_service.py` | `AuthService.login` (chỉ logic đọc `password_hash` + `is_active`) | **TINH GỌN** | Đọc `password_hash` + `is_active` qua một helper nhỏ trả `DatabaseError` (đúng domain) thay vì `UnauthorizedError`. |
| `backend/app/api/dependencies.py` | `require_current_doctor_or_admin` | **REWRITE** | Gọi lại `require_roles({DOCTOR, ADMIN})` từ `core/security.py`. Move import `ForbiddenError` lên top (chỉ giữ nếu vẫn cần — sau refactor sẽ KHÔNG cần). |
| `backend/app/services/audit_service.py` | `AuditService.log_event` | **THÊM PARAM `role`** | Đồng nhất với schema `audit_logs.role` + `AuditLogCreate.role` đã có. |
| `backend/app/services/consent_service.py` | `ConsentService.accept_consent` | **PASS `role`** | Truyền `role` vào `log_event`. |
| `backend/app/services/assignment_service.py` | `AssignmentService.create_assignment` + `deactivate_assignment` | **PASS `role`** | Truyền `role` vào `log_event`. |
| `backend/app/api/consent.py` | `accept_consent` route | **TRUYỀN role** | Lấy `current_user.role.value` truyền xuống service. |
| `backend/app/api/admin.py` | `create_assignment` + `deactivate_assignment` route | **TRUYỀN role** | Lấy `current_user.role.value` truyền xuống service. |

### 1.2 Signatures chi tiết

**`BaseRepository._rows`** — file `base.py`:

```python
# THÊM MỚI sau _first_row (line ~37)
def _rows(self, data: object) -> list[JSONRow]:
    """Convert a Supabase response payload into a list of JSON rows.

    Returns an empty list when the payload is missing or malformed,
    so callers can iterate safely without nil-checks.
    """
    if not isinstance(data, list):
        return []

    rows: list[JSONRow] = []
    for item in data:
        if isinstance(item, dict):
            rows.append(cast(JSONRow, item))

    return rows
```

Sau khi thêm: 4 file con (`user_repo`, `consent_repo`, `audit_repo`, `assignment_repo`) **xóa method `_rows` của chính nó**, nhưng vẫn dùng `self._rows(result.data)` ở các method `list_*` — vì method được kế thừa từ `BaseRepository`. Không cần đổi callsite.

**`AuthService._row_to_user_response`** — file `auth_service.py`:

```python
# TRƯỚC (lines 110-132): viết tay 4 helper parse JSONRow
def _row_to_user_response(self, row: JSONRow) -> UserResponse:
    return UserResponse(
        id=self._get_required_string(row=row, field_name="id"),
        ...
    )

# SAU: dùng Pydantic
def _row_to_user_response(self, row: JSONRow) -> UserResponse:
    """Convert a raw users row into a public user response model."""
    return UserResponse.model_validate(dict(row))
```

**`AuthService.login`** — chỉ đoạn đọc `password_hash` + `is_active`:

```python
# TRƯỚC (line 51-60): qua _get_required_string + _get_required_bool
password_hash = self._get_required_string(
    row=user_row,
    field_name="password_hash",
)
if not self.verify_password(payload.password, password_hash):
    raise InvalidCredentialsError()

is_active = self._get_required_bool(row=user_row, field_name="is_active")
if not is_active:
    raise UnauthorizedError("User account is inactive")

# SAU: 2 nhánh rõ ràng — validate là DatabaseError, business invalid là Unauthorized/InvalidCredentials
password_hash = user_row.get("password_hash")
if not isinstance(password_hash, str) or not password_hash:
    raise DatabaseError("User row missing password_hash")

if not self.verify_password(payload.password, password_hash):
    raise InvalidCredentialsError()

is_active = user_row.get("is_active")
if not isinstance(is_active, bool):
    raise DatabaseError("User row missing is_active")
if not is_active:
    raise UnauthorizedError("User account is inactive")
```

Lý do giữ `password_hash` truy cập trực tiếp dict (không qua Pydantic): `UserResponse` cố ý KHÔNG có field `password_hash` (security — không leak qua response). Dùng schema riêng cho login row sẽ over-engineer cho chỉ 1 callsite. Đây là phương án minimum viable.

**`require_current_doctor_or_admin`** — file `dependencies.py`:

```python
# TRƯỚC (lines 133-150): tay viết logic + import ForbiddenError trong hàm
def require_current_doctor_or_admin(
    current_user: Annotated[CurrentUserClaims, Depends(get_current_user)],
) -> CurrentUserClaims:
    if current_user.role not in {UserRole.DOCTOR, UserRole.ADMIN}:
        allowed_roles = ", ".join(...)
        from app.core.exceptions import ForbiddenError  # ← vi phạm "imports at top"
        raise ForbiddenError(f"Requires one of these roles: {allowed_roles}")
    return current_user

# SAU: tận dụng require_roles có sẵn
def require_current_doctor_or_admin(
    current_user: Annotated[CurrentUserClaims, Depends(get_current_user)],
) -> CurrentUserClaims:
    """Require current user to be a doctor or admin."""
    require_roles(current_user, {UserRole.DOCTOR, UserRole.ADMIN})
    return current_user
```

Đồng thời: thêm `require_roles` vào import list ở đầu file (line 10):

```python
from app.core.security import (
    CurrentUserClaims,
    decode_access_token,
    require_admin,
    require_doctor,
    require_patient,
    require_roles,  # ← thêm
)
```

Và xóa import `ForbiddenError` bên trong hàm (không còn cần).

**`AuditService.log_event`** — file `audit_service.py`:

```python
# TRƯỚC
async def log_event(
    self,
    *,
    user_id: str | None,
    action: AuditAction,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> None: ...

# SAU: thêm role
async def log_event(
    self,
    *,
    user_id: str | None,
    action: AuditAction,
    role: str | None = None,  # ← THÊM (default None để backward compatible)
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> None:
    ...
    data: JSONRow = {
        "user_id": user_id,
        "role": role,  # ← THÊM
        "action": action.value,
        ...
    }
```

Schema `audit_logs.role` constraint chấp nhận `'patient'`, `'doctor'`, `'admin'`, `'system'`, hoặc `NULL` (`docs/schema.sql:394-398`). `UserRole(str, Enum)` đã trả 3 giá trị đầu khi `.value`. `None` cho event không gắn user (system event).

**Callers update:**

```python
# consent_service.accept_consent — thêm role param
async def accept_consent(
    self,
    user_id: str,
    payload: ConsentAcceptRequest,
    role: str,                       # ← THÊM (required, lấy từ route)
    ip_address: str | None = None,
) -> ConsentResponse:
    ...
    await self._audit_service.log_event(
        user_id=user_id,
        role=role,                   # ← TRUYỀN
        action=AuditAction.CONSENT_ACCEPTED,
        ...
    )

# assignment_service.create_assignment / deactivate_assignment — thêm role param
async def create_assignment(
    self,
    payload: AssignmentCreateRequest,
    assigned_by: str,
    role: str,                       # ← THÊM
    ip_address: str | None = None,
) -> AssignmentResponse: ...
```

Và route (`api/consent.py`, `api/admin.py`) truyền `current_user.role.value`.

### 1.3 Logical order of changes (dependency order)

1. `base.py`: thêm `_rows`.
2. `user_repo.py`, `consent_repo.py`, `audit_repo.py`, `assignment_repo.py`: xóa `_rows` riêng + `cast`/`Mapping` imports không còn dùng.
3. `auth_service.py`: rewrite `_row_to_user_response`, xóa 4 helper, sửa `login`.
4. `core/security.py`: không thay đổi (`require_roles` đã đúng signature).
5. `api/dependencies.py`: refactor `require_current_doctor_or_admin`, sửa import.
6. `services/audit_service.py`: thêm `role` param.
7. `services/consent_service.py`, `services/assignment_service.py`: thêm `role` param + truyền xuống.
8. `api/consent.py`, `api/admin.py`: truyền `current_user.role.value` vào service.

### 1.4 Verification cho PR4

- `make check` PASS (ruff + mypy strict).
- `git diff --stat` chỉ chạm 11 file backend.
- API contract (OpenAPI) **không đổi** — chỉ refactor internal.

---

## 2. PR5 — Automated tests (task 2.24)

### 2.1 Cấu trúc thư mục

```text
backend/tests/
├── __init__.py                  # giữ nguyên
├── conftest.py                  # MỚI — fixtures shared
├── fakes/
│   ├── __init__.py              # MỚI
│   └── fake_supabase.py         # MỚI — in-memory Supabase chain stub
├── test_health.py               # MỚI — smoke endpoint
├── test_security.py             # MỚI — JWT decode + require_roles unit
├── test_auth_service.py         # MỚI — register/login/hash/JWT business logic
├── test_auth_api.py             # MỚI — POST /register, /login, GET /me
├── test_rbac.py                 # MỚI — admin/doctor/patient guards
├── test_consent.py              # MỚI — accept + status
├── test_audit.py                # MỚI — log_event sanitize + role
└── test_assignment.py           # MỚI — create, deactivate, list, ensure_doctor_can_access_patient
```

### 2.2 `conftest.py` — fixtures dùng chung

```python
# Tóm tắt — KHÔNG full code, chỉ signature
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies import (
    get_supabase, get_user_repo, get_consent_repo,
    get_audit_repo, get_assignment_repo,
    get_current_user,
)
from app.core.security import CurrentUserClaims
from app.core.constants import UserRole
from tests.fakes.fake_supabase import FakeSupabase

@pytest.fixture
def fake_supabase() -> FakeSupabase: ...

@pytest.fixture
def client(fake_supabase: FakeSupabase) -> TestClient:
    """TestClient with overridden get_supabase → FakeSupabase."""

@pytest.fixture
def admin_user() -> CurrentUserClaims: ...
@pytest.fixture
def doctor_user() -> CurrentUserClaims: ...
@pytest.fixture
def patient_user() -> CurrentUserClaims: ...

@pytest.fixture
def auth_as(client: TestClient):
    """Returns a callable: auth_as(role) overrides get_current_user."""
```

### 2.3 `fakes/fake_supabase.py` — Supabase chain stub

Mục đích: replicate chain `supabase.table(...).select(...).eq(...).execute()` trong memory để test không cần Supabase thật. Keep it minimal — chỉ implement subset thực sự dùng (`select`, `insert`, `update`, `delete`, `eq`, `order`, `limit`, `execute`).

```python
# fakes/fake_supabase.py — signature only
class FakeQuery:
    def __init__(self, table: "FakeTable", op: str) -> None: ...
    def select(self, *cols: str) -> "FakeQuery": ...
    def insert(self, data: dict | list[dict]) -> "FakeQuery": ...
    def update(self, data: dict) -> "FakeQuery": ...
    def delete(self) -> "FakeQuery": ...
    def eq(self, col: str, value: object) -> "FakeQuery": ...
    def order(self, col: str, desc: bool = False) -> "FakeQuery": ...
    def limit(self, n: int) -> "FakeQuery": ...
    def execute(self) -> "FakeResult": ...

class FakeResult:
    data: list[dict]

class FakeTable:
    rows: list[dict]
    def __init__(self, name: str) -> None: ...

class FakeSupabase:
    def __init__(self) -> None:
        self._tables: dict[str, FakeTable] = {}

    def table(self, name: str) -> FakeQuery: ...

    # helper for tests
    def seed(self, table: str, rows: list[dict]) -> None: ...
```

Đủ độ phong phú để cover business logic (filter `eq`, sort `order`, paginate `limit`). Không reproduce constraint check, RLS, hay function — đó là DB integration test ngoài scope MVP test.

### 2.4 Test cases — cover matrix

| File | Test name | Verify |
|------|-----------|--------|
| `test_health.py` | `test_health_returns_ok` | `GET /api/v1/health` → 200 + body. |
| `test_security.py` | `test_decode_access_token_valid` | JWT hợp lệ → `CurrentUserClaims`. |
| `test_security.py` | `test_decode_access_token_expired_raises_unauthorized` | exp quá hạn → `UnauthorizedError`. |
| `test_security.py` | `test_decode_access_token_invalid_role_raises_unauthorized` | role không nằm trong enum → raise. |
| `test_security.py` | `test_require_roles_allows_member` | role nằm trong set → no raise. |
| `test_security.py` | `test_require_roles_rejects_outsider` | role không nằm trong set → `ForbiddenError`. |
| `test_auth_service.py` | `test_register_creates_user_with_local_provider` | `register()` trả `UserResponse`, FakeSupabase có 1 row. |
| `test_auth_service.py` | `test_register_duplicate_email_raises_already_exists` | seed user → register → `AlreadyExistsError`. |
| `test_auth_service.py` | `test_login_returns_token_with_correct_claims` | login → JWT payload có `sub/email/role/exp`. |
| `test_auth_service.py` | `test_login_wrong_password_raises_invalid_credentials` | sai password → `InvalidCredentialsError`. |
| `test_auth_service.py` | `test_login_inactive_user_raises_unauthorized` | `is_active=False` → `UnauthorizedError`. |
| `test_auth_service.py` | `test_login_missing_password_hash_raises_database_error` | seed row thiếu `password_hash` → `DatabaseError`. (verify fix mới ở PR4) |
| `test_auth_api.py` | `test_register_endpoint_returns_201` | `POST /auth/register` → 200 (note: code hiện trả default 200, mình giữ behavior — KHÔNG đổi). |
| `test_auth_api.py` | `test_login_endpoint_returns_token` | `POST /auth/login` → 200 + `access_token`. |
| `test_auth_api.py` | `test_me_without_token_returns_403` | `GET /auth/me` không bearer → 403 (HTTPBearer auto_error). |
| `test_auth_api.py` | `test_me_with_invalid_token_returns_401` | bearer giả → 401. |
| `test_rbac.py` | `test_patient_cannot_access_admin_endpoint` | patient JWT → `POST /admin/assignments` → 403. |
| `test_rbac.py` | `test_doctor_cannot_create_assignment` | doctor JWT → `POST /admin/assignments` → 403. |
| `test_rbac.py` | `test_admin_can_create_assignment` | admin JWT → 200 + body. |
| `test_rbac.py` | `test_doctor_or_admin_route_accepts_both` | (nếu có route nào dùng `require_current_doctor_or_admin` — hiện chưa có route nào dùng, sẽ unit test thẳng dependency). |
| `test_consent.py` | `test_accept_consent_creates_record_and_audit` | `POST /consent/accept` → record + audit log với `role=patient`. |
| `test_consent.py` | `test_consent_status_before_acceptance` | seed user, không seed consent → `has_valid_consent=False`. |
| `test_consent.py` | `test_consent_status_after_acceptance_current_version` | seed accept v1 → `has_valid_consent=True`. |
| `test_consent.py` | `test_consent_status_old_version_does_not_satisfy` | seed v0 → `has_valid_consent=False, latest_accepted_policy_version='v0'`. |
| `test_audit.py` | `test_log_event_includes_role` | gọi `log_event(role='patient', ...)` → row insert có `role='patient'`. |
| `test_audit.py` | `test_log_event_role_none_when_not_provided` | không pass role → row có `role=None`. |
| `test_audit.py` | `test_sanitize_metadata_drops_unsafe_types` | metadata `{"obj": SomeClass()}` → string repr. |
| `test_assignment.py` | `test_create_assignment_persists_and_audits` | admin tạo → row + audit log. |
| `test_assignment.py` | `test_create_assignment_idempotent_on_existing_active` | tạo trùng → trả assignment cũ, không insert mới. |
| `test_assignment.py` | `test_create_assignment_rejects_non_doctor_doctor_id` | doctor_id thực ra là patient role → `ForbiddenError`. |
| `test_assignment.py` | `test_create_assignment_rejects_non_patient_patient_id` | patient_id thực ra là doctor role → `ForbiddenError`. |
| `test_assignment.py` | `test_deactivate_assignment_marks_inactive_and_audits` | deactivate → `is_active=False` + audit log. |
| `test_assignment.py` | `test_deactivate_unknown_id_raises_not_found` | id không tồn tại → `NotFoundError`. |
| `test_assignment.py` | `test_ensure_doctor_can_access_patient_passes_when_assigned` | seed assignment → no raise. |
| `test_assignment.py` | `test_ensure_doctor_can_access_patient_fails_when_not_assigned` | không seed → `ForbiddenError`. |
| `test_assignment.py` | `test_list_my_patients_returns_only_active` | seed 2 active + 1 deactive → trả 2. |

**Total: ~30 test cases.**

### 2.5 Dependencies cần thêm

`backend/pyproject.toml`:

```toml
[dependency-groups]
dev = [
    "pytest>=9.0.3",          # đã có
    "pytest-asyncio>=1.3.0",  # đã có
    "httpx>=0.28.0",          # ← THÊM (TestClient của FastAPI dùng httpx)
]
```

(Nếu `pyproject.toml` đã có `httpx` qua transitive — kiểm tra lại; nếu có thì bỏ qua.)

### 2.6 Verification cho PR5

- `uv run pytest -v` → all green (≥ 30 test pass).
- `uv run pytest --cov=backend/app --cov-report=term-missing` → coverage ≥ 70% trên `backend/app/services/` + `backend/app/db/repositories/` (target — không gate hard).
- `make check` PASS (test files type-check qua mypy strict).

---

## 3. PR6 — Sync `[3]database_auth_implementation_process.md`

### 3.1 Phần sẽ cập nhật

| Phần trong note | Action | Nội dung mới |
|-----------------|--------|--------------|
| **Phần 5** (lỗi đã gặp + cách fix) | THÊM 1 mục con `5.X` | Liệt kê 4 vấn đề mới đã fix ở PR4: (1) DRY `_rows`; (2) parse helper bị thay bằng `model_validate`; (3) `require_current_doctor_or_admin` dùng `require_roles`; (4) `audit_service.log_event` nhận `role`. |
| **Phần 11** (bảng "Vấn đề → Cách xử lý") | THÊM 4 dòng | Map từng vấn đề → file + commit hash PR4. |
| **Phần 13** (file map) | UPDATE | Đánh dấu file nào còn `_rows` private (không còn) + audit_service signature mới. |
| **Phần 14** (Task → Status) | UPDATE | 2.24 ⬜ → ✅ (sau PR5 merged). 2.25 vẫn ✅. Note "code-quality refactor done" cho 2.13/2.14/2.18. |
| **Phần 17 (mới)** hoặc cuối Phần 15 | THÊM | Mục "Test suite — overview" liệt kê 30 test cases dạng bullet (không full code, chỉ tên + verify). |
| **Phần 18 (Next implementation direction)** | UPDATE | Còn lại: Google OAuth (2.27) + frontend UI (2.26). Tham chiếu đến `MILESTONE2_GAP_REPORT.md`. |

### 3.2 Cam kết khi sync

- Giữ phong cách viết tiếng Việt, structured, "Mục đích / Vì sao / Lỗi / Flow / Bài học".
- KHÔNG xóa nội dung gốc. Chỉ thêm mục mới + đánh dấu status trong bảng.
- KHÔNG dịch sang tiếng Anh.
- KHÔNG thay đổi cấu trúc 18 phần đã có.

### 3.3 Verification cho PR6

- Diff chỉ chạm `[3]database_auth_implementation_process.md`.
- ToC sync với heading mới (nếu có thêm sub-section).
- `git diff --stat` < 200 dòng thay đổi.

---

## 4. Câu hỏi cần xác nhận trước khi implement

1. **DRY `_rows`**: bạn muốn dùng phương án **đẩy lên BaseRepository** (đề xuất chính), hay tách helper module riêng (`db/repositories/_helpers.py`)? Khuyến nghị: lên base (đỡ thêm import).
2. **`AuthService.login` đọc `password_hash`**: bạn muốn dùng **dict access trực tiếp + `DatabaseError`** (đề xuất chính, MVP), hay tạo schema riêng `LoginRow(BaseModel)` để Pydantic validate (sạch hơn nhưng cho 1 callsite)? Khuyến nghị: phương án 1.
3. **`audit_service.log_event` thêm `role`**: bạn muốn `role: str | None` (đề xuất chính, đơn giản), hay `role: UserRole | str | None` (chấp nhận enum hoặc string)? Khuyến nghị: `str | None` để khớp với `AuditLogCreate.role` schema sẵn có.
4. **Ngưỡng test**: 30 test case như §2.4 OK chưa, hay bạn muốn thêm test cho path nào? (Hiện chưa có integration test với Supabase thật — đó sẽ là milestone CI sau.)
5. **Mixed-language error string**: tôi không tìm thấy ký tự tiếng Việt trong `backend/app/`. Có thể bạn đang nhớ đoạn nào cụ thể? Nếu có file/line, tôi sẽ thêm vào scope; nếu không, mình bỏ điểm này khỏi PR4 và ghi rõ trong note.

---

## 5. Estimate

| PR | Thời gian |
|----|-----------|
| PR4 (refactor) | ~1.5h |
| PR5 (test) | ~3-4h (chính là viết FakeSupabase + 30 test) |
| PR6 (sync note) | ~30min |

**Tổng:** ~5-6h. Sẽ tạo PR tuần tự, đợi merge xong PR4 mới chạy PR5 (vì test reflect code đã refactor).
