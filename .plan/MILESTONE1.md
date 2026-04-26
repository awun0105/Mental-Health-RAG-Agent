# Khởi tạo Milestone 1 - Foundation cho project


## Mục tiêu
Hoàn thành Milestone 1 (Foundation) - tạo toàn bộ cấu trúc code cơ bản để project có thể chạy được (FastAPI backend + Streamlit frontend).

## Các bước thực hiện

### 1. Thêm LlamaIndex dependencies
Chạy tại root:
```bash
uv add --package backend llama-index llama-index-vector-stores-qdrant llama-index-embeddings-openai
```

### 2. Tạo cấu trúc thư mục backend
Tạo các thư mục và `__init__.py` files:
- `backend/app/__init__.py`
- `backend/app/api/__init__.py`
- `backend/app/core/__init__.py`
- `backend/app/agents/__init__.py`
- `backend/app/services/__init__.py`
- `backend/app/schemas/__init__.py`
- `backend/app/db/__init__.py`
- `backend/app/ingestion/__init__.py`
- `backend/tests/__init__.py`
- `backend/data/raw/.gitkeep`
- `backend/data/processed/.gitkeep`

### 3. Tạo `backend/app/core/config.py`
Pydantic Settings class đọc `.env`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Mental Health AI Platform"
    app_version: str = "0.1.0"
    debug: bool = False

    openai_api_key: str = ""
    qdrant_url: str = "http://localhost:6333"
    supabase_url: str = ""
    supabase_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### 4. Tạo `backend/app/main.py`
FastAPI application entrypoint:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router

app = FastAPI(
    title="Mental Health AI Platform",
    version="0.1.0",
    description="Privacy-first, human-in-the-loop AI system for mental health support",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1", tags=["health"])
```

### 5. Tạo `backend/app/api/health.py`
Health check endpoint:
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}
```

### 6. Tạo cấu trúc frontend
- `frontend/app.py`: Streamlit entrypoint cơ bản với page config và navigation placeholder
- `frontend/pages/.gitkeep`
- `frontend/components/.gitkeep`

`frontend/app.py`:
```python
import streamlit as st

st.set_page_config(
    page_title="Mental Health AI Platform",
    page_icon="🧠",
    layout="wide",
)

st.title("Mental Health AI Platform")
st.write("Welcome to the Mental Health Sovereign Agentic AI Platform")
```

### 7. Tạo `.env.example` ở root
```env
# Rename this file to .env and fill in your actual values
OPENAI_API_KEY=
QDRANT_URL=http://localhost:6333
SUPABASE_URL=
SUPABASE_KEY=
```

### 8. Sửa `README.md`
- Thay tất cả placeholder `[Project Name]`, `[Feature Name 6]`, `[Step 1 Name]`, etc. bằng nội dung thực tế dựa trên SRDS
- Sửa GitHub badge URLs từ NVIDIA repo sang `awun0105/Mental-Health-Sovereign-Agentic-AI-Platform`
- Điền Workflow steps dựa trên SRDS Section 10 (Patient Chat Flow, Session Closure Flow, Doctor Copilot Flow, Knowledge Ingestion Flow)
- Điền Prerequisites, Hardware Requirements, Target Audience với thông tin thực tế
- Điền Core Workflows table

### 9. Tạo `docs/DFD.md`
Tạo Data Flow Diagram document dựa trên SRDS Section 10 (Data Flow Design), bao gồm:
- Patient Chat Flow (Section 10.1)
- Session Closure and Clinical Profile Flow (Section 10.2)
- Doctor Conversational Copilot Flow (Section 10.3)
- Knowledge Ingestion Flow (Section 10.4)
Sử dụng Mermaid diagrams.

### 10. Cập nhật Makefile
Thêm command `make ingest` (placeholder cho future ingestion pipeline):
```makefile
ingest:
	cd backend && uv run python -m app.ingestion.cli
```

### 11. Verify
- Chạy `make install` (uv sync) để verify dependencies
- Chạy `make dev-be` để verify FastAPI starts successfully
- Chạy `make dev-fe` để verify Streamlit starts successfully
- Chạy `make check` để verify linting/type-checking passes
