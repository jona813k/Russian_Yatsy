"""
Gladiator tournament simulator — round-robin PvP between all 10 characters.
Each matchup is run N times; winner is whoever wins the majority.
"""
import heapq
import random
from itertools import combinations

SUMMON_TIERS = [
    {'min_level':  1, 'attack':  1, 'speed': 2.0, 'hp':  10, 'name': 'Imp'},
    {'min_level':  6, 'attack':  3, 'speed': 2.0, 'hp':  25, 'name': 'Wolf'},
    {'min_level': 12, 'attack':  6, 'speed': 2.0, 'hp':  50, 'name': 'Orc'},
    {'min_level': 18, 'attack': 11, 'speed': 2.0, 'hp': 100, 'name': 'Skeleton'},
    {'min_level': 24, 'attack': 18, 'speed': 2.0, 'hp': 200, 'name': 'Dragon'},
]
ATTACK_SPEED_CAP = 5.0
SPELL_CD = 4.0
MAX_TIME = 300.0
SIMS_PER_MATCHUP = 200

def get_summon(level):
    if level <= 0:
        return None
    tier = None
    for t in SUMMON_TIERS:
        if level >= t['min_level']:
            tier = t
    return dict(tier) if tier else None

def dark_mult(hit_count, dark_level):
    if dark_level == 0 or hit_count == 0:
        return 1.0
    tier2 = max(3, 15 - dark_level)
    tier3 = max(8, 30 - dark_level * 2)
    if hit_count < tier2:
        pct = 10 + dark_level
    elif hit_count < tier3:
        pct = 25 + dark_level
    else:
        pct = 50 + dark_level
    return 1.0 + pct / 100.0

def simulate_once(fa, fb, rng):
    """
    Returns 'a' or 'b' — which fighter wins.
    fa / fb are the raw character dicts from the dataset.
    """
    sa, sb = fa['stats'], fb['stats']
    ia = set(fa['items'])
    ib = set(fb['items'])

    # Mutable state per fighter (use lists for closure mutation)
    hp   = [sa['current_hp'], sb['current_hp']]
    maxhp= [sa['max_hp'],     sb['max_hp']]

    summon = [get_summon(sa['summon_level']), get_summon(sb['summon_level'])]
    s_hp   = [summon[0]['hp'] if summon[0] else 0, summon[1]['hp'] if summon[1] else 0]
    s_alive= [summon[0] is not None,               summon[1] is not None]

    hits = [0, 0]          # dark-level hit counter per attacker
    consec = [0, 0]        # consecutive attack counter (triple_hit)
    frost = [0.0, 0.0]     # attacker[i] is frozen until frost[i]

    stats = [sa, sb]
    items = [ia, ib]

    queue = []
    ctr = [0]

    def push(t, etype):
        ctr[0] += 1
        heapq.heappush(queue, (round(t, 4), ctr[0], etype))

    # Initial events: fighters indexed 0=A, 1=B
    for i in (0, 1):
        aspeed = min(ATTACK_SPEED_CAP, stats[i]['attack_speed'])
        push(round(1.0 / aspeed, 4), f'{i}_atk')
        if stats[i]['spell_level'] > 0:
            push(SPELL_CD, f'{i}_spell')
        if summon[i]:
            push(summon[i]['speed'], f'{i}_summon')

    while queue and hp[0] > 0 and hp[1] > 0:
        t, _, etype = heapq.heappop(queue)
        if t > MAX_TIME:
            break

        # Parse event
        idx = int(etype[0])   # attacker index (0 or 1)
        opp = 1 - idx
        ev  = etype[2:]       # 'atk', 'spell', 'summon'

        if ev == 'atk':
            st = stats[idx]
            it = items[idx]
            is_berserker = 'berserker' in it and hp[idx] < maxhp[idx] * 0.5
            eff_asp = min(ATTACK_SPEED_CAP, st['attack_speed'] * (1.20 if is_berserker else 1.0))
            next_cd = round(1.0 / eff_asp, 4)

            dmg = st['attack_dmg']
            is_execute = 'atk_execute' in it and hp[opp] < maxhp[opp] * 0.20
            if is_execute:
                dmg += 15

            crit = rng.random() < st['crit_chance']
            if crit:
                mult = 2.25 if 'crit_125' in it else 2.0
                dmg = int(dmg * mult)

            dm = dark_mult(hits[idx], st['dark_level'])
            eff_armor = 0.0 if 'armor_pen' in it else min(0.90, stats[opp]['armor'])

            blocked = rng.random() < stats[opp]['block_chance']

            if blocked:
                if 'block_reflect' in items[opp]:
                    reflect = max(1, int(st['attack_dmg'] * dm * (1 - min(0.90, stats[opp].get('armor', 0)))))
                    hp[idx] = max(0, hp[idx] - reflect)
            elif s_alive[opp]:
                raw = max(1, int(dmg * dm))          # summons have no armor
                if 'summon_survive' in items[opp]:
                    raw = max(1, int(raw * 0.9))
                s_hp[opp] = max(0, s_hp[opp] - raw)
                if s_hp[opp] <= 0:
                    s_alive[opp] = False
                hits[idx] += 1
                consec[idx] += 1
            else:
                final_dmg = max(1, int(dmg * dm * (1 - eff_armor)))
                hp[opp] = max(0, hp[opp] - final_dmg)
                hits[idx] += 1
                consec[idx] += 1

                # Lifesteal
                if st['lifesteal'] > 0:
                    heal = min(round(final_dmg * st['lifesteal']), maxhp[idx] - hp[idx])
                    if heal > 0:
                        hp[idx] += heal

                if 'heal_on_attack' in it:
                    hp[idx] = min(maxhp[idx], hp[idx] + 3)

                # Crit freeze: slow opponent's next attack
                if crit and 'crit_freeze' in it and hp[opp] > 0:
                    frost[opp] = max(frost[opp], t + 2.0)

                # Triple hit every 3 consecutive attacks
                if 'triple_hit' in it and consec[idx] % 3 == 0 and hp[opp] > 0:
                    hp[opp] = max(0, hp[opp] - 20)

            if hp[opp] > 0 and hp[idx] > 0:
                push(t + next_cd, f'{idx}_atk')

        elif ev == 'spell':
            st = stats[idx]
            it = items[idx]
            base_dmg = 17 + 3 * st['spell_level']
            dm = dark_mult(hits[idx], st['dark_level'])

            if 'spell_heal_summon' in it and s_alive[idx] and summon[idx]:
                # Heals own summon instead of attacking
                heal = int(base_dmg / 2)
                s_hp[idx] = min(summon[idx]['hp'], s_hp[idx] + heal)
            else:
                spell_dmg = max(1, int(base_dmg * dm))
                hp[opp] = max(0, hp[opp] - spell_dmg)

                if 'lifesteal_spell' in it and st['lifesteal'] > 0:
                    heal = min(round(spell_dmg * st['lifesteal'] * 0.5), maxhp[idx] - hp[idx])
                    if heal > 0:
                        hp[idx] += heal

                if 'spell_fire' in it and hp[opp] > 0:
                    burn_dmg = max(1, int(base_dmg * 0.10))
                    for tick in range(1, 4):
                        push(t + tick, f'{idx}_burn_{burn_dmg}')

                if 'spell_frost' in it and hp[opp] > 0:
                    frost[opp] = max(frost[opp], t + 3.0)

            if hp[opp] > 0 and hp[idx] > 0:
                push(t + SPELL_CD, f'{idx}_spell')

        elif ev.startswith('burn_'):
            bdmg = int(ev.split('_')[1])
            if hp[opp] > 0:
                hp[opp] = max(0, hp[opp] - bdmg)

        elif ev == 'summon':
            if s_alive[idx] and summon[idx]:
                dmg = summon[idx]['attack']
                dm = dark_mult(hits[idx], stats[idx]['dark_level'])
                dmg = max(1, int(dmg * dm))

                # Summon attacks go to opponent's summon first if alive
                if s_alive[opp]:
                    s_hp[opp] = max(0, s_hp[opp] - dmg)
                    if s_hp[opp] <= 0:
                        s_alive[opp] = False
                else:
                    hp[opp] = max(0, hp[opp] - dmg)

                if 'summon_upgrade' in items[idx] and summon[idx]:
                    heal = min(int(dmg * 0.10), summon[idx]['hp'] - s_hp[idx])
                    if heal > 0:
                        s_hp[idx] += heal

                if hp[opp] > 0:
                    push(t + summon[idx]['speed'], f'{idx}_summon')

    if hp[0] <= 0 and hp[1] <= 0:
        # Both died — whoever has more hp remaining wins (both are 0, so tie → A wins)
        return 'a'
    if hp[0] > 0 and hp[1] <= 0:
        return 'a'
    if hp[1] > 0 and hp[0] <= 0:
        return 'b'
    # Time limit — whoever has more hp wins
    return 'a' if hp[0] >= hp[1] else 'b'


def simulate_matchup(fa, fb, n=SIMS_PER_MATCHUP):
    rng = random.Random(42)
    wins_a = 0
    for _ in range(n):
        result = simulate_once(fa, fb, rng)
        if result == 'a':
            wins_a += 1
    wins_b = n - wins_a
    return wins_a, wins_b


# ─── Character data ───────────────────────────────────────────────────────────
fighters = [
    {"id": 10, "name": "Superwoman", "stats": {"max_hp": 392, "current_hp": 392, "attack_dmg": 52, "attack_speed": 0.5, "crit_chance": 0.24, "armor": 0.27, "block_chance": 0.03, "lifesteal": 0.6, "dark_level": 4, "summon_level": 14, "spell_level": 14}, "items": ["research_2slots", "armor_hp_ratio", "hp_to_atk", "hp_double_armor", "berserker", "atk_execute"]},
    {"id": 9,  "name": "Superman",   "stats": {"max_hp": 100, "current_hp": 100, "attack_dmg": 34, "attack_speed": 1.05, "crit_chance": 0.29, "armor": 0.25, "block_chance": 0.03, "lifesteal": 0.32, "dark_level": 7, "summon_level": 30, "spell_level": 2}, "items": ["crit_125", "summon_survive"]},
    {"id": 8,  "name": "Tom",        "stats": {"max_hp": 100, "current_hp": 100, "attack_dmg": 31, "attack_speed": 1.0,  "crit_chance": 0.08, "armor": 0.29, "block_chance": 0.11, "lifesteal": 0.24, "dark_level": 7, "summon_level": 24, "spell_level": 14}, "items": ["block_reflect", "crit_freeze"]},
    {"id": 7,  "name": "Kop",        "stats": {"max_hp": 205, "current_hp": 205, "attack_dmg": 41, "attack_speed": 1.2,  "crit_chance": 0.19, "armor": 0.55, "block_chance": 0.15, "lifesteal": 0.09, "dark_level": 0, "summon_level": 14, "spell_level": 8},  "items": ["lifesteal_5pct"]},
    {"id": 6,  "name": "Je",         "stats": {"max_hp": 175, "current_hp": 175, "attack_dmg": 41, "attack_speed": 0.975,"crit_chance": 0.08, "armor": 0.19, "block_chance": 0.11, "lifesteal": 0.16, "dark_level": 0, "summon_level": 25, "spell_level": 5},  "items": ["armor_pen", "spell_heal_summon"]},
    {"id": 5,  "name": "Pikachu",    "stats": {"max_hp": 100, "current_hp": 100, "attack_dmg": 32, "attack_speed": 0.975,"crit_chance": 0.04, "armor": 0.33, "block_chance": 0.19, "lifesteal": 0.16, "dark_level": 7, "summon_level": 24, "spell_level": 7},  "items": ["lifesteal_spell", "summon_upgrade"]},
    {"id": 4,  "name": "PeterParker","stats": {"max_hp": 280, "current_hp": 280, "attack_dmg": 49, "attack_speed": 0.875,"crit_chance": 0.23, "armor": 0.39, "block_chance": 0.03, "lifesteal": 0.09, "dark_level": 2, "summon_level": 22, "spell_level": 0},  "items": ["lifesteal_5pct"]},
    {"id": 3,  "name": "SpiderMan",  "stats": {"max_hp": 100, "current_hp": 100, "attack_dmg": 34, "attack_speed": 0.65, "crit_chance": 0.22, "armor": 0.25, "block_chance": 0.17, "lifesteal": 0.33, "dark_level": 2, "summon_level": 13, "spell_level": 19}, "items": ["lifesteal_5pct", "spell_fire"]},
    {"id": 2,  "name": "Batman2",    "stats": {"max_hp": 220, "current_hp": 219, "attack_dmg": 43, "attack_speed": 1.025,"crit_chance": 0.24, "armor": 0.53, "block_chance": 0.13, "lifesteal": 0.22, "dark_level": 1, "summon_level": 0,  "spell_level": 10}, "items": ["heal_on_attack"]},
    {"id": 1,  "name": "Batman1",    "stats": {"max_hp": 250, "current_hp": 250, "attack_dmg": 48, "attack_speed": 1.2,  "crit_chance": 0.15, "armor": 0.41, "block_chance": 0.03, "lifesteal": 0.1,  "dark_level": 6, "summon_level": 23, "spell_level": 2},  "items": ["atk_flat", "crit_freeze"]},
]

# Note: atk_flat (+5 atk) applied to Batman1
for f in fighters:
    if 'atk_flat' in f['items']:
        f['stats']['attack_dmg'] += 5

# Note: lifesteal_5pct (+5% lifesteal)
for f in fighters:
    if 'lifesteal_5pct' in f['items']:
        f['stats']['lifesteal'] = round(f['stats']['lifesteal'] + 0.05, 4)

# ─── Round-robin tournament ───────────────────────────────────────────────────
wins = {f['id']: 0 for f in fighters}
results_matrix = {}

print(f"Running {SIMS_PER_MATCHUP} simulations per matchup ({len(fighters)*(len(fighters)-1)//2} total matchups)...\n")

for fa, fb in combinations(fighters, 2):
    wa, wb = simulate_matchup(fa, fb)
    winner_id = fa['id'] if wa > wb else fb['id']
    loser_id  = fb['id'] if wa > wb else fa['id']
    wins[winner_id] += 1
    results_matrix[(fa['id'], fb['id'])] = (wa, wb)
    pct_a = wa / SIMS_PER_MATCHUP * 100
    winner_name = fa['name'] if wa > wb else fb['name']
    print(f"  {fa['name']:12} vs {fb['name']:12}  ->  {wa:3}/{SIMS_PER_MATCHUP}  {pct_a:5.1f}%  winner: {winner_name}")

# ─── Rankings ─────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("  GLADIATOR RANKINGS")
print("="*60)
ranked = sorted(fighters, key=lambda f: wins[f['id']], reverse=True)

summon_names = {0: 'none', 1: 'Imp', 6: 'Wolf', 12: 'Orc', 18: 'Skeleton', 24: 'Dragon'}
def summon_label(level):
    tier = None
    for mn in sorted(summon_names.keys()):
        if level >= mn:
            tier = summon_names[mn]
    return tier or 'none'

for rank, f in enumerate(ranked, 1):
    s = f['stats']
    print(f"  #{rank}  {f['name']:12}  Wins: {wins[f['id']]}/9   "
          f"HP:{s['current_hp']:3}/{s['max_hp']:3}  "
          f"ATK:{s['attack_dmg']:2}  SPD:{s['attack_speed']:.3f}  "
          f"CRIT:{s['crit_chance']:.0%}  ARMOR:{s['armor']:.0%}  "
          f"LS:{s['lifesteal']:.0%}  "
          f"Summon:{summon_label(s['summon_level'])}")

print()

# ─── Crazy Joe vs all 10 presets ──────────────────────────────────────────────
crazy_joe = {
    "id": 16, "name": "Crazy Joe",
    "stats": {
        "max_hp": 280, "current_hp": 280,
        "attack_dmg": 42, "attack_speed": 0.9, "crit_chance": 0.01,
        "armor": 0.75, "block_chance": 0.03, "lifesteal": 0.12,
        "dark_level": 3, "summon_level": 29, "spell_level": 14,
    },
    "items": ["spell_fire", "hp_to_atk"],
}
# Apply hp_to_atk: +5% of max_hp to attack_dmg
crazy_joe['stats']['attack_dmg'] += int(crazy_joe['stats']['max_hp'] * 0.05)

print("="*60)
print("  CRAZY JOE vs ALL 10 PRESETS")
print(f"  Joe stats: HP={crazy_joe['stats']['max_hp']} ATK={crazy_joe['stats']['attack_dmg']} "
      f"SPD={crazy_joe['stats']['attack_speed']} ARMOR={crazy_joe['stats']['armor']:.0%} "
      f"Dark={crazy_joe['stats']['dark_level']} Summon={summon_label(crazy_joe['stats']['summon_level'])} "
      f"Spell={crazy_joe['stats']['spell_level']}")
print("="*60)

joe_wins = 0
for opp in fighters:
    wa, wb = simulate_matchup(crazy_joe, opp)
    pct = wa / SIMS_PER_MATCHUP * 100
    winner = "Crazy Joe" if wa > wb else opp['name']
    if wa > wb: joe_wins += 1
    print(f"  Crazy Joe vs {opp['name']:12}  ->  Joe {wa:3}/{SIMS_PER_MATCHUP}  ({pct:5.1f}%)  winner: {winner}")

print(f"\n  Crazy Joe overall: {joe_wins}/10 wins vs the preset roster")
print()
