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
    6:  {'attr': 'item_slots',    'per_die':  0,    'threshold':  None,  'has_threshold': False, 'special': 'research'},
    7:  {'attr': 'gold',          'per_die':  20,   'threshold':  20,    'has_threshold': True},
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
     'desc': 'Gaining armor upgrades also gives HP (1% armor → 2 HP).'},
    {'id': 'shop_free_reroll', 'name': 'Oracle Lens',         'tier': 1, 'cost': 100,
     'desc': 'Future shops and forges each have 1 free reroll.'},
    {'id': 'item_discount',    'name': 'Merchant Badge',      'tier': 1, 'cost': 100,
     'desc': 'Item costs are reduced by 20%.'},
    {'id': 'gold_level_bonus', 'name': 'Gold Vein',           'tier': 1, 'cost': 100,
     'desc': 'Gold upgrades give 5 extra gold per upgrade.'},
    {'id': 'bounty_50g',       'name': 'Bounty Token',        'tier': 1, 'cost': 100,
     'desc': 'Gain 50 gold each time you kill an enemy.'},
    {'id': 'summon_survive',   'name': 'Soul Tether',         'tier': 1, 'cost': 100,
     'desc': 'Your summon survives fights and gains 1 level per fight won.'},
    {'id': 'block_reflect',    'name': 'Thorned Buckler',     'tier': 1, 'cost': 100,
     'desc': 'Blocked damage is returned to the attacker.'},
    {'id': 'block_atk_buff',   'name': "Guardian's Edge",     'tier': 1, 'cost': 100,
     'desc': 'Blocking an enemy attack increases your attack damage by 5 for 2s.'},
    {'id': 'lifesteal_spell',  'name': 'Siphon Stone',        'tier': 1, 'cost': 100,
     'desc': 'Lifesteal now also applies to spell damage.'},
    {'id': 'lifesteal_5pct',   'name': 'Vampiric Pendant',    'tier': 1, 'cost': 100,
     'desc': '+5% permanent lifesteal.'},
    {'id': 'heal_on_attack',   'name': 'Bloodbond Hilt',      'tier': 1, 'cost': 100,
     'desc': 'Heal 3 HP on every attack hit.'},

    # ── Tier 2 — second and third pre-boss shops ───────────────────────────
    {'id': 'atk_execute',      'name': 'Finishing Blade',     'tier': 2, 'cost': 100,
     'desc': '+15 attack damage when the enemy is below 20% HP.'},
    {'id': 'armor_pen',        'name': 'Armor Shredder',      'tier': 2, 'cost': 100,
     'desc': 'Your attacks ignore all enemy armor.'},
    {'id': 'berserker',        'name': 'Berserker Band',      'tier': 2, 'cost': 100,
     'desc': 'Gain 20% attack speed when below 50% HP.'},
    {'id': 'crit_to_aspeed',   'name': 'Swiftcrit Rune',      'tier': 2, 'cost': 100,
     'desc': 'Future crit upgrades convert to attack speed instead.'},
    {'id': 'crit_freeze',      'name': 'Frostcrit Gem',       'tier': 2, 'cost': 100,
     'desc': 'Crits freeze the enemy, slowing their attack speed by 50% for 2s.'},
    {'id': 'crit_lifesteal',   'name': 'Crimson Fang',        'tier': 2, 'cost': 100,
     'desc': 'Crits heal for the bonus crit damage. Disables normal lifesteal.'},
    {'id': 'armor_to_spell',   'name': 'Arcane Dissolution',  'tier': 2, 'cost': 100,
     'desc': 'Remove all your armor and gain that much as spell levels (5% → 1 level).'},
    {'id': 'hp_to_atk',        'name': 'Bloodprice Sigil',    'tier': 2, 'cost': 100,
     'desc': 'Gain attack equal to 5% of your max HP.'},
    {'id': 'hp_double_armor',  'name': 'Ironflesh Pact',      'tier': 2, 'cost': 100,
     'desc': 'Double your max HP and gain -30% armor.'},
    {'id': 'research_2slots',  'name': "Scholar's Tome",      'tier': 2, 'cost': 100,
     'desc': 'Gain 2 item slots and 2 free item credits.'},
    {'id': 'summon_upgrade',   'name': "Summoner's Codex",    'tier': 2, 'cost': 100,
     'desc': 'Upgrade summon abilities: enrage at 35% HP, spell vamp 15%, dragon aura 10%.'},
    {'id': 'spell_fire',       'name': 'Flame Rune',          'tier': 2, 'cost': 100,
     'desc': 'Your spell burns enemies for 10% of spell damage per second over 3s.'},
    {'id': 'spell_frost',      'name': 'Frost Staff',         'tier': 2, 'cost': 100,
     'desc': 'Your spell slows enemy attack speed by 50% for 3s.'},
    {'id': 'spell_heal_summon','name': 'Life Conduit',        'tier': 2, 'cost': 100,
     'desc': 'Your spell heals your summon instead of damaging (1 heal per 2 spell dmg).'},
    {'id': 'armor_to_block',   'name': 'Shield Conversion',   'tier': 2, 'cost': 100,
     'desc': 'Convert all armor to block (1% armor → 0.5% block).'},
]

FORGE_LEVELS = [
    # ── Forge I  (after Level 1 boss) ──────────────────────────────────────
    [
        {
            'id':   'add_d12',
            'name': 'Add d12',
            'desc': 'Add a 12-sided die to your pool permanently. '
                    'Every future upgrade phase you roll 7 dice — '
                    'the d12 can show any value 1-12, opening paths '
                    'to higher numbers like 7, 8, 9, 10, 11 and 12.',
            'icon': '🎲',
        },
        {
            'id':   'add_d3',
            'name': 'Add d3',
            'desc': 'Add a 3-sided die to your pool permanently. '
                    'It always rolls 1, 2, or 3 — reliable fuel for '
                    'Attack Speed, Attack Damage, and Crit upgrades.',
            'icon': '🟢',
        },
        {
            'id':   'remove_die',
            'name': 'Remove a Die',
            'desc': 'Permanently remove one d6 from your pool (5 dice total). '
                    'Fewer dice means less noise and more control over '
                    'which numbers you hit.',
            'icon': '❌',
        },
    ],
    # ── Forge II  (after Level 2 boss) ─────────────────────────────────────
    [
        {
            'id':   'loaded_high',
            'name': 'Load: High Numbers',
            'desc': 'All your dice are loaded toward high faces. '
                    'Each die has 3/12 chance to roll 4, 5, or 6 '
                    'but only 1/12 chance to roll 1, 2, or 3 — '
                    'great for Armor, HP, and Research upgrades.',
            'icon': '⚖️',
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
            'id':   'risky_die',
            'name': 'Risky Die',
            'desc': 'Replace one d6 with a Risky Die whose faces are '
                    '1, 2, 3, 10, 11, 12. High ceiling, high floor — '
                    'great for reaching the hardest numbers.',
            'icon': '🎰',
        },
    ],
]

ATTACK_SPEED_CAP = 5.0  # maximum attacks per second
