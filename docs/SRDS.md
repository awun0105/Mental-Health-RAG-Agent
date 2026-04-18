# Software Requirements and Design Specification (SRDS)

## Project: Mental Health AI Platform

   Version: 1.0
   Prepared by: Lam Quang Anh Quan
   Date: 19/4/2026

   ---

## 1. Project Overview

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

💬 _Specifies the verifiable requirements of the software product (The "What")._

### 2.1 Non-Functional Requirements (QoS)

💬 _Quality attributes constraining functional behavior._

➥ **Instructions:** Keep it brief and realistic for a 1-week project.

Example:

- **Performance:** API response time (Time-to-first-token) should be under 3 seconds.
- **Security:** API keys and Database URIs must be injected via environment variables (`.env`). Passwords must not be logged in plain text.

### 2.2 Functional Requirements

💬 _Externally observable behaviors of the system._

➥ **Instructions:** List the core features using the REQ template below. Focus on Auth, Chat, RAG Search, and Health Scoring.

**Format:**

- **ID:** REQ-FUNC-[001]
- **Feature:** [Feature Name]
- **Statement:** The system shall...
- **Acceptance Criteria:** How to verify it works.

_(Example)_

- **ID:** REQ-FUNC-001
- **Feature:** Agentic Chat Interface
- **Statement:** The system shall allow users to chat with an AI Agent that can autonomously decide when to ask follow-up questions and when to provide a DSM-5 based diagnosis.

### 2.3 AI/ML Specific Requirements

   💬 _Requirements unique to the LLM and RAG components._

   ➥ **Instructions:** Specify models, guardrails, and data isolation.

Example:

- **LLM Models:** Text generation using `gpt-4o-mini`
- **Embedding models:** embeddings using `text-embedding-3-small`.
- **RAG Configuration:** ...
- **Safety & Guardrails:** The Agent MUST refuse to answer queries unrelated to mental health. The Agent MUST output a warning if suicidal intent is detected.
- **Data Isolation & Privacy:** ...
- **Hallucination Prevention:** The Agent must strictly rely on the retrieved DSM-5 context. If no context matches, it must state it cannot diagnose the issue.

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
