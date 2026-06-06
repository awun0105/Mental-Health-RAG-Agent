# Database Model — Milestone 2

**Project:** Mental Health Sovereign Agentic AI Platform
**Scope:** Application Database bằng Supabase/PostgreSQL
**Milestone:** Milestone 2 — Data & Auth Foundation
**Status:** Modeling document, dùng làm reference trước khi tạo `docs/schema.sql`

---

## 1. Trạng thái

- Milestone 1: hoàn thành.
- Milestone 2: chuẩn bị triển khai.
- Database scope hiện tại: Application DB bằng Supabase/PostgreSQL.
- Chưa triển khai Vector DB/Qdrant trong tài liệu này.
- Chưa triển khai Langfuse trace store trong tài liệu này.
- Chưa triển khai production-grade RLS trong tài liệu này.

Tài liệu này dùng để chốt mô hình dữ liệu trước khi viết SQL schema, repositories, services, auth APIs và tests cho Milestone 2.

---

## 2. Core Tables

Milestone 2 sẽ thiết kế các bảng chính sau:

| # | Table | Purpose |
|---|---|---|
| 1 | `users` | Lưu application users, role, auth provider, trạng thái active |
| 2 | `doctor_assignments` | Lưu quan hệ doctor-patient do admin tạo |
| 3 | `consent_records` | Lưu consent policy version mà user đã chấp nhận |
| 4 | `chat_sessions` | Lưu một phiên chat patient-facing |
| 5 | `chat_messages` | Lưu message trong từng chat session |
| 6 | `clinical_profiles` | Lưu doctor-facing clinical profile do AI tạo sau session |
| 7 | `stress_risk_scores` | Lưu score/risk severity theo patient/session |
| 8 | `audit_logs` | Lưu sensitive actions và system events |

---

## 3. Out of Scope for Milestone 2

Các phần sau chưa triển khai trong Milestone 2:

- Qdrant vector collections.
- DSM-5/treatment document chunks.
- Knowledge ingestion pipeline.
- Langfuse traces.
- Clinical agent workflow.
- Doctor copilot API.
- Production-grade RLS policies.
- Data retention automation.
- Backup/PITR automation.
- Multi-tenant organization model.
- Full HIPAA/GDPR/PDPA compliance certification.

---

## 4. Access Principles

Các nguyên tắc truy cập dữ liệu cốt lõi:

- Patient chỉ được truy cập dữ liệu của chính mình.
- Patient không được truy cập `clinical_profiles`.
- Patient không được xem differential diagnosis hoặc doctor-facing clinical reasoning.
- Doctor chỉ được truy cập patient đã được assign.
- Admin quản lý users và assignments.
- Admin không mặc định được xem raw chat nếu policy chưa cho phép.
- Sensitive actions phải ghi `audit_logs`.
- Backend FastAPI là nơi enforce authorization chính trong MVP.
- Frontend chỉ render dữ liệu mà backend đã trả về, không tự quyết định quyền truy cập.
- Không bao giờ expose `password_hash` qua API response.
- Không lưu secrets trong database hoặc source code.

---

## 5. Global Design Decisions

### 5.1 Application `users` table là source chính cho role và app JWT

Supabase có thể xử lý OAuth flow, nhưng application vẫn cần bảng `users` riêng để lưu:

- role: `patient`, `doctor`, `admin`;
- active/deactivated status;
- mapping Google OAuth identity;
- doctor-patient assignment relationship;
- consent tracking;
- audit actor identity;
- app-issued JWT claims.

Backend sẽ phát hành app JWT riêng. JWT nên chứa tối thiểu:

```text
sub  = application user id
role = application role
exp  = expiration time
```

### 5.2 Backend RBAC trước, RLS hardening sau

Trong Milestone 2, authorization được enforce chủ yếu ở FastAPI backend bằng:

- `get_current_user`;
- `require_role`;
- assignment check;
- consent check;
- audit logging;
- tests cho 401/403.

RLS nên được thêm sau như hardening layer, đặc biệt trước production hoặc nếu frontend truy cập Supabase trực tiếp bằng anon key.

### 5.3 JSONB dùng cho data còn linh hoạt

Các field AI-generated hoặc metadata chưa ổn định được lưu bằng JSONB:

- `chat_sessions.metadata`;
- `clinical_profiles.symptoms`;
- `clinical_profiles.risk_markers`;
- `clinical_profiles.evidence_snippets`;
- `stress_risk_scores.evidence`;
- `audit_logs.metadata`.

Không dùng JSONB để thay thế các quan hệ chính như user, session, assignment hoặc role.

### 5.4 Có lưu raw chat nhưng hạn chế expose

MVP cần lưu `chat_messages` để phục vụ:

- patient session history;
- safety workflow;
- silent clinical analyzer;
- clinical profile generation;
- risk score calculation;
- evidence snippet extraction;
- debugging/evaluation có kiểm soát.

Tuy nhiên raw chat là dữ liệu rất nhạy cảm. Doctor dashboard nên ưu tiên `clinical_profiles`, `stress_risk_scores` và `evidence_snippets`, không mặc định hiển thị toàn bộ raw chat.

---

## 6. Enum / Value Conventions

Các enum dưới đây nên được định nghĩa đồng bộ ở:

```text
backend/app/core/constants.py
```

và được phản ánh bằng `CHECK` constraints trong SQL schema nếu phù hợp.

### 6.1 `UserRole`

| Value | Meaning |
|---|---|
| `patient` | Người dùng patient-facing chat |
| `doctor` | Doctor/counselor dùng dashboard và copilot |
| `admin` | Quản trị user, assignment, config |

### 6.2 `AuthProvider`

| Value | Meaning |
|---|---|
| `local` | Email/password local login |
| `google` | Google OAuth qua Supabase |

### 6.3 `SessionStatus`

| Value | Meaning |
|---|---|
| `active` | Session đang mở |
| `closed` | Session đã đóng chủ động |
| `timeout` | Session đóng do inactivity timeout |

### 6.4 `MessageRole`

| Value | Meaning |
|---|---|
| `user` | Message từ patient/user |
| `assistant` | Message từ AI assistant |
| `system` | System message hoặc workflow-generated message |

### 6.5 `SafetySeverity`

| Value | Meaning |
|---|---|
| `none` | Không có safety flag |
| `low` | Rủi ro thấp |
| `medium` | Rủi ro trung bình |
| `high` | Rủi ro cao |
| `critical` | Crisis/self-harm/violence cấp tính |

### 6.6 `RiskSeverity`

| Value | Meaning |
|---|---|
| `low` | Risk score thấp |
| `medium` | Risk score trung bình |
| `high` | Risk score cao |
| `critical` | Risk score critical, cần ưu tiên review |

### 6.7 `AuditAction`

Khuyến nghị dùng bộ action naming nhất quán dưới đây:

| Value | Meaning |
|---|---|
| `user_registered` | User đăng ký mới |
| `user_login` | User login thành công |
| `consent_accepted` | User chấp nhận consent |
| `doctor_assignment_created` | Admin tạo assignment |
| `assignment_deactivated` | Admin deactivate assignment |
| `session_started` | Patient chat session bắt đầu |
| `session_closed` | Patient chat session kết thúc |
| `crisis_workflow_activated` | Safety workflow được kích hoạt |
| `clinical_profile_generated` | Silent clinical analyzer tạo profile |
| `doctor_viewed_profile` | Doctor xem clinical profile |
| `differential_diagnosis_generated` | Doctor-facing differential support được generate |
| `doctor_copilot_query` | Doctor hỏi copilot |
| `admin_config_change` | Admin thay đổi config |

Milestone 2 tối thiểu cần audit:

- `user_registered`;
- `user_login`;
- `consent_accepted`;
- `doctor_assignment_created`;
- `assignment_deactivated`.

Các action clinical/agent sẽ được dùng rõ hơn ở milestone sau.

---

## 7. Relationship Summary

```text
users
  ├── consent_records.user_id
  ├── chat_sessions.user_id
  ├── clinical_profiles.patient_id
  ├── stress_risk_scores.patient_id
  ├── audit_logs.user_id
  ├── doctor_assignments.doctor_id
  ├── doctor_assignments.patient_id
  └── doctor_assignments.assigned_by

chat_sessions
  ├── chat_messages.session_id
  ├── clinical_profiles.session_id
  └── stress_risk_scores.session_id
```

Core access relationship:

```text
doctor user -- doctor_assignments --> patient user
```

Core clinical data relationship:

```text
patient user --> chat_sessions --> chat_messages
patient user --> chat_sessions --> clinical_profiles
patient user --> chat_sessions --> stress_risk_scores
```

---

# Table: users

## Purpose

Bảng `users` lưu thông tin user ở application layer.

Bảng này không chỉ phục vụ đăng nhập, mà còn là nguồn chính để backend xác định:

- user là patient, doctor hay admin;
- user có đang active không;
- user đăng ký bằng local email/password hay Google OAuth;
- user nào thực hiện sensitive action trong audit log;
- user nào được assign trong doctor-patient assignment;
- app JWT sẽ được phát hành với user ID và role nào.

Trong MVP, bảng `users` là source of truth cho application-level identity, role và authorization metadata.

---

## Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key của application user |
| `auth_user_id` | UUID | No | ID từ Supabase Auth (auth.users.id), dùng để map giữa Supabase Auth và application user |
| `email` | VARCHAR(255) | Yes | Email đăng nhập, unique toàn hệ thống |
| `password_hash` | VARCHAR(255) | No | Password đã hash bằng bcrypt; nullable cho Google OAuth users |
| `full_name` | VARCHAR(255) | Yes | Tên hiển thị của user |
| `role` | VARCHAR(20) | Yes | Role: `patient`, `doctor`, `admin` |
| `auth_provider` | VARCHAR(50) | Yes | Provider: `local` hoặc `google` |
| `provider_user_id` | VARCHAR(255) | No | ID từ Google/Supabase OAuth provider |
| `avatar_url` | TEXT | No | Avatar từ Google profile nếu có |
| `is_active` | BOOLEAN | Yes | Soft activation flag; inactive user không được login/use API |
| `created_at` | TIMESTAMPTZ | Yes | Thời điểm tạo user |
| `updated_at` | TIMESTAMPTZ | Yes | Thời điểm cập nhật user gần nhất |

---

## Constraints

- `id` là primary key.
- `auth_user_id` nếu tồn tại phải unique (không được trùng).
- `email` phải unique.
- `email` không được null.
- `full_name` không được null.
- `role` chỉ được nhận một trong ba giá trị: `patient`, `doctor`, `admin`.
- `auth_provider` chỉ được nhận một trong hai giá trị: `local`, `google`.
- `is_active` mặc định là `true`.
- `created_at` mặc định là thời điểm hiện tại.
- `updated_at` mặc định là thời điểm hiện tại.
- `password_hash` có thể null cho Google OAuth users.
- `provider_user_id` có thể null cho local users.

---

## Access Rules

- User chỉ được xem thông tin cơ bản của chính mình qua `/auth/me`.
- Admin có thể list users để quản lý role/assignment.
- Doctor không được tự ý list toàn bộ users.
- Patient không được list users.
- Backend không bao giờ trả `password_hash` ra API response.
- Frontend không được tự quyết định role; role luôn lấy từ backend/JWT/database.

---

## Auth Rules

### Local email/password user

Local user cần có:

- `email`;
- `password_hash`;
- `full_name`;
- `role`;
- `auth_provider = local`.

### Google OAuth user

Google OAuth user cần có:

- `email`;
- `full_name`;
- `role`;
- `auth_provider = google`;
- `provider_user_id`;
- `avatar_url`, nếu Google trả về.

Google OAuth user có thể không có `password_hash`.

---

## Index Strategy

| `email` | Login bằng email, check duplicate email |
| `role` | Admin list users theo role |
| `auth_user_id` | Map nhanh giữa Supabase Auth `auth.users.id` và application user |
| `(auth_provider, provider_user_id)` | Tìm user khi Google OAuth callback hoặc provider identity callback |
| `is_active` | Lọc active users nếu cần |

---

## Backend Service Rules

`UserRepository` cần có các method chính:

```text
get_by_id(user_id)
get_by_email(email)
email_exists(email)
get_by_provider_id(provider, provider_user_id)
list_by_role(role)
create(data)
update(user_id, data)
```

`AuthService` cần dùng bảng này để:

- register local user;
- verify email/password;
- map Google OAuth user;
- issue app JWT;
- reject inactive user;
- ghi audit log cho register/login.

---

## Failure Cases

| Case | Expected Result |
|---|---|
| Email đã tồn tại khi register | `409 Conflict` |
| Login sai email/password | `401 Unauthorized` |
| Login local nhưng user không có `password_hash` | `401 Unauthorized` |
| JWT hợp lệ nhưng user đã inactive | `401 Unauthorized` hoặc `403 Forbidden`, tùy API convention |
| Role không đủ quyền | `403 Forbidden` |

---

## Notes

- Bảng này là application-level users table, không thay thế hoàn toàn Supabase Auth internals.
- Google OAuth vẫn có thể đi qua Supabase, nhưng backend sẽ map OAuth identity về bảng `users`.
- `auth_user_id` dùng để map với `auth.users.id` của Supabase Auth.
- Khi dùng Google OAuth qua Supabase, `auth_user_id` sẽ được populate.
- `provider_user_id` vẫn giữ để lưu ID từ Google (hoặc provider khác).
- Trong tương lai, `auth_user_id` có thể trở thành source chính cho identity nếu fully rely vào Supabase Auth.
- Backend là nơi phát hành app JWT riêng.
- Không lưu plain-text password.
- Không expose `password_hash` qua schema response.
- Nếu sau này muốn gắn chặt hơn với Supabase Auth, có thể thêm cột `auth_user_id`.

---

# Table: doctor_assignments

## Purpose

Bảng `doctor_assignments` lưu quan hệ phân công giữa doctor/counselor và patient.

Đây là bảng nền tảng để backend enforce rule:

> Doctor chỉ được truy cập dữ liệu của patient nếu tồn tại một active assignment giữa doctor đó và patient đó.

Trong project này, doctor-patient assignment không chỉ là dữ liệu quản trị. Nó là một phần của security model.

Bảng này được dùng trong các workflow sau:

- Admin assign doctor cho patient.
- Admin deactivate assignment khi doctor không còn phụ trách patient.
- Doctor dashboard chỉ list assigned patients.
- Doctor clinical profile view chỉ mở được nếu doctor được assign.
- Doctor copilot chỉ trả lời về patient nếu doctor được assign.
- Audit log ghi lại assignment creation/deactivation.
- Future clinical endpoints dùng assignment check trước khi trả patient data.

---

## Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key của assignment |
| `doctor_id` | UUID | Yes | FK đến `users.id`, user này phải có role `doctor` |
| `patient_id` | UUID | Yes | FK đến `users.id`, user này phải có role `patient` |
| `assigned_by` | UUID | Yes | FK đến `users.id`, admin tạo assignment |
| `is_active` | BOOLEAN | Yes | Assignment còn hiệu lực hay đã bị deactivate |
| `created_at` | TIMESTAMPTZ | Yes | Thời điểm tạo assignment |

---

## Relationships

| Relationship | Description |
|---|---|
| `doctor_assignments.doctor_id -> users.id` | Doctor được assign |
| `doctor_assignments.patient_id -> users.id` | Patient được assign |
| `doctor_assignments.assigned_by -> users.id` | Admin tạo assignment |

Logic relationship:

- Một doctor có thể được assign nhiều patients.
- Một patient có thể được assign cho nhiều doctors/counselors nếu policy cho phép.
- Một assignment chỉ hợp lệ nếu `doctor_id` là role `doctor`, `patient_id` là role `patient`, `assigned_by` là role `admin`, và `is_active = true`.
- PostgreSQL foreign key chỉ đảm bảo user tồn tại. Việc đảm bảo role đúng sẽ được enforce ở backend service layer trong MVP.

---

## Constraints

- `id` là primary key.
- `doctor_id` không được null.
- `patient_id` không được null.
- `assigned_by` không được null.
- `doctor_id` references `users(id)`.
- `patient_id` references `users(id)`.
- `assigned_by` references `users(id)`.
- `is_active` mặc định là `true`.
- `created_at` mặc định là thời điểm hiện tại.
- Không cho phép duplicate active assignment giữa cùng một doctor và patient.

Khuyến nghị:

> Dùng partial unique index cho active assignment để mô hình linh hoạt hơn và đúng với soft-delete/deactivation workflow.

```sql
CREATE UNIQUE INDEX unique_active_doctor_patient_assignment
ON doctor_assignments(doctor_id, patient_id)
WHERE is_active = TRUE;
```

---

## Access Rules

### Admin

Admin có quyền:

- tạo assignment mới;
- deactivate assignment;
- list assignments;
- list doctors;
- list patients;
- xem assignment status.

Admin action phải đi qua backend endpoint và được audit log.

### Doctor

Doctor có quyền:

- xem danh sách patients được assign cho mình;
- truy cập doctor-facing data của assigned patients ở các milestone sau;
- không được tự tạo assignment;
- không được tự deactivate assignment;
- không được xem patients không được assign.

### Patient

Patient:

- không được tạo assignment;
- không được chỉnh assignment;
- không được list toàn bộ doctors/patients;
- có thể được backend dùng assignment để xác định doctor phụ trách nếu cần hiển thị thông tin cơ bản sau này.

---

## Backend Rule Cốt Lõi

Bất kỳ doctor-facing endpoint nào liên quan đến patient data phải check:

```text
current_user.role == doctor
AND
exists active doctor_assignments where:
  doctor_id = current_user.id
  patient_id = requested_patient_id
  is_active = true
```

Nếu không có active assignment, backend phải trả:

```text
403 Forbidden
```

---

## Lifecycle Rules

### Create assignment

1. Admin gửi request tạo assignment với `doctor_id` và `patient_id`.
2. Backend xác thực current user.
3. Backend kiểm tra current user có role `admin`.
4. Backend load doctor user.
5. Backend kiểm tra doctor user tồn tại và có role `doctor`.
6. Backend load patient user.
7. Backend kiểm tra patient user tồn tại và có role `patient`.
8. Backend kiểm tra assignment active đã tồn tại chưa.
9. Nếu đã tồn tại, có thể trả về assignment hiện tại theo hướng idempotent.
10. Nếu chưa tồn tại, tạo row mới trong `doctor_assignments`.
11. Ghi audit log action `doctor_assignment_created`.

### Deactivate assignment

1. Admin gửi request deactivate assignment.
2. Backend xác thực current user.
3. Backend kiểm tra current user có role `admin`.
4. Backend tìm assignment theo `assignment_id`.
5. Nếu không tồn tại, trả `404 Not Found`.
6. Nếu tồn tại, update `is_active = false`.
7. Ghi audit log action `assignment_deactivated`.

### Reassign

Nếu dùng partial unique index cho active assignments:

- Có thể deactivate assignment cũ.
- Sau đó có thể tạo assignment mới giữa cùng doctor-patient.
- Lịch sử assignment cũ vẫn được giữ lại trong database.

---

## Audit Requirements

| Action | Actor | Resource Type | Resource ID | Metadata |
|---|---|---|---|---|
| `doctor_assignment_created` | admin | `assignment` | assignment id | doctor_id, patient_id |
| `assignment_deactivated` | admin | `assignment` | assignment id | doctor_id, patient_id nếu có |

Các event doctor xem profile/patient sẽ được thêm rõ hơn ở milestone clinical/dashboard sau.

---

## Index Strategy

| Index | Reason |
|---|---|
| `doctor_id` where `is_active = true` | Doctor dashboard list assigned patients |
| `patient_id` where `is_active = true` | Tìm doctors phụ trách patient |
| `(doctor_id, patient_id)` where `is_active = true` | Check doctor có quyền truy cập patient hay không |
| `assigned_by` | Audit/admin review assignment do admin nào tạo |
| `created_at` | Sort assignment history |

---

## Backend Service Rules

`AssignmentService` cần có các method chính:

```text
create_assignment(doctor_id, patient_id, assigned_by)
deactivate_assignment(assignment_id, deactivated_by)
is_doctor_assigned_to_patient(doctor_id, patient_id)
list_patients_for_doctor(doctor_id)
list_doctors_for_patient(patient_id)
```

`AssignmentRepository` cần có các method chính:

```text
get_active_assignment(doctor_id, patient_id)
is_assigned(doctor_id, patient_id)
list_patients_for_doctor(doctor_id)
list_doctors_for_patient(patient_id)
deactivate(assignment_id)
```

---

## Failure Cases

| Case | Expected Result |
|---|---|
| Unauthenticated request tạo assignment | `401 Unauthorized` |
| Non-admin tạo assignment | `403 Forbidden` |
| `doctor_id` không tồn tại | `404 Not Found` |
| `doctor_id` không phải role doctor | `403 Forbidden` |
| `patient_id` không tồn tại | `404 Not Found` |
| `patient_id` không phải role patient | `403 Forbidden` |
| Assignment active đã tồn tại | Trả assignment hiện tại hoặc conflict tùy service design |
| Doctor query unassigned patient | `403 Forbidden` |
| Deactivate assignment không tồn tại | `404 Not Found` |

Khuyến nghị MVP:

> `create_assignment` nên idempotent: nếu active assignment đã tồn tại thì trả về assignment hiện tại, không tạo duplicate và không fail không cần thiết.

---

## Notes

- Bảng này không lưu clinical data.
- Bảng này là access-control relationship table.
- Không dùng frontend để quyết định doctor được xem patient nào.
- Frontend chỉ hiển thị dữ liệu mà backend đã filter.
- Patient-facing API không cần expose assignment chi tiết trong MVP.
- Doctor-facing API bắt buộc dựa vào assignment check.
- Clinical profile access, doctor copilot patient-context mode và doctor dashboard ở các milestone sau đều phải dùng bảng này để enforce authorization.
- Nếu sau này có organization/multi-tenant support, bảng này có thể cần thêm `organization_id`.
- Nếu sau này có counselor/team-based care, có thể cần thêm `assignment_type`, `role_in_care_team`, hoặc `scope`.

---

# Table: consent_records

## Purpose

Bảng `consent_records` lưu lại việc user đã chấp nhận consent policy version nào và vào thời điểm nào.

Đây là bảng quan trọng vì project xử lý dữ liệu sức khỏe tinh thần nhạy cảm. Trước khi patient dùng nền tảng, backend cần biết user đã chấp nhận policy version hiện tại hay chưa.

Bảng này được dùng trong các workflow sau:

- Patient accept consent sau khi register/login lần đầu.
- Backend kiểm tra consent trước khi cho dùng patient chat.
- Khi consent policy version thay đổi, user cần accept lại version mới.
- Audit log ghi lại event `consent_accepted`.
- Admin/compliance reviewer có thể kiểm tra lịch sử consent nếu cần.

---

## Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key của consent record |
| `user_id` | UUID | Yes | FK đến `users.id`, user chấp nhận consent |
| `policy_version` | VARCHAR(20) | Yes | Version của consent policy, ví dụ `1.0` |
| `accepted` | BOOLEAN | Yes | User có accepted hay không; MVP thường là `true` |
| `accepted_at` | TIMESTAMPTZ | Yes | Thời điểm user accepted consent |

---

## Relationships

| Relationship | Description |
|---|---|
| `consent_records.user_id -> users.id` | User đã chấp nhận consent |

Logic relationship:

- Một user có thể có nhiều consent records theo thời gian.
- Mỗi lần policy version thay đổi, user có thể cần tạo consent record mới.
- Backend kiểm tra consent bằng current policy version từ config.

---

## Constraints

- `id` là primary key.
- `user_id` không được null.
- `user_id` references `users(id)`.
- `policy_version` không được null.
- `accepted` không được null, default `true`.
- `accepted_at` mặc định là thời điểm hiện tại.

Không bắt buộc unique trên `(user_id, policy_version)` trong MVP. Lý do:

- Nếu user accept lại cùng version, ta vẫn có thể giữ record lịch sử.
- Service có thể idempotent nếu muốn tránh duplicate.

Nếu muốn enforce mỗi user chỉ có một accepted record trên mỗi policy version, có thể thêm unique index sau:

```sql
CREATE UNIQUE INDEX unique_user_policy_consent
ON consent_records(user_id, policy_version)
WHERE accepted = TRUE;
```

---

## Access Rules

### Patient/User

User có quyền:

- xem consent status của chính mình;
- accept consent cho chính mình;
- không được accept consent thay user khác.

### Doctor

Doctor không cần truy cập consent records của patient trong MVP, trừ khi có workflow compliance cụ thể sau này.

### Admin

Admin có thể xem consent status trong admin/compliance workflow nếu cần, nhưng action này nên được audit nếu xem dữ liệu nhạy cảm ở quy mô lớn.

---

## Lifecycle Rules

### Check consent status

1. Backend lấy current policy version từ config: `current_consent_policy_version`.
2. Backend query `consent_records` theo `user_id`, `policy_version`, `accepted = true`.
3. Nếu tồn tại record, user có valid consent.
4. Nếu không tồn tại, backend trả trạng thái consent required.

### Accept consent

1. User gửi request accept consent.
2. Backend xác thực current user.
3. Backend kiểm tra policy version trong request có match current policy version không, hoặc dùng current version từ backend.
4. Backend tạo row trong `consent_records`.
5. Backend ghi audit log action `consent_accepted`.

---

## Audit Requirements

| Action | Actor | Resource Type | Resource ID | Metadata |
|---|---|---|---|---|
| `consent_accepted` | user | `consent` | consent record id | policy_version |

Audit metadata không nên chứa raw sensitive chat data. Chỉ cần chứa policy version và context tối thiểu.

---

## Index Strategy

| Index | Reason |
|---|---|
| `user_id` | Lấy latest consent của user |
| `(user_id, policy_version)` | Check user đã accept current policy version chưa |
| `accepted_at` | Sort consent history |
| `(user_id, accepted_at)` | Lấy latest consent nhanh hơn |

---

## Backend Service Rules

`ConsentRepository` cần có các method chính:

```text
get_latest_by_user(user_id)
has_accepted_version(user_id, policy_version)
create(data)
```

`ConsentService` cần có các method chính:

```text
accept_consent(user_id, policy_version)
has_valid_consent(user_id)
get_latest_consent(user_id)
get_current_policy_version()
```

---

## Failure Cases

| Case | Expected Result |
|---|---|
| User chưa login gọi consent status | `401 Unauthorized` |
| User accept consent thay user khác | `403 Forbidden` |
| User chưa accept current policy version nhưng gọi patient chat | `403 Consent Required` |
| Policy version request không hợp lệ | `400 Bad Request` hoặc backend bỏ qua client version và dùng current server version |

---

## Notes

- Consent record không thay thế legal/compliance review.
- Milestone 2 chỉ lưu version và timestamp.
- Nội dung consent policy thực tế có thể nằm trong docs/config hoặc frontend text.
- Khi policy version thay đổi, `current_consent_policy_version` trong config phải được update.
- Consent status nên được frontend kiểm tra sau login.

---

# Table: chat_sessions

## Purpose

Bảng `chat_sessions` lưu một phiên chat patient-facing.

Một session là đơn vị workflow chính cho:

- patient chat;
- session closure;
- silent clinical analysis;
- clinical profile generation;
- stress/risk score calculation;
- evidence snippet extraction;
- audit và trace linkage.

Trong Milestone 2, bảng này chủ yếu được thiết kế và tạo schema. Chat API và agent workflow sẽ được triển khai rõ hơn ở milestone sau.

---

## Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key của chat session |
| `user_id` | UUID | Yes | FK đến `users.id`, patient sở hữu session |
| `status` | VARCHAR(20) | Yes | `active`, `closed`, hoặc `timeout` |
| `started_at` | TIMESTAMPTZ | Yes | Thời điểm session bắt đầu |
| `ended_at` | TIMESTAMPTZ | No | Thời điểm session kết thúc, null nếu active |
| `metadata` | JSONB | Yes | Metadata phụ: closure reason, channel, locale, trace ids |

---

## Relationships

| Relationship | Description |
|---|---|
| `chat_sessions.user_id -> users.id` | Patient sở hữu session |
| `chat_messages.session_id -> chat_sessions.id` | Messages thuộc session |
| `clinical_profiles.session_id -> chat_sessions.id` | Clinical profile được tạo từ session |
| `stress_risk_scores.session_id -> chat_sessions.id` | Risk score được tính từ session |

Logic relationship:

- Một patient có nhiều chat sessions.
- Một session có nhiều messages.
- Một session có thể tạo một clinical profile sau khi closed/timeout.
- Một session có thể tạo một stress/risk score.

---

## Constraints

- `id` là primary key.
- `user_id` không được null.
- `user_id` references `users(id)`.
- `status` không được null và chỉ nhận `active`, `closed`, `timeout`.
- `started_at` mặc định là thời điểm hiện tại.
- `ended_at` nullable khi session còn active.
- `metadata` mặc định là `{}`.

Application-level constraint:

- `user_id` phải là user role `patient` khi tạo patient chat session.
- Không nên có quá nhiều active sessions cùng lúc cho cùng một patient nếu product policy muốn mỗi patient chỉ có một active session.

Nếu muốn enforce một active session trên mỗi patient ở DB level, có thể thêm partial unique index sau:

```sql
CREATE UNIQUE INDEX unique_active_session_per_patient
ON chat_sessions(user_id)
WHERE status = 'active';
```

MVP có thể chưa cần index này nếu flow chat chưa hoàn thiện.

---

## Access Rules

### Patient

Patient có quyền:

- tạo session cho chính mình;
- xem session history của chính mình;
- end session của chính mình.

Patient không được:

- xem session của user khác;
- xem clinical profile được tạo từ session;
- sửa metadata nội bộ như trace IDs hoặc clinical workflow state.

### Doctor

Doctor chỉ có thể xem thông tin session của assigned patients nếu endpoint doctor-facing cần hiển thị.

Doctor không mặc định được xem full raw chat. Nếu có raw chat access sau này, phải:

- có active assignment;
- có policy cho phép;
- audit log action truy cập.

### Admin

Admin không mặc định được xem raw chat/session details nếu policy chưa cho phép. Admin có thể dùng aggregate/admin metadata nếu cần quản trị hệ thống.

---

## Lifecycle Rules

### Start session

1. Patient login.
2. Backend check valid consent.
3. Backend tạo `chat_sessions` với `status = active`.
4. Backend ghi audit log action `session_started` nếu workflow cần.

### Close session

1. Patient bấm End Session, hoặc system detect closure intent, hoặc timeout.
2. Backend update `status = closed` hoặc `timeout`.
3. Backend set `ended_at = now()`.
4. Backend trigger hoặc gọi Silent Clinical Analyzer ở milestone sau.
5. Backend ghi audit log action `session_closed`.

### Session timeout

1. Backend/background workflow detect inactivity.
2. Backend update `status = timeout`.
3. Backend set `ended_at = now()`.
4. Backend có thể tạo gentle closure message.
5. Backend có thể trigger silent clinical analysis.

---

## Audit Requirements

| Action | Actor | Resource Type | Resource ID | Metadata |
|---|---|---|---|---|
| `session_started` | patient/system | `chat_session` | session id | optional channel/trace info |
| `session_closed` | patient/system | `chat_session` | session id | closure reason, status |

Milestone 2 có thể chưa cần full session audit implementation nếu chat API chưa làm, nhưng schema phải sẵn sàng.

---

## Index Strategy

| Index | Reason |
|---|---|
| `user_id` | Lấy sessions của patient |
| `(user_id, started_at)` | Sort session history của patient |
| `status` | Tìm active/timeout sessions |
| `started_at` | Query theo time window |
| `ended_at` | Query closed sessions hoặc cleanup/retention sau này |

---

## Backend Service Rules

Milestone sau sẽ cần `SessionRepository` hoặc service tương ứng với các method:

```text
create_session(user_id, metadata)
get_by_id(session_id)
list_by_user(user_id)
get_active_session(user_id)
close_session(session_id, reason)
mark_timeout(session_id)
```

Milestone 2 có thể chỉ tạo schema và Pydantic model nếu cần.

---

## Failure Cases

| Case | Expected Result |
|---|---|
| User chưa login tạo session | `401 Unauthorized` |
| User chưa accept consent tạo session | `403 Consent Required` |
| Doctor tạo patient chat session | `403 Forbidden` |
| Patient xem session của user khác | `403 Forbidden` |
| Session không tồn tại | `404 Not Found` |
| End session đã closed | Idempotent return hoặc `409 Conflict`, tùy service design |

---

## Notes

- `metadata` có thể chứa `closure_reason`, `locale`, `channel`, `client_info`, `langfuse_trace_id` sau này.
- Không lưu quá nhiều clinical inference trong `metadata`; doctor-facing clinical data nên nằm ở `clinical_profiles`.
- Session là đơn vị chính để nối chat messages, clinical profile và risk score.

---

# Table: chat_messages

## Purpose

Bảng `chat_messages` lưu từng message trong một chat session.

Bảng này cần cho:

- patient xem lại session history;
- AI trả lời theo context;
- safety guardrail metadata;
- silent clinical analyzer đọc session sau closure;
- evidence snippet extraction;
- risk score calculation;
- future evaluation/debugging có kiểm soát.

Raw chat là dữ liệu rất nhạy cảm, nên bảng này cần access control nghiêm ngặt.

---

## Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key của message |
| `session_id` | UUID | Yes | FK đến `chat_sessions.id` |
| `role` | VARCHAR(20) | Yes | `user`, `assistant`, hoặc `system` |
| `content` | TEXT | Yes | Nội dung message |
| `safety_flag` | BOOLEAN | Yes | Message có safety flag hay không |
| `safety_severity` | VARCHAR(20) | Yes | `none`, `low`, `medium`, `high`, `critical` |
| `trace_id` | VARCHAR(255) | No | Link sang Langfuse/internal trace nếu có |
| `created_at` | TIMESTAMPTZ | Yes | Thời điểm tạo message |

---

## Relationships

| Relationship | Description |
|---|---|
| `chat_messages.session_id -> chat_sessions.id` | Message thuộc session |

Logic relationship:

- Một session có nhiều messages.
- Messages được sort theo `created_at`.
- `role` phân biệt message từ patient, assistant, hoặc system.
- Safety metadata nằm ở message level để biết tín hiệu rủi ro xuất hiện ở đâu.

---

## Constraints

- `id` là primary key.
- `session_id` không được null.
- `session_id` references `chat_sessions(id)`.
- `role` chỉ được nhận `user`, `assistant`, `system`.
- `content` không được null.
- `safety_flag` default `false`.
- `safety_severity` default `none` và chỉ nhận `none`, `low`, `medium`, `high`, `critical`.
- `created_at` mặc định là thời điểm hiện tại.

Application-level consistency:

- Nếu `safety_flag = false`, `safety_severity` nên là `none`.
- Nếu `safety_severity` là `high` hoặc `critical`, safety workflow phải được kích hoạt hoặc ghi nhận.

---

## Access Rules

### Patient

Patient có quyền:

- xem messages thuộc sessions của chính mình;
- tạo user message trong active session của chính mình.

Patient không được:

- xem messages của user khác;
- sửa/xóa message sau khi đã ghi;
- xem internal system notes nếu sau này có system metadata nhạy cảm.

### Doctor

Doctor không mặc định được xem full raw chat trong dashboard.

Nếu doctor-facing endpoint cần raw chat access sau này, backend phải check:

- doctor role;
- active doctor-patient assignment;
- policy cho phép raw chat access;
- audit log access event.

### Admin

Admin không mặc định được xem raw chat. Admin access nếu có phải được policy-gated và audit-logged.

---

## Lifecycle Rules

### Insert patient message

1. Patient gửi message.
2. Backend xác thực current user.
3. Backend check consent.
4. Backend check session thuộc patient và đang active.
5. Backend chạy Safety Guardrail trước normal response ở milestone agent.
6. Backend insert message với role `user`.
7. Backend lưu safety metadata nếu có.

### Insert assistant message

1. Agent workflow tạo assistant response.
2. Backend insert message với role `assistant`.
3. Backend lưu trace ID nếu có.
4. Nếu safety response, set safety metadata phù hợp.

### Insert system message

System message chỉ dùng cho workflow nội bộ hoặc visible system events. Cần cẩn thận để không lộ prompt nội bộ hoặc clinical reasoning cho patient.

---

## Audit Requirements

Không audit từng message mặc định để tránh audit log quá lớn và tránh copy raw chat vào audit metadata.

Các event nên audit ở mức workflow:

| Action | Resource Type | Resource ID | Metadata |
|---|---|---|---|
| `crisis_workflow_activated` | `chat_session` | session id | severity, message_id, no raw content hoặc snippet tối thiểu |
| `session_started` | `chat_session` | session id | optional |
| `session_closed` | `chat_session` | session id | closure reason |

Nếu doctor/admin xem raw chat sau này, audit event nên là access event, không phải copy toàn bộ message content.

---

## Index Strategy

| Index | Reason |
|---|---|
| `session_id` | Lấy messages của session |
| `(session_id, created_at)` | Render ordered chat history |
| `created_at` | Query theo time window, retention/archive |
| `safety_flag` | Tìm messages có safety flag |
| `safety_severity` | Review critical/high risk messages |
| `trace_id` | Link message với Langfuse/internal trace |

---

## Backend Service Rules

Milestone sau sẽ cần `MessageRepository` hoặc service tương ứng với các method:

```text
create_message(session_id, role, content, safety_metadata, trace_id)
list_by_session(session_id)
list_flagged_messages(patient_id or session_id)
get_by_id(message_id)
```

Service layer phải đảm bảo:

- patient chỉ ghi message vào session của chính mình;
- assistant/system message chỉ được tạo bởi backend workflow;
- không log raw message content ra application logs nếu không cần.

---

## Failure Cases

| Case | Expected Result |
|---|---|
| User chưa login gửi message | `401 Unauthorized` |
| User chưa accept consent gửi message | `403 Consent Required` |
| Patient gửi message vào session của user khác | `403 Forbidden` |
| Gửi message vào closed session | `409 Conflict` hoặc tạo session mới tùy product flow |
| Session không tồn tại | `404 Not Found` |
| Role message không hợp lệ | `400 Bad Request` |

---

## Notes

- Raw chat là sensitive data.
- Không đưa raw chat vào `audit_logs.metadata` nếu không cần.
- Không dùng bảng này làm doctor-facing clinical summary; clinical summary nằm ở `clinical_profiles`.
- Evidence snippets nên được extract vừa đủ, không copy toàn bộ session.
- Sau này cần retention/anonymization/purge policy cho bảng này.

---

# Table: clinical_profiles

## Purpose

Bảng `clinical_profiles` lưu doctor-facing clinical profile do Silent Clinical Analyzer tạo sau khi patient session kết thúc.

Bảng này là doctor-facing. Patient không được truy cập bảng này.

Clinical profile giúp doctor/counselor review:

- summary của session;
- symptoms/signals được extract;
- risk markers;
- evidence snippets;
- context để chuẩn bị clinical review;
- input cho doctor copilot patient-context mode ở milestone sau.

AI-generated profile không phải final diagnosis. Nó là decision-support artifact cho professional review.

---

## Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key của clinical profile |
| `session_id` | UUID | Yes | FK đến `chat_sessions.id` |
| `patient_id` | UUID | Yes | FK đến `users.id`, patient mà profile thuộc về |
| `summary` | TEXT | Yes | Doctor-facing session summary |
| `symptoms` | JSONB | Yes | Extracted symptoms/signals, default `[]` |
| `risk_markers` | JSONB | Yes | Risk markers, default `[]` |
| `evidence_snippets` | JSONB | Yes | Supporting snippets, default `[]` |
| `generated_at` | TIMESTAMPTZ | Yes | Thời điểm profile được generate |

---

## Relationships

| Relationship | Description |
|---|---|
| `clinical_profiles.session_id -> chat_sessions.id` | Session nguồn của profile |
| `clinical_profiles.patient_id -> users.id` | Patient mà profile thuộc về |

Logic relationship:

- Một patient có nhiều clinical profiles theo sessions.
- Một session trong MVP thường tạo một clinical profile.
- Profile phải được tạo từ session của cùng patient.
- Doctor chỉ được xem profile nếu doctor được assign với patient.

---

## Constraints

- `id` là primary key.
- `session_id` không được null.
- `session_id` references `chat_sessions(id)`.
- `patient_id` không được null.
- `patient_id` references `users(id)`.
- `summary` không được null.
- `symptoms` default `[]`.
- `risk_markers` default `[]`.
- `evidence_snippets` default `[]`.
- `generated_at` mặc định là thời điểm hiện tại.

Application-level constraints:

- `patient_id` phải là user role `patient`.
- `session_id` phải thuộc về cùng `patient_id`.
- Clinical profile chỉ nên được generate sau khi session đã closed/timeout.
- Patient-facing API không được expose table này.

MVP có thể không đặt `UNIQUE(session_id)` để giữ linh hoạt. Nếu muốn enforce một profile/session, có thể thêm:

```sql
CREATE UNIQUE INDEX unique_clinical_profile_per_session
ON clinical_profiles(session_id);
```

Nếu sau này cần versioning profile, không dùng unique này mà thêm `version` hoặc bảng `clinical_profile_versions`.

---

## JSONB Field Conventions

### `symptoms`

Nên là array object hoặc string thống nhất. Ví dụ:

```json
[
  {
    "label": "sleep difficulty",
    "evidence_message_id": "...",
    "confidence": "medium"
  }
]
```

### `risk_markers`

Nên chứa severity/source rõ ràng. Ví dụ:

```json
[
  {
    "marker": "self-harm ideation",
    "severity": "high",
    "source": "patient_message",
    "evidence_message_id": "..."
  }
]
```

### `evidence_snippets`

Nên chứa snippet ngắn, không copy toàn bộ raw chat. Ví dụ:

```json
[
  {
    "snippet": "short supporting text",
    "message_id": "...",
    "timestamp": "...",
    "category": "risk_marker"
  }
]
```

Không lưu quá nhiều raw content nếu không cần.

---

## Access Rules

### Patient

Patient không được:

- xem `clinical_profiles`;
- xem symptoms/risk markers theo clinical language;
- xem DSM-5/differential diagnosis content;
- gọi API doctor-facing profile.

Patient có thể xem simplified emotional trend ở UI khác, không phải bảng này.

### Doctor

Doctor có quyền xem profile nếu:

```text
current_user.role == doctor
AND active assignment exists with patient_id
```

Doctor access phải được audit log bằng action `doctor_viewed_profile` ở milestone clinical/dashboard.

### Admin

Admin không mặc định được xem clinical profile nếu policy chưa cho phép. Nếu admin access được thêm sau, phải policy-gated và audit-logged.

---

## Lifecycle Rules

### Generate clinical profile

1. Session kết thúc bằng manual end, closure intent, hoặc timeout.
2. Backend/agent workflow load session messages.
3. Silent Clinical Analyzer tạo profile.
4. Backend validate output bằng Pydantic schema.
5. Backend insert row vào `clinical_profiles`.
6. Backend ghi audit log action `clinical_profile_generated`.
7. Doctor dashboard có thể hiển thị profile cho assigned doctor.

### Doctor view profile

1. Doctor gọi endpoint xem patient profile.
2. Backend xác thực current user.
3. Backend check role doctor.
4. Backend check active assignment với patient.
5. Backend load clinical profile.
6. Backend ghi audit log action `doctor_viewed_profile`.
7. Backend trả doctor-facing response.

---

## Audit Requirements

| Action | Actor | Resource Type | Resource ID | Metadata |
|---|---|---|---|---|
| `clinical_profile_generated` | system | `clinical_profile` | profile id | session_id, patient_id, trace_id nếu có |
| `doctor_viewed_profile` | doctor | `clinical_profile` | profile id | patient_id, assignment_id nếu có |

Audit metadata không nên chứa full raw chat hoặc full profile content.

---

## Index Strategy

| Index | Reason |
|---|---|
| `patient_id` | Doctor dashboard load profiles theo patient |
| `session_id` | Load profile từ session |
| `(patient_id, generated_at)` | Sort profile timeline |
| `generated_at` | Review profile generation history |

Nếu query JSONB nhiều sau này, có thể thêm GIN index cho `risk_markers` hoặc `symptoms`, nhưng không cần trong Milestone 2.

---

## Backend Service Rules

Milestone sau sẽ cần `ClinicalProfileRepository` hoặc service tương ứng với các method:

```text
create_profile(session_id, patient_id, summary, symptoms, risk_markers, evidence_snippets)
get_by_id(profile_id)
list_by_patient(patient_id)
get_latest_by_patient(patient_id)
get_by_session(session_id)
```

Clinical access service phải enforce:

```text
doctor role + active assignment
```

---

## Failure Cases

| Case | Expected Result |
|---|---|
| Patient gọi API clinical profile | `403 Forbidden` |
| Doctor xem unassigned patient profile | `403 Forbidden` |
| Profile không tồn tại | `404 Not Found` |
| Session chưa closed nhưng generate profile | `409 Conflict` hoặc background workflow defer |
| Clinical analyzer output invalid | Không ghi DB; log/evaluate lỗi an toàn |

---

## Notes

- Patient-facing AI không được expose clinical profile.
- Doctor-facing output phải ghi rõ là decision support, không phải diagnosis cuối cùng.
- DSM-5 differential diagnosis support là doctor-only và thuộc milestone sau.
- `evidence_snippets` nên là snippet ngắn, có source reference rõ ràng.
- Khi workflow ổn định hơn, có thể chuẩn hóa `symptoms`, `risk_markers`, `evidence_snippets` thành bảng con.
- `symptoms`, `risk_markers`, `evidence_snippets` hiện được lưu dưới dạng JSONB để tối ưu tốc độ phát triển ở MVP.
- Nếu cần analytics/reporting sâu (ví dụ: thống kê triệu chứng theo thời gian hoặc population), nên chuẩn hóa thành các bảng riêng:

  - `symptom_catalog`
  - `clinical_profile_symptoms`

- Khi đó, `clinical_profiles.symptoms` có thể được thay bằng quan hệ many-to-many.
- Quyết định chuẩn hóa sẽ được thực hiện sau khi ổn định clinical analyzer và xác định rõ nhu cầu analytics.

---

# Table: stress_risk_scores

## Purpose

Bảng `stress_risk_scores` lưu session-level stress/risk score để hỗ trợ:

- patient simplified trend;
- doctor dashboard prioritization;
- risk trend visualization;
- clinical review;
- safety/evaluation workflow;
- evidence-grounded interpretation.

Score là internal scale 0-100. Patient-facing UI nên hiển thị đơn giản hơn, ví dụ Low/Medium/High, không nhất thiết hiển thị số chi tiết.

---

## Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key của risk score |
| `session_id` | UUID | Yes | FK đến `chat_sessions.id` |
| `patient_id` | UUID | Yes | FK đến `users.id` |
| `score` | INTEGER | Yes | Score 0-100 |
| `severity` | VARCHAR(20) | Yes | `low`, `medium`, `high`, `critical` |
| `evidence` | JSONB | Yes | Evidence/explanation cho score, default `{}` |
| `calculated_at` | TIMESTAMPTZ | Yes | Thời điểm score được tính |

---

## Relationships

| Relationship | Description |
|---|---|
| `stress_risk_scores.session_id -> chat_sessions.id` | Session nguồn của score |
| `stress_risk_scores.patient_id -> users.id` | Patient mà score thuộc về |

Logic relationship:

- Một patient có nhiều scores theo sessions.
- Một session trong MVP thường có một final score.
- Có thể có nhiều score nếu sau này tính lại hoặc có interim scoring.

---

## Constraints

- `id` là primary key.
- `session_id` không được null.
- `session_id` references `chat_sessions(id)`.
- `patient_id` không được null.
- `patient_id` references `users(id)`.
- `score` không được null.
- `score` phải nằm trong khoảng 0 đến 100.
- `severity` chỉ được nhận `low`, `medium`, `high`, `critical`.
- `evidence` default `{}`.
- `calculated_at` mặc định là thời điểm hiện tại.

Application-level constraints:

- `patient_id` phải là role `patient`.
- `session_id` phải thuộc cùng patient.
- Score phải được tính từ session evidence, không hallucinate.

---

## Evidence JSONB Convention

`evidence` nên chứa thông tin giải thích score nhưng không copy quá nhiều raw chat.

Ví dụ:

```json
{
  "signals": [
    {
      "type": "sleep_difficulty",
      "weight": "medium",
      "evidence_message_id": "..."
    }
  ],
  "safety": {
    "highest_severity": "medium",
    "crisis_detected": false
  },
  "model_trace_id": "..."
}
```

Không nên lưu full prompt hoặc full raw chat trong field này.

---

## Access Rules

### Patient

Patient có thể xem trend đơn giản của chính mình:

- severity category;
- trend over time;
- supportive framing.

Patient-facing UI không nên hiển thị alarming clinical language hoặc diagnosis.

### Doctor

Doctor có thể xem numerical score, severity, trend và evidence nếu:

```text
current_user.role == doctor
AND active assignment exists with patient_id
```

### Admin

Admin không mặc định xem patient risk scores nếu policy chưa cho phép. Aggregate/operational dashboard có thể dùng de-identified data sau này.

---

## Lifecycle Rules

### Calculate score

1. Session có messages.
2. Safety/clinical workflow extract signals.
3. Risk scoring logic tính score 0-100 và severity.
4. Backend validate score range và severity.
5. Backend insert row vào `stress_risk_scores`.
6. Nếu severity high/critical, safety/doctor review workflow có thể được trigger.

### View trend

1. Patient/doctor gọi trend endpoint.
2. Backend xác thực current user.
3. Backend check access rule.
4. Backend query scores theo `patient_id` order by `calculated_at`.
5. Backend trả response phù hợp role.

---

## Audit Requirements

Milestone 2 không nhất thiết audit mọi score calculation nếu workflow chưa làm. Ở milestone sau, nên audit/log event khi:

| Action | Actor | Resource Type | Resource ID | Metadata |
|---|---|---|---|---|
| `crisis_workflow_activated` | system | `chat_session` | session id | score_id, severity |
| `doctor_viewed_profile` | doctor | `patient` hoặc `clinical_profile` | patient/profile id | có thể bao gồm score_id |

Score generation trace chi tiết nên đi qua Langfuse ở milestone observability, không thay thế `audit_logs`.

---

## Index Strategy

| Index | Reason |
|---|---|
| `patient_id` | Lấy score trend theo patient |
| `(patient_id, calculated_at)` | Render risk trend timeline |
| `session_id` | Load score theo session |
| `severity` | Filter high/critical patients |
| `calculated_at` | Query theo time window |

---

## Backend Service Rules

Milestone sau sẽ cần `RiskScoreRepository` hoặc service tương ứng với các method:

```text
create_score(session_id, patient_id, score, severity, evidence)
get_by_session(session_id)
list_by_patient(patient_id)
list_recent_high_risk(limit)
```

Doctor dashboard service sẽ cần query assigned patients + latest risk score.

---

## Failure Cases

| Case | Expected Result |
|---|---|
| Score ngoài 0-100 | Validation error, không ghi DB |
| Severity không hợp lệ | Validation error, không ghi DB |
| Patient xem score của user khác | `403 Forbidden` |
| Doctor xem score của unassigned patient | `403 Forbidden` |
| Session không thuộc patient | Validation error hoặc `409 Conflict` |

---

## Notes

- Score không phải diagnosis.
- Patient-facing display cần supportive, không gây hoảng sợ.
- Doctor-facing display có thể chi tiết hơn nhưng vẫn là decision support.
- Evidence nên đủ để explain score nhưng không expose quá nhiều raw chat.
- Nếu sau này score được tính nhiều lần trên cùng session, cần thêm field như `score_type`, `version`, hoặc `calculation_reason`.

---

# Table: audit_logs

## Purpose

Bảng `audit_logs` lưu sensitive actions và system events để hỗ trợ traceability, compliance-oriented review và incident investigation.

Audit log là một trong các bảng quan trọng nhất của project vì hệ thống xử lý dữ liệu mental health nhạy cảm và có role separation giữa patient, doctor và admin.

Bảng này dùng để ghi lại:

- user registration/login;
- consent acceptance;
- admin assignment changes;
- session start/close;
- crisis workflow activation;
- clinical profile generation;
- doctor access to clinical profile;
- doctor copilot query;
- differential diagnosis support generation;
- admin config changes.

---

## Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key của audit log |
| `user_id` | UUID | No | FK đến `users.id`, actor thực hiện action; nullable cho system event |
| `role` | VARCHAR(20) | No | Role của actor tại thời điểm action |
| `action` | VARCHAR(100) | Yes | Audit action name |
| `resource_type` | VARCHAR(100) | No | Loại resource bị tác động, ví dụ `user`, `assignment`, `clinical_profile` |
| `resource_id` | VARCHAR(255) | No | ID của resource bị tác động |
| `metadata` | JSONB | Yes | Context bổ sung, default `{}` |
| `ip_address` | VARCHAR(45) | No | IPv4/IPv6 address nếu capture được |
| `created_at` | TIMESTAMPTZ | Yes | Thời điểm audit event được ghi |

---

## Relationships

| Relationship | Description |
|---|---|
| `audit_logs.user_id -> users.id` | User thực hiện action, nếu có |

`resource_id` không dùng foreign key cứng vì audit log có thể tham chiếu nhiều loại resource khác nhau.

---

## Constraints

- `id` là primary key.
- `user_id` nullable.
- `user_id` references `users(id)` nếu có.
- `action` không được null.
- `metadata` default `{}`.
- `created_at` mặc định là thời điểm hiện tại.

Application-level constraints:

- Audit log nên append-only.
- Không update/delete audit logs trừ maintenance/compliance procedure đặc biệt.
- `metadata` không nên chứa full raw chat hoặc secrets.
- `role` nên ghi lại role tại thời điểm action, không chỉ join current role.

---

## Action Naming

Khuyến nghị dùng action values thống nhất:

```text
user_registered
user_login
consent_accepted
doctor_assignment_created
assignment_deactivated
session_started
session_closed
crisis_workflow_activated
clinical_profile_generated
doctor_viewed_profile
differential_diagnosis_generated
doctor_copilot_query
admin_config_change
```

Milestone 2 tối thiểu implement:

```text
user_registered
user_login
consent_accepted
doctor_assignment_created
assignment_deactivated
```

---

## Metadata Convention

`metadata` nên là JSON object nhỏ, chỉ chứa context cần thiết.

Ví dụ login:

```json
{
  "method": "google"
}
```

Ví dụ assignment created:

```json
{
  "doctor_id": "...",
  "patient_id": "..."
}
```

Ví dụ clinical profile generated:

```json
{
  "session_id": "...",
  "patient_id": "...",
  "trace_id": "..."
}
```

Không lưu:

- plain-text password;
- API keys;
- JWT tokens;
- full raw chat;
- full clinical profile content;
- full prompt nội bộ nếu không cần.

---

## Access Rules

### Patient

Patient không mặc định xem audit logs. Có thể sau này có personal activity log đơn giản, nhưng cần thiết kế riêng để không expose internal metadata.

### Doctor

Doctor không mặc định xem audit logs toàn hệ thống. Có thể xem audit liên quan đến hành động của chính mình nếu có feature riêng.

### Admin

Admin/compliance reviewer có thể xem audit logs nếu có policy cho phép.

Audit viewer endpoint phải:

- require admin/compliance role;
- hỗ trợ filter theo user/action/resource/time;
- không expose quá nhiều metadata nhạy cảm;
- audit chính hành động xem audit nếu cần.

---

## Lifecycle Rules

### Write audit log

1. Service gọi `AuditService.log(...)`.
2. `AuditService` normalize action, actor, resource, metadata.
3. `AuditRepository` insert row vào `audit_logs`.
4. Không chỉnh sửa row sau khi ghi.

### Query audit logs

1. Admin/compliance endpoint xác thực current user.
2. Backend check role và policy.
3. Backend query theo filter.
4. Backend trả paginated results.
5. Nếu audit viewer là sensitive action, ghi thêm audit event.

---

## Index Strategy

| Index | Reason |
|---|---|
| `user_id` | Query logs theo actor |
| `action` | Query logs theo action type |
| `created_at` | Query time window, sort recent events |
| `(resource_type, resource_id)` | Query logs của một resource |
| `(user_id, created_at)` | User activity timeline |
| `(action, created_at)` | Event review theo action/time |

---

## Backend Service Rules

`AuditRepository` cần có các method chính:

```text
create(data)
list_by_user(user_id, limit)
list_by_action(action, limit)
```

`AuditService` cần có các method chính:

```text
log(action, user_id, role, resource_type, resource_id, metadata)
get_user_logs(user_id, limit)
get_logs_by_action(action, limit)
```

Các service khác không nên insert trực tiếp vào `audit_logs`; nên đi qua `AuditService` để naming và metadata nhất quán.

---

## Failure Cases

| Case | Expected Result |
|---|---|
| Audit insert fail trong non-critical flow | Log application error; không expose stack trace |
| Audit insert fail trong critical compliance flow | Có thể fail closed tùy endpoint |
| Metadata chứa non-serializable object | Validate trước khi insert |
| Action name không nằm trong enum | Validation error hoặc reject |

---

## Notes

- Audit log không thay thế Langfuse trace.
- Langfuse trace phục vụ LLMOps/prompt/retrieval/model output.
- Audit log phục vụ application-level sensitive action tracking.
- Không lưu secrets hoặc raw chat quá mức trong audit metadata.
- Production có thể cần append-only hardening, retention policy, export policy và backup strategy.

---

# 8. Access Matrix

| Data / Action | Patient | Doctor | Admin | System |
|---|---:|---:|---:|---:|
| Register/login self | Yes | Yes | Yes | No |
| View `/auth/me` | Own only | Own only | Own only | No |
| List users | No | No | Yes | No |
| Create doctor assignment | No | No | Yes | No |
| Deactivate assignment | No | No | Yes | No |
| View own consent status | Yes | Yes | Yes | No |
| Accept own consent | Yes | Yes | Yes | No |
| Create own chat session | Yes | No | No | Optional |
| View own chat sessions | Yes | No | No | Optional |
| View raw chat of assigned patient | No | Policy-gated | Policy-gated | Yes for workflow |
| View clinical profile | No | Assigned patient only | Policy-gated | Yes for workflow |
| View risk score | Own simplified only | Assigned patient only | Policy-gated | Yes for workflow |
| Write audit log | No direct | No direct | No direct | Yes |
| View audit logs | No | No by default | Yes, policy-gated | Optional |

---

# 9. Global Index Summary

| Table | Recommended Indexes |
|---|---|
| `users` | `email`, `role`, `(auth_provider, provider_user_id)`, `is_active` |
| `doctor_assignments` | `doctor_id where is_active`, `patient_id where is_active`, unique `(doctor_id, patient_id) where is_active`, `assigned_by`, `created_at` |
| `consent_records` | `user_id`, `(user_id, policy_version)`, `(user_id, accepted_at)`, `accepted_at` |
| `chat_sessions` | `user_id`, `(user_id, started_at)`, `status`, `started_at`, `ended_at` |
| `chat_messages` | `session_id`, `(session_id, created_at)`, `created_at`, `safety_flag`, `safety_severity`, `trace_id` |
| `clinical_profiles` | `patient_id`, `session_id`, `(patient_id, generated_at)`, `generated_at` |
| `stress_risk_scores` | `patient_id`, `(patient_id, calculated_at)`, `session_id`, `severity`, `calculated_at` |
| `audit_logs` | `user_id`, `action`, `created_at`, `(resource_type, resource_id)`, `(user_id, created_at)`, `(action, created_at)` |

---

# 10. DBML Draft for ERD

Có thể paste phần này vào dbdiagram.io để tạo ERD ban đầu.

```dbml
Table users {
  id uuid [pk]
  email varchar [unique, not null]
  password_hash varchar
  full_name varchar [not null]
  role varchar [not null]
  auth_provider varchar [not null]
  provider_user_id varchar
  avatar_url text
  is_active boolean
  created_at timestamptz
  updated_at timestamptz
}

Table doctor_assignments {
  id uuid [pk]
  doctor_id uuid [not null]
  patient_id uuid [not null]
  assigned_by uuid [not null]
  is_active boolean
  created_at timestamptz
}

Table consent_records {
  id uuid [pk]
  user_id uuid [not null]
  policy_version varchar [not null]
  accepted boolean [not null]
  accepted_at timestamptz
}

Table chat_sessions {
  id uuid [pk]
  user_id uuid [not null]
  status varchar [not null]
  started_at timestamptz
  ended_at timestamptz
  metadata jsonb
}

Table chat_messages {
  id uuid [pk]
  session_id uuid [not null]
  role varchar [not null]
  content text [not null]
  safety_flag boolean
  safety_severity varchar
  trace_id varchar
  created_at timestamptz
}

Table clinical_profiles {
  id uuid [pk]
  session_id uuid [not null]
  patient_id uuid [not null]
  summary text [not null]
  symptoms jsonb
  risk_markers jsonb
  evidence_snippets jsonb
  generated_at timestamptz
}

Table stress_risk_scores {
  id uuid [pk]
  session_id uuid [not null]
  patient_id uuid [not null]
  score integer [not null]
  severity varchar [not null]
  evidence jsonb
  calculated_at timestamptz
}

Table audit_logs {
  id uuid [pk]
  user_id uuid
  role varchar
  action varchar [not null]
  resource_type varchar
  resource_id varchar
  metadata jsonb
  ip_address varchar
  created_at timestamptz
}

Ref: doctor_assignments.doctor_id > users.id
Ref: doctor_assignments.patient_id > users.id
Ref: doctor_assignments.assigned_by > users.id

Ref: consent_records.user_id > users.id

Ref: chat_sessions.user_id > users.id
Ref: chat_messages.session_id > chat_sessions.id

Ref: clinical_profiles.session_id > chat_sessions.id
Ref: clinical_profiles.patient_id > users.id

Ref: stress_risk_scores.session_id > chat_sessions.id
Ref: stress_risk_scores.patient_id > users.id

Ref: audit_logs.user_id > users.id
```

---

# 11. Mapping to Milestone 2 Implementation Tasks

| Milestone 2 Task | Database Model Relevance |
|---|---|
| 2.1 Dependencies | Supabase/JWT/password hashing support cho model này |
| 2.2 Config | Supabase URL/key, JWT, Google OAuth, consent policy version |
| 2.3 `docs/schema.sql` | SQL implementation trực tiếp từ tài liệu này |
| 2.4 Constants | Enum/value conventions trong section 6 |
| 2.5 Exceptions | Failure cases của từng bảng |
| 2.6 Supabase client | Data access layer cho toàn bộ tables |
| 2.7 Base repository | Repository abstraction cho tables |
| 2.8 Pydantic schemas | Request/response models dựa trên field definitions |
| 2.9 UserRepository | Bảng `users` |
| 2.10 ConsentRepository | Bảng `consent_records` |
| 2.11 AuditRepository | Bảng `audit_logs` |
| 2.12 AssignmentRepository | Bảng `doctor_assignments` |
| 2.13 AuthService | `users`, `audit_logs` |
| 2.14 AuditService | `audit_logs` |
| 2.15 ConsentService | `consent_records`, `audit_logs` |
| 2.16 AssignmentService | `doctor_assignments`, `users`, `audit_logs` |
| 2.17 Security/RBAC | `users`, `doctor_assignments` |
| 2.18 API dependencies | Wiring repositories/services |
| 2.19 Auth API | `users`, `audit_logs` |
| 2.20 Consent API | `consent_records`, `audit_logs` |
| 2.21 Admin API | `users`, `doctor_assignments`, `audit_logs` |
| 2.22 Main app routers | Expose APIs that use these tables |
| 2.23 `.env.example` | Supabase/JWT/OAuth/consent config |
| 2.24 Tests | Validate constraints, RBAC, consent, audit, assignment |
| 2.25 Verify | Confirm DB/API works end-to-end |
| 2.26 Frontend auth UI | Consumes auth/consent APIs |
| 2.27 Google OAuth setup | Supports `users.auth_provider`, `provider_user_id`, `avatar_url` |

---

# 12. Implementation Notes for `docs/schema.sql`

Khi chuyển tài liệu này sang `docs/schema.sql`, ưu tiên:

1. Enable UUID extension.
2. Tạo `users` trước vì các bảng khác phụ thuộc vào `users`.
3. Tạo `doctor_assignments`, `consent_records`, `chat_sessions`.
4. Tạo `chat_messages`, `clinical_profiles`, `stress_risk_scores`.
5. Tạo `audit_logs`.
6. Thêm `CHECK` constraints cho enum string values.
7. Thêm indexes sau khi tạo bảng.
8. Ưu tiên partial unique index cho active doctor-patient assignment.
9. Chưa bật full RLS trong Milestone 2 nếu backend RBAC đang là lớp kiểm soát chính.
10. Không đưa secrets, tokens, full raw chat hoặc internal prompts vào seed/audit metadata.

Recommended creation order:

```text
users
consent_records
doctor_assignments
chat_sessions
chat_messages
clinical_profiles
stress_risk_scores
audit_logs
indexes
```

---

# 13. Open Questions / Future Decisions

Các câu hỏi chưa cần giải quyết ngay trong Milestone 2:

- Có cần `auth_user_id` để link chặt hơn với Supabase Auth internals không?
- Có cần enforce one active session per patient bằng partial unique index không?
- Có cần `clinical_profile_versions` khi clinical analyzer output thay đổi không?
- Có cần `deactivated_at` và `deactivated_by` trong `doctor_assignments` không?
- Có cần organization/multi-tenant model không?
- Có cần RLS policies ngay sau Milestone 2 hay để trước production?
- Retention policy cho `chat_messages` sẽ là bao lâu?
- Admin role có được xem raw chat không, và theo policy nào?
- Audit log retention/export policy sẽ như thế nào?
- Có cần mã hóa một số cột nhạy cảm ở application layer không?

---

# 14. Definition of Done for Database Modeling

Database modeling được coi là xong khi:

- Tất cả 8 core tables đã có purpose, fields, relationships, constraints, access rules và index strategy.
- Access rules thể hiện rõ patient/doctor/admin separation.
- Doctor assignment enforcement được mô tả rõ.
- Patient không được truy cập clinical profile.
- Consent tracking có policy version.
- Audit logging có action naming convention.
- JSONB fields có convention để tránh dữ liệu lộn xộn.
- Có mapping sang Milestone 2 implementation tasks.
- Có DBML draft để vẽ ERD.
- Sẵn sàng chuyển sang `docs/schema.sql`.
