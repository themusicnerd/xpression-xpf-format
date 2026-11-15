"""Render a full-frame logo IN/OUT with animated sparkles (1920x1080, alpha PNG frames).

  LOGO=logo.png python sparkle_logo_render.py
  Then: ProRes 4444 (see skills/xpression-media-prep) -> XPression Video Coder.
"""
import os
"""Render Future Gems logo IN / OUT videos with animated sparkles (1920x1080, alpha)."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

W, H = 1920, 1080
CX, CY = W / 2, H / 2
CIRCLE_D = 930                     # a little under the Applause circle so overshoot never clips
LOGO_W = 750                       # logo width inside the circle
PERIOD = 60                        # twinkle period (frames) -> seamless loop 90..149
SRC = os.environ.get('LOGO', 'logo.png')   # transparent logo PNG; sparkles are auto-detected
OUT = sys.argv[1] if len(sys.argv) > 1 else 'frames'

OPAL = ['#7d83ff', '#aeabff', '#ffc5fc', '#ffbebb', '#fce39d', '#94f7ca', '#82e4f4']

def ease_out_back(t, s=1.70158):
    t = min(max(t, 0), 1) - 1
    return t * t * ((s + 1) * t + s) + 1

def ease_in_back(t, s=1.70158):
    t = min(max(t, 0), 1)
    return t * t * ((s + 1) * t - s)

def ease_out_cubic(t):
    t = min(max(t, 0), 1)
    return 1 - (1 - t) ** 3

def clamp01(t):
    return min(max(t, 0.0), 1.0)

# ---------- prepare logo pieces ----------
src = Image.open(SRC).convert('RGBA')
a = np.asarray(src)
lab, n = ndimage.label(a[..., 3] > 20)
objs = ndimage.find_objects(lab)
sparkle_ids = []
for i, s in enumerate(objs):
    h = s[0].stop - s[0].start; w = s[1].stop - s[1].start
    area = (lab[s] == i + 1).sum()
    if area / (w * h) < 0.16 and abs(w - h) < 0.05 * max(w, h):
        sparkle_ids.append(i + 1)

scale = LOGO_W / src.width
logo_h = src.height * scale
logo_x0 = CX - LOGO_W / 2
logo_y0 = CY - logo_h / 2

# letters only (sparkles removed)
letters = a.copy()
mask_sp = np.isin(lab, sparkle_ids)
# dilate so anti-aliased edges of sparkles are removed too
mask_sp = ndimage.binary_dilation(mask_sp, iterations=6)
letters[mask_sp, 3] = 0
letters_img = Image.fromarray(letters).resize((LOGO_W, round(logo_h)), Image.LANCZOS)
SH_PAD = 40
_la = Image.new('L', (letters_img.width + SH_PAD * 2, letters_img.height + SH_PAD * 2), 0)
_la.paste(letters_img.split()[3], (SH_PAD, SH_PAD))
_la = _la.filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * 0.42))
letters_shadow = Image.new('RGBA', _la.size, (59, 42, 107, 0))
letters_shadow.putalpha(_la)
LETTER_SH_OFFSET = (4, 9)

sparkles = []   # dicts: sprite (RGBA at native target size *1), centre, size
for k, sid in enumerate(sparkle_ids):
    s = objs[sid - 1]
    pad = 40
    y0, y1 = max(s[0].start - pad, 0), min(s[0].stop + pad, a.shape[0])
    x0, x1 = max(s[1].start - pad, 0), min(s[1].stop + pad, a.shape[1])
    crop = a[y0:y1, x0:x1].copy()
    crop[~ndimage.binary_dilation(lab[y0:y1, x0:x1] == sid, iterations=6), 3] = 0
    tw = max(4, round((x1 - x0) * scale * 2))   # 2x supersample for rotation quality
    th = max(4, round((y1 - y0) * scale * 2))
    sprite = Image.fromarray(crop).resize((tw, th), Image.LANCZOS)
    cx = logo_x0 + ((x0 + x1) / 2) * scale
    cy = logo_y0 + ((y0 + y1) / 2) * scale
    size = (s[1].stop - s[1].start) * scale
    sparkles.append(dict(sprite=sprite, cx=cx, cy=cy, size=size))

def white_copy(img):
    w = Image.new('RGBA', img.size, (255, 255, 255, 0)); w.putalpha(img.split()[3]); return w

# order sparkles by size (largest first) to stagger the pop-in
sparkles.sort(key=lambda d: -d['size'])
for sp in sparkles:
    sp['white'] = white_copy(sp['sprite'])

# ambient sparkles around the circle (recoloured copies of the largest star shape)
base = sparkles[0]['sprite']
base_a = np.asarray(base)[..., 3]

def tinted_star(hex_col, px):
    r, g, b = int(hex_col[1:3], 16), int(hex_col[3:5], 16), int(hex_col[5:7], 16)
    arr = np.zeros(base_a.shape + (4,), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3] = r, g, b, base_a
    img = Image.fromarray(arr).resize((px * 2, px * 2), Image.LANCZOS)
    return img

R = CIRCLE_D / 2
ambient = []
specs = [(28, 1.12, 150, 4), (72, 1.08, 95, 5), (150, 1.14, 120, 1), (205, 1.10, 85, 6),
         (250, 1.15, 135, 2), (322, 1.09, 100, 3), (112, 1.22, 70, 0), (345, 1.24, 60, 6)]
for j, (ang, rr, px, col) in enumerate(specs):
    th = math.radians(ang)
    cx_, cy_ = CX + math.cos(th) * R * rr, CY - math.sin(th) * R * rr
    lim = H / 2 - px * 1.3 - 20          # twinkle peak ~1.15x plus glow margin
    cy_ = min(max(cy_, CY - lim), CY + lim)
    ambient.append(dict(sprite=tinted_star(OPAL[col], px), cx=cx_, cy=cy_, size=px, phase=j * 0.37))

# soft white glow sprite for ambient sparkles
def glow_of(sprite):
    al = sprite.split()[3]
    big = Image.new('L', (sprite.width * 2, sprite.height * 2), 0)
    big.paste(al, (sprite.width // 2, sprite.height // 2))
    big = big.filter(ImageFilter.GaussianBlur(sprite.width / 6))
    g = Image.new('RGBA', big.size, (255, 255, 255, 0))
    g.putalpha(big.point(lambda v: int(v * 0.85)))
    return g

for d in ambient:
    d['glow'] = glow_of(d['sprite'])

# circle (supersampled for clean edge)
SS = 3
circ_big = Image.new('L', (CIRCLE_D * SS, CIRCLE_D * SS), 0)
ImageDraw.Draw(circ_big).ellipse((0, 0, CIRCLE_D * SS - 1, CIRCLE_D * SS - 1), fill=255)
circ_mask = circ_big.resize((CIRCLE_D, CIRCLE_D), Image.LANCZOS)
circle = Image.new('RGBA', (CIRCLE_D, CIRCLE_D), (255, 255, 255, 255))
circle.putalpha(circ_mask)
# subtle drop shadow so the white disc reads on the pastel / amethyst bar
shadow = Image.new('RGBA', (CIRCLE_D + 120, CIRCLE_D + 120), (40, 30, 90, 0))
sh_a = Image.new('L', shadow.size, 0)
sh_a.paste(circ_mask, (60, 60))
shadow.putalpha(sh_a.filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * 0.35)))

def paste_scaled(frame, img, cx, cy, sc, rot=0.0, alpha=1.0, ss=1):
    """paste img centred at cx,cy scaled by sc (img may be supersampled by ss)."""
    if sc <= 0.01 or alpha <= 0.003:
        return
    w = max(1, round(img.width * sc / ss)); h = max(1, round(img.height * sc / ss))
    im = img
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
        w = max(1, round(im.width * sc / ss)); h = max(1, round(im.height * sc / ss))
    im = im.resize((w, h), Image.LANCZOS)
    if alpha < 1:
        al = im.split()[3].point(lambda v: int(v * alpha))
        im.putalpha(al)
    frame.alpha_composite(im, (round(cx - w / 2), round(cy - h / 2))) if (
        0 <= round(cx - w / 2) and 0 <= round(cy - h / 2) and
        round(cx - w / 2) + w <= W and round(cy - h / 2) + h <= H) else _safe(frame, im, cx - w / 2, cy - h / 2)

def _safe(frame, im, x, y):
    tmp = Image.new('RGBA', frame.size, (0, 0, 0, 0))
    tmp.paste(im, (round(x), round(y)), im)
    frame.alpha_composite(tmp)

def twinkle(f, phase):
    """periodic (PERIOD frames) scale factor and brightness for a sparkle."""
    x = 2 * math.pi * (f / PERIOD + phase)
    sc = 1.0 + 0.24 * math.sin(x)
    rot = 8 * math.sin(x + 0.6)
    return sc, rot

def draw_state(f, circ_s, circ_a, logo_s, logo_a, sp_env, amb_env, mode='in'):
    frame = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if circ_s > 0.01 and circ_a > 0:
        paste_scaled(frame, shadow, CX, CY + 10, circ_s, alpha=circ_a)
        paste_scaled(frame, circle, CX, CY, circ_s, alpha=circ_a)
    # logo letters
    if logo_a > 0:
        lx = CX + (logo_x0 + LOGO_W / 2 - CX) * logo_s
        ly = CY + (logo_y0 + logo_h / 2 - CY) * logo_s
        paste_scaled(frame, letters_shadow, lx + LETTER_SH_OFFSET[0] * logo_s, ly + LETTER_SH_OFFSET[1] * logo_s, logo_s, alpha=logo_a)
        paste_scaled(frame, letters_img, lx, ly, logo_s, alpha=logo_a)
    # logo sparkles
    for i, sp in enumerate(sparkles):
        e = sp_env(i)
        if e <= 0:
            continue
        tsc, trot = twinkle(f, i * 0.23)
        sc = e * (1 + (tsc - 1) * clamp01(e))
        rot = (1 - clamp01(e)) * 120 + trot * clamp01(e)
        x = CX + (sp['cx'] - CX) * logo_s
        y = CY + (sp['cy'] - CY) * logo_s
        paste_scaled(frame, sp['sprite'], x, y, sc * logo_s, rot=rot, alpha=min(1, e * 1.5), ss=2)
        glint = max(0.0, math.sin(2 * math.pi * (f / PERIOD + i * 0.23))) ** 6 * clamp01(e)
        if glint > 0.02:
            paste_scaled(frame, sp['white'], x, y, sc * logo_s * 0.82, rot=rot, alpha=glint * 0.75, ss=2)
    # ambient sparkles outside the circle
    for j, d in enumerate(ambient):
        e = amb_env(j)
        if e <= 0:
            continue
        # gentle fade/twinkle cycle per sparkle (periodic)
        cyc = 0.5 + 0.5 * math.sin(2 * math.pi * (f / PERIOD + d['phase']))
        sc = e * (0.55 + 0.6 * cyc)
        al = e * (0.35 + 0.65 * cyc)
        rot = 25 * math.sin(2 * math.pi * (f / PERIOD + d['phase']))
        x = CX + (d['cx'] - CX) * circ_s
        y = CY + (d['cy'] - CY) * circ_s
        paste_scaled(frame, d['glow'], x, y, sc * 1.1, alpha=al * 0.8, ss=2)
        paste_scaled(frame, d['sprite'], x, y, sc, rot=rot, alpha=al, ss=2)
    return frame

def render_in(outdir, n=150):
    os.makedirs(outdir, exist_ok=True)
    for f in range(n):
        circ_s = ease_out_back(f / 24, 1.2) if f < 24 else 1.0
        circ_a = clamp01(f / 8)
        t_logo = (f - 10) / 26
        logo_s = 0.86 + 0.14 * ease_out_cubic(t_logo)
        logo_a = clamp01(t_logo * 1.4)
        def sp_env(i, f=f):
            t0 = 30 + i * 6
            return ease_out_back((f - t0) / 18, 2.6) if f >= t0 else 0.0
        def amb_env(j, f=f):
            t0 = 40 + j * 5
            return clamp01((f - t0) / 14) if f >= t0 else 0.0
        draw_state(f, circ_s, circ_a, logo_s, logo_a, sp_env, amb_env).save(f'{outdir}/{f:04d}.png')
        if f % 30 == 0:
            print('in', f, flush=True)

def render_out(outdir, n=100, start=90):
    os.makedirs(outdir, exist_ok=True)
    for k in range(n):
        f = start + k          # continue the twinkle phase from the IN loop point
        def sp_env(i, k=k):
            t0 = i * 3
            return 1 - ease_in_back((k - t0) / 16) if k >= t0 else 1.0
        def amb_env(j, k=k):
            return 1 - clamp01((k - j * 2) / 12)
        logo_a = 1 - clamp01((k - 12) / 18)
        logo_s = 1 - 0.1 * ease_out_cubic((k - 12) / 18)
        circ_s = 1 - ease_in_back((k - 22) / 26, 0.9) if k >= 22 else 1.0
        circ_a = 1 - clamp01((k - 40) / 8)
        draw_state(f, max(circ_s, 0), circ_a, logo_s, logo_a, sp_env, amb_env).save(f'{outdir}/{k:04d}.png')
        if k % 25 == 0:
            print('out', k, flush=True)

if __name__ == '__main__':
    which = sys.argv[2] if len(sys.argv) > 2 else 'both'
    if which in ('in', 'both'):
        render_in(os.path.join(OUT, 'in'))
    if which in ('out', 'both'):
        render_out(os.path.join(OUT, 'out'))
