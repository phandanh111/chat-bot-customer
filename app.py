"""
Streamlit UI for the RAG Chatbot Customer Service.
Run with: streamlit run app.py
"""

import streamlit as st
import httpx

# Configuration
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Hỗ Trợ Khách Hàng",
    page_icon="💬",
    layout="centered",
)

st.title("💬 Trợ Lý Hỗ Trợ Khách Hàng")
st.markdown("Hỗ trợ tự động giải đáp các thắc mắc của bạn.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Display sources if available
        if "sources" in message and message["sources"]:
            with st.expander("Nguồn tham khảo"):
                for idx, src in enumerate(message["sources"]):
                    st.markdown(
                        f"**[{idx+1}] {src['source']}** "
                        f"(Độ phù hợp: {src['score']})"
                    )
                    st.text(src["content"])

# React to user input
if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)

    chat_history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            with st.spinner("Đang tìm câu trả lời..."):
                response = httpx.post(
                    f"{API_URL}/api/chat",
                    json={"question": prompt, "history": chat_history},
                    timeout=60.0,
                )
                response.raise_for_status()
                result = response.json()
                
                answer = result.get("answer", "")
                sources = result.get("sources", [])
                
                message_placeholder.markdown(answer)
                
                if sources:
                    with st.expander("Nguồn tham khảo"):
                        for idx, src in enumerate(sources):
                            st.markdown(
                                f"**[{idx+1}] {src['source']}** "
                                f"(Độ phù hợp: {src['score']})"
                            )
                            st.text(src["content"])
                
                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })
                
        except httpx.ConnectError:
            error_msg = "Không thể kết nối đến máy chủ API. Vui lòng kiểm tra xem `python main.py` đã chạy chưa."
            message_placeholder.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        except Exception as e:
            error_msg = f"Đã có lỗi xảy ra: {str(e)}"
            message_placeholder.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Cấu hình")
    
    # Check API health
    try:
        health = httpx.get(f"{API_URL}/api/health", timeout=2.0)
        if health.status_code == 200:
            st.success("API đang hoạt động ✅")
        else:
            st.warning("API phản hồi bất thường ⚠️")
    except Exception:
        st.error("API chưa được khởi động ❌")
        st.info("Chạy `python main.py` ở terminal khác để khởi động backend.")
    
    st.markdown("---")
    
    # Collection Info
    st.subheader("📊 Dữ liệu (Vector Store)")
    if st.button("Làm mới thông tin", key="refresh_info"):
        try:
            info = httpx.get(f"{API_URL}/api/collection/info", timeout=5.0).json()
            st.session_state.collection_info = info
        except Exception:
            pass
            
    if "collection_info" in st.session_state:
        info = st.session_state.collection_info
        st.metric("Total Documents", info.get("total_documents", 0))
    else:
        try:
            info = httpx.get(f"{API_URL}/api/collection/info", timeout=5.0).json()
            st.session_state.collection_info = info
            st.metric("Total Documents", info.get("total_documents", 0))
        except Exception:
            st.caption("Không thể lấy thông tin dữ liệu.")
            
    st.markdown("---")
    
    # Clear Chat
    if st.button("Xóa lịch sử chat", type="primary"):
        st.session_state.messages = []
        st.rerun()
