import { useState } from 'react';
import { rpgApi } from '../../api.js';
import { C } from '../../theme.js';

function ForgeRow({ choice, onPick, loading }) {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => !loading && onPick(choice.id)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '9px 12px',
        background: hovered ? 'rgba(122,58,154,0.12)' : 'rgba(10,4,20,0.6)',
        border: `1px solid ${hovered ? C.purple : C.purple + '55'}`,
        borderRadius: 5,
        cursor: 'pointer',
        transition: 'all 0.12s',
      }}
    >
      {/* Icon */}
      <span style={{
        fontSize: 20,
        lineHeight: 1,
        flexShrink: 0,
        filter: 'drop-shadow(0 0 4px rgba(192,132,252,0.4))',
      }}>
        {choice.icon}
      </span>

      {/* Name */}
      <span style={{
        flex: 1,
        color: C.yellow,
        fontWeight: '600',
        fontSize: 13,
        fontFamily: "'Cinzel', serif",
        letterSpacing: 0.5,
      }}>
        {choice.name}
      </span>

      {/* Info icon */}
      <span
        title={choice.desc}
        onClick={e => e.stopPropagation()}
        style={{
          flexShrink: 0,
          color: C.muted,
          fontSize: 14,
          cursor: 'help',
          lineHeight: 1,
          padding: '0 4px',
        }}
      >
        ℹ
      </span>

      {/* Button */}
      <button
        onClick={e => { e.stopPropagation(); onPick(choice.id); }}
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

  async function reroll() {
    setLoading(true);
    try {
      const resp = await rpgApi.forgeReroll(runId);
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
      {/* Compact header */}
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
          color: C.purple,
          fontWeight: '700',
          fontSize: 13,
          fontFamily: "'Cinzel', serif",
          letterSpacing: 1,
        }}>
          The Forge
        </span>
        <span style={{ color: C.muted, fontSize: 11, fontFamily: "'Cinzel', serif", marginLeft: 4 }}>
          — the champion has fallen. Pick one gift.
        </span>
        <button
          onClick={reroll}
          disabled={loading || gold < 50}
          title={gold < 50 ? 'Need 50g to reroll' : 'Replace one choice with an unseen option'}
          style={{
            marginLeft: 'auto',
            background: gold >= 50 ? 'rgba(122,58,154,0.4)' : 'rgba(60,40,80,0.3)',
            color: gold >= 50 ? C.sand : C.muted,
            border: `1px solid ${gold >= 50 ? C.purple : C.purple + '44'}`,
            borderRadius: 4,
            padding: '3px 10px',
            fontSize: 11,
            fontFamily: "'Cinzel', serif",
            fontWeight: '600',
            letterSpacing: 0.5,
            cursor: loading || gold < 50 ? 'default' : 'pointer',
            whiteSpace: 'nowrap',
          }}
        >
          Reroll (50g)
        </button>
      </div>

      {/* Choice rows */}
      <div style={{ padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 6 }}>
        {choices.map(choice => (
          <ForgeRow key={choice.id} choice={choice} onPick={pick} loading={loading} />
        ))}
      </div>
    </div>
  );
}
