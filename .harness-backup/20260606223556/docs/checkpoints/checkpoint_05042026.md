# Project Checkpoint — Mental Health Sovereign Agentic AI Platform

**Purpose of this file:**
This file is a handoff/checkpoint document for continuing the current project work in a new chat. It summarizes the project context, the working style expected from the assistant, the architectural decisions made so far, the implementation status, and the next steps.

**Recommended usage in the next chat:**
Upload or paste this file first, then upload the latest project files or provide terminal outputs requested in the final section.

---

# 1. Project Identity

## Project name

**Mental Health Sovereign Agentic AI Platform**

## High-level vision

The project is a **privacy-first, self-hostable, human-in-the-loop AI platform for mental health support and clinical workflow assistance**.

It supports two main user groups:

1. **Patients**
   - Can chat with an empathetic AI support companion.
   - Receive psychological first-aid, coping exercises, grounding, journaling prompts, and crisis-safe guidance.
   - Must **not** receive diagnostic labels or disorder names from the AI.

2. **Doctors / Counselors**
   - Can view assigned patients.
   - Can review AI-generated clinical profiles after patient sessions.
   - Can see risk/stress scores, evidence snippets, and doctor-facing decision-support content.
   - Can later use a doctor copilot grounded in patient profile data and DSM-5/treatment knowledge.

The AI is **not a replacement for licensed professionals**. Doctor-facing outputs are decision-support artifacts only.

---

# 2. Product and Safety Principles

These principles must guide all implementation decisions:

1. **Privacy-first**
   - Minimize sensitive data exposure.
   - Mental health chat, clinical profile, risk scores, and audit logs are sensitive.

2. **Self-hostable / sovereign target**
   - The platform should eventually run in private cloud, dedicated VPC, on-premise, or air-gapped environments.
   - Managed Supabase Cloud is acceptable for dev/demo with fake data, but not automatically for real patient data without policy/compliance review.

3. **Human-in-the-loop**
   - AI assists clinicians but does not make final diagnosis or treatment decisions.

4. **No direct diagnosis for patients**
   - Patient-facing AI must avoid disorder labels and clinical diagnosis claims.
   - DSM-5 reasoning and differential diagnosis support must remain doctor-facing only.

5. **Doctor assignment enforcement**
   - Doctors can only access patients assigned to them.
   - This must be enforced in FastAPI backend, not frontend.

6. **Audit-ready operations**
   - Login, consent acceptance, doctor access, assignment changes, crisis workflow activation, clinical profile generation, and doctor copilot queries should be audit logged.

7. **Backend-enforced authorization first**
   - MVP uses FastAPI JWT/RBAC/assignment checks as the primary authorization layer.
   - Production-grade PostgreSQL/Supabase RLS is deferred as a hardening step.

8. **Evidence-grounded clinical reasoning**
   - Doctor-facing clinical reasoning should later be grounded in retrieved DSM-5/treatment evidence.
   - If evidence is weak, the system should state uncertainty.

---

# 3. Source Documents and Current Planning Files

The project currently has or should have these important docs:

```text
docs/SRDS.md
docs/DFD.md
docs/DATABASE_MODEL.md
docs/schema.sql
docs/_notes/[3]E2E_database_design_and_development_fit.md
```

Additional planning files provided earlier:

```text
MASTER_PLAN.md
MILESTONE1.md
MILESTONE2.md
```

## Source-of-truth hierarchy

1. **SRDS.md**
   - Product, architecture, safety, privacy, clinical rules.

2. **MASTER_PLAN.md**
   - 7 milestone roadmap for MVP.

3. **MILESTONE1.md**
   - Foundation tasks already completed.

4. **MILESTONE2.md**
   - Current implementation backlog: Data & Auth Foundation.

5. **DATABASE_MODEL.md**
   - Current database modeling reference for Milestone 2.

6. **docs/schema.sql**
   - SQL schema reference for Application DB.

---

# 4. Tech Stack

## MVP stack

```text
Backend: FastAPI
Frontend: Streamlit
Package/dependency manager: uv workspace
Agent orchestration: LangGraph
RAG framework: LlamaIndex
Vector database: Qdrant
Application DB/Auth: Supabase/PostgreSQL
Observability: Langfuse later
Deployment: local/dev first; Docker Compose/private infra later
```

## Important stack boundaries

```text
Supabase/PostgreSQL = Application DB
Qdrant = vector knowledge/RAG database
Langfuse = LLM traces/observability, not application audit log
```

Application DB stores:

- users
- doctor-patient assignments
- consent records
- chat sessions
- chat messages
- clinical profiles
- stress/risk scores
- audit logs

Qdrant stores later:

- DSM-5 chunks
- treatment/coping chunks
- policy/safety chunks

---

# 5. Repository Baseline

The project uses a uv workspace.

Expected root structure from latest observed state:

```text
.
├── backend
│   ├── app
│   │   ├── agents
│   │   ├── api
│   │   ├── core
│   │   ├── db
│   │   ├── ingestion
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── schemas
│   │   └── services
│   ├── data
│   │   ├── processed
│   │   └── raw
│   ├── pyproject.toml
│   ├── README.md
│   └── tests
│       └── __init__.py
├── docs
│   ├── AGENT.md
│   ├── DFD.md
│   ├── SRDS.md
│   ├── DATABASE_MODEL.md
│   ├── schema.sql
│   └── _notes
├── frontend
│   ├── components
│   ├── main.py
│   ├── pages
│   ├── pyproject.toml
│   └── README.md
├── Makefile
├── pyproject.toml
├── README.md
└── uv.lock
```

Important detail:

```text
Frontend entrypoint is frontend/main.py, not frontend/app.py.
```

The Makefile runs:

```makefile
dev-be:
	cd backend && uv run uvicorn app.main:app --reload

dev-fe:
	cd frontend && uv run streamlit run main.py

check:
	uv run ruff check .
	uv run mypy .
```

There may also be a `make lint` command locally; `make check` is the canonical quality gate used in this conversation.

---

# 6. User Preferences for Assistant Behavior

The assistant in the next chat should act as a **staff engineer / technical coordinator**.

The user wants to implement the project step by step and understand the purpose of each step.

## Required response structure for implementation steps

Every time the assistant asks the user to create a file, write code, or modify code, use this structure:

```text
1. Goal
2. Vì sao cần làm bước này
3. File cần tạo/sửa
4. Code/nội dung cần thêm
5. Giải thích code chính
6. Cách kiểm tra
7. Kết quả cần báo lại
8. Có commit không + commit command/message
```

## Coordination style

- Be direct and clear.
- Work as if pair-programming with the user.
- Explain why a file exists and where it fits in the architecture.
- Do not dump unrelated future work.
- Move in small logical units, but not too tiny if the user asks to speed up.
- When a step is complete, state the next step.
- For every answer, include whether to commit or not.
- If commit is recommended, provide the exact `git add` and `git commit -m "..."` command.
- If not committing, explain why.

## Code style requirements

The user explicitly requested:

- Code must have full type hints.
- Follow PEP 8 style.
- Must pass `mypy` with `strict = true` from root config.
- Avoid `Any` unless unavoidable.
- Prefer:
  - `str | None` instead of `Optional[str]`
  - `dict[str, object]` or JSON-specific aliases instead of `dict[str, Any]`
  - `list[...]` instead of `List[...]`
  - `Mapping[...]` for covariant read-only row data where useful
- Use explicit imports.
- Keep `__init__.py` files empty unless there is a clear reason to re-export.
- Do not put setup side effects in `__init__.py`.

## Dependency management rule

This is a uv workspace. Backend dependencies must be added with:

```bash
uv add --package backend <package>
```

Do **not** run plain `uv add <package>` unless intentionally adding to root.

Example:

```bash
uv add --package backend supabase
uv add --package backend python-jose[cryptography]
uv add --package backend passlib[bcrypt]
uv add --package backend email-validator
```

---

# 7. Confirmed Milestone Status

## Milestone 1 — Foundation

Status: **completed and verified**.

Verified outputs:

```text
git status: clean
make check: pass
backend health: pass
frontend: pass
```

Observed backend health endpoint:

```json
{"status":"healthy","version":"0.1.0"}
```

Current baseline files existed before Milestone 2 work:

```text
backend/app/main.py
backend/app/api/health.py
backend/app/core/config.py
backend/app/db/__init__.py
backend/app/schemas/__init__.py
backend/app/services/__init__.py
frontend/main.py
docs/DFD.md
.env
.env.example
Makefile
```

Milestone 1 frontend has a Streamlit health-check button that calls:

```python
requests.get("http://localhost:8000/api/v1/health")
```

This is acceptable for Milestone 1. Later it should use `BACKEND_URL` config instead of hardcoded URL.

---

# 8. Milestone 2 Scope

Milestone 2 is **Data & Auth Foundation**.

Goal:

- Supabase/PostgreSQL schema
- Supabase client
- Repository pattern
- JWT auth
- Google OAuth through Supabase
- RBAC
- Consent tracking
- Doctor-patient assignments
- Audit logging
- Basic API endpoints
- Basic frontend auth UI later
- Tests

Milestone 2 does **not** include:

- RAG ingestion
- Qdrant collections
- LangGraph agents
- DSM-5 retrieval
- Doctor copilot workflow
- Clinical dashboard UI
- Production-grade RLS
- Production backup/PITR automation

---

# 9. Database Modeling Decisions

The file `docs/DATABASE_MODEL.md` was created/updated and should model all 8 core tables:

```text
1. users
2. doctor_assignments
3. consent_records
4. chat_sessions
5. chat_messages
6. clinical_profiles
7. stress_risk_scores
8. audit_logs
```

## Important modeling updates already made

### users.auth_user_id

The user updated `DATABASE_MODEL.md` to include:

```text
users.auth_user_id UUID nullable
```

Purpose:

```text
users.id = application user id
users.auth_user_id = Supabase Auth auth.users.id, if applicable
```

This helps map Supabase Auth users to application users.

Recommended SQL index:

```sql
CREATE UNIQUE INDEX IF NOT EXISTS unique_users_auth_user_id
ON users(auth_user_id)
WHERE auth_user_id IS NOT NULL;
```

### clinical_profiles JSONB normalization note

The user also updated the modeling notes to document that:

- `clinical_profiles.symptoms`
- `clinical_profiles.risk_markers`
- `clinical_profiles.evidence_snippets`

are JSONB for MVP flexibility.

Future normalization path if analytics/reporting become important:

```text
symptom_catalog
clinical_profile_symptoms
```

This is a future improvement, not Milestone 2 implementation.

---

# 10. docs/schema.sql

Status: User reported **DB-2.1 done**.

Location:

```text
docs/schema.sql
```

Important clarification:

```text
docs/schema.sql = SQL database schema reference
backend/app/schemas/*.py = Pydantic API/data schemas
```

`schema.sql` should include `auth_user_id` in `users`.

Recommended `users` block:

```sql
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Supabase Auth mapping
    auth_user_id UUID,

    email CITEXT UNIQUE NOT NULL,
    password_hash VARCHAR(255),

    full_name VARCHAR(255) NOT NULL,

    role VARCHAR(20) NOT NULL
        CHECK (role IN ('patient', 'doctor', 'admin')),

    auth_provider VARCHAR(50) NOT NULL DEFAULT 'local'
        CHECK (auth_provider IN ('local', 'google')),

    provider_user_id VARCHAR(255),
    avatar_url TEXT,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT users_google_provider_requires_provider_user_id
        CHECK (
            auth_provider != 'google'
            OR provider_user_id IS NOT NULL
        )
);
```

Important: the previous DB-level constraint requiring local users to have a password was intentionally removed. Password requirement should be enforced in `AuthService.register`, not locked too rigidly in DB.

Recommended index:

```sql
CREATE UNIQUE INDEX IF NOT EXISTS unique_users_auth_user_id
ON users(auth_user_id)
WHERE auth_user_id IS NOT NULL;
```

Schema should use:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;
```

Rationale:

- `pgcrypto` gives `gen_random_uuid()`.
- `citext` gives case-insensitive email behavior.

---

# 11. Completed / Instructed Implementation Steps

This section distinguishes confirmed steps from instructed-but-not-confirmed steps.

## DB-2.2 — Backend dependencies

User reported done.

Dependencies added to backend:

```text
supabase
python-jose[cryptography]
passlib[bcrypt]
```

Also later added for Pydantic `EmailStr`:

```text
email-validator
```

Correct install commands:

```bash
uv add --package backend supabase
uv add --package backend python-jose[cryptography]
uv add --package backend passlib[bcrypt]
uv add --package backend email-validator
```

## DB-2.3 — backend/app/core/config.py

User reported done and `make check` pass.

Expected config fields:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "Mental Health AI Platform"
    app_version: str = "0.1.0"
    debug: bool = False

    # External Services
    openai_api_key: str = ""
    qdrant_url: str = "http://localhost:6333"

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""

    # JWT
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    # OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # App URLs
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:8501"

    # Consent
    current_consent_policy_version: str = "v1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

`.env.example` should include:

```env
OPENAI_API_KEY=
QDRANT_URL=http://localhost:6333

SUPABASE_URL=
SUPABASE_KEY=

JWT_SECRET_KEY=change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:8501

CURRENT_CONSENT_POLICY_VERSION=v1
```

## DB-2.4 — backend/app/db/supabase_client.py

User reported done.

Purpose:

- Single connection manager for Supabase client.
- Foundation for repository layer.
- Avoid scattered `create_client(...)` calls.

Expected file:

```python
from supabase import Client, create_client

from app.core.config import settings


class SupabaseClientManager:
    _client: Client | None

    def __init__(self) -> None:
        self._client = None

    def get_client(self) -> Client:
        if self._client is None:
            if not settings.supabase_url or not settings.supabase_key:
                raise ValueError("Supabase URL and KEY must be set in environment variables")

            self._client = create_client(
                settings.supabase_url,
                settings.supabase_key,
            )
        return self._client


supabase_client_manager = SupabaseClientManager()


def get_supabase_client() -> Client:
    return supabase_client_manager.get_client()
```

Potential commit message for DB-2.2 to DB-2.4:

```bash
git add backend/pyproject.toml backend/app/core/config.py backend/app/db/supabase_client.py .env.example uv.lock
git commit -m "feat(backend): setup data/auth foundation (dependencies, config, supabase client)"
```

## DB-2.5 — backend/app/core/constants.py

Instructed. User later moved on, likely completed, but new chat should verify file exists.

Purpose:

- Central enum vocabulary for roles, providers, statuses, severities, audit actions.
- Avoid string typos.

Expected enums:

```text
AuthProvider: local, google
UserRole: patient, doctor, admin
SessionStatus: active, closed, timeout
MessageRole: user, assistant, system
SafetySeverity: none, low, medium, high, critical
RiskSeverity: low, medium, high, critical
AuditAction:
  user_registered
  user_login
  consent_accepted
  session_started
  session_closed
  crisis_workflow_activated
  clinical_profile_generated
  doctor_viewed_profile
  differential_diagnosis_generated
  doctor_copilot_query
  doctor_assignment_created
  assignment_deactivated
  admin_config_change
```

Potential commit:

```bash
git add backend/app/core/constants.py
git commit -m "feat(backend): add core domain constants and enums"
```

## DB-2.6 — backend/app/core/exceptions.py

Instructed. User moved on, likely completed, but new chat should verify.

Purpose:

- Central exception hierarchy.
- Avoid direct `HTTPException` throughout service layer.
- FastAPI handler converts app exceptions to consistent JSON.

Expected exception classes:

```text
AppException
NotFoundError
AlreadyExistsError
UnauthorizedError
ForbiddenError
InvalidCredentialsError
ConsentRequiredError
DatabaseError
app_exception_handler
```

Potential commit:

```bash
git add backend/app/core/exceptions.py
git commit -m "feat(backend): add application exception hierarchy"
```

## DB-2.7 — Pydantic schemas

Instructed. User moved on, likely completed, but new chat should verify.

Files expected:

```text
backend/app/schemas/user.py
backend/app/schemas/consent.py
backend/app/schemas/audit.py
backend/app/schemas/assignment.py
backend/app/schemas/session.py
```

Purpose:

- API request/response contracts.
- Avoid exposing `password_hash`.
- Provide typed models for repositories/services.

Important schema names:

```text
UserCreate
UserLogin
GoogleExchangeRequest
UserResponse
TokenResponse

ConsentAcceptRequest
ConsentResponse
ConsentStatusResponse

AuditLogCreate
AuditLogResponse

AssignmentCreateRequest
AssignmentResponse

ChatSessionResponse
ChatMessageResponse
```

Potential commit:

```bash
git add backend/pyproject.toml uv.lock backend/app/schemas/user.py backend/app/schemas/consent.py backend/app/schemas/audit.py backend/app/schemas/assignment.py backend/app/schemas/session.py
git commit -m "feat(backend): add Pydantic schemas for data and auth models"
```

## DB-2.8 — BaseRepository

User reported mypy initially failed, then fixed and passed.

Expected file:

```text
backend/app/db/repositories/base.py
```

A directory should exist:

```text
backend/app/db/repositories/__init__.py
```

`__init__.py` should stay empty.

Important fix:

- Supabase typing rejected `dict[str, object]` for `.insert()` / `.update()`.
- Fixed using JSON type aliases and `Mapping`.

Expected type aliases:

```python
from typing import TypeAlias

JSONValue: TypeAlias = (
    str
    | int
    | float
    | bool
    | None
    | list["JSONValue"]
    | dict[str, "JSONValue"]
)

JSONRow: TypeAlias = dict[str, JSONValue]
```

Important BaseRepository methods:

```text
_to_model(row: Mapping[str, JSONValue]) -> ModelT
_first_row(data: object) -> JSONRow | None
get_by_id(record_id: str) -> ModelT | None
create(data: JSONRow) -> ModelT
update(record_id: str, data: JSONRow) -> ModelT | None
delete(record_id: str) -> bool
```

Potential commit:

```bash
git add backend/app/db/repositories/__init__.py backend/app/db/repositories/base.py
git commit -m "feat(backend): add base repository for Supabase data access"
```

## DB-2.9 — UserRepository

Instructed. User asked for next step, so likely completed, but new chat should verify.

Expected file:

```text
backend/app/db/repositories/user_repo.py
```

Purpose:

- Query `users` table.
- Support auth/RBAC/admin workflows.

Expected methods:

```text
get_by_email(email: str) -> JSONRow | None
email_exists(email: str) -> bool
get_by_auth_user_id(auth_user_id: str) -> JSONRow | None
get_by_provider_identity(auth_provider: AuthProvider, provider_user_id: str) -> JSONRow | None
list_by_role(role: UserRole) -> list[UserResponse]
deactivate(user_id: str) -> UserResponse | None
```

Important reason `get_by_email` returns raw `JSONRow`:

- Login needs `password_hash`.
- `UserResponse` intentionally does not expose `password_hash`.

Potential commit:

```bash
git add backend/app/db/repositories/user_repo.py
git commit -m "feat(backend): add user repository"
```

## DB-2.10 — ConsentRepository

This was the **last instructed step** before creating this checkpoint.

Status: **not confirmed done in original chat**.

Expected file:

```text
backend/app/db/repositories/consent_repo.py
```

Purpose:

- Query `consent_records` table.
- Check if user accepted current policy version.
- Get latest consent.

If not yet created, create it with:

```python
from collections.abc import Mapping
from typing import cast

from supabase import Client

from app.core.exceptions import DatabaseError
from app.db.repositories.base import BaseRepository, JSONRow, JSONValue
from app.schemas.consent import ConsentResponse


class ConsentRepository(BaseRepository[ConsentResponse]):
    """Repository for consent_records table."""

    def __init__(self, db: Client) -> None:
        super().__init__(db=db, table_name="consent_records")

    def _to_model(self, row: Mapping[str, JSONValue]) -> ConsentResponse:
        """Convert a raw consent_records row into a response model."""
        return ConsentResponse.model_validate(dict(row))

    def _rows(self, data: object) -> list[JSONRow]:
        """Convert a Supabase response payload into a list of JSON rows."""
        if not isinstance(data, list):
            return []

        rows: list[JSONRow] = []
        for item in data:
            if isinstance(item, dict):
                rows.append(cast(JSONRow, item))

        return rows

    async def get_latest_by_user(self, user_id: str) -> ConsentResponse | None:
        """Return the most recent consent record for a user."""
        try:
            result = (
                self._db.table(self._table_name)
                .select("*")
                .eq("user_id", user_id)
                .order("accepted_at", desc=True)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to fetch latest consent record") from exc

        row = self._first_row(result.data)
        if row is None:
            return None

        return self._to_model(row)

    async def has_accepted_version(self, user_id: str, policy_version: str) -> bool:
        """Return True when a user has accepted a specific policy version."""
        try:
            result = (
                self._db.table(self._table_name)
                .select("id")
                .eq("user_id", user_id)
                .eq("policy_version", policy_version)
                .eq("accepted", True)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to check consent policy version") from exc

        return self._first_row(result.data) is not None

    async def list_by_user(self, user_id: str) -> list[ConsentResponse]:
        """List all consent records for a user, newest first."""
        try:
            result = (
                self._db.table(self._table_name)
                .select("*")
                .eq("user_id", user_id)
                .order("accepted_at", desc=True)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to list consent records") from exc

        return [self._to_model(row) for row in self._rows(result.data)]
```

After creation:

```bash
make check
```

Potential commit:

```bash
git add backend/app/db/repositories/consent_repo.py
git commit -m "feat(backend): add consent repository"
```

---

# 12. Important Design Decisions Made During Work

## __init__.py files

Current decision:

```text
Keep __init__.py files empty unless there is a clear need to re-export package APIs.
```

Reason:

- Codebase is still small.
- Explicit imports are easier to trace.
- Avoid import cycles and side effects.

## Supabase setup timing

The user asked why Supabase/project/tool setup had not happened yet.

Decision/explanation:

```text
We intentionally delayed actual Supabase project setup until after modeling, schema, config, client, and repository foundation.
```

Reason:

- Schema was still changing (`auth_user_id`, JSONB notes, constraints).
- Applying SQL too early would cause rework.
- Backend was not ready to test real queries.

Recommended sequence:

```text
Design/modeling
→ schema.sql
→ config/client/repository foundation
→ Supabase project setup
→ apply schema
→ test connection and CRUD queries
```

However, if user wants infrastructure earlier, it is acceptable to insert a Supabase setup step after repositories are partially ready.

---

# 13. Next Steps After This Checkpoint

The next chat should first verify actual repo state because some steps were instructed but not all were explicitly confirmed.

## Immediate verification commands

Ask user to run and paste:

```bash
git status
find backend/app -maxdepth 4 -type f | sort
make check
git log --oneline -n 10
```

This will reveal:

- which files were actually created;
- whether commits were made;
- whether DB-2.10 was completed;
- whether repo is clean.

## If DB-2.10 is not done

Continue with:

```text
DB-2.10 — ConsentRepository
```

Then `make check`, then commit.

## If DB-2.10 is done

Proceed with:

```text
DB-2.11 — AuditRepository
DB-2.12 — AssignmentRepository
DB-2.13 — AuthService
DB-2.14 — AuditService
DB-2.15 — ConsentService
DB-2.16 — AssignmentService
DB-2.17 — security.py for JWT utilities/RBAC
DB-2.18 — api/dependencies.py for FastAPI DI
DB-2.19 — auth.py routes
DB-2.20 — consent.py routes
DB-2.21 — admin.py routes
DB-2.22 — update main.py with routers + exception handler
DB-2.23 — Supabase project setup and apply docs/schema.sql
DB-2.24 — smoke test connection and basic DB operations
DB-2.25 — tests for auth/RBAC/consent/audit/assignment
DB-2.26 — frontend auth UI in frontend/main.py or pages
DB-2.27 — Google OAuth setup in Google Cloud Console + Supabase Dashboard
```

The exact numbering can be adjusted, but keep logical order.

---

# 14. Proposed Upcoming Repository Files

Expected repository files after finishing repository layer:

```text
backend/app/db/repositories/base.py
backend/app/db/repositories/user_repo.py
backend/app/db/repositories/consent_repo.py
backend/app/db/repositories/audit_repo.py
backend/app/db/repositories/assignment_repo.py
```

## DB-2.11 — AuditRepository should support

```text
list_by_user(user_id: str, limit: int = 50) -> list[AuditLogResponse]
list_by_action(action: AuditAction, limit: int = 50) -> list[AuditLogResponse]
list_by_resource(resource_type: str, resource_id: str, limit: int = 50) -> list[AuditLogResponse]
```

Potential commit:

```bash
git add backend/app/db/repositories/audit_repo.py
git commit -m "feat(backend): add audit repository"
```

## DB-2.12 — AssignmentRepository should support

```text
get_active_assignment(doctor_id: str, patient_id: str) -> AssignmentResponse | None
is_assigned(doctor_id: str, patient_id: str) -> bool
list_patients_for_doctor(doctor_id: str) -> list[AssignmentResponse]
list_doctors_for_patient(patient_id: str) -> list[AssignmentResponse]
deactivate(assignment_id: str) -> AssignmentResponse | None
```

Potential commit:

```bash
git add backend/app/db/repositories/assignment_repo.py
git commit -m "feat(backend): add doctor assignment repository"
```

---

# 15. Future Services Layer Plan

After repositories, create services.

Expected files:

```text
backend/app/services/auth_service.py
backend/app/services/audit_service.py
backend/app/services/consent_service.py
backend/app/services/assignment_service.py
```

## AuthService responsibilities

- Register local user.
- Hash password using bcrypt/passlib.
- Login local user.
- Verify password.
- Create app JWT.
- Decode JWT or delegate decode to security module.
- Google OAuth URL generation through Supabase.
- Google OAuth callback handling.
- Map Supabase/Auth/Google identity to `users` table.
- Use `auth_user_id` where available.
- Issue app JWT after OAuth.
- Log auth events.

Important: do not return or expose `password_hash`.

## AuditService responsibilities

- Central logging method.
- Avoid raw sensitive data in audit metadata.
- Log user_id, role, action, resource_type, resource_id, metadata, ip_address.

## ConsentService responsibilities

- Accept consent.
- Check if user accepted current policy version.
- Return latest consent/status.
- Use `settings.current_consent_policy_version`.
- Log consent acceptance.

## AssignmentService responsibilities

- Create/deactivate doctor-patient assignments.
- Ensure doctor_id has role doctor.
- Ensure patient_id has role patient.
- Ensure assigned_by is admin/current admin user.
- Check assignment for doctor access.
- Log assignment changes.

---

# 16. Future API Layer Plan

Expected files:

```text
backend/app/api/dependencies.py
backend/app/api/auth.py
backend/app/api/consent.py
backend/app/api/admin.py
```

## dependencies.py

Should wire:

```text
get_supabase
get_user_repo
get_consent_repo
get_audit_repo
get_assignment_repo
get_audit_service
get_auth_service
get_consent_service
get_assignment_service
get_current_user
```

## auth.py

Endpoints:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
GET /api/v1/auth/me
GET /api/v1/auth/google/url
GET /api/v1/auth/google/callback
POST /api/v1/auth/google/exchange
```

Google OAuth flow should avoid passing JWT directly in URL. Use a short-lived one-time code from backend callback, then frontend exchanges via POST.

## consent.py

Endpoints:

```text
POST /api/v1/consent/accept
GET /api/v1/consent/status
```

## admin.py

Endpoints:

```text
GET /api/v1/admin/users
GET /api/v1/admin/users/doctors
GET /api/v1/admin/users/patients
POST /api/v1/admin/assignments
PATCH /api/v1/admin/assignments/{assignment_id}/deactivate
GET /api/v1/admin/assignments
GET /api/v1/doctor/my-patients
```

Exact endpoint layout can be adjusted, but keep role checks and assignment checks strict.

---

# 17. Supabase Setup Plan

Supabase setup has not been fully coordinated yet.

Recommended when ready:

## Step S-1 — choose environment

For current dev:

```text
Managed Supabase dev project is acceptable if using fake/dev data.
```

Do not use real patient data.

## Step S-2 — create project

Need:

```text
SUPABASE_URL
SUPABASE_KEY
DATABASE_URL optional for psql
```

Clarify key:

- Backend can use service role key in local/dev server-side environment.
- Never expose service role key to frontend.
- `.env` is not committed.
- `.env.example` only contains placeholders.

## Step S-3 — run schema

Use Supabase SQL Editor or psql:

```bash
psql "$DATABASE_URL" -f docs/schema.sql
```

or paste contents of `docs/schema.sql` into Supabase SQL Editor.

## Step S-4 — update .env

```env
SUPABASE_URL=...
SUPABASE_KEY=...
JWT_SECRET_KEY=...
```

Generate JWT secret locally:

```bash
openssl rand -hex 32
```

## Step S-5 — smoke test client

Do not build a full API first. A small temporary script or health extension can verify Supabase connection.

Do not commit `.env`.

---

# 18. Current Risks / Things To Verify in New Chat

The next chat should verify these before continuing:

1. Did the user actually commit DB-2.2 to DB-2.4?
2. Did the user commit DB-2.5 constants?
3. Did the user commit DB-2.6 exceptions?
4. Did the user commit DB-2.7 schemas?
5. Did the user commit DB-2.8 BaseRepository?
6. Did the user complete and commit DB-2.9 UserRepository?
7. Did the user complete DB-2.10 ConsentRepository?
8. Does `make check` still pass?
9. Does `docs/schema.sql` include `auth_user_id`?
10. Does `DATABASE_MODEL.md` include `auth_user_id` and clinical_profiles JSONB normalization notes?

Use terminal commands:

```bash
git status
git log --oneline -n 10
find backend/app -maxdepth 4 -type f | sort
make check
grep -n "auth_user_id" docs/schema.sql docs/DATABASE_MODEL.md
```

---

# 19. Guidance for the Next Assistant

The next assistant should not restart from scratch.

It should ask the user for current repo state and continue from the first incomplete step.

Recommended opening in new chat:

```text
Đọc checkpoint này. Tôi đang làm Milestone 2 của Mental Health Sovereign Agentic AI Platform.
Hãy tiếp tục đóng vai staff engineer/technical coordinator.
Trước khi điều phối tiếp, hãy yêu cầu tôi cung cấp git status, git log, find backend/app, make check để xác định bước hiện tại.
```

Then the assistant should continue according to actual state.

---

# 20. What the User Should Provide in the New Chat

To continue smoothly, provide:

## Required

1. This `checkpoint.md` file.
2. Current terminal output:

```bash
git status
git log --oneline -n 10
find backend/app -maxdepth 4 -type f | sort
make check
```

3. Current `docs/schema.sql` if continuing database setup.
4. Current `docs/DATABASE_MODEL.md` if reviewing schema/model alignment.

## Very useful

Paste or upload these files if asked:

```text
backend/app/core/config.py
backend/app/core/constants.py
backend/app/core/exceptions.py
backend/app/db/supabase_client.py
backend/app/db/repositories/base.py
backend/app/db/repositories/user_repo.py
backend/app/db/repositories/consent_repo.py
backend/app/schemas/user.py
backend/app/schemas/consent.py
backend/app/schemas/audit.py
backend/app/schemas/assignment.py
backend/app/schemas/session.py
backend/pyproject.toml
pyproject.toml
Makefile
.env.example
```

Do **not** paste `.env` values if they contain real secrets.

---

# 21. Recommended Alternative Workflow

A convenient alternative is to keep a project handoff file in the repo:

```text
docs/_notes/CHECKPOINT.md
```

At the end of each work session, update it with:

```text
- last completed step
- current git commit hash
- current blockers
- next step
- any decisions made
```

This makes future chat handoffs much easier.

Suggested commit for adding this checkpoint to the repo:

```bash
git add docs/_notes/CHECKPOINT.md
git commit -m "docs: add project implementation checkpoint"
```

However, if this checkpoint contains temporary process details, keep it outside repo or in `_notes` rather than top-level docs.

---

# 22. Current Most Likely Next Step

Most likely next step depends on whether DB-2.10 was completed.

## If DB-2.10 not completed

Continue with:

```text
DB-2.10 — create ConsentRepository
```

## If DB-2.10 completed and committed

Continue with:

```text
DB-2.11 — create AuditRepository
```

The assistant should ask for repo state before deciding.
