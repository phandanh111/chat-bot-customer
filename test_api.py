import httpx
import sys

payload = {
    "question": "test",
    "history": [{"role": "user", "content": "hello"}] * 31
}

res = httpx.post('http://localhost:8000/api/chat', json=payload)
print(res.status_code)
print(res.text)
