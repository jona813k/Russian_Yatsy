import { useState, useEffect, useRef } from 'react';
import { rpgApi } from '../../api.js';
import { C } from '../../theme.js';
import { HPBar } from '../ui/HPBar.jsx';
import { Btn } from '../ui/Btn.jsx';
import { PlayerSprite } from '../sprites/PlayerSprite.jsx';
import { EnemySprite } from '../sprites/EnemySprite.jsx';
import { SummonSprite } from '../sprites/SummonSprite.jsx';

// type: 'attack' | 'spell' | 'summon' | 'burn' | 'enemy' | 'system'
function getMsgColor(type, msg) {
  if (type === 'system') return msg.includes('Victory') ? C.green : C.crimson;
  if (type === 'enemy')  return '#C8B49A';
  if (type === 'summon') return '#C084FC';
  if (type === 'spell')  return '#60A5FA';
  if (type === 'burn')   return '#F97316';
  // attack
  if (msg.includes('CRIT') || msg.includes('EXECUTE') || msg.includes('×3')) return C.yellow;
  return C.crimson;
}

function ArenaBackground() {
  return (
    <div style={{
      position: 'absolute', inset: 0, overflow: 'hidden', borderRadius: 8,
      pointerEvents: 'none',
    }}>
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '40%',
        background: 'linear-gradient(180deg, #1A0C04 0%, #261408 60%, transparent 100%)',
      }} />
      {Array.from({ length: 3 }, (_, row) =>
        Array.from({ length: 8 }, (_, col) => (
          <div key={`${row}-${col}`} style={{
            position: 'absolute',
            top: row * 22,
            left: col * 72 + (row % 2 === 0 ? 0 : 36),
            width: 70, height: 20, borderRadius: 1,
            border: '1px solid rgba(92,58,16,0.3)',
            background: row % 2 === 0 ? 'rgba(30,18,8,0.4)' : 'rgba(38,22,10,0.35)',
          }} />
        ))
      )}
      {[80, 300].map((x, i) => (
        <div key={i} style={{ position: 'absolute', top: 8, left: x, width: 24, textAlign: 'center' }}>
          <div style={{ width: 6, height: 20, background: '#5C3A10', borderRadius: 2, margin: '0 auto' }} />
          <div style={{
            width: 12, height: 16, borderRadius: '50% 50% 40% 40%',
            background: 'radial-gradient(ellipse, #E8C84A 0%, #D4722A 60%, transparent 100%)',
            margin: '-8px auto 0',
          }} />
        </div>
      ))}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, height: '50%',
        background: 'linear-gradient(0deg, #6B4A1A 0%, #8A6A3A 30%, transparent 100%)',
        opacity: 0.35,
      }} />
      <div style={{
        position: 'absolute', bottom: '15%', left: '10%', right: '10%',
        height: 1, background: 'rgba(200,169,110,0.15)', borderRadius: 1,
      }} />
      <div style={{
        position: 'absolute', top: 40, left: 0, right: 0, height: 30,
        display: 'flex', gap: 0, overflow: 'hidden', opacity: 0.3,
      }}>
        {Array.from({ length: 40 }, (_, i) => (
          <div key={i} style={{
            width: 10, height: 20 + Math.sin(i * 1.4) * 6,
            borderRadius: '50% 50% 0 0', background: '#0F0604',
            marginTop: 10 - Math.sin(i * 0.9) * 4, flexShrink: 0,
          }} />
        ))}
      </div>
    </div>
  );
}

function CharacterCard({ name, hp, maxHp, alive, isBoss, isPlayer, _accentColor }) {
  const hpColor = alive
    ? (hp / maxHp > 0.6 ? C.hpHigh : hp / maxHp > 0.3 ? C.hpMid : C.hpLow)
    : '#444';
  const borderColor = !alive ? C.borderDim : _accentColor ?? (isPlayer ? C.bronze : isBoss ? C.scarlet : C.crimson);
  return (
    <div style={{
      background: `linear-gradient(180deg, rgba(30,18,8,0.9) 0%, rgba(15,10,4,0.95) 100%)`,
      border: `1px solid ${borderColor}`, borderRadius: 6, padding: '6px 10px',
      minWidth: 110, textAlign: 'center', opacity: alive ? 1 : 0.5,
      transition: 'opacity 0.4s, border-color 0.3s',
      boxShadow: isBoss && alive ? `0 0 15px rgba(220,32,32,0.3)` : 'none',
    }}>
      <div style={{ fontSize: 9, color: C.muted, letterSpacing: 2, textTransform: 'uppercase', fontFamily: "'Cinzel', serif", marginBottom: 3 }}>
        {_accentColor ? 'Summon' : isPlayer ? 'You' : isBoss ? '⚠ Champion' : 'Enemy'}
      </div>
      <div style={{
        fontSize: 12, fontWeight: '600',
        color: alive ? (_accentColor ?? (isPlayer ? C.bronze : isBoss ? C.scarlet : C.textDim)) : C.muted,
        fontFamily: "'Cinzel', serif", marginBottom: 5,
        whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
      }}>
        {alive ? name : `${name} ✝`}
      </div>
      <HPBar current={Math.max(0, hp)} max={maxHp} color={hpColor} />
      <div style={{ fontSize: 10, color: C.muted, marginTop: 2, fontFamily: 'monospace' }}>
        {Math.max(0, Math.round(hp))} / {maxHp}
      </div>
    </div>
  );
}

export function CombatScreen({ run, runId, onRunUpdate, onError }) {
  const enemy  = run.enemy;
  const summon = run.summon_stats;
  const darkLevel = run.player.dark_level ?? 0;

  const [log, setLog]                 = useState([]);   // [{ msg, side, type }]
  const [loading, setLoading]         = useState(false);
  const [playerHp, setPlayerHp]       = useState(run.player.current_hp);
  const [enemyHp, setEnemyHp]         = useState(enemy?.hp ?? 0);
  const [summonHp, setSummonHp]       = useState(summon?.hp ?? 0);
  const [summonAlive, setSummonAlive] = useState(!!summon);
  const [darkMult, setDarkMult]       = useState(1.0);
  const [pendingNext, setPendingNext] = useState(null);
  const [logOpen, setLogOpen]         = useState(true);
  const [combatError, setCombatError] = useState(null);
  const [retryCount, setRetryCount]   = useState(0);

  const [playerAnim, setPlayerAnim] = useState('idle');
  const [enemyAnim, setEnemyAnim]   = useState('idle');
  const [summonAnim, setSummonAnim] = useState('idle');

  const logRef     = useRef(null);
  const hasStarted = useRef(false);

  const playerMaxHp = run.player.max_hp;
  const enemyMaxHp  = enemy?.hp ?? 1;
  const summonMaxHp = summon?.hp ?? 1;

  useEffect(() => { hasStarted.current = false; }, [retryCount]);

  useEffect(() => {
    if (hasStarted.current) return;
    hasStarted.current = true;
    async function runCombat() {
      setLoading(true);
      setCombatError(null);
      try {
        const resp = await rpgApi.startCombat(runId);
        setLoading(false);
        if (!resp.combat) {
          console.error('[CombatScreen] startCombat response missing combat data', resp);
          setCombatError('Server returned no combat data. Please retry.');
          return;
        }
        animateEvents(resp.combat.events, resp);
      } catch (e) {
        console.error('[CombatScreen] startCombat failed', e);
        setLoading(false);
        setCombatError(`Combat failed to start: ${e?.message ?? 'unknown error'}. Please retry.`);
      }
    }
    runCombat();
  }, []);

  function triggerAnim(setter, anim, duration = 500) {
    setter(anim);
    setTimeout(() => setter('idle'), duration);
  }

  function animateEvents(events, finalResp) {
    if (!events?.length) { onRunUpdate(finalResp); return; }
    const speedFactor = Math.max(1, (events[events.length - 2]?.time ?? 1) / 15);

    events.forEach(ev => {
      setTimeout(() => {
        if (ev.type === 'player_attack') {
          setEnemyHp(ev.enemy_hp);
          setPlayerHp(ev.player_hp);
          if (ev.dark_mult != null) setDarkMult(ev.dark_mult);
          triggerAnim(setPlayerAnim, 'attack', 450);
          setTimeout(() => triggerAnim(setEnemyAnim, 'hit', 320), 200);
          let atk = `You struck for ${ev.dmg}${ev.crit ? ' (CRIT!)' : ''}${ev.execute ? ' ⚡EXECUTE' : ''}${ev.triple_hit ? ' ×3' : ''}`;
          if (ev.heal > 0) atk += ` +${ev.heal}hp`;
          addLog(atk, 'player', 'attack');
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
          if (ev.summon_heal) sp += ` (${summon?.name}+${ev.summon_heal}hp)`;
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
          let sm = `${summon?.name ?? 'Summon'}: ${ev.dmg} dmg`;
          if (ev.summon_heal) sm += ` +${ev.summon_heal}hp`;
          addLog(sm, 'player', 'summon');
        } else if (ev.type === 'enemy_regen') {
          setEnemyHp(ev.enemy_hp);
          addLog(`${enemy?.name} regenerates ${ev.heal} HP`, 'enemy', 'enemy');
        } else if (ev.type === 'enemy_attack') {
          if (ev.blocked) {
            triggerAnim(setPlayerAnim, 'hit', 320);
            let blk = `${enemy?.name} — blocked!`;
            if (ev.thorns) blk += ` (${ev.thorns} reflected)`;
            if (ev.enemy_hp != null) setEnemyHp(ev.enemy_hp);
            addLog(blk, 'enemy', 'enemy');
          } else {
            triggerAnim(setEnemyAnim, 'attack', 450);
            setTimeout(() => triggerAnim(setPlayerAnim, 'hit', 320), 200);
            setPlayerHp(ev.player_hp);
            if (ev.summon_hp != null) setSummonHp(ev.summon_hp);
            if (ev.summon_died) { setSummonAlive(false); triggerAnim(setSummonAnim, 'dead', 1100); }
            let msg = ev.summon_hp != null && !ev.summon_died
              ? `${enemy?.name} strikes ${summon?.name} for ${ev.summon_dmg}`
              : `${enemy?.name} strikes you for ${ev.dmg}`;
            if (ev.summon_died) msg += ` — ${summon?.name} falls!`;
            if (ev.enemy_lifesteal_heal) msg += ` [+${ev.enemy_lifesteal_heal}hp]`;
            if (ev.enemy_hp != null) setEnemyHp(ev.enemy_hp);
            addLog(msg, 'enemy', 'enemy');
          }
        } else if (ev.type === 'combat_end') {
          setPlayerHp(ev.player_hp);
          setEnemyHp(ev.enemy_hp);
          if (ev.result === 'win') {
            triggerAnim(setEnemyAnim, 'dead', 1200);
            addLog('Victory! The crowd roars!', 'system', 'system');
          } else {
            triggerAnim(setPlayerAnim, 'dead', 1200);
            addLog('You have fallen…', 'system', 'system');
          }
          setPendingNext(finalResp);
        }
      }, (ev.time / speedFactor) * 1000);
    });
  }

  function addLog(msg, side, type) {
    setLog(prev => [...prev.slice(-50), { msg, side, type }]);
    setTimeout(() => {
      if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
    }, 50);
  }

  return (
    <div>
      {/* === ARENA === */}
      <div style={{
        position: 'relative', borderRadius: 8, border: `1px solid ${C.border}`,
        overflow: 'hidden', minHeight: 220, marginBottom: 16,
      }}>
        <ArenaBackground />

        <div style={{
          position: 'relative', zIndex: 2, display: 'flex',
          alignItems: 'flex-end', justifyContent: 'center',
          padding: '10px 16px 10px', gap: 24,
        }}>
          {/* ── Player + Summon side ── */}
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8 }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5 }}>
              <PlayerSprite anim={playerAnim} size={140} />
              <CharacterCard name="Gladiator" hp={playerHp} maxHp={playerMaxHp} alive={playerHp > 0} isPlayer />
            </div>
            {summon && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5 }}>
                <SummonSprite name={summon.name} anim={summonAnim} size={140} />
                <CharacterCard
                  name={summonAlive ? summon.name : `${summon.name} ✝`}
                  hp={summonHp} maxHp={summonMaxHp}
                  alive={summonAlive} isPlayer={false} isBoss={false}
                  _accentColor={C.purple}
                />
              </div>
            )}
          </div>

          {/* ── VS ── */}
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', paddingBottom: 50, padding: '0 16px 50px' }}>
            <div style={{
              color: C.crimson, fontSize: 14, fontWeight: '700',
              fontFamily: "'Cinzel Decorative', serif", letterSpacing: 3,
              textShadow: `0 0 10px rgba(155,26,26,0.5)`,
            }}>
              VS
            </div>
          </div>

          {/* ── Enemy side ── */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5 }}>
            <EnemySprite name={enemy?.name ?? 'Human Soldier'} anim={enemyAnim} size={140} isBoss={enemy?.is_boss} />
            <CharacterCard
              name={enemy?.name ?? 'Enemy'} hp={enemyHp} maxHp={enemyMaxHp}
              alive={enemyHp > 0} isBoss={enemy?.is_boss}
            />
            {/* Dark debuff badge */}
            {darkLevel > 0 && (
              <div style={{
                background: 'rgba(192,132,252,0.12)',
                border: `1px solid rgba(192,132,252,0.4)`,
                borderRadius: 4,
                padding: '2px 8px',
                fontSize: 10,
                fontFamily: 'monospace',
                color: '#C084FC',
                letterSpacing: 0.5,
                whiteSpace: 'nowrap',
              }}>
                Dark {darkLevel}: ×{darkMult.toFixed(2)}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* === COMBAT LOG === */}
      {combatError ? (
        <div style={{ padding: 16, textAlign: 'center' }}>
          <div style={{ color: C.scarlet, fontSize: 13, fontFamily: "'Cinzel', serif", marginBottom: 12 }}>
            {combatError}
          </div>
          <Btn onClick={() => { setCombatError(null); setRetryCount(c => c + 1); }} color={C.bronze}>
            Retry
          </Btn>
        </div>
      ) : loading ? (
        <div style={{ color: C.muted, fontSize: 13, padding: 12, fontFamily: "'Cinzel', serif", textAlign: 'center' }}>
          The battle begins…
        </div>
      ) : (
        <>
          <div style={{
            background: `linear-gradient(180deg, #1A0E06 0%, #130A04 100%)`,
            border: `1px solid ${C.border}`,
            borderRadius: 6, overflow: 'hidden',
          }}>
            {/* Header / toggle */}
            <div
              onClick={() => setLogOpen(o => !o)}
              style={{
                background: `linear-gradient(90deg, #3A1A08, #2A1004)`,
                borderBottom: logOpen ? `1px solid ${C.border}` : 'none',
                padding: '6px 12px', display: 'flex', alignItems: 'center', gap: 8,
                cursor: 'pointer', userSelect: 'none',
              }}
            >
              <span style={{ color: C.gold, fontSize: 10, letterSpacing: 2, textTransform: 'uppercase', fontFamily: "'Cinzel', serif", flex: 1 }}>
                Battle Chronicle
              </span>
              {log.length > 0 && !logOpen && (
                <span style={{ color: getMsgColor(log[log.length-1].type, log[log.length-1].msg), fontSize: 11, fontFamily: "'Cinzel', serif" }}>
                  {log[log.length - 1].msg.slice(0, 40)}{log[log.length - 1].msg.length > 40 ? '…' : ''}
                </span>
              )}
              <span style={{ color: C.muted, fontSize: 11 }}>{logOpen ? '▲' : '▼'}</span>
            </div>

            {logOpen && (
              <div ref={logRef} style={{ padding: '4px 8px', maxHeight: 160, overflowY: 'auto' }}>
                {/* Column headers */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, padding: '2px 4px 4px', borderBottom: `1px solid rgba(92,58,16,0.2)`, marginBottom: 2 }}>
                  <div style={{ textAlign: 'right', paddingRight: 4, color: C.bronze, fontSize: 9, fontFamily: "'Cinzel', serif", letterSpacing: 1, textTransform: 'uppercase' }}>You</div>
                  <div style={{ textAlign: 'left', paddingLeft: 4, color: '#C8B49A', fontSize: 9, fontFamily: "'Cinzel', serif", letterSpacing: 1, textTransform: 'uppercase' }}>Enemy</div>
                </div>
                {log.length === 0 ? (
                  <div style={{ color: C.muted, fontSize: 12, fontFamily: "'Cinzel', serif", padding: '4px 0' }}>Combat beginning…</div>
                ) : (
                  log.map((entry, i) => {
                    const color = getMsgColor(entry.type, entry.msg);
                    if (entry.side === 'system') {
                      return (
                        <div key={i} style={{
                          fontSize: 11, color, padding: '2px 0',
                          borderBottom: `1px solid rgba(92,58,16,0.1)`,
                          fontFamily: "'Cinzel', serif", letterSpacing: 0.3,
                          textAlign: 'center',
                        }}>
                          {entry.msg}
                        </div>
                      );
                    }
                    return (
                      <div key={i} style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: 6,
                        padding: '2px 0',
                        borderBottom: `1px solid rgba(92,58,16,0.1)`,
                        fontSize: 11,
                        fontFamily: "'Cinzel', serif",
                        letterSpacing: 0.3,
                      }}>
                        <div style={{ textAlign: 'right', color: entry.side === 'player' ? color : 'transparent', paddingRight: 4 }}>
                          {entry.side === 'player' ? entry.msg : '\u00A0'}
                        </div>
                        <div style={{ textAlign: 'left', color: entry.side === 'enemy' ? color : 'transparent', paddingLeft: 4 }}>
                          {entry.side === 'enemy' ? entry.msg : '\u00A0'}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}
          </div>

          {pendingNext && (
            <Btn onClick={() => onRunUpdate(pendingNext)} color={C.bronze} style={{ marginTop: 12 }}>
              Continue →
            </Btn>
          )}
        </>
      )}
    </div>
  );
}
