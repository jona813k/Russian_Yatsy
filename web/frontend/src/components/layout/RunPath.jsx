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
        fontSize: 27,
        color: accent,
        minWidth: 16,
        textAlign: 'center',
        opacity: isDone ? 0.5 : 1,
      }}>
        {isDone ? '✓' : cfg.symbol}
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: 14,
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
          <div style={{ fontSize: 12, color: C.mutedDim, fontFamily: 'monospace' }}>{sub}</div>
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
  const currentLevel = run.level;

  // Only show nodes for the current level
  const levelNodes = path.filter(node => node.level === currentLevel);

  return (
    <div style={{ minWidth: 200, maxWidth: 155, height: 450 }}>
      <div style={{
        color: C.muted,
        fontSize: 15,
        letterSpacing: 2,
        marginBottom: 8,
        textTransform: 'uppercase',
        fontFamily: "'Cinzel', serif",
        paddingLeft: 4,
        borderBottom: `1px solid ${C.borderDim}`,
        paddingBottom: 6,
      }}>
        Level {currentLevel}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {levelNodes.map((node, i) => (
          <PathNode key={i} node={node} />
        ))}
      </div>
    </div>
  );
}
