<a id="readme-top"></a>

# Mental-Health-Sovereign-Agentic-AI-Platform

A privacy-first, human-in-the-loop AI platform for mental health support. The system uses RAG and multi-agent orchestration to provide safe patient support and clinically grounded decision support for doctors.

## Table of Contents
- [Overview](#overview)
- [Use Case / Problem Description](#use-case--problem-description)
- [Core Workflows](#core-workflows)
- [Software Components](#software-components)
- [Target Audience](#target-audience)
- [Repository Structure Overview](#repository-structure-overview)
- [Documentation](#documentation)
- [Prerequisites](#prerequisites)
- [Hardware Requirements](#hardware-requirements)
- [Quickstart Guide](#quickstart-guide)
- [License](#license)

## Overview
This repository contains the source code and documentation for **Mental-Health-Sovereign-Agentic-AI-Platform**.

The platform is designed for two main experiences:

- **Patients:** a safe, empathetic chat experience for psychological first-aid, coping guidance, and crisis escalation. The AI must not directly diagnose patients.
- **Doctors / Counselors:** a clinical workspace where doctors can review generated patient profiles, inspect evidence snippets, ask the AI about a patient report, and query clinical knowledge from the curated knowledge base.

The long-term goal is a sovereign AI system that can run in private infrastructure so sensitive mental health data stays under organizational control.

## Key Features

- **Multi-Agent Orchestration:** LangGraph coordinates patient support, safety guardrails, silent clinical analysis, DSM-5 retrieval, and doctor copilot workflows.
- **RAG Grounding:** LlamaIndex retrieves evidence from curated DSM-5 and treatment knowledge bases.
- **Dual-Database Design:** Qdrant stores vector knowledge; Supabase/PostgreSQL stores users, sessions, clinical profiles, scores, consent records, and audit logs.
- **Doctor Conversational Copilot:** Doctors can chat with AI about assigned patient profiles, generated reports, evidence snippets, risk scores, or general clinical knowledge.
- **Patient Safety Guardrails:** Crisis detection and no-direct-diagnosis policies protect patient-facing conversations.
- **Audit and Observability:** Langfuse traces prompts, retrieval, model outputs, latency, and cost.
- **uv Workspace:** Backend and frontend dependencies are managed in one Python workspace.

## Use Case / Problem Description

Mental health data is highly sensitive, and clinical AI workflows must be safe, explainable, and controlled. This project addresses that challenge by combining:

- Private mental health chat support for patients.
- Doctor-facing summaries and clinical decision support.
- RAG grounded in curated medical knowledge.
- Human-in-the-loop design so doctors retain final clinical authority.
- A roadmap toward self-hosted, privacy-first deployment.

## Software Components

1. **Backend API:** FastAPI service for health checks, future chat APIs, agent workflows, and RAG endpoints.
2. **Frontend UI:** Streamlit interface for patient and doctor workflows.
3. **Agent Orchestration:** LangGraph manages stateful multi-agent flows.
4. **RAG Engine:** LlamaIndex handles document ingestion, indexing, retrieval, and citations.
5. **Vector Database:** Qdrant stores DSM-5, treatment, and policy knowledge chunks.
6. **Application Database:** Self-hosted Supabase/PostgreSQL stores users, sessions, patient profiles, doctor assignments, audit logs, and scores.
7. **LLM Layer:** Provider abstraction starts with configurable hosted LLMs and can later evolve to LiteLLM or self-hosted vLLM.
8. **Observability:** Langfuse tracks prompts, retrieval context, outputs, cost, and latency.

## Technical Diagram

High-level MVP architecture:

```text
Streamlit UI
    |
    v
FastAPI Backend
    |
    +--> LangGraph Agent Orchestrator
    |       +--> Safety Guardrail Agent
    |       +--> Patient Empathetic Agent
    |       +--> Silent Clinical Analyzer
    |       +--> DSM-5 Retrieval Agent
    |       +--> Doctor Conversational Clinical Copilot
    |
    +--> LlamaIndex RAG Service --> Qdrant
    +--> Supabase / PostgreSQL
    +--> LLM Provider Abstraction
    +--> Langfuse
```

## Workflow

1. **Knowledge Ingestion:** Curated DSM-5 and treatment documents are cleaned, chunked, embedded, and stored in Qdrant.
2. **Patient Chat:** The patient talks with an empathetic AI agent that provides safe support without direct diagnosis.
3. **Safety Check:** A guardrail agent detects crisis or self-harm signals and routes to a safety response when needed.
4. **Silent Clinical Profile:** At session closure, the system generates a doctor-facing profile with symptoms, risk markers, and evidence snippets.
5. **Doctor Review:** The doctor reviews assigned patient profiles, stress/risk trends, and generated reports.
6. **Doctor AI Chat:** The doctor asks the copilot about a patient profile/report or general clinical knowledge from the knowledge base.

## Core Workflows

| Workflow Name | Description | Reference / Link |
| --- | --- | --- |
| Patient Support Chat | Empathetic, non-diagnostic chat grounded in treatment guidance. | `docs/SRDS.md` |
| Crisis Safety Flow | Detects crisis/self-harm signals and returns safety guidance. | `docs/SRDS.md` |
| Clinical Profile Generation | Converts a completed patient session into a doctor-facing summary. | `docs/SRDS.md` |
| Doctor Copilot | Lets doctors ask questions about assigned patient profiles, generated reports, and clinical knowledge. | `docs/SRDS.md` |
| Knowledge Ingestion | Loads, chunks, embeds, and stores clinical documents in Qdrant. | `docs/SRDS.md` |

## Target Audience

1. **Patients:** People seeking a safe space for emotional support and simple coping guidance.
2. **Doctors / Counselors:** Professionals who need faster review of patient sessions and clinically grounded AI assistance.
3. **Developers / AI Engineers:** Builders implementing RAG, multi-agent workflows, safety checks, and clinical data systems.
4. **Clinic or Organization Admins:** Teams responsible for privacy, deployment, access control, and compliance.

## Repository Structure Overview

| Directory / File | Description |
| :--- | :--- |
| **`pyproject.toml` & `uv.lock`** | Root uv workspace configuration and locked dependency graph. |
| **`.env.example`** | Template for local environment variables. |
| **`backend/`** | FastAPI backend, LangGraph agents, RAG services, data access, ingestion, and tests. |
| **`backend/app/api/`** | API routes such as health checks and future chat endpoints. |
| **`backend/app/agents/`** | LangGraph agent nodes, states, and graph definitions. |
| **`backend/app/services/`** | RAG, LLM provider, Qdrant, and other service logic. |
| **`backend/app/db/`** | Supabase/PostgreSQL integration and persistence logic. |
| **`backend/app/ingestion/`** | Document ingestion pipeline for clinical knowledge sources. |
| **`backend/data/`** | Raw and processed clinical documents; large files are ignored by Git. |
| **`frontend/`** | Streamlit frontend application. |
| **`docs/`** | SRDS, data-flow documentation, and agent architecture documentation. |
| **`_notes/`** | Project notes, setup history, and development logs. |

### Project Structure

```text
Mental-Health-Sovereign-Agentic-AI-Platform/
├── pyproject.toml              # Root uv workspace configuration
├── uv.lock                     # Locked dependencies
├── .python-version             # Python version
├── .env.example                # Environment variable template
├── Makefile                    # Common setup, run, and check commands
├── README.md                   # Project overview and quickstart
│
├── backend/
│   ├── pyproject.toml          # Backend dependencies
│   ├── app/
│   │   ├── api/                # FastAPI routes
│   │   ├── core/               # Settings and configuration
│   │   ├── agents/             # LangGraph workflows
│   │   ├── services/           # RAG, LLM, and external service logic
│   │   ├── schemas/            # Pydantic models
│   │   ├── db/                 # Database access
│   │   ├── ingestion/          # Knowledge ingestion pipeline
│   │   └── main.py             # FastAPI entrypoint
│   ├── data/
│   │   ├── raw/                # Raw clinical documents
│   │   └── processed/          # Processed document artifacts
│   └── tests/                  # Backend tests
│
├── frontend/
│   ├── pyproject.toml          # Frontend dependencies
│   └── main.py                 # Streamlit entrypoint
│
├── docs/
│   ├── SRDS.md                 # Requirements and design specification
│   ├── DFD.md                  # Data flow documentation
│   └── AGENT.md                # Agent architecture documentation
│
└── _notes/                     # Project notes and setup logs
```

## Documentation

- `docs/SRDS.md` — main requirements and design specification.
- `docs/DFD.md` — data flow documentation.
- `docs/AGENT.md` — agent architecture and workflow notes.
- `_notes/[1]setup_process.md` — project setup history and notes.

## Prerequisites

Before running the project locally, install or prepare:

- Python 3.11+
- `uv`
- API keys for the selected LLM provider, such as OpenAI or Gemini
- Qdrant connection settings
- Supabase/PostgreSQL connection settings
- Optional: Langfuse keys for tracing

## Hardware Requirements

For local development:

- **Minimum:** 8GB RAM, 2 CPU cores
- **Recommended:** 16GB RAM, 4 CPU cores
- **Supported OS:** Linux, macOS, or Windows with WSL

For production, requirements depend on deployment size, self-hosted model usage, database size, and traffic.

## Quickstart Guide

### Local Deployment (Development Mode with `uv Workspace`)

#### Installation Steps:

1. Clone the repository:
    ```bash
    git clone https://github.com/awun0105/Mental-Health-Sovereign-Agentic-AI-Platform.git
    cd Mental-Health-Sovereign-Agentic-AI-Platform
    ```

2. Install `uv`:
    ```bash
    # macOS/Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Windows PowerShell
    irm https://astral.sh/uv/install.ps1 | iex
    ```

3. Install the workspace dependencies:
    ```bash
    make install
    ```

4. Configure environment variables:
    ```bash
    cp .env.example .env
    # Edit .env with your LLM, Qdrant, Supabase/PostgreSQL, and Langfuse settings.
    ```

5. Run the backend:
    ```bash
    make dev-be
    ```

6. Run the frontend in another terminal:
    ```bash
    make dev-fe
    ```

7. Run quality checks before committing:
    ```bash
    make check
    uv run pre-commit run --all-files
    ```

## License

License information has not been finalized yet.

----

<p align="right">(<a href="#readme-top">back to top</a>)</p>
