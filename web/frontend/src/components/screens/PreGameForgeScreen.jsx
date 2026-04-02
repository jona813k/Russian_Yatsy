import { useState } from 'react';
import { rpgApi } from '../../api.js';
import { C } from '../../theme.js';

function SpecRow({ choice, onPick, loading }) {
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
        height: 78,
        padding: '11px 14px',
        background: hovered ? 'rgba(212,175,55,0.07)' : 'rgba(15,10,4,0.5)',
        border: `1px solid ${hovered ? C.gold : C.border}`,
        borderRadius: 5,
        cursor: 'pointer',
        transition: 'all 0.12s',
      }}
    >
      {/* Icon */}
      <span style={{ fontSize: 24, lineHeight: 1, flexShrink: 0 }}>{choice.icon}</span>

      {/* Name + desc */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          color: C.yellow,
          fontWeight: '700',
          fontSize: 15,
          fontFamily: "'Cinzel', serif",
          letterSpacing: 0.5,
          marginBottom: 3,
        }}>
          {choice.name}
        </div>
        <div style={{
          color: '#c8b87a',
          fontSize: 13,
          fontFamily: "'Cinzel', serif",
          letterSpacing: 0.3,
        }}>
          {choice.desc}
        </div>
      </div>

      {/* Button */}
      <button
        onClick={e => { e.stopPropagation(); onPick(choice.id); }}
        disabled={loading}
        style={{
          flexShrink: 0,
          background: hovered ? C.crimson : 'rgba(155,26,26,0.6)',
          color: C.sand,
          border: `1px solid ${C.crimson}`,
          borderRadius: 4,
          padding: '6px 14px',
          fontSize: 13,
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

export function PreGameForgeScreen({ run, runId, onRunUpdate, onError }) {
  const [loading, setLoading] = useState(false);
  const choices = run.pre_game_forge_choices || [];

  async function pick(choiceId) {
    setLoading(true);
    try {
      const resp = await rpgApi.preGameForgePick(runId, choiceId);
      onRunUpdate(resp);
    } catch (e) { if (onError) onError(e); else console.error(e); }
    setLoading(false);
  }

  return (
    <div style={{
      background: `linear-gradient(180deg, #1E1208, #130A04)`,
      border: `1px solid ${C.gold}`,
      borderRadius: 6,
      overflow: 'hidden',
    }}>
      {/* Compact header */}
      <div style={{
        background: `linear-gradient(90deg, #3A2808, #281A04)`,
        borderBottom: `1px solid ${C.gold}55`,
        padding: '8px 12px',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}>
        <span style={{ color: C.gold, fontSize: 18 }}>⚗</span>
        <span style={{
          color: C.gold,
          fontWeight: '700',
          fontSize: 16,
          fontFamily: "'Cinzel', serif",
          letterSpacing: 1,
        }}>
          Choose Your Path
        </span>
        <span style={{ color: C.muted, fontSize: 13, fontFamily: "'Cinzel', serif", marginLeft: 4 }}>
          — shapes your upgrade board for the entire run
        </span>
      </div>

      {/* Choice rows */}
      <div style={{ padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 6 }}>
        {choices.map(choice => (
          <SpecRow key={choice.id} choice={choice} onPick={pick} loading={loading} />
        ))}
      </div>
    </div>
  );
}
