#!/usr/bin/env python3
"""Review every decoded capture frame for repeats, tiny changes and possible pops.

Idea credit: gsimone's contact-sheet skill. Original code. Flags are review
candidates, not proof of renderer faults or dropped frames. Audio is ignored.
"""
import argparse
import csv
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw


def changed_pixels(a, b):
    return sum(any(p) for p in ImageChops.difference(a, b).getdata())


def analyze(video, out, columns=4):
    probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                            '-show_streams', '-show_frames', '-show_entries',
                            'stream=width,height:frame=best_effort_timestamp_time',
                            '-of', 'json', str(video)], capture_output=True, text=True, check=True)
    info = json.loads(probe.stdout)
    w, h = info['streams'][0]['width'], info['streams'][0]['height']
    times = [f.get('best_effort_timestamp_time', '') for f in info['frames']]
    records, states, thumbnails = [], [], []
    previous = None
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', str(video), '-map', '0:v:0',
                                    '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                                    '-threads', '1', '-'], stdout=subprocess.PIPE, stderr=errors)
        try:
            index = 0
            while True:
                # BufferedReader.read fills the requested size unless EOF occurs.
                raw = process.stdout.read(w*h*3)
                if not raw:
                    break
                if len(raw) != w*h*3:
                    raise ValueError('incomplete decoded frame')
                frame = Image.frombytes('RGB', (w, h), raw)
                count = changed_pixels(previous, frame) if previous is not None else None
                flags = []
                if count == 0:
                    flags.append('NO CHANGE')
                elif count is not None and count/(w*h) < 0.0005:
                    flags.append('TINY CHANGE')
                if count != 0:
                    states.append({'start': index, 'length': 0})
                    thumb = frame.copy()
                    thumb.thumbnail((240, 180))
                    thumbnails.append(thumb)
                states[-1]['length'] += 1
                records.append({'frame': index, 'time_seconds': times[index] if index < len(times) else '',
                                'state': len(states)-1, 'changed_pixels': count,
                                'changed_percent': 100*count/(w*h) if count is not None else '',
                                'flags': flags})
                previous = frame
                index += 1
            if process.wait() != 0:
                errors.seek(0)
                raise ValueError(errors.read().decode(errors='replace'))
        finally:
            process.stdout.close()
            if process.poll() is None:
                process.kill()
                process.wait()
    if not records:
        raise ValueError('capture has no video frames')
    pops = []
    for state in states[1:-1]:
        if state['length'] == 1:
            pops.append(state['start'])
            records[state['start']]['flags'].append('ONE-FRAME POP')
    with (out/'transitions.csv').open('w', newline='') as dest:
        writer = csv.DictWriter(dest, fieldnames=list(records[0]))
        writer.writeheader()
        for record in records:
            writer.writerow(dict(record, flags='; '.join(record['flags'])))
    sheet = Image.new('RGB', (columns*256, math.ceil(len(states)/columns)*216), 'black')
    draw = ImageDraw.Draw(sheet)
    for i, (state, thumb) in enumerate(zip(states, thumbnails)):
        x, y = (i % columns)*256, (i // columns)*216
        sheet.paste(thumb, (x, y))
        label = f"State {i}, frame {state['start']}, length {state['length']}"
        draw.text((x+2, y+182), label, fill='white')
        if state['start'] in pops:
            draw.text((x+2, y+198), 'ONE-FRAME POP', fill='yellow')
    sheet.save(out/'contact-sheet.png')
    lines = ['# Capture review', '', f'{len(records)} frames, {len(states)} states.', '',
             'States group consecutive frames with identical decoded RGB bytes. Frame indices start at 0.',
             'Differences use all pixels, without tolerance; TINY CHANGE means under 0.05 percent.',
             'Single-frame states between different neighbours are possible pops. Motion and capture noise can trigger them.',
             'NO CHANGE can be intentional; this does not establish a dropped frame.',
             'Label emulator and real-console captures separately and record capture settings.', '',
             '[Contact sheet](contact-sheet.png) and [per-frame transitions](transitions.csv).', '']
    for flag in ('NO CHANGE', 'TINY CHANGE', 'ONE-FRAME POP'):
        frames = [str(r['frame']) for r in records if flag in r['flags']]
        lines.append(f"{flag}: {', '.join(frames) or 'none'}")
    (out/'report.md').write_text('\n'.join(lines)+'\n')
    return records


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('video', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--columns', type=int, default=4)
    args = ap.parse_args()
    if args.columns < 1:
        ap.error('columns must be positive')
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        print('SKIP: ffmpeg and ffprobe are required for capture review')
        return 0
    try:
        records = analyze(args.video, args.out, args.columns)
    except (OSError, ValueError, KeyError, IndexError, subprocess.CalledProcessError) as exc:
        ap.error(str(exc))
    print(f"Reviewed {len(records)} frames in {args.out}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
