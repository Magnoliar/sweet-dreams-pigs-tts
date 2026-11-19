# -*- coding: utf-8 -*-
"""Build English Tabletop Simulator (TTS) Save JSON for Sweet Dreams, Little Pigs!

Reads tts_en/cards_en.js via Node and tts_en/scripts/Global.lua, and outputs:
- tts_en/SweetDreams_EN_TTS_Save.json

Does NOT modify tts/*, sim/*, web/*, print/*, or 规则书.md.
"""
import json
import os
import random
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TTS_EN_DIR = os.path.dirname(os.path.abspath(__file__))
LUA_PATH = os.path.join(TTS_EN_DIR, 'scripts', 'Global.lua')
OUT_JSON = os.path.join(TTS_EN_DIR, 'SweetDreams_EN_TTS_Save.json')

# 2000 x 1600 board pixel geometry
BOARD_W = 2000.0
BOARD_H = 1600.0
GRID_COL_PX = [445.0, 726.5, 1007.0, 1287.0, 1565.5]
GRID_ROW_PX = [224.0, 502.0, 781.0, 1061.0, 1340.5]

YELLOW_TRACK_X = 181.5
YELLOW_TRACK_Y = [
    101.0, 150.0, 248.5, 349.0, 445.0, 544.5, 642.5, 739.5,
    837.5, 936.0, 1034.5, 1132.0, 1231.5, 1330.0, 1427.0, 1476.0,
]

PINK_TRACK_X = 1824.0
PINK_TRACK_Y = [
    1476.0, 1426.5, 1329.5, 1231.5, 1132.5, 1034.0, 936.0, 837.5,
    739.0, 642.0, 542.0, 444.0, 346.5, 246.5, 149.0, 101.0,
]

BOARD_SCALE_X = 5.5
BOARD_SCALE_Z = 5.5
BOARD_ASPECT = BOARD_W / BOARD_H  # 1.25
BOARD_WORLD_HALF_W = 5.5 * BOARD_ASPECT  # 6.875
BOARD_WORLD_HALF_H = 5.5


def file_url(*parts):
    full = os.path.join(ROOT, *parts).replace('\\', '/')
    return f'file:///{full}'


def load_cards_data():
    js = (
        "const C = require('./tts_en/cards_en.js');"
        "console.log(JSON.stringify({"
        "  CARDS: C.CARDS,"
        "  SERIES: C.SERIES,"
        "  HOUSE_RULES: C.HOUSE_RULES,"
        "  RULESET: C.RULESET"
        "}));"
    )
    res = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, check=True, encoding='utf-8')
    return json.loads(res.stdout.strip())


def make_transform(pos, rot=(0.0, 180.0, 0.0), scale=(1.0, 1.0, 1.0)):
    return {
        'posX': round(pos[0], 4),
        'posY': round(pos[1], 4),
        'posZ': round(pos[2], 4),
        'rotX': round(rot[0], 4),
        'rotY': round(rot[1], 4),
        'rotZ': round(rot[2], 4),
        'scaleX': round(scale[0], 4),
        'scaleY': round(scale[1], 4),
        'scaleZ': round(scale[2], 4),
    }


def base_object(name, guid, nickname='', description='', gm_notes='', transform=None, locked=False):
    return {
        'GUID': guid,
        'Name': name,
        'Transform': transform or make_transform((0, 1, 0)),
        'Nickname': nickname,
        'Description': description,
        'GMNotes': gm_notes,
        'ColorDiffuse': {'r': 1.0, 'g': 1.0, 'b': 1.0},
        'LayoutGroupSortIndex': 0,
        'Value': 0,
        'Locked': locked,
        'Grid': True,
        'Snap': True,
        'IgnoreFoW': False,
        'MeasureMovement': False,
        'DragSelectable': True,
        'Autoraise': True,
        'Sticky': True,
        'Tooltip': True,
        'GridProjection': False,
        'HideWhenFaceDown': False,
        'Hands': False,
        'LuaScript': '',
        'LuaScriptState': '',
        'XmlUI': '',
    }


def pixel_to_board_local(px, py):
    lx = (0.5 - px / BOARD_W) * 2.0 * BOARD_ASPECT
    lz = (py / BOARD_H - 0.5) * 2.0
    return {'x': round(lx, 4), 'y': 0.1, 'z': round(lz, 4)}


def pixel_to_world_approx(px, py, y=1.35):
    half_w = BOARD_WORLD_HALF_W
    half_h = BOARD_WORLD_HALF_H
    wx = (px / BOARD_W - 0.5) * 2.0 * half_w
    wz = (0.5 - py / BOARD_H) * 2.0 * half_h
    return (wx, y, wz)


def build_board():
    snaps = []
    for r in range(5):
        for c in range(5):
            snaps.append({
                'Position': pixel_to_board_local(GRID_COL_PX[c], GRID_ROW_PX[r]),
                'Rotation': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            })
    for y in YELLOW_TRACK_Y:
        snaps.append({
            'Position': pixel_to_board_local(YELLOW_TRACK_X, y),
            'Rotation': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        })
    for y in PINK_TRACK_Y:
        snaps.append({
            'Position': pixel_to_board_local(PINK_TRACK_X, y),
            'Rotation': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        })

    board = base_object(
        name='Custom_Tile',
        guid='b0a001',
        nickname='Sweet Dreams 5x5 Quilt Board',
        description='5x5 Cozy Quilt Board with dual 0-15 Dream Star tracks',
        transform=make_transform((0.0, 1.0, 0.0), (0.0, 180.0, 0.0), (BOARD_SCALE_X, 1.0, BOARD_SCALE_Z)),
        locked=True,
    )
    board['CustomImage'] = {
        'ImageURL': file_url('tts_en', '04_Board_5x5_Quilt.png'),
        'ImageSecondaryURL': '',
        'ImageScalar': 1.0,
        'WidthScale': 0.0,
        'CustomTile': {'Type': 3, 'Thickness': 0.25, 'Stackable': False, 'Stretch': True},
    }
    board['AttachedSnapPoints'] = snaps
    return board


def make_custom_deck_def(face_url, back_url, num_w, num_h):
    return {
        'FaceURL': face_url,
        'BackURL': back_url,
        'NumWidth': num_w,
        'NumHeight': num_h,
        'BackIsHidden': True,
        'UniqueBack': False,
        'Type': 0,
    }


def make_card_obj(card_id, guid, deck_key, deck_def, nickname, description, gm_notes, pos, rot):
    obj = base_object(
        name='CardCustom',
        guid=guid,
        nickname=nickname,
        description=description,
        gm_notes=gm_notes,
        transform=make_transform(pos, rot, (1.0, 1.0, 1.0)),
        locked=False,
    )
    obj['CardID'] = card_id
    obj['SidewaysCard'] = False
    obj['Hands'] = True
    obj['HideWhenFaceDown'] = True
    obj['CustomDeck'] = {str(deck_key): deck_def}
    return obj


def make_deck_obj(guid, nickname, description, deck_key, deck_def, cards, pos, rot):
    obj = base_object(
        name='DeckCustom',
        guid=guid,
        nickname=nickname,
        description=description,
        transform=make_transform(pos, rot, (1.0, 1.0, 1.0)),
        locked=False,
    )
    obj['SidewaysCard'] = False
    obj['Hands'] = False
    obj['HideWhenFaceDown'] = True
    obj['DeckIDs'] = [c['CardID'] for c in cards]
    obj['CustomDeck'] = {str(deck_key): deck_def}
    obj['ContainedObjects'] = cards
    return obj


def format_card_meta(card, series_map, role='market'):
    s_list = card['series'] if isinstance(card['series'], list) else [card['series']]
    s_names = ' / '.join(series_map[s]['name'] for s in s_list if s in series_map)
    nick = f"{card['name']} (Cost {card['cost']}☁️ | Play {card['cloud']}☁️ / Dream {card['dreamCloud']}☁️)"
    desc = f"[{s_names}] Cost:{card['cost']}☁️ | Play:{card['cloud']}☁️ | Dream:{card['dreamCloud']}☁️\n{card['text']}\n— {card['flavor']}"
    gm = json.dumps({
        'key': card['key'],
        'name': card['name'],
        'cost': card['cost'],
        'cloud': card['cloud'],
        'dream': card['dreamCloud'],
        'series': s_list,
        'role': role,
    }, ensure_ascii=False, separators=(',', ':'))
    return nick, desc, gm


def build_all_decks_and_cards(data):
    cards_db = data['CARDS']
    series_map = data['SERIES']
    hr_db = data['HOUSE_RULES']
    ruleset = data['RULESET']

    back_url = file_url('tts_en', '00_CardBack_EN.png')
    hr_back_url = file_url('tts_en', '05_HouseRule_CardBack_EN.png')
    deck1_def = make_custom_deck_def(file_url('tts_en', '01_Market_Staple_69_10x7.png'), back_url, 10, 7)
    deck2_def = make_custom_deck_def(file_url('tts_en', '02_Starters_Help_22_6x4.png'), back_url, 6, 4)
    deck3_def = make_custom_deck_def(file_url('tts_en', '03_HouseRules_12_4x3.png'), hr_back_url, 4, 3)

    # 1. Market (61) + Staple (8) = 69 cards (100..168)
    market_keys = []
    for k, n in ruleset['market']:
        market_keys.extend([k] * n)
    assert len(market_keys) == 61

    market_cards = []
    for idx, k in enumerate(market_keys):
        nick, desc, gm = format_card_meta(cards_db[k], series_map, role='market')
        market_cards.append(make_card_obj(
            100 + idx, f'c1{idx:04x}', 1, deck1_def, nick, desc, gm, (-10.8, 1.3, 6.2), (0, 90, 180)
        ))

    rng = random.Random(20261114)
    rng.shuffle(market_cards)
    market_deck = make_deck_obj(
        'd3c001', 'Market Deck (61 cards)', '24 Market card types; shuffle and reveal 5 slots', 1, deck1_def,
        market_cards, (-10.8, 1.3, 6.2), (0, 90, 180)
    )

    staple_k, staple_n = ruleset['staple']
    assert staple_n == 8
    staple_cards = []
    for i in range(staple_n):
        idx = 61 + i
        nick, desc, gm = format_card_meta(cards_db[staple_k], series_map, role='staple')
        staple_cards.append(make_card_obj(
            100 + idx, f'c1{idx:04x}', 1, deck1_def, nick, desc, gm, (-15.4, 1.3, 6.2), (0, 90, 0)
        ))
    staple_deck = make_deck_obj(
        'd3c002', 'Staple Supply: Bedtime Apple (8)', 'Always available to buy for 2☁️', 1, deck1_def,
        staple_cards, (-15.4, 1.3, 6.2), (0, 90, 0)
    )

    # 2. Pink starters (10) + Yellow starters (10) + 2 Help cards = 22 cards (200..221)
    starter_keys = []
    for k, n in ruleset['starters']:
        starter_keys.extend([k] * n)
    assert len(starter_keys) == 10

    pink_cards = []
    for idx, k in enumerate(starter_keys):
        nick, desc, gm = format_card_meta(cards_db[k], series_map, role='pink_starter')
        pink_cards.append(make_card_obj(
            200 + idx, f'c2{idx:04x}', 2, deck2_def, nick, desc, gm, (-7.0, 1.3, -8.2), (0, 180, 180)
        ))
    rng.shuffle(pink_cards)
    pink_deck = make_deck_obj(
        'd3c003', 'Pink Starter Deck (10)', 'Pink Pigs starting deck', 2, deck2_def,
        pink_cards, (-7.0, 1.3, -8.2), (0, 180, 180)
    )

    yellow_cards = []
    for i, k in enumerate(starter_keys):
        idx = 10 + i
        nick, desc, gm = format_card_meta(cards_db[k], series_map, role='yellow_starter')
        yellow_cards.append(make_card_obj(
            200 + idx, f'c2{idx:04x}', 2, deck2_def, nick, desc, gm, (7.0, 1.3, 8.2), (0, 0, 180)
        ))
    rng.shuffle(yellow_cards)
    yellow_deck = make_deck_obj(
        'd3c004', 'Yellow Starter Deck (10)', 'Yellow Pigs starting deck', 2, deck2_def,
        yellow_cards, (7.0, 1.3, 8.2), (0, 0, 180)
    )

    help_gm = json.dumps({'key': 'help', 'name': 'Player Aid', 'type': 'help'}, ensure_ascii=False, separators=(',', ':'))
    help_pink = make_card_obj(
        220, 'c20014', 2, deck2_def, 'Player Aid (Pink)',
        'Turn sequence, icons, 3 play modes & series resonance reference', help_gm, (7.8, 1.15, -8.2), (0, 180, 0)
    )
    help_yellow = make_card_obj(
        221, 'c20015', 2, deck2_def, 'Player Aid (Yellow)',
        'Turn sequence, icons, 3 play modes & series resonance reference', help_gm, (-7.8, 1.15, 8.2), (0, 0, 0)
    )

    # 3. 12 House Rule cards (300..311)
    hr_keys = list(hr_db.keys())
    assert len(hr_keys) == 12
    hr_cards = []
    for idx, hk in enumerate(hr_keys):
        hr = hr_db[hk]
        hr_gm = json.dumps({'key': hr['key'], 'name': hr['name'], 'type': 'house_rule'}, ensure_ascii=False, separators=(',', ':'))
        hr_cards.append(make_card_obj(
            300 + idx, f'c3{idx:04x}', 3, deck3_def,
            f"House Rule: {hr['name']}",
            f"[{hr['tag']}] {hr['text']}\n— {hr['flavor']}",
            hr_gm, (-10.8, 1.3, -6.2), (0, 90, 180)
        ))
    rng.shuffle(hr_cards)
    hr_deck = make_deck_obj(
        'd3c005', "Tonight's House Rules (12)", 'Optional variants: flip 1 card face-up onto the Active House Rule pad', 3, deck3_def,
        hr_cards, (-10.8, 1.3, -6.2), (0, 90, 180)
    )

    return [market_deck, staple_deck, pink_deck, yellow_deck, help_pink, help_yellow, hr_deck]


def build_pigs():
    objs = []
    pink_awake = file_url('tts_en', 'tokens', 'pink_pig_awake.png')
    pink_sleep = file_url('tts_en', 'tokens', 'pink_pig_asleep.png')
    yellow_awake = file_url('tts_en', 'tokens', 'yellow_pig_awake.png')
    yellow_sleep = file_url('tts_en', 'tokens', 'yellow_pig_asleep.png')

    for i, col_idx in enumerate([1, 2, 3]):
        pos = pixel_to_world_approx(GRID_COL_PX[col_idx], GRID_ROW_PX[4], 1.35)
        pig = base_object(
            name='Custom_Tile',
            guid=f'p1910{i+1}',
            nickname=f'Pink Pig #{i+1}',
            description='Press F to flip between Awake and Asleep',
            gm_notes=json.dumps({'type': 'pig', 'color': 'Pink', 'index': i + 1}),
            transform=make_transform(pos, (0, 180, 0), (0.72, 1.0, 0.72)),
        )
        pig['CustomImage'] = {
            'ImageURL': pink_awake,
            'ImageSecondaryURL': pink_sleep,
            'ImageScalar': 1.0,
            'WidthScale': 0.0,
            'CustomTile': {'Type': 3, 'Thickness': 0.2, 'Stackable': False, 'Stretch': True},
        }
        objs.append(pig)

    for i, col_idx in enumerate([1, 2, 3]):
        pos = pixel_to_world_approx(GRID_COL_PX[col_idx], GRID_ROW_PX[0], 1.35)
        pig = base_object(
            name='Custom_Tile',
            guid=f'p1920{i+1}',
            nickname=f'Yellow Pig #{i+1}',
            description='Press F to flip between Awake and Asleep',
            gm_notes=json.dumps({'type': 'pig', 'color': 'Yellow', 'index': i + 1}),
            transform=make_transform(pos, (0, 0, 0), (0.72, 1.0, 0.72)),
        )
        pig['CustomImage'] = {
            'ImageURL': yellow_awake,
            'ImageSecondaryURL': yellow_sleep,
            'ImageScalar': 1.0,
            'WidthScale': 0.0,
            'CustomTile': {'Type': 3, 'Thickness': 0.2, 'Stackable': False, 'Stretch': True},
        }
        objs.append(pig)

    return objs


def build_tokens_and_props():
    objs = []

    pink_m_pos = pixel_to_world_approx(PINK_TRACK_X, PINK_TRACK_Y[0], 1.35)
    pink_m = base_object(
        name='Custom_Tile',
        guid='5c0001',
        nickname='Pink Dream Star Marker',
        description='Tracks Pink score (0-15) along the right track',
        gm_notes=json.dumps({'type': 'score_marker', 'color': 'Pink'}),
        transform=make_transform(pink_m_pos, (0, 180, 0), (0.28, 1.0, 0.28)),
    )
    pink_m['CustomImage'] = {
        'ImageURL': file_url('tts_en', 'tokens', 'score_pink.png'),
        'ImageSecondaryURL': '',
        'ImageScalar': 1.0,
        'WidthScale': 0.0,
        'CustomTile': {'Type': 2, 'Thickness': 0.2, 'Stackable': False, 'Stretch': True},
    }
    objs.append(pink_m)

    yellow_m_pos = pixel_to_world_approx(YELLOW_TRACK_X, YELLOW_TRACK_Y[0], 1.35)
    yellow_m = base_object(
        name='Custom_Tile',
        guid='5c0002',
        nickname='Yellow Dream Star Marker',
        description='Tracks Yellow score (0-15) along the left track',
        gm_notes=json.dumps({'type': 'score_marker', 'color': 'Yellow'}),
        transform=make_transform(yellow_m_pos, (0, 180, 0), (0.28, 1.0, 0.28)),
    )
    yellow_m['CustomImage'] = {
        'ImageURL': file_url('tts_en', 'tokens', 'score_yellow.png'),
        'ImageSecondaryURL': '',
        'ImageScalar': 1.0,
        'WidthScale': 0.0,
        'CustomTile': {'Type': 2, 'Thickness': 0.2, 'Stackable': False, 'Stretch': True},
    }
    objs.append(yellow_m)

    bowl = base_object(
        name='Bowl',
        guid='b0w101',
        nickname='Wooden Snore Bowl',
        description='Holds Snore chips earned this turn',
        transform=make_transform((12.2, 1.05, -6.2), (0, 0, 0), (0.95, 0.95, 0.95)),
        locked=True,
    )
    bowl['ColorDiffuse'] = {'r': 0.56, 'g': 0.36, 'b': 0.22}
    objs.append(bowl)

    bases = [(16.8, 1.2, -3.5), (16.8, 1.2, -1.5), (16.8, 1.2, 0.5)]
    chip_url = file_url('tts_en', 'tokens', 'snore_chip_1.png')
    for i in range(30):
        bx, by, bz = bases[i % 3]
        lvl = i // 3
        chip = base_object(
            name='Custom_Tile',
            guid=f'50c0{i+1:02d}',
            nickname='Snore Chip (1☁️)',
            description='1 Snore currency chip',
            gm_notes=json.dumps({'type': 'snore_chip', 'value': 1}),
            transform=make_transform((bx, by + lvl * 0.16, bz), (0, 180, 0), (0.38, 1.0, 0.38)),
        )
        chip['CustomImage'] = {
            'ImageURL': chip_url,
            'ImageSecondaryURL': '',
            'ImageScalar': 1.0,
            'WidthScale': 0.0,
            'CustomTile': {'Type': 2, 'Thickness': 0.15, 'Stackable': False, 'Stretch': True},
        }
        objs.append(chip)

    blanket_url = file_url('tts_en', 'tokens', 'felt_blanket.png')
    for i in range(6):
        b = base_object(
            name='Custom_Tile',
            guid=f'b1a00{i+1}',
            nickname='Felt Blanket',
            description='Protects 1 of your sleeping pigs from being moved until Wake',
            gm_notes=json.dumps({'type': 'blanket'}),
            transform=make_transform((12.2, 1.2 + i * 0.16, 6.2), (0, 180, 0), (0.62, 1.0, 0.62)),
        )
        b['CustomImage'] = {
            'ImageURL': blanket_url,
            'ImageSecondaryURL': '',
            'ImageScalar': 1.0,
            'WidthScale': 0.0,
            'CustomTile': {'Type': 3, 'Thickness': 0.15, 'Stackable': False, 'Stretch': True},
        }
        objs.append(b)

    pdf = base_object(
        name='Custom_PDF',
        guid='f00001',
        nickname='Sweet Dreams, Little Pigs! Rulebook (EN)',
        description='Click to browse the illustrated English rulebook',
        transform=make_transform((17.0, 1.15, 4.5), (0, 180, 0), (1.2, 1.0, 1.2)),
    )
    pdf['CustomPDF'] = {
        'PDFUrl': file_url('tts_en', 'SweetDreams_Rulebook_EN_TTS.pdf'),
        'PDFPage': 0,
        'PDFPageOffset': 0,
        'PDFPassword': '',
    }
    objs.append(pdf)

    panel = base_object(
        name='BlockSquare',
        guid='c71001',
        nickname='Sweet Dreams Control Panel',
        description='Automated game helper control panel',
        transform=make_transform((12.2, 1.05, 0.0), (0, 180, 0), (6.0, 0.2, 8.8)),
        locked=True,
    )
    panel['ColorDiffuse'] = {'r': 0.28, 'g': 0.20, 'b': 0.15}
    objs.append(panel)

    trash_pad = base_object(
        name='BlockSquare',
        guid='c71002',
        nickname='🔥 Digest Box (Removed Cards)',
        description='Drop Digested Starter cards here; auto-resets on New Game',
        transform=make_transform((17.0, 1.05, -6.2), (0, 180, 0), (3.0, 0.2, 3.6)),
        locked=True,
    )
    trash_pad['ColorDiffuse'] = {'r': 0.36, 'g': 0.22, 'b': 0.17}
    objs.append(trash_pad)

    hr_pad = base_object(
        name='BlockSquare',
        guid='c71003',
        nickname='🌙 Active House Rule Pad',
        description='Place 1 House Rule card face-up here to activate it',
        transform=make_transform((-15.4, 1.05, -6.2), (0, 90, 0), (2.6, 0.2, 3.5)),
        locked=True,
    )
    hr_pad['ColorDiffuse'] = {'r': 0.22, 'g': 0.20, 'b': 0.34}
    objs.append(hr_pad)

    buy_btn_positions = [
        ('b0y001', 'Buy Market Slot 1', (-8.75, 1.05,  2.2)),
        ('b0y002', 'Buy Market Slot 2', (-13.35, 1.05,  2.2)),
        ('b0y003', 'Buy Market Slot 3', (-17.95, 1.05,  2.2)),
        ('b0y004', 'Buy Market Slot 4', (-8.75, 1.05, -2.2)),
        ('b0y005', 'Buy Market Slot 5', (-13.35, 1.05, -2.2)),
        ('b0y006', 'Buy Market Slot 6', (-17.95, 1.05, -2.2)),
        ('b0y007', 'Buy Staple: Bedtime Apple', (-13.35, 1.05, 6.2)),
    ]
    for guid, nick, pos in buy_btn_positions:
        btn = base_object(
            name='BlockSquare',
            guid=guid,
            nickname=nick,
            description='Click to buy card, pay Snores from Bowl, and place on top of your deck',
            transform=make_transform(pos, (0, 90, 0), (1.8, 0.2, 0.6)),
            locked=True,
        )
        btn['ColorDiffuse'] = {'r': 0.96, 'g': 0.78, 'b': 0.35}
        objs.append(btn)

    return objs


def make_hand_trigger(guid, color, pos, rot_y):
    obj = base_object(
        name='HandTrigger',
        guid=guid,
        nickname=f'{color} Hand',
        transform=make_transform(pos, (0.0, rot_y, 0.0), (16.0, 3.0, 2.6)),
        locked=True,
    )
    obj['FogColor'] = color
    return obj


def make_scripting_trigger(guid, nickname, pos, scale):
    return base_object(
        name='ScriptingTrigger',
        guid=guid,
        nickname=nickname,
        transform=make_transform(pos, (0.0, 0.0, 0.0), scale),
        locked=True,
    )


def build_triggers():
    objs = [
        make_hand_trigger('0a0001', 'Pink', (0.0, 3.0, -12.2), 0.0),
        make_hand_trigger('0a0002', 'Yellow', (0.0, 3.0, 12.2), 180.0),
        make_scripting_trigger('20e101', 'PinkPlayZone', (-1.0, 2.0, -8.2), (9.6, 3.0, 4.2)),
        make_scripting_trigger('20e102', 'YellowPlayZone', (1.0, 2.0, 8.2), (9.6, 3.0, 4.2)),
        make_scripting_trigger('20e103', 'PinkDiscardZone', (5.0, 2.0, -8.2), (2.8, 3.0, 3.4)),
        make_scripting_trigger('20e104', 'YellowDiscardZone', (-5.0, 2.0, 8.2), (2.8, 3.0, 3.4)),
        make_scripting_trigger('20e105', 'HouseRuleZone', (-15.4, 2.0, -6.2), (3.5, 3.0, 2.6)),
        make_scripting_trigger('20e106', 'SnoreBowlZone', (12.2, 2.0, -6.2), (2.8, 3.0, 2.8)),
        make_scripting_trigger('20e107', 'TrashZone', (17.0, 2.0, -6.2), (3.0, 3.0, 3.6)),
    ]
    market_slots = [
        (-10.8, 2.0,  2.2),
        (-15.4, 2.0,  2.2),
        (-20.0, 2.0,  2.2),
        (-10.8, 2.0, -2.2),
        (-15.4, 2.0, -2.2),
        (-20.0, 2.0, -2.2),
    ]
    for i, sp in enumerate(market_slots):
        objs.append(make_scripting_trigger(f'20e20{i+1}', f'MarketSlot{i+1}', sp, (3.5, 3.0, 2.6)))
    return objs


def build_xml_ui():
    return """<Panel id="hudRoot" rectAlignment="UpperRight" offsetXY="-14 -60" width="336" height="486" color="#00000000" raycastTarget="false">
  <Panel id="hudCollapsed" active="false" rectAlignment="UpperRight" width="136" height="38" color="#3B291EE6">
    <Button id="btnExpandHud" onClick="onClickToggleHud" color="#F5C759" textColor="#331A0D" fontSize="13" fontStyle="Bold">Show Helper</Button>
  </Panel>
  <Panel id="hudExpanded" active="true" rectAlignment="UpperRight" width="336" height="486" color="#FDF6ECEB">
    <VerticalLayout spacing="6" padding="10 10 10 10" childForceExpandWidth="true" childForceExpandHeight="false">
      <HorizontalLayout spacing="6" preferredHeight="32" childForceExpandWidth="false" childForceExpandHeight="true">
        <Text preferredWidth="236" alignment="MiddleLeft" fontSize="15" fontStyle="Bold" color="#3B291E">Sweet Dreams Helper</Text>
        <Button id="btnCollapseHud" preferredWidth="74" onClick="onClickToggleHud" color="#E8D8C8" textColor="#3B291E" fontSize="13" fontStyle="Bold">Hide</Button>
      </HorizontalLayout>
      <Panel color="#3D291F" preferredHeight="32">
        <Text id="hudStatus" alignment="MiddleCenter" fontSize="13" fontStyle="Bold" color="#FFF0D1">R1 · Pink Turn | Pink 0★ vs Yellow 0★</Text>
      </Panel>
      <Button preferredHeight="36" onClick="onClickNewGame" color="#F5C759" textColor="#331A0D" fontSize="14" fontStyle="Bold">[Setup] New Game / Reset</Button>
      <HorizontalLayout spacing="8" preferredHeight="242" childForceExpandWidth="true" childForceExpandHeight="true">
        <Panel color="#FDE8EF">
          <VerticalLayout spacing="5" padding="6 6 6 6" childForceExpandWidth="true" childForceExpandHeight="false">
            <Text preferredHeight="24" alignment="MiddleCenter" fontSize="14" fontStyle="Bold" color="#8C1D40">Pink Pigs</Text>
            <Button preferredHeight="36" onClick="onClickPinkWake" color="#FAB8CE" textColor="#400F1F" fontSize="13" fontStyle="Bold">Wake &amp; Score</Button>
            <Button preferredHeight="36" onClick="onClickPinkSnore" color="#F5CCD9" textColor="#400F1F" fontSize="13" fontStyle="Bold">Tally Snores</Button>
            <Button preferredHeight="36" onClick="onClickPinkEnd" color="#F09EB8" textColor="#400F1F" fontSize="13" fontStyle="Bold">End Turn</Button>
            <HorizontalLayout spacing="4" preferredHeight="32" childForceExpandWidth="true" childForceExpandHeight="true">
              <Button onClick="onClickPinkDrawOne" color="#FCE0EA" textColor="#400F1F" fontSize="11" fontStyle="Bold">+1 Card</Button>
              <Button onClick="onClickPinkReshuffle" color="#EAD1DB" textColor="#400F1F" fontSize="11" fontStyle="Bold">Shuffle</Button>
            </HorizontalLayout>
            <HorizontalLayout spacing="4" preferredHeight="32" childForceExpandWidth="true" childForceExpandHeight="true">
              <Button onClick="onClickPinkStarPlus" color="#FFD673" textColor="#400F1F" fontSize="13" fontStyle="Bold">+1★</Button>
              <Button onClick="onClickPinkStarMinus" color="#E0D1D6" textColor="#400F1F" fontSize="13" fontStyle="Bold">-1★</Button>
            </HorizontalLayout>
          </VerticalLayout>
        </Panel>
        <Panel color="#FEF6DC">
          <VerticalLayout spacing="5" padding="6 6 6 6" childForceExpandWidth="true" childForceExpandHeight="false">
            <Text preferredHeight="24" alignment="MiddleCenter" fontSize="14" fontStyle="Bold" color="#734E08">Yellow Pigs</Text>
            <Button preferredHeight="36" onClick="onClickYellowWake" color="#FAD973" textColor="#40290A" fontSize="13" fontStyle="Bold">Wake &amp; Score</Button>
            <Button preferredHeight="36" onClick="onClickYellowSnore" color="#FAE89E" textColor="#40290A" fontSize="13" fontStyle="Bold">Tally Snores</Button>
            <Button preferredHeight="36" onClick="onClickYellowEnd" color="#F0C74D" textColor="#40290A" fontSize="13" fontStyle="Bold">End Turn</Button>
            <HorizontalLayout spacing="4" preferredHeight="32" childForceExpandWidth="true" childForceExpandHeight="true">
              <Button onClick="onClickYellowDrawOne" color="#FCF2CC" textColor="#40290A" fontSize="11" fontStyle="Bold">+1 Card</Button>
              <Button onClick="onClickYellowReshuffle" color="#E6DBB8" textColor="#40290A" fontSize="11" fontStyle="Bold">Shuffle</Button>
            </HorizontalLayout>
            <HorizontalLayout spacing="4" preferredHeight="32" childForceExpandWidth="true" childForceExpandHeight="true">
              <Button onClick="onClickYellowStarPlus" color="#FFD673" textColor="#40290A" fontSize="13" fontStyle="Bold">+1★</Button>
              <Button onClick="onClickYellowStarMinus" color="#E0DCC7" textColor="#40290A" fontSize="13" fontStyle="Bold">-1★</Button>
            </HorizontalLayout>
          </VerticalLayout>
        </Panel>
      </HorizontalLayout>
      <HorizontalLayout spacing="8" preferredHeight="32" childForceExpandWidth="true" childForceExpandHeight="true">
        <Button onClick="onClickSnorePlus" color="#D1EBF7" textColor="#1A334D" fontSize="13" fontStyle="Bold">Bowl +1 Snore</Button>
        <Button onClick="onClickSnoreMinus" color="#D6D6E0" textColor="#2E2938" fontSize="13" fontStyle="Bold">Bowl -1 Snore</Button>
      </HorizontalLayout>
      <Panel color="#523D2E" preferredHeight="48">
        <VerticalLayout spacing="2" padding="4 4 4 4" childForceExpandWidth="true" childForceExpandHeight="true">
          <Text alignment="MiddleCenter" fontSize="10" color="#F5EBDC">90°=Skip(0☁) | Face-Down=Dream | Drag Digested Starters to Box</Text>
          <Text alignment="MiddleCenter" fontSize="10" color="#FFE099">Adjust conditional/instant ☁ &amp; ★ bonuses manually with +/-</Text>
        </VerticalLayout>
      </Panel>
    </VerticalLayout>
  </Panel>
</Panel>"""


def build_save():
    data = load_cards_data()
    with open(LUA_PATH, 'r', encoding='utf-8') as f:
        lua_script = f.read()

    object_states = [build_board()]
    object_states.extend(build_all_decks_and_cards(data))
    object_states.extend(build_pigs())
    object_states.extend(build_tokens_and_props())
    object_states.extend(build_triggers())

    save = {
        'SaveName': 'Sweet Dreams, Little Pigs! (English)',
        'GameMode': 'Sweet Dreams, Little Pigs!',
        'Date': '11/19/2026 10:00:00 AM',
        'VersionNumber': 'v13.2',
        'GameType': 'Board Game',
        'GameComplexity': 'Light-Medium',
        'PlayingTime': [15, 25],
        'PlayerCounts': [2, 2],
        'Tags': ['Card Game', 'Deckbuilding', 'Strategy', 'English'],
        'Gravity': 0.5,
        'PlayArea': 0.5,
        'Table': 'Table_RPG',
        'Sky': 'Sky_Museum',
        'Note': 'Sweet Dreams, Little Pigs! — 2-player cozy deckbuilding & spatial grid battle. Use the Helper panel on the right for one-click Setup, Wake & Score, Tally Snores, and End Turn!',
        'TabStates': {},
        'Grid': {
            'Type': 0,
            'Lines': False,
            'Color': {'r': 0.0, 'g': 0.0, 'b': 0.0},
            'Opacity': 0.75,
            'ThickLines': False,
            'Snapping': False,
            'Offset': False,
            'BothSnapping': False,
            'xSize': 2.0,
            'ySize': 2.0,
            'PosOffset': {'x': 0.0, 'y': 1.0, 'z': 0.0},
        },
        'Lighting': {
            'LightIntensity': 0.54,
            'LightColor': {'r': 1.0, 'g': 0.9804, 'b': 0.8902},
            'AmbientIntensity': 1.3,
            'AmbientType': 0,
            'AmbientSkyColor': {'r': 0.5, 'g': 0.5, 'b': 0.5},
            'AmbientEquatorColor': {'r': 0.5, 'g': 0.5, 'b': 0.5},
            'AmbientGroundColor': {'r': 0.5, 'g': 0.5, 'b': 0.5},
            'ReflectionIntensity': 1.0,
            'LutIndex': 0,
            'LutContribution': 1.0,
        },
        'Hands': {
            'Enable': True,
            'DisableUnused': False,
            'Hiding': 0,
        },
        'Turns': {
            'Enable': False,
            'Type': 0,
            'TurnOrder': ['Pink', 'Yellow'],
            'Reverse': False,
            'SkipEmpty': False,
            'DisableInteractions': False,
            'PassTurns': True,
        },
        'CameraStates': [
            {
                'Name': 'Table Overview',
                'Position': {'x': 0.0, 'y': 1.2, 'z': 0.0},
                'Rotation': {'x': 55.0, 'y': 0.0, 'z': 0.0},
                'Distance': 22.0,
                'Zoomed': False,
            },
            {
                'Name': 'Main Board',
                'Position': {'x': 0.0, 'y': 1.2, 'z': 0.0},
                'Rotation': {'x': 68.0, 'y': 0.0, 'z': 0.0},
                'Distance': 12.5,
                'Zoomed': False,
            },
            {
                'Name': 'Control Panel',
                'Position': {'x': 12.2, 'y': 1.2, 'z': 0.0},
                'Rotation': {'x': 65.0, 'y': 0.0, 'z': 0.0},
                'Distance': 10.5,
                'Zoomed': False,
            },
            {
                'Name': 'Market & House Rules',
                'Position': {'x': -14.8, 'y': 1.2, 'z': 0.0},
                'Rotation': {'x': 62.0, 'y': 0.0, 'z': 0.0},
                'Distance': 14.0,
                'Zoomed': False,
            },
        ],
        'LuaScript': lua_script,
        'LuaScriptState': '',
        'XmlUI': build_xml_ui(),
        'ObjectStates': object_states,
    }

    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(save, f, ensure_ascii=False, indent=2)

    print(f'Generated {OUT_JSON} with {len(object_states)} top-level ObjectStates.')


if __name__ == '__main__':
    build_save()
