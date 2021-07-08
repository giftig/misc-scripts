#!/usr/bin/env python3

import argparse
import logging
import json
import os
import subprocess

logger = logging.getLogger(__name__)

RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
CYAN = '\033[36m'
GREY = '\033[90m'
RESET = '\033[0m'

MAX_FILENAME_LEN = 40


def _col(s, c):
    return '{}{}{}'.format(c, s, RESET)


def _trim(s):
    if len(s) <= MAX_FILENAME_LEN:
        return s

    return s[:MAX_FILENAME_LEN - 1] + '…'


def get_metadata(f):
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'stream',
        '-of', 'json',
        f
    ]

    output = None
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return None

    return json.loads(output.decode('utf-8'))


def _summarise_video(md):
    return {
        'encoding': md['codec_name'],
        'dim': '{coded_width}x{coded_height}'.format(**md),
        'aspect_ratio': md.get('display_aspect_ratio'),
        'duration': md.get('tags', {}).get('DURATION')
    }


def _summarise_audio(md):
    return {
        'lang': md.get('tags', {}).get('language'),
        'dub': md.get('disposition', {}).get('dub', 0) == 1
    }


def _summarise_sub(md):
    return {
        'lang': md.get('tags', {}).get('language')
    }


def summarise(md):
    """Take metadata and produce a stream summary"""
    summary = {'video': [], 'audio': [], 'subtitle': []}

    for s in md['streams']:
        codec_type = s['codec_type']

        func = {
            'video': _summarise_video,
            'audio': _summarise_audio,
            'subtitle': _summarise_sub
        }.get(codec_type)

        if func is None:
            continue

        res = func(s)

        summary[codec_type].append(res)

    return summary


def prettify(record):
    """Prettify a media summary"""
    v = record['video'][0]
    codec = v['encoding'].lower()
    codec = _col(codec, GREEN) if codec == 'h264' else _col(codec, RED)
    vidcomp = [
        codec,
        _col(v.get('aspect_ratio'), GREY),
        _col(v.get('dim'), GREY)
    ]
    vidtext = ' '.join([e for e in vidcomp if e is not None])
    vidtext = '🎥' + vidtext

    sub = record['subtitle'][0] if len(record['subtitle']) > 0 else None
    lang = (sub or {}).get('lang')
    lang = lang.lower() if lang else None
    subtext = None

    if sub is None:
        subtext = _col('---', RED)
    elif lang is None:
        subtext = _col('unk', YELLOW)
    else:
        col = GREEN if lang in {'en', 'eng'} else RED
        subtext = _col(lang, col)

    subtext = '🗨️' + subtext

    audio_langs = set(
        [(a.get('lang') or 'unk').lower() for a in record['audio']]
    )
    audtext = None

    if len(audio_langs) == 0:
        audtext = _col('---', RED)
    else:
        has_jp = bool(audio_langs.intersection({'jp', 'jpn'}))
        has_en = bool(audio_langs.intersection({'en', 'eng'}))
        is_unknown = not has_jp and not has_en and 'unk' in audio_langs

        entries = []
        if has_jp:
            entries.append('jpn')
        if has_en:
            entries.append('eng')
        if not entries:
            entries.append(audio_langs.pop())

        txt = '/'.join(entries)

        audtext = _col(
            txt,
            GREEN if has_jp else YELLOW if has_en or is_unknown else RED
        )

    audtext = '🔊' + audtext

    return '{:<50} {} {}'.format(vidtext, audtext, subtext)


def process_files(files):
    maxlen = 0
    for f in files:
        maxlen = max(maxlen, len(f))

    maxlen = min(maxlen, MAX_FILENAME_LEN)

    for f in files:
        if os.path.isdir(f):
            continue

        summary = '---FAILED---'
        try:
            summary = prettify(summarise(get_metadata(f)))
        except Exception:
            pass

        print(
            '{} {}'.format(
                _col(_trim(f).ljust(maxlen + 5), CYAN),
                summary
            )
        )


def expand_files(files):
    """Expand directories into file lists, recursing if desired"""
    expanded = []

    for f in files:
        if os.path.isdir(f):
            for root, _, files in os.walk(f):
                expanded.extend([os.path.join(root, ff) for ff in files])
        else:
            expanded.append(f)

    return expanded


def main():
    parser = argparse.ArgumentParser('media-summary')
    parser.add_argument(
        '-r', '-R', '--recursive', action='store_true', dest='recursive'
    )
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()

    files = args.files

    if args.recursive:
        files = expand_files(files)

    files.sort()

    process_files(files)


if __name__ == '__main__':
    main()
