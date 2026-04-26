# [1] SETUP DỰ ÁN AI MENTAL HEALTH AGENTS

Dưới đây là bản tóm tắt toàn bộ quy trình setup và cấu trúc dự án **AI-Mental-Health-Agent** đã được **cập nhật chuẩn xác nhất**.

**Mô tả dự án:** Hệ thống hỗ trợ sức khỏe tâm thần sử dụng RAG và Multi-Agent.
**Kiến trúc:** Modular Monolith (tách biệt Frontend/Backend) sử dụng uv Workspace.

text

## PHẦN 1: CẤU TRÚC THƯ MỤC

``` text
AI-Mental-Health-Agent/
├── _notes/                  # SOPs, ghi chú cá nhân, tài liệu nháp (Git bỏ qua)
│   └── [1]Setup_process.md       # (Nơi lưu file này)
├── docs/                    # ================= [ TÀI LIỆU DỰ ÁN ] ===============
│   ├── SRS.md               # Software Requirements and Design Specification (SRDS)
│   └── DFD.md               # Data Flow Diagrams (Luồng dữ liệu)
│
├── notebooks/               # Thử nghiệm Jupyter Notebook (Test prompt, R&D)
│
├── pyproject.toml           # (Gốc) Cấu hình Workspace, Linter (Ruff), Type Checker (Mypy)
├── uv.lock                  # Lock file version thư viện cho toàn dự án
├── .python-version          # Version Python do uv tự động quản lý
├── .env                     # Chứa API Keys thật (Git bỏ qua)
├── .env.example             # Chứa cấu trúc API Keys mẫu
├── .gitignore               # Cấu hình bỏ qua file rác, file ẩn
├── .pre-commit-config.yaml  # Cấu hình "Người gác cổng" Git
├── Makefile                 # "Bảng điều khiển" gom các lệnh chạy dự án
├── README.md                # Hướng dẫn chạy dự án cho người mới
│
├── backend/                 # ================= [ LÕI HỆ THỐNG ] =================
│   ├── pyproject.toml       # Thư viện riêng cho Backend
│   ├── app/
│   │   ├── api/             # Routes (v1/endpoints) - Nhận request từ Frontend
│   │   ├── core/            # Config, Security, Constants (CORS, JWT)
│   │   ├── agents/          # LangGraph Nodes, States & Graphs
│   │   ├── services/        # Logic stateless: RAG, OpenAI, Qdrant
│   │   ├── schemas/         # Pydantic models (Request/Response validation)
│   │   ├── db/              # Logic stateful: Kết nối Supabase/Postgres
│   │   ├── ingestion/       # Pipeline ETL: Load -> Chunk -> Embed -> Qdrant
│   │   └── main.py          # Điểm khởi chạy FastAPI
│   ├── data/
│   │   ├── raw/             # PDF gốc (vd: DSM-5)
│   │   └── processed/       # Metadata/file đã xử lý
│   └── tests/               # Bộ câu hỏi test tự động (Pytest)
│
└── frontend/                # ================= [ GIAO DIỆN UI ] =================
    ├── pyproject.toml       # Thư viện riêng cho Frontend
    ├── app.py               # Điểm khởi chạy Streamlit
    ├── pages/               # Các trang con (vd: chat_bot.py)
    └── components/          # Thành phần UI dùng chung
```

---

## PHẦN 2: QUY TRÌNH SETUP

### GIAI ĐOẠN 1: KHỞI TẠO KHUNG XƯƠNG DỰ ÁN (SCAFFOLDING)

Gồm: uv init, tạo thư mục con (Backend/Frontend), tạo sẵn các thư mục rỗng.

Giai đoạn này tập trung vào việc tạo ra các thư mục vật lý (folders) và khai báo định danh ban đầu cho dự án. Chúng ta sẽ thiết lập một nền móng **Monorepo** (Kho chứa mã nguồn nguyên khối), nơi cả Frontend và Backend "sống chung" dưới một mái nhà nhưng có không gian riêng biệt.

**Mục đích (Tại sao lại setup thế này?)**

* **Tại sao dùng `uv` thay vì `pip/virtualenv`?** `uv` được viết bằng Rust, tốc độ cài đặt môi trường nhanh hơn gấp 10-100 lần. Quan trọng nhất, nó hỗ trợ tính năng **Workspace**, cho phép Frontend và Backend chia sẻ chung một môi trường ảo (virtual environment) nhưng vẫn không bị lẫn lộn thư viện của nhau.
* **Tại sao khởi tạo với cờ `--app`?** Python thường mặc định bạn đang viết một "Thư viện" (để tải lên PyPI). Việc thêm `--app` khẳng định đây là một "Ứng dụng web" chạy trực tiếp, giúp bỏ qua các bước đóng gói thừa thãi.
* **Tại sao không dùng thư mục `src/` cho Backend?** Chuẩn mực của cộng đồng FastAPI là đặt trực tiếp code vào thư mục `app/` để các lệnh import trở nên tự nhiên và ngắn gọn (vd: `from app.services import...`) thay vì phải gõ dài dòng `from src.app.services...`.

---

**🛠 Các bước thực hiện chi tiết**

#### Bước 1: Khởi tạo Root (Thư mục gốc)

*Báo cho hệ thống biết đây là điểm bắt đầu của một dự án lớn.*

1. Mở Terminal, đi đến thư mục rỗng nơi bạn muốn chứa dự án (ví dụ: `AI-Mental-Health-Agent/`).
2. Chạy lệnh khởi tạo:

   ```bash
   uv init
   ```

3. Lệnh trên sẽ tự động sinh ra một số file mẫu. Hãy xóa file `hello.py` thừa thãi đi:

   ```bash
   rm hello.py
   ```

#### Bước 2: Khởi tạo Sub-projects (Backend và Frontend)

*Tạo 2 phân khu độc lập cho Giao diện và Lõi xử lý.*

1. Đứng tại thư mục gốc, chạy 2 lệnh sau để tạo thư mục ứng dụng:

   ```bash
   uv init --app backend
   uv init --app frontend
   ```

2. Tương tự như bước 1, `uv` sẽ sinh ra các file `hello.py` bên trong 2 thư mục này. Hãy dọn dẹp chúng:

   ```bash
   rm backend/hello.py frontend/hello.py
   ```

#### Bước 3: Dựng sẵn các thư mục nội bộ (Scaffolding)

*Tạo sẵn các "ngăn kéo" chuẩn mực để khi bắt tay vào code, bạn không phải suy nghĩ xem nên đặt file ở đâu.*

Đứng tại **thư mục gốc**, copy và chạy lần lượt các cụm lệnh sau:

**1. Dựng khung cho Backend (Lõi hệ thống):**

```bash
mkdir -p backend/app/api backend/app/core backend/app/agents backend/app/services backend/app/schemas backend/app/db backend/app/ingestion backend/tests
```

*(Giải thích nhanh các "ngăn kéo" của Backend):*

* `api/`: Nhận request từ người dùng (Routes).
* `core/`: Chứa cấu hình bảo mật, biến môi trường, JWT.
* `agents/`: Nơi chứa bộ não LangGraph (Nodes, Edges, State).
* `services/`: Nơi làm việc với bên thứ 3 (OpenAI, tra cứu Qdrant).
* `db/`: Kết nối Database chính (Supabase/PostgreSQL) lưu lịch sử.
* `schemas/`: Định nghĩa kiểu dữ liệu vào/ra (Pydantic).
* `ingestion/`: Các script chạy ngầm để nạp PDF vào Vector DB.
* `tests/`: Nơi chứa code kiểm thử tự động (Pytest).

**2. Dựng khung chứa Data cho RAG:**

```bash
mkdir -p backend/data/raw backend/data/processed
```

*(Lưu ý: `raw` chứa PDF gốc như DSM-5, `processed` chứa dữ liệu đã băm nhỏ).*

**3. Dựng khung cho Frontend:**

```bash
mkdir -p frontend/pages frontend/components
```

**4. Dựng khung Tài liệu & Nghiên cứu (Nằm ở Root):**

```bash
mkdir -p docs notebooks _notes
```

---
**✅ Kết quả nghiệm thu Giai đoạn 1:**
Lúc này, nếu bạn mở cây thư mục trong VS Code, bạn sẽ thấy một bộ khung khổng lồ, rõ ràng và ngăn nắp. Toàn bộ nền móng vật lý đã hoàn thiện!

---

### GIAI ĐOẠN 2: KHAI BÁO CẤU HÌNH TRUNG TÂM (`pyproject.toml`)

Gồm: Xử lý dứt điểm 3 file pyproject.toml (ở Root, Backend, Frontend). Set up các rule cho Ruff và Mypy luôn tại đây.

Giai đoạn này thiết lập "bộ não" điều phối toàn bộ dự án. Chúng ta sẽ cấu hình 3 file `pyproject.toml` (nằm ở Root, Backend và Frontend) để định nghĩa không gian làm việc (Workspace), quy tắc kiểm duyệt code (Linter/Formatter), và khai báo tính chất của từng ứng dụng con.

**💡 Mục đích (Tại sao lại setup thế này?)**

* **Tại sao có đến 3 file `pyproject.toml`?** * File ở **Root** quản lý cấu hình chung (Workspace) và các công cụ dùng cho toàn dự án (Ruff, Mypy).
  * File ở **Backend/Frontend** chỉ quản lý danh sách thư viện của riêng chúng, giúp tách biệt hoàn toàn "đồ đạc" của hai bên.
* **Tại sao phải thêm `package = false`?** Theo mặc định, các công cụ Python cho rằng bạn đang viết một thư viện để tải lên mạng (như `numpy` hay `pandas`) và sẽ cố gắng đóng gói (build) nó. Dự án của chúng ta là ứng dụng Web chạy trực tiếp (Web API, UI), nên phải tắt tính năng đóng gói này đi để tránh lỗi `Failed to build`.
* **Ruff và Mypy là gì?** * **Ruff:** Công cụ viết bằng Rust, tốc độ siêu nhanh. Nó thay thế cùng lúc 3 công cụ cũ (Flake8 để tìm lỗi, Black để format code đẹp, Isort để sắp xếp thư viện).
  * **Mypy:** Công cụ ép kiểu dữ liệu (Type Checker). Vì Python rất dễ dãi trong việc truyền sai kiểu dữ liệu, Mypy sẽ đóng vai trò "bắt lỗi từ trong trứng" trước khi code làm sập server.
* **Tại sao cấu hình `pytest-asyncio` ở backend?** FastAPI và LangGraph sử dụng toàn bộ là xử lý bất đồng bộ (`async def`). Thư viện Test mặc định của Python không hiểu `async`, nên ta phải cấu hình thêm module này.

---

**🛠 Các bước thực hiện chi tiết**

#### Bước 1: Cấu hình thư mục Gốc (Root)

*Nhiệm vụ: Liên kết Workspace và thiết lập luật chơi chung cho code (Ruff, Mypy).*

1. Mở file `pyproject.toml` nằm ở **ngoài cùng (thư mục gốc)**.
2. Xóa toàn bộ nội dung mặc định và dán đoạn cấu hình chuẩn mực dưới đây vào:

```toml
[project]
name = "mental-health-rag-agent"
version = "0.1.0"
description = "Hệ thống hỗ trợ sức khỏe tâm thần sử dụng RAG và Multi-Agent"
readme = "README.md"
requires-python = ">=3.11"
dependencies = []

# 1. KHAI BÁO WORKSPACE: Liên kết 2 thư mục con thành một thể thống nhất
[tool.uv.workspace]
members = ["backend", "frontend"]

# 2. CẤU HÌNH RUFF: Luật format và dọn dẹp code
[tool.ruff]
line-length = 100
target-version = "py311"
extend-exclude = [".venv", "__pycache__", "docs", "data"]

[tool.ruff.lint]
select = ["E", "F", "I"] # E: pycodestyle (Lỗi format), F: Pyflakes (Lỗi logic), I: isort (Sắp xếp import)

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

# 3. CẤU HÌNH MYPY: Kiểm tra chặt chẽ kiểu dữ liệu (Type Hint)
[tool.mypy]
python_version = "3.11"
strict = true                   # Bật chế độ kiểm tra nghiêm ngặt nhất
ignore_missing_imports = true   # Bỏ qua lỗi nếu các thư viện bên ngoài không có type hints
warn_return_any = true          # Cảnh báo nếu hàm không khai báo kiểu trả về
warn_unused_ignores = true      # Cảnh báo nếu dùng # type: ignore thừa thãi
exclude = [
    "tests",
    ".venv",
]
```

#### Bước 2: Cấu hình ứng dụng Backend

*Nhiệm vụ: Chặn đóng gói thư viện và setup luật test bất đồng bộ.*

1. Mở file `backend/pyproject.toml`.
2. Giữ nguyên phần `[project]` mặc định ở đầu file, cuộn xuống **cuối file** và dán thêm đoạn sau:

```toml
# BẮT BUỘC: Khai báo đây là Web App chạy trực tiếp, không phải Package để build
[tool.uv]
package = false

# Cấu hình Pytest để hỗ trợ chạy test các hàm async của FastAPI / LangGraph
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

#### Bước 3: Cấu hình ứng dụng Frontend

*Nhiệm vụ: Chặn đóng gói thư viện.*

1. Mở file `frontend/pyproject.toml`.
2. Giữ nguyên phần `[project]` mặc định ở đầu file, cuộn xuống **cuối file** và dán thêm đoạn sau:

```toml
# BẮT BUỘC: Khai báo đây là Web App chạy trực tiếp, không phải Package để build
[tool.uv]
package = false
```

---
**✅ Kết quả nghiệm thu Giai đoạn 2:**
Bạn đã thiết lập xong hệ thống "đường ống" cấu hình. Các công cụ chất lượng code đã biết phải áp dụng luật gì, và `uv` đã biết cách cư xử đúng đắn với Backend và Frontend. Từ giờ trở đi, chúng ta mới bắt đầu cài đặt thư viện vào dự án.

---

### GIAI ĐOẠN 3: CÀI ĐẶT THƯ VIỆN (DEPENDENCIES & VIRTUAL ENVIRONMENT)

Gồm: Gom toàn bộ các lệnh uv add (cho Core, cho Backend, cho Frontend, cho Dev tools) vào một chỗ để chạy một lần cho xong.

Giai đoạn này giống như việc "bơm nguyên liệu" vào các căn phòng đã xây. Chúng ta sẽ sử dụng `uv` để tải về các thư viện cần thiết cho Backend (FastAPI, AI), Frontend (Streamlit) và các công cụ hỗ trợ Dev (Linting, Testing).

**Mục đích (Tại sao lại setup thế này?)**

* **Tại sao không dùng lệnh `pip install`?** Trong kiến trúc này, chúng ta đã bỏ file `requirements.txt`. Khi bạn dùng `uv add`, công cụ này sẽ tự động làm 3 việc cùng lúc: tải thư viện siêu tốc, tự động ghi tên thư viện vào file `pyproject.toml` tương ứng, và quan trọng nhất là cập nhật file `uv.lock` để chốt chặt phiên bản.
* **Tại sao phải dùng cờ `--package`?** Vì chúng ta đang đứng ở "phòng khách" (thư mục gốc), cờ `--package backend` sẽ báo cho `uv` biết hãy ném gói hàng này vào đúng "phòng ngủ" của Backend. Nếu không có cờ này, thư viện sẽ bị cài lộn xộn ở Root.
* **Tại sao phải có cờ `--dev`?** Có những thư viện chỉ dùng trong lúc gõ code (như Pytest để test, Ruff để làm đẹp code). Khi đưa sản phẩm lên server thật (Production), chúng ta không cần chúng. Cờ `--dev` giúp tách biệt các thư viện này ra, làm cho ứng dụng khi deploy nhẹ nhàng và bảo mật hơn.
* **Sự kì diệu của `uv.lock`:** Sau khi chạy các lệnh dưới đây, file `uv.lock` sẽ xuất hiện. Nó ghi lại chính xác mã băm (hash) của hàng trăm thư viện phụ thuộc. Dù 5 năm sau bạn cài lại dự án, nó vẫn chạy y hệt như ngày hôm nay, chấm dứt hoàn toàn nỗi đau "Dependency Hell" (Lỗi xung đột phiên bản ngầm).

---

**🛠 Các bước thực hiện chi tiết**

**⚠️ LƯU Ý QUAN TRỌNG:** Trong toàn bộ Giai đoạn này, bạn **luôn phải đứng ở thư mục gốc (Root)** của dự án trên Terminal. Không `cd` vào bất kỳ thư mục con nào.

#### Bước 1: Cài đặt công cụ Dev dùng chung (Toàn cục)

*Nhiệm vụ: Cài đặt các "người gác cổng" (Ruff, Mypy, Pre-commit) để soi lỗi cho cả Backend lẫn Frontend.*

Chạy lệnh sau:

```bash
uv add --dev ruff mypy pre-commit
```

*(Giải thích: Các công cụ này sẽ được ghi vào file `pyproject.toml` ở thư mục Root, nằm trong mục `[dependency-groups] dev`).*

#### Bước 2: Cài đặt thư viện Lõi cho Backend

*Nhiệm vụ: Trang bị vũ khí hạng nặng cho AI và API.*

Chạy lệnh sau (có thể copy/paste toàn bộ một lần):

```bash
uv add --package backend fastapi uvicorn langgraph langchain-openai qdrant-client pydantic-settings
```

*(Giải thích các gói):*

* `fastapi`, `uvicorn`: Xây dựng và chạy máy chủ Web API.
* `langgraph`: Khung sườn (framework) xây dựng các Agent có khả năng suy luận đa bước.
* `langchain-openai`: Giao tiếp với API của OpenAI (dùng mô hình GPT-4o, text-embedding).
* `qdrant-client`: Kết nối với cơ sở dữ liệu Vector (Qdrant) để thực hiện RAG.
* `pydantic-settings`: Đọc file `.env` và quản lý cấu hình một cách an toàn, chuẩn xác.

#### Bước 3: Cài đặt công cụ Kiểm thử (Test) cho Backend

*Nhiệm vụ: Trang bị Pytest để tự động hóa việc test API và đánh giá độ ảo giác của AI.*

Chạy lệnh sau:

```bash
uv add --dev --package backend pytest pytest-asyncio
```

*(Giải thích: Phải có cả `--dev` vì chỉ dùng lúc test, và `--package backend` vì chỉ test phần logic lõi. `pytest-asyncio` giúp test các hàm `async def` của FastAPI mượt mà).*

#### Bước 4: Cài đặt thư viện cho Frontend

*Nhiệm vụ: Trang bị công cụ dựng giao diện và vẽ biểu đồ.*

Chạy lệnh sau:

```bash
uv add --package frontend streamlit requests plotly
```

*(Giải thích: `streamlit` là framework giao diện siêu tốc, `requests` dùng để gọi API từ Backend, `plotly` để vẽ biểu đồ tâm lý học nếu cần).*

#### Bước 5: Chốt hạ và Đồng bộ hóa (Sync)

*Nhiệm vụ: Ra lệnh cho `uv` rà soát lại toàn bộ dự án, giải quyết các xung đột (nếu có), và sinh ra môi trường ảo `.venv` chính thức.*

Chạy lệnh chốt hạ:

```bash
uv sync
```

---
**✅ Kết quả nghiệm thu Giai đoạn 3:**

1. Mở file `backend/pyproject.toml` và `frontend/pyproject.toml`, bạn sẽ thấy danh sách `dependencies` đã được tự động điền đầy đủ.
2. Tại thư mục gốc, một thư mục ẩn tên là `.venv/` đã xuất hiện. Đây chính là "bộ não" thực thi mã Python của toàn bộ dự án.
3. File `uv.lock` cũng đã xuất hiện ở thư mục gốc, khóa cứng mọi phiên bản thư viện.

---

### GIAI ĐOẠN 4: THIẾT LẬP MÔI TRƯỜNG & "KHÓA AN TOÀN" GIT

Gồm: Tạo .env, .gitignore, và setup pre-commit (người gác cổng).

Giai đoạn này thiết lập các ranh giới bảo mật và chất lượng cho dự án. Chúng ta sẽ tạo các file ẩn để bảo vệ API Keys (`.env`), dọn dẹp kho lưu trữ (`.gitignore`), và thiết lập một "người gác cổng" tự động (`pre-commit`) để ép buộc toàn bộ code phải sạch sẽ, không có lỗi trước khi được lưu vào lịch sử Git.

**Mục đích (Tại sao lại setup thế này?)**

* **Tại sao cần `.env` và `.env.example`?** Trong các dự án AI, bạn sẽ sử dụng rất nhiều API Keys (như OpenAI) hoặc mật khẩu Database (Supabase). Tuyệt đối **không bao giờ** viết thẳng (hardcode) các khóa này vào trong file code Python. Chúng ta lưu chúng ở file `.env` (file này chỉ tồn tại trên máy tính của bạn). Còn file `.env.example` là một bản mẫu để trống giá trị, giúp người mới vào team biết họ cần chuẩn bị những API Keys nào.
* **Tại sao cần `.gitignore` chuẩn mực?** Khi bạn chạy code, Python và các công cụ (Ruff, Mypy, Pytest) sinh ra hàng ngàn file rác bộ nhớ đệm (cache). Nếu bạn đẩy cục rác này lên GitHub, dự án sẽ phình to, chậm chạp và làm lộ thông tin hệ thống. File `.gitignore` chính là danh sách "cấm vận" đối với Git.
* **Pre-commit Hooks là gì?** Ở Giai đoạn 2, chúng ta đã khai báo luật cho Ruff (làm đẹp code) và Mypy (soi lỗi logic). Nhưng nếu bạn... quên chạy chúng thì sao? `pre-commit` chính là giải pháp. Nó tự động kích hoạt Ruff và Mypy ngay khoảnh khắc bạn gõ lệnh `git commit`. Nếu code có lỗi, nó sẽ từ chối không cho bạn commit. Điều này giúp dự án **chống lại sự lười biếng hay đãng trí** của con người.

---

**🛠 Các bước thực hiện chi tiết**

**⚠️ LƯU Ý:** Đảm bảo bạn đang đứng ở **thư mục gốc (Root)** của dự án.

#### Bước 1: Thiết lập danh sách cấm vận Git (`.gitignore`)

*Nhiệm vụ: Chặn rác hệ thống, chặn đẩy dữ liệu quá nặng và chặn rò rỉ bảo mật.*

1. Tạo một file tên là `.gitignore` ở thư mục gốc.
2. Dán nội dung tối ưu sau vào file:

```text
# ==========================================
# 1. Môi trường & Biến bảo mật (SỐNG CÒN)
# ==========================================
.venv/
.env
.env.*
!.env.example

# ==========================================
# 2. Bộ nhớ đệm (Cache) của Python & Công cụ
# ==========================================
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
htmlcov/

# ==========================================
# 3. Notebooks (Dành cho Data Science)
# ==========================================
.ipynb_checkpoints/

# ==========================================
# 4. Thư mục cá nhân & Tài liệu nháp
# ==========================================
_notes/
*.md.backup

# ==========================================
# 5. Hệ điều hành & IDE (Code Editor)
# ==========================================
.DS_Store
Thumbs.db
.vscode/
.idea/
.cursorignore
.cursorindexingignore

# ==========================================
# 6. Dữ liệu (Tránh đẩy file PDF, DB nặng lên Git)
# ==========================================
backend/data/raw/*
backend/data/processed/*
!backend/data/raw/.gitkeep
!backend/data/processed/.gitkeep
```

*(Mẹo nhỏ ở phần 6: Git không cho phép đẩy thư mục rỗng. Khai báo trên giúp chặn đẩy mọi file PDF nặng lên Git, nhưng vẫn ép Git tạo sẵn thư mục `raw` và `processed` bằng cách cho phép ngoại lệ file rỗng `.gitkeep`).*

**Hành động phụ:** Hãy tạo ngay 2 file trống có tên `.gitkeep` và đặt chúng vào trong thư mục `backend/data/raw/` và `backend/data/processed/`.

#### Bước 2: Quản lý Biến môi trường (Mật khẩu & API)

*Nhiệm vụ: Tạo nơi an toàn để chứa cấu hình.*

1. Tạo file `.env` ở thư mục gốc (Nhắc lại: File này đã bị Git chặn ở Bước 1) và dán:

```env
OPENAI_API_KEY=sk-your-real-api-key-here
QDRANT_URL=http://localhost:6333
SUPABASE_URL=your-real-supabase-url
SUPABASE_KEY=your-real-supabase-key
```

1. Tạo file `.env.example` ở thư mục gốc (File này sẽ được đẩy lên Git làm mẫu) và dán:

```env
# Đổi tên file này thành .env và điền các giá trị thực tế của bạn
OPENAI_API_KEY=
QDRANT_URL=http://localhost:6333
SUPABASE_URL=
SUPABASE_KEY=
```

#### Bước 3: Thiết lập "Người gác cổng" (`pre-commit`)

*Nhiệm vụ: Tự động hóa việc kiểm duyệt code trước khi lưu vào kho Git.*

1. Tạo file tên là `.pre-commit-config.yaml` ở thư mục gốc.
2. Dán cấu hình sau vào file:

```yaml
# File cấu hình khóa an toàn trước khi git commit
repos:
  # 1. Các kiểm tra cơ bản của Git
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace         # Tự động xóa dấu cách thừa ở cuối dòng
      - id: end-of-file-fixer           # Đảm bảo file luôn kết thúc bằng 1 dòng trống
      - id: check-yaml                  # Báo lỗi nếu bạn viết sai cú pháp YAML
      - id: check-added-large-files     # Chặn đứng việc lỡ tay commit file data quá lớn

  # 2. Sử dụng uv để chạy các công cụ cục bộ (Nhanh hơn gấp 10 lần)
  - repo: local
    hooks:
      # Kiểm tra và tự động fix format code
      - id: ruff-check
        name: Ruff Linter
        entry: uv run ruff check --fix
        language: system
        types_or: [python, pyi]
        require_serial: true

      # Chuẩn hóa cách lề, ngoặc kép
      - id: ruff-format
        name: Ruff Formatter
        entry: uv run ruff format
        language: system
        types_or: [python, pyi]
        require_serial: true

      # Bắt lỗi truyền sai kiểu dữ liệu
      - id: mypy
        name: Mypy Type Checker
        entry: uv run mypy .
        language: system
        types_or: [python, pyi]
        pass_filenames: false
        require_serial: true
```

1. **Cài đặt Hook vào Git:**
Tại Terminal (đứng ở thư mục gốc), chạy lệnh sau để gắn thiết lập này vào hệ thống Git của dự án:

```bash
uv run pre-commit install
```

*(Nếu thành công, bạn sẽ thấy dòng chữ: `pre-commit installed at .git/hooks/pre-commit`)*.

---
**✅ Kết quả nghiệm thu Giai đoạn 4:**
Lúc này, toàn bộ tài sản trí tuệ và bảo mật của dự án đã được an toàn. Bất kỳ ai vào dự án code cẩu thả, quên format, hay cố tình đẩy file rác lên mạng đều sẽ bị chặn đứng một cách tàn nhẫn nhưng cực kỳ hiệu quả bởi hệ thống tự động này.

---

### GIAI ĐOẠN 5: TỰ ĐỘNG HÓA LỆNH (MAKEFILE) & NGHIỆM THU

Gồm: Tạo Makefile, viết README.md, chạy uv sync và test thử.

Đây là bước "đóng gói" trải nghiệm phát triển (Developer Experience - DX). Chúng ta sẽ tạo ra một "bảng điều khiển" (`Makefile`) để gom tất cả các câu lệnh dài dòng thành những phím tắt siêu ngắn. Cuối cùng, chúng ta viết tài liệu hướng dẫn (`README.md`) để đảm bảo dự án chạy trơn tru trên mọi hệ điều hành (Windows, macOS, Linux) và tiến hành chạy thử nghiệm thu.

**Mục đích (Tại sao lại setup thế này?)**

* **Tại sao phải dùng `Makefile`?** Để giảm tải nhận thức (Cognitive Load). Thay vì mỗi ngày mở máy lên bạn phải nhớ và gõ dòng lệnh `cd backend && uv run uvicorn app.main:app --reload`, bạn chỉ cần gõ `make dev-be`. Nó giúp chuẩn hóa thao tác, mọi thành viên trong team tương lai đều chạy code theo đúng một cách duy nhất.
* **Tại sao phải viết `README.md` phân chia hệ điều hành?** Mặc định, lệnh `make` chạy rất mượt trên Linux và macOS, nhưng lại thường xuyên báo lỗi trên Windows thuần (PowerShell/CMD). Việc viết README rõ ràng giúp dự án của bạn trở nên chuyên nghiệp, không "bỏ rơi" các lập trình viên dùng Windows bằng cách cung cấp cho họ các lệnh `uv` gốc để chạy trực tiếp.
* **Tại sao lại nghiệm thu ở bước này?** Trải qua 4 giai đoạn với hàng loạt cấu hình phức tạp, đây là lúc chúng ta kích hoạt toàn bộ hệ thống để đảm bảo mọi "bánh răng" (Ruff, Mypy, FastAPI, Streamlit, Pre-commit) đều khớp vào nhau hoàn hảo.

---

**🛠 Các bước thực hiện chi tiết**

**⚠️ LƯU Ý:** Đảm bảo bạn đang đứng ở **thư mục gốc (Root)** của dự án.

#### Bước 1: Tạo "Bảng điều khiển" (`Makefile`)

*Nhiệm vụ: Gom nhóm các câu lệnh phức tạp thành các phím tắt.*

1. Tạo một file tên là `Makefile` (không có đuôi mở rộng như .txt hay .md) ở thư mục gốc.
2. Dán đoạn code sau vào file. **(QUAN TRỌNG: Khoảng trống trước các lệnh như `uv sync` BẮT BUỘC phải là phím `TAB`, tuyệt đối không dùng dấu cách/Space, nếu không Makefile sẽ báo lỗi).**

```makefile
# ==============================================================================
# BẢNG ĐIỀU KHIỂN DỰ ÁN (MAKEFILE)
# Lưu ý: Bắt buộc dùng phím [TAB] để lề các câu lệnh bên dưới.
# ==============================================================================

.PHONY: help install dev-be dev-fe format check clean

# Hiển thị danh sách các lệnh hỗ trợ
help:
 @echo "Các lệnh hỗ trợ:"
 @echo "  make install    - Cài đặt/Đồng bộ thư viện (uv sync)"
 @echo "  make dev-be     - Chạy Backend server (FastAPI) có reload"
 @echo "  make dev-fe     - Chạy Frontend server (Streamlit)"
 @echo "  make format     - Tự động dọn dẹp và format code bằng Ruff"
 @echo "  make check      - Kiểm tra lỗi code (Ruff Linting + Mypy Type checking)"
 @echo "  make clean      - Xóa các file rác, bộ nhớ đệm (cache)"

# Cài đặt môi trường
install:
 uv sync

# Chạy Backend (Cổng mặc định thường là 8000)
dev-be:
 cd backend && uv run uvicorn app.main:app --reload

# Chạy Frontend (Cổng mặc định thường là 8501)
dev-fe:
 cd frontend && uv run streamlit run app.py

# Dọn dẹp và format code
format:
 uv run ruff check . --fix
 uv run ruff format .

# Kiểm tra chất lượng code (Ruff + Mypy)
check:
 uv run ruff check .
 uv run mypy .

# Dọn dẹp file rác
clean:
 find . -type d -name "__pycache__" -exec rm -rf {} +
 find . -type d -name ".pytest_cache" -exec rm -rf {} +
 find . -type d -name ".ruff_cache" -exec rm -rf {} +
 find . -type d -name ".mypy_cache" -exec rm -rf {} +
```

#### Bước 2: Viết tài liệu Onboarding (`README.md`)

*Nhiệm vụ: Hướng dẫn người mới (hoặc chính bạn sau này) cách chạy dự án trên mọi nền tảng.*

1. Mở file `README.md` ở thư mục gốc.
2. Xóa nội dung cũ và dán nội dung chuẩn mực sau:

```markdown
# 🧠 AI Mental Health Agent

Hệ thống hỗ trợ sức khỏe tâm thần sử dụng RAG và Multi-Agent, được xây dựng với FastAPI, Streamlit và công cụ quản lý môi trường siêu tốc `uv`.

## 🚀 Hướng dẫn cài đặt và chạy dự án

### 1. Yêu cầu bắt buộc ban đầu (Dành cho mọi OS)
Dự án này sử dụng `uv` để quản lý môi trường (nhanh hơn pip 10-100 lần). Hãy cài đặt `uv` trước:
- **macOS / Linux:** `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Windows (PowerShell):** `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

---

### Lựa chọn A: Dành cho Linux / macOS / Windows WSL (Khuyên dùng)
Dự án đã được tích hợp sẵn `Makefile` để tối ưu hóa thao tác:
1. Cài đặt toàn bộ thư viện: `make install`
2. Mở Terminal 1 để chạy Backend: `make dev-be`
3. Mở Terminal 2 để chạy Frontend: `make dev-fe`
4. Dọn rác và Format code trước khi đẩy lên Git: `make format` và `make check`

---

### Lựa chọn B: Dành cho Windows thuần (PowerShell / CMD)
Nếu máy bạn không hỗ trợ lệnh `make`, đừng lo! Hãy chạy trực tiếp các lệnh gốc sau:
1. Cài đặt toàn bộ thư viện: `uv sync`
2. Mở Terminal 1 để chạy Backend:
   `cd backend`
   `uv run uvicorn app.main:app --reload`
3. Mở Terminal 2 để chạy Frontend:
   `cd frontend`
   `uv run streamlit run app.py`
```

#### Bước 3: Chạy thử Nghiệm thu toàn hệ thống

*Nhiệm vụ: Kích hoạt lần đầu để đảm bảo không có lỗi thiết lập.*

Tại Terminal gốc, hãy gõ lần lượt các lệnh sau để test:

1. Gõ `make help`: Màn hình phải in ra danh sách các lệnh hướng dẫn.
2. Gõ `make check`: Mypy và Ruff sẽ quét qua hệ thống (có thể sẽ pass luôn vì chưa có code lỗi).
3. Gõ `git add .` và `git commit -m "Initial enterprise setup"`: Hệ thống Pre-commit Hook sẽ bật lên, quét các file, tự động sửa các lỗi khoảng trắng (nếu có) và cho phép bạn lưu lịch sử thành công.

---
**✅ Kết quả nghiệm thu GIAI ĐOẠN 5 (Và toàn bộ dự án):**
Xin chúc mừng! Bạn đang sở hữu một bộ khung dự án (Boilerplate) đạt chuẩn **Senior/Enterprise Level**. Nó siêu tốc (nhờ `uv`), an toàn (nhờ `Pre-commit` & `.env`), mạnh mẽ (kiến trúc Monorepo), và cực kỳ dễ sử dụng (nhờ `Makefile`). Từ khoảnh khắc này, bạn hoàn toàn có thể đóng phần Setup lại và 100% tập trung não bộ vào việc viết Logic AI!

---

## PHẦN 3: TRIẾT LÝ KIẾN TRÚC (DESIGN DECISIONS & FAQ)

Việc hiểu rõ **"Tại sao lại làm thế này?"** quan trọng hơn rất nhiều so với việc chỉ gõ lệnh theo hướng dẫn. Khi hiểu được triết lý thiết kế (Design Philosophy), bạn sẽ dễ dàng mở rộng dự án sau này mà không làm phá vỡ cấu trúc ban đầu, đồng thời có thể tự tin giải thích kiến trúc hệ thống với các kỹ sư khác hoặc nhà tuyển dụng.

Dưới đây là phân tích chi tiết từng quyết định cốt lõi của dự án **AI-Mental-Health-Agent**. Mỗi quyết định đều được đưa ra sau khi cân nhắc kỹ lưỡng giữa tốc độ phát triển, khả năng bảo trì, khả năng scale và kinh nghiệm thực chiến từ các dự án RAG + Multi-Agent.

---

### Quyết định 1: Kiến trúc "Modular Monolith + Decoupled Frontend"

Nhiều người mới làm AI hay nghĩ ngay đến Microservices vì nghe “xịn”. Thực tế, ở quy mô hiện tại (và cả tương lai gần), Microservices sẽ trở thành “cái bẫy” gây tốn kém thời gian setup server, xử lý latency và debug khó khăn.

**1.1 Tách biệt Frontend (Decoupled UI)**

* Streamlit được đặt hoàn toàn riêng trong thư mục `frontend/`.
* Giao tiếp với Backend chỉ qua REST API (không import trực tiếp).
* **Lợi ích:**
  * Frontend sập hoặc đang bảo trì → Backend vẫn chạy bình thường.
  * Có thể deploy Frontend lên Streamlit Cloud / Vercel / Render (rẻ hoặc miễn phí).
  * Toàn bộ ngân sách server mạnh GPU chỉ cần dành cho Backend.
* **Nếu làm ngược (gộp chung):** Code HTML + FastAPI + AI nằm chung một project → khó scale, khó test UI riêng, deploy chậm.

**1.2 Modular Monolith (Nguyên khối theo Module)**

* Toàn bộ lõi hệ thống (API, RAG, LangGraph, Ingestion) nằm trong **một ứng dụng FastAPI duy nhất** (`backend/app`).
* Nhưng được chia thành các lớp rõ ràng:
  * `api/` → chỉ nhận request và trả response (không viết logic).
  * `agents/` → não bộ LangGraph (node, state, graph).
  * `services/` → logic RAG, vector search, LLM call.
  * `ingestion/` → pipeline nạp dữ liệu (chạy batch riêng).
  * `db/` → kết nối Supabase (stateful).
* **Lợi ích:**
  * Debug cực nhanh (gọi hàm trực tiếp trong cùng process).
  * Phát triển tốc độ cao ở giai đoạn PoC.
  * Dễ refactor sau này: muốn tách `agents/` thành microservice riêng chỉ cần “bứng” thư mục ra, thay đổi ít code.
* **Edge case:** Khi dự án có 1 triệu user/ngày, bạn có thể tách từng module thành service riêng mà không phải viết lại từ đầu.

---

### Quyết định 2: Sử dụng uv Workspace (Monorepo)

Đây là quyết định then chốt giúp dự án chạy “siêu tốc” và dễ quản lý nhất hiện nay.

**Tại sao không dùng nhiều virtual environment riêng lẻ hay Poetry?**

* Trước đây lập trình viên Python hay phải tạo `.venv` cho backend, `.venv` cho frontend → mỗi lần code phải activate từng cái, rất dễ nhầm.
* `uv` (viết bằng Rust) + **Workspace** giải quyết triệt để vấn đề này.

**Lợi ích cụ thể:**

* Chỉ **một `.venv` duy nhất** ở thư mục gốc, nhưng `uv` vẫn tách biệt dependencies của backend và frontend một cách thông minh.
* Lệnh `uv sync` (chỉ 1 lệnh) → clone project về máy mới là cài Python + tất cả thư viện đúng version ngay lập tức.
* `uv.lock` thay thế hoàn toàn `requirements.txt`: nó lưu **mã băm (hash)** của mọi thư viện phụ thuộc → dự án mang tính **Deterministic** (chạy ở đâu cũng giống hệt nhau, không bao giờ “hôm qua chạy được, hôm nay lỗi”).
* Tốc độ cài đặt nhanh gấp 10–20 lần so với pip/poetry.
* Dễ chia sẻ tooling chung (ruff, mypy, pre-commit) ở root.

**Nếu làm ngược:** Dùng nhiều `requirements.txt` riêng → dễ bị lệch version, contributor clone về mất hàng giờ cài đặt, CI/CD phức tạp.

---

### Quyết định 3: Không dùng thư mục `src/` (Theo chuẩn FastAPI)

Bạn có thể đã quen với cấu trúc `src/` từ các dự án Python cũ hoặc Java/C++. Chúng ta cố tình **bỏ** nó.

**Lý do chi tiết:**

* Thư mục `src/` (src-layout) được thiết kế tối ưu cho việc **xây dựng thư viện** (package) để người khác `pip install`.
* Dự án của chúng ta là **Web Application / Service**, không phải thư viện. Người dùng cuối không cài qua pip mà truy cập qua browser hoặc API.
* Tác giả FastAPI (Sebastián Ramírez) chính thức khuyến khích dùng cấu trúc phẳng với thư mục `app/`.
* **Lợi ích import:**

  ```python
  from app.services.rag import query_dsm5          # ngắn, dễ đọc
  # thay vì
  from src.app.services.rag import query_dsm5      # dài dòng, dễ lỗi
  ```

* Uvicorn cũng dễ dàng tìm thấy `app.main:app` hơn.

**Edge case:** Nếu sau này bạn muốn xuất package (ví dụ publish lên PyPI), lúc đó mới chuyển sang src-layout. Hiện tại không cần.

---

### Quyết định 4: Phân định rạch ròi "Database Kép" (Dual-Database Separation)

Đây là một trong những quyết định **sống còn** của hệ thống RAG + Multi-Agent. Tuyệt đối không gom code Qdrant và Supabase vào chung một file `database.py`.

**4.1 Thư mục `db/` — Stateful (Trạng thái)**

* Kết nối Supabase / PostgreSQL.
* Lưu: tài khoản user, mật khẩu, lịch sử chat, **state của LangGraph** (để agent nhớ cuộc trò chuyện).
* Nếu database này sập → user mất tài khoản, AI quên hết lịch sử.

**4.2 Thư mục `services/` — Stateless (Công cụ tra cứu)**

* Kết nối Qdrant (Vector DB), OpenAI, RAG logic.
* Qdrant chỉ lưu “kiến thức hàn lâm” (chunk từ DSM-5, tài liệu tâm lý).
* Không lưu thông tin cá nhân của user.
* **Lợi ích lớn nhất (Dependency Inversion):**
  * Muốn đổi Qdrant sang Pinecone, ChromaDB hay Weaviate? Chỉ sửa code trong `services/`, toàn bộ `api/`, `agents/`, `db/` **không cần động một dòng nào**.
  * Qdrant bị cháy server? Chỉ cần bật instance mới và chạy lại script ingestion → AI “học lại” trong 5 phút, user không bị ảnh hưởng.

**Ví dụ thực tế:**

* User hỏi: “Tôi bị trầm cảm, triệu chứng như thế nào?” → `services/` gọi Qdrant tìm chunk DSM-5.
* User nói: “Nhớ lại cuộc trò chuyện lần trước tôi kể…” → `db/` lấy state từ Supabase.

---

### Quyết định 5: Code Quality & Developer Experience (Ruff + Mypy + Pre-commit + Makefile)

Chúng ta không chỉ code mà còn xây dựng **quy trình chuyên nghiệp ngay từ ngày đầu**.

* Ruff (linter + formatter cực nhanh) + Mypy (type checker) được cấu hình ở root.
* Pre-commit hooks tự động chạy trước mỗi `git commit` → không thể push code bẩn.
* Makefile là “bảng điều khiển” duy nhất: `make dev-be`, `make format`, `make check`…
* `package = false` trong `pyproject.toml` của backend/frontend (bắt buộc) để uv biết đây là **ứng dụng web**, không phải package.

**Lợi ích:**

* Code luôn sạch, dễ đọc, ít bug.
* Bất kỳ ai clone project về cũng chỉ cần gõ `make install` là chạy được.
* Giảm cognitive load khi làm việc nhóm.

---

### Quyết định 6: Tạm hoãn Docker và `requirements.txt`

Chúng ta cố tình **không** tạo `Dockerfile` và `requirements.txt` ngay từ đầu.

**Lý do:**

* Giai đoạn PoC bạn sẽ liên tục thêm thư viện (pdfplumber, beautifulsoup4, langchain-community…). Mỗi lần thêm phải rebuild Docker image mất 3–5 phút → giết chết cảm hứng code.
* `uv` + `uv.lock` đã đủ mạnh để đảm bảo môi trường đồng nhất ở local và CI/CD.
* Chỉ khi toàn bộ chức năng chính (chatbot + RAG + agent) chạy ổn định, chúng ta mới thêm Docker + docker-compose để deploy production.

**Khi nào nên làm:**

* Sau khi Frontend và Backend đã “nói chuyện” trơn tru.
* Trước khi đưa lên VPS / AWS / Railway.

---

### ❓ FAQ - Các câu hỏi thường gặp khi mở rộng

**Q1: Muốn cài thêm thư viện thì dùng lệnh gì?**
→ Luôn dùng `uv add`:

```bash
uv add --package backend beautifulsoup4          # cho backend
uv add --package frontend plotly                 # cho frontend
uv add --dev --package backend pytest            # dev dependency
```

**Q2: Folder `tests/` có quan trọng không?**
→ Rất quan trọng! Đặc biệt với RAG, bạn cần test độ chính xác, hallucination, retrieval quality. Đây là nơi viết unit test và evaluation pipeline.

**Q3: Tại sao frontend lại chia `pages/` và `components/`?**
→ Streamlit tự động đọc thư mục `pages/` để tạo menu sidebar (ví dụ `pages/1_Chatbot.py` sẽ thành mục “1 Chatbot”). `components/` chứa các UI tái sử dụng (button, chart, chat bubble…) để code không bị lặp.

**Q4: Muốn thêm tính năng cào dữ liệu định kỳ (web scraper) thì để code ở đâu?**
→ Tạo thư mục `backend/app/workers/` hoặc file `backend/app/services/scraper.py`. Dùng Background Tasks của FastAPI hoặc sau này tích hợp Celery + Redis.

**Q5: Làm CI/CD (GitHub Actions) thì cấu hình như thế nào?**
→ Rất đơn giản nhờ Makefile. Trong `.github/workflows/ci.yml` bạn chỉ cần chạy:

```yaml
- name: Check & Test
  run: |
    make install
    make check
    cd backend && uv run pytest
```

**Q6: Sau này muốn chuyển sang production database thật thì sao?**
→ Supabase đã là production-ready. Còn Qdrant bạn có thể chuyển sang Qdrant Cloud hoặc self-host với Docker mà không ảnh hưởng kiến trúc.


Dưới đây là **Workflow 4 bước "bất tử"** mỗi khi bạn muốn thêm một thư viện mới vào dự án này:

---

### Bước 1: Cài đặt vào Package (Library Installation)
Bạn phải xác định thư viện đó dùng cho ai (Backend hay Frontend).
* **Nếu dùng cho Backend:** `uv add --package backend <tên-thư-viện>`
* **Nếu dùng cho Frontend:** `uv add --package frontend <tên-thư-viện>`

### Bước 2: Cài đặt "Bản đồ kiểu" cho Mypy (Type Stubs)
Nhiều thư viện Python cũ không có sẵn thông tin kiểu dữ liệu. Để Mypy không báo lỗi `import-untyped`, hãy cài thêm gói `types-*` vào nhóm Dev.
* **Lệnh:** `uv add --dev types-<tên-thư-viện>`
* *(Lưu ý: Không phải thư viện nào cũng cần gói này, nếu cài mà báo không tìm thấy thì bỏ qua).*

### Bước 3: Khai báo trong Code (Import)
Mở file `.py` bạn muốn dùng và viết lệnh `import`.
* **Ví dụ:** `import requests` hoặc `import pandas as pd`.

### Bước 4: Chạy bộ lọc tự động (The "Make" Chain)
Sau khi xong 3 bước trên, bạn chạy chuỗi lệnh này để dự án tự "sạch":
1.  **`make format`**: Để Ruff tự sắp xếp lại các dòng import cho đúng chuẩn.
2.  **`make check`**: Để Mypy xác nhận bạn đã dùng thư viện đó đúng cách.

---

### Bảng tóm tắt Workflow cho bạn dễ nhớ

| Hành động | Lệnh thực hiện | Mục đích |
| :--- | :--- | :--- |
| **Thêm đồ vào kho** | `uv add --package ...` | Để máy có file mà chạy. |
| **Thêm từ điển** | `uv add --dev types-...` | Để Mypy hiểu thư viện đó là gì. |
| **Lôi đồ ra dùng** | `import ...` (trong file .py) | Để Python biết bạn cần dùng nó ở file này. |
| **Kiểm tra lại** | `make format` & `make check` | Để đảm bảo mọi thứ hoàn hảo trước khi lưu (commit). |

---

### Tại sao bạn thấy phức tạp?
Đó là vì dự án này đang được thiết lập theo tiêu chuẩn **Sovereign Agentic AI** (AI Agent có chủ quyền và tự chủ). Với tiêu chuẩn này:
* Code phải **cực kỳ rõ ràng** về kiểu dữ liệu (Strict typing).
* Cấu trúc phải **chia nhỏ** (Modular) để Agent dễ dàng đọc và sửa lỗi cho bạn sau này.
