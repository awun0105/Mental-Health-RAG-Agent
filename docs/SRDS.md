1. # Software Requirements and Design Specification (SRDS)
   ## Project: AI-Powered Mental Health Counseling Agent

   Version: 1.0  
   Prepared by: [Your Name]  
   Date: [Current Date]  

   ---

   ## 1. System Overview
   💬 _Provides background, context, and the boundaries of the system to be built._

   ### 1.1 Product Perspective & Context
   💬 _What is this product and why is it being built?_
   ➥ **Instructions:** Describe the product's primary purpose in 3-4 sentences. Explain that this is a Proof of Concept (PoC) / Portfolio project aiming to build an autonomous AI agent for preliminary mental health counseling based on the DSM-5 manual.

   ### 1.2 Stakeholder Concerns
   💬 _Who cares about this system and what are their main priorities?_
   ➥ **Instructions:** Briefly list the target users and developer concerns.
   * **End Users:** Seek a safe, private, and empathetic conversational interface to track their mental health.
   * **Developer/Reviewer (You & Recruiters):** Focus on clean architecture (Modular Monolith), proper Multi-Agent implementation (LangGraph), and LLM observability.

   ### 1.3 Assumptions & Constraints
   💬 _What limits the design and requirements?_
   ➥ **Instructions:** List the project constraints. 
   * *Example:* "Must be completed within a 1-week sprint."
   * *Example:* "Relies on OpenAI API (gpt-4o-mini) and Qdrant Cloud for vector storage."
   * *Example:* "Uses a condensed Vietnamese version of the DSM-5 PDF as the sole medical knowledge base."

   ---

   ## 2. System Requirements
   💬 _Specifies the verifiable requirements of the software product (The "What")._

   ### 2.1 Functional Requirements
   💬 _Externally observable behaviors of the system._
   ➥ **Instructions:** List the core features using the REQ template below. Focus on Auth, Chat, RAG Search, and Health Scoring.

   **Format:**
   * **ID:** REQ-FUNC-[001]
   * **Feature:** [Feature Name]
   * **Statement:** The system shall...
   * **Acceptance Criteria:** How to verify it works.

   *(Example)*
   * **ID:** REQ-FUNC-001
   * **Feature:** Agentic Chat Interface
   * **Statement:** The system shall allow users to chat with an AI Agent that can autonomously decide when to ask follow-up questions and when to provide a DSM-5 based diagnosis.

   ### 2.2 Non-Functional Requirements (QoS)
   💬 _Quality attributes constraining functional behavior._
   ➥ **Instructions:** Keep it brief and realistic for a 1-week project.
   * **Performance:** API response time (Time-to-first-token) should be under 3 seconds.
   * **Security:** API keys and Database URIs must be injected via environment variables (`.env`). Passwords must not be logged in plain text.

   ### 2.3 AI/ML Specific Requirements
   💬 _Requirements unique to the LLM and RAG components._
   ➥ **Instructions:** Specify models, guardrails, and data isolation.
   * **Models:** Text generation using `gpt-4o-mini`, embeddings using `text-embedding-3-small`.
   * **Guardrails:** The Agent MUST refuse to answer queries unrelated to mental health. The Agent MUST output a warning if suicidal intent is detected.
   * **Hallucination Prevention:** The Agent must strictly rely on the retrieved DSM-5 context. If no context matches, it must state it cannot diagnose the issue.

   ---

   ## 3. System Architecture & Design
   💬 _Documents the architectural elements that fulfill the requirements (The "How")._

   ### 3.1 Technology Stack Summary
   💬 _Core technologies used in the system._
   ➥ **Instructions:** List the stack clearly.
   * **Frontend:** Streamlit, Plotly
   * **Backend:** FastAPI, Python 3.11+ (Managed by `uv` Workspace)
   * **AI/RAG Core:** LlamaIndex, LangGraph, OpenAI API
   * **Databases:** Supabase (PostgreSQL for user/state), Qdrant (Vector DB for DSM-5 chunks)

   ### 3.2 System Architecture (Logical View)
   💬 _How do the components talk to each other?_
   ➥ **Instructions:** Insert a Mermaid.js diagram or a link to a C4 Context image showing Streamlit sending HTTP requests to FastAPI, which then interacts with Supabase, Qdrant, and OpenAI.

   ### 3.3 Database Schema
   💬 _How is data structured and stored?_
   ➥ **Instructions:** Briefly describe the tables.
   * **Relational (Supabase):** * `Users` table (id, username, password_hash)
     * `Chat_History` table (id, user_id, message_role, content, timestamp)
     * `Health_Scores` table (id, user_id, score_value, evaluation_notes, timestamp)
   * **Vector (Qdrant):** * `dsm5_collection`: Stores text chunks and metadata (document title, keywords).

   ### 3.4 Multi-Agent Workflow (LangGraph Design)
   💬 _The internal state machine of the AI brain._
   ➥ **Instructions:** Define the graph nodes and edges.
   * **State Definition:** {messages, current_symptoms, diagnosis_ready, final_score}
   * **Nodes:** 1. `GuardrailNode`: Checks for harmful intent.
     2. `InterviewerNode`: Chats to collect symptoms.
     3. `RAGSearcherNode`: Queries Qdrant for DSM-5 criteria.
     4. `EvaluatorNode`: Calculates the health score.
   * **Edges (Conditional):** Logic to route between chatting, searching, or concluding the session.

   ---

   ## 4. Testing & LLMOps Strategy
   💬 _How will the system be tested and monitored in production?_

   ### 4.1 Testing Approach
   💬 _Ensuring code logic works._
   ➥ **Instructions:** Mention that `pytest` and `pytest-asyncio` will be used to test FastAPI endpoints and LangGraph state transitions locally.

   ### 4.2 Observability & LLMOps
   💬 _Monitoring the AI's behavior and cost._
   ➥ **Instructions:** * **Tracing:** Langfuse will be integrated as a callback handler to trace all LlamaIndex and LangGraph executions.
   * **Metrics Tracked:** Token usage, OpenAI API cost per user session, Latency, and retrieval context quality.
