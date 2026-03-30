# Russian Yatzy RPG — Game Design Notes

A living document for balance tweaks, forge ideas, and item ideas.
Edit freely — add rows, mark status, cross things out.

---

## Balance Notes

### Stats to change

| # | Stat | Issue | Proposed fix |
|---|------|--------|--------------|
| 1 | Attack Speed | Threshold bonus at 4 is too strong — easy to farm | Raise threshold_at from 4 → 5 (harder to trigger) |
| 4 | Armor | Strictly better than Block (10) — same per_die, easier to roll, no late-game scaling | Lower per_die slightly OR give Block a scaling multiplier at high counts |
| 10 | Block | Weaker and harder to reach than Armor all game | Raise threshold bonus: 0.01 → 0.02 at threshold, and/or lower threshold_at to 2 so it activates earlier |
| 12 | Dark | Level 1 is enough for all fights; extra levels feel wasted but bosses require it | Cap or slow down the hit_count multiplier early; make each dark_level add more at high hit counts |

### Enemy strength

| Level | Enemy | Issue | Proposed fix |
|-------|-------|--------|--------------|
| 1 | Soldiers + Bandit Captain | Feel right | Keep as-is |
| 2 | Orc Warrior (200 HP / 10 atk) | Too easy — player is overleveled by now | Raise to ~350 HP / 14 atk |
| 2 | Orc Berserker (180 HP / 14 atk) | Same — trivial | Raise to ~300 HP / 18 atk |
| 2 | Orc Warchief boss | OK | Keep or minor tweak |
| 3 | Dark Knight (350 HP / 20 atk) | Too easy | Raise to ~600 HP / 26 atk |
| 3 | Shadow Mage (280 HP / 24 atk) | Too easy | Raise to ~500 HP / 28 atk, maybe add a spell mechanic |
| 3 | Demon Lord boss | OK | Keep — the spike is intentional |

---

## Forge Ideas

Three forge tiers. Each offers exactly 3 choices (pick 1).

- **Pre-game Forge** — picked before the first enemy. Alters the *upgrade table* (thresholds and per_die values).
- **Forge I** — after Level 1 boss. Alters the *dice pool* (add/remove dice).
- **Forge II** — after Level 2 boss. Alters the *dice odds* (how dice roll).

---

### Pre-game Forge (alters upgrade table)

Each stat normally requires **6 collected dice** to fully complete.
This forge raises or lowers that target for specific stats, or removes a stat entirely.
- Target **7** → harder to max, less total gain that run
- Target **5** → easier to max, fires earlier in the turn
- **Removed** → you gain zero progress in that stat for the entire run

### Rules for removed stats
- The number card stays visible on the upgrade board — shown greyed out with a cross/strikethrough, never hidden. Removing the box would cause confusion about what the dice can do.
- Dice showing that face value are **not** wasted: they can still combine with other dice to form pair numbers (e.g. a 2 can still pair with a 5 to make 7, even if stat 2 is removed). Single-number selection for that stat is simply disabled.
- Same applies to **completed** stats (6/6 already filled): dice of that face value can still contribute to pair combinations in later turns.

Your three options map directly to your described options:

| ID | Name | Changes | Flavour / build direction | Status |
|----|------|---------|--------------------------|--------|
| `spec_a` | *(name TBD)* | 1 (Spd): target 6→7 · 12 (Dark): target 6→5 · 2 (Dmg): **removed** | Attack Speed is harder to max; Dark comes online faster; you never get Damage — full Dark/magic build | **Implement** |
| `spec_b` | *(name TBD)* | 1 (Spd): target 6→5 · 2 (Dmg): target 6→5 · 3 (Crit): target 6→5 | All three attack stats are easier to complete — pure aggressive build that peaks early | **Implement** |
| `spec_c` | *(name TBD)* | 4 (Armor): **removed** · 5 (HP): **removed** · 1 (Spd): target 6→7 · 2 (Dmg): target 6→7 | No Armor, no HP at all; offense stats are also harder to max — designed to force you into summon/spell/dark | **Implement** |
| *(idea)* | *(name TBD)* | 4 (Armor): target 6→5 · 5 (HP): target 6→5 · 10 (Block): target 6→5 | All three defensive stats are easier to complete — survival-first build | Idea |
| *(idea)* | *(name TBD)* | 7 (Gold): target 6→5 · 8 (Summon): target 6→5 · 9 (Spell): target 6→5 · 6 (Research): target 6→5 | High-numbers build — pair numbers and research all fire earlier | Idea |

---

### Forge I — Dice Pool (after Level 1 boss)

| ID | Name | Effect | Status |
|----|------|--------|--------|
| `add_d12` | Add d12 | +1 twelve-sided die (rolls 1–12). Opens access to numbers 7–12. | **Implemented** |
| `add_d3` | Add d3 | +1 three-sided die (rolls 1–3). Reliable feed for Spd/Dmg/Crit. | **Implemented** |
| `remove_die` | Remove a Die | Remove one d6 permanently (5 dice total). Less noise, more control. | **Implemented** |
| *(idea)* | Twin Die | Duplicate one die you already own (your choice). Doubles down on any path. | Idea |
| *(idea)* | Balanced Die | Add a d6 with faces 2,3,4,4,5,6 (no 1s). Reliable mid-range, never wastes a roll on 1. | Idea |
| *(idea)* | Pair Die | Add a die with faces that always show complementary pairs (1+6, 2+5, 3+4). Each roll feeds both halves of a pair number (7). Dedicated gold/summon fuel. | Idea |
| *(idea)* | Extra d6 | Simply add a standard d6. More dice = more options but also more noise. Straightforward pick for a cautious player. | Idea |

---

### Forge II — Dice Odds (after Level 2 boss)

| ID | Name | Effect | Status |
|----|------|--------|--------|
| `loaded_high` | Load: High Numbers | All dice weighted 3× toward faces 4–6. Great for Armor/HP/Research. | **Implemented** |
| `free_reroll` | Free Reroll | Once per upgrade turn, reroll all dice before selecting — costs no turn. | **Implemented** |
| `risky_die` | Risky Die | Replace one d6 with faces 1,2,3,10,11,12. High ceiling for hard numbers. | **Implemented** |
| *(idea)* | Echo | Once per upgrade phase, completing a number (6/6) gives +1 free toward a second number of your choice. Cross-stat combo enabler. | Idea |
| *(idea)* | Resonance | When you collect a pair sum (7–12), also get +1 toward the smaller component number (e.g. collect 9 via 3+6, also get +1 toward 6). Pairs feel "free". | Idea |
| *(idea)* | Cascade | After fully completing any number in an upgrade turn, one free extra die is added to your next roll (resets each turn). Snowball finisher. | Idea |
| *(idea)* | Lucky Die | One of your dice has a 50% chance to count as 2 when collected. High ceiling for runs that need to cross thresholds. | Idea |

---

## Shop Items

Bought between fights when you have gold + item slots. Two fixed forges already gate items behind slots.

| ID | Name | Cost | Effect | Status |
|----|------|------|--------|--------|
| `vampiric_tome` | Vampiric Tome | 100 | Spells heal you for 30% of their damage. | **Implemented** |
| `thorns_vest` | Thorns Vest | 60 | When hit, deal 3 damage back. | **Implemented** |
| `battle_drum` | Battle Drum | 80 | Summon attacks 25% faster. | **Implemented** |
| `focusing_lens` | Focusing Lens | 120 | Spell cooldown 4s → 2.5s. | **Implemented** |
| `lucky_charm` | Lucky Charm | 70 | +5% crit chance in combat. | **Implemented** |
| `iron_gauntlets` | Iron Gauntlets | 80 | +8 attack damage in combat. | **Implemented** |
| `mana_surge` | Mana Surge | 90 | Spell deals +10 bonus damage per cast. | **Implemented** |
| `ancient_shield` | Ancient Shield | 70 | +10% armor in combat. | **Implemented** |
| `battle_horn` | Battle Horn | 100 | Attack cooldown -0.25s. | **Implemented** |
| `phoenix_feather` | Phoenix Feather | 180 | Once per fight, survive a killing blow at 1 HP. | **Implemented** |
| *(idea)* | Dark Codex | 110 | +2 dark level permanently. Great if you missed dark in upgrades. | Idea |
| *(idea)* | Block Talisman | 80 | +8% block chance in combat. Pairs well with spec_dark where armor is weak. | Idea |
| *(idea)* | Summoner's Idol | 90 | +3 summon level permanently (outside upgrade phase). | Idea |
| *(idea)* | Spell Amplifier | 100 | Spell crits are possible — 15% chance to double spell damage. | Idea |
| *(idea)* | Second Wind | 130 | At the start of each combat, heal 20% of missing HP. | Idea |
| *(idea)* | Whetstone | 50 | Cheap. +5 attack damage permanently. Good early-game top-up if you missed Dmg upgrades. | Idea |
| *(idea)* | Berserker Amulet | 110 | Below 30% HP, attack cooldown is halved. High-risk high-reward finisher. | Idea |
| *(idea)* | Cursed Blade | 70 | +15 attack damage BUT you take 2 extra damage per enemy hit. Risk/reward option. | Idea |
| *(idea)* | Mirror Shield | 150 | Block reflects 100% of blocked damage back to the attacker (instead of just negating it). Synergises with high block_chance builds. | Idea |
| *(idea)* | Momentum Ring | 120 | Each consecutive hit you land (no misses) gives +1 dmg stacking up to +10. Resets on enemy attack. | Idea |
