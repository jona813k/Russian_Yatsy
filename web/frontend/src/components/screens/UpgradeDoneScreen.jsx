import { useState } from 'react';
import { rpgApi } from '../../api.js';
import { C } from '../../theme.js';
import { Btn } from '../ui/Btn.jsx';

const NUMBER_NAMES = {
  1:'Ones',2:'Twos',3:'Threes',4:'Fours',5:'Fives',6:'Sixes',
  7:'Sevens',8:'Eights',9:'Nines',10:'Tens',11:'Elevens',12:'Twelves',
};

export function UpgradeDoneScreen({ run, runId, onRunUpdate, onError }) {
  const [loading, setLoading] = useState(false);
  const upgrades = run.last_upgrades || [];

  async function proceed() {
    setLoading(true);
    try {
      const resp = await rpgApi.upgradeFinish(runId);
      onRunUpdate(resp);
    } catch (e) { if (onError) onError(e); else console.error(e); }
    setLoading(false);
  }

  return (
    <div style={{ maxWidth: 420 }}>
      <div style={{
        background: `linear-gradient(180deg, #1E1208, #130A04)`,
        border: `1px solid ${C.bronze}`,
        borderRadius: 8,
        overflow: 'hidden',
        boxShadow: '0 8px 30px rgba(0,0,0,0.5)',
      }}>
        {/* Header */}
        <div style={{
          background: `linear-gradient(90deg, #3A2008, #2A1404)`,
          borderBottom: `1px solid ${C.bronze}66`,
          padding: '14px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
        }}>
          <span style={{ fontSize: 22 }}>⚔</span>
          <div>
            <div style={{
              color: C.gold,
              fontWeight: '700',
              fontSize: 16,
              fontFamily: "'Cinzel', serif",
              letterSpacing: 1,
            }}>
              Training Complete
            </div>
            <div style={{ color: C.muted, fontSize: 11, fontFamily: "'Cinzel', serif" }}>
              Your gladiator has grown stronger
            </div>
          </div>
        </div>

        {/* Upgrades list */}
        <div style={{ padding: '14px 18px' }}>
          {upgrades.length === 0 ? (
            <div style={{ color: C.muted, marginBottom: 16, fontSize: 12, fontFamily: "'Cinzel', serif" }}>
              No upgrades this phase.
            </div>
          ) : (
            <div style={{ marginBottom: 16 }}>
              {upgrades.map((u, i) => (
                <div key={i} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '7px 0',
                  borderBottom: `1px solid ${C.borderDim}`,
                }}>
                  <span style={{
                    color: C.muted,
                    fontSize: 12,
                    fontFamily: "'Cinzel', serif",
                  }}>
                    {NUMBER_NAMES[u.number] || u.number}
                  </span>
                  <span style={{
                    color: u.threshold_bonus ? C.yellow : C.green,
                    fontWeight: '600',
                    fontSize: 12,
                    fontFamily: 'monospace',
                    background: u.threshold_bonus
                      ? 'rgba(232,200,74,0.1)'
                      : 'rgba(74,154,90,0.1)',
                    border: `1px solid ${u.threshold_bonus ? C.yellow + '44' : C.green + '44'}`,
                    borderRadius: 3,
                    padding: '1px 6px',
                  }}>
                    {u.threshold_bonus ? '★ ' : '+'}{u.desc}
                  </span>
                </div>
              ))}
            </div>
          )}

          <Btn
            onClick={proceed}
            disabled={loading}
            color={C.crimson}
            style={{ fontSize: 13 }}
          >
            {loading ? 'Preparing…' : `Enter the Arena${run.is_boss ? ' — Champion' : ''}`}
          </Btn>
        </div>
      </div>
    </div>
  );
}
