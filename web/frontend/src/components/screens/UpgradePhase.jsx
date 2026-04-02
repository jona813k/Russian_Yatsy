import { useState } from 'react';
import { rpgApi } from '../../api.js';
import { C } from '../../theme.js';
import { Die } from '../ui/Die.jsx';
import { Btn } from '../ui/Btn.jsx';

const NUMBER_NAMES = {
  1:'Ones',2:'Twos',3:'Threes',4:'Fours',5:'Fives',6:'Sixes',
  7:'Sevens',8:'Eights',9:'Nines',10:'Tens',11:'Elevens',12:'Twelves',
};

const DIE_STAT_LABELS = {
  1:'Spd',2:'Dmg',3:'Crit',4:'Armor',5:'HP',
  6:'Research',7:'Gold',8:'Summon',9:'Spell',10:'Block',11:'Life Steal',12:'Dark',
};

const UPGRADE_INFO = {
  1:  { perDie:'+3% speed',   bonus:'+3% at 4' },
  2:  { perDie:'+1 dmg',      bonus:'+1 at 4' },
  3:  { perDie:'+1% crit',    bonus:'+1% at 4' },
  4:  { perDie:'+2% armor',   bonus:'+2% at 4' },
  5:  { perDie:'+5 HP',       bonus:'+5 at 4' },
  6:  { perDie:null,           bonus:'+slot at 4 / +pick at 6' },
  7:  { perDie:'+20 gold',    bonus:'+20g at 4' },
  8:  { perDie:'+1 summon',   bonus:'+1 at 4' },
  9:  { perDie:'+1 spell',    bonus:'+1 at 4' },
  10: { perDie:'+2% block',   bonus:'+2% at 3' },
  11: { perDie:'+1% LS',      bonus:'+1% at 3' },
  12: { perDie:'+1 dark',     bonus:'+1 at 3' },
};

// Stat accent colors
const STAT_COLORS = {
  1:'#6BBFDC',2:'#DC6B6B',3:'#E8C84A',4:'#7ACC7A',5:'#DC8B4A',
  6:'#C084FC',7:'#D4AF37',8:'#9B60DC',9:'#60B0DC',10:'#4ADE80',
  11:'#F87171',12:'#C084FC',
};

function computeCollectedValues(diceArr, targetNum) {
  const remaining = [...diceArr];
  const collected = [];
  for (let i = remaining.length - 1; i >= 0; i--) {
    if (remaining[i] === targetNum) collected.push(remaining.splice(i, 1)[0]);
  }
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

// Sand + wood table background for the prep room
function TableBackground() {
  return (
    <div style={{
      position: 'absolute', inset: 0, borderRadius: 6, overflow: 'hidden', pointerEvents: 'none',
    }}>
      {/* Wood grain effect */}
      {Array.from({ length: 8 }, (_, i) => (
        <div key={i} style={{
          position: 'absolute',
          left: 0, right: 0,
          top: `${i * 14}%`,
          height: '12%',
          background: i % 2 === 0
            ? 'rgba(92,58,16,0.08)'
            : 'rgba(60,32,10,0.06)',
          borderTop: '1px solid rgba(92,58,16,0.05)',
        }} />
      ))}
      {/* Torch glow from corner */}
      <div style={{
        position: 'absolute', top: -20, right: -20,
        width: 150, height: 150,
        background: 'radial-gradient(ellipse, rgba(212,114,42,0.1) 0%, transparent 70%)',
      }} />
    </div>
  );
}

export function UpgradePhase({ run, runId, onRunUpdate, onError }) {
  const yatzy = run.yatzy;
  const [selectedIndices, setSelectedIndices] = useState([]);
  const [failedDiceDisplay, setFailedDiceDisplay] = useState(null); // shows in prep table as illegal
  const [actionResult, setActionResult] = useState(null);
  const [rerolling, setRerolling] = useState(false);
  const [stagedDice, setStagedDice] = useState([]);

  // No auto-clear on turn change — staged dice persist so the player can see
  // what they already collected alongside the new roll (see handleCollect).

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

  const targetNumber = (() => {
    if (selectedNumber !== null && selectedNumber !== undefined) return selectedNumber;
    if (selectedIndices.length === 0) return null;
    if (selectedIndices.length === 1) {
      const v = dice[selectedIndices[0]];
      return legalNumbers.includes(v) ? v : null;
    }
    if (selectedIndices.length === 2) return dice[selectedIndices[0]] + dice[selectedIndices[1]];
    return null;
  })();

  const isLegalTarget = targetNumber !== null && legalNumbers.includes(targetNumber);

  function getDieState(idx) {
    if (selectedIndices.includes(idx)) return 'userSelected';
    const dieVal = dice[idx];
    if (selectedIndices.length === 2) {
      if (!isLegalTarget) return 'illegal';
      const groupForTarget = diceGroups[String(targetNumber)] || [];
      return groupForTarget.includes(idx) ? 'preview' : 'illegal';
    }
    if (selectedIndices.length === 1) {
      const selVal = dice[selectedIndices[0]];
      const pairSum = selVal + dieVal;
      if (pairSum >= 7 && pairSum <= 12 && legalNumbers.includes(pairSum)) return 'normal';
      if (dieVal === selVal && legalNumbers.includes(selVal)) return 'preview';
      const anyLegal = Object.entries(diceGroups).some(([n, idxs]) =>
        idxs.includes(idx) && legalNumbers.includes(parseInt(n)));
      return anyLegal ? 'normal' : 'illegal';
    }
    const anyLegal = Object.entries(diceGroups).some(([n, idxs]) =>
      idxs.includes(idx) && legalNumbers.includes(parseInt(n)));
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
    const tempDice = [...dice];
    const justCollected = computeCollectedValues(dice, targetNumber).map(v => {
      const idx = tempDice.indexOf(v);
      if (idx !== -1) tempDice[idx] = null;
      return { value: v, dieType: idx !== -1 ? diceTypes[idx] : undefined };
    });
    try {
      const resp = await rpgApi.upgradeSelect(runId, targetNumber);
      setSelectedIndices([]);
      setActionResult(resp.action_result);
      const st = resp.action_result?.state;
      const hasFailed = !!resp.action_result?.info?.failed_dice;

      if (st === 'completed_number' || st === 'won' || st === 'bonus_turn') {
        // Number finished — clear staged and start fresh
        setStagedDice([]);
      } else if (!hasFailed) {
        // Mid-turn re-roll: accumulate collected dice into staged area
        setStagedDice(prev => [...prev, ...justCollected]);
      } else {
        // Failed roll (turn_end) — move collected dice to staged so they stay
        // visible alongside the new roll; do NOT clear them
        setStagedDice(prev => [...prev, ...justCollected]);
      }

      if (hasFailed) {
        setFailedDiceDisplay(resp.action_result.info.failed_dice);
        setTimeout(() => { setFailedDiceDisplay(null); setStagedDice([]); onRunUpdate(resp); }, 1200);
      } else {
        onRunUpdate(resp);
      }
    } catch (e) { if (onError) onError(e); else console.error(e); }
  }

  async function handleSkip() {
    setStagedDice([]);
    try {
      const resp = await rpgApi.upgradeSkip(runId);
      setActionResult(resp.action_result);
      onRunUpdate(resp);
    } catch (e) { if (onError) onError(e); else console.error(e); }
  }

  if (!yatzy) return null;

  return (
    <div>
      {/* === TURNS REMAINING === */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        marginBottom: 8,
        padding: '6px 12px',
        background: 'rgba(30,18,8,0.8)',
        border: `1px solid ${C.border}`,
        borderRadius: 6,
      }}>
        <span style={{ color: C.muted, fontSize: 11, fontFamily: "'Cinzel', serif", letterSpacing: 1 }}>
          Turns
        </span>
        <div style={{ display: 'flex', gap: 5 }}>
          {Array.from({ length: run.upgrade_turns_max }, (_, i) => (
            <div key={i} style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              background: i < turnsRemaining
                ? `radial-gradient(circle, ${C.gold} 30%, ${C.bronze} 100%)`
                : '#2A1808',
              border: `1px solid ${i < turnsRemaining ? C.gold : C.borderDim}`,
              boxShadow: i < turnsRemaining ? `0 0 6px ${C.gold}66` : 'none',
              transition: 'all 0.3s',
            }} />
          ))}
        </div>
        <span style={{ color: C.gold, fontWeight: '600', fontSize: 13, fontFamily: 'monospace' }}>
          {turnsRemaining}
        </span>
      </div>

      {/* === WAR TABLE (dice area) === */}
      <div style={{
        position: 'relative',
        background: `linear-gradient(135deg, #1E1208, #261808)`,
        border: `1px solid ${C.border}`,
        borderRadius: 8,
        padding: '10px 12px',
        marginBottom: 10,
      }}>
        <TableBackground />
        <div style={{ position: 'relative', zIndex: 1 }}>
          {/* Header */}
          <div style={{
            fontSize: 9,
            color: C.muted,
            letterSpacing: 3,
            textTransform: 'uppercase',
            fontFamily: "'Cinzel', serif",
            marginBottom: 10,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}>
            <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, transparent, ${C.border})` }} />
            Preparation Table
            <div style={{ flex: 1, height: 1, background: `linear-gradient(270deg, transparent, ${C.border})` }} />
          </div>

          {/* Stash row — fixed height, always rendered to prevent layout shift */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            minHeight: 28,
            marginBottom: 8,
            padding: '3px 0',
          }}>
            {stagedDice.length > 0 && (
              <>
                <span style={{ color: C.mutedDim, fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', fontFamily: "'Cinzel', serif", flexShrink: 0 }}>
                  Stash
                </span>
                <div style={{ width: 1, height: 16, background: C.borderDim, flexShrink: 0 }} />
                {stagedDice.map((d, i) => (
                  <div key={i} style={{
                    width: 22, height: 22,
                    borderRadius: 4,
                    background: 'rgba(92,58,16,0.25)',
                    border: `1px solid ${C.border}66`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 10,
                    color: C.muted,
                    fontFamily: 'monospace',
                    fontWeight: '600',
                  }}>
                    {d.value}
                  </div>
                ))}
              </>
            )}
          </div>

          {/* Active dice — shows current roll, or failed dice as illegal while transitioning */}
          <div style={{ display: 'flex', gap: 7, alignItems: 'center', minHeight: 60 }}>
            {(failedDiceDisplay || dice).map((val, idx) => (
              <Die
                key={idx}
                value={val}
                state={failedDiceDisplay ? 'illegal' : getDieState(idx)}
                dieType={failedDiceDisplay ? undefined : diceTypes[idx]}
                onClick={failedDiceDisplay ? undefined : () => handleDieClick(idx)}
              />
            ))}
          </div>
        </div>
      </div>

      {/* === ACTIONS === */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 10, flexWrap: 'wrap', alignItems: 'center', minHeight: 40 }}>
        {run.free_reroll_available && !selectedNumber && !hasSkipOnly && (
          <Btn
            color={C.purple}
            disabled={rerolling}
            style={{ fontSize: 12 }}
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
            Free Reroll
          </Btn>
        )}

        {hasSkipOnly && (
          <Btn onClick={handleSkip} color={C.stone} style={{ fontSize: 12 }}>
            No Moves — Skip
          </Btn>
        )}

        {isLegalTarget && (() => {
          const collectedDice = computeCollectedValues(dice, targetNumber);
          const singleCount = collectedDice.filter(v => v === targetNumber).length;
          const pairCount = Math.floor((collectedDice.length - singleCount) / 2);
          const units = singleCount + pairCount;
          const statColor = STAT_COLORS[targetNumber] || C.gold;
          return (
            <Btn
              onClick={handleCollect}
              color={C.crimson}
              style={{ fontSize: 12, boxShadow: `0 0 12px ${statColor}44` }}
            >
              Collect {units} {NUMBER_NAMES[targetNumber] || targetNumber}
            </Btn>
          );
        })()}
      </div>

      {/* === PROGRESS GRID (carved stone tablet style) === */}
      <div style={{
        background: `linear-gradient(180deg, #1A0C04, #130804)`,
        border: `1px solid ${C.border}`,
        borderRadius: 8,
        overflow: 'hidden',
      }}>
        <div style={{
          background: `linear-gradient(90deg, #3A1A08, #2A1004)`,
          borderBottom: `1px solid ${C.border}`,
          padding: '7px 14px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <span style={{ color: C.gold, fontSize: 10, letterSpacing: 2, textTransform: 'uppercase', fontFamily: "'Cinzel', serif" }}>
            Training Progress
          </span>
          <span style={{ color: C.muted, fontSize: 10, fontFamily: 'monospace' }}>
            {Object.values(progress).filter(v => parseInt(v) >= 6).length} / 12 complete
          </span>
        </div>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(6, 1fr)',
          gap: 6,
          padding: 10,
        }}>
          {Array.from({ length: 12 }, (_, i) => {
            const n = i + 1;
            const removed = statRemoved.includes(n);
            const target = statTargets[n] ?? 6;
            const count = Math.min(parseInt(progress[String(n)] || 0), target);
            const info = UPGRADE_INFO[n];
            const statColor = removed ? C.mutedDim : (STAT_COLORS[n] || C.gold);
            const baseThreshold = n >= 10 ? 3 : 4;
            const thresholdAt = target !== 6 ? Math.max(1, Math.round(baseThreshold * target / 6)) : baseThreshold;
            const tooltipLines = removed
              ? 'Removed — no stat gain, but dice still count for pair combinations.'
              : [
                  info.perDie ? `Each die: ${info.perDie}` : null,
                  `Collect ${thresholdAt}: ${info.bonus}`,
                  target !== 6 ? `Target: ${target}` : null,
                ].filter(Boolean).join('\n');

            return (
              <div key={n} style={{
                background: removed ? '#0A0604' : `rgba(30,18,8,0.8)`,
                borderRadius: 5,
                padding: '9px 6px',
                textAlign: 'center',
                border: `1px solid ${removed ? C.borderDim : statColor + '44'}`,
                opacity: removed ? 0.4 : 1,
                position: 'relative',
                cursor: 'help',
              }} title={tooltipLines}>
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2 }}>
                  <span style={{ fontSize: 14, color: removed ? C.mutedDim : statColor, fontFamily: 'monospace', fontWeight: '600' }}>
                    {n}
                  </span>
                </div>
                <div style={{
                  fontSize: 10,
                  color: removed ? C.mutedDim : statColor,
                  marginBottom: 4,
                  whiteSpace: 'nowrap',
                  fontFamily: "'Cinzel', serif",
                  letterSpacing: 0.5,
                }}>
                  {removed ? '✕' : DIE_STAT_LABELS[n]}
                </div>
                {/* Progress bars */}
                <div style={{ display: 'flex', gap: 1.5, justifyContent: 'center' }}>
                  {Array.from({ length: target }, (_, j) => (
                    <div key={j} style={{
                      width: Math.max(12, Math.floor(96 / target)),
                      height: 19,
                      borderRadius: 2,
                      background: removed
                        ? '#1A0C04'
                        : j < count
                        ? statColor
                        : '#1A0A04',
                      border: j === thresholdAt - 1 && !removed
                        ? `1px solid ${statColor}aa`
                        : `1px solid ${removed ? C.borderDim : (j < count ? statColor + '88' : C.borderDim)}`,
                      boxShadow: j < count && !removed ? `0 0 4px ${statColor}44` : 'none',
                      transition: 'all 0.3s',
                    }} />
                  ))}
                </div>
                {/* Threshold marker */}
                {!removed && (
                  <div style={{ fontSize: 12, color: count >= thresholdAt ? statColor : C.mutedDim, marginTop: 2, fontFamily: 'monospace' }}>
                    {count}/{target}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
