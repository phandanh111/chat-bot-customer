import streamlit as st
import httpx
import json

API_BASE_URL = "http://localhost:8000"
CHAT_TIMEOUT = 60.0
HEALTH_TIMEOUT = 2.0
INFO_TIMEOUT = 5.0
DOC_TIMEOUT = 30.0

st.set_page_config(page_title="Hỗ Trợ Khách Hàng", page_icon="💬", layout="centered")
st.title("💬 Trợ Lý Hỗ Trợ Khách Hàng")

tab_chat, tab_docs = st.tabs(["💬 Chat", "📁 Quản lý tài liệu"])


# ── CHAT TAB ──────────────────────────────────────────────────────────────────

with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
        st.chat_message("user").markdown(prompt)
        chat_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                with st.spinner("Đang tìm câu trả lời..."):
                    answer = ""
                    with httpx.Client(timeout=CHAT_TIMEOUT) as client:
                        with client.stream(
                            "POST",
                            f"{API_BASE_URL}/api/chat/stream",
                            json={"question": prompt, "history": chat_history},
                        ) as response:
                            response.raise_for_status()
                            for line in response.iter_lines():
                                if not line:
                                    continue
                                event = json.loads(line)
                                if event.get("type") == "token":
                                    answer += event.get("content", "")
                                    message_placeholder.markdown(answer + "▌")
                    message_placeholder.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
            except httpx.ConnectError:
                error_msg = "Không thể kết nối đến máy chủ API. Vui lòng kiểm tra xem `python main.py` đã chạy chưa."
                message_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = f"Đã có lỗi xảy ra: {str(e)}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})


# ── DOCUMENT MANAGEMENT TAB ───────────────────────────────────────────────────

with tab_docs:
    st.subheader("📁 Quản lý tài liệu")

    # ── Actions row ──
    col_upload, col_ingest, col_cache = st.columns([2, 1, 1])

    with col_upload:
        uploaded_file = st.file_uploader(
            "Upload tài liệu mới",
            type=["txt", "md", "pdf", "docx"],
            label_visibility="collapsed",
        )

    with col_ingest:
        st.write("")
        if st.button("⬆️ Upload & Ingest", use_container_width=True, disabled=uploaded_file is None):
            try:
                resp = httpx.post(
                    f"{API_BASE_URL}/api/ingest/upload",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue())},
                    timeout=DOC_TIMEOUT,
                )
                resp.raise_for_status()
                data = resp.json()
                st.success(f"✅ {data['message']} ({data['total_chunks']} chunks)")
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi upload: {e}")

    with col_cache:
        st.write("")
        if st.button("🗑️ Xóa cache", use_container_width=True):
            try:
                httpx.post(f"{API_BASE_URL}/api/cache/clear", timeout=INFO_TIMEOUT).raise_for_status()
                st.success("Cache đã được xóa.")
            except Exception as e:
                st.error(f"Lỗi: {e}")

    st.divider()

    # ── Document list ──
    try:
        docs_resp = httpx.get(f"{API_BASE_URL}/api/documents", timeout=INFO_TIMEOUT)
        docs_resp.raise_for_status()
        documents = docs_resp.json().get("documents", [])
    except Exception:
        st.error("Không thể lấy danh sách tài liệu. Kiểm tra server đang chạy chưa.")
        documents = []

    if not documents:
        st.info("Chưa có tài liệu nào. Upload file ở trên để bắt đầu.")
    else:
        st.caption(f"{len(documents)} tài liệu")
        for doc in documents:
            with st.expander(f"📄 {doc}"):
                is_editable = doc.endswith(".txt") or doc.endswith(".md")

                if is_editable:
                    cache_key = f"doc_content_{doc}"
                    if cache_key not in st.session_state:
                        try:
                            content_resp = httpx.get(
                                f"{API_BASE_URL}/api/documents/{doc}", timeout=INFO_TIMEOUT
                            )
                            content_resp.raise_for_status()
                            st.session_state[cache_key] = content_resp.json().get("content", "")
                        except Exception:
                            st.session_state[cache_key] = ""

                    new_content = st.text_area(
                        "Nội dung",
                        value=st.session_state[cache_key],
                        height=350,
                        key=f"textarea_{doc}",
                    )

                    col_save, col_del = st.columns([1, 1])
                    with col_save:
                        if st.button("💾 Lưu & Cập nhật", key=f"save_{doc}", use_container_width=True):
                            try:
                                resp = httpx.put(
                                    f"{API_BASE_URL}/api/documents/{doc}",
                                    json={"content": new_content},
                                    timeout=DOC_TIMEOUT,
                                )
                                resp.raise_for_status()
                                data = resp.json()
                                st.success(f"✅ {data['message']}")
                                del st.session_state[cache_key]
                                st.rerun()
                            except Exception as e:
                                st.error(f"Lỗi lưu: {e}")
                    with col_del:
                        if st.button("🗑️ Xóa file", key=f"del_{doc}", use_container_width=True, type="secondary"):
                            try:
                                httpx.delete(
                                    f"{API_BASE_URL}/api/documents/{doc}", timeout=INFO_TIMEOUT
                                ).raise_for_status()
                                st.success(f"Đã xóa '{doc}'.")
                                if cache_key in st.session_state:
                                    del st.session_state[cache_key]
                                st.rerun()
                            except Exception as e:
                                st.error(f"Lỗi xóa: {e}")
                else:
                    st.caption(f"File `{doc.split('.')[-1].upper()}` — không hỗ trợ chỉnh sửa trực tiếp. Re-upload để cập nhật.")
                    if st.button("🗑️ Xóa file", key=f"del_{doc}", use_container_width=True, type="secondary"):
                        try:
                            httpx.delete(
                                f"{API_BASE_URL}/api/documents/{doc}", timeout=INFO_TIMEOUT
                            ).raise_for_status()
                            st.success(f"Đã xóa '{doc}'.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi xóa: {e}")


# ── SIDEBAR ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Cấu hình")
    try:
        health = httpx.get(f"{API_BASE_URL}/api/health", timeout=HEALTH_TIMEOUT)
        if health.status_code == 200:
            st.success("API đang hoạt động ✅")
        else:
            st.warning("API phản hồi bất thường ⚠️")
    except Exception:
        st.error("API chưa được khởi động ❌")
        st.info("Chạy `python main.py` ở terminal khác để khởi động backend.")

    st.markdown("---")
    st.subheader("📊 Vector Store")
    try:
        info = httpx.get(f"{API_BASE_URL}/api/collection/info", timeout=INFO_TIMEOUT).json()
        st.metric("Total Chunks", info.get("total_documents", 0))
    except Exception:
        st.caption("Không thể lấy thông tin.")

    st.markdown("---")
    if st.button("Xóa lịch sử chat", type="primary"):
        st.session_state.messages = []
        st.rerun()
