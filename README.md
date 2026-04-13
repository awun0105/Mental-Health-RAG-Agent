<a id="readme-top"></a>

# Mental-Health-RAG-Agent

A mental health support system utilizing Retrieval-Augmented Generation (RAG) to combine the reasoning power of large language models (LLMs) with accurate medical data (like the DSM-5). The system employs a Multi-Agent architecture to ensure accuracy, safety, and personalization during consultations.

<div align="center">
  
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)

[![Docker](https://img.shields.io/badge/Docker-Required-blue.svg)](https://www.docker.com/)

[![GitHub Stars](https://img.shields.io/github/stars/NVIDIA-AI-Blueprints/retail-shopping-assistant?style=social)](https://github.com/NVIDIA-AI-Blueprints/retail-shopping-assistant/stargazers)

[![GitHub last commit](https://img.shields.io/github/last-commit/NVIDIA-AI-Blueprints/retail-shopping-assistant)](https://github.com/NVIDIA-AI-Blueprints/retail-shopping-assistant/commits)

</div>

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
This repository contains the source code and configuration for **Mental-Health-RAG-Agent**. It showcases how to build and deploy **a safe psychological consultation system** using **FastAPI, Streamlit, LangGraph, Qdrant (Vector DB), and Supabase**.

By utilizing this project, developers can **build complex AI conversation flows with long-term memory and deep document retrieval capabilities**, unlocking new application possibilities in **the Digital Healthcare domain**.

## Key Features

- **Multi-Agent Orchestration (LangGraph)** — Orchestrates specialized agents (e.g., Symptom Collection Agent, DSM-5 Retrieval Agent, Safety Check Agent).
- **Dual-Database Architecture** — Clear separation between the "Knowledge Library" (Qdrant Vector DB) and the "Patient Record/State" (Supabase PostgreSQL).
- **Decoupled Application** — Backend (FastAPI) and Frontend (Streamlit) operate independently, communicating via REST APIs.
- **Lightning-Fast Monorepo Setup** — Superfast management of the entire workspace and dependencies using `uv`, avoiding Dependency Hell.
- **Modular Ingestion Pipeline** — Independent RAG data ingestion script (Load -> Split -> Embed -> Qdrant), making it easy to update new documents.
- **[Feature Name 6, e.g., Deployment options]** — [Detailed description of the feature, e.g., Deployment assets for docker compose as well as helm deployment.]

## Use Case / Problem Description

The **[Project Name]** addresses the challenge of **[Describe the core problem, e.g., interacting with massive volumes of unstructured data]**. 

This solution can be applied to a multitude of use cases such as:
* **[Use Case 1, e.g., Smart space monitoring]**
* **[Use Case 2, e.g., Automated reporting]**
* **[Use Case 3, e.g., Anomaly detection]**

This is crucial for environments where **[Explain why this matters, e.g., quick and accurate analysis leads to better operational efficiency]**.


## Software Components

1. **Core AI / Agents**: LangGraph (State/Flow management), LangChain, and LLMs (such as OpenAI GPT-4o / Text-Embedding-3-small).
2. **Vector Database (Stateless)**: Qdrant, used for storing and performing Semantic Search on medical documents.
3. **Relational Database (Stateful)**: Supabase (PostgreSQL), used for storing user information, chat history, and acting as a Checkpointer for LangGraph.
4. **Backend API**: FastAPI provides high-speed internal communication endpoints.
5. **User Interface**: Streamlit builds the interactive Chat/Dashboard interface for end-users.

## Technical Diagram

The following image represents the architecture and workflow.

<p align="center">
  <img src="./docs/assets/arch_diagram.png" width="750">
</p>

## Workflow

The following is a step-by-step explanation of the workflow from the end-user perspective:

1. **[Step 1 Name, e.g., Data Ingestion]** — [Description of the step, e.g., Multimodal enterprise documents are ingested and processed by the extraction pipeline.]
2. **[Step 2 Name, e.g., User Query]** — [Description of the step, e.g., The user interacts with the system through the UI or APIs, submitting a request.]
3. **[Step 3 Name, e.g., Query Processing]** — [Description of the step, e.g., The query is processed by the backend service and converted into embeddings for semantic search.]
4. **[Step 4 Name, e.g., Retrieval]** — [Description of the step, e.g., The system matches the processed query against enterprise data stored in the vector database.]
5. **[Step 5 Name, e.g., Response Generation]** — [Description of the step, e.g., The selected context is passed into the inference model to generate a grounded, accurate response.]

## Core Workflows
We provide multiple reference workflows to demonstrate how individual components interact:

| Workflow Name | Description | Reference / Link |
|----------|-------------|------------------|
| **[Workflow 1: e.g., Basic Q&A]** | [Describe what it does, e.g., Retrieval and Q&A on short data clips] | [Link to doc/script] |
| **[Workflow 2: e.g., Real-Time Alerts]** | [Describe what it does, e.g., Continuous processing for anomaly detection] | [Link to doc/script] |
| **[Workflow 3]** | [Describe what it does] | [Link to doc/script] |


## Target Audience
This blueprint is designed with multiple configuration options. It is intended for:

1. **[Audience A, e.g., IT Engineers / System Admins]:** Professionals focused on deployment and maintenance. The repository offers easy-to-manage configurations (e.g., Docker Compose).
2. **[Audience B, e.g., GenAI Developers / ML Engineers]:** Experts who need to customize the pipelines, fine-tune models, or modify processing logic for specific proprietary datasets.


## Repository Structure Overview

| Directory / File | Description |
| :--- | :--- |
| **`Root Workspace/`** | **Global configurations for the `uv` monorepo.** |
| ├── `pyproject.toml` & `uv.lock` | Workspace configuration and dependency lock files for the entire project. |
| ├── `.env` & `.env.example` | Environment variables (API keys, DB URLs). `.env` is secure and ignored by Git. |
| **`backend/`** | **Core System: FastAPI application, LangGraph workflows, and RAG services.** |
| ├── `app/api/` | RESTful API endpoints (e.g., `/chat`, `/health-scores`) receiving frontend requests. |
| ├── `app/agents/` | Multi-Agent logic using LangGraph (Agent Nodes, State definitions, Graph compilation). |
| ├── `app/services/` | Stateless AI services: Qdrant vector database search, OpenAI model integrations. |
| ├── `app/db/` | Stateful database connections: Supabase/PostgreSQL for user accounts and chat history. |
| ├── `app/ingestion/` | Standalone data pipelines (e.g., scripts to parse DSM-5 PDFs, embed, and upload to Qdrant). |
| ├── `app/schemas/` | Pydantic models for strict input/output data validation. |
| ├── `app/core/` | Application configurations, global constants, and security settings (CORS). |
| ├── `data/` | Stores static medical documents (`raw/` for original PDFs, `processed/` for cleaned data). |
| └── `tests/` | Automated testing suite utilizing `pytest` and `pytest-asyncio` to evaluate RAG accuracy. |
| **`frontend/`** | **User Interface: Interactive Streamlit web application.** |
| ├── `app.py` | Main entry point and routing for the Streamlit dashboard. |
| ├── `pages/` | Individual application features (e.g., the Chat interface, Health tracking dashboard). |
| └── `components/` | Reusable UI widgets and custom visual elements (e.g., chat bubbles, metric cards). |
| **`docs/`** | **Official Project Documentation (System Blueprints).** |
| ├── `SRDS.md` | Software Requirements and Design Specification. |
| └── `DFD.md` | Data Flow Diagrams mapping the exact movement of data from User to Backend. |
| **`notebooks/`** | **R&D Environment:** Jupyter notebooks for experimenting with chunking strategies and prompts. |

### Project Structure

```text
Mental-Health-RAG-Agent/
├── pyproject.toml           # Root Workspace configuration for uv, linking backend and frontend
├── uv.lock                  # Common library version lock file for the entire project
├── .python-version          # Python version automatically managed by uv
├── .env                     # Contains actual API Keys (Secure - ignored by Git)
├── .env.example             # Template file containing API Key names for public reference
├── .gitignore               # Config to ignore junk, hidden, and environment files
├── README.md                # Project introduction and setup guide
│
├── backend/                 # ================= [ CORE SYSTEM ] =================
│   ├── pyproject.toml       # Backend-specific library management (FastAPI, LangGraph...)
│   ├── app/                 # Main backend source code directory
│   │   ├── api/             # Defines RESTful endpoints (e.g., /chat, /history)
│   │   ├── core/            # Contains configurations, constants, and security (CORS)
│   │   ├── agents/          # Contains LangGraph logic (Nodes, State, Graph)
│   │   ├── services/        # Handles RAG processing, OpenAI model calls, Qdrant queries
│   │   ├── schemas/         # Defines Pydantic models (Input/output data validation)
│   │   ├── db/              # Database connection to Supabase (PostgreSQL)
│   │   ├── ingestion/       # Contains one-way data ingestion pipelines
│   │   │   └── load_dsm5.py # Reads PDF files, embeds, and uploads to Qdrant
│   │   └── main.py          # Main entry point to run the FastAPI application
│   ├── data/                # Stores static medical data
│   │   ├── raw/             # Contains raw document files (e.g., dsm5_sample.pdf)
│   │   └── processed/       # Contains data after preprocessing
│   └── tests/               # Automated testing suite (pytest & pytest-asyncio)
│
├── frontend/                # ================= [ USER INTERFACE ] =================
│   ├── pyproject.toml       # Frontend-specific library management (Streamlit, Plotly...)
│   ├── app.py               # Main entry point for the Streamlit UI
│   ├── pages/               # Application feature pages (Chat, Dashboard)
│   └── components/          # Reusable UI components
│
├── docs/                    # ================= [ PROJECT DOCUMENTATION ] ===============
│   ├── SRDS.md               # Software Requirements and Design Specification
│   └── DFD.md               # Data Flow Diagram
│
└── notebooks/               # ================= [ R&D (RESEARCH) ] =============
│   └── ...                  # Jupyter Notebook testing area (Test prompts, chunking)


## Documentation

For detailed instructions, API references, and advanced configurations, please refer to the [Official Documentation](#link-to-docs) or the `docs/` folder.

## Prerequisites

Before deploying **[Project Name]**, ensure you have the following:

- **[Requirement 1, e.g., Valid API Keys from Provider X]**
- **[Requirement 2, e.g., Specific Developer License]**
- **[Requirement 3, e.g., Access to specific cloud resources]**

## Hardware Requirements

_The platform requirements can vary depending on the deployment topology._

- **Minimum Configuration:** [e.g., 16GB RAM, 4 CPU cores]
- **Recommended Configuration:** [e.g., 32GB RAM, Dedicated GPU with 16GB VRAM]
- **Supported OS:** [e.g., Ubuntu 22.04 / Windows 11 / macOS]

## Quickstart Guide

### Local Deployment (Development Mode with `uv Workspace`)
**Ideal for:** Superfast local development without needing to build Docker, with centralized package management.

#### Installation Steps:

1. Clone the repository:
    ```bash
    git clone [https://github.com/your_username/AI-Mental-Health-Agent.git](https://github.com/your_username/AI-Mental-Health-Agent.git)
    cd AI-Mental-Health-Agent
    ```

2. Install `uv` (Superfast package manager):
    ```bash
    # MacOS/Linux
    curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
    
    # Windows (Powershell)
    irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex
    ```

3. Install the entire environment:
    ```bash
    uv sync
    ```

4. Configure environment variables:
    ```bash
    cp .env.example .env
    # Edit .env with your credentials (OPENAI_API_KEY, QDRANT_URL, SUPABASE_URL, etc.)
    ```

5. Launch the system:
    * **Start Backend:** Open a new terminal in the root directory and type:
      ```bash
      cd backend && uv run uvicorn app.main:app --reload
      ```
    * **Start Frontend:** Open a second terminal in the root directory and type:
      ```bash
      cd frontend && uv run streamlit run app.py
      ```


## License

Distributed under the **[License Name, e.g., MIT / Apache 2.0]** License. See `LICENSE` for more information.

----

<p align="right">(<a href="#readme-top">back to top</a>)</p>
