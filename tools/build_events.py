"""Check every event in the lines and build the developers' event reference sheet.

Reads dialogue/events.json (every event name and what the app should do) and each line's
markers. Stops with an error if a line uses an event that isn't in the list, so a typo can't
reach the app. Writes flutter/nova_character/EVENTS.md: events grouped by line, then the
ones not used in a line yet.

Usage: python3 tools/build_events.py
"""
import glob, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
catalog = {k: v for k, v in json.load(open(os.path.join(ROOT, 'dialogue', 'events.json'))).items() if not k.startswith('_')}

lines, used, unknown = [], set(), []
for p in sorted(glob.glob(os.path.join(ROOT, 'dialogue', '*', 'cues.json'))):
    line = os.path.basename(os.path.dirname(p))
    d = json.load(open(p))
    events = [m for m in d.get('markers', []) if m['type'] == 'event']
    for m in events:
        if m['name'] not in catalog: unknown.append(f"{line}: '{m['name']}' at {m['time']} s")
        used.add(m['name'])
    lines.append((line, d.get('title') or line, events))
if unknown:
    sys.exit('Events missing from dialogue/events.json:\n  ' + '\n  '.join(unknown))

md = ['# Nova app events', '',
      'Events Nova sends to the app while he talks. Listen for them on `NovaController.events`; '
      'each `NovaEvent` has the `name` below and the time in the line. Generated from the Nova '
      'character repo, so this list always matches the lines in this package.', '',
      '## Every line', '', '| Event | What the app should do |', '|---|---|']
md += [f"| `{n}` | {v['does']} |" for n, v in catalog.items() if v.get('builtIn')]
for line, title, events in lines:
    md += ['', f'## {title}', '', f'Line id: `{line}`', '']
    if not events:
        md.append('No events in this line.')
        continue
    md += ['| Time | Event | What the app should do |', '|---|---|---|']
    md += [f"| {m['time']:.2f} s | `{m['name']}` | {catalog[m['name']]['does']} |" for m in events]
planned = [(n, v) for n, v in catalog.items() if n not in used and not v.get('builtIn') and not v.get('sample')]
if planned:
    md += ['', '## Planned (not in a line yet)', '', 'Names agreed for the FTUX flow. They appear in a line once its audio is timed.', '',
           '| Event | What the app should do |', '|---|---|']
    md += [f"| `{n}` | {v['does']} |" for n, v in planned]
open(os.path.join(ROOT, 'flutter', 'nova_character', 'EVENTS.md'), 'w').write('\n'.join(md) + '\n')
print('events checked:', len(used), 'used,', len(planned), 'planned')
