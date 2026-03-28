"""
RPG Mode Simulation Script
==========================
Runs the game headlessly using the RPG engine directly (no HTTP overhead).
Reports win rates, balance data, and bug surface info.

Usage:
    python simulate_rpg.py                         # 500 games, default settings
    python simulate_rpg.py --games 2000            # more games
    python simulate_rpg.py --strategy high_first   # prefer high-number upgrades
    python simulate_rpg.py --forge1 add_d12 --forge2 risky_die
    python simulate_rpg.py --all-forges            # run every forge combo (6 paths x N games)
    python simulate_rpg.py --verbose               # print each game's story
"""

import sys
import os
import argparse
import random
from collections import defaultdict, Counter

# ── project root on path ────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.backend.rpg_engine import RPGRun, FORGE_LEVELS, LEVELS, SHOP_ITEMS


# ─────────────────────────────────────────────────────────────────────────────
# Upgrade-phase bot strategies
# ─────────────────────────────────────────────────────────────────────────────

def pick_action(legal_actions, player_progress, strategy='greedy'):
    """
    Choose an action from the list returned by engine.get_legal_actions().

    Strategies:
      random     – uniform random choice
      greedy     – prefer the number with the most progress already (finish what you started)
      high_first – prefer higher numbers (7-12, harder to reach but stronger stats)
      low_first  – prefer lower numbers (1-6, easier to hit consistently)
      balanced   – prefer the number with the LEAST progress (diversify upgrades)
    """
    selectable = [a for a in legal_actions if a['type'] in ('select', 'collect')]
    skip       = next((a for a in legal_actions if a['type'] == 'skip_turn'), None)

    if not selectable:
        return skip  # forced skip

    if strategy == 'random':
        return random.choice(selectable)

    if strategy == 'greedy':
        return max(selectable, key=lambda a: player_progress.get(a['number'], 0))

    if strategy == 'high_first':
        return max(selectable, key=lambda a: a['number'])

    if strategy == 'low_first':
        return min(selectable, key=lambda a: a['number'])

    if strategy == 'balanced':
        return min(selectable, key=lambda a: player_progress.get(a['number'], 0))

    return random.choice(selectable)


def play_upgrade_phase(run, strategy='greedy', verbose=False):
    """Drive the upgrade phase to completion."""
    MAX_ACTIONS = 500  # safety — prevent infinite loops
    actions_taken = 0

    while run.phase == 'upgrade' and not run.upgrade_done and actions_taken < MAX_ACTIONS:
        engine = run.upgrade_engine
        legal  = engine.get_legal_actions()

        if not legal:
            break  # engine says nothing to do (shouldn't happen)

        skip_only = len(legal) == 1 and legal[0]['type'] == 'skip_turn'

        if skip_only:
            result = engine.execute_action(legal[0])
        else:
            # Use free reroll if available and the roll looks poor
            if run.free_reroll_available:
                dice = engine.state.dice_values
                legal_numbers = {a.get('number') for a in legal if a.get('number')}
                useful = sum(
                    1 for d in dice
                    if d in legal_numbers or any((d + x) in legal_numbers for x in dice)
                )
                # Reroll if fewer than 2 dice are obviously useful
                if useful < 2:
                    run.use_free_reroll()
                    legal = engine.get_legal_actions()
                    if not legal:
                        break

            action = pick_action(legal, engine.player.progress, strategy)
            result = engine.execute_action(action)

        run.handle_action_result(result)
        actions_taken += 1

        if verbose:
            state = result.get('state', '')
            num   = result.get('info', {}).get('completed') or result.get('info', {}).get('collected')
            print(f"      [{state}] num={num}")

    if run.phase == 'upgrade' and run.upgrade_done:
        run.finish_upgrade()


def play_shop(run, verbose=False):
    """Simple shop bot: buy the cheapest affordable item, skip if nothing useful."""
    if run.phase not in ('shop', 'pre_boss_shop'):
        return
    owned_ids = {i['id'] for i in run.owned_items}
    slots     = max(1, run.player.item_slots)
    available = slots - len(run.owned_items)

    if available > 0:
        affordable = [
            item for item in run.shop_items
            if run.player.gold >= item['cost'] and item['id'] not in owned_ids
        ]
        if affordable:
            # Buy the most expensive item we can afford (most impactful)
            best = max(affordable, key=lambda i: i['cost'])
            run.buy_item(best['id'])
            if verbose:
                print(f"      [shop] bought {best['name']} for {best['cost']}g")

    run.close_shop()


# ─────────────────────────────────────────────────────────────────────────────
# Single game runner
# ─────────────────────────────────────────────────────────────────────────────

def play_game(upgrade_strategy='greedy', forge1_id=None, forge2_id=None, verbose=False):
    """
    Play one full run and return a result dict.
    forge1_id / forge2_id: specific forge choice ID to pick, or None for first option.
    """
    run    = RPGRun()
    result = {
        'outcome':       None,   # 'win' or 'lose'
        'level_reached': 1,
        'fight_reached': 0,
        'hp_remaining':  0,
        'forge1':        None,
        'forge2':        None,
        'collections':   defaultdict(int),   # number → total collected
        'fights':        [],                 # list of {enemy, result, player_hp_before}
        'gold_spent':    0,
        'items_bought':  [],
    }

    MAX_PHASES = 200
    phase_count = 0

    while run.phase not in ('game_over', 'victory') and phase_count < MAX_PHASES:
        phase_count += 1
        phase = run.phase

        if verbose:
            print(f"  Phase={phase} L{run.level_idx+1} F{run.fight_idx}")

        # ── Upgrade ──────────────────────────────────────────────────────────
        if phase in ('upgrade', 'upgrade_done'):
            before_progress = {
                n: run.upgrade_engine.player.progress.get(n, 0)
                for n in range(1, 13)
            }
            play_upgrade_phase(run, upgrade_strategy, verbose)
            after_progress = {
                n: run.upgrade_engine.player.progress.get(n, 0) if run.upgrade_engine else 0
                for n in range(1, 13)
            }
            for n in range(1, 13):
                gained = after_progress.get(n, 0) - before_progress.get(n, 0)
                if gained > 0:
                    result['collections'][n] += gained

        # ── Pre-boss shop / regular shop ─────────────────────────────────────
        elif phase in ('pre_boss_shop', 'shop'):
            gold_before = run.player.gold
            play_shop(run, verbose)
            result['gold_spent'] += gold_before - run.player.gold

        # ── Combat ───────────────────────────────────────────────────────────
        elif phase == 'combat':
            enemy    = run.current_enemy
            hp_before = run.player.current_hp
            combat   = run.run_combat()
            result['fights'].append({
                'enemy':        enemy['name'],
                'is_boss':      enemy['is_boss'],
                'result':       combat['result'],
                'player_hp_before': hp_before,
                'player_hp_after':  run.player.current_hp,
            })
            if verbose:
                outcome = '✓' if combat['result'] == 'win' else '✗'
                print(f"      [combat {outcome}] vs {enemy['name']} "
                      f"HP: {hp_before} → {run.player.current_hp}")

        # ── Forge ─────────────────────────────────────────────────────────────
        elif phase == 'forge':
            choices = run.forge_choices
            forge_num = 1 if result['forge1'] is None else 2

            if forge_num == 1:
                chosen_id = forge1_id or choices[0]['id']
            else:
                chosen_id = forge2_id or choices[0]['id']

            chosen = next((c for c in choices if c['id'] == chosen_id), choices[0])
            run.pick_forge(chosen['id'])

            if forge_num == 1:
                result['forge1'] = chosen['id']
                if verbose:
                    print(f"      [forge I] chose {chosen['name']}")
            else:
                result['forge2'] = chosen['id']
                if verbose:
                    print(f"      [forge II] chose {chosen['name']}")

        else:
            # Unknown phase guard
            if verbose:
                print(f"      [unknown phase: {phase}]")
            break

        result['level_reached'] = run.level_idx + 1
        result['fight_reached'] = run.fight_idx

    # ── End of run ────────────────────────────────────────────────────────────
    result['outcome']      = 'win' if run.phase == 'victory' else 'lose'
    result['hp_remaining'] = run.player.current_hp
    if result['outcome'] == 'win':
        result['level_reached'] = 3
        result['fight_reached'] = 2

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Reporting
# ─────────────────────────────────────────────────────────────────────────────

STAT_LABELS = {
    1: 'Atk Speed', 2: 'Atk Dmg', 3: 'Crit', 4: 'Armor', 5: 'HP',
    6: 'Research', 7: 'Gold', 8: 'Summon', 9: 'Spell', 10: 'Block',
    11: 'Lifesteal', 12: 'Dark',
}

def print_report(results, label=''):
    n = len(results)
    wins  = [r for r in results if r['outcome'] == 'win']
    loses = [r for r in results if r['outcome'] == 'lose']

    win_rate = len(wins) / n * 100

    print()
    print('=' * 60)
    if label:
        print(f'  {label}')
    print(f'  Games played : {n}')
    print(f'  Win rate     : {win_rate:.1f}%  ({len(wins)} wins / {len(loses)} losses)')

    if wins:
        avg_hp = sum(r['hp_remaining'] for r in wins) / len(wins)
        print(f'  Avg HP on win: {avg_hp:.1f}')

    if loses:
        level_dist = Counter(r['level_reached'] for r in loses)
        fight_dist = Counter(
            f"L{r['level_reached']}F{r['fight_reached']+1}" for r in loses
        )
        print(f'  Losses by level: ' +
              ', '.join(f"L{l}: {c}" for l, c in sorted(level_dist.items())))
        print(f'  Losses by fight: ' +
              ', '.join(f"{k}: {v}" for k, v in fight_dist.most_common(5)))

    # Forge choice popularity
    forge1_counter = Counter(r['forge1'] for r in results if r['forge1'])
    forge2_counter = Counter(r['forge2'] for r in results if r['forge2'])
    if forge1_counter:
        print('  Forge I  chosen: ' +
              ', '.join(f"{k}x{v}" for k, v in forge1_counter.most_common()))
    if forge2_counter:
        print('  Forge II chosen: ' +
              ', '.join(f"{k}x{v}" for k, v in forge2_counter.most_common()))

    # Win rates by forge1 choice (if multiple)
    if len(forge1_counter) > 1:
        print()
        print('  Win rate by Forge I choice:')
        for choice_id, count in forge1_counter.most_common():
            choice_wins = sum(
                1 for r in wins if r['forge1'] == choice_id
            )
            rate = choice_wins / count * 100
            print(f'    {choice_id:<20} {rate:5.1f}%  ({choice_wins}/{count})')

    if len(forge2_counter) > 1:
        print()
        print('  Win rate by Forge II choice:')
        for choice_id, count in forge2_counter.most_common():
            choice_wins = sum(
                1 for r in wins if r['forge2'] == choice_id
            )
            rate = choice_wins / count * 100
            print(f'    {choice_id:<20} {rate:5.1f}%  ({choice_wins}/{count})')

    # Average upgrade collections across all games
    print()
    print('  Avg upgrade collections per stat (per game):')
    for n_stat in range(1, 13):
        avg = sum(r['collections'].get(n_stat, 0) for r in results) / n
        bar = '#' * int(avg * 2)
        print(f'    {n_stat:>2} {STAT_LABELS[n_stat]:<12} {avg:4.1f}  {bar}')

    print('=' * 60)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

FORGE1_CHOICES = [c['id'] for c in FORGE_LEVELS[0]]
FORGE2_CHOICES = [c['id'] for c in FORGE_LEVELS[1]]

def main():
    parser = argparse.ArgumentParser(description='RPG mode simulator')
    parser.add_argument('--games',    type=int, default=500,
                        help='Number of games to simulate (default: 500)')
    parser.add_argument('--strategy', choices=['random', 'greedy', 'high_first', 'low_first', 'balanced'],
                        default='greedy',
                        help='Upgrade-phase strategy (default: greedy)')
    parser.add_argument('--forge1',   choices=FORGE1_CHOICES, default=None,
                        help='Force a specific Forge I choice')
    parser.add_argument('--forge2',   choices=FORGE2_CHOICES, default=None,
                        help='Force a specific Forge II choice')
    parser.add_argument('--all-forges', action='store_true',
                        help='Run every forge combination (9 paths x N/9 games each)')
    parser.add_argument('--all-strategies', action='store_true',
                        help='Run every upgrade strategy and compare')
    parser.add_argument('--verbose',  action='store_true',
                        help='Print each game turn-by-turn')
    args = parser.parse_args()

    print(f'\nRPG Simulation -- {args.games} games -- strategy: {args.strategy}')

    if args.all_strategies:
        strategies = ['random', 'greedy', 'high_first', 'low_first', 'balanced']
        per = max(100, args.games // len(strategies))
        for strat in strategies:
            results = [
                play_game(upgrade_strategy=strat, verbose=False)
                for _ in range(per)
            ]
            print_report(results, label=f'Strategy: {strat}  ({per} games)')
        return

    if args.all_forges:
        per = max(50, args.games // (len(FORGE1_CHOICES) * len(FORGE2_CHOICES)))
        all_results = []
        print(f'\nRunning all {len(FORGE1_CHOICES) * len(FORGE2_CHOICES)} forge combos '
              f'x {per} games each\n')
        combo_results = []
        for f1 in FORGE1_CHOICES:
            for f2 in FORGE2_CHOICES:
                results = [
                    play_game(upgrade_strategy=args.strategy,
                              forge1_id=f1, forge2_id=f2,
                              verbose=False)
                    for _ in range(per)
                ]
                wins = sum(1 for r in results if r['outcome'] == 'win')
                rate = wins / per * 100
                combo_results.append((rate, f1, f2, results))
                all_results.extend(results)

        # Sort by win rate
        combo_results.sort(reverse=True)
        print('  Forge combo win rates (best to worst):')
        for rate, f1, f2, _ in combo_results:
            bar = '#' * int(rate / 5)
            print(f'    {f1:<20} + {f2:<20}  {rate:5.1f}%  {bar}')

        print_report(all_results, label=f'All forge combos combined  ({len(all_results)} games)')
        return

    # ── Standard run ──────────────────────────────────────────────────────────
    results = []
    milestone = max(1, args.games // 10)
    for i in range(args.games):
        if args.verbose:
            print(f'\n── Game {i+1} ──────────────────────────────────')
        r = play_game(
            upgrade_strategy=args.strategy,
            forge1_id=args.forge1,
            forge2_id=args.forge2,
            verbose=args.verbose,
        )
        results.append(r)
        if not args.verbose and (i + 1) % milestone == 0:
            done = (i + 1) / args.games * 100
            print(f'  {done:5.1f}%  ({i+1}/{args.games})', end='\r')

    print_report(
        results,
        label=f'strategy={args.strategy}  forge1={args.forge1 or "first"}  '
              f'forge2={args.forge2 or "first"}',
    )


if __name__ == '__main__':
    main()
