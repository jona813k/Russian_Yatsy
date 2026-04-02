import { C, SHADOW } from '../../theme.js';

export function Panel({ children, style, gold = false, purple = false }) {
  const borderColor = gold ? C.gold : purple ? C.purple : C.border;
  const bgColor = gold ? '#1E1404' : purple ? '#180A20' : C.panel;
  return (
    <div style={{
      background: bgColor,
      border: `1px solid ${borderColor}`,
      borderRadius: 6,
      padding: 16,
      boxShadow: SHADOW,
      position: 'relative',
      ...style,
    }}>
      {/* Corner accents */}
      <div style={{
        position: 'absolute', top: 3, left: 3,
        width: 8, height: 8,
        borderTop: `2px solid ${borderColor}`,
        borderLeft: `2px solid ${borderColor}`,
        opacity: 0.7,
      }} />
      <div style={{
        position: 'absolute', top: 3, right: 3,
        width: 8, height: 8,
        borderTop: `2px solid ${borderColor}`,
        borderRight: `2px solid ${borderColor}`,
        opacity: 0.7,
      }} />
      <div style={{
        position: 'absolute', bottom: 3, left: 3,
        width: 8, height: 8,
        borderBottom: `2px solid ${borderColor}`,
        borderLeft: `2px solid ${borderColor}`,
        opacity: 0.7,
      }} />
      <div style={{
        position: 'absolute', bottom: 3, right: 3,
        width: 8, height: 8,
        borderBottom: `2px solid ${borderColor}`,
        borderRight: `2px solid ${borderColor}`,
        opacity: 0.7,
      }} />
      {children}
    </div>
  );
}
