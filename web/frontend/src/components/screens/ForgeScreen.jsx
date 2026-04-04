import { useState } from 'react';
import { rpgApi } from '../../api.js';
import { C } from '../../theme.js';

function ForgeRow({ choice, gold, onPick, onReroll, loading }) {
  const [hovered, setHovered] = useState(false);
  const canReroll = gold >= 50;
  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '9px 12px',
        background: hovered ? 'rgba(122,58,154,0.12)' : 'rgba(10,4,20,0.6)',
        border: `1px solid ${hovered ? C.purple : C.purple + '55'}`,
        borderRadius: 5,
        cursor: 'default',
        transition: 'all 0.12s',
      }}
    >
      {/* Icon */}
      <span style={{
        fontSize: 20, lineHeight: 1, flexShrink: 0,
        filter: 'drop-shadow(0 0 4px rgba(192,132,252,0.4))',
      }}>
        {choice.icon}
      </span>

      {/* Name + info icon */}
      <span style={{
        flex: 1,
        color: C.yellow,
        fontWeight: '600',
        fontSize: 13,
        fontFamily: "'Cinzel', serif",
        letterSpacing: 0.5,
        display: 'flex',
        alignItems: 'center',
        gap: 5,
      }}>
        {choice.name}
        <span
          title={choice.desc}
          style={{
            color: C.muted,
            fontSize: 13,
            cursor: 'help',
            lineHeight: 1,
            userSelect: 'none',
          }}
        >
          ℹ
        </span>
      </span>

      {/* Reroll button */}
      <button
        onClick={() => !loading && onReroll(choice.id)}
        disabled={loading || !canReroll}
        title={canReroll ? 'Replace this option with something unseen (50g)' : 'Need 50g to reroll'}
        style={{
          flexShrink: 0,
          background: canReroll ? 'rgba(60,40,80,0.5)' : 'rgba(30,20,40,0.3)',
          color: canReroll ? C.muted : C.mutedDim,
          border: `1px solid ${canReroll ? C.purple + '66' : C.purple + '22'}`,
          borderRadius: 4,
          padding: '3px 8px',
          fontSize: 10,
          fontFamily: "'Cinzel', serif",
          letterSpacing: 0.5,
          cursor: loading || !canReroll ? 'default' : 'pointer',
          transition: 'all 0.12s',
          whiteSpace: 'nowrap',
        }}
      >
        🔄 50g
      </button>

      {/* Choose button */}
      <button
        onClick={() => !loading && onPick(choice.id)}
        disabled={loading}
        style={{
          flexShrink: 0,
          background: hovered ? C.purple : 'rgba(122,58,154,0.4)',
          color: C.sand,
          border: `1px solid ${C.purple}`,
          borderRadius: 4,
          padding: '4px 12px',
          fontSize: 11,
          fontFamily: "'Cinzel', serif",
          fontWeight: '600',
          letterSpacing: 1,
          textTransform: 'uppercase',
          cursor: loading ? 'default' : 'pointer',
          transition: 'all 0.12s',
        }}
      >
        Choose
      </button>
    </div>
  );
}

export function ForgeScreen({ run, runId, onRunUpdate, onError }) {
  const [loading, setLoading] = useState(false);
  const choices = run.forge_choices || [];
  const gold = run.player?.gold ?? 0;

  async function pick(choiceId) {
    setLoading(true);
    try {
      const resp = await rpgApi.forgePick(runId, choiceId);
      onRunUpdate(resp);
    } catch (e) { if (onError) onError(e); else console.error(e); }
    setLoading(false);
  }

  async function reroll(choiceId) {
    setLoading(true);
    try {
      const resp = await rpgApi.forgeReroll(runId, choiceId);
      onRunUpdate(resp);
    } catch (e) { if (onError) onError(e); else console.error(e); }
    setLoading(false);
  }

  return (
    <div style={{
      background: `linear-gradient(180deg, #180828, #0E0618)`,
      border: `1px solid ${C.purple}`,
      borderRadius: 6,
      overflow: 'hidden',
      boxShadow: `0 0 20px rgba(122,58,154,0.15)`,
    }}>
      {/* Header */}
      <div style={{
        background: `linear-gradient(90deg, #2A1A40, #1E1030)`,
        borderBottom: `1px solid ${C.purple}55`,
        padding: '8px 12px',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}>
        <span style={{ color: C.purple, fontSize: 14 }}>⚒</span>
        <span style={{
          color: C.purple, fontWeight: '700', fontSize: 13,
          fontFamily: "'Cinzel', serif", letterSpacing: 1,
        }}>
          The Forge
        </span>
        <span style={{ color: C.muted, fontSize: 11, fontFamily: "'Cinzel', serif", marginLeft: 4 }}>
          — the champion has fallen. Pick one gift.
        </span>
        <span style={{
          marginLeft: 'auto',
          color: C.gold, fontSize: 12, fontFamily: 'monospace', fontWeight: '600',
          background: 'rgba(212,175,55,0.1)', border: `1px solid ${C.gold}44`,
          borderRadius: 3, padding: '1px 7px',
        }}>
          {gold}g
        </span>
      </div>

      {/* Choice rows */}
      <div style={{ padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 6 }}>
        {choices.map(choice => (
          <ForgeRow
            key={choice.id}
            choice={choice}
            gold={gold}
            onPick={pick}
            onReroll={reroll}
            loading={loading}
          />
        ))}
      </div>
    </div>
  );
}
