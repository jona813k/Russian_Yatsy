# Russian Yatzy RPG

A roguelike RPG where dice rolling drives character progression. Between each fight you play a solo game of Russian Yatzy to upgrade your stats. The numbers you collect determine what kind of fighter you become.

---

## Run Structure

```
Pre-game Forge
    └── Level 1: 2 normal enemies + boss  →  6 upgrade turns
            └── Shop  →  Forge I
    └── Level 2: 2 normal enemies + boss  →  5 upgrade turns
            └── Shop  →  Forge II
    └── Level 3: 2 normal enemies + boss  →  4 upgrade turns
                └── Victory
```

Each level you get fewer upgrade turns, so early choices matter.

---

## The Yatzy Game (Upgrade Phase)

### Goal
Collect dice showing each number 1–12. You need **6 collected** per number to fully max it out (the default; some specialisations change this).

### Dice Pool
You start with **6 standard d6** dice (faces 1–6). The Forge lets you modify this pool.

### How a Turn Works

1. **Roll all dice in hand.**
2. **Pick a number** — any number you can make from the current roll that isn't already maxed.
   - **Singles (1–6):** any die face-matching the number counts.
   - **Pairs (7–12):** any two dice that sum to the number count as one collection unit.
3. **All matching dice are automatically collected.** The rest re-roll.
4. Repeat from step 3 until no dice remain *or* the new roll has no match for your chosen number — in that case the turn ends.
5. **Bonus turn:** if you use every die in hand without the turn ending, you get a free extra turn.
6. **Completed number:** collecting the 6th (or final) unit of a number returns all dice to your hand and lets you pick a new number immediately.

### Legal Moves
- You can only pick a number you can currently make from the dice showing.
- You cannot pick a number you've already maxed for this upgrade phase.
- If the roll has no valid number at all, the turn is skipped automatically.

---

## Stats (Numbers → Upgrades)

Each number maps to a specific stat. Each collected die gives a small bonus; reaching the **threshold** (4 collected by default, 3 for numbers 10–12) gives an extra bonus on top.

| # | Stat | Per die | Threshold bonus | Notes |
|---|------|---------|-----------------|-------|
| 1 | Attack Speed | +0.025 attacks/s | +0.025 | Capped at 5.0 attacks/s |
| 2 | Attack Damage | +1 | +1 | Flat damage per hit |
| 3 | Crit Chance | +1% | +1% | 2× damage on crit |
| 4 | Armor | +2% | +2% | Reduces incoming damage |
| 5 | Max HP | +5 | +5 | Also heals you |
| 6 | Research | special | — | 4 collected → +1 item slot; 6 → +1 free item |
| 7 | Gold | +20g | +20g | Carried into shop |
| 8 | Summon | +1 level | +1 level | Spawns a creature that fights for you |
| 9 | Spell | +1 level | +1 level | Periodic magic nuke |
| 10 | Block | +2% | +2% | Chance to completely negate a hit |
| 11 | Lifesteal | +2% | +2% | Heal a % of damage dealt |
| 12 | Dark | +1 level | +1 level | Ramp-up damage multiplier on long fights |

### Dark multiplier ramp-up
Dark scales with *hits landed* in a fight (not time). The more dark levels, the earlier and stronger the bonus kicks in:
- Early hits: +(10 + dark_level)%
- Mid hits: +(25 + dark_level)%
- Late hits: +(50 + dark_level)%

---

## Combat

Combat is simulated server-side and returned as an event list the frontend animates.

### Player Stats at Start
- 100 HP, 8 attack damage, 0.5 attacks/s, 1% crit, 5% armor, 3% block — all modified by upgrades.

### Combat Loop (event-driven, shared timeline)
Player, summon (if active), and enemies all act on independent timers based on attack speed. The fight plays out tick-by-tick until someone dies.

- **Attack:** `damage = attack_dmg × (1 - enemy_armor)`, crits deal 2× (or 2.25× with upgrade).
- **Block:** a successful block negates all damage from that hit.
- **Lifesteal:** heals player for `lifesteal%` of damage dealt.
- **Spell:** fires every few seconds, scales with spell_level. Can burn, slow, or heal summon depending on items.
- **Summon:** fights alongside player. Tier scales with summon_level (see below).

### Summon Tiers

| Min level | Name | Attack | HP | Notes |
|-----------|------|--------|----|-------|
| 1 | Imp | 1 | 10 | — |
| 5 | Wolf | 3 | 25 | — |
| 10 | Orc | 6 | 50 | Enrages below 25% HP |
| 15 | Skeleton | 11 | 100 | +10% spell vamp, enrages |
| 20 | Dragon | 18 | 200 | +10% spell vamp, 5% dragon aura, enrages |

### Enemies

**Level 1**
| Enemy | HP | Attack | Speed | Boss |
|-------|-----|--------|-------|------|
| Human Soldier | 100 | 4 | 1.5/s | No |
| Human Soldier | 100 | 4 | 1.5/s | No |
| Bandit Captain | 600 | 8 | 2.0/s | Yes |

**Level 2**
| Enemy | HP | Attack | Speed | Notes | Boss |
|-------|-----|--------|-------|-------|------|
| Orc Warrior | 350 | 14 | 2.0/s | 10% armor | No |
| Orc Berserker | 300 | 18 | 1.5/s | 10% armor, regenerates HP | No |
| Orc Warchief | 1200 | 16 | 2.0/s | — | Yes |

**Level 3**
| Enemy | HP | Attack | Speed | Notes | Boss |
|-------|-----|--------|-------|-------|------|
| Dark Knight | 600 | 26 | 2.0/s | 20% armor | No |
| Shadow Mage | 500 | 28 | 1.5/s | 20% armor, 60% lifesteal | No |
| Demon Lord | 2000 | 30 | 1.8/s | — | Yes |

---

## Pre-game Forge (Before Level 1)

Pick one specialisation that reshapes how stats scale for the entire run. Some stats are made easier or harder to max; some can be removed entirely (dice of that face still work in pairs).

| Spec | Name | Effect |
|------|------|--------|
| `spec_a` | Standard | No changes. All stats upgrade normally (6 per number). |
| `spec_b` | Aggressor | Attack Speed, Damage, Crit max at 4. HP and Armor require 7. |
| `spec_c` | Mage | Spell and Summon max at 5. Attack Speed, Damage, Crit require 7. |

**Rule for removed stats:** The number card stays visible on the upgrade board (greyed out). Dice of that face value are not wasted — they can still contribute as one half of a pair combination.

---

## Forge I (After Level 1 Boss) — Dice Pool

| Option | Effect |
|--------|--------|
| Add d12 | +1 twelve-sided die permanently. Can show 1–12, opening access to high numbers. |
| Add d3 | +1 three-sided die permanently. Always shows 1–3 — reliable for low stats. |
| Remove a Die | Drop one d6 permanently. 5 dice total; less noise, more control. |

---

## Forge II (After Level 2 Boss) — Dice Odds

| Option | Effect |
|--------|--------|
| Load: High Numbers | All dice weighted 3× toward faces 4–6 (1/12 each for 1–3, 3/12 each for 4–6). |
| Free Reroll | Once per upgrade turn, reroll all dice before selecting. Costs no turn. |
| Risky Die | Replace one d6 with faces 1, 2, 3, 10, 11, 12. High ceiling for hard numbers. |

---

## Shop

Appears before each boss fight. Costs 100g each. You need item slots (from Research / stat 6) to carry items.

### Tier 1 items (pre-boss 1)

| Item | Effect |
|------|--------|
| Whetstone | +5 permanent attack damage |
| Fury Talisman | Every 3rd attack deals +20 bonus damage |
| Sharpshooter Lens | Crits deal 2.25× instead of 2× |
| Iron Plate | +10% permanent armor |
| Bulwark Rune | Armor upgrades also give HP (1% armor → 2 HP) |
| Oracle Lens | Future shops/forges each get 1 free reroll |
| Merchant Badge | All item costs -20% |
| Gold Vein | Gold upgrades give +5 extra gold each |
| Bounty Token | +50g each time you kill an enemy |
| Soul Tether | Summon survives fights; gains 1 level per fight won |
| Thorned Buckler | Blocked damage is reflected back to the attacker |
| Guardian's Edge | Blocking gives +5 attack damage for 2s |
| Siphon Stone | Lifesteal also applies to spell damage |
| Vampiric Pendant | +5% permanent lifesteal |
| Bloodbond Hilt | Heal 3 HP on every attack hit |

### Tier 2 items (pre-boss 2 and 3)

| Item | Effect |
|------|--------|
| Finishing Blade | +15 attack damage when enemy is below 20% HP |
| Armor Shredder | Your attacks ignore all enemy armor |
| Berserker Band | +20% attack speed when below 50% HP |
| Swiftcrit Rune | Future crit upgrades convert to attack speed instead |
| Frostcrit Gem | Crits slow enemy attack speed -50% for 2s |
| Crimson Fang | Crits heal for the bonus crit damage; disables normal lifesteal |
| Arcane Dissolution | Remove all your armor; gain that much as spell levels (5% → 1 level) |
| Bloodprice Sigil | Gain attack equal to 5% of your max HP |
| Ironflesh Pact | Double max HP; -30% armor |
| Scholar's Tome | +2 item slots and +2 free item credits |
| Summoner's Codex | Upgrade summon: enrage at 35% HP, 15% spell vamp, 10% dragon aura |
| Flame Rune | Spell burns for 10% of spell damage/s over 3s |
| Frost Staff | Spell slows enemy attack speed -50% for 3s |
| Life Conduit | Spell heals your summon instead of dealing damage |
| Shield Conversion | Convert all armor to block (1% armor → 0.5% block) |

---

## How to Run

```bash
# Backend
pip install fastapi uvicorn
python -m uvicorn web.backend.main:app --reload --port 8000

# Frontend
cd web/frontend
npm install
npm run dev        # http://localhost:5173
```

---

## Balance Notes

Open issues to revisit:

- **Stat 4 (Armor)** is strictly better than Stat 10 (Block) right now. Same per_die, easier to roll singles, no late-game ramp. Block needs a scaling advantage.
- **Stat 12 (Dark)** level 1 carries most fights; extra levels feel weak early but the boss forces it. The ramp-up thresholds could scale more aggressively at low levels.
- **Level 2 enemies** feel too easy after a good upgrade phase. Orc Warrior and Berserker HP/attack could be raised further.
