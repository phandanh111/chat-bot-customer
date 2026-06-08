def format_chat_history(
    history: list[dict],
    window_size: int,
    max_content_length: int | None = None,
) -> str:
    if not history:
        return ""
    lines = []
    for m in history[-window_size:]:
        role = "Khách" if m["role"] == "user" else "Bot"
        content = m["content"]
        if max_content_length is not None:
            content = content[:max_content_length]
        lines.append(f"{role}: {content}")
    return "Lịch sử hội thoại:\n" + "\n".join(lines) + "\n\n"
