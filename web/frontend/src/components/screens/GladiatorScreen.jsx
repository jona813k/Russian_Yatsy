/**
 * GladiatorScreen — Gladiator Showdown gauntlet UI.
 *
 * All 3 tier fights run simultaneously in a vertical gallery.
 * Each FightPanel is a self-contained animated arena.
 */
import { useState, useEffect, useRef } from 'react';
import { gladiatorApi } from '../../api.js';
import { C } from '../../theme.js';
import { Btn } from '../ui/Btn.jsx';
import { HPBar } from '../ui/HPBar.jsx';
import { PlayerSprite } from '../sprites/PlayerSprite.jsx';
import { SummonSprite } from '../sprites/SummonSprite.jsx';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const SUMMON_TIERS = [
  { min: 1,  name: 'Imp',      hp: 10  },
  { min: 6,  name: 'Wolf',     hp: 25  },
  { min: 12, name: 'Orc',      hp: 50  },
  { min: 18, name: 'Skeleton', hp: 100 },
  { min: 24, name: 'Dragon',   hp: 200 },
];

function getSummon(level) {
  if (!level || level <= 0) return null;
  let tier = null;
  for (const t of SUMMON_TIERS) { if (level >= t.min) tier = t; }
  return tier;
}

function getMsgColor(type, msg) {
  if (type === 'system') return msg?.includes('Victory') ? C.green : C.crimson;
  if (type === 'enemy')  return '#C8B49A';
  if (type === 'summon') return '#C084FC';
  if (type === 'spell')  return '#60A5FA';
  if (type === 'burn')   return '#F97316';
  if (msg?.includes('CRIT') || msg?.includes('EXECUTE') || msg?.includes('×3')) return C.yellow;
  return C.crimson;
}

function triggerAnim(setter, anim, duration = 500) {
  setter(anim);
  setTimeout(() => setter('idle'), duration);
}

// ---------------------------------------------------------------------------
// Compact arena background (scaled down version)
// ---------------------------------------------------------------------------

function ArenaBackground() {
  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', borderRadius: 6, pointerEvents: 'none' }}>
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '40%',
        background: 'linear-gradient(180deg, #1A0C04 0%, #261408 60%, transparent 100%)',
      }} />
      {Array.from({ length: 3 }, (_, row) =>
        Array.from({ length: 8 }, (_, col) => (
          <div key={`${row}-${col}`} style={{
            position: 'absolute',
            top: row * 18, left: col * 72 + (row % 2 === 0 ? 0 : 36),
            width: 70, height: 16, borderRadius: 1,
            border: '1px solid rgba(92,58,16,0.25)',
            background: row % 2 === 0 ? 'rgba(30,18,8,0.4)' : 'rgba(38,22,10,0.35)',
          }} />
        ))
      )}
      {[60, 260].map((x, i) => (
        <div key={i} style={{ position: 'absolute', top: 6, left: x, width: 20, textAlign: 'center' }}>
          <div style={{ width: 4, height: 14, background: '#5C3A10', borderRadius: 2, margin: '0 auto' }} />
          <div style={{
            width: 9, height: 12, borderRadius: '50% 50% 40% 40%',
            background: 'radial-gradient(ellipse, #E8C84A 0%, #D4722A 60%, transparent 100%)',
            margin: '-6px auto 0',
          }} />
        </div>
      ))}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, height: '50%',
        background: 'linear-gradient(0deg, #6B4A1A 0%, #8A6A3A 30%, transparent 100%)',
        opacity: 0.3,
      }} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Compact HP card
// ---------------------------------------------------------------------------

function MiniCard({ label, name, hp, maxHp, accentColor, alive }) {
  const hpColor = alive
    ? (hp / maxHp > 0.6 ? C.hpHigh : hp / maxHp > 0.3 ? C.hpMid : C.hpLow)
    : '#444';
  return (
    <div style={{
      background: 'rgba(15,10,4,0.85)',
      border: `1px solid ${alive ? (accentColor ?? C.crimson) : C.borderDim}`,
      borderRadius: 4, padding: '3px 7px',
      minWidth: 90, textAlign: 'center',
      opacity: alive ? 1 : 0.5,
      transition: 'opacity 0.4s',
    }}>
      <div style={{ fontSize: 8, color: C.muted, letterSpacing: 1.5, textTransform: 'uppercase', fontFamily: "'Cinzel', serif", marginBottom: 2 }}>
        {label}
      </div>
      <div style={{
        fontSize: 10, color: alive ? (accentColor ?? C.textDim) : C.muted,
        fontFamily: "'Cinzel', serif", marginBottom: 3,
        whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 90,
      }}>
        {alive ? name : `${name} ✝`}
      </div>
      <HPBar current={Math.max(0, hp)} max={maxHp} color={hpColor} />
      <div style={{ fontSize: 9, color: C.muted, marginTop: 1, fontFamily: 'monospace' }}>
        {Math.max(0, Math.round(hp))}/{maxHp}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Individual fight panel
// ---------------------------------------------------------------------------

function FightPanel({ fight, playerStats, playerName, onDone }) {
  const opp          = fight?.opponent_stats ?? {};
  const playerMax    = playerStats?.max_hp ?? 100;
  const playerSummon = getSummon(playerStats?.summon_level ?? 0);
  const oppSummon    = opp?.summon ?? null;
  const oppMax       = opp?.max_hp ?? 100;
  const darkLevel    = playerStats?.dark_level ?? 0;

  const [playerHp,       setPlayerHp]       = useState(playerMax);
  const [enemyHp,        setEnemyHp]        = useState(oppMax);
  const [summonHp,       setSummonHp]       = useState(playerSummon?.hp ?? 0);
  const [summonAlive,    setSummonAlive]    = useState(!!playerSummon);
  const [oppSummonHp,    setOppSummonHp]    = useState(oppSummon?.hp ?? 0);
  const [oppSummonAlive, setOppSummonAlive] = useState(!!oppSummon);
  const [playerAnim,     setPlayerAnim]     = useState('idle');
  const [enemyAnim,      setEnemyAnim]      = useState('idle');
  const [summonAnim,     setSummonAnim]     = useState('idle');
  const [oppSummonAnim,  setOppSummonAnim]  = useState('idle');
  const [darkMult,       setDarkMult]       = useState(1.0);
  const [oppDarkMult,    setOppDarkMult]    = useState(1.0);
  const [log,            setLog]            = useState([]);
  const [result,         setResult]         = useState(null); // 'win' | 'loss' | null
  const [logOpen,        setLogOpen]        = useState(false);

  const addLog = (msg, side, type) =>
    setLog(prev => [...prev.slice(-8), { msg, side, type }]);

  useEffect(() => {
    if (!fight?.combat) return;   // preview panels have no combat yet — don't touch result state

    const events      = fight.combat.events ?? [];
    const finalResult = fight.combat.result ?? 'loss';

    if (!events.length) {
      setResult(finalResult);
      onDone?.();
      return;
    }

    const speedFactor = Math.max(1, (events[events.length - 2]?.time ?? 1) / 12);

    events.forEach(ev => {
      setTimeout(() => {
        if (ev.type === 'player_attack') {
          setPlayerHp(ev.player_hp);
          setEnemyHp(ev.enemy_hp);
          if (ev.dark_mult != null) setDarkMult(ev.dark_mult);

          if (ev.blocked_by_opp) {
            triggerAnim(setPlayerAnim, 'attack', 450);
            let blk = `${fight.opponent_name} blocked!`;
            if (ev.reflect_dmg) blk += ` (${ev.reflect_dmg} reflected)`;
            addLog(blk, 'player', 'attack');
          } else if (ev.opp_summon_dmg != null) {
            triggerAnim(setPlayerAnim, 'attack', 450);
            setTimeout(() => triggerAnim(setOppSummonAnim, 'hit', 320), 180);
            setOppSummonHp(ev.opp_summon_hp);
            if (ev.opp_summon_died) setOppSummonAlive(false);
            let txt = `Struck ${oppSummon?.name ?? 'summon'} for ${ev.dmg}${ev.crit ? ' (CRIT!)' : ''}`;
            if (ev.opp_summon_died) txt += ' — falls!';
            addLog(txt, 'player', 'attack');
          } else {
            triggerAnim(setPlayerAnim, 'attack', 450);
            setTimeout(() => triggerAnim(setEnemyAnim, 'hit', 320), 200);
            let txt = `Struck for ${ev.dmg}${ev.crit ? ' (CRIT!)' : ''}${ev.execute ? ' ⚡EXECUTE' : ''}${ev.triple_hit ? ' ×3' : ''}`;
            if (ev.heal > 0) txt += ` +${ev.heal}hp`;
            addLog(txt, 'player', 'attack');
          }

        } else if (ev.type === 'spell') {
          setEnemyHp(ev.enemy_hp);
          setPlayerHp(ev.player_hp);
          if (ev.summon_hp != null) setSummonHp(ev.summon_hp);
          if (ev.dark_mult != null) setDarkMult(ev.dark_mult);
          triggerAnim(setPlayerAnim, 'attack', 450);
          setTimeout(() => triggerAnim(setEnemyAnim, 'hit', 320), 200);
          let sp = `Spell — ${ev.dmg} dmg${ev.heal > 0 ? ` +${ev.heal}hp` : ''}`;
          if (ev.frost) sp += ' [Frost]';
          if (ev.burn_applied) sp += ' [Burn]';
          if (ev.summon_heal) sp += ` (${playerSummon?.name}+${ev.summon_heal}hp)`;
          addLog(sp, 'player', 'spell');

        } else if (ev.type === 'burn_tick') {
          setEnemyHp(ev.enemy_hp);
          triggerAnim(setEnemyAnim, 'hit', 320);
          addLog(`Burn — ${ev.dmg} dmg`, 'player', 'burn');

        } else if (ev.type === 'summon_attack') {
          setEnemyHp(ev.enemy_hp);
          if (ev.dark_mult != null) setDarkMult(ev.dark_mult);
          triggerAnim(setSummonAnim, 'attack', 450);
          setTimeout(() => triggerAnim(setEnemyAnim, 'hit', 320), 180);
          let sm = `${playerSummon?.name ?? 'Summon'}: ${ev.dmg} dmg`;
          if (ev.summon_heal) sm += ` +${ev.summon_heal}hp`;
          addLog(sm, 'player', 'summon');

        } else if (ev.type === 'enemy_attack') {
          if (ev.dark_mult != null) setOppDarkMult(ev.dark_mult);
          if (ev.blocked) {
            triggerAnim(setPlayerAnim, 'hit', 320);
            let blk = `${fight.opponent_name} — blocked!`;
            if (ev.thorns) { blk += ` (${ev.thorns} reflected)`; setEnemyHp(ev.enemy_hp); }
            addLog(blk, 'enemy', 'enemy');
          } else {
            triggerAnim(setEnemyAnim, 'attack', 450);
            setPlayerHp(ev.player_hp);
            if (ev.summon_hp != null) {
              setSummonHp(ev.summon_hp);
              setTimeout(() => triggerAnim(setSummonAnim, 'hit', 320), 200);
            } else {
              setTimeout(() => triggerAnim(setPlayerAnim, 'hit', 320), 200);
            }
            if (ev.summon_died) { setSummonAlive(false); triggerAnim(setSummonAnim, 'dead', 1100); }
            let msg = ev.summon_hp != null && !ev.summon_died
              ? `${fight.opponent_name} strikes ${playerSummon?.name} for ${ev.summon_dmg}`
              : `${fight.opponent_name} strikes you for ${ev.dmg}`;
            if (ev.summon_died) msg += ` — ${playerSummon?.name} falls!`;
            if (ev.enemy_lifesteal_heal) { msg += ` [+${ev.enemy_lifesteal_heal}hp]`; setEnemyHp(ev.enemy_hp); }
            addLog(msg, 'enemy', 'enemy');
          }

        } else if (ev.type === 'opp_spell') {
          setPlayerHp(ev.player_hp);
          setEnemyHp(ev.enemy_hp);
          if (ev.opp_summon_hp != null) setOppSummonHp(ev.opp_summon_hp);
          triggerAnim(setEnemyAnim, 'attack', 450);
          setTimeout(() => triggerAnim(setPlayerAnim, 'hit', 320), 200);
          if (ev.dmg === 0 && ev.opp_summon_heal) {
            addLog(`${fight.opponent_name} heals ${oppSummon?.name} +${ev.opp_summon_heal}hp`, 'enemy', 'spell');
          } else {
            let sp = `${fight.opponent_name} spell — ${ev.dmg} dmg${ev.heal > 0 ? ` +${ev.heal}hp` : ''}`;
            if (ev.burn_applied) sp += ' [Burn]';
            if (ev.frost) sp += ' [Frost]';
            addLog(sp, 'enemy', 'spell');
          }

        } else if (ev.type === 'opp_burn_tick') {
          setPlayerHp(ev.player_hp);
          triggerAnim(setPlayerAnim, 'hit', 320);
          addLog(`${fight.opponent_name} burn — ${ev.dmg} dmg`, 'enemy', 'burn');

        } else if (ev.type === 'opp_summon_attack') {
          setPlayerHp(ev.player_hp);
          if (ev.opp_summon_hp != null) setOppSummonHp(ev.opp_summon_hp);
          triggerAnim(setOppSummonAnim, 'attack', 450);
          setTimeout(() => triggerAnim(setPlayerAnim, 'hit', 320), 180);
          let sm = `${oppSummon?.name ?? 'Summon'}: ${ev.dmg} dmg`;
          if (ev.opp_summon_heal) sm += ` +${ev.opp_summon_heal}hp`;
          addLog(sm, 'enemy', 'summon');

        } else if (ev.type === 'combat_end') {
          setPlayerHp(ev.player_hp);
          setEnemyHp(ev.enemy_hp);
          const r = ev.result;
          if (r === 'win') {
            triggerAnim(setEnemyAnim, 'dead', 1200);
            addLog('Victory! The crowd roars!', 'system', 'system');
          } else {
            triggerAnim(setPlayerAnim, 'dead', 1200);
            addLog('Fallen…', 'system', 'system');
          }
          setTimeout(() => {
            setResult(r);
            onDone?.();
          }, 1400);
        }
      }, (ev.time / speedFactor) * 1000);
    });
  }, [fight]);

  // ── Panel render ───────────────────────────────────────────────────────────
  return (
    <div style={{
      border: `1px solid ${result === 'win' ? C.green + '66' : result === 'loss' ? C.crimson + '55' : C.border}`,
      borderRadius: 8,
      overflow: 'hidden',
      background: 'rgba(10,6,2,0.6)',
      transition: 'border-color 0.5s',
    }}>
      {/* Arena row */}
      <div style={{
        position: 'relative', height: 170,
        display: 'flex', alignItems: 'flex-end', justifyContent: 'center',
        padding: '8px 12px 8px', gap: 16,
      }}>
        <ArenaBackground />

        {/* Result overlay */}
        {result && (
          <div style={{
            position: 'absolute', inset: 0, zIndex: 10,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: result === 'win'
              ? 'rgba(0,0,0,0.45)'
              : 'rgba(0,0,0,0.55)',
            pointerEvents: 'none',
          }}>
            <div style={{
              fontSize: 22, fontFamily: "'Cinzel Decorative', serif",
              letterSpacing: 3,
              color: result === 'win' ? C.gold : C.scarlet,
              textShadow: result === 'win'
                ? '0 0 20px rgba(212,175,55,0.7)'
                : '0 0 20px rgba(155,26,26,0.7)',
            }}>
              {result === 'win' ? '⚔ Victory' : '💀 Defeated'}
            </div>
          </div>
        )}

        {/* Player side */}
        <div style={{ position: 'relative', zIndex: 2, display: 'flex', alignItems: 'flex-end', gap: 6 }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
            <PlayerSprite anim={playerAnim} size={100} />
            <MiniCard
              label="You" name={playerName}
              hp={playerHp} maxHp={playerMax}
              alive={playerHp > 0} accentColor={C.bronze}
            />
            {darkLevel > 0 && (
              <div style={{
                fontSize: 9, fontFamily: 'monospace', color: '#C084FC',
                background: 'rgba(192,132,252,0.1)',
                border: '1px solid rgba(192,132,252,0.3)',
                borderRadius: 3, padding: '1px 5px', whiteSpace: 'nowrap',
              }}>
                Dark {darkLevel}: ×{darkMult.toFixed(2)}
              </div>
            )}
          </div>
          {playerSummon && summonAlive && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
              <SummonSprite name={playerSummon.name} anim={summonAnim} size={78} />
              <MiniCard
                label="Summon" name={playerSummon.name}
                hp={summonHp} maxHp={playerSummon.hp}
                alive={summonAlive} accentColor="#C084FC"
              />
            </div>
          )}
        </div>

        {/* VS */}
        <div style={{
          position: 'relative', zIndex: 2,
          color: C.crimson, fontSize: 12, fontWeight: '700',
          fontFamily: "'Cinzel Decorative', serif", letterSpacing: 2,
          paddingBottom: 48, flexShrink: 0,
          textShadow: '0 0 8px rgba(155,26,26,0.5)',
        }}>
          VS
        </div>

        {/* Opponent side (mirrored) */}
        <div style={{ position: 'relative', zIndex: 2, display: 'flex', alignItems: 'flex-end', gap: 6, flexDirection: 'row-reverse' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
            <div style={{ transform: 'scaleX(-1)' }}>
              <PlayerSprite anim={enemyAnim} size={100} />
            </div>
            <MiniCard
              label="Gladiator" name={fight?.opponent_name ?? '???'}
              hp={enemyHp} maxHp={oppMax}
              alive={enemyHp > 0} accentColor={C.scarlet}
            />
            {opp?.dark_level > 0 && (
              <div style={{
                fontSize: 9, fontFamily: 'monospace', color: '#F87171',
                background: 'rgba(248,113,113,0.08)',
                border: '1px solid rgba(248,113,113,0.25)',
                borderRadius: 3, padding: '1px 5px', whiteSpace: 'nowrap',
              }}>
                Dark {opp.dark_level}: ×{oppDarkMult.toFixed(2)}
              </div>
            )}
          </div>
          {oppSummon && oppSummonAlive && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
              <div style={{ transform: 'scaleX(-1)' }}>
                <SummonSprite name={oppSummon.name} anim={oppSummonAnim} size={78} />
              </div>
              <MiniCard
                label="Summon" name={oppSummon.name}
                hp={oppSummonHp} maxHp={oppSummon.hp}
                alive={oppSummonAlive} accentColor="#E87070"
              />
            </div>
          )}
        </div>
      </div>

      {/* Collapsible log strip */}
      <div style={{ borderTop: `1px solid ${C.borderDim}`, background: 'rgba(12,7,2,0.7)' }}>
        <div
          onClick={() => setLogOpen(o => !o)}
          style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '4px 10px', cursor: 'pointer', userSelect: 'none',
          }}
        >
          <span style={{ fontSize: 9, color: C.muted, letterSpacing: 2, textTransform: 'uppercase', fontFamily: "'Cinzel', serif" }}>
            Battle Chronicle
          </span>
          {!logOpen && log.length > 0 && (
            <span style={{ fontSize: 9, color: getMsgColor(log[log.length-1].type, log[log.length-1].msg), fontFamily: "'Cinzel', serif", maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {log[log.length-1].msg}
            </span>
          )}
          <span style={{ color: C.muted, fontSize: 9 }}>{logOpen ? '▲' : '▼'}</span>
        </div>
        {logOpen && (
          <div style={{ padding: '2px 10px 6px', display: 'flex', flexDirection: 'column', gap: 1 }}>
            {log.length === 0 ? (
              <div style={{ fontSize: 10, color: C.muted, fontFamily: "'Cinzel', serif", opacity: 0.5 }}>
                Awaiting combat…
              </div>
            ) : log.slice(-6).map((entry, i) => {
              const color = getMsgColor(entry.type, entry.msg);
              return (
                <div key={i} style={{
                  fontSize: 10, color, fontFamily: "'Cinzel', serif", letterSpacing: 0.2,
                  opacity: i < log.slice(-6).length - 1 ? 0.55 : 1,
                  whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                }}>
                  {entry.side === 'player' ? '▶ ' : entry.side === 'enemy' ? '◀ ' : '◆ '}
                  {entry.msg}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main screen
// ---------------------------------------------------------------------------

export function GladiatorScreen({ gauntlet: initialGauntlet, playerStats, onUpdate, onFinish }) {
  const [g, setG]               = useState(initialGauntlet);
  const [phase, setPhase]       = useState('pre_tier'); // pre_tier | animating | tier_result
  const [loading, setLoading]   = useState(false);
  const [tierFights, setTierFights] = useState(null);  // [{opponent_name, opponent_stats, combat}, ...]
  const [tierResult, setTierResult] = useState(null);  // { wins, advancing, eliminated }
  const [showLeaderboard, setShowLeaderboard] = useState(false);
  const [leaderboard, setLeaderboard]         = useState([]);

  const doneCount = useRef(0);

  useEffect(() => { onUpdate(g); }, [g]);

  // Reset between tiers
  useEffect(() => {
    if (phase === 'pre_tier') {
      setTierFights(null);
      setTierResult(null);
      doneCount.current = 0;
    }
  }, [phase]);

  function handleFightDone() {
    doneCount.current += 1;
    if (doneCount.current >= 3) {
      // All 3 animations finished — short pause then show result
      setTimeout(() => setPhase('tier_result'), 800);
    }
  }

  async function doFightTier() {
    setLoading(true);
    try {
      const resp = await gladiatorApi.fightTier(g.gauntlet_id);
      doneCount.current = 0;
      setTierFights(resp.fights);
      setTierResult({
        wins:      resp.tier_wins,
        advancing: resp.advancing,
        eliminated: resp.eliminated,
      });
      setG(resp.gauntlet);
      setPhase('animating');
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
    } catch (e) { console.error(e); }
  }

  const playerName = g.player_name;
  const opponents  = g.opponents ?? [];

  // ── Tier result overlay ───────────────────────────────────────────────────
  if (phase === 'tier_result' && tierResult) {
    const { wins, advancing, eliminated } = tierResult;
    return (
      <div style={overlayStyle}>
        <div style={cardStyle}>
          {eliminated ? (
            <>
              <div style={{ fontSize: 28, marginBottom: 10 }}>⚔</div>
              <div style={{ color: C.scarlet, fontSize: 18, fontFamily: "'Cinzel Decorative', serif", letterSpacing: 2, marginBottom: 8 }}>
                Eliminated
              </div>
              <div style={{ color: C.textDim, fontSize: 13, marginBottom: 4 }}>
                {playerName} fell with{' '}
                <span style={{ color: C.gold, fontWeight: '700' }}>{g.current_wins} win{g.current_wins !== 1 ? 's' : ''}</span>
              </div>
              <div style={{ color: C.muted, fontSize: 11, marginBottom: 8 }}>
                Tier result: {wins}/3 wins
              </div>
              <div style={{ color: C.muted, fontSize: 11, marginBottom: 20 }}>
                Your record has been saved to the leaderboard.
              </div>
              <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
                <Btn onClick={loadLeaderboard} color={C.gold} style={{ fontSize: 12, color: C.dark }}>Leaderboard</Btn>
                <Btn onClick={onFinish} color={C.stone} style={{ fontSize: 12 }}>New Run</Btn>
              </div>
            </>
          ) : (
            <>
              <div style={{ fontSize: 28, marginBottom: 10 }}>🏆</div>
              <div style={{ color: C.gold, fontSize: 18, fontFamily: "'Cinzel Decorative', serif", letterSpacing: 2, marginBottom: 8 }}>
                Advancing!
              </div>
              <div style={{ color: C.textDim, fontSize: 13, marginBottom: 4 }}>
                {playerName} won{' '}
                <span style={{ color: C.gold, fontWeight: '700' }}>{wins}/3</span>{' '}
                fights this tier
              </div>
              <div style={{ color: C.muted, fontSize: 11, marginBottom: 20 }}>
                Total wins: {g.current_wins}
              </div>
              <Btn
                onClick={() => setPhase('pre_tier')}
                color={C.crimson}
                style={{ fontSize: 13, padding: '10px 24px' }}
              >
                Next Tier →
              </Btn>
            </>
          )}

          {showLeaderboard && leaderboard.length > 0 && (
            <div style={{ marginTop: 20, textAlign: 'left' }}>
              <div style={{ fontSize: 10, color: C.muted, letterSpacing: 3, textTransform: 'uppercase', marginBottom: 8 }}>Leaderboard</div>
              {leaderboard.map((row, i) => (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between',
                  padding: '4px 0', borderBottom: `1px solid ${C.borderDim}`, fontSize: 12,
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

  // ── Complete (no opponents at next tier) ──────────────────────────────────
  if (g.status === 'complete' && phase !== 'tier_result') {
    return (
      <div style={overlayStyle}>
        <div style={cardStyle}>
          <div style={{ fontSize: 28, marginBottom: 10 }}>👑</div>
          <div style={{ color: C.gold, fontSize: 18, fontFamily: "'Cinzel Decorative', serif", letterSpacing: 2, marginBottom: 8 }}>
            Undefeated!
          </div>
          <div style={{ color: C.textDim, fontSize: 13, marginBottom: 20 }}>
            No challengers remain. {playerName} stands alone.
          </div>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
            <Btn onClick={loadLeaderboard} color={C.gold} style={{ fontSize: 12, color: C.dark }}>Leaderboard</Btn>
            <Btn onClick={onFinish} color={C.stone} style={{ fontSize: 12 }}>New Run</Btn>
          </div>
        </div>
      </div>
    );
  }

  // ── Gallery view ──────────────────────────────────────────────────────────
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>

      {/* Tier strip */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '6px 12px', marginBottom: 10,
        background: 'rgba(20,10,4,0.7)',
        border: `1px solid ${C.borderDim}`, borderRadius: 6,
        fontFamily: "'Cinzel', serif",
      }}>
        <div style={{ fontSize: 10, color: C.gold, letterSpacing: 2, textTransform: 'uppercase' }}>
          Gladiator Showdown
        </div>
        <div style={{ fontSize: 10, color: C.muted }}>
          Tier {g.current_wins + 1} — need 2/3 wins to advance
        </div>
        <div style={{ fontSize: 11, color: C.bronze, fontFamily: 'monospace' }}>
          {g.current_wins} W total
        </div>
      </div>

      {/* 3-fight gallery */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 12 }}>
        {[0, 1, 2].map(i => {
          const fightData = tierFights ? tierFights[i] : null;
          const opponent  = opponents[i];
          // Pre-fight preview (before animation starts): show opponent name from gauntlet
          const previewFight = fightData ?? (opponent ? {
            opponent_name:  opponent.name,
            opponent_stats: opponent.stats,
            combat:         null,
          } : null);

          return (
            <div key={i}>
              <FightPanel
                fight={previewFight}
                playerStats={playerStats}
                playerName={playerName}
                onDone={fightData ? handleFightDone : undefined}
              />
            </div>
          );
        })}
      </div>

      {/* Action bar */}
      {phase === 'pre_tier' && (
        <Btn
          onClick={doFightTier}
          disabled={loading}
          color={C.crimson}
          style={{ width: '100%', fontSize: 13, padding: '11px 0', letterSpacing: 2 }}
        >
          {loading ? 'Preparing fights…' : '⚔ Fight All Three'}
        </Btn>
      )}

      {phase === 'animating' && (
        <div style={{
          textAlign: 'center', color: C.muted, fontSize: 11,
          padding: '8px 0', fontFamily: "'Cinzel', serif", letterSpacing: 1,
        }}>
          The arena roars…
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const overlayStyle = {
  minHeight: '100vh',
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  background: 'radial-gradient(ellipse at 50% 20%, #1E0C04 0%, #0F0A04 60%)',
  fontFamily: "'Cinzel', serif", padding: 20,
};

const cardStyle = {
  textAlign: 'center', width: '100%', maxWidth: 400,
  background: 'linear-gradient(180deg, rgba(30,18,8,0.97) 0%, rgba(15,10,4,0.99) 100%)',
  border: `1px solid ${C.border}`, borderRadius: 8,
  padding: '30px 32px', boxShadow: '0 20px 60px rgba(0,0,0,0.8)',
};
