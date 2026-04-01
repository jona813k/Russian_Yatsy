import { useState } from 'react';
import { rpgApi } from '../../api.js';
import { C } from '../../theme.js';
import { Btn } from '../ui/Btn.jsx';

function SpecCard({ choice, onPick, loading }) {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered
          ? `linear-gradient(135deg, #281A06, #1C1004)`
          : `linear-gradient(135deg, #1E1208, #130A04)`,
        border: `1px solid ${hovered ? C.gold : C.border}`,
        borderRadius: 8,
        padding: '14px 16px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: 14,
        transition: 'all 0.15s',
        cursor: 'pointer',
        boxShadow: hovered ? `0 0 18px rgba(212,175,55,0.12)` : 'none',
      }}
      onClick={() => !loading && onPick(choice.id)}
    >
      <div style={{
        fontSize: 30,
        lineHeight: 1,
        flexShrink: 0,
        filter: 'drop-shadow(0 0 4px rgba(212,175,55,0.4))',
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
          lineHeight: 1.6,
          letterSpacing: 0.3,
        }}>
          {choice.desc}
        </div>
        <Btn
          onClick={(e) => { e.stopPropagation(); onPick(choice.id); }}
          disabled={loading}
          color={C.crimson}
          style={{ fontSize: 12, padding: '6px 16px' }}
        >
          Choose Path
        </Btn>
      </div>
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
    <div style={{ maxWidth: 540 }}>
      <div style={{
        background: `linear-gradient(180deg, #1E1208, #130A04)`,
        border: `1px solid ${C.gold}`,
        borderRadius: 8,
        overflow: 'hidden',
        boxShadow: `0 0 30px rgba(212,175,55,0.1)`,
      }}>
        {/* Header */}
        <div style={{
          background: `linear-gradient(90deg, #3A2808, #281A04)`,
          borderBottom: `1px solid ${C.gold}66`,
          padding: '16px 18px',
        }}>
          <div style={{
            color: C.gold,
            fontWeight: '700',
            fontSize: 20,
            fontFamily: "'Cinzel Decorative', serif",
            letterSpacing: 2,
            marginBottom: 6,
          }}>
            Choose Your Path
          </div>
          <div style={{ color: C.muted, fontSize: 12, fontFamily: "'Cinzel', serif", lineHeight: 1.6, letterSpacing: 0.3 }}>
            Every gladiator has a style. Choose your specialisation before your first battle —
            it shapes your upgrade board for the entire run. Some paths remove stats, but those
            dice still count for pair combinations.
          </div>
        </div>

        <div style={{ padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {choices.map(choice => (
            <SpecCard key={choice.id} choice={choice} onPick={pick} loading={loading} />
          ))}
        </div>
      </div>
    </div>
  );
}
