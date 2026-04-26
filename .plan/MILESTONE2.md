# Milestone 2 - Data and Auth Foundation

## Mục tiêu
Hoàn thành Milestone 2 (Data & Auth Foundation) — thiết lập database schema, Supabase client, Repository pattern, Authentication (JWT + Google OAuth), RBAC, Consent tracking, và Audit logging. Sau milestone này, hệ thống có thể register/login users (bao gồm đăng nhập/đăng ký bằng tài khoản Google thông qua Supabase built-in OAuth provider), phân quyền theo role, quản lý doctor-patient assignments, ghi consent, và audit log.

## Bảng theo dõi tiến độ

Đặt bảng này ở đầu file hoặc issue để track:


## Milestone 2 — Progress Tracker

| # | Task | Status |
|---|------|--------|
| 2.1 | Thêm dependencies (supabase, passlib, python-jose) | ⬜ |
| 2.2 | Cập nhật `core/config.py` — thêm JWT + Supabase settings | ⬜ |
| 2.3 | Tạo Database Schema SQL | ⬜ |
| 2.4 | Tạo `core/constants.py` — Enums (UserRole, SessionStatus, etc.) | ⬜ |
| 2.5 | Tạo `core/exceptions.py` — Custom exception hierarchy | ⬜ |
| 2.6 | Tạo `db/supabase_client.py` — Singleton Supabase connection | ⬜ |
| 2.7 | Tạo `db/repositories/base.py` — Abstract Base Repository | ⬜ |
| 2.8 | Tạo Pydantic schemas (user, consent, audit, session) | ⬜ |
| 2.9 | Tạo `db/repositories/user_repo.py` | ⬜ |
| 2.10 | Tạo `db/repositories/consent_repo.py` | ⬜ |
| 2.11 | Tạo `db/repositories/audit_repo.py` | ⬜ |
| 2.12 | Tạo `db/repositories/assignment_repo.py` | ⬜ |
| 2.13 | Tạo `services/auth_service.py` — Register, Login, JWT | ⬜ |
| 2.14 | Tạo `services/audit_service.py` — Audit logging | ⬜ |
| 2.15 | Tạo `services/consent_service.py` — Consent tracking | ⬜ |
| 2.16 | Tạo `services/assignment_service.py` — Doctor-patient assignments | ⬜ |
| 2.17 | Tạo `core/security.py` — JWT utils + RBAC dependencies | ⬜ |
| 2.18 | Tạo `api/dependencies.py` — FastAPI DI wiring | ⬜ |
| 2.19 | Tạo `api/auth.py` — Auth endpoints | ⬜ |
| 2.20 | Tạo `api/consent.py` — Consent endpoints | ⬜ |
| 2.21 | Tạo `api/admin.py` — Admin + Assignment endpoints | ⬜ |
| 2.22 | Cập nhật `main.py` — Register routers + exception handlers | ⬜ |
| 2.23 | Cập nhật `.env.example` | ⬜ |
| 2.24 | Tạo tests cho auth, RBAC, consent, audit | ⬜ |
| 2.25 | Verify — chạy server + chạy tests + make check | ⬜ |
| 2.26 | Cập nhật `frontend/main.py` — Google OAuth + Email/Password login UI | ⬜ |
| 2.27 | Setup Google OAuth bên ngoài code (Google Cloud Console + Supabase Dashboard) | ⬜ |


Khi hoàn thành mỗi task, đổi ⬜ thành ✅.

> **Lưu ý:** Tính năng **Google OAuth** (đăng nhập/đăng ký bằng tài khoản Google) được tích hợp xuyên suốt các task 2.2, 2.3, 2.4, 2.8, 2.9, 2.13, 2.18, 2.19, 2.23, 2.26, 2.27. Flow: Frontend → Backend generate OAuth URL → Supabase → Google → Supabase callback → Backend callback endpoint → Issue app JWT → Redirect to Frontend.

---

## Các bước thực hiện chi tiết

### 2.1 Thêm dependencies

Chạy tại root:
```bash
uv add --package backend "supabase>=2.15.0" "python-jose[cryptography]>=3.4.0" "passlib[bcrypt]>=1.7.4"
```

Giải thích:
- `supabase` — Supabase Python client để kết nối Supabase/Postgres
- `python-jose[cryptography]` — Tạo và verify JWT tokens
- `passlib[bcrypt]` — Hash passwords bằng bcrypt

---

### 2.2 Cập nhật `backend/app/core/config.py`

Thêm các settings mới cho JWT và Supabase auth vào class `Settings` đã có từ Milestone 1:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "Mental Health AI Platform"
    app_version: str = "0.1.0"
    debug: bool = False

    # LLM
    openai_api_key: str = ""

    # Vector DB
    qdrant_url: str = "http://localhost:6333"

    # Application DB
    supabase_url: str = ""
    supabase_key: str = ""

    # JWT Auth (MỚI)
    jwt_secret_key: str = ""  # Generate with: openssl rand -hex 32
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    # Google OAuth (MỚI)
    google_client_id: str = ""
    google_client_secret: str = ""
    frontend_url: str = "http://localhost:8501"
    backend_url: str = "http://localhost:8000"

    # Consent (MỚI)
    current_consent_policy_version: str = "1.0"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
```

---

### 2.3 Tạo Database Schema SQL

Tạo file `docs/schema.sql` chứa toàn bộ SQL để tạo bảng trong Supabase/Postgres. Đây là file reference — bạn sẽ chạy SQL này trong Supabase SQL Editor hoặc psql.

Các bảng cần tạo (dựa trên SRDS Section 9.1 — Core Data Entities):

```sql
-- docs/schema.sql
-- Mental Health AI Platform — Database Schema
-- Run this in Supabase SQL Editor or psql

-- 1. Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- NULLABLE: Google OAuth users không có password
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('patient', 'doctor', 'admin')),
    auth_provider VARCHAR(50) NOT NULL DEFAULT 'local',  -- 'local' hoặc 'google'
    provider_user_id VARCHAR(255),  -- Google/Supabase user ID
    avatar_url TEXT,  -- Google profile picture URL
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Doctor-Patient Assignments
CREATE TABLE doctor_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doctor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assigned_by UUID NOT NULL REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(doctor_id, patient_id)
);

-- 4. Consent Records
CREATE TABLE consent_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    policy_version VARCHAR(20) NOT NULL,
    accepted BOOLEAN NOT NULL DEFAULT TRUE,
    accepted_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Chat Sessions
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'closed', 'timeout')),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

-- 6. Chat Messages
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    safety_flag BOOLEAN DEFAULT FALSE,
    safety_severity VARCHAR(20) DEFAULT 'none',
    trace_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Clinical Profiles (doctor-facing, generated post-session)
CREATE TABLE clinical_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    symptoms JSONB DEFAULT '[]',
    risk_markers JSONB DEFAULT '[]',
    evidence_snippets JSONB DEFAULT '[]',
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Stress / Risk Scores
CREATE TABLE stress_risk_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    evidence JSONB DEFAULT '{}',
    calculated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. Audit Logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    role VARCHAR(20),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_provider ON users(auth_provider, provider_user_id);
CREATE INDEX idx_doctor_assignments_doctor ON doctor_assignments(doctor_id) WHERE is_active = TRUE;
CREATE INDEX idx_doctor_assignments_patient ON doctor_assignments(patient_id) WHERE is_active = TRUE;
CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_status ON chat_sessions(status);
CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX idx_clinical_profiles_patient ON clinical_profiles(patient_id);
CREATE INDEX idx_stress_scores_patient ON stress_risk_scores(patient_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX idx_consent_records_user ON consent_records(user_id);
```

Sau khi tạo file, chạy SQL này trong Supabase Dashboard → SQL Editor, hoặc:
```bash
psql $DATABASE_URL -f docs/schema.sql
```

---

### 2.4 Tạo `backend/app/core/constants.py`

Định nghĩa tất cả Enums dùng chung trong project:

```python
# backend/app/core/constants.py
from enum import Enum


class AuthProvider(str, Enum):
    """Authentication provider types."""
    LOCAL = "local"
    GOOGLE = "google"


class UserRole(str, Enum):
    """User roles in the system."""
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class SessionStatus(str, Enum):
    """Chat session statuses."""
    ACTIVE = "active"
    CLOSED = "closed"
    TIMEOUT = "timeout"


class MessageRole(str, Enum):
    """Chat message sender roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SafetySeverity(str, Enum):
    """Safety risk severity levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskSeverity(str, Enum):
    """Stress/risk score severity categories."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditAction(str, Enum):
    """Audit log action types. Extend as needed."""
    USER_REGISTERED = "user_registered"
    USER_LOGIN = "user_login"
    CONSENT_ACCEPTED = "consent_accepted"
    SESSION_STARTED = "session_started"
    SESSION_CLOSED = "session_closed"
    CRISIS_DETECTED = "crisis_detected"
    PROFILE_GENERATED = "profile_generated"
    DOCTOR_VIEWED_PROFILE = "doctor_viewed_profile"
    DOCTOR_COPILOT_QUERY = "doctor_copilot_query"
    ASSIGNMENT_CREATED = "assignment_created"
    ASSIGNMENT_REMOVED = "assignment_removed"
    ADMIN_CONFIG_CHANGED = "admin_config_changed"
```

---

### 2.5 Tạo `backend/app/core/exceptions.py`

Custom exception hierarchy + FastAPI exception handlers:

```python
# backend/app/core/exceptions.py
from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base exception for the application."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppException):
    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(
            message=f"{resource} with id '{resource_id}' not found",
            status_code=404,
        )


class AlreadyExistsError(AppException):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            message=f"{resource} '{identifier}' already exists",
            status_code=409,
        )


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Not authenticated") -> None:
        super().__init__(message=message, status_code=401)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message=message, status_code=403)


class InvalidCredentialsError(AppException):
    def __init__(self) -> None:
        super().__init__(message="Invalid email or password", status_code=401)


class ConsentRequiredError(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="Consent acceptance required before using the platform",
            status_code=403,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Global exception handler for AppException and subclasses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )
```

---

### 2.6 Tạo `backend/app/db/supabase_client.py`

Singleton Supabase client connection, được khởi tạo trong FastAPI lifespan:

```python
# backend/app/db/supabase_client.py
from supabase import Client, create_client

from app.core.config import Settings


def create_supabase_client(settings: Settings) -> Client:
    """Create a Supabase client instance.

    This should be called once during application startup (lifespan)
    and stored in app.state.
    """
    if not settings.supabase_url or not settings.supabase_key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY must be set in environment variables."
        )
    return create_client(settings.supabase_url, settings.supabase_key)
```

---

### 2.7 Tạo `backend/app/db/repositories/base.py`

Tạo thư mục `backend/app/db/repositories/` với `__init__.py` và abstract base repository:

```python
# backend/app/db/repositories/__init__.py
# (empty)
```

```python
# backend/app/db/repositories/base.py
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from supabase import Client

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository for Supabase/Postgres data access.

    All concrete repositories must inherit from this class and implement
    the abstract methods. Services should depend on this abstraction.
    """

    def __init__(self, db: Client, table_name: str) -> None:
        self._db = db
        self._table_name = table_name

    @abstractmethod
    def _to_model(self, data: dict[str, Any]) -> T:
        """Convert a raw database row dict to the domain model."""
        ...

    async def get_by_id(self, record_id: str) -> T | None:
        """Fetch a single record by its UUID primary key."""
        result = (
            self._db.table(self._table_name)
            .select("*")
            .eq("id", record_id)
            .execute()
        )
        if result.data:
            return self._to_model(result.data[0])
        return None

    async def create(self, data: dict[str, Any]) -> T:
        """Insert a new record and return the created model."""
        result = self._db.table(self._table_name).insert(data).execute()
        return self._to_model(result.data[0])

    async def update(self, record_id: str, data: dict[str, Any]) -> T | None:
        """Update a record by ID and return the updated model."""
        result = (
            self._db.table(self._table_name)
            .update(data)
            .eq("id", record_id)
            .execute()
        )
        if result.data:
            return self._to_model(result.data[0])
        return None

    async def delete(self, record_id: str) -> bool:
        """Delete a record by ID. Returns True if deleted."""
        result = (
            self._db.table(self._table_name)
            .delete()
            .eq("id", record_id)
            .execute()
        )
        return len(result.data) > 0
```

---

### 2.8 Tạo Pydantic schemas

Tạo 4 schema files. Mỗi file chứa request/response models cho một domain.

**`backend/app/schemas/user.py`:**
```python
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.core.constants import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.PATIENT


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleCallbackParams(BaseModel):
    """Query params từ Supabase Google OAuth callback."""
    code: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    auth_provider: str = "local"
    avatar_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
```

**`backend/app/schemas/consent.py`:**
```python
from datetime import datetime
from pydantic import BaseModel


class ConsentAccept(BaseModel):
    policy_version: str


class ConsentResponse(BaseModel):
    id: str
    user_id: str
    policy_version: str
    accepted: bool
    accepted_at: datetime

    model_config = {"from_attributes": True}
```

**`backend/app/schemas/audit.py`:**
```python
from datetime import datetime
from typing import Any
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    user_id: str | None
    role: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    metadata: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}
```

**`backend/app/schemas/assignment.py`:**
```python
from datetime import datetime
from pydantic import BaseModel


class AssignmentCreate(BaseModel):
    doctor_id: str
    patient_id: str


class AssignmentResponse(BaseModel):
    id: str
    doctor_id: str
    patient_id: str
    assigned_by: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
```

---

### 2.9 Tạo `backend/app/db/repositories/user_repo.py`

```python
from typing import Any
from supabase import Client
from app.db.repositories.base import BaseRepository
from app.schemas.user import UserResponse


class UserRepository(BaseRepository[UserResponse]):
    def __init__(self, db: Client) -> None:
        super().__init__(db, "users")

    def _to_model(self, data: dict[str, Any]) -> UserResponse:
        return UserResponse(**data)

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        """Get raw user data by email (includes password_hash for auth)."""
        result = (
            self._db.table(self._table_name)
            .select("*")
            .eq("email", email)
            .execute()
        )
        if result.data:
            return result.data[0]
        return None

    async def email_exists(self, email: str) -> bool:
        result = (
            self._db.table(self._table_name)
            .select("id")
            .eq("email", email)
            .execute()
        )
        return len(result.data) > 0

    async def get_by_provider_id(
        self, provider: str, provider_user_id: str
    ) -> dict[str, Any] | None:
        """Get raw user data by auth_provider + provider_user_id (cho Google OAuth)."""
        result = (
            self._db.table(self._table_name)
            .select("*")
            .eq("auth_provider", provider)
            .eq("provider_user_id", provider_user_id)
            .execute()
        )
        if result.data:
            return result.data[0]
        return None

    async def list_by_role(self, role: str) -> list[UserResponse]:
        result = (
            self._db.table(self._table_name)
            .select("*")
            .eq("role", role)
            .eq("is_active", True)
            .execute()
        )
        return [self._to_model(row) for row in result.data]
```

---

### 2.10 Tạo `backend/app/db/repositories/consent_repo.py`

```python
from typing import Any
from supabase import Client
from app.db.repositories.base import BaseRepository
from app.schemas.consent import ConsentResponse


class ConsentRepository(BaseRepository[ConsentResponse]):
    def __init__(self, db: Client) -> None:
        super().__init__(db, "consent_records")

    def _to_model(self, data: dict[str, Any]) -> ConsentResponse:
        return ConsentResponse(**data)

    async def get_latest_by_user(self, user_id: str) -> ConsentResponse | None:
        result = (
            self._db.table(self._table_name)
            .select("*")
            .eq("user_id", user_id)
            .order("accepted_at", desc=True)
            .limit(1)
            .execute()
        )
        if result.data:
            return self._to_model(result.data[0])
        return None

    async def has_accepted_version(self, user_id: str, policy_version: str) -> bool:
        result = (
            self._db.table(self._table_name)
            .select("id")
            .eq("user_id", user_id)
            .eq("policy_version", policy_version)
            .eq("accepted", True)
            .execute()
        )
        return len(result.data) > 0
```

---

### 2.11 Tạo `backend/app/db/repositories/audit_repo.py`

```python
from typing import Any
from supabase import Client
from app.db.repositories.base import BaseRepository
from app.schemas.audit import AuditLogResponse


class AuditRepository(BaseRepository[AuditLogResponse]):
    def __init__(self, db: Client) -> None:
        super().__init__(db, "audit_logs")

    def _to_model(self, data: dict[str, Any]) -> AuditLogResponse:
        return AuditLogResponse(**data)

    async def list_by_user(
        self, user_id: str, limit: int = 50
    ) -> list[AuditLogResponse]:
        result = (
            self._db.table(self._table_name)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [self._to_model(row) for row in result.data]

    async def list_by_action(
        self, action: str, limit: int = 50
    ) -> list[AuditLogResponse]:
        result = (
            self._db.table(self._table_name)
            .select("*")
            .eq("action", action)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [self._to_model(row) for row in result.data]
```

---

### 2.12 Tạo `backend/app/db/repositories/assignment_repo.py`

```python
from typing import Any

from supabase import Client

from app.db.repositories.base import BaseRepository
from app.schemas.assignment import AssignmentResponse


class AssignmentRepository(BaseRepository[AssignmentResponse]):
    def __init__(self, db: Client) -> None:
        super().__init__(db, "doctor_assignments")

    def _to_model(self, data: dict[str, Any]) -> AssignmentResponse:
        return AssignmentResponse(**data)

    async def get_active_assignment(
        self, doctor_id: str, patient_id: str
    ) -> AssignmentResponse | None:
        result = (
            self._db.table(self._table_name)
            .select("*")
            .eq("doctor_id", doctor_id)
            .eq("patient_id", patient_id)
            .eq("is_active", True)
            .execute()
        )
        if result.data:
            return self._to_model(result.data[0])
        return None

    async def is_assigned(self, doctor_id: str, patient_id: str) -> bool:
        result = await self.get_active_assignment(doctor_id, patient_id)
        return result is not None

    async def list_patients_for_doctor(
        self, doctor_id: str
    ) -> list[AssignmentResponse]:
        result = (
            self._db.table(self._table_name)
            .select("*")
            .eq("doctor_id", doctor_id)
            .eq("is_active", True)
            .execute()
        )
        return [self._to_model(row) for row in result.data]

    async def list_doctors_for_patient(
        self, patient_id: str
    ) -> list[AssignmentResponse]:
        result = (
            self._db.table(self._table_name)
            .select("*")
            .eq("patient_id", patient_id)
            .eq("is_active", True)
            .execute()
        )
        return [self._to_model(row) for row in result.data]

    async def deactivate(self, assignment_id: str) -> AssignmentResponse | None:
        """Soft-delete: set is_active=False instead of deleting."""
        return await self.update(assignment_id, {"is_active": False})
```

## Task 2.13 — Tạo `backend/app/services/auth_service.py`

Service xử lý register, login, JWT token creation, và **Google OAuth** (đăng nhập/đăng ký qua Google). Đây là service quan trọng nhất của Milestone 2.

```python
# backend/app/services/auth_service.py
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from supabase import Client

from app.core.config import settings
from app.core.constants import AuditAction, AuthProvider, UserRole
from app.core.exceptions import (
    AlreadyExistsError,
    InvalidCredentialsError,
    UnauthorizedError,
)
from app.db.repositories.user_repo import UserRepository
from app.schemas.user import TokenResponse, UserCreate, UserResponse
from app.services.audit_service import AuditService


# Password hashing context — bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Handles user registration, login, JWT token management, and Google OAuth.

    This service encapsulates all authentication logic. It depends on
    UserRepository for data access, AuditService for logging, and
    Supabase Client for Google OAuth flow.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        audit_service: AuditService,
        supabase: Client,
    ) -> None:
        self._user_repo = user_repo
        self._audit_service = audit_service
        self._supabase = supabase

    async def register(self, data: UserCreate) -> UserResponse:
        """Register a new user.

        Args:
            data: User registration data (email, password, full_name, role).

        Returns:
            UserResponse with the created user's public data.

        Raises:
            AlreadyExistsError: If email is already registered.
        """
        if await self._user_repo.email_exists(data.email):
            raise AlreadyExistsError("User", data.email)

        password_hash = pwd_context.hash(data.password)

        user = await self._user_repo.create({
            "email": data.email,
            "password_hash": password_hash,
            "full_name": data.full_name,
            "role": data.role.value,
        })

        await self._audit_service.log(
            user_id=user.id,
            role=data.role.value,
            action=AuditAction.USER_REGISTERED,
            resource_type="user",
            resource_id=user.id,
        )

        return user

    async def login(self, email: str, password: str) -> TokenResponse:
        """Authenticate a user and return a JWT token.

        Args:
            email: User email.
            password: Plain-text password.

        Returns:
            TokenResponse with access_token and user data.

        Raises:
            InvalidCredentialsError: If email not found or password incorrect.
        """
        raw_user = await self._user_repo.get_by_email(email)
        if raw_user is None:
            raise InvalidCredentialsError()

        if not pwd_context.verify(password, raw_user["password_hash"]):
            raise InvalidCredentialsError()

        user = UserResponse(**raw_user)
        token = self._create_access_token(
            subject=user.id,
            role=user.role.value,
        )

        await self._audit_service.log(
            user_id=user.id,
            role=user.role.value,
            action=AuditAction.USER_LOGIN,
            resource_type="user",
            resource_id=user.id,
        )

        return TokenResponse(access_token=token, user=user)

    def _create_access_token(self, subject: str, role: str) -> str:
        """Create a signed JWT token.

        Args:
            subject: User ID to encode as 'sub' claim.
            role: User role to encode as 'role' claim.

        Returns:
            Encoded JWT string.
        """
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_expiration_minutes
        )
        payload: dict[str, Any] = {
            "sub": subject,
            "role": role,
            "exp": expire,
        }
        return jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    @staticmethod
    def decode_token(token: str) -> dict[str, Any]:
        """Decode and verify a JWT token.

        Args:
            token: The JWT string.

        Returns:
            Decoded payload dict with 'sub' and 'role'.

        Raises:
            UnauthorizedError: If token is invalid or expired.
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            if payload.get("sub") is None:
                raise UnauthorizedError("Invalid token: missing subject")
            return payload
        except JWTError as e:
            raise UnauthorizedError(f"Invalid token: {e}") from e

    # ─── Google OAuth ────────────────────────────────────────────────────────

    def get_google_oauth_url(self) -> str:
        """Generate Supabase Google OAuth URL để redirect user đến Google login.

        Dùng Supabase built-in Google OAuth provider. Supabase sẽ handle
        toàn bộ OAuth flow với Google, sau đó redirect về callback URL
        của backend với authorization code.

        Returns:
            Google OAuth URL string để frontend redirect user đến.
        """
        callback_url = f"{settings.backend_url}/api/v1/auth/google/callback"
        response = self._supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": callback_url,
            },
        })
        return response.url

    async def handle_google_callback(self, code: str) -> TokenResponse:
        """Xử lý callback từ Supabase sau khi user đăng nhập Google thành công.

        Flow:
        1. Exchange authorization code cho Supabase session
        2. Extract user info (email, full_name, avatar_url) từ user_metadata
        3. Tìm user hiện có bằng provider_user_id, hoặc bằng email (link accounts),
           hoặc tạo user mới
        4. Issue app JWT token
        5. Audit log

        Args:
            code: Authorization code từ Supabase redirect.

        Returns:
            TokenResponse với access_token và user data.
        """
        # 1. Exchange code for Supabase session
        session_response = self._supabase.auth.exchange_code_for_session({
            "auth_code": code,
        })
        supabase_user = session_response.user

        # 2. Extract user info
        email = supabase_user.email
        metadata = supabase_user.user_metadata or {}
        full_name = metadata.get("full_name") or metadata.get("name") or email
        avatar_url = metadata.get("avatar_url") or metadata.get("picture")
        provider_user_id = supabase_user.id

        # 3. Find or create user
        # 3a. Tìm bằng provider_user_id (returning user)
        existing = await self._user_repo.get_by_provider_id(
            provider=AuthProvider.GOOGLE.value,
            provider_user_id=provider_user_id,
        )
        if existing:
            user = UserResponse(**existing)
        else:
            # 3b. Tìm bằng email (link accounts — user đã register local trước đó)
            existing_by_email = await self._user_repo.get_by_email(email)
            if existing_by_email:
                # Update existing user to link Google account
                updated = await self._user_repo.update(
                    existing_by_email["id"],
                    {
                        "auth_provider": AuthProvider.GOOGLE.value,
                        "provider_user_id": provider_user_id,
                        "avatar_url": avatar_url,
                    },
                )
                user = updated
            else:
                # 3c. Tạo user mới (đăng ký qua Google — không cần password)
                user = await self._user_repo.create({
                    "email": email,
                    "full_name": full_name,
                    "role": UserRole.PATIENT.value,
                    "auth_provider": AuthProvider.GOOGLE.value,
                    "provider_user_id": provider_user_id,
                    "avatar_url": avatar_url,
                })

        # 4. Issue app JWT token
        token = self._create_access_token(
            subject=user.id,
            role=user.role.value if isinstance(user.role, UserRole) else user.role,
        )

        # 5. Audit log
        await self._audit_service.log(
            user_id=user.id,
            role=user.role.value if isinstance(user.role, UserRole) else user.role,
            action=AuditAction.USER_LOGIN,
            resource_type="user",
            resource_id=user.id,
            metadata={"method": "google"},
        )

        return TokenResponse(access_token=token, user=user)
```

---

## Task 2.14 — Tạo `backend/app/services/audit_service.py`

Service ghi audit log cho mọi sensitive action (SRDS Section 11.3).

```python
# backend/app/services/audit_service.py
from typing import Any

from app.core.constants import AuditAction
from app.db.repositories.audit_repo import AuditRepository
from app.schemas.audit import AuditLogResponse


class AuditService:
    """Records audit logs for all sensitive actions.

    Every security-relevant event (login, profile access, crisis detection,
    consent acceptance, admin changes) must be logged through this service.
    """

    def __init__(self, audit_repo: AuditRepository) -> None:
        self._audit_repo = audit_repo

    async def log(
        self,
        action: AuditAction,
        user_id: str | None = None,
        role: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLogResponse:
        """Write an audit log entry.

        Args:
            action: The action being logged (from AuditAction enum).
            user_id: ID of the user performing the action.
            role: Role of the user at the time of action.
            resource_type: Type of resource affected (e.g., "user", "session", "profile").
            resource_id: ID of the affected resource.
            metadata: Additional context (e.g., IP address, request details).

        Returns:
            The created AuditLogResponse.
        """
        return await self._audit_repo.create({
            "user_id": user_id,
            "role": role,
            "action": action.value,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "metadata": metadata or {},
        })

    async def get_user_logs(
        self, user_id: str, limit: int = 50
    ) -> list[AuditLogResponse]:
        """Get audit logs for a specific user."""
        return await self._audit_repo.list_by_user(user_id, limit)

    async def get_logs_by_action(
        self, action: AuditAction, limit: int = 50
    ) -> list[AuditLogResponse]:
        """Get audit logs filtered by action type."""
        return await self._audit_repo.list_by_action(action.value, limit)
```

---

## Task 2.15 — Tạo `backend/app/services/consent_service.py`

Service quản lý consent records (SRDS Section 11.2).

```python
# backend/app/services/consent_service.py
from app.core.config import settings
from app.core.constants import AuditAction
from app.db.repositories.consent_repo import ConsentRepository
from app.schemas.consent import ConsentResponse
from app.services.audit_service import AuditService


class ConsentService:
    """Manages patient consent records.

    Patients must accept terms before using the platform. Consent records
    store policy version and timestamp. Policy version changes require
    re-acceptance.
    """

    def __init__(
        self,
        consent_repo: ConsentRepository,
        audit_service: AuditService,
    ) -> None:
        self._consent_repo = consent_repo
        self._audit_service = audit_service

    async def accept_consent(
        self, user_id: str, policy_version: str
    ) -> ConsentResponse:
        """Record that a user accepted a specific policy version.

        Args:
            user_id: The user accepting consent.
            policy_version: The policy version being accepted.

        Returns:
            The created ConsentResponse.
        """
        consent = await self._consent_repo.create({
            "user_id": user_id,
            "policy_version": policy_version,
            "accepted": True,
        })

        await self._audit_service.log(
            user_id=user_id,
            action=AuditAction.CONSENT_ACCEPTED,
            resource_type="consent",
            resource_id=consent.id,
            metadata={"policy_version": policy_version},
        )

        return consent

    async def has_valid_consent(self, user_id: str) -> bool:
        """Check if user has accepted the current policy version.

        Args:
            user_id: The user to check.

        Returns:
            True if user has accepted the current policy version.
        """
        return await self._consent_repo.has_accepted_version(
            user_id, settings.current_consent_policy_version
        )

    async def get_latest_consent(self, user_id: str) -> ConsentResponse | None:
        """Get the most recent consent record for a user."""
        return await self._consent_repo.get_latest_by_user(user_id)

    def get_current_policy_version(self) -> str:
        """Return the current consent policy version from config."""
        return settings.current_consent_policy_version
```

---

## Task 2.16 — Tạo `backend/app/services/assignment_service.py`

Service quản lý doctor-patient assignments.

```python
# backend/app/services/assignment_service.py
from app.core.constants import AuditAction, UserRole
from app.core.exceptions import ForbiddenError, NotFoundError
from app.db.repositories.assignment_repo import AssignmentRepository
from app.db.repositories.user_repo import UserRepository
from app.schemas.assignment import AssignmentResponse
from app.services.audit_service import AuditService


class AssignmentService:
    """Manages doctor-patient assignment relationships.

    Only admins can create/deactivate assignments. Assignments are used
    to enforce that doctors can only access their assigned patients' data.
    """

    def __init__(
        self,
        assignment_repo: AssignmentRepository,
        user_repo: UserRepository,
        audit_service: AuditService,
    ) -> None:
        self._assignment_repo = assignment_repo
        self._user_repo = user_repo
        self._audit_service = audit_service

    async def create_assignment(
        self,
        doctor_id: str,
        patient_id: str,
        assigned_by: str,
    ) -> AssignmentResponse:
        """Assign a patient to a doctor.

        Args:
            doctor_id: UUID of the doctor.
            patient_id: UUID of the patient.
            assigned_by: UUID of the admin creating the assignment.

        Returns:
            The created AssignmentResponse.

        Raises:
            NotFoundError: If doctor or patient not found.
            ForbiddenError: If doctor_id is not a doctor or patient_id is not a patient.
        """
        doctor = await self._user_repo.get_by_id(doctor_id)
        if doctor is None:
            raise NotFoundError("User (doctor)", doctor_id)
        if doctor.role != UserRole.DOCTOR:
            raise ForbiddenError(f"User {doctor_id} is not a doctor")

        patient = await self._user_repo.get_by_id(patient_id)
        if patient is None:
            raise NotFoundError("User (patient)", patient_id)
        if patient.role != UserRole.PATIENT:
            raise ForbiddenError(f"User {patient_id} is not a patient")

        # Check if already assigned
        existing = await self._assignment_repo.get_active_assignment(
            doctor_id, patient_id
        )
        if existing is not None:
            return existing  # Idempotent — return existing assignment

        assignment = await self._assignment_repo.create({
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "assigned_by": assigned_by,
        })

        await self._audit_service.log(
            user_id=assigned_by,
            role=UserRole.ADMIN.value,
            action=AuditAction.ASSIGNMENT_CREATED,
            resource_type="assignment",
            resource_id=assignment.id,
            metadata={
                "doctor_id": doctor_id,
                "patient_id": patient_id,
            },
        )

        return assignment

    async def deactivate_assignment(
        self, assignment_id: str, deactivated_by: str
    ) -> AssignmentResponse:
        """Soft-delete an assignment (set is_active=False).

        Args:
            assignment_id: UUID of the assignment.
            deactivated_by: UUID of the admin deactivating.

        Returns:
            The updated AssignmentResponse.

        Raises:
            NotFoundError: If assignment not found.
        """
        result = await self._assignment_repo.deactivate(assignment_id)
        if result is None:
            raise NotFoundError("Assignment", assignment_id)

        await self._audit_service.log(
            user_id=deactivated_by,
            role=UserRole.ADMIN.value,
            action=AuditAction.ASSIGNMENT_DEACTIVATED,
            resource_type="assignment",
            resource_id=assignment_id,
        )

        return result

    async def is_doctor_assigned_to_patient(
        self, doctor_id: str, patient_id: str
    ) -> bool:
        """Check if a doctor is actively assigned to a patient.

        This is the core RBAC check for clinical data access.
        """
        return await self._assignment_repo.is_assigned(doctor_id, patient_id)

    async def list_patients_for_doctor(
        self, doctor_id: str
    ) -> list[AssignmentResponse]:
        """List all active patient assignments for a doctor."""
        return await self._assignment_repo.list_patients_for_doctor(doctor_id)

    async def list_doctors_for_patient(
        self, patient_id: str
    ) -> list[AssignmentResponse]:
        """List all active doctor assignments for a patient."""
        return await self._assignment_repo.list_doctors_for_patient(patient_id)
```

---

## Task 2.17 — Tạo `backend/app/core/security.py`

JWT verification utilities và FastAPI RBAC dependency functions. Đây là file kết nối auth_service với FastAPI's dependency injection.

```python
# backend/app/core/security.py
from typing import Annotated

from fastapi import Depends, Header

from app.core.constants import UserRole
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.db.repositories.user_repo import UserRepository
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    user_repo: UserRepository = Depends(),  # Will be overridden in dependencies.py
) -> UserResponse:
    """Extract and verify JWT from Authorization header, return current user.

    Usage: Add as a dependency to any protected route.

    Raises:
        UnauthorizedError: If token is missing, invalid, or user not found.
    """
    if authorization is None:
        raise UnauthorizedError("Missing Authorization header")

    # Expect "Bearer <token>"
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Invalid Authorization header format. Use: Bearer <token>")

    token = parts[1]
    payload = AuthService.decode_token(token)

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token: missing subject")

    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("User not found")

    if not user.is_active:
        raise UnauthorizedError("User account is deactivated")

    return user


def require_role(*allowed_roles: UserRole):
    """Factory that creates a dependency requiring specific roles.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(UserRole.ADMIN))])
        async def admin_endpoint(...): ...

    Or as a parameter dependency:
        current_user: UserResponse = Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN))
    """
    async def role_checker(
        current_user: UserResponse = Depends(get_current_user),
    ) -> UserResponse:
        if current_user.role not in allowed_roles:
            raise ForbiddenError(
                f"Role '{current_user.role.value}' is not allowed. "
                f"Required: {[r.value for r in allowed_roles]}"
            )
        return current_user

    return role_checker
```

**Lưu ý quan trọng:** `get_current_user` ở trên dùng `Depends()` placeholder cho `user_repo`. Trong thực tế, dependency sẽ được wired đúng thông qua `api/dependencies.py` (task 2.18). Có 2 cách tiếp cận:

**Cách 1 (Đơn giản hơn):** Đặt `get_current_user` trực tiếp trong `api/dependencies.py` thay vì `core/security.py`, để nó có access trực tiếp đến `get_user_repo()`. Giữ `require_role` trong `core/security.py`.

**Cách 2 (Như trên):** Dùng FastAPI dependency override. Chọn cách nào phù hợp hơn với coding style.

**Khuyến nghị dùng Cách 1** — đặt `get_current_user` trong `api/dependencies.py` để tránh circular imports. `core/security.py` chỉ chứa `require_role` factory và JWT utility functions.

Nếu dùng Cách 1, `core/security.py` sẽ đơn giản hơn:

```python
# backend/app/core/security.py (Cách 1 — khuyến nghị)
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings
from app.core.constants import UserRole
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.schemas.user import UserResponse


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT access token.

    Args:
        token: The JWT string from Authorization header.

    Returns:
        Decoded payload with 'sub' (user_id) and 'role'.

    Raises:
        UnauthorizedError: If token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("sub") is None:
            raise UnauthorizedError("Invalid token: missing subject")
        return payload
    except JWTError as e:
        raise UnauthorizedError(f"Invalid token: {e}") from e


def require_role(*allowed_roles: UserRole):
    """Factory that creates a FastAPI dependency requiring specific user roles.

    Usage in routes:
        @router.get("/admin-only")
        async def admin_endpoint(
            user: UserResponse = Depends(require_role(UserRole.ADMIN)),
        ): ...

    Args:
        allowed_roles: One or more UserRole values that are permitted.

    Returns:
        A FastAPI dependency function that validates the user's role.
    """
    from app.api.dependencies import get_current_user  # Lazy import to avoid circular
    from fastapi import Depends

    async def role_checker(
        current_user: UserResponse = Depends(get_current_user),
    ) -> UserResponse:
        if current_user.role not in allowed_roles:
            raise ForbiddenError(
                f"Role '{current_user.role.value}' not allowed. "
                f"Required: {[r.value for r in allowed_roles]}"
            )
        return current_user

    return role_checker
```

---

## Task 2.18 — Tạo `backend/app/api/dependencies.py`

Central FastAPI dependency injection wiring. Tất cả route handlers lấy services từ đây.

```python
# backend/app/api/dependencies.py
from typing import Annotated

from fastapi import Depends, Header, Request
from supabase import Client

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.db.repositories.assignment_repo import AssignmentRepository
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.consent_repo import ConsentRepository
from app.db.repositories.user_repo import UserRepository
from app.schemas.user import UserResponse
from app.services.assignment_service import AssignmentService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.consent_service import ConsentService


# --- Database Client ---

def get_supabase(request: Request) -> Client:
    """Get Supabase client from app state (initialized in lifespan)."""
    return request.app.state.supabase


# --- Repositories ---

def get_user_repo(db: Client = Depends(get_supabase)) -> UserRepository:
    return UserRepository(db)


def get_audit_repo(db: Client = Depends(get_supabase)) -> AuditRepository:
    return AuditRepository(db)


def get_consent_repo(db: Client = Depends(get_supabase)) -> ConsentRepository:
    return ConsentRepository(db)


def get_assignment_repo(db: Client = Depends(get_supabase)) -> AssignmentRepository:
    return AssignmentRepository(db)


# --- Services ---

def get_audit_service(
    audit_repo: AuditRepository = Depends(get_audit_repo),
) -> AuditService:
    return AuditService(audit_repo)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
    audit_service: AuditService = Depends(get_audit_service),
    db: Client = Depends(get_supabase),
) -> AuthService:
    return AuthService(user_repo=user_repo, audit_service=audit_service, supabase=db)


def get_consent_service(
    consent_repo: ConsentRepository = Depends(get_consent_repo),
    audit_service: AuditService = Depends(get_audit_service),
) -> ConsentService:
    return ConsentService(consent_repo=consent_repo, audit_service=audit_service)


def get_assignment_service(
    assignment_repo: AssignmentRepository = Depends(get_assignment_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    audit_service: AuditService = Depends(get_audit_service),
) -> AssignmentService:
    return AssignmentService(
        assignment_repo=assignment_repo,
        user_repo=user_repo,
        audit_service=audit_service,
    )


# --- Auth Dependencies ---

async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserResponse:
    """Extract JWT from Authorization header, verify, and return current user.

    Usage: Add as dependency to any protected route.
        @router.get("/me")
        async def me(user: UserResponse = Depends(get_current_user)): ...

    Raises:
        UnauthorizedError: If token missing, invalid, expired, or user not found.
    """
    if authorization is None:
        raise UnauthorizedError("Missing Authorization header")

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Invalid Authorization format. Use: Bearer <token>")

    payload = decode_access_token(parts[1])
    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token: missing subject")

    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("User not found")
    if not user.is_active:
        raise UnauthorizedError("User account is deactivated")

    return user
```

---

## Task 2.19 — Tạo `backend/app/api/auth.py`

Auth API endpoints: register, login, get current user, **Google OAuth login/register**.

```python
# backend/app/api/auth.py
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse

from app.api.dependencies import get_auth_service, get_current_user
from app.core.config import settings
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Register a new user account."""
    return await auth_service.register(data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate and receive a JWT access token."""
    return await auth_service.login(data.email, data.password)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Get the currently authenticated user's profile."""
    return current_user


# ─── Google OAuth ────────────────────────────────────────────────────────────


@router.get("/google")
async def google_login(
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """Trả về Supabase Google OAuth URL để frontend redirect user đến.

    Frontend gọi endpoint này, nhận URL, rồi redirect user đến Google login page.
    Sau khi user đăng nhập Google, Supabase sẽ redirect về /auth/google/callback.
    """
    url = auth_service.get_google_oauth_url()
    return {"url": url}


@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code từ Supabase"),
    auth_service: AuthService = Depends(get_auth_service),
) -> RedirectResponse:
    """Callback endpoint nhận authorization code từ Supabase sau Google login.

    Flow:
    1. Nhận `code` query param từ Supabase redirect
    2. Gọi auth_service.handle_google_callback(code) để exchange code,
       find/create user, issue JWT
    3. Redirect về frontend với access_token và user_name trong query params

    Frontend sẽ đọc query params để lưu token vào session state.
    """
    token_response = await auth_service.handle_google_callback(code)
    params = urlencode({
        "access_token": token_response.access_token,
        "user_name": token_response.user.full_name,
    })
    return RedirectResponse(url=f"{settings.frontend_url}?{params}")
```

---

## Task 2.20 — Tạo `backend/app/api/consent.py`

```python
# backend/app/api/consent.py
from fastapi import APIRouter, Depends

from app.api.dependencies import get_consent_service, get_current_user
from app.core.config import settings
from app.schemas.consent import ConsentAccept, ConsentResponse
from app.schemas.user import UserResponse
from app.services.consent_service import ConsentService

router = APIRouter(prefix="/consent", tags=["consent"])


@router.post("/accept", response_model=ConsentResponse, status_code=201)
async def accept_consent(
    data: ConsentAccept,
    current_user: UserResponse = Depends(get_current_user),
    consent_service: ConsentService = Depends(get_consent_service),
) -> ConsentResponse:
    """Accept a consent policy version.

    Patients must accept consent before using the chat system.
    Consent records store policy version and timestamp per SRDS Section 11.2.
    """
    return await consent_service.accept_consent(
        user_id=current_user.id,
        policy_version=data.policy_version,
    )


@router.get("/status")
async def consent_status(
    current_user: UserResponse = Depends(get_current_user),
    consent_service: ConsentService = Depends(get_consent_service),
) -> dict:
    """Check if the current user has accepted the latest consent policy.

    Returns:
        - has_accepted: bool — whether user accepted the current policy version
        - current_policy_version: str — the version they need to accept
        - latest_consent: ConsentResponse | None — their most recent consent record
    """
    current_version = settings.current_consent_policy_version
    has_accepted = await consent_service.has_accepted_current(
        user_id=current_user.id,
    )
    latest = await consent_service.get_latest_consent(
        user_id=current_user.id,
    )
    return {
        "has_accepted": has_accepted,
        "current_policy_version": current_version,
        "latest_consent": latest,
    }
```

---

## Task 2.21 — Tạo `backend/app/api/admin.py`

Admin endpoints cho user management và doctor-patient assignment. Tất cả endpoints yêu cầu role ADMIN (trừ doctor xem danh sách patients của mình).

```python
# backend/app/api/admin.py
from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_assignment_service,
    get_current_user,
    get_user_repo,
)
from app.core.constants import UserRole
from app.core.security import require_role
from app.db.repositories.user_repo import UserRepository
from app.schemas.assignment import AssignmentCreate, AssignmentResponse
from app.schemas.user import UserResponse
from app.services.assignment_service import AssignmentService

router = APIRouter(prefix="/admin", tags=["admin"])


# ─── User Management (Admin only) ───────────────────────────────────────────


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    role: str | None = None,
    _admin: UserResponse = Depends(require_role(UserRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repo),
) -> list[UserResponse]:
    """List all users, optionally filtered by role. Admin only."""
    if role:
        return await user_repo.list_by_role(role)
    # list_all not in base repo — use Supabase select all
    result = user_repo._db.table("users").select("*").execute()
    return [UserResponse(**row) for row in result.data]


@router.patch("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: str,
    _admin: UserResponse = Depends(require_role(UserRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserResponse:
    """Deactivate a user account. Admin only."""
    user = await user_repo.update(user_id, {"is_active": False})
    if user is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("User", user_id)
    return user


@router.patch("/users/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: str,
    _admin: UserResponse = Depends(require_role(UserRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserResponse:
    """Reactivate a user account. Admin only."""
    user = await user_repo.update(user_id, {"is_active": True})
    if user is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("User", user_id)
    return user


# ─── Doctor-Patient Assignments ──────────────────────────────────────────────


@router.post("/assignments", response_model=AssignmentResponse, status_code=201)
async def create_assignment(
    data: AssignmentCreate,
    admin: UserResponse = Depends(require_role(UserRole.ADMIN)),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentResponse:
    """Assign a doctor to a patient. Admin only.

    Validates that:
    - doctor_id belongs to a user with role=doctor
    - patient_id belongs to a user with role=patient
    - Assignment doesn't already exist
    """
    return await assignment_service.create_assignment(
        doctor_id=data.doctor_id,
        patient_id=data.patient_id,
        assigned_by=admin.id,
    )


@router.delete("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def deactivate_assignment(
    assignment_id: str,
    admin: UserResponse = Depends(require_role(UserRole.ADMIN)),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentResponse:
    """Deactivate a doctor-patient assignment (soft delete). Admin only."""
    return await assignment_service.deactivate_assignment(
        assignment_id=assignment_id,
        deactivated_by=admin.id,
    )


@router.get("/assignments", response_model=list[AssignmentResponse])
async def list_assignments(
    doctor_id: str | None = None,
    patient_id: str | None = None,
    _admin: UserResponse = Depends(require_role(UserRole.ADMIN)),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> list[AssignmentResponse]:
    """List assignments, optionally filtered by doctor or patient. Admin only."""
    if doctor_id:
        return await assignment_service.list_patients_for_doctor(doctor_id)
    if patient_id:
        return await assignment_service.list_doctors_for_patient(patient_id)
    # List all active assignments
    result = (
        assignment_service._assignment_repo._db
        .table("doctor_assignments")
        .select("*")
        .eq("is_active", True)
        .execute()
    )
    return [AssignmentResponse(**row) for row in result.data]


# ─── Doctor: View own patients ───────────────────────────────────────────────


@router.get("/my-patients", response_model=list[AssignmentResponse])
async def my_patients(
    doctor: UserResponse = Depends(require_role(UserRole.DOCTOR)),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> list[AssignmentResponse]:
    """List patients assigned to the current doctor. Doctor only."""
    return await assignment_service.list_patients_for_doctor(doctor.id)
```

---

## Task 2.22 — Cập nhật `backend/app/main.py`

Đây là thay đổi quan trọng nhất. Cần thêm:
1. **Lifespan** — khởi tạo Supabase client khi app start, cleanup khi shutdown
2. **Exception handlers** — map custom exceptions sang HTTP responses
3. **New routers** — auth, consent, admin

Thay thế toàn bộ nội dung `backend/app/main.py` hiện tại:

```python
# backend/app/main.py
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.consent import router as consent_router
from app.api.health import router as health_router
from app.core.exceptions import AppException
from app.db.supabase_client import create_supabase_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan: initialize and cleanup shared resources.

    - Startup: Create Supabase client, store in app.state
    - Shutdown: Cleanup (Supabase client doesn't need explicit close)
    """
    # --- Startup ---
    app.state.supabase = create_supabase_client()
    yield
    # --- Shutdown ---
    # Supabase Python client doesn't require explicit cleanup.
    # Add cleanup for other resources here in future milestones
    # (e.g., Qdrant client, Langfuse flush).


app = FastAPI(
    title="Mental Health AI Platform",
    version="0.1.0",
    description="Privacy-first, human-in-the-loop AI system for mental health support",
    lifespan=lifespan,
)

# ─── Middleware ───────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Exception Handlers ─────────────────────────────────────────────────────


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Map all custom AppException subclasses to JSON error responses.

    Each AppException carries its own status_code (e.g., 404, 401, 403, 409).
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


# ─── Routers ─────────────────────────────────────────────────────────────────

API_V1_PREFIX = "/api/v1"

app.include_router(health_router, prefix=API_V1_PREFIX, tags=["health"])
app.include_router(auth_router, prefix=API_V1_PREFIX, tags=["auth"])
app.include_router(consent_router, prefix=API_V1_PREFIX, tags=["consent"])
app.include_router(admin_router, prefix=API_V1_PREFIX, tags=["admin"])
```

**Giải thích thay đổi so với file hiện tại (`backend/app/main.py` lines 1-20):**
- Thêm `lifespan` context manager để khởi tạo Supabase client vào `app.state.supabase` (được dùng bởi `api/dependencies.py` → `get_supabase()`)
- Thêm `AppException` handler để tất cả custom exceptions (NotFoundError 404, UnauthorizedError 401, ForbiddenError 403, AlreadyExistsError 409, InvalidCredentialsError 401) tự động trả về JSON response đúng status code
- Thêm 3 routers mới: auth, consent, admin
- Dùng `API_V1_PREFIX` constant thay vì hardcode string

---

## Task 2.23 — Cập nhật `.env.example`

Nếu file `.env.example` đã tồn tại ở root, thêm JWT settings. Nếu chưa có, tạo mới:

```env
# .env.example
# Rename this file to .env and fill in your actual values

# ─── LLM Provider ────────────────────────────────────────────────────────────
OPENAI_API_KEY=

# ─── Vector Database ─────────────────────────────────────────────────────────
QDRANT_URL=http://localhost:6333

# ─── Application Database ────────────────────────────────────────────────────
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-or-service-role-key

# ─── JWT Authentication (Milestone 2) ────────────────────────────────────────
# Generate with: openssl rand -hex 32
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# ─── Google OAuth (Milestone 2) ──────────────────────────────────────────────
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
FRONTEND_URL=http://localhost:8501
BACKEND_URL=http://localhost:8000

# ─── Consent ─────────────────────────────────────────────────────────────────
CURRENT_CONSENT_POLICY_VERSION=1.0
```

Cũng đảm bảo `.env` nằm trong `.gitignore` (kiểm tra file `.gitignore` ở root).

---

## Task 2.24 — Tạo tests

Tạo các test files trong `backend/tests/`. Tất cả tests dùng `pytest` + `pytest-asyncio` (đã có trong dev dependencies). Mock Supabase client để tests không cần database thật.

**File 1: `backend/tests/conftest.py`** — Shared fixtures

```python
# backend/tests/conftest.py
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client with mocked Supabase."""
    # Mock Supabase client in app.state
    mock_supabase = MagicMock()
    app.state.supabase = mock_supabase
    return TestClient(app)


@pytest.fixture
def mock_supabase() -> MagicMock:
    """Standalone mock Supabase client for unit tests."""
    mock = MagicMock()
    # Default: table().select().execute() returns empty
    mock.table.return_value.select.return_value.execute.return_value.data = []
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    return mock


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data as returned from Supabase."""
    return {
        "id": "test-user-id-123",
        "email": "patient@example.com",
        "password_hash": "$2b$12$LJ3m4ys3Lz0QqV9vX5K8XOxZz1234567890abcdef",  # bcrypt hash
        "full_name": "Test Patient",
        "role": "patient",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00+00:00",
        "updated_at": "2025-01-01T00:00:00+00:00",
    }


@pytest.fixture
def sample_doctor_data() -> dict:
    """Sample doctor data."""
    return {
        "id": "test-doctor-id-456",
        "email": "doctor@example.com",
        "password_hash": "$2b$12$LJ3m4ys3Lz0QqV9vX5K8XOxZz1234567890abcdef",
        "full_name": "Dr. Test",
        "role": "doctor",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00+00:00",
        "updated_at": "2025-01-01T00:00:00+00:00",
    }


@pytest.fixture
def auth_headers() -> dict:
    """Generate valid JWT auth headers for testing.

    Creates a real JWT token using test settings.
    """
    from app.services.auth_service import AuthService

    # Temporarily set a test secret key
    from app.core.config import settings
    original_key = settings.jwt_secret_key
    settings.jwt_secret_key = "test-secret-key-for-testing-only"

    token = AuthService._create_access_token_static(
        subject="test-user-id-123",
        role="patient",
    )

    yield {"Authorization": f"Bearer {token}"}

    # Restore
    settings.jwt_secret_key = original_key
```

**Lưu ý:** `_create_access_token_static` là một static method helper mà bạn có thể thêm vào `AuthService` hoặc dùng trực tiếp `jose.jwt.encode` trong fixture. Cách đơn giản hơn:

```python
# Thay thế auth_headers fixture bằng cách dùng jose trực tiếp:
@pytest.fixture
def auth_headers() -> dict:
    from datetime import datetime, timedelta, timezone
    from jose import jwt

    payload = {
        "sub": "test-user-id-123",
        "role": "patient",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, "test-secret-key", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}
```

---

**File 2: `backend/tests/test_health.py`** — Verify health endpoint still works

```python
# backend/tests/test_health.py
from fastapi.testclient import TestClient

from app.main import app


def test_health_check():
    """Health endpoint should return 200 with status healthy."""
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
```

---

**File 3: `backend/tests/test_auth.py`** — Auth service + endpoint tests

```python
# backend/tests/test_auth.py
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.constants import UserRole
from app.core.exceptions import AlreadyExistsError, InvalidCredentialsError
from app.db.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService


class TestAuthService:
    """Unit tests for AuthService (mocked dependencies)."""

    @pytest.fixture
    def mock_user_repo(self, mock_supabase: MagicMock) -> UserRepository:
        return UserRepository(mock_supabase)

    @pytest.fixture
    def mock_audit_service(self, mock_supabase: MagicMock) -> AuditService:
        from app.db.repositories.audit_repo import AuditRepository
        return AuditService(AuditRepository(mock_supabase))

    @pytest.fixture
    def auth_service(
        self,
        mock_user_repo: UserRepository,
        mock_audit_service: AuditService,
        mock_supabase: MagicMock,
    ) -> AuthService:
        return AuthService(
            user_repo=mock_user_repo,
            audit_service=mock_audit_service,
            supabase=mock_supabase,
        )

    async def test_register_success(
        self, auth_service: AuthService, mock_supabase: MagicMock
    ):
        """Register should create user and return UserResponse."""
        # Mock: email doesn't exist
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        # Mock: insert returns new user
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {
                "id": "new-user-id",
                "email": "new@example.com",
                "full_name": "New User",
                "role": "patient",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00+00:00",
            }
        ]

        data = UserCreate(
            email="new@example.com",
            password="securepassword123",
            full_name="New User",
            role=UserRole.PATIENT,
        )
        result = await auth_service.register(data)
        assert result.email == "new@example.com"
        assert result.role == UserRole.PATIENT

    async def test_register_duplicate_email(
        self, auth_service: AuthService, mock_supabase: MagicMock
    ):
        """Register with existing email should raise AlreadyExistsError."""
        # Mock: email already exists
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "existing-id"}
        ]

        data = UserCreate(
            email="existing@example.com",
            password="password",
            full_name="Existing",
        )
        with pytest.raises(AlreadyExistsError):
            await auth_service.register(data)

    async def test_login_invalid_email(
        self, auth_service: AuthService, mock_supabase: MagicMock
    ):
        """Login with non-existent email should raise InvalidCredentialsError."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        with pytest.raises(InvalidCredentialsError):
            await auth_service.login("nonexistent@example.com", "password")


class TestAuthEndpoints:
    """Integration tests for auth API endpoints."""

    def test_register_endpoint(self, client: TestClient):
        """POST /api/v1/auth/register should return 201."""
        # This test requires mocking the Supabase responses
        # through the app.state.supabase mock set up in conftest
        # Full integration test — implement after Supabase is configured
        pass

    def test_login_endpoint(self, client: TestClient):
        """POST /api/v1/auth/login should return token."""
        pass

    def test_me_without_token(self, client: TestClient):
        """GET /api/v1/auth/me without token should return 401."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
```

---

**File 4: `backend/tests/test_rbac.py`** — RBAC / role-based access tests

```python
# backend/tests/test_rbac.py
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import settings


def _make_token(user_id: str, role: str) -> str:
    """Helper to create JWT tokens for testing."""
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key or "test-secret",
        algorithm=settings.jwt_algorithm,
    )


class TestRBAC:
    """Test role-based access control on protected endpoints."""

    def test_admin_endpoint_with_patient_token(self, client):
        """Patient should get 403 on admin-only endpoints."""
        token = _make_token("patient-id", "patient")
        # Need to mock user lookup to return a patient user
        # This is a placeholder — implement after full DI wiring
        pass

    def test_admin_endpoint_with_admin_token(self, client):
        """Admin should get 200 on admin-only endpoints."""
        pass

    def test_doctor_my_patients_with_patient_token(self, client):
        """Patient should get 403 on doctor-only endpoints."""
        pass

    def test_expired_token(self, client):
        """Expired token should return 401."""
        payload = {
            "sub": "user-id",
            "role": "patient",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
        }
        token = jwt.encode(
            payload,
            settings.jwt_secret_key or "test-secret",
            algorithm=settings.jwt_algorithm,
        )
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    def test_missing_authorization_header(self, client):
        """No Authorization header should return 401."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_malformed_token(self, client):
        """Malformed token should return 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not-a-valid-jwt"},
        )
        assert response.status_code == 401
```

---

**File 5: `backend/tests/test_consent.py`** — Consent tracking tests

```python
# backend/tests/test_consent.py
import pytest
from unittest.mock import MagicMock

from app.db.repositories.consent_repo import ConsentRepository
from app.db.repositories.audit_repo import AuditRepository
from app.services.audit_service import AuditService
from app.services.consent_service import ConsentService


class TestConsentService:
    """Unit tests for ConsentService."""

    @pytest.fixture
    def consent_service(self, mock_supabase: MagicMock) -> ConsentService:
        consent_repo = ConsentRepository(mock_supabase)
        audit_repo = AuditRepository(mock_supabase)
        audit_service = AuditService(audit_repo)
        return ConsentService(
            consent_repo=consent_repo,
            audit_service=audit_service,
        )

    async def test_accept_consent(
        self, consent_service: ConsentService, mock_supabase: MagicMock
    ) -> None:
        """Accept consent should create a consent record."""
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {
                "id": "consent-id-1",
                "user_id": "user-123",
                "policy_version": "1.0",
                "accepted": True,
                "accepted_at": "2025-01-01T00:00:00+00:00",
            }
        ]
        # Also mock the audit log insert
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {
                "id": "consent-id-1",
                "user_id": "user-123",
                "policy_version": "1.0",
                "accepted": True,
                "accepted_at": "2025-01-01T00:00:00+00:00",
            }
        ]

        result = await consent_service.accept_consent(
            user_id="user-123",
            policy_version="1.0",
        )
        assert result.accepted is True
        assert result.policy_version == "1.0"
        assert result.user_id == "user-123"

    async def test_has_accepted_current(
        self, consent_service: ConsentService, mock_supabase: MagicMock
    ) -> None:
        """Should return True if user accepted current policy version."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"id": "consent-id-1"}
        ]

        result = await consent_service.has_accepted_current(user_id="user-123")
        assert result is True

    async def test_has_not_accepted(
        self, consent_service: ConsentService, mock_supabase: MagicMock
    ) -> None:
        """Should return False if user has not accepted current policy version."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

        result = await consent_service.has_accepted_current(user_id="user-123")
        assert result is False

    async def test_get_latest_consent_exists(
        self, consent_service: ConsentService, mock_supabase: MagicMock
    ) -> None:
        """Should return the latest consent record if it exists."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": "consent-id-2",
                "user_id": "user-123",
                "policy_version": "1.0",
                "accepted": True,
                "accepted_at": "2025-06-15T10:30:00+00:00",
            }
        ]

        result = await consent_service.get_latest_consent(user_id="user-123")
        assert result is not None
        assert result.id == "consent-id-2"
        assert result.policy_version == "1.0"

    async def test_get_latest_consent_none(
        self, consent_service: ConsentService, mock_supabase: MagicMock
    ) -> None:
        """Should return None if user has no consent records."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []

        result = await consent_service.get_latest_consent(user_id="user-123")
        assert result is None

    async def test_accept_consent_duplicate_version(
        self, consent_service: ConsentService, mock_supabase: MagicMock
    ) -> None:
        """Accepting the same policy version twice should still succeed.

        The system allows re-acceptance (idempotent). Each acceptance
        creates a new record with a new timestamp.
        """
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {
                "id": "consent-id-3",
                "user_id": "user-123",
                "policy_version": "1.0",
                "accepted": True,
                "accepted_at": "2025-06-16T08:00:00+00:00",
            }
        ]

        result = await consent_service.accept_consent(
            user_id="user-123",
            policy_version="1.0",
        )
        assert result.accepted is True
        assert result.id == "consent-id-3"


class TestConsentEndpoints:
    """Integration tests for consent API endpoints."""

    def test_accept_consent_without_auth(self, client) -> None:
        """POST /api/v1/consent/accept without token should return 401."""
        response = client.post(
            "/api/v1/consent/accept",
            json={"policy_version": "1.0"},
        )
        assert response.status_code == 401

    def test_consent_status_without_auth(self, client) -> None:
        """GET /api/v1/consent/status without token should return 401."""
        response = client.get("/api/v1/consent/status")
        assert response.status_code == 401
```

---

## Task 2.24 (tiếp tục) — File 6: `backend/tests/test_audit.py`

Audit logging tests — verify that sensitive actions are properly logged per SRDS Section 11.3.

```python
# backend/tests/test_audit.py
import pytest
from unittest.mock import MagicMock

from app.core.constants import AuditAction
from app.db.repositories.audit_repo import AuditRepository
from app.services.audit_service import AuditService


class TestAuditService:
    """Unit tests for AuditService."""

    @pytest.fixture
    def audit_service(self, mock_supabase: MagicMock) -> AuditService:
        audit_repo = AuditRepository(mock_supabase)
        return AuditService(audit_repo)

    async def test_log_creates_audit_record(
        self, audit_service: AuditService, mock_supabase: MagicMock
    ) -> None:
        """AuditService.log should insert a record into audit_logs table."""
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {
                "id": "audit-id-1",
                "user_id": "user-123",
                "role": "patient",
                "action": AuditAction.USER_LOGIN.value,
                "resource_type": "user",
                "resource_id": "user-123",
                "metadata": {},
                "created_at": "2025-01-01T00:00:00+00:00",
            }
        ]

        result = await audit_service.log(
            user_id="user-123",
            role="patient",
            action=AuditAction.USER_LOGIN,
            resource_type="user",
            resource_id="user-123",
        )
        assert result is not None
        assert result.action == AuditAction.USER_LOGIN.value
        assert result.user_id == "user-123"

    async def test_log_with_metadata(
        self, audit_service: AuditService, mock_supabase: MagicMock
    ) -> None:
        """AuditService.log should support optional metadata dict."""
        metadata = {"ip_address": "192.168.1.1", "user_agent": "TestClient"}
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {
                "id": "audit-id-2",
                "user_id": "admin-456",
                "role": "admin",
                "action": AuditAction.ADMIN_CONFIG_CHANGE.value,
                "resource_type": "config",
                "resource_id": "jwt_expiration",
                "metadata": metadata,
                "created_at": "2025-01-01T00:00:00+00:00",
            }
        ]

        result = await audit_service.log(
            user_id="admin-456",
            role="admin",
            action=AuditAction.ADMIN_CONFIG_CHANGE,
            resource_type="config",
            resource_id="jwt_expiration",
            metadata=metadata,
        )
        assert result.metadata == metadata

    async def test_log_without_user(
        self, audit_service: AuditService, mock_supabase: MagicMock
    ) -> None:
        """AuditService.log should work without user_id (system events)."""
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {
                "id": "audit-id-3",
                "user_id": None,
                "role": None,
                "action": AuditAction.CRISIS_WORKFLOW_ACTIVATED.value,
                "resource_type": "session",
                "resource_id": "session-789",
                "metadata": {},
                "created_at": "2025-01-01T00:00:00+00:00",
            }
        ]

        result = await audit_service.log(
            action=AuditAction.CRISIS_WORKFLOW_ACTIVATED,
            resource_type="session",
            resource_id="session-789",
        )
        assert result.user_id is None
        assert result.action == AuditAction.CRISIS_WORKFLOW_ACTIVATED.value

    async def test_list_by_user(
        self, audit_service: AuditService, mock_supabase: MagicMock
    ) -> None:
        """Should return audit logs filtered by user_id."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": "audit-id-1",
                "user_id": "user-123",
                "role": "patient",
                "action": AuditAction.USER_LOGIN.value,
                "resource_type": "user",
                "resource_id": "user-123",
                "metadata": {},
                "created_at": "2025-01-01T00:00:00+00:00",
            },
            {
                "id": "audit-id-4",
                "user_id": "user-123",
                "role": "patient",
                "action": AuditAction.CONSENT_ACCEPTED.value,
                "resource_type": "consent",
                "resource_id": "consent-id-1",
                "metadata": {},
                "created_at": "2025-01-01T01:00:00+00:00",
            },
        ]

        # Access the underlying repo directly for this test
        audit_repo = AuditRepository(mock_supabase)
        results = await audit_repo.list_by_user("user-123", limit=50)
        assert len(results) == 2
        assert results[0].user_id == "user-123"

    async def test_list_by_action(
        self, audit_service: AuditService, mock_supabase: MagicMock
    ) -> None:
        """Should return audit logs filtered by action type."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": "audit-id-5",
                "user_id": "doctor-789",
                "role": "doctor",
                "action": AuditAction.DOCTOR_VIEWED_PROFILE.value,
                "resource_type": "clinical_profile",
                "resource_id": "profile-001",
                "metadata": {"patient_id": "patient-123"},
                "created_at": "2025-01-02T00:00:00+00:00",
            },
        ]

        audit_repo = AuditRepository(mock_supabase)
        results = await audit_repo.list_by_action(
            AuditAction.DOCTOR_VIEWED_PROFILE.value, limit=50
        )
        assert len(results) == 1
        assert results[0].action == AuditAction.DOCTOR_VIEWED_PROFILE.value


class TestAuditCoverage:
    """Verify that all SRDS Section 11.3 audit events are defined.

    SRDS requires audit logs for:
    - Login and role-sensitive access
    - Doctor viewing patient profiles
    - Clinical profile generation
    - Differential diagnosis support generation
    - Crisis workflow activation
    - Consent acceptance
    - Administrative configuration changes
    """

    def test_all_required_audit_actions_defined(self) -> None:
        """All SRDS-required audit actions must exist in AuditAction enum."""
        required_actions = [
            "USER_LOGIN",
            "USER_REGISTERED",
            "DOCTOR_VIEWED_PROFILE",
            "CLINICAL_PROFILE_GENERATED",
            "CRISIS_WORKFLOW_ACTIVATED",
            "CONSENT_ACCEPTED",
            "ADMIN_CONFIG_CHANGE",
            "DOCTOR_ASSIGNMENT_CREATED",
            "DOCTOR_ASSIGNMENT_DEACTIVATED",
        ]
        for action_name in required_actions:
            assert hasattr(AuditAction, action_name), (
                f"AuditAction.{action_name} is required by SRDS Section 11.3 "
                f"but not defined in core/constants.py"
            )
```

---

## Task 2.24 (tiếp tục) — File 7: `backend/tests/test_assignment.py`

Doctor-patient assignment tests.

```python
# backend/tests/test_assignment.py
import pytest
from unittest.mock import MagicMock

from app.core.constants import UserRole
from app.core.exceptions import ForbiddenError, NotFoundError
from app.db.repositories.assignment_repo import AssignmentRepository
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.user_repo import UserRepository
from app.services.assignment_service import AssignmentService
from app.services.audit_service import AuditService


class TestAssignmentService:
    """Unit tests for AssignmentService."""

    @pytest.fixture
    def assignment_service(self, mock_supabase: MagicMock) -> AssignmentService:
        assignment_repo = AssignmentRepository(mock_supabase)
        user_repo = UserRepository(mock_supabase)
        audit_repo = AuditRepository(mock_supabase)
        audit_service = AuditService(audit_repo)
        return AssignmentService(
            assignment_repo=assignment_repo,
            user_repo=user_repo,
            audit_service=audit_service,
        )

    async def test_create_assignment(
        self, assignment_service: AssignmentService, mock_supabase: MagicMock
    ) -> None:
        """Should create a doctor-patient assignment."""
        # Mock: doctor exists with role=doctor
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": "doctor-001",
                "email": "doctor@example.com",
                "full_name": "Dr. Smith",
                "role": "doctor",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00+00:00",
            }
        ]

        # Mock: assignment insert
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {
                "id": "assign-001",
                "doctor_id": "doctor-001",
                "patient_id": "patient-001",
                "assigned_by": "admin-001",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00+00:00",
            }
        ]

        result = await assignment_service.create_assignment(
            doctor_id="doctor-001",
            patient_id="patient-001",
            assigned_by="admin-001",
        )
        assert result.doctor_id == "doctor-001"
        assert result.patient_id == "patient-001"
        assert result.is_active is True

    async def test_is_doctor_assigned_to_patient(
        self, assignment_service: AssignmentService, mock_supabase: MagicMock
    ) -> None:
        """Should return True if doctor is assigned to patient."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": "assign-001",
                "doctor_id": "doctor-001",
                "patient_id": "patient-001",
                "assigned_by": "admin-001",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00+00:00",
            }
        ]

        result = await assignment_service.is_doctor_assigned(
            doctor_id="doctor-001",
            patient_id="patient-001",
        )
        assert result is True

    async def test_is_doctor_not_assigned(
        self, assignment_service: AssignmentService, mock_supabase: MagicMock
    ) -> None:
        """Should return False if doctor is NOT assigned to patient."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

        result = await assignment_service.is_doctor_assigned(
            doctor_id="doctor-001",
            patient_id="patient-999",
        )
        assert result is False

    async def test_deactivate_assignment(
        self, assignment_service: AssignmentService, mock_supabase: MagicMock
    ) -> None:
        """Should soft-delete assignment by setting is_active=False."""
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": "assign-001",
                "doctor_id": "doctor-001",
                "patient_id": "patient-001",
                "assigned_by": "admin-001",
                "is_active": False,
                "created_at": "2025-01-01T00:00:00+00:00",
            }
        ]

        result = await assignment_service.deactivate_assignment(
            assignment_id="assign-001",
            deactivated_by="admin-001",
        )
        assert result.is_active is False

    async def test_list_patients_for_doctor(
        self, assignment_service: AssignmentService, mock_supabase: MagicMock
    ) -> None:
        """Should return all active assignments for a doctor."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": "assign-001",
                "doctor_id": "doctor-001",
                "patient_id": "patient-001",
                "assigned_by": "admin-001",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00+00:00",
            },
            {
                "id": "assign-002",
                "doctor_id": "doctor-001",
                "patient_id": "patient-002",
                "assigned_by": "admin-001",
                "is_active": True,
                "created_at": "2025-01-02T00:00:00+00:00",
            },
        ]

        # Access repo directly
        assignment_repo = AssignmentRepository(mock_supabase)
        results = await assignment_repo.list_patients_for_doctor("doctor-001")
        assert len(results) == 2


class TestAssignmentEndpoints:
    """Integration tests for assignment API endpoints."""

    def test_create_assignment_without_auth(self, client) -> None:
        """POST /api/v1/admin/assignments without token should return 401."""
        response = client.post(
            "/api/v1/admin/assignments",
            json={"doctor_id": "doc-1", "patient_id": "pat-1"},
        )
        assert response.status_code == 401

    def test_list_assignments_without_auth(self, client) -> None:
        """GET /api/v1/admin/assignments without token should return 401."""
        response = client.get("/api/v1/admin/assignments")
        assert response.status_code == 401

    def test_doctor_my_patients_without_auth(self, client) -> None:
        """GET /api/v1/admin/my-patients without token should return 401."""
        response = client.get("/api/v1/admin/my-patients")
        assert response.status_code == 401
```

---

## Task 2.25 — Verify

Sau khi hoàn thành tất cả tasks 2.1-2.24, chạy các bước verify sau:

### Bước 1: Kiểm tra dependencies

```bash
cd /path/to/project
uv sync
```

Đảm bảo không có lỗi dependency resolution. Kiểm tra `supabase`, `python-jose`, `passlib` đã được cài.

### Bước 2: Kiểm tra linting + type checking

```bash
make check
```

Đảm bảo:
- Ruff không báo lỗi (formatting + linting)
- Mypy không báo lỗi type (strict mode)

Nếu có lỗi Mypy, sửa bằng cách thêm type annotations hoặc `# type: ignore[specific-error]` cho third-party libs không có stubs (ví dụ `supabase`, `jose`).

### Bước 3: Chạy FastAPI server

```bash
make dev-be
```

Kiểm tra:
- Server starts thành công trên `http://localhost:8000`
- `GET http://localhost:8000/api/v1/health` trả về `{"status": "healthy", "version": "0.1.0"}`
- Swagger docs tại `http://localhost:8000/docs` hiển thị tất cả routers: health, auth, consent, admin
- Kiểm tra lifespan events log (Supabase client initialized / failed gracefully nếu chưa có credentials)

### Bước 4: Test API endpoints thủ công (dùng Swagger UI hoặc curl)

**Lưu ý:** Cần có Supabase project đã setup với schema.sql (task 2.3) và `.env` đã điền `SUPABASE_URL`, `SUPABASE_KEY`, `JWT_SECRET_KEY`.

```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!","full_name":"Test User"}'

# Expected: 201 Created with UserResponse

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}'

# Expected: 200 OK with {"access_token": "...", "token_type": "bearer", "user": {...}}

# 3. Get current user (use token from step 2)
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <TOKEN_FROM_STEP_2>"

# Expected: 200 OK with UserResponse

# 4. Test unauthorized access
curl http://localhost:8000/api/v1/auth/me

# Expected: 401 Unauthorized

# 5. Accept consent
curl -X POST http://localhost:8000/api/v1/consent/accept \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"policy_version":"1.0"}'

# Expected: 201 Created with ConsentResponse

# 6. Check consent status
curl http://localhost:8000/api/v1/consent/status \
  -H "Authorization: Bearer <TOKEN>"

# Expected: 200 OK with {"has_accepted": true, "current_policy_version": "1.0", ...}

# 7. Test RBAC — patient trying admin endpoint
curl http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer <PATIENT_TOKEN>"

# Expected: 403 Forbidden
```

### Bước 5: Chạy automated tests

```bash
cd backend
uv run pytest tests/ -v --tb=short
```

Đảm bảo:
- Tất cả unit tests pass (test_auth, test_rbac, test_consent, test_audit, test_assignment)
- Không có warnings nghiêm trọng
- Coverage report (nếu có): aim for >80% trên services/ và core/

### Bước 6: Chạy Streamlit frontend

```bash
make dev-fe
```

Kiểm tra frontend vẫn chạy bình thường (không bị break bởi backend changes).

### Bước 7: Pre-commit hooks

```bash
git add -A
git commit -m "feat: implement Milestone 2 - Data and Auth Foundation"
```

Pre-commit hooks sẽ tự động chạy Ruff + Mypy. Nếu fail, sửa lỗi và commit lại.

---

## Task 2.26 — Cập nhật `frontend/main.py` — Google OAuth + Email/Password Login UI

Thay thế nội dung `frontend/main.py` hiện tại bằng version mới hỗ trợ cả đăng nhập Email/Password lẫn Google OAuth. Frontend dùng Streamlit.

```python
# frontend/main.py
import requests
import streamlit as st

from config import settings

st.set_page_config(page_title="Mental Health AI", page_icon="🧠", layout="wide")

BACKEND_URL = settings.backend_url


# ─── Handle OAuth Callback ──────────────────────────────────────────────────
# Khi Supabase redirect về frontend với ?access_token=...&user_name=...,
# đọc query params và lưu vào session state.
query_params = st.query_params
if "access_token" in query_params:
    st.session_state["access_token"] = query_params["access_token"]
    st.session_state["user_name"] = query_params.get("user_name", "User")
    st.query_params.clear()  # Xóa query params khỏi URL


# ─── Auth State ──────────────────────────────────────────────────────────────

if "access_token" in st.session_state:
    # ── Đã đăng nhập ──
    st.sidebar.success(f"Xin chào, {st.session_state.get('user_name', 'User')}!")

    if st.sidebar.button("🚪 Đăng xuất"):
        del st.session_state["access_token"]
        if "user_name" in st.session_state:
            del st.session_state["user_name"]
        st.rerun()

    st.title("🧠 Mental Health AI Platform")
    st.write("Chào mừng bạn đến với nền tảng hỗ trợ sức khỏe tâm thần.")
    st.info("Các tính năng chat và phân tích sẽ được bổ sung ở các milestone tiếp theo.")

else:
    # ── Chưa đăng nhập ──
    st.title("🧠 Mental Health AI Platform")
    st.subheader("Đăng nhập để tiếp tục")

    col_email, col_google = st.columns(2)

    # ── Cột trái: Email/Password ──
    with col_email:
        st.markdown("### 📧 Đăng nhập bằng Email")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Mật khẩu", type="password")
            submitted = st.form_submit_button("Đăng nhập")

            if submitted:
                if email and password:
                    try:
                        resp = requests.post(
                            f"{BACKEND_URL}/api/v1/auth/login",
                            json={"email": email, "password": password},
                            timeout=10,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state["access_token"] = data["access_token"]
                            st.session_state["user_name"] = data["user"]["full_name"]
                            st.rerun()
                        else:
                            st.error(resp.json().get("detail", "Đăng nhập thất bại"))
                    except requests.exceptions.ConnectionError:
                        st.error("Không thể kết nối đến server. Hãy đảm bảo backend đang chạy.")
                else:
                    st.warning("Vui lòng nhập email và mật khẩu.")

    # ── Cột phải: Google OAuth ──
    with col_google:
        st.markdown("### 🔑 Đăng nhập bằng Google")
        st.write("Đăng nhập hoặc đăng ký nhanh bằng tài khoản Google của bạn.")

        if st.button("🌐 Đăng nhập với Google", use_container_width=True):
            try:
                resp = requests.get(
                    f"{BACKEND_URL}/api/v1/auth/google",
                    timeout=10,
                )
                if resp.status_code == 200:
                    google_url = resp.json()["url"]
                    st.markdown(
                        f'<meta http-equiv="refresh" content="0;url={google_url}">',
                        unsafe_allow_html=True,
                    )
                else:
                    st.error("Không thể lấy Google login URL.")
            except requests.exceptions.ConnectionError:
                st.error("Không thể kết nối đến server.")
```

**Giải thích:**
- **OAuth callback handling:** Khi Supabase hoàn tất Google login, backend redirect về frontend với `?access_token=...&user_name=...`. Streamlit đọc `st.query_params` để lưu token.
- **2 cột login:** Email/Password (trái) + Google OAuth (phải) — user chọn 1 trong 2 cách.
- **Google button:** Gọi `GET /api/v1/auth/google` để lấy OAuth URL, rồi dùng `meta refresh` để redirect user đến Google.
- **Logout:** Xóa `access_token` khỏi `st.session_state` và rerun app.

> **Lưu ý:** File `frontend/config.py` cần import `backend_url` từ settings. Nếu settings chưa có field này, thêm `backend_url: str = "http://localhost:8000"` vào `frontend/config.py`.

---

## Task 2.27 — Setup Google OAuth bên ngoài code (manual, 1 lần)

Đây là các bước setup thủ công cần thực hiện 1 lần trước khi Google OAuth hoạt động:

### Bước 1: Google Cloud Console

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo hoặc chọn project
3. Vào **APIs & Services → Credentials**
4. Tạo **OAuth 2.0 Client ID** (Application type: Web application)
5. Thêm **Authorized redirect URI**: `https://<SUPABASE_PROJECT_REF>.supabase.co/auth/v1/callback`
6. Copy **Client ID** và **Client Secret**

### Bước 2: Supabase Dashboard

1. Truy cập [Supabase Dashboard](https://supabase.com/dashboard)
2. Chọn project → **Authentication → Providers**
3. Tìm **Google** → Enable
4. Paste **Client ID** và **Client Secret** từ bước 1
5. Save

### Bước 3: Cập nhật `.env`

```env
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
FRONTEND_URL=http://localhost:8501
BACKEND_URL=http://localhost:8000
```

### Bước 4: Verify

1. Chạy backend: `make dev-be`
2. Chạy frontend: `make dev-fe`
3. Mở `http://localhost:8501`
4. Click **"Đăng nhập với Google"**
5. Đăng nhập bằng tài khoản Google
6. Kiểm tra redirect về frontend với token
7. Kiểm tra user đã được tạo trong bảng `users` với `auth_provider='google'`

---
