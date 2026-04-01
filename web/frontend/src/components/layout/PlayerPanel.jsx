import { C } from '../../theme.js';
import { HPBar } from '../ui/HPBar.jsx';

const STAT_LABELS = {
  attack_speed: 'Atk Speed', attack_dmg: 'Atk Dmg', crit_chance: 'Crit',
  armor: 'Armor', max_hp: 'Max HP', item_slots: 'Item Slots', free_items: 'Free Picks', gold: 'Gold',
  summon_level: 'Summon Lvl', spell_level: 'Spell Lvl', block_chance: 'Block',
  lifesteal: 'Lifesteal', dark_level: 'Dark Lvl', current_hp: 'HP',
};

function fmt(attr, val) {
  if (attr === 'attack_speed') return `${val.toFixed(2)}s`;
  if (['crit_chance', 'armor', 'block_chance', 'lifesteal'].includes(attr))
    return `${(val * 100).toFixed(1)}%`;
  if (attr === 'current_hp' || attr === 'max_hp') return Math.round(val);
  return typeof val === 'number' ? (Number.isInteger(val) ? val : val.toFixed(2)) : val;
}

function StatRow({ label, value, highlight }) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '3px 0',
      borderBottom: `1px solid ${C.borderDim}`,
    }}>
      <span style={{ color: C.muted, fontSize: 11, fontFamily: "'Cinzel', serif" }}>{label}</span>
      <span style={{
        color: highlight ? C.yellow : C.textDim,
        fontWeight: '600',
        fontSize: 11,
        fontFamily: 'monospace',
      }}>
        {value}
      </span>
    </div>
  );
}

export function PlayerPanel({ player, ownedItems }) {
  const stats = [
    ['current_hp',   `${Math.round(player.current_hp)} / ${player.max_hp}`],
    ['attack_dmg',   fmt('attack_dmg', player.attack_dmg)],
    ['attack_speed', fmt('attack_speed', player.attack_speed)],
    ['crit_chance',  fmt('crit_chance', player.crit_chance)],
    ['armor',        fmt('armor', player.armor)],
    ['block_chance', fmt('block_chance', player.block_chance)],
    ['lifesteal',    fmt('lifesteal', player.lifesteal)],
    player.dark_level > 0 && ['dark_level', player.dark_level],
    player.summon_level > 0 && ['summon_level', player.summon_level],
    player.spell_level > 0 && ['spell_level', player.spell_level],
    ['gold',         player.gold],
    ['item_slots',   player.item_slots],
    player.free_items > 0 && ['free_items', player.free_items],
  ].filter(Boolean);

  return (
    <div style={{
      minWidth: 160,
      maxWidth: 180,
      background: `linear-gradient(180deg, #1E1208, #180C04)`,
      border: `1px solid ${C.border}`,
      borderRadius: 6,
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        background: `linear-gradient(90deg, #3A1A08, #2A1004)`,
        borderBottom: `1px solid ${C.border}`,
        padding: '8px 12px',
        textAlign: 'center',
      }}>
        <div style={{
          color: C.gold,
          fontWeight: '700',
          fontSize: 12,
          letterSpacing: 2,
          textTransform: 'uppercase',
          fontFamily: "'Cinzel', serif",
        }}>
          Gladiator
        </div>
      </div>

      {/* HP section */}
      <div style={{ padding: '10px 12px 8px', borderBottom: `1px solid ${C.borderDim}` }}>
        <HPBar current={player.current_hp} max={player.max_hp} />
        <div style={{ fontSize: 10, color: C.muted, textAlign: 'right', marginTop: 3, fontFamily: 'monospace' }}>
          {Math.round(player.current_hp)} / {player.max_hp}
        </div>
      </div>

      {/* Stats */}
      <div style={{ padding: '6px 12px' }}>
        {stats.map(([attr, val]) => (
          <StatRow key={attr} label={STAT_LABELS[attr] || attr} value={val} />
        ))}
      </div>

      {/* Items */}
      {ownedItems?.length > 0 && (
        <div style={{
          borderTop: `1px solid ${C.border}`,
          padding: '8px 12px',
        }}>
          <div style={{
            fontSize: 9,
            color: C.muted,
            letterSpacing: 2,
            textTransform: 'uppercase',
            fontFamily: "'Cinzel', serif",
            marginBottom: 5,
          }}>
            Equipped
          </div>
          {ownedItems.map(item => (
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
    </div>
  );
}
