# -*- coding: utf-8 -*-
"""Build complete English Tabletop Simulator (TTS) Mod Image Pack in tts_en/ for Sweet Dreams, Little Pigs!

Outputs in tts_en/:
- 00_CardBack_EN.png                 (520 x 720, English titled card back, zero bleed)
- 01_Market_Staple_69_10x7.png       (3900 x 3780, 10x7 grid of 390x540 cards: 61 market + 8 apple)
- 02_Starters_Help_22_6x4.png        (2340 x 2160, 6x4 grid of 390x540 cards: 10 pink + 10 yellow + 2 help)
- 03_HouseRules_12_4x3.png           (2080 x 2160, 4x3 grid of 520x720 cards: 12 house rules)
- 04_Board_5x5_Quilt.png             (2000 x 1600, language-independent 5x5 quilt board)
- 05_HouseRule_CardBack_EN.png       (520 x 720, English titled house rule card back)
- SweetDreams_EN_Thumbnail.png       (512 x 512, English TTS save thumbnail)
- tokens/pink_pig_awake.png          (512 x 512 RGBA transparent)
- tokens/pink_pig_asleep.png         (512 x 512 RGBA transparent)
- tokens/yellow_pig_awake.png        (512 x 512 RGBA transparent)
- tokens/yellow_pig_asleep.png       (512 x 512 RGBA transparent)
- tokens/score_pink.png              (512 x 512 RGBA transparent)
- tokens/score_yellow.png            (512 x 512 RGBA transparent)
- tokens/snore_chip_1.png            (512 x 512 RGBA transparent)
- tokens/felt_blanket.png            (512 x 512 RGBA transparent)

Does NOT modify tts/*, sim/*, web/*, print/*, or 规则书.md.
"""
import functools
import json
import math
import os
import shutil
import subprocess
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TTS_ZH_DIR = os.path.join(ROOT, 'tts')
TTS_EN_DIR = os.path.dirname(os.path.abspath(__file__))
TOKENS_EN_DIR = os.path.join(TTS_EN_DIR, 'tokens')

TMP_DECK_HTML = os.path.join(TTS_EN_DIR, '_tts_decks_en.html')
TMP_BACKS_HTML = os.path.join(TTS_EN_DIR, '_tts_backs_en.html')

SHEETS_SPEC = [
    {
        'id': 'market',
        'filename': '01_Market_Staple_69_10x7.png',
        'cols': 10,
        'rows': 7,
        'card_w': 390,
        'card_h': 540,
    },
    {
        'id': 'starters',
        'filename': '02_Starters_Help_22_6x4.png',
        'cols': 6,
        'rows': 4,
        'card_w': 390,
        'card_h': 540,
    },
    {
        'id': 'houserules',
        'filename': '03_HouseRules_12_4x3.png',
        'cols': 4,
        'rows': 3,
        'card_w': 520,
        'card_h': 720,
    },
]

TOKEN_COPY_MAP = {
    '粉小猪_清醒.png': 'pink_pig_awake.png',
    '粉小猪_熟睡.png': 'pink_pig_asleep.png',
    '黄小猪_清醒.png': 'yellow_pig_awake.png',
    '黄小猪_熟睡.png': 'yellow_pig_asleep.png',
    '美梦分标记_粉.png': 'score_pink.png',
    '美梦分标记_黄.png': 'score_yellow.png',
    '呼噜筹码_1点.png': 'snore_chip_1.png',
    '毛毡小被子.png': 'felt_blanket.png',
}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def load_tts_decks():
    js = (
        "const C = require('./tts_en/cards_en.js');"
        "const R = C.RULESET;"
        "const starters = [];"
        "for (const [k, n] of R.starters) for (let i=0;i<n;i++) starters.push(k);"
        "const market = [];"
        "for (const [k, n] of R.market) for (let i=0;i<n;i++) market.push(k);"
        "const staple = [];"
        "for (let i=0;i<R.staple[1];i++) staple.push(R.staple[0]);"
        "const hrKeys = Object.keys(C.HOUSE_RULES);"
        "console.log(JSON.stringify({starters, market, staple, hrKeys, allKeys: Object.keys(C.CARDS)}));"
    )
    res = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, check=True, encoding='utf-8')
    data = json.loads(res.stdout.strip())

    sheet_market = data['market'] + data['staple']
    assert len(sheet_market) == 69
    sheet_starters = data['starters'] + data['starters'] + ['__help__', '__help__']
    assert len(sheet_starters) == 22
    sheet_hr = ['__hr__' + k for k in data['hrKeys']]
    assert len(sheet_hr) == 12
    return {
        'market': sheet_market,
        'starters': sheet_starters,
        'houserules': sheet_hr,
        'allKeys': data['allKeys'],
    }


def copy_board_and_tokens():
    src_board = os.path.join(TTS_ZH_DIR, '04_主棋盘_5x5布艺拼图棋盘.png')
    dst_board = os.path.join(TTS_EN_DIR, '04_Board_5x5_Quilt.png')
    shutil.copy2(src_board, dst_board)
    print(f'Copied {os.path.basename(dst_board)}: {Image.open(dst_board).size}')

    for zh_fn, en_fn in TOKEN_COPY_MAP.items():
        src = os.path.join(TTS_ZH_DIR, 'tokens', zh_fn)
        dst = os.path.join(TOKENS_EN_DIR, en_fn)
        shutil.copy2(src, dst)
    print(f'Copied {len(TOKEN_COPY_MAP)} RGBA tokens to tts_en/tokens/')


def prepare_clean_bases():
    """Prepare textless base images for CardBack (520x720), Thumbnail (512x512), and HouseRule CardBack (520x720)."""
    # 1. CardBack base: erase Chinese title in y=[66..230], x=[50..470] of 520x720 with sampled cream + gentle blur
    cb_src = os.path.join(TTS_ZH_DIR, '00_通用卡背_CardBack.png')
    cb = Image.open(cb_src).convert('RGBA')
    assert cb.size == (520, 720)
    arr = np.array(cb)
    # Sample clean cream from y=[225..248], x=[60..160]
    cream_sample = arr[225:248, 60:160, :3].reshape(-1, 3)
    cream_rgb = tuple(int(v) for v in np.median(cream_sample, axis=0))
    patch = Image.new('RGBA', (430, 185), cream_rgb + (255,))
    # Add very subtle paper grain matching original
    rng = np.random.default_rng(42)
    p_arr = np.array(patch, dtype=np.int16)
    noise = rng.integers(-2, 3, size=(185, 430, 3))
    p_arr[:, :, :3] = np.clip(p_arr[:, :, :3] + noise, 0, 255)
    patch = Image.fromarray(p_arr.astype(np.uint8), 'RGBA')
    mask = Image.new('L', (430, 185), 0)
    ImageDraw.Draw(mask).rounded_rectangle((10, 10, 420, 175), radius=20, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(8))
    cb.paste(patch, (45, 52), mask)
    cb_clean_path = os.path.join(TTS_EN_DIR, '_tmp_cb_base.png')
    cb.convert('RGB').save(cb_clean_path, 'PNG')

    # 2. Thumbnail base (512x512): erase Chinese title in y=[22..170], x=[36..476]
    th_src = os.path.join(TTS_ZH_DIR, '猪你好梦_TTS存档缩略图.png')
    th = Image.open(th_src).convert('RGBA')
    assert th.size == (512, 512)
    th_arr = np.array(th)
    th_sample = th_arr[165:185, 30:130, :3].reshape(-1, 3)
    th_rgb = tuple(int(v) for v in np.median(th_sample, axis=0))
    t_patch = Image.new('RGBA', (450, 150), th_rgb + (255,))
    tp_arr = np.array(t_patch, dtype=np.int16)
    t_noise = rng.integers(-2, 3, size=(150, 450, 3))
    tp_arr[:, :, :3] = np.clip(tp_arr[:, :, :3] + t_noise, 0, 255)
    t_patch = Image.fromarray(tp_arr.astype(np.uint8), 'RGBA')
    t_mask = Image.new('L', (450, 150), 0)
    ImageDraw.Draw(t_mask).rounded_rectangle((10, 10, 440, 140), radius=20, fill=255)
    t_mask = t_mask.filter(ImageFilter.GaussianBlur(8))
    th.paste(t_patch, (31, 20), t_mask)
    th_clean_path = os.path.join(TTS_EN_DIR, '_tmp_th_base.png')
    th.convert('RGB').save(th_clean_path, 'PNG')

    # 3. House Rule CardBack base (520x720) from textless art/out/v2/1_一稿/hr_card_back.png
    hr_art_path = os.path.join(ROOT, 'art', 'out', 'v2', '1_一稿', 'hr_card_back.png')
    art = Image.open(hr_art_path).convert('RGBA')
    a_arr = np.array(art)
    corners = np.concatenate([
        a_arr[:40, :40, :3].reshape(-1, 3),
        a_arr[:40, -40:, :3].reshape(-1, 3),
        a_arr[-40:, :40, :3].reshape(-1, 3),
        a_arr[-40:, -40:, :3].reshape(-1, 3),
    ])
    bg_rgb = tuple(int(x) for x in np.median(corners, axis=0))

    W, H = 520, 720
    im = Image.new('RGBA', (W, H), bg_rgb + (255,))
    aw, ah = 436, 436
    art_rs = art.resize((aw, ah), Image.LANCZOS)
    amask = Image.new('L', (aw, ah), 0)
    ImageDraw.Draw(amask).rectangle((18, 18, aw - 19, ah - 19), fill=255)
    amask = amask.filter(ImageFilter.GaussianBlur(12))
    im.paste(art_rs, ((W - aw) // 2, 198), amask)

    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ov)
    draw.rounded_rectangle((18, 18, W - 19, H - 19), radius=26, outline=(224, 182, 118, 210), width=3)
    draw.rounded_rectangle((28, 28, W - 29, H - 29), radius=20, outline=(196, 154, 98, 165), width=2)

    def star4(sx, sy, ro, ri, col):
        pts = []
        for i in range(8):
            ang = -math.pi / 2 + i * math.pi / 4
            r = ro if i % 2 == 0 else ri
            pts.append((sx + r * math.cos(ang), sy + r * math.sin(ang)))
        draw.polygon(pts, fill=col)

    for (sx, sy) in [(50, 50), (W - 50, 50), (50, H - 50), (W - 50, H - 50)]:
        star4(sx, sy, 8.5, 3.2, (246, 198, 92, 220))

    credit_font = ImageFont.truetype(r'C:\Windows\Fonts\segoesc.ttf', 12) if os.path.exists(r'C:\Windows\Fonts\segoesc.ttf') else ImageFont.load_default()
    cr = 'Design by zhuzhu & For zhubao'
    bc = draw.textbbox((0, 0), cr, font=credit_font)
    draw.text(((W - (bc[2] - bc[0])) / 2, H - 78), cr, font=credit_font, fill=(224, 194, 156, 165))
    star4(W // 2 - 22, H - 48, 4.5, 1.8, (236, 186, 86, 195))
    star4(W // 2, H - 48, 7.0, 2.6, (246, 198, 92, 225))
    star4(W // 2 + 22, H - 48, 4.5, 1.8, (236, 186, 86, 195))

    hr_clean_path = os.path.join(TTS_EN_DIR, '_tmp_hr_base.png')
    Image.alpha_composite(im, ov).convert('RGB').save(hr_clean_path, 'PNG')
    return cb_clean_path, th_clean_path, hr_clean_path


def build_backs_html():
    """Render crisp SVG hand-lettered English titles onto CardBack, Thumbnail, and HouseRule CardBack."""
    html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>English Card Backs & Thumbnail</title>
  <style>
    @font-face {
      font-family: 'MiorningGoupaHei';
      src: url('../web/fonts/MiorningGoupaHei-Regular.woff2') format('woff2');
      font-weight: 100 900;
    }
    @font-face {
      font-family: 'Nunito';
      src: url('fonts/Nunito.ttf') format('truetype');
      font-weight: 300 900;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #222; display: flex; gap: 20px; padding: 20px; }
    .art-box { position: relative; overflow: hidden; flex-shrink: 0; }
    .art-box > img { width: 100%; height: 100%; display: block; }
    .title-svg { position: absolute; left: 0; top: 0; width: 100%; height: 100%; pointer-events: none; }
  </style>
</head>
<body>
  <!-- 1. Main Card Back (520x720) -->
  <div id="box-cb" class="art-box" style="width:520px;height:720px;">
    <img src="_tmp_cb_base.png" alt="">
    <svg class="title-svg" viewBox="0 0 520 720" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="gPinkGold1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#f24c82"/>
          <stop offset="50%" stop-color="#ff7e52"/>
          <stop offset="100%" stop-color="#f5ae28"/>
        </linearGradient>
        <linearGradient id="gGoldPink1" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#f5a524"/>
          <stop offset="50%" stop-color="#f2577c"/>
          <stop offset="100%" stop-color="#f59824"/>
        </linearGradient>
        <filter id="softShadow" x="-15%" y="-15%" width="130%" height="130%">
          <feDropShadow dx="0" dy="3" stdDeviation="2.5" flood-color="#9e4c32" flood-opacity="0.22"/>
        </filter>
      </defs>
      <g filter="url(#softShadow)">
        <text x="260" y="146" text-anchor="middle"
              font-family="'MiorningGoupaHei', sans-serif"
              font-size="52" font-weight="700" letter-spacing="0.5"
              fill="url(#gPinkGold1)" stroke="#fffaf0" stroke-width="5.5" paint-order="stroke fill">Sweet Dreams,</text>
        <text x="260" y="206" text-anchor="middle"
              font-family="'MiorningGoupaHei', sans-serif"
              font-size="48" font-weight="700" letter-spacing="0.8"
              fill="url(#gGoldPink1)" stroke="#fffaf0" stroke-width="5.5" paint-order="stroke fill">Little Pigs!</text>
      </g>
      <!-- Cute sparkle accents -->
      <path d="M446 98 L449 107 L458 110 L449 113 L446 122 L443 113 L434 110 L443 107 Z" fill="#f7b733"/>
      <path d="M74 166 L76 172 L82 174 L76 176 L74 182 L72 176 L66 174 L72 172 Z" fill="#f25c86"/>
    </svg>
  </div>

  <!-- 2. Save Thumbnail (512x512) -->
  <div id="box-th" class="art-box" style="width:512px;height:512px;">
    <img src="_tmp_th_base.png" alt="">
    <svg class="title-svg" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
      <g filter="url(#softShadow)">
        <text x="256" y="88" text-anchor="middle"
              font-family="'MiorningGoupaHei', sans-serif"
              font-size="50" font-weight="700" letter-spacing="0.5"
              fill="url(#gPinkGold1)" stroke="#fffaf0" stroke-width="5.5" paint-order="stroke fill">Sweet Dreams,</text>
        <text x="256" y="144" text-anchor="middle"
              font-family="'MiorningGoupaHei', sans-serif"
              font-size="46" font-weight="700" letter-spacing="0.8"
              fill="url(#gGoldPink1)" stroke="#fffaf0" stroke-width="5.5" paint-order="stroke fill">Little Pigs!</text>
      </g>
      <path d="M446 42 L449 51 L458 54 L449 57 L446 66 L443 57 L434 54 L443 51 Z" fill="#f7b733"/>
      <path d="M66 108 L68 114 L74 116 L68 118 L66 124 L64 118 L58 116 L64 114 Z" fill="#f25c86"/>
    </svg>
  </div>

  <!-- 3. House Rule Card Back (520x720) -->
  <div id="box-hr" class="art-box" style="width:520px;height:720px;">
    <img src="_tmp_hr_base.png" alt="">
    <svg class="title-svg" viewBox="0 0 520 720" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="gHr1" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#ffd15c"/>
          <stop offset="50%" stop-color="#ff7a8a"/>
          <stop offset="100%" stop-color="#ffba49"/>
        </linearGradient>
        <linearGradient id="gHr2" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#ff8a75"/>
          <stop offset="50%" stop-color="#ffd56b"/>
          <stop offset="100%" stop-color="#ff7a8a"/>
        </linearGradient>
        <filter id="hrGlow" x="-15%" y="-15%" width="130%" height="130%">
          <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#1c0b04" flood-opacity="0.55"/>
        </filter>
      </defs>
      <g filter="url(#hrGlow)">
        <text x="260" y="128" text-anchor="middle"
              font-family="'MiorningGoupaHei', sans-serif"
              font-size="43" font-weight="700" letter-spacing="1.2"
              fill="url(#gHr1)" stroke="#3e2010" stroke-width="5.5" paint-order="stroke fill">TONIGHT'S</text>
        <text x="260" y="182" text-anchor="middle"
              font-family="'MiorningGoupaHei', sans-serif"
              font-size="45" font-weight="700" letter-spacing="1.0"
              fill="url(#gHr2)" stroke="#3e2010" stroke-width="5.5" paint-order="stroke fill">HOUSE RULE</text>
      </g>
      <path d="M432 84 L435 93 L444 96 L435 99 L432 108 L429 99 L420 96 L429 93 Z" fill="#ffd15c"/>
      <path d="M88 140 L90 146 L96 148 L90 150 L88 156 L86 150 L80 148 L86 146 Z" fill="#ffd15c"/>
    </svg>
  </div>
</body>
</html>
"""
    with open(TMP_BACKS_HTML, 'w', encoding='utf-8') as f:
        f.write(html)


def build_decks_html(decks_map):
    sheets_payload = []
    for sp in SHEETS_SPEC:
        sheets_payload.append({
            'id': sp['id'],
            'filename': sp['filename'],
            'cols': sp['cols'],
            'rows': sp['rows'],
            'cardW': sp['card_w'],
            'cardH': sp['card_h'],
            'keys': decks_map[sp['id']],
        })

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Sweet Dreams, Little Pigs! — EN TTS Sprite Sheets</title>
  <link rel="stylesheet" href="../web/style.css">
  <style>
    @font-face {{
      font-family: 'MiorningGoupaHei';
      src: url('../web/fonts/MiorningGoupaHei-Regular.woff2') format('woff2');
      font-weight: 100 900;
    }}
    @font-face {{
      font-family: 'Nunito';
      src: url('fonts/Nunito.ttf') format('truetype');
      font-weight: 300 900;
    }}
    * {{ box-sizing: border-box; }}
    html, body {{
      margin: 0; padding: 0;
      background: #2c1f16 !important;
      overflow: visible;
    }}
    .tts-sheet {{
      position: relative; display: grid; gap: 0; padding: 0; margin: 0;
      background: #e6d7be; overflow: hidden;
    }}
    .tts-slot {{
      position: relative; overflow: hidden; margin: 0; padding: 0;
      background: #e6d7be;
    }}
    .tts-slot > .card {{
      width: 156px; height: 216px;
      margin: 0 !important; border-radius: 0 !important; box-shadow: none !important;
      transform-origin: top left; transition: none !important; cursor: default;
      font-family: 'Nunito', sans-serif;
    }}
    /* MiorningGoupaHei for titles/badges + Nunito for card body */
    .card-title {{
      font-family: 'MiorningGoupaHei', sans-serif;
      font-weight: 700;
      font-size: 11.2px;
      letter-spacing: -0.01em;
      padding: 2.5px 5px 2px;
    }}
    .card-series {{
      font-family: 'MiorningGoupaHei', sans-serif;
      font-weight: 700;
      font-size: 9.6px;
      letter-spacing: 0.02em;
      padding: 2px 5.5px 2px 3px;
    }}
    .card-cost, .card-cloud, .card-dream {{
      font-family: 'MiorningGoupaHei', sans-serif;
      font-weight: 700;
    }}
    .card-body {{
      font-family: 'Nunito', sans-serif;
      font-weight: 700;
      font-size: 8.8px;
      line-height: 1.24;
      letter-spacing: 0;
      padding: 2px 5px 3px;
      word-break: normal;
      overflow-wrap: break-word;
    }}
    .card-fn {{
      font-size: 7.2px;
      line-height: 1.18;
      margin-top: 1.5px;
      font-weight: 600;
      color: #4d5f7d;
    }}
    .ico-fx {{ width: 14.5px; height: 14.5px; }}
    .fx-token {{ vertical-align: -2.8px; }}
    .fx-arrow {{ margin: 0 1px; font-weight: 800; }}
    .card-dream {{
      right: 4px; bottom: 3px;
      font-size: 9.5px; padding: 1px 4.5px 1px 3px;
    }}
    .card-dream .ico-cloud {{ width: 12px; height: 12px; }}
    .card-dream .ico-mode-inline {{ width: 10.5px; height: 10.5px; }}

    /* Help Card English tuning */
    .help-head-title {{
      font-family: 'MiorningGoupaHei', sans-serif;
      font-weight: 700;
      font-size: 10.2px;
      letter-spacing: 0.01em;
    }}
    .help-head-pill {{ font-family: 'MiorningGoupaHei', sans-serif; font-size: 7.8px; font-weight: 700; }}
    .help-sec {{ padding: 1.5px 3.5px; }}
    .help-sec-title {{
      font-family: 'MiorningGoupaHei', sans-serif;
      font-weight: 700; font-size: 7.4px; letter-spacing: 0.01em;
    }}
    .help-sec-sub {{ font-family: 'Nunito', sans-serif; font-size: 6.2px; font-weight: 700; }}
    .help-flow-row {{ font-size: 6.3px; line-height: 1.12; font-weight: 700; gap: 2px; }}
    .help-mode-row {{ font-size: 6.2px; line-height: 1.12; font-weight: 700; gap: 2px; }}
    .help-step-tag {{ font-family: 'MiorningGoupaHei', sans-serif; font-size: 5.9px; font-weight: 700; padding: 0.5px 2.5px; min-width: 22px; }}
    .help-ico-grid {{ gap: 1px 2px; }}
    .help-ico-item {{ font-size: 6.1px; font-weight: 700; gap: 1.5px; }}
    .help-ico {{ width: 9px; height: 9px; }}
    .help-bond-row {{ font-size: 5.8px; font-weight: 700; gap: 1px; }}
    .help-ser-pill {{ font-family: 'MiorningGoupaHei', sans-serif; font-size: 5.5px; font-weight: 700; padding: 0.5px 2.5px 0.5px 1.5px; gap: 1px; }}
    .help-ser-wrap {{ width: 9px; height: 9px; }}
    .help-ser-ico {{ width: 7px; height: 7px; }}
    .help-note {{ font-size: 5.8px; font-weight: 700; }}

    /* House Rule Card English tuning */
    .hr-art {{ padding: 0; overflow: hidden; }}
    .hr-art-img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
    .hr-head-label {{
      font-family: 'MiorningGoupaHei', sans-serif;
      font-weight: 700; font-size: 8.4px; letter-spacing: 0.03em;
    }}
    .hr-title {{
      font-family: 'MiorningGoupaHei', sans-serif;
      font-weight: 700; font-size: 10.6px; letter-spacing: -0.01em;
    }}
    .hr-title-badge {{ font-family: 'MiorningGoupaHei', sans-serif; font-size: 7.4px; font-weight: 700; padding: 1px 4.5px; }}
    .hr-body {{
      font-family: 'Nunito', sans-serif;
      font-weight: 700; font-size: 7.7px; line-height: 1.2;
      padding: 2px 5.5px 1px;
    }}
    .hr-body .ico-fx {{ width: 12px; height: 12px; }}
    .hr-flavor {{
      font-family: 'Nunito', sans-serif;
      font-style: italic;
      font-weight: 600;
      font-size: 6.5px; line-height: 1.15;
      padding: 1px 5.5px 3px;
    }}
  </style>
</head>
<body>
<div id="ttsRoot"></div>
<script src="../tts_en/cards_en.js"></script>
<script>
(function() {{
  const PC = window.PigCards;
  const SERIES_ICON = {{
    start: 'series_start',
    staple: 'series_staple',
    eat: 'series_eat',
    push: 'series_push',
    sleep: 'sleep',
    pal: 'series_pal',
  }};
  const FX_ICON_MAP = {{
    '☁': {{ file: 'cloud', alt: 'Snore' }},
    '⭐': {{ file: 'star', alt: 'Star' }},
    '🃏': {{ file: 'draw', alt: 'Draw' }},
    '🐾': {{ file: 'walk', alt: 'Walk' }},
    '💤': {{ file: 'sleep', alt: 'Sleep' }},
    '💥': {{ file: 'push', alt: 'Bump' }},
    '🔥': {{ file: 'trash', alt: 'Digest' }},
    '🛏': {{ file: 'blanket', alt: 'Blanket' }},
    '🍎': {{ file: 'series_eat', alt: 'Feast' }},
    '🐷': {{ file: 'series_push', alt: 'Bump' }},
    '🌀': {{ file: 'series_pal', alt: 'Cuddle' }},
  }};
  const SERIES_BADGE_BG = {{
    start: '#9c7838',
    staple: '#6a9e3b',
    eat: '#e8482e',
    push: '#e8871c',
    sleep: '#3857d4',
    pal: '#bf3482',
  }};
  function escHtml(str) {{
    return String(str).replace(/[&<>"']/g, (ch) => ({{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }}[ch]));
  }}
  function iconHtml(file, cls, alt) {{
    return `<img class="ico ${{cls}}" src="../web/art/icons/${{file}}.webp" alt="${{escHtml(alt || '')}}">`;
  }}
  function formatCardText(text, iconCls) {{
    const cls = iconCls || 'ico-fx';
    const tokRe = /(\\+?\\s*(?:☁\\uFE0F?|⭐\\uFE0F?|🃏|🐾|💤|💥|🔥|🛏\\uFE0F?|🍎|🐷|🌀)(?:\\s*×\\d+)?|\\s*➔\\s*)/g;
    let out = '';
    let last = 0, m;
    while ((m = tokRe.exec(text)) !== null) {{
      if (m.index > last) out += escHtml(text.slice(last, m.index));
      const tok = m[0], trimmed = tok.trim();
      if (trimmed === '➔') {{
        out += '<span class="fx-arrow" aria-hidden="true">→</span>';
      }} else {{
        const gm = tok.match(/^(\\+?)\\s*(☁\\uFE0F?|⭐\\uFE0F?|🃏|🐾|💤|💥|🔥|🛏\\uFE0F?|🍎|🐷|🌀)(?:\\s*×(\\d+))?$/);
        if (gm) {{
          const plus = gm[1] ? '<span class="fx-plus">+</span>' : '';
          const base = gm[2].replace(/\\uFE0F/g, '');
          const info = FX_ICON_MAP[base];
          const ico = iconHtml(info.file, cls, info.alt);
          const mul = gm[3] ? `<span class="fx-mul"><span class="fx-x">×</span><span class="fx-num">${{gm[3]}}</span></span>` : '';
          out += `<span class="fx-token">${{plus}}${{ico}}${{mul}}</span>`;
        }} else {{
          out += escHtml(tok);
        }}
      }}
      last = tokRe.lastIndex;
    }}
    if (last < text.length) out += escHtml(text.slice(last));
    return out;
  }}
  function seriesBadgeColor(d) {{
    if (Array.isArray(d.series)) {{
      const c1 = SERIES_BADGE_BG[d.series[0]] || '#888';
      const c2 = SERIES_BADGE_BG[d.series[1]] || c1;
      return `linear-gradient(125deg, ${{c1}} 48%, ${{c2}} 52%)`;
    }}
    return SERIES_BADGE_BG[d.series] || '#888';
  }}
  function seriesLabel(d) {{
    if (Array.isArray(d.series)) {{
      return d.series.map((x) => `<span class="ico-series-wrap">${{iconHtml(SERIES_ICON[x], 'ico-series', PC.SERIES[x].name)}}</span>`).join('<span class="ico-plus">+</span>');
    }}
    const s = PC.SERIES[d.series];
    return `<span class="ico-series-wrap">${{iconHtml(SERIES_ICON[d.series], 'ico-series', s.name)}}</span><span>${{s.name}}</span>`;
  }}
  function formatCardBody(text, iconCls) {{
    const idx = String(text).indexOf('\\n*');
    if (idx < 0) return `<span class="card-text">${{formatCardText(text, iconCls)}}</span>`;
    return `<span class="card-text">${{formatCardText(text.slice(0, idx), iconCls)}}</span><div class="card-fn">${{formatCardText(text.slice(idx + 1), iconCls)}}</div>`;
  }}
  function buildCardEl(key) {{
    const d = PC.CARDS[key];
    const el = document.createElement('div');
    el.className = 'card';
    el.dataset.key = key;
    const cloudBadge = d.cloud > 0
      ? `<span class="card-cloud">${{iconHtml('mode_complete', 'ico-mode-inline', 'Full')}}${{iconHtml('cloud', 'ico-cloud', 'Snore')}}<span>${{d.cloud}}</span></span>`
      : '';
    const dreamVal = d.dreamCloud != null ? d.dreamCloud : ((d.series === 'start' || d.series === 'staple' || d.cost <= 2) ? 1 : 2);
    const dreamBadge = `<span class="card-dream">${{iconHtml('mode_dream', 'ico-mode-inline', 'Dream')}}${{iconHtml('cloud', 'ico-cloud', 'Snore')}}<span>${{dreamVal}}</span></span>`;
    el.innerHTML = `
      <div class="card-art">
        <img src="../print/_art_hires/${{key}}.png" alt="${{escHtml(d.name)}}">
        ${{d.cost > 0 ? `<span class="card-cost">${{iconHtml('cloud', 'ico-cost', 'Cost')}}<span>${{d.cost}}</span></span>` : ''}}
        <span class="card-series" style="background:${{seriesBadgeColor(d)}}">${{seriesLabel(d)}}</span>
      </div>
      <div class="card-title">
        <span class="card-title-text">${{escHtml(d.name)}}</span>
        ${{cloudBadge}}
      </div>
      <div class="card-body">${{formatCardBody(d.text, 'ico-fx')}}${{dreamBadge}}</div>
    `;
    return el;
  }}
  function buildHelpCardEl() {{
    const tgt = PC.RULESET.target || 15;
    const el = document.createElement('div');
    el.className = 'card help-card';
    el.dataset.key = 'help';
    const ico = (file, alt) => iconHtml(file, 'help-ico', alt);
    const serPill = (s, label) =>
      `<span class="help-ser-pill" style="background:${{SERIES_BADGE_BG[s]}}"><span class="help-ser-wrap">${{iconHtml(SERIES_ICON[s], 'help-ser-ico', label)}}</span><span>${{label}}</span></span>`;
    el.innerHTML = `
      <div class="help-head">
        <span class="help-head-title">Player Aid</span>
        <span class="help-head-pill">${{iconHtml('star', 'ico', 'Star')}}<span>${{tgt}} to Win</span></span>
      </div>
      <div class="help-body">
        <div class="help-sec">
          <div class="help-sec-title"><span>Turn Sequence</span><span class="help-sec-sub">Discard all at end</span></div>
          <div class="help-flow-list">
            <div class="help-flow-row"><span class="help-step-tag t1">Wake</span><span>Wake Rug pigs; +1★/pig &amp; +1★/pair</span></div>
            <div class="help-flow-row"><span class="help-step-tag t2">Romp</span><span>Play cards &amp; tally Snores in Bowl</span></div>
            <div class="help-flow-row"><span class="help-step-tag t3">Dream</span><span>Buy ≤3 cards, discard all, draw 5</span></div>
          </div>
        </div>
        <div class="help-sec">
          <div class="help-sec-title"><span>3 Play Modes</span><span class="help-sec-sub">Play / Dream</span></div>
          <div class="help-mode-list">
            <div class="help-mode-row">${{ico('mode_complete', 'Full')}}<span>Full Play: Resonance + Card Snores</span></div>
            <div class="help-mode-row">${{ico('mode_play', 'Skip')}}<span>Skip (90°): Resonance, 0 Card Snores</span></div>
            <div class="help-mode-row">${{ico('mode_dream', 'Dream')}}<span>Face-Down: No Resonance, Dream ☁</span></div>
          </div>
        </div>
        <div class="help-sec">
          <div class="help-sec-title"><span>Icons</span><span class="help-sec-sub">Floor wakes pigs</span></div>
          <div class="help-ico-grid">
            <div class="help-ico-item">${{ico('walk', 'Walk')}}<span>Walk 1 step</span></div>
            <div class="help-ico-item">${{ico('sleep', 'Sleep')}}<span>Sleep on Rug</span></div>
            <div class="help-ico-item">${{ico('push', 'Bump')}}<span>Bump adj. pig</span></div>
            <div class="help-ico-item">${{ico('draw', 'Draw')}}<span>Draw 1 card</span></div>
            <div class="help-ico-item">${{ico('trash', 'Digest')}}<span>Trash Starter</span></div>
            <div class="help-ico-item">${{ico('star', 'Star')}}<span>+1 Dream Star</span></div>
            <div class="help-ico-item full">${{ico('cloud', 'Snore')}}<span>Snore: Cards &amp; Rug Pig+1 &amp; Pillow+1</span></div>
          </div>
        </div>
        <div class="help-sec">
          <div class="help-sec-title"><span>Resonance</span><span class="help-sec-sub">2+ same series</span></div>
          <div class="help-bond-list">
            <div class="help-bond-row">${{serPill('eat', 'Feast')}}<span>→</span>${{ico('draw', 'Draw')}}<span>×1</span></div>
            <div class="help-bond-row">${{serPill('push', 'Bump')}}<span>→</span>${{ico('walk', 'Walk')}}<span>×1</span></div>
            <div class="help-bond-row">${{serPill('sleep', 'Snooze')}}<span>→</span>${{ico('cloud', 'Snore')}}<span>1+</span>${{ico('blanket', 'Tuck')}}</div>
            <div class="help-bond-row">${{serPill('pal', 'Cuddle')}}<span>→</span>${{ico('sleep', 'Sleep')}}<span>×1</span></div>
          </div>
          <div class="help-note">Dual-series counts for both · 1×/turn each</div>
        </div>
      </div>
    `;
    return el;
  }}

  const HR_ART_FILE = {{
    pillow_double: 'soft_pillow',
    three_line: 'line_up',
  }};
  function buildHouseRuleCardEl(key) {{
    const d = PC.HOUSE_RULES[key];
    const el = document.createElement('div');
    el.className = 'card hr-card';
    el.dataset.key = 'hr_' + key;
    const artFile = HR_ART_FILE[key] || key;
    el.innerHTML = `
      <div class="hr-head">
        <span class="hr-head-label">🌙 TONIGHT'S HOUSE RULE</span>
      </div>
      <div class="hr-art"><img class="hr-art-img" src="../web/art/hr_${{artFile}}.webp" alt="${{escHtml(d.name)}}"></div>
      <div class="hr-title">
        <span class="card-title-text">${{escHtml(d.name)}}</span>
        <span class="hr-title-badge">${{escHtml(d.tag)}}</span>
      </div>
      <div class="hr-body">${{formatCardText(d.text, 'ico-fx')}}</div>
      <div class="hr-flavor">“${{escHtml(d.flavor)}}”</div>
    `;
    return el;
  }}

  const SHEETS = {json.dumps(sheets_payload, ensure_ascii=False)};
  const root = document.getElementById('ttsRoot');
  for (const sh of SHEETS) {{
    const totalSlots = sh.cols * sh.rows;
    const sheetEl = document.createElement('div');
    sheetEl.className = 'tts-sheet';
    sheetEl.id = 'sheet-' + sh.id;
    sheetEl.style.width = (sh.cols * sh.cardW) + 'px';
    sheetEl.style.height = (sh.rows * sh.cardH) + 'px';
    sheetEl.style.gridTemplateColumns = `repeat(${{sh.cols}}, ${{sh.cardW}}px)`;
    sheetEl.style.gridTemplateRows = `repeat(${{sh.rows}}, ${{sh.cardH}}px)`;

    const scale = sh.cardW / 156.0;
    for (let i = 0; i < totalSlots; i++) {{
      const slot = document.createElement('div');
      slot.className = 'tts-slot';
      slot.style.width = sh.cardW + 'px';
      slot.style.height = sh.cardH + 'px';
      if (i < sh.keys.length) {{
        const key = sh.keys[i];
        const cardEl = key === '__help__'
          ? buildHelpCardEl()
          : key.startsWith('__hr__')
            ? buildHouseRuleCardEl(key.slice(6))
            : buildCardEl(key);
        cardEl.style.transform = `scale(${{scale}})`;
        slot.appendChild(cardEl);
      }}
      sheetEl.appendChild(slot);
    }}
    root.appendChild(sheetEl);
  }}
}})();
</script>
</body>
</html>
"""
    with open(TMP_DECK_HTML, 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    os.makedirs(TTS_EN_DIR, exist_ok=True)
    os.makedirs(TOKENS_EN_DIR, exist_ok=True)

    decks_map = load_tts_decks()
    copy_board_and_tokens()
    tmp_bases = prepare_clean_bases()
    build_backs_html()
    build_decks_html(decks_map)

    handler = functools.partial(QuietHandler, directory=ROOT)
    srv = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            # 1. Render English Card Back, Thumbnail, and House Rule Card Back
            bp = browser.new_page(viewport={'width': 1800, 'height': 900}, device_scale_factor=1)
            bp.goto(f'http://127.0.0.1:{port}/tts_en/_tts_backs_en.html', wait_until='networkidle')
            bp.evaluate("async () => { await document.fonts.ready; }")
            for elem_id, fname in [
                ('#box-cb', '00_CardBack_EN.png'),
                ('#box-th', 'SweetDreams_EN_Thumbnail.png'),
                ('#box-hr', '05_HouseRule_CardBack_EN.png'),
            ]:
                out_p = os.path.join(TTS_EN_DIR, fname)
                bp.locator(elem_id).screenshot(path=out_p, type='png')
                print(f'Saved {fname}: {Image.open(out_p).size}')
            bp.close()

            # 2. Render & verify all 3 English deck sprite sheets
            page = browser.new_page(viewport={'width': 4200, 'height': 4200}, device_scale_factor=1)
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
            page.goto(f'http://127.0.0.1:{port}/tts_en/_tts_decks_en.html', wait_until='networkidle')
            page.evaluate("""async () => {
                await document.fonts.ready;
                await Promise.all(Array.from(document.querySelectorAll('img')).map(im =>
                    im.complete ? null : new Promise(res => { im.onload = res; im.onerror = res; })
                ));
            }""")

            check = page.evaluate("""() => {
                const imgs = Array.from(document.querySelectorAll('img'));
                const broken = imgs.filter(i => !i.complete || i.naturalWidth === 0).map(i => i.getAttribute('src'));
                const clippedCards = Array.from(document.querySelectorAll('.card[data-key]'))
                    .filter(c => {
                        const b = c.querySelector('.card-body');
                        return b && b.scrollHeight > b.clientHeight + 1;
                    }).map(c => c.dataset.key);
                const titleClips = Array.from(document.querySelectorAll('.card[data-key]'))
                    .filter(c => {
                        const t = c.querySelector('.card-title-text');
                        return t && t.scrollWidth > t.clientWidth + 1;
                    }).map(c => c.dataset.key);
                const helpClip = Array.from(document.querySelectorAll('.card.help-card .help-body')).filter(b => b.scrollHeight > b.clientHeight + 1).length;
                const helpRowClip = Array.from(document.querySelectorAll('.card.help-card .help-flow-row, .card.help-card .help-mode-row, .card.help-card .help-ico-item, .card.help-card .help-bond-row, .card.help-card .help-note, .card.help-card .help-sec-title'))
                    .filter(el => el.scrollWidth > el.clientWidth + 1).map(el => el.innerText.trim());
                const hrClip = Array.from(document.querySelectorAll('.card.hr-card'))
                    .filter(c => {
                        const els = c.querySelectorAll('.hr-body, .hr-flavor, .hr-art');
                        return Array.from(els).some(b => b.scrollHeight > b.clientHeight + 1 || b.scrollWidth > b.clientWidth + 1);
                    }).map(c => c.dataset.key);

                const gameCards = Array.from(document.querySelectorAll('.card[data-key]')).filter(c => window.PigCards && window.PigCards.CARDS[c.dataset.key]);
                const dreamTextOverlaps = [];
                for (const c of gameCards) {
                    const db = c.querySelector('.card-dream');
                    const ct = c.querySelector('.card-text');
                    const fn = c.querySelector('.card-fn');
                    const dr = db.getBoundingClientRect();
                    for (const target of [ct, fn]) {
                        if (!target) continue;
                        const rects = [];
                        const tw = document.createTreeWalker(target, NodeFilter.SHOW_TEXT);
                        while (tw.nextNode()) {
                            const node = tw.currentNode;
                            if (!node.nodeValue || !node.nodeValue.trim()) continue;
                            const rg = document.createRange();
                            rg.selectNodeContents(node);
                            for (const r of rg.getClientRects()) {
                                if (r.width > 0 && r.height > 0) rects.push(r);
                            }
                        }
                        for (const elChild of target.querySelectorAll('img, .fx-token')) {
                            const r = elChild.getBoundingClientRect();
                            if (r.width > 0 && r.height > 0) rects.push(r);
                        }
                        for (const r of rects) {
                            const ox = Math.min(r.right, dr.right) - Math.max(r.left, dr.left);
                            const oy = Math.min(r.bottom, dr.bottom) - Math.max(r.top, dr.top);
                            if (ox > -1.0 && oy > -1.0) {
                                dreamTextOverlaps.push({ k: c.dataset.key, ox: +ox.toFixed(1), oy: +oy.toFixed(1) });
                                break;
                            }
                        }
                    }
                }
                return {
                    imgCount: imgs.length,
                    broken,
                    clippedCards: [...new Set(clippedCards)],
                    titleClips: [...new Set(titleClips)],
                    helpClip,
                    helpRowClip: [...new Set(helpRowClip)],
                    hrClip: [...new Set(hrClip)],
                    dreamTextOverlaps: dreamTextOverlaps.filter((v, i, a) => a.findIndex(x => x.k === v.k) === i),
                    totalCards: document.querySelectorAll('.card').length,
                };
            }""")
            print('EN TTS Deck HTML check:', json.dumps(check, ensure_ascii=False, indent=2))
            assert len(errors) == 0, f'Page/console errors: {errors}'
            assert len(check['broken']) == 0, f"Broken images: {check['broken']}"
            assert check['totalCards'] == 103
            assert len(check['clippedCards']) == 0, f"Clipped card bodies: {check['clippedCards']}"
            assert len(check['titleClips']) == 0, f"Clipped card titles: {check['titleClips']}"
            assert check['helpClip'] == 0 and len(check['helpRowClip']) == 0, f"Help card clipped: {check['helpClip']} {check['helpRowClip']}"
            assert len(check['hrClip']) == 0, f"House rule clipped: {check['hrClip']}"
            assert len(check['dreamTextOverlaps']) == 0, f"Dream badge overlaps: {check['dreamTextOverlaps']}"

            for sp in SHEETS_SPEC:
                el = page.locator(f"#sheet-{sp['id']}")
                out_path = os.path.join(TTS_EN_DIR, sp['filename'])
                el.screenshot(path=out_path, type='png')
                print(f"Saved {sp['filename']}: {Image.open(out_path).size}")
            page.close()
            browser.close()
    finally:
        srv.shutdown()
        for tmp in (TMP_DECK_HTML, TMP_BACKS_HTML, *tmp_bases):
            if os.path.exists(tmp):
                os.remove(tmp)

    print('ALL ENGLISH TTS IMAGE PACK GENERATION & VERIFICATION PASSED!')


if __name__ == '__main__':
    main()
