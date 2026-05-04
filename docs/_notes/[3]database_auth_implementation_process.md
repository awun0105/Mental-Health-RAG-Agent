**Project:** Mental Health Sovereign Agentic AI Platform
**Giai đoạn:** Milestone 2 — Data & Auth Foundation
**Mục đích tài liệu:** Ghi lại toàn bộ quá trình implement phần database/auth foundation đã làm trong project, theo dạng process document để sau này đọc lại có thể hiểu rõ:

- đã làm những bước nào;
- vì sao làm theo thứ tự đó;
- mỗi file được tạo ra để làm gì;
- các lớp architecture liên kết với nhau như thế nào;
- flow hoạt động thực tế khi register/login/consent/assignment;
- các lỗi đã gặp khi tích hợp Supabase thật và cách xử lý;
- các decision quan trọng đã chốt trong quá trình implement.

---

# PHẦN 1: BỐI CẢNH VÀ MỤC TIÊU CỦA GIAI ĐOẠN DATABASE IMPLEMENTATION

## 1.1 Milestone này đang giải quyết vấn đề gì?

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

Milestone 2 là phần dựng “xương sống identity + database + authorization” cho toàn bộ platform.

1.2 Tại sao chưa làm LangGraph/RAG ở giai đoạn này?
LangGraph agent và RAG cần dựa trên các dữ liệu sau:

user là ai;

user thuộc role nào;

patient đã consent chưa;

doctor có được assign cho patient đó không;

message/session lưu ở đâu;

clinical profile sẽ gắn với patient/session nào;

audit log ghi event như thế nào.

Nếu chưa có database/auth foundation, agent dù chạy được cũng sẽ không có ranh giới an toàn về privacy, role và audit.

Vì vậy thứ tự đúng là:

Milestone 1: Project foundation
Milestone 2: Data/Auth foundation
Milestone 3+: Chat/session/agent/RAG
1.3 Nguyên tắc thiết kế áp dụng trong milestone này
Các nguyên tắc xuyên suốt:

Backend-enforced authorization

frontend không được tự quyết định quyền;

FastAPI backend phải kiểm tra JWT, role và assignment.

Doctor assignment enforcement

doctor chỉ được xem patient được assign;

logic này nằm ở backend service, không nằm ở Streamlit.

Consent-first

user phải accept policy version hiện tại;

consent được lưu lại bằng database record.

Audit-ready

các action nhạy cảm phải có audit log;

audit log là application audit, không thay thế bởi Langfuse.

Strict typing

code phải pass mypy strict;

không dùng Any nếu có thể tránh;

raw Supabase rows được type bằng JSON aliases.

Repository-Service-API layering

API route không query Supabase trực tiếp;

repository chỉ làm data access;

service chứa business rules;

dependency layer wire các object lại với nhau.

PHẦN 2: KIẾN TRÚC TỔNG THỂ SAU KHI IMPLEMENT MILESTONE 2
2.1 Layer architecture
Sau khi implement, backend có kiến trúc theo lớp:

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
Supabase/PostgreSQL
Ví dụ flow register:

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
Ví dụ flow consent:

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
Ví dụ flow doctor assignment:

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
2.2 Các folder liên quan trong milestone này
backend/app/core/
Chứa cấu hình và logic nền tảng:

config.py

constants.py

exceptions.py

security.py

backend/app/db/
Chứa kết nối database và repository layer:

supabase_client.py

repositories/base.py

repositories/user_repo.py

repositories/consent_repo.py

repositories/audit_repo.py

repositories/assignment_repo.py

backend/app/schemas/
Chứa Pydantic request/response contracts:

user.py

consent.py

audit.py

assignment.py

session.py

backend/app/services/
Chứa business logic:

auth_service.py

audit_service.py

consent_service.py

assignment_service.py

backend/app/api/
Chứa FastAPI routes và dependency injection:

dependencies.py

auth.py

consent.py

admin.py

health.py

docs/
Chứa tài liệu database:

DATABASE_MODEL.md

schema.sql

PHẦN 3: DATABASE MODELING VÀ SCHEMA IMPLEMENTATION
3.1 Mục tiêu của database model
Application DB dùng Supabase/PostgreSQL để lưu dữ liệu nghiệp vụ chính:

users
doctor_assignments
consent_records
chat_sessions
chat_messages
clinical_profiles
stress_risk_scores
audit_logs
Trong milestone này, không phải bảng nào cũng đã có repository/API ngay. Một số bảng được model sẵn để chuẩn bị cho milestone sau.

Ví dụ:

chat_sessions

chat_messages

clinical_profiles

stress_risk_scores

đã nằm trong schema vì thuộc data model tổng thể, nhưng chưa implement repository/service trong Milestone 2 vì chat/clinical workflow thuộc milestone sau.

3.2 Vì sao cần users riêng thay vì chỉ dùng Supabase Auth?
Supabase có auth.users, nhưng project cần application-level user vì cần lưu:

role: patient / doctor / admin;

provider: local / google;

active status;

doctor-patient assignment;

consent record;

audit log reference;

app JWT subject.

Do đó, bảng public.users là source chính cho application authorization.

Cột quan trọng:

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
Ý nghĩa:

id: application user id, dùng trong app JWT;

auth_user_id: mapping Supabase Auth user nếu dùng OAuth;

password_hash: chỉ có local user;

role: quyết định quyền trong backend;

auth_provider: local/google;

is_active: soft deactivate.

3.3 Vì sao dùng auth_user_id nullable?
Cột này được thêm để chuẩn bị cho Google OAuth/Supabase Auth mapping.

Local email/password user có thể chưa có Supabase Auth user, nên nullable.

Google OAuth user về sau có thể map:

users.auth_user_id = auth.users.id
Index khuyến nghị:

CREATE UNIQUE INDEX IF NOT EXISTS unique_users_auth_user_id
ON users(auth_user_id)
WHERE auth_user_id IS NOT NULL;
3.4 Vì sao dùng JSONB cho một số field?
Các field AI/clinical còn thay đổi nhiều:

clinical symptoms;

risk markers;

evidence snippets;

risk score evidence;

audit metadata;

session metadata.

Do đó, dùng JSONB cho MVP giúp iterate nhanh.

Nhưng không dùng JSONB cho các quan hệ chính như user, role, assignment, session ID. Các field đó vẫn là cột rõ ràng để enforce FK, index và access rule.

Nguyên tắc:

Structured authorization data → normal columns
Flexible AI/metadata data     → JSONB
3.5 File docs/schema.sql
Vai trò:

là SQL reference schema cho application DB;

dùng để apply vào Supabase project;

chứa extensions, table definitions, constraints, indexes;

sau smoke test đã bổ sung grant privileges cho service_role.

Các extension cần có:

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;
Ý nghĩa:

pgcrypto: dùng gen_random_uuid();

citext: email case-insensitive.

Sau khi tích hợp Supabase thật, phát hiện backend dùng secret/service role key nhưng chưa có quyền trên table custom. Vì vậy thêm grant:

GRANT USAGE ON SCHEMA public TO service_role;

GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA public
TO service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLES TO service_role;
Ý nghĩa:

cho backend service role query các bảng application;

tránh lỗi permission denied for table users;

đảm bảo bảng tạo mới sau này cũng có quyền cho service role.

PHẦN 4: CORE CONFIG, CONSTANTS, EXCEPTIONS, SECURITY
4.1 backend/app/core/config.py
Mục đích
File này quản lý toàn bộ environment settings của backend.

Các nhóm config:

App metadata
External services
Supabase
JWT
Google OAuth
Backend/frontend URLs
Consent policy version
Vì sao cần file này?
Nếu code đọc env trực tiếp ở nhiều nơi, project sẽ khó maintain.

Vì vậy ta gom toàn bộ vào:

settings = Settings()
Các service/repository khác chỉ import settings.

Vấn đề runtime đã gặp
Ban đầu BaseSettings đọc:

.env
theo current working directory. Nhưng make dev-be chạy:

cd backend && uv run uvicorn app.main:app --reload
nên backend tìm .env trong backend/.env, không phải root .env.

Điều này gây lỗi:

Supabase URL and KEY must be set in environment variables
Quyết định fix
Sửa config.py để đọc root .env cố định bằng Path.

Architecture decision:

1 source of truth = root .env
Không copy .env vào backend/ vì sẽ tạo duplicate config.

Flow sử dụng
config.py
    ↓
supabase_client.py reads settings.supabase_url/settings.supabase_key
    ↓
auth_service.py reads JWT settings
    ↓
consent_service.py reads current policy version
4.2 backend/app/core/constants.py
Mục đích
Định nghĩa enum vocabulary dùng toàn hệ thống.

Các nhóm enum:

AuthProvider
UserRole
SessionStatus
MessageRole
SafetySeverity
RiskSeverity
AuditAction
Vì sao cần file này?
Không để code rải rác string như:

"patient"
"doctor"
"user_login"
"consent_accepted"
Nếu viết string tay nhiều nơi sẽ dễ typo.

Dùng enum giúp:

code rõ hơn;

mypy hỗ trợ tốt hơn;

schema/API nhất quán;

database value thống nhất.

File nào sử dụng?
schemas/user.py dùng UserRole, AuthProvider;

auth_service.py dùng AuthProvider, UserRole;

audit_repo.py dùng AuditAction;

audit_service.py dùng AuditAction;

consent_service.py dùng AuditAction.CONSENT_ACCEPTED;

assignment_service.py dùng UserRole, AuditAction.

4.3 backend/app/core/exceptions.py
Mục đích
Tạo exception hierarchy chung cho application.

Các exception chính:

AppException
NotFoundError
AlreadyExistsError
UnauthorizedError
ForbiddenError
InvalidCredentialsError
ConsentRequiredError
DatabaseError
Vì sao cần file này?
Service layer không nên throw trực tiếp HTTPException, vì service layer không nên biết quá nhiều về HTTP.

Thay vào đó:

Service raises AppException subclass
FastAPI exception handler converts to JSON response
Ví dụ:

InvalidCredentialsError → 401
ForbiddenError          → 403
AlreadyExistsError      → 409
DatabaseError           → 500
Lỗi đã gặp
Khi wire vào main.py, mypy báo:

Argument 2 to add_exception_handler has incompatible type
Nguyên nhân:

app_exception_handler(request: Request, exc: AppException)
trong khi FastAPI/Starlette muốn handler nhận:

exc: Exception
Cách fix
Đổi handler signature:

exc: Exception
và bên trong check:

if isinstance(exc, AppException)
Kết quả:

type-check pass;

vẫn giữ JSON response format cho custom exceptions.

4.4 backend/app/core/security.py
Mục đích
Xử lý JWT decoding và role-based access helper.

Nội dung chính:

CurrentUserClaims
decode_access_token
require_roles
require_admin
require_doctor
require_patient
Vì sao cần file này?
AuthService tạo token, nhưng API cần decode token.

Tách security.py giúp:

không trộn token decode vào route;

role check dùng thống nhất;

dependency layer có thể gọi lại;

tests sau này dễ hơn.

Flow hoạt động
Request with Authorization: Bearer <JWT>
    ↓
api/dependencies.py get_current_user()
    ↓
security.decode_access_token()
    ↓
CurrentUserClaims(user_id, email, role)
    ↓
route/service dùng current_user
Token chứa gì?
JWT payload:

sub   = user id
email = email
role  = patient/doctor/admin
exp   = expiration timestamp
Trong config hiện tại token sống 60 phút:

JWT_EXPIRATION_MINUTES=60
PHẦN 5: SUPABASE CLIENT VÀ REPOSITORY LAYER
5.1 backend/app/db/supabase_client.py
Mục đích
Tạo Supabase client dùng chung cho backend.

Vì sao cần file này?
Không muốn mỗi repository tự gọi:

create_client(...)
Vì như vậy:

config bị lặp;

khó test;

khó đổi Supabase client;

dễ tạo nhiều client không cần thiết.

Cách hoạt động
get_supabase_client()
    ↓
SupabaseClientManager.get_client()
    ↓
nếu chưa có client:
    đọc settings.supabase_url/settings.supabase_key
    create_client()
    cache lại
    return client
Lỗi đã gặp liên quan env
Khi settings chưa đọc được .env, file này raise:

ValueError: Supabase URL and KEY must be set in environment variables
Sau khi fix config.py, Supabase client hoạt động đúng.

5.2 backend/app/db/repositories/base.py
Mục đích
Tạo BaseRepository dùng chung cho các bảng Supabase.

Cung cấp CRUD chung:

get_by_id
create
update
delete
_first_row
_to_model
Vì sao cần BaseRepository?
Các repository đều có pattern giống nhau:

select by id
insert row
update row
delete row
convert row → Pydantic model
catch DB error
Nếu viết lặp ở từng repo, code dài và dễ lệch style.

Vấn đề typing đã gặp
Supabase Python SDK có typing không dễ khớp với:

dict[str, object]
Khi dùng mypy strict, .insert() / .update() có thể báo lỗi.

Cách fix
Tạo JSON type aliases:

JSONValue
JSONRow
Ý nghĩa:

JSONValue = str | int | float | bool | None | list[JSONValue] | dict[str, JSONValue]
JSONRow   = dict[str, JSONValue]
Lợi ích:

tránh dùng Any;

thể hiện đúng dữ liệu Supabase trả về;

giúp repository strict typing ổn định.

5.3 backend/app/db/repositories/user_repo.py
Mục đích
Repository cho bảng users.

Method quan trọng:

get_by_email
email_exists
get_by_auth_user_id
get_by_provider_identity
list_by_role
deactivate
Vì sao get_by_email trả raw row?
Login cần đọc:

password_hash
Nhưng UserResponse không được expose password_hash.

Vì vậy:

get_by_email() trả JSONRow | None;

AuthService.login() đọc password_hash từ raw row;

response ra client vẫn dùng UserResponse.

Flow sử dụng
Register:

AuthService.register()
    ↓
UserRepository.email_exists()
    ↓
UserRepository.create()
Login:

AuthService.login()
    ↓
UserRepository.get_by_email()
    ↓
verify password hash
Admin/assignment:

AssignmentService.create_assignment()
    ↓
UserRepository.get_by_id(doctor_id)
UserRepository.get_by_id(patient_id)
5.4 backend/app/db/repositories/consent_repo.py
Mục đích
Repository cho bảng consent_records.

Method quan trọng:

get_latest_by_user
has_accepted_version
list_by_user
Vì sao cần riêng repository này?
Consent logic có query đặc thù:

lấy consent mới nhất;

kiểm tra user đã accept policy version hiện tại chưa;

list lịch sử consent.

Không nên để các query này nằm trong service hoặc route.

Flow sử dụng
ConsentService.get_status()
    ↓
ConsentRepository.has_accepted_version()
ConsentRepository.get_latest_by_user()
5.5 backend/app/db/repositories/audit_repo.py
Mục đích
Repository cho bảng audit_logs.

Method quan trọng:

list_by_user
list_by_action
list_by_resource
Vì sao cần audit repository?
Audit log là dữ liệu nhạy cảm và cần query theo nhiều góc:

user nào thực hiện action;

action loại gì;

resource nào bị tác động.

Repository giúp các query này tập trung một nơi.

Flow sử dụng
AuditService.log_event()
    ↓
AuditRepository.create()
Query review sau này:

AuditRepository.list_by_user()
AuditRepository.list_by_action()
AuditRepository.list_by_resource()
5.6 backend/app/db/repositories/assignment_repo.py
Mục đích
Repository cho bảng doctor_assignments.

Method quan trọng:

get_active_assignment
is_assigned
list_patients_for_doctor
list_doctors_for_patient
deactivate
Vì sao file này rất quan trọng?
Doctor assignment là security boundary chính của doctor-facing workflow.

Doctor không được xem patient chỉ vì có role doctor. Doctor phải có active assignment.

Flow sử dụng
AssignmentService.ensure_doctor_can_access_patient()
    ↓
AssignmentRepository.is_assigned()
Doctor dashboard:

GET /doctor/my-patients
    ↓
AssignmentService.list_patients_for_doctor()
    ↓
AssignmentRepository.list_patients_for_doctor()
Note về field thời gian
Schema hiện tại AssignmentResponse dùng:

created_at
Do đó các repository query order nên dùng:

created_at
Không nên dùng assigned_at nếu bảng không có field này.

PHẦN 6: PYDANTIC SCHEMAS — API CONTRACTS
6.1 Vì sao cần schemas?
Schemas là ranh giới giữa:

external API request/response
và
internal database/service logic
Lợi ích:

validate input;

chuẩn hóa output;

không expose sensitive fields;

OpenAPI docs rõ ràng;

mypy type-check tốt hơn.

6.2 backend/app/schemas/user.py
Mục đích
Định nghĩa request/response cho user/auth.

Classes:

UserCreate
UserLogin
GoogleExchangeRequest
UserResponse
TokenResponse
Điểm quan trọng
UserResponse không có:

password_hash
Đây là intentional.

TokenResponse gồm:

access_token
token_type
user
Lỗi đã gặp:

AuthService.login() ban đầu chỉ trả token, thiếu user, dẫn tới mypy lỗi. Sau đó service được sửa để trả đủ TokenResponse.

6.3 backend/app/schemas/consent.py
Mục đích
Định nghĩa contract cho consent.

Classes:

ConsentAcceptRequest
ConsentResponse
ConsentStatusResponse
Điểm quan trọng
ConsentAcceptRequest chỉ có:

policy_version
không có accepted.

Ý nghĩa:

Client gọi /consent/accept nghĩa là accepted = true
Do đó ConsentService tự set:

accepted=True
Lỗi đã gặp:

Service ban đầu giả định payload.accepted, nhưng schema không có field này. Sau đó service được sửa để dùng payload.policy_version.

ConsentStatusResponse có:

has_valid_consent
current_policy_version
latest_accepted_policy_version
không có accepted hoặc latest_consent.

6.4 backend/app/schemas/audit.py
Mục đích
Định nghĩa audit log request/response.

Dùng cho:

AuditRepository;

AuditService;

future admin audit views.

Audit response chứa các thông tin như:

id
user_id
action
resource_type
resource_id
metadata
ip_address
created_at
Nguyên tắc metadata
Audit metadata không nên chứa raw sensitive content nếu không cần.

Ví dụ nên ghi:

policy_version
doctor_id
patient_id
method
Không nên ghi toàn bộ raw chat message vào audit metadata.

6.5 backend/app/schemas/assignment.py
Mục đích
Định nghĩa contract cho doctor-patient assignment.

Classes:

AssignmentCreateRequest
AssignmentResponse
Field chính:

doctor_id
patient_id
assigned_by
is_active
created_at
Service đã được kiểm tra khớp với schema này.

6.6 backend/app/schemas/session.py
Vì sao có schema session nhưng chưa có repository?
File này chuẩn bị cho milestone sau.

Milestone 2 chưa implement:

SessionRepository
MessageRepository
ChatService
vì chat workflow thuộc milestone tiếp theo.

Quyết định:

Schema có thể tồn tại trước để chuẩn hóa response model tương lai.
Repository chỉ tạo khi có use-case trong milestone hiện tại.
PHẦN 7: SERVICE LAYER — BUSINESS LOGIC
7.1 Vì sao cần service layer?
Repository chỉ biết đọc/ghi DB. API route chỉ nhận request/trả response.

Business rules phải nằm ở service.

Ví dụ:

email đã tồn tại chưa;

password hash/verify;

user active không;

doctor_id có thật sự là doctor không;

patient_id có thật sự là patient không;

consent policy hiện tại là gì;

ghi audit log sau action.

Nếu không có service layer, logic sẽ rải rác trong route, khó test và dễ leak authorization.

7.2 backend/app/services/auth_service.py
Mục đích
Xử lý local authentication:

register
login
hash password
verify password
create JWT
convert raw user row → UserResponse
Register flow
UserCreate payload
    ↓
email_exists(payload.email)
    ↓
hash_password(payload.password)
    ↓
create users row
    ↓
return UserResponse
Login flow
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
JWT flow
Token payload chứa:

sub   = user.id
email = user.email
role  = user.role
exp   = expiration timestamp
Lỗi đã gặp
Lỗi 1: Exception constructor mismatch
AlreadyExistsError cần:

resource
identifier
InvalidCredentialsError không nhận message.

Service được sửa để dùng đúng constructor.

Lỗi 2: TokenResponse thiếu user
Schema yêu cầu:

user: UserResponse
Service được sửa để convert raw row sang UserResponse.

Lỗi 3: bcrypt/passlib runtime
Khi register, passlib báo lỗi liên quan bcrypt version:

module 'bcrypt' has no attribute '__about__'
ValueError: password cannot be longer than 72 bytes
Dù password không dài, lỗi đến từ incompatibility giữa passlib và bcrypt version mới.

Fix:

uv add --package backend "bcrypt==4.3.0"
hoặc pin <5.

Mục tiêu:

stable password hashing
7.3 backend/app/services/audit_service.py
Mục đích
Tạo một nơi duy nhất để ghi audit log.

Method chính:

log_event()
Vì sao không ghi audit trực tiếp từ từng service?
Nếu từng service tự gọi repository với payload riêng:

format audit dễ lệch;

metadata không được sanitize;

khó thêm policy sau này;

khó test.

Do đó mọi sensitive action nên gọi:

AuditService.log_event()
Metadata sanitization
Service sanitize metadata để đảm bảo JSON-safe.

Nguyên tắc:

scalar values giữ nguyên;

object phức tạp convert string;

không nên đưa raw sensitive text nếu không cần.

Flow sử dụng
Consent:

ConsentService.accept_consent()
    ↓
AuditService.log_event(action=CONSENT_ACCEPTED)
Assignment:

AssignmentService.create_assignment()
    ↓
AuditService.log_event(action=DOCTOR_ASSIGNMENT_CREATED)
7.4 backend/app/services/consent_service.py
Mục đích
Xử lý consent business logic.

Method:

accept_consent
get_status
Accept flow
current user id
ConsentAcceptRequest(policy_version)
    ↓
create consent_records row with accepted=True
    ↓
log audit event consent_accepted
    ↓
return ConsentResponse
Status flow
current policy version from settings
    ↓
ConsentRepository.has_accepted_version(user_id, version)
    ↓
ConsentRepository.get_latest_by_user(user_id)
    ↓
ConsentStatusResponse
Lỗi đã gặp
Schema thật không có accepted trong request.

Fix:

Client gửi policy_version
Service tự set accepted=True
Schema thật trả:

has_valid_consent
current_policy_version
latest_accepted_policy_version
Service được sửa theo đúng schema.

7.5 backend/app/services/assignment_service.py
Mục đích
Xử lý doctor-patient assignment business logic.

Method:

create_assignment
deactivate_assignment
ensure_doctor_can_access_patient
list_patients_for_doctor
list_doctors_for_patient
Create assignment flow
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
Vì sao check role ở service?
Database FK chỉ biết user tồn tại, không biết user đó có role doctor/patient đúng với business rule không.

Service phải enforce:

doctor_id must belong to doctor
patient_id must belong to patient
Deactivate flow
Không hard delete assignment.

deactivate assignment
    ↓
set is_active=false
    ↓
audit log assignment_deactivated
Lý do:

giữ history;

audit được;

không phá trace.

Authorization method
ensure_doctor_can_access_patient()
Đây là method cực quan trọng cho milestone sau:

doctor dashboard
clinical profile access
doctor copilot
PHẦN 8: API DEPENDENCY INJECTION VÀ ROUTERS
8.1 backend/app/api/dependencies.py
Mục đích
Wire toàn bộ dependencies cho FastAPI.

Bao gồm:

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
require_current_admin
require_current_doctor
require_current_patient
require_current_doctor_or_admin
Vì sao cần file này?
Không muốn routes tự tạo repository/service.

Ví dụ không nên viết trong route:

db = get_supabase_client()
repo = UserRepository(db)
service = AuthService(repo)
Thay vào đó dùng:

Depends(get_auth_service)
Lợi ích:

route sạch;

dependency graph rõ;

dễ mock trong tests;

tránh duplicate construction logic;

không có circular import.

Flow protected route
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
8.2 backend/app/api/auth.py
Mục đích
Expose auth endpoints.

Routes:

POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
Flow register
HTTP request
    ↓
UserCreate validation
    ↓
AuthService.register()
    ↓
UserResponse
Flow login
HTTP request
    ↓
UserLogin validation
    ↓
AuthService.login()
    ↓
TokenResponse
Flow me
Bearer token
    ↓
get_current_user()
    ↓
CurrentUserClaims
8.3 backend/app/api/consent.py
Mục đích
Expose consent endpoints.

Routes:

POST /api/v1/consent/accept
GET  /api/v1/consent/status
Flow accept
Bearer token
    ↓
current_user
    ↓
ConsentAcceptRequest(policy_version)
    ↓
ConsentService.accept_consent(user_id, payload, ip_address)
    ↓
ConsentResponse
Flow status
Bearer token
    ↓
current_user
    ↓
ConsentService.get_status(user_id)
    ↓
ConsentStatusResponse
8.4 backend/app/api/admin.py
Mục đích
Expose admin/doctor assignment endpoints.

Routes implemented:

POST  /api/v1/admin/assignments
PATCH /api/v1/admin/assignments/{assignment_id}/deactivate
GET   /api/v1/doctor/my-patients
Create assignment route
Requires:

admin role
Flow:

Bearer token
    ↓
require_current_admin
    ↓
AssignmentService.create_assignment()
Doctor my patients route
Requires:

doctor role
Flow:

Bearer token
    ↓
require_current_doctor
    ↓
AssignmentService.list_patients_for_doctor()
Vì sao /doctor/my-patients không nằm dưới /admin?
Domain rõ hơn:

admin routes = quản trị
doctor routes = doctor tự xem dữ liệu của mình
8.5 backend/app/main.py
Mục đích
FastAPI application entrypoint.

Nội dung đã wire:

CORS middleware
AppException handler
health router
auth router
consent router
admin router
Lỗi đã xử lý
Ban đầu có import duplicate:

from app.api.health import router as health_router
from app.api import admin, auth, consent, health
Đã sửa về style thống nhất:

from app.api import admin, auth, consent, health
và include:

health.router
auth.router
consent.router
admin.router
Verify
Mở:

http://localhost:8000/docs
Kết quả cần thấy route groups:

health
auth
consent
admin
PHẦN 9: SUPABASE SETUP VÀ RUNTIME INTEGRATION
9.1 Tạo Supabase project
Đã tạo Supabase Cloud dev project.

Lưu ý:

Chỉ dùng fake/dev data
Không dùng real patient data
9.2 SUPABASE_URL đúng là gì?
Đã xác định:

SUPABASE_URL=https://<project-ref>.supabase.co
Không dùng:

/rest/v1
/dashboard
project URL trong dashboard UI
Vì supabase-py tự thêm path REST API khi cần.

Sai nếu dùng:

https://<project-ref>.supabase.co/rest/v1/
9.3 SUPABASE_KEY dùng key nào?
Backend dùng secret/service role key:

sb_secret_...
Không dùng publishable key cho backend.

Lý do:

backend cần full quyền CRUD cho application tables;

publishable/anon key phù hợp frontend khi có RLS;

service role key chỉ dùng server-side.

Không bao giờ:

paste key vào chat
commit .env
expose service role key ra frontend
9.4 Apply schema
Dùng Supabase Dashboard:

SQL Editor
→ paste docs/schema.sql
→ Run
Sau đó verify tables:

users
doctor_assignments
consent_records
chat_sessions
chat_messages
clinical_profiles
stress_risk_scores
audit_logs
9.5 Permission issue đã gặp
Khi chạy query Supabase trực tiếp:

permission denied for table users
Supabase gợi ý:

GRANT SELECT ON public.users TO service_role
Nguyên nhân:

bảng custom được tạo trong public schema;

service_role chưa có explicit table privileges;

backend dùng secret key nhưng PostgREST role vẫn cần quyền table.

Fix bằng SQL grant ở Supabase SQL Editor và thêm vào docs/schema.sql.

Sau khi fix, Python direct query pass:

data=[] count=None
Điều này chứng minh:

Supabase URL đúng
Supabase key đúng
table tồn tại
permission đã ổn
PHẦN 10: SMOKE TEST END-TO-END
10.1 Mục tiêu smoke test
Kiểm tra runtime thật:

FastAPI
→ service layer
→ repository layer
→ Supabase
→ response
Không chỉ kiểm tra type/lint.

10.2 Test register
Request:

POST /api/v1/auth/register
Payload:

email
password
full_name
role
Kết quả pass:

200 OK
UserResponse returned
password_hash not exposed
Record được tạo trong users.

10.3 Test login
Request:

POST /api/v1/auth/login
Kết quả pass:

access_token
token_type=bearer
user
10.4 Token handling lesson
Khi lấy token trong terminal, không nên copy thủ công từ JSON dài vì terminal có thể wrap line.

Cách tốt:

TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"patient.dev@example.com","password":"Password123!"}' \
  | jq -r .access_token)
Sau đó:

echo $TOKEN
Dùng token:

curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
Ghi chú
Người dùng ban đầu dùng ACCESS_TOKEN, sau đó lấy TOKEN. Cả hai đều là biến shell tạm, miễn là header dùng đúng biến có token.

10.5 Test /auth/me
Kết quả pass:

{
  "user_id": "...",
  "email": "patient.dev@example.com",
  "role": "patient"
}
Điều này xác nhận:

JWT creation OK
JWT decoding OK
Authorization header OK
CurrentUserClaims OK
10.6 Test consent accept
Request:

POST /api/v1/consent/accept
Payload:

{"policy_version":"v1"}
Kết quả pass:

ConsentResponse returned
accepted=true
Điều này xác nhận:

ConsentService
ConsentRepository
AuditService
AuditRepository
Supabase insert
đều chạy được.

10.7 Test consent status
Request:

GET /api/v1/consent/status
Kết quả pass:

{
  "has_valid_consent": true,
  "current_policy_version": "v1",
  "latest_accepted_policy_version": "v1"
}
Điều này xác nhận:

ConsentRepository.has_accepted_version()
ConsentRepository.get_latest_by_user()
settings.current_consent_policy_version
đều khớp.

PHẦN 11: CÁC LỖI ĐÃ GẶP VÀ BÀI HỌC
11.1 git add . lỡ stage quá nhiều
Nguy cơ:

.env
backend/.env
__pycache__
*.pyc
Cách xử lý nếu chưa commit:

git reset
Sau đó add đúng file cần commit.

Cần đảm bảo .gitignore có:

.env
backend/.env
__pycache__/
*.pyc
.venv/
11.2 .env không được backend đọc
Nguyên nhân:

make dev-be chạy từ backend/
BaseSettings env_file=".env" tìm backend/.env
Fix:

config.py đọc root .env bằng Path
Architecture principle:

Root .env là source of truth
Không duplicate backend/.env
11.3 Supabase permission denied
Lỗi:

permission denied for table users
Fix:

grant privileges to service_role
Bài học:

tạo bảng custom trong Supabase không đủ;

backend key/role cần table privileges;

grant phải nằm trong schema.sql để tái tạo DB không lỗi.

11.4 Supabase URL sai format
Lỗi có thể gặp:

Invalid path specified in request URL
Nguyên nhân thường là URL sai, ví dụ có /rest/v1.

Correct:

https://<project-ref>.supabase.co
11.5 passlib/bcrypt version issue
Lỗi:

(trapped) error reading bcrypt version
ValueError: password cannot be longer than 72 bytes
Nguyên nhân:

passlib incompatible với bcrypt version mới
Fix:

uv add --package backend "bcrypt==4.3.0"
Commit khuyến nghị:

fix(auth): pin bcrypt to a passlib-compatible version for stable password hashing
11.6 Token copy thủ công bị hiểu nhầm
Terminal wrap làm token nhìn như xuống dòng, nhưng token thật có thể vẫn là một dòng.

Cách tránh:

jq extract token tự động
Command:

TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"patient.dev@example.com","password":"Password123!"}' \
  | jq -r .access_token)
11.7 Curl command bị paste trùng
Lỗi:

curl -X POST http://localhostcurl -X POST ...
Kết quả:

Not authenticated
Bài học:

khi smoke test, copy command nguyên khối;

nếu lỗi auth, test /auth/me trước để xác định token có đúng không.

PHẦN 12: ARCHITECTURE FLOW THEO TỪNG WORKFLOW
12.1 Register user flow
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
Security notes:

password không bao giờ trả ra response;

password lưu DB dạng hash;

duplicate email trả AlreadyExistsError.

12.2 Login flow
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
JWT notes:

token sống 60 phút;

mỗi lần login cấp token mới;

token cũ vẫn dùng được nếu chưa expired;

logout hiện tại là frontend xóa token, chưa có server-side revocation.

12.3 Protected route flow
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
Nếu token invalid/expired:

UnauthorizedError → 401 JSON response
12.4 Consent flow
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
Status:

Client
  ↓ GET /api/v1/consent/status
ConsentService.get_status()
  ↓ has_accepted_version()
  ↓ get_latest_by_user()
ConsentStatusResponse
12.5 Assignment flow
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
Doctor:

Doctor
  ↓ GET /api/v1/doctor/my-patients
require_current_doctor()
  ↓
AssignmentService.list_patients_for_doctor()
  ↓
AssignmentRepository.list_patients_for_doctor()
Future clinical access:

Doctor requests patient clinical profile
  ↓
AssignmentService.ensure_doctor_can_access_patient()
  ↓
only then return doctor-facing data
PHẦN 13: FILES IMPLEMENTED TRONG MILESTONE 2 VÀ MỤC ĐÍCH
Core files
backend/app/core/config.py
Quản lý settings/env. Sau fix, đọc root .env.

backend/app/core/constants.py
Định nghĩa enums domain-wide.

backend/app/core/exceptions.py
Định nghĩa custom exception hierarchy và JSON exception handler.

backend/app/core/security.py
Decode JWT và role check helpers.

Database client
backend/app/db/supabase_client.py
Tạo/cached Supabase client dùng chung.

Repository files
backend/app/db/repositories/base.py
Base CRUD repository + JSON typing.

backend/app/db/repositories/user_repo.py
Data access cho users.

backend/app/db/repositories/consent_repo.py
Data access cho consent records.

backend/app/db/repositories/audit_repo.py
Data access cho audit logs.

backend/app/db/repositories/assignment_repo.py
Data access cho doctor-patient assignments.

Schema files
backend/app/schemas/user.py
Auth/user request-response models.

backend/app/schemas/consent.py
Consent accept/status models.

backend/app/schemas/audit.py
Audit log models.

backend/app/schemas/assignment.py
Assignment models.

backend/app/schemas/session.py
Future session/message response models.

Service files
backend/app/services/auth_service.py
Register/login/password/JWT logic.

backend/app/services/audit_service.py
Centralized audit logging.

backend/app/services/consent_service.py
Consent accept/status business logic.

backend/app/services/assignment_service.py
Doctor-patient assignment validation, access check, audit logging.

API files
backend/app/api/dependencies.py
FastAPI DI for repos/services/current user/role guards.

backend/app/api/auth.py
Auth endpoints.

backend/app/api/consent.py
Consent endpoints.

backend/app/api/admin.py
Admin assignment and doctor my-patients endpoints.

backend/app/main.py
FastAPI app wiring: routers, CORS, exception handler.

Docs/config files
docs/schema.sql
Reference SQL schema + grants.

docs/DATABASE_MODEL.md
Data modeling reference.

.env.example
Environment variable template.

backend/pyproject.toml
uv.lock
Backend dependencies and locked versions, including Supabase/JWT/password hashing/bcrypt pin.

PHẦN 14: CURRENT STATUS SAU DB-2.24
Completed
DB-2.1 schema.sql
DB-2.2 backend dependencies
DB-2.3 config
DB-2.4 Supabase client
DB-2.5 constants
DB-2.6 exceptions
DB-2.7 Pydantic schemas
DB-2.8 BaseRepository
DB-2.9 UserRepository
DB-2.10 ConsentRepository
DB-2.11 AuditRepository
DB-2.12 AssignmentRepository
DB-2.13 AuthService
DB-2.14 AuditService
DB-2.15 ConsentService
DB-2.16 AssignmentService
DB-2.17 security.py
DB-2.18 dependencies.py
DB-2.19 auth routes
DB-2.20 consent routes
DB-2.21 admin/doctor assignment routes
DB-2.22 main.py router + exception wiring
DB-2.23 Supabase setup + schema apply
DB-2.24 smoke test register/login/me/consent
Verified runtime flows
Supabase direct query: pass
Register: pass
Login: pass
/auth/me: pass
Consent accept: pass
Consent status: pass
Backend docs visible: pass
Important unresolved / future tasks
DB-2.25 automated tests
DB-2.26 frontend auth UI
DB-2.27 Google OAuth setup
Nếu project muốn giữ Milestone 2 strict theo original plan, nên làm tiếp:

automated tests
frontend auth UI
Google OAuth
Nếu muốn chuyển sớm sang chat/session foundation, có thể bắt đầu Phase 3 nhưng nên ghi rõ test/frontend/OAuth còn pending.

PHẦN 15: COMMIT STRATEGY VÀ SAFETY RULES
15.1 Không dùng git add . bừa bãi
Trước commit nên chạy:

git status
Nếu lỡ:

git add .
mà chưa commit:

git reset
Sau đó add đúng file.

15.2 Không commit secrets
Không commit:

.env
backend/.env
Supabase service role key
JWT secret
Google OAuth secret
access token
15.3 Commit messages nên rõ ràng
Ví dụ tốt:

fix(config,database,auth): stabilize Supabase environment loading, backend table privileges, and bcrypt password hashing
Không nên:

fix stuff
update
add files
PHẦN 16: BÀI HỌC KIẾN TRÚC SAU GIAI ĐOẠN NÀY
16.1 Database không chỉ là schema
Trong project này, database foundation gồm:

schema
permissions
repository layer
service layer
API layer
security checks
runtime smoke tests
Chỉ tạo bảng chưa đủ.

16.2 Service role key không phải là magic key
Dù dùng sb_secret_..., table privileges vẫn cần được grant đúng cho PostgREST role.

16.3 Type strict giúp phát hiện mismatch sớm
Các lỗi như:

TokenResponse missing user
ConsentAcceptRequest has no accepted
ConsentStatusResponse unexpected fields
được mypy bắt trước khi runtime.

Điều này chứng minh strict typing có giá trị thật.

16.4 Architecture layering giúp debug nhanh
Khi lỗi xảy ra, ta tách được:

env config issue
Supabase permission issue
schema mismatch
dependency issue
JWT copy issue
curl command issue
Vì mỗi layer có trách nhiệm rõ.

16.5 Manual smoke test vẫn cần thiết
make check pass không đảm bảo app chạy thật.

Smoke test đã phát hiện:

env path issue;

Supabase grant issue;

bcrypt runtime issue;

token handling issue.

PHẦN 17: CHECKLIST ĐỌC LẠI TRƯỚC KHI TIẾP TỤC
Trước khi sang phase tiếp theo, kiểm tra:

git status
make check
Kiểm tra .gitignore có:

.env
.env.*
!.env.example
backend/.env
__pycache__/
*.pyc
.venv/
Kiểm tra Supabase:

users row created
consent_records row created
audit_logs row created
Kiểm tra docs:

docs/schema.sql có grant service_role
docs/DATABASE_MODEL.md khớp schema
PHẦN 18: NEXT IMPLEMENTATION DIRECTION
Có hai hướng tiếp theo.

Hướng A — Hoàn thiện phần còn lại của Milestone 2
DB-2.25 automated tests
DB-2.26 frontend auth UI
DB-2.27 Google OAuth
Phù hợp nếu muốn Milestone 2 thật đầy đủ trước khi chuyển phase.

Hướng B — Sang Phase 3: Session & Chat Foundation
SessionRepository
MessageRepository
SessionService
ChatService
Chat API routes
patient chat flow
Phù hợp nếu muốn bắt đầu core AI interaction layer.

Khuyến nghị kỹ thuật:

Nếu mục tiêu là foundation chắc, làm DB-2.25 tests trước. Nếu mục tiêu là prototype nhanh, sang Phase 3 nhưng vẫn ghi test debt lại.

PHẦN 19: TÓM TẮT MỘT CÂU
Milestone 2 đã biến project từ một skeleton FastAPI/Streamlit thành một backend có database thật, identity thật, JWT auth thật, consent tracking thật, doctor-patient assignment foundation và audit logging foundation, với Supabase/PostgreSQL làm Application DB và FastAPI backend làm lớp enforce authorization chính.
