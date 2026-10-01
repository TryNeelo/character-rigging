"""Rebuild everything and zip the Flutter component for the developers.

Runs build_rig.py, build_preview.py (every line) and build_flutter.py, then writes
dist/nova_character-<version>.zip with the package and its demo app (no build output).

Usage: python3 tools/make_handoff.py
"""
import glob, os, re, subprocess, sys, zipfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
run = lambda *a: subprocess.run([sys.executable, *a], cwd=ROOT, check=True)
run('tools/build_rig.py')
for d in sorted(glob.glob(os.path.join(ROOT, 'dialogue', '*', 'cues.json'))):
    run('tools/build_preview.py', os.path.basename(os.path.dirname(d)))
run('tools/build_flutter.py')

PKG = os.path.join(ROOT, 'flutter', 'nova_character')
version = re.search(r'^version: (\S+)', open(os.path.join(PKG, 'pubspec.yaml')).read(), re.M).group(1)
SKIP = {'build', '.dart_tool', '.idea', 'Pods', '.symlinks', 'ephemeral', '.gradle'}
os.makedirs(os.path.join(ROOT, 'dist'), exist_ok=True)
out = os.path.join(ROOT, 'dist', f'nova_character-{version}.zip')
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for here, dirs, files in os.walk(PKG):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            if f in ('.DS_Store', 'pubspec.lock') and here == PKG: continue
            if f == '.DS_Store' or f.startswith('.flutter-plugins'): continue
            p = os.path.join(here, f)
            z.write(p, os.path.join('nova_character', os.path.relpath(p, PKG)))
print('wrote', out, f'{os.path.getsize(out) / 1024:.0f} KB')
