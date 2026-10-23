#!/usr/bin/env python3
"""Render the crank previews to ../renders. Run export.py first (the STL views import them).

  python3 cad/tools/render.py            # everything
  python3 cad/tools/render.py crank_base # only images whose name contains one of the arguments
"""
import subprocess, sys, os, tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.dirname(HERE)
ROOT = os.path.dirname(CAD)
OUT = os.path.join(ROOT, 'renders')
STL = os.path.join(ROOT, 'stl')
ISO = '0,0,0,55,0,25,0'

# name: (source, size, camera, extra args, full CGAL render?)
#   source = .scad file in cad/, or 'stl:<part>' for an exported STL (print orientation)
VIEWS = {
    # viewall + autocenter: the exploded knob is 150 mm out on +x, so a fixed distance crops it
    'crank_assembly':  ('crank_assembly.scad', (1400, 1100), '0,0,0,62,0,32,0', ['-D', 'EXPLODE=45'], False),
    'crank_stack_sec': ('crank_assembly.scad', (1200, 900), '0,0,10,72,0,20,470', ['-D', 'SECTION=true'], False),
    'crank_base':      ('stl:base', (1100, 850), ISO, [], False),
    'crank_stator':    ('stl:stator', (1100, 850), ISO, [], False),
    'crank_top':       ('stl:top', (1100, 850), ISO, [], False),
    'crank_rotor':     ('stl:rotor', (1100, 850), ISO, [], False),
    'crank_gear_big':  ('stl:gear_big', (1100, 850), ISO, [], False),
    'crank_arm':       ('stl:arm', (1100, 850), ISO, [], False),
    'crank_tray':      ('stl:tray', (1100, 850), ISO, [], False),
}


def render(name, td):
    src, (w, h), cam, extra, full = VIEWS[name]
    extra = list(extra)
    if src.startswith('stl:'):
        part = src[4:]
        src = os.path.join(td, name + '.scad')
        with open(src, 'w') as f:
            f.write(f'import("{os.path.join(STL, "crank_" + part + ".stl")}");\n')
    else:
        src = os.path.join(CAD, src)
    view = ['--camera=' + cam] + (['--viewall', '--autocenter'] if cam.startswith('0,0,0,') else [])
    cmd = ['openscad', '-o', os.path.join(OUT, name + '.png'), f'--imgsize={w},{h}',
           '--colorscheme=Tomorrow', *(['--render'] if full else []), *view, *extra, src]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return name, r.returncode, (r.stderr.strip().splitlines()[-1:] or ['']) if r.returncode else ''


def main():
    os.makedirs(OUT, exist_ok=True)
    args = sys.argv[1:]
    names = [n for n in VIEWS if not args or any(a in n for a in args)]
    rc = 0
    with tempfile.TemporaryDirectory() as td, ThreadPoolExecutor(os.cpu_count() or 4) as ex:
        for name, code, err in ex.map(lambda n: render(n, td), names):
            print(f'{"ok  " if code == 0 else "FAIL"} {name}.png {err or ""}')
            rc |= code
    return 1 if rc else 0


if __name__ == '__main__':
    sys.exit(main())
