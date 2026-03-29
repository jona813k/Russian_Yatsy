/**
 * RPG Adventure mode — full game loop built on top of the Russian Yatzy engine.
 * Phases: upgrade → combat → (shop after boss) → repeat × 3 levels
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { rpgApi, RunExpiredError } from './api';

// ---------------------------------------------------------------------------
// Colours (matching the existing Yatzy palette)
// ---------------------------------------------------------------------------
const C = {
  bg:        '#1a1a2e',
  panel:     '#16213e',
  border:    '#0f3460',
  green:     '#3a9e5f',
  orange:    '#e07b2a',
  blue:      '#2e86c1',
  yellow:    '#ffe066',
  red:       '#c0392b',
  gold:      '#f1c40f',
  purple:    '#8e44ad',
  text:      '#e0e0e0',
  muted:     '#888',
  dark:      '#111',
};

const NUMBER_NAMES = {
  1: 'Ones', 2: 'Twos', 3: 'Threes', 4: 'Fours', 5: 'Fives', 6: 'Sixes',
  7: 'Sevens', 8: 'Eights', 9: 'Nines', 10: 'Tens', 11: 'Elevens', 12: 'Twelves',
};

const DIE_STAT_LABELS = {
  1: 'Spd', 2: 'Dmg', 3: 'Crit', 4: 'Armor', 5: 'HP',
  6: 'Res', 7: 'Gold', 8: 'Summon', 9: 'Spell', 10: 'Block',
  11: 'Lifesteal', 12: 'Dark',
};

const STAT_LABELS = {
  attack_speed: 'Atk Speed', attack_dmg: 'Atk Dmg', crit_chance: 'Crit',
  armor: 'Armor', max_hp: 'Max HP', item_slots: 'Item Slots', free_items: 'Free Picks', gold: 'Gold',
  summon_level: 'Summon Lvl', spell_level: 'Spell Lvl', block_chance: 'Block',
  lifesteal: 'Lifesteal', dark_level: 'Dark Lvl', current_hp: 'HP',
};

// Per-die effect and bonus threshold info for the upgrade tracker tooltips
const UPGRADE_INFO = {
  1:  { perDie: '+3% atk speed',      bonus: '+3% atk speed at 4' },
  2:  { perDie: '+1 attack dmg',     bonus: '+1 dmg at 4' },
  3:  { perDie: '+1% crit',          bonus: '+1% crit at 4' },
  4:  { perDie: '+2% armor',         bonus: '+2% armor at 4' },
  5:  { perDie: '+5 max HP',         bonus: '+5 HP at 4' },
  6:  { perDie: null,                bonus: '+1 item slot at 4  /  +1 free pick at 6' },
  7:  { perDie: '+20 gold',          bonus: '+20 gold at 4' },
  8:  { perDie: '+1 summon level',   bonus: '+1 summon at 4' },
  9:  { perDie: '+1 spell level',    bonus: '+1 spell at 4' },
  10: { perDie: '+2% block chance',  bonus: '+2% block at 3' },
  11: { perDie: '+1% lifesteal',     bonus: '+1% lifesteal at 3' },
  12: { perDie: '+1 dark level',     bonus: '+1 dark at 3' },
};

// ---------------------------------------------------------------------------
// Small reusable components
// ---------------------------------------------------------------------------

function Panel({ children, style }) {
  return (
    <div style={{
      background: C.panel, border: `1px solid ${C.border}`,
      borderRadius: 8, padding: 16, ...style,
    }}>
      {children}
    </div>
  );
}

function Btn({ children, onClick, disabled, color, style }) {
  const bg = disabled ? '#333' : (color || C.orange);
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        background: bg, color: disabled ? C.muted : '#fff',
        border: 'none', borderRadius: 6, padding: '10px 20px',
        cursor: disabled ? 'default' : 'pointer', fontSize: 14,
        fontWeight: 'bold', transition: 'opacity .15s',
        ...style,
      }}
    >
      {children}
    </button>
  );
}

function HPBar({ current, max, color }) {
  const pct = Math.max(0, Math.min(100, (current / max) * 100));
  return (
    <div style={{ background: '#333', borderRadius: 4, height: 12, overflow: 'hidden' }}>
      <div style={{
        width: `${pct}%`, height: '100%',
        background: color || C.green, transition: 'width .3s',
      }} />
    </div>
  );
}

function StatRow({ label, value, highlight }) {
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '3px 0', color: highlight ? C.yellow : C.text, fontSize: 13,
    }}>
      <span style={{ color: C.muted }}>{label}</span>
      <span style={{ fontWeight: 'bold' }}>{value}</span>
    </div>
  );
}

function fmt(attr, val) {
  if (attr === 'attack_speed') return `${val.toFixed(2)}s`;
  if (['crit_chance', 'armor', 'block_chance', 'lifesteal'].includes(attr))
    return `${(val * 100).toFixed(1)}%`;
  if (attr === 'current_hp' || attr === 'max_hp') return Math.round(val);
  return typeof val === 'number' ? (Number.isInteger(val) ? val : val.toFixed(2)) : val;
}

// ---------------------------------------------------------------------------
// Player stats panel
// ---------------------------------------------------------------------------

function PlayerPanel({ player, ownedItems }) {
  const stats = [
    ['current_hp',   `${player.current_hp} / ${player.max_hp}`],
    ['attack_dmg',   fmt('attack_dmg', player.attack_dmg)],
    ['attack_speed', fmt('attack_speed', player.attack_speed)],
    ['crit_chance',  fmt('crit_chance', player.crit_chance)],
    ['armor',        fmt('armor', player.armor)],
    ['block_chance', fmt('block_chance', player.block_chance)],
    ['lifesteal',    fmt('lifesteal', player.lifesteal)],
    ['dark_level',   player.dark_level],
    ['summon_level', player.summon_level],
    ['spell_level',  player.spell_level],
    ['gold',         player.gold],
    ['item_slots',   player.item_slots],
    ['free_items',   player.free_items],
  ];

  return (
    <Panel style={{ minWidth: 180 }}>
      <div style={{ color: C.yellow, fontWeight: 'bold', marginBottom: 8, fontSize: 14 }}>
        Hero
      </div>
      <HPBar current={player.current_hp} max={player.max_hp} />
      <div style={{ fontSize: 11, color: C.muted, textAlign: 'right', marginBottom: 8 }}>
        {player.current_hp} / {player.max_hp} HP
      </div>
      {stats.map(([attr, val]) => (
        <StatRow key={attr} label={STAT_LABELS[attr] || attr} value={val} />
      ))}
      {ownedItems?.length > 0 && (
        <div style={{ marginTop: 8, borderTop: `1px solid ${C.border}`, paddingTop: 8 }}>
          <div style={{ fontSize: 11, color: C.muted, marginBottom: 4 }}>Items</div>
          {ownedItems.map(item => (
            <div key={item.id} style={{ fontSize: 12, color: C.green }}>• {item.name}</div>
          ))}
        </div>
      )}
    </Panel>
  );
}

// ---------------------------------------------------------------------------
// Run header (level / fight progress)
// ---------------------------------------------------------------------------

function RunHeader({ run }) {
  const fightLabel = run.fight_index === 2 ? 'Boss' : `Fight ${run.fight_index + 1}`;
  const phaseLabel = {
    upgrade: `Upgrade Phase (${run.upgrade_turns_max - run.upgrade_turns_used} turns left)`,
    upgrade_done: 'Upgrades Ready',
    combat: 'Combat',
    pre_boss_shop: 'Pre-Boss Shop',
    shop: 'Shop',
    forge: '⚒️ Forge',
    game_over: 'Game Over',
    victory: 'Victory!',
  }[run.phase] || run.phase;

  return (
    <div style={{
      display: 'flex', gap: 12, alignItems: 'center',
      background: C.panel, border: `1px solid ${C.border}`,
      borderRadius: 8, padding: '10px 16px', marginBottom: 16,
    }}>
      <span style={{ color: C.blue, fontWeight: 'bold' }}>Level {run.level}</span>
      <span style={{ color: C.muted }}>·</span>
      <span style={{ color: run.is_boss ? C.red : C.text }}>{fightLabel}</span>
      <span style={{ color: C.muted }}>·</span>
      <span style={{ color: C.orange }}>{phaseLabel}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Upgrade phase — Yatzy UI (adapted from App.jsx)
// ---------------------------------------------------------------------------

function DieFace({ value }) {
  const pip = (x, y) => (
    <circle key={`${x}${y}`} cx={x} cy={y} r={3.5} fill="currentColor" />
  );
  const layouts = {
    1: [[18, 18]],
    2: [[10, 10], [26, 26]],
    3: [[10, 10], [18, 18], [26, 26]],
    4: [[10, 10], [26, 10], [10, 26], [26, 26]],
    5: [[10, 10], [26, 10], [18, 18], [10, 26], [26, 26]],
    6: [[10, 10], [26, 10], [10, 18], [26, 18], [10, 26], [26, 26]],
  };
  if (value <= 6) {
    return (
      <svg width={36} height={36} style={{ display: 'block' }}>
        {(layouts[value] || []).map(([x, y]) => pip(x, y))}
      </svg>
    );
  }
  return <span style={{ fontSize: 16, fontWeight: 'bold', lineHeight: '36px' }}>{value}</span>;
}

// Base backgrounds per die type (used for normal/idle state only)
const DIE_TYPE_BG = {
  d12:   '#d8b4fe',  // purple-300
  d3:    '#fed7aa',  // orange-200
  risky: '#fca5a5',  // red-300
};

function Die({ value, state, dieType, onClick }) {
  const typeBg = DIE_TYPE_BG[dieType];
  const styles = {
    normal:       { background: typeBg || '#e8e8e8', color: '#222',  border: `2px solid ${typeBg ? 'rgba(0,0,0,.2)' : '#aaa'}` },
    userSelected: { background: C.yellow,  color: '#222',  border: `2px solid ${C.orange}` },
    preview:      { background: '#fff3cd', color: '#222',  border: `2px dashed ${C.orange}` },
    illegal:      { background: '#444',    color: '#666',  border: '2px solid #333' },
    setAside:     { background: '#555',    color: '#888',  border: '2px solid #444' },
  };
  const s = styles[state] || styles.normal;
  return (
    <div
      onClick={onClick}
      style={{
        ...s, width: 52, height: 52, borderRadius: 8,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        cursor: state === 'illegal' || state === 'setAside' ? 'default' : 'pointer',
        transition: 'all .1s', userSelect: 'none',
      }}
    >
      <DieFace value={value} />
    </div>
  );
}

/** Compute which die values will be collected for targetNum (mirrors backend logic). */
function computeCollectedValues(diceArr, targetNum) {
  const remaining = [...diceArr];
  const collected = [];
  // Singles first
  for (let i = remaining.length - 1; i >= 0; i--) {
    if (remaining[i] === targetNum) collected.push(remaining.splice(i, 1)[0]);
  }
  // Pairs (greedy)
  outer: for (let i = 0; i < remaining.length; i++) {
    for (let j = i + 1; j < remaining.length; j++) {
      if (remaining[i] + remaining[j] === targetNum) {
        collected.push(remaining[i], remaining[j]);
        remaining.splice(j, 1);
        remaining.splice(i, 1);
        i--;
        continue outer;
      }
    }
  }
  return collected;
}

function UpgradePhase({ run, runId, onRunUpdate, onError }) {
  const yatzy = run.yatzy;
  const [selectedIndices, setSelectedIndices] = useState([]);
  const [skipTimer, setSkipTimer] = useState(null);
  const [failedDice, setFailedDice] = useState(null);
  const [actionResult, setActionResult] = useState(null);
  const [rerolling, setRerolling] = useState(false);
  const [stagedDice, setStagedDice] = useState([]);

  const dice = yatzy?.dice || [];
  const diceTypes = yatzy?.dice_types || [];
  const progress = yatzy?.progress || {};
  const legalActions = yatzy?.legal_actions || [];
  const diceGroups = yatzy?.dice_groups || {};
  const poolSize = run.upgrade_pool_size ?? 6;
  const selectedNumber = yatzy?.selected_number;
  const turnsRemaining = yatzy?.turns_remaining ?? 0;

  const statRemoved = run.stat_removed || [];
  const statTargets = run.stat_targets || {};

  const legalNumbers = legalActions
    .filter(a => a.type === 'select' || a.type === 'collect')
    .filter(a => !statRemoved.includes(a.number))
    .map(a => a.number);
  const hasSkipOnly = legalActions.length === 1 && legalActions[0]?.type === 'skip_turn';

  // Compute preview from selected dice
  const targetNumber = (() => {
    if (selectedIndices.length === 0) return null;
    if (selectedIndices.length === 1) {
      const v = dice[selectedIndices[0]];
      return legalNumbers.includes(v) ? v : null;
    }
    if (selectedIndices.length === 2) {
      return dice[selectedIndices[0]] + dice[selectedIndices[1]];
    }
    return null;
  })();

  const isLegalTarget = targetNumber !== null && legalNumbers.includes(targetNumber);

  // Die state
  function getDieState(idx) {
    if (selectedIndices.includes(idx)) return 'userSelected';

    const dieVal = dice[idx];

    // Two dice selected — show preview for all matching dice of the target
    if (selectedIndices.length === 2) {
      if (!isLegalTarget) return 'illegal';
      const groupForTarget = diceGroups[String(targetNumber)] || [];
      return groupForTarget.includes(idx) ? 'preview' : 'illegal';
    }

    // One die selected — keep pair-candidates clickable
    if (selectedIndices.length === 1) {
      const selVal = dice[selectedIndices[0]];
      const pairSum = selVal + dieVal;

      // This die could pair with the selected die to form a legal number
      if (pairSum >= 7 && pairSum <= 12 && legalNumbers.includes(pairSum)) return 'normal';

      // This die matches the singles target (will be collected together)
      if (dieVal === selVal && legalNumbers.includes(selVal)) return 'preview';

      // Any other legal use
      const anyLegal = Object.entries(diceGroups).some(([n, idxs]) =>
        idxs.includes(idx) && legalNumbers.includes(parseInt(n))
      );
      return anyLegal ? 'normal' : 'illegal';
    }

    // Nothing selected — highlight anything legal
    const anyLegal = Object.entries(diceGroups).some(([n, idxs]) =>
      idxs.includes(idx) && legalNumbers.includes(parseInt(n))
    );
    return anyLegal ? 'normal' : 'illegal';
  }

  function handleDieClick(idx) {
    if (getDieState(idx) === 'setAside' || getDieState(idx) === 'illegal') return;
    setSelectedIndices(prev => {
      if (prev.includes(idx)) return prev.filter(i => i !== idx);
      if (prev.length >= 2) return [idx];
      return [...prev, idx];
    });
  }

  async function handleCollect() {
    if (!isLegalTarget) return;
    // Pair each collected value with its die type (consume from left to avoid double-match)
    const tempDice = [...dice];
    const justCollected = computeCollectedValues(dice, targetNumber).map(v => {
      const idx = tempDice.indexOf(v);
      if (idx !== -1) tempDice[idx] = null; // consume so duplicate values map correctly
      return { value: v, dieType: idx !== -1 ? diceTypes[idx] : undefined };
    });
    try {
      const resp = await rpgApi.upgradeSelect(runId, targetNumber);
      setSelectedIndices([]);
      setActionResult(resp.action_result);
      const st = resp.action_result?.state;
      if (st === 'turn_end' || st === 'completed_number' || st === 'won' || st === 'bonus_turn') {
        setStagedDice([]);
      } else {
        setStagedDice(prev => [...prev, ...justCollected]);
      }
      if (resp.action_result?.info?.failed_dice) {
        setFailedDice(resp.action_result.info.failed_dice);
        setTimeout(() => { setFailedDice(null); onRunUpdate(resp); }, 1500);
      } else {
        onRunUpdate(resp);
      }
    } catch (e) { if (onError) onError(e); else console.error(e); }
  }

  // Auto-skip when no valid combos
  useEffect(() => {
    if (!hasSkipOnly || skipTimer) return;
    const t = setTimeout(async () => {
      setSkipTimer(null);
      setStagedDice([]);
      try {
        const resp = await rpgApi.upgradeSkip(runId);
        setActionResult(resp.action_result);
        onRunUpdate(resp);
      } catch (e) { if (onError) onError(e); else console.error(e); }
    }, 1500);
    setSkipTimer(t);
    return () => clearTimeout(t);
  }, [hasSkipOnly, runId]);

  if (!yatzy) return null;

  return (
    <div>
      {/* Turn counter */}
      <div style={{
        display: 'flex', gap: 8, marginBottom: 12, alignItems: 'center',
      }}>
        <span style={{ color: C.muted, fontSize: 13 }}>Turns remaining:</span>
        {Array.from({ length: run.upgrade_turns_max }, (_, i) => (
          <div key={i} style={{
            width: 12, height: 12, borderRadius: '50%',
            background: i < turnsRemaining ? C.blue : '#333',
          }} />
        ))}
        <span style={{ color: C.blue, fontWeight: 'bold', fontSize: 13 }}>{turnsRemaining}</span>
      </div>

      {/* Failed dice overlay */}
      {failedDice && (
        <div style={{
          background: `${C.red}22`, border: `1px solid ${C.red}`,
          borderRadius: 6, padding: '8px 12px', marginBottom: 10, color: C.red, fontSize: 13,
        }}>
          No match — failed dice: {failedDice.join(', ')}
        </div>
      )}

      {/* Dice area — two labelled boxes side by side */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 12, alignItems: 'flex-start' }}>

        {/* Active dice box */}
        <div style={{
          flex: 1, background: '#1a2a3a', border: `1px solid ${C.blue}44`,
          borderRadius: 8, padding: '8px 10px',
        }}>
          <div style={{ fontSize: 11, color: C.blue, marginBottom: 6, letterSpacing: 1, textTransform: 'uppercase' }}>
            Roll
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', minHeight: 52 }}>
            {dice.map((val, idx) => (
              <Die key={idx} value={val} state={getDieState(idx)} dieType={diceTypes[idx]} onClick={() => handleDieClick(idx)} />
            ))}
          </div>
        </div>

        {/* Stashed / collected-this-turn box */}
        <div style={{
          flex: '0 0 auto', background: '#1a1a2a', border: '1px solid #333',
          borderRadius: 8, padding: '8px 10px', minWidth: 80,
          opacity: stagedDice.length === 0 ? 0.35 : 1,
        }}>
          <div style={{ fontSize: 11, color: C.muted, marginBottom: 6, letterSpacing: 1, textTransform: 'uppercase' }}>
            Stashed
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', minHeight: 52 }}>
            {stagedDice.length === 0
              ? <span style={{ color: '#444', fontSize: 11, alignSelf: 'center' }}>—</span>
              : stagedDice.map((d, i) => <Die key={i} value={d.value} state="setAside" dieType={d.dieType} />)
            }
          </div>
        </div>

      </div>

      {run.free_reroll_available && !selectedNumber && !hasSkipOnly && (
        <Btn
          color={C.purple}
          disabled={rerolling}
          style={{ marginBottom: 8, fontSize: 13 }}
          onClick={async () => {
            setRerolling(true);
            setSelectedIndices([]);
            try {
              const resp = await rpgApi.upgradeReroll(runId);
              onRunUpdate(resp);
            } catch (e) { if (onError) onError(e); else console.error(e); }
            setRerolling(false);
          }}
        >
          🔄 Free Reroll
        </Btn>
      )}

      {hasSkipOnly && (
        <div style={{ color: C.muted, fontSize: 13, marginBottom: 8 }}>
          No valid moves — skipping turn…
        </div>
      )}

      {isLegalTarget && (() => {
        const collectedDice = computeCollectedValues(dice, targetNumber);
        const singleCount = collectedDice.filter(v => v === targetNumber).length;
        const pairCount = Math.floor((collectedDice.length - singleCount) / 2);
        const units = singleCount + pairCount;
        return (
          <Btn onClick={handleCollect} style={{ marginBottom: 16 }}>
            Collect {units} {NUMBER_NAMES[targetNumber] || targetNumber}
          </Btn>
        );
      })()}

      {/* Progress grid */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 6, marginTop: 8,
      }}>
        {Array.from({ length: 12 }, (_, i) => {
          const n = i + 1;
          const removed = statRemoved.includes(n);
          const target = statTargets[n] ?? 6;
          const count = Math.min(parseInt(progress[String(n)] || 0), target);
          const info = UPGRADE_INFO[n];
          const baseThreshold = n >= 10 ? 3 : 4;
          const thresholdAt = target !== 6 ? Math.max(1, Math.round(baseThreshold * target / 6)) : baseThreshold;
          const tooltipLines = removed
            ? 'Removed by specialisation — no stat gain, but dice still count toward pair combinations.'
            : [
                info.perDie ? `Each die: ${info.perDie}` : null,
                `Collect ${thresholdAt}: ${info.bonus}`,
                target !== 6 ? `Target: ${target} (modified by specialisation)` : null,
              ].filter(Boolean).join('\n');
          return (
            <div key={n} style={{
              background: removed ? '#111' : '#1a1a3e',
              borderRadius: 6, padding: '6px 4px',
              textAlign: 'center',
              border: `1px solid ${removed ? '#333' : C.border}`,
              opacity: removed ? 0.45 : 1,
              position: 'relative',
            }}>
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2 }}>
                <span style={{ fontSize: 11, color: removed ? '#555' : C.muted }}>{n}</span>
                <span
                  title={tooltipLines}
                  style={{
                    fontSize: 9, color: C.blue, cursor: 'help', lineHeight: 1,
                    border: `1px solid ${C.blue}`, borderRadius: '50%',
                    width: 11, height: 11, display: 'inline-flex',
                    alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                  }}
                >i</span>
              </div>
              <div style={{ fontSize: 9, color: removed ? '#555' : C.orange, marginBottom: 4, whiteSpace: 'nowrap' }}>
                {removed ? '✕' : DIE_STAT_LABELS[n]}
              </div>
              <div style={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
                {Array.from({ length: target }, (_, j) => (
                  <div key={j} style={{
                    width: Math.max(4, Math.floor(36 / target)), height: 14, borderRadius: 2,
                    background: removed ? '#222' : (j < count ? C.green : '#333'),
                  }} />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Upgrade done screen — shows what was gained
// ---------------------------------------------------------------------------

function UpgradeDoneScreen({ run, runId, onRunUpdate, onError }) {
  const [loading, setLoading] = useState(false);

  async function proceed() {
    setLoading(true);
    try {
      const resp = await rpgApi.upgradeFinish(runId);
      onRunUpdate(resp);
    } catch (e) { if (onError) onError(e); else console.error(e); }
    setLoading(false);
  }

  const upgrades = run.last_upgrades || [];

  return (
    <Panel style={{ maxWidth: 420 }}>
      <div style={{ color: C.green, fontWeight: 'bold', fontSize: 18, marginBottom: 16 }}>
        Upgrades Applied
      </div>
      {upgrades.length === 0 ? (
        <div style={{ color: C.muted, marginBottom: 16 }}>No upgrades this phase.</div>
      ) : (
        <div style={{ marginBottom: 16 }}>
          {upgrades.map((u, i) => (
            <div key={i} style={{
              display: 'flex', justifyContent: 'space-between',
              padding: '4px 0', borderBottom: `1px solid ${C.border}`,
              color: C.text, fontSize: 13,
            }}>
              <span style={{ color: C.muted }}>{NUMBER_NAMES[u.number] || u.number}</span>
              <span style={{ color: u.threshold_bonus ? C.yellow : C.green }}>{u.desc}</span>
            </div>
          ))}
        </div>
      )}
      <Btn onClick={proceed} disabled={loading}>
        {loading ? 'Loading…' : `Fight ${run.is_boss ? 'Boss' : `#${run.fight_index + 1}`}`}
      </Btn>
    </Panel>
  );
}

// ---------------------------------------------------------------------------
// Run path — right-side column showing all upcoming nodes
// ---------------------------------------------------------------------------

const ENEMY_EMOJIS  = {
  'Human Soldier': '🪖', 'Bandit Captain': '🗡️',
  'Orc Warrior': '🪓', 'Orc Berserker': '💢', 'Orc Warchief': '👑',
  'Dark Knight': '🖤', 'Shadow Mage': '🔮', 'Demon Lord': '👿',
};

function PathNode({ node }) {
  const isDone    = node.status === 'done';
  const isCurrent = node.status === 'current';

  let emoji, label, accent, sub;
  if (node.type === 'upgrade') {
    emoji = '🎲'; label = `Upgrade`; accent = C.blue;
    const poolNote = node.pool_size && node.pool_size !== 6 ? ` · ${node.pool_size}d` : '';
    sub = `${node.turns} turns${poolNote}`;
  } else if (node.type === 'boss') {
    emoji = '💀'; label = node.enemy_name; accent = C.red;
    sub = `HP ${node.enemy_hp}`;
  } else if (node.type === 'fight') {
    emoji = ENEMY_EMOJIS[node.enemy_name] ?? '⚔️';
    label = node.enemy_name; accent = C.orange;
    sub = `HP ${node.enemy_hp}`;
  } else if (node.type === 'pre_boss_shop') {
    emoji = '🛒'; label = 'Pre-Boss Shop'; accent = C.gold; sub = null;
  } else if (node.type === 'forge') {
    emoji = '⚒️'; label = 'Forge'; accent = C.purple; sub = 'Pick 1 of 3';
  } else {
    emoji = '🛒'; label = 'Shop'; accent = C.gold; sub = null;
  }

  const bg     = isCurrent ? `${accent}18` : 'transparent';
  const border = isCurrent ? accent : isDone ? '#2a2a2a' : C.border;
  const col    = isDone ? '#444' : isCurrent ? accent : C.text;

  return (
    <div style={{
      background: bg, border: `1px solid ${border}`,
      borderRadius: 6, padding: '5px 8px',
      display: 'flex', alignItems: 'center', gap: 7,
      opacity: isDone ? 0.45 : 1,
    }}>
      <span style={{ fontSize: 13, minWidth: 18, textAlign: 'center' }}>
        {isDone ? '✓' : emoji}
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: 11, color: col,
          fontWeight: isCurrent ? 'bold' : 'normal',
          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
        }}>
          {label}
        </div>
        {sub && !isDone && (
          <div style={{ fontSize: 9, color: C.muted }}>{sub}</div>
        )}
      </div>
      {isCurrent && <span style={{ fontSize: 9, color: accent }}>◀</span>}
    </div>
  );
}

function RunPath({ run }) {
  const path = run.path || [];

  return (
    <div style={{ minWidth: 150, maxWidth: 170 }}>
      <div style={{
        color: C.muted, fontSize: 10, letterSpacing: 1,
        marginBottom: 8, textTransform: 'uppercase',
      }}>
        Path Ahead
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {path.map((node, i) => {
          const isFirstOfLevel = node.type === 'upgrade' && node.fight === 0
            || node.type === 'pre_boss_shop' && node.fight === 0;
          return (
            <div key={i}>
              {isFirstOfLevel && (
                <div style={{
                  color: C.muted, fontSize: 9, letterSpacing: 1,
                  padding: '6px 4px 2px', textTransform: 'uppercase',
                  borderTop: i > 0 ? `1px solid ${C.border}` : 'none',
                  marginTop: i > 0 ? 4 : 0,
                }}>
                  Level {node.level}
                </div>
              )}
              <PathNode node={node} />
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Combat screen — visual battle arena
// ---------------------------------------------------------------------------

const SUMMON_EMOJIS = { Imp: '😈', Wolf: '🐺', Orc: '👹', Wyvern: '🦎', Dragon: '🐉' };

function CharacterCard({ name, emoji, hp, maxHp, alive = true, accent, label }) {
  return (
    <div style={{
      background: C.panel, border: `1px solid ${alive ? accent : '#444'}`,
      borderRadius: 8, padding: '10px 12px', minWidth: 130, textAlign: 'center',
      opacity: alive ? 1 : 0.45, transition: 'opacity .4s',
    }}>
      {label && (
        <div style={{ fontSize: 10, color: C.muted, marginBottom: 4, letterSpacing: 1 }}>
          {label}
        </div>
      )}
      <div style={{ fontSize: 32, lineHeight: 1, marginBottom: 4 }}>{emoji}</div>
      <div style={{ fontSize: 12, fontWeight: 'bold', color: alive ? accent : C.muted, marginBottom: 6 }}>
        {alive ? name : `${name} ✝`}
      </div>
      <HPBar current={Math.max(0, hp)} max={maxHp} color={alive ? accent : '#555'} />
      <div style={{ fontSize: 10, color: C.muted, marginTop: 3 }}>
        {Math.max(0, hp)} / {maxHp}
      </div>
    </div>
  );
}

function CombatScreen({ run, runId, onRunUpdate, onError }) {
  const enemy   = run.enemy;
  const summon  = run.summon_stats;   // null if no summon

  const [log, setLog]             = useState([]);
  const [loading, setLoading]     = useState(false);
  const [playerHp, setPlayerHp]   = useState(run.player.current_hp);
  const [enemyHp, setEnemyHp]     = useState(enemy?.hp ?? 0);
  const [summonHp, setSummonHp]   = useState(summon?.hp ?? 0);
  const [summonAlive, setSummonAlive] = useState(!!summon);
  const [darkStacks, setDarkStacks] = useState({ hitCount: 0, mult: 1.0 });
  const [pendingNext, setPendingNext] = useState(null); // finalResp waiting for Next click
  const logRef    = useRef(null);
  const hasStarted = useRef(false);

  const playerMaxHp = run.player.max_hp;
  const enemyMaxHp  = enemy?.hp ?? 1;
  const summonMaxHp = summon?.hp ?? 1;

  useEffect(() => {
    if (hasStarted.current) return;
    hasStarted.current = true;

    async function runCombat() {
      setLoading(true);
      try {
        const resp = await rpgApi.startCombat(runId);
        setLoading(false);
        animateEvents(resp.combat.events, resp);
      } catch (e) {
        console.error(e);
        setLoading(false);
      }
    }
    runCombat();
  }, []);

  function animateEvents(events, finalResp) {
    if (!events?.length) { onRunUpdate(finalResp); return; }
    const speedFactor = Math.max(1, (events[events.length - 2]?.time ?? 1) / 15);

    events.forEach(ev => {
      setTimeout(() => {
        if (ev.type === 'player_attack') {
          setEnemyHp(ev.enemy_hp);
          setPlayerHp(ev.player_hp);
          if (ev.hit_count != null) setDarkStacks({ hitCount: ev.hit_count, mult: ev.dark_mult ?? 1.0 });
          addLog(`⚔️ You hit for ${ev.dmg}${ev.crit ? ' (CRIT!)' : ''}${ev.heal > 0 ? ` +${ev.heal}hp` : ''}${ev.dark_mult > 1 ? ` 🌑×${ev.dark_mult}` : ''}`);
        } else if (ev.type === 'spell') {
          setEnemyHp(ev.enemy_hp);
          setPlayerHp(ev.player_hp);
          addLog(`✨ Spell: ${ev.dmg} dmg${ev.heal > 0 ? ` +${ev.heal}hp` : ''}${ev.dark_mult > 1 ? ` 🌑×${ev.dark_mult}` : ''}`);
        } else if (ev.type === 'summon_attack') {
          setEnemyHp(ev.enemy_hp);
          addLog(`${SUMMON_EMOJIS[summon?.name] ?? '🐾'} ${summon?.name ?? 'Summon'}: ${ev.dmg} dmg${ev.dark_mult > 1 ? ` 🌑×${ev.dark_mult}` : ''}`);
        } else if (ev.type === 'enemy_attack') {
          if (ev.blocked) {
            addLog(`🛡️ ${enemy?.name} blocked!`);
          } else {
            setPlayerHp(ev.player_hp);
            if (ev.summon_hp != null) setSummonHp(ev.summon_hp);
            if (ev.summon_died) setSummonAlive(false);
            let msg = `💥 ${enemy?.name} hits for ${ev.dmg}`;
            if (ev.summon_died) msg += ` — ${summon?.name} defeated!`;
            if (ev.thorns) { setEnemyHp(ev.enemy_hp); msg += ` (${ev.thorns} thorns)`; }
            addLog(msg);
          }
        } else if (ev.type === 'combat_end') {
          setPlayerHp(ev.player_hp);
          setEnemyHp(ev.enemy_hp);
          addLog(ev.result === 'win' ? '🏆 Victory!' : '💀 Defeated…');
          setPendingNext(finalResp);
        }
      }, (ev.time / speedFactor) * 1000);
    });
  }

  function addLog(msg) {
    setLog(prev => [...prev.slice(-40), msg]);
    setTimeout(() => {
      if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
    }, 50);
  }

  return (
    <div>
      {/* Battle arena */}
      <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', marginBottom: 14, flexWrap: 'wrap' }}>
        {/* Player side */}
        <CharacterCard
          name="Hero" emoji="🧙" hp={playerHp} maxHp={playerMaxHp}
          alive={playerHp > 0} accent={C.green} label="YOU"
        />
        {summon && (
          <CharacterCard
            name={summon.name} emoji={SUMMON_EMOJIS[summon.name] ?? '🐾'}
            hp={summonHp} maxHp={summonMaxHp}
            alive={summonAlive} accent={C.purple} label="SUMMON"
          />
        )}

        {/* VS divider */}
        <div style={{
          flex: 1, textAlign: 'center', color: C.muted,
          fontSize: 22, fontWeight: 'bold', alignSelf: 'center',
        }}>
          vs
        </div>

        {/* Enemy side */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
          <CharacterCard
            name={enemy?.name ?? 'Enemy'}
            emoji={ENEMY_EMOJIS[enemy?.name] ?? '👾'}
            hp={enemyHp} maxHp={enemyMaxHp}
            alive={enemyHp > 0} accent={enemy?.is_boss ? C.red : C.orange}
            label={enemy?.is_boss ? '⚠️ BOSS' : 'ENEMY'}
          />
          {run.player.dark_level > 0 && darkStacks.hitCount > 0 && (
            <div style={{
              background: '#1a0a2a', border: '1px solid #6b21a8',
              borderRadius: 6, padding: '3px 8px',
              fontSize: 12, color: '#c084fc',
              display: 'flex', gap: 6, alignItems: 'center',
            }}>
              <span>🌑 Dark</span>
              <span style={{ color: '#e879f9', fontWeight: 'bold' }}>×{darkStacks.mult}</span>
              <span style={{ color: '#888', fontSize: 11 }}>({darkStacks.hitCount} hits)</span>
            </div>
          )}
        </div>
      </div>

      {/* Combat log */}
      {loading
        ? <div style={{ color: C.muted, fontSize: 13, padding: 8 }}>Simulating…</div>
        : (
          <>
            <div
              ref={logRef}
              style={{
                background: C.panel, border: `1px solid ${C.border}`, borderRadius: 8,
                padding: 10, maxHeight: 180, overflowY: 'auto',
              }}
            >
              {log.length === 0
                ? <div style={{ color: C.muted, fontSize: 13 }}>Combat starting…</div>
                : log.map((l, i) => (
                  <div key={i} style={{ fontSize: 12, color: C.text, padding: '1px 0' }}>{l}</div>
                ))
              }
            </div>
            {pendingNext && (
              <Btn
                onClick={() => onRunUpdate(pendingNext)}
                color={C.green}
                style={{ marginTop: 12 }}
              >
                Next →
              </Btn>
            )}
          </>
        )
      }
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pre-game forge screen — pick a specialisation before the first enemy
// ---------------------------------------------------------------------------

function PreGameForgeScreen({ run, runId, onRunUpdate, onError }) {
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
    <Panel style={{ maxWidth: 520 }}>
      <div style={{ color: C.gold, fontWeight: 'bold', fontSize: 22, marginBottom: 4 }}>
        ⚗️ Specialisation
      </div>
      <div style={{ color: C.muted, fontSize: 13, marginBottom: 20 }}>
        Choose your path before the first battle. This alters your upgrade board
        for the entire run — some stats become easier to max, others are removed entirely.
        Removed stats are shown greyed out on your board but their dice still count toward pair combinations.
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {choices.map(choice => (
          <div key={choice.id} style={{
            background: '#1a1228', border: `1px solid ${C.gold}`,
            borderRadius: 8, padding: 14,
            display: 'flex', alignItems: 'flex-start', gap: 14,
          }}>
            <div style={{ fontSize: 28, lineHeight: 1 }}>{choice.icon}</div>
            <div style={{ flex: 1 }}>
              <div style={{ color: C.yellow, fontWeight: 'bold', fontSize: 15, marginBottom: 4 }}>
                {choice.name}
              </div>
              <div style={{ color: C.muted, fontSize: 13, marginBottom: 10 }}>{choice.desc}</div>
              <Btn onClick={() => pick(choice.id)} disabled={loading} color={C.orange}
                style={{ fontSize: 13, padding: '6px 16px' }}>
                Choose
              </Btn>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}

// ---------------------------------------------------------------------------
// Forge screen — pick 1 of 3 die upgrades after defeating a boss
// ---------------------------------------------------------------------------

function ForgeScreen({ run, runId, onRunUpdate, onError }) {
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
    <Panel style={{ maxWidth: 480 }}>
      <div style={{ color: C.purple, fontWeight: 'bold', fontSize: 20, marginBottom: 4 }}>
        ⚒️ Forge
      </div>
      <div style={{ color: C.muted, fontSize: 13, marginBottom: 20 }}>
        The boss has fallen. Choose one forge upgrade to carry into the next level.
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {choices.map(choice => (
          <div key={choice.id} style={{
            background: '#1a1040', border: `1px solid ${C.purple}`,
            borderRadius: 8, padding: 14,
            display: 'flex', alignItems: 'flex-start', gap: 14,
          }}>
            <div style={{ fontSize: 28, lineHeight: 1 }}>{choice.icon}</div>
            <div style={{ flex: 1 }}>
              <div style={{ color: C.yellow, fontWeight: 'bold', fontSize: 15, marginBottom: 4 }}>
                {choice.name}
              </div>
              <div style={{ color: C.muted, fontSize: 13, marginBottom: 10 }}>{choice.desc}</div>
              <Btn onClick={() => pick(choice.id)} disabled={loading} color={C.purple}
                style={{ fontSize: 13, padding: '6px 16px' }}>
                Choose
              </Btn>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}

// ---------------------------------------------------------------------------
// Shop screen
// ---------------------------------------------------------------------------

function ShopScreen({ run, runId, onRunUpdate, onError }) {
  const [loading, setLoading] = useState(false);
  const items = run.shop_items || [];
  const owned = (run.owned_items || []).map(i => i.id);
  const freepicks = run.player.free_items ?? 0;

  async function buy(itemId, useFree = false) {
    setLoading(true);
    try {
      const resp = await rpgApi.buyItem(runId, itemId, useFree);
      onRunUpdate(resp);
    } catch (e) { if (onError) onError(e); else console.error(e); }
    setLoading(false);
  }

  async function reroll() {
    setLoading(true);
    try {
      const resp = await rpgApi.rerollShop(runId);
      onRunUpdate(resp);
    } catch (e) { if (onError) onError(e); else console.error(e); }
    setLoading(false);
  }

  async function close() {
    setLoading(true);
    try {
      const resp = await rpgApi.closeShop(runId);
      onRunUpdate(resp);
    } catch (e) { if (onError) onError(e); else console.error(e); }
    setLoading(false);
  }

  return (
    <Panel style={{ maxWidth: 460 }}>
      <div style={{ color: C.gold, fontWeight: 'bold', fontSize: 18, marginBottom: 4 }}>
        {run.phase === 'pre_boss_shop' ? '🛒 Pre-Boss Shop' : '🛒 Shop'}
      </div>
      <div style={{ color: C.muted, fontSize: 13, marginBottom: 16 }}>
        Gold: <span style={{ color: C.gold, fontWeight: 'bold' }}>{run.player.gold}</span>
        {freepicks > 0 && (
          <>{' · '}Free picks: <span style={{ color: C.green, fontWeight: 'bold' }}>{freepicks}</span></>
        )}
      </div>

      {items.map(item => {
        const alreadyOwned = owned.includes(item.id);
        const isPotion = item.id === 'heal_potion';
        const canBuyGold = !alreadyOwned && run.player.gold >= item.cost;
        const canFree = !alreadyOwned && !isPotion && freepicks > 0;
        return (
          <div key={item.id} style={{
            background: alreadyOwned ? '#1a3a1a' : '#16213e',
            border: `1px solid ${alreadyOwned ? C.green : C.border}`,
            borderRadius: 8, padding: 12, marginBottom: 10,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ color: C.yellow, fontWeight: 'bold' }}>{item.name}</span>
              <span style={{ color: C.gold, fontWeight: 'bold' }}>{item.cost}g</span>
            </div>
            <div style={{ color: C.muted, fontSize: 13, marginBottom: 8 }}>{item.desc}</div>
            {alreadyOwned
              ? <span style={{ color: C.green, fontSize: 12 }}>✓ Owned</span>
              : <div style={{ display: 'flex', gap: 8 }}>
                  <Btn onClick={() => buy(item.id, false)} disabled={!canBuyGold || loading} style={{ fontSize: 13, padding: '6px 14px' }}>
                    Buy
                  </Btn>
                  {canFree && (
                    <Btn onClick={() => buy(item.id, true)} disabled={loading} color={C.green} style={{ fontSize: 13, padding: '6px 14px' }}>
                      Free
                    </Btn>
                  )}
                </div>
            }
          </div>
        );
      })}

      {run.owned_items?.length > 0 && (
        <div style={{ marginTop: 16, borderTop: `1px solid ${C.border}`, paddingTop: 12 }}>
          <div style={{ color: C.muted, fontSize: 12, marginBottom: 6 }}>Your items:</div>
          {run.owned_items.map(item => (
            <div key={item.id} style={{ color: C.green, fontSize: 13 }}>✓ {item.name}</div>
          ))}
        </div>
      )}

      <div style={{ display: 'flex', gap: 10, marginTop: 16, alignItems: 'center' }}>
        <Btn onClick={close} disabled={loading} color={C.blue}>
          {run.phase === 'pre_boss_shop' ? '⚔️ Fight Boss' : `Continue to Level ${run.level + 1}`}
        </Btn>
        <Btn
          onClick={reroll}
          disabled={loading || run.player.gold < 30}
          color={C.muted}
          style={{ fontSize: 13 }}
        >
          🔀 Reroll (30g)
        </Btn>
      </div>
    </Panel>
  );
}

// ---------------------------------------------------------------------------
// Game over / victory screens
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// History screen
// ---------------------------------------------------------------------------

const COLLECTION_LABELS = {
  1:'Spd', 2:'Dmg', 3:'Crit', 4:'Armor', 5:'HP',
  6:'Res', 7:'Gold', 8:'Summon', 9:'Spell', 10:'Block', 11:'LS', 12:'Dark',
};

const FORGE_LABELS = {
  add_d12: 'd12', add_d3: 'd3', remove_die: '-die',
  loaded_high: 'Load↑', free_reroll: 'Reroll', risky_die: 'Risky',
};

function HistoryEntry({ entry }) {
  const [open, setOpen] = useState(false);
  const win = entry.outcome === 'win';
  const date = new Date(entry.timestamp).toLocaleString([], {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
  const s = entry.end_stats || {};
  const cols = entry.collections || {};
  const maxCols = Math.max(1, ...Object.values(cols).map(Number));

  return (
    <div style={{
      border: `1px solid ${win ? C.green : C.red}`,
      borderRadius: 8, marginBottom: 8, overflow: 'hidden',
    }}>
      {/* Header row — always visible */}
      <div
        onClick={() => setOpen(o => !o)}
        style={{
          display: 'flex', alignItems: 'center', gap: 10,
          padding: '8px 12px', cursor: 'pointer',
          background: win ? '#0d2a1a' : '#2a0d0d',
        }}
      >
        <span style={{ fontSize: 18 }}>{win ? '🏆' : '💀'}</span>
        <span style={{ color: win ? C.green : C.red, fontWeight: 'bold', minWidth: 36 }}>
          {win ? 'WIN' : 'LOSE'}
        </span>
        <span style={{ color: C.muted, fontSize: 12 }}>
          {win ? 'All 3 levels' : `L${entry.level_reached} F${entry.fight_reached}`}
        </span>
        <span style={{ color: C.muted, fontSize: 11, marginLeft: 'auto' }}>{date}</span>
        <span style={{ color: C.muted, fontSize: 11 }}>{open ? '▲' : '▼'}</span>
      </div>

      {open && (
        <div style={{ padding: '10px 12px', background: C.panel }}>

          {/* Forge path */}
          {entry.forges?.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ color: C.muted, fontSize: 10, marginBottom: 4 }}>FORGE PATH</div>
              <div style={{ display: 'flex', gap: 6 }}>
                {entry.forges.map((f, i) => (
                  <span key={i} style={{
                    background: C.purple + '33', border: `1px solid ${C.purple}`,
                    borderRadius: 4, padding: '2px 8px', fontSize: 12, color: C.purple,
                  }}>
                    {i + 1}. {FORGE_LABELS[f] || f}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Items */}
          {entry.item_names?.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ color: C.muted, fontSize: 10, marginBottom: 4 }}>ITEMS BOUGHT</div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {entry.item_names.map((name, i) => (
                  <span key={i} style={{
                    background: C.gold + '22', border: `1px solid ${C.gold}`,
                    borderRadius: 4, padding: '2px 8px', fontSize: 12, color: C.gold,
                  }}>
                    {name}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Upgrade collections bar chart */}
          <div style={{ marginBottom: 10 }}>
            <div style={{ color: C.muted, fontSize: 10, marginBottom: 6 }}>UPGRADE COLLECTIONS</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 4 }}>
              {Array.from({ length: 12 }, (_, i) => {
                const n = i + 1;
                const count = Number(cols[n] || 0);
                const pct = (count / maxCols) * 100;
                return (
                  <div key={n} style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 9, color: C.muted }}>{COLLECTION_LABELS[n]}</div>
                    <div style={{
                      height: 40, background: '#222', borderRadius: 3,
                      display: 'flex', alignItems: 'flex-end', margin: '2px 0',
                    }}>
                      <div style={{
                        width: '100%', height: `${pct}%`,
                        background: count > 0 ? C.blue : '#333', borderRadius: 3,
                        transition: 'height .3s',
                      }} />
                    </div>
                    <div style={{ fontSize: 10, color: count > 0 ? C.text : C.muted }}>{count}</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* End stats */}
          <div>
            <div style={{ color: C.muted, fontSize: 10, marginBottom: 6 }}>FINAL CHARACTER STATS</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2px 16px' }}>
              {[
                ['HP', `${s.current_hp} / ${s.max_hp}`],
                ['Atk Dmg', s.attack_dmg],
                ['Atk Speed', `${s.attack_speed?.toFixed(2)}s`],
                ['Crit', `${((s.crit_chance || 0) * 100).toFixed(1)}%`],
                ['Armor', `${((s.armor || 0) * 100).toFixed(1)}%`],
                ['Block', `${((s.block_chance || 0) * 100).toFixed(1)}%`],
                s.lifesteal > 0   && ['Lifesteal', `${(s.lifesteal * 100).toFixed(1)}%`],
                s.summon_level > 0 && ['Summon Lvl', s.summon_level],
                s.spell_level > 0  && ['Spell Lvl', s.spell_level],
                s.dark_level > 0   && ['Dark Lvl', s.dark_level],
                ['Gold', s.gold],
              ].filter(Boolean).map(([label, val]) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '1px 0' }}>
                  <span style={{ color: C.muted }}>{label}</span>
                  <span style={{ color: C.text, fontWeight: 'bold' }}>{val}</span>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}
    </div>
  );
}

function HistoryScreen({ onBack }) {
  const [history, setHistory] = useState(null);
  const [clearing, setClearing] = useState(false);

  useEffect(() => {
    rpgApi.getHistory().then(setHistory).catch(() => setHistory([]));
  }, []);

  async function clearAll() {
    if (!window.confirm('Delete all run history?')) return;
    setClearing(true);
    await rpgApi.clearHistory();
    setHistory([]);
    setClearing(false);
  }

  const wins  = (history || []).filter(r => r.outcome === 'win').length;
  const total = (history || []).length;

  return (
    <div style={{
      minHeight: '100vh', background: C.bg, fontFamily: 'monospace',
      color: C.text, padding: 16,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0, color: C.gold }}>Run History</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          {total > 0 && (
            <Btn onClick={clearAll} disabled={clearing} color={C.red}
              style={{ fontSize: 12, padding: '6px 12px' }}>
              Clear All
            </Btn>
          )}
          <Btn onClick={onBack} color={C.blue} style={{ fontSize: 12, padding: '6px 12px' }}>
            ← Back
          </Btn>
        </div>
      </div>

      {history === null ? (
        <div style={{ color: C.muted }}>Loading…</div>
      ) : history.length === 0 ? (
        <div style={{ color: C.muted, textAlign: 'center', marginTop: 60 }}>
          No runs yet. Complete a game to see your history.
        </div>
      ) : (
        <>
          <div style={{
            display: 'flex', gap: 20, marginBottom: 16,
            background: C.panel, borderRadius: 8, padding: '10px 16px',
          }}>
            <span style={{ color: C.muted, fontSize: 13 }}>
              Total runs: <span style={{ color: C.text, fontWeight: 'bold' }}>{total}</span>
            </span>
            <span style={{ color: C.muted, fontSize: 13 }}>
              Wins: <span style={{ color: C.green, fontWeight: 'bold' }}>{wins}</span>
            </span>
            <span style={{ color: C.muted, fontSize: 13 }}>
              Win rate: <span style={{ color: C.yellow, fontWeight: 'bold' }}>
                {total > 0 ? Math.round(wins / total * 100) : 0}%
              </span>
            </span>
          </div>
          <div style={{ maxWidth: 640 }}>
            {history.map(entry => (
              <HistoryEntry key={entry.run_id + entry.timestamp} entry={entry} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function GameOverScreen({ run, onRestart }) {
  return (
    <Panel style={{ textAlign: 'center', maxWidth: 360 }}>
      <div style={{ fontSize: 48, marginBottom: 8 }}>💀</div>
      <div style={{ color: C.red, fontWeight: 'bold', fontSize: 22, marginBottom: 8 }}>
        Defeated
      </div>
      <div style={{ color: C.muted, fontSize: 14, marginBottom: 20 }}>
        You fell on Level {run.level}, Fight {run.fight_index + 1}.
        <br />Make different choices and try again.
      </div>
      <Btn onClick={onRestart} color={C.blue}>Start New Run</Btn>
    </Panel>
  );
}

function VictoryScreen({ run, onRestart }) {
  return (
    <Panel style={{ textAlign: 'center', maxWidth: 360 }}>
      <div style={{ fontSize: 48, marginBottom: 8 }}>🏆</div>
      <div style={{ color: C.gold, fontWeight: 'bold', fontSize: 22, marginBottom: 8 }}>
        Victory!
      </div>
      <div style={{ color: C.text, fontSize: 14, marginBottom: 20 }}>
        You conquered all 3 levels!
        <br />Remaining HP: <span style={{ color: C.green }}>{run.player.current_hp}</span>
      </div>
      <Btn onClick={onRestart} color={C.green}>Play Again</Btn>
    </Panel>
  );
}

// ---------------------------------------------------------------------------
// Main RpgApp component
// ---------------------------------------------------------------------------

export default function RpgApp({ onBack }) {
  const [run, setRun]           = useState(null);
  const [runId, setRunId]       = useState(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);
  const [showHistory, setShowHistory] = useState(false);

  async function startRun() {
    setLoading(true);
    setError(null);
    try {
      const resp = await rpgApi.newRun();
      setRun(resp);
      setRunId(resp.run_id);
    } catch (e) {
      setError('Could not connect to server. Is the backend running?');
    }
    setLoading(false);
  }

  function handleRunUpdate(resp) {
    setRun(resp);
  }

  function handleError(e) {
    if (e instanceof RunExpiredError) {
      // Server was restarted — wipe local state so user can start fresh
      setRun(null);
      setRunId(null);
      setError(e.message);
    } else {
      console.error(e);
    }
  }

  // ---------------------------------------------------------------------------
  // Start screen
  // ---------------------------------------------------------------------------
  if (showHistory) {
    return <HistoryScreen onBack={() => setShowHistory(false)} />;
  }

  if (!run) {
    return (
      <div style={{
        minHeight: '100vh', background: C.bg, display: 'flex',
        flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        fontFamily: 'monospace', color: C.text,
      }}>
        <div style={{ fontSize: 40, marginBottom: 8 }}>⚔️</div>
        <h1 style={{ color: C.gold, marginBottom: 8 }}>Russian Yatzy: Adventure</h1>
        <p style={{ color: C.muted, marginBottom: 24, textAlign: 'center', maxWidth: 400 }}>
          Roll dice to upgrade your hero between battles.
          Survive 3 levels to claim victory.
        </p>
        {error && (
          <div style={{ color: C.red, marginBottom: 16, fontSize: 13 }}>{error}</div>
        )}
        <div style={{ display: 'flex', gap: 12 }}>
          <Btn onClick={startRun} disabled={loading}>
            {loading ? 'Starting…' : 'Begin Adventure'}
          </Btn>
          <Btn onClick={() => setShowHistory(true)} color={C.blue}>History</Btn>
          <Btn onClick={onBack} color={C.blue}>Back</Btn>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Main layout
  // ---------------------------------------------------------------------------
  const phase = run.phase;

  function renderMain() {
    if (phase === 'pre_game_forge') {
      return (
        <PreGameForgeScreen run={run} runId={runId} onRunUpdate={handleRunUpdate} onError={handleError} />
      );
    }
    if (phase === 'upgrade') {
      return (
        <UpgradePhase run={run} runId={runId} onRunUpdate={handleRunUpdate} onError={handleError} />
      );
    }
    if (phase === 'upgrade_done') {
      return (
        <UpgradeDoneScreen run={run} runId={runId} onRunUpdate={handleRunUpdate} onError={handleError} />
      );
    }
    if (phase === 'combat') {
      return (
        <CombatScreen key={`${run.level}-${run.fight_index}`} run={run} runId={runId} onRunUpdate={handleRunUpdate} onError={handleError} />
      );
    }
    if (phase === 'pre_boss_shop' || phase === 'shop') {
      return (
        <ShopScreen run={run} runId={runId} onRunUpdate={handleRunUpdate} onError={handleError} />
      );
    }
    if (phase === 'forge') {
      return (
        <ForgeScreen run={run} runId={runId} onRunUpdate={handleRunUpdate} onError={handleError} />
      );
    }
    if (phase === 'game_over') {
      return <GameOverScreen run={run} onRestart={() => setRun(null)} />;
    }
    if (phase === 'victory') {
      return <VictoryScreen run={run} onRestart={() => setRun(null)} />;
    }
    return <div style={{ color: C.muted }}>Unknown phase: {phase}</div>;
  }

  return (
    <div style={{
      minHeight: '100vh', background: C.bg, fontFamily: 'monospace',
      color: C.text, padding: 16,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0, color: C.gold }}>⚔️ Adventure</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <Btn onClick={() => setShowHistory(true)} color={C.blue} style={{ padding: '6px 12px', fontSize: 12 }}>
            History
          </Btn>
          <Btn onClick={onBack} color={C.blue} style={{ padding: '6px 14px', fontSize: 12 }}>
            ← Back
          </Btn>
        </div>
      </div>

      <RunHeader run={run} />

      <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
        <PlayerPanel player={run.player} ownedItems={run.owned_items} />
        <div style={{ flex: 1 }}>
          {renderMain()}
        </div>
        <RunPath run={run} />
      </div>
    </div>
  );
}
