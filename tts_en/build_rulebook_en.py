# -*- coding: utf-8 -*-
"""Build 10-page illustrated English A5 Rulebook PDF for Tabletop Simulator,
faithfully translated from the 10-page Chinese TTS lightweight rulebook,
using cute rounded English fonts (MiorningGoupaHei + Nunito).

Output: tts_en/SweetDreams_Rulebook_EN_TTS.pdf
"""
import functools
import json
import os
import subprocess
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TTS_EN_DIR = os.path.dirname(os.path.abspath(__file__))
TMP_HTML = os.path.join(TTS_EN_DIR, '_rulebook_en.html')
TMP_COVER_BASE = os.path.join(TTS_EN_DIR, '_tmp_rb_cover_base.png')
TMP_PDF = os.path.join(TTS_EN_DIR, '_rulebook_en_raw.pdf')
OUT_PDF = os.path.join(TTS_EN_DIR, 'SweetDreams_Rulebook_EN_TTS.pdf')


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def load_en_data():
    js = (
        "const C = require('./tts_en/cards_en.js');"
        "console.log(JSON.stringify({CARDS: C.CARDS, SERIES: C.SERIES, HOUSE_RULES: C.HOUSE_RULES, RULESET: C.RULESET}));"
    )
    res = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, check=True, encoding='utf-8')
    return json.loads(res.stdout.strip())


def prepare_cover_base():
    """Erase Chinese title & bottom text from print/_rulebook_assets/cover_a4.png for clean English cover."""
    src = os.path.join(ROOT, 'print', '_rulebook_assets', 'cover_a4.png')
    im = Image.open(src).convert('RGBA')
    w, h = im.size
    arr = np.array(im)
    rng = np.random.default_rng(7)

    # 1. Erase top Chinese title area (y = 8%..32%)
    y0, y1 = int(h * 0.08), int(h * 0.32)
    sample = arr[int(h * 0.04):int(h * 0.07), int(w * 0.1):int(w * 0.3), :3].reshape(-1, 3)
    bg = tuple(int(v) for v in np.median(sample, axis=0))
    patch = Image.new('RGBA', (w, y1 - y0), bg + (255,))
    pa = np.array(patch, dtype=np.int16)
    pa[:, :, :3] = np.clip(pa[:, :, :3] + rng.integers(-2, 3, size=(y1 - y0, w, 3)), 0, 255)
    mask = Image.new('L', (w, y1 - y0), 0)
    ImageDraw.Draw(mask).rectangle((int(w * 0.04), 8, int(w * 0.96), y1 - y0 - 8), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(12))
    im.paste(Image.fromarray(pa.astype(np.uint8), 'RGBA'), (0, y0), mask)

    # 2. Erase bottom Chinese pills / credit area (y = 88%..99%) with feathered cream-blue fade
    by0, by1 = int(h * 0.88), int(h * 0.995)
    b_arr = np.array(im)
    for y in range(by0, by1):
        left_rgb = np.median(b_arr[y, int(w * 0.03):int(w * 0.14), :3], axis=0)
        right_rgb = np.median(b_arr[y, int(w * 0.86):int(w * 0.97), :3], axis=0)
        row_col = np.clip((left_rgb + right_rgb) * 0.5, 0, 255)
        x0, x1 = int(w * 0.14), int(w * 0.86)
        noise = rng.integers(-2, 3, size=(x1 - x0, 3))
        b_arr[y, x0:x1, :3] = np.clip(row_col + noise, 0, 255).astype(np.uint8)
    b_patch = Image.fromarray(b_arr[by0:by1, :, :], 'RGBA')
    b_mask = Image.new('L', (w, by1 - by0), 0)
    ImageDraw.Draw(b_mask).rectangle((int(w * 0.15), 14, int(w * 0.85), by1 - by0), fill=255)
    b_mask = b_mask.filter(ImageFilter.GaussianBlur(14))
    im.paste(b_patch, (0, by0), b_mask)

    im.convert('RGB').save(TMP_COVER_BASE, 'PNG')


def build_rulebook_html(data):
    hr = data['HOUSE_RULES']

    def ico(name, size=12):
        return f'<img class="ico" style="width:{size}px;height:{size}px;" src="../web/art/icons/{name}.webp">'

    def fmt(text):
        rep = [
            ('☁️', ico('cloud', 11)), ('☁', ico('cloud', 11)),
            ('⭐', ico('star', 11)),
            ('🃏', ico('draw', 11)),
            ('🐾', ico('walk', 11)),
            ('💤', ico('sleep', 11)),
            ('💥', ico('push', 11)),
            ('🔥', ico('trash', 11)),
            ('🛏️', ico('blanket', 11)), ('🛏', ico('blanket', 11)),
            ('🍎', ico('series_eat', 11)),
            ('🐷', ico('series_push', 11)),
            ('🌀', ico('series_pal', 11)),
            ('➔', '→'),
        ]
        s = text
        for a, b in rep:
            s = s.replace(a, b)
        return s

    HR_ART_FILE = {
        'pillow_double': 'soft_pillow',
        'three_line': 'line_up',
    }
    HR_TAG_COL = {
        'pillow_double': '#d98218',
        'corner_star': '#c97a16',
        'small_market': '#2e8540',
        'wake_bounty': '#d9482b',
        'double_res': '#8c3bc4',
        'three_line': '#3857d4',
        'piggy_bank': '#c87a19',
        'apple_sale': '#5a9932',
        'warm_blanket': '#3b7dd8',
        'night_party': '#a634b8',
        'fast_sprint': '#e04e39',
        'dream_boost': '#5264b8',
    }

    def hr_cards_grid(keys):
        items = []
        for k in keys:
            h = hr[k]
            af = HR_ART_FILE.get(k, k)
            tc = HR_TAG_COL.get(k, '#8c4b14')
            items.append(f"""
            <div class="hr-mini">
              <div class="hr-mini-head">
                <span>🌙 Tonight's House Rule</span>
                <span class="hr-mini-tag" style="background:{tc};">{h['tag']}</span>
              </div>
              <div class="hr-mini-art"><img src="../web/art/hr_{af}.webp" alt=""></div>
              <div class="hr-mini-name">{h['name']}</div>
              <div class="hr-mini-txt">{fmt(h['text'])}</div>
            </div>""")
        return '<div class="hr-grid">' + ''.join(items) + '</div>'

    def grid3x3(cells):
        # cells is list of 9: None, 'P' (pink pig), 'K' (pink pig on pillow), 'L' (line)
        divs = []
        for i, c in enumerate(cells):
            cls = 'g3-cell'
            if i == 4:
                cls += ' g3-pillow'
            inner = ''
            if c == 'P':
                inner = '<span class="g3-pig"></span>'
            divs.append(f'<div class="{cls}">{inner}</div>')
        return '<div class="g3-box">' + ''.join(divs) + '</div>'

    hr_keys = list(hr.keys())
    hr_page1 = hr_cards_grid(hr_keys[:6])
    hr_page2 = hr_cards_grid(hr_keys[6:])

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Sweet Dreams, Little Pigs! — English Rulebook</title>
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
  @page {{ size: 148mm 210mm; margin: 0; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Nunito', sans-serif;
    color: #362216;
    background: #faf3e6;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  .page {{
    width: 148mm; height: 210mm;
    background: #fdf8ee;
    position: relative;
    overflow: hidden;
    page-break-after: always;
    display: flex;
    flex-direction: column;
  }}
  .page:last-child {{ page-break-after: auto; }}

  .hdr {{
    height: 9mm;
    padding: 0 9mm;
    display: flex; align-items: center; justify-content: space-between;
    font-size: 7.2pt; font-weight: 700; color: #9c7a56;
    border-bottom: 1px solid rgba(196, 154, 98, 0.28);
    flex-shrink: 0;
  }}
  .ftr {{
    height: 8mm;
    padding: 0 9mm;
    display: flex; align-items: center; justify-content: space-between;
    font-size: 7pt; font-weight: 700; color: #9c7a56;
    border-top: 1px solid rgba(196, 154, 98, 0.22);
    margin-top: auto;
    flex-shrink: 0;
  }}
  .tab {{
    position: absolute; right: 0; top: 34mm;
    background: #d95d5d; color: #fff;
    font-family: 'MiorningGoupaHei', sans-serif;
    font-weight: 600; font-size: 7.2pt;
    padding: 5px 3px;
    writing-mode: vertical-rl;
    border-radius: 5px 0 0 5px;
    letter-spacing: 0.5px;
  }}
  .tab-play {{ background: #e68a2e; }}
  .tab-card {{ background: #4678c8; }}
  .tab-hr {{ background: #9c52b8; }}
  .tab-qa {{ background: #8c6642; }}

  .banner-top {{
    width: 100%; height: 24mm; object-fit: cover; object-position: center 45%;
    display: block; flex-shrink: 0;
    -webkit-mask-image: linear-gradient(to bottom, #000 58%, transparent 100%);
    mask-image: linear-gradient(to bottom, #000 58%, transparent 100%);
  }}
  .content {{
    padding: 2mm 9mm 2mm;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 3.2px;
  }}
  .content-no-banner {{ padding-top: 3mm; }}

  h1 {{
    font-family: 'MiorningGoupaHei', sans-serif;
    font-size: 15.5pt; font-weight: 700; color: #4a2612;
    line-height: 1.15;
  }}
  .sub-lead {{
    font-size: 7.8pt; font-weight: 700; color: #6e4e38; line-height: 1.3;
    margin-bottom: 2px;
  }}
  .sec-bar {{
    background: #ead7bc; color: #4a2612;
    font-family: 'MiorningGoupaHei', sans-serif; font-weight: 600; font-size: 9pt;
    padding: 2.5px 8px; border-radius: 6px;
    display: flex; justify-content: space-between; align-items: center;
  }}
  .sec-bar small {{ font-family: 'Nunito', sans-serif; font-size: 7pt; font-weight: 700; color: #7a5436; }}
  .ico {{ vertical-align: -2px; object-fit: contain; display: inline-block; }}
  p, li {{ font-size: 7.4pt; line-height: 1.33; font-weight: 600; }}
  b {{ font-weight: 800; color: #361c0d; }}

  /* Cover */
  .cover-wrap {{ position: relative; width: 100%; height: 100%; }}
  .cover-bg {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
  .cover-title-svg {{ position: absolute; left: 0; top: 0; width: 100%; height: 100%; }}
  .cover-pills {{
    position: absolute; bottom: 10.5mm; left: 50%; transform: translateX(-50%);
    display: flex; gap: 6px; white-space: nowrap;
  }}
  .cpill {{
    font-family: 'MiorningGoupaHei', sans-serif; font-weight: 600; font-size: 8.5pt;
    padding: 3px 12px; border-radius: 999px; color: #4a2612;
  }}
  .cover-credit {{
    position: absolute; bottom: 4.5mm; left: 50%; transform: translateX(-50%);
    font-size: 7.5pt; font-style: italic; color: #8c6a4a; font-weight: 700;
  }}

  /* Page 2 Components */
  .comp-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; }}
  .comp-card {{
    background: #f6ecdb; border: 1px solid #e2cbb0; border-radius: 8px;
    padding: 4px 5px; text-align: center;
    display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px;
  }}
  .comp-imgs {{ height: 34px; display: flex; align-items: center; justify-content: center; gap: 3px; }}
  .comp-imgs img {{ max-height: 32px; max-width: 44px; object-fit: contain; border-radius: 3px; }}
  .comp-title {{ font-family: 'MiorningGoupaHei', sans-serif; font-size: 7.8pt; font-weight: 600; color: #4a2612; }}
  .comp-sub {{ font-size: 6.7pt; color: #7a583c; font-weight: 700; }}

  .setup-box {{
    background: #eef5fc; border: 1.2px solid #b8d3ee; border-radius: 9px;
    padding: 6px 9px; display: flex; flex-direction: column; gap: 4px;
  }}
  .setup-head {{ font-family: 'MiorningGoupaHei', sans-serif; font-size: 8.5pt; font-weight: 600; color: #1d578c; display: flex; align-items: center; gap: 5px; }}
  .setup-row {{ display: flex; align-items: flex-start; gap: 6px; font-size: 7.3pt; line-height: 1.3; font-weight: 600; }}
  .num-dot {{
    width: 15px; height: 15px; border-radius: 50%; background: #4c8fd6; color: #fff;
    font-family: 'MiorningGoupaHei', sans-serif; font-size: 7.5pt; font-weight: 700;
    display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 1px;
  }}

  /* Page 3 Tabletop Diagram */
  .table-box {{
    background: #f5ebd9; border: 1px solid #dec6a4; border-radius: 10px;
    padding: 5px; display: grid; grid-template-columns: 22mm minmax(0, 1fr) 21mm; gap: 4px; align-items: center;
    overflow: hidden;
  }}
  .t-col {{ display: flex; flex-direction: column; gap: 3px; min-width: 0; }}
  .t-slot {{
    background: #fff9ee; border: 1px solid #d4b58e; border-radius: 5px;
    padding: 2.5px 3px; text-align: center; font-size: 6.1pt; line-height: 1.15; font-weight: 700;
    overflow-wrap: break-word;
  }}
  .t-mid {{ display: flex; flex-direction: column; gap: 3px; align-items: center; min-width: 0; }}
  .t-player {{
    width: 100%; border-radius: 6px; padding: 2.5px 5px; text-align: center; font-size: 6.3pt; font-weight: 700;
  }}
  .t-yellow {{ background: #fff3cc; border: 1px solid #e6c25a; }}
  .t-pink {{ background: #ffeaf0; border: 1px solid #eba0b9; }}
  .t-board-row {{ display: grid; grid-template-columns: minmax(0, 1fr) 34mm minmax(0, 1fr); align-items: center; gap: 3px; width: 100%; }}
  .t-side-note {{ font-size: 5.7pt; line-height: 1.15; font-weight: 700; }}
  .t-board-img {{ width: 34mm; border-radius: 5px; border: 1px solid #2b3f66; display: block; }}

  .card-box {{
    background: #fff9ef; border: 1px solid #e0c7a4; border-radius: 8px;
    padding: 5px 8px;
  }}
  .zone-row {{ display: flex; align-items: center; gap: 7px; margin-top: 3px; }}
  .zone-pill {{
    font-family: 'MiorningGoupaHei', sans-serif; font-size: 7pt; font-weight: 600; color: #fff;
    padding: 2px 7px; border-radius: 999px; min-width: 26mm; text-align: center; flex-shrink: 0;
  }}

  /* Page 4 Wake & Romp */
  .flow-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; margin: 2px 0; }}
  .flow-card {{ border-radius: 8px; padding: 4px 6px; border: 1px solid rgba(0,0,0,0.08); }}
  .flow-t {{ font-family: 'MiorningGoupaHei', sans-serif; font-size: 8.2pt; font-weight: 700; margin-bottom: 1px; }}
  .flow-s {{ font-size: 6.7pt; font-weight: 700; color: #5c422c; }}

  .cuddle-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin: 2px 0; }}
  .cuddle-item {{
    background: #f5ebd9; border-radius: 8px; padding: 4px; text-align: center;
    display: flex; flex-direction: column; align-items: center; gap: 2px;
  }}
  .g3-box {{
    display: grid; grid-template-columns: repeat(3, 12px); grid-template-rows: repeat(3, 12px); gap: 1.5px;
  }}
  .g3-cell {{ background: #e87a7a; border-radius: 2px; display: flex; align-items: center; justify-content: center; }}
  .g3-pillow {{ background: #f2c265; }}
  .g3-pig {{ width: 8px; height: 8px; border-radius: 50%; background: #ff70a6; border: 1.5px solid #fff; }}

  .res-4 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 5px; }}
  .res-box {{
    background: #fff9ef; border: 1px solid #e0c7a4; border-radius: 8px; padding: 4px 7px;
  }}
  .res-pill {{
    display: inline-flex; align-items: center; gap: 3px;
    font-family: 'MiorningGoupaHei', sans-serif; font-size: 7.2pt; font-weight: 600; color: #fff;
    padding: 1px 7px; border-radius: 999px; margin-bottom: 2px;
  }}

  /* Page 5 Modes & Dream */
  table {{ width: 100%; border-collapse: collapse; font-size: 7.1pt; }}
  th {{
    background: #8b5a2b; color: #fff8eb; font-family: 'MiorningGoupaHei', sans-serif;
    font-weight: 600; padding: 3px 6px; text-align: left;
  }}
  td {{ padding: 3.5px 6px; border-bottom: 1px solid #e6d3b8; font-weight: 700; vertical-align: middle; }}
  tr:nth-child(even) td {{ background: #fbf4e4; }}

  .warn-box {{ background: #fff5d6; border: 1.2px solid #ebba4d; border-radius: 8px; padding: 4.5px 8px; }}
  .pink-box {{ background: #fff0f5; border: 1.2px solid #f0a8c2; border-radius: 8px; padding: 4.5px 8px; }}
  .blue-box {{ background: #eef5fc; border: 1.2px solid #b8d3ee; border-radius: 8px; padding: 4.5px 8px; }}

  /* Page 6 Card Anatomy & Icons */
  .anat-wrap {{ display: grid; grid-template-columns: 1fr 37mm 1fr; gap: 5px; align-items: center; }}
  .anat-col {{ display: flex; flex-direction: column; gap: 6px; }}
  .anat-item {{ font-size: 6.7pt; line-height: 1.22; font-weight: 700; }}
  .anat-badge {{
    display: inline-flex; align-items: center; justify-content: center;
    width: 13px; height: 13px; border-radius: 50%; background: #4a2612; color: #fff;
    font-family: 'MiorningGoupaHei', sans-serif; font-size: 7pt; font-weight: 700; margin-right: 3px;
  }}
  .icons-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; }}
  .ico-card {{
    background: #fff9ef; border: 1px solid #e2cbb0; border-radius: 7px;
    padding: 3.5px 6px; display: flex; align-items: flex-start; gap: 5px;
  }}

  /* Page 7 Text Actions */
  .act-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; }}
  .act-box {{ background: #f6ecdb; border-radius: 7px; padding: 3.5px 6px; font-size: 6.8pt; line-height: 1.25; font-weight: 600; }}
  .act-box b {{ font-family: 'MiorningGoupaHei', sans-serif; font-size: 7.3pt; color: #6e3614; }}

  /* Page 8-9 House Rules Grid */
  .hr-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 5px; }}
  .hr-mini {{
    background: #fffaf0; border: 1.2px solid #c99d68; border-radius: 8px;
    overflow: hidden; display: flex; flex-direction: column;
  }}
  .hr-mini-head {{
    background: #4e2b15; color: #ffe49c; padding: 2px 5px;
    display: flex; justify-content: space-between; align-items: center;
    font-family: 'MiorningGoupaHei', sans-serif; font-size: 6.6pt; font-weight: 600;
  }}
  .hr-mini-tag {{ color: #fff; padding: 0.5px 5px; border-radius: 999px; font-size: 6pt; }}
  .hr-mini-art {{ height: 22mm; overflow: hidden; }}
  .hr-mini-art img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
  .hr-mini-name {{ font-family: 'MiorningGoupaHei', sans-serif; font-size: 8pt; font-weight: 700; color: #3d210f; padding: 2px 6px 0; }}
  .hr-mini-txt {{ font-size: 6.6pt; line-height: 1.22; font-weight: 700; color: #4f3524; padding: 1px 6px 4px; }}

  /* Page 10 Q&A */
  .qa-item {{ border-bottom: 1px dashed #dec6a4; padding-bottom: 3px; }}
  .qa-q {{ font-family: 'MiorningGoupaHei', sans-serif; font-size: 7.8pt; font-weight: 600; color: #4a2612; display: flex; align-items: center; gap: 4px; }}
  .q-tag {{ background: #6b4226; color: #fff; font-size: 6.8pt; padding: 0.5px 5px; border-radius: 4px; }}
  .qa-a {{ font-size: 6.9pt; line-height: 1.28; font-weight: 600; color: #4a3425; margin-top: 1px; }}
</style>
</head>
<body>

<!-- PAGE 1: COVER -->
<div class="page">
  <div class="cover-wrap">
    <img class="cover-bg" src="_tmp_rb_cover_base.png" alt="Cover">
    <svg class="cover-title-svg" viewBox="0 0 560 794" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="cg1" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#f24c82"/>
          <stop offset="50%" stop-color="#ff7e52"/>
          <stop offset="100%" stop-color="#f5ae28"/>
        </linearGradient>
        <linearGradient id="cg2" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#f5a524"/>
          <stop offset="50%" stop-color="#f2577c"/>
          <stop offset="100%" stop-color="#f59824"/>
        </linearGradient>
        <filter id="cs" x="-15%" y="-15%" width="130%" height="130%">
          <feDropShadow dx="0" dy="3" stdDeviation="3" flood-color="#9e4c32" flood-opacity="0.22"/>
        </filter>
      </defs>
      <g filter="url(#cs)">
        <text x="280" y="136" text-anchor="middle" font-family="'MiorningGoupaHei', sans-serif" font-size="60" font-weight="700" fill="url(#cg1)" stroke="#fffaf0" stroke-width="6" paint-order="stroke fill">Sweet Dreams,</text>
        <text x="280" y="202" text-anchor="middle" font-family="'MiorningGoupaHei', sans-serif" font-size="56" font-weight="700" fill="url(#cg2)" stroke="#fffaf0" stroke-width="6" paint-order="stroke fill">Little Pigs!</text>
      </g>
      <rect x="205" y="220" width="150" height="24" rx="12" fill="#fff7e2" stroke="#e0b678" stroke-width="1.5"/>
      <text x="280" y="236" text-anchor="middle" font-family="'MiorningGoupaHei', sans-serif" font-size="12" font-weight="600" fill="#6b4226">✦  Rulebook  ✦</text>
    </svg>
    <div class="cover-pills">
      <span class="cpill" style="background:#ffdce6;">2 Players</span>
      <span class="cpill" style="background:#ffefc2;">Ages 8+</span>
      <span class="cpill" style="background:#dceeff;">15–25 Min</span>
    </div>
    <div class="cover-credit">Design by zhuzhu &amp; For zhubao</div>
  </div>
</div>

<!-- PAGE 2: COMPONENTS & 5-STEP SETUP -->
<div class="page">
  <img class="banner-top" src="../print/_rulebook_assets/banner_reunion.png" alt="">
  <div class="tab">SETUP</div>
  <div class="content">
    <h1>Components &amp; 5-Step Setup</h1>
    <p class="sub-lead">Two rival piggy families take alternating naps on one cozy rug: while one snoozes and dreams, the other wakes up to romp and claim the best spots!</p>

    <div class="comp-grid">
      <div class="comp-card">
        <div class="comp-imgs"><img src="04_Board_5x5_Quilt.png"></div>
        <div class="comp-title">5×5 Quilt Board</div>
        <div class="comp-sub">1 Board (with Star Tracks)</div>
      </div>
      <div class="comp-card">
        <div class="comp-imgs"><img src="tokens/pink_pig_awake.png"><img src="tokens/yellow_pig_awake.png"></div>
        <div class="comp-title">Wooden Pig Tokens</div>
        <div class="comp-sub">6 Pigs (3 Pink, 3 Yellow)</div>
      </div>
      <div class="comp-card">
        <div class="comp-imgs"><img src="tokens/score_pink.png"><img src="tokens/score_yellow.png"></div>
        <div class="comp-title">Dream Star Markers</div>
        <div class="comp-sub">2 Markers (Pink / Yellow)</div>
      </div>
      <div class="comp-card">
        <div class="comp-imgs"><img src="tokens/snore_chip_1.png"></div>
        <div class="comp-title">Bowl &amp; Snore Chips</div>
        <div class="comp-sub">1 Bowl · 30 Chips (1☁️ each)</div>
      </div>
      <div class="comp-card">
        <div class="comp-imgs"><img src="tokens/felt_blanket.png"></div>
        <div class="comp-title">Felt Blankets</div>
        <div class="comp-sub">6 Blankets</div>
      </div>
      <div class="comp-card">
        <div class="comp-imgs"><img src="00_CardBack_EN.png"></div>
        <div class="comp-title">65×90mm Cards</div>
        <div class="comp-sub">103 Cards Total</div>
      </div>
    </div>

    <div class="setup-box" style="margin-top:2px;">
      <div class="setup-head">✔ Follow These 5 Steps (or click [Setup] New Game in TTS)</div>
      <div class="setup-row"><span class="num-dot">1</span><span><b>Flip a House Rule (Optional):</b> Shuffle the 12 House Rule cards and place 1 face-up beside the board (recommended to skip on your very first game).</span></div>
      <div class="setup-row"><span class="num-dot">2</span><span><b>Board, Markers &amp; Pigs:</b> Lay out the 5×5 Board. Place Score Markers at <b>0</b> (Yellow top-left, Pink bottom-right). Stand 3 Pigs <b>Awake</b> on your back-row Floor tiles.</span></div>
      <div class="setup-row"><span class="num-dot">3</span><span><b>Set Up the Dream Market:</b> Stack 8 <b>Bedtime Apples</b> face-up. Shuffle the 61 Market cards and reveal <b>5</b> face-up in the Market display.</span></div>
      <div class="setup-row"><span class="num-dot">4</span><span><b>Personal Decks:</b> Each player takes 10 Starters (4× Big Yawn, 4× Scoot Over, 2× Squeeze In), shuffles them face-down as a Draw Pile, and leaves room for Play &amp; Discard zones.</span></div>
      <div class="setup-row"><span class="num-dot">5</span><span><b>Starting Hands &amp; Bowl:</b> <b>Pink (1st)</b> draws <b>4 cards</b>. <b>Yellow (2nd)</b> draws <b>5 cards</b> and starts Turn 1 with <b>+2{ico('cloud',11)}</b> in the Bowl!</span></div>
    </div>
  </div>
  <div class="ftr"><span>Components &amp; 5-Step Setup</span><span>2 / 10</span></div>
</div>

<!-- PAGE 3: TABLETOP LAYOUT & VICTORY -->
<div class="page">
  <div class="hdr"><span>Sweet Dreams, Little Pigs! — Rulebook</span><span>Tabletop Layout &amp; Goal</span></div>
  <div class="tab">SETUP</div>
  <div class="content content-no-banner">
    <div class="sec-bar"><span>Tabletop Layout Diagram</span><small>Click [Setup] in TTS to auto-arrange</small></div>
    <div class="table-box">
      <div class="t-col">
        <div class="t-slot" style="background:#3d2b22;color:#ffe6a3;">🌙 House Rule<br><span style="font-weight:600;color:#fff;">Flip 1</span></div>
        <div class="t-slot"><b>Dream Market</b><br>61-Card Deck<br>Slot 1 · Slot 2<br>Slot 3 · Slot 4<br>Slot 5<br><span style="color:#6a9e3b;">8× Bedtime Apple</span></div>
      </div>
      <div class="t-mid">
        <div class="t-player t-yellow"><b>Yellow (2nd)</b> · Draw 5 + 2{ico('cloud',10)} T1</div>
        <div class="t-board-row">
          <div class="t-side-note" style="text-align:right;color:#8a5a08;"><b>Yellow Track</b><br>Left 0↓15<br><br><span style="color:#2b4a7a;"><b>Outer 16 Floor</b><br>Landing here wakes pigs!</span></div>
          <img class="t-board-img" src="04_Board_5x5_Quilt.png" alt="">
          <div class="t-side-note" style="color:#a82454;"><b>Center Pillow</b><br>+1{ico('cloud',10)} if asleep<br><br><b>Pink Track</b><br>Right 0↑15</div>
        </div>
        <div class="t-player t-pink"><b>Pink (1st)</b> · Draw 4</div>
      </div>
      <div class="t-col">
        <div class="t-slot"><b>Snore Bowl</b><br>30× {ico('cloud',10)}1 Chips</div>
        <div class="t-slot"><b>Control Panel</b><br>Wake / Snore / End</div>
        <div class="t-slot"><b>6× Blankets</b><br>Protect Sleepers</div>
      </div>
    </div>

    <div class="sec-bar"><span>Game Goal &amp; Victory</span><small>Reach 15 Dream Stars (12 in Quick Game)</small></div>
    <div class="card-box">
      <p>• First player to reach <b>15 Dream Stars ({ico('star',11)})</b> (or <b>12{ico('star',11)}</b> in a Quick Game) triggers the end of the game.</p>
      <p>• <b>Pink (1st Player) reaches it first:</b> Pink finishes their turn, then <b>Yellow (2nd Player)</b> takes one final turn so both players have equal turns.</p>
      <p>• <b>Yellow (2nd Player) reaches it first or overtakes:</b> Game ends immediately after Yellow's turn! Highest score wins; ties share victory.</p>
    </div>

    <div class="sec-bar"><span>Board Zones Explained</span><small>Rug vs Pillow vs Floor</small></div>
    <div class="card-box">
      <div class="zone-row"><span class="zone-pill" style="background:#e6558a;">3×3 Cozy Rug</span><p><b>Only Sleep Zone:</b> Pigs must stand on these 9 pink tiles to Sleep. At Wake: +1{ico('star',10)} per sleeper + 1{ico('star',10)} per cuddling pair.</p></div>
      <div class="zone-row"><span class="zone-pill" style="background:#d98a1c;">Center Pillow</span><p><b>Golden Spot:</b> When tallying Snores in Dream, your sleeping pig here grants an extra <b>+1{ico('cloud',10)}</b>.</p></div>
      <div class="zone-row"><span class="zone-pill" style="background:#2f5597;">Outer 16 Floor</span><p><b>Instant Wake-Up:</b> Any sleeping pig pushed or moved onto the dark-blue Floor wakes up immediately!</p></div>
    </div>
  </div>
  <div class="ftr"><span>Tabletop Layout &amp; Goal</span><span>3 / 10</span></div>
</div>

<!-- PAGE 4: HOW TO PLAY (PART 1: WAKE & ROMP) -->
<div class="page">
  <img class="banner-top" src="../print/_rulebook_assets/banner_midnight.png" alt="">
  <div class="tab tab-play">PLAY</div>
  <div class="content">
    <h1>How to Play (1): Wake &amp; Romp</h1>
    <p class="sub-lead">On your turn, resolve these 3 phases in order—takes just 3 minutes to learn!</p>

    <div class="flow-3">
      <div class="flow-card" style="background:#fff0e0;border-color:#f0b884;">
        <div class="flow-t" style="color:#b85a08;">1. 🌅 Wake</div>
        <div class="flow-s">+1{ico('star',10)}/pig &amp; pair → Stand all</div>
      </div>
      <div class="flow-card" style="background:#ffe8ef;border-color:#f0a8c2;">
        <div class="flow-t" style="color:#a82454;">2. ☀️ Romp</div>
        <div class="flow-s">Play cards → Resonance</div>
      </div>
      <div class="flow-card" style="background:#eef3ff;border-color:#a8c0f0;">
        <div class="flow-t" style="color:#2b4aa8;">3. 🌙 Dream</div>
        <div class="flow-s">Tally {ico('cloud',10)} → Buy ≤3 → Draw 5</div>
      </div>
    </div>

    <div class="sec-bar"><span>1. 🌅 Wake Phase</span><small>Score stars first, then stand up all sleeping pigs</small></div>
    <p>• <b>Sleep Stars:</b> Advance <b>1 space ({ico('star',10)}×1)</b> for each of your <b>Asleep</b> pigs on the 3×3 Rug.</p>
    <p>• <b>Cuddle Bonus:</b> Advance <b>+1 space ({ico('star',10)}×1)</b> for each orthogonally adjacent pair of your sleeping pigs (diagonals don't count).</p>
    <p>• <b>Rise &amp; Shine:</b> After scoring, flip all your sleeping pigs back to <b>Awake</b> and return their Felt Blankets to the supply.</p>

    <div class="cuddle-3">
      <div class="cuddle-item">
        {grid3x3([None,None,None,None,'P',None,None,None,None])}
        <div style="font-family:'MiorningGoupaHei';font-size:7.6pt;font-weight:700;">1 Pig = 1{ico('star',10)}</div>
        <div style="font-size:6.3pt;color:#7a583c;font-weight:700;">1 sleeper + 0 pairs</div>
      </div>
      <div class="cuddle-item">
        {grid3x3([None,None,None,None,'P','P',None,None,None])}
        <div style="font-family:'MiorningGoupaHei';font-size:7.6pt;font-weight:700;">2 Cuddling = 3{ico('star',10)}</div>
        <div style="font-size:6.3pt;color:#7a583c;font-weight:700;">2 sleepers + 1 pair</div>
      </div>
      <div class="cuddle-item">
        {grid3x3([None,None,None,'P','P',None,'P',None,None])}
        <div style="font-family:'MiorningGoupaHei';font-size:7.6pt;font-weight:700;">3 Connected = 5{ico('star',10)}</div>
        <div style="font-size:6.3pt;color:#7a583c;font-weight:700;">3 sleepers + 2 pairs</div>
      </div>
    </div>

    <div class="sec-bar"><span>2. ☀️ Romp Phase &amp; 4 Series Resonances</span><small>2+ cards of same series = Bonus!</small></div>
    <p>• <b>Play One by One:</b> Play cards from hand into your Play Zone in any order, resolving icons left-to-right before playing the next card.</p>
    <p>• <b>Series Resonance:</b> When your <b>2nd card</b> of a series enters your Play Zone this turn (upright or 90° skipped), trigger its bonus once per series per turn! <i>(Dual-series cards count for both; face-down Dream cards do not count.)</i></p>

    <div class="res-4">
      <div class="res-box"><span class="res-pill" style="background:#e8482e;">{ico('series_eat',10)} 2× Feast</span><p>Draw <b>{ico('draw',11)}×1</b> <i>before</i> this card's actions.</p></div>
      <div class="res-box"><span class="res-pill" style="background:#e8871c;">{ico('series_push',10)} 2× Bump</span><p>Bonus <b>{ico('walk',11)}×1</b> <i>after</i> this card's actions.</p></div>
      <div class="res-box"><span class="res-pill" style="background:#3857d4;">{ico('sleep',10)} 2× Snooze</span><p>Bowl <b>+{ico('cloud',11)}×1</b> now &amp; <b>{ico('blanket',11)}×1</b> after.</p></div>
      <div class="res-box"><span class="res-pill" style="background:#bf3482;">{ico('series_pal',10)} 2× Cuddle</span><p>Bonus <b>{ico('sleep',11)}×1</b> <i>after</i> this card's actions.</p></div>
    </div>
  </div>
  <div class="ftr"><span>How to Play (1): Wake &amp; Romp</span><span>4 / 10</span></div>
</div>

<!-- PAGE 5: HOW TO PLAY (PART 2: 3 MODES & DREAM) -->
<div class="page">
  <div class="hdr"><span>Sweet Dreams, Little Pigs! — Rulebook</span><span>3 Play Modes &amp; Dream Phase</span></div>
  <div class="tab tab-play">PLAY</div>
  <div class="content content-no-banner">
    <div class="sec-bar"><span>Three Ways to Use Every Card</span><small>Full Play / Skip Play / Discard to Dream</small></div>
    <p>Each card in your hand can either be played during Romp (Full or Skip) or kept face-down to Dream:</p>
    <table>
      <thead><tr><th style="width:24%;">Mode</th><th style="width:38%;">Actions &amp; Resonance</th><th>Snore / Dream {ico('cloud',10)}</th></tr></thead>
      <tbody>
        <tr><td>{ico('mode_complete',12)} <b>Full Play</b><br><span style="font-size:6.2pt;color:#6e4e38;">(Upright)</span></td><td>Resolve all printed steps.<br><b>Counts for Resonance.</b></td><td><b>Earns title-bar {ico('cloud',10)}</b> (0 if unmarked).</td></tr>
        <tr><td>{ico('mode_play',12)} <b>Skip Play</b><br><span style="font-size:6.2pt;color:#6e4e38;">(Turn 90°)</span></td><td>Skip any printed step.<br><b>Counts for Resonance.</b></td><td><b>0 title-bar {ico('cloud',10)}</b> (conditional bonuses still apply).</td></tr>
        <tr><td>{ico('mode_dream',12)} <b>Dream</b><br><span style="font-size:6.2pt;color:#6e4e38;">(Face-Down)</span></td><td>No actions.<br><b>No Resonance.</b></td><td><b>Earns bottom-right Dream {ico('cloud',10)} (1 or 2).</b></td></tr>
      </tbody>
    </table>

    <div class="warn-box">
      <p><b>⚠ No Cards Kept in Hand!</b> When you stop playing cards and enter Dream, all remaining cards in hand must be placed <b>face-down</b> in your Play Zone for Dream {ico('cloud',10)}, then discarded at turn end.</p>
    </div>

    <div class="sec-bar"><span>3. 🌙 Dream Phase</span><small>Tally Snores → Buy Cards (Top of Deck) → Draw 5</small></div>
    <div class="blue-box">
      <p><b>① Tally Snores ({ico('cloud',10)}):</b> Upright Card {ico('cloud',10)} + Face-Down Dream {ico('cloud',10)} + Conditional {ico('cloud',10)} + 1{ico('cloud',10)} per Rug Sleeper + 1{ico('cloud',10)} Pillow + Snooze Resonance / Turn 1 Bonus.</p>
    </div>
    <p>• <b>② Buy Cards (Max 3/turn):</b> Spend {ico('cloud',10)} in your Bowl to buy Market cards or Bedtime Apples. Refill empty Market slots immediately. <b>Bought cards go face-down on TOP of your draw deck!</b></p>
    <p>• <b>③ Turn Cleanup:</b> Return all {ico('cloud',10)} chips to supply, move <b>all</b> Play Zone cards to Discard, and draw <b>5 cards</b> (reshuffle Discard when Draw runs out).</p>

    <div class="pink-box">
      <p><b>🐷 Piggy Whisper:</b> Have an expensive card with <b>2{ico('cloud',10)}</b> in the bottom-right corner (like <i>Giant Pumpkin</i>)? If you'd have to Skip a step anyway, keeping it face-down to Dream guarantees 2{ico('cloud',10)}!</p>
    </div>

    <div class="sec-bar"><span>Quick Turn Example</span><small>2 Pink pigs cuddling (1 on Pillow)</small></div>
    <div class="card-box" style="display:flex;flex-direction:column;gap:2.5px;">
      <p><b>1. Wake:</b> 2 sleeping pigs (+2{ico('star',10)}) + 1 cuddling pair (+1{ico('star',10)}) = <b>+3{ico('star',10)}</b>; stand both pigs up.</p>
      <p><b>2. Romp:</b> Play <i>Tuck In</i> (1{ico('cloud',10)}, walk to Pillow, sleep &amp; blanket) + <i>Scoot Over</i> (walk &amp; sleep). Place <i>Giant Pumpkin</i> face-down to Dream.</p>
      <p><b>3. Dream:</b> 1{ico('cloud',10)} (Tuck In) + 2{ico('cloud',10)} (Pumpkin Dream) + 2{ico('cloud',10)} (2 sleepers) + 1{ico('cloud',10)} (Pillow) = <b>6{ico('cloud',10)}</b> → Buy <i>Family Reunion</i>!</p>
    </div>
  </div>
  <div class="ftr"><span>3 Play Modes &amp; Dream Phase</span><span>5 / 10</span></div>
</div>

<!-- PAGE 6: CARD ANATOMY & 7 ICONS -->
<div class="page">
  <img class="banner-top" src="../print/_rulebook_assets/banner_pillow.png" alt="">
  <div class="tab tab-card">CARDS</div>
  <div class="content">
    <h1>Card Anatomy &amp; 7 Icons</h1>
    <div class="sec-bar"><span>How to Read a Card (Example: Family Reunion)</span><small>65×90mm Standard Card</small></div>

    <div class="anat-wrap">
      <div class="anat-col">
        <div class="anat-item"><span class="anat-badge">1</span><b>Buy Cost (Top-Left)</b><br>Snore {ico('cloud',10)} needed to buy (Starters have no cost).</div>
        <div class="anat-item"><span class="anat-badge">3</span><b>Illustration</b><br>Shows the piggy scene at a glance.</div>
        <div class="anat-item"><span class="anat-badge">4</span><b>Card Title</b><br>Same-named cards are identical.</div>
      </div>
      <div style="width:36mm;height:49.8mm;border:2px solid #c99d68;border-radius:8px;overflow:hidden;background:#fffaf0;box-shadow:0 3px 8px rgba(0,0,0,0.15);display:flex;flex-direction:column;">
        <div style="position:relative;height:25mm;overflow:hidden;flex-shrink:0;">
          <img src="../print/_art_hires/reunion.png" style="width:100%;height:100%;object-fit:cover;display:block;">
          <span style="position:absolute;top:3px;left:3px;background:rgba(30,18,10,0.85);color:#fff;font-family:'MiorningGoupaHei';font-size:6.8pt;padding:0.5px 5px;border-radius:999px;">{ico('cloud',9)} 6</span>
          <span style="position:absolute;top:3px;right:3px;background:#bf3482;color:#fff;font-family:'MiorningGoupaHei';font-size:6.2pt;padding:0.5px 4.5px;border-radius:999px;display:inline-flex;align-items:center;gap:2px;">{ico('series_pal',8)} Cuddle</span>
        </div>
        <div style="padding:2px 5px;display:flex;justify-content:space-between;align-items:center;border-top:1px solid #e5d2b5;flex-shrink:0;">
          <span style="font-family:'MiorningGoupaHei';font-size:7.4pt;font-weight:700;">Family Reunion</span>
          <span style="background:#eaf5ff;border:1px solid #b8dbf7;color:#19619b;font-family:'MiorningGoupaHei';font-size:6.2pt;padding:0 3.5px;border-radius:4px;">{ico('mode_complete',8)}{ico('cloud',8)}1</span>
        </div>
        <div style="padding:2px 5px 12px;font-size:5.8pt;line-height:1.22;font-weight:700;position:relative;flex:1;">
          Scamper* → {ico('walk',9)}×1 → {ico('sleep',9)}×2; all 3 asleep on Rug: +{ico('star',9)}×1
          <div style="font-size:5pt;color:#546685;margin-top:1px;">*Move your awake pig next to another own pig</div>
          <span style="position:absolute;right:4px;bottom:3px;background:rgba(116,72,198,0.14);border:1px solid rgba(116,72,198,0.35);color:#523094;font-family:'MiorningGoupaHei';font-size:6pt;padding:0 4px;border-radius:999px;">{ico('mode_dream',8)}{ico('cloud',8)}2</span>
        </div>
      </div>
      <div class="anat-col">
        <div class="anat-item"><span class="anat-badge">2</span><b>Series Badge (Top-Right)</b><br>Counts toward Resonance (dual-series counts for both).</div>
        <div class="anat-item"><span class="anat-badge">5</span><b>Play {ico('cloud',10)} (Title-Right)</b><br>Earned on Full Play (omitted if 0).</div>
        <div class="anat-item"><span class="anat-badge">6</span><b>Actions &amp; Effects</b><br>Resolve left-to-right.</div>
        <div class="anat-item"><span class="anat-badge">7</span><b>Dream {ico('cloud',10)} (Bottom-Right)</b><br>Earned if discarded face-down to Dream (1 or 2).</div>
      </div>
    </div>

    <div class="sec-bar"><span>7 Card Icons Explained</span><small>Orthogonal directions only</small></div>
    <div class="icons-grid">
      <div class="ico-card">{ico('cloud',16)}<div><b>Snore ×N:</b> Currency to buy cards in Dream.</div></div>
      <div class="ico-card">{ico('walk',16)}<div><b>Walk ×N:</b> Move 1 Awake pig 1 orthogonal empty tile.</div></div>
      <div class="ico-card">{ico('sleep',16)}<div><b>Sleep ×N:</b> Flip 1 Awake pig on the 3×3 Rug to Asleep.</div></div>
      <div class="ico-card">{ico('push',16)}<div><b>Bump ×N:</b> Awake pig pushes adj. pig 1 tile back (into empty tile) &amp; steps in.</div></div>
      <div class="ico-card">{ico('draw',16)}<div><b>Draw ×N:</b> Draw N cards (reshuffle Discard if empty).</div></div>
      <div class="ico-card">{ico('trash',16)}<div><b>Digest ×N:</b> Remove N Starters (Discard/Hand/Play) from the game.</div></div>
      <div class="ico-card" style="grid-column:span 2;">{ico('star',16)}<div><b>Dream Star ×N:</b> Advance your score marker N spaces (first to 15 / Quick 12 triggers end).</div></div>
    </div>

    <div class="blue-box">
      <p><b>✔ Split Multi-Step Icons Freely:</b> When a card says {ico('walk',11)}×2 or {ico('sleep',11)}×2, you may use different pigs for each step or the same pig twice!</p>
    </div>
  </div>
  <div class="ftr"><span>Card Anatomy &amp; 7 Icons</span><span>6 / 10</span></div>
</div>

<!-- PAGE 7: SPECIAL RULES, TEXT ACTIONS & PLAYER AID -->
<div class="page">
  <div class="hdr"><span>Sweet Dreams, Little Pigs! — Rulebook</span><span>Board Rules, Text Actions &amp; Player Aid</span></div>
  <div class="tab tab-card">CARDS</div>
  <div class="content content-no-banner">
    <div class="sec-bar"><span>Special Board Rules: Floor Wake-Up &amp; Felt Blankets</span><small>Off Rug = Wake · Blanket = Shield</small></div>
    <div class="card-box" style="display:flex;flex-direction:column;gap:4px;">
      <p>• <b>Floor Wake-Up:</b> A sleeping pig moved onto another Rug tile stays asleep. The moment it lands on the outer 16 <b>Floor</b> tiles, it wakes up immediately (and loses its Blanket).</p>
      <p>• <b>{ico('blanket',11)} Felt Blanket:</b> Protects your sleeping pig until your next Wake—it cannot be bumped, quaked, swapped, or sleepwalked by the opponent (only <i>Pull the Quilt</i> can strip it first; you may still move it with <i>Sleepwalk</i> or <i>Snuggle Up</i>).</p>
    </div>

    <div class="sec-bar"><span>Card Text Actions Quick Reference</span><small>All orthogonal · Blocked by Blankets</small></div>
    <div class="act-grid">
      <div class="act-box"><b>Chain Bump (Overhill):</b> Push the far-end pig in an adjacent line of pigs 1 tile away (your pig doesn't move).</div>
      <div class="act-box"><b>Row Push (Excuse Me!):</b> Your Awake pig pushes 1–2 adjacent lined-up pigs 1 tile back and steps into the first spot.</div>
      <div class="act-box"><b>Whistle Quake (Snore Train):</b> Pick 1 of your sleeping pigs; push all orthogonally adjacent pigs 1 tile outward.</div>
      <div class="act-box"><b>Sleepwalk 1:</b> Move any 1 sleeping pig on the board 1 orthogonal step into an empty tile (wakes if moved to Floor).</div>
      <div class="act-box"><b>Snuggle (Snuggle Up):</b> Move 1 of your sleeping pigs 1 step within the 3×3 Rug and place a Blanket on it.</div>
      <div class="act-box"><b>Swap (Hook a Tail):</b> Swap 1 of your Awake pigs with any orthogonally adjacent pig (wakes enemy if moved to Floor).</div>
      <div class="act-box"><b>Scamper (Save a Spot / Reunion):</b> Move 1 of your Awake pigs directly to an empty tile orthogonally adjacent to another own pig.</div>
      <div class="act-box"><b>Lure (Lullaby Hum):</b> Move 1 Awake enemy pig 1 orthogonal step into an empty tile.</div>
    </div>

    <div class="sec-bar"><span>Player Aid Card (65×90mm × 2)</span><small>1 per player for instant reference</small></div>
    <div class="card-box" style="display:flex;flex-direction:column;gap:3px;">
      <p>• <b>Turn Sequence:</b> Wake (+1{ico('star',10)}/pig &amp; pair → stand) → Romp (play cards) → Dream (face-down {ico('cloud',10)} → buy ≤3 to top of deck → discard all &amp; draw 5).</p>
      <p>• <b>3 Play Modes:</b> Full Play = Resonance + Title {ico('cloud',10)}; 90° Skip = Resonance only (0{ico('cloud',10)}); Face-Down = Dream {ico('cloud',10)} only (no Resonance).</p>
      <p>• <b>4 Resonances (2+ same series):</b> {ico('series_eat',10)} Draw 1 · {ico('series_push',10)} Walk 1 · {ico('sleep',10)} +1{ico('cloud',10)} &amp; Blanket · {ico('series_pal',10)} Sleep 1.</p>
    </div>
  </div>
  <div class="ftr"><span>Board Rules, Text Actions &amp; Player Aid</span><span>7 / 10</span></div>
</div>

<!-- PAGE 8: HOUSE RULES (1-6) -->
<div class="page">
  <img class="banner-top" src="../print/_rulebook_assets/banner_tuck.png" alt="">
  <div class="tab tab-hr">VARIANTS</div>
  <div class="content">
    <h1>Tonight's House Rules (1–6)</h1>
    <div class="sec-bar"><span>12 House Rule Cards (1–6)</span><small>Place 1 face-up on the Active House Rule pad</small></div>
    {hr_page1}
    <div class="pink-box" style="margin-top:2px;">
      <p><b>🐷 Piggy Whisper:</b> Play your first game without House Rules to learn the 3 phases &amp; Resonances. Afterward, flip 1 random House Rule each game—the TTS script applies it automatically!</p>
    </div>
  </div>
  <div class="ftr"><span>Tonight's House Rules (1–6)</span><span>8 / 10</span></div>
</div>

<!-- PAGE 9: HOUSE RULES (7-12) -->
<div class="page">
  <div class="hdr"><span>Sweet Dreams, Little Pigs! — Rulebook</span><span>Tonight's House Rules (7–12)</span></div>
  <div class="tab tab-hr">VARIANTS</div>
  <div class="content content-no-banner">
    <div class="sec-bar"><span>12 House Rule Cards (7–12)</span><small>Economy · Discount · Shield · Combo · Fast · Discard</small></div>
    {hr_page2}
    <div class="blue-box">
      <p><b>✔ 3 Popular Variant Pickups:</b></p>
      <p>• <b>⚡ 10-Min Turbo:</b> <i>12-Star Sprint</i> (12{ico('star',10)} goal, both draw 5 on Turn 1).</p>
      <p>• <b>💰 Big-Spender Party:</b> <i>Piggy Bank</i> or <i>Resonance Party</i> for explosive 5–6{ico('cloud',10)} turns.</p>
      <p>• <b>🌀 Discard Engine:</b> <i>Dream Booster</i> + <i>Apple Sale</i> to turn cheap discards into steady {ico('cloud',10)}!</p>
    </div>
  </div>
  <div class="ftr"><span>Tonight's House Rules (7–12)</span><span>9 / 10</span></div>
</div>

<!-- PAGE 10: FAQ / Q&A -->
<div class="page">
  <img class="banner-top" src="../print/_rulebook_assets/banner_pumpkin.png" alt="">
  <div class="tab tab-qa">Q &amp; A</div>
  <div class="content">
    <h1>Frequently Asked Questions (Q&amp;A)</h1>
    <div class="sec-bar"><span>7 Core Gameplay Clarifications</span><small>Quick rules check</small></div>

    <div class="qa-item">
      <div class="qa-q"><span class="q-tag">Q1</span>Where do I pick Starters to remove for {ico('trash',10)} Digest?</div>
      <div class="qa-a">Never look through your face-down Draw Pile. Pick 1 Starter from your <b>Discard Pile, Hand, or Play Zone</b> (prefer <i>Big Yawn</i> or an already-skipped card). An upright card in Play keeps its printed {ico('cloud',10)}. Skip if none exist.</div>
    </div>
    <div class="qa-item">
      <div class="qa-q"><span class="q-tag">Q2</span>Do cards stay in the Play Zone after triggering Resonance? Can a 3rd card trigger it again?</div>
      <div class="qa-a">Yes, all played cards stay in your Play Zone until Turn Cleanup. Each series triggers Resonance <b>at most once per turn</b> (a 3rd or 4th card of the same series does not re-trigger it).</div>
    </div>
    <div class="qa-item">
      <div class="qa-q"><span class="q-tag">Q3</span>If my Draw Pile runs out mid-turn, can I shuffle my Play Zone?</div>
      <div class="qa-a"><b>No.</b> Cards in your Play Zone are active this turn and cannot be shuffled. Only your <b>Discard Pile</b> is shuffled to form a new Draw Pile.</div>
    </div>
    <div class="qa-item">
      <div class="qa-q"><span class="q-tag">Q4</span>Does a sleeping pig wake up if pushed onto another Rug tile?</div>
      <div class="qa-a"><b>No.</b> It stays asleep as long as it lands on any of the 9 central Rug tiles. It only wakes up if pushed or moved onto the outer 16 Floor tiles.</div>
    </div>
    <div class="qa-item">
      <div class="qa-q"><span class="q-tag">Q5</span>What can move a pig protected by a Felt Blanket?</div>
      <div class="qa-a">Until your next Wake, opponents cannot Bump, Quake, Swap, or Sleepwalk it—unless they play <i>Pull the Quilt</i> to strip the Blanket first. You may still move it with your own <i>Sleepwalk</i> or <i>Snuggle Up</i>.</div>
    </div>
    <div class="qa-item">
      <div class="qa-q"><span class="q-tag">Q6</span>If I skip 1 step on a card, does the whole card fail?</div>
      <div class="qa-a"><b>No!</b> Turn the card 90° (Skip Play): its title-bar {ico('cloud',10)} becomes <b>0</b>, but all other steps, conditional bonuses, and Series Resonance still work normally. (Skipping a Resonance/conditional bonus step does not penalize the card.)</div>
    </div>
    <div class="qa-item" style="border-bottom:none;">
      <div class="qa-q"><span class="q-tag">Q7</span>What happens when someone reaches 15{ico('star',10)}?</div>
      <div class="qa-a">If Pink hits 15{ico('star',10)}, Yellow gets 1 final turn so both have equal turns. If Yellow hits 15{ico('star',10)} or leads after Yellow's final turn, the game ends immediately.</div>
    </div>

    <div class="warn-box">
      <p><b>⚠ 4 Easy-to-Miss Rules:</b> ① Discard <b>all</b> cards at turn end (keep 0); ② Bought cards go on <b>TOP</b> of your Draw Pile; ③ Blanketed pigs are immune to enemy pushes; ④ Unspent {ico('cloud',10)} is cleared each turn (unless <i>Piggy Bank</i> is active).</p>
    </div>
  </div>
  <div class="ftr"><span>FAQ &amp; Quick Reminders</span><span>10 / 10</span></div>
</div>

</body>
</html>
"""
    with open(TMP_HTML, 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    data = load_en_data()
    prepare_cover_base()
    build_rulebook_html(data)

    handler = functools.partial(QuietHandler, directory=ROOT)
    srv = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 900, 'height': 1200})
            page.goto(f'http://127.0.0.1:{port}/tts_en/_rulebook_en.html', wait_until='networkidle')
            page.evaluate("""async () => {
                await document.fonts.ready;
                await Promise.all(Array.from(document.querySelectorAll('img')).map(im =>
                    im.complete ? null : new Promise(res => { im.onload = res; im.onerror = res; })
                ));
            }""")
            page.pdf(
                path=TMP_PDF,
                width='148mm',
                height='210mm',
                print_background=True,
                margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'},
            )
            browser.close()
    finally:
        srv.shutdown()
        for tmp in (TMP_HTML, TMP_COVER_BASE):
            if os.path.exists(tmp):
                os.remove(tmp)

    src_doc = fitz.open(TMP_PDF)
    out_doc = fitz.open()
    for pg in src_doc:
        pix = pg.get_pixmap(dpi=150, alpha=False)
        img_bytes = pix.tobytes('jpeg', jpg_quality=85)
        new_pg = out_doc.new_page(width=pg.rect.width, height=pg.rect.height)
        new_pg.insert_image(pg.rect, stream=img_bytes)
    out_doc.save(OUT_PDF, deflate=True, garbage=4)
    page_count = len(out_doc)
    out_doc.close()
    src_doc.close()
    if os.path.exists(TMP_PDF):
        os.remove(TMP_PDF)

    sz_kb = os.path.getsize(OUT_PDF) / 1024.0
    print(f'Saved {OUT_PDF}: {page_count} pages, {sz_kb:.1f} KB')


if __name__ == '__main__':
    main()
