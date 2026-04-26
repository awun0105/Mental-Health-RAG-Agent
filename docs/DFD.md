# Data Flow Diagrams (DFD)

> All diagrams in this document are derived from the
> [Software Requirements and Design Specification (SRDS)](./SRDS.md),
> Sections 8, 9, and 10.

---

This document contains **9 diagrams** cover completely all data flows in SRDS.md:

| # | Diagram | Mermaid type | Source SRDS |
|---|---------|-------------|------------|
| 1 | System Context (Level 0) | `graph TB` | Section 8.1 |
| 2 | Data Storage Mapping | `graph LR` | Section 9.1 + 9.2 |
| 3 | Patient Chat Flow | `sequenceDiagram` | Section 10.1 |
| 4 | Session Closure & Clinical Profile | `sequenceDiagram` | Section 10.2 |
| 5 | Doctor Copilot Flow | `sequenceDiagram` | Section 10.3 |
| 6 | Knowledge Ingestion Flow | `sequenceDiagram` | Section 10.4 |
| 7 | Agent Orchestration Graph | `graph TD` | Section 8.2 |
| 8 | RBAC Data Access Flow | `flowchart TD` | Section 11.1 |
| 9 | End-to-End Data Lifecycle | `graph LR` | Tổng hợp | [4-cite-1](#4-cite-1) [4-cite-2](#4-cite-2) [4-cite-0](#4-cite-0) [4-cite-3](#4-cite-3)

---



## 1. System Context Diagram (Level 0)

High-level view of external actors and the platform boundary.

```mermaid
graph TB
    Patient["Patient"]
    Doctor["Doctor / Counselor"]
    Admin["Administrator"]

    subgraph Platform["Mental Health AI Platform"]
        UI["Streamlit UI"]
        API["FastAPI Backend"]
        Agents["LangGraph Agent Orchestrator"]
        RAG["LlamaIndex RAG Service"]
        Qdrant["Qdrant Vector DB"]
        Supabase["Supabase / PostgreSQL"]
        LLM["LLM Provider"]
        Langfuse["Langfuse Observability"]
    end

    Patient -- "Chat messages" --> UI
    Doctor -- "Dashboard queries, Copilot questions" --> UI
    Admin -- "User management, Ingestion triggers" --> UI

    UI -- "HTTP requests" --> API
    API -- "Agent invocation" --> Agents
    Agents -- "Retrieval queries" --> RAG
    RAG -- "Semantic search" --> Qdrant
    API -- "CRUD operations" --> Supabase
    Agents -- "Chat completion, Embeddings" --> LLM
    Agents -- "Traces" --> Langfuse
    RAG -- "Traces" --> Langfuse

    UI -- "Responses" --> Patient
    UI -- "Clinical data, Copilot answers" --> Doctor
    UI -- "Admin confirmations" --> Admin
```

---

## 2. Data Storage Mapping

Where each data entity lives and who can access it.

```mermaid
graph LR
    subgraph Supabase["Supabase / PostgreSQL"]
        Users["users"]
        Roles["roles"]
        Assignments["doctor_assignments"]
        Sessions["chat_sessions"]
        Messages["chat_messages"]
        Profiles["clinical_profiles"]
        Scores["stress_risk_scores"]
        Consent["consent_records"]
        Audit["audit_logs"]
    end

    subgraph Qdrant["Qdrant Vector DB"]
        TreatmentKB["treatment_knowledge"]
        DSM5KB["dsm5_clinical"]
        SafetyKB["safety_policy"]
    end

    subgraph Langfuse["Langfuse"]
        Traces["prompt_traces"]
        Evals["evaluation_datasets"]
    end

    Patient["Patient"] -. "read/write" .-> Sessions
    Patient -. "read/write" .-> Messages
    Patient -. "DENIED" .-x Profiles
    Patient -. "DENIED" .-x DSM5KB

    Doctor["Doctor"] -. "read (assigned only)" .-> Profiles
    Doctor -. "read (assigned only)" .-> Scores
    Doctor -. "read" .-> DSM5KB
    Doctor -. "read" .-> TreatmentKB

    Admin["Admin"] -. "full" .-> Users
    Admin -. "full" .-> Assignments
    Admin -. "read" .-> Audit
```

---

## 3. Patient Chat Flow

**Reference:** SRDS Section 10.1

```mermaid
sequenceDiagram
    actor P as Patient
    participant UI as Streamlit Chat UI
    participant API as FastAPI Backend
    participant LG as LangGraph Orchestrator
    participant SG as Safety Guardrail Agent
    participant PA as Patient Empathetic Agent
    participant RAG as LlamaIndex RAG Service
    participant Qdrant as Qdrant
    participant LLM as LLM Provider
    participant DB as Supabase / PostgreSQL
    participant LF as Langfuse

    P ->> UI: Send chat message
    UI ->> API: POST /api/v1/chat {session_id, content}
    API ->> DB: Load session context + user role
    API ->> LG: Invoke agent graph (state)

    LG ->> SG: Route to Safety Guardrail Agent
    SG ->> LLM: Crisis detection prompt
    LLM -->> SG: Classification result

    alt Crisis Detected
        SG -->> LG: safety_flag=true, safety_severity=critical
        LG -->> API: Hardcoded safety response
        API ->> DB: Persist message + safety event (high-priority)
        API ->> LF: Log crisis event trace
        API -->> UI: Safety response + crisis resources
        UI -->> P: Display safety message + hotline
    else No Crisis
        SG -->> LG: safety_flag=false
        LG ->> PA: Route to Patient Empathetic Agent
        PA ->> RAG: Retrieve treatment guidance
        RAG ->> Qdrant: Semantic search (treatment_knowledge)
        Qdrant -->> RAG: Relevant chunks
        RAG -->> PA: Retrieved context
        PA ->> LLM: Generate empathetic response (context + history)
        LLM -->> PA: Grounded response (no diagnosis)
        PA -->> LG: Response + metadata
        LG -->> API: Final response
        API ->> DB: Persist message + AI response + trace IDs
        API ->> LF: Log prompt, retrieval, latency, cost
        API -->> UI: AI response
        UI -->> P: Display empathetic response
    end
```

---

## 4. Session Closure and Clinical Profile Flow

**Reference:** SRDS Section 10.2

```mermaid
sequenceDiagram
    actor P as Patient
    participant UI as Streamlit Chat UI
    participant API as FastAPI Backend
    participant LG as LangGraph Orchestrator
    participant CA as Silent Clinical Analyzer
    participant LLM as LLM Provider
    participant DB as Supabase / PostgreSQL
    participant LF as Langfuse
    actor D as Doctor

    alt Manual End
        P ->> UI: Click "End Session"
    else Intent Detection
        Note over LG: Patient says goodbye / signals end
    else Inactivity Timeout
        Note over API: No message for N minutes
        API ->> UI: Gentle timeout warning
    end

    UI ->> API: POST /api/v1/sessions/{id}/end
    API ->> DB: Mark session status = closed
    API ->> LG: Trigger post-session analysis

    LG ->> CA: Invoke Silent Clinical Analyzer
    CA ->> DB: Load full session message history
    DB -->> CA: All messages + safety events
    CA ->> LLM: Extract symptoms, risk markers, duration signals
    LLM -->> CA: Structured clinical extraction

    CA ->> CA: Compute stress/risk score (0-100)
    CA ->> CA: Select supporting evidence snippets

    CA -->> LG: Clinical profile + score
    LG -->> API: Analysis complete

    API ->> DB: Store clinical_profile
    API ->> DB: Store stress_risk_score
    API ->> DB: Audit log (profile_generated)
    API ->> LF: Trace analysis prompt + output

    API -->> UI: Simplified trend update (no clinical details)
    UI -->> P: "Session ended. Here is your wellness trend."

    Note over D: Doctor sees new profile in dashboard queue
    D ->> UI: Open patient dashboard
    UI ->> API: GET /api/v1/patients/{id}/profile
    API ->> DB: Verify doctor-patient assignment
    API ->> DB: Fetch clinical profile + scores
    API ->> DB: Audit log (doctor_viewed_profile)
    API -->> UI: Clinical profile + evidence snippets + score
    UI -->> D: Display clinical summary
```

---

## 5. Doctor Conversational Copilot Flow

**Reference:** SRDS Section 10.3

```mermaid
sequenceDiagram
    actor D as Doctor
    participant UI as Streamlit Copilot UI
    participant API as FastAPI Backend
    participant Auth as RBAC Check
    participant LG as LangGraph Orchestrator
    participant DC as Doctor Copilot Agent
    participant RAG as LlamaIndex RAG Service
    participant Qdrant as Qdrant
    participant LLM as LLM Provider
    participant DB as Supabase / PostgreSQL
    participant LF as Langfuse

    D ->> UI: Select patient profile OR clinical-knowledge mode
    D ->> UI: Ask question

    UI ->> API: POST /api/v1/copilot {patient_id?, question, mode}
    API ->> Auth: Verify doctor role + patient assignment
    Auth -->> API: Authorized

    API ->> LG: Invoke agent graph (doctor workflow)
    LG ->> DC: Route to Doctor Copilot Agent

    alt Patient-Context Mode
        DC ->> DB: Load patient profile, report, evidence, scores
        DB -->> DC: Patient-specific data
        DC ->> RAG: Retrieve DSM-5 + treatment evidence
        RAG ->> Qdrant: Search (dsm5_clinical + treatment_knowledge)
        Qdrant -->> RAG: Relevant chunks
        RAG -->> DC: Retrieved context
        DC ->> LLM: Generate response (patient data + KB evidence)
        LLM -->> DC: Decision-support response with citations
    else Clinical-Knowledge Mode
        DC ->> RAG: Retrieve DSM-5 + treatment evidence only
        RAG ->> Qdrant: Search (dsm5_clinical + treatment_knowledge)
        Qdrant -->> RAG: Relevant chunks
        RAG -->> DC: Retrieved context
        DC ->> LLM: Generate response (KB evidence only, no patient data)
        LLM -->> DC: Clinical knowledge response with citations
    end

    Note over DC: Response includes source classification,<br/>uncertainty notes, "not a final diagnosis" disclaimer

    DC -->> LG: Response + source metadata
    LG -->> API: Final response

    API ->> DB: Audit log (copilot_query, patient_id, mode)
    API ->> LF: Trace prompt, retrieval, latency, cost
    API -->> UI: Copilot response with citations
    UI -->> D: Display response + source labels
```

---

## 6. Knowledge Ingestion Flow

**Reference:** SRDS Section 10.4

```mermaid
sequenceDiagram
    actor A as Admin / Developer
    participant CLI as Ingestion CLI (make ingest)
    participant Pipeline as DSM5Ingestion Pipeline
    participant LLM as LLM Provider (Embeddings)
    participant Qdrant as Qdrant Vector DB
    participant DB as Supabase / PostgreSQL
    participant Test as Retrieval Test Suite

    A ->> CLI: Run ingestion command
    CLI ->> Pipeline: Start ingestion (data_dir, collection, access_level)

    Pipeline ->> Pipeline: Load source documents (PDF, text)
    Pipeline ->> Pipeline: Clean and extract text + metadata
    Pipeline ->> Pipeline: Semantic chunking (SemanticSplitterNodeParser)
    Pipeline ->> Pipeline: Enrich metadata (source, category, access_level, page)

    Pipeline ->> LLM: Generate embeddings for all chunks
    LLM -->> Pipeline: Embedding vectors

    Pipeline ->> Qdrant: Write chunks to target collection
    Qdrant -->> Pipeline: Confirmation

    Pipeline ->> DB: Store knowledge_source version record
    DB -->> Pipeline: Stored

    Pipeline -->> CLI: Ingestion complete (N chunks)
    CLI -->> A: Summary report

    A ->> Test: Run retrieval quality tests
    Test ->> Qdrant: Test queries against expected results
    Qdrant -->> Test: Search results
    Test ->> Test: Evaluate faithfulness, relevance, coverage
    Test -->> A: Quality report (pass/fail)
```

---

## 7. Agent Orchestration Graph

**Reference:** SRDS Section 8.2

Overview of how LangGraph routes requests through agent nodes.

```mermaid
graph TD
    Entry["Entry Point"]
    Router["Router Agent"]
    SG["Safety Guardrail Agent"]
    PA["Patient Empathetic Agent"]
    TreatRAG["Treatment RAG Agent"]
    CA["Silent Clinical Analyzer"]
    DSM5["DSM-5 Retrieval Agent"]
    DC["Doctor Copilot Agent"]
    Audit["Audit / Trace Node"]
    End["END"]

    Entry --> Router

    Router -- "role=patient" --> SG
    Router -- "role=doctor" --> DC
    Router -- "trigger=session_end" --> CA

    SG -- "crisis=true" --> Audit
    SG -- "crisis=false" --> PA

    PA --> TreatRAG
    TreatRAG --> Audit

    CA --> Audit

    DC --> DSM5
    DSM5 --> Audit

    Audit --> End
```

---

## 8. RBAC Data Access Flow

How role-based access control gates every data request.

```mermaid
flowchart TD
    Request["Incoming API Request"]
    JWT["Extract JWT Token"]
    Verify["Verify Token + Load User"]
    Role{"Check User Role"}

    PatientGate{"Resource = own data?"}
    DoctorGate{"Patient assigned?"}
    AdminGate{"Action permitted?"}

    Allow["Allow Access"]
    Deny["403 Forbidden"]
    AuditLog["Write Audit Log"]

    Request --> JWT --> Verify --> Role

    Role -- "patient" --> PatientGate
    Role -- "doctor" --> DoctorGate
    Role -- "admin" --> AdminGate

    PatientGate -- "yes" --> Allow
    PatientGate -- "no" --> Deny

    DoctorGate -- "yes" --> Allow
    DoctorGate -- "no" --> Deny

    AdminGate -- "yes" --> Allow
    AdminGate -- "no" --> Deny

    Allow --> AuditLog
    Deny --> AuditLog
```

---

## 9. End-to-End Data Lifecycle

Summary of how data flows from creation to consumption across the entire platform.

```mermaid
graph LR
    subgraph Ingestion["Knowledge Ingestion"]
        Docs["Source Documents"] --> Chunk["Semantic Chunking"]
        Chunk --> Embed["Embedding"]
        Embed --> Store["Qdrant Collections"]
    end

    subgraph PatientFlow["Patient Session"]
        Msg["Patient Message"] --> Safety["Safety Check"]
        Safety --> Response["Empathetic Response"]
        Response --> Persist["Persist to Supabase"]
    end

    subgraph AnalysisFlow["Post-Session Analysis"]
        Persist --> Analyze["Silent Clinical Analyzer"]
        Analyze --> Profile["Clinical Profile"]
        Analyze --> Score["Stress/Risk Score"]
        Profile --> DoctorDB["Store in Supabase"]
        Score --> DoctorDB
    end

    subgraph DoctorFlow["Doctor Workflow"]
        DoctorDB --> Dashboard["Doctor Dashboard"]
        Dashboard --> Copilot["Doctor Copilot"]
        Store --> Copilot
        Copilot --> Decision["Clinical Decision Support"]
    end

    subgraph Observability["Observability"]
        Safety -.-> Langfuse["Langfuse Traces"]
        Response -.-> Langfuse
        Analyze -.-> Langfuse
        Copilot -.-> Langfuse
    end
```

---

*End of DFD.md*
