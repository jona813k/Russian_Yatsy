import { motion } from 'framer-motion';

const idleVariants = {
  idle: {
    y: [0, -3, 0],
    transition: { duration: 2.0, repeat: Infinity, ease: 'easeInOut' },
  },
  attack: {
    x: [0, 30, 0],
    transition: { duration: 0.4, times: [0, 0.25, 1] },
  },
  hit: {
    x: [0, -8, 6, 0],
    transition: { duration: 0.3 },
  },
  dead: {
    opacity: [1, 0.5, 0],
    y: [0, 10, 30],
    transition: { duration: 0.8 },
  },
};

function ImpShape() {
  return (
    <>
      {/* Wings */}
      <path d="M 25 35 Q 10 20 8 30 Q 12 38 20 40 Z" fill="#5A0808" />
      <path d="M 55 35 Q 70 20 72 30 Q 68 38 60 40 Z" fill="#5A0808" />
      {/* Body */}
      <ellipse cx="40" cy="52" rx="16" ry="20" fill="#8B1A1A" />
      {/* Head */}
      <circle cx="40" cy="28" r="16" fill="#9B2020" />
      {/* Horns */}
      <path d="M 30 18 L 26 6 L 33 16" fill="#5A0808" />
      <path d="M 50 18 L 54 6 L 47 16" fill="#5A0808" />
      {/* Eyes */}
      <circle cx="35" cy="27" r="4" fill="#FF4500" />
      <circle cx="45" cy="27" r="4" fill="#FF4500" />
      <circle cx="35" cy="27" r="2" fill="#1A0804" />
      <circle cx="45" cy="27" r="2" fill="#1A0804" />
      {/* Grin */}
      <path d="M 33 35 Q 40 40 47 35" stroke="#5A0808" strokeWidth="1.5" fill="none" />
      {/* Tail */}
      <path d="M 40 70 Q 50 80 55 74 Q 48 72 46 80" stroke="#8B1A1A" strokeWidth="2" fill="none" />
      <polygon points="55,72 58,76 62,70" fill="#5A0808" />
      {/* Arms */}
      <rect x="18" y="40" width="8" height="16" rx="3" fill="#9B2020" />
      <rect x="54" y="40" width="8" height="16" rx="3" fill="#9B2020" />
      {/* Claws */}
      {[20,23,26].map((x,i) => <line key={i} x1={x} y1="56" x2={x-1} y2="62" stroke="#5A0808" strokeWidth="1.5" strokeLinecap="round" />)}
      {[56,59,62].map((x,i) => <line key={i} x1={x} y1="56" x2={x+1} y2="62" stroke="#5A0808" strokeWidth="1.5" strokeLinecap="round" />)}
      {/* Legs */}
      <rect x="30" y="68" width="9" height="14" rx="3" fill="#9B2020" />
      <rect x="41" y="68" width="9" height="14" rx="3" fill="#9B2020" />
    </>
  );
}

function WolfShape() {
  return (
    <>
      {/* Body (quadruped) */}
      <ellipse cx="40" cy="68" rx="26" ry="16" fill="#6A6A5A" />
      {/* Head */}
      <ellipse cx="22" cy="54" rx="16" ry="13" fill="#6A6A5A" />
      {/* Snout */}
      <path d="M 8 58 Q 4 60 6 64 Q 8 66 14 64 Q 16 60 12 58 Z" fill="#5A5A4A" />
      {/* Ears */}
      <polygon points="16,42 12,30 22,40" fill="#5A5A4A" />
      <polygon points="26,40 30,28 34,40" fill="#5A5A4A" />
      <polygon points="17,42 14,33 21,41" fill="#9A7A6A" />
      <polygon points="27,40 30,31 33,40" fill="#9A7A6A" />
      {/* Eyes */}
      <circle cx="18" cy="52" r="3.5" fill="#E8C030" />
      <circle cx="28" cy="50" r="3.5" fill="#E8C030" />
      <circle cx="18" cy="52" r="1.5" fill="#1A0804" />
      <circle cx="28" cy="50" r="1.5" fill="#1A0804" />
      {/* Nose */}
      <ellipse cx="8" cy="62" rx="3" ry="2" fill="#2A1A10" />
      {/* Mouth */}
      <path d="M 5 64 Q 8 68 11 64" stroke="#2A1A10" strokeWidth="1.5" fill="none" />
      {/* Fur texture */}
      <path d="M 30 55 Q 38 52 46 55 Q 38 50 30 55" fill="#5A5A4A" opacity="0.5" />
      {/* Tail */}
      <path d="M 65 62 Q 76 52 74 46 Q 70 52 68 58 Q 66 56 65 62 Z" fill="#6A6A5A" />
      {/* Legs */}
      <rect x="15" y="76" width="8" height="20" rx="3" fill="#5A5A4A" />
      <rect x="25" y="76" width="8" height="20" rx="3" fill="#5A5A4A" />
      <rect x="46" y="76" width="8" height="20" rx="3" fill="#5A5A4A" />
      <rect x="56" y="76" width="8" height="20" rx="3" fill="#5A5A4A" />
      {/* Paws */}
      <ellipse cx="19" cy="96" rx="5" ry="3" fill="#4A4A3A" />
      <ellipse cx="29" cy="96" rx="5" ry="3" fill="#4A4A3A" />
      <ellipse cx="50" cy="96" rx="5" ry="3" fill="#4A4A3A" />
      <ellipse cx="60" cy="96" rx="5" ry="3" fill="#4A4A3A" />
    </>
  );
}

function OrcSummonShape() {
  return (
    <>
      {/* Simple barbarian-style orc, smaller */}
      <ellipse cx="40" cy="20" rx="15" ry="16" fill="#3A2808" />
      <ellipse cx="40" cy="22" rx="12" ry="13" fill="#5A7A30" />
      <circle cx="36" cy="20" r="2.5" fill="#E8C030" />
      <circle cx="44" cy="20" r="2.5" fill="#E8C030" />
      <circle cx="36" cy="20" r="1" fill="#1A0804" />
      <circle cx="44" cy="20" r="1" fill="#1A0804" />
      <path d="M 34 28 L 33 32" stroke="#E8D5B0" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M 46 28 L 47 32" stroke="#E8D5B0" strokeWidth="1.5" strokeLinecap="round" />
      {/* War paint */}
      <path d="M 30 18 L 36 22" stroke="#8B1A1A" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M 50 18 L 44 22" stroke="#8B1A1A" strokeWidth="1.5" strokeLinecap="round" />
      {/* Neck */}
      <rect x="35" y="33" width="10" height="6" rx="2" fill="#5A7A30" />
      {/* Body */}
      <rect x="26" y="38" width="28" height="28" rx="4" fill="#5A7A30" />
      <ellipse cx="24" cy="44" rx="8" ry="6" fill="#4A5A28" />
      <ellipse cx="56" cy="44" rx="8" ry="6" fill="#4A5A28" />
      {/* Belt */}
      <rect x="24" y="63" width="32" height="5" rx="2" fill="#4A2808" />
      {/* Legs */}
      <rect x="28" y="67" width="10" height="22" rx="3" fill="#5A7A30" />
      <rect x="42" y="67" width="10" height="22" rx="3" fill="#5A7A30" />
      <rect x="26" y="87" width="14" height="4" rx="2" fill="#3C2808" />
      <rect x="40" y="87" width="14" height="4" rx="2" fill="#3C2808" />
      {/* Arms */}
      <rect x="14" y="40" width="10" height="22" rx="3" fill="#5A7A30" />
      <rect x="56" y="40" width="10" height="22" rx="3" fill="#5A7A30" />
      {/* Axe */}
      <rect x="64" y="28" width="4" height="36" rx="2" fill="#6B3A10" />
      <path d="M 62 30 Q 57 34 57 40 Q 57 46 62 50 L 68 46 Q 70 42 70 40 Q 70 36 68 32 Z" fill="#9090B0" />
    </>
  );
}

function SkeletonShape() {
  return (
    <>
      {/* Skull */}
      <circle cx="40" cy="20" r="16" fill="#E8D5B0" />
      {/* Eye sockets */}
      <circle cx="34" cy="18" r="5" fill="#1A0A04" />
      <circle cx="46" cy="18" r="5" fill="#1A0A04" />
      <circle cx="34" cy="18" r="2.5" fill="#3A2A10" />
      <circle cx="46" cy="18" r="2.5" fill="#3A2A10" />
      {/* Nasal cavity */}
      <path d="M 38 24 L 40 28 L 42 24" fill="#1A0A04" />
      {/* Teeth */}
      {[33,36,39,42,45].map((x,i) => (
        <rect key={i} x={x} y="30" width="2.5" height="5" rx="1" fill="#E8D5B0" />
      ))}
      <rect x="31" y="29" width="18" height="4" fill="#1A0A04" />
      {/* Jaw */}
      <path d="M 26 28 Q 26 36 40 36 Q 54 36 54 28 Z" fill="#D4C09A" />
      {/* Spine/neck */}
      {[0,1,2].map(i => (
        <rect key={i} x="37" y={38+i*6} width="6" height="5" rx="2" fill="#D4C09A" />
      ))}
      {/* Ribcage */}
      {[0,1,2].map(i => (
        <React.Fragment key={i}>
          <path d={`M 40 ${54+i*8} Q 28 ${50+i*8} 26 ${58+i*8}`} stroke="#D4C09A" strokeWidth="3" fill="none" strokeLinecap="round" />
          <path d={`M 40 ${54+i*8} Q 52 ${50+i*8} 54 ${58+i*8}`} stroke="#D4C09A" strokeWidth="3" fill="none" strokeLinecap="round" />
        </React.Fragment>
      ))}
      {/* Pelvis */}
      <path d="M 28 78 Q 28 88 40 88 Q 52 88 52 78 Q 52 72 40 72 Q 28 72 28 78 Z" fill="#D4C09A" />
      {/* Arm bones */}
      <rect x="15" y="48" width="6" height="26" rx="3" fill="#D4C09A" />
      <rect x="57" y="48" width="6" height="26" rx="3" fill="#D4C09A" />
      {/* Forearms */}
      <rect x="12" y="72" width="5" height="20" rx="2" fill="#D4C09A" />
      <rect x="59" y="72" width="5" height="20" rx="2" fill="#D4C09A" />
      {/* Sword in right hand */}
      <rect x="64" y="60" width="4" height="28" rx="1.5" fill="#9090B0" />
      <polygon points="64,60 68,60 66,54" fill="#9090B0" />
      <rect x="61" y="84" width="11" height="3" rx="1" fill="#C8A030" />
      {/* Leg bones */}
      <rect x="32" y="88" width="6" height="26" rx="3" fill="#D4C09A" />
      <rect x="42" y="88" width="6" height="26" rx="3" fill="#D4C09A" />
      <ellipse cx="35" cy="116" rx="6" ry="3" fill="#D4C09A" />
      <ellipse cx="45" cy="116" rx="6" ry="3" fill="#D4C09A" />
    </>
  );
}

// Import React for Fragment usage in SkeletonShape
import React from 'react';

function DragonShape() {
  return (
    <>
      {/* Body */}
      <ellipse cx="40" cy="65" rx="22" ry="28" fill="#2A6A1A" />
      {/* Neck */}
      <rect x="32" y="35" width="16" height="30" rx="5" fill="#2A6A1A" />
      {/* Head */}
      <ellipse cx="40" cy="28" rx="18" ry="16" fill="#2A6A1A" />
      {/* Snout */}
      <path d="M 22 28 Q 18 30 16 34 Q 18 36 24 34 Q 26 30 24 28 Z" fill="#1A5A10" />
      {/* Horns */}
      <path d="M 32 14 Q 28 4 32 0 Q 34 6 35 12" fill="#1A4A0A" />
      <path d="M 48 14 Q 52 4 48 0 Q 46 6 45 12" fill="#1A4A0A" />
      {/* Eyes */}
      <circle cx="34" cy="24" r="4" fill="#E8C030" />
      <circle cx="46" cy="24" r="4" fill="#E8C030" />
      <circle cx="34" cy="24" r="2" fill="#1A0804" />
      <circle cx="46" cy="24" r="2" fill="#1A0804" />
      {/* Nostrils */}
      <circle cx="18" cy="32" r="1.5" fill="#1A0804" />
      <circle cx="16" cy="34" r="1.5" fill="#1A0804" />
      {/* Teeth */}
      {[21,24,27].map((x,i) => <polygon key={i} points={`${x},34 ${x+2},34 ${x+1},39`} fill="#E8D5B0" />)}
      {/* Wings */}
      <path d="M 22 50 Q 2 28 -4 14 Q 6 26 10 44 Q 14 56 22 60 Z" fill="#1A5A10" />
      <path d="M 22 50 Q 0 48 -2 58 Q 8 52 12 58 Q 16 62 22 62 Z" fill="#2A6A1A" opacity="0.7" />
      <path d="M 58 50 Q 78 28 84 14 Q 74 26 70 44 Q 66 56 58 60 Z" fill="#1A5A10" />
      <path d="M 58 50 Q 80 48 82 58 Q 72 52 68 58 Q 64 62 58 62 Z" fill="#2A6A1A" opacity="0.7" />
      {/* Scales/texture */}
      {[[35,45],[40,42],[45,45],[37,52],[43,52],[40,59],[36,66],[44,66]].map(([x,y],i) => (
        <ellipse key={i} cx={x} cy={y} rx="3" ry="2" fill="#1A5A10" opacity="0.5" />
      ))}
      {/* Tail */}
      <path d="M 55 80 Q 70 90 74 82 Q 68 82 66 88 Q 64 84 62 86" stroke="#2A6A1A" strokeWidth="4" fill="none" strokeLinecap="round" />
      <polygon points="73,80 76,84 79,78" fill="#1A5A10" />
      {/* Arms/claws */}
      <rect x="14" y="58" width="10" height="18" rx="4" fill="#2A6A1A" />
      <rect x="56" y="58" width="10" height="18" rx="4" fill="#2A6A1A" />
      {[16,19,22].map((x,i) => <line key={i} x1={x} y1="76" x2={x-1} y2="83" stroke="#1A4A0A" strokeWidth="2" strokeLinecap="round" />)}
      {[58,61,64].map((x,i) => <line key={i} x1={x} y1="76" x2={x+1} y2="83" stroke="#1A4A0A" strokeWidth="2" strokeLinecap="round" />)}
      {/* Legs */}
      <rect x="26" y="86" width="12" height="18" rx="4" fill="#1A5A10" />
      <rect x="42" y="86" width="12" height="18" rx="4" fill="#1A5A10" />
      {[27,30,33].map((x,i) => <line key={i} x1={x} y1="104" x2={x} y2="112" stroke="#1A4A0A" strokeWidth="2" strokeLinecap="round" />)}
      {[43,46,49].map((x,i) => <line key={i} x1={x} y1="104" x2={x} y2="112" stroke="#1A4A0A" strokeWidth="2" strokeLinecap="round" />)}
    </>
  );
}

const SUMMON_SHAPES = {
  Imp:      ImpShape,
  Wolf:     WolfShape,
  Orc:      OrcSummonShape,
  Skeleton: SkeletonShape,
  Dragon:   DragonShape,
};

export function SummonSprite({ name, anim = 'idle', size = 120 }) {
  const Shape = SUMMON_SHAPES[name] || ImpShape;
  return (
    <motion.svg
      viewBox="0 0 80 120"
      width={size * 0.667}
      height={size}
      style={{ overflow: 'visible', display: 'block' }}
      variants={idleVariants}
      animate={anim}
    >
      <Shape />
    </motion.svg>
  );
}
