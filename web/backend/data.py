"""
Static game data — all constants, stat definitions, enemy tables, shop items, forge menus.
Nothing here has logic; it's all configuration.
"""

STAT_DEFS = {
    1:  {'attr': 'attack_speed',  'per_die': 0.025, 'threshold': 0.025,  'has_threshold': True},
    2:  {'attr': 'attack_dmg',    'per_die':  1,    'threshold':  1,     'has_threshold': True},
    3:  {'attr': 'crit_chance',   'per_die':  0.01, 'threshold':  0.01,  'has_threshold': True},
    4:  {'attr': 'armor',         'per_die':  0.02, 'threshold':  0.02,  'has_threshold': True},
    5:  {'attr': 'max_hp',        'per_die':  5,    'threshold':  5,     'has_threshold': True},
    6:  {'attr': 'gold',          'per_die':  20,   'threshold':  20,    'has_threshold': True},
    7:  {'attr': 'item_slots',    'per_die':  0,    'threshold':  None,  'has_threshold': False, 'special': 'research'},
    8:  {'attr': 'summon_level',  'per_die':  1,    'threshold':  1,     'has_threshold': True},
    9:  {'attr': 'spell_level',   'per_die':  1,    'threshold':  1,     'has_threshold': True},
    10: {'attr': 'block_chance',  'per_die':  0.02, 'threshold':  0.02,  'has_threshold': True},
    11: {'attr': 'lifesteal',     'per_die':  0.02, 'threshold':  0.02,  'has_threshold': True},
    12: {'attr': 'dark_level',    'per_die':  1,    'threshold':  1,     'has_threshold': True},
}

SUMMON_TIERS = [
    {'min_level':  1, 'name': 'Imp',      'attack':  1, 'speed': 2.0, 'hp':  10},
    {'min_level':  6, 'name': 'Wolf',     'attack':  3, 'speed': 2.0, 'hp':  25},
    {'min_level': 12, 'name': 'Orc',      'attack':  6, 'speed': 2.0, 'hp':  50},
    {'min_level': 18, 'name': 'Skeleton', 'attack': 11, 'speed': 2.0, 'hp': 100},
    {'min_level': 24, 'name': 'Dragon',   'attack': 18, 'speed': 2.0, 'hp': 200},
]

LEVELS = [
    {
        'level': 1,
        'upgrade_turns': 6,
        'enemies': [
            {'name': 'Human Soldier',       'hp': 150, 'attack':  4, 'speed': 1.5, 'is_boss': False},
            {'name': 'Angry Human Soldier', 'hp': 150, 'attack':  9, 'speed': 1.5, 'is_boss': False},
            {'name': 'Bandit Captain',      'hp': 600, 'attack': 10, 'speed': 2.0, 'is_boss': True},
        ],
    },
    {
        'level': 2,
        'upgrade_turns': 5,
        'enemies': [
            {'name': 'Orc Warrior',   'hp': 350,  'attack': 14, 'speed': 2.0, 'armor': 0.10, 'is_boss': False},
            {'name': 'Orc Berserker', 'hp': 350,  'attack': 18, 'speed': 1.5, 'armor': 0.10, 'regen': 3, 'is_boss': False},
            {'name': 'Orc Warchief',  'hp': 1200, 'attack': 16, 'speed': 2.0, 'armor': 0.10, 'regen': 3, 'is_boss': True},
        ],
    },
    {
        'level': 3,
        'upgrade_turns': 4,
        'enemies': [
            {'name': 'Dark Knight',  'hp': 600,  'attack': 26, 'speed': 2.0, 'armor': 0.20, 'is_boss': False},
            {'name': 'Shadow Mage',  'hp': 1000, 'attack': 28, 'speed': 1.5, 'armor': 0.20, 'lifesteal': 0.5, 'is_boss': False},
            {'name': 'Demon Lord',   'hp': 2000, 'attack': 35, 'speed': 1.8, 'lifesteal': 0.5, 'is_boss': True},
        ],
    },
]

SHOP_ITEMS = [
    # ── Tier 1 — first pre-boss shop ──────────────────────────────────────
    {'id': 'atk_flat',         'name': 'Whetstone',           'tier': 1, 'cost': 100,
     'desc': '+5 permanent attack damage.'},
    {'id': 'triple_hit',       'name': 'Fury Talisman',       'tier': 1, 'cost': 100,
     'desc': 'Every 3rd attack deals an additional 20 damage.'},
    {'id': 'crit_125',         'name': 'Sharpshooter Lens',   'tier': 1, 'cost': 100,
     'desc': 'Crits now deal 2.25× damage instead of 2×.'},
    {'id': 'armor_flat',       'name': 'Iron Plate',          'tier': 1, 'cost': 100,
     'desc': '+10% permanent armor.'},
    {'id': 'armor_hp_ratio',   'name': 'Bulwark Rune',        'tier': 1, 'cost': 100,
     'desc': 'Gaining armor upgrades also gives HP (1% armor → 1 HP).'},
    {'id': 'shop_free_reroll', 'name': 'Oracle Lens',         'tier': 1, 'cost': 100,
     'desc': 'Future shops and forges each have 1 free reroll.'},
    {'id': 'item_discount',    'name': 'Merchant Badge',      'tier': 1, 'cost': 100,
     'desc': 'Item costs are reduced by 20%.'},
    {'id': 'gold_level_bonus', 'name': 'Gold Vein',           'tier': 1, 'cost': 100,
     'desc': 'Gold upgrades give 10 extra gold per upgrade.'},
    {'id': 'bounty_50g',       'name': 'Bounty Token',        'tier': 1, 'cost': 100,
     'desc': 'Gain 50 gold each time you kill an enemy.'},
    {'id': 'summon_survive',   'name': 'Iron Pelt',           'tier': 1, 'cost': 100,
     'desc': 'Your summon has 10% armor — all damage it takes is reduced by 10%.'},
    {'id': 'block_reflect',    'name': 'Thorned Buckler',     'tier': 1, 'cost': 100,
     'desc': 'Blocked damage is returned to the attacker.'},
    {'id': 'block_atk_buff',   'name': "Guardian's Edge",     'tier': 1, 'cost': 100,
     'desc': 'Blocking an enemy attack increases your attack damage by 5 for 2s.'},
    {'id': 'lifesteal_spell',  'name': 'Siphon Stone',        'tier': 1, 'cost': 100,
     'desc': 'Spell damage heals you for 50% of your lifesteal rate.'},
    {'id': 'lifesteal_5pct',   'name': 'Vampiric Pendant',    'tier': 1, 'cost': 100,
     'desc': '+5% permanent lifesteal.'},
    {'id': 'heal_on_attack',   'name': 'Bloodbond Hilt',      'tier': 1, 'cost': 100,
     'desc': 'Heal 3 HP on every attack hit.'},
    {'id': 'gladiator_key',    'name': 'Gladiator Key',        'tier': 1, 'cost': 100,
     'desc': 'Grants entry to the Gladiator Showdown after a victorious run. '
             'Without this key your run will not be recorded.'},

    # ── Tier 2 — second pre-boss shop ─────────────────────────────────────
    {'id': 'atk_execute',      'name': 'Finishing Blade',     'tier': 2, 'cost': 100,
     'desc': '+15 attack damage when the enemy is below 20% HP.'},
    {'id': 'armor_pen',        'name': 'Armor Shredder',      'tier': 2, 'cost': 100,
     'desc': 'Your attacks ignore all enemy armor.'},
    {'id': 'berserker',        'name': 'Berserker Band',      'tier': 2, 'cost': 100,
     'desc': 'Gain 20% attack speed when below 50% HP.'},
    {'id': 'crit_to_aspeed',   'name': 'Swiftcrit Rune',      'tier': 2, 'cost': 100,
     'desc': 'Future crit upgrades convert to attack speed instead.'},
    {'id': 'crit_freeze',      'name': 'Frostcrit Gem',       'tier': 2, 'cost': 100,
     'desc': 'Crits freeze the enemy, slowing their attack speed by 30% for 2s.'},
    {'id': 'crit_lifesteal',   'name': 'Crimson Fang',        'tier': 2, 'cost': 100,
     'desc': 'Crits heal for the bonus crit damage. Disables normal lifesteal.'},
    {'id': 'armor_to_spell',   'name': 'Arcane Dissolution',  'tier': 2, 'cost': 100,
     'desc': 'Remove all your armor and gain that much as spell levels (5% → 1 level).'},
    {'id': 'hp_to_atk',        'name': 'Bloodprice Sigil',    'tier': 2, 'cost': 100,
     'desc': 'Gain attack equal to 5% of your max HP.'},
    {'id': 'hp_double_armor',  'name': 'Ironflesh Pact',      'tier': 2, 'cost': 100,
     'desc': 'Double your max HP and gain -30% armor.'},
    {'id': 'research_2slots',  'name': "Scholar's Tome",      'tier': 1, 'cost': 100,
     'desc': 'Gain 3 item slots.'},
    {'id': 'summon_upgrade',   'name': "Summoner's Codex",    'tier': 2, 'cost': 100,
     'desc': 'Your summon heals itself for 10% of the damage it deals (lifesteal).'},
    {'id': 'spell_fire',       'name': 'Flame Rune',          'tier': 2, 'cost': 100,
     'desc': 'Your spell burns enemies for 10% of spell damage per second over 3s.'},
    {'id': 'spell_frost',      'name': 'Frost Staff',         'tier': 2, 'cost': 100,
     'desc': 'Your spell slows enemy attack speed by 30% for 3s.'},
    {'id': 'spell_heal_summon','name': 'Life Conduit',        'tier': 2, 'cost': 100,
     'desc': 'Your spell heals your summon instead of damaging (1 heal per 2 spell dmg).'},
    {'id': 'armor_to_block',   'name': 'Shield Conversion',   'tier': 2, 'cost': 100,
     'desc': 'Convert all armor to block (1% armor → 0.5% block).'},
    {'id': 'gladiator_key',    'name': 'Gladiator Key',        'tier': 2, 'cost': 150,
     'desc': 'Grants entry to the Gladiator Showdown after a victorious run. '
             'Without this key your run will not be recorded.'},

    # ── Tier 3 — third pre-boss shop ──────────────────────────────────────
    {'id': 'gladiator_key',    'name': 'Gladiator Key',        'tier': 3, 'cost': 200,
     'desc': 'Grants entry to the Gladiator Showdown after a victorious run. '
             'Without this key your run will not be recorded.'},
]

FORGE_LEVELS = [
    # ── Forge I  (after Level 1 boss) — pool of 6, 3 shown randomly ───────
    [
        {
            'id':   'add_d12',
            'name': 'Add d12',
            'desc': 'Add a 12-sided die to your pool permanently. '
                    'Can show any value 1–12, opening paths to '
                    'higher numbers like 7, 8, 9, 10, 11, and 12.',
            'icon': '🎲',
        },
        {
            'id':   'add_d3',
            'name': 'Add d3',
            'desc': 'Add a 3-sided die to your pool permanently. '
                    'Always rolls 1, 2, or 3 — reliable fuel for '
                    'Speed, Damage, and Crit upgrades.',
            'icon': '🟢',
        },
        {
            'id':   'add_bomb_die',
            'name': 'Bomb Die',
            'desc': 'Extra die that auto-stashes its value at '
                    'the start of every turn — if not collected on the first roll it is stashed automatically.',
            'icon': '💣',
        },
        {
            'id':   'add_2_5_die',
            'name': 'Binary Die',
            'desc': 'Add a 6-sided die that can only land on 2 or 5. '
                    'Reliable, focused — always feeds Damage or HP.',
            'icon': '⚀',
        },
        {
            'id':   'add_retry_die',
            'name': 'Retry Die',
            'desc': 'Add a 6-sided die that can be rerolled once per '
                    'turn. Select it alone to get a second chance '
                    'at a better value.',
            'icon': '🔁',
        },
        {
            'id':   'add_logic_die',
            'name': 'Logic Die',
            'desc': 'Add a 6-sided die that rolls in a fixed sequence: '
                    '1→2→3→4→5→6→1→… throughout the entire run. '
                    'Predictable — if you remember where it was.',
            'icon': '🔢',
        },
    ],
    # ── Forge II  (after Level 2 boss) — pool of 6, 3 shown randomly ─────────
    [
        {
            'id':   'risky_die',
            'name': 'Risky Die',
            'desc': 'Add a 6-sided die whose faces are 1, 2, 3, 10, 11, 12. '
                    'High ceiling, high floor — great for reaching the hardest numbers.',
            'icon': '🎰',
        },
        {
            'id':   'free_reroll',
            'name': 'Free Reroll',
            'desc': 'Once per upgrade turn, before selecting a number, '
                    'you may reroll all your dice for free. '
                    'It does not cost a turn.',
            'icon': '🔄',
        },
        {
            'id':   'loaded_high',
            'name': 'Load: High Numbers',
            'desc': 'All normal dice are weighted toward high faces. '
                    'Each d6 has 2× more chance to roll 4, 5, or 6 '
                    'than 1, 2, or 3.',
            'icon': '⬆️',
        },
        {
            'id':   'loaded_low',
            'name': 'Load: Low Numbers',
            'desc': 'All normal dice are weighted toward low faces. '
                    'Each d6 has 2× more chance to roll 1, 2, or 3 '
                    'than 4, 5, or 6.',
            'icon': '⬇️',
        },
        {
            'id':   'add_mirror_die',
            'name': 'Mirror Die',
            'desc': 'Add a 6-sided die that always copies the highest '
                    'value rolled among your other dice. '
                    'Doubles your best result every roll.',
            'icon': '🪞',
        },
        {
            'id':   'dice_plus_one',
            'name': 'Sharpened Dice',
            'desc': 'All your normal d6s permanently roll +1 higher '
                    '(2–7 instead of 1–6), pushing them into '
                    'mid and high stat territory.',
            'icon': '⬆️',
        },
    ],
]

ATTACK_SPEED_CAP = 5.0  # maximum attacks per second
