"""
Seed the gladiator DB with the 10 tournament characters at their assigned tiers.

Tier assignment (based on simulation ranking):
  Tier 3 (wins_achieved=3): Batman run1, Je
  Tier 2 (wins_achieved=2): Kop, Superman
  Tier 1 (wins_achieved=1): Superwoman, Tom, Pikachu
  Tier 0 (wins_achieved=0): Batman run2, PeterParker, SpiderMan
"""
import sqlite3, json
from pathlib import Path

DB_PATH = Path('web/backend/gladiator.db')

characters = [
    # ── Tier 0 ──────────────────────────────────────────────────────
    {
        'name': 'Batman', 'run_id': 'seed-run-2', 'tier': 0,
        'timestamp': '2026-04-03T20:02:37.763225+00:00',
        'stats': {"max_hp": 220, "current_hp": 220, "attack_dmg": 43, "attack_speed": 1.025,
                  "crit_chance": 0.24, "armor": 0.53, "block_chance": 0.13, "lifesteal": 0.22,
                  "dark_level": 1, "summon_level": 0, "spell_level": 10, "gold": 40,
                  "item_slots": 2, "free_items": 1, "extra_d12": 0, "extra_d3": 0,
                  "removed_dice": 0, "has_risky_die": False, "loaded_high": False,
                  "has_free_reroll": False, "dice_plus_one": False, "has_2_5_die": True,
                  "has_retry_die": False, "has_logic_die": False, "logic_die_pos": 0,
                  "loaded_low": False, "has_mirror_die": False, "has_bomb_die": True,
                  "has_gladiator_key": False, "has_shop_free_reroll": False,
                  "has_item_discount": False, "has_crit_to_aspeed": False,
                  "has_armor_gives_hp": False, "has_gold_level_bonus": False,
                  "has_summon_upgrade": False},
        'items': ['heal_on_attack'],
    },
    {
        'name': 'PeterParker', 'run_id': 'seed-run-4', 'tier': 0,
        'timestamp': '2026-04-04T20:00:54.178327+00:00',
        'stats': {"max_hp": 280, "current_hp": 280, "attack_dmg": 49, "attack_speed": 0.875,
                  "crit_chance": 0.23, "armor": 0.39, "block_chance": 0.03, "lifesteal": 0.14,
                  "dark_level": 2, "summon_level": 22, "spell_level": 0, "gold": 80,
                  "item_slots": 1, "free_items": 0, "extra_d12": 0, "extra_d3": 0,
                  "removed_dice": 0, "has_risky_die": False, "loaded_high": True,
                  "has_free_reroll": False, "dice_plus_one": False, "has_2_5_die": True,
                  "has_retry_die": False, "has_logic_die": False, "logic_die_pos": 0,
                  "loaded_low": False, "has_mirror_die": False, "has_bomb_die": False,
                  "has_gladiator_key": False, "has_shop_free_reroll": False,
                  "has_item_discount": False, "has_crit_to_aspeed": False,
                  "has_armor_gives_hp": False, "has_gold_level_bonus": False,
                  "has_summon_upgrade": False},
        'items': ['lifesteal_5pct'],
    },
    {
        'name': 'SpiderMan', 'run_id': 'seed-run-3', 'tier': 0,
        'timestamp': '2026-04-03T20:39:54.172212+00:00',
        'stats': {"max_hp": 100, "current_hp": 100, "attack_dmg": 34, "attack_speed": 0.65,
                  "crit_chance": 0.22, "armor": 0.25, "block_chance": 0.17, "lifesteal": 0.38,
                  "dark_level": 2, "summon_level": 13, "spell_level": 19, "gold": 10,
                  "item_slots": 4, "free_items": 1, "extra_d12": 0, "extra_d3": 0,
                  "removed_dice": 0, "has_risky_die": False, "loaded_high": False,
                  "has_free_reroll": False, "dice_plus_one": False, "has_2_5_die": False,
                  "has_retry_die": False, "has_logic_die": True, "logic_die_pos": 39,
                  "loaded_low": False, "has_mirror_die": True, "has_bomb_die": False,
                  "has_gladiator_key": False, "has_shop_free_reroll": False,
                  "has_item_discount": False, "has_crit_to_aspeed": False,
                  "has_armor_gives_hp": False, "has_gold_level_bonus": False,
                  "has_summon_upgrade": False},
        'items': ['lifesteal_5pct', 'spell_fire'],
    },

    # ── Tier 1 ──────────────────────────────────────────────────────
    {
        'name': 'Superwoman', 'run_id': 'seed-run-10', 'tier': 1,
        'timestamp': '2026-04-10T18:10:08.809392+00:00',
        'stats': {"max_hp": 392, "current_hp": 392, "attack_dmg": 52, "attack_speed": 0.5,
                  "crit_chance": 0.24, "armor": 0.27, "block_chance": 0.03, "lifesteal": 0.6,
                  "dark_level": 4, "summon_level": 14, "spell_level": 14, "gold": 60,
                  "item_slots": 6, "free_items": 1, "extra_d12": 0, "extra_d3": 0,
                  "removed_dice": 0, "has_risky_die": False, "loaded_high": False,
                  "has_free_reroll": False, "dice_plus_one": True, "has_2_5_die": True,
                  "has_retry_die": False, "has_logic_die": False, "logic_die_pos": 0,
                  "loaded_low": False, "has_mirror_die": False, "has_bomb_die": False,
                  "has_gladiator_key": False, "has_shop_free_reroll": False,
                  "has_item_discount": False, "has_crit_to_aspeed": False,
                  "has_armor_gives_hp": True, "has_gold_level_bonus": False,
                  "has_summon_upgrade": False},
        'items': ['research_2slots', 'armor_hp_ratio', 'hp_to_atk', 'hp_double_armor', 'berserker', 'atk_execute'],
    },
    {
        'name': 'Tom', 'run_id': 'seed-run-8', 'tier': 1,
        'timestamp': '2026-04-05T17:29:04.851289+00:00',
        'stats': {"max_hp": 100, "current_hp": 100, "attack_dmg": 31, "attack_speed": 1.0,
                  "crit_chance": 0.08, "armor": 0.29, "block_chance": 0.11, "lifesteal": 0.24,
                  "dark_level": 7, "summon_level": 24, "spell_level": 14, "gold": 100,
                  "item_slots": 2, "free_items": 0, "extra_d12": 0, "extra_d3": 0,
                  "removed_dice": 0, "has_risky_die": True, "loaded_high": False,
                  "has_free_reroll": False, "dice_plus_one": False, "has_2_5_die": False,
                  "has_retry_die": True, "has_logic_die": False, "logic_die_pos": 0,
                  "loaded_low": False, "has_mirror_die": False, "has_bomb_die": False,
                  "has_gladiator_key": False, "has_shop_free_reroll": False,
                  "has_item_discount": False, "has_crit_to_aspeed": False,
                  "has_armor_gives_hp": False, "has_gold_level_bonus": False,
                  "has_summon_upgrade": False},
        'items': ['block_reflect', 'crit_freeze'],
    },
    {
        'name': 'Pikachu', 'run_id': 'seed-run-5', 'tier': 1,
        'timestamp': '2026-04-05T08:07:58.361359+00:00',
        'stats': {"max_hp": 100, "current_hp": 100, "attack_dmg": 32, "attack_speed": 0.975,
                  "crit_chance": 0.04, "armor": 0.33, "block_chance": 0.19, "lifesteal": 0.16,
                  "dark_level": 7, "summon_level": 24, "spell_level": 7, "gold": 0,
                  "item_slots": 4, "free_items": 0, "extra_d12": 1, "extra_d3": 0,
                  "removed_dice": 0, "has_risky_die": False, "loaded_high": False,
                  "has_free_reroll": False, "dice_plus_one": True, "has_2_5_die": False,
                  "has_retry_die": False, "has_logic_die": False, "logic_die_pos": 0,
                  "loaded_low": False, "has_mirror_die": False, "has_bomb_die": False,
                  "has_gladiator_key": False, "has_shop_free_reroll": False,
                  "has_item_discount": False, "has_crit_to_aspeed": False,
                  "has_armor_gives_hp": False, "has_gold_level_bonus": False,
                  "has_summon_upgrade": True},
        'items': ['lifesteal_spell', 'summon_upgrade'],
    },

    # ── Tier 2 ──────────────────────────────────────────────────────
    {
        'name': 'Kop', 'run_id': 'seed-run-7', 'tier': 2,
        'timestamp': '2026-04-05T15:32:33.782118+00:00',
        'stats': {"max_hp": 205, "current_hp": 205, "attack_dmg": 41, "attack_speed": 1.2,
                  "crit_chance": 0.19, "armor": 0.55, "block_chance": 0.15, "lifesteal": 0.14,
                  "dark_level": 0, "summon_level": 14, "spell_level": 8, "gold": 90,
                  "item_slots": 0, "free_items": 0, "extra_d12": 1, "extra_d3": 0,
                  "removed_dice": 0, "has_risky_die": False, "loaded_high": False,
                  "has_free_reroll": True, "dice_plus_one": False, "has_2_5_die": False,
                  "has_retry_die": False, "has_logic_die": False, "logic_die_pos": 0,
                  "loaded_low": False, "has_mirror_die": False, "has_bomb_die": False,
                  "has_gladiator_key": False, "has_shop_free_reroll": False,
                  "has_item_discount": False, "has_crit_to_aspeed": False,
                  "has_armor_gives_hp": False, "has_gold_level_bonus": False,
                  "has_summon_upgrade": False},
        'items': ['lifesteal_5pct'],
    },
    {
        'name': 'Superman', 'run_id': 'seed-run-9', 'tier': 2,
        'timestamp': '2026-04-10T17:34:03.018070+00:00',
        'stats': {"max_hp": 100, "current_hp": 100, "attack_dmg": 34, "attack_speed": 1.05,
                  "crit_chance": 0.29, "armor": 0.25, "block_chance": 0.03, "lifesteal": 0.32,
                  "dark_level": 7, "summon_level": 30, "spell_level": 2, "gold": 50,
                  "item_slots": 2, "free_items": 0, "extra_d12": 0, "extra_d3": 0,
                  "removed_dice": 0, "has_risky_die": True, "loaded_high": False,
                  "has_free_reroll": False, "dice_plus_one": False, "has_2_5_die": False,
                  "has_retry_die": False, "has_logic_die": True, "logic_die_pos": 43,
                  "loaded_low": False, "has_mirror_die": False, "has_bomb_die": False,
                  "has_gladiator_key": True, "has_shop_free_reroll": False,
                  "has_item_discount": False, "has_crit_to_aspeed": False,
                  "has_armor_gives_hp": False, "has_gold_level_bonus": False,
                  "has_summon_upgrade": False},
        'items': ['crit_125', 'summon_survive'],
    },

    # ── Tier 3 ──────────────────────────────────────────────────────
    {
        'name': 'Je', 'run_id': 'seed-run-6', 'tier': 3,
        'timestamp': '2026-04-05T14:48:37.360028+00:00',
        'stats': {"max_hp": 175, "current_hp": 175, "attack_dmg": 41, "attack_speed": 0.975,
                  "crit_chance": 0.08, "armor": 0.19, "block_chance": 0.11, "lifesteal": 0.16,
                  "dark_level": 0, "summon_level": 25, "spell_level": 5, "gold": 40,
                  "item_slots": 2, "free_items": 0, "extra_d12": 0, "extra_d3": 0,
                  "removed_dice": 0, "has_risky_die": False, "loaded_high": False,
                  "has_free_reroll": True, "dice_plus_one": False, "has_2_5_die": True,
                  "has_retry_die": False, "has_logic_die": False, "logic_die_pos": 0,
                  "loaded_low": False, "has_mirror_die": False, "has_bomb_die": False,
                  "has_gladiator_key": True, "has_shop_free_reroll": False,
                  "has_item_discount": False, "has_crit_to_aspeed": False,
                  "has_armor_gives_hp": False, "has_gold_level_bonus": False,
                  "has_summon_upgrade": False},
        'items': ['armor_pen', 'spell_heal_summon'],
    },
    {
        'name': 'Batman', 'run_id': 'seed-run-1', 'tier': 3,
        'timestamp': '2026-04-03T19:20:28.950346+00:00',
        'stats': {"max_hp": 250, "current_hp": 250, "attack_dmg": 53, "attack_speed": 1.2,
                  "crit_chance": 0.15, "armor": 0.41, "block_chance": 0.03, "lifesteal": 0.1,
                  "dark_level": 6, "summon_level": 23, "spell_level": 2, "gold": 80,
                  "item_slots": 6, "free_items": 2, "extra_d12": 0, "extra_d3": 0,
                  "removed_dice": 0, "has_risky_die": False, "loaded_high": False,
                  "has_free_reroll": False, "dice_plus_one": False, "has_2_5_die": False,
                  "has_retry_die": False, "has_logic_die": True, "logic_die_pos": 42,
                  "loaded_low": False, "has_mirror_die": True, "has_bomb_die": False,
                  "has_gladiator_key": False, "has_shop_free_reroll": False,
                  "has_item_discount": False, "has_crit_to_aspeed": False,
                  "has_armor_gives_hp": False, "has_gold_level_bonus": False,
                  "has_summon_upgrade": False},
        'items': ['atk_flat', 'crit_freeze'],
    },
]

conn = sqlite3.connect(str(DB_PATH))
conn.execute('DELETE FROM characters')

for c in characters:
    conn.execute(
        '''INSERT INTO characters (name, run_id, timestamp, stats_json, items_json, wins_achieved)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (c['name'], c['run_id'], c['timestamp'],
         json.dumps(c['stats']), json.dumps(c['items']), c['tier'])
    )

conn.commit()
conn.close()

# Verify
conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
rows = conn.execute('SELECT id, name, wins_achieved FROM characters ORDER BY wins_achieved, id').fetchall()
conn.close()

tier_names = {0: 'Tier 0 (Bronze)', 1: 'Tier 1 (Silver)', 2: 'Tier 2 (Gold)', 3: 'Tier 3 (Champion)'}
current_tier = None
for r in rows:
    t = r['wins_achieved']
    if t != current_tier:
        current_tier = t
        print(f"\n  {tier_names.get(t, f'Tier {t}')}:")
    print(f"    [{r['id']}] {r['name']}")

print(f"\nTotal: {len(rows)} characters seeded.")
