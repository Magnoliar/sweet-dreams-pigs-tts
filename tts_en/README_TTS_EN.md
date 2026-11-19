# Sweet Dreams, Little Pigs! — English TTS Mod Pack (`tts_en/`)

Complete English localization of **Sweet Dreams, Little Pigs!** for Tabletop Simulator (TTS), including all 103 cards (Market, Starters, Player Aid, 12 House Rules), English card backs & cover thumbnails, 10-page illustrated English A5 PDF rulebook, 2D floating HUD, 3D control panel, and full Lua automation script.

## 1. Quick Local Playtest
Copy these two files into your TTS Saves folder (`%USERPROFILE%\Documents\My Games\Tabletop Simulator\Saves\`):
- `tts_en/SweetDreams_EN_TTS_Save.json`
- `tts_en/SweetDreams_EN_TTS_Save.png`

Then open Tabletop Simulator -> **Games -> Save & Load** -> load **`Sweet Dreams, Little Pigs! (English)`**.

## 2. Publish to Steam Workshop
`tts_en/SweetDreams_EN_Workshop_Save.json` is already pre-patched to load all 15 assets from:
`https://raw.githubusercontent.com/Magnoliar/sweet-dreams-pigs-tts/main/tts_en/...`

1. Copy `tts_en/SweetDreams_EN_Workshop_Save.json` and `tts_en/SweetDreams_EN_Workshop_Save.png` into your TTS `Saves` folder.
2. Load it in TTS, verify all cards & PDF load cleanly, then click **Modding -> Workshop -> Upload**!

*(If hosting at a different URL or using Steam Cloud, re-run `python tts_en/patch_urls_en.py <base_url_or_mapping.json> --output tts_en/SweetDreams_EN_Workshop_Save.json`.)*
