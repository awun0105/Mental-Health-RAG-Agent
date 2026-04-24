# Software Requirements and Design Specification (SRDS)

## Project: Mental Health AI Platform

   Version: 2.0

   Prepared by: awun0105

   Date: 24/4/2026

   ---

## 1. System Overview

### 1.1 Product Perspective & Context

The **Mental Health AI Platform** is an advanced AI-integrated web application specifically designed to optimize clinical workflows in mental health centers and clinics. The system serves as an intelligent bridge connecting two primary user groups: **Patients** and **Medical Professionals / Counselors**, while strictly adhering to the **Human-in-the-loop** principle to ensure the highest level of medical safety.

The platform leverages the power of Retrieval-Augmented Generation (RAG) to accurately retrieve and apply domain-specific knowledge from two core knowledge bases:
1. **The official DSM-5 manual in Vietnamese (Hướng dẫn chẩn đoán rối loạn tâm thần**: Used strictly for internal reasoning and clinical diagnostics.
2. **"Diagnosis and Treatment of Common Mental Disorders" manual (CHẨN ĐOÁN VÀ ĐIỀU TRỊ MỘT SỐ RỐI LOẠN TÂM THẦN THƯỜNG GẶP)**: Used for providing safe, practical psychological first-aid and coping strategies.

This dual-source approach ensures all responses and analyses are grounded in clinically validated, localized medical standards while maintaining conversational safety.

### 1.2 User Experiences

#### 1.2.1 Patient Experience (Safe & Empathetic 24/7 Conversational Space)

For patients, the platform provides a private, secure, and always-available 24/7 conversational environment.

- **Empathetic Listener**: The AI acts as a thoughtful companion, using open-ended questions to help patients comfortably share their emotions and challenges.
- **Immediate Psychological First Aid**: Drawing from the dedicated treatment knowledge base and LLM intrinsic safety guidelines, the AI delivers soothing advice and simple, immediately applicable psychological coping exercises (e.g., breathing techniques, grounding exercises).
- **Medical Safety Protection**: To prevent panic or the nocebo effect, the AI **never directly diagnoses or names any disorder** during the conversation.
- **Automated Dual-Trigger Session Closure**: The system intelligently detects the end of a session through an Intent-based trigger (e.g., the user saying goodbye) or a Time-based timeout. Once triggered, the AI silently synthesizes the symptoms and forwards the clinical profile to the doctor.
- **Transparency for Users**: Instead of overwhelming clinical summaries, patients can view their session-based "Stress/Health Score" trends to track their emotional well-being over time.

#### 1.2.2 Experience for Medical Professionals / Counselors (Professional Clinical Dashboard)

For doctors and counselors, the system automatically transforms into a highly professional **Clinical Dashboard**.

- **Intelligent Patient Profiles**: Doctors can immediately review complete patient profiles alongside AI-synthesized analyses and symptom summaries derived from the conversation history.
- **Differential Diagnosis Reports**: The AI evaluates patient symptoms against the DSM-5 vector database and generates a structured Differential Diagnosis Report, highlighting potential disorders and critical red flags.
- **Intelligent Academic Copilot**: The AI goes beyond simple summarization to serve as a powerful academic assistant. Doctors can directly ask questions and cross-reference diagnostic criteria from the DSM-5 manual with the specific details of each patient’s profile.
- **Optimized Clinical Decision-Making**: This enables doctors to save maximum time on profile analysis and reach the most accurate final treatment decisions, grounded in solid data and their own professional judgment.

### 1.3 Stakeholder Concerns

The Mental Health AI Platform is designed to address the distinct needs, expectations, and potential risks perceived by its key stakeholders. These concerns directly influence the functional and non-functional requirements of the system. The stakeholders are grouped into three primary categories:

#### 1.3.1 Patients (Primary End Users)

Patients require a safe, non-judgmental, and always-accessible space to express emotional distress. Their main concerns include:

- **Data Privacy and Confidentiality**: Mental health information is highly sensitive; any perceived breach could deter usage or cause irreversible psychological harm.
- **Empathy and Natural Interaction**: The AI must maintain a consistently warm, supportive tone without sounding mechanical or clinical, as patients may be in vulnerable emotional states.
- **Psychological Safety**: Avoidance of direct diagnostic statements or alarming medical jargon during conversation to prevent nocebo effects or increased anxiety.
- **Transparency and Control**: Users want the option to review their emotional health trends over time without being overwhelmed by medical jargon.
- **Accessibility**: 24/7 availability with low technical barriers, especially for users experiencing acute distress.

#### 1.3.2 Medical Professionals and Counselors

Doctors and counselors need reliable, time-saving tools that augment rather than replace their clinical judgment. Their primary concerns are:

- **Accuracy and Reliability of AI Outputs**: Preliminary symptom summaries and differential diagnoses must be faithful to the DSM-5 Vietnamese manual and the patient’s actual conversation history.
- **Efficiency in Workflow**: The Clinical Dashboard must reduce time spent on manual note review and allow quick cross-referencing of diagnostic criteria with patient-specific data.
- **Human-in-the-Loop Control**: The system must never present AI conclusions as final diagnoses; all treatment decisions remain the sole responsibility of the licensed professional.
- **Usability and Integration**: The interface must be intuitive for busy clinicians who may not have deep technical expertise.
- Automatic forwarding of the clinical profile to the assigned doctor is treated as system-mediated implicit consent, which patients agree to via the Terms of Service upon registration.
#### 1.3.3 Technical Stakeholders (Recruiters, Engineers, and Evaluators)

Technical audiences evaluate the solution’s robustness, maintainability, and production readiness. Their key concerns include:

- **Architectural Quality and Scalability**: Clear separation of concerns (FastAPI backend, structured agent workflows via LangGraph, and observability through Langfuse).
- **LLMOps and Cost Management**: Transparent tracking of token usage, latency, and operational costs in real time.
- **Reliability and Safety Guardrails**: Demonstrated use of RAG, multi-agent orchestration, and strict evaluation pipelines (e.g., achieving a Faithfulness score > 0.75 via Ragas/DeepEval) to minimize hallucination and ensure regulatory alignment.
- **Development Efficiency**: Ability to deliver a fully functional, production-grade system within a constrained 1-week sprint.

---

## 2. System Requirements

This section specifies the verifiable functional and non-functional requirements of the Mental Health AI Platform.

### 2.1 Non-Functional Requirements (QoS)

**Performance & Scalability**
- API response time (Time-to-First-Token) for chat interactions shall not exceed 3 seconds under normal load.
- The system shall support concurrent usage by at least 200 active users (patients and doctors) with graceful degradation.
- The RAG retrieval pipeline shall maintain sub-second latency even when the vector knowledge bases grow significantly.

**Security & Data Privacy (Healthcare Compliance)**
- All sensitive mental health data (chat history, clinical profiles, health scores) must be encrypted both at rest and in transit (TLS 1.3+).
- User authentication and session management shall follow secure practices (JWT with short expiry, refresh tokens, and secure HTTP-only cookies).
- The platform shall enforce strict data isolation between patients and doctors; doctors can only access patient data after system-mediated forwarding.
- Compliance with personal data protection regulations and healthcare data handling best practices.

**Reliability, Fault Tolerance & AI Evaluation**
- The system shall implement graceful error handling and retry mechanisms for external services (OpenAI API, vector database).
- **Automated AI Evaluation:** Before any production deployment, the RAG pipelines must pass automated testing using Ragas/DeepEval, achieving a Correctness Score of > 4.0/5 and a Faithfulness Score of > 0.75 to ensure strict adherence to medical texts.

**Observability & LLMOps**
- All LLM calls, RAG retrievals, and agent workflows shall be fully traced and logged using Langfuse (or equivalent observability platform).
- Token usage, latency, cost per session, and trace transitions shall be monitored in real-time with alerting thresholds.

**Usability & Accessibility**
- The patient interface shall be intuitive, empathetic in tone, and accessible on both desktop and mobile devices (web).
- The doctor dashboard shall provide a professional, efficient workspace optimized for clinical decision-making.
- The entire application shall support Vietnamese as the primary language with clear, natural,culturally appropriate communication.

---

### 2.2 Functional Requirements

**REQ-FUNC-001**
**Feature:** User Authentication & Role-Based Access Control (RBAC)
**Statement:** The system shall support secure registration, login, and RBAC to differentiate between Patient and Medical Professional roles, routing them to entirely different UI experiences and AI workflows.
**Acceptance Criteria:**
- Support for “assigned doctor” mechanism: Each patient record includes an `assigned_doctor_id` field (nullable). Doctors or admins can manually assign patients via the Clinical Dashboard.
- Doctor dashboard displays a Patient List containing only those patients explicitly assigned to them.
- Patient registration and session routing are automatically determined by role-based access control (RBAC) using JWT claims.
- Patients can only access the chat interface and session-based mental health/stress tracking in the personal profile.
- Doctors can access the Clinical Workspace, patient lists, and AI-generated diagnostic reports for each patient profiles on the list.
- Session management shall automatically route users to the correct interface based on role.
**REQ-FUNC-002**
**Feature:** Empathetic 24/7 Patient Chat Interface
**Statement:** The system shall provide a private, secure conversational interface where patients can chat 24/7 with an AI Agent acting as an empathetic listener.
**Acceptance Criteria:**
- The AI shall use open-ended questions and maintain a warm, supportive tone.
- The interface shall maintain conversation memory across current session boundaries.

**REQ-FUNC-003**
**Feature:** Dual-Trigger Session Closure & Silent Profile Generation
**Statement:** The system shall intelligently detect the end of a session via a Dual-Trigger mechanism (Intent-based, Time-based timeout, and Manual button) to silently synthesize symptoms and generate a clinical profile without displaying any diagnosis or raw summary to the patient.
**Acceptance Criteria:**
- Dual-Trigger includes: (1) Intent-based detection using a predefined keyword list combined with a lightweight LLM intent classifier (gpt-4o-mini, temperature=0.0), (2) Time-based timeout after 60 minutes of inactivity (with a gentle 5-minute warning), (3) Manual “End Session” button always visible in the patient chat interface.
- Once triggered, the system silently generates a clinical profile using the Treatment knowledge base and forwards it automatically to the assigned doctor.
- Patients shall NOT view the clinical profile, raw chat summary, or differential diagnosis (only Stress/Health Score trends are visible).
- Edge case handling: If the user indicates intent to end but continues chatting, the session shall not be closed immediately.

**REQ-FUNC-004**
**Feature:** Psychological First Aid & Coping Exercises
**Statement:** The system shall provide immediate soothing advice and simple psychological coping exercises during patient conversations.
**Acceptance Criteria:**
- Advice and exercises must be retrieved from the "Diagnosis and Treatment of Common Mental Disorders" manual or strict LLM intrinsic safety guidelines.
- Responses shall never include direct diagnostic statements or medical jargon.

**REQ-FUNC-005**
**Feature:** Professional Clinical Workspace for Doctors
**Statement:** The system shall provide doctors with a Clinical Dashboard displaying patient profiles,session-based mental health/stress tracking of patient inside the patient profile, AI-synthesized symptom summaries and Differential Diagnosis Reports, including specific snippet quotes from the patient's conversation as verifiable evidence, without exposing the entire raw chat log.
**Acceptance Criteria:**
- Doctors can review AI-synthesized patient summaries alongside auto-extracted entities (symptoms, durations) and verifiable chat snippets.
- Doctors CANNOT access the full, raw chat history of the patient.
- Dashboard shall support search, filtering, and patient assignment.

**REQ-FUNC-006**
**Feature:** Differential Diagnosis Generation & Academic Copilot
**Statement:** The system shall cross-reference patient symptoms against the DSM-5 knowledge base to generate a Differential Diagnosis Report for the doctor.
**Acceptance Criteria:**
- The AI shall highlight matched criteria, cite specific DSM-5 sections, and flag critical risks (Red Flags).
- All responses must explicitly state they are clinical support tools, not final diagnoses.

**REQ-FUNC-007**
**Feature:** Session-Based Stress Scoring
**Statement:** The system shall calculate a hidden “Stress/Risk Score” for each patient session to enable emotional health trend tracking over time.
**Acceptance Criteria:**
- The score is computed using a silent LLM-as-Judge (gpt-4o-mini, temperature=0.0) grounded exclusively in the Treatment knowledge base and conversation history.
- Scoring factors include: number and severity of symptoms, sentiment analysis, frequency of negative emotions, and engagement with coping exercises.
- Internal scale: 0-100. Patients see only simplified categories (Low / Medium / High) plus a trend graph (7-day and 30-day). Doctors see the full 0-100 score with detailed breakdown and verifiable chat evidence snippets.
- Scores are updated in real-time during sessions and persisted in Supabase for historical trend visualization in both patient and doctor dashboards.

**REQ-FUNC-008**
**Feature:** AI Safety & Crisis Guardrail
**Statement:** The system shall proactively monitor inputs for self-harm, suicidal ideation, or violence.
**Acceptance Criteria:**
- If detected, the AI must instantly bypass regular workflows, issue a standardized safety warning, and provide emergency hotline numbers(113).
- After crisis → notify doctor Imediately.

---

### 2.3 AI/ML Specific Requirements
- **RAG pipeline**: Hybrid search + reranking (bắt buộc)
- **LLM Models:** Text generation shall use `gpt-4o-mini` with configurable temperature (lower for clinical reasoning, slightly higher for empathetic patient chat) - Patient chat temperature ≈ 0.7–0.8 (empathetic), Doctor copilot temperature ≈ 0.0–0.2 (clinical precision).
- **Embedding Models:** Text embeddings shall use `text-embedding-3-small` (or equivalent) for high-quality vector representation.
- **Dual-Database RAG Configuration:**
  - **Internal Reasoning:** Vector storage in Qdrant for the DSM-5 manual.
  - **External Response:** Separate collection/metadata for Treatment guidelines. The system shall implement a robust RAG pipeline using LlamaIndex, with vector storage in Qdrant. Retrieval shall prioritize relevance and recency of chat context when applicable.
- **Safety & Guardrails:**
  - Strict Guardrail node implementation to intercept crisis queries.
  - The Agent must refuse to answer queries unrelated to mental health support.
  - The Agent must detect and respond appropriately to suicidal ideation or crisis situations with clear warning messages and suggested professional help.
  - No direct diagnosis shall ever be given to the patient by the AI.
- **Data Isolation & Privacy:** Patient chat data and clinical profiles shall be strictly isolated in Supabase.
- **Hallucination Prevention:** All clinical reasoning and advice must be grounded in retrieved knowledge base contexts. If insufficient relevant context is found, the system shall explicitly state limitations and avoid speculation.
- **Agent Orchestration:** Multi-agent workflows shall be implemented using LangGraph, utilizing dynamic routing based on `user_role` to manage distinct state transitions for Patients (Empathy Node => Symptom Extractor) and Doctors (Clinical Analyzer => DSM-5 Tool => Differential Diagnosis).
- **Role-based RAG Routing:** A LangGraph Router Node uses the `user_role` extracted from JWT to dynamically route requests:
  • Patient workflows → Treatment knowledge base collection + strict safety guardrails and coping exercise tools.
  • Doctor workflows → DSM-5 knowledge base collection + Academic Copilot and differential diagnosis tools.
- **Conversation Memory:** Persistent cross-session memory is maintained in Supabase (`chat_messages` table and user profiles). Within-session state uses LangGraph checkpointing persisted to Supabase. New sessions retrieve recent history and restore checkpoint as needed.
- **Consent & Data Forwarding:** Automatic forwarding of clinical profiles to the assigned doctor constitutes system-mediated implicit consent, as patients accept the relevant terms during registration. All forwarding actions are fully audited.

## 3. System Architecture & Design

   💬 _Documents the architectural elements that fulfill the requirements (The "How")._

### 3.1 Technology Stack Summary

   💬 _Core technologies used in the system._

   ➥ **Instructions:** List the stack clearly.

Example:

- **Frontend:** Streamlit, Plotly
- **Backend:** FastAPI, Python 3.11+ (Managed by `uv` Workspace)
- **AI/RAG Engine:** LlamaIndex, LangGraph, OpenAI API
- **Databases:** Supabase (PostgreSQL for user/state), Qdrant (Vector DB for DSM-5 chunks).
- **Observability & LLMOps:**...
- **Infrastructure & Deployment:**...

### 3.2 High-Level Architecture (Logical View)

   💬 _How do the components talk to each other?_
   ➥ **Instructions:** Insert a Mermaid.js diagram (C4 Context image or component diagram)

### 3.3 Detailed Design Considerations

- **3.3.1 Backend Architecture**

- **3.3.2 Multi-Agent Workflow (LangGraph)**

- **3.3.3 Database Design**

- **3.3.4 Caching & Performance Optimization**

- **3.3.5 Security Architecture**

- **3.3.6 Deployment & Containerization Strategy**

_(Bạn sẽ điền chi tiết low-level design vào từng phần con này)_

### 3.4 Data Flow

Mô tả luồng dữ liệu chính (Patient Chat → RAG → Silent Analysis → Doctor Dashboard).

---

## 4. Testing & LLMOps Strategy

   💬 _How will the system be tested and monitored in production?_

### 4.1 Testing Approach

   💬 _Ensuring code logic works._
   ➥ **Instructions:** Mention that `pytest` and `pytest-asyncio` will be used to test FastAPI endpoints and LangGraph state transitions locally.

- Unit Testing

- Integration Testing

- End-to-End Testing

- AI-Specific Testing (Safety, Faithfulness, Hallucination)

### 4.2 Observability & LLMOps

   💬 _Monitoring the AI's behavior and cost._
   ➥ **Instructions:** * **Tracing:** Langfuse will be integrated as a callback handler to trace all LlamaIndex and LangGraph executions.

- **Metrics Tracked:** Token usage, OpenAI API cost per user session, Latency, and retrieval context quality.

- Tracing & Logging

- Metrics & Alerting

- Cost Monitoring

- Model Evaluation Pipeline
