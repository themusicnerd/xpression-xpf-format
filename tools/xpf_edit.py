#!/usr/bin/env python3
"""xpf_edit - common batch edits on Ross XPression .xpf projects.

Every command reads IN.xpf and (for edits) writes OUT.xpf; the input is never modified.
Edits are text substitutions on the main project XML (entry 1), so XPression's own
formatting is preserved.

  python xpf_edit.py summary   IN.xpf
  python xpf_edit.py datalinq  IN.xpf                                  # list links / columns in use
  python xpf_edit.py relink    IN.xpf OUT.xpf --from "Old Source" --to "New Source"
  python xpf_edit.py shiftcols IN.xpf OUT.xpf --link "Source" --map 2:3,3:4,5:6,6:7,9:10
  python xpf_edit.py colour    IN.xpf OUT.xpf --material Glass --hex 7D83FF [--alpha FF]
  python xpf_edit.py media     IN.xpf OUT.xpf --old "Video\\a.mov" --new "Video\\a.avi"
  python xpf_edit.py rename-material IN.xpf OUT.xpf --old "Old_Video" --new "New_Video"
"""
import argparse, collections, re, sys
import xml.etree.ElementTree as ET
import xpfpack


def load(path):
    header, entries = xpfpack.read(path)
    return header, entries, xpfpack.data(entries[1]).decode('utf-8')


def save(path, header, entries, xml_text):
    ET.fromstring(xml_text.encode('utf-8'))          # refuse to write malformed XML
    xpfpack.set_data(entries[1], xml_text.encode('utf-8'))
    xpfpack.write(path, header, entries)
    print(f'wrote {path}')


def summary(xml_text):
    r = ET.fromstring(xml_text.encode('utf-8'))
    print('Files:')
    for cat in r.find('filemanager'):
        for it in cat:
            print(f'  {cat.tag:7s} {it.text}')
    print('Materials:')
    for m in r.find('materials').iter('material'):
        if m.get('id'):
            diff = m.find('.//pass/diffuse')
            frags = [f.findtext('name') for f in m.iter('fragment')]
            print(f'  {m.get("id"):>4} {m.findtext("name")!s:40s} diffuse={diff.text if diff is not None else "-"} {frags}')
    mats = {m.get('id'): m.findtext('name') for m in r.find('materials').iter('material') if m.get('id')}
    print('Scenes:')
    for s in r.find('scenes'):
        print(f'  {s.findtext("name")}')
        for o in s.find('objects').iter('object'):
            mid = o.findtext('matid')
            print(f'     {o.get("type"):12s} {o.findtext("name")!s:24s} {("mat=" + mats.get(mid, mid)) if mid else ""}')
    print('Sequencer:')
    for g in r.find('sequencer').iter('group'):
        n = len([i for i in g.iter('item') if i.get('type') == 'seqitem'])
        print(f'  group {g.get("id")} "{g.get("name")}" takes={n}')


def datalinq(xml_text):
    links = collections.Counter(re.findall(r'<link>([^<]*)</link>', xml_text))
    cols = collections.Counter(re.findall(r'<col>([^<]*)</col>', xml_text))
    print('DataLinq links:'); [print(f'  {v:5d}  {k}') for k, v in links.most_common()]
    print('Columns:'); [print(f'  {v:5d}  {k.replace("&lt;", "<").replace("&gt;", ">")}') for k, v in cols.most_common()]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('cmd')
    p.add_argument('inp')
    p.add_argument('out', nargs='?')
    p.add_argument('--from', dest='frm'); p.add_argument('--to')
    p.add_argument('--link'); p.add_argument('--map')
    p.add_argument('--material'); p.add_argument('--hex'); p.add_argument('--alpha', default='FF')
    p.add_argument('--old'); p.add_argument('--new')
    a = p.parse_args()

    header, entries, x = load(a.inp)
    if a.cmd == 'summary':
        return summary(x)
    if a.cmd == 'datalinq':
        return datalinq(x)
    if not a.out:
        sys.exit('this command needs an OUT.xpf path')

    if a.cmd == 'relink':
        old, new = f'<link>{a.frm}</link>', f'<link>{a.to}</link>'
        n = x.count(old); x = x.replace(old, new); print(f'relinked {n} datasinks')

    elif a.cmd == 'shiftcols':
        mapping = dict(tuple(int(v) for v in pair.split(':')) for pair in a.map.split(','))
        def fix(m):
            link, col = m.group(1), m.group(2)
            if a.link and link != a.link:
                return m.group(0)
            col = re.sub(r'array&lt;(\d+)&gt;', lambda c: f'array&lt;{mapping.get(int(c.group(1)), int(c.group(1)))}&gt;', col)
            return f'<link>{link}</link><col>{col}</col>'
        x, n = re.subn(r'<link>([^<]*)</link><col>([^<]*)</col>', fix, x)
        print(f'checked {n} datasinks')

    elif a.cmd == 'colour':
        hexv = (a.alpha + a.hex).upper()
        pat = re.compile(r'(<material id="\d+"[^>]*><name>' + re.escape(a.material) + r'</name>.*?<diffuse>)([0-9A-Fa-f]{8})(</diffuse>)', re.S)
        x, n = pat.subn(lambda m: m.group(1) + hexv + m.group(3), x, count=1)
        print(f'recoloured {n} material(s) -> {hexv}')

    elif a.cmd == 'media':
        old, new = f'<item>{a.old}</item>', f'<item>{a.new}</item>'
        n = x.count(old); x = x.replace(old, new); print(f'replaced {n} file reference(s)')

    elif a.cmd == 'rename-material':
        old, new = f'<name>{a.old}</name>', f'<name>{a.new}</name>'
        n = x.count(old); x = x.replace(old, new); print(f'renamed {n} material(s)')
    else:
        sys.exit(f'unknown command {a.cmd}')

    save(a.out, header, entries, x)


if __name__ == '__main__':
    main()
