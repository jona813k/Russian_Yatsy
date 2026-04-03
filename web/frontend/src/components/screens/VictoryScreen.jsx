import { useState } from 'react';
import { rpgApi, gladiatorApi } from '../../api.js';
import { C } from '../../theme.js';
import { Btn } from '../ui/Btn.jsx';

export function VictoryScreen({ run, runId, onRestart, onGauntlet }) {
  const [gladLoading, setGladLoading] = useState(false);
  const [gladError, setGladError]     = useState(null);
  const [statusMsg, setStatusMsg]     = useState(null);

  const hasKey = run.player.has_gladiator_key;

  async function enterShowdown() {
    setGladLoading(true);
    setGladError(null);
    try {
      const status = await gladiatorApi.getStatus();
      if (!status.active) {
        setStatusMsg(`Showdown locked — only ${status.character_count} of ${status.required} champions registered.`);
        setGladLoading(false);
        return;
      }
      const gauntlet = await rpgApi.gladiatorEnter(runId);
      onGauntlet(gauntlet);
    } catch (e) {
      setGladError(e.message || 'Could not enter the showdown.');
    }
    setGladLoading(false);
  }
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 400,
    }}>
      <div style={{
        textAlign: 'center',
        maxWidth: 400,
        background: `linear-gradient(180deg, #1E1A04, #130E02)`,
        border: `1px solid ${C.gold}`,
        borderRadius: 8,
        padding: '36px 40px',
        boxShadow: `0 0 50px rgba(212,175,55,0.2)`,
      }}>
        {/* Laurel wreath SVG */}
        <svg viewBox="0 0 100 80" width={90} height={72} style={{ display: 'block', margin: '0 auto 14px' }}>
          {/* Left laurel */}
          {[0,1,2,3,4].map(i => {
            const angle = -40 + i * 20;
            const rad = angle * Math.PI / 180;
            const cx = 20 + Math.cos(rad) * 20;
            const cy = 50 + Math.sin(rad) * 15;
            return (
              <ellipse key={i} cx={cx} cy={cy} rx={10} ry={5}
                transform={`rotate(${angle + 90}, ${cx}, ${cy})`}
                fill="#3A6A1A" opacity="0.8" />
            );
          })}
          {/* Right laurel */}
          {[0,1,2,3,4].map(i => {
            const angle = 40 - i * 20;
            const rad = angle * Math.PI / 180;
            const cx = 80 - Math.cos(rad) * 20;
            const cy = 50 + Math.sin(Math.abs(rad)) * 15;
            return (
              <ellipse key={i} cx={cx} cy={cy} rx={10} ry={5}
                transform={`rotate(${-angle - 90}, ${cx}, ${cy})`}
                fill="#3A6A1A" opacity="0.8" />
            );
          })}
          {/* Trophy */}
          <path d="M 40 15 Q 40 5 50 5 Q 60 5 60 15 L 58 35 Q 58 45 50 48 Q 42 45 42 35 Z" fill="#D4AF37" />
          <rect x="46" y="45" width="8" height="12" fill="#C8A030" />
          <rect x="40" y="55" width="20" height="4" rx="2" fill="#D4AF37" />
          {/* Stars */}
          {[[22,18],[78,18],[50,8]].map(([x,y],i) => (
            <circle key={i} cx={x} cy={y} r={3} fill="#E8C84A" opacity="0.9" />
          ))}
        </svg>

        <div style={{
          color: C.gold,
          fontWeight: '700',
          fontSize: 26,
          fontFamily: "'Cinzel Decorative', serif",
          letterSpacing: 3,
          marginBottom: 8,
          textShadow: `0 0 25px rgba(212,175,55,0.5)`,
        }}>
          Champion!
        </div>

        {/* Decorative line */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '12px 0' }}>
          <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, transparent, ${C.gold}66)` }} />
          <span style={{ color: C.gold, fontSize: 14 }}>⚔</span>
          <div style={{ flex: 1, height: 1, background: `linear-gradient(270deg, transparent, ${C.gold}66)` }} />
        </div>

        <div style={{
          color: C.textDim,
          fontSize: 12,
          marginBottom: 8,
          fontFamily: "'Cinzel', serif",
          lineHeight: 1.7,
          letterSpacing: 0.5,
        }}>
          You have conquered all three levels.<br />
          The arena erupts in your name.
        </div>

        <div style={{
          color: C.green,
          fontSize: 13,
          fontFamily: 'monospace',
          marginBottom: 24,
          background: 'rgba(74,154,90,0.1)',
          border: `1px solid ${C.green}44`,
          borderRadius: 4,
          padding: '6px 12px',
          display: 'inline-block',
        }}>
          {Math.round(run.player.current_hp)} HP remaining
        </div>

        {/* Gladiator Showdown entry */}
        {hasKey && (
          <div style={{ marginBottom: 16 }}>
            <div style={{
              fontSize: 11, color: C.gold, letterSpacing: 2,
              textTransform: 'uppercase', marginBottom: 10, opacity: 0.8,
            }}>
              ⚔ Gladiator Showdown
            </div>
            {statusMsg && (
              <div style={{ color: C.muted, fontSize: 11, marginBottom: 8 }}>{statusMsg}</div>
            )}
            {gladError && (
              <div style={{ color: C.scarlet, fontSize: 11, marginBottom: 8 }}>{gladError}</div>
            )}
            <Btn
              onClick={enterShowdown}
              disabled={gladLoading}
              color={C.crimson}
              style={{ fontSize: 12, padding: '8px 20px', letterSpacing: 1, marginBottom: 8, width: '100%' }}
            >
              {gladLoading ? 'Entering…' : 'Enter the Showdown'}
            </Btn>
          </div>
        )}

        {!hasKey && (
          <div style={{
            color: C.muted, fontSize: 11, marginBottom: 16,
            padding: '6px 10px',
            background: 'rgba(0,0,0,0.3)',
            borderRadius: 4,
            border: `1px solid ${C.borderDim}`,
          }}>
            No Gladiator Key — run not recorded.
          </div>
        )}

        <br />
        <Btn onClick={onRestart} color={C.gold} style={{ fontSize: 13, color: C.dark }}>
          Fight Again
        </Btn>
      </div>
    </div>
  );
}
