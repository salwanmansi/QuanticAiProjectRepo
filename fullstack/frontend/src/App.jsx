
import React from 'react';
import Chat from './components/Chat';

export default function App() {
  return (
    <div className="app">
      <header className="app__header">
        <div className="app__title">Quantic AI Project</div>
        <div className="app__subtitle">Atlas Systems Group - Policy Bot</div>
      </header>
      <Chat />
      <footer className="app__footer">
        <span>all‑MiniLM‑L6‑v2 embeddings · gemma‑3‑27b‑it via OpenRouter</span>
      </footer>
    </div>
  );
}
