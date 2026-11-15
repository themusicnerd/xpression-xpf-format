---
name: xpression-datalinq-sheets
description: Drive Ross XPression graphics from a Google Sheet through DataLinq (JSON). Use when building or fixing a run-sheet-driven lower-third pack, mapping sheet columns to text and image fields, or when graphics show the wrong field after columns were added or moved.
---

# Google Sheets → XPression DataLinq

## The pattern

1. The operator keeps a Google Sheet (one row per take). Typical columns: `ETA | AT | ID | Top Text | Bottom Text | Filename | Song Name | Song Artist | Spotify URL | Art | Song Album Art URL`.
2. A **JSON DataLinq source** in the XPression DataLinq Server reads the Sheets `values` API:
   `https://sheets.googleapis.com/v4/spreadsheets/<SHEET_ID>/values/<TAB>!A1:M100?alt=json&key=<API_KEY>`
   Build the URL in a helper tab of the sheet so it is easy to change.
3. Each take field uses a datasink of the form `values<%Row%>\array<N>`:
   - `values<r>` is the **0-based row** of the returned range. Row 0 is the header row.
   - `array<N>` is the **0-based column** within the range (A = 0 when the range starts at column A).
   - `%Row%` comes from a scene DataLinq key, usually `%relid%`, so take 1 reads row 1, and so on.

## When columns change

Inserting columns to the **left** of mapped fields moves every index. Work out the new numbers from the header row, then:

```bash
python tools/xpf_edit.py datalinq Project.xpf                      # see current indices
python tools/xpf_edit.py shiftcols Project.xpf Project-new.xpf --link MySource --map 2:3,3:4,5:6,6:7,9:10
```

Also **widen the range** in the source URL (for example `A1:I100` → `A1:M100`). Otherwise the right-hand columns silently drop out.

The Sheets API drops **trailing** empty cells but keeps **leading** ones as `""`. Empty ETA/AT columns on the left therefore don't shift anything.

## Sheet-side tips

- Fill the album-art column with a formula (for example a custom `getSpotifyAlbumArt(url)` Apps Script that reads Spotify's oEmbed `thumbnail_url`), so the operator only pastes Spotify links.
- Build the filename with a formula that includes the concert or show name. Then multi-show days don't produce clashing recordings.
- Keep one header row and spacer rows per show; IDs restart per show.
- Don't put API keys in public repos. Restrict the key to the Sheets API and referrer/IP where you can.

## Check the result

- Open the source URL in a browser and count across the header array to confirm each index.
- In XPression, select a take → Template Data → each published object's DataLinq tab should show the source and `values<%Row%>\array<N>` you expect.
- Use **Live Update** so text edits in the sheet appear on air without re-taking.
