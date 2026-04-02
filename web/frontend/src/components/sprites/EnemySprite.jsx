import { motion } from 'framer-motion';

// Enemies face LEFT (toward the player on the left side)
// Achieved via scaleX(-1) on the wrapper

const variants = {
  idle: {
    y: [0, -4, 0],
    transition: { duration: 3.0, repeat: Infinity, ease: 'easeInOut' },
  },
  attack: {
    x: [0, -45, 0],
    transition: { duration: 0.45, times: [0, 0.25, 1], ease: 'easeOut' },
  },
  hit: {
    x: [0, 10, -8, 5, 0],
    transition: { duration: 0.32 },
  },
  dead: {
    rotate: [0, -5, -88],
    y: [0, 0, 28],
    x: [0, 0, -18],
    opacity: [1, 1, 0.15],
    transition: { duration: 1.1, times: [0, 0.25, 1], ease: 'easeIn' },
  },
};

// ============================================================
// Individual enemy shapes — all drawn facing RIGHT, then mirrored
// ============================================================

function Legionnaire() {
  return (
    <>
      {/* Yellow cape */}
      <path d="M 30 48 Q 12 65 15 94 L 64 94 Q 68 65 50 48 Z" fill="#8A7010" opacity="0.8" />
      {/* Helmet */}
      <ellipse cx="40" cy="22" rx="18" ry="20" fill="#9090A8" />
      <ellipse cx="35" cy="16" rx="7" ry="6" fill="#A0A0C0" opacity="0.35" />
      <rect x="22" y="30" width="36" height="6" rx="2" fill="#7878A0" />
      <rect x="22" y="28" width="9" height="16" rx="3" fill="#6868A0" />
      <rect x="49" y="28" width="9" height="16" rx="3" fill="#6868A0" />
      <rect x="26" y="34" width="28" height="5" rx="2" fill="#6060A0" />
      {/* Yellow plume */}
      <path d="M 40 2 C 35 5 32 11 35 17 C 37 13 39 9 40 9 C 41 9 43 13 45 17 C 48 11 45 5 40 2 Z" fill="#C8A030" />
      <rect x="38.5" y="6" width="3" height="14" rx="1.5" fill="#D4B040" />
      <rect x="36" y="17" width="8" height="6" rx="2" fill="#C8A030" />
      {/* Face */}
      <rect x="29" y="30" width="22" height="14" rx="3" fill="#C87840" />
      <circle cx="36" cy="37" r="3" fill="#1A0804" />
      <circle cx="44" cy="37" r="3" fill="#1A0804" />
      <circle cx="37" cy="36.2" r="1.2" fill="#3A2818" />
      <circle cx="45" cy="36.2" r="1.2" fill="#3A2818" />
      <path d="M 30 33 L 39 34" stroke="#7A4818" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M 41 34 L 50 33" stroke="#7A4818" strokeWidth="1.5" strokeLinecap="round" />
      {/* Neck */}
      <rect x="36" y="43" width="8" height="7" rx="2" fill="#C87840" />
      {/* Pauldrons */}
      <ellipse cx="24" cy="52" rx="10" ry="7" fill="#9090A8" />
      <ellipse cx="56" cy="52" rx="10" ry="7" fill="#9090A8" />
      {/* Torso */}
      <rect x="25" y="50" width="30" height="32" rx="5" fill="#8080A0" />
      <line x1="25" y1="57" x2="55" y2="57" stroke="#6060A0" strokeWidth="1.5" />
      <line x1="25" y1="64" x2="55" y2="64" stroke="#6060A0" strokeWidth="1.5" />
      <line x1="25" y1="71" x2="55" y2="71" stroke="#6060A0" strokeWidth="1.5" />
      <line x1="40" y1="50" x2="40" y2="82" stroke="#6060A0" strokeWidth="1" />
      {/* Belt */}
      <rect x="23" y="80" width="34" height="7" rx="3" fill="#3A3A6A" />
      {[0,1,2,3,4,5,6,7].map(i => (
        <circle key={i} cx={25.5 + i * 4} cy={83.5} r="1.5" fill="#9090A8" />
      ))}
      {/* Pteryges */}
      {[0,1,2,3,4,5,6,7].map(i => (
        <rect key={i} x={23 + i * 4} y="86" width="3.5" height="14" rx="2"
          fill={i % 2 === 0 ? '#2A2A5A' : '#3A3A6A'} />
      ))}
      {/* Legs */}
      <rect x="28" y="99" width="11" height="22" rx="3" fill="#C87840" />
      <rect x="41" y="99" width="11" height="22" rx="3" fill="#C87840" />
      <rect x="27" y="108" width="13" height="12" rx="3" fill="#8080A0" />
      <rect x="40" y="108" width="13" height="12" rx="3" fill="#8080A0" />
      <rect x="24" y="119" width="18" height="5" rx="2" fill="#2A2A4A" />
      <rect x="38" y="119" width="18" height="5" rx="2" fill="#2A2A4A" />
      {/* Shield arm (left) */}
      <rect x="14" y="48" width="10" height="24" rx="4" fill="#C87840" />
      {/* Oval shield (parma) */}
      <ellipse cx="9" cy="62" rx="9" ry="16" fill="#8080A0" />
      <ellipse cx="9" cy="62" rx="7" ry="14" fill="#6060A0" />
      <ellipse cx="9" cy="62" rx="3" ry="3" fill="#9090A8" />
      {/* Pilum (javelin) — right arm */}
      <rect x="57" y="48" width="10" height="24" rx="4" fill="#C87840" />
      <rect x="67" y="10" width="4" height="70" rx="2" fill="#8A6820" />
      <polygon points="67,10 71,10 69,2" fill="#9898B0" />
    </>
  );
}

function Mercenary() {
  return (
    <>
      {/* Leather hood/cloak */}
      <path d="M 26 34 Q 12 55 15 90 L 65 90 Q 68 55 54 34 Z" fill="#3C2808" opacity="0.9" />
      {/* Hood */}
      <ellipse cx="40" cy="24" rx="18" ry="20" fill="#3C2808" />
      <path d="M 22 24 Q 22 44 32 44 L 48 44 Q 58 44 58 24 Z" fill="#2A1A04" />
      {/* Scarf/wrapping */}
      <rect x="27" y="35" width="26" height="10" rx="4" fill="#5C3A10" />
      {/* Face in shadow */}
      <rect x="30" y="32" width="20" height="14" rx="3" fill="#A06030" />
      <circle cx="36" cy="39" r="2.5" fill="#1A0804" />
      <circle cx="44" cy="39" r="2.5" fill="#1A0804" />
      {/* Scar */}
      <path d="M 43 34 L 45 38 L 47 40" stroke="#7A2010" strokeWidth="1.5" strokeLinecap="round" fill="none" />
      {/* Neck */}
      <rect x="36" y="43" width="8" height="7" rx="2" fill="#A06030" />
      {/* Mismatched armor */}
      <rect x="25" y="50" width="30" height="32" rx="4" fill="#4A2A08" />
      <rect x="25" y="50" width="14" height="32" rx="4" fill="#3A2208" />
      {/* Leather straps */}
      <path d="M 28 50 L 52 60 M 28 58 L 52 70 M 28 66 L 52 78" stroke="#6B3A10" strokeWidth="1.5" />
      {/* Rivets */}
      {[[30,54],[40,54],[50,54],[30,62],[40,62],[50,62]].map(([x,y],i) => (
        <circle key={i} cx={x} cy={y} r="1.5" fill="#C8A030" opacity="0.7" />
      ))}
      {/* Belt */}
      <rect x="23" y="80" width="34" height="6" rx="2" fill="#3C2008" />
      <rect x="37" y="79" width="6" height="8" rx="1" fill="#6B3A10" />
      {/* Legs */}
      <rect x="28" y="85" width="11" height="30" rx="3" fill="#3C2808" />
      <rect x="41" y="85" width="11" height="30" rx="3" fill="#3C2808" />
      <rect x="26" y="112" width="15" height="5" rx="2" fill="#2A1A04" />
      <rect x="39" y="112" width="15" height="5" rx="2" fill="#2A1A04" />
      {/* Left arm dagger */}
      <rect x="10" y="50" width="9" height="24" rx="3" fill="#A06030" />
      <rect x="12" y="34" width="4" height="20" rx="1.5" fill="#9898B0" />
      <polygon points="12,34 16,34 14,28" fill="#9898B0" />
      <rect x="9" y="51" width="11" height="3" rx="1" fill="#6B3A10" />
      {/* Right arm dagger */}
      <rect x="57" y="50" width="9" height="24" rx="3" fill="#A06030" />
      <rect x="60" y="34" width="4" height="20" rx="1.5" fill="#9898B0" />
      <polygon points="60,34 64,34 62,28" fill="#9898B0" />
      <rect x="57" y="51" width="11" height="3" rx="1" fill="#6B3A10" />
    </>
  );
}

function Barbarian() {
  return (
    <>
      {/* Fur cloak */}
      <path d="M 18 46 Q 4 65 8 98 L 72 98 Q 76 65 62 46 Z" fill="#5C3A18" opacity="0.85" />
      {/* Wild hair */}
      <ellipse cx="40" cy="21" rx="20" ry="21" fill="#3A2808" />
      {/* Hair spikes */}
      {[-14,-10,-6,-2,2,6,10,14].map((x, i) => (
        <path key={i}
          d={`M ${40+x} 2 Q ${40+x-2} -2 ${40+x+2} 2 Q ${40+x+4} 4 ${40+x} 6`}
          fill="#3A2808" />
      ))}
      {/* Face (greenish orc skin) */}
      <ellipse cx="40" cy="24" rx="15" ry="16" fill="#5A7A30" />
      {/* War paint — red lines */}
      <path d="M 29 20 L 37 25 L 30 30" stroke="#8B1A1A" strokeWidth="2" fill="none" strokeLinecap="round" />
      <path d="M 51 20 L 43 25 L 50 30" stroke="#8B1A1A" strokeWidth="2" fill="none" strokeLinecap="round" />
      {/* Tusks */}
      <path d="M 33 34 L 31 40" stroke="#E8D5B0" strokeWidth="2" strokeLinecap="round" />
      <path d="M 47 34 L 49 40" stroke="#E8D5B0" strokeWidth="2" strokeLinecap="round" />
      {/* Eyes (yellow, menacing) */}
      <circle cx="36" cy="23" r="3.5" fill="#E8C030" />
      <circle cx="44" cy="23" r="3.5" fill="#E8C030" />
      <circle cx="36" cy="23" r="1.5" fill="#1A0804" />
      <circle cx="44" cy="23" r="1.5" fill="#1A0804" />
      {/* Nose */}
      <ellipse cx="40" cy="28" rx="3" ry="2" fill="#4A6A28" />
      {/* Neck */}
      <rect x="34" y="38" width="12" height="8" rx="3" fill="#5A7A30" />
      {/* Chest — massive, bare-ish */}
      <rect x="22" y="46" width="36" height="38" rx="5" fill="#5A7A30" />
      {/* Fur shoulder pieces */}
      <ellipse cx="21" cy="52" rx="11" ry="8" fill="#5C3A18" />
      <ellipse cx="59" cy="52" rx="11" ry="8" fill="#5C3A18" />
      {/* Chest tribal tattoo */}
      <path d="M 35 52 Q 40 58 45 52 Q 40 60 35 52 Z" stroke="#3A5A20" strokeWidth="1.5" fill="none" />
      <path d="M 36 60 L 40 68 L 44 60" stroke="#3A5A20" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      {/* Belt/loincloth */}
      <rect x="21" y="82" width="38" height="8" rx="3" fill="#4A2808" />
      <path d="M 25 90 L 25 106 L 35 106 L 35 90" fill="#3C2008" />
      <path d="M 39 90 L 39 106 L 49 106 L 49 90" fill="#4A2808" />
      {/* Legs */}
      <rect x="26" y="96" width="13" height="24" rx="4" fill="#5A7A30" />
      <rect x="41" y="96" width="13" height="24" rx="4" fill="#5A7A30" />
      <rect x="24" y="118" width="17" height="5" rx="2" fill="#3C2008" />
      <rect x="39" y="118" width="17" height="5" rx="2" fill="#3C2008" />
      {/* Left arm */}
      <rect x="10" y="48" width="12" height="30" rx="5" fill="#5A7A30" />
      {/* Right arm */}
      <rect x="58" y="48" width="12" height="30" rx="5" fill="#5A7A30" />
      {/* Battle axe */}
      <rect x="68" y="20" width="5" height="58" rx="2" fill="#8A6820" />
      {/* Axe head */}
      <path d="M 66 22 Q 58 28 58 40 Q 58 52 66 56 L 73 50 Q 78 42 78 38 Q 78 30 73 24 Z" fill="#9898B0" />
      <path d="M 68 24 Q 64 30 64 38 Q 64 46 68 50 L 72 46 Q 74 40 74 38 Q 74 32 72 28 Z" fill="#B0B0C8" opacity="0.4" />
      <circle cx="67" cy="22" r="2.5" fill="#9898B0" />
    </>
  );
}

function Berserker() {
  return (
    <>
      {/* Bloodied fur cloak */}
      <path d="M 18 44 Q 4 62 8 96 L 72 96 Q 76 62 62 44 Z" fill="#6B2208" opacity="0.85" />
      {/* Wilder hair */}
      <ellipse cx="40" cy="20" rx="21" ry="20" fill="#2A1A04" />
      {[-16,-12,-8,-4,0,4,8,12,16].map((x, i) => (
        <path key={i} d={`M ${40+x} 1 Q ${40+x-3} -4 ${40+x+2} 2`} fill="#2A1A04" />
      ))}
      {/* Orc face — more crazed */}
      <ellipse cx="40" cy="23" rx="15" ry="16" fill="#4A6A28" />
      {/* Aggressive war paint */}
      <path d="M 26 18 L 40 26 L 28 32" stroke="#8B1A1A" strokeWidth="3" fill="none" strokeLinecap="round" />
      <path d="M 54 18 L 40 26 L 52 32" stroke="#8B1A1A" strokeWidth="3" fill="none" strokeLinecap="round" />
      {/* Blood splatter */}
      <circle cx="44" cy="20" r="2" fill="#6B1010" />
      <circle cx="32" cy="26" r="1.5" fill="#6B1010" />
      <circle cx="48" cy="30" r="1" fill="#6B1010" />
      {/* Tusks */}
      <path d="M 32 35 L 30 42" stroke="#E8D5B0" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M 48 35 L 50 42" stroke="#E8D5B0" strokeWidth="2.5" strokeLinecap="round" />
      {/* Eyes (frenzied red) */}
      <circle cx="35" cy="22" r="4" fill="#DC2020" />
      <circle cx="45" cy="22" r="4" fill="#DC2020" />
      <circle cx="35" cy="22" r="1.5" fill="#1A0804" />
      <circle cx="45" cy="22" r="1.5" fill="#1A0804" />
      {/* Nose ring */}
      <path d="M 37 29 Q 40 31 43 29" stroke="#C8A030" strokeWidth="1.5" fill="none" />
      {/* Neck */}
      <rect x="33" y="38" width="14" height="8" rx="3" fill="#4A6A28" />
      {/* Chest */}
      <rect x="21" y="46" width="38" height="38" rx="5" fill="#4A6A28" />
      {/* Fur shoulder pieces */}
      <ellipse cx="20" cy="52" rx="12" ry="9" fill="#6B2208" />
      <ellipse cx="60" cy="52" rx="12" ry="9" fill="#6B2208" />
      {/* Chest wounds/scars */}
      <path d="M 28 54 L 34 58 M 30 64 L 38 60" stroke="#6B1010" strokeWidth="1.5" strokeLinecap="round" />
      {/* Belt */}
      <rect x="20" y="82" width="40" height="7" rx="3" fill="#3C1808" />
      {/* Legs */}
      <rect x="25" y="88" width="13" height="28" rx="4" fill="#4A6A28" />
      <rect x="42" y="88" width="13" height="28" rx="4" fill="#4A6A28" />
      <rect x="23" y="114" width="17" height="5" rx="2" fill="#2A1008" />
      <rect x="40" y="114" width="17" height="5" rx="2" fill="#2A1008" />
      {/* Both arms — dual wielding */}
      <rect x="9" y="46" width="12" height="28" rx="4" fill="#4A6A28" />
      <rect x="59" y="46" width="12" height="28" rx="4" fill="#4A6A28" />
      {/* Left axe */}
      <rect x="2" y="28" width="4" height="44" rx="2" fill="#6B3A10" />
      <path d="M 0 30 Q -4 36 -4 42 Q -4 48 0 52 L 6 46 Q 8 42 8 40 Q 8 36 6 32 Z" fill="#9898B0" />
      {/* Right axe */}
      <rect x="74" y="28" width="4" height="44" rx="2" fill="#6B3A10" />
      <path d="M 80 30 Q 84 36 84 42 Q 84 48 80 52 L 74 46 Q 72 42 72 40 Q 72 36 74 32 Z" fill="#9898B0" />
    </>
  );
}

function Champion() {
  return (
    <>
      {/* Massive red cape */}
      <path d="M 25 46 Q 5 68 8 100 L 72 100 Q 75 68 55 46 Z" fill="#7A1010" opacity="0.9" />
      {/* Full plate helmet */}
      <ellipse cx="40" cy="22" rx="20" ry="21" fill="#5A5A6A" />
      <ellipse cx="35" cy="15" rx="8" ry="7" fill="#6A6A7A" opacity="0.4" />
      {/* Crown */}
      <path d="M 22 12 L 22 20 L 27 16 L 32 20 L 40 14 L 48 20 L 53 16 L 58 20 L 58 12 Z" fill="#D4AF37" />
      {[27,40,53].map((x,i) => (
        <circle key={i} cx={x} cy={i === 1 ? 12 : 14} r="3" fill="#DC2020" />
      ))}
      <rect x="20" y="29" width="40" height="6" rx="2" fill="#4A4A5A" />
      <rect x="20" y="26" width="11" height="18" rx="3" fill="#3A3A4A" />
      <rect x="49" y="26" width="11" height="18" rx="3" fill="#3A3A4A" />
      <rect x="24" y="33" width="32" height="5" rx="2" fill="#3A3A4A" />
      {/* Face visor */}
      <rect x="29" y="30" width="22" height="14" rx="3" fill="#A06030" />
      <rect x="30" y="31" width="20" height="3" rx="1" fill="#2A2A3A" />
      <circle cx="36" cy="39" r="3" fill="#1A0804" />
      <circle cx="44" cy="39" r="3" fill="#1A0804" />
      {/* Neck */}
      <rect x="35" y="43" width="10" height="7" rx="2" fill="#5A5A6A" />
      {/* Massive pauldrons */}
      <ellipse cx="22" cy="52" rx="13" ry="9" fill="#4A4A5A" />
      <ellipse cx="58" cy="52" rx="13" ry="9" fill="#4A4A5A" />
      {[18,24,30].map((x,i) => <circle key={i} cx={x} cy={50+i*2} r="1.5" fill="#D4AF37" />)}
      {[50,56,62].map((x,i) => <circle key={i} cx={x} cy={50+i*2} r="1.5" fill="#D4AF37" />)}
      {/* Torso — plate armor */}
      <rect x="23" y="50" width="34" height="34" rx="6" fill="#4A4A5A" />
      <line x1="23" y1="58" x2="57" y2="58" stroke="#3A3A4A" strokeWidth="2" />
      <line x1="23" y1="66" x2="57" y2="66" stroke="#3A3A4A" strokeWidth="2" />
      <line x1="23" y1="74" x2="57" y2="74" stroke="#3A3A4A" strokeWidth="2" />
      <line x1="40" y1="50" x2="40" y2="84" stroke="#3A3A4A" strokeWidth="1.5" />
      {/* Gold trim */}
      <rect x="23" y="50" width="34" height="34" rx="6" fill="none" stroke="#D4AF37" strokeWidth="1.5" />
      {/* Chest emblem */}
      <path d="M 40 57 L 37 62 L 32 62 L 36 65 L 34 70 L 40 67 L 46 70 L 44 65 L 48 62 L 43 62 Z" fill="#D4AF37" />
      {/* Belt */}
      <rect x="22" y="82" width="36" height="7" rx="3" fill="#3A3A4A" />
      {/* Legs — plate */}
      <rect x="27" y="88" width="13" height="28" rx="4" fill="#4A4A5A" />
      <rect x="40" y="88" width="13" height="28" rx="4" fill="#4A4A5A" />
      <rect x="26" y="113" width="15" height="5" rx="2" fill="#3A3A4A" />
      <rect x="39" y="113" width="15" height="5" rx="2" fill="#3A3A4A" />
      {/* Arms */}
      <rect x="11" y="50" width="12" height="28" rx="4" fill="#4A4A5A" />
      <rect x="57" y="50" width="12" height="28" rx="4" fill="#4A4A5A" />
      {/* Greatsword — two handed, huge */}
      <rect x="64" y="10" width="7" height="60" rx="3" fill="#9898B0" />
      <polygon points="64,10 71,10 67.5,2" fill="#B0B0C8" />
      <path d="M 63 10 L 71 10 L 70 14 L 65 14 Z" fill="#B0B0C8" opacity="0.5" />
      <rect x="60" y="62" width="18" height="5" rx="2" fill="#D4AF37" />
      <rect x="65" y="67" width="7" height="16" rx="2" fill="#5C3A10" />
      <circle cx="68.5" cy="84" r="5" fill="#D4AF37" />
      <circle cx="68.5" cy="84" r="3" fill="#C8A030" />
    </>
  );
}

function DarkKnight() {
  return (
    <>
      {/* Dark shadow aura */}
      {[0,1,2].map(i => (
        <ellipse key={i} cx="40" cy="80" rx={30+i*8} ry={20+i*5}
          fill="#3A1A5A" opacity={0.15-i*0.04} />
      ))}
      {/* Black cape */}
      <path d="M 28 46 Q 8 66 10 96 L 70 96 Q 72 66 52 46 Z" fill="#1A0A2A" opacity="0.95" />
      {/* Dark helmet */}
      <ellipse cx="40" cy="22" rx="18" ry="20" fill="#1A1A2A" />
      <ellipse cx="35" cy="16" rx="7" ry="6" fill="#2A2A3A" opacity="0.4" />
      <rect x="22" y="30" width="36" height="6" rx="2" fill="#0A0A18" />
      <rect x="22" y="28" width="9" height="16" rx="3" fill="#0A0A18" />
      <rect x="49" y="28" width="9" height="16" rx="3" fill="#0A0A18" />
      <rect x="26" y="34" width="28" height="5" rx="2" fill="#0A0A18" />
      {/* Purple plume */}
      <path d="M 40 2 C 35 5 32 11 35 17 C 37 13 39 9 40 9 C 41 9 43 13 45 17 C 48 11 45 5 40 2 Z" fill="#6A2A9A" />
      <rect x="38.5" y="6" width="3" height="14" rx="1.5" fill="#7A3AAA" />
      <rect x="36" y="17" width="8" height="6" rx="2" fill="#6A2A9A" />
      {/* Glowing eyes */}
      <circle cx="36" cy="37" r="4" fill="#3A1A5A" />
      <circle cx="44" cy="37" r="4" fill="#3A1A5A" />
      <circle cx="36" cy="37" r="2.5" fill="#9B60DC" />
      <circle cx="44" cy="37" r="2.5" fill="#9B60DC" />
      <circle cx="36.5" cy="36.5" r="1" fill="#C084FC" />
      <circle cx="44.5" cy="36.5" r="1" fill="#C084FC" />
      {/* Neck */}
      <rect x="36" y="43" width="8" height="7" rx="2" fill="#1A1A2A" />
      {/* Dark pauldrons */}
      <ellipse cx="24" cy="52" rx="10" ry="7" fill="#1A1A2A" />
      <ellipse cx="56" cy="52" rx="10" ry="7" fill="#1A1A2A" />
      {/* Purple trim */}
      <path d="M 15 52 Q 24 44 33 52 Q 24 60 15 52 Z" fill="#6A2A9A" opacity="0.6" />
      <path d="M 47 52 Q 56 44 65 52 Q 56 60 47 52 Z" fill="#6A2A9A" opacity="0.6" />
      {/* Torso */}
      <rect x="25" y="50" width="30" height="32" rx="5" fill="#1A1A2A" />
      <line x1="25" y1="57" x2="55" y2="57" stroke="#6A2A9A" strokeWidth="1.5" />
      <line x1="25" y1="64" x2="55" y2="64" stroke="#6A2A9A" strokeWidth="1.5" />
      <line x1="25" y1="71" x2="55" y2="71" stroke="#6A2A9A" strokeWidth="1.5" />
      <line x1="40" y1="50" x2="40" y2="82" stroke="#6A2A9A" strokeWidth="1" />
      <rect x="25" y="50" width="30" height="32" rx="5" fill="none" stroke="#6A2A9A" strokeWidth="1" />
      {/* Chest void rune */}
      <path d="M 40 56 L 37 63 L 43 63 Z M 37 59 L 43 59 M 40 56 L 40 70" stroke="#9B60DC" strokeWidth="1" fill="none" />
      {/* Belt */}
      <rect x="23" y="80" width="34" height="7" rx="3" fill="#0A0A18" />
      {[0,1,2,3,4,5,6,7].map(i => (
        <circle key={i} cx={25.5 + i * 4} cy={83.5} r="1.5" fill="#6A2A9A" />
      ))}
      {/* Pteryges */}
      {[0,1,2,3,4,5,6,7].map(i => (
        <rect key={i} x={23 + i * 4} y="86" width="3.5" height="14" rx="2"
          fill={i % 2 === 0 ? '#0A0A20' : '#18183A'} />
      ))}
      {/* Legs */}
      <rect x="28" y="99" width="11" height="22" rx="3" fill="#1A1A2A" />
      <rect x="41" y="99" width="11" height="22" rx="3" fill="#1A1A2A" />
      <rect x="27" y="108" width="13" height="12" rx="3" fill="#0A0A18" />
      <rect x="40" y="108" width="13" height="12" rx="3" fill="#0A0A18" />
      <rect x="24" y="119" width="18" height="5" rx="2" fill="#0A0A14" />
      <rect x="38" y="119" width="18" height="5" rx="2" fill="#0A0A14" />
      {/* Shield arm */}
      <rect x="14" y="48" width="10" height="24" rx="4" fill="#1A1A2A" />
      {/* Dark shield */}
      <rect x="3" y="44" width="20" height="36" rx="5" fill="#0A0A18" />
      <rect x="3" y="44" width="20" height="36" rx="5" fill="none" stroke="#6A2A9A" strokeWidth="1.5" />
      <circle cx="13" cy="62" r="5" fill="#3A1A5A" />
      <circle cx="13" cy="62" r="3" fill="#9B60DC" />
      {/* Sword arm */}
      <rect x="57" y="48" width="10" height="24" rx="4" fill="#1A1A2A" />
      {/* Corrupt blade — dark with purple glow */}
      <rect x="65" y="26" width="6" height="30" rx="2" fill="#2A1A3A" />
      <line x1="68" y1="26" x2="68" y2="56" stroke="#9B60DC" strokeWidth="1.5" opacity="0.8" />
      <polygon points="65,26 71,26 68,20" fill="#2A1A3A" />
      <line x1="66" y1="22" x2="70" y2="26" stroke="#9B60DC" strokeWidth="1" opacity="0.8" />
      <rect x="62" y="54" width="14" height="4" rx="2" fill="#6A2A9A" />
      <rect x="65" y="58" width="6" height="13" rx="2" fill="#0A0A18" />
      <circle cx="68" cy="72" r="4" fill="#3A1A5A" />
      <circle cx="68" cy="72" r="2.5" fill="#9B60DC" />
    </>
  );
}

function ShadowMage() {
  return (
    <>
      {/* Magical particles */}
      {[[15,30],[65,40],[20,70],[60,80],[10,90],[70,60]].map(([x,y],i) => (
        <circle key={i} cx={x} cy={y} r={2+i%2} fill="#8B60DC" opacity={0.3+i*0.06} />
      ))}
      {/* Dark robes — tall, flowing */}
      <path d="M 32 50 Q 20 70 18 110 L 62 110 Q 60 70 48 50 Z" fill="#1A0A2A" />
      <path d="M 24 70 Q 12 85 10 115 L 24 115 Q 22 90 30 70 Z" fill="#180828" opacity="0.8" />
      <path d="M 56 70 Q 68 85 70 115 L 56 115 Q 58 90 50 70 Z" fill="#180828" opacity="0.8" />
      {/* Hood */}
      <ellipse cx="40" cy="22" rx="18" ry="19" fill="#1A0A2A" />
      <path d="M 22 22 Q 22 40 32 42 L 48 42 Q 58 40 58 22 Z" fill="#0A0418" />
      {/* Cowl shadow on face */}
      <path d="M 26 28 Q 24 40 30 44 L 50 44 Q 56 40 54 28 Q 48 36 40 36 Q 32 36 26 28 Z" fill="#0F0820" />
      {/* Gaunt pale face */}
      <ellipse cx="40" cy="33" rx="10" ry="11" fill="#D4C0A0" opacity="0.7" />
      {/* Hollow eyes glowing */}
      <circle cx="36" cy="31" r="4" fill="#0A0418" />
      <circle cx="44" cy="31" r="4" fill="#0A0418" />
      <circle cx="36" cy="31" r="2.5" fill="#7A3AAA" />
      <circle cx="44" cy="31" r="2.5" fill="#7A3AAA" />
      <circle cx="36.5" cy="30.5" r="1.2" fill="#C084FC" />
      <circle cx="44.5" cy="30.5" r="1.2" fill="#C084FC" />
      {/* Robe belt/sash */}
      <rect x="27" y="72" width="26" height="5" rx="2" fill="#4A2A6A" />
      {/* Robes vertical folds */}
      {[30,36,42,48,54].map((x,i) => (
        <line key={i} x1={x} y1="50" x2={x-2} y2="110" stroke="#0A0418" strokeWidth="1" opacity="0.5" />
      ))}
      {/* Slim legs under robe */}
      <rect x="32" y="105" width="8" height="16" rx="3" fill="#1A0A2A" />
      <rect x="40" y="105" width="8" height="16" rx="3" fill="#1A0A2A" />
      <rect x="30" y="119" width="12" height="4" rx="2" fill="#0A0414" />
      <rect x="38" y="119" width="12" height="4" rx="2" fill="#0A0414" />
      {/* Sleeves */}
      <path d="M 24 52 Q 12 60 8 80 L 16 80 Q 18 64 26 56 Z" fill="#1A0A2A" />
      <path d="M 56 52 Q 68 60 72 80 L 64 80 Q 62 64 54 56 Z" fill="#1A0A2A" />
      {/* Hands */}
      <ellipse cx="13" cy="80" rx="4" ry="5" fill="#D4C0A0" opacity="0.6" />
      <ellipse cx="67" cy="80" rx="4" ry="5" fill="#D4C0A0" opacity="0.6" />
      {/* Staff — right hand */}
      <rect x="68" y="10" width="5" height="80" rx="2" fill="#3A2808" />
      {/* Staff orb */}
      <circle cx="70" cy="9" r="10" fill="#1A0A2A" />
      <circle cx="70" cy="9" r="8" fill="#3A1A5A" />
      <circle cx="70" cy="9" r="5" fill="#7A3AAA" />
      <circle cx="70" cy="9" r="3" fill="#9B60DC" />
      <circle cx="70" cy="9" r="1.5" fill="#C084FC" />
      {/* Staff glow rays */}
      {[0,60,120,180,240,300].map((deg,i) => {
        const rad = (deg * Math.PI) / 180;
        return <line key={i} x1={70} y1={9}
          x2={70 + Math.cos(rad)*16} y2={9 + Math.sin(rad)*16}
          stroke="#7A3AAA" strokeWidth="1" opacity="0.4" />;
      })}
      {/* Left hand spell effect */}
      <circle cx="13" cy="80" r="8" fill="#3A1A5A" opacity="0.5" />
      <circle cx="13" cy="80" r="5" fill="#7A3AAA" opacity="0.4" />
    </>
  );
}

function DemonLord() {
  return (
    <>
      {/* Hellfire aura */}
      {[0,1,2,3].map(i => (
        <ellipse key={i} cx="40" cy="90" rx={28+i*10} ry={15+i*6}
          fill="#DC2020" opacity={0.08-i*0.015} />
      ))}
      {/* Wings */}
      <path d="M 22 50 Q 0 30 -5 10 Q 5 20 10 40 Q 14 55 22 58 Z" fill="#1A0A0A" />
      <path d="M 22 50 Q -2 45 -8 55 Q 0 50 10 56 Q 16 60 22 60 Z" fill="#2A0A0A" />
      <path d="M 58 50 Q 80 30 85 10 Q 75 20 70 40 Q 66 55 58 58 Z" fill="#1A0A0A" />
      <path d="M 58 50 Q 82 45 88 55 Q 80 50 70 56 Q 64 60 58 60 Z" fill="#2A0A0A" />
      {/* Body */}
      <path d="M 24 50 Q 8 70 10 100 L 70 100 Q 72 70 56 50 Z" fill="#3A0808" opacity="0.9" />
      {/* Head */}
      <ellipse cx="40" cy="22" rx="20" ry="21" fill="#5A0A0A" />
      {/* Horns */}
      <path d="M 25 14 Q 16 -2 20 -8 Q 22 4 28 12" fill="#1A0404" />
      <path d="M 55 14 Q 64 -2 60 -8 Q 58 4 52 12" fill="#1A0404" />
      <line x1="25" y1="14" x2="20" y2="-8" stroke="#2A0A08" strokeWidth="3" />
      <line x1="55" y1="14" x2="60" y2="-8" stroke="#2A0A08" strokeWidth="3" />
      {/* Face */}
      <ellipse cx="40" cy="25" rx="15" ry="16" fill="#6A0A0A" />
      {/* Demonic eyes */}
      <ellipse cx="35" cy="22" rx="5" ry="4" fill="#FF4500" />
      <ellipse cx="45" cy="22" rx="5" ry="4" fill="#FF4500" />
      <circle cx="35" cy="22" r="2.5" fill="#1A0804" />
      <circle cx="45" cy="22" r="2.5" fill="#1A0804" />
      {/* Pupils — slit like a demon */}
      <rect x="34" y="20" width="2" height="4" rx="1" fill="#FF6030" />
      <rect x="44" y="20" width="2" height="4" rx="1" fill="#FF6030" />
      {/* Jagged teeth */}
      <path d="M 32 33 L 34 38 L 36 33 L 38 38 L 40 33 L 42 38 L 44 33 L 46 38 L 48 33" stroke="#E8D5B0" strokeWidth="1.5" fill="none" strokeLinejoin="round" />
      {/* Nose */}
      <path d="M 38 28 L 36 32 L 40 33 L 44 32 L 42 28" fill="#5A0808" />
      {/* Neck */}
      <rect x="33" y="40" width="14" height="10" rx="4" fill="#5A0A0A" />
      {/* Dark plate chest */}
      <rect x="22" y="50" width="36" height="36" rx="6" fill="#2A0808" />
      <rect x="22" y="50" width="36" height="36" rx="6" fill="none" stroke="#8B1A1A" strokeWidth="1.5" />
      {/* Hellfire runes */}
      <path d="M 32 56 L 28 62 L 34 62 L 30 70" stroke="#FF4500" strokeWidth="2" fill="none" strokeLinecap="round" />
      <path d="M 48 56 L 52 62 L 46 62 L 50 70" stroke="#FF4500" strokeWidth="2" fill="none" strokeLinecap="round" />
      <circle cx="40" cy="63" r="5" fill="#3A0808" />
      <circle cx="40" cy="63" r="3" fill="#8B1A1A" />
      <circle cx="40" cy="63" r="1.5" fill="#FF4500" />
      {/* Shoulder spikes */}
      {[-4,-2,0,2,4].map((x,i) => (
        <path key={i} d={`M ${18+i*3} 52 L ${16+i*3} 44 L ${21+i*3} 52`} fill="#1A0404" />
      ))}
      {[-4,-2,0,2,4].map((x,i) => (
        <path key={i} d={`M ${62-i*3} 52 L ${64-i*3} 44 L ${59-i*3} 52`} fill="#1A0404" />
      ))}
      {/* Arms */}
      <rect x="10" y="52" width="13" height="28" rx="4" fill="#5A0A0A" />
      <rect x="57" y="52" width="13" height="28" rx="4" fill="#5A0A0A" />
      {/* Claws */}
      {[8,10,12,14,16].map((x,i) => <line key={i} x1={x} y1="82" x2={x-2+i*0.5} y2="90" stroke="#1A0404" strokeWidth="2" strokeLinecap="round" />)}
      {[64,66,68,70,72].map((x,i) => <line key={i} x1={x} y1="82" x2={x+2-i*0.5} y2="90" stroke="#1A0404" strokeWidth="2" strokeLinecap="round" />)}
      {/* Belt */}
      <rect x="21" y="84" width="38" height="7" rx="3" fill="#1A0404" />
      {/* Legs */}
      <rect x="26" y="90" width="14" height="26" rx="4" fill="#3A0808" />
      <rect x="40" y="90" width="14" height="26" rx="4" fill="#3A0808" />
      <rect x="24" y="114" width="18" height="5" rx="2" fill="#1A0404" />
      <rect x="38" y="114" width="18" height="5" rx="2" fill="#1A0404" />
      {/* Hellfire feet */}
      {[25,28,31,34,37].map((x,i) => (
        <circle key={i} cx={x} cy={119} r="1.5" fill="#FF4500" opacity={0.5+i*0.08} />
      ))}
      {[41,44,47,50,53].map((x,i) => (
        <circle key={i} cx={x} cy={119} r="1.5" fill="#FF4500" opacity={0.5+i*0.08} />
      ))}
    </>
  );
}

const ENEMY_SHAPES = {
  'Human Soldier':  Legionnaire,
  'Bandit Captain': Mercenary,
  'Orc Warrior':    Barbarian,
  'Orc Berserker':  Berserker,
  'Orc Warchief':   Champion,
  'Dark Knight':    DarkKnight,
  'Shadow Mage':    ShadowMage,
  'Demon Lord':     DemonLord,
};

export function EnemySprite({ name, anim = 'idle', size = 160, isBoss = false }) {
  const Shape = ENEMY_SHAPES[name] || Legionnaire;
  const bossGlow = isBoss ? '0 0 20px rgba(220,32,32,0.5)' : 'none';

  return (
    <motion.svg
      viewBox="-10 0 100 124"
      width={size * 0.75}
      height={size}
      style={{
        overflow: 'visible',
        display: 'block',
        transform: 'scaleX(-1)',
        filter: anim === 'hit'
          ? 'brightness(2.5) saturate(0)'
          : isBoss ? 'drop-shadow(0 0 8px #DC2020)' : 'none',
      }}
      variants={variants}
      animate={anim}
    >
      <Shape />
    </motion.svg>
  );
}
