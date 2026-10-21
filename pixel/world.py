"""Detailed GBA-overworld style map, drawn at 1x with 16px tiles (all original art).

Layout (rows of 16px):
  0-1   dense staggered forest
  2-8   your contribution graph, one cell per day (Sun..Sat)
  9     cliff ledge (with a stone staircase)
  10    dirt road the trainer walks on
  11    forest
"""
import math
import random
from PIL import Image, ImageDraw, ImageFilter
from .art import hx, draw_creature

T = 16
ROWS = 12
GRID_TOP = 2          # first day row
CLIFF_ROW, ROAD_ROW = 9, 10

C = {
    # vibrant mint field
    "grass": hx("7ee08e"), "grass_a": hx("70d684"), "grass_b": hx("8eea9a"),
    "grass_d": hx("4cba6a"), "grass_l": hx("bdf7b0"), "grass_dd": hx("3fa660"),
    # foliage ramp (dark -> light) + outline
    "out": hx("0a2e20"),
    "leaf": [hx("0e4630"), hx("17663c"), hx("238a48"), hx("3aae56"), hx("68d05e"), hx("b6f088")],
    "leaf_dark": [hx("0a3a30"), hx("0f5440"), hx("19744c"), hx("29955a"), hx("47b562"), hx("8ad88a")],
    "leaf_back": [hx("0b3c2a"), hx("125634"), hx("1c7840"), hx("2f984c"), hx("52b856"), hx("8edc78")],
    "bush": [hx("125a36"), hx("1d7a42"), hx("2e9c50"), hx("4cbe5c"), hx("86de6e"), hx("c4f69a")],
    "tree_d": hx("238a48"), "tree_m": hx("3aae56"), "tree_l": hx("68d05e"),
    "trunk": hx("94603a"), "trunk_d": hx("5a3620"), "trunk_l": hx("c08858"),
    "tall_d": hx("0f5a34"), "tall_m": hx("259848"), "tall_l": hx("52c062"), "tall_h": hx("a8f08c"),
    "road": hx("dca870"), "road_a": hx("d09c64"), "road_d": hx("a8703e"), "road_l": hx("f2c890"),
    "cliff": [hx("4a1c12"), hx("7c3420"), hx("a84a2c"), hx("cc6a3c"), hx("ea9258")],
    "cliff_out": hx("3a140c"),
    "stone": hx("c8c0b0"), "stone_d": hx("807868"), "stone_l": hx("f0eadc"),
    "water": [hx("1d4fae"), hx("2a6fd6"), hx("3a92ee"), hx("5cb6fa"), hx("a6e2ff")],
    "water_l": hx("a6e2ff"), "foam": hx("f2fcff"),
    "sand": hx("f0e2a0"), "sand_d": hx("d4b874"), "sand_l": hx("fff4c8"),
    "rock": hx("98a4b8"), "rock_d": hx("566278"), "rock_l": hx("dce6f2"),
    "lily": hx("4cc25a"), "lily_d": hx("1f7a3c"), "lily_l": hx("9ae67a"),
    "wall": hx("fff6e4"), "wall_d": hx("d6c4a4"), "wall_s": hx("b8a484"), "door": hx("6a4226"),
    "win": hx("5aaaf8"), "win_l": hx("dff4ff"),
    "fl_r": hx("ff5a6a"), "fl_y": hx("ffe04a"), "fl_w": hx("ffffff"), "fl_p": hx("f088ff"),
    "fl_b": hx("68b4ff"),
}
WILD_COLORS = ["#ff9f2e", "#ff6a9a", "#9a6cff", "#3cc8f0", "#9ee03c", "#ff5a48",
               "#ffd83a", "#d07cff", "#5aa8ff", "#e89a58", "#2ed8a8", "#ff8a6a"]
WILD_KINDS = ["blob", "bunny", "bird", "mushroom", "spark", "bot", "snake", "flame", "moon"]

SHADOW_TINT = (0.56, 0.68, 0.86)        # cool blue-green shadow (multiply)
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
_L = (-0.55, -0.72, 0.62)
_n = math.sqrt(sum(v * v for v in _L))
LIGHT = tuple(v / _n for v in _L)


def _shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def _dith(x, y):
    return (BAYER[y % 4][x % 4] + 0.5) / 16


def _ramp_pick(ramp, v, x, y):
    """Map v in 0..1 onto a colour ramp with ordered dithering between steps."""
    f = v * (len(ramp) - 1) + (_dith(x, y) - 0.5) * 0.9
    return ramp[max(0, min(len(ramp) - 1, int(round(f))))]


# ================================================================ sprites
def _lit_blob(size, circles, ramp, out, seed, rim=True, noise=0.09, ao=0.28):
    """Volumetric leafy clump: union of spheres lit from top-left, with creases
    between clumps, dithered ramp shading, rim light and a dark outline."""
    w, h = size
    rng = random.Random(seed)
    mask = Image.new("L", size, 0)
    md = ImageDraw.Draw(mask)
    for cx, cy, r in circles:
        md.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    m = mask.load()
    s = Image.new("RGBA", size, (0, 0, 0, 0))
    sp = s.load()
    lx, ly, lz = LIGHT
    for y in range(h):
        for x in range(w):
            if not m[x, y]:
                continue
            best = second = -99
            bn = (0, 0, 1)
            for k, (cx, cy, r) in enumerate(circles):
                dx, dy = (x + .5 - cx) / r, (y + .5 - cy) / r
                d2 = dx * dx + dy * dy
                if d2 > 1:
                    continue
                nz = math.sqrt(1 - d2)
                height = nz * r + cy * 0.55
                if height > best:
                    second, best, bn = best, height, (dx, dy, nz)
                elif height > second:
                    second = height
            i = max(0.0, bn[0] * lx + bn[1] * ly + bn[2] * lz) * 0.95 + 0.05
            if best - second < 1.3:                       # crease between clumps
                i -= 0.22
            i -= ao * (y / h) ** 2                         # darker underneath
            i += rng.uniform(-noise, noise)                # leaf texture
            sp[x, y] = _ramp_pick(ramp[:-1], max(0, min(1, i)), x, y) + (255,)
    # rim light on the lit edge, outline everywhere else
    edge = mask.filter(ImageFilter.MaxFilter(3))
    e = edge.load()
    for y in range(h):
        for x in range(w):
            if e[x, y] and not m[x, y]:
                sp[x, y] = out + (255,)
            elif rim and m[x, y]:
                up = y == 0 or not m[x, y - 1]
                left = x == 0 or not m[x - 1, y]
                if (up or left) and y < h * 0.6 and (x + y) % 3:
                    sp[x, y] = ramp[-1] + (255,)
    return s


def _tree(ramp, seed=1):
    rng = random.Random(seed)
    s = Image.new("RGBA", (26, 27), (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    o = C["out"] + (255,)
    d.rectangle([10, 17, 15, 25], fill=o)                         # trunk
    d.rectangle([11, 17, 14, 24], fill=C["trunk"] + (255,))
    d.line([11, 17, 11, 24], fill=C["trunk_l"] + (255,))
    d.line([14, 17, 14, 24], fill=C["trunk_d"] + (255,))
    d.point([(12, 21), (13, 19), (12, 23)], fill=C["trunk_d"] + (255,))
    d.line([9, 25, 16, 25], fill=o)                               # roots
    j = lambda: rng.uniform(-0.6, 0.6)
    circles = [(13 + j(), 6 + j(), 5.6), (7.5 + j(), 9 + j(), 5.0), (18.5 + j(), 9 + j(), 5.0),
               (13 + j(), 11 + j(), 5.5), (8 + j(), 14.5 + j(), 4.9), (18 + j(), 14.5 + j(), 4.9),
               (13 + j(), 16.5 + j(), 4.6)]
    canopy = _lit_blob((26, 23), circles, ramp, C["out"], seed)
    s.alpha_composite(canopy, (0, 0))
    return s


def _bush(seed=3):
    rng = random.Random(seed)
    j = lambda: rng.uniform(-0.5, 0.5)
    return _lit_blob((18, 15), [(6 + j(), 8, 4.6), (11 + j(), 6, 4.8), (12 + j(), 10, 4.2),
                                (7, 11 + j(), 3.8)], C["bush"], C["out"], seed + 50, ao=0.2)


def _house(roof, roof_d, roof_l):
    s = Image.new("RGBA", (26, 25), (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    o = C["out"] + (255,)
    A = lambda c: c + (255,)
    d.rectangle([3, 11, 22, 24], fill=o)                          # walls
    d.rectangle([4, 11, 21, 23], fill=A(C["wall"]))
    d.rectangle([18, 12, 21, 23], fill=A(C["wall_d"]))            # shaded side
    d.rectangle([4, 12, 21, 13], fill=A(C["wall_s"]))             # eave shadow
    d.line([4, 23, 21, 23], fill=A(C["wall_s"]))
    d.rectangle([11, 16, 14, 23], fill=o)                         # door
    d.rectangle([12, 17, 13, 23], fill=A(C["door"]))
    d.point([(13, 20)], fill=A(C["fl_y"]))
    for wx in (6, 17):                                            # windows + flower box
        d.rectangle([wx - 1, 15, wx + 2, 19], fill=o)
        d.rectangle([wx, 16, wx + 1, 18], fill=A(C["win"]))
        d.point([(wx, 16)], fill=A(C["win_l"]))
        d.line([wx - 1, 20, wx + 2, 20], fill=A(C["leaf"][2]))
        d.point([(wx - 1, 20), (wx + 1, 20)], fill=A(C["fl_r"]))
    d.rectangle([18, 1, 21, 7], fill=o)                           # chimney
    d.rectangle([19, 2, 20, 7], fill=A(C["stone"]))
    d.point([(19, 2)], fill=A(C["stone_l"]))
    d.polygon([(0, 12), (6, 2), (19, 2), (25, 12)], fill=o)       # roof
    d.polygon([(1, 11), (7, 3), (18, 3), (24, 11)], fill=A(roof))
    for y in range(4, 12):                                        # shingles + vertical gradient
        x0, x1 = 1 + (11 - y) * 6 // 9, 24 - (11 - y) * 6 // 9
        if y >= 9:
            d.line([x0, y, x1, y], fill=A(roof_d))
        if y % 2 == 0:
            for x in range(x0 + (y // 2) % 2 * 2, x1, 4):
                d.point([(x, y)], fill=A(roof_d))
    d.line([7, 3, 18, 3], fill=A(roof_l))
    d.line([2, 10, 7, 4], fill=A(roof_l))
    d.line([3, 10, 8, 4], fill=A(roof_l))
    return s


TREES = [_tree(C["leaf"], k) for k in range(4)]
TREES_BACK = [_tree(C["leaf_back"], k + 10) for k in range(3)]
TREES_DARK = [_tree(C["leaf_dark"], k + 20) for k in range(3)]
BUSHES = [_bush(k) for k in range(3)]
HOUSES = [_house(hx("f2463c"), hx("b02a2a"), hx("ff9c86")),
          _house(hx("3a7cf2"), hx("2350b8"), hx("94c4ff")),
          _house(hx("ff9a24"), hx("c0661a"), hx("ffd078"))]


# ================================================================ ground pieces
def _grass_field(img, seed=3):
    """Whole-map grass with low-frequency colour patches blended by dithering."""
    W, H = img.size
    rng = random.Random(seed)
    cell = 20
    small = Image.new("L", (W // cell + 3, H // cell + 3))
    small.putdata([rng.randrange(256) for _ in range(small.width * small.height)])
    noise = small.resize((small.width * cell, small.height * cell), Image.BICUBIC).load()
    px = img.load()
    tones = [C["grass_a"], C["grass"], C["grass_b"]]
    for y in range(H):
        for x in range(W):
            v = noise[x + 7, y + 7] / 255
            px[x, y] = _ramp_pick(tones, v, x, y)


def _grass_tile(d, x, y, rng):
    for _ in range(rng.randint(2, 4)):                            # grass blade clusters
        gx, gy = x + rng.randint(1, 12), y + rng.randint(3, 13)
        d.point([(gx, gy), (gx + 2, gy), (gx + 1, gy + 1), (gx + 4, gy + 1)], fill=C["grass_d"])
        d.point([(gx, gy - 1), (gx + 2, gy - 1)], fill=C["grass_l"])
        d.point([(gx + 4, gy)], fill=C["grass_l"])
    r = rng.random()
    if r < 0.11:                                                  # flower cluster
        col = rng.choice([C["fl_r"], C["fl_y"], C["fl_w"], C["fl_p"], C["fl_b"]])
        for _ in range(rng.randint(2, 4)):
            fx, fy = x + rng.randint(3, 12), y + rng.randint(3, 12)
            d.point([(fx, fy + 2)], fill=C["grass_dd"])
            d.point([(fx, fy - 1), (fx - 1, fy), (fx + 1, fy), (fx, fy + 1)], fill=col)
            d.point([(fx, fy)], fill=C["fl_y"] if col != C["fl_y"] else hx("ff8a3a"))
            d.point([(fx + 1, fy + 1)], fill=_shade(col, 0.7))
    elif r < 0.15:                                                # pebble
        px, py = x + rng.randint(3, 11), y + rng.randint(4, 11)
        d.ellipse([px, py + 1, px + 4, py + 3], fill=C["grass_dd"])
        d.ellipse([px, py, px + 3, py + 2], fill=C["rock_d"])
        d.point([(px + 1, py)], fill=C["rock_l"])


def _tall_grass_tile(d, x, y, frame):
    d.rectangle([x, y, x + T - 1, y + T - 1], fill=C["tall_m"])
    for yy in range(y, y + T, 2):                                 # dark base texture
        for xx in range(x + (yy // 2) % 2, x + T, 3):
            d.point([(xx, yy)], fill=C["tall_d"])
    sway = frame % 2
    for row, shift in ((0, 0), (5, 4), (10, 0)):
        for col in range(0, 16, 8):
            bx = x + col + shift - (sway if row == 5 else 0)
            by = y + row
            d.line([(bx, by + 5), (bx + 1, by + 3), (bx + 2, by + 1), (bx + 3, by + 3),
                    (bx + 4, by + 1), (bx + 5, by + 3), (bx + 6, by + 5)], fill=C["tall_d"])
            d.line([(bx + 1, by + 5), (bx + 2, by + 2)], fill=C["tall_l"])
            d.line([(bx + 4, by + 2), (bx + 5, by + 5)], fill=C["tall_l"])
            d.point([(bx + 2, by + 1), (bx + 4 + sway, by + 1)], fill=C["tall_h"])


def _cliff(img, x0, x1, y):
    """Grass lip + layered rock face with lit strata and boulders."""
    d = ImageDraw.Draw(img)
    rng = random.Random(5)
    R = C["cliff"]
    d.rectangle([x0, y + 3, x1, y + 15], fill=R[2])
    for x in range(x0, x1 + 1):                                   # wavy grass lip
        dip = (1 if (x // 5) % 2 else 0) + (1 if (x // 13) % 3 == 0 else 0)
        d.line([x, y, x, y + 2 + dip], fill=C["grass"])
        d.point([(x, y + 3 + dip)], fill=C["grass_dd"])
        d.point([(x, y + 4 + dip)], fill=C["cliff_out"])
        if (x * 7) % 11 == 0:                                     # dangling grass
            d.point([(x, y + 5 + dip)], fill=C["grass_dd"])
    for sy, tone in ((y + 7, 3), (y + 11, 3)):                    # strata
        x = x0
        while x < x1:
            w = rng.randint(6, 13)
            off = rng.randint(-1, 1)
            d.line([x + 1, sy + off, x + w - 2, sy + off], fill=R[tone])
            d.point([(x + 1, sy + off)], fill=R[4])
            d.line([x, sy + off + 1, x + w - 1, sy + off + 1], fill=R[2])
            d.line([x + w - 1, sy + off - 2, x + w - 1, sy + off + 2], fill=R[1])
            x += w
    x = x0
    while x < x1:                                                 # boulders
        x += rng.randint(10, 22)
        by = y + rng.randint(6, 10)
        d.ellipse([x, by, x + 5, by + 4], fill=R[1])
        d.ellipse([x, by, x + 4, by + 3], fill=R[3])
        d.point([(x + 1, by + 1)], fill=R[4])
    d.line([x0, y + 14, x1, y + 14], fill=R[1])
    d.line([x0, y + 15, x1, y + 15], fill=C["cliff_out"])


def _stairs(d, x, y):
    d.rectangle([x, y + 3, x + T - 1, y + T - 1], fill=C["stone_d"])
    for sy in range(y + 4, y + 16, 3):
        d.rectangle([x + 1, sy, x + T - 2, sy + 1], fill=C["stone"])
        d.line([x + 1, sy, x + T - 2, sy], fill=C["stone_l"])
        d.point([(x + T - 2, sy + 1)], fill=C["stone_d"])
    d.line([x, y + 3, x, y + T - 1], fill=C["cliff_out"])
    d.line([x + T - 1, y + 3, x + T - 1, y + T - 1], fill=C["cliff_out"])


def _road(img, x0, x1, y, rng):
    d = ImageDraw.Draw(img)
    px = img.load()
    for yy in range(y, y + T):
        for xx in range(x0, x1 + 1):
            v = 0.5 + 0.35 * math.sin(xx * 0.09 + yy * 0.4) * math.sin(xx * 0.023)
            px[xx, yy] = _ramp_pick([C["road_a"], C["road"]], v, xx, yy)
    for yy, k in ((y, 0.55), (y + 1, 0.7), (y + 2, 0.85)):        # cliff contact shadow
        for xx in range(x0, x1 + 1):
            if k < 0.8 or (xx + yy) % 2:
                px[xx, yy] = _shade(px[xx, yy], k)
    for xx in range(x0, x1 + 1, 2):                               # wheel ruts
        px[xx, y + 6] = C["road_l"]
        px[xx + 1, y + 11] = C["road_d"]
    for _ in range((x1 - x0) // 5):                               # pebbles
        qx, qy = rng.randint(x0, x1 - 3), y + rng.randint(4, 13)
        d.point([(qx, qy + 1), (qx + 1, qy + 1)], fill=C["road_d"])
        d.point([(qx, qy)], fill=C["road_l"])
    for xx in range(x0, x1 + 1):                                  # grass edge below
        if (xx * 5) % 7 < 3:
            d.point([(xx, y + T - 1)], fill=C["grass_d"])
        d.point([(xx, y + T - 2)], fill=C["road_d"]) if (xx * 3) % 5 == 0 else None


def _pond(img, x, y, w, h, frame, seed):
    """Sandy rim, wet edge, depth-banded water, lily pads, rock and glints."""
    d = ImageDraw.Draw(img)
    rng = random.Random(seed)
    d.rounded_rectangle([x, y + 1, x + w - 1, y + h - 1], radius=9, fill=C["sand_d"])
    d.rounded_rectangle([x, y, x + w - 1, y + h - 2], radius=9, fill=C["sand"])
    d.arc([x + 1, y, x + w - 2, y + 14], 200, 330, fill=C["sand_l"])
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([2, 2, w - 3, h - 3], radius=8, fill=255)
    depth = [mask]
    for k in (2, 4, 7):
        depth.append(depth[-1].filter(ImageFilter.MinFilter(3 if k == 2 else 5)))
    W = C["water"]
    p = img.load()
    dm = [m.load() for m in depth]
    for yy in range(h):
        for xx in range(w):
            if not dm[0][xx, yy]:
                continue
            lvl = sum(1 for m in dm if m[xx, yy])                  # 1 edge .. 4 deep
            v = {1: 0.82, 2: 0.6, 3: 0.42, 4: 0.25}[lvl]
            if yy < 6:                                             # rim shadow on water
                v -= 0.25
            p[x + xx, y + yy] = _ramp_pick(W[:-1], max(0, v), x + xx, y + yy)
    d.line([x + 6, y + h - 4, x + w - 7, y + h - 4], fill=W[3])
    for k in range(max(1, w * h // 420)):                          # lily pads
        lx, ly = x + rng.randint(6, w - 13), y + rng.randint(9, h - 11)
        d.ellipse([lx, ly + 1, lx + 7, ly + 5], fill=W[0])
        d.ellipse([lx, ly, lx + 7, ly + 4], fill=C["lily_d"])
        d.ellipse([lx, ly, lx + 6, ly + 3], fill=C["lily"])
        d.point([(lx + 1, ly + 1), (lx + 2, ly + 1)], fill=C["lily_l"])
        d.line([lx + 3, ly + 2, lx + 6, ly + 2], fill=W[1])
        if rng.random() < 0.6:
            d.point([(lx + 2, ly)], fill=C["fl_p"])
            d.point([(lx + 2, ly + 1)], fill=C["fl_w"])
    if w * h > 600:                                                # a rock
        rx, ry = x + w - 14, y + h - 13
        d.ellipse([rx - 1, ry + 3, rx + 8, ry + 7], fill=W[0])
        d.ellipse([rx, ry, rx + 7, ry + 5], fill=C["rock_d"])
        d.ellipse([rx, ry, rx + 5, ry + 3], fill=C["rock"])
        d.point([(rx + 1, ry + 1), (rx + 2, ry + 1)], fill=C["rock_l"])
    for k in range(w * h // 240 + 2):                              # glints
        sx = x + 6 + (k * 17 + frame * 2) % (w - 14)
        sy = y + 10 + (k * 7) % max(1, h - 15)
        d.line([sx, sy, sx + 3, sy], fill=W[4])


def _apply_shadows(img, objects, W, H):
    """Cast every object's silhouette down-right as a cool, dithered shadow,
    plus a soft ambient-occlusion pass around their bases."""
    hard = Image.new("L", (W, H), 0)
    for _, spr, x, y in objects:
        a = spr.getchannel("A")
        sw, sh = spr.size
        squash = a.resize((sw, max(1, int(sh * 0.62))), Image.NEAREST)
        hard.paste(255, (x + 4, y + int(sh * 0.45)), squash)
    soft = hard.filter(ImageFilter.GaussianBlur(3))
    hp, sp, px = hard.load(), soft.load(), img.load()
    tr, tg, tb = SHADOW_TINT
    for yy in range(H):
        for xx in range(W):
            k = 0.0
            if hp[xx, yy]:
                k = 1.0
            else:
                s = sp[xx, yy] / 255
                if s > 0.08 and _dith(xx, yy) < s * 1.6:
                    k = 0.5
            if k:
                r, g, b = px[xx, yy]
                f = 1 - (1 - 0) * 0
                px[xx, yy] = (int(r * (1 - k * (1 - tr))), int(g * (1 - k * (1 - tg))),
                              int(b * (1 - k * (1 - tb))))


# ================================================================ planning
def plan(weeks, seed=7):
    rng = random.Random(seed)
    n = len(weeks)
    cols = n + 2
    grid = {}
    kinds = {0: "grass", 1: "tall", 2: "bush", 3: "tree", 4: "tree2"}
    for c in range(cols):
        for r in range(GRID_TOP, GRID_TOP + 7):
            grid[(c, r)] = "tree" if c in (0, cols - 1) else "grass"
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            grid[(wi + 1, GRID_TOP + di)] = kinds[day[1]] if day else "grass"

    # one house per month on its busiest day
    best = {}
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            if day and day[0] > 0:
                m = (wi * 7 + di) // 30
                if m not in best or day[0] > best[m][0]:
                    best[m] = (day[0], (wi + 1, GRID_TOP + di))
    for _, cell in best.values():
        grid[cell] = "house"

    # quiet stretches sometimes become ponds
    ponds, used = [], set()
    for wi in range(n - 1):
        for di in range(6):
            for bw, bh in ((4, 3), (3, 3), (3, 2), (2, 3), (2, 2)):
                block = [(wi + 1 + a, GRID_TOP + di + b) for a in range(bw) for b in range(bh)]
                if all(grid.get(p) == "grass" for p in block) and not any(
                        (bx + dx, by + dy) in used for bx, by in block
                        for dx in (-2, -1, 0, 1, 2) for dy in (-1, 0, 1)):
                    if rng.random() < 0.25:
                        ponds.append((wi + 1, GRID_TOP + di, bw, bh))
                        used.update(block)
                    break
    for p in used:
        grid[p] = "pond"

    open_cells = [p for p, k in grid.items() if k == "grass"]
    rng.shuffle(open_cells)
    return grid, ponds, open_cells


class World:
    def __init__(self, weeks, langs, seed=7):
        self.weeks, self.langs = weeks, langs
        self.cols = len(weeks) + 2
        self.W, self.H = self.cols * T, ROWS * T
        self.grid, self.ponds, open_cells = plan(weeks, seed)
        rng = random.Random(seed + 1)

        # --- trees as points, packed into forests
        trees = []
        def add(px, py, pool):
            trees.append((py, px, rng.choice(pool)))
        for k in range(-1, self.W // 11 + 2):              # top forest, two staggered rows
            add(k * 11 + 3, 2, TREES_BACK)
            add(k * 11 + 8, 12, TREES_BACK)
            add(k * 11 + 3, 22, TREES)
        for k in range(-1, self.W // 11 + 2):              # bottom forest
            add(k * 11 + 6, ROAD_ROW * T + 29, TREES)
            add(k * 11 + 1, ROAD_ROW * T + 39, TREES_BACK)
        g = self.grid
        is_tree = lambda c, r: g.get((c, r)) in ("tree", "tree2")
        for (c, r), kind in g.items():
            if kind not in ("tree", "tree2"):
                continue
            pool = TREES_DARK if kind == "tree2" else TREES
            cx, cy = c * T + 8, r * T + 9
            add(cx, cy, pool)
            if is_tree(c + 1, r):
                add(cx + 8, cy + 1, pool)
            if is_tree(c, r + 1):
                add(cx + 1, cy + 8, pool)
            if is_tree(c + 1, r + 1) and is_tree(c + 1, r) and is_tree(c, r + 1):
                add(cx + 8, cy + 8, pool)
        self.trees = trees

        # --- creatures: your languages + wild ones, plus swimmers in ponds
        self.critters = []
        spots = sorted(open_cells, key=lambda p: (p[0] * 7919) % 101)
        for k, (c, r) in enumerate(spots[:max(14, len(spots) // 5)]):
            if k < len(langs) * 2:
                lang = langs[k % len(langs)]
                kind, color = lang["name"], lang["color"]
            else:
                kind = "wild:" + rng.choice(WILD_KINDS)
                color = rng.choice(WILD_COLORS)
            self.critters.append((c * T + rng.randint(-2, 2), r * T + rng.randint(-3, 1),
                                  kind, color, rng.randint(0, 7)))
        self.swimmers = []
        for (pc, pr, bw, bh) in self.ponds:
            if bw * bh >= 6:
                self.swimmers.append((pc * T + bw * T // 2 - 8, pr * T + bh * T // 2 - 6,
                                      rng.choice(["moon", "blob", "bird"]),
                                      rng.choice(WILD_COLORS), rng.randint(0, 7)))

        # --- butterflies
        self.flies = [(rng.uniform(40, self.W - 40), rng.uniform(GRID_TOP * T + 8, 8 * T),
                       rng.uniform(0, 6.28), rng.choice([C["fl_w"], C["fl_y"], C["fl_p"]]))
                      for _ in range(7)]

        self._ground = {}

    # ---------------------------------------------------------------- layers
    def _ground_for(self, phase):
        if phase in self._ground:
            return self._ground[phase]
        img = Image.new("RGB", (self.W, self.H), C["grass"])
        _grass_field(img)
        d = ImageDraw.Draw(img)
        for c in range(self.cols):
            for r in range(ROWS):
                rng = random.Random(c * 131 + r * 17)
                if self.grid.get((c, r)) == "tall":
                    _tall_grass_tile(d, c * T, r * T, phase + c)
                else:
                    _grass_tile(d, c * T, r * T, rng)
        _cliff(img, 0, self.W - 1, CLIFF_ROW * T)
        _road(img, 0, self.W - 1, ROAD_ROW * T, random.Random(9))
        _stairs(d, 3 * T, CLIFF_ROW * T)
        for k, (pc, pr, bw, bh) in enumerate(self.ponds):
            _pond(img, pc * T, pr * T, bw * T, bh * T, phase, k + 3)
        _apply_shadows(img, self.objects(), self.W, self.H)
        self._ground[phase] = img
        return img

    def objects(self):
        """Static objects as (depth_key, sprite, x, y)."""
        objs = []
        for py, px, spr in self.trees:
            objs.append((py + 12, spr, px - 13, py - 13))
        for (c, r), kind in self.grid.items():
            x, y = c * T, r * T
            if kind == "bush":
                objs.append((y + 15, BUSHES[(c + r) % 3], x, y + 3))
            elif kind == "house":
                objs.append((y + 16, HOUSES[(c * 7 + r) % 3], x - 5, y - 7))
        return sorted(objs, key=lambda o: o[0])

    def static_layers(self, rows):
        """Base picture (ground + every object) and, for each creature row,
        a thin transparent strip of the objects that should sit in front of it."""
        base = self._ground_for(0).copy()
        objs = self.objects()
        for _, spr, x, y in objs:
            base.paste(spr, (x, y), spr)
        fronts = {}
        for r in rows:
            foot = r * T + 14
            layer = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
            for key, spr, x, y in objs:
                if key > foot:
                    layer.alpha_composite(spr, (x, y)) if x >= 0 and y >= 0 else \
                        layer.paste(spr, (x, y), spr)
            y0, y1 = r * T - 6, r * T + 16
            fronts[r] = (layer.crop((0, y0, self.W, y1)), y0)
        return base, fronts

    def frame(self, i):
        phase = (i // 3) % 4
        img = self._ground_for(phase).copy()

        # depth-sorted objects
        objs = [(k, "img", (spr, x, y)) for k, spr, x, y in self.objects()]
        for k, (x, y, kind, color, ph) in enumerate(self.critters):
            hop = 1 if ((i + ph * 3) // 4) % 2 else 0
            objs.append((y + 14, "crit", (x, y - hop, kind, color)))
        objs.sort(key=lambda o: o[0])

        for _, typ, a in objs:
            if typ == "img":
                spr, x, y = a
                img.paste(spr, (x, y), spr)
            else:
                x, y, kind, color = a
                ImageDraw.Draw(img).ellipse([x + 3, y + 12, x + 12, y + 15], fill=C["grass_dd"])
                _creature(img, x, y, kind, color)

        # swimmers: only the top half shows, with a ripple ring
        d = ImageDraw.Draw(img)
        for x, y, kind, color, ph in self.swimmers:
            bob = 1 if ((i + ph) // 5) % 2 else 0
            tmp = Image.new("RGB", (16, 16), C["water"][2])
            _creature(tmp, 0, 0, "wild:" + kind, color)
            img.paste(tmp.crop((0, 2, 16, 10)), (x, y + 2 + bob))
            r = 8 + (i // 3) % 3
            d.ellipse([x + 8 - r, y + 9, x + 8 + r, y + 13], outline=C["water"][4])

        # butterflies
        for bx, by, ph, col in self.flies:
            t = i * 0.12 + ph
            x = int(bx + math.sin(t) * 22)
            y = int(by + math.sin(t * 1.7) * 7)
            if (i // 2) % 2:
                d.point([(x - 1, y), (x + 1, y), (x, y + 1)], fill=col)
            else:
                d.point([(x - 1, y - 1), (x + 1, y - 1), (x - 1, y), (x + 1, y), (x, y + 1)],
                        fill=col)
            d.point([(x, y)], fill=C["out"])
        return img


def _creature(img, x, y, kind, color):
    name = kind[5:] if kind.startswith("wild:") else kind
    draw_creature(img, x, y, name, color, template=kind.startswith("wild:"))
