import React from 'react';
import Message from './Message';
import { ask } from '../api';

export default function Chat() {
  const [messages, setMessages] = React.useState(() => {
    const saved = localStorage.getItem('rag_chat_messages');
    return saved ? JSON.parse(saved) : [];
  });
  const [input, setInput] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');

  React.useEffect(() => {
    localStorage.setItem('rag_chat_messages', JSON.stringify(messages));
  }, [messages]);

  const send = async () => {
    const q = input.trim();
    if (!q || loading) return;

    setError('');
    setLoading(true);

    // Push user message + a temporary typing bubble
    setMessages(prev => [
      ...prev,
      { role: 'user', content: q },
      { role: 'assistant', typing: true }
    ]);
    setInput('');

    try {
      const data = await ask(q);
      const content = data?.answer ?? '(no answer)';
      const sources = Array.isArray(data?.sources)
        ? data.sources
        : (typeof data?.sources === 'string' && data.sources.length
            ? data.sources.split('\n').filter(Boolean)
            : []);

      // Replace the last typing bubble with the real answer
      setMessages(prev => {
        const next = [...prev];
        if (next.length && next[next.length - 1]?.typing) next.pop();
        next.push({ role: 'assistant', content, sources });
        return next;
      });
    } catch (e) {
      setError(e?.message || 'Request failed.');
      setMessages(prev => {
        const next = [...prev];
        if (next.length && next[next.length - 1]?.typing) next.pop();
        next.push({ role: 'assistant', content: 'Request failed.' });
        return next;
      });
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!loading) send();
    }
  };

  const clearChat = () => {
    setMessages([]);
    localStorage.removeItem('rag_chat_messages');
    sessionStorage.removeItem('rag_chat_messages');
  };

  return (
    <div className="chat">
      <div className="toolbar">
        <button className="sendbtn" onClick={clearChat} disabled={loading}>Clear</button>
        {loading ? <span>Thinking…</span> : null}
        {error ? <span className="error">• {error}</span> : null}
      </div>
      <div className="messages" id="messages">
        {messages.length === 0 ? (
          <div className="meta">Ask a question about your Documents. Shift+Enter for newline.</div>
        ) : null}
        {messages.map((m, i) => (
          <Message key={i} role={m.role} content={m.content} sources={m.sources} typing={m.typing} />
        ))}
      </div>
      <div className="composer">
        <textarea
          className="textarea"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Type your question…"
          disabled={loading}
        />
        <button className="sendbtn" onClick={send} disabled={loading || !input.trim()}>Send</button>
      </div>
    </div>
  );
}