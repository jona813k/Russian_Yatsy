import { C } from '../../theme.js';

export function Btn({ children, onClick, disabled, color, style }) {
  const bg = disabled ? '#2A1A08' : (color || C.crimson);
  const border = disabled ? C.borderDim : (color || C.crimson);
  const textColor = disabled ? C.mutedDim : C.sand;

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        background: disabled ? bg : `linear-gradient(180deg, ${bg}EE 0%, ${bg}BB 100%)`,
        color: textColor,
        border: `1px solid ${border}`,
        borderRadius: 4,
        padding: '9px 20px',
        cursor: disabled ? 'default' : 'pointer',
        fontSize: 13,
        fontWeight: '600',
        fontFamily: "'Cinzel', serif",
        letterSpacing: '0.05em',
        transition: 'all .15s',
        boxShadow: disabled ? 'none' : `0 2px 8px ${bg}88, inset 0 1px 0 rgba(255,255,255,0.08)`,
        textTransform: 'uppercase',
        ...style,
      }}
      onMouseEnter={e => {
        if (!disabled) {
          e.currentTarget.style.boxShadow = `0 4px 14px ${bg}CC, inset 0 1px 0 rgba(255,255,255,0.12)`;
          e.currentTarget.style.transform = 'translateY(-1px)';
        }
      }}
      onMouseLeave={e => {
        if (!disabled) {
          e.currentTarget.style.boxShadow = `0 2px 8px ${bg}88, inset 0 1px 0 rgba(255,255,255,0.08)`;
          e.currentTarget.style.transform = 'translateY(0)';
        }
      }}
    >
      {children}
    </button>
  );
}
