# Quy trình E2E Database Design & Development — Mental Health Sovereign Agentic AI Platform

**Phiên bản:** Project-fit draft cho Milestone 2
**Ngày cập nhật:** 03/05/2026
**Trạng thái project:** Milestone 1 đã hoàn thành; Milestone 2 — Data & Auth Foundation chuẩn bị bắt đầu
**Mục đích:** Ghi lại quy trình thiết kế, thiết lập, triển khai, tích hợp và vận hành database cho project, để sau này nhìn lại có thể hiểu rõ đã làm gì, vì sao làm như vậy, dùng công cụ gì, và quy trình thay đổi database diễn ra như thế nào.

---

## Phạm vi của tài liệu này

Tài liệu này tập trung vào **Application Database** của project, tức là phần database dùng để lưu dữ liệu nghiệp vụ và dữ liệu vận hành của nền tảng:

- người dùng;
- role;
- doctor-patient assignment;
- consent records;
- chat sessions;
- chat messages;
- clinical profiles;
- stress/risk scores;
- audit logs.

Database chính của phần này là **Supabase/PostgreSQL**.

Tài liệu này **không** đi sâu vào database vector của RAG. Phần knowledge chunks, embeddings, DSM-5 documents, treatment documents và policy/safety documents sẽ nằm ở **Qdrant** và thuộc Milestone 3. Tuy nhiên, trong giai đoạn chiến lược vẫn cần nhắc đến Qdrant để phân định rõ ranh giới giữa Application DB và Vector DB.

Tài liệu này cũng **không** tự khẳng định hệ thống đã đạt chuẩn y tế/pháp lý như HIPAA/GDPR/PDPA. Mục tiêu là thiết kế theo hướng hỗ trợ compliance review: có consent, RBAC, audit, data isolation, secret management, backup và operational traceability.

---

## Nguyên tắc nền tảng khi làm database cho project này

Project là nền tảng AI hỗ trợ sức khỏe tinh thần, nên database không chỉ là nơi lưu dữ liệu CRUD thông thường. Đây là nơi chứa dữ liệu nhạy cảm như hội thoại bệnh nhân, hồ sơ lâm sàng do AI tạo, risk score, consent, audit trail và quyền truy cập của bác sĩ. Vì vậy, mọi quyết định database phải đi theo các nguyên tắc sau:

1. **Privacy-first:** không lưu hoặc expose dữ liệu nhạy cảm nhiều hơn mức cần thiết.
2. **Role separation:** patient, doctor/counselor và admin phải có quyền truy cập khác nhau.
3. **Doctor assignment enforcement:** doctor chỉ được truy cập bệnh nhân đã được assign.
4. **Patient không thấy clinical profile:** clinical profiles, differential diagnosis support và DSM-5 clinical reasoning chỉ dành cho doctor-facing workflow.
5. **Audit-ready:** các hành động nhạy cảm như login, consent acceptance, doctor xem profile, tạo assignment, tạo clinical profile, crisis event phải được ghi audit log.
6. **Migration-first:** mọi thay đổi schema phải đi qua file SQL/migration, không sửa tay trực tiếp trên production database.
7. **Backend-enforced authorization:** backend FastAPI phải kiểm tra JWT, role và assignment trước khi trả dữ liệu; không dựa vào frontend routing.
8. **Không commit secrets:** database URL, Supabase key, JWT secret, OAuth client secret không được đưa vào Git.
9. **MVP trước, hardening sau:** Milestone 2 tập trung làm chắc Data/Auth Foundation; các phần như advanced RLS, pg_audit, PITR, Prometheus/Grafana, data retention automation sẽ được hoàn thiện dần ở các milestone sau.

---

# Giai đoạn 0: Database Strategy & Architecture

Đây là giai đoạn định hướng tổng thể trước khi đi vào modeling hoặc viết SQL. Mục tiêu là xác định rõ database cần phục vụ những workflow nào, loại dữ liệu nào sẽ nằm ở đâu, nền tảng nào được chọn, và trade-off nào được chấp nhận trong MVP.

## Bước 0.1: Phân tích yêu cầu kiến trúc CSDL theo domain của project

Trong project Mental Health Sovereign Agentic AI Platform, Application DB phải phục vụ các nhóm workflow chính sau:

- **Authentication & RBAC:** user đăng ký/đăng nhập, phân quyền patient/doctor/admin.
- **Google OAuth:** đăng nhập/đăng ký bằng Google thông qua Supabase built-in OAuth provider, nhưng backend vẫn phát hành app JWT riêng.
- **Consent tracking:** patient phải chấp nhận consent policy version hiện tại trước khi dùng nền tảng.
- **Doctor-patient assignment:** admin assign doctor cho patient; doctor chỉ được xem patient được assign.
- **Patient chat session:** lưu session và message phục vụ hội thoại patient-facing.
- **Silent clinical profile:** sau khi session kết thúc, AI tạo profile cho doctor review, không hiển thị cho patient.
- **Stress/risk scoring:** lưu score theo session/patient để dashboard hiển thị trend.
- **Audit logging:** ghi lại mọi sensitive action và các event quan trọng.

Từ các workflow này, database cần thỏa mãn các yêu cầu phi chức năng:

- dữ liệu có quan hệ rõ ràng, cần foreign keys và constraints;
- query doctor dashboard cần nhanh theo doctor/patient/risk/time;
- audit log là append-only hoặc gần append-only;
- chat messages có thể tăng nhanh nhất, cần index tốt và có kế hoạch archiving sau MVP;
- clinical data phải được phân quyền nghiêm ngặt ở backend;
- production/private deployment phải hỗ trợ backup, restore và secret management.

## Bước 0.2: Phân định ranh giới giữa các loại database/storage

Project dùng nhiều lớp lưu trữ khác nhau. Không nên dồn tất cả vào một database.

| Lớp lưu trữ | Công cụ | Dữ liệu lưu | Ghi chú |
|---|---|---|---|
| Application DB | Supabase/PostgreSQL | users, sessions, messages, clinical profiles, risk scores, consent, audit logs | Là system of record cho dữ liệu nghiệp vụ |
| Vector DB | Qdrant | DSM-5 chunks, treatment/coping chunks, policy/safety chunks | Thuộc Milestone 3, dùng cho semantic retrieval/RAG |
| LLM trace store | Langfuse | prompt traces, retrieved context, model output, latency, cost | Thuộc observability/LLMOps, không thay thế audit log |
| File/document storage | Local/Supabase Storage/future object storage | raw documents, processed docs nếu cần | MVP có thể dùng `backend/data/raw` và `backend/data/processed` |

Nguyên tắc phân tách:

- PostgreSQL lưu dữ liệu transactional và dữ liệu cần quan hệ rõ ràng.
- Qdrant chỉ lưu vectorized knowledge chunks và metadata phục vụ retrieval.
- Langfuse lưu trace của AI workflow; audit log trong PostgreSQL vẫn là nguồn chính cho compliance-oriented application audit.
- Raw documents hoặc PDF không nên nhét vào PostgreSQL nếu kích thước lớn; chỉ lưu metadata/reference nếu cần.

## Bước 0.3: Đánh giá và lựa chọn nền tảng database

Quyết định cho MVP:

- Dùng **Supabase/PostgreSQL** cho Application DB.
- Trong local development có thể dùng **Supabase CLI local stack** hoặc Supabase project riêng cho dev/demo.
- Với dữ liệu thật hoặc môi trường nhạy cảm, target phải là **self-hosted Supabase/Postgres trong private environment**.
- Managed Supabase Cloud chỉ nên dùng cho demo hoặc dữ liệu giả, không dùng cho real patient data nếu chưa có policy/compliance review.

Lý do chọn Supabase/PostgreSQL:

- PostgreSQL phù hợp với dữ liệu quan hệ như user, session, message, assignment, consent, audit.
- Supabase giúp tăng tốc development nhờ có client SDK, Auth/OAuth integration, dashboard, SQL editor và CLI.
- PostgreSQL dễ backup, dễ migrate, dễ kiểm soát constraints/indexes.
- Supabase/Postgres phù hợp định hướng sovereign/self-hostable hơn so với backend database SaaS đóng.

Công cụ dùng trong bước này:

- **SRDS.md:** source of truth cho yêu cầu sản phẩm, privacy, safety, role separation.
- **MASTER_PLAN.md:** source of truth cho thứ tự milestone.
- **MILESTONE2.md:** source of truth cho task implementation cụ thể của Data & Auth Foundation.
- **Supabase Documentation:** tham khảo Supabase Auth, database, CLI, local development.
- **PostgreSQL Documentation:** tham khảo constraints, indexes, JSONB, query planning.
- **Draw.io / Mermaid / Miro:** vẽ high-level architecture và data flow.

## Bước 0.4: Xác định trade-offs và mitigation plan

Bước này không phải là bước viết code hay tạo database ngay. Đây là bước “ngồi lại để quyết định trước”: trong MVP, ta sẽ chọn cách làm nào, cách làm đó có điểm yếu gì, và ta sẽ giảm rủi ro bằng cách nào.

Với project Mental Health Sovereign Agentic AI Platform, bước này đặc biệt quan trọng vì hệ thống xử lý dữ liệu sức khỏe tinh thần, có nhiều loại người dùng khác nhau như patient, doctor/counselor và admin, đồng thời có dữ liệu nhạy cảm như chat messages, clinical profiles, risk scores, consent records và audit logs.

Một quyết định database trong project này không chỉ cần tối ưu cho việc “làm nhanh”, mà còn phải cân bằng giữa:

- tốc độ triển khai MVP;
- privacy-first design;
- role-based access control;
- doctor-patient assignment enforcement;
- consent tracking;
- auditability;
- clinical safety;
- khả năng self-host/private deployment sau này.

**Trade-off** nghĩa là khi chọn một phương án, ta được lợi ở một mặt nhưng phải chấp nhận điểm yếu ở mặt khác.

Ví dụ: nếu chọn Streamlit cho frontend MVP, ta được lợi là làm nhanh, phù hợp prototype, nhưng phải chấp nhận rằng Streamlit không mạnh và linh hoạt như một frontend production bằng React/Next.js. Cách giảm rủi ro là giữ backend API tách biệt để sau này đổi frontend không ảnh hưởng core backend.

Với database cũng tương tự. Bước 0.4 dùng để ghi lại các quyết định kiểu này trước khi viết schema và service.

**Mitigation plan** là kế hoạch giảm rủi ro. Không phải lúc nào MVP cũng chọn được phương án hoàn hảo ngay từ đầu. Nhiều khi ta chọn phương án đủ tốt để đi nhanh, nhưng phải ghi rõ:

- rủi ro của phương án đó là gì;
- khi nào rủi ro đó có thể gây vấn đề;
- ta sẽ kiểm soát rủi ro bằng cách nào;
- sau này khi production hóa sẽ nâng cấp ra sao.

---

### Trade-off 1: Supabase Auth `auth.users` vs bảng `users` riêng của application

#### Vấn đề là gì?

Supabase có sẵn hệ thống Auth riêng. Khi dùng Supabase Auth, Supabase có bảng nội bộ tên là `auth.users`. Bảng này lưu user identity phục vụ authentication.

Tuy nhiên, project của mình không chỉ cần biết “user này đăng nhập được hay không”. Hệ thống còn cần lưu nhiều thông tin nghiệp vụ riêng của application, ví dụ:

- user này là `patient`, `doctor` hay `admin`;
- doctor nào được assign cho patient nào;
- user đã chấp nhận consent policy version nào;
- user có đang active hay đã bị deactivated;
- Google OAuth account nào tương ứng với application user nào;
- audit log cần gắn với user ID nào;
- app JWT cần chứa user ID và role nào.

Vì vậy, Milestone 2 thiết kế một bảng `users` riêng trong public schema của application database. Bảng này chứa:

- `email`;
- `password_hash` cho local email/password login;
- `full_name`;
- `role`: `patient`, `doctor`, `admin`;
- `auth_provider`: `local` hoặc `google`;
- `provider_user_id`: Google/Supabase provider user ID;
- `avatar_url`;
- `is_active`;
- `created_at`, `updated_at`.

Điều này giúp backend kiểm soát role, assignment và app JWT theo cách rõ ràng. Với Google OAuth, Supabase xử lý OAuth flow, còn application lưu provider identity vào `users.provider_user_id`.

#### Vì sao đây là trade-off?

Có hai hướng thiết kế.

##### Hướng A: Dùng hoàn toàn Supabase Auth `auth.users`

Lợi ích:

- tận dụng Supabase Auth nhiều hơn;
- OAuth/session management đi theo chuẩn Supabase hơn;
- ít phải tự quản lý identity logic.

Hạn chế:

- business role như `patient`, `doctor`, `admin` vẫn phải lưu thêm ở bảng khác;
- doctor-patient assignment vẫn cần bảng application riêng;
- consent và audit vẫn cần liên kết với application-level user;
- backend khó kiểm soát app-specific JWT theo đúng yêu cầu riêng của project;
- code có thể phụ thuộc sâu hơn vào Supabase Auth internals.

##### Hướng B: Dùng bảng `users` riêng cho application

Lợi ích:

- backend chủ động quản lý role;
- dễ gắn với `doctor_assignments`, `consent_records`, `audit_logs`;
- dễ phát hành app JWT riêng;
- dễ hỗ trợ cả local email/password login và Google OAuth;
- phù hợp hơn với kiến trúc self-hostable, backend-controlled;
- dễ enforce clinical access rule theo logic riêng của project.

Hạn chế:

- có thể bị trùng khái niệm user với Supabase Auth;
- cần mapping giữa Google/Supabase OAuth user và application user;
- nếu sau này muốn dùng Supabase Auth sâu hơn, có thể cần thêm cột mapping hoặc refactor nhẹ.

#### Quyết định cho project

Trong Milestone 2, ta chọn hướng:

> Dùng bảng `users` riêng của application làm source chính cho role, assignment, consent, audit và app JWT.

Google OAuth vẫn đi qua Supabase, nhưng sau khi OAuth thành công, backend sẽ tìm hoặc tạo user tương ứng trong bảng `users`.

Quy trình dự kiến:

1. User đăng nhập bằng Google.
2. Supabase xử lý OAuth với Google.
3. Backend nhận callback/code từ Supabase.
4. Backend lấy thông tin Google user.
5. Backend tìm user trong bảng `users` bằng `auth_provider='google'` và `provider_user_id`.
6. Nếu chưa có, backend có thể tìm theo email để link account.
7. Nếu vẫn chưa có, backend tạo user mới với role mặc định là `patient`.
8. Backend phát hành app JWT riêng.
9. Backend ghi audit log cho login event.

#### Mitigation plan

Để giảm rủi ro của quyết định này:

- Không expose Supabase service role key cho frontend.
- Backend là nơi duy nhất phát hành app JWT.
- Frontend không được tự quyết định role.
- Role luôn được lấy từ database/backend.
- Bảng `users` có `auth_provider` và `provider_user_id` để mapping Google/Supabase user.
- Nếu sau này muốn liên kết chặt hơn với Supabase Auth, có thể thêm cột `auth_user_id`.
- Không lưu role quan trọng chỉ trong Google metadata hoặc frontend session.
- Khi user login bằng Google, backend phải kiểm tra xem email đã tồn tại chưa để tránh tạo duplicate account không cần thiết.
- Nếu link local account với Google account, backend phải update `auth_provider`, `provider_user_id`, `avatar_url` một cách có kiểm soát.
- Audit log phải ghi lại login method, ví dụ `metadata={"method": "google"}`.

Nói ngắn gọn:

> Ta chấp nhận quản lý user ở application layer để có toàn quyền kiểm soát RBAC, doctor-patient assignment, consent và clinical access. Rủi ro là phải mapping OAuth cẩn thận, nên cần lưu `auth_provider`, `provider_user_id`, và về sau có thể thêm `auth_user_id`.

---

### Trade-off 2: Backend RBAC trước, database RLS hardening sau

#### Vấn đề là gì?

Có hai lớp bảo vệ quyền truy cập dữ liệu:

##### 1. Application-level authorization

Đây là lớp kiểm soát quyền trong FastAPI backend. Backend sẽ kiểm tra:

- user đã login chưa;
- JWT có hợp lệ không;
- user có đang active không;
- user là `patient`, `doctor` hay `admin`;
- doctor có được assign với patient này không;
- user đã accept consent chưa;
- action này có cần ghi audit log không.

Các thành phần liên quan trong Milestone 2:

- `get_current_user`;
- `require_role`;
- `AssignmentService.is_doctor_assigned_to_patient`;
- `ConsentService`;
- `AuditService`;
- tests cho 401/403.

##### 2. Database-level authorization / RLS

RLS là Row Level Security của PostgreSQL/Supabase. Nó cho phép viết policy ngay trong database để giới hạn từng dòng dữ liệu.

Ví dụ:

- patient chỉ được select chat session của chính mình;
- doctor chỉ được select patient đã được assign;
- admin mới được tạo doctor-patient assignment;
- user không được truy cập clinical profile nếu không có quyền.

#### Vì sao đây là trade-off?

Nếu làm RLS đầy đủ ngay từ đầu:

Lợi ích:

- database có lớp bảo vệ riêng;
- nếu backend query nhầm, database vẫn có thể chặn;
- tốt hơn cho production security;
- phù hợp nếu frontend truy cập Supabase trực tiếp bằng anon key.

Hạn chế:

- mất nhiều thời gian thiết kế policy;
- debug khó hơn trong MVP;
- policy dễ sai khi workflow còn đang thay đổi;
- nếu backend dùng service role key, RLS có thể bị bypass tùy cấu hình;
- phải test nhiều trường hợp row-level access phức tạp.

Nếu làm backend RBAC trước:

Lợi ích:

- nhanh hơn cho Milestone 2;
- dễ test bằng FastAPI/pytest;
- logic nằm ở service/dependency layer, dễ đọc;
- phù hợp với Repository pattern và Service layer trong plan;
- dễ thay đổi khi API và workflow còn đang phát triển.

Hạn chế:

- nếu một endpoint quên check role hoặc assignment, có thể gây data leak;
- database chưa tự bảo vệ mạnh ở row-level;
- chưa đủ production hardening nếu chỉ dựa vào backend checks.

#### Quyết định cho project

Trong Milestone 2, ta chọn:

> Backend-enforced RBAC trước. Database RLS sẽ được thêm dần như một hardening layer sau khi schema và API ổn định, đặc biệt trước khi production hoặc nếu frontend truy cập Supabase trực tiếp.

Tức là hiện tại FastAPI backend phải kiểm soát quyền bằng:

- `get_current_user`;
- `require_role`;
- `AssignmentService.is_doctor_assigned_to_patient`;
- `ConsentService.has_valid_consent`;
- `AuditService.log`;
- tests cho RBAC.

#### Mitigation plan

Để giảm rủi ro:

- Tất cả protected endpoints phải dùng dependency lấy current user.
- Admin endpoints phải dùng `require_role(UserRole.ADMIN)`.
- Doctor endpoints phải dùng `require_role(UserRole.DOCTOR)`.
- Patient endpoints phải đảm bảo patient chỉ query dữ liệu của chính mình.
- Clinical endpoints ở milestone sau phải check doctor-patient assignment.
- Patient không bao giờ có API để lấy `clinical_profiles`.
- Doctor chỉ được xem patient nếu có active assignment.
- Admin có thể quản lý assignment/user, nhưng không mặc định được xem raw chat nếu policy chưa cho phép.
- Viết tests cho các case `401 Unauthorized` và `403 Forbidden`.
- Viết tests để đảm bảo patient không gọi được admin/doctor endpoints.
- Viết tests để đảm bảo doctor không xem được unassigned patient.
- Audit log mọi sensitive access như doctor xem profile, tạo assignment, deactivate assignment, consent accepted.
- Nếu frontend sau này truy cập Supabase trực tiếp bằng anon key, phải bật RLS đầy đủ trước.
- Trước production, cần review DB-level permissions và thêm RLS policies cho các bảng nhạy cảm.

Nói ngắn gọn:

> Ta chưa làm RLS full ngay vì MVP cần đi nhanh và backend workflow còn đang thay đổi. Nhưng backend bắt buộc phải chặn quyền nghiêm túc bằng JWT, role, assignment check và tests. RLS sẽ là lớp hardening sau.

---

### Trade-off 3: Dùng JSONB cho clinical data linh hoạt

#### Vấn đề là gì?

Một số dữ liệu clinical/AI-generated trong project chưa chắc có cấu trúc cố định ngay từ đầu.

Ví dụ:

- `symptoms`;
- `risk_markers`;
- `evidence_snippets`;
- `metadata`;
- `evidence`;
- trace metadata;
- safety metadata.

Các field này có thể thay đổi khi ta implement thêm agent workflow ở các milestone sau, đặc biệt là:

- Safety Guardrail Agent;
- Silent Clinical Analyzer;
- DSM-5 Retrieval Agent;
- Doctor Copilot Agent;
- Stress/Risk Scoring workflow.

Ở Milestone 2, ta mới dựng Data/Auth Foundation. Agent workflow chưa ổn định, nên nếu schema clinical quá cứng ngay từ đầu, rất dễ phải migration nhiều lần.

#### Vì sao đây là trade-off?

Có hai hướng thiết kế.

##### Hướng A: Chuẩn hóa thành nhiều bảng/cột ngay

Ví dụ:

- bảng `symptoms`;
- bảng `risk_markers`;
- bảng `clinical_evidence_snippets`;
- bảng `score_evidence_items`;
- bảng `clinical_profile_versions`.

Lợi ích:

- dữ liệu có cấu trúc rõ;
- query dễ hơn;
- constraint chặt hơn;
- analytics sau này tốt hơn.

Hạn chế:

- thiết kế chậm hơn;
- dễ sai vì agent output chưa ổn định;
- mỗi lần đổi format output của AI lại phải migration;
- MVP bị nặng database design quá sớm;
- khó iterate nhanh ở giai đoạn đang tìm đúng workflow.

##### Hướng B: Dùng JSONB cho một số field linh hoạt

Ví dụ:

```sql
symptoms JSONB DEFAULT '[]',
risk_markers JSONB DEFAULT '[]',
evidence_snippets JSONB DEFAULT '[]',
metadata JSONB DEFAULT '{}',
evidence JSONB DEFAULT '{}'
```

Lợi ích:

- linh hoạt;
- phù hợp với AI-generated data giai đoạn đầu;
- dễ lưu array/object phức tạp;
- không cần migration mỗi khi format nhỏ thay đổi;
- phù hợp với MVP khi agent output còn đang evolve.

Hạn chế:

- database constraint yếu hơn;
- query phức tạp hơn nếu sau này cần analytics;
- dễ lưu dữ liệu lộn xộn nếu backend không validate;
- khó đảm bảo schema thống nhất nếu không có Pydantic model;
- JSONB có thể bị lạm dụng thành nơi nhét mọi thứ.

#### Quyết định cho project

Trong Milestone 2, ta dùng JSONB cho các field có cấu trúc còn linh hoạt:

- `chat_sessions.metadata`;
- `clinical_profiles.symptoms`;
- `clinical_profiles.risk_markers`;
- `clinical_profiles.evidence_snippets`;
- `stress_risk_scores.evidence`;
- `audit_logs.metadata`.

Các field định danh, phân quyền và query chính vẫn phải là cột rõ ràng, ví dụ:

- `users.email`;
- `users.role`;
- `doctor_assignments.doctor_id`;
- `doctor_assignments.patient_id`;
- `chat_sessions.user_id`;
- `chat_messages.session_id`;
- `clinical_profiles.patient_id`;
- `stress_risk_scores.score`;
- `audit_logs.action`;
- `audit_logs.created_at`.

Không dùng JSONB để thay thế các quan hệ chính như user, session, assignment hoặc role.

#### Mitigation plan

Để giảm rủi ro:

- Dùng Pydantic schemas ở backend để validate cấu trúc JSON trước khi ghi vào database.
- Không để mọi thứ tùy tiện nhét vào `metadata`.
- Đặt convention rõ cho từng JSONB field.
- `symptoms` nên là array các object hoặc string có format thống nhất.
- `risk_markers` nên là array có severity/source nếu cần.
- `evidence_snippets` nên chứa snippet text ngắn, source message/session reference, timestamp nếu có.
- `audit_logs.metadata` không nên chứa raw chat hoặc dữ liệu quá nhạy cảm nếu không cần.
- Khi format clinical profile ổn định, có thể chuẩn hóa thêm bảng con.
- Nếu query JSONB nhiều, có thể thêm GIN index hoặc generated columns sau.
- Không lưu doctor-facing diagnosis/differential diagnosis vào JSONB rồi vô tình expose qua patient API.
- API response models phải tách patient-facing và doctor-facing rõ ràng.

Nói ngắn gọn:

> Ta dùng JSONB vì output AI và clinical analyzer còn thay đổi trong MVP. Rủi ro là dữ liệu thiếu chuẩn và khó query. Cách giảm rủi ro là validate bằng Pydantic schemas, đặt convention rõ, và chuẩn hóa sau khi workflow ổn định.

---

### Trade-off 4: Lưu raw chat để phân tích session nhưng hạn chế hiển thị

#### Vấn đề là gì?

Hệ thống cần lưu chat messages vì nhiều lý do:

- patient cần session history;
- Safety Guardrail cần metadata để phát hiện crisis/self-harm/violence;
- Silent Clinical Analyzer cần đọc session để tạo clinical profile;
- Stress/Risk Scoring cần evidence;
- doctor-facing clinical profile cần evidence snippets;
- audit/debug/evaluation cần trace;
- future workflow có thể cần xem lại session context.

Tuy nhiên, raw chat là dữ liệu rất nhạy cảm. Trong mental health context, message của patient có thể chứa thông tin cá nhân, cảm xúc, sang chấn, rủi ro tự hại, quan hệ gia đình, sức khỏe, công việc hoặc các thông tin riêng tư khác.

Vì vậy, không thể xem raw chat như dữ liệu bình thường. Việc lưu raw chat phải đi kèm với giới hạn truy cập, audit logging, retention policy và UI policy.

#### Vì sao đây là trade-off?

Nếu không lưu raw chat:

Lợi ích:

- giảm rủi ro privacy;
- ít dữ liệu nhạy cảm trong database;
- đơn giản hơn về compliance;
- giảm hậu quả nếu database bị lộ.

Hạn chế:

- không tạo được clinical profile chất lượng;
- không có evidence snippets;
- khó audit/evaluate AI workflow;
- doctor thiếu context;
- không hiển thị được session history cho patient;
- không tính risk trend tốt;
- khó debug safety incident.

Nếu lưu raw chat:

Lợi ích:

- đủ dữ liệu cho patient chat/session history;
- đủ dữ liệu cho Silent Clinical Analyzer;
- hỗ trợ evidence snippets;
- hỗ trợ stress/risk score;
- hỗ trợ debugging và evaluation;
- hỗ trợ audit khi có incident;
- giúp hệ thống có khả năng cải thiện workflow sau này.

Hạn chế:

- database chứa dữ liệu cực kỳ nhạy cảm;
- nguy cơ leak nếu phân quyền sai;
- doctor/admin access phải được kiểm soát kỹ;
- cần retention/deletion/anonymization policy;
- backup cũng trở thành dữ liệu nhạy cảm;
- logs/debug output không được vô tình in raw message.

#### Quyết định cho project

Trong MVP, ta vẫn lưu `chat_messages`, vì nếu không lưu thì các workflow quan trọng như session closure, clinical profile generation, stress/risk scoring và evidence snippet extraction sẽ không hoạt động tốt.

Tuy nhiên:

> Raw chat không nên là dữ liệu được expose mặc định trên doctor dashboard. Doctor-facing UI nên ưu tiên `clinical_profiles`, `stress_risk_scores` và `evidence_snippets`.

Access rule:

- Patient được xem chat/session của chính mình.
- Doctor chỉ được xem dữ liệu bệnh nhân được assign.
- Patient không được xem `clinical_profiles`.
- Doctor dashboard không mặc định hiển thị toàn bộ raw chat.
- Admin quản lý user/assignment/config, nhưng không mặc định được xem raw chat nếu policy chưa cho phép.
- Nếu sau này có raw chat access cho doctor/admin, action đó phải được policy-gated và audit-logged.

#### Mitigation plan

Để giảm rủi ro:

- Patient chỉ query session/message của chính mình.
- Doctor chỉ query assigned patients.
- Patient không có API để lấy `clinical_profiles`.
- Doctor dashboard ưu tiên `evidence_snippets` và clinical profile thay vì full raw chat.
- Raw chat access, nếu có, phải có lý do nghiệp vụ rõ ràng.
- Raw chat access phải được audit log.
- Audit log không nên lưu nguyên nội dung message nhạy cảm trừ khi thật sự cần.
- Backend không được log raw message ra console/application logs một cách tùy tiện.
- Frontend không nên render raw chat ở doctor view nếu không có explicit workflow.
- Backup chứa raw chat phải được xem là sensitive data.
- Production cần encryption, backup policy, restore test và access review.
- Sau này cần có retention policy cho chat messages.
- Sau này có thể thêm anonymization/purge job.
- Evidence snippets nên trích vừa đủ để doctor hiểu context, không copy toàn bộ session nếu không cần.
- Khi có crisis event, lưu severity và metadata cần thiết, nhưng tránh phơi bày quá nhiều nội dung nhạy cảm trong audit metadata.

Nói ngắn gọn:

> Ta cần lưu raw chat để hệ thống hoạt động, nhưng không được biến raw chat thành dữ liệu ai cũng xem được. Raw chat phải được bảo vệ bằng role, assignment check, UI policy, audit log và retention policy.

---

### Tóm tắt các trade-offs trong Milestone 2

| Trade-off                                               | Quyết định cho MVP                                                                                       | Rủi ro chính                                     | Mitigation                                                                                     |
| ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| Supabase Auth `auth.users` vs application `users` table | Dùng bảng `users` riêng của application làm source chính cho role, assignment, consent, audit và app JWT | Trùng/mapping user với Supabase Auth             | Lưu `auth_provider`, `provider_user_id`; backend phát hành JWT; có thể thêm `auth_user_id` sau |
| Backend RBAC vs database RLS full                       | Backend RBAC trước, RLS hardening sau                                                                    | Route quên check quyền có thể leak data          | `get_current_user`, `require_role`, assignment check, tests 401/403, audit sensitive access    |
| JSONB vs schema chuẩn hóa                               | Dùng JSONB cho clinical/AI-generated fields còn linh hoạt                                                | Dữ liệu thiếu chuẩn, khó query analytics         | Pydantic validation, convention rõ, chuẩn hóa sau khi workflow ổn định                         |
| Lưu raw chat vs minimize sensitive data                 | Có lưu raw chat, nhưng hạn chế hiển thị và không expose mặc định cho doctor/admin                        | Dữ liệu nhạy cảm có thể bị lộ nếu phân quyền sai | Role/assignment check, evidence snippets, audit log, retention policy, no raw chat in logs     |

---

### Kết luận của Bước 0.4

Bước 0.4 giúp ta ghi lại các quyết định “chọn A thay vì B” trước khi bắt đầu viết database schema và backend service.

Nếu không có bước này, khi vào Milestone 2 sẽ dễ bị lẫn các câu hỏi nền tảng như:

- Có dùng Supabase Auth hoàn toàn không?
- App JWT do ai phát hành?
- Role lưu ở đâu?
- Doctor access check ở backend hay database?
- Có cần RLS full ngay không?
- Clinical profile dùng schema cứng hay JSONB?
- Có lưu raw chat không?
- Patient có thấy clinical profile không?
- Admin có được xem raw chat không?

Quyết định hiện tại cho MVP là:

1. Dùng application `users` table làm source chính cho role, assignment, consent, audit và app JWT.
2. Dùng backend-enforced RBAC trước, RLS hardening sau.
3. Dùng JSONB cho các field clinical/AI-generated còn linh hoạt.
4. Lưu raw chat để phục vụ workflow, nhưng hạn chế hiển thị và bảo vệ bằng role, assignment check, audit log và retention policy.

Một câu tóm gọn:

> Bước 0.4 là bước ghi lại các quyết định kiến trúc có đánh đổi trong database design, kèm lý do và cách giảm rủi ro, để MVP đi nhanh nhưng không phá vỡ định hướng privacy-first, doctor-assignment, consent, audit và clinical safety của project.

## Bước 0.5: Output cần có sau Giai đoạn 0

Sau giai đoạn này, cần có hoặc xác nhận các artifact sau:

- quyết định dùng Supabase/Postgres cho Application DB;
- quyết định Qdrant dành cho vector knowledge base, không thay thế Application DB;
- quyết định Milestone 2 dùng backend-issued JWT;
- danh sách bảng core của Milestone 2;
- quy tắc phân quyền cơ bản patient/doctor/admin;
- nguyên tắc audit và consent;
- ghi chú managed Supabase chỉ dùng cho dev/demo, self-hosted/private target cho dữ liệu thật.

---

# Giai đoạn 1: Database Modeling — Thiết kế mô hình dữ liệu

Đây là giai đoạn chưa cần deploy database thật. Mục tiêu là xác định các entity, quan hệ, constraints, access rules, index strategy và growth assumption trước khi viết SQL chính thức.

## Bước 1.1: Xác định core entities của project

Trong Milestone 2, core entities cần modeling gồm:

| Entity | Bảng dự kiến | Vai trò trong hệ thống |
|---|---|---|
| User | `users` | Lưu thông tin user, role, auth provider, active status |
| Doctor Assignment | `doctor_assignments` | Mapping doctor-patient do admin tạo |
| Consent Record | `consent_records` | Lưu consent policy version user đã chấp nhận |
| Chat Session | `chat_sessions` | Lưu metadata của một phiên chat patient-facing |
| Chat Message | `chat_messages` | Lưu message của patient/assistant/system trong session |
| Clinical Profile | `clinical_profiles` | Doctor-facing summary do AI tạo sau session closure |
| Stress/Risk Score | `stress_risk_scores` | Score 0-100 và severity theo session/patient |
| Audit Log | `audit_logs` | Lưu sensitive actions và system events |

Các entity chưa nên đưa vào Milestone 2 nếu chưa cần:

- `knowledge_sources`: có thể để Milestone 3 khi làm ingestion/RAG.
- `notifications`: có thể để Milestone 5 khi dashboard notification rõ hơn.
- `clinical_profile_versions`: có thể để sau khi profile generation workflow ổn định.
- `organization` hoặc multi-tenant tables: để production/enterprise phase nếu cần.

## Bước 1.2: Xác định field chính cho từng bảng

### `users`

Mục tiêu: lưu identity và role metadata ở application layer.

Các field chính:

- `id`: UUID primary key.
- `email`: unique, not null.
- `password_hash`: nullable vì Google OAuth users không có password local.
- `full_name`: tên hiển thị.
- `role`: `patient`, `doctor`, `admin`.
- `auth_provider`: `local` hoặc `google`.
- `provider_user_id`: ID từ Google/Supabase OAuth provider.
- `avatar_url`: ảnh đại diện từ Google nếu có.
- `is_active`: soft deactivate user.
- `created_at`, `updated_at`: timestamps.

### `doctor_assignments`

Mục tiêu: enforce doctor chỉ xem bệnh nhân được assign.

Các field chính:

- `id`: UUID primary key.
- `doctor_id`: FK đến `users.id`.
- `patient_id`: FK đến `users.id`.
- `assigned_by`: FK đến admin user trong `users.id`.
- `is_active`: soft deactivate assignment.
- `created_at`: thời điểm assign.
- unique constraint trên `(doctor_id, patient_id)` hoặc unique partial index cho active assignment tùy cách implement.

### `consent_records`

Mục tiêu: lưu version consent user đã chấp nhận.

Các field chính:

- `id`: UUID primary key.
- `user_id`: FK đến `users.id`.
- `policy_version`: ví dụ `1.0`.
- `accepted`: boolean.
- `accepted_at`: timestamp.

### `chat_sessions`

Mục tiêu: lưu một phiên chat patient-facing.

Các field chính:

- `id`: UUID primary key.
- `user_id`: FK đến patient user.
- `status`: `active`, `closed`, `timeout`.
- `started_at`, `ended_at`.
- `metadata`: JSONB cho thông tin phụ như channel, locale, closure reason, trace IDs.

### `chat_messages`

Mục tiêu: lưu message trong session.

Các field chính:

- `id`: UUID primary key.
- `session_id`: FK đến `chat_sessions.id`.
- `role`: `user`, `assistant`, `system`.
- `content`: nội dung message.
- `safety_flag`: có flag safety hay không.
- `safety_severity`: `none`, `low`, `medium`, `high`, `critical`.
- `trace_id`: link sang Langfuse trace hoặc internal workflow trace.
- `created_at`.

### `clinical_profiles`

Mục tiêu: lưu doctor-facing clinical profile do Silent Clinical Analyzer tạo sau session.

Các field chính:

- `id`: UUID primary key.
- `session_id`: FK đến `chat_sessions.id`.
- `patient_id`: FK đến `users.id`.
- `summary`: summary dành cho doctor.
- `symptoms`: JSONB array.
- `risk_markers`: JSONB array.
- `evidence_snippets`: JSONB array, ưu tiên snippet thay vì full raw chat.
- `generated_at`.

Nguyên tắc: patient không được query bảng này qua API.

### `stress_risk_scores`

Mục tiêu: lưu score và severity cho trend/dashboard.

Các field chính:

- `id`: UUID primary key.
- `session_id`: FK đến `chat_sessions.id`.
- `patient_id`: FK đến `users.id`.
- `score`: integer 0-100.
- `severity`: `low`, `medium`, `high`, `critical`.
- `evidence`: JSONB giải thích tín hiệu tính score.
- `calculated_at`.

### `audit_logs`

Mục tiêu: audit all sensitive actions.

Các field chính:

- `id`: UUID primary key.
- `user_id`: user thực hiện action, nullable cho system events.
- `role`: role tại thời điểm action.
- `action`: enum/string như `user_login`, `consent_accepted`, `doctor_viewed_profile`.
- `resource_type`: ví dụ `user`, `session`, `clinical_profile`, `assignment`.
- `resource_id`: ID của resource bị tác động.
- `metadata`: JSONB chứa context bổ sung, không nên chứa dữ liệu nhạy cảm quá mức.
- `ip_address`: optional.
- `created_at`.

## Bước 1.3: Xác định quan hệ giữa các bảng

Quan hệ cốt lõi:

- Một `user` role patient có nhiều `chat_sessions`.
- Một `chat_session` có nhiều `chat_messages`.
- Một `chat_session` có thể sinh ra một hoặc nhiều `clinical_profiles` nếu sau này cần versioning; MVP có thể là một profile/session.
- Một `chat_session` có thể có một hoặc nhiều `stress_risk_scores` nếu sau này tính lại; MVP có thể một score/session.
- Một doctor và một patient được nối qua `doctor_assignments`.
- Một user có nhiều `consent_records` theo policy version.
- Một user có nhiều `audit_logs`.

Access rules cần gắn với quan hệ:

- Patient chỉ được truy cập session/message của chính mình.
- Patient không được truy cập `clinical_profiles` hoặc doctor-facing differential diagnosis.
- Doctor chỉ được truy cập patient data nếu tồn tại active assignment trong `doctor_assignments`.
- Admin được quản lý user và assignment, nhưng không nên mặc định xem raw chat nếu policy chưa cho phép.
- Mọi truy cập doctor-facing clinical data phải ghi audit log.

## Bước 1.4: Vẽ ERD

Có thể dùng **dbdiagram.io** hoặc **Draw.io/Miro**. Với dbdiagram.io, có thể bắt đầu từ skeleton sau rồi chỉnh theo `docs/schema.sql` chính thức.

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
  score int [not null]
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

## Bước 1.5: Xác định volume & growth projection cho MVP

Giả định cho MVP local/dev:

- 10-100 users.
- 5-20 doctors/counselors.
- 50-500 patient sessions.
- 1.000-20.000 chat messages.
- 50-500 clinical profiles.
- 50-500 stress/risk score records.
- 1.000-50.000 audit logs tùy mức trace/audit.

Giả định sau khi demo/clinical pilot:

- chat messages và audit logs sẽ tăng nhanh nhất;
- dashboard queries sẽ thường filter theo doctor, patient, status, risk severity, created_at;
- clinical profile/evidence snippets có thể tăng vừa phải nhưng chứa dữ liệu nhạy cảm;
- JSONB fields cần được kiểm soát để không trở thành nơi chứa dữ liệu không có schema.

Quyết định tối ưu cho Milestone 2:

- Chưa cần partitioning.
- Bắt buộc tạo indexes cho email, role, assignment, session, profile, score, audit created_at.
- Chưa cần materialized views.
- Sau khi vượt khoảng 1-5 triệu chat messages hoặc audit logs, xem xét partition theo thời gian và archiving.

## Bước 1.6: Output cần có sau Giai đoạn 1

Sau giai đoạn modeling, cần có:

- danh sách bảng chính thức cho Milestone 2;
- ERD hoặc dbdiagram skeleton;
- danh sách field/constraints/indexes;
- danh sách access rules theo role;
- danh sách assumptions về volume/growth;
- quyết định trường nào dùng JSONB và trường nào bắt buộc chuẩn hóa.

---

# Giai đoạn 2: Database Engineering & Implementation — Khởi tạo & lập trình CSDL

Đây là giai đoạn biến mô hình dữ liệu thành database thật có thể chạy được. Với project hiện tại, giai đoạn này tương ứng trực tiếp với nhiều task trong Milestone 2.

## Bước 2.1: Cài dependencies phục vụ Supabase, JWT và password hashing

Chạy tại root repository:

```bash
uv add --package backend "supabase>=2.15.0" "python-jose[cryptography]>=3.4.0" "passlib[bcrypt]>=1.7.4"
```

Ý nghĩa:

- `supabase`: Python client để backend FastAPI kết nối Supabase/Postgres.
- `python-jose[cryptography]`: tạo và verify app JWT.
- `passlib[bcrypt]`: hash password local users bằng bcrypt.

Công cụ sử dụng:

- **uv workspace** của project.
- **VS Code terminal** hoặc terminal bất kỳ.
- **backend/pyproject.toml** để kiểm tra dependencies đã được thêm đúng.

## Bước 2.2: Cập nhật config và environment variables

Cập nhật `backend/app/core/config.py` để có các settings phục vụ database/auth:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `JWT_EXPIRATION_MINUTES`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `FRONTEND_URL`
- `BACKEND_URL`
- `CURRENT_CONSENT_POLICY_VERSION`

Tạo hoặc cập nhật `.env.example`:

```env
# LLM Provider
OPENAI_API_KEY=

# Vector Database
QDRANT_URL=http://localhost:6333

# Application Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-backend-supabase-key

# JWT Authentication
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Google OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
FRONTEND_URL=http://localhost:8501
BACKEND_URL=http://localhost:8000

# Consent
CURRENT_CONSENT_POLICY_VERSION=1.0
```

Tạo JWT secret cho local `.env`:

```bash
openssl rand -hex 32
```

Lưu ý bảo mật:

- `.env` phải nằm trong `.gitignore`.
- `SUPABASE_KEY` dùng ở backend không được đưa vào Streamlit frontend nếu đó là service role key.
- Trong production nên tách rõ `SUPABASE_ANON_KEY` và `SUPABASE_SERVICE_ROLE_KEY`; Milestone 2 có thể giữ tên `SUPABASE_KEY` để khớp plan, nhưng cần comment rõ đây là backend-only key.

## Bước 2.3: Khởi tạo database environment

Có hai cách làm tùy môi trường.

### Cách A — Local Supabase bằng Supabase CLI

Phù hợp cho development không dùng dữ liệu thật.

```bash
supabase init
supabase start
```

Sau khi start, Supabase CLI sẽ cung cấp:

- API URL;
- anon key;
- service role key;
- DB URL/connection string;
- local Studio URL.

Lưu các giá trị cần thiết vào `.env` local.

### Cách B — Supabase Cloud cho dev/demo

Phù hợp khi muốn setup nhanh để test end-to-end, nhưng chỉ dùng dữ liệu giả.

Các bước:

1. Tạo project trong Supabase Dashboard.
2. Lấy Project URL và API key.
3. Lấy Database connection string.
4. Lưu vào `.env` local.
5. Kết nối bằng DBeaver/pgAdmin để kiểm tra schema.

### Cách C — Self-hosted Supabase/Postgres cho private deployment

Đây là target đúng cho dữ liệu nhạy cảm hoặc demo nghiêm túc hơn.

Các bước tổng quan:

1. Dựng Supabase self-hosted hoặc Postgres trong private network.
2. Bật TLS cho network traffic ở môi trường production.
3. Thiết lập backup policy.
4. Cấp backend credentials theo nguyên tắc least privilege.
5. Không để database public nếu không cần.

Công cụ sử dụng:

- **Supabase CLI** cho local.
- **Supabase Dashboard** cho cloud/dev.
- **DBeaver** hoặc **pgAdmin 4** để inspect schema/query.
- **psql** để chạy SQL script.

## Bước 2.4: Kết nối công cụ quản trị database

Không nên chỉ dựa vào giao diện web khi làm database. Cần có ít nhất một công cụ quản trị chuyên dụng.

Công cụ khuyến nghị:

- **DBeaver:** dễ dùng, hỗ trợ PostgreSQL tốt, xem table/index/foreign key/query plan.
- **pgAdmin 4:** phù hợp nếu quen PostgreSQL ecosystem.
- **psql:** phù hợp khi chạy script, migration, dump/restore.
- **Supabase SQL Editor:** tiện để chạy nhanh SQL trong dashboard dev/demo.

Thông tin kết nối cần có:

- host;
- port;
- database name;
- user;
- password;
- SSL mode nếu là remote/cloud;
- connection string nếu dùng psql.

Kiểm tra kết nối:

```sql
select now();
select version();
```

## Bước 2.5: Lập trình schema SQL

Tạo file:

```text
docs/schema.sql
```

File này là reference schema cho Milestone 2. Nội dung nên được tổ chức theo thứ tự:

1. enable extension;
2. tạo bảng;
3. tạo constraints/check constraints;
4. tạo indexes;
5. tạo optional triggers như `updated_at` nếu cần;
6. comment ghi chú bảo mật nếu cần.

Các bảng bắt buộc trong Milestone 2:

- `users`
- `doctor_assignments`
- `consent_records`
- `chat_sessions`
- `chat_messages`
- `clinical_profiles`
- `stress_risk_scores`
- `audit_logs`

Chạy schema:

```bash
psql "$DATABASE_URL" -f docs/schema.sql
```

Hoặc copy nội dung vào Supabase Dashboard → SQL Editor và chạy.

Sau khi chạy, verify nhanh:

```sql
select table_name
from information_schema.tables
where table_schema = 'public'
order by table_name;
```

Kiểm tra indexes:

```sql
select indexname, tablename
from pg_indexes
where schemaname = 'public'
order by tablename, indexname;
```

## Bước 2.6: Lập trình database logic tối thiểu

Không nên đưa quá nhiều business logic vào database trong MVP, vì project còn đang thay đổi nhanh. Tuy nhiên, một số logic hạ tầng có thể nằm ở DB rất hợp lý.

Nên làm trong Milestone 2:

- UUID extension.
- `CHECK` constraints cho role/status/severity.
- FK constraints giữa các bảng.
- indexes theo query path chính.
- optional `updated_at` trigger cho `users` nếu muốn timestamp tự cập nhật.

Chưa nên làm trong Milestone 2 nếu chưa thật sự cần:

- stored procedures xử lý clinical workflow;
- trigger tự tạo clinical profile;
- trigger tự tính risk score;
- trigger ghi audit log cho mọi table mutation.

Lý do: clinical workflow thuộc agent/backend layer ở các milestone sau. Nếu đẩy sớm vào database sẽ khó test và khó thay đổi.

Ví dụ optional trigger `updated_at`:

```sql
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger trg_users_updated_at
before update on users
for each row
execute function set_updated_at();
```

## Bước 2.7: Thiết lập bảo mật database ở mức MVP

Milestone 2 cần phân biệt rõ hai lớp bảo mật:

1. **Application-level authorization:** FastAPI kiểm tra JWT, role, consent, assignment.
2. **Database-level protection:** credentials, least privilege, optional RLS, backup encryption, network restriction.

Trong MVP, yêu cầu bắt buộc:

- `.env` không commit.
- Supabase key chỉ dùng server-side.
- Backend endpoints phải dùng `get_current_user` và `require_role`.
- Doctor access phải check active assignment trước khi trả clinical data ở các milestone sau.
- Audit log phải ghi consent, login, assignment, doctor profile access, clinical profile generation, crisis workflow events.

Về RLS:

- Nếu backend dùng service role key để truy cập Supabase, RLS có thể bị bypass tùy cách cấu hình; vì vậy không được xem RLS là lớp bảo vệ duy nhất.
- Nếu frontend sau này truy cập Supabase trực tiếp bằng anon key, phải bật RLS đầy đủ trước khi release.
- Ở Milestone 2, có thể ghi RLS policy như hardening note, nhưng không để RLS thay thế backend RBAC.

## Bước 2.8: Nạp dữ liệu mẫu — database seeding

Mục tiêu của seed data là test API, RBAC và dashboard workflow bằng dữ liệu giả.

Dữ liệu mẫu nên có:

- 1 admin user.
- 1 doctor user.
- 1-2 patient users.
- 1 active doctor-patient assignment.
- 1 consent record cho patient.
- 1 chat session giả.
- vài chat messages giả không chứa dữ liệu thật.
- 1 clinical profile giả cho doctor-facing test.
- 1 stress/risk score giả.
- vài audit logs giả.

Cách seed khuyến nghị trong Milestone 2:

- Với user/password: tạo user qua API `/api/v1/auth/register` để password được hash đúng bằng backend.
- Với assignment/consent: có thể tạo qua API để test audit log cùng lúc.
- Với dữ liệu session/profile/score giả: có thể dùng `seed.sql` hoặc script Python sau khi schema đã ổn định.

Không dùng dữ liệu bệnh nhân thật trong local/dev seed.

File có thể tạo sau:

```text
docs/seed.sql
backend/scripts/seed_dev.py
```

## Bước 2.9: Tích hợp Authentication & Authorization

Milestone 2 có hai auth flow.

### Flow 1 — Email/password local login

1. User gọi `/api/v1/auth/register`.
2. Backend hash password bằng bcrypt.
3. Backend lưu user vào `users`.
4. User gọi `/api/v1/auth/login`.
5. Backend verify password hash.
6. Backend phát hành app JWT chứa `sub=user.id` và `role`.
7. Frontend lưu JWT trong Streamlit session state.
8. Các API protected đọc Authorization header `Bearer <token>`.

### Flow 2 — Google OAuth qua Supabase

1. Frontend gọi `/api/v1/auth/google`.
2. Backend gọi Supabase OAuth provider để lấy Google OAuth URL.
3. Frontend redirect user đến Google login.
4. Google/Supabase callback về backend `/api/v1/auth/google/callback`.
5. Backend exchange Supabase authorization code lấy Supabase user/session.
6. Backend tìm hoặc tạo user trong bảng `users`.
7. Backend phát hành app JWT.
8. Backend không đưa JWT trực tiếp qua URL; thay vào đó tạo one-time `auth_code` ngắn hạn.
9. Frontend nhận `auth_code`, gọi `/api/v1/auth/google/exchange` để lấy app JWT.

Lưu ý:

- Không truyền JWT qua query params vì có thể lộ qua browser history, logs hoặc Referer header.
- `_pending_tokens` in-memory chỉ phù hợp single-instance dev; production cần Redis hoặc store có TTL.
- Google OAuth setup ngoài code nằm ở Google Cloud Console và Supabase Dashboard.

## Bước 2.10: Database testing trước khi tích hợp sâu

Các nhóm test cần có:

### Schema tests

- Tạo user trùng email phải fail unique constraint.
- Role ngoài `patient/doctor/admin` phải fail check constraint.
- Session status ngoài `active/closed/timeout` phải fail.
- Score ngoài 0-100 phải fail.
- FK doctor/patient/session không tồn tại phải fail.

### Repository/service tests

- `UserRepository.get_by_email` trả đúng user.
- `ConsentRepository.has_accepted_version` hoạt động đúng.
- `AssignmentRepository.is_assigned` trả đúng active assignment.
- `AuditRepository.create` ghi đúng action/resource.

### API tests

- Register/login/me.
- Consent accept/status.
- Admin create assignment.
- Doctor xem `my-patients`.
- Patient gọi admin endpoint phải trả 403.
- Missing/malformed/expired token phải trả 401.

Công cụ:

- **pytest** và **pytest-asyncio**.
- **FastAPI TestClient**.
- **curl/Postman** cho manual verification.
- **DBeaver Query Analyzer** hoặc `EXPLAIN ANALYZE` cho query cơ bản.

---

# Giai đoạn 3: Database Integration — Tích hợp CSDL vào backend/frontend

Sau khi schema chạy được, bước tiếp theo là nối database vào codebase FastAPI và Streamlit. Đây là phần biến database từ “có bảng” thành “có workflow chạy được”.

## Bước 3.1: Tạo Supabase client trong backend

Tạo file:

```text
backend/app/db/supabase_client.py
```

Mục tiêu:

- tạo Supabase client từ `settings.supabase_url` và `settings.supabase_key`;
- validate env vars trước khi backend start;
- khởi tạo một lần trong FastAPI lifespan;
- lưu client vào `app.state.supabase`.

Công cụ:

- **supabase Python SDK**.
- **FastAPI lifespan**.
- **Pydantic Settings**.

## Bước 3.2: Tạo repository layer

Tạo package:

```text
backend/app/db/repositories/
```

Các repository Milestone 2:

- `base.py`: abstract/shared repository methods.
- `user_repo.py`: user lookup/create/update/list.
- `consent_repo.py`: consent lookup/create/version check.
- `audit_repo.py`: audit log create/list.
- `assignment_repo.py`: doctor-patient assignment create/check/list/deactivate.

Nguyên tắc:

- API route không query Supabase trực tiếp nếu có thể tránh.
- Service layer dùng repository.
- Repository trả về Pydantic response model hoặc raw dict khi cần field nội bộ như `password_hash`.
- Không để business logic như “doctor có quyền xem patient không” nằm rải rác ở nhiều route.

## Bước 3.3: Tạo Pydantic schemas

Tạo schema files:

```text
backend/app/schemas/user.py
backend/app/schemas/consent.py
backend/app/schemas/audit.py
backend/app/schemas/assignment.py
```

Vai trò:

- định nghĩa request/response shape;
- validate dữ liệu API boundary;
- tránh trả password hash ra client;
- chuẩn hóa enum role/status/action;
- giúp OpenAPI docs rõ ràng.

## Bước 3.4: Tạo service layer

Tạo services:

```text
backend/app/services/auth_service.py
backend/app/services/audit_service.py
backend/app/services/consent_service.py
backend/app/services/assignment_service.py
```

Vai trò từng service:

- `AuthService`: register, login, JWT, Google OAuth callback/exchange.
- `AuditService`: ghi audit log cho sensitive actions.
- `ConsentService`: accept/check current consent policy version.
- `AssignmentService`: create/deactivate/list doctor-patient assignments và check assignment.

Nguyên tắc:

- Service là nơi chứa business rules.
- Repository chỉ làm data access.
- API route chỉ parse input, gọi service, trả output.

## Bước 3.5: Tạo security và dependency injection layer

Tạo/cập nhật:

```text
backend/app/core/security.py
backend/app/api/dependencies.py
```

`core/security.py` nên chứa:

- `decode_access_token`;
- `require_role`;
- các helper liên quan JWT/RBAC.

`api/dependencies.py` nên chứa:

- `get_supabase`;
- `get_user_repo`, `get_audit_repo`, `get_consent_repo`, `get_assignment_repo`;
- `get_auth_service`, `get_audit_service`, `get_consent_service`, `get_assignment_service`;
- `get_current_user`.

Mục tiêu:

- mọi route protected đều dùng cùng một cách lấy current user;
- dễ mock trong tests;
- tránh circular imports;
- tránh viết lại RBAC logic nhiều nơi.

## Bước 3.6: Tạo API routers

Tạo/cập nhật routers:

```text
backend/app/api/auth.py
backend/app/api/consent.py
backend/app/api/admin.py
backend/app/main.py
```

Endpoints Milestone 2:

### Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/auth/google`
- `GET /api/v1/auth/google/callback`
- `POST /api/v1/auth/google/exchange`

### Consent

- `POST /api/v1/consent/accept`
- `GET /api/v1/consent/status`

### Admin / Assignment

- `GET /api/v1/admin/users`
- `PATCH /api/v1/admin/users/{user_id}/deactivate`
- `PATCH /api/v1/admin/users/{user_id}/activate`
- `POST /api/v1/admin/assignments`
- `DELETE /api/v1/admin/assignments/{assignment_id}`
- `GET /api/v1/admin/assignments`
- `GET /api/v1/admin/my-patients`

Lưu ý naming:

- `my-patients` đang nằm dưới `/admin` trong Milestone 2 plan, nhưng về mặt domain có thể cân nhắc sau này chuyển sang `/doctor/my-patients` để rõ hơn.
- Trong Milestone 2 nên ưu tiên khớp plan để giảm scope creep.

## Bước 3.7: Cập nhật FastAPI app entrypoint

Cập nhật:

```text
backend/app/main.py
```

Nội dung cần có:

- FastAPI lifespan khởi tạo Supabase client.
- CORS middleware.
- `AppException` handler.
- include routers: health, auth, consent, admin.
- prefix thống nhất `/api/v1`.

Sau khi cập nhật, verify:

```bash
make dev-be
```

Mở:

```text
http://localhost:8000/docs
```

Kiểm tra các router auth/consent/admin đã xuất hiện trong OpenAPI docs.

## Bước 3.8: Cập nhật frontend auth UI

Milestone 1 tạo Streamlit frontend entrypoint. Trước khi sửa cần kiểm tra file đang dùng là:

- `frontend/app.py`, hoặc
- `frontend/main.py`.

Nếu Makefile đang chạy `streamlit run frontend/app.py`, thì Milestone 2 nên cập nhật đúng file đó hoặc đổi Makefile cho thống nhất. Tránh tạo `frontend/main.py` nhưng app thật vẫn chạy `frontend/app.py`.

Frontend auth UI cần hỗ trợ:

- email/password login;
- Google OAuth login;
- nhận `auth_code` sau Google callback;
- gọi backend exchange để lấy JWT;
- lưu `access_token` vào `st.session_state`;
- logout xóa session state.

Công cụ:

- **Streamlit**.
- **requests**.
- **FastAPI backend endpoints**.

## Bước 3.9: Manual integration verification

Sau khi backend/frontend/database nối với nhau, chạy checklist thủ công.

### 1. Health check

```bash
curl http://localhost:8000/api/v1/health
```

Expected: `200 OK`.

### 2. Register patient

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"patient@example.com","password":"password123","full_name":"Test Patient","role":"patient"}'
```

Expected: `201 Created`, không trả `password_hash`.

### 3. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"patient@example.com","password":"password123"}'
```

Expected: trả `access_token` và user info.

### 4. Get current user

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <TOKEN>"
```

Expected: trả user hiện tại.

### 5. Accept consent

```bash
curl -X POST http://localhost:8000/api/v1/consent/accept \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"policy_version":"1.0"}'
```

Expected: tạo consent record và audit log.

### 6. Patient gọi admin endpoint

```bash
curl http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer <PATIENT_TOKEN>"
```

Expected: `403 Forbidden`.

### 7. Admin tạo assignment

```bash
curl -X POST http://localhost:8000/api/v1/admin/assignments \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"doctor_id":"<DOCTOR_ID>","patient_id":"<PATIENT_ID>"}'
```

Expected: tạo active assignment và audit log.

### 8. Doctor xem danh sách patient được assign

```bash
curl http://localhost:8000/api/v1/admin/my-patients \
  -H "Authorization: Bearer <DOCTOR_TOKEN>"
```

Expected: trả danh sách assignment active của doctor.

## Bước 3.10: Automated verification

Chạy backend tests:

```bash
cd backend
uv run pytest tests/ -v --tb=short
```

Chạy lint/type-check/pre-commit theo Makefile hiện có:

```bash
make check
```

Chạy frontend:

```bash
make dev-fe
```

Khi hoàn thành, commit:

```bash
git add -A
git commit -m "feat: implement Milestone 2 data and auth foundation"
```

---

# Giai đoạn 4: Database Schema Migration & Administration — Quản lý phiên bản & bảo trì

Giai đoạn này trả lời câu hỏi: khi cần thêm bảng, thêm cột, sửa constraint, thêm index hoặc nâng version database thì làm như thế nào cho an toàn và có lịch sử rõ ràng.

## Bước 4.1: Không sửa tay production database

Nguyên tắc:

- Không mở DBeaver/SQL Editor production rồi sửa schema trực tiếp nếu không có migration file.
- Không xóa cột/bảng đang được code production dùng.
- Không đổi type dữ liệu lớn mà chưa test trên local/staging.
- Không chạy script nguy hiểm nếu chưa backup.

Mọi thay đổi schema phải có:

- file migration SQL;
- review trong Git;
- test local/staging;
- kế hoạch rollback hoặc forward-fix;
- backup trước deploy nếu thay đổi lớn.

## Bước 4.2: Chuyển từ `docs/schema.sql` sang migrations

Trong Milestone 2, `docs/schema.sql` là reference schema dễ đọc. Khi schema bắt đầu thay đổi nhiều, cần dùng migration folder.

Cách làm với Supabase CLI:

```bash
supabase migration new init_milestone2_schema
```

Lệnh này tạo file dạng:

```text
supabase/migrations/<timestamp>_init_milestone2_schema.sql
```

Sau đó copy nội dung schema đã ổn định từ:

```text
docs/schema.sql
```

vào migration file.

Test local:

```bash
supabase db reset
```

Apply lên remote/staging khi đã review:

```bash
supabase db push
```

Lưu ý:

- `docs/schema.sql` có thể tiếp tục giữ như tài liệu reference.
- `supabase/migrations/` là nguồn chính cho lịch sử thay đổi schema.
- Git/GitHub là nơi lưu version history.

## Bước 4.3: Quy trình tạo migration mới

Ví dụ muốn thêm cột `last_login_at` vào `users`.

Tạo migration:

```bash
supabase migration new add_last_login_at_to_users
```

Viết SQL:

```sql
alter table users
add column last_login_at timestamptz;

create index idx_users_last_login_at on users(last_login_at);
```

Test local:

```bash
supabase db reset
uv run pytest tests/ -v --tb=short
```

Nếu pass, commit:

```bash
git add supabase/migrations docs/schema.sql backend tests
 git commit -m "feat(db): add last_login_at to users"
```

## Bước 4.4: Safe schema change pattern

Khi hệ thống đã có dữ liệu hoặc có người dùng, thay đổi schema nên đi theo pattern an toàn.

### Thêm field mới

1. Add nullable column.
2. Deploy code có thể đọc/ghi field mới nhưng không bắt buộc.
3. Backfill dữ liệu nếu cần.
4. Add NOT NULL/default/constraint ở migration sau.

### Đổi tên field

1. Add field mới.
2. Code ghi cả field cũ và field mới trong một thời gian.
3. Backfill.
4. Code đọc field mới.
5. Xóa field cũ sau khi chắc chắn không còn dùng.

### Xóa field/bảng

1. Kiểm tra code không còn đọc/ghi field/bảng đó.
2. Backup.
3. Deploy migration xóa trên staging.
4. Quan sát logs/tests.
5. Deploy production.

### Thêm index

1. Xác định query chậm bằng `EXPLAIN ANALYZE` hoặc dashboard.
2. Tạo index phù hợp.
3. Với bảng lớn, cân nhắc `CREATE INDEX CONCURRENTLY` trong production.
4. Verify query plan sau khi tạo index.

## Bước 4.5: Performance tuning & views

Các query có khả năng quan trọng trong project:

- tìm user theo email khi login;
- list users theo role;
- check doctor-patient active assignment;
- list sessions theo patient;
- list messages theo session;
- list clinical profiles theo patient;
- list risk scores theo patient/time;
- list audit logs theo user/action/time.

Indexes cần có ngay từ Milestone 2:

- `idx_users_email`
- `idx_users_role`
- `idx_users_provider`
- `idx_doctor_assignments_doctor`
- `idx_doctor_assignments_patient`
- `idx_chat_sessions_user`
- `idx_chat_sessions_status`
- `idx_chat_messages_session`
- `idx_clinical_profiles_patient`
- `idx_stress_scores_patient`
- `idx_audit_logs_user`
- `idx_audit_logs_action`
- `idx_audit_logs_created`
- `idx_consent_records_user`

Views có thể cân nhắc sau Milestone 2:

- `doctor_patient_overview`: join assignment + patient + latest score + latest profile timestamp.
- `patient_risk_trend`: patient scores theo thời gian.
- `audit_sensitive_access`: filter audit actions liên quan doctor/profile/clinical access.

Materialized views chỉ nên dùng khi dashboard query chậm và dữ liệu đủ lớn.

Công cụ:

```sql
explain analyze
select ...;
```

Ngoài ra có thể dùng:

- DBeaver query plan;
- Supabase Query Insights;
- `pg_stat_statements` nếu được bật.

## Bước 4.6: Backup & Disaster Recovery Strategy

Vì dữ liệu mental health rất nhạy cảm, backup không chỉ là chuyện “có file dump”. Backup phải được mã hóa, kiểm soát truy cập và test restore.

MVP/local:

```bash
supabase db dump --file backup_local.sql
```

Hoặc dùng PostgreSQL trực tiếp:

```bash
pg_dump "$DATABASE_URL" > backup.sql
```

Staging/production:

- backup tự động hằng ngày;
- Point-in-Time Recovery nếu dùng managed/self-hosted setup hỗ trợ;
- mã hóa backup at-rest;
- giới hạn người được download backup;
- restore test định kỳ trên staging;
- ghi lại runbook restore.

Restore test tối thiểu:

1. Tạo database staging trống.
2. Restore backup gần nhất.
3. Chạy migration mới nhất nếu cần.
4. Chạy smoke tests.
5. Kiểm tra sample queries: users, assignments, consent, audit.

## Bước 4.7: CI/CD cho database

Khi dự án có migration folder, nên thêm GitHub Actions hoặc CI tương đương.

Workflow đề xuất:

1. Pull request tạo/sửa migration.
2. CI start local Supabase/Postgres.
3. CI apply migrations từ đầu.
4. CI chạy backend tests.
5. CI chạy lint/type-check.
6. Reviewer kiểm tra SQL migration.
7. Merge vào main.
8. Deploy migration lên staging.
9. Sau khi staging pass, deploy production.

Công cụ:

- **GitHub Actions**.
- **Supabase CLI**.
- **pytest**.
- **Ruff/Mypy/pre-commit**.

## Bước 4.8: Monitoring, alerting & cost optimization

Cần theo dõi:

- database connection usage;
- slow queries;
- error rates;
- storage growth;
- chat message growth;
- audit log growth;
- backup status;
- failed login spikes;
- unusually high doctor profile access;
- failed authorization attempts.

Công cụ MVP/dev:

- Supabase Dashboard logs.
- PostgreSQL logs.
- DBeaver query plan.

Công cụ production/future:

- `pg_stat_statements`.
- Prometheus + Grafana.
- OpenTelemetry.
- Alert qua email/Slack.

Cost optimization:

- index đúng query path;
- archive old chat/audit records theo retention policy;
- không lưu duplicate raw content không cần thiết;
- không query full raw chat cho dashboard nếu chỉ cần snippets/summary;
- dùng pagination cho audit logs/messages.

## Bước 4.9: Data retention và deletion policy

Project cần hỗ trợ compliance-oriented privacy, nên về lâu dài phải có retention policy.

Milestone 2 chỉ cần thiết kế để không khóa đường phát triển:

- dùng `is_active` để deactivate user thay vì hard delete ngay;
- audit logs không nên bị xóa tùy tiện;
- raw chat retention nên cấu hình theo organization policy;
- khi có yêu cầu xóa dữ liệu, cần phân biệt:
  - xóa/anonymize dữ liệu patient;
  - giữ audit event ở dạng tối thiểu nếu policy yêu cầu;
  - không phá vỡ foreign keys.

Pattern tương lai:

- soft delete cho user/session nếu cần;
- scheduled purge job;
- anonymization job;
- retention metadata per organization.

---

# Security & Compliance Checklist cho project này

| Yếu tố | Việc cần làm trong project | Công cụ / Cách thực hiện | Giai đoạn |
|---|---|---|---|
| Secrets management | Không commit `.env`, JWT secret, Supabase key, OAuth secret | `.gitignore`, `.env.example`, Vault/K8s Secrets sau này | M2, M7 |
| Authentication | Email/password + Google OAuth, backend-issued JWT | FastAPI, Supabase OAuth, python-jose, passlib/bcrypt | M2 |
| Role-based access | Patient/doctor/admin được enforce ở backend | `require_role`, `get_current_user`, API dependencies | M2 |
| Doctor assignment | Doctor chỉ xem patient được assign | `doctor_assignments`, `AssignmentService` | M2, M5 |
| Consent tracking | Lưu policy version và timestamp | `consent_records`, `ConsentService` | M2 |
| Audit logging | Ghi login, consent, assignment, profile access, clinical generation, crisis events | `audit_logs`, `AuditService` | M2-M6 |
| Patient/doctor data separation | Patient không thấy clinical profile/differential diagnosis | API authorization, route separation, frontend routing | M2-M5 |
| Raw chat minimization | Doctor dashboard ưu tiên evidence snippets | `clinical_profiles.evidence_snippets`, UI policy | M4-M5 |
| Data encryption | TLS in transit, encryption at rest nếu production | Supabase/Postgres config, infra config | M7 |
| RLS hardening | Bật RLS nếu frontend dùng Supabase trực tiếp hoặc production cần DB-level guard | Supabase RLS policies | M7 hoặc hardening sau M2 |
| Backup | Backup mã hóa, restore test | `pg_dump`, Supabase backup/PITR | M7 |
| Vulnerability management | Kiểm tra SQL injection, permission leak, schema exposure | pytest, code review, Supabase Security Advisor | M2-M7 |
| Clinical safety data boundary | Không lưu/expose doctor-facing diagnosis cho patient | schema + API + frontend separation | M4-M6 |
| Traceability | Link DB events với Langfuse trace IDs khi có AI workflow | `trace_id`, Langfuse | M4-M6 |

---

# Mapping quy trình này với Milestone 2

| Nhóm việc trong quy trình | Milestone 2 task liên quan |
|---|---|
| Dependencies Supabase/JWT/password hashing | 2.1 |
| Config/env variables | 2.2, 2.23 |
| Database schema | 2.3 |
| Enums/constants | 2.4 |
| Exceptions | 2.5 |
| Supabase client | 2.6 |
| Repository pattern | 2.7, 2.9, 2.10, 2.11, 2.12 |
| Pydantic schemas | 2.8 |
| Auth service | 2.13 |
| Audit service | 2.14 |
| Consent service | 2.15 |
| Assignment service | 2.16 |
| JWT/RBAC/security | 2.17, 2.18 |
| Auth/consent/admin routers | 2.19, 2.20, 2.21 |
| FastAPI app wiring | 2.22 |
| Tests | 2.24, 2.25 |
| Streamlit auth UI | 2.26 |
| Google OAuth external setup | 2.27 |

---

# Checklist artifact sau khi hoàn thành Milestone 2 database/auth setup

Sau khi hoàn thành Milestone 2, repo nên có ít nhất các artifact sau:

```text
docs/schema.sql
.env.example
backend/app/core/config.py
backend/app/core/constants.py
backend/app/core/exceptions.py
backend/app/core/security.py
backend/app/db/supabase_client.py
backend/app/db/repositories/base.py
backend/app/db/repositories/user_repo.py
backend/app/db/repositories/consent_repo.py
backend/app/db/repositories/audit_repo.py
backend/app/db/repositories/assignment_repo.py
backend/app/schemas/user.py
backend/app/schemas/consent.py
backend/app/schemas/audit.py
backend/app/schemas/assignment.py
backend/app/services/auth_service.py
backend/app/services/audit_service.py
backend/app/services/consent_service.py
backend/app/services/assignment_service.py
backend/app/api/dependencies.py
backend/app/api/auth.py
backend/app/api/consent.py
backend/app/api/admin.py
backend/app/main.py
backend/tests/test_auth.py
backend/tests/test_rbac.py
backend/tests/test_consent.py
backend/tests/test_audit.py
backend/tests/test_assignment.py
frontend/app.py hoặc frontend/main.py
```

Optional nhưng nên có sau khi schema ổn định:

```text
docs/ERD.md
supabase/migrations/<timestamp>_init_milestone2_schema.sql
docs/seed.sql hoặc backend/scripts/seed_dev.py
docs/database_runbook.md
```

---

# Từ điển thuật ngữ project-specific

| Thuật ngữ | Ý nghĩa trong project |
|---|---|
| Application DB | Supabase/Postgres, lưu dữ liệu nghiệp vụ như users, sessions, consent, audit |
| Vector DB | Qdrant, lưu embeddings/chunks cho RAG |
| Supabase | Application layer quanh PostgreSQL, hỗ trợ Auth/OAuth, dashboard, CLI |
| PostgreSQL | Relational database chính của Application DB |
| RLS | Row Level Security, chính sách bảo vệ dữ liệu ở database level |
| RBAC | Role-Based Access Control, phân quyền theo patient/doctor/admin |
| JWT | Token do backend phát hành sau login để gọi API protected |
| Google OAuth | Đăng nhập bằng Google thông qua Supabase provider, sau đó backend phát hành app JWT |
| Consent Record | Bản ghi user đã chấp nhận policy version nào, lúc nào |
| Audit Log | Bản ghi sensitive action/system event phục vụ review và incident investigation |
| Doctor Assignment | Mapping doctor-patient dùng để enforce quyền truy cập clinical data |
| Clinical Profile | Doctor-facing summary do AI tạo sau session, không hiển thị cho patient |
| Evidence Snippet | Đoạn evidence trích từ session/knowledge source, ưu tiên hơn raw chat trong doctor UI |
| Stress/Risk Score | Điểm 0-100 và severity hỗ trợ dashboard/trend/risk prioritization |
| JSONB | Kiểu dữ liệu PostgreSQL lưu JSON có thể query/index, dùng cho metadata/evidence/symptoms |
| Migration | File SQL versioned dùng để thay đổi schema an toàn |
| Seed | Dữ liệu giả dùng để test local/dev |
| Service role key | Supabase key có quyền cao, chỉ dùng ở backend/server-side |
| Anon key | Supabase key public hơn, chỉ dùng với RLS phù hợp nếu frontend truy cập trực tiếp |
| PITR | Point-in-Time Recovery, khôi phục database về một thời điểm cụ thể |

---

# Quy trình thực thi đề xuất ngay trước khi bắt đầu Milestone 2

1. Đọc lại SRDS Section về Data Design, Security, Consent, Audit và Implementation Roadmap.
2. Mở `MILESTONE2.md` và giữ progress tracker làm checklist chính.
3. Tạo hoặc xác nhận Supabase local/cloud dev project.
4. Cập nhật `.env.example` và `.env` local.
5. Làm task 2.1-2.3 trước: dependencies, config, schema.
6. Verify schema chạy được bằng psql/Supabase SQL Editor.
7. Tạo constants/exceptions/repositories/schemas/services theo thứ tự Milestone 2.
8. Tạo API routers và wire vào `main.py`.
9. Test manual bằng curl trước.
10. Viết/hoàn thiện pytest cho auth, RBAC, consent, audit, assignment.
11. Cập nhật frontend auth UI.
12. Setup Google OAuth ở Google Cloud Console và Supabase Dashboard.
13. Chạy `make check`, `make dev-be`, `make dev-fe`, `pytest`.
14. Commit toàn bộ thay đổi với message rõ ràng.
