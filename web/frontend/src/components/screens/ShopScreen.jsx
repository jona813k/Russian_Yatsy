import { useState } from 'react';
import { rpgApi } from '../../api.js';
import { C } from '../../theme.js';

function ItemRow({ item, alreadyOwned, canBuyGold, canFree, loading, onBuy, onFree }) {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '8px 10px',
        background: alreadyOwned
          ? 'rgba(74,154,90,0.08)'
          : hovered ? 'rgba(205,127,50,0.08)' : 'rgba(10,6,2,0.5)',
        border: `1px solid ${alreadyOwned ? C.green + '55' : hovered ? C.bronze : C.border + '88'}`,
        borderRadius: 5,
        transition: 'all 0.12s',
      }}
    >
      {/* Name + desc */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <span style={{
          color: alreadyOwned ? C.green : C.sand,
          fontWeight: '600',
          fontSize: 12,
          fontFamily: "'Cinzel', serif",
          letterSpacing: 0.5,
        }}>
          {item.name}
        </span>
        <span style={{
          color: C.muted,
          fontSize: 11,
          fontFamily: "'Cinzel', serif",
          marginLeft: 8,
        }}>
          — {item.desc}
        </span>
      </div>

      {/* Cost badge */}
      <span style={{
        flexShrink: 0,
        color: C.gold,
        fontWeight: '700',
        fontSize: 11,
        fontFamily: 'monospace',
        background: 'rgba(212,175,55,0.1)',
        border: `1px solid ${C.gold}44`,
        borderRadius: 3,
        padding: '2px 6px',
      }}>
        {item.cost}g
      </span>

      {/* Action */}
      {alreadyOwned ? (
        <span style={{ flexShrink: 0, color: C.green, fontSize: 11, fontFamily: "'Cinzel', serif" }}>⚔ owned</span>
      ) : (
        <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
          <button
            onClick={onBuy}
            disabled={!canBuyGold || loading}
            style={{
              background: canBuyGold ? (hovered ? C.crimson : 'rgba(155,26,26,0.5)') : 'rgba(60,40,30,0.4)',
              color: canBuyGold ? C.sand : C.muted,
              border: `1px solid ${canBuyGold ? C.crimson : C.borderDim}`,
              borderRadius: 4,
              padding: '3px 10px',
              fontSize: 11,
              fontFamily: "'Cinzel', serif",
              fontWeight: '600',
              letterSpacing: 1,
              textTransform: 'uppercase',
              cursor: canBuyGold && !loading ? 'pointer' : 'default',
              transition: 'all 0.12s',
            }}
          >
            Buy
          </button>
          {canFree && (
            <button
              onClick={onFree}
              disabled={loading}
              style={{
                background: 'rgba(74,154,90,0.3)',
                color: C.green,
                border: `1px solid ${C.green}`,
                borderRadius: 4,
                padding: '3px 10px',
                fontSize: 11,
                fontFamily: "'Cinzel', serif",
                fontWeight: '600',
                letterSpacing: 1,
                textTransform: 'uppercase',
                cursor: loading ? 'default' : 'pointer',
                transition: 'all 0.12s',
              }}
            >
              Free
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export function ShopScreen({ run, runId, onRunUpdate, onError }) {
  const [loading, setLoading] = useState(false);
  const items = run.shop_items || [];
  const owned = (run.owned_items || []).map(i => i.id);
  const freepicks = run.player.free_items ?? 0;
  const isBossShop = run.phase === 'pre_boss_shop';

  async function buy(itemId, useFree = false) {
    setLoading(true);
    try {
      const resp = await rpgApi.buyItem(runId, itemId, useFree);
      onRunUpdate(resp);
    } catch (e) { if (onError) onError(e); else console.error(e); }
    setLoading(false);
  }

  async function reroll() {
    setLoading(true);
    try {
      const resp = await rpgApi.rerollShop(runId);
      onRunUpdate(resp);
    } catch (e) { if (onError) onError(e); else console.error(e); }
    setLoading(false);
  }

  async function close() {
    setLoading(true);
    try {
      const resp = await rpgApi.closeShop(runId);
      onRunUpdate(resp);
    } catch (e) { if (onError) onError(e); else console.error(e); }
    setLoading(false);
  }

  return (
    <div style={{
      background: `linear-gradient(180deg, #1E1208, #130A04)`,
      border: `1px solid ${C.border}`,
      borderRadius: 6,
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        background: `linear-gradient(90deg, #3A2808, #281A04)`,
        borderBottom: `1px solid ${C.border}55`,
        padding: '8px 12px',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}>
        <span style={{ color: C.gold, fontSize: 14 }}>⚖</span>
        <span style={{
          color: C.gold,
          fontWeight: '700',
          fontSize: 13,
          fontFamily: "'Cinzel', serif",
          letterSpacing: 1,
        }}>
          The Market
        </span>
        {/* Gold */}
        <span style={{
          color: C.gold,
          fontWeight: '700',
          fontSize: 13,
          fontFamily: 'monospace',
          background: 'rgba(212,175,55,0.1)',
          border: `1px solid ${C.gold}44`,
          borderRadius: 3,
          padding: '1px 7px',
          marginLeft: 4,
        }}>
          {run.player.gold}g
        </span>
        {freepicks > 0 && (
          <span style={{
            color: C.green,
            fontWeight: '700',
            fontSize: 11,
            fontFamily: 'monospace',
            background: 'rgba(74,154,90,0.15)',
            border: `1px solid ${C.green}44`,
            borderRadius: 3,
            padding: '1px 6px',
          }}>
            {freepicks} free
          </span>
        )}
        {isBossShop && (
          <span style={{ marginLeft: 'auto', color: C.scarlet, fontSize: 11, fontFamily: "'Cinzel', serif", letterSpacing: 1 }}>
            ⚠ Champion ahead
          </span>
        )}
      </div>

      {/* Item rows */}
      <div style={{ padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 5 }}>
        {items.map(item => {
          const alreadyOwned = owned.includes(item.id);
          const isGoldOnly = item.id === 'heal_potion' || item.id === 'gladiator_key';
          const canBuyGold = !alreadyOwned && run.player.gold >= item.cost;
          const canFree = !alreadyOwned && !isGoldOnly && freepicks > 0;
          return (
            <ItemRow
              key={item.id}
              item={item}
              alreadyOwned={alreadyOwned}
              canBuyGold={canBuyGold}
              canFree={canFree}
              loading={loading}
              onBuy={() => buy(item.id, false)}
              onFree={() => buy(item.id, true)}
            />
          );
        })}
      </div>

      {/* Footer actions */}
      <div style={{
        borderTop: `1px solid ${C.borderDim}`,
        padding: '8px 10px',
        display: 'flex',
        gap: 8,
        alignItems: 'center',
      }}>
        <button
          onClick={close}
          disabled={loading}
          style={{
            background: C.crimson,
            color: C.sand,
            border: `1px solid ${C.scarlet}`,
            borderRadius: 4,
            padding: '5px 14px',
            fontSize: 11,
            fontFamily: "'Cinzel', serif",
            fontWeight: '600',
            letterSpacing: 1,
            textTransform: 'uppercase',
            cursor: loading ? 'default' : 'pointer',
            transition: 'all 0.12s',
          }}
        >
          {isBossShop ? 'Face the Champion' : `Advance →`}
        </button>
        <button
          onClick={reroll}
          disabled={loading || run.player.gold < 30}
          style={{
            background: 'transparent',
            color: run.player.gold >= 30 ? C.muted : C.mutedDim,
            border: `1px solid ${run.player.gold >= 30 ? C.borderDim : C.borderDim + '66'}`,
            borderRadius: 4,
            padding: '5px 12px',
            fontSize: 11,
            fontFamily: "'Cinzel', serif",
            letterSpacing: 1,
            cursor: loading || run.player.gold < 30 ? 'default' : 'pointer',
            transition: 'all 0.12s',
          }}
        >
          Refresh (30g)
        </button>
      </div>
    </div>
  );
}
