"""
Combat simulation — event-driven fight resolver.
Returns a timed event list the frontend can step through for animation.
"""
import heapq
import random
from typing import Optional

from .data import SUMMON_TIERS, ATTACK_SPEED_CAP
from .player import PlayerStats


def get_summon_stats(level: int) -> Optional[dict]:
    """Return summon stats for a given summon level, or None if level is 0."""
    if level <= 0:
        return None
    tier = None
    for t in SUMMON_TIERS:
        if level >= t['min_level']:
            tier = t
    return dict(tier) if tier else None


def get_dark_multiplier(hit_count: int, dark_level: int) -> float:
    """
    Damage multiplier from dark vulnerability stacks.
    hit_count is the number of hits landed BEFORE the current attack.

    Each dark level raises the % bonus by 1 AND lowers the hit thresholds,
    so investing heavily rewards you with earlier and stronger ramp-up.
    """
    if dark_level == 0 or hit_count == 0:
        return 1.0
    tier2 = max(3, 15 - dark_level)
    tier3 = max(8, 30 - dark_level * 2)
    if hit_count < tier2:
        bonus_pct = 10 + dark_level
    elif hit_count < tier3:
        bonus_pct = 25 + dark_level
    else:
        bonus_pct = 50 + dark_level
    return 1.0 + bonus_pct / 100.0


def simulate_combat(player: PlayerStats, enemy: dict, owned_items: list,
                    summon_hp_start: int = None) -> dict:
    """
    Simulate one fight and return the result.

    Returns:
        result:              'win' | 'lose'
        player_hp_remaining: int
        summon_hp_remaining: int
        events:              list of timed events for frontend animation
    """
    rng = random.Random()

    item_ids = {i['id'] for i in owned_items}
    # Tier 1 combat items
    has_triple_hit        = 'triple_hit'       in item_ids
    has_crit_125          = 'crit_125'         in item_ids
    has_block_reflect     = 'block_reflect'    in item_ids
    has_block_atk_buff    = 'block_atk_buff'   in item_ids
    has_lifesteal_spell   = 'lifesteal_spell'  in item_ids
    has_heal_on_attack    = 'heal_on_attack'   in item_ids
    has_bounty_50g        = 'bounty_50g'       in item_ids  # noqa: F841 (used in rpg_engine)
    # Tier 2 combat items
    has_atk_execute       = 'atk_execute'      in item_ids
    has_armor_pen         = 'armor_pen'        in item_ids
    has_berserker         = 'berserker'        in item_ids
    has_crit_freeze       = 'crit_freeze'      in item_ids
    has_crit_lifesteal    = 'crit_lifesteal'   in item_ids
    has_spell_fire        = 'spell_fire'       in item_ids
    has_spell_frost       = 'spell_frost'      in item_ids
    has_spell_heal_summon = 'spell_heal_summon' in item_ids

    spell_cooldown  = 4.0
    enemy_armor     = enemy.get('armor',     0.0)
    enemy_regen     = enemy.get('regen',     0)
    enemy_lifesteal = enemy.get('lifesteal', 0.0)
    eff_enemy_armor = 0.0 if has_armor_pen else enemy_armor

    eff_crit   = player.crit_chance
    eff_dmg    = player.attack_dmg
    eff_armor  = min(0.90, player.armor)  # can be negative → player takes extra damage
    eff_aspeed = min(ATTACK_SPEED_CAP, player.attack_speed)
    atk_cd     = round(1.0 / eff_aspeed, 4)

    # Mutable state (lists so closures can mutate them)
    player_hp    = [player.current_hp]
    enemy_hp     = [enemy['hp']]
    summon       = get_summon_stats(player.summon_level)

    start_hp = summon['hp'] if summon else 0
    if summon_hp_start is not None and summon:
        start_hp = min(summon_hp_start, summon['hp'])
    summon_hp    = [start_hp]
    summon_alive = [summon is not None]

    hit_count        = [0]
    atk_consecutive  = [0]
    frost_until      = [0.0]
    guard_buff_until = [0.0]

    events  = []
    counter = [0]
    queue   = []

    def push(t, etype, data=None):
        counter[0] += 1
        heapq.heappush(queue, (round(t, 4), counter[0], etype, data or {}))

    push(atk_cd,         'player_attack')
    push(enemy['speed'], 'enemy_attack')
    if player.spell_level > 0:
        push(spell_cooldown, 'spell')
    if summon:
        push(summon['speed'], 'summon_attack')
    if enemy_regen > 0:
        push(1.0, 'enemy_regen')

    MAX_TIME = 300.0

    while queue and player_hp[0] > 0 and enemy_hp[0] > 0:
        t, _, etype, _data = heapq.heappop(queue)
        if t > MAX_TIME:
            break

        if etype == 'player_attack':
            if has_berserker and player_hp[0] < player.max_hp * 0.5:
                effective_aspeed = min(ATTACK_SPEED_CAP, eff_aspeed * 1.20)
                current_atk_cd = round(1.0 / effective_aspeed, 4)
            else:
                current_atk_cd = atk_cd

            guard_bonus = 5 if (has_block_atk_buff and t <= guard_buff_until[0]) else 0
            dmg = eff_dmg + guard_bonus
            is_execute = has_atk_execute and enemy_hp[0] < enemy['hp'] * 0.20
            if is_execute:
                dmg += 15

            crit = rng.random() < eff_crit
            crit_mult = 2.25 if has_crit_125 else 2.0
            if crit:
                dmg = int(dmg * crit_mult)

            dark_mult = get_dark_multiplier(hit_count[0], player.dark_level)
            dmg = max(1, int(dmg * dark_mult * (1 - eff_enemy_armor)))
            hit_count[0] += 1
            atk_consecutive[0] += 1

            heal = 0
            if crit and has_crit_lifesteal:
                base_dmg = max(1, int((eff_dmg + guard_bonus + (15 if is_execute else 0))
                                      * dark_mult * aura_mult * (1 - eff_enemy_armor)))
                crit_bonus = dmg - base_dmg
                crit_ls_heal = min(crit_bonus, player.max_hp - player_hp[0])
                if crit_ls_heal > 0:
                    player_hp[0] += crit_ls_heal
                    heal += crit_ls_heal
            elif player.lifesteal > 0:
                ls_heal = min(round(dmg * player.lifesteal), player.max_hp - player_hp[0])
                player_hp[0] += ls_heal
                heal += ls_heal
            if has_heal_on_attack:
                atk_heal = min(3, player.max_hp - player_hp[0])
                player_hp[0] += atk_heal
                heal += atk_heal

            enemy_hp[0] = max(0, enemy_hp[0] - dmg)
            ev = {
                'time': t, 'type': 'player_attack',
                'dmg': dmg, 'crit': crit, 'heal': heal,
                'dark_mult': round(dark_mult, 2),
                'hit_count': hit_count[0],
                'enemy_hp': enemy_hp[0], 'player_hp': player_hp[0],
            }
            if is_execute:
                ev['execute'] = True
            events.append(ev)

            if crit and has_crit_freeze and enemy_hp[0] > 0:
                frost_until[0] = max(frost_until[0], t + 2.0)

            if has_triple_hit and atk_consecutive[0] % 3 == 0 and enemy_hp[0] > 0:
                bonus_dmg = 20
                enemy_hp[0] = max(0, enemy_hp[0] - bonus_dmg)
                events.append({
                    'time': t, 'type': 'player_attack',
                    'dmg': bonus_dmg, 'crit': False, 'heal': 0,
                    'dark_mult': round(dark_mult, 2),
                    'hit_count': hit_count[0],
                    'enemy_hp': enemy_hp[0], 'player_hp': player_hp[0],
                    'triple_hit': True,
                })

            if enemy_hp[0] > 0:
                push(t + current_atk_cd, 'player_attack')

        elif etype == 'spell':
            base_spell_dmg = 17 + 3 * player.spell_level
            dark_mult = get_dark_multiplier(hit_count[0], player.dark_level)

            heal = 0
            if has_spell_heal_summon and summon_alive[0] and summon:
                summon_heal = int(base_spell_dmg / 2)
                summon_hp[0] = min(summon['hp'], summon_hp[0] + summon_heal)
                events.append({
                    'time': t, 'type': 'spell',
                    'dmg': 0, 'heal': 0, 'dark_mult': 1.0,
                    'enemy_hp': enemy_hp[0], 'player_hp': player_hp[0],
                    'summon_heal': summon_heal, 'summon_hp': summon_hp[0],
                })
                if enemy_hp[0] > 0:
                    push(t + spell_cooldown, 'spell')
                continue

            dmg = max(1, int(base_spell_dmg * dark_mult))
            if has_lifesteal_spell and player.lifesteal > 0:
                siphon_heal = min(round(dmg * player.lifesteal), player.max_hp - player_hp[0])
                if siphon_heal > 0:
                    player_hp[0] += siphon_heal
                    heal += siphon_heal

            enemy_hp[0] = max(0, enemy_hp[0] - dmg)
            ev = {
                'time': t, 'type': 'spell',
                'dmg': dmg, 'heal': heal, 'dark_mult': round(dark_mult, 2),
                'enemy_hp': enemy_hp[0], 'player_hp': player_hp[0],
            }
            if has_spell_frost and enemy_hp[0] > 0:
                frost_until[0] = max(frost_until[0], t + 3.0)
                ev['frost'] = True
            if has_spell_fire and enemy_hp[0] > 0:
                burn_dmg = max(1, int(base_spell_dmg * 0.10))
                for tick in range(1, 4):
                    push(t + tick, 'burn_tick', {'dmg': burn_dmg})
                ev['burn_applied'] = True
            events.append(ev)
            if enemy_hp[0] > 0:
                push(t + spell_cooldown, 'spell')

        elif etype == 'burn_tick':
            if enemy_hp[0] > 0:
                bdmg = _data.get('dmg', 5)
                enemy_hp[0] = max(0, enemy_hp[0] - bdmg)
                events.append({
                    'time': t, 'type': 'burn_tick',
                    'dmg': bdmg, 'enemy_hp': enemy_hp[0],
                })

        elif etype == 'summon_attack':
            if summon_alive[0]:
                dmg = summon['attack']
                dark_mult = get_dark_multiplier(hit_count[0], player.dark_level)
                dmg = max(1, int(dmg * dark_mult))
                enemy_hp[0] = max(0, enemy_hp[0] - dmg)
                events.append({
                    'time': t, 'type': 'summon_attack',
                    'dmg': dmg, 'dark_mult': round(dark_mult, 2),
                    'enemy_hp': enemy_hp[0],
                })
                if enemy_hp[0] > 0:
                    push(t + summon['speed'], 'summon_attack')

        elif etype == 'enemy_regen':
            heal = min(enemy_regen, enemy['hp'] - enemy_hp[0])
            if heal > 0:
                enemy_hp[0] += heal
                events.append({
                    'time': t, 'type': 'enemy_regen',
                    'heal': heal, 'enemy_hp': enemy_hp[0],
                })
            if enemy_hp[0] > 0:
                push(t + 1.0, 'enemy_regen')

        elif etype == 'enemy_attack':
            blocked = rng.random() < player.block_chance
            ev = {'time': t, 'type': 'enemy_attack', 'blocked': blocked}

            if blocked:
                ev['player_hp'] = player_hp[0]
                if has_block_reflect and enemy_hp[0] > 0:
                    thorns = enemy['attack']
                    enemy_hp[0] = max(0, enemy_hp[0] - thorns)
                    ev['thorns'] = thorns
                    ev['enemy_hp'] = enemy_hp[0]
                if has_block_atk_buff:
                    guard_buff_until[0] = t + 2.0
            elif summon_alive[0]:
                raw = enemy['attack']
                summon_hp[0] = max(0, summon_hp[0] - raw)
                ev['summon_dmg'] = raw
                ev['summon_hp']  = summon_hp[0]
                ev['player_hp']  = player_hp[0]
                if summon_hp[0] <= 0:
                    summon_alive[0] = False
                    ev['summon_died'] = True
            else:
                raw = enemy['attack']
                dmg_to_player = max(1, int(raw * (1 - eff_armor)))
                player_hp[0] = max(0, player_hp[0] - dmg_to_player)
                ev['dmg']       = dmg_to_player
                ev['player_hp'] = player_hp[0]

                if enemy_lifesteal > 0 and enemy_hp[0] > 0:
                    ls_heal = min(int(dmg_to_player * enemy_lifesteal), enemy['hp'] - enemy_hp[0])
                    if ls_heal > 0:
                        enemy_hp[0] += ls_heal
                        ev['enemy_lifesteal_heal'] = ls_heal
                        ev['enemy_hp'] = enemy_hp[0]

            events.append(ev)
            if player_hp[0] > 0 and enemy_hp[0] > 0:
                next_atk_delay = enemy['speed']
                if frost_until[0] > t:
                    next_atk_delay = round(enemy['speed'] / 0.7, 4)
                push(t + next_atk_delay, 'enemy_attack')

    result = 'win' if enemy_hp[0] <= 0 else 'lose'
    events.append({
        'time': events[-1]['time'] if events else 0,
        'type': 'combat_end',
        'result': result,
        'player_hp': player_hp[0],
        'enemy_hp': enemy_hp[0],
    })

    return {
        'result': result,
        'player_hp_remaining': player_hp[0],
        'summon_hp_remaining': summon_hp[0] if summon_alive[0] else 0,
        'events': events,
    }
