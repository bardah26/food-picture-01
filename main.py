#!/usr/bin/env python3
"""Make the best-looking food picture.

Draws one big cheeseburger on a plate, with fries and a ketchup dip,
using only the Python standard library. Deterministic: the same bytes
on every run. Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).
"""

import os
import struct
import zlib

W, H = 768, 1024
OUT_NAME = "entry.png"


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, rgb):
        self.w = w
        self.h = h
        self.px = bytearray(rgb * (w * h))

    def put(self, x, y, rgb):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(rgb)

    def blend(self, x, y, rgb, a):
        """Blend rgb over the pixel with alpha a (0..1)."""
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            for k in range(3):
                self.px[i + k] = int(self.px[i + k] * (1.0 - a) + rgb[k] * a)

    def hline(self, x0, x1, y, rgb):
        if y < 0 or y >= self.h:
            return
        x0 = max(0, x0)
        x1 = min(self.w - 1, x1)
        for x in range(x0, x1 + 1):
            self.put(x, y, rgb)

    def rect(self, x0, y0, x1, y1, rgb):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            self.hline(x0, x1, y, rgb)

    def blend_rect(self, x0, y0, x1, y1, rgb, a):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            for x in range(max(0, x0), min(self.w, x1 + 1)):
                self.blend(x, y, rgb, a)

    def circle(self, cx, cy, r, rgb):
        r2 = r * r
        for y in range(max(0, cy - r), min(self.h, cy + r + 1)):
            dy = y - cy
            dx = int((r2 - dy * dy) ** 0.5) if r2 - dy * dy >= 0 else 0
            self.hline(cx - dx, cx + dx, y, rgb)

    def blend_circle(self, cx, cy, r, rgb, a):
        r2 = r * r
        for y in range(max(0, cy - r), min(self.h, cy + r + 1)):
            dy = y - cy
            rest = r2 - dy * dy
            if rest < 0:
                continue
            dx = int(rest ** 0.5)
            for x in range(max(0, cx - dx), min(self.w, cx + dx + 1)):
                self.blend(x, y, rgb, a)

    def ellipse(self, cx, cy, rx, ry, rgb):
        for y in range(max(0, cy - ry), min(self.h, cy + ry + 1)):
            dy = (y - cy) / ry
            if abs(dy) > 1:
                continue
            dx = int(rx * (1.0 - dy * dy) ** 0.5)
            self.hline(cx - dx, cx + dx, y, rgb)

    def blend_ellipse(self, cx, cy, rx, ry, rgb, a):
        for y in range(max(0, cy - ry), min(self.h, cy + ry + 1)):
            dy = (y - cy) / ry
            if abs(dy) > 1:
                continue
            dx = int(rx * (1.0 - dy * dy) ** 0.5)
            for x in range(max(0, cx - dx), min(self.w, cx + dx + 1)):
                self.blend(x, y, rgb, a)

    def ellipse_outline(self, cx, cy, rx, ry, rgb, t=3):
        for k in range(t):
            self.ellipse(cx, cy, rx - k, ry - k, rgb) if False else None
        # draw by scanning: keep pixels whose normalized radius is in [1-t/r, 1]
        for y in range(max(0, cy - ry), min(self.h, cy + ry + 1)):
            for x in range(max(0, cx - rx), min(self.w, cx + rx + 1)):
                v = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if 0.92 <= v <= 1.0:
                    self.put(x, y, rgb)

    def polygon(self, pts, rgb):
        """Scanline fill for a simple polygon."""
        if not pts:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.hline(int(xs[i]), int(xs[i + 1]), y, rgb)

    def rounded_rect(self, x0, y0, x1, y1, r, rgb):
        self.rect(x0 + r, y0, x1 - r, y1, rgb)
        self.rect(x0, y0 + r, x1, y1 - r, rgb)
        for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                       (x0 + r, y1 - r), (x1 - r, y1 - r)):
            self.circle(cx, cy, r, rgb)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------- drawing
def draw():
    c = Canvas(W, H, (255, 243, 222))

    # Warm background: vertical gradient cream -> soft peach.
    top = (255, 246, 228)
    mid = (255, 228, 196)
    bot = (255, 205, 158)
    for y in range(H):
        t = y / (H - 1)
        col = lerp(top, mid, t) if t < 0.55 else lerp(mid, bot, (t - 0.55) / 0.45)
        c.hline(0, W - 1, y, col)

    # Soft light glow behind the plate.
    c.blend_circle(384, 640, 330, (255, 255, 255), 0.28)
    c.blend_circle(384, 640, 220, (255, 255, 255), 0.22)

    # Wooden table band at the bottom.
    c.rect(0, 800, W - 1, H - 1, (178, 126, 76))
    c.rect(0, 800, W - 1, 806, (150, 102, 58))
    for yy, shade in ((880, (160, 110, 62)), (960, (160, 110, 62))):
        c.rect(0, yy, W - 1, yy + 3, shade)
    # wood grain: a few long soft strokes
    for (gx, gy, glen) in ((60, 840, 200), (420, 850, 260), (120, 920, 300),
                           (500, 930, 200), (250, 990, 280), (620, 990, 120)):
        c.blend_rect(gx, gy, gx + glen, gy + 3, (140, 95, 55), 0.35)

    # (fries and garnish are drawn at the end, on top of the plate,
    # so the plate does not cover them)

    # ---- plate shadow and plate ----
    c.blend_ellipse(384, 760, 315, 62, (120, 70, 40), 0.30)
    c.ellipse(384, 735, 305, 105, (238, 238, 232))
    c.ellipse(384, 735, 305, 105, (250, 250, 246))
    c.ellipse_outline(384, 735, 305, 105, (205, 205, 198), 4)
    c.ellipse_outline(384, 735, 258, 84, (225, 225, 218), 3)

    # ---- ketchup dip bowl, left of the plate ----
    c.blend_ellipse(150, 742, 72, 20, (120, 70, 40), 0.25)
    c.ellipse(150, 722, 68, 34, (250, 250, 246))
    c.ellipse(150, 716, 58, 24, (215, 40, 30))
    c.ellipse(150, 712, 44, 16, (235, 70, 50))
    c.blend_ellipse(138, 708, 16, 7, (255, 255, 255), 0.55)

    # ---- cherry tomato + parsley, on the plate in front of the burger ----
    c.circle(232, 792, 20, (215, 45, 35))
    c.blend_circle(225, 785, 7, (255, 255, 255), 0.6)
    c.circle(232, 770, 6, (90, 150, 60))
    # parsley leaves
    for (lx, ly) in ((560, 792), (590, 800), (535, 802)):
        c.ellipse(lx, ly, 16, 8, (70, 140, 55))

    # ---- burger: bottom bun ----
    c.rounded_rect(212, 700, 556, 762, 26, (222, 164, 72))
    c.rounded_rect(212, 700, 556, 722, 26, (235, 182, 95))
    c.rect(212, 748, 556, 762, (198, 140, 55))

    # ---- patty, with a bumpy edge ----
    c.rounded_rect(196, 658, 572, 712, 24, (108, 66, 32))
    for bx in range(210, 565, 32):
        c.circle(bx, 706, 12, (96, 58, 28))
    c.rect(196, 658, 572, 672, (128, 82, 42))
    # patty grill marks
    for gx in (260, 330, 400, 470):
        c.blend_rect(gx, 668, gx + 8, 700, (80, 48, 24), 0.5)

    # ---- cheese, dripping over the patty ----
    c.polygon([(200, 636), (568, 636), (568, 668), (200, 668)], (255, 172, 32))
    # drips
    for (dx, dlen) in ((230, 34), (300, 48), (370, 30), (440, 46), (510, 32)):
        c.polygon([(dx - 14, 664), (dx + 14, 664), (dx, 664 + dlen)], (255, 172, 32))
        c.circle(dx, 664 + dlen, 8, (255, 172, 32))
    c.rect(200, 636, 568, 646, (255, 196, 70))

    # ---- tomato slice ----
    c.ellipse(384, 628, 178, 26, (222, 62, 42))
    c.ellipse(384, 628, 158, 18, (238, 92, 62))
    c.ellipse(384, 628, 120, 10, (250, 120, 85))

    # ---- lettuce, wavy green band ----
    c.rect(204, 600, 564, 632, (112, 182, 72))
    for lx in range(212, 565, 28):
        c.circle(lx, 630, 15, (98, 168, 62))
        c.circle(lx + 14, 626, 12, (126, 196, 84))
    c.rect(204, 600, 564, 610, (138, 205, 95))

    # ---- top bun: big golden dome ----
    # dome gradient in horizontal bands
    dome_top = (246, 190, 92)
    dome_mid = (232, 168, 70)
    dome_bot = (210, 140, 52)
    for i, y in enumerate(range(440, 612)):
        t = i / 171.0
        col = lerp(dome_top, dome_mid, t) if t < 0.5 else lerp(dome_mid, dome_bot, (t - 0.5) * 2)
        dy = (y - 600) / 168.0
        if abs(dy) > 1:
            continue
        dx = int(196 * (1.0 - dy * dy) ** 0.5)
        c.hline(384 - dx, 384 + dx, y, col)
    # (no outline around the dome: a full ellipse ring would cut through
    # the burger below it)
    # sesame seeds
    c.blend_ellipse(305, 495, 58, 30, (255, 235, 180), 0.30)
    c.blend_ellipse(298, 490, 36, 18, (255, 255, 255), 0.22)
    # sesame seeds
    seeds = [
        (300, 500), (350, 470), (410, 480), (460, 510), (330, 540),
        (390, 545), (450, 555), (280, 560), (500, 560), (360, 505),
        (430, 520), (320, 585), (480, 590),
    ]
    for (sx, sy) in seeds:
        c.ellipse(sx, sy, 11, 6, (255, 240, 200))
        c.ellipse(sx, sy - 1, 9, 4, (255, 248, 220))

    # ---- fries on the plate, right of the burger ----
    fry_col = (250, 200, 80)
    fry_dark = (228, 172, 55)
    for (fx, fy) in ((566, 700), (580, 716), (560, 730)):
        c.rounded_rect(fx, fy, fx + 110, fy + 18, 8, fry_col)
        c.rect(fx + 96, fy, fx + 110, fy + 18, fry_dark)

    # ---- warm rim light on the plate's right edge ----
    c.blend_ellipse(640, 735, 40, 70, (255, 220, 160), 0.25)

    return c


# ---------------------------------------------------------------- PNG out
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(canvas, path):
    raw = bytearray()
    w = canvas.w
    for y in range(canvas.h):
        raw.append(0)  # filter: none
        raw += canvas.px[y * w * 3:(y + 1) * w * 3]
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    data = b"\x89PNG\r\n\x1a\n"
    data += chunk(b"IHDR", ihdr)
    data += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    data += chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    path = os.path.join(out_dir, OUT_NAME)
    write_png(draw(), path)
    print("wrote", path)


if __name__ == "__main__":
    main()
