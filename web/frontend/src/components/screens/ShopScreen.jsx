import { useState } from 'react';
import { rpgApi } from '../../api.js';
import { C } from '../../theme.js';
import { Btn } from '../ui/Btn.jsx';

// Canvas awning top for the market
function MarketAwning() {
  return (
    <div style={{ position: 'relative', height: 40, overflow: 'hidden', borderRadius: '6px 6px 0 0' }}>
      {/* Awning stripes */}
      <div style={{
        position: 'absolute', inset: 0,
        background: `repeating-linear-gradient(
          90deg,
          #3A1A08 0px, #3A1A08 30px,
          #2A1004 30px, #2A1004 60px
        )`,
      }} />
      {/* Awning scalloped edge */}
      <svg style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: 20 }} viewBox="0 0 400 20" preserveAspectRatio="none">
        {Array.from({ length: 14 }, (_, i) => (
          <path key={i}
            d={`M ${i * 30} 0 Q ${i * 30 + 15} 20 ${i * 30 + 30} 0`}
            fill="#1E0C04"
          />
        ))}
      </svg>
      {/* Merchant sign */}
      <div style={{
        position: 'absolute',
        left: '50%',
        transform: 'translateX(-50%)',
        top: 6,
        background: '#1E0C04',
        border: `1px solid ${C.gold}`,
        borderRadius: 3,
        padding: '2px 14px',
        fontSize: 10,
        color: C.gold,
        letterSpacing: 3,
        textTransform: 'uppercase',
        fontFamily: "'Cinzel', serif",
        whiteSpace: 'nowrap',
      }}>
        The Market
      </div>
    </div>
  );
}

function ItemCard({ item, alreadyOwned, canBuyGold, canFree, loading, onBuy, onFree }) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: alreadyOwned
          ? `linear-gradient(135deg, rgba(26,58,26,0.9), rgba(20,46,20,0.9))`
          : hovered
          ? `linear-gradient(135deg, rgba(38,22,10,0.95), rgba(30,16,6,0.95))`
          : `linear-gradient(135deg, rgba(30,18,8,0.9), rgba(22,12,4,0.9))`,
        border: `1px solid ${alreadyOwned ? C.green + '88' : hovered ? C.bronze : C.border}`,
        borderRadius: 6,
        padding: '12px 14px',
        marginBottom: 8,
        transition: 'all 0.15s',
        boxShadow: alreadyOwned ? `inset 0 0 12px rgba(74,154,90,0.08)` : 'none',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
        <span style={{
          color: alreadyOwned ? C.green : C.sand,
          fontWeight: '600',
          fontSize: 13,
          fontFamily: "'Cinzel', serif",
          letterSpacing: 0.5,
        }}>
          {item.name}
        </span>
        <span style={{
          color: C.gold,
          fontWeight: '700',
          fontSize: 12,
          fontFamily: 'monospace',
          background: 'rgba(212,175,55,0.1)',
          border: `1px solid ${C.gold}44`,
          borderRadius: 3,
          padding: '1px 6px',
        }}>
          {item.cost}g
        </span>
      </div>
      <div style={{
        color: C.muted,
        fontSize: 11,
        marginBottom: alreadyOwned ? 0 : 10,
        fontFamily: "'Cinzel', serif",
        lineHeight: 1.5,
        letterSpacing: 0.3,
      }}>
        {item.desc}
      </div>
      {alreadyOwned ? (
        <span style={{ color: C.green, fontSize: 11, fontFamily: "'Cinzel', serif" }}>⚔ Equipped</span>
      ) : (
        <div style={{ display: 'flex', gap: 8 }}>
          <Btn
            onClick={onBuy}
            disabled={!canBuyGold || loading}
            color={canBuyGold ? C.crimson : C.stone}
            style={{ fontSize: 11, padding: '5px 14px' }}
          >
            Buy
          </Btn>
          {canFree && (
            <Btn
              onClick={onFree}
              disabled={loading}
              color={C.green}
              style={{ fontSize: 11, padding: '5px 14px' }}
            >
              Free
            </Btn>
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

  const isBossShop = run.phase === 'pre_boss_shop';

  return (
    <div style={{ maxWidth: 480 }}>
      {/* Market stall */}
      <div style={{
        border: `1px solid ${C.border}`,
        borderRadius: 8,
        overflow: 'hidden',
        background: `linear-gradient(180deg, #1E1208, #130A04)`,
        boxShadow: '0 8px 30px rgba(0,0,0,0.5)',
      }}>
        <MarketAwning />

        <div style={{ padding: '14px 16px' }}>
          {/* Gold & free picks bar */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            marginBottom: 16,
            padding: '8px 12px',
            background: 'rgba(15,10,4,0.6)',
            border: `1px solid ${C.borderDim}`,
            borderRadius: 5,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 14 }}>⚖</span>
              <span style={{ color: C.muted, fontSize: 11, fontFamily: "'Cinzel', serif" }}>Gold:</span>
              <span style={{
                color: C.gold,
                fontWeight: '700',
                fontSize: 15,
                fontFamily: 'monospace',
                textShadow: `0 0 8px ${C.gold}44`,
              }}>
                {run.player.gold}
              </span>
            </div>
            {freepicks > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ color: C.muted, fontSize: 11, fontFamily: "'Cinzel', serif" }}>Free picks:</span>
                <span style={{
                  color: C.green,
                  fontWeight: '700',
                  fontSize: 14,
                  fontFamily: 'monospace',
                  background: 'rgba(74,154,90,0.15)',
                  border: `1px solid ${C.green}44`,
                  borderRadius: 3,
                  padding: '1px 6px',
                }}>
                  {freepicks}
                </span>
              </div>
            )}
            {isBossShop && (
              <span style={{
                marginLeft: 'auto',
                color: C.scarlet,
                fontSize: 11,
                fontFamily: "'Cinzel', serif",
                letterSpacing: 1,
              }}>
                ⚠ Champion ahead
              </span>
            )}
          </div>

          {/* Items */}
          {items.map(item => {
            const alreadyOwned = owned.includes(item.id);
            const isPotion = item.id === 'heal_potion';
            const canBuyGold = !alreadyOwned && run.player.gold >= item.cost;
            const canFree = !alreadyOwned && !isPotion && freepicks > 0;
            return (
              <ItemCard
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

          {/* Owned items summary */}
          {run.owned_items?.length > 0 && (
            <div style={{
              marginTop: 12,
              borderTop: `1px solid ${C.borderDim}`,
              paddingTop: 10,
            }}>
              <div style={{ color: C.muted, fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', fontFamily: "'Cinzel', serif", marginBottom: 5 }}>
                Your Arsenal
              </div>
              {run.owned_items.map(item => (
                <div key={item.id} style={{
                  fontSize: 11,
                  color: C.green,
                  fontFamily: "'Cinzel', serif",
                  padding: '1px 0',
                }}>
                  ⚔ {item.name}
                </div>
              ))}
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', gap: 10, marginTop: 16, alignItems: 'center' }}>
            <Btn onClick={close} disabled={loading} color={C.crimson}>
              {isBossShop ? 'Face the Champion' : `Advance to Level ${run.level + 1}`}
            </Btn>
            <Btn
              onClick={reroll}
              disabled={loading || run.player.gold < 30}
              color={C.stone}
              style={{ fontSize: 12 }}
            >
              Refresh (30g)
            </Btn>
          </div>
        </div>
      </div>
    </div>
  );
}
