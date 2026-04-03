import { useState } from 'react';
import { C } from '../../theme.js';
import { Btn } from '../ui/Btn.jsx';

// Colosseum arch SVG decoration
function ColossumArch({ style }) {
  return (
    <svg viewBox="0 0 400 120" style={{ width: '100%', ...style }} preserveAspectRatio="none">
      {/* Stone blocks */}
      {Array.from({ length: 8 }, (_, i) => (
        <rect key={i} x={i * 50} y={60} width={48} height={58} rx={1}
          fill={i % 2 === 0 ? '#2A1A08' : '#221208'} />
      ))}
      {/* Arch pillars */}
      <rect x={0} y={0} width={50} height={120} fill="#1E1008" />
      <rect x={350} y={0} width={50} height={120} fill="#1E1008" />
      {/* Arch curve */}
      <path d="M 50 120 Q 50 10 200 10 Q 350 10 350 120 Z" fill="#0F0A04" />
      {/* Arch stones */}
      {Array.from({ length: 12 }, (_, i) => {
        const angle = (i / 11) * Math.PI;
        const cx = 200 + Math.cos(Math.PI - angle) * 150;
        const cy = 10 + Math.sin(angle) * 80;
        return (
          <ellipse key={i} cx={cx} cy={cy} rx={18} ry={9}
            transform={`rotate(${(i / 11) * 180 - 90}, ${cx}, ${cy})`}
            fill={i % 2 === 0 ? '#2A1A08' : '#221208'}
          />
        );
      })}
      {/* Sand floor */}
      <path d="M 50 110 Q 200 100 350 110 L 350 120 L 50 120 Z" fill="#8A6A3A" opacity="0.6" />
      {/* Torch lights */}
      {[80, 320].map((x, i) => (
        <g key={i}>
          <rect x={x} y={20} width={6} height={20} rx={2} fill="#6B3A10" />
          <ellipse cx={x+3} cy={18} rx={5} ry={8} fill="#D4722A" opacity="0.9" />
          <ellipse cx={x+3} cy={14} rx={3} ry={6} fill="#E8C84A" opacity="0.8" />
        </g>
      ))}
      {/* Crowd silhouette */}
      {Array.from({ length: 28 }, (_, i) => {
        const x = 10 + i * 14;
        const y = 55 + Math.sin(i * 1.3) * 4;
        const h = 12 + Math.sin(i * 0.8) * 4;
        return <ellipse key={i} cx={x} cy={y} rx={5} ry={h} fill="#1A0C04" opacity="0.7" />;
      })}
    </svg>
  );
}

export function StartScreen({ onStart, onHistory, onBack, loading, error }) {
  const [name, setName] = useState('');

  return (
    <div style={{
      minHeight: '100vh',
      background: `radial-gradient(ellipse at 50% 40%, #2A1408 0%, #0F0A04 60%)`,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: "'Cinzel', serif",
      color: C.text,
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Background torch glow */}
      <div style={{
        position: 'absolute',
        top: '20%',
        left: '15%',
        width: 200,
        height: 300,
        background: 'radial-gradient(ellipse, rgba(212,114,42,0.12) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute',
        top: '20%',
        right: '15%',
        width: 200,
        height: 300,
        background: 'radial-gradient(ellipse, rgba(212,114,42,0.12) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      {/* Colosseum arch */}
      <div style={{ width: '100%', maxWidth: 600, marginBottom: -20, position: 'relative', zIndex: 1 }}>
        <ColossumArch />
      </div>

      {/* Main content card */}
      <div style={{
        position: 'relative',
        zIndex: 2,
        textAlign: 'center',
        padding: '48px 56px 40px',
        background: `linear-gradient(180deg, rgba(30,18,8,0.95) 0%, rgba(15,10,4,0.98) 100%)`,
        border: `1px solid ${C.border}`,
        borderRadius: 8,
        maxWidth: 480,
        width: '90%',
        boxShadow: '0 20px 60px rgba(0,0,0,0.8)',
      }}>
        {/* Corner accents */}
        {[
          { top: 4, left: 4, borderTop: true, borderLeft: true },
          { top: 4, right: 4, borderTop: true, borderRight: true },
          { bottom: 4, left: 4, borderBottom: true, borderLeft: true },
          { bottom: 4, right: 4, borderBottom: true, borderRight: true },
        ].map((corner, i) => (
          <div key={i} style={{
            position: 'absolute',
            top: corner.top, right: corner.right, bottom: corner.bottom, left: corner.left,
            width: 16, height: 16,
            borderTop: corner.borderTop ? `2px solid ${C.gold}` : undefined,
            borderLeft: corner.borderLeft ? `2px solid ${C.gold}` : undefined,
            borderBottom: corner.borderBottom ? `2px solid ${C.gold}` : undefined,
            borderRight: corner.borderRight ? `2px solid ${C.gold}` : undefined,
            opacity: 0.7,
          }} />
        ))}

        {/* Title */}
        <div style={{ fontSize: 11, letterSpacing: 5, color: C.muted, textTransform: 'uppercase', marginBottom: 8 }}>
          The Arena Awaits
        </div>
        <h1 style={{
          fontFamily: "'Cinzel Decorative', 'Cinzel', serif",
          fontSize: 28,
          color: C.gold,
          marginBottom: 4,
          textShadow: `0 0 30px rgba(212,175,55,0.4)`,
          lineHeight: 1.2,
          letterSpacing: 2,
        }}>
          Russian Yatzy
        </h1>
        <div style={{
          fontSize: 15,
          color: C.bronze,
          letterSpacing: 4,
          textTransform: 'uppercase',
          marginBottom: 8,
        }}>
          Gladiator
        </div>

        {/* Divider */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '16px 0' }}>
          <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, transparent, ${C.gold}55)` }} />
          <span style={{ color: C.gold, fontSize: 16 }}>⚔</span>
          <div style={{ flex: 1, height: 1, background: `linear-gradient(270deg, transparent, ${C.gold}55)` }} />
        </div>

        <p style={{ color: C.muted, fontSize: 12, marginBottom: 20, lineHeight: 1.7, letterSpacing: 0.5 }}>
          Roll your dice between battles.<br />
          Grow stronger. Survive three levels.<br />
          Claim glory in the arena.
        </p>

        {/* Gladiator name input */}
        <div style={{ marginBottom: 20 }}>
          <input
            type="text"
            placeholder="Enter your gladiator name…"
            value={name}
            onChange={e => setName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !loading && onStart(name.trim() || 'Anonymous')}
            maxLength={32}
            style={{
              width: '100%',
              boxSizing: 'border-box',
              padding: '9px 14px',
              background: 'rgba(15,10,4,0.8)',
              border: `1px solid ${name.trim() ? C.gold + '88' : C.borderDim}`,
              borderRadius: 4,
              color: name.trim() ? C.text : C.muted,
              fontFamily: "'Cinzel', serif",
              fontSize: 13,
              letterSpacing: 1,
              outline: 'none',
              transition: 'border-color 0.2s',
            }}
          />
        </div>

        {error && (
          <div style={{
            color: C.scarlet,
            marginBottom: 16,
            fontSize: 12,
            padding: '8px 12px',
            background: 'rgba(155,26,26,0.15)',
            borderRadius: 4,
            border: `1px solid ${C.crimson}`,
          }}>
            {error}
          </div>
        )}

        <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Btn onClick={() => onStart(name.trim() || 'Anonymous')} disabled={loading} color={C.crimson} style={{ fontSize: 13, padding: '10px 28px', letterSpacing: 2 }}>
            {loading ? 'Entering Arena…' : 'Enter the Arena'}
          </Btn>
          <Btn onClick={onHistory} color={C.stone} style={{ fontSize: 12, padding: '10px 18px' }}>
            History
          </Btn>
          {onBack && (
            <Btn onClick={onBack} color={C.stone} style={{ fontSize: 12, padding: '10px 18px' }}>
              ← Back
            </Btn>
          )}
        </div>
      </div>

      {/* Sand floor */}
      <div style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        height: 80,
        background: `linear-gradient(180deg, transparent, rgba(140,106,58,0.25))`,
        pointerEvents: 'none',
      }} />
    </div>
  );
}
