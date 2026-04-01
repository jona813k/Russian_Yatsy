import { motion } from 'framer-motion';

const variants = {
  idle: {
    y: [0, -4, 0],
    transition: { duration: 2.8, repeat: Infinity, ease: 'easeInOut' },
  },
  attack: {
    x: [0, 45, 0],
    transition: { duration: 0.45, times: [0, 0.25, 1], ease: 'easeOut' },
  },
  hit: {
    x: [0, -10, 8, -5, 0],
    transition: { duration: 0.32 },
  },
  dead: {
    rotate: [0, 5, 88],
    y: [0, 0, 28],
    x: [0, 0, 18],
    opacity: [1, 1, 0.15],
    transition: { duration: 1.1, times: [0, 0.25, 1], ease: 'easeIn' },
  },
};

// The player gladiator — Roman-inspired, faces right toward the enemy
export function PlayerSprite({ anim = 'idle', size = 160 }) {
  return (
    <motion.svg
      viewBox="0 0 80 124"
      width={size * 0.667}
      height={size}
      style={{ overflow: 'visible', display: 'block', filter: anim === 'hit' ? 'brightness(2) saturate(0)' : 'none' }}
      variants={variants}
      animate={anim}
    >
      {/* Red cape (behind body) */}
      <path d="M 30 48 Q 12 65 15 94 L 64 94 Q 68 65 50 48 Z" fill="#7A1010" opacity="0.8" />

      {/* === HELMET === */}
      {/* Main dome */}
      <ellipse cx="40" cy="22" rx="18" ry="20" fill="#C8A030" />
      {/* Helmet highlight */}
      <ellipse cx="35" cy="16" rx="7" ry="6" fill="#D4B040" opacity="0.4" />
      {/* Brim */}
      <rect x="22" y="30" width="36" height="6" rx="2" fill="#B89020" />
      {/* Cheek guards */}
      <rect x="22" y="28" width="9" height="16" rx="3" fill="#A07820" />
      <rect x="49" y="28" width="9" height="16" rx="3" fill="#A07820" />
      {/* Neck guard */}
      <rect x="26" y="34" width="28" height="5" rx="2" fill="#9A7018" />

      {/* Red crest plume */}
      <path d="M 40 2 C 35 5 32 11 35 17 C 37 13 39 9 40 9 C 41 9 43 13 45 17 C 48 11 45 5 40 2 Z" fill="#8B1A1A" />
      <rect x="38.5" y="6" width="3" height="14" rx="1.5" fill="#9B2020" />
      {/* Plume base */}
      <rect x="36" y="17" width="8" height="6" rx="2" fill="#8B1A1A" />

      {/* === FACE === */}
      <rect x="29" y="30" width="22" height="14" rx="3" fill="#C87840" />
      {/* Eyes (stern gladiator expression) */}
      <circle cx="36" cy="37" r="3" fill="#1A0804" />
      <circle cx="44" cy="37" r="3" fill="#1A0804" />
      <circle cx="37" cy="36.2" r="1.2" fill="#3A2818" />
      <circle cx="45" cy="36.2" r="1.2" fill="#3A2818" />
      {/* Brow line (fierce) */}
      <path d="M 30 33 L 39 35" stroke="#7A4818" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M 41 35 L 50 33" stroke="#7A4818" strokeWidth="1.5" strokeLinecap="round" />

      {/* === NECK & SHOULDERS === */}
      <rect x="36" y="43" width="8" height="7" rx="2" fill="#C87840" />
      {/* Pauldrons */}
      <ellipse cx="24" cy="52" rx="10" ry="7" fill="#C8A030" />
      <ellipse cx="56" cy="52" rx="10" ry="7" fill="#C8A030" />
      <ellipse cx="24" cy="51" rx="6" ry="4" fill="#D4B040" opacity="0.3" />
      <ellipse cx="56" cy="51" rx="6" ry="4" fill="#D4B040" opacity="0.3" />

      {/* === TORSO (Lorica Segmentata) === */}
      <rect x="25" y="50" width="30" height="32" rx="5" fill="#B89028" />
      {/* Armor segments */}
      <line x1="25" y1="57" x2="55" y2="57" stroke="#8A6810" strokeWidth="1.5" />
      <line x1="25" y1="64" x2="55" y2="64" stroke="#8A6810" strokeWidth="1.5" />
      <line x1="25" y1="71" x2="55" y2="71" stroke="#8A6810" strokeWidth="1.5" />
      {/* Center breastplate seam */}
      <line x1="40" y1="50" x2="40" y2="82" stroke="#8A6810" strokeWidth="1" />
      {/* Chest highlight */}
      <ellipse cx="34" cy="56" rx="5" ry="4" fill="#C8A030" opacity="0.2" />

      {/* === BELT & PTERYGES === */}
      <rect x="23" y="80" width="34" height="7" rx="3" fill="#5C3A10" />
      {/* Belt studs */}
      {[0,1,2,3,4,5,6,7].map(i => (
        <circle key={i} cx={25.5 + i * 4} cy={83.5} r="1.5" fill="#C8A030" />
      ))}
      {/* Leather hanging strips */}
      {[0,1,2,3,4,5,6,7].map(i => (
        <rect key={i} x={23 + i * 4} y="86" width="3.5" height="14" rx="2"
          fill={i % 2 === 0 ? '#6B3A10' : '#8B4A18'} />
      ))}
      {/* Strip studs */}
      {[0,1,2,3,4,5,6,7].map(i => (
        <circle key={i} cx={24.75 + i * 4} cy={91} r="1" fill="#C8A030" opacity="0.7" />
      ))}

      {/* === LEGS === */}
      <rect x="28" y="99" width="11" height="22" rx="3" fill="#C87840" />
      <rect x="41" y="99" width="11" height="22" rx="3" fill="#C87840" />
      {/* Greaves (shin guards) */}
      <rect x="27" y="108" width="13" height="12" rx="3" fill="#B89028" />
      <rect x="40" y="108" width="13" height="12" rx="3" fill="#B89028" />
      <line x1="33.5" y1="109" x2="33.5" y2="119" stroke="#8A6810" strokeWidth="1" />
      <line x1="46.5" y1="109" x2="46.5" y2="119" stroke="#8A6810" strokeWidth="1" />
      {/* Sandals */}
      <rect x="24" y="119" width="18" height="5" rx="2" fill="#3C200A" />
      <rect x="38" y="119" width="18" height="5" rx="2" fill="#3C200A" />
      {/* Sandal straps */}
      <line x1="26" y1="119" x2="26" y2="124" stroke="#5C3A10" strokeWidth="1.5" />
      <line x1="30" y1="119" x2="30" y2="124" stroke="#5C3A10" strokeWidth="1.5" />
      <line x1="40" y1="119" x2="40" y2="124" stroke="#5C3A10" strokeWidth="1.5" />
      <line x1="44" y1="119" x2="44" y2="124" stroke="#5C3A10" strokeWidth="1.5" />

      {/* === SHIELD ARM (left) === */}
      <rect x="14" y="48" width="10" height="24" rx="4" fill="#C87840" />
      {/* Scutum shield */}
      <rect x="3" y="44" width="20" height="36" rx="5" fill="#8B1A1A" />
      <rect x="5" y="46" width="16" height="32" rx="4" fill="#721414" />
      {/* Shield decorative border */}
      <rect x="5" y="46" width="16" height="32" rx="4" fill="none" stroke="#C8A030" strokeWidth="1.5" />
      {/* Shield boss */}
      <circle cx="13" cy="62" r="5" fill="#C8A030" />
      <circle cx="13" cy="62" r="3.5" fill="#A07820" />
      <circle cx="13" cy="62" r="1.5" fill="#C8A030" />
      {/* Shield eagle emblem */}
      <path d="M 13 53 L 11 58 L 8 56 L 11 60 L 9 65 L 13 62 L 17 65 L 15 60 L 18 56 L 15 58 Z"
        fill="#C8A030" opacity="0.6" />

      {/* === SWORD ARM (right) === */}
      <rect x="57" y="48" width="10" height="24" rx="4" fill="#C87840" />
      {/* Gladius */}
      <rect x="65" y="26" width="6" height="30" rx="2" fill="#9898B0" />
      {/* Blade edge highlight */}
      <line x1="68" y1="26" x2="68" y2="56" stroke="#C0C0D8" strokeWidth="1" opacity="0.6" />
      {/* Blade tip */}
      <polygon points="65,26 71,26 68,20" fill="#9898B0" />
      {/* Crossguard */}
      <rect x="62" y="54" width="14" height="4" rx="2" fill="#C8A030" />
      {/* Grip */}
      <rect x="65" y="58" width="6" height="13" rx="2" fill="#5C3A10" />
      {/* Grip wrap */}
      <line x1="65" y1="61" x2="71" y2="61" stroke="#3C200A" strokeWidth="1" />
      <line x1="65" y1="65" x2="71" y2="65" stroke="#3C200A" strokeWidth="1" />
      <line x1="65" y1="69" x2="71" y2="69" stroke="#3C200A" strokeWidth="1" />
      {/* Pommel */}
      <circle cx="68" cy="72" r="4" fill="#C8A030" />
      <circle cx="68" cy="72" r="2.5" fill="#A07820" />
    </motion.svg>
  );
}
