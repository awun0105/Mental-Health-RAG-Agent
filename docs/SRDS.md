# Software Requirements and Design Specification (SRDS)

## Project: Mental Health Sovereign Agentic AI Platform

**Version:** 2.1

**Prepared by:** awun0105

**Last updated:** 26 April 2026

---

## 1. Executive Summary

The **Mental Health Sovereign Agentic AI Platform** is a privacy-first, human-in-the-loop
AI system for mental health support and clinical workflow assistance. It combines
Retrieval-Augmented Generation (RAG), multi-agent orchestration, clinical safety guardrails,
and auditable data governance to support two primary user groups:

1. **Patients**, who need a safe, empathetic, always-available conversational space.
2. **Doctors / Counselors**, who need clinically grounded summaries, risk signals, and
   decision-support tools without losing final medical authority.

The platform is designed around the principle that **AI must assist clinical decision-making,
not replace licensed professionals**. Patients must never receive direct diagnostic labels
from the AI. Instead, the system provides psychological first-aid, coping exercises, crisis
escalation, and safe conversational support. Clinical reasoning, DSM-5 cross-referencing, and
differential diagnosis support are reserved for doctors and counselors.

This SRDS applies the provided **Sovereign Agentic AI Platform** blueprint selectively. The
blueprint is used as the long-term architecture direction, while the implementation roadmap is
divided into practical phases so the project can deliver a working MVP before adopting heavier
enterprise infrastructure.

---

## 2. Product Vision and Design Intent

### 2.1 Product Vision

The long-term vision is to build a **private, self-hostable AI operating system for mental
health organizations**. The platform should allow clinics, counseling centers, hospitals, or
healthcare teams to run AI-assisted mental health workflows in their own controlled
infrastructure, such as:

- On-premise servers.
- Private cloud.
- Dedicated VPC.
- Future air-gapped deployments for highly sensitive environments.

The system should reduce dependency on external AI SaaS tools for sensitive mental health
data while preserving the flexibility to use external LLM providers only when explicitly
allowed by deployment policy.

### 2.2 Core Product Principles

1. **Privacy-first and sovereign by design**
   - Mental health conversations, patient profiles, and clinical summaries are sensitive data.
   - The architecture must support self-hosted deployment and strict data isolation.
   - External LLM usage must be configurable and auditable.

2. **Human-in-the-loop clinical safety**
   - The AI must not act as an autonomous doctor.
   - Final diagnosis and treatment decisions remain the responsibility of licensed professionals.
   - Doctor-facing outputs must be framed as decision support, not final conclusions.

3. **No direct diagnosis for patients**
   - The patient-facing AI must avoid disorder names, alarming medical jargon, and diagnostic
     claims.
   - Patient responses should focus on empathy, stabilization, coping exercises, and safe
     next steps.

4. **Grounded and evidence-based AI behavior**
   - Clinical reasoning must be grounded in curated knowledge sources.
   - Doctor-facing reports must cite retrieved DSM-5 or treatment guideline evidence.
   - If retrieved evidence is insufficient, the system must state uncertainty rather than
     hallucinate.

5. **Audit-ready operations**
   - AI prompts, retrieved context, generated summaries, risk flags, doctor access, consent
     events, and escalation events must be traceable.
   - The system should support compliance-oriented review and incident investigation.

6. **Phased implementation**
   - The MVP must be simple enough to build and validate quickly.
   - Enterprise-grade components such as Kubernetes, Keycloak, Milvus, Neo4j, vLLM, NATS,
     Dagster, and GitOps are future layers, not MVP blockers.

---

## 3. Blueprint Application Strategy

### 3.1 Blueprint Elements Applied Directly

The following parts of the Sovereign Agentic AI Platform blueprint are directly applicable to
this project and should influence the core SRDS requirements from the beginning:

| Blueprint Area | Application in This Project |
| --- | --- |
| Sovereign / privacy-first principle | The system must support self-hosted or private-cloud deployment for sensitive mental health data. |
| Multi-agent architecture | Patient support, safety guardrails, silent clinical analysis, doctor copilot, and routing should be modeled as specialized agents. |
| RAG and long-term memory | DSM-5 and treatment manuals should be indexed into a vector database; patient sessions and clinical profiles should persist in the application database. |
| Human-in-the-loop | Doctors remain responsible for final decisions; AI provides structured support only. |
| Audit-ready design | Every sensitive AI action must produce traceable logs and metadata. |
| Observability | Langfuse and later OpenTelemetry should trace prompts, retrieval, latency, cost, and safety outcomes. |
| Security and compliance | RBAC, encryption, consent tracking, data isolation, and secret management are core requirements. |
| Enterprise deployment roadmap | Kubernetes, Helm, GitOps, self-hosted models, and air-gapped deployment remain part of the long-term target architecture. |

### 3.2 Blueprint Elements Deferred from the MVP

The following blueprint components are useful but should not be mandatory for the first MVP.
They are intentionally deferred to avoid over-engineering before the clinical workflow and AI
safety model are validated.

| Deferred Component | Reason for Deferral | Future Use |
| --- | --- | --- |
| Kubernetes + Helm + ArgoCD / Flux | Too heavy for the first local MVP and early iteration. | Production and enterprise deployments. |
| Milvus | Qdrant is already aligned with the repository and is simpler for the current vector search needs. | Consider only if vector scale becomes very large. |
| Neo4j | Knowledge graph reasoning is not required for the first DSM-5 RAG workflow. | Add when entity relationships and graph reasoning become essential. |
| NATS JetStream | Event-driven architecture is not required for the first chat and ingestion flows. | Use for real-time event triggers such as document uploads, risk alerts, and patient assignment events. |
| Dagster / Meltano | Initial document ingestion can be implemented as simpler scripts or jobs. | Use for large-scale scheduled ingestion and enterprise data pipelines. |
| vLLM self-hosted inference | Requires GPU infrastructure and model operations maturity. | Add when the platform must run fully private LLM inference. |
| MCP Protocol | Valuable for agent-tool standardization but not necessary for the first internal agent workflow. | Add when tools, agents, and external systems need standardized communication. |
| SeaweedFS | Not required until the system manages large document or file volumes. | Add for scalable object storage in enterprise deployments. |
| Full air-gapped deployment | Requires mature packaging, model hosting, and update workflows. | Long-term regulated enterprise deployment model. |

---

## 4. Stakeholders and User Experiences

### 4.1 Patients

Patients need a safe, private, non-judgmental space for emotional expression and mental health
support. Their primary needs are:

- Empathetic conversation.
- Immediate psychological first-aid.
- Crisis support and escalation when necessary.
- Privacy and control over sensitive data.
- Simple emotional health trends without exposure to clinical jargon.

The patient-facing AI must behave like an empathetic support companion, not like a diagnosing
clinician.

### 4.2 Doctors and Counselors

Doctors and counselors need workflow acceleration without compromising clinical authority.
Their primary needs are:

- Structured patient summaries.
- Symptom timelines and extracted evidence snippets.
- Differential diagnosis support grounded in DSM-5.
- A conversational AI copilot that can answer questions about an assigned patient's generated
  profile, generated clinical report, evidence snippets, stress / risk score, and relevant
  clinical knowledge retrieved from the knowledge base.
- Risk flags and crisis indicators.
- Patient stress / risk score trends.
- Searchable and filterable clinical dashboard.

Doctor-facing AI outputs must clearly state that they are decision-support artifacts, not final
diagnoses.

### 4.3 Administrators

Administrators manage organizational configuration, users, doctor-patient assignments, audit
review, deployment settings, and compliance requirements.

### 4.4 Technical Stakeholders

Engineers, reviewers, and maintainers need a system that is modular, testable, observable,
secure, and capable of evolving from MVP to production-grade sovereign deployment.

---

## 5. Functional Requirements

### REQ-FUNC-001: Authentication and Role-Based Access Control

The system shall support secure authentication and role-based access control for Patients,
Doctors / Counselors, and Administrators.

**Acceptance criteria**

- Users can register and log in securely.
- User roles are represented explicitly in the application database.
- Patients are routed to the patient chat and personal health trend interface.
- Doctors are routed to the clinical dashboard and doctor copilot interface.
- Administrators can manage users, doctor assignments, and system configuration.
- Doctors can only access assigned patient records.
- All access to sensitive patient data is recorded in the audit log.

### REQ-FUNC-002: Patient Empathetic Chat

The system shall provide a private, always-available chat interface where patients can express
emotions, describe difficulties, and receive supportive responses.

**Acceptance criteria**

- The AI uses warm, non-judgmental, culturally appropriate language.
- The AI asks open-ended questions when more context is needed.
- The AI avoids direct diagnosis and disorder labels.
- The AI can suggest simple coping exercises such as breathing, grounding, journaling, and
  contacting trusted support.
- The AI response is grounded in the treatment knowledge base when clinical advice is involved.
- The conversation state is associated with a user session.

### REQ-FUNC-003: Crisis Detection and Safety Escalation

The system shall detect inputs that suggest self-harm, suicidal ideation, violence, or acute
crisis and immediately route the conversation to a safety workflow.

**Acceptance criteria**

- Crisis detection runs before normal RAG response generation.
- When crisis risk is detected, the system bypasses normal conversational flow.
- The AI provides a standardized safety response with urgent help-seeking guidance.
- The system recommends contacting local emergency services or trusted people immediately.
- The system creates a high-priority risk event for doctor / counselor review.
- The event is logged with timestamp, session ID, severity level, and generated response.
- The safety workflow does not attempt to diagnose the patient.

### REQ-FUNC-004: Session Closure and Silent Clinical Profile Generation

The system shall detect when a patient session is ending and generate a silent clinical profile
for doctor review without showing clinical conclusions to the patient.

**Acceptance criteria**

- Session closure can be triggered by a manual "End Session" action.
- Session closure can be triggered by intent detection when the patient clearly wants to end.
- Session closure can be triggered by inactivity timeout with a gentle warning.
- The generated clinical profile is not visible to the patient.
- The patient may see simplified emotional health trends, not raw clinical analysis.
- The generated profile includes symptom summary, duration indicators, risk signals, and
  supporting conversation snippets.
- The profile is forwarded to the assigned doctor when available.

### REQ-FUNC-005: Doctor Clinical Dashboard

The system shall provide doctors and counselors with a clinical dashboard for reviewing
assigned patient records and AI-generated clinical support artifacts.

**Acceptance criteria**

- Doctors can view a list of assigned patients.
- Doctors can search and filter patients by risk level, recent activity, and assignment status.
- Doctors can view clinical profiles generated from patient sessions.
- Doctors can view stress / risk score trends.
- Doctors can view evidence snippets without needing full raw chat access by default.
- Doctor access is logged for audit review.

### REQ-FUNC-006: DSM-5 Differential Diagnosis Support

The system shall generate doctor-facing differential diagnosis support grounded in the DSM-5
knowledge base.

**Acceptance criteria**

- The output clearly states that it is not a final diagnosis.
- The output lists possible conditions only as hypotheses for professional review.
- Each hypothesis includes matched DSM-5 criteria and retrieved source references.
- The system highlights missing information and uncertainty.
- The system flags red flags and urgent risk indicators.
- The system never exposes differential diagnosis content to the patient-facing interface.

### REQ-FUNC-007: Doctor Conversational Clinical Copilot

The system shall allow doctors to chat with an AI copilot about assigned patient profiles,
generated clinical reports, evidence snippets, stress / risk scores, and clinical knowledge
retrieved from the DSM-5 and treatment knowledge bases.

**Acceptance criteria**

- The doctor can ask follow-up questions about an assigned patient's generated profile or
  report, including symptoms, risk markers, extracted evidence, timeline, and stress / risk
  score interpretation.
- The doctor can ask general clinical knowledge questions against the extracted knowledge base
  without selecting a specific patient profile.
- The copilot supports two explicit modes: patient-context mode and clinical-knowledge mode.
- Patient-context answers are grounded in the selected patient profile, generated report,
  evidence snippets, and relevant DSM-5 or treatment knowledge base chunks.
- Clinical-knowledge answers are grounded only in the curated knowledge base and must not
  include patient-specific information.
- Responses cite whether the answer is based on patient profile data, generated report data,
  retrieved knowledge base chunks, or a combination of those sources.
- The system states limitations when evidence is incomplete.
- The copilot enforces doctor-patient assignment rules and cannot answer questions about
  unassigned patients.
- The copilot does not modify patient records without explicit doctor action.

### REQ-FUNC-008: Session-Based Stress / Risk Scoring

The system shall compute a session-level stress / risk score to support trend visualization and
clinical prioritization.

**Acceptance criteria**

- Scores are calculated from conversation signals, extracted symptoms, sentiment indicators,
  and risk markers.
- Scores use an internal 0-100 scale.
- Patients see simplified categories such as Low, Medium, and High.
- Doctors can see the numerical score, trend, and evidence breakdown.
- Scores are persisted for longitudinal trend analysis.
- Scoring prompts and evidence are traceable for audit and evaluation.

### REQ-FUNC-009: Knowledge Base Ingestion

The system shall support ingestion of curated mental health knowledge sources into the RAG
system.

**Acceptance criteria**

- Supported sources include DSM-5 Vietnamese materials and treatment guideline documents.
- Documents are parsed, cleaned, chunked, embedded, and stored in Qdrant.
- Each chunk includes metadata such as source, section, page, language, and intended audience.
- DSM-5 content and treatment guidance can be separated by collection or metadata policy.
- Ingestion jobs are repeatable and version-aware.

### REQ-FUNC-010: Audit Logging and Consent Tracking

The system shall maintain an audit trail for sensitive user actions, AI actions, and data access.

**Acceptance criteria**

- Audit logs record user ID, role, action type, timestamp, target resource, and relevant metadata.
- AI-generated clinical summaries are traceable to source session and retrieval context.
- Doctor access to patient profiles is logged.
- Consent acceptance is stored and versioned.
- System-mediated forwarding of clinical profiles is recorded.

### REQ-FUNC-011: Observability and LLMOps

The system shall trace AI workflows, retrieval behavior, model calls, latency, and cost.

**Acceptance criteria**

- Prompt inputs, retrieved chunks, model outputs, and agent transitions are traceable.
- Latency and cost are measured per user session and per workflow.
- Safety guardrail activations are tracked.
- Evaluation results are stored for review.
- Langfuse is used as the initial LLM observability platform.

### REQ-FUNC-012: Administrative Configuration

The system shall provide configuration mechanisms for deployment mode, LLM provider, knowledge
base settings, safety policies, and user management.

**Acceptance criteria**

- Administrators can configure allowed LLM providers.
- Administrators can manage roles and doctor-patient assignments.
- Safety policy changes are versioned.
- Sensitive values are stored through secret management, not hard-coded configuration.

---

## 6. Non-Functional Requirements

### 6.1 Privacy and Security

- Sensitive data must be encrypted in transit using TLS.
- Production deployments must encrypt sensitive data at rest.
- Access to patient data must be role-restricted and audit-logged.
- Secrets must not be stored in source code.
- The system must support self-hosted deployment for organizations that cannot send data to
  external SaaS providers.
- External LLM usage must be configurable, explicitly documented, and traceable.

### 6.2 Safety and Clinical Risk Management

- The system must prioritize crisis detection over normal response generation.
- Patient-facing responses must avoid direct diagnosis.
- Doctor-facing outputs must clearly state they are decision-support artifacts.
- The system must refuse or safely redirect non-mental-health requests.
- The system must avoid hallucinating clinical facts when retrieval evidence is weak.

### 6.3 Reliability

- The backend must handle external service failures gracefully.
- RAG retrieval failures must produce safe fallback behavior.
- Model provider failures must not expose stack traces or sensitive data to users.
- Critical risk events must be persisted reliably.

### 6.4 Performance

- Patient chat should target time-to-first-response under 3 seconds in normal MVP conditions.
- RAG retrieval should target sub-second vector search under the expected MVP corpus size.
- Doctor dashboard queries should remain responsive under the expected user volume.

### 6.5 Observability

- AI workflow traces must include prompt, model, retrieval, response, latency, token usage, and
  cost metadata where available.
- Application metrics should include request volume, error rate, latency, and safety event count.
- Future production deployments should integrate OpenTelemetry, Prometheus, and Grafana.

### 6.6 Compliance Orientation

The system is not automatically compliant by implementation alone, but it must be designed in a
way that supports compliance review for:

- GDPR-like privacy requirements.
- HIPAA-like healthcare data handling principles.
- Vietnam cybersecurity and personal data protection expectations.
- Internal clinical governance policies.

### 6.7 Maintainability

- Backend, frontend, agent logic, RAG services, and database access should remain modular.
- The system should use typed schemas for API boundaries.
- Safety policies and prompts should be versioned.
- The architecture should allow later migration from external LLM APIs to self-hosted models.

---

## 7. Technology Stack Decisions

This section defines the selected technology stack. The goal is to avoid ambiguous "or" choices
for the MVP while still preserving a future enterprise migration path.

### 7.1 Backend: FastAPI

**Decision:** Use **FastAPI** as the backend API framework.

**Rationale**

- FastAPI is Python-native and works well with AI / ML libraries.
- It provides strong typing through Pydantic schemas.
- It is suitable for REST APIs, streaming responses, internal service endpoints, and future
  WebSocket support.
- It is lightweight enough for MVP development while remaining production-capable.

### 7.2 Frontend: Streamlit

**Decision:** Use **Streamlit** as the initial frontend framework.

**Rationale**

- Streamlit enables fast iteration for AI product prototypes and dashboards.
- It is suitable for patient chat prototypes, doctor dashboards, and internal evaluation tools.
- It keeps the MVP simple before investing in a full custom frontend.
- A future production UI can migrate to React / Next.js if needed without changing the backend
  architecture.

### 7.3 Agent Orchestration: LangGraph

**Decision:** Use **LangGraph** for multi-agent orchestration.

**Rationale**

- The platform requires explicit stateful workflows rather than a single prompt chain.
- LangGraph is well suited for graph-based agent routing, conditional transitions, and
  checkpointable state.
- The mental health workflow naturally maps to agent nodes such as Safety Guardrail, Patient
  Empathetic Agent, Silent Clinical Analyzer, DSM-5 Retrieval Agent, Doctor Copilot, and Router.
- LangGraph keeps agent control flow visible and testable, which is important for clinical
  safety and auditability.

### 7.4 RAG Framework: LlamaIndex

**Decision:** Use **LlamaIndex** as the primary RAG framework.

**Rationale**

- LlamaIndex is focused on document ingestion, chunking, indexing, retrieval, query engines,
  citations, and knowledge-base workflows.
- The project needs reliable document-grounded retrieval over DSM-5 and treatment manuals.
- LlamaIndex provides a cleaner fit for RAG-centric development than using LangChain as the
  main RAG layer.
- LangGraph will handle orchestration, while LlamaIndex will handle document indexing and
  retrieval. This separation keeps responsibilities clear.

**Non-decision**

- LangChain is not selected as the MVP RAG core. It may be introduced later only for specific
  integrations or tools that LlamaIndex does not cover well.

### 7.5 Vector Database: Qdrant

**Decision:** Use **Qdrant** as the primary vector database.

**Rationale**

- Qdrant is purpose-built for vector similarity search and metadata filtering.
- It fits the repository's existing direction and dependency choices.
- It is easier to tune for semantic search over DSM-5 and treatment knowledge bases than using
  the application database as the main vector store.
- It supports separation between clinical knowledge collections, treatment guidance collections,
  and future domain-specific collections.
- It keeps vector search concerns separate from transactional application data.

**Non-decision**

- PostgreSQL + pgvector is not selected as the primary vector search layer for the MVP.
  PostgreSQL remains the system of record for application data, while Qdrant handles vector
  retrieval.

### 7.6 Application Database and Auth Layer: Self-Hosted Supabase / Postgres

**Decision:** Use **self-hosted Supabase backed by PostgreSQL** for users, roles, sessions,
clinical profiles, stress scores, consent records, and audit logs.

**Rationale**

- Supabase provides a productive application layer around PostgreSQL.
- PostgreSQL is reliable for relational data such as users, doctor assignments, sessions,
  messages, clinical profiles, and audit records.
- Supabase can support authentication, RBAC patterns, storage, and real-time capabilities if
  needed.
- Self-hosted Supabase aligns with the sovereign architecture goal because sensitive mental
  health data can remain inside the organization's infrastructure.
- This keeps transactional data separate from Qdrant's vector retrieval workload.

**Deployment note**

- For demos or non-sensitive prototypes, managed Supabase may be acceptable.
- For real patient data, the target deployment should be self-hosted Supabase in a private
  environment.

### 7.7 LLM Provider Layer: Provider Abstraction First, LiteLLM Later

**Decision:** Implement an internal LLM provider abstraction in the MVP, with a roadmap to
LiteLLM as the production LLM gateway.

**Rationale**

- Early development may use OpenAI or Gemini through configuration for speed.
- The code should not hard-code a single provider.
- A provider abstraction makes it easier to migrate to LiteLLM, self-hosted models, or hybrid
  routing later.
- LiteLLM is valuable for enterprise routing, cost tracking, fallback, retries, and policy
  control, but it is not required before core workflows are validated.

### 7.8 Observability: Langfuse First

**Decision:** Use **Langfuse** as the initial LLM observability and tracing platform.

**Rationale**

- Langfuse is designed for prompt tracing, model call monitoring, token usage, latency, cost,
  and evaluation workflows.
- It directly supports the auditability and LLMOps needs of this project.
- It is lighter to adopt in the MVP than a full OpenTelemetry + Prometheus + Grafana stack.

**Future extension**

- Add OpenTelemetry, Prometheus, and Grafana for full platform observability in production.

### 7.9 Infrastructure: Local Development First, Kubernetes Later

**Decision:** Use local / Docker Compose style development for MVP and target Kubernetes +
Helm + GitOps for production.

**Rationale**

- Kubernetes is the right long-term target for a scalable sovereign AI platform.
- It is too heavy as a first requirement while the product logic and clinical workflow are
  still being built.
- Deferring Kubernetes avoids infrastructure complexity blocking product validation.

---

## 8. High-Level System Architecture

### 8.1 MVP Logical Components

```text
Patient / Doctor UI (Streamlit)
        |
        v
FastAPI Backend
        |
        +--> LangGraph Agent Orchestrator
        |       |
        |       +--> Safety Guardrail Agent
        |       +--> Patient Empathetic Agent
        |       +--> Silent Clinical Analyzer
        |       +--> DSM-5 Retrieval Agent
        |       +--> Doctor Conversational Clinical Copilot
        |
        +--> LlamaIndex RAG Service
        |       |
        |       +--> Qdrant Vector Database
        |
        +--> Supabase / Postgres
        |       |
        |       +--> Users, Roles, Sessions
        |       +--> Clinical Profiles
        |       +--> Stress Scores
        |       +--> Consent Records
        |       +--> Audit Logs
        |
        +--> LLM Provider Abstraction
        |       |
        |       +--> OpenAI / Gemini initially
        |       +--> LiteLLM / vLLM in future
        |
        +--> Langfuse
                |
                +--> Prompt Traces, Retrieval Traces, Cost, Latency, Evaluation
```

### 8.2 Agent Architecture

| Agent / Node | Purpose | User Exposure |
| --- | --- | --- |
| Router Agent | Routes requests by user role, session state, and safety status. | Internal |
| Safety Guardrail Agent | Detects crisis, self-harm, violence, and unsafe content. | Patient and doctor workflows |
| Patient Empathetic Agent | Generates supportive patient-facing responses without diagnosis. | Patient-facing |
| Treatment RAG Agent | Retrieves coping guidance and psychological first-aid content. | Patient-facing through safe response |
| Silent Clinical Analyzer | Summarizes symptoms and risk indicators after session closure. | Doctor-facing only |
| DSM-5 Retrieval Agent | Retrieves DSM-5 criteria and evidence for clinical reasoning. | Doctor-facing only |
| Doctor Conversational Clinical Copilot | Lets doctors chat about assigned patient profiles, generated reports, and clinical knowledge base content with citations and uncertainty notes. | Doctor-facing |
| Audit / Trace Node | Records workflow metadata, prompts, retrieval, and outputs. | Internal |

### 8.3 Knowledge Base Separation

The RAG system should separate knowledge by intended use:

1. **Treatment / coping knowledge base**
   - Used for patient-facing psychological first-aid and coping exercises.
   - Responses must be gentle, non-diagnostic, and actionable.

2. **DSM-5 clinical reasoning knowledge base**
   - Used only for doctor-facing differential diagnosis support.
   - Must not be exposed directly to patients.

3. **Policy and safety knowledge base**
   - Contains crisis response policies, no-direct-diagnosis rules, escalation procedures, and
     refusal guidelines.

Separation can be implemented with different Qdrant collections or strict metadata filters.

---

## 9. Data Design

### 9.1 Core Data Entities

| Entity | Stored In | Description |
| --- | --- | --- |
| User | Supabase / Postgres | Authentication identity, profile, and role metadata. |
| Role | Supabase / Postgres | Patient, Doctor, Counselor, Admin. |
| Doctor Assignment | Supabase / Postgres | Mapping between patients and assigned doctors. |
| Chat Session | Supabase / Postgres | Session metadata, status, start time, end time. |
| Chat Message | Supabase / Postgres | Patient and AI messages with timestamps and safety metadata. |
| Clinical Profile | Supabase / Postgres | Doctor-facing AI summary generated after session closure. |
| Stress / Risk Score | Supabase / Postgres | Session-level and longitudinal scoring output. |
| Consent Record | Supabase / Postgres | Accepted terms, policy version, consent timestamp. |
| Audit Log | Supabase / Postgres | Sensitive actions, doctor access, AI workflow events. |
| Knowledge Chunk | Qdrant | Embedded DSM-5, treatment, or policy document chunk. |
| Trace | Langfuse | Prompt, model, retrieval, token, latency, and evaluation metadata. |

### 9.2 Data Isolation Rules

- Patients can access their own chat interface and simplified trend data.
- Patients cannot access clinical profiles or differential diagnosis reports.
- Doctors can access only assigned patient profiles.
- Administrators can manage assignments and configuration but should not access raw chat content
  unless explicitly authorized by policy.
- Raw chat access should be minimized; evidence snippets are preferred for doctor workflows.

---

## 10. Data Flow Design

### 10.1 Patient Chat Flow

1. Patient sends a message through the Streamlit chat UI.
2. FastAPI receives the message and loads session context.
3. LangGraph routes the message through the Safety Guardrail Agent.
4. If crisis risk is detected, the crisis workflow returns a safety response and logs an event.
5. If no crisis is detected, the Patient Empathetic Agent prepares the response plan.
6. LlamaIndex retrieves relevant treatment guidance from Qdrant.
7. The LLM generates a grounded, empathetic, non-diagnostic response.
8. The message, response, safety metadata, and trace IDs are persisted.
9. Langfuse records prompt, retrieval, latency, and model metadata.

### 10.2 Session Closure and Clinical Profile Flow

1. Session closure is triggered by user action, intent detection, or inactivity timeout.
2. The Silent Clinical Analyzer reviews the session history.
3. The analyzer extracts symptoms, duration signals, stress indicators, coping attempts, and
   risk markers.
4. The system generates a doctor-facing clinical profile with evidence snippets.
5. The profile is stored in Supabase / Postgres.
6. The assigned doctor is notified or the profile appears in the dashboard queue.
7. The patient sees only a simplified session trend update.

### 10.3 Doctor Conversational Copilot Flow

1. Doctor opens an assigned patient profile.
2. Doctor asks a question about the generated patient profile, generated clinical report,
   evidence snippets, stress / risk score, or relevant clinical knowledge.
3. The backend verifies that the doctor is authorized to access the selected patient profile.
4. LangGraph routes the request to the Doctor Conversational Clinical Copilot.
5. If the question is patient-specific, the copilot loads the generated profile, report data,
   evidence snippets, and stress / risk score before retrieval.
6. If the question is general clinical knowledge, the copilot uses only the curated knowledge
   base without loading patient-specific data.
7. LlamaIndex retrieves DSM-5 or treatment knowledge base evidence from Qdrant.
8. The LLM generates a decision-support response with citations, uncertainty notes, and source
   classification.
9. If differential diagnosis support is included, the response states that it is not a final
   diagnosis.
10. The action is audit-logged and traced in Langfuse.

### 10.4 Knowledge Ingestion Flow

1. Administrator or developer adds a curated source document.
2. The ingestion pipeline extracts text and metadata.
3. The text is cleaned and chunked.
4. Embeddings are generated.
5. Chunks are written to the appropriate Qdrant collection or metadata namespace.
6. A knowledge source version record is stored.
7. Retrieval quality is evaluated with a test set before production use.

---

## 11. Security, Privacy, and Compliance Design

### 11.1 Authentication and Authorization

- MVP uses Supabase Auth / Postgres-backed identity management.
- Roles must be enforced by backend authorization checks, not only by frontend routing.
- Doctor-patient assignment checks must happen on every protected clinical data request.

### 11.2 Consent Model

- Patients must accept terms explaining AI support, doctor review, and system-mediated clinical
  profile forwarding.
- Consent records must store policy version and timestamp.
- Changes to consent policy must create a new version.

### 11.3 Audit Logging

Audit logs must cover:

- Login and role-sensitive access.
- Doctor viewing patient profiles.
- Clinical profile generation.
- Differential diagnosis support generation.
- Crisis workflow activation.
- Consent acceptance.
- Administrative configuration changes.

### 11.4 Secret Management

- API keys, database passwords, and model credentials must never be committed to Git.
- Local development uses `.env` files excluded from version control.
- Production uses managed secret storage such as Vault or Kubernetes Secrets.

### 11.5 Data Protection

- TLS must be used for network traffic in production.
- Sensitive database fields should be encrypted at rest where supported.
- Backups must be encrypted and access-controlled.
- Data retention policies should be configurable by organization.

---

## 12. AI Safety and Evaluation Strategy

### 12.1 Safety Policies

The platform must enforce:

- No direct diagnosis in patient-facing responses.
- Crisis detection before normal generation.
- Refusal or safe redirection for unrelated requests.
- Grounded clinical advice only when supported by retrieved context.
- Clear uncertainty statements when evidence is insufficient.
- Doctor-facing outputs framed as decision support.

### 12.2 Evaluation Dimensions

The AI system should be evaluated across:

| Metric | Purpose |
| --- | --- |
| Faithfulness | Checks whether outputs are grounded in retrieved evidence. |
| Correctness | Checks factual correctness against curated references. |
| Safety | Checks crisis handling, refusal behavior, and no-direct-diagnosis compliance. |
| Hallucination Rate | Measures unsupported clinical claims. |
| Retrieval Relevance | Checks whether retrieved chunks match the query and task. |
| Latency | Measures response speed for patient and doctor workflows. |
| Cost | Tracks model usage cost per workflow and per session. |

### 12.3 Evaluation Tooling

- Use pytest and pytest-asyncio for backend and agent workflow tests.
- Use Ragas or DeepEval for RAG faithfulness and answer quality.
- Use curated red-team prompts for crisis and unsafe diagnosis testing.
- Use Langfuse datasets and traces for prompt evaluation and regression tracking.

### 12.4 Minimum Safety Test Set

The project should maintain test cases for:

- Suicidal ideation.
- Self-harm ambiguity.
- Panic attack support.
- Direct request for diagnosis from a patient.
- Doctor request for DSM-5 criteria.
- Doctor request with insufficient evidence.
- Non-mental-health request.
- Prompt injection attempt asking to reveal hidden clinical analysis.

---

## 13. Deployment Roadmap

### Phase 1: Local MVP

**Goal:** Build a working patient chat, doctor dashboard skeleton, RAG ingestion, and safety
guardrail flow.

**Stack**

- FastAPI.
- Streamlit.
- LangGraph.
- LlamaIndex.
- Qdrant.
- Self-hosted Supabase / Postgres for local or private deployment target.
- Configurable external LLM provider for development.
- Langfuse tracing.

### Phase 2: Clinical-Grade Workflow

**Goal:** Strengthen the system for realistic clinical review workflows.

**Additions**

- Strong RBAC and doctor-patient assignment enforcement.
- Silent clinical profile generation.
- DSM-5 doctor copilot.
- Stress / risk scoring.
- Audit logging.
- RAG evaluation and safety regression tests.
- Improved consent and policy versioning.

### Phase 3: Production Privacy-First Deployment

**Goal:** Prepare for controlled production use.

**Additions**

- Docker Compose or equivalent private deployment packaging.
- Hardened self-hosted Supabase / Postgres.
- Qdrant persistence and backup.
- Langfuse deployment and retention policy.
- OpenTelemetry, Prometheus, and Grafana.
- Secret management with Vault or Kubernetes Secrets.
- Encrypted backups and operational runbooks.

### Phase 4: Sovereign Enterprise Platform

**Goal:** Align with the full Sovereign Agentic AI Platform blueprint.

**Additions**

- LiteLLM gateway for provider routing, fallback, cost tracking, and policy enforcement.
- vLLM for self-hosted model inference when GPU infrastructure is available.
- Kubernetes + Helm deployment.
- GitOps with ArgoCD or Flux.
- Keycloak for enterprise OAuth2 / OIDC.
- NATS JetStream for event-driven workflows.
- Dagster / Meltano for enterprise data ingestion.
- Neo4j for knowledge graph reasoning if clinically justified.
- Milvus only if vector scale exceeds Qdrant's practical fit for the deployment.
- Air-gapped deployment option for highly regulated environments.

---

## 14. Implementation Roadmap

### Milestone 1: Foundation

- Keep uv workspace structure.
- Implement FastAPI application entrypoint.
- Implement Streamlit application entrypoint.
- Add configuration loading.
- Add health check endpoint.
- Add development environment documentation.

### Milestone 2: Data and Auth Foundation

- Set up Supabase / Postgres schema.
- Define users, roles, sessions, chat messages, doctor assignments, and audit logs.
- Implement backend authorization checks.
- Add consent record model.

### Milestone 3: RAG Foundation

- Implement document ingestion for DSM-5 and treatment documents.
- Store embeddings in Qdrant.
- Add metadata filters for patient-safe and doctor-only knowledge.
- Implement LlamaIndex retrieval service.
- Add retrieval tests.

### Milestone 4: Agent Workflow

- Implement LangGraph router.
- Implement Safety Guardrail Agent.
- Implement Patient Empathetic Agent.
- Implement Silent Clinical Analyzer.
- Implement DSM-5 Retrieval Agent.
- Implement Doctor Conversational Clinical Copilot.

### Milestone 5: UI Workflows

- Build patient chat interface.
- Build doctor patient list.
- Build clinical profile view.
- Build stress / risk trend view.
- Add admin assignment workflow.

### Milestone 6: Safety and Evaluation

- Add crisis prompt test set.
- Add no-direct-diagnosis test set.
- Add RAG faithfulness evaluation.
- Add Langfuse trace review workflow.
- Add regression checks for unsafe outputs.

### Milestone 7: Production Readiness

- Add deployment configuration.
- Add backups and restore process.
- Add monitoring and alerting.
- Add secret management.
- Add operational runbooks.
- Add privacy and compliance review checklist.

---

## 15. Out of Scope for the MVP

The following capabilities are intentionally out of scope for the first MVP:

- Fully autonomous diagnosis.
- Patient-facing disorder labeling.
- Replacement of licensed doctors or counselors.
- Insurance, billing, or electronic medical record integration.
- Full Kubernetes production deployment.
- Air-gapped packaging.
- Self-hosted GPU model inference.
- Knowledge graph reasoning with Neo4j.
- Enterprise event bus with NATS.
- Large-scale ELT orchestration with Dagster / Meltano.

---

## 16. Success Criteria

The MVP is considered successful when:

- A patient can complete a safe chat session.
- The system avoids direct diagnosis in patient-facing responses.
- The safety guardrail detects crisis-like messages and escalates appropriately.
- A session can generate a doctor-facing clinical profile.
- A doctor can view assigned patient summaries and ask DSM-5-grounded questions.
- RAG responses include traceable retrieved context.
- AI prompts, retrieval, outputs, latency, and cost are traced in Langfuse.
- Basic tests validate safety, retrieval, and role-based access behavior.

The production roadmap is considered successful when:

- Sensitive data can run in a self-hosted private environment.
- LLM providers can be routed through a policy-controlled gateway.
- Audit logs support compliance review.
- Safety and faithfulness evaluation are part of the release process.
- The system can scale toward sovereign enterprise deployment without rewriting the core
  application architecture.
