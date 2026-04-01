import { useState } from 'react';
import { rpgApi } from '../../api.js';
import { C } from '../../theme.js';
import { Btn } from '../ui/Btn.jsx';

function ForgeCard({ choice, onPick, loading }) {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered
          ? `linear-gradient(135deg, #200A30, #160820)`
          : `linear-gradient(135deg, #180828, #0E0618)`,
        border: `1px solid ${hovered ? C.purple : C.purple + '66'}`,
        borderRadius: 8,
        padding: 16,
        display: 'flex',
        alignItems: 'flex-start',
        gap: 14,
        transition: 'all 0.15s',
        boxShadow: hovered ? `0 0 20px rgba(122,58,154,0.2)` : 'none',
        cursor: 'pointer',
      }}
      onClick={() => !loading && onPick(choice.id)}
    >
      {/* Icon */}
      <div style={{
        fontSize: 28,
        lineHeight: 1,
        flexShrink: 0,
        filter: 'drop-shadow(0 0 6px rgba(192,132,252,0.5))',
      }}>
        {choice.icon}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{
          color: C.yellow,
          fontWeight: '700',
          fontSize: 14,
          fontFamily: "'Cinzel', serif",
          marginBottom: 5,
          letterSpacing: 0.5,
        }}>
          {choice.name}
        </div>
        <div style={{
          color: C.muted,
          fontSize: 12,
          fontFamily: "'Cinzel', serif",
          marginBottom: 10,
          lineHeight: 1.5,
          letterSpacing: 0.3,
        }}>
          {choice.desc}
        </div>
        <Btn
          onClick={(e) => { e.stopPropagation(); onPick(choice.id); }}
          disabled={loading}
          color={C.purple}
          style={{ fontSize: 12, padding: '6px 16px' }}
        >
          Choose
        </Btn>
      </div>
    </div>
  );
}

export function ForgeScreen({ run, runId, onRunUpdate, onError }) {
  const [loading, setLoading] = useState(false);
  const choices = run.forge_choices || [];

  async function pick(choiceId) {
    setLoading(true);
    try {
      const resp = await rpgApi.forgePick(runId, choiceId);
      onRunUpdate(resp);
    } catch (e) { if (onError) onError(e); else console.error(e); }
    setLoading(false);
  }

  return (
    <div style={{ maxWidth: 500 }}>
      <div style={{
        background: `linear-gradient(180deg, #180828, #0E0618)`,
        border: `1px solid ${C.purple}`,
        borderRadius: 8,
        overflow: 'hidden',
        boxShadow: `0 0 30px rgba(122,58,154,0.2)`,
      }}>
        {/* Header */}
        <div style={{
          background: `linear-gradient(90deg, #2A1A40, #1E1030)`,
          borderBottom: `1px solid ${C.purple}66`,
          padding: '14px 18px',
        }}>
          <div style={{
            color: C.purple,
            fontWeight: '700',
            fontSize: 18,
            fontFamily: "'Cinzel Decorative', serif",
            letterSpacing: 2,
            marginBottom: 4,
          }}>
            ⚒ The Forge
          </div>
          <div style={{ color: C.muted, fontSize: 12, fontFamily: "'Cinzel', serif", letterSpacing: 0.5 }}>
            The champion has fallen. The forge-master offers you one gift.
          </div>
        </div>

        <div style={{ padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {choices.map(choice => (
            <ForgeCard key={choice.id} choice={choice} onPick={pick} loading={loading} />
          ))}
        </div>
      </div>
    </div>
  );
}
