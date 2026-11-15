# Ross XPression `.xpf` project format (unofficial notes)

Notes and a small Python tool for reading and rewriting **Ross Video XPression** project files (`.xpf`), worked out from a real XPression 11.5 (build 5816) project. They let developers and LLM agents inspect a project and batch-edit it (for example, repoint DataLinq sources, swap media, recolour materials) without clicking through the XPression UI.

> Unofficial and not affiliated with Ross Video. Always keep a backup and open the result in XPression to check it before going to air.

## Container layout

All integers are little-endian.

| Offset | Size | Field |
|---|---|---|
| 0 | 5 | magic `xpFSO` |
| 5 | 2 | version (`1`) |
| 7 | 8 | `u64` offset of the directory |
| 15 | 4 | `u32` entry count *n* |
| 19 | 4 | `XPF!` |
| 23 | to 120 | zero padding (data starts at byte 120) |

The entries follow the header back to back. Each one is a standalone **zlib** stream.

The directory at `dirofs`:

1. `n × u64`: pointers to the entry records, which come straight after this table.
2. `n × 30-byte` records: `u64 offset`, `u64 compressed size`, `u64 uncompressed size`, then 6 bytes (all zero in the samples seen).

Rebuilding the file this way (same header, entries in order, recalculated offsets) gave a byte-identical copy of an untouched project.

## Entries seen

| # | Content |
|---|---|
| 0 | `<project>` XML: version, frame size, frame rate, counts, last save |
| 1 | `<xpf>` XML: **the whole project** (scenes, materials, fonts, sequencer, DataLinq links …) |
| 2…19 | BMP scene and material thumbnails |
| 20 | `<thumbnaillist>` XML: take IDs that have thumbnails |
| 21… | BMP take thumbnails (320×180, 32-bit), in `thumbnaillist` order |

## Main XML (entry 1), useful paths

- `xpf/filemanager/{images,video,fonts,audio}/item`: file paths, relative to the project folder (for example `..\Other Project\Video\clip.avi`). Materials refer to these by **index** (`fileids/id`).
- `xpf/materials//material`: `name`, plus `passes/pass` with `diffuse` as `AARRGGBB`. Video and image textures are in `shaderfragments/fragment` (`fileid`, `playmode`, `loopin`, `loopout`, `freerun` …).
- `xpf/scenes/scene`: `name`, `objects//object[@type=quad|text|slab|layerobject|…]` with `position`, `scale`, `matid`, `width` and `height`. Coordinates are in pixels with the origin at the **bottom-left**.
- `xpf/sequencer/groups/group/items/item[@type="seqitem"]`: takes. Each has `content` (cached preview text) and `templatedata/object[@id]/items/item/datasink`:
  ```xml
  <datasink><link>MyDataLinqSource</link><col>values&lt;%Row%&gt;\array&lt;3&gt;</col></datasink>
  ```
  `link` is the DataLinq source name as set in the DataLinq Server. `col` is a path into the source's JSON: with the Google Sheets `values` API, `values<row>\array<column>` with both counted from 0. `%Row%` comes from the scene's DataLinq key, which is often `%relid%`.
- `xpf/datalinqservers/server`: host and port of the DataLinq server.

## Tool

```bash
python xpf_tool.py info   Project.xpf          # list entries
python xpf_tool.py unpack Project.xpf out/     # 000.xml, 001.xml, 002.bmp … + manifest.json
# edit out/001.xml (keep it well-formed UTF-8)
python xpf_tool.py pack   out/ Project-edited.xpf
```

`xpfpack.py` is the small read/write library behind it.

## Tips

- Edit the XML as text (search and replace) rather than re-serialising it, so XPression's formatting and attribute order stay as they were.
- Write to a **new** file name and open it in XPression. Don't overwrite a project that's currently open.
- Thumbnails and the cached take `content` text are refreshed by XPression; they don't need to match your edits.

## Media notes

- XPression's own rendered clips use the `XPVC` FourCC (Ross's codec). Tools like ffmpeg can't decode it.
- **XPression 64-bit does not load QuickTime files at all.** On 11.5 (build 5816), both QuickTime Animation and ProRes 4444 `.mov` files used as video materials fail with *"Quicktime files are not supported in 64-bit … Please convert it to XPression codec."* Convert clips to the XPression codec (`XPVC` in an `.avi`) on a machine that has the Ross codec installed, for example from a PNG/TGA image sequence with alpha.
- Swapping media by text edit works: change the path in `filemanager/video/item` (or drop the new clip in under the same file name). Materials refer to files by index, so nothing else needs to change.
