
// Simple API wrapper.
// In dev, CRA's `proxy` forwards to Flask at http://127.0.0.1:8000
// For prod builds, set REACT_APP_API_BASE to your deployed backend URL.
const apiBase = (process.env.REACT_APP_API_BASE || '').replace(/\/+$/, '');

export async function ask(question) {
  const res = await fetch(`${apiBase}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question })
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }

  return res.json();
}