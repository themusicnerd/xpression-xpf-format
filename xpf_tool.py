#!/usr/bin/env python3
"""xpf_tool - unpack / repack Ross XPression .xpf project files.

  python xpf_tool.py info   Project.xpf
  python xpf_tool.py unpack Project.xpf outdir/      # writes 000.xml, 001.xml, 002.bmp ... + manifest.json
  python xpf_tool.py pack   outdir/ New.xpf          # rebuilds from an unpacked folder
"""
import json, os, sys, zlib
import xpfpack

def kind(raw):
    if raw[:5] == b'<?xml': return 'xml'
    if raw[:2] == b'BM': return 'bmp'
    return 'bin'

def info(path):
    h, es = xpfpack.read(path)
    for i, e in enumerate(es):
        raw = xpfpack.data(e)
        head = raw[:120].decode('utf8', 'replace').replace('\r\n', ' ') if kind(raw) == 'xml' else ''
        print(f'{i:3d} {kind(raw):3s} comp={len(e["comp"]):8d} raw={e["raw_size"]:8d} {head[:90]}')

def unpack(path, out):
    os.makedirs(out, exist_ok=True)
    h, es = xpfpack.read(path)
    man = dict(header=h.hex(), entries=[])
    for i, e in enumerate(es):
        raw = xpfpack.data(e)
        name = f'{i:03d}.{kind(raw)}'
        open(os.path.join(out, name), 'wb').write(raw)
        man['entries'].append(dict(file=name, extra=e['extra'].hex()))
    json.dump(man, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)

def pack(src, path):
    man = json.load(open(os.path.join(src, 'manifest.json')))
    es = []
    for m in man['entries']:
        raw = open(os.path.join(src, m['file']), 'rb').read()
        e = dict(extra=bytes.fromhex(m['extra']))
        xpfpack.set_data(e, raw)
        es.append(e)
    xpfpack.write(path, bytes.fromhex(man['header']), es)

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    {'info': lambda: info(sys.argv[2]), 'unpack': lambda: unpack(sys.argv[2], sys.argv[3]),
     'pack': lambda: pack(sys.argv[2], sys.argv[3])}.get(cmd, lambda: print(__doc__))()
