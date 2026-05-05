import streamlit as st
import httpx
import json

from app.constants import (
    CHAT_REQUEST_TIMEOUT,
    COLLECTION_INFO_TIMEOUT,
    HEALTH_CHECK_TIMEOUT,
    STREAMLIT_API_URL,
)

st.set_page_config(page_title="Hỗ Trợ Khách Hàng", page_icon="💬", layout="centered")
st.title("💬 Trợ Lý Hỗ Trợ Khách Hàng")
st.markdown("Hỗ trợ tự động giải đáp các thắc mắc của bạn.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("Nguồn tham khảo"):
                for idx, src in enumerate(message["sources"]):
                    st.markdown(f"**[{idx+1}] {src['source']}** (Độ phù hợp: {src['score']})")
                    st.text(src["content"])

if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
    st.chat_message("user").markdown(prompt)
    chat_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            with st.spinner("Đang tìm câu trả lời..."):
                answer = ""
                sources = []
                with httpx.Client(timeout=CHAT_REQUEST_TIMEOUT) as client:
                    with client.stream(
                        "POST",
                        f"{STREAMLIT_API_URL}/api/chat/stream",
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
                            elif event.get("type") == "done":
                                sources = event.get("sources", [])
                message_placeholder.markdown(answer)
                if sources:
                    with st.expander("Nguồn tham khảo"):
                        for idx, src in enumerate(sources):
                            st.markdown(f"**[{idx+1}] {src['source']}** (Độ phù hợp: {src['score']})")
                            st.text(src["content"])
                st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
        except httpx.ConnectError:
            error_msg = "Không thể kết nối đến máy chủ API. Vui lòng kiểm tra xem `python main.py` đã chạy chưa."
            message_placeholder.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        except Exception as e:
            error_msg = f"Đã có lỗi xảy ra: {str(e)}"
            message_placeholder.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

with st.sidebar:
    st.header("⚙️ Cấu hình")
    try:
        health = httpx.get(f"{STREAMLIT_API_URL}/api/health", timeout=HEALTH_CHECK_TIMEOUT)
        if health.status_code == 200:
            st.success("API đang hoạt động ✅")
        else:
            st.warning("API phản hồi bất thường ⚠️")
    except Exception:
        st.error("API chưa được khởi động ❌")
        st.info("Chạy `python main.py` ở terminal khác để khởi động backend.")

    st.markdown("---")
    st.subheader("📊 Dữ liệu (Vector Store)")
    if st.button("Làm mới thông tin", key="refresh_info"):
        try:
            info = httpx.get(f"{STREAMLIT_API_URL}/api/collection/info", timeout=COLLECTION_INFO_TIMEOUT).json()
            st.session_state.collection_info = info
        except Exception:
            pass

    if "collection_info" in st.session_state:
        st.metric("Total Documents", st.session_state.collection_info.get("total_documents", 0))
    else:
        try:
            info = httpx.get(f"{STREAMLIT_API_URL}/api/collection/info", timeout=COLLECTION_INFO_TIMEOUT).json()
            st.session_state.collection_info = info
            st.metric("Total Documents", info.get("total_documents", 0))
        except Exception:
            st.caption("Không thể lấy thông tin dữ liệu.")

    st.markdown("---")
    if st.button("Xóa lịch sử chat", type="primary"):
        st.session_state.messages = []
        st.rerun()
