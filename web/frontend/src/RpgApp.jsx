/**
 * RPG Adventure mode — gladiator theme orchestrator.
 * All game logic and API calls are unchanged; only visual rendering is new.
 */
import { useState } from 'react';
import { rpgApi, RunExpiredError } from './api';
import { GladiatorScreen } from './components/screens/GladiatorScreen.jsx';

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
import { BugReportModal } from './components/ui/BugReportModal.jsx';

const BUG_REPORTING = import.meta.env.VITE_ENABLE_BUG_REPORTING === 'true';

export default function RpgApp({ onBack }) {
  const [run, setRun]           = useState(null);
  const [runId, setRunId]       = useState(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [gauntlet, setGauntlet] = useState(null);  // active gladiator gauntlet state
  const [showBugReport, setShowBugReport] = useState(false);

  async function startRun(name = 'Anonymous') {
    setLoading(true);
    setError(null);
    try {
      const resp = await rpgApi.newRun(name);
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

  // ── Gladiator Showdown screen ───────────────────────────────────────────
  if (gauntlet) {
    return (
      <GladiatorScreen
        gauntlet={gauntlet}
        runId={runId}
        onUpdate={setGauntlet}
        onFinish={() => { setGauntlet(null); setRun(null); setRunId(null); }}
      />
    );
  }

  // ── Start screen ────────────────────────────────────────────────────────
  if (!run) {
    return (
      <>
        <StartScreen
          onStart={(name) => startRun(name)}
          onHistory={() => setShowHistory(true)}
          onBack={onBack}
          loading={loading}
          error={error}
        />
        {BUG_REPORTING && showBugReport && (
          <BugReportModal run={null} runId={null} onClose={() => setShowBugReport(false)} />
        )}
        {BUG_REPORTING && (
          <button
            onClick={() => setShowBugReport(true)}
            style={{
              position: 'fixed', bottom: 16, right: 16, zIndex: 100,
              background: 'rgba(15,10,4,0.85)',
              color: C.muted,
              border: `1px solid ${C.borderDim}`,
              borderRadius: 4,
              padding: '5px 12px',
              cursor: 'pointer',
              fontSize: 11,
              fontFamily: "'Cinzel', serif",
            }}
          >
            🐛 Bug
          </button>
        )}
      </>
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
    if (phase === 'victory')         return <VictoryScreen run={run} runId={runId} onRestart={() => setRun(null)} onGauntlet={setGauntlet} />;
    return <div style={{ color: C.muted, fontFamily: "'Cinzel', serif" }}>Unknown phase: {phase}</div>;
  }

  return (
    <div style={{
      height: '100vh',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      background: `radial-gradient(ellipse at 50% 0%, #1E0C04 0%, #0F0A04 50%)`,
      fontFamily: "'Cinzel', serif",
      color: C.text,
      padding: '10px 14px 8px',
    }}>
      {/* Top bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 8,
        flexShrink: 0,
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
          {BUG_REPORTING && <button
            onClick={() => setShowBugReport(true)}
            title="Report a bug"
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
            onMouseEnter={e => { e.target.style.color = C.scarlet; e.target.style.borderColor = C.crimson; }}
            onMouseLeave={e => { e.target.style.color = C.muted; e.target.style.borderColor = C.borderDim; }}
          >
            🐛 Bug
          </button>}
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

      {/* RunHeader — fixed */}
      <div style={{ flexShrink: 0 }}>
        <RunHeader run={run} />
      </div>

      {/* Main 3-column layout — fills remaining viewport height, each column scrolls internally */}
      <div style={{
        flex: 1,
        overflow: 'hidden',
        display: 'flex',
        gap: 12,
        alignItems: 'stretch',
        minHeight: 0,
      }}>
        {/* Player panel */}
        <div style={{ flexShrink: 0, overflowY: 'auto', paddingRight: 2 }}>
          <PlayerPanel player={run.player} ownedItems={run.owned_items} />
        </div>

        {/* Main content */}
        <div style={{ flex: 1, overflowY: 'auto', minWidth: 0, paddingRight: 4 }}>
          {renderMain()}
        </div>

        {/* Run path */}
        <div style={{ flexShrink: 0, overflowY: 'auto' }}>
          <RunPath run={run} />
        </div>
      </div>

      {BUG_REPORTING && showBugReport && (
        <BugReportModal run={run} runId={runId} onClose={() => setShowBugReport(false)} />
      )}
    </div>
  );
}
