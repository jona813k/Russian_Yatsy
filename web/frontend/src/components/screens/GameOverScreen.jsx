import { C } from '../../theme.js';
import { Btn } from '../ui/Btn.jsx';

export function GameOverScreen({ run, onRestart }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 400,
    }}>
      <div style={{
        textAlign: 'center',
        maxWidth: 380,
        background: `linear-gradient(180deg, #2A0A0A, #1A0404)`,
        border: `1px solid ${C.crimson}`,
        borderRadius: 8,
        padding: '36px 40px',
        boxShadow: `0 0 40px rgba(155,26,26,0.2)`,
      }}>
        {/* Skull SVG */}
        <svg viewBox="0 0 80 80" width={70} height={70} style={{ marginBottom: 14, display: 'block', margin: '0 auto 14px' }}>
          <circle cx="40" cy="35" r="28" fill="#2A1A0A" />
          <circle cx="40" cy="35" r="24" fill="#E8D5B0" opacity="0.15" />
          <circle cx="29" cy="32" r="8" fill="#1A0A04" />
          <circle cx="51" cy="32" r="8" fill="#1A0A04" />
          <circle cx="29" cy="32" r="5" fill="#3A1A10" />
          <circle cx="51" cy="32" r="5" fill="#3A1A10" />
          <path d="M 35 46 L 34 52 L 36 52 L 37 58 L 43 58 L 44 52 L 46 52 L 45 46 Z" fill="#1A0A04" />
          {[30,34,38,42,46,50].map((x,i) => (
            <rect key={i} x={x} y="55" width="3" height="7" rx="1" fill="#E8D5B0" opacity="0.2" />
          ))}
          <path d="M 24 50 Q 24 62 40 62 Q 56 62 56 50 Z" fill="#E8D5B0" opacity="0.08" />
        </svg>

        <div style={{
          color: C.scarlet,
          fontWeight: '700',
          fontSize: 24,
          fontFamily: "'Cinzel Decorative', serif",
          letterSpacing: 3,
          marginBottom: 10,
          textShadow: `0 0 20px rgba(220,32,32,0.4)`,
        }}>
          Fallen
        </div>

        {/* Decorative line */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '12px 0' }}>
          <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, transparent, ${C.crimson}66)` }} />
          <span style={{ color: C.crimson, fontSize: 12 }}>✝</span>
          <div style={{ flex: 1, height: 1, background: `linear-gradient(270deg, transparent, ${C.crimson}66)` }} />
        </div>

        <div style={{
          color: C.muted,
          fontSize: 12,
          marginBottom: 24,
          fontFamily: "'Cinzel', serif",
          lineHeight: 1.7,
          letterSpacing: 0.5,
        }}>
          You fell on Level {run.level}, Fight {run.fight_index + 1}.<br />
          The crowd grows silent.<br />
          Rise again, gladiator.
        </div>

        <Btn onClick={onRestart} color={C.crimson} style={{ fontSize: 13 }}>
          Return to the Arena
        </Btn>
      </div>
    </div>
  );
}
