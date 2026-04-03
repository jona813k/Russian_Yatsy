/**
 * GladiatorScreen — Gladiator Showdown gauntlet UI.
 *
 * Receives the gauntlet state from the backend and lets the player fight
 * (or skip) through opponents 3 at a time, advancing until they lose.
 */
import { useState, useEffect, useRef } from 'react';
import { gladiatorApi } from '../../api.js';
import { C } from '../../theme.js';
import { Btn } from '../ui/Btn.jsx';
import { HPBar } from '../ui/HPBar.jsx';

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatRow({ label, value, color }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
      <span style={{ color: C.muted, fontSize: 11, fontFamily: "'Cinzel', serif" }}>{label}</span>
      <span style={{ color: color ?? C.text, fontSize: 11, fontFamily: 'monospace', fontWeight: '600' }}>{value}</span>
    </div>
  );
}

function OpponentCard({ opponent }) {
  const s = opponent.stats;
  return (
    <div style={{
      background: 'rgba(30,10,4,0.85)',
      border: `1px solid ${C.crimson}66`,
      borderRadius: 6,
      padding: '14px 18px',
      marginBottom: 14,
    }}>
      <div style={{ fontSize: 10, color: C.muted, letterSpacing: 3, textTransform: 'uppercase', marginBottom: 6 }}>
        Opponent
      </div>
      <div style={{
        fontSize: 16, color: C.scarlet, fontFamily: "'Cinzel', serif",
        fontWeight: '700', letterSpacing: 1, marginBottom: 10,
      }}>
        {opponent.name}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 20px' }}>
        <StatRow label="HP"           value={s.max_hp}                         color={C.hpHigh} />
        <StatRow label="Attack"       value={s.attack_dmg}                     color={C.sand} />
        <StatRow label="Speed"        value={`${s.attack_speed}/s`}            color={C.bronze} />
        <StatRow label="Armor"        value={`${s.armor}%`}                    color={C.stone} />
        <StatRow label="Crit"         value={`${s.crit_chance}%`}              color={C.yellow} />
        <StatRow label="Lifesteal"    value={`${s.lifesteal}%`}                color={C.green} />
        {s.dark_level > 0   && <StatRow label="Dark"    value={s.dark_level}   color="#C084FC" />}
        {s.summon_level > 0 && <StatRow label="Summon"  value={s.summon_level} color={C.bronze} />}
        {s.spell_level > 0  && <StatRow label="Spell"   value={s.spell_level}  color="#60A5FA" />}
      </div>
    </div>
  );
}

function FightPips({ wins, total = 3 }) {
  return (
    <div style={{ display: 'flex', gap: 6, justifyContent: 'center', marginBottom: 6 }}>
      {Array.from({ length: total }, (_, i) => (
        <div key={i} style={{
          width: 12, height: 12, borderRadius: '50%',
          background: i < wins ? C.green : 'rgba(255,255,255,0.1)',
          border: `1px solid ${i < wins ? C.green : C.borderDim}`,
          transition: 'background 0.3s',
        }} />
      ))}
    </div>
  );
}

function CombatLog({ lines }) {
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [lines]);

  if (!lines.length) return null;
  return (
    <div ref={ref} style={{
      height: 140,
      overflowY: 'auto',
      background: 'rgba(0,0,0,0.5)',
      border: `1px solid ${C.borderDim}`,
      borderRadius: 4,
      padding: '8px 10px',
      marginBottom: 12,
      fontFamily: 'monospace',
      fontSize: 11,
    }}>
      {lines.map((l, i) => (
        <div key={i} style={{ color: l.color ?? C.textDim, marginBottom: 1 }}>{l.text}</div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Event → log line converter (mirrors CombatScreen logic)
// ---------------------------------------------------------------------------

function eventsToLog(events) {
  return events.map(ev => {
    if (ev.type === 'player_attack') {
      let text = `You struck for ${ev.dmg}${ev.crit ? ' (CRIT!)' : ''}`;
      if (ev.heal > 0) text += ` +${ev.heal}hp`;
      if (ev.dark_mult > 1) text += ` [Dark ×${ev.dark_mult}]`;
      return { text, color: ev.crit ? C.yellow : C.sand };
    }
    if (ev.type === 'enemy_attack') {
      if (ev.blocked) return { text: 'You blocked the attack!', color: C.green };
      if (ev.summon_dmg != null) return { text: `Summon took ${ev.summon_dmg} damage`, color: C.muted };
      return { text: `Opponent hits you for ${ev.dmg}`, color: C.scarlet };
    }
    if (ev.type === 'spell') return { text: `Spell: ${ev.dmg} damage`, color: '#60A5FA' };
    if (ev.type === 'summon_attack') return { text: `Summon attacks for ${ev.dmg}`, color: C.bronze };
    if (ev.type === 'combat_end') {
      return ev.result === 'win'
        ? { text: '— Victory! —', color: C.green }
        : { text: '— Defeated —', color: C.scarlet };
    }
    return null;
  }).filter(Boolean);
}

// ---------------------------------------------------------------------------
// Main screen
// ---------------------------------------------------------------------------

export function GladiatorScreen({ gauntlet: initialGauntlet, onUpdate, onFinish }) {
  const [g, setG]             = useState(initialGauntlet);
  const [phase, setPhase]     = useState('pre_fight');  // pre_fight | animating | post_fight | tier_result | done
  const [log, setLog]         = useState([]);
  const [loading, setLoading] = useState(false);
  const [lastResult, setLastResult] = useState(null);  // 'win' | 'lose'
  const [tierResult, setTierResult] = useState(null);  // { advancing, eliminated, wins }
  const [showLeaderboard, setShowLeaderboard] = useState(false);
  const [leaderboard, setLeaderboard]         = useState([]);

  // Sync upward whenever g changes
  useEffect(() => { onUpdate(g); }, [g]);

  const currentOpponent = g.next_opponent;
  const winsLabel = g.current_wins === 0 ? '0 wins' : `${g.current_wins} win${g.current_wins !== 1 ? 's' : ''}`;

  async function doFight(skip) {
    setLoading(true);
    setLog([]);
    try {
      const resp = await gladiatorApi.fight(g.gauntlet_id, skip);

      // Build log from events
      const events = resp.combat?.events ?? [];
      const newLog = skip ? [
        { text: `[Fight skipped]`, color: C.muted },
        { text: resp.fight_result === 'win' ? '— Victory! —' : '— Defeated —',
          color: resp.fight_result === 'win' ? C.green : C.scarlet },
      ] : eventsToLog(events);
      setLog(newLog);
      setLastResult(resp.fight_result);

      // Animate events if watching
      if (!skip && events.length > 0) {
        setPhase('animating');
        const duration = Math.min(8000, (events[events.length - 2]?.time ?? 5) * 600);
        setTimeout(() => {
          setG(resp);
          setPhase('post_fight');
          if (resp.tier_done) {
            setTierResult({ advancing: resp.advancing, eliminated: resp.eliminated, wins: resp.current_wins });
            setPhase('tier_result');
          }
        }, duration);
      } else {
        setG(resp);
        setPhase('post_fight');
        if (resp.tier_done) {
          setTierResult({ advancing: resp.advancing, eliminated: resp.eliminated, wins: resp.current_wins });
          setPhase('tier_result');
        }
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  }

  async function loadLeaderboard() {
    try {
      const rows = await gladiatorApi.getLeaderboard();
      setLeaderboard(rows);
      setShowLeaderboard(true);
    } catch (e) {
      console.error(e);
    }
  }

  // ── Tier result (advance or eliminated) ─────────────────────────────────
  if (phase === 'tier_result' && tierResult) {
    if (tierResult.eliminated) {
      return (
        <div style={containerStyle}>
          <div style={cardStyle}>
            <div style={{ fontSize: 28, marginBottom: 10 }}>⚔</div>
            <div style={{ color: C.scarlet, fontSize: 18, fontFamily: "'Cinzel Decorative', serif", letterSpacing: 2, marginBottom: 8 }}>
              Eliminated
            </div>
            <div style={{ color: C.textDim, fontSize: 13, marginBottom: 6 }}>
              {g.player_name} fell at{' '}
              <span style={{ color: C.gold, fontWeight: '700' }}>{tierResult.wins} win{tierResult.wins !== 1 ? 's' : ''}</span>
            </div>
            <div style={{ color: C.muted, fontSize: 11, marginBottom: 20 }}>
              Your record has been added to the leaderboard.
            </div>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Btn onClick={loadLeaderboard} color={C.gold} style={{ fontSize: 12, color: C.dark }}>
                Leaderboard
              </Btn>
              <Btn onClick={onFinish} color={C.stone} style={{ fontSize: 12 }}>
                New Run
              </Btn>
            </div>

            {showLeaderboard && leaderboard.length > 0 && (
              <div style={{ marginTop: 20, textAlign: 'left' }}>
                <div style={{ fontSize: 10, color: C.muted, letterSpacing: 3, textTransform: 'uppercase', marginBottom: 8 }}>
                  Leaderboard
                </div>
                {leaderboard.map((row, i) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between',
                    padding: '4px 0', borderBottom: `1px solid ${C.borderDim}`,
                    fontSize: 12,
                  }}>
                    <span style={{ color: i === 0 ? C.gold : C.text, fontFamily: "'Cinzel', serif" }}>
                      {i === 0 ? '👑 ' : `${i + 1}. `}{row.name}
                    </span>
                    <span style={{ color: C.bronze, fontFamily: 'monospace' }}>
                      {row.wins_achieved} win{row.wins_achieved !== 1 ? 's' : ''}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      );
    }

    // Advancing
    return (
      <div style={containerStyle}>
        <div style={cardStyle}>
          <div style={{ fontSize: 28, marginBottom: 10 }}>🏆</div>
          <div style={{ color: C.gold, fontSize: 18, fontFamily: "'Cinzel Decorative', serif", letterSpacing: 2, marginBottom: 8 }}>
            Advancing!
          </div>
          <div style={{ color: C.textDim, fontSize: 13, marginBottom: 20 }}>
            {g.player_name} moves to{' '}
            <span style={{ color: C.gold, fontWeight: '700' }}>{tierResult.wins} win{tierResult.wins !== 1 ? 's' : ''}</span>
          </div>
          <Btn
            onClick={() => { setPhase('pre_fight'); setLog([]); setLastResult(null); setTierResult(null); }}
            color={C.crimson}
            style={{ fontSize: 13, padding: '10px 24px' }}
          >
            Continue →
          </Btn>
        </div>
      </div>
    );
  }

  // ── Done (no opponents at next tier — auto-win) ──────────────────────────
  if (g.status === 'complete' && phase !== 'tier_result') {
    return (
      <div style={containerStyle}>
        <div style={cardStyle}>
          <div style={{ fontSize: 28, marginBottom: 10 }}>👑</div>
          <div style={{ color: C.gold, fontSize: 18, fontFamily: "'Cinzel Decorative', serif", letterSpacing: 2, marginBottom: 8 }}>
            Undefeated!
          </div>
          <div style={{ color: C.textDim, fontSize: 13, marginBottom: 20 }}>
            No challengers remain at this level.
          </div>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
            <Btn onClick={loadLeaderboard} color={C.gold} style={{ fontSize: 12, color: C.dark }}>Leaderboard</Btn>
            <Btn onClick={onFinish} color={C.stone} style={{ fontSize: 12 }}>New Run</Btn>
          </div>
        </div>
      </div>
    );
  }

  // ── Active fight screen ──────────────────────────────────────────────────
  return (
    <div style={containerStyle}>
      <div style={{ ...cardStyle, maxWidth: 460 }}>
        {/* Header */}
        <div style={{
          fontSize: 10, color: C.muted, letterSpacing: 4,
          textTransform: 'uppercase', marginBottom: 4,
        }}>
          Gladiator Showdown
        </div>
        <div style={{
          color: C.gold, fontSize: 15, fontFamily: "'Cinzel', serif",
          letterSpacing: 1, marginBottom: 14,
          textShadow: `0 0 10px rgba(212,175,55,0.4)`,
        }}>
          {g.player_name} — {winsLabel}
        </div>

        {/* Fight pips for current tier */}
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 10, color: C.muted, marginBottom: 4 }}>
            Round {g.fight_in_tier + (phase === 'post_fight' || phase === 'animating' ? 0 : 0)} of 3
            {' — '}{g.wins_in_tier} win{g.wins_in_tier !== 1 ? 's' : ''} so far
          </div>
          <FightPips wins={g.wins_in_tier} total={3} />
        </div>

        {/* Opponent card */}
        {currentOpponent && (phase === 'pre_fight' || phase === 'animating') && (
          <OpponentCard opponent={currentOpponent} />
        )}

        {/* Combat log */}
        <CombatLog lines={log} />

        {/* Post-fight result banner */}
        {phase === 'post_fight' && lastResult && (
          <div style={{
            textAlign: 'center',
            padding: '10px 16px',
            marginBottom: 12,
            borderRadius: 4,
            background: lastResult === 'win'
              ? 'rgba(74,154,90,0.15)'
              : 'rgba(155,26,26,0.15)',
            border: `1px solid ${lastResult === 'win' ? C.green + '66' : C.crimson + '66'}`,
            color: lastResult === 'win' ? C.green : C.scarlet,
            fontSize: 13,
            fontFamily: "'Cinzel', serif",
            letterSpacing: 1,
          }}>
            {lastResult === 'win' ? '⚔ Victory' : '💀 Defeated'}
          </div>
        )}

        {/* Action buttons */}
        {(phase === 'pre_fight') && currentOpponent && (
          <div style={{ display: 'flex', gap: 10 }}>
            <Btn
              onClick={() => doFight(false)}
              disabled={loading}
              color={C.crimson}
              style={{ flex: 1, fontSize: 13, padding: '10px 0' }}
            >
              {loading ? 'Fighting…' : `Fight ${currentOpponent.name}`}
            </Btn>
            <Btn
              onClick={() => doFight(true)}
              disabled={loading}
              color={C.stone}
              style={{ fontSize: 12, padding: '10px 16px' }}
            >
              Skip
            </Btn>
          </div>
        )}

        {phase === 'animating' && (
          <div style={{ textAlign: 'center', color: C.muted, fontSize: 12, padding: 10 }}>
            Simulating…
          </div>
        )}

        {phase === 'post_fight' && !loading && g.status === 'active' && g.next_opponent && (
          <Btn
            onClick={() => { setPhase('pre_fight'); setLog([]); setLastResult(null); }}
            color={C.bronze}
            style={{ width: '100%', fontSize: 13, padding: '10px 0', marginTop: 4 }}
          >
            Next Fight →
          </Btn>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const containerStyle = {
  minHeight: '100vh',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  background: `radial-gradient(ellipse at 50% 20%, #1E0C04 0%, #0F0A04 60%)`,
  fontFamily: "'Cinzel', serif",
  padding: 20,
};

const cardStyle = {
  textAlign: 'center',
  width: '100%',
  maxWidth: 400,
  background: `linear-gradient(180deg, rgba(30,18,8,0.97) 0%, rgba(15,10,4,0.99) 100%)`,
  border: `1px solid ${C.border}`,
  borderRadius: 8,
  padding: '30px 32px',
  boxShadow: '0 20px 60px rgba(0,0,0,0.8)',
};
