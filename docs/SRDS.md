# Software Requirements and Design Specification (SRDS)

## Project: Mental Health AI Platform

   Version: 1.0

   Prepared by: awun0105

   Date: 19/4/2026

   ---

## 1. System Overview

### 1.1 Product Perspective & Context

  The **Mental Health AI Platform** is an advanced AI-integrated web application specifically designed to optimize clinical workflows in mental health centers and clinics. The system serves as an intelligent bridge connecting two primary user groups: **Patients** and **Medical Professionals / Counselors**, while strictly adhering to the **Human-in-the-loop** principle to ensure the highest level of medical safety.

  The platform leverages the power of Retrieval-Augmented Generation (RAG) to accurately retrieve and apply domain-specific knowledge from its core knowledge base — the official **DSM-5 (Diagnostic and Statistical Manual of Mental Disorders) manual in Vietnamese**, ensuring all responses and analyses are grounded in clinically validated, localized medical standards.

### 1.2 User Experiences

#### 1.2.1 Patient Experience (Safe & Empathetic 24/7 Conversational Space)

  For patients, the platform provides a private, secure, and always-available 24/7 conversational environment.

- **Empathetic Listener**: The AI acts as a thoughtful companion, using open-ended questions to help patients comfortably share their emotions and challenges.
- **Immediate Psychological First Aid**: Drawing from the clinical knowledge base of the **DSM-5** and other standardized medical materials, the AI delivers soothing advice and simple, immediately applicable psychological coping exercises.
- **Medical Safety Protection**: To prevent panic or the nocebo effect, the AI **never directly diagnoses or names any disorder** during the conversation. Instead, the system silently analyzes the entire chat history, synthesizes symptoms, and builds a detailed clinical profile, which is then **forwarded directly to the doctor**.
- **Transparency for Users**: Patients have the option to view the complete AI-generated clinical assessment after the chat session ends (if they wish).

#### 1.2.2 Experience for Medical Professionals / Counselors (Professional Clinical Dashboard)

For doctors and counselors, the system automatically transforms into a highly professional **Clinical Dashboard**.

- **Intelligent Patient Profiles**: Doctors can immediately review complete patient profiles alongside AI-synthesized analyses, symptom summaries, and preliminary diagnostic insights derived from the conversation history.
- **Intelligent Academic Copilot**: The AI goes beyond simple summarization to serve as a powerful academic assistant. Doctors can directly ask questions and cross-reference diagnostic criteria from the DSM-5 manual with the specific details of each patient’s profile.
- **Optimized Clinical Decision-Making**: This enables doctors to save maximum time on profile analysis and reach the most accurate final treatment decisions, grounded in solid data and their own professional judgment.

### 1.3 Stakeholder Concerns

The Mental Health AI Platform is designed to address the distinct needs, expectations, and potential risks perceived by its key stakeholders. These concerns directly influence the functional and non-functional requirements of the system. The stakeholders are grouped into three primary categories:

#### 1.3.1 Patients (Primary End Users)

Patients require a safe, non-judgmental, and always-accessible space to express emotional distress. Their main concerns include:

- **Data Privacy and Confidentiality**: Mental health information is highly sensitive; any perceived breach could deter usage or cause irreversible psychological harm.
- **Empathy and Natural Interaction**: The AI must maintain a consistently warm, supportive tone without sounding mechanical or clinical, as patients may be in vulnerable emotional states.
- **Psychological Safety**: Avoidance of direct diagnostic statements or alarming medical jargon during conversation to prevent nocebo effects or increased anxiety.
- **Transparency and Control**: Users want the option to review AI-generated clinical summaries after the session without being overwhelmed during the chat itself.
- **Accessibility**: 24/7 availability with low technical barriers, especially for users experiencing acute distress.

Failure to address these concerns could result in low user adoption, increased dropout rates, or ethical risks related to mental health support.

#### 1.3.2 Medical Professionals and Counselors

Doctors and counselors need reliable, time-saving tools that augment rather than replace their clinical judgment. Their primary concerns are:

- **Accuracy and Reliability of AI Outputs**: Preliminary symptom summaries and clinical profiles must be faithful to the DSM-5 Vietnamese manual and the patient’s actual conversation history.
- **Efficiency in Workflow**: The Clinical Dashboard must reduce time spent on manual note review and allow quick cross-referencing of diagnostic criteria with patient-specific data.
- **Human-in-the-Loop Control**: The system must never present AI conclusions as final diagnoses; all treatment decisions remain the sole responsibility of the licensed professional.
- **Usability and Integration**: The interface must be intuitive for busy clinicians who may not have deep technical expertise.

Addressing these ensures higher acceptance by medical staff and improves overall quality of care.

#### 1.3.3 Technical Stakeholders (Recruiters, Engineers, and Evaluators)

Technical audiences evaluate the solution’s robustness, maintainability, and production readiness. Their key concerns include:

- **Architectural Quality and Scalability**: Clear separation of concerns (FastAPI backend, structured agent workflows via LangGraph, and observability through Langfuse).
- **LLMOps and Cost Management**: Transparent tracking of token usage, latency, and operational costs in real time.
- **Reliability and Safety Guardrails**: Demonstrated use of RAG, multi-agent orchestration, and strict constraints on medical knowledge to minimize hallucination and ensure regulatory alignment.
- **Development Efficiency**: Ability to deliver a fully functional, production-grade system within a constrained 1-week sprint.

Satisfying these stakeholders validates the technical excellence and commercial viability of the platform.

---

## 2. System Requirements

This section specifies the verifiable functional and non-functional requirements of the Mental Health AI Platform.

### 2.1 Non-Functional Requirements (QoS)

**Performance & Scalability**

- API response time (Time-to-First-Token) for chat interactions shall not exceed 3 seconds under normal load.
- The system shall support concurrent usage by at least 200 active users (patients and doctors) with graceful degradation.
- The RAG retrieval pipeline shall maintain sub-second latency even when the DSM-5 knowledge base grows significantly.

**Security & Data Privacy (Healthcare Compliance)**

- All sensitive mental health data (chat history, clinical profiles, health scores) must be encrypted both at rest and in transit (TLS 1.3+).
- User authentication and session management shall follow secure practices (JWT with short expiry, refresh tokens, and secure HTTP-only cookies).
- The platform shall enforce strict data isolation between patients and doctors; doctors can only access patient data after explicit consent or system-mediated forwarding.
- Compliance with personal data protection regulations and healthcare data handling best practices (inspired by HIPAA principles and Vietnamese personal data protection laws).

**Reliability & Fault Tolerance**

- The system shall implement graceful error handling and retry mechanisms for external services (OpenAI API, vector database).
- Critical components (chat service, profile analysis) shall include circuit breakers and fallback strategies to ensure continuous availability.
- All AI-generated clinical profiles shall include traceability (audit logs) for medical review.

**Observability & LLMOps**

- All LLM calls, RAG retrievals, and agent workflows shall be fully traced and logged using Langfuse (or equivalent observability platform).
- Token usage, latency, cost per session, and retrieval quality metrics shall be monitored in real-time with alerting thresholds.
- The platform shall support A/B testing and continuous evaluation of different prompt strategies and model versions.

**Usability & Accessibility**

- The patient interface shall be intuitive, empathetic in tone, and accessible on both desktop and mobile devices.
- The doctor dashboard shall provide a professional, efficient workspace optimized for clinical decision-making with minimal cognitive load.
- The entire application shall support Vietnamese as the primary language with clear, natural, and culturally appropriate communication.

### 2.2 Functional Requirements

**REQ-FUNC-001**
**Feature:** User Authentication & Role-Based Access Control
**Statement:** The system shall support secure registration, login, and Role-Based Access Control (RBAC) to differentiate between Patient and Medical Professional roles.
**Acceptance Criteria:**

- Patients can only access chat and personal health tracking.
- Doctors can access the Clinical Dashboard, patient profiles, and AI-generated analyses.
- Session management shall automatically route users to the correct interface based on role.

**REQ-FUNC-002**
**Feature:** Empathetic 24/7 Patient Chat Interface
**Statement:** The system shall provide a private, secure conversational interface where patients can chat 24/7 with an AI Agent acting as an empathetic listener.
**Acceptance Criteria:**

- The AI shall use open-ended questions and maintain a warm, supportive tone.
- The interface shall support continuous conversation with memory of previous sessions.

**REQ-FUNC-003**
**Feature:** Silent Symptom Analysis & Profile Generation
**Statement:** The system shall silently analyze the entire chat history to detect symptoms and generate a structured clinical profile without displaying any diagnosis directly to the patient.
**Acceptance Criteria:**

- The profile shall be forwarded automatically to the assigned doctor.
- Patients shall have an optional view of the AI-generated clinical assessment after the session ends.

**REQ-FUNC-004**
**Feature:** Psychological First Aid & Coping Exercises
**Statement:** The system shall provide immediate, DSM-5-grounded soothing advice and simple psychological coping exercises during patient conversations.
**Acceptance Criteria:**

- All advice and exercises must be retrieved via RAG from the DSM-5 knowledge base.
- Responses shall never include direct diagnostic statements.

**REQ-FUNC-005**
**Feature:** Professional Clinical Dashboard for Doctors
**Statement:** The system shall provide doctors with a comprehensive Clinical Dashboard displaying patient profiles, AI-synthesized symptom summaries, and preliminary clinical insights.
**Acceptance Criteria:**

- Doctors can review full conversation history and AI-generated profiles.
- Dashboard shall support search and filtering of assigned patients.

**REQ-FUNC-006**
**Feature:** Academic Copilot & DSM-5 Cross-Referencing
**Statement:** The system shall allow doctors to query the AI Assistant to cross-reference DSM-5 diagnostic criteria with specific patient profiles and conversation data.
**Acceptance Criteria:**

- The AI shall function as an intelligent academic copilot using RAG over the DSM-5 Vietnamese manual.
- All responses shall clearly indicate they are supportive tools, not final diagnoses.

**REQ-FUNC-007**
**Feature:** Health Scoring & Progress Tracking
**Statement:** The system shall calculate and track a mental health score (tốt/khá/trung bình/kém) based on conversation analysis and store historical trends for both patients and doctors.
**Acceptance Criteria:**

- Scores shall be stored securely and visible in the patient’s health tracking section and doctor’s dashboard.

### 2.3 AI/ML Specific Requirements

- **LLM Models:** Text generation shall use `gpt-4o-mini` (or equivalent high-performance model) with configurable temperature for balanced creativity and factual accuracy.
- **Embedding Models:** Text embeddings shall use `text-embedding-3-small` (or equivalent) for high-quality vector representation of DSM-5 content and chat history.
- **RAG Configuration:** The system shall implement a robust RAG pipeline using LlamaIndex, with vector storage in Qdrant. Retrieval shall prioritize relevance and recency of chat context when applicable.
- **Safety & Guardrails:**
  - The Agent must refuse to answer queries unrelated to mental health support.
  - The Agent must detect and respond appropriately to suicidal ideation or crisis situations with clear warning messages and suggested professional help.
  - No direct diagnosis shall ever be presented to patients in the chat interface.
- **Data Isolation & Privacy:** Patient chat data and clinical profiles shall be strictly isolated. AI analysis shall run in a secure backend process with minimal data exposure.
- **Hallucination Prevention:** All clinical reasoning and advice must be grounded in retrieved DSM-5 context. If insufficient relevant context is found, the system shall explicitly state limitations and avoid speculation.
- **Agent Orchestration:** Multi-agent workflows shall be implemented using LangGraph to manage conversation flow, symptom analysis, profile generation, and doctor assistance tasks with clear state management.

---

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
