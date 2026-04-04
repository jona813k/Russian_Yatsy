import { createRoot } from 'react-dom/client';
import App from './App';

// ── Console log buffer ────────────────────────────────────────────────────────
// Captures the last 150 console entries so they can be included in bug reports.
const LOG_BUFFER_SIZE = 150;
window.__consoleLogs = [];

['log', 'warn', 'error'].forEach(level => {
  const original = console[level].bind(console);
  console[level] = (...args) => {
    original(...args);
    const line = args.map(a => {
      try { return typeof a === 'object' ? JSON.stringify(a) : String(a); }
      catch { return '[unserializable]'; }
    }).join(' ');
    window.__consoleLogs.push(`[${level.toUpperCase()}] ${new Date().toISOString()} ${line}`);
    if (window.__consoleLogs.length > LOG_BUFFER_SIZE) window.__consoleLogs.shift();
  };
});

createRoot(document.getElementById('root')).render(<App />);
