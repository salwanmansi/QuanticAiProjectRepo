import React from 'react';
import clsx from 'clsx';

function formatSourceLine(s) {
  if (!s) return 'unknown';

  // Backward compatibility: if sources are strings, just show them.
  if (typeof s === 'string') return s;

  const src = s.source ?? 'unknown';
  const page = s.page != null ? `, page ${s.page}` : '';
  const score = typeof s.score === 'number' ? ` • score ${s.score}` : '';
  return `${src}${page}${score}`;
}

export default function Message({ role, content, sources, typing }) {
  const isUser = role === 'user';

  return (
    <div className={clsx('bubble', isUser ? 'bubble--user' : 'bubble--ai')}>
      {typing ? (
        <div className="typing">
          <span className="dot" />
          <span className="dot" />
          <span className="dot" />
        </div>
      ) : (
        <div>{content}</div>
      )}

      {!isUser && !typing && Array.isArray(sources) && sources.length ? (
        <div className="sources">
          {sources.map((s, idx) => {
            const line = formatSourceLine(s);
            const snippet =
              typeof s === 'object' && s?.snippet ? String(s.snippet).trim() : '';

            return (
              <div key={idx} className="sourceItem">
                <div className="sourceLine">{line}</div>
                {snippet ? <div className="sourceSnippet">{snippet}</div> : null}
              </div>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}