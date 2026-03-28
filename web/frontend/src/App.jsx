import { useState, useEffect, useCallback, useMemo } from 'react';
import { api } from './api';
import RpgApp from './RpgApp';

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------
const C = {
  bg: '#f5f5f0',
  white: '#ffffff',
  border: '#d0d0c8',
  green: '#3a9e5f',
  greenLight: '#e8f7ee',
  orange: '#e07b2a',
  orangeLight: '#fff3e0',
  yellow: '#ffe066',
  yellowLight: '#fffbe6',
  blue: '#2e86c1',
  blueLight: '#eaf4fb',
  red: '#c0392b',
  text: '#1a1a1a',
  textMuted: '#888',
  dieSetAside: '#e0e0e0',
};

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------
function useGame() {
  const [state, setState] = useState(null);
  const [lastResult, setLastResult] = useState(null);
  const [failedRoll, setFailedRoll] = useState(null); // { dice, number } shown briefly on turn_end
  const [aiHint, setAiHint] = useState(null);
  const [lastPicked, setLastPicked] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const startGame = useCallback(async () => {
    setLoading(true);
    setError(null);
    setAiHint(null);
    setLastPicked(null);
    setLastResult(null);
    setFailedRoll(null);
    try { setState(await api.newGame()); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, []);

  const selectNumber = useCallback(async (number) => {
    if (!state || loading) return;
    setLoading(true);
    setLastPicked(number);
    const collectingNumber = number; // capture before async
    try {
      const newState = await api.selectNumber(state.session_id, number);
      const result = newState.result ?? null;
      setLastResult(result);

      // If the turn ended because remaining dice didn't match, show them briefly
      // before revealing the fresh 6-dice roll for the new turn
      if (result?.state === 'turn_end' && result?.info?.failed_dice?.length) {
        setFailedRoll({ dice: result.info.failed_dice, number: collectingNumber });
        setState(newState);
        setTimeout(() => setFailedRoll(null), 1600);
      } else {
        setState(newState);
      }
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [state, loading]);

  const skipTurn = useCallback(async () => {
    if (!state || loading) return;
    setLoading(true);
    try {
      const newState = await api.skipTurn(state.session_id);
      setLastResult(newState.result ?? null);
      setState(newState);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [state, loading]);

  return { state, lastResult, failedRoll, aiHint, lastPicked, loading, error, startGame, selectNumber, skipTurn };
}

// ---------------------------------------------------------------------------
// Turn status banner — shows what just happened after each collect
// ---------------------------------------------------------------------------
function TurnStatus({ lastResult, state }) {
  if (!lastResult) return null;

  const rs = lastResult.state;
  const n = state?.selected_number;
  const remaining = state?.num_dice_in_hand ?? 0;
  const collected = lastResult.info?.collected ?? 0;

  let msg, bg, color;

  if (rs === 'continue') {
    msg = `Collected ${collected} — rolling ${remaining} remaining ${remaining === 1 ? 'die' : 'dice'} (still collecting ${n}s)`;
    bg = C.blueLight; color = C.blue;
  } else if (rs === 'turn_end') {
    msg = `No more ${n}s — turn ended, new roll with 6 dice`;
    bg = '#fef9e7'; color = '#b7950b';
  } else if (rs === 'completed_number') {
    msg = `✓ ${lastResult.info?.completed}s complete! Fresh roll with 6 dice`;
    bg = C.greenLight; color = C.green;
  } else if (rs === 'bonus_turn') {
    msg = `All 6 dice used — bonus roll with 6 fresh dice!`;
    bg = C.greenLight; color = C.green;
  } else {
    return null;
  }

  return (
    <div style={{
      padding: '8px 14px', borderRadius: 8, fontSize: 13,
      background: bg, color, marginBottom: 12,
      border: `1px solid ${color}44`,
    }}>
      {msg}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Die pips
// ---------------------------------------------------------------------------
const PIP_POSITIONS = {
  1: [[50,50]],
  2: [[28,28],[72,72]],
  3: [[28,28],[50,50],[72,72]],
  4: [[28,28],[72,28],[28,72],[72,72]],
  5: [[28,28],[72,28],[50,50],[28,72],[72,72]],
  6: [[28,24],[72,24],[28,50],[72,50],[28,76],[72,76]],
};

function DieFace({ value, size }) {
  if (value >= 1 && value <= 6) {
    return (
      <svg width={size - 16} height={size - 16} viewBox="0 0 100 100">
        {PIP_POSITIONS[value].map(([cx, cy], i) => (
          <circle key={i} cx={cx} cy={cy} r={9} fill="currentColor" />
        ))}
      </svg>
    );
  }
  return <span style={{ fontSize: size * 0.36, fontWeight: 700 }}>{value}</span>;
}

// ---------------------------------------------------------------------------
// Die — visual states:
//   userSelected : player clicked this die (bold orange)
//   preview      : will also be collected (dashed orange)
//   illegal      : can't be used this roll (faded)
//   setAside     : collected earlier this turn (grey, non-interactive)
// ---------------------------------------------------------------------------
function Die({ value, onClick, userSelected, preview, illegal, setAside, size = 64 }) {
  const [hovered, setHovered] = useState(false);

  let bg, border, color, cursor, opacity;
  if (setAside) {
    bg = C.dieSetAside; border = `2px dashed ${C.border}`;
    color = C.textMuted; cursor = 'default'; opacity = 0.55;
  } else if (userSelected) {
    bg = C.yellow; border = `3px solid ${C.orange}`;
    color = C.text; cursor = 'pointer'; opacity = 1;
  } else if (preview) {
    bg = C.yellowLight; border = `2px dashed ${C.orange}`;
    color = C.text; cursor = 'pointer'; opacity = 1;
  } else if (illegal) {
    bg = C.white; border = `2px solid ${C.border}`;
    color = C.border; cursor = 'default'; opacity = 0.35;
  } else {
    bg = hovered ? C.yellowLight : C.white;
    border = `2px solid ${hovered ? C.orange : C.border}`;
    color = C.text; cursor = 'pointer'; opacity = 1;
  }

  return (
    <div
      onClick={!illegal && !setAside ? onClick : undefined}
      onMouseEnter={() => !illegal && !setAside && setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        width: size, height: size, borderRadius: 14,
        border, background: bg, color, cursor, opacity,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        transition: 'all 0.1s',
        boxShadow: userSelected
          ? `0 0 0 3px ${C.orange}55`
          : '0 1px 4px rgba(0,0,0,0.12)',
        userSelect: 'none',
      }}
    >
      <DieFace value={value} size={size} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// FailedRollDisplay — shows the dice that were rolled but didn't match,
// briefly before the new turn starts
// ---------------------------------------------------------------------------
function FailedRollDisplay({ failedRoll }) {
  if (!failedRoll) return null;
  return (
    <div>
      <div style={{
        padding: '8px 14px', borderRadius: 8, fontSize: 13,
        background: '#fef9e7', color: '#b7950b',
        border: '1px solid #f0d060',
        marginBottom: 12,
      }}>
        No more <strong>{failedRoll.number}s</strong> — turn ended
      </div>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', opacity: 0.5 }}>
        {failedRoll.dice.map((value, i) => (
          <Die key={i} value={value} illegal size={64} />
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// DiceBoard
//
// Turn cycle (all within one "turn"):
//   Roll 6 dice → pick number → collect matching → re-roll remaining → repeat
//   Turn ends when remaining dice can't match the chosen number
//   Turn also ends if all 6 dice are used (bonus roll starts fresh)
//
// Selection rules:
//   Click 1 die (value 1-6)          → indicates single collection for that value
//   Click 2 dice of same value       → same as clicking 1 (singles)
//   Click 2 dice with different vals → indicates pair collection for their sum
//   All other matching dice auto-preview, collected together on submit
// ---------------------------------------------------------------------------
function DiceBoard({ state, onSelect, onSkip, disabled }) {
  const [selected, setSelected] = useState(new Set());
  useEffect(() => { setSelected(new Set()); }, [state]);

  const { dice = [], dice_groups = {}, selected_number, collected_this_turn = 0 } = state;

  // Derive which number the selection intends to collect
  const derivedTarget = useMemo(() => {
    const sel = Array.from(selected);
    if (sel.length === 0) return null;
    const values = sel.map(i => dice[i]);

    if (sel.length === 1) {
      const v = values[0];
      return (v <= 6 && dice_groups[String(v)]) ? v : null;
    }
    if (sel.length === 2) {
      const [a, b] = values;
      // Two dice selected → always try pair first (6+6=12, not 6 singles)
      const sum = a + b;
      if (sum <= 12 && dice_groups[String(sum)]) return sum;
      // Fall back to singles only if both dice show same value and pair isn't legal
      if (a === b && a <= 6 && dice_groups[String(a)]) return a;
      return null;
    }
    return null;
  }, [selected, dice, dice_groups]);

  // All dice that will be collected (user picks + auto-matched)
  const previewIndices = useMemo(
    () => derivedTarget != null ? (dice_groups[String(derivedTarget)] ?? []) : [],
    [derivedTarget, dice_groups]
  );

  const legalDice = useMemo(
    () => new Set(Object.values(dice_groups).flat()),
    [dice_groups]
  );

  // Auto-skip when no dice can form any legal combination (e.g. need 12 but no 6+6)
  useEffect(() => {
    if (legalDice.size === 0 && !disabled && onSkip) {
      const t = setTimeout(() => onSkip(), 1500);
      return () => clearTimeout(t);
    }
  }, [legalDice.size, disabled, onSkip]);

  function handleDieClick(i) {
    if (disabled) return;
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(i)) { next.delete(i); }
      else if (next.size >= 2) { return new Set([i]); }
      else { next.add(i); }
      return next;
    });
  }

  function handleSubmit() {
    if (derivedTarget == null || disabled) return;
    onSelect(derivedTarget);
  }

  const invalidSelection = selected.size > 0 && derivedTarget == null;

  return (
    <div>
      {/* Set-aside dice: collected earlier in this same turn */}
      {selected_number && collected_this_turn > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
          <span style={{ fontSize: 13, color: C.textMuted }}>
            Set aside ({selected_number}s):
          </span>
          <div style={{ display: 'flex', gap: 6 }}>
            {Array.from({ length: collected_this_turn }).map((_, i) => (
              <Die key={i} value={selected_number} setAside size={48} />
            ))}
          </div>
        </div>
      )}

      {/* Current roll label */}
      {selected_number && (
        <div style={{ fontSize: 13, color: C.blue, marginBottom: 8 }}>
          Re-rolled {dice.length} {dice.length === 1 ? 'die' : 'dice'} — still collecting <strong>{selected_number}s</strong>
        </div>
      )}

      {/* Active dice */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        {dice.map((value, i) => (
          <Die
            key={i}
            value={value}
            onClick={() => handleDieClick(i)}
            userSelected={selected.has(i)}
            preview={!selected.has(i) && previewIndices.includes(i)}
            illegal={!legalDice.has(i)}
            disabled={disabled}
            size={64}
          />
        ))}
      </div>

      {/* Collect button */}
      <div style={{ marginTop: 14, minHeight: 44 }}>
        {derivedTarget != null && !disabled && (
          <button onClick={handleSubmit} style={{
            padding: '10px 24px', fontSize: 15, fontWeight: 600,
            borderRadius: 8, border: 'none',
            background: C.orange, color: C.white, cursor: 'pointer',
            boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
          }}>
            Collect {derivedTarget}s &nbsp;
            <span style={{ fontWeight: 400, fontSize: 13 }}>
              ({previewIndices.length} {previewIndices.length === 1 ? 'die' : 'dice'})
            </span>
          </button>
        )}
        {invalidSelection && (
          <p style={{ color: C.red, fontSize: 13, margin: 0 }}>
            These dice don't form a valid combination
          </p>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Progress board
// ---------------------------------------------------------------------------
function ProgressBoard({ progress, completed }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 8, marginTop: 28 }}>
      {Array.from({ length: 12 }, (_, i) => i + 1).map(n => {
        const count = progress?.[String(n)] ?? progress?.[n] ?? 0;
        const done = completed?.includes(n) || count >= 6;
        return (
          <div key={n} style={{
            padding: '8px 6px',
            textAlign: 'center',
            border: `2px solid ${done ? C.green : C.border}`,
            borderRadius: 8,
            background: done ? C.greenLight : C.white,
          }}>
            <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 5 }}>{n}</div>
            <div style={{ display: 'flex', gap: 3, justifyContent: 'center' }}>
              {Array.from({ length: 6 }, (_, i) => (
                <div key={i} style={{
                  width: 8,
                  height: 20,
                  borderRadius: 3,
                  background: i < count ? C.green : '#e0e0da',
                }} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Coach panel
// ---------------------------------------------------------------------------
function CoachPanel({ aiHint, playerPicked }) {
  const [open, setOpen] = useState(false);
  if (!aiHint?.available || !aiHint.rankings?.length) return null;
  const best = aiHint.rankings[0];
  const wasOptimal = playerPicked === best.number;

  return (
    <div style={{
      marginTop: 16, padding: '10px 14px', borderRadius: 8, fontSize: 14,
      border: `1.5px solid ${wasOptimal ? C.green : C.orange}`,
      background: wasOptimal ? C.greenLight : C.orangeLight,
    }}>
      <span style={{ fontWeight: 600 }}>AI: </span>
      {wasOptimal
        ? <span style={{ color: C.green }}>✓ optimal choice</span>
        : <span style={{ color: C.orange }}>
            recommended <strong>{best.number}</strong>, you picked <strong>{playerPicked}</strong>
          </span>
      }
      <button onClick={() => setOpen(o => !o)} style={{
        marginLeft: 12, fontSize: 12, color: C.textMuted,
        background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline',
      }}>
        {open ? 'hide' : 'see ranking'}
      </button>
      {open && (
        <ol style={{ margin: '8px 0 0 0', paddingLeft: 20 }}>
          {aiHint.rankings.map(r => (
            <li key={r.number} style={{ color: r.rank === 1 ? C.green : C.text }}>
              {r.number} — collects {r.collectible} dice{r.rank === 1 ? ' ★' : ''}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Mode selector
// ---------------------------------------------------------------------------
function ModeSelect({ onSelect }) {
  return (
    <div style={{
      minHeight: '100vh', background: '#1a1a2e', display: 'flex',
      flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      fontFamily: 'monospace', color: '#e0e0e0',
    }}>
      <h1 style={{ color: '#f1c40f', marginBottom: 8 }}>Russian Yatzy</h1>
      <p style={{ color: '#888', marginBottom: 32 }}>Choose a mode</p>
      <div style={{ display: 'flex', gap: 24 }}>
        <button onClick={() => onSelect('classic')} style={{
          background: '#2e86c1', color: '#fff', border: 'none', borderRadius: 8,
          padding: '20px 36px', fontSize: 18, cursor: 'pointer', fontFamily: 'monospace',
        }}>
          🎲 Classic
          <div style={{ fontSize: 12, color: '#cde', marginTop: 6 }}>Pure Yatzy game</div>
        </button>
        <button onClick={() => onSelect('adventure')} style={{
          background: '#c0392b', color: '#fff', border: 'none', borderRadius: 8,
          padding: '20px 36px', fontSize: 18, cursor: 'pointer', fontFamily: 'monospace',
        }}>
          ⚔️ Adventure
          <div style={{ fontSize: 12, color: '#fcc', marginTop: 6 }}>RPG roguelike</div>
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------
export default function App() {
  const [mode, setMode] = useState(null);
  const game = useGame();

  useEffect(() => {
    if (mode === 'classic') game.startGame();
  }, [mode]);

  if (!mode) return <ModeSelect onSelect={setMode} />;
  if (mode === 'adventure') return <RpgApp onBack={() => setMode(null)} />;

  // Classic Yatzy mode
  const { state, lastResult, failedRoll, aiHint, lastPicked, loading, error, startGame, selectNumber, skipTurn } = game;

  if (!state && loading) return <div style={{ padding: 40 }}>Loading…</div>;

  return (
    <div style={{
      maxWidth: 680, margin: '0 auto', padding: '32px 24px',
      fontFamily: "'Segoe UI', system-ui, sans-serif",
      color: C.text, background: C.bg, minHeight: '100vh',
    }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 28 }}>Russian Yatzy</h1>
        <span style={{ color: C.textMuted, fontSize: 14 }}>Turn {state?.turns ?? 0}</span>
      </div>

      {error && <p style={{ color: C.red, fontSize: 14 }}>Error: {error}</p>}

      {state && (
        <>
          {state.is_won ? (
            <div>
              <h2 style={{ color: C.green }}>Finished in {state.turns} turns!</h2>
              <button onClick={startGame} style={btnStyle}>Play again</button>
            </div>
          ) : (
            <div>
              {failedRoll
                ? <FailedRollDisplay failedRoll={failedRoll} />
                : <>
                    <TurnStatus lastResult={lastResult} state={state} />
                    <DiceBoard state={state} onSelect={selectNumber} onSkip={skipTurn} disabled={loading} />
                  </>
              }
            </div>
          )}

          <ProgressBoard progress={state.progress} completed={state.completed} />

          <div style={{ marginTop: 24 }}>
            <button onClick={startGame} disabled={loading} style={btnStyle}>New game</button>
          </div>
        </>
      )}
    </div>
  );
}

const btnStyle = {
  padding: '8px 20px', fontSize: 14, borderRadius: 6,
  border: `1px solid ${C.border}`, background: C.white, cursor: 'pointer',
};
