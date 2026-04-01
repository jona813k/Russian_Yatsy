import { C } from '../../theme.js';

const NODE_CONFIG = {
  upgrade:       { symbol: '⚔', label: 'Prepare',     color: C.blue    },
  fight:         { symbol: '⚔', label: '',             color: C.orange  },
  boss:          { symbol: '☠', label: '',             color: C.scarlet },
  pre_boss_shop: { symbol: '⚖', label: 'Market',       color: C.gold    },
  shop:          { symbol: '⚖', label: 'Market',       color: C.gold    },
  forge:         { symbol: '⚒', label: 'Forge',        color: C.purple  },
};

function PathNode({ node }) {
  const isDone    = node.status === 'done';
  const isCurrent = node.status === 'current';
  const cfg = NODE_CONFIG[node.type] || NODE_CONFIG.fight;

  const label = node.type === 'fight' || node.type === 'boss'
    ? node.enemy_name
    : cfg.label;

  const sub = node.type === 'upgrade'
    ? `${node.turns} turns`
    : (node.type === 'fight' || node.type === 'boss') && node.enemy_hp
    ? `${node.enemy_hp} HP`
    : node.type === 'forge'
    ? 'Pick 1 of 3'
    : null;

  const accent = isCurrent ? cfg.color : isDone ? C.mutedDim : C.muted;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      padding: '5px 7px',
      borderRadius: 4,
      background: isCurrent ? `${cfg.color}18` : 'transparent',
      border: `1px solid ${isCurrent ? cfg.color : isDone ? C.borderDim : 'transparent'}`,
      opacity: isDone ? 0.4 : 1,
      transition: 'all 0.2s',
    }}>
      <span style={{
        fontSize: 12,
        color: accent,
        minWidth: 16,
        textAlign: 'center',
        opacity: isDone ? 0.5 : 1,
      }}>
        {isDone ? '✓' : cfg.symbol}
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: 10,
          color: accent,
          fontWeight: isCurrent ? '600' : '400',
          fontFamily: "'Cinzel', serif",
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}>
          {label}
        </div>
        {sub && !isDone && (
          <div style={{ fontSize: 9, color: C.mutedDim, fontFamily: 'monospace' }}>{sub}</div>
        )}
      </div>
      {isCurrent && (
        <span style={{ fontSize: 8, color: cfg.color }}>◀</span>
      )}
    </div>
  );
}

export function RunPath({ run }) {
  const path = run.path || [];

  return (
    <div style={{ minWidth: 140, maxWidth: 155 }}>
      <div style={{
        color: C.muted,
        fontSize: 9,
        letterSpacing: 2,
        marginBottom: 8,
        textTransform: 'uppercase',
        fontFamily: "'Cinzel', serif",
        paddingLeft: 4,
        borderBottom: `1px solid ${C.borderDim}`,
        paddingBottom: 6,
      }}>
        Path Ahead
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {path.map((node, i) => {
          const isFirstOfLevel =
            (node.type === 'upgrade' && node.fight === 0) ||
            (node.type === 'pre_boss_shop' && node.fight === 0);
          return (
            <div key={i}>
              {isFirstOfLevel && (
                <div style={{
                  color: C.mutedDim,
                  fontSize: 8,
                  letterSpacing: 2,
                  padding: '5px 4px 2px',
                  textTransform: 'uppercase',
                  fontFamily: "'Cinzel', serif",
                  borderTop: i > 0 ? `1px solid ${C.borderDim}` : 'none',
                  marginTop: i > 0 ? 4 : 0,
                }}>
                  Level {node.level}
                </div>
              )}
              <PathNode node={node} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
