---
name: xpression-project-edit
description: Inspect and batch-edit Ross XPression .xpf projects without the XPression UI. Use to rebrand a project from a template, repoint DataLinq sources or columns, recolour materials, swap logo/video files, rename materials, or audit what a project references.
---

# Editing XPression `.xpf` projects

An `.xpf` is an `xpFSO` container of zlib streams. Entry **1** is the whole project as XML; the rest are metadata and thumbnails. The tools in `tools/` read and write it losslessly: rebuilding an unedited file gives back identical bytes.

## Before you start

1. **Work on a copy and write to a new file name.** Never overwrite a project that is open in XPression. XPression keeps it in memory and will overwrite your edit on its next save.
2. Get the **latest saved** file. If the operator has been working in XPression, ask them to save, then re-read the file.
3. Run an audit first:
   ```bash
   python tools/xpf_edit.py summary  Project.xpf   # files, materials (+diffuse), scene objects, take groups
   python tools/xpf_edit.py datalinq Project.xpf   # DataLinq sources and column paths in use
   ```

## Common edits

| Task | Command |
|---|---|
| Rename the DataLinq source on every take | `xpf_edit.py relink IN OUT --from "2024 Applause" --to "FutureGems"` |
| Shift spreadsheet columns (columns inserted) | `xpf_edit.py shiftcols IN OUT --link FutureGems --map 2:3,3:4,5:6,6:7,9:10` |
| Recolour a material | `xpf_edit.py colour IN OUT --material Glass --hex 7D83FF` |
| Point a material at a new clip or image | `xpf_edit.py media IN OUT --old "Video\a.mov" --new "Video\a.avi"` |
| Rename a material | `xpf_edit.py rename-material IN OUT --old X --new Y` |

Chain edits through temporary files, or edit `001.xml` directly after `xpf_tool.py unpack`, then `pack` it again.

## How things are wired (what to look for in the XML)

- **Files**: `filemanager/{images,video,fonts,audio}/item`, relative to the project folder. Materials refer to files by global index (`fileids/id`, counting through images, then video, then fonts …). To swap a clip, change the **path**, not the index.
- **Materials**: `materials//material` → `passes/pass/diffuse` (`AARRGGBB`), plus `shaderfragments/fragment` (`Video`, `Texture`, `ReflectionMap2D` …). One material is often shared by several objects and scenes, so a single recolour can restyle a whole pack.
- **Objects**: `scenes/scene/objects//object` has `matid`/`matguid`, `position`, `scale`, `width`, `height`. Coordinates are in pixels with the origin at the bottom-left. A full-frame logo clip is usually a 1920×1080 quad scaled down (for example 0.2 as a lower-third bug, 0.8 on a full screen).
- **Takes**: `sequencer//item[@type="seqitem"]`, each with `templatedata/object[@id]/…/datasink` (`link`, `col`). `content` is only cached preview text and doesn't need editing.

## Check the result

1. Re-run `summary` and `datalinq` on the output and confirm the counts. For example, *400 datasinks* means 80 takes × 5 fields.
2. Confirm the XML parses (the tools refuse to write malformed XML).
3. Ask the operator to open the new file in XPression and look at the **error/status list**. It reports missing files, unsupported media and missing fonts by material.

## Gotchas

- Materials the operator adds in the UI may point at old files: check `fileids` against `filemanager`.
- XPression may rewrite paths (for example `..\Project\Video\x.mov` → `Video\x.mov`) when it saves. Match on the current text.
- An unused leftover material is harmless. Leave it unless asked.
