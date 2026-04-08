# 🤖 RAG Customer Support Chatbot

Chatbot chăm sóc khách hàng thông minh sử dụng **Retrieval Augmented Generation (RAG)**, tự động trả lời câu hỏi dựa trên tài liệu nội bộ của doanh nghiệp.

## ✨ Tính năng

- 💬 **Chat thông minh** — Trả lời câu hỏi bằng tiếng Việt dựa trên tài liệu đã nạp
- 📚 **Nạp tài liệu linh hoạt** — Hỗ trợ `.txt`, `.md`, `.pdf`, `.docx`
- 🔍 **Tìm kiếm ngữ nghĩa** — Sử dụng Vietnamese Embedding để tìm nội dung liên quan nhất
- 🧠 **Chunking thông minh** — Tự động chọn chiến lược chia nhỏ phù hợp theo loại file
- 📊 **Nguồn tham khảo** — Hiển thị nguồn dữ liệu mà chatbot sử dụng để trả lời
- 🖥️ **Giao diện Streamlit** — Web UI trực quan, dễ sử dụng

## 🏗️ Kiến trúc

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────────────┐
│  Streamlit  │────▶│   FastAPI    │────▶│       RAG Service        │
│   Web UI    │◀────│   Backend    │◀────│   (Pipeline điều phối)   │
│  (app.py)   │     │  (main.py)   │     └──────────┬───────────────┘
└─────────────┘     └──────────────┘                │
                                          ┌─────────┴─────────┐
                                          ▼                   ▼
                                   ┌──────────────┐   ┌──────────────┐
                                   │  Embedding   │   │  LLM Service │
                                   │   Service    │   │   (Ollama)   │
                                   │  vietnamese- │   │  ministral-  │
                                   │  embedding   │   │    3:8b      │
                                   └──────┬───────┘   └──────────────┘
                                          │
                                          ▼
                                   ┌──────────────┐
                                   │   ChromaDB   │
                                   │ Vector Store │
                                   └──────────────┘
```

## 🔄 Luồng hoạt động

### Nạp tài liệu (Ingestion)

```
Tài liệu (.md, .txt, .pdf, .docx)
    │
    ▼
Chọn chiến lược Chunking
    ├── File .md → MarkdownChunkingService (chia theo heading ##, ###)
    │                 └── Enrichment: chuyển bullet-list → câu tự nhiên
    └── File khác → ChunkingService (RecursiveCharacterTextSplitter)
    │
    ▼
Tạo Embedding (vietnamese-embedding, 768 chiều)
    │
    ▼
Lưu vào ChromaDB (cosine similarity)
```

### Trả lời câu hỏi (Query)

```
Câu hỏi của khách hàng
    │
    ▼
Tạo Embedding cho câu hỏi
    │
    ▼
Tìm kiếm Top-K chunks tương đồng nhất trong ChromaDB
    │
    ▼
Ghép context (chunks) + câu hỏi → Gửi cho LLM
    │
    ▼
LLM sinh câu trả lời bằng tiếng Việt
    │
    ▼
Trả về: Câu trả lời + Nguồn tham khảo
```

## 📁 Cấu trúc dự án

```
chat-bot-customer/
├── app.py                              # Streamlit Web UI
├── main.py                             # FastAPI Backend (entry point)
├── ingest.py                           # CLI nạp tài liệu
├── requirements.txt                    # Dependencies
├── .env / .env.example                 # Cấu hình môi trường
│
├── app/
│   ├── config.py                       # Quản lý cấu hình (pydantic-settings)
│   ├── models/
│   │   └── schemas.py                  # Pydantic models (request/response)
│   ├── services/
│   │   ├── rag_service.py              # Điều phối pipeline RAG
│   │   ├── chunking_service.py         # Chunking cho text thường
│   │   ├── markdown_chunking_service.py # Chunking cho markdown + enrichment
│   │   ├── embedding_service.py        # Tạo embedding vectors
│   │   ├── vector_store.py             # ChromaDB operations
│   │   └── llm_service.py             # Giao tiếp với Ollama LLM
│   ├── api/
│   │   └── routes.py                   # API endpoints (FastAPI)
│   └── utils/
│       └── document_loader.py          # Đọc file (.txt, .md, .pdf, .docx)
│
└── data/
    ├── documents/                      # Thư mục chứa tài liệu gốc
    └── chroma_db/                      # ChromaDB persistent storage
```

## 🛠️ Tech Stack

| Thành phần | Công nghệ | Chi tiết |
|------------|-----------|----------|
| **LLM** | Ollama + Ministral 3:8B | Model ngôn ngữ chạy local |
| **Embedding** | `dangvantuan/vietnamese-embedding` | Vector 768 chiều, tối ưu cho tiếng Việt |
| **Vector DB** | ChromaDB | Lưu trữ persistent, cosine similarity |
| **Backend** | FastAPI | REST API, async, auto-docs |
| **Frontend** | Streamlit | Giao diện chat trực quan |
| **Chunking** | LangChain Text Splitters | Recursive + Markdown Header |

## 🚀 Cài đặt & Chạy

### Yêu cầu

- Python 3.12+
- [Ollama](https://ollama.com/download) đã cài đặt

### Bước 1: Clone & Cài dependencies

```bash
git clone <repo-url>
cd chat-bot-customer

python -m venv venv
source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

### Bước 2: Cấu hình

```bash
cp .env.example .env
# Chỉnh sửa .env nếu cần
```

### Bước 3: Cài model LLM

```bash
ollama pull ministral-3:8b
ollama serve  # Nếu Ollama chưa chạy
```

### Bước 4: Nạp tài liệu

Đặt file tài liệu vào `data/documents/`, sau đó:

```bash
python ingest.py               # Nạp toàn bộ thư mục
python ingest.py --clear       # Xóa data cũ + nạp lại
python ingest.py --file <path> # Nạp 1 file cụ thể
```

### Bước 5: Chạy ứng dụng

**Terminal 1 — Backend:**
```bash
source venv/bin/activate
python main.py
# → API chạy tại http://localhost:8000
# → Swagger UI tại http://localhost:8000/docs
```

**Terminal 2 — Web UI:**
```bash
source venv/bin/activate
streamlit run app.py
# → Giao diện chat tại http://localhost:8501
```

## 📡 API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|--------|
| `POST` | `/api/chat` | Gửi câu hỏi, nhận câu trả lời + nguồn |
| `POST` | `/api/ingest/directory` | Nạp toàn bộ `data/documents/` |
| `POST` | `/api/ingest/upload` | Upload & nạp 1 file |
| `GET` | `/api/collection/info` | Thông tin vector store |
| `DELETE` | `/api/collection/clear` | Xóa toàn bộ dữ liệu |
| `GET` | `/api/health` | Health check |

## 🧩 Chiến lược Chunking

Dự án sử dụng **2 chiến lược chunking**, tự động chọn theo loại file:

### 1. Recursive Text Splitting (cho `.txt`, `.pdf`, `.docx`)
- Chia theo paragraph → sentence → word
- `chunk_size`: 500 ký tự, `overlap`: 50
- Tối ưu cho văn bản dạng tự do

### 2. Markdown Header Splitting + Enrichment (cho `.md`)
- Chia theo heading `##`, `###` — mỗi section = 1 chunk
- **Chunk Enrichment**: Chuyển dữ liệu dạng bullet-list (`- Key: Value`) thành **câu tiếng Việt tự nhiên** trước khi tạo embedding → cải thiện retrieval accuracy
- Tối ưu cho dữ liệu có cấu trúc (danh sách chi nhánh, bảng giá, FAQ...)

**Ví dụ Enrichment:**
```
Trước: "- Quận: Gò Vấp"
Sau:   "Chi nhánh The New Gym Quang Trung, tại quận Gò Vấp, thuộc Hồ Chí Minh."
```

## 📂 Tài liệu hiện có

| File | Nội dung | Chunks |
|------|----------|--------|
| `clubs_summary.md` | Danh sách 15 chi nhánh The New Gym | 15 |
| `dieu_khoan_dieu_kien.md` | Điều khoản & Điều kiện sử dụng | 45 |
| `chinh_sach_bao_mat.md` | Chính sách bảo mật thông tin | 17 |
| `bang_gia_t03_2026.md` | Bảng giá gói tập tháng 03/2026 | 16 |

## ⚙️ Cấu hình

Các biến môi trường trong `.env`:

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL của Ollama server |
| `LLM_MODEL` | `ministral-3:8b` | Model LLM sử dụng |
| `EMBED_MODEL` | `dangvantuan/vietnamese-embedding` | Model embedding |
| `EXERCISE_EMBED_LIMIT` | `500` | Kích thước tối đa mỗi chunk (ký tự) |
| `EXERCISE_CONTEXT_LIMIT` | `6` | Số chunks trả về khi tìm kiếm |
| `CHROMA_DB_PATH` | `data/chroma_db` | Đường dẫn lưu ChromaDB |
| `COLLECTION_NAME` | `customer_support_docs` | Tên collection trong ChromaDB |

## 📝 Cập nhật dữ liệu

Khi cần cập nhật tài liệu (ví dụ: thay đổi giá, thêm chi nhánh mới):

1. Sửa/thêm file `.md` trong `data/documents/`
2. Chạy `python ingest.py --clear` để nạp lại
3. Restart backend `python main.py`

## 📄 License

MIT License
