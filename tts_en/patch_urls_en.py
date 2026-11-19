# -*- coding: utf-8 -*-
"""Patch local file:/// URLs in tts_en/SweetDreams_EN_TTS_Save.json to public HTTPS URLs for Steam Workshop.

Usage:
  1. List all unique asset URLs:
     python tts_en/patch_urls_en.py --list

  2. Patch using a GitHub raw / CDN base URL:
     python tts_en/patch_urls_en.py https://raw.githubusercontent.com/Magnoliar/sweet-dreams-pigs-tts/main --output tts_en/SweetDreams_EN_Workshop_Save.json

  3. Patch using a JSON mapping file (filename or relative path -> https://...):
     python tts_en/patch_urls_en.py urls_mapping.json --output tts_en/SweetDreams_EN_Workshop_Save.json
"""
import argparse
import json
import os
import sys
from urllib.parse import quote

TTS_EN_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SAVE = os.path.join(TTS_EN_DIR, 'SweetDreams_EN_TTS_Save.json')
URL_KEYS = ('ImageURL', 'ImageSecondaryURL', 'FaceURL', 'BackURL', 'PDFUrl')


def collect_urls(obj, found=None):
    if found is None:
        found = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in URL_KEYS and isinstance(v, str) and v:
                found.add(v)
            else:
                collect_urls(v, found)
    elif isinstance(obj, list):
        for item in obj:
            collect_urls(item, found)
    return found


def rel_repo_path(url):
    norm = url.replace('\\', '/')
    for marker in ('/tts_en/', '/tts/', '/print/'):
        idx = norm.rfind(marker)
        if idx != -1:
            return norm[idx + 1:]
    return None


def patch_with_base(url, base_url, encode=True):
    rel = rel_repo_path(url)
    if not rel:
        return url
    base = base_url.rstrip('/')
    if encode:
        rel_enc = '/'.join(quote(seg, safe='') for seg in rel.split('/'))
        return f'{base}/{rel_enc}'
    return f'{base}/{rel}'


def patch_with_mapping(url, mapping):
    if url in mapping:
        return mapping[url]
    rel = rel_repo_path(url)
    if rel and rel in mapping:
        return mapping[rel]
    fname = os.path.basename(url.replace('\\', '/'))
    if fname in mapping:
        return mapping[fname]
    return url


def apply_patch(obj, fn, stats):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in URL_KEYS and isinstance(v, str) and v:
                new_v = fn(v)
                if new_v != v:
                    obj[k] = new_v
                    stats['replaced'] += 1
            else:
                apply_patch(v, fn, stats)
    elif isinstance(obj, list):
        for item in obj:
            apply_patch(item, fn, stats)


def main():
    parser = argparse.ArgumentParser(description='Patch asset URLs in Sweet Dreams, Little Pigs! (EN) TTS Save JSON.')
    parser.add_argument('target', nargs='?', help='Base HTTPS URL or path to JSON mapping file')
    parser.add_argument('--list', action='store_true', help='List all unique asset URLs in the save JSON')
    parser.add_argument('--no-encode', action='store_true', help='Do not percent-encode characters in base URL mode')
    parser.add_argument('--input', default=DEFAULT_SAVE, help='Input TTS save JSON path')
    parser.add_argument('--output', default=None, help='Output TTS save JSON path (defaults to overwriting input)')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if args.list:
        urls = sorted(collect_urls(data))
        print(f'Found {len(urls)} unique asset URLs:')
        for u in urls:
            print(' ', u)
        return

    if not args.target:
        parser.print_help()
        sys.exit(1)

    if args.target.startswith('http://') or args.target.startswith('https://'):
        fn = lambda u: patch_with_base(u, args.target, encode=not args.no_encode)
    elif os.path.isfile(args.target):
        with open(args.target, 'r', encoding='utf-8') as mf:
            mapping = json.load(mf)
        fn = lambda u: patch_with_mapping(u, mapping)
    else:
        print(f'Error: target "{args.target}" is neither an http(s) URL nor an existing JSON file.', file=sys.stderr)
        sys.exit(1)

    stats = {'replaced': 0}
    apply_patch(data, fn, stats)
    out_path = args.output or args.input
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f'Patched {stats["replaced"]} URL fields -> {out_path}')


if __name__ == '__main__':
    main()
