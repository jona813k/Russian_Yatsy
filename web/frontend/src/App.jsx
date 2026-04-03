import { useState } from 'react';
import RpgApp from './RpgApp';
import ClassicGame from './components/screens/ClassicGame';

function ModeSelect({ onSelect }) {
  return (
    <div style={{
      minHeight: '100vh', background: '#1a1a2e', display: 'flex',
      flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      fontFamily: 'monospace', color: '#e0e0e0',
    }}>
      <h1 style={{ color: '#f1c40f', marginBottom: 8 }}>Russian Yatzy</h1>
      <p style={{ color: '#888', marginBottom: 32 }}>Choose a mode</p>
      <div style={{ display: 'flex', gap: 24 }}>
        <button onClick={() => onSelect('classic')} style={{
          background: '#2e86c1', color: '#fff', border: 'none', borderRadius: 8,
          padding: '20px 36px', fontSize: 18, cursor: 'pointer', fontFamily: 'monospace',
        }}>
          🎲 Classic
          <div style={{ fontSize: 12, color: '#cde', marginTop: 6 }}>Pure Yatzy game</div>
        </button>
        <button onClick={() => onSelect('adventure')} style={{
          background: '#c0392b', color: '#fff', border: 'none', borderRadius: 8,
          padding: '20px 36px', fontSize: 18, cursor: 'pointer', fontFamily: 'monospace',
        }}>
          ⚔️ Adventure
          <div style={{ fontSize: 12, color: '#fcc', marginTop: 6 }}>RPG roguelike</div>
        </button>
      </div>
    </div>
  );
}

export default function App() {
  const [mode, setMode] = useState(null);

  if (!mode)        return <ModeSelect onSelect={setMode} />;
  if (mode === 'adventure') return <RpgApp onBack={() => setMode(null)} />;
  return <ClassicGame />;
}
