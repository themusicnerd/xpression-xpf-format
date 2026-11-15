"""Read/write XPression .xpf containers (xpFSO)."""
import struct, zlib

HDR_LEN = 120

def read(path):
    d = open(path, 'rb').read()
    assert d[:5] == b'xpFSO'
    dirofs, = struct.unpack_from('<Q', d, 7)
    n, = struct.unpack_from('<I', d, 15)
    ptrs = struct.unpack_from('<%dQ' % n, d, dirofs)
    entries = []
    for p in ptrs:
        off, csz, rsz = struct.unpack_from('<QQQ', d, p)
        extra = d[p + 24:p + 30]
        comp = d[off:off + csz]
        entries.append(dict(comp=comp, raw_size=rsz, extra=extra))
    return d[:HDR_LEN], entries

def data(entry):
    return zlib.decompress(entry['comp'])

def set_data(entry, raw, level=6):
    entry['comp'] = zlib.compress(raw, level)
    entry['raw_size'] = len(raw)

def write(path, header, entries):
    body = bytearray(header)
    recs = []
    for e in entries:
        recs.append((len(body), len(e['comp']), e['raw_size'], e['extra']))
        body += e['comp']
    dirofs = len(body)
    n = len(entries)
    rec_start = dirofs + 8 * n
    body += struct.pack('<%dQ' % n, *[rec_start + 30 * i for i in range(n)])
    for off, csz, rsz, extra in recs:
        body += struct.pack('<QQQ', off, csz, rsz) + extra
    struct.pack_into('<Q', body, 7, dirofs)
    struct.pack_into('<I', body, 15, n)
    open(path, 'wb').write(bytes(body))
