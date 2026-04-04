import { useState } from 'react';
import { C } from '../../theme.js';
import { Btn } from './Btn.jsx';
import { debugApi } from '../../api.js';

const LOG_LINE_MAX = 300;
const LOG_SKIP_PATTERNS = [
  '[UpgradePhase] render',   // full state dump on every render
  '[handleCollect] response', // full run state in response log
  '[handleCollect] timeout fired', // same, on timeout
];

function filterLogs(logs) {
  return logs
    .filter(line => !LOG_SKIP_PATTERNS.some(p => line.includes(p)))
    .map(line => line.length > LOG_LINE_MAX ? line.slice(0, LOG_LINE_MAX) + '…' : line);
}

function buildRunState(run, runId) {
  if (!run || !runId) return {};
  const p = run.player ?? {};
  return {
    run_id:       runId,
    name:         run.name,
    phase:        run.phase,
    level:        run.level,
    fight_index:  run.fight_index,
    is_boss:      run.is_boss,
    enemy:        run.enemy ? { name: run.enemy.name, hp: run.enemy.hp, is_boss: run.enemy.is_boss } : null,
    player: {
      current_hp:    p.current_hp,
      max_hp:        p.max_hp,
      attack_dmg:    p.attack_dmg,
      attack_speed:  p.attack_speed,
      crit_chance:   p.crit_chance,
      armor:         p.armor,
      block_chance:  p.block_chance,
      lifesteal:     p.lifesteal,
      dark_level:    p.dark_level,
      summon_level:  p.summon_level,
      spell_level:   p.spell_level,
      gold:          p.gold,
      item_slots:    p.item_slots,
    },
    owned_items:   (run.owned_items ?? []).map(i => i.id),
    stat_targets:  run.stat_targets ?? {},
    stat_removed:  run.stat_removed ?? [],
    forge_history: run.forge_history ?? [],
    yatzy: run.yatzy ? {
      dice:           run.yatzy.dice,
      turns_remaining: run.yatzy.turns_remaining,
      selected_number: run.yatzy.selected_number,
      legal_actions:   run.yatzy.legal_actions,
    } : null,
  };
}

export function BugReportModal({ run, runId, onClose }) {
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState('idle'); // idle | sending | sent | error

  async function handleSend() {
    if (!description.trim()) return;
    setStatus('sending');
    try {
      await debugApi.submitBugReport({
        description:  description.trim(),
        run_state:    buildRunState(run, runId),
        console_logs: filterLogs(window.__consoleLogs ?? []),
        browser:      navigator.userAgent,
        url:          window.location.href,
      });
      setStatus('sent');
    } catch (e) {
      console.error('[BugReportModal] submit failed', e);
      setStatus('error');
    }
  }

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'rgba(0,0,0,0.75)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 20,
      }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div style={{
        background: `linear-gradient(180deg, #1E1208 0%, #0F0A04 100%)`,
        border: `1px solid ${C.border}`,
        borderRadius: 8,
        padding: '20px 24px',
        width: '100%',
        maxWidth: 480,
        display: 'flex',
        flexDirection: 'column',
        gap: 14,
        boxShadow: '0 20px 60px rgba(0,0,0,0.9)',
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ color: C.gold, fontSize: 14, fontFamily: "'Cinzel', serif", letterSpacing: 1 }}>
            Report a Bug
          </span>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: C.muted, fontSize: 18, cursor: 'pointer', lineHeight: 1 }}
          >
            ✕
          </button>
        </div>

        {status === 'sent' ? (
          <>
            <p style={{ color: C.green, fontSize: 13, fontFamily: "'Cinzel', serif", margin: 0, textAlign: 'center', padding: '16px 0' }}>
              Report sent — thank you!
            </p>
            <Btn onClick={onClose} color={C.bronze} style={{ fontSize: 11, padding: '7px 16px', alignSelf: 'flex-end' }}>
              Close
            </Btn>
          </>
        ) : (
          <>
            <p style={{ color: C.textDim, fontSize: 12, fontFamily: "'Cinzel', serif", margin: 0, lineHeight: 1.6 }}>
              Describe what happened. The current game state and console logs will be attached automatically.
            </p>

            <textarea
              autoFocus
              placeholder="e.g. Game got stuck after collecting armor, the collect button stopped responding"
              value={description}
              onChange={e => setDescription(e.target.value)}
              style={{
                background: '#080604',
                color: C.text,
                border: `1px solid ${status === 'error' ? C.scarlet : C.borderDim}`,
                borderRadius: 4,
                padding: '10px 12px',
                fontFamily: "'Cinzel', serif",
                fontSize: 12,
                lineHeight: 1.6,
                resize: 'vertical',
                minHeight: 100,
                outline: 'none',
              }}
            />

            {status === 'error' && (
              <p style={{ color: C.scarlet, fontSize: 11, fontFamily: "'Cinzel', serif", margin: 0 }}>
                Failed to send — are you on the live site?
              </p>
            )}

            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <Btn onClick={onClose} color={C.stone} style={{ fontSize: 11, padding: '7px 16px' }}>
                Cancel
              </Btn>
              <Btn
                onClick={handleSend}
                disabled={!description.trim() || status === 'sending'}
                color={C.crimson}
                style={{ fontSize: 11, padding: '7px 16px' }}
              >
                {status === 'sending' ? 'Sending…' : 'Send Report'}
              </Btn>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
