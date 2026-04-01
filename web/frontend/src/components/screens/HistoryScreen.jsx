import { useState, useEffect } from 'react';
import { rpgApi } from '../../api.js';
import { C } from '../../theme.js';
import { Btn } from '../ui/Btn.jsx';

const COLLECTION_LABELS = {
  1:'Spd',2:'Dmg',3:'Crit',4:'Armor',5:'HP',
  6:'Res',7:'Gold',8:'Summon',9:'Spell',10:'Block',11:'LS',12:'Dark',
};

const FORGE_LABELS = {
  add_d12:'d12', add_d3:'d3', remove_die:'-die',
  loaded_high:'Load↑', free_reroll:'Reroll', risky_die:'Risky',
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
      border: `1px solid ${win ? C.green + '88' : C.crimson + '88'}`,
      borderRadius: 6,
      marginBottom: 8,
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div
        onClick={() => setOpen(o => !o)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '9px 14px',
          cursor: 'pointer',
          background: win
            ? `linear-gradient(90deg, rgba(26,58,26,0.9), rgba(15,26,15,0.9))`
            : `linear-gradient(90deg, rgba(42,13,13,0.9), rgba(26,8,8,0.9))`,
          userSelect: 'none',
        }}
      >
        <span style={{ fontSize: 16 }}>{win ? '⚔' : '✝'}</span>
        <span style={{
          color: win ? C.green : C.scarlet,
          fontWeight: '700',
          fontSize: 12,
          fontFamily: "'Cinzel', serif",
          minWidth: 36,
          letterSpacing: 1,
        }}>
          {win ? 'WIN' : 'LOSS'}
        </span>
        <span style={{ color: C.muted, fontSize: 11, fontFamily: "'Cinzel', serif" }}>
          {win ? 'All 3 levels conquered' : `Fell at Level ${entry.level_reached}, Fight ${entry.fight_reached}`}
        </span>
        <span style={{ color: C.mutedDim, fontSize: 10, marginLeft: 'auto', fontFamily: 'monospace' }}>
          {date}
        </span>
        <span style={{ color: C.muted, fontSize: 10 }}>{open ? '▲' : '▼'}</span>
      </div>

      {/* Details */}
      {open && (
        <div style={{
          padding: '12px 14px',
          background: `linear-gradient(180deg, #1E1208, #130A04)`,
          borderTop: `1px solid ${C.borderDim}`,
        }}>
          {/* Stats grid */}
          <div style={{ marginBottom: 12 }}>
            <div style={{ color: C.muted, fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', fontFamily: "'Cinzel', serif", marginBottom: 6 }}>Final Stats</div>
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
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, padding: '1px 0' }}>
                  <span style={{ color: C.muted, fontFamily: "'Cinzel', serif" }}>{label}</span>
                  <span style={{ color: C.textDim, fontWeight: '600', fontFamily: 'monospace' }}>{val}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Forge path */}
          {entry.forges?.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ color: C.muted, fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', fontFamily: "'Cinzel', serif", marginBottom: 5 }}>Forge Path</div>
              <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                {entry.forges.map((f, i) => (
                  <span key={i} style={{
                    background: 'rgba(122,58,154,0.2)',
                    border: `1px solid ${C.purple}66`,
                    borderRadius: 3,
                    padding: '2px 7px',
                    fontSize: 11,
                    color: C.purple,
                    fontFamily: 'monospace',
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
              <div style={{ color: C.muted, fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', fontFamily: "'Cinzel', serif", marginBottom: 5 }}>Items</div>
              <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                {entry.item_names.map((name, i) => (
                  <span key={i} style={{
                    background: 'rgba(212,175,55,0.1)',
                    border: `1px solid ${C.gold}55`,
                    borderRadius: 3,
                    padding: '2px 7px',
                    fontSize: 11,
                    color: C.gold,
                    fontFamily: "'Cinzel', serif",
                  }}>
                    {name}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Collections bar chart */}
          <div>
            <div style={{ color: C.muted, fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', fontFamily: "'Cinzel', serif", marginBottom: 6 }}>Upgrade Collections</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 4 }}>
              {Array.from({ length: 12 }, (_, i) => {
                const n = i + 1;
                const count = Number(cols[n] || 0);
                const pct = (count / maxCols) * 100;
                return (
                  <div key={n} style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 8, color: C.muted, fontFamily: "'Cinzel', serif" }}>{COLLECTION_LABELS[n]}</div>
                    <div style={{ height: 36, background: '#1A0A04', borderRadius: 3, display: 'flex', alignItems: 'flex-end', margin: '2px 0' }}>
                      <div style={{
                        width: '100%',
                        height: `${pct}%`,
                        background: count > 0 ? `linear-gradient(180deg, ${C.bronze}, ${C.crimson})` : '#2A1208',
                        borderRadius: 3,
                        transition: 'height .3s',
                        minHeight: count > 0 ? 2 : 0,
                      }} />
                    </div>
                    <div style={{ fontSize: 9, color: count > 0 ? C.textDim : C.mutedDim, fontFamily: 'monospace' }}>{count}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function HistoryScreen({ onBack }) {
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
      minHeight: '100vh',
      background: `radial-gradient(ellipse at 50% 20%, #1E0C04 0%, #0F0A04 60%)`,
      fontFamily: "'Cinzel', serif",
      color: C.text,
      padding: 20,
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20,
        paddingBottom: 12,
        borderBottom: `1px solid ${C.border}`,
      }}>
        <h2 style={{
          margin: 0,
          color: C.gold,
          fontSize: 20,
          fontFamily: "'Cinzel Decorative', serif",
          letterSpacing: 2,
        }}>
          Arena Chronicle
        </h2>
        <div style={{ display: 'flex', gap: 8 }}>
          {total > 0 && (
            <Btn onClick={clearAll} disabled={clearing} color={C.crimson}
              style={{ fontSize: 11, padding: '6px 12px' }}>
              Clear
            </Btn>
          )}
          <Btn onClick={onBack} color={C.stone} style={{ fontSize: 11, padding: '6px 12px' }}>
            ← Back
          </Btn>
        </div>
      </div>

      {/* Stats summary */}
      {history !== null && history.length > 0 && (
        <div style={{
          display: 'flex',
          gap: 24,
          marginBottom: 16,
          padding: '10px 16px',
          background: `linear-gradient(90deg, #1E1208, #1A1004)`,
          border: `1px solid ${C.border}`,
          borderRadius: 6,
        }}>
          {[
            ['Runs', total, C.textDim],
            ['Victories', wins, C.green],
            ['Win Rate', `${total > 0 ? Math.round(wins / total * 100) : 0}%`, C.gold],
          ].map(([label, val, color]) => (
            <div key={label}>
              <span style={{ color: C.muted, fontSize: 11 }}>{label}: </span>
              <span style={{ color, fontWeight: '700', fontSize: 12, fontFamily: 'monospace' }}>{val}</span>
            </div>
          ))}
        </div>
      )}

      {history === null ? (
        <div style={{ color: C.muted, fontFamily: "'Cinzel', serif" }}>Loading…</div>
      ) : history.length === 0 ? (
        <div style={{ color: C.muted, textAlign: 'center', marginTop: 60, fontFamily: "'Cinzel', serif", fontSize: 13 }}>
          No battles recorded yet. Enter the arena to begin your legend.
        </div>
      ) : (
        <div style={{ maxWidth: 660 }}>
          {history.map(entry => (
            <HistoryEntry key={entry.run_id + entry.timestamp} entry={entry} />
          ))}
        </div>
      )}
    </div>
  );
}
