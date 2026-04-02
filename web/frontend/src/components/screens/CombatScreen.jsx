import { useState, useEffect, useRef } from 'react';
import { rpgApi } from '../../api.js';
import { C } from '../../theme.js';
import { HPBar } from '../ui/HPBar.jsx';
import { Btn } from '../ui/Btn.jsx';
import { PlayerSprite } from '../sprites/PlayerSprite.jsx';
import { EnemySprite } from '../sprites/EnemySprite.jsx';
import { SummonSprite } from '../sprites/SummonSprite.jsx';

// Combat log message colors
function getMsgColor(msg) {
  if (msg.includes('CRIT') || msg.includes('EXECUTE')) return C.yellow;
  if (msg.includes('You hit') || msg.includes('Spell:')) return C.sand;
  if (msg.includes('hits for') || msg.includes('Defeated')) return C.scarlet;
  if (msg.includes('Victory') || msg.includes('blocked')) return C.green;
  if (msg.includes('Burn:')) return C.orange;
  if (msg.includes('regenerates') || msg.includes('+') && msg.includes('hp')) return '#4ADE80';
  if (msg.includes('Dark')) return '#C084FC';
  return C.textDim;
}

function ArenaBackground() {
  return (
    <div style={{
      position: 'absolute', inset: 0, overflow: 'hidden', borderRadius: 8,
      pointerEvents: 'none',
    }}>
      {/* Stone wall */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '40%',
        background: 'linear-gradient(180deg, #1A0C04 0%, #261408 60%, transparent 100%)',
      }} />
      {/* Stone brick pattern */}
      {Array.from({ length: 3 }, (_, row) =>
        Array.from({ length: 8 }, (_, col) => (
          <div key={`${row}-${col}`} style={{
            position: 'absolute',
            top: row * 22,
            left: col * 72 + (row % 2 === 0 ? 0 : 36),
            width: 70,
            height: 20,
            borderRadius: 1,
            border: '1px solid rgba(92,58,16,0.3)',
            background: row % 2 === 0
              ? 'rgba(30,18,8,0.4)'
              : 'rgba(38,22,10,0.35)',
          }} />
        ))
      )}
      {/* Torches */}
      {[80, 300].map((x, i) => (
        <div key={i} style={{
          position: 'absolute',
          top: 8,
          left: x,
          width: 24,
          textAlign: 'center',
        }}>
          <div style={{ width: 6, height: 20, background: '#5C3A10', borderRadius: 2, margin: '0 auto' }} />
          <div style={{
            width: 12, height: 16,
            borderRadius: '50% 50% 40% 40%',
            background: 'radial-gradient(ellipse, #E8C84A 0%, #D4722A 60%, transparent 100%)',
            margin: '-8px auto 0',
            animation: `flicker${i} 0.3s alternate infinite`,
          }} />
        </div>
      ))}
      {/* Sand arena floor */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, height: '50%',
        background: 'linear-gradient(0deg, #6B4A1A 0%, #8A6A3A 30%, transparent 100%)',
        opacity: 0.35,
      }} />
      {/* Arena floor lines */}
      <div style={{
        position: 'absolute',
        bottom: '15%',
        left: '10%',
        right: '10%',
        height: 1,
        background: 'rgba(200,169,110,0.15)',
        borderRadius: 1,
      }} />
      {/* Crowd silhouette */}
      <div style={{
        position: 'absolute',
        top: 40,
        left: 0,
        right: 0,
        height: 30,
        display: 'flex',
        gap: 0,
        overflow: 'hidden',
        opacity: 0.3,
      }}>
        {Array.from({ length: 40 }, (_, i) => (
          <div key={i} style={{
            width: 10,
            height: 20 + Math.sin(i * 1.4) * 6,
            borderRadius: '50% 50% 0 0',
            background: '#0F0604',
            marginTop: 10 - Math.sin(i * 0.9) * 4,
            flexShrink: 0,
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
      border: `1px solid ${borderColor}`,
      borderRadius: 6,
      padding: '6px 10px',
      minWidth: 110,
      textAlign: 'center',
      opacity: alive ? 1 : 0.5,
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

function StatChip({ label, value, color }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 4,
      background: 'rgba(15,10,4,0.7)',
      border: `1px solid ${color}44`,
      borderRadius: 3, padding: '2px 6px',
    }}>
      <span style={{ color: C.mutedDim, fontSize: 9, fontFamily: "'Cinzel', serif", letterSpacing: 0.5 }}>{label}</span>
      <span style={{ color, fontSize: 10, fontFamily: 'monospace', fontWeight: '600' }}>{value}</span>
    </div>
  );
}

export function CombatScreen({ run, runId, onRunUpdate, onError }) {
  const enemy   = run.enemy;
  const summon  = run.summon_stats;

  const [log, setLog]               = useState([]);
  const [loading, setLoading]       = useState(false);
  const [playerHp, setPlayerHp]     = useState(run.player.current_hp);
  const [enemyHp, setEnemyHp]       = useState(enemy?.hp ?? 0);
  const [summonHp, setSummonHp]     = useState(summon?.hp ?? 0);
  const [summonAlive, setSummonAlive] = useState(!!summon);
  const [darkStacks, setDarkStacks] = useState({ hitCount: 0, mult: 1.0 });
  const [pendingNext, setPendingNext] = useState(null);
  const [logOpen, setLogOpen] = useState(false);

  // Sprite animation states
  const [playerAnim, setPlayerAnim] = useState('idle');
  const [enemyAnim, setEnemyAnim]   = useState('idle');
  const [summonAnim, setSummonAnim] = useState('idle');

  const logRef    = useRef(null);
  const hasStarted = useRef(false);

  const playerMaxHp = run.player.max_hp;
  const enemyMaxHp  = enemy?.hp ?? 1;
  const summonMaxHp = summon?.hp ?? 1;

  const SUMMON_NAMES = { Imp: 'Imp', Wolf: 'Wolf', Orc: 'Orc', Skeleton: 'Skeleton', Dragon: 'Dragon' };

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
          if (ev.hit_count != null) setDarkStacks({ hitCount: ev.hit_count, mult: ev.dark_mult ?? 1.0 });
          triggerAnim(setPlayerAnim, 'attack', 450);
          setTimeout(() => triggerAnim(setEnemyAnim, 'hit', 320), 200);
          let atk = `You struck for ${ev.dmg}${ev.crit ? ' (CRIT!)' : ''}${ev.execute ? ' ⚡EXECUTE' : ''}${ev.triple_hit ? ' ×3' : ''}`;
          if (ev.heal > 0) atk += ` +${ev.heal}hp`;
          if (ev.dark_mult > 1) atk += ` [Dark ×${ev.dark_mult}]`;
          addLog(atk);
        } else if (ev.type === 'spell') {
          setEnemyHp(ev.enemy_hp);
          setPlayerHp(ev.player_hp);
          if (ev.summon_hp != null) setSummonHp(ev.summon_hp);
          triggerAnim(setPlayerAnim, 'attack', 450);
          setTimeout(() => triggerAnim(setEnemyAnim, 'hit', 320), 200);
          let sp = `Spell — ${ev.dmg} dmg${ev.heal > 0 ? ` +${ev.heal}hp` : ''}`;
          if (ev.dark_mult > 1) sp += ` [Dark ×${ev.dark_mult}]`;
          if (ev.frost) sp += ' [Frost]';
          if (ev.burn_applied) sp += ' [Burn]';
          if (ev.summon_heal) sp += ` (${summon?.name}+${ev.summon_heal}hp)`;
          addLog(sp);
        } else if (ev.type === 'burn_tick') {
          setEnemyHp(ev.enemy_hp);
          triggerAnim(setEnemyAnim, 'hit', 320);
          addLog(`Burn — ${ev.dmg} dmg`);
        } else if (ev.type === 'summon_attack') {
          setEnemyHp(ev.enemy_hp);
          triggerAnim(setSummonAnim, 'attack', 450);
          setTimeout(() => triggerAnim(setEnemyAnim, 'hit', 320), 180);
          addLog(`${summon?.name ?? 'Summon'}${ev.enraged ? ' [Enraged]' : ''}: ${ev.dmg} dmg${ev.dark_mult > 1 ? ` [×${ev.dark_mult}]` : ''}`);
        } else if (ev.type === 'enemy_regen') {
          setEnemyHp(ev.enemy_hp);
          addLog(`${enemy?.name} regenerates ${ev.heal} HP`);
        } else if (ev.type === 'enemy_attack') {
          if (ev.blocked) {
            triggerAnim(setPlayerAnim, 'hit', 320);
            let blk = `${enemy?.name} — blocked!`;
            if (ev.thorns) blk += ` (${ev.thorns} reflected)`;
            if (ev.enemy_hp != null) setEnemyHp(ev.enemy_hp);
            addLog(blk);
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
            addLog(msg);
          }
        } else if (ev.type === 'combat_end') {
          setPlayerHp(ev.player_hp);
          setEnemyHp(ev.enemy_hp);
          if (ev.result === 'win') {
            triggerAnim(setEnemyAnim, 'dead', 1200);
            addLog('Victory! The crowd roars!');
          } else {
            triggerAnim(setPlayerAnim, 'dead', 1200);
            addLog('You have fallen…');
          }
          setPendingNext(finalResp);
        }
      }, (ev.time / speedFactor) * 1000);
    });
  }

  function addLog(msg) {
    setLog(prev => [...prev.slice(-50), msg]);
    setTimeout(() => {
      if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
    }, 50);
  }

  return (
    <div>
      {/* === ARENA === */}
      <div style={{
        position: 'relative',
        borderRadius: 8,
        border: `1px solid ${C.border}`,
        overflow: 'hidden',
        minHeight: 220,
        marginBottom: 16,
      }}>
        <ArenaBackground />

        {/* Character display row */}
        <div style={{
          position: 'relative',
          zIndex: 2,
          display: 'flex',
          alignItems: 'flex-end',
          justifyContent: 'space-between',
          padding: '10px 16px 10px',
          gap: 8,
        }}>
          {/* ── Player + Summon side ── */}
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8 }}>
            {/* Player column */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5 }}>
              <PlayerSprite anim={playerAnim} size={140} />
              <CharacterCard name="Gladiator" hp={playerHp} maxHp={playerMaxHp} alive={playerHp > 0} isPlayer />
            </div>
            {/* Summon column — right next to player */}
            {summon && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5 }}>
                <SummonSprite name={summon.name} anim={summonAnim} size={140} />
                <CharacterCard
                  name={summonAlive ? summon.name : `${summon.name} ✝`}
                  hp={summonHp}
                  maxHp={summonMaxHp}
                  alive={summonAlive}
                  isPlayer={false}
                  isBoss={false}
                  _accentColor={C.purple}
                />
              </div>
            )}
          </div>

          {/* ── VS — always centered ── */}
          <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', paddingBottom: 50 }}>
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
          </div>
        </div>
      </div>

      {/* === COMBAT LOG === */}
      {loading ? (
        <div style={{ color: C.muted, fontSize: 13, padding: 12, fontFamily: "'Cinzel', serif", textAlign: 'center' }}>
          The battle begins…
        </div>
      ) : (
        <>
          {/* Battle log — collapsed by default */}
          <div style={{
            background: `linear-gradient(180deg, #1A0E06 0%, #130A04 100%)`,
            border: `1px solid ${C.border}`,
            borderRadius: 6,
            overflow: 'hidden',
          }}>
            {/* Log header / toggle */}
            <div
              onClick={() => setLogOpen(o => !o)}
              style={{
                background: `linear-gradient(90deg, #3A1A08, #2A1004)`,
                borderBottom: logOpen ? `1px solid ${C.border}` : 'none',
                padding: '6px 12px',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                cursor: 'pointer',
                userSelect: 'none',
              }}
            >
              <span style={{ color: C.gold, fontSize: 10, letterSpacing: 2, textTransform: 'uppercase', fontFamily: "'Cinzel', serif", flex: 1 }}>
                Battle Chronicle
              </span>
              {log.length > 0 && !logOpen && (
                <span style={{ color: C.muted, fontSize: 11, fontFamily: "'Cinzel', serif" }}>
                  {log[log.length - 1].slice(0, 40)}{log[log.length - 1].length > 40 ? '…' : ''}
                </span>
              )}
              <span style={{ color: C.muted, fontSize: 11 }}>{logOpen ? '▲' : '▼'}</span>
            </div>
            {logOpen && (
              <div ref={logRef} style={{ padding: 8, maxHeight: 130, overflowY: 'auto' }}>
                {log.length === 0 ? (
                  <div style={{ color: C.muted, fontSize: 12, fontFamily: "'Cinzel', serif" }}>Combat beginning…</div>
                ) : (
                  log.map((l, i) => (
                    <div key={i} style={{
                      fontSize: 12,
                      color: getMsgColor(l),
                      padding: '2px 0',
                      borderBottom: `1px solid rgba(92,58,16,0.1)`,
                      fontFamily: "'Cinzel', serif",
                      letterSpacing: 0.3,
                    }}>
                      {l}
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {pendingNext && (
            <Btn
              onClick={() => onRunUpdate(pendingNext)}
              color={C.bronze}
              style={{ marginTop: 12 }}
            >
              Continue →
            </Btn>
          )}
        </>
      )}
    </div>
  );
}
