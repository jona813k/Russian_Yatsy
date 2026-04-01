import { C } from '../../theme.js';

const PHASE_LABELS = {
  upgrade:      (run) => `Prepare — ${run.upgrade_turns_max - run.upgrade_turns_used} turns left`,
  upgrade_done: () => 'Ready for Battle',
  combat:       () => 'In the Arena',
  pre_boss_shop: () => 'Before the Champion',
  shop:         () => 'The Marketplace',
  forge:        () => 'The Forge',
  game_over:    () => 'Fallen',
  victory:      () => 'Champion!',
};

export function RunHeader({ run }) {
  const fightLabel = run.fight_index === 2 ? 'Champion' : `Fight ${run.fight_index + 1}`;
  const phaseLabel = (PHASE_LABELS[run.phase] || (() => run.phase))(run);
  const isBoss = run.is_boss;

  return (
    <div style={{
      display: 'flex',
      gap: 0,
      alignItems: 'stretch',
      background: `linear-gradient(90deg, #1E0C04, #261404, #1E0C04)`,
      border: `1px solid ${C.border}`,
      borderRadius: 6,
      marginBottom: 16,
      overflow: 'hidden',
    }}>
      {/* Level badge */}
      <div style={{
        background: `linear-gradient(180deg, #3A1A08, #2A1004)`,
        borderRight: `1px solid ${C.border}`,
        padding: '8px 16px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minWidth: 80,
      }}>
        <span style={{ color: C.muted, fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', fontFamily: "'Cinzel', serif" }}>LEVEL</span>
        <span style={{ color: C.gold, fontWeight: '700', fontSize: 22, fontFamily: "'Cinzel', serif", lineHeight: 1 }}>
          {run.level}
        </span>
      </div>

      {/* Fight info */}
      <div style={{
        borderRight: `1px solid ${C.borderDim}`,
        padding: '8px 16px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
      }}>
        <span style={{ color: C.muted, fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', fontFamily: "'Cinzel', serif" }}>
          {isBoss ? 'CHAMPION' : 'OPPONENT'}
        </span>
        <span style={{
          color: isBoss ? C.scarlet : C.textDim,
          fontWeight: '600',
          fontSize: 13,
          fontFamily: "'Cinzel', serif",
        }}>
          {fightLabel}
        </span>
      </div>

      {/* Phase */}
      <div style={{
        padding: '8px 16px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        flex: 1,
      }}>
        <span style={{ color: C.muted, fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', fontFamily: "'Cinzel', serif" }}>PHASE</span>
        <span style={{ color: C.orange, fontWeight: '600', fontSize: 13, fontFamily: "'Cinzel', serif" }}>{phaseLabel}</span>
      </div>
    </div>
  );
}
