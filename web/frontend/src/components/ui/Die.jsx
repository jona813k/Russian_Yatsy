import { C } from '../../theme.js';

// Pip layouts for d6 faces
const PIP_LAYOUTS = {
  1: [[18, 18]],
  2: [[10, 10], [26, 26]],
  3: [[10, 10], [18, 18], [26, 26]],
  4: [[10, 10], [26, 10], [10, 26], [26, 26]],
  5: [[10, 10], [26, 10], [18, 18], [10, 26], [26, 26]],
  6: [[10, 10], [26, 10], [10, 18], [26, 18], [10, 26], [26, 26]],
};

function DieFace({ value, color = '#1A0A04' }) {
  if (value <= 6) {
    return (
      <svg width={36} height={36} style={{ display: 'block' }}>
        {(PIP_LAYOUTS[value] || []).map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r={4} fill={color} />
        ))}
      </svg>
    );
  }
  return (
    <svg width={36} height={36} style={{ display: 'block' }}>
      <text
        x={18} y={24}
        textAnchor="middle"
        fontSize={14}
        fontWeight="bold"
        fontFamily="'Cinzel', serif"
        fill={color}
      >
        {value}
      </text>
    </svg>
  );
}

// Base backgrounds per die type
const DIE_TYPE_STYLES = {
  d12:   { bg: '#2A1840', border: '#7A3A9A', text: '#C084FC' },
  d3:    { bg: '#1A1A08', border: '#8A7A20', text: '#E8C84A' },
  risky: { bg: '#3A0808', border: '#8B1A1A', text: '#F87171' },
  normal:{ bg: '#2A1A08', border: C.border,  text: C.sand },
};

const STATE_OVERRIDES = {
  userSelected: { bg: '#3A2A04', border: C.gold,    textColor: '#1A0A04' },
  preview:      { bg: '#2A2004', border: C.yellow,  textColor: '#1A0A04' },
  illegal:      { bg: '#0F0804', border: '#2A1808',  textColor: '#3A2A18', opacity: 0.4 },
  setAside:     { bg: '#1A1008', border: '#3A2808',  textColor: C.muted,   opacity: 0.6 },
  rolling:      { bg: '#181008', border: C.borderDim, textColor: C.mutedDim },
};

export function Die({ value, state = 'normal', dieType, onClick }) {
  const typeStyle = DIE_TYPE_STYLES[dieType] || DIE_TYPE_STYLES.normal;
  const override = STATE_OVERRIDES[state];

  const bg = override?.bg ?? typeStyle.bg;
  const border = override?.border ?? typeStyle.border;
  const textColor = override?.textColor ?? typeStyle.text;
  const opacity = override?.opacity ?? 1;
  const isSelected = state === 'userSelected';
  const isPreview = state === 'preview';

  return (
    <div
      onClick={onClick}
      style={{
        background: isSelected
          ? `linear-gradient(135deg, #4A3A08, #3A2A04)`
          : `linear-gradient(135deg, ${bg}EE, ${bg}CC)`,
        border: `2px solid ${border}`,
        borderRadius: 6,
        width: 54,
        height: 54,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: (state === 'illegal' || state === 'setAside') ? 'default' : 'pointer',
        transition: 'all .12s',
        userSelect: 'none',
        opacity,
        boxShadow: isSelected
          ? `0 0 10px ${C.gold}88, inset 0 1px 0 rgba(255,255,255,0.1)`
          : isPreview
          ? `0 0 6px ${C.yellow}66`
          : `inset 0 1px 0 rgba(255,255,255,0.06), 0 2px 4px rgba(0,0,0,0.4)`,
        transform: isSelected ? 'translateY(-3px) scale(1.05)' : 'none',
        borderStyle: isPreview ? 'dashed' : 'solid',
      }}
    >
      <DieFace value={value} color={textColor} />
    </div>
  );
}
