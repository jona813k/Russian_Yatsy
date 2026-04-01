/**
 * RPG Adventure mode — gladiator theme orchestrator.
 * All game logic and API calls are unchanged; only visual rendering is new.
 */
import { useState } from 'react';
import { rpgApi, RunExpiredError } from './api';

// Layout
import { RunHeader }   from './components/layout/RunHeader.jsx';
import { PlayerPanel } from './components/layout/PlayerPanel.jsx';
import { RunPath }     from './components/layout/RunPath.jsx';

// Screens
import { StartScreen }         from './components/screens/StartScreen.jsx';
import { CombatScreen }        from './components/screens/CombatScreen.jsx';
import { UpgradePhase }        from './components/screens/UpgradePhase.jsx';
import { UpgradeDoneScreen }   from './components/screens/UpgradeDoneScreen.jsx';
import { ShopScreen }          from './components/screens/ShopScreen.jsx';
import { ForgeScreen }         from './components/screens/ForgeScreen.jsx';
import { PreGameForgeScreen }  from './components/screens/PreGameForgeScreen.jsx';
import { GameOverScreen }      from './components/screens/GameOverScreen.jsx';
import { VictoryScreen }       from './components/screens/VictoryScreen.jsx';
import { HistoryScreen }       from './components/screens/HistoryScreen.jsx';

// Theme
import { C } from './theme.js';

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
    } catch {
      setError('Could not connect to server. Is the backend running?');
    }
    setLoading(false);
  }

  function handleRunUpdate(resp) {
    setRun(resp);
  }

  function handleError(e) {
    if (e instanceof RunExpiredError) {
      setRun(null);
      setRunId(null);
      setError(e.message);
    } else {
      console.error(e);
    }
  }

  // ── History screen ──────────────────────────────────────────────────────
  if (showHistory) {
    return <HistoryScreen onBack={() => setShowHistory(false)} />;
  }

  // ── Start screen ────────────────────────────────────────────────────────
  if (!run) {
    return (
      <StartScreen
        onStart={startRun}
        onHistory={() => setShowHistory(true)}
        onBack={onBack}
        loading={loading}
        error={error}
      />
    );
  }

  // ── Active run ───────────────────────────────────────────────────────────
  const phase = run.phase;

  function renderMain() {
    const props = { run, runId, onRunUpdate: handleRunUpdate, onError: handleError };

    if (phase === 'pre_game_forge')  return <PreGameForgeScreen {...props} />;
    if (phase === 'upgrade')         return <UpgradePhase {...props} />;
    if (phase === 'upgrade_done')    return <UpgradeDoneScreen {...props} />;
    if (phase === 'combat')          return <CombatScreen key={`${run.level}-${run.fight_index}`} {...props} />;
    if (phase === 'pre_boss_shop' || phase === 'shop') return <ShopScreen {...props} />;
    if (phase === 'forge')           return <ForgeScreen {...props} />;
    if (phase === 'game_over')       return <GameOverScreen run={run} onRestart={() => setRun(null)} />;
    if (phase === 'victory')         return <VictoryScreen run={run} onRestart={() => setRun(null)} />;
    return <div style={{ color: C.muted, fontFamily: "'Cinzel', serif" }}>Unknown phase: {phase}</div>;
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: `radial-gradient(ellipse at 50% 0%, #1E0C04 0%, #0F0A04 50%)`,
      fontFamily: "'Cinzel', serif",
      color: C.text,
      padding: 16,
    }}>
      {/* Top bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 14,
      }}>
        <h2 style={{
          margin: 0,
          color: C.gold,
          fontSize: 17,
          fontFamily: "'Cinzel Decorative', serif",
          letterSpacing: 2,
          textShadow: `0 0 15px rgba(212,175,55,0.3)`,
        }}>
          ⚔ Russian Yatzy: Gladiator
        </h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => setShowHistory(true)}
            style={{
              background: 'transparent',
              color: C.muted,
              border: `1px solid ${C.borderDim}`,
              borderRadius: 4,
              padding: '5px 12px',
              cursor: 'pointer',
              fontSize: 11,
              fontFamily: "'Cinzel', serif",
              letterSpacing: 1,
              transition: 'all 0.15s',
            }}
            onMouseEnter={e => { e.target.style.color = C.text; e.target.style.borderColor = C.border; }}
            onMouseLeave={e => { e.target.style.color = C.muted; e.target.style.borderColor = C.borderDim; }}
          >
            History
          </button>
          {onBack && (
            <button
              onClick={onBack}
              style={{
                background: 'transparent',
                color: C.muted,
                border: `1px solid ${C.borderDim}`,
                borderRadius: 4,
                padding: '5px 12px',
                cursor: 'pointer',
                fontSize: 11,
                fontFamily: "'Cinzel', serif",
                letterSpacing: 1,
                transition: 'all 0.15s',
              }}
              onMouseEnter={e => { e.target.style.color = C.text; e.target.style.borderColor = C.border; }}
              onMouseLeave={e => { e.target.style.color = C.muted; e.target.style.borderColor = C.borderDim; }}
            >
              ← Exit
            </button>
          )}
        </div>
      </div>

      <RunHeader run={run} />

      <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
        <PlayerPanel player={run.player} ownedItems={run.owned_items} />
        <div style={{ flex: 1, minWidth: 0 }}>
          {renderMain()}
        </div>
        <RunPath run={run} />
      </div>
    </div>
  );
}
