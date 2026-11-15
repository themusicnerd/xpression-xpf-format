---
name: xpression-media-prep
description: Make animated logos, stings and overlays with alpha for Ross XPression and get them into the XPression codec. Use when rendering clips for XPression, when a video material shows black or errors, or when building animated elements (for example twinkling sparkles) procedurally.
---

# Media for XPression

## The rule

**XPression 64-bit does not load QuickTime files** (QuickTime Animation, ProRes and the like). The error is *"Quicktime files are not supported in 64-bit … Please convert it to XPression codec."* Final clips should be **XPression codec (`XPVC`) `.avi`**.

## Workflow that works

1. Render frames with alpha (PNG sequence) at the project frame rate. 1080i/p59.94 projects use `60000/1001`.
2. Wrap them as **ProRes 4444 with alpha**:
   ```bash
   ffmpeg -framerate 60000/1001 -i frames/%04d.png -c:v prores_ks -profile:v 4444 \
          -pix_fmt yuva444p10le -alpha_bits 16 -vendor apl0 "LOGO - IN.mov"
   ```
3. On the XPression machine (or any PC with the Ross codec installed), convert the `.mov` to the XPression codec with **Ross's XPression Video Coder**. Match the project's resolution and frame rate. Alternatively, render straight to the XPression AVI codec from After Effects if the codec is installed there.
4. Save the result as `.avi` and point the material's file at it (see `xpression-project-edit` → `media`).

ffmpeg can't decode `XPVC`, so you can't inspect existing XPression clips outside XPression. Match their size and frame count from `ffprobe` output instead (it still reports width, height, frame rate and frame count).

## Designing full-frame logo clips

- Keep the clip the same size as the one it replaces (often 1920×1080 with the logo centred), so existing quads, scales and positions still line up.
- Leave a **transparent margin on every frame**, including any overshoot or "back" easing and drop shadows. Anything that touches the frame edge gets cut off flat (a circle turns into a "square" at the top and bottom).
- Match the original IN/OUT lengths (for example 150 and 100 frames) so scene directors stay in sync.
- For an animation that keeps going while the graphic holds, make the tail of the IN clip a seamless loop (for example frames 90–149, with every periodic motion using a 60-frame period). Then set Loop In/Out on the material's video fragment.
- Add a soft drop shadow under pastel or light artwork that sits on white, so it still reads on air.

## Procedural sparkles (pattern)

1. Load the logo PNG and label connected components in its alpha (`scipy.ndimage.label`).
2. Sparkles are the small, square-ish, low-fill components (fill < 0.16). Remove them from the lettering layer, and keep each one as its own sprite with its original gradient.
3. Animate each sprite: pop-in scale with an `easeOutBack` overshoot, staggered starts, then a periodic scale/rotate twinkle plus a white "glint" overlay at its peaks.
4. Add a few extra stars around the logo in brand colours, with a soft glow, clamped inside the frame.
5. Composite on a transparent 1920×1080 canvas → PNG sequence → ProRes 4444 → XPression codec.

## Check the result

- Before encoding, scan every frame's alpha on the outer 2 px rows and columns. They should all be zero.
- Make an MP4 preview over the bar/background colour for sign-off.
- After conversion, check the error/status list in XPression for the material.
