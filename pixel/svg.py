"""Animated SVG version of the town.

The pixel art is embedded as crisp, pre-scaled PNGs; everything that moves is
animated with SMIL/CSS, which GitHub renders inside a README <img>.
No JavaScript, no external files.
"""
import base64, io, math, random
from PIL import Image, ImageEnhance
from .art import hx, TRAINER, TRAINER_PAL, WHITE, draw_text, text_width, rounded_box
from .world import World, T, ROAD_ROW, GRID_TOP, C, _creature

EMBED = 4          # pixel art is stored at 4x so it stays sharp on any screen
DAY = 30           # seconds for a full day/night cycle
SCENE = 12         # seconds for the trainer + text box sequence


def _png(img, scale=EMBED):
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _image(href_id, x, y, w, h, extra=""):
    return f'<use xlink:href="#{href_id}" x="{x}" y="{y}" {extra}/>'


def _hex(c):
    return "#%02x%02x%02x" % c


def render_svg(data, out_path):
    weeks, langs = data["weeks"], data["languages"]
    world = World(weeks, langs)
    W, MAP_H = world.W, world.H
    BOX = 68
    H = MAP_H + 4 + BOX
    rng = random.Random(11)
    defs, body = [], []

    # ------------------------------------------------------------ creatures
    def critter_sprite(kind, color, top_only=False):
        s = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        _creature(s, 0, 0, kind, color)
        return s.crop((0, 2, 16, 10)) if top_only else s

    sprite_ids = {}
    def sprite_id(kind, color, top_only=False):
        key = (kind, color, top_only)
        if key not in sprite_ids:
            sid = f"c{len(sprite_ids)}"
            spr = critter_sprite(kind, color, top_only)
            defs.append(f'<image id="{sid}" width="16" height="{spr.height}" '
                        f'xlink:href="{_png(spr)}"/>')
            sprite_ids[key] = sid
        return sprite_ids[key]

    open_kinds = ("grass", "tall")
    crit_rows = sorted({(y + 4) // T for _, y, *_ in world.critters})
    base, fronts = world.static_layers(crit_rows)
    pop = lambda im: ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(1.22)).enhance(1.06)
    base = pop(base)
    fronts = {r: (pop(im), y0) for r, (im, y0) in fronts.items()}

    # ------------------------------------------------------------ static map
    defs.append(f'<image id="base" width="{W}" height="{MAP_H}" xlink:href="{_png(base)}"/>')
    body.append(_image("base", 0, 0, W, MAP_H))

    # cloud shadows drift across the whole map
    body.append('<g filter="url(#soft)" fill="#0b3a24" opacity=".13">')
    for k in range(3):
        cy, dur = 40 + k * 45, 55 + k * 14
        body.append(
            f'<ellipse cx="0" cy="{cy}" rx="{70 + k * 18}" ry="{22 + k * 5}">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="-160 0" to="{W + 160} 0" dur="{dur}s" begin="-{k * 19}s" '
            f'repeatCount="indefinite"/></ellipse>')
    body.append('</g>')

    # pond ripples, sparkles and swimmers
    for k, (pc, pr, bw, bh) in enumerate(world.ponds):
        px, py, pw, ph = pc * T, pr * T, bw * T, bh * T
        for s in range(max(2, bw * bh // 3)):
            sx = px + 7 + rng.random() * (pw - 14)
            sy = py + 9 + rng.random() * (ph - 15)
            b = rng.random() * 3
            body.append(
                f'<path d="M{sx:.0f} {sy - 1:.0f}h1v1h1v1h-1v1h-1v-1h-1v-1h1z" fill="#eef9ff" '
                f'opacity="0"><animate attributeName="opacity" values="0;1;0;0" '
                f'keyTimes="0;.15;.3;1" dur="3s" begin="{b:.1f}s" repeatCount="indefinite"/>'
                f'</path>')
    for x, y, kind, color, ph in world.swimmers:
        sid = sprite_id("wild:" + kind, color, top_only=True)
        b = rng.random() * 2
        body.append(
            f'<ellipse cx="{x + 8}" cy="{y + 10}" rx="6" ry="2" fill="none" '
            f'stroke="#a8dcf8" stroke-width=".8">'
            f'<animate attributeName="rx" values="5;13" dur="2.4s" begin="{b:.1f}s" '
            f'repeatCount="indefinite"/>'
            f'<animate attributeName="ry" values="1.5;4" dur="2.4s" begin="{b:.1f}s" '
            f'repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values=".9;0" dur="2.4s" begin="{b:.1f}s" '
            f'repeatCount="indefinite"/></ellipse>')
        body.append(
            f'<g><animateTransform attributeName="transform" type="translate" '
            f'values="0 0;0 1;0 0" dur="1.8s" begin="{b:.1f}s" repeatCount="indefinite"/>'
            + _image(sid, x, y + 2, 16, 8) + '</g>')

    # ------------------------------------------------------------ walking creatures
    by_row = {}
    for x, y, kind, color, ph in world.critters:
        by_row.setdefault((y + 4) // T, []).append((x, y, kind, color))

    def run(c, r):
        lo = hi = c
        while lo - 1 >= 1 and world.grid.get((lo - 1, r)) in open_kinds and c - lo < 3:
            lo -= 1
        while world.grid.get((hi + 1, r)) in open_kinds and hi - c < 3:
            hi += 1
        return lo * T, hi * T

    for r in crit_rows:
        for x, y, kind, color in by_row.get(r, []):
            sid = sprite_id(kind, color)
            lo, hi = run(x // T, r)
            dur = rng.uniform(9, 17)
            b = rng.uniform(0, dur)
            if hi - lo >= T:
                a, z = max(lo, x - 2 * T), min(hi, x + 2 * T)
                xs = [x, z, z, a, a, x]
                kt = "0;.25;.4;.75;.88;1"
            else:
                xs, kt = [x, x + 3, x + 3, x - 2, x], "0;.3;.5;.8;1"
            vals = ";".join(f"{v - x} 0" for v in xs)
            hop = rng.uniform(.45, .7)
            body.append(
                f'<g><animateTransform attributeName="transform" type="translate" '
                f'values="{vals}" keyTimes="{kt}" dur="{dur:.1f}s" begin="-{b:.1f}s" '
                f'calcMode="spline" keySplines="{";".join([".45 0 .55 1"] * (len(xs) - 1))}" '
                f'repeatCount="indefinite"/>'
                f'<ellipse cx="{x + 8}" cy="{y + 14}" rx="5" ry="1.8" fill="#0a3a26" opacity=".32"/>'
                f'<g><animateTransform attributeName="transform" type="translate" '
                f'values="0 0;0 -1.5;0 0" dur="{hop:.2f}s" repeatCount="indefinite"/>'
                + _image(sid, x, y, 16, 16) + '</g></g>')
        if r in fronts:
            strip, y0 = fronts[r]
            fid = f"f{r}"
            defs.append(f'<image id="{fid}" width="{W}" height="{strip.height}" '
                        f'xlink:href="{_png(strip)}"/>')
            body.append(_image(fid, 0, y0, W, strip.height))

    # falling leaves from the top forest
    for k in range(6):
        lx = rng.uniform(30, W - 30)
        dur = rng.uniform(7, 11)
        col = rng.choice(["#4caf62", "#78c870", "#e0a040"])
        path = (f"M{lx:.0f} 18 q 14 20 -4 40 q -16 22 6 46 q 10 18 -2 30")
        body.append(
            f'<rect x="-1.5" y="-1" width="3" height="2" fill="{col}" opacity="0">'
            f'<animateMotion path="{path}" dur="{dur:.1f}s" begin="-{k * 1.7:.1f}s" '
            f'rotate="auto" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.1;.8;1" '
            f'dur="{dur:.1f}s" begin="-{k * 1.7:.1f}s" repeatCount="indefinite"/></rect>')

    # butterflies
    for k in range(8):
        cx, cy = rng.uniform(40, W - 40), rng.uniform(GRID_TOP * T + 6, 8 * T)
        dx, dy = rng.uniform(25, 60), rng.uniform(8, 18)
        path = (f"M{cx:.0f} {cy:.0f} c {dx:.0f} {-dy:.0f} {dx * 1.6:.0f} {dy:.0f} "
                f"{dx:.0f} {dy * 1.4:.0f} s {-dx * 1.8:.0f} {dy * .5:.0f} {-dx:.0f} "
                f"{-dy * 1.4:.0f}")
        col = rng.choice(["#ffffff", "#f8e060", "#f0a0e0", "#a8d8ff"])
        dur = rng.uniform(8, 14)
        body.append(
            f'<g><animateMotion path="{path}" dur="{dur:.1f}s" begin="-{k * 1.3:.1f}s" '
            f'repeatCount="indefinite"/>'
            f'<rect x="-2" y="-1.5" width="4" height="2" fill="{col}">'
            f'<animate attributeName="height" values="2;.6;2" dur=".28s" '
            f'repeatCount="indefinite"/></rect>'
            f'<rect x="-.5" y="-1.5" width="1" height="3" fill="#2a3040"/></g>')

    # ------------------------------------------------------------ trainer
    road_y = ROAD_ROW * T
    today_x = (data["today_week"] + 1) * T
    start_x = max(T, today_x - 12 * T)
    walk_end = 0.42                                           # fraction of SCENE
    for f in range(2):
        spr = Image.new("RGBA", (8, 13), (0, 0, 0, 0))
        for j, row in enumerate(TRAINER[f]):
            for i, ch in enumerate(row):
                if ch != ".":
                    spr.putpixel((i, j + 1 - f), TRAINER_PAL[ch] + (255,))
        defs.append(f'<image id="tr{f}" width="16" height="26" xlink:href="{_png(spr, EMBED * 2)}"/>')
    steps = 24
    kts = [round(walk_end * k / steps, 4) for k in range(steps + 1)] + [1]
    vis0 = ";".join("1" if k % 2 == 0 or k == steps else "0" for k in range(steps + 1)) + ";1"
    vis1 = ";".join("0" if k % 2 == 0 or k == steps else "1" for k in range(steps + 1)) + ";0"
    kt = ";".join(str(k) for k in kts)
    body.append(
        f'<g><animateTransform attributeName="transform" type="translate" '
        f'values="{start_x} 0;{today_x} 0;{today_x} 0" keyTimes="0;{walk_end};1" '
        f'dur="{SCENE}s" repeatCount="indefinite"/>'
        f'<ellipse cx="8" cy="{road_y + 13}" rx="6" ry="2" fill="#9a6a48"/>'
        + f'<use xlink:href="#tr0" x="0" y="{road_y - 12}" opacity="1">'
        f'<animate attributeName="opacity" values="{vis0}" keyTimes="{kt}" '
        f'calcMode="discrete" dur="{SCENE}s" repeatCount="indefinite"/></use>'
        f'<use xlink:href="#tr1" x="0" y="{road_y - 12}" opacity="0">'
        f'<animate attributeName="opacity" values="{vis1}" keyTimes="{kt}" '
        f'calcMode="discrete" dur="{SCENE}s" repeatCount="indefinite"/></use>'
        + '</g>')

    # ------------------------------------------------------------ lighting
    body.append(
        f'<rect width="{W}" height="{MAP_H}" fill="url(#sun)" style="mix-blend-mode:soft-light"/>')
    body.append('<g style="mix-blend-mode:screen" opacity=".5">')
    for k in range(5):                                         # light shafts
        x0 = 60 + k * W / 5 + rng.uniform(-30, 30)
        wdt = rng.uniform(26, 50)
        dur = rng.uniform(6, 10)
        body.append(
            f'<path d="M{x0:.0f} -10h{wdt:.0f}l-120 {MAP_H + 20}h-{wdt:.0f}z" fill="url(#ray)" '
            f'opacity=".3"><animate attributeName="opacity" values=".08;.4;.08" '
            f'dur="{dur:.1f}s" begin="-{rng.uniform(0, dur):.1f}s" repeatCount="indefinite"/>'
            f'</path>')
    body.append('</g>')
    body.append(
        f'<rect width="{W}" height="{MAP_H}" fill="url(#vig)" style="mix-blend-mode:multiply"/>')

    # ------------------------------------------------------------ day / night
    night_vals = "0;0;.18;.62;.62;.2;0"
    night_kt = "0;.38;.48;.58;.84;.94;1"
    body.append(
        f'<rect width="{W}" height="{MAP_H}" fill="#ffa868" opacity="0" '
        f'style="mix-blend-mode:multiply"><animate attributeName="opacity" '
        f'values="0;0;.48;.12;0;.22;0" keyTimes="0;.34;.45;.55;.86;.92;1" dur="{DAY}s" '
        f'repeatCount="indefinite"/></rect>')
    body.append(
        f'<rect width="{W}" height="{MAP_H}" fill="#2a3478" opacity="0" '
        f'style="mix-blend-mode:multiply"><animate attributeName="opacity" '
        f'values="{night_vals}" keyTimes="{night_kt}" dur="{DAY}s" '
        f'repeatCount="indefinite"/></rect>')

    glow_anim = (f'<animate attributeName="opacity" values="0;0;.6;1;1;.4;0" '
                 f'keyTimes="{night_kt}" dur="{DAY}s" repeatCount="indefinite"/>')
    body.append(f'<g opacity="0" filter="url(#glow)">{glow_anim}')
    for (c, r), kind in world.grid.items():                 # lit windows
        if kind == "house":
            hx0, hy0 = c * T - 5, r * T - 7
            for wx in (6, 17):
                body.append(f'<rect x="{hx0 + wx}" y="{hy0 + 15}" width="2" height="3" '
                            f'fill="#ffd860"/>')
    for k in range(16):                                      # fireflies
        cx, cy = rng.uniform(20, W - 20), rng.uniform(GRID_TOP * T, 9 * T)
        path = (f"M{cx:.0f} {cy:.0f} c 10 -8 22 4 14 12 s -18 6 -20 -4 s 6 -14 6 -8")
        dur = rng.uniform(5, 9)
        body.append(
            f'<circle r="1" fill="#f6ff8a"><animateMotion path="{path}" dur="{dur:.1f}s" '
            f'begin="-{rng.uniform(0, dur):.1f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="1;.15;1" dur="{rng.uniform(1, 2):.1f}s" '
            f'repeatCount="indefinite"/></circle>')
    body.append('</g>')

    # ------------------------------------------------------------ text box
    half_w = W // 2
    box = Image.new("RGBA", (half_w, BOX // 2), (0, 0, 0, 0))
    rounded_box(box, 1, 0, half_w - 2, BOX // 2, WHITE, hx("3a7090"), inner=hx("88c0d0"))
    defs.append(f'<image id="box" width="{W}" height="{BOX}" xlink:href="{_png(box, EMBED * 2)}"/>')
    body.append(_image("box", 0, MAP_H + 4, W, BOX))

    line1, line2 = data["msg1"], data["msg2"]
    t0, t1 = walk_end + 0.03, 0.80                            # typing window
    n = len(line1) + len(line2)
    for li, (line, offset) in enumerate(((line1, 0), (line2, len(line1)))):
        txt = Image.new("RGBA", (half_w, 9), (0, 0, 0, 0))
        draw_text(txt, 9, 0, line)
        lid = f"l{li}"
        defs.append(f'<image id="{lid}" width="{W}" height="18" xlink:href="{_png(txt, EMBED * 2)}"/>')
        widths = [0] + [2 * (9 + text_width(line[:k]) + 1) for k in range(1, len(line) + 1)]
        times = [t0 + (t1 - t0) * (offset + k) / n for k in range(len(line) + 1)]
        vals = "0;" + ";".join(str(v) for v in widths) + ";0"
        kt = "0;" + ";".join(f"{t:.4f}" for t in times) + ";1"
        cy = MAP_H + 4 + 16 + li * 22
        defs.append(
            f'<clipPath id="cl{li}"><rect x="0" y="{cy - 2}" width="0" height="22">'
            f'<animate attributeName="width" values="{vals}" keyTimes="{kt}" '
            f'calcMode="discrete" dur="{SCENE}s" repeatCount="indefinite"/></rect></clipPath>')
        body.append(f'<g clip-path="url(#cl{li})">' + _image(lid, 0, cy, W, 18) + '</g>')
    ax, ay = W - 30, MAP_H + 4 + 42
    body.append(
        f'<path d="M{ax} {ay}h8l-4 5z" fill="#e04040" opacity="0">'
        f'<animate attributeName="opacity" values="0;0;1;0;1;0;1;0" '
        f'keyTimes="0;{t1};{t1 + .03};{t1 + .07};{t1 + .11};{t1 + .15};{t1 + .19};1" '
        f'calcMode="discrete" dur="{SCENE}s" repeatCount="indefinite"/></path>')

    # ------------------------------------------------------------ location sign
    sw = text_width(data["title"]) + 14
    sign = Image.new("RGBA", (sw, 13), (0, 0, 0, 0))
    rounded_box(sign, 0, 0, sw, 13, hx("e8c890"), hx("5a3818"), inner=hx("a87040"))
    draw_text(sign, 7, 3, data["title"], color=hx("4a2810"), shadow=hx("f8e0b0"))
    defs.append(f'<image id="sign" width="{sw * 2}" height="26" xlink:href="{_png(sign, EMBED * 2)}"/>')
    body.append(_image("sign", 6, 6, sw * 2, 26))

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" '
        f'height="{H}" shape-rendering="crispEdges">'
        f'<style>image{{image-rendering:pixelated;image-rendering:crisp-edges}}</style>'
        f'<defs>'
        f'<filter id="soft" x="-50%" y="-50%" width="200%" height="200%">'
        f'<feGaussianBlur stdDeviation="9"/></filter>'
        f'<radialGradient id="sun" cx=".08" cy="-.1" r="1.1">'
        f'<stop offset="0" stop-color="#fff2b0"/><stop offset=".45" stop-color="#ffe9a0" stop-opacity=".55"/>'
        f'<stop offset="1" stop-color="#2a8ad0" stop-opacity=".12"/></radialGradient>'
        f'<linearGradient id="ray" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#fff6c8"/><stop offset="1" stop-color="#fff6c8" stop-opacity="0"/>'
        f'</linearGradient>'
        f'<radialGradient id="vig" cx=".5" cy=".5" r=".75">'
        f'<stop offset=".62" stop-color="#fff"/><stop offset="1" stop-color="#9aa8c8"/></radialGradient>'
        f'<filter id="glow" x="-200%" y="-200%" width="500%" height="500%">'
        f'<feGaussianBlur stdDeviation="1.6" result="b"/><feMerge><feMergeNode in="b"/>'
        f'<feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        + "".join(defs) + '</defs>'
        f'<rect width="{W}" height="{H}" fill="#1c2430"/>'
        + "".join(body) + '</svg>')
    with open(out_path, "w") as fh:
        fh.write(svg)
