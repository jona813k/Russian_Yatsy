import { C } from '../../theme.js';

export function HPBar({ current, max, color }) {
  const pct = max > 0 ? Math.max(0, Math.min(100, (current / max) * 100)) : 0;
  // Dynamic color based on HP%
  const barColor = color || (pct > 60 ? C.hpHigh : pct > 30 ? C.hpMid : C.hpLow);

  return (
    <div style={{
      background: '#1A0C04',
      borderRadius: 3,
      height: 10,
      overflow: 'hidden',
      border: `1px solid ${C.borderDim}`,
      position: 'relative',
    }}>
      <div style={{
        width: `${pct}%`,
        height: '100%',
        background: `linear-gradient(90deg, ${barColor}CC, ${barColor})`,
        transition: 'width 0.4s ease',
        borderRadius: 3,
      }} />
      {/* Shine */}
      <div style={{
        position: 'absolute',
        top: 0, left: 0,
        width: `${pct}%`,
        height: '40%',
        background: 'rgba(255,255,255,0.12)',
        borderRadius: 3,
        transition: 'width 0.4s ease',
      }} />
    </div>
  );
}
