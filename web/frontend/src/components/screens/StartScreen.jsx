import { useState } from 'react';
import { C } from '../../theme.js';
import { Btn } from '../ui/Btn.jsx';

// ── Rules modal ──────────────────────────────────────────────────────────────
const SECTIONS = [
  {
    key: 'overview',
    label: 'Overview',
    content: [
      { head: 'The Run', body: 'Each run consists of three levels. Every level has three fights — the last of which is a boss. Defeat all three levels to complete your run and unlock the Gladiator Showdown.' },
      { head: 'Between fights', body: 'After each fight you roll dice to score points and upgrade your gladiator. After the third fight of each level you visit the Shop and the Forge before moving on.' },
      { head: 'Gladiator Showdown', body: 'After completing a run you can enter the arena and fight real characters left by other players. Win 2 out of 3 fights per tier to advance. Tiers expand as stronger gladiators conquer them.' },
    ],
  },
  {
    key: 'dice',
    label: 'Dice & Scoring',
    content: [
      { head: 'Your dice', body: 'You start with five standard d6s. You have up to two re-rolls per turn — lock the dice you want to keep, then re-roll the rest.' },
      { head: 'Scoring categories', body: 'Categories mirror classic Yatzy: Ones–Sixes (sum of that face), Three/Four of a Kind (sum of all dice), Full House (25 pts), Small Straight (30 pts), Large Straight (40 pts), Chance (sum of all), and Yatzy (50 pts). Upper section bonus: 35 pts if Ones–Sixes sum ≥ 63.' },
      { head: 'Special dice', body: 'Unlock extra dice through upgrades: d12 (rolls 1–12), d3 (rolls 1–3), Risky Die (0 or 12), Bomb Die (explodes for bonus damage in combat), Mirror Die (copies another die), Logic Die (remembers a face), 2/5 Die (always 2 or 5), and more.' },
    ],
  },
  {
    key: 'upgrades',
    label: 'Upgrades',
    content: [
      { head: 'Upgrade phase', body: 'After each fight you are presented with two upgrade choices — pick one. Each upgrade improves one of your gladiator\'s stats. You also earn gold which can be spent at the Shop.' },
      { head: 'Stats you can improve', body: 'Max HP · Attack Damage · Attack Speed · Crit Chance · Armor · Block Chance · Lifesteal · Dark Level · Summon Level · Spell Level' },
      { head: 'Dark Level', body: 'As you land more hits in a fight, your damage multiplier ramps up. Higher dark level makes the ramp steeper and the peak multiplier higher — big reward for sustained combat.' },
      { head: 'Summon', body: 'High enough Summon Level spawns a creature that fights alongside you: Imp (lvl 1) → Wolf (6) → Orc (12) → Skeleton (18) → Dragon (24). The summon absorbs hits before they reach you.' },
      { head: 'Spells', body: 'Spell Level unlocks and powers up a spell cast automatically every 4 seconds. Higher level = more spell damage.' },
    ],
  },
  {
    key: 'combat',
    label: 'Combat',
    content: [
      { head: 'Auto-battle', body: 'Combat is fully automatic. Your gladiator attacks, casts spells, and your summon strikes — all based on their stats. Watch the Battle Chronicle for a live log of every hit.' },
      { head: 'Attack order', body: 'Both fighters attack simultaneously on their own timers (1 ÷ Attack Speed seconds per swing). Higher Attack Speed = more swings per second.' },
      { head: 'Damage formula', body: 'Each hit: Attack Damage × Dark Multiplier, then reduced by the target\'s Armor %. A critical hit doubles the damage (some items change the multiplier). Blocked hits deal no damage.' },
      { head: 'Summon targeting', body: 'Enemy attacks hit your summon first. Once the summon falls, attacks reach you directly. Same applies to the enemy.' },
      { head: 'Victory', body: 'Reduce the enemy to 0 HP. If the timer expires, the fighter with more HP remaining wins.' },
    ],
  },
  {
    key: 'items',
    label: 'Items',
    content: [
      { head: 'Shop items', body: 'Bought between levels. Each item grants a permanent passive effect for the rest of the run.' },
      { head: 'Forge', body: 'The Forge lets you reroll your upgrade choices or swap out a specific upgrade. Use it to fine-tune your build after each level.' },
      { head: 'Notable items', body: 'Lifesteal +5% · Armor Pen (ignore enemy armor) · Berserker (+20% attack speed below 50% HP) · Crit Freeze (slow enemy on crit) · Block Reflect (bounce blocked damage back) · Spell Fire (spells leave a burn DoT) · HP→ATK (5% of max HP added as attack damage)' },
    ],
  },
];

function RulesModal({ onClose }) {
  const [tab, setTab] = useState('overview');
  const section = SECTIONS.find(s => s.key === tab);

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 200,
        background: 'rgba(0,0,0,0.75)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 16,
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: 'linear-gradient(180deg, #1E1208 0%, #0F0A04 100%)',
          border: `1px solid ${C.border}`,
          borderRadius: 8,
          width: '100%',
          maxWidth: 600,
          maxHeight: '85vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 24px 64px rgba(0,0,0,0.9)',
          fontFamily: "'Cinzel', serif",
        }}
      >
        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '16px 20px 12px',
          borderBottom: `1px solid ${C.borderDim}`,
          flexShrink: 0,
        }}>
          <div>
            <div style={{ fontSize: 10, letterSpacing: 4, color: C.muted, textTransform: 'uppercase', marginBottom: 2 }}>
              Gladiator Codex
            </div>
            <div style={{ fontSize: 18, color: C.gold, letterSpacing: 2, fontFamily: "'Cinzel Decorative', serif" }}>
              How to Play
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none', border: 'none', color: C.muted,
              fontSize: 18, cursor: 'pointer', padding: '4px 8px',
              fontFamily: "'Cinzel', serif",
            }}
          >
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div style={{
          display: 'flex', gap: 0,
          borderBottom: `1px solid ${C.borderDim}`,
          flexShrink: 0,
          overflowX: 'auto',
        }}>
          {SECTIONS.map(s => (
            <button
              key={s.key}
              onClick={() => setTab(s.key)}
              style={{
                background: 'none',
                border: 'none',
                borderBottom: tab === s.key ? `2px solid ${C.gold}` : '2px solid transparent',
                color: tab === s.key ? C.gold : C.muted,
                padding: '10px 16px',
                cursor: 'pointer',
                fontSize: 11,
                fontFamily: "'Cinzel', serif",
                letterSpacing: 1,
                textTransform: 'uppercase',
                whiteSpace: 'nowrap',
                transition: 'color 0.15s',
              }}
            >
              {s.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div style={{ overflowY: 'auto', padding: '20px 24px 24px', flex: 1 }}>
          {section.content.map((item, i) => (
            <div key={i} style={{ marginBottom: i < section.content.length - 1 ? 20 : 0 }}>
              <div style={{
                fontSize: 12, color: C.bronze, letterSpacing: 1.5,
                textTransform: 'uppercase', marginBottom: 6,
                display: 'flex', alignItems: 'center', gap: 8,
              }}>
                <span style={{ color: C.gold, opacity: 0.5 }}>—</span>
                {item.head}
              </div>
              <div style={{
                fontSize: 12.5, color: C.text, lineHeight: 1.75,
                opacity: 0.85,
              }}>
                {item.body}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div style={{
          padding: '12px 20px',
          borderTop: `1px solid ${C.borderDim}`,
          textAlign: 'center',
          flexShrink: 0,
        }}>
          <Btn onClick={onClose} color={C.stone} style={{ fontSize: 11, padding: '7px 24px' }}>
            Close
          </Btn>
        </div>
      </div>
    </div>
  );
}

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
  const [showRules, setShowRules] = useState(false);

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
          <Btn onClick={() => setShowRules(true)} color={C.stone} style={{ fontSize: 12, padding: '10px 18px' }}>
            How to Play
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

      {showRules && <RulesModal onClose={() => setShowRules(false)} />}

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
