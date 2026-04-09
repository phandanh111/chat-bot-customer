# The New Gym — RAG Customer Support Chatbot

Chatbot hỗ trợ khách hàng tự động cho hệ thống phòng tập **The New Gym**, sử dụng kiến trúc **Retrieval-Augmented Generation (RAG)** kết hợp với tích hợp **Map API** để gợi ý chi nhánh gần nhất theo vị trí thực tế của khách hàng.

---

## Kiến trúc hệ thống

```
Khách hàng (Streamlit UI)
        │
        ▼
  FastAPI Backend  ──────────────────────────────────────────────────┐
        │                                                            │
        ├── RAGService.query()                                       │
        │       │                                                    │
        │       ├─ [1] Normalize query (acronym fix: hvt→HVT...)     │
        │       ├─ [2] Embed query → EmbeddingService                │
        │       │         (dangvantuan/vietnamese-embedding)         │
        │       ├─ [3] Search ChromaDB → VectorStoreService          │
        │       ├─ [4] Detect location intent → MapService           │
        │       │         → Nominatim (OpenStreetMap API)            │
        │       │         → Haversine distance → top-3 branches      │
        │       ├─ [5] Inject Map context vào RAG context            │
        │       └─ [6] Generate answer → LLMService                  │
        │                 (Ollama - ministral-3:8b)                  │
        └────────────────────────────────────────────────────────────┘
```

---

## Tính năng chính

- **Hỏi đáp tự động** dựa trên tài liệu nội bộ (chính sách giá, điều khoản, bảo mật, chi nhánh)
- **Phân biệt Gói Tập vs Gói PT** — chunking tối ưu để tránh nhầm lẫn giữa 2 loại giá
- **Gợi ý chi nhánh gần nhất** theo vị trí khách hàng nhập vào (tích hợp OpenStreetMap Nominatim)
- **Chuẩn hóa từ viết tắt** tự động (`hvt → HVT`, `pt → PT`, `uvk → UVK`...) để cải thiện độ chính xác embedding
- **Hai luồng chunking** — Markdown Header Splitter cho file `.md`, Recursive Text Splitter cho các định dạng còn lại
- **Chat UI** đơn giản bằng Streamlit, kết nối realtime với FastAPI backend

---

## Cấu trúc thư mục

```
chat-bot-customer/
├── app/
│   ├── api/
│   │   └── routes.py               # FastAPI endpoints
│   ├── models/
│   │   └── schemas.py              # Pydantic schemas
│   ├── services/
│   │   ├── rag_service.py          # Orchestrator chính (RAG pipeline)
│   │   ├── llm_service.py          # Gọi Ollama API để sinh câu trả lời
│   │   ├── embedding_service.py    # Mã hóa văn bản thành vector
│   │   ├── vector_store.py         # Quản lý ChromaDB
│   │   ├── chunking_service.py     # Text splitter thông thường
│   │   ├── markdown_chunking_service.py  # Markdown header splitter + enrichment
│   │   └── map_service.py          # Geocoding + tính khoảng cách chi nhánh
│   ├── utils/
│   │   ├── document_loader.py      # Đọc file (txt, md, pdf, docx)
│   │   └── geo_utils.py            # Tọa độ 15 chi nhánh + Haversine formula
│   ├── config.py                   # Cấu hình từ .env (pydantic-settings)
│   └── constants.py                # Toàn bộ hằng số dự án
├── data/
│   ├── documents/                  # Tài liệu nguồn để ingest
│   │   ├── bang_gia_goi_tap.md
│   │   ├── bang_gia_pt.md
│   │   ├── clubs_summary.md
│   │   ├── chinh_sach_bao_mat.md
│   │   └── dieu_khoan_dieu_kien.md
│   └── chroma_db/                  # Vector database (tự sinh, không commit)
├── app.py                          # Streamlit UI
├── main.py                         # FastAPI entry point
├── ingest.py                       # CLI script nạp tài liệu
├── test_cases.md                   # Bộ câu hỏi kiểm thử RAG
├── .env                            # Cấu hình cục bộ (không commit)
├── .env.example                    # Mẫu cấu hình
└── requirements.txt
```

---

## Cài đặt

### Yêu cầu

- Python 3.11+
- [Ollama](https://ollama.com) đã cài và đang chạy
- Model LLM: `ollama pull ministral-3:8b`

### Các bước

```bash
# 1. Tạo môi trường ảo
python -m venv venv
source venv/bin/activate

# 2. Cài thư viện
pip install -r requirements.txt

# 3. Tạo file cấu hình
cp .env.example .env

# 4. Nạp tài liệu vào vector store
python ingest.py --clear

# 5. Khởi động backend
python main.py

# 6. Khởi động UI (terminal riêng)
streamlit run app.py
```

---

## Cấu hình `.env`

| Biến | Mặc định | Mô tả |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL Ollama server |
| `LLM_MODEL` | `ministral-3:8b` | Tên model LLM |
| `EMBED_MODEL` | `dangvantuan/vietnamese-embedding` | Model embedding tiếng Việt |
| `EXERCISE_EMBED_LIMIT` | `500` | Kích thước tối đa mỗi chunk (ký tự) |
| `EXERCISE_CONTEXT_LIMIT` | `4` | Số chunk tối đa đưa vào context |
| `CHROMA_DB_PATH` | `data/chroma_db` | Đường dẫn lưu ChromaDB |
| `COLLECTION_NAME` | `customer_support_docs` | Tên collection ChromaDB |

---

## Quản lý tài liệu

### Nạp tài liệu mới

```bash
# Nạp toàn bộ thư mục data/documents/
python ingest.py

# Nạp 1 file cụ thể
python ingest.py --file data/documents/bang_gia_goi_tap.md

# Xóa sạch rồi nạp lại
python ingest.py --clear
```

### Cập nhật bảng giá

Chỉnh sửa trực tiếp các file `.md` trong `data/documents/`, sau đó chạy lại:

```bash
python ingest.py --clear
```

**Lưu ý định dạng:** Viết giá theo dạng paragraph liền mạch, tránh dùng bullet list (`-`) để ngăn chunker tách giá khỏi tên chi nhánh.

### Thêm chi nhánh mới

Chỉnh sửa **duy nhất** file `app/utils/geo_utils.py` — thêm tọa độ vào `BRANCHES_COORDINATES`. Danh sách chi nhánh trong System Prompt và thuật toán tìm chi nhánh gần nhất sẽ tự động cập nhật.

---

## API Endpoints

| Method | Endpoint | Mô tả |
|---|---|---|
| `POST` | `/api/chat` | Gửi câu hỏi, nhận câu trả lời |
| `POST` | `/api/ingest/directory` | Nạp toàn bộ `data/documents/` |
| `POST` | `/api/ingest/upload` | Upload và nạp 1 file |
| `GET` | `/api/collection/info` | Thông tin vector store |
| `DELETE` | `/api/collection/clear` | Xóa toàn bộ vector store |
| `GET` | `/api/health` | Kiểm tra trạng thái API |

### Ví dụ gọi API

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Gói PT Silver bao nhiêu tiền?", "history": []}'
```

---

## Tính năng Map (Gợi ý chi nhánh gần nhất)

Khi khách nhắc đến tên quận/huyện hoặc khu vực (ví dụ: *"tôi ở Thủ Đức"*, *"gần Quận 7"*):

1. Hệ thống nhận diện địa điểm qua regex pattern matching
2. Gọi **OpenStreetMap Nominatim API** (miễn phí, không cần API key) để lấy tọa độ
3. Tính khoảng cách đến 15 chi nhánh bằng **công thức Haversine**
4. Tiêm thông tin khoảng cách vào context trước khi đưa vào LLM

> Tọa độ 15 chi nhánh được lưu tĩnh trong `geo_utils.py` nên không mất thời gian geocode khi startup.

---

## Tài liệu nguồn

| File | Nội dung |
|---|---|
| `bang_gia_goi_tap.md` | Bảng giá thẻ hội viên (gói tập tự tập) theo từng nhóm chi nhánh |
| `bang_gia_pt.md` | Bảng giá gói thuê PT (Personal Trainer) |
| `clubs_summary.md` | Danh sách 15 chi nhánh với địa chỉ và thông tin cụ thể |
| `chinh_sach_bao_mat.md` | Chính sách bảo mật dữ liệu thành viên |
| `dieu_khoan_dieu_kien.md` | Điều khoản và điều kiện sử dụng dịch vụ |
