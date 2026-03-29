"""Test the chat SSE endpoint with both a simple and tool-calling query."""
import httpx


def test_chat(label: str, messages: list[dict], thread_id: str, filename: str):
    """Send a chat request and save the raw SSE output."""
    print(f'[{label}] Sending request...')
    resp = httpx.post(
        'http://localhost:8000/api/chat',
        json={
            'messages': messages,
            'thread_id': thread_id,
        },
        timeout=120,
    )
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f'Status: {resp.status_code}\n')
        f.write(f'Content-Type: {resp.headers.get("content-type", "")}\n')
        f.write(f'x-vercel-ai-ui-message-stream: {resp.headers.get("x-vercel-ai-ui-message-stream", "")}\n')
        f.write('---\n')
        f.write(resp.text)
    print(f'[{label}] Done → {filename} ({resp.status_code})')


# Test 1: Simple direct response (no tools)
test_chat(
    label='Simple',
    messages=[{'role': 'user', 'content': 'What can you help me with?'}],
    thread_id='test-simple-001',
    filename='sse_test_simple.txt',
)

# Test 2: Tool-calling query (flights + hotels)
test_chat(
    label='Tools',
    messages=[{'role': 'user', 'content': 'Find me cheap flights from Delhi to Goa for next week Wednesday to Sunday'}],
    thread_id='test-tools-001',
    filename='sse_test_tools.txt',
)

print('All tests completed!')
