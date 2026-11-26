#!/usr/bin/env python3
"""news-image-20261126 v4 — masthead is the date itself.

Identical to v3 (ATLAS layout, same facts, same illustrations) except
one change the user asked for: the big masthead title "THE ATLAS" is
replaced by the day, date and year — "THURSDAY 26 NOVEMBER 2026" — so
the date is the headline. The duplicate date at the top right is
removed (only "EDITION TO 01:00 UTC" and the slug stay there). The
title font size is fit-checked in code so it always fits one line.
"""
import math
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT = "entry4.png"

# ---- palette: cream paper, navy, red, gold + vivid warm accents ----
PAPER = (246, 241, 227)
CARD = (255, 253, 246)
INK = (22, 35, 63)
NAVY = (27, 42, 74)
NAVY2 = (34, 52, 92)
RED = (179, 39, 30)
RED_D = (142, 31, 22)
GOLD = (200, 147, 42)
GOLD_L = (227, 179, 65)
TEAL = (31, 111, 107)
GREEN = (46, 125, 50)
GREY = (107, 107, 102)
LINE = (216, 208, 188)
SKY = (214, 226, 232)
DARK_SKY = (27, 42, 74)
ORANGE = (214, 96, 32)
AMBER = (235, 150, 40)
DUSK_TOP = (36, 46, 90)
DUSK_MID = (122, 70, 112)
DUSK_LOW = (232, 122, 58)
FLAME_O = (255, 140, 60)
FLAME_Y = (255, 205, 90)
SMOKE = (148, 150, 158)
SMOKE_D = (118, 120, 130)

FD = "/usr/share/fonts/truetype/dejavu/"
FL = "/usr/share/fonts/truetype/liberation/"


def F(path, size):
    return ImageFont.truetype(path, size)


SERIFB = lambda s: F(FD + "DejaVuSerif-Bold.ttf", s)
SERIF = lambda s: F(FD + "DejaVuSerif.ttf", s)
SERIFI = lambda s: F(FL + "LiberationSerif-Italic.ttf", s)
SANSB = lambda s: F(FD + "DejaVuSans-Bold.ttf", s)
SANS = lambda s: F(FD + "DejaVuSans.ttf", s)
MONOB = lambda s: F(FD + "DejaVuSansMono-Bold.ttf", s)
MONO = lambda s: F(FD + "DejaVuSansMono.ttf", s)


def wrap(d, text, font, max_w):
    """Greedy word wrap; returns list of lines that fit max_w."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text(d, xy, s, font, fill, anchor="la"):
    d.text(xy, s, font=font, fill=fill, anchor=anchor)


def vgrad_stops(d, x, y, w, h, stops, bands=48):
    """Vertical gradient through colour stops [(pos 0..1, (r,g,b)), ...]."""
    for i in range(bands):
        t = i / (bands - 1)
        c = stops[-1][1]
        for s in range(len(stops) - 1):
            p0, c0 = stops[s]
            p1, c1 = stops[s + 1]
            if p0 <= t <= p1:
                u = (t - p0) / (p1 - p0) if p1 > p0 else 0
                c = tuple(int(c0[k] + (c1[k] - c0[k]) * u) for k in range(3))
                break
        y0 = y + i * h / bands
        d.rectangle([x, y0, x + w, y + (i + 1) * h / bands + 1], fill=c)


def glow(d, cx, cy, rx, ry, c_outer, c_inner, steps=6):
    """Soft radial glow: concentric ellipses, outer (c_outer) to inner
    bright core (c_inner). Drawn largest first so the bright core sits
    on top. Pure flat colours — deterministic, no alpha needed."""
    for i in range(steps):
        t = i / (steps - 1)
        w = rx * (1 - t * 0.55)
        h = ry * (1 - t * 0.55)
        c = tuple(int(c_outer[k] + (c_inner[k] - c_outer[k]) * t)
                  for k in range(3))
        d.ellipse([cx - w, cy - h, cx + w, cy + h], fill=c)


def hgrad_stops(d, x, y, w, h, stops, bands=32):
    """Horizontal gradient through colour stops [(pos 0..1, (r,g,b))]."""
    for i in range(bands):
        t = i / (bands - 1)
        c = stops[-1][1]
        for s in range(len(stops) - 1):
            p0, c0 = stops[s]
            p1, c1 = stops[s + 1]
            if p0 <= t <= p1:
                u = (t - p0) / (p1 - p0) if p1 > p0 else 0
                c = tuple(int(c0[k] + (c1[k] - c0[k]) * u) for k in range(3))
                break
        x0 = x + i * w / bands
        d.rectangle([x0, y, x + (i + 1) * w / bands + 1, y + h], fill=c)


def status_chip(d, x, y, status):
    """Status tag, right-aligned at x. Returns its left edge."""
    colors = {"CONFIRMED": (GREEN, (255, 255, 255)),
              "REPORTED": (GOLD, (255, 255, 255)),
              "CLAIM": (RED, (255, 255, 255))}
    bg, fg = colors[status]
    font = SANSB(8)
    w = int(d.textlength(status, font=font)) + 8
    d.rounded_rectangle([x - w, y, x, y + 14], radius=3, fill=bg)
    d.text((x - w / 2, y + 7), status, font=font, fill=fg, anchor="mm")
    return x - w


# ---- world map: coarse continent polygons (lon, lat) ----
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-80, 73),
     (-65, 60), (-55, 47), (-70, 42), (-75, 35), (-80, 26), (-90, 21),
     (-97, 16), (-105, 20), (-115, 28), (-125, 40), (-125, 49),
     (-140, 60), (-155, 58), (-165, 60)],
    # Greenland
    [(-58, 64), (-45, 60), (-30, 68), (-22, 70), (-30, 76), (-55, 76),
     (-60, 74)],
    # South America
    [(-80, 10), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-72, -18),
     (-70, -23), (-65, -28), (-62, -35), (-58, -38), (-65, -45),
     (-68, -52), (-66, -55), (-70, -54), (-73, -50), (-73, -40),
     (-73, -30), (-77, -22), (-79, -15), (-80, -8)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 48), (0, 50), (3, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (28, 66), (25, 70),
     (18, 70), (12, 65), (5, 60), (-2, 57), (-5, 50), (-9, 43), (-9, 37)],
    # Africa
    [(-6, 35), (-10, 31), (-15, 27), (-17, 15), (-17, 12), (-12, 8),
     (-8, 4), (-4, 5), (6, 4), (9, 4), (13, -2), (12, -6), (13, -12),
     (12, -18), (16, -22), (16, -28), (20, -35), (26, -34), (32, -28),
     (35, -24), (40, -16), (41, -10), (46, -2), (51, 2), (51, 11),
     (44, 11), (40, 15), (38, 18), (37, 22), (35, 28), (33, 31),
     (30, 32), (22, 33), (11, 34), (10, 37)],
    # Asia
    [(28, 62), (40, 68), (50, 70), (60, 69), (70, 72), (80, 73), (90, 75),
     (100, 77), (110, 74), (120, 73), (130, 72), (140, 72), (150, 70),
     (160, 69), (170, 67), (178, 65), (170, 60), (162, 58), (158, 52),
     (150, 59), (142, 55), (140, 45), (135, 43), (130, 42), (127, 40),
     (122, 38), (120, 32), (115, 23), (110, 20), (108, 12), (105, 9),
     (103, 2), (100, 6), (97, 10), (94, 16), (91, 22), (88, 22), (85, 19),
     (80, 13), (77, 8), (74, 12), (70, 20), (66, 25), (61, 25), (57, 26),
     (54, 27), (52, 28), (50, 30), (48, 30), (44, 29), (42, 31), (40, 36),
     (36, 36), (33, 36), (30, 36), (28, 41), (28, 47), (30, 55), (28, 60)],
    # Australia
    [(113, -22), (114, -30), (115, -35), (118, -35), (124, -33), (129, -32),
     (132, -32), (135, -35), (138, -35), (140, -38), (145, -38), (150, -37),
     (153, -32), (153, -27), (150, -22), (146, -19), (142, -15), (142, -11),
     (137, -12), (135, -15), (132, -12), (130, -13), (126, -14), (122, -17),
     (118, -20)],
]


def _inside(px, py, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > py) != (yj > py):
            xint = (xj - xi) * (py - yi) / (yj - yi) + xi
            if px < xint:
                inside = not inside
        j = i
    return inside


def draw_map_base(d, x0, y0, w, h):
    """Dotted world map (equirectangular lon -168..192, lat 75..-55),
    no pins — pins are drawn separately so leader lines sit under them."""
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=4, fill=NAVY)
    for k in range(1, 6):
        gx = x0 + w * k / 6
        d.line([gx, y0 + 4, gx, y0 + h - 4], fill=(52, 68, 110), width=1)
    for k in range(1, 4):
        gy = y0 + h * k / 4
        d.line([x0 + 4, gy, x0 + w - 4, gy], fill=(52, 68, 110), width=1)

    step = 5
    xi = x0 + 3
    while xi < x0 + w - 2:
        yi = y0 + 3
        while yi < y0 + h - 2:
            lon = (xi - x0) / w * 360.0 - 168
            lat = 75 - (yi - y0) / h * 130.0
            if any(_inside(lon, lat, poly) for poly in CONTINENTS):
                d.ellipse([xi - 1, yi - 1, xi + 1, yi + 1], fill=(150, 168, 200))
            yi += step
        xi += step
    # map label + compass rose (atlas touches)
    d.text((x0 + 10, y0 + 8), "THE WORLD — 10 PINS, 34 STORIES",
           font=SANSB(9), fill=GOLD_L, anchor="la")
    cx, cy, r = x0 + w - 26, y0 + 26, 15
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GOLD_L, width=2)
    d.polygon([(cx, cy - r + 3), (cx - 5, cy + 6), (cx + 5, cy + 6)],
              fill=GOLD_L)
    d.text((cx, cy - r - 9), "N", font=SANSB(9), fill=GOLD_L, anchor="mb")


# display offsets (px) for pins that would overlap on the big map
PIN_OFFSETS = {14: (16, -12), 15: (-18, 12)}


def draw_pins(d, x0, y0, w, h, pins):
    """Numbered red pins; pins is a list of (num, lon, lat)."""
    def proj(lon, lat):
        px = x0 + (lon + 168) / 360.0 * w
        py = y0 + (75 - lat) / 130.0 * h
        return px, py

    for num, lon, lat in pins:
        px, py = proj(lon, lat)
        dx, dy = PIN_OFFSETS.get(num, (0, 0))
        if (dx, dy) != (0, 0):
            d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(255, 255, 255))
            d.line([px, py, px + dx, py + dy], fill=(255, 255, 255), width=1)
            px, py = px + dx, py + dy
        d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=RED,
                  outline=(255, 255, 255), width=1)
        d.text((px, py), str(num), font=SANSB(8), fill=(255, 255, 255),
               anchor="mm")

# ---------------------------------------------------------------------------
# Lead illustrations — NEW in v2, more vivid: richer warm colours,
# dynamic detailed flat-vector scenes (not the minimal v1 drawings)
# ---------------------------------------------------------------------------

def art_tariffs(d, x, y, w, h):
    """Tariff-rate bar chart, v3 — more REAL, market-fall feeling:
    warm paper ground with faint gridlines, bars with DEPTH (drop
    shadow, vertical gradient, bright top edge, gold cap highlight),
    Nasdaq line with pale-red AREA shading under it, a bright core,
    glow underlay and a bold arrowhead. The fall feels dramatic."""
    d.rectangle([x, y, x + w, y + h], fill=(238, 231, 210))
    # faint horizontal gridlines (paper texture / depth)
    for gy in (0.3, 0.55, 0.8):
        d.line([x + 8, y + h * gy, x + w - 8, y + h * gy],
               fill=(226, 218, 196), width=1)
    d.line([x + 8, y + h - 24, x + w - 8, y + h - 24], fill=INK, width=1)
    # baseline ticks
    for tx in range(5):
        txx = x + 8 + tx * (w - 16) / 4
        d.line([txx, y + h - 24, txx, y + h - 21], fill=INK, width=1)
    rates = [("CHN", 20), ("VNM", 20), ("IND", 17), ("EU", 15), ("SGP", 10)]
    bw = 32
    gap = (w - 16 - bw * len(rates)) / (len(rates) - 1)
    maxv = 20.0
    # Nasdaq line first, confined to the top band (y+4..y+13), ending
    # before the pill so it never crosses the bar labels below
    tag = "NASDAQ -4%"
    tw = int(d.textlength(tag, font=SANSB(9))) + 12
    pill_x0 = x + w - tw - 4
    pts = [(x + 12, y + 5), (x + w * 0.3, y + 8), (x + w * 0.55, y + 6),
           (pill_x0 - 12, y + 12)]
    # pale-red AREA shading under the falling line (market-fall mood)
    area = pts + [(pill_x0 - 12, y + 16), (x + 12, y + 16)]
    d.polygon(area, fill=(238, 196, 188))
    # soft glow underlay, then bright core, then arrowhead
    d.line(pts, fill=(244, 178, 168), width=9, joint="curve")
    d.line(pts, fill=(232, 130, 118), width=7, joint="curve")
    d.line(pts, fill=RED, width=3, joint="curve")
    d.polygon([(pill_x0 - 12, y + 12), (pill_x0 - 24, y + 7),
               (pill_x0 - 21, y + 16)], fill=RED)
    d.rounded_rectangle([pill_x0, y + 1, x + w - 4, y + 12], radius=3,
                        fill=RED)
    d.text((pill_x0 + tw / 2, y + 6), tag, font=SANSB(9),
           fill=(255, 255, 255), anchor="mm")
    bar_bot = y + h - 24
    for i, (lab, v) in enumerate(rates):
        bx = x + 8 + i * (bw + gap)
        bh = (h - 42) * v / maxv
        by = bar_bot - bh
        base = RED if v >= 20 else NAVY2
        dark = (150, 32, 24) if v >= 20 else (22, 36, 66)
        light = (205, 70, 58) if v >= 20 else (64, 84, 128)
        # drop shadow (depth) behind the bar
        d.rectangle([bx + 3, by + 3, bx + bw + 3, bar_bot + 3],
                    fill=(200, 192, 172))
        # vertical gradient body: light top -> base -> dark bottom
        vgrad_stops(d, bx, by, bw, bh,
                    [(0.0, light), (0.45, base), (1.0, dark)], bands=14)
        # bright top edge + gold cap with highlight
        d.rectangle([bx, by, bx + bw, by + 2], fill=(255, 255, 255))
        d.rectangle([bx, by, bx + bw, by + 3],
                    fill=GOLD_L if v >= 20 else GOLD)
        d.rectangle([bx, by + 3, bx + 3, bar_bot], fill=light)
        # value label with a cream backing so the line never strikes it
        lab_y = by - 2
        d.rectangle([bx + bw / 2 - 14, lab_y - 11, bx + bw / 2 + 14,
                     lab_y + 1], fill=(238, 231, 210))
        d.text((bx + bw / 2, lab_y), str(v) + "%", font=SANSB(10),
               fill=INK, anchor="mb")
        d.text((bx + bw / 2, y + h - 20), lab, font=SANSB(8), fill=GREY,
               anchor="ma")


def art_refinery(d, x, y, w, h):
    """Ras Tanura at dusk, v3 — MORE REAL, like a real scene: a soft
    layered dusk sky (deep indigo -> violet -> magenta -> burning
    orange -> gold horizon) with drifting cloud bands, a low sun with a
    wide glow, a detailed refinery (distillation towers with pipes,
    catwalks and lit windows, round storage tanks with highlights,
    drums), thick layered smoke plumes, and a flare with a layered
    flame, halo glow and warm light spilling onto the towers."""
    vgrad_stops(d, x, y, w, h, [(0.0, (30, 38, 82)), (0.3, (74, 52, 104)),
                                (0.55, (140, 66, 108)), (0.75, (208, 96, 62)),
                                (0.9, (240, 140, 66)),
                                (1.0, (248, 176, 92))], bands=64)
    # stars in the upper sky (fading with the dusk)
    for sx, sy, r in [(0.1, 0.1, 1), (0.28, 0.06, 1), (0.5, 0.12, 1),
                      (0.85, 0.08, 1), (0.94, 0.2, 1), (0.38, 0.04, 1),
                      (0.66, 0.05, 1), (0.2, 0.18, 1)]:
        d.ellipse([x + w * sx - r, y + h * sy - r, x + w * sx + r,
                   y + h * sy + r], fill=(222, 228, 242))
    # soft cloud bands drifting across the sky (layered, lit from below)
    for (cx, cy, cw, ch, col) in [
            (0.02, 0.16, 0.34, 0.1, (96, 72, 116)),
            (0.08, 0.2, 0.3, 0.09, (150, 88, 110)),
            (0.55, 0.12, 0.4, 0.09, (88, 64, 112)),
            (0.62, 0.16, 0.32, 0.08, (158, 92, 108)),
            (0.3, 0.3, 0.36, 0.08, (196, 116, 84))]:
        d.ellipse([x + w * cx, y + h * cy, x + w * (cx + cw),
                   y + h * (cy + ch)], fill=col)
    # low sun with a wide layered glow over the horizon
    sx, sy = x + w * 0.3, y + h * 0.66
    glow(d, sx, sy, 34, 20, (232, 122, 58), (255, 200, 110), steps=6)
    d.ellipse([sx - 11, sy - 11, sx + 11, sy + 11], fill=(255, 214, 130))
    d.ellipse([sx - 7, sy - 7, sx + 7, sy + 7], fill=(255, 236, 180))
    # thick layered smoke plumes drifting right (dark core, pale tops)
    for (ox, oy, ow, oh, col) in [
            (0.6, 0.0, 0.22, 0.2, (96, 96, 110)),
            (0.56, 0.08, 0.22, 0.22, (128, 128, 140)),
            (0.66, 0.14, 0.18, 0.18, (104, 104, 118)),
            (0.52, 0.2, 0.16, 0.14, (150, 150, 162)),
            (0.74, 0.06, 0.14, 0.12, (168, 168, 178)),
            (0.46, 0.28, 0.12, 0.1, (140, 140, 152))]:
        d.ellipse([x + w * ox, y + h * oy, x + w * (ox + ow),
                   y + h * (oy + oh)], fill=col)
    # ground with a warm light spill from the flare side
    d.rectangle([x, y + h - 20, x + w, y + h], fill=(14, 22, 42))
    hgrad_stops(d, x + w * 0.55, y + h - 20, w * 0.45, 20,
                [(0.0, (14, 22, 42)), (0.6, (66, 40, 34)),
                 (1.0, (120, 62, 32))], bands=16)
    # round storage tanks with highlights (foreground depth)
    for tx, tw in [(0.46, 0.09), (0.56, 0.08)]:
        d.ellipse([x + w * tx, y + h - 34, x + w * (tx + tw),
                   y + h - 28], fill=(120, 128, 148))
        d.rectangle([x + w * tx, y + h - 31, x + w * (tx + tw), y + h - 20],
                    fill=(74, 86, 118))
        d.rectangle([x + w * tx, y + h - 31, x + w * (tx + tw * 0.3),
                     y + h - 20], fill=(104, 116, 148))
        d.line([x + w * tx, y + h - 26, x + w * (tx + tw), y + h - 26],
               fill=(140, 148, 168), width=1)
    # distillation towers: body, pipes, catwalk, lit windows
    for tx, tw, th in [(0.06, 0.11, 0.5), (0.22, 0.13, 0.6),
                       (0.4, 0.11, 0.46)]:
        d.rectangle([x + w * tx, y + h - 20 - h * th, x + w * (tx + tw),
                     y + h - 20], fill=(52, 66, 100))
        # sunlit left edge + dark right edge (depth)
        d.rectangle([x + w * tx, y + h - 20 - h * th,
                     x + w * (tx + 0.02), y + h - 20], fill=(150, 96, 80))
        d.rectangle([x + w * (tx + tw - 0.02), y + h - 20 - h * th,
                     x + w * (tx + tw), y + h - 20], fill=(30, 40, 66))
        d.rectangle([x + w * tx, y + h - 20 - h * th, x + w * (tx + tw),
                     y + h - 20 - h * th + 4], fill=(96, 110, 146))
        # horizontal pipes between towers
        d.line([x + w * (tx + tw), y + h - 20 - h * th * 0.55,
                x + w * (tx + tw + 0.09), y + h - 20 - h * th * 0.55],
               fill=(96, 110, 146), width=2)
        for wy in (0.18, 0.32, 0.46):
            d.rectangle([x + w * (tx + 0.02), y + h * wy,
                         x + w * (tx + 0.05), y + h * wy + 3], fill=GOLD_L)
            d.rectangle([x + w * (tx + tw - 0.05), y + h * wy,
                         x + w * (tx + tw - 0.02), y + h * wy + 3],
                        fill=GOLD_L)
    # flare stack: wide halo glow, layered flame, light on the stack
    fx = x + w * 0.68
    glow(d, fx, y + h * 0.14, 26, 22, (232, 122, 58), (255, 190, 90),
         steps=6)
    d.ellipse([fx - 16, y + h * 0.02, fx + 16, y + h * 0.3], fill=FLAME_O)
    d.ellipse([fx - 10, y + h * 0.06, fx + 10, y + h * 0.26], fill=FLAME_Y)
    d.rectangle([fx - 3, y + h * 0.26, fx + 3, y + h - 20], fill=(96, 110, 146))
    d.rectangle([fx - 3, y + h * 0.26, fx - 1, y + h - 20],
                fill=(255, 170, 90))
    d.polygon([(fx, y + h * 0.02), (fx - 9, y + h * 0.24),
               (fx + 9, y + h * 0.24)], fill=FLAME_O)
    d.polygon([(fx, y + h * 0.1), (fx - 5, y + h * 0.24),
               (fx + 5, y + h * 0.24)], fill=(255, 232, 150))
    d.polygon([(fx, y + h * 0.16), (fx - 2, y + h * 0.24),
               (fx + 2, y + h * 0.24)], fill=(255, 255, 230))
    # oil drums with highlight
    for dx in (0.55, 0.6):
        d.rectangle([x + w * dx, y + h - 32, x + w * dx + 12, y + h - 20],
                    fill=GOLD)
        d.rectangle([x + w * dx, y + h - 32, x + w * dx + 3, y + h - 20],
                    fill=GOLD_L)
        d.line([x + w * dx, y + h - 26, x + w * dx + 12, y + h - 26],
               fill=(160, 110, 20), width=1)
    # 4 drones shot down, with dashed motion trails + red lights
    for dx, dy in [(0.82, 0.28), (0.88, 0.42), (0.76, 0.52), (0.9, 0.6)]:
        cx, cy = x + w * dx, y + h * dy
        for k in range(4):
            d.line([cx - 13 - k * 6, cy + 6 + k * 3, cx - 8 - k * 6,
                    cy + 6 + k * 3], fill=(200, 210, 225), width=1)
        d.line([cx - 6, cy - 4, cx + 6, cy + 4], fill=(220, 228, 240), width=2)
        d.line([cx - 6, cy + 4, cx + 6, cy - 4], fill=(220, 228, 240), width=2)
        d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=RED)
    # price tag
    tag = "BRENT $94.61  +3.5%"
    tw = int(d.textlength(tag, font=SANSB(10))) + 12
    d.rounded_rectangle([x + 8, y + 6, x + 8 + tw, y + 24], radius=3,
                        fill=(255, 253, 246))
    d.text((x + 14, y + 15), tag, font=SANSB(10), fill=RED, anchor="lm")


def art_airbase(d, x, y, w, h):
    """Savasleyka at dusk, v3 — MORE REAL: a deeper layered night sky
    (indigo -> slate violet -> ember horizon) with a pale moon glow,
    searchlight beams with a wide faint cone AND a narrow bright core,
    a runway in perspective with edge lights and a dashed centreline,
    five jets with soft ground shadows, panel lines and canopy dots,
    a layered blast (glow halo, orange shell, yellow core, white-hot
    heart, rising smoke column, flying embers) — motion and depth."""
    vgrad_stops(d, x, y, w, h, [(0.0, (20, 30, 58)), (0.35, (40, 46, 84)),
                                (0.6, (72, 62, 102)), (0.85, (120, 78, 96)),
                                (1.0, (150, 96, 88))], bands=64)
    # stars, some brighter, some dim
    for sx, sy, r, col in [(0.08, 0.08, 1, (210, 220, 238)),
                           (0.5, 0.05, 1, (210, 220, 238)),
                           (0.92, 0.12, 1, (210, 220, 238)),
                           (0.3, 0.16, 1, (190, 200, 225)),
                           (0.68, 0.06, 2, (235, 240, 250)),
                           (0.18, 0.26, 1, (180, 192, 220))]:
        d.ellipse([x + w * sx - r, y + h * sy - r, x + w * sx + r,
                   y + h * sy + r], fill=col)
    # pale moon glow, upper right
    mx, my = x + w * 0.82, y + h * 0.14
    glow(d, mx, my, 16, 16, (90, 100, 140), (225, 230, 240), steps=5)
    d.ellipse([mx - 5, my - 5, mx + 5, my + 5], fill=(240, 242, 248))
    # searchlight beams: wide faint cone + narrow bright core, from the
    # lower corners, sweeping up
    d.polygon([(x + 6, y + h), (x + w * 0.42, y + h * 0.1),
               (x + w * 0.55, y + h * 0.14), (x + w * 0.3, y + h)],
              fill=(120, 132, 162))
    d.polygon([(x + 16, y + h), (x + w * 0.45, y + h * 0.12),
               (x + w * 0.51, y + h * 0.14), (x + w * 0.28, y + h)],
              fill=(190, 200, 222))
    d.polygon([(x + w - 6, y + h), (x + w * 0.62, y + h * 0.08),
               (x + w * 0.5, y + h * 0.12), (x + w * 0.78, y + h)],
              fill=(120, 132, 162))
    d.polygon([(x + w - 16, y + h), (x + w * 0.59, y + h * 0.1),
               (x + w * 0.53, y + h * 0.12), (x + w * 0.76, y + h)],
              fill=(190, 200, 222))
    # ground with warm spill near the blast
    d.rectangle([x, y + h - 16, x + w, y + h], fill=(16, 24, 44))
    hgrad_stops(d, x, y + h - 16, w * 0.4, 16,
                [(0.0, (120, 62, 34)), (1.0, (16, 24, 44))], bands=12)
    # runway (diagonal band) with dashed centreline + edge lights
    d.polygon([(x + 10, y + h - 16), (x + w - 60, y + 6),
               (x + w - 30, y + 6), (x + 40, y + h - 16)], fill=(118, 122, 128))
    d.polygon([(x + 10, y + h - 16), (x + w - 60, y + 6),
               (x + w - 52, y + 6), (x + 22, y + h - 16)],
              fill=(150, 154, 158))
    for k in range(6):
        t0 = 0.08 + k * 0.16
        t1 = t0 + 0.08
        ax = x + 26 + (w - 90) * t0
        ay = y + h - 22 - (h - 36) * t0
        bx = x + 26 + (w - 90) * t1
        by = y + h - 22 - (h - 36) * t1
        d.line([ax, ay, bx, by], fill=(255, 255, 255), width=2)
    for k in range(5):
        t = 0.12 + k * 0.2
        ex = x + 16 + (w - 80) * t
        ey = y + h - 18 - (h - 30) * t
        d.ellipse([ex - 1, ey - 1, ex + 1, ey + 1], fill=FLAME_Y)
    # blast at the first jet: halo glow, layered shell, smoke column
    bx, by = x + w * 0.18, y + h * 0.55
    glow(d, bx, by, 30, 20, (214, 96, 32), (255, 190, 90), steps=6)
    d.ellipse([bx - 18, by - 12, bx + 18, by + 12], fill=FLAME_O)
    d.ellipse([bx - 11, by - 7, bx + 11, by + 7], fill=FLAME_Y)
    d.ellipse([bx - 5, by - 3, bx + 5, by + 3], fill=(255, 248, 220))
    # embers flying out of the blast
    for ex, ey in [(0.08, 0.44), (0.26, 0.4), (0.3, 0.62), (0.1, 0.66)]:
        d.ellipse([x + w * ex - 1, y + h * ey - 1, x + w * ex + 1,
                   y + h * ey + 1], fill=FLAME_Y)
    # layered smoke columns rising (dark core, pale lit top)
    for (ox, oy, ow, oh, col) in [(0.3, 0.4, 0.15, 0.12, (110, 112, 122)),
                                  (0.34, 0.34, 0.12, 0.1, (150, 150, 160)),
                                  (0.48, 0.28, 0.13, 0.1, (118, 120, 130)),
                                  (0.52, 0.22, 0.1, 0.08, (158, 158, 168)),
                                  (0.66, 0.2, 0.15, 0.11, (112, 114, 124)),
                                  (0.7, 0.14, 0.11, 0.08, (152, 152, 162))]:
        d.ellipse([x + w * ox, y + h * oy, x + w * (ox + ow),
                   y + h * (oy + oh)], fill=col)
    # 5 jets (top-down delta silhouettes) with soft ground shadow,
    # panel line, canopy dot, red X marks + motion lines
    jets = [(0.18, 0.55, 1), (0.36, 0.45, -1), (0.55, 0.38, 1),
            (0.72, 0.28, -1), (0.85, 0.18, 1)]
    for jx, jy, s in jets:
        cx, cy = x + w * jx, y + h * jy
        # soft shadow under the jet (depth)
        sh_y0, sh_y1 = sorted((cy + 8 * s, cy + 13 * s))
        d.ellipse([cx - 11, sh_y0, cx + 11, sh_y1],
                  fill=(10, 14, 28))
        d.line([cx - 16, cy + 10 * s, cx - 8, cy + 10 * s],
               fill=(200, 210, 225), width=1)
        d.polygon([(cx, cy - 13 * s), (cx - 10, cy + 9 * s),
                   (cx - 3, cy + 5 * s), (cx, cy + 9 * s),
                   (cx + 3, cy + 5 * s), (cx + 10, cy + 9 * s)],
                  fill=NAVY)
        # lighter top edge + panel line + canopy dot
        d.line([cx - 2, cy - 12 * s, cx - 2, cy + 4 * s],
               fill=(96, 116, 150), width=1)
        d.line([cx - 8, cy + 2 * s, cx + 8, cy + 2 * s],
               fill=(60, 76, 108), width=1)
        cp_y0, cp_y1 = sorted((cy - 8 * s, cy - 4 * s))
        d.ellipse([cx - 2, cp_y0, cx + 2, cp_y1], fill=TEAL)
        d.line([cx - 8, cy - 8, cx + 8, cy + 8], fill=RED, width=3)
        d.line([cx - 8, cy + 8, cx + 8, cy - 8], fill=RED, width=3)
    # big numeral + place label
    d.text((x + 12, y + h - 6), "5 PLANES", font=MONOB(16), fill=RED,
           anchor="lb")
    d.text((x + w - 10, y + h - 8), "NIZHNY NOVGOROD", font=SANSB(8),
           fill=(220, 226, 240), anchor="rb")


# ---------------------------------------------------------------------------
# Medium icons — v3, MORE REAL and more detailed (34x34): highlights,
# soft shadows, extra elements, richer colours, a sense of depth.
# Same names/signatures as v2 so the layout code is untouched.
# ---------------------------------------------------------------------------

def _ibg(d, x, y, fill):
    d.rounded_rectangle([x, y, x + 34, y + 34], radius=4, fill=fill)
    # soft top light (depth) + faint bottom shade
    d.rounded_rectangle([x, y, x + 34, y + 3], radius=2, fill=(255, 255, 255))
    d.line([x + 4, y + 33, x + 30, y + 33], fill=(0, 0, 0), width=1)


def icon_rocket(d, x, y):
    _ibg(d, x, y, DARK_SKY)
    for sx, sy in [(5, 5), (28, 4), (18, 8), (30, 20), (6, 26)]:
        d.ellipse([x + sx, y + sy, x + sx + 2, y + sy + 2], fill=(210, 220, 240))
    # layered engine flame (orange -> yellow -> white core)
    d.polygon([(x + 17, y + 25), (x + 12, y + 33), (x + 22, y + 33)],
              fill=ORANGE)
    d.polygon([(x + 17, y + 27), (x + 14, y + 33), (x + 20, y + 33)],
              fill=FLAME_Y)
    d.polygon([(x + 17, y + 29), (x + 15, y + 33), (x + 19, y + 33)],
              fill=(255, 248, 220))
    d.polygon([(x + 17, y + 4), (x + 12, y + 18), (x + 22, y + 18)],
              fill=(255, 253, 246))
    d.line([x + 13, y + 5, x + 13, y + 17], fill=(220, 224, 232), width=1)
    d.rectangle([x + 13, y + 17, x + 21, y + 25], fill=RED)
    d.rectangle([x + 13, y + 17, x + 15, y + 25], fill=(205, 70, 58))
    d.polygon([(x + 12, y + 18), (x + 8, y + 25), (x + 13, y + 22)],
              fill=GOLD)
    d.polygon([(x + 22, y + 18), (x + 26, y + 25), (x + 21, y + 22)],
              fill=GOLD)
    d.ellipse([x + 15, y + 10, x + 19, y + 14], fill=TEAL)
    d.ellipse([x + 15, y + 10, x + 17, y + 12], fill=(140, 220, 210))


def icon_flame(d, x, y):
    _ibg(d, x, y, (240, 224, 200))
    # building with shading + lit windows (foreground depth)
    d.rectangle([x + 6, y + 21, x + 14, y + 31], fill=(90, 106, 140))
    d.rectangle([x + 6, y + 21, x + 8, y + 31], fill=(120, 134, 168))
    d.rectangle([x + 20, y + 24, x + 28, y + 31], fill=(58, 74, 110))
    d.rectangle([x + 8, y + 24, x + 10, y + 27], fill=FLAME_Y)
    d.rectangle([x + 22, y + 26, x + 24, y + 28], fill=FLAME_Y)
    # layered flame: outer orange, mid yellow, white-hot core
    d.polygon([(x + 17, y + 3), (x + 8, y + 21), (x + 14, y + 21),
               (x + 17, y + 15), (x + 20, y + 21), (x + 26, y + 21)],
              fill=ORANGE)
    d.polygon([(x + 17, y + 9), (x + 12, y + 21), (x + 22, y + 21)],
              fill=FLAME_Y)
    d.polygon([(x + 17, y + 14), (x + 14, y + 21), (x + 20, y + 21)],
              fill=(255, 248, 220))
    # embers + two-tone smoke
    d.ellipse([x + 5, y + 5, x + 9, y + 9], fill=SMOKE)
    d.ellipse([x + 25, y + 7, x + 30, y + 12], fill=SMOKE)
    d.ellipse([x + 6, y + 6, x + 8, y + 8], fill=(190, 192, 200))
    d.ellipse([x + 14, y + 2, x + 16, y + 4], fill=FLAME_Y)


def icon_store(d, x, y):
    _ibg(d, x, y, (240, 224, 200))
    # ground shadow under the shop
    d.ellipse([x + 5, y + 30, x + 29, y + 33], fill=(200, 188, 164))
    d.rectangle([x + 6, y + 12, x + 28, y + 31], fill=CARD, outline=NAVY,
                width=2)
    d.rectangle([x + 7, y + 13, x + 9, y + 30], fill=(232, 224, 204))
    for i, c in enumerate([RED, CARD, RED, CARD, RED]):
        d.rectangle([x + 5 + i * 5, y + 6, x + 10 + i * 5, y + 12], fill=c)
    d.line([x + 5, y + 12, x + 30, y + 12], fill=NAVY, width=1)
    d.rectangle([x + 10, y + 17, x + 14, y + 21], fill=TEAL)
    d.rectangle([x + 20, y + 17, x + 24, y + 21], fill=TEAL)
    d.line([x + 10, y + 17, x + 14, y + 17], fill=(140, 220, 210), width=1)
    d.rectangle([x + 14, y + 24, x + 20, y + 31], fill=NAVY)
    d.ellipse([x + 18, y + 27, x + 19, y + 28], fill=GOLD_L)
    d.rounded_rectangle([x + 26, y + 1, x + 33, y + 9], radius=2, fill=RED)
    d.text((x + 29, y + 5), "17h", font=SANSB(6), fill=(255, 255, 255),
           anchor="mm")


def icon_globe(d, x, y):
    _ibg(d, x, y, NAVY)
    # ocean with a lighter crescent (depth) + gold rim
    d.ellipse([x + 5, y + 5, x + 29, y + 29], fill=(58, 90, 140))
    d.ellipse([x + 8, y + 7, x + 20, y + 19], fill=(84, 120, 168))
    d.ellipse([x + 5, y + 5, x + 29, y + 29], outline=GOLD_L, width=2)
    d.ellipse([x + 17, y + 5, x + 17, y + 29], outline=GOLD_L, width=1)
    d.line([x + 5, y + 17, x + 29, y + 17], fill=GOLD_L, width=1)
    # two continents + a red pin with a white ring
    d.ellipse([x + 20, y + 9, x + 23, y + 12], fill=RED)
    d.ellipse([x + 19, y + 8, x + 24, y + 13], outline=(255, 255, 255),
              width=1)
    d.ellipse([x + 11, y + 20, x + 15, y + 24], fill=GOLD_L)
    d.ellipse([x + 22, y + 20, x + 26, y + 24], fill=(120, 160, 200))


def icon_pylon(d, x, y):
    _ibg(d, x, y, (240, 224, 200))
    # tower with shading + crossarm + insulator dots
    d.polygon([(x + 17, y + 4), (x + 9, y + 31), (x + 14, y + 31),
               (x + 17, y + 18), (x + 20, y + 31), (x + 25, y + 31)],
              fill=NAVY)
    d.polygon([(x + 17, y + 4), (x + 9, y + 31), (x + 12, y + 31),
               (x + 17, y + 18)], fill=(64, 84, 128))
    d.line([x + 4, y + 13, x + 30, y + 13], fill=NAVY, width=2)
    d.ellipse([x + 4, y + 11, x + 7, y + 14], fill=CARD)
    d.ellipse([x + 27, y + 11, x + 30, y + 14], fill=CARD)
    # lightning bolt with a soft glow behind it
    d.ellipse([x + 20, y + 8, x + 26, y + 24], fill=(250, 226, 150))
    d.polygon([(x + 24, y + 5), (x + 18, y + 16), (x + 22, y + 16),
               (x + 16, y + 27), (x + 27, y + 13), (x + 22, y + 13)],
              fill=GOLD_L)
    d.ellipse([x + 5, y + 5, x + 8, y + 8], fill=GOLD_L)
    d.ellipse([x + 27, y + 20, x + 30, y + 23], fill=GOLD_L)


def icon_scales(d, x, y):
    _ibg(d, x, y, (240, 224, 200))
    # base shadow + pillar with highlight + beam
    d.ellipse([x + 10, y + 29, x + 24, y + 32], fill=(200, 188, 164))
    d.line([x + 17, y + 5, x + 17, y + 28], fill=NAVY, width=2)
    d.line([x + 16, y + 5, x + 16, y + 28], fill=(96, 116, 150), width=1)
    d.line([x + 7, y + 8, x + 27, y + 8], fill=NAVY, width=2)
    d.ellipse([x + 15, y + 3, x + 19, y + 7], fill=GOLD)
    # chains + pans with shading (left pan heavier: justice tipping)
    d.line([x + 7, y + 8, x + 4, y + 17], fill=NAVY, width=1)
    d.line([x + 7, y + 8, x + 10, y + 17], fill=NAVY, width=1)
    d.line([x + 27, y + 8, x + 24, y + 15], fill=NAVY, width=1)
    d.line([x + 27, y + 8, x + 30, y + 15], fill=NAVY, width=1)
    d.polygon([(x + 1, y + 17), (x + 13, y + 17), (x + 7, y + 21)],
              fill=GOLD)
    d.polygon([(x + 1, y + 17), (x + 13, y + 17), (x + 7, y + 19)],
              fill=GOLD_L)
    d.polygon([(x + 21, y + 15), (x + 33, y + 15), (x + 27, y + 19)],
              fill=GOLD)
    d.rectangle([x + 12, y + 28, x + 22, y + 31], fill=NAVY)


def icon_nofly(d, x, y):
    _ibg(d, x, y, (240, 224, 200))
    # small cloud + shaded plane
    d.ellipse([x + 3, y + 4, x + 10, y + 8], fill=(214, 226, 232))
    d.ellipse([x + 7, y + 2, x + 13, y + 6], fill=(214, 226, 232))
    d.polygon([(x + 10, y + 18), (x + 16, y + 12), (x + 24, y + 12),
               (x + 21, y + 17), (x + 16, y + 18), (x + 13, y + 23)],
              fill=NAVY)
    d.polygon([(x + 10, y + 18), (x + 16, y + 12), (x + 19, y + 12),
               (x + 16, y + 18)], fill=(64, 84, 128))
    d.ellipse([x + 17, y + 13, x + 19, y + 15], fill=(140, 220, 210))
    # red ban circle + diagonal
    d.ellipse([x + 5, y + 5, x + 29, y + 29], outline=RED, width=3)
    d.line([x + 9, y + 25, x + 25, y + 9], fill=RED, width=3)


def icon_talks(d, x, y):
    _ibg(d, x, y, NAVY)
    # EU circle: blue disc, gold rim, 8 stars, 4-WAY pill
    d.ellipse([x + 7, y + 7, x + 27, y + 27], fill=(58, 90, 140))
    d.ellipse([x + 9, y + 9, x + 19, y + 19], fill=(84, 120, 168))
    d.ellipse([x + 7, y + 7, x + 27, y + 27], outline=GOLD_L, width=1)
    for k in range(8):
        a = math.pi * 2 * k / 8 - math.pi / 2
        sx, sy = x + 17 + 8 * math.cos(a), y + 17 + 8 * math.sin(a)
        d.ellipse([sx - 1.5, sy - 1.5, sx + 1.5, sy + 1.5], fill=GOLD_L)
    d.rounded_rectangle([x + 10, y + 28, x + 24, y + 33], radius=2,
                        fill=GOLD)
    d.text((x + 17, y + 30), "4-WAY", font=SANSB(6), fill=NAVY,
           anchor="mm")


def icon_building(d, x, y):
    _ibg(d, x, y, (240, 224, 200))
    # building with shading, lit + dark windows, ground shadow
    d.ellipse([x + 6, y + 30, x + 27, y + 33], fill=(200, 188, 164))
    d.rectangle([x + 8, y + 6, x + 25, y + 31], fill=(120, 124, 128))
    d.rectangle([x + 8, y + 6, x + 11, y + 31], fill=(150, 154, 158))
    d.rectangle([x + 22, y + 6, x + 25, y + 31], fill=(92, 96, 100))
    for wy in (10, 16, 22):
        d.rectangle([x + 11, y + wy, x + 15, y + wy + 3], fill=FLAME_Y)
        d.rectangle([x + 18, y + wy, x + 22, y + wy + 3], fill=CARD)
    d.rectangle([x + 12, y + 28, x + 16, y + 31], fill=NAVY)
    # red alert badge with glow
    d.ellipse([x + 23, y + 2, x + 34, y + 13], fill=(244, 178, 168))
    d.ellipse([x + 24, y + 3, x + 33, y + 12], fill=RED)
    d.text((x + 28, y + 7), "!", font=SANSB(9), fill=(255, 255, 255),
           anchor="mm")


def icon_asteroid(d, x, y):
    _ibg(d, x, y, DARK_SKY)
    # cratered rock: lit crescent, dark side, craters with inner shadow
    d.ellipse([x + 5, y + 7, x + 29, y + 31], fill=(150, 152, 148))
    d.ellipse([x + 5, y + 7, x + 18, y + 31], fill=(176, 178, 174))
    d.ellipse([x + 5, y + 7, x + 29, y + 31], outline=(110, 112, 108),
              width=1)
    d.ellipse([x + 11, y + 12, x + 19, y + 20], fill=(110, 112, 108))
    d.ellipse([x + 12, y + 13, x + 18, y + 19], fill=(96, 98, 94))
    d.ellipse([x + 20, y + 20, x + 25, y + 25], fill=(110, 112, 108))
    d.ellipse([x + 9, y + 22, x + 13, y + 26], fill=(110, 112, 108))
    # impact starburst + stars
    d.polygon([(x + 28, y + 4), (x + 25, y + 10), (x + 31, y + 10)],
              fill=FLAME_Y)
    d.polygon([(x + 29, y + 2), (x + 27, y + 12), (x + 31, y + 12)],
              fill=(250, 226, 150))
    for sx, sy in [(4, 4), (30, 6), (7, 30)]:
        d.ellipse([x + sx, y + sy, x + sx + 2, y + sy + 2], fill=(210, 220, 240))


def icon_chart(d, x, y):
    _ibg(d, x, y, (240, 224, 200))
    # gridline + axes + bars with gradient tops and shadows
    d.line([x + 5, y + 14, x + 30, y + 14], fill=(226, 218, 196), width=1)
    d.line([x + 5, y + 28, x + 30, y + 28], fill=INK, width=1)
    for i, bh in enumerate((18, 15, 12, 8)):
        bx = x + 7 + i * 6
        d.rectangle([bx + 1, y + 28 - bh + 1, bx + 5, y + 29],
                    fill=(200, 192, 172))
        d.rectangle([bx, y + 28 - bh, bx + 4, y + 28], fill=NAVY2)
        d.rectangle([bx, y + 28 - bh, bx + 4, y + 28 - bh + 2], fill=GOLD_L)
    # falling red line with pale area shading + arrowhead
    d.polygon([(x + 5, y + 8), (x + 30, y + 21), (x + 30, y + 24),
               (x + 5, y + 11)], fill=(238, 196, 188))
    d.line([x + 5, y + 8, x + 30, y + 21], fill=RED, width=2)
    d.polygon([(x + 30, y + 21), (x + 24, y + 19), (x + 28, y + 25)],
              fill=RED)


def icon_tanker(d, x, y):
    _ibg(d, x, y, (214, 226, 232))
    # two-tone sea + hull with shading, portholes, lit bridge windows
    d.rectangle([x, y + 24, x + 34, y + 34], fill=(168, 196, 208))
    d.line([x + 3, y + 28, x + 12, y + 28], fill=TEAL, width=1)
    d.line([x + 20, y + 30, x + 31, y + 30], fill=TEAL, width=1)
    d.rectangle([x + 4, y + 14, x + 18, y + 25], fill=(150, 152, 148))
    d.rectangle([x + 4, y + 14, x + 7, y + 25], fill=(176, 178, 174))
    d.ellipse([x + 6, y + 11, x + 16, y + 15], fill=(150, 152, 148))
    d.ellipse([x + 8, y + 19, x + 10, y + 21], fill=(90, 94, 96))
    d.ellipse([x + 13, y + 19, x + 15, y + 21], fill=(90, 94, 96))
    d.rectangle([x + 18, y + 18, x + 27, y + 25], fill=NAVY)
    d.rectangle([x + 21, y + 20, x + 25, y + 23], fill=FLAME_Y)
    d.ellipse([x + 8, y + 25, x + 13, y + 30], fill=INK)
    d.ellipse([x + 21, y + 25, x + 26, y + 30], fill=INK)
    # layered flame on the deck
    d.polygon([(x + 11, y + 2), (x + 7, y + 11), (x + 10, y + 11),
               (x + 11, y + 8), (x + 12, y + 11), (x + 15, y + 11)],
              fill=ORANGE)
    d.polygon([(x + 11, y + 6), (x + 9, y + 11), (x + 13, y + 11)],
              fill=FLAME_Y)

# ---------------------------------------------------------------------------
# Content (same facts as v1 / NEWS_NOTES.md; numbers match the notes)
# ---------------------------------------------------------------------------

LEADS = [
    dict(num=1, region="WORLD", clock="17:41", clock_sub="UTC",
         status="CONFIRMED", src="REUTERS",
         head="TRUMP HITS 14 TRADING PARTNERS WITH NEW TARIFFS",
         deck="China capped at 20% — 40% if the truce fails. EU, Japan, "
              "Korea at 15%. Nasdaq fell almost 4%.",
         art="tariffs"),
    dict(num=10, region="MIDDLE EAST", clock="15:16", clock_sub="UTC",
         status="CLAIM", src="REUTERS",
         head="HOUTHIS CLAIM STRIKE ON SAUDI'S BIGGEST REFINERY",
         deck="Riyadh says 4 drones were shot down; smoke seen over Ras "
              "Tanura. Brent settles at $94.61, up 3.5%.",
         art="refinery"),
    dict(num=4, region="EUROPE", clock="25 NOV", clock_sub="REPORTED",
         status="CONFIRMED", src="REUTERS",
         head="UKRAINE HITS RUSSIAN AIR BASE — 5 PLANES OUT",
         deck="Savasleyka, east of Moscow: 3 MiG-31s and 2 Su-34s knocked "
              "out in long-range strikes.",
         art="airbase"),
]

REGION_COLOR = {"WORLD": RED, "EUROPE": NAVY2, "MIDDLE EAST": GOLD,
                "AFRICA": GREEN, "AMERICAS": TEAL, "OCEANIA": (120, 70, 140)}

# medium cards grouped BY REGION (atlas gazetteer), 2 columns of 6:
# (num, region, time, status, source, headline, icon)
MEDIUM_COLS = [
    [
        (5, "EUROPE", "25 NOV", "CONFIRMED", "ISW",
         "RUSSIA POUNDS UKRAINE'S POWER GRID AS WINTER BITES",
         icon_pylon),
        (6, "EUROPE", "14:01 UTC", "CONFIRMED", "REUTERS",
         "POLAND PLANS NO-FLY ZONE ON EASTERN BORDER", icon_nofly),
        (7, "EUROPE", "16:20 UTC", "CONFIRMED", "ISW",
         "EU TO JOIN NEXT UKRAINE–RUSSIA TALKS", icon_talks),
        (8, "EUROPE", "OVERNIGHT", "REPORTED", "UKRAINE DAILY",
         "UKRAINIAN DRONES HIT TWO RUSSIAN REFINERIES OVERNIGHT",
         icon_flame),
        (9, "EUROPE", "REPORTED 25 NOV", "REPORTED", "UKR. GEN. STAFF",
         "RUSSIA BREAKS YEARLY TROOP-LOSS RECORD IN UKRAINE",
         icon_chart),
        (11, "MIDDLE EAST", "13:09 UTC", "CONFIRMED", "REUTERS",
         "JUDGES URGE DROPPING NETANYAHU'S BRIBERY CASE", icon_scales),
    ],
    [
        (12, "MIDDLE EAST", "EARLY WED", "CONFIRMED", "MEDICS",
         "SECOND HAMAS SECURITY CHIEF KILLED IN 24 HOURS",
         icon_building),
        (13, "MIDDLE EAST", "10:27 UTC", "CONFIRMED", "UN NEWS",
         "UN WARNS OF 'FURTHER ATROCITY CRIMES' IN GAZA", icon_globe),
        (2, "WORLD", "25 NOV", "CONFIRMED", "AP",
         "PAKISTAN'S FIRST ASTRONAUT REACHES CHINA'S SPACE STATION",
         icon_rocket),
        (3, "WORLD", "REPORTED 25 NOV", "REPORTED", "JABULANI RADIO",
         "CLOSE-UP REVEALS STADIUM-SIZED CRATER ON DART ASTEROID",
         icon_asteroid),
        (27, "AMERICAS", "EARLY WED", "CONFIRMED", "AP",
         "ALL CARTAGENA HOSTAGES FREED AFTER 17-HOUR SIEGE",
         icon_store),
        (15, "AFRICA", "02:14 · 26 NOV", "CONFIRMED", "AL JAZEERA",
         "FUEL TANKER FIRE KILLS 31 NEAR CAIRO", icon_tanker),
    ],
]

NUMBERS = [
    ("14", "TRADING PARTNERS HIT BY NEW US TARIFFS"),
    ("20%", "CHINA TARIFF CAP — 40% IF TRUCE FAILS"),
    ("$94.61", "BRENT CRUDE, UP 3.5% AFTER RAS TANURA"),
    ("31", "KILLED IN CAIRO TANKER FIRE"),
    ("5", "PLANES KNOCKED OUT AT SAVASLEYKA"),
    ("432,519", "RUSSIAN CASUALTIES IN 2026 SO FAR"),
]

ALSO = [
    (14, "Shipping attacks escalate in Strait of Hormuz"),
    (16, "RSF drone strikes kill 19 in Sudan's Blue Nile"),
    (17, "DR Congo rebels pull back; army retakes town"),
    (18, "Ebola responders trapped as fighting rages in Ituri"),
    (19, "Morocco funds defence industry: 22bn dirhams"),
    (20, "China opens graft probe into Shanghai party chief"),
    (21, "North Korea expels a Swiss diplomat"),
    (22, "India announces Rs 15,000 cr package for Nepal"),
    (23, "Bangladesh raises garment minimum wage 36%"),
    (24, "N. Korea troop buildup for Russia hasn't appeared"),
    (25, "US unveils F-15EX fighters at Kadena, Okinawa"),
    (26, "Xiamen Airlines orders 50 Boeing 737-8 jets"),
    (28, "Petrobras unveils a $122bn investment plan"),
    (29, "Venezuela reveals $237.5bn of public debt"),
    (30, "Colombia marks 10 years of its peace agreement"),
    (31, "Nasdaq slides almost 4% as AI fears spread"),
    (32, "Australia signs landmark treaty with Solomons"),
    (33, "Australia apologises to LGBTQ+ veterans"),
    (34, "Australian inflation jumps to 4.9%"),
]

# map pins: #32 swapped for #25 (Kadena) so no pin hides under a callout
PINS = [(1, -77, 39), (2, 99, 40), (4, 43, 55), (6, 21, 52),
        (10, 50, 27), (11, 35, 32), (14, 56, 26), (15, 31, 30),
        (25, 128, 26), (27, -75, 10)]

FOOTER = [
    ("DATE CHECK — ",
     "Every numbered story happened or was first reported 25–26 Nov 2026 "
     "(UTC). Flags: the Shenzhou-24 launch hour is disputed (morning vs "
     "sunset reports); the Dimorphos crater images are thinly sourced; "
     "the refinery names in #8 and the “20-year low” figure are reported, "
     "not confirmed; the Bezeq favour value differs (Reuters ~1.8bn "
     "shekels, CNN >1bn); the RSF toll is 19 vs 20; Cartagena hostage "
     "counts differ (20/25/30/50+); the Solomons’ non-renewal of its "
     "China pact was not confirmed by PM Wale."),
    ("LEFT OUT — ",
     "BepiColombo (Mercury orbit, 21 Nov), Indonesia VP names (submitted "
     "23 Nov), Huawei verdict & AFCON CAS ruling (24 Nov — yesterday’s "
     "edition)."),
    ("SOURCES — ",
     "Reuters · AP · Guardian · CNN · UN News · Al Jazeera · ISW · "
     "Ukraine Daily · Starlit Daily · AFREEQUE · SelfStudys · Libre News "
     "· OilPrice · Kitco · TVNZ.  CONFIRMED = verified · REPORTED = "
     "single source · CLAIM = asserted, unconfirmed."),
]

M = 22
CW = 980  # content width: x 22..1002

# hero map geometry
MAP_X, MAP_Y, MAP_W, MAP_H = M, 100, CW, 380
# lead callouts straddling the map's bottom edge (y 400..550)
CALL_Y, CALL_H, CALL_W = 400, 150, 290
CALL_X = [30, 367, 704]


def pin_xy(lon, lat):
    px = MAP_X + (lon + 168) / 360.0 * MAP_W
    py = MAP_Y + (75 - lat) / 130.0 * MAP_H
    return px, py


# leader lines: callout top edge -> map pin (drawn under pins + callouts)
LEADERS = [
    # (callout top point, pin lon/lat)
    ((270, CALL_Y), (-77, 39)),    # tariffs -> US
    ((596, CALL_Y), (43, 55)),     # Savasleyka
    ((704, CALL_Y), (50, 27)),     # Ras Tanura (diagonal)
]


def draw():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- top rule + masthead: the DATE is the headline (v4) ----
    d.rectangle([0, 0, W, 5], fill=RED)
    text(d, (M, 12), "THE WORLD, PINNED TO THE PAGE  ·  34 STORIES  ·  "
                     "7 REGIONS", SANSB(11), INK)
    # big date title, fit-checked to one line; max width leaves room
    # for the right-side edition lines
    title = "THURSDAY 26 NOVEMBER 2026"
    tsize = 48
    while d.textlength(title, font=SERIFB(tsize)) > CW - 110 and tsize > 30:
        tsize -= 1
    text(d, (M, 28), title, SERIFB(tsize), INK)
    rx = M + CW
    # no duplicate date here any more — only edition + slug
    text(d, (rx, 14), "EDITION TO 01:00 UTC", MONOB(11), RED, anchor="ra")
    text(d, (rx, 32), "NEWS-IMAGE-20261126", SANS(9), GREY, anchor="ra")
    text(d, (M, 74),
         "From the Shenzhou-24 launch to a tariff shock at 17:41 UTC and a "
         "tanker fire after midnight — every story pinned where it "
         "happened.", SERIFI(12), INK)
    d.line([M, 94, M + CW, 94], fill=INK, width=1)

    # ---- hero map ----
    draw_map_base(d, MAP_X, MAP_Y, MAP_W, MAP_H)
    # leader lines (under pins and callouts)
    for (lx, ly), (lon, lat) in LEADERS:
        px, py = pin_xy(lon, lat)
        d.line([lx, ly, px, py + 10], fill=(255, 255, 255), width=2)
        d.ellipse([px - 3, py + 7, px + 3, py + 13], fill=(255, 255, 255))
    draw_pins(d, MAP_X, MAP_Y, MAP_W, MAP_H, PINS)

    # ---- three lead callouts on the map ----
    art = {"tariffs": art_tariffs, "refinery": art_refinery,
           "airbase": art_airbase}
    for i, lead in enumerate(LEADS):
        cx = CALL_X[i]
        cy = CALL_Y
        d.rounded_rectangle([cx, cy, cx + CALL_W, cy + CALL_H], radius=5,
                            fill=CARD, outline=NAVY, width=2)
        d.rectangle([cx + 6, cy, cx + CALL_W - 6, cy + 4], fill=RED)
        # numbered pin badge on the callout's top-left corner
        bx, by = cx + 2, cy + 2
        d.ellipse([bx - 11, by - 11, bx + 11, by + 11], fill=RED,
                  outline=(255, 255, 255), width=2)
        d.text((bx, by), str(lead["num"]), font=SANSB(11),
               fill=(255, 255, 255), anchor="mm")
        # clock + status
        if lead["clock"] == "25 NOV":
            d.text((cx + 20, cy + 8), "25 NOV", font=MONOB(15), fill=INK,
                   anchor="la")
            d.text((cx + 92, cy + 12), "REPORTED", font=SANS(8), fill=GREY,
                   anchor="la")
        else:
            d.text((cx + 20, cy + 8), lead["clock"], font=MONOB(16),
                   fill=INK, anchor="la")
            d.text((cx + 78, cy + 13), "UTC", font=SANSB(9), fill=GREY,
                   anchor="la")
        status_chip(d, cx + CALL_W - 8, cy + 10, lead["status"])
        # vivid illustration
        art[lead["art"]](d, cx + 10, cy + 28, CALL_W - 20, 58)
        # headline + deck + source
        hy = cy + 90
        for ln in wrap(d, lead["head"], SANSB(11), CALL_W - 20)[:2]:
            d.text((cx + 10, hy), ln, font=SANSB(11), fill=INK, anchor="la")
            hy += 13
        dy = cy + 118
        for ln in wrap(d, lead["deck"], SANS(9), CALL_W - 20)[:2]:
            d.text((cx + 10, dy), ln, font=SANS(9), fill=(60, 60, 58),
                   anchor="la")
            dy += 10
        text(d, (cx + 10, cy + CALL_H - 9),
             "#%d · %s · %s" % (lead["num"], lead["region"], lead["src"]),
             SANSB(8), GREY)

    # ---- numbers strip: slim split-flap ----
    ny = 556
    cell_w, gap = 160, 4
    for i, (num, label) in enumerate(NUMBERS):
        cx = M + i * (cell_w + gap)
        d.rounded_rectangle([cx, ny, cx + cell_w, ny + 36], radius=3, fill=NAVY)
        d.line([cx + 4, ny + 17, cx + cell_w - 4, ny + 17],
               fill=(52, 68, 110), width=1)
        d.text((cx + cell_w / 2, ny + 2), num, font=MONOB(14),
               fill=(255, 253, 246), anchor="ma")
        lines = wrap(d, label, SANS(7), cell_w - 10)
        ly = ny + 19
        for ln in lines[:2]:
            d.text((cx + cell_w / 2, ly), ln, font=SANS(7),
                   fill=(200, 210, 225), anchor="ma")
            ly += 8

    # ---- gazetteer: 12 medium stories grouped by region, 2 columns ----
    gy = 596
    text(d, (M, gy), "THE GAZETTEER — 12 MORE STORIES, BY REGION",
         SANSB(11), INK)
    text(d, (M + CW, gy),
         "WORLD 3 · EUROPE 6 · MIDDLE EAST 5 · AFRICA 5 · ASIA 7 · "
         "AMERICAS 5 · OCEANIA 3", SANS(9), GREY, anchor="ra")
    row_h = 40
    col_w = (CW - 10) // 2
    for col, cards in enumerate(MEDIUM_COLS):
        cx = M + col * (col_w + 10)
        for r, (num, region, when, status, src, head, icon) in enumerate(cards):
            ry = 628 + r * row_h
            d.rounded_rectangle([cx, ry, cx + col_w, ry + row_h - 4], radius=4,
                                fill=CARD, outline=LINE, width=1)
            d.rectangle([cx, ry + 4, cx + 4, ry + row_h - 8],
                        fill=REGION_COLOR[region])
            icon(d, cx + 8, ry + 3)
            tx = cx + 48
            meta_red = "#%d · %s · " % (num, region)
            d.text((tx, ry + 4), meta_red, font=SANSB(8), fill=RED,
                   anchor="la")
            off = d.textlength(meta_red, font=SANSB(8))
            d.text((tx + off, ry + 4), "%s · %s · %s" % (when, src, status),
                   font=SANS(8), fill=GREY, anchor="la")
            hy = ry + 15
            for ln in wrap(d, head, SANSB(10), col_w - 54)[:2]:
                d.text((tx, hy), ln, font=SANSB(10), fill=INK, anchor="la")
                hy += 11

    # ---- ALSO: 19 more stories, 3 columns ----
    ay = 874
    text(d, (M, ay), "ALSO — 19 MORE STORIES", SANSB(11), INK, anchor="la")
    acol_w = (CW - 20) // 3
    for i, (num, line) in enumerate(ALSO):
        col = i // 7
        row = i % 7
        axx = M + col * (acol_w + 10)
        ayy = 886 + row * 9.5
        d.text((axx, ayy), str(num), font=SANSB(9), fill=RED, anchor="la")
        d.text((axx + 20, ayy), line, font=SANS(8), fill=INK, anchor="la")

    # ---- Date Check footer ----
    fy = 950
    d.line([M, fy, M + CW, fy], fill=INK, width=1)
    fy += 6
    for bold, body in FOOTER:
        lines = wrap(d, bold + body, SANS(8), CW)
        for ln in lines:
            d.text((M, fy), ln, font=SANS(8), fill=(60, 60, 58), anchor="la")
            fy += 9
        fy += 2
    return img, fy


def main():
    img, fy_end = draw()
    img.save(OUT, format="PNG")
    print("saved", OUT, img.size, "footer ends at y=%d" % fy_end)
    assert fy_end <= 1020, "footer overflows bottom edge"


if __name__ == "__main__":
    main()
