"""Animated SVG party screen: your top languages as a GBA-style party.

Static pixel art is drawn at half resolution and embedded as a crisp PNG;
HP bars, creatures, sparkles, glow, shine and the text box are animated
with SMIL. Everything is self-contained, so it renders in a README <img>.
"""
import random
from PIL import Image, ImageDraw
from .art import hx, WHITE, draw_text, text_width, rounded_box, draw_creature
from .svg import _png, EMBED

S = 2                                    # half-res unit -> SVG px
CODES = {"TypeScript": "TS", "JavaScript": "JS", "Python": "PY", "HTML": "HTML",
         "CSS": "CSS", "Jupyter Notebook": "NB", "Shell": "SH", "GLSL": "GLSL",
         "C++": "CPP", "Rust": "RS", "Go": "GO", "Java": "JAVA", "Dockerfile": "DOCK"}
INK = hx("142850")


def _code(name):
    return CODES.get(name, "".join(ch for ch in name.upper() if ch.isalnum())[:3])


def _hp_colors(pct):
    if pct > 50:
        return "#3ee070", "#b4ffc4"
    if pct > 20:
        return "#ffcf2e", "#fff3a0"
    return "#ff5a36", "#ffb8a0"


def _lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def _panel(img, x, y, w, h, selected):
    """Glossy GBA party panel."""
    border = hx("ff9a2a") if selected else hx("10285e")
    inner = hx("9ad8ff") if selected else hx("6aa6f2")
    fill = hx("2f86ec") if selected else hx("2a60c4")
    rounded_box(img, x, y, w, h, fill, border, inner=inner)
    d = ImageDraw.Draw(img)
    gloss = hx("4a9cf6") if selected else hx("3a74d6")
    d.rectangle([x + 3, y + 3, x + w - 4, y + (h - 6) * 2 // 5 + 3], fill=gloss)
    d.line([x + 4, y + 3, x + w - 5, y + 3], fill=hx("8ccaff") if selected else hx("6aa0ec"))
    if selected:                                         # double border like the games
        d.rectangle([x + 1, y + 1, x + w - 2, y + 1], fill=hx("ffd070"))


def _hp_frame(img, x, y, w):
    d = ImageDraw.Draw(img)
    rounded_box(img, x - 19, y - 2, 18, 11, hx("ffa63a"), hx("2a2a2a"))
    draw_text(img, x - 15, y, "HP", color=hx("2a2a2a"), shadow=hx("ffd890"))
    d.rectangle([x - 1, y - 1, x + w, y + 7], fill=hx("2a2a2a"))
    d.rectangle([x, y, x + w - 1, y + 6], fill=hx("44546a"))
    d.line([x, y + 6, x + w - 1, y + 6], fill=hx("33404f"))


def _badge(img, x, y, lang):
    col = hx(lang["color"] or "#9aa0a6")
    code = _code(lang["name"])
    w = text_width(code) + 7
    rounded_box(img, x, y, w, 11, col, hx("142030"))
    light = _lum(col) > 150
    draw_text(img, x + 4, y + 2, code, color=hx("1a1a1a") if light else WHITE,
              shadow=None if light else hx("1a1a2a"))
    return w


def render_party_svg(data, out_path):
    langs = data["languages"][:5]
    W = (len(data["weeks"]) + 2) * 16
    w2, h2 = W // S, 168
    rng = random.Random(4)
    static = Image.new("RGBA", (w2, h2), (0, 0, 0, 0))
    defs, body, anim = [], [], []

    # ------------------------------------------------------------ title tab
    title = data["party_title"]
    rounded_box(static, 6, 4, text_width(title) + 18, 15, WHITE, hx("2a2a3a"), inner=hx("c8c8d8"))
    draw_text(static, 15, 8, title)

    def bar_anim(x, y, w, pct, delay):
        """Animated HP fill + count-up percentage (all in half-res units)."""
        col, hi = _hp_colors(pct)
        fw = max(1, round(w * pct / 100))
        X, Y, FW = x * S, y * S, fw * S
        spl = 'calcMode="spline" keyTimes="0;1" keySplines=".15 .7 .3 1"'
        body.append(
            f'<rect x="{X}" y="{Y}" width="0" height="{6 * S}" fill="{col}">'
            f'<animate attributeName="width" values="0;{FW}" {spl} dur="1.4s" '
            f'begin="{delay:.2f}s" fill="freeze"/></rect>'
            f'<rect x="{X}" y="{Y}" width="0" height="{S}" fill="{hi}">'
            f'<animate attributeName="width" values="0;{FW}" {spl} dur="1.4s" '
            f'begin="{delay:.2f}s" fill="freeze"/></rect>'
            f'<rect x="{X}" y="{Y + 4 * S}" width="0" height="{S}" fill="#000" opacity=".18">'
            f'<animate attributeName="width" values="0;{FW}" {spl} dur="1.4s" '
            f'begin="{delay:.2f}s" fill="freeze"/></rect>')
        # count-up text: discrete swaps between pre-drawn numbers
        steps = 12
        for k in range(1, steps + 1):
            p = pct * (1 - (1 - k / steps) ** 2.2)
            txt = f"{p:.2f}%"
            im = Image.new("RGBA", (text_width(txt) + 2, 9), (0, 0, 0, 0))
            draw_text(im, 0, 0, txt, color=WHITE, shadow=INK)
            iid = f"p{len(defs)}"
            defs.append(f'<image id="{iid}" width="{im.width * S}" height="{im.height * S}" '
                        f'xlink:href="{_png(im, EMBED * S)}"/>')
            t0 = delay + 1.4 * (k - 1) / steps
            t1 = delay + 1.4 * k / steps
            end = "" if k == steps else f'<set attributeName="opacity" to="0" begin="{t1:.2f}s"/>'
            body.append(
                f'<use xlink:href="#{iid}" x="{(x + w - im.width + 2) * S}" y="{(y + 9) * S}" '
                f'opacity="0"><set attributeName="opacity" to="1" begin="{t0:.2f}s"/>{end}</use>')

    def creature(lang, x, y, scale, bob, speed, delay):
        spr = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        draw_creature(spr, 0, 0, lang["name"], lang["color"])
        cid = f"cr{len(defs)}"
        defs.append(f'<image id="{cid}" width="{16 * scale * S}" height="{16 * scale * S}" '
                    f'xlink:href="{_png(spr, EMBED * S * scale)}"/>')
        body.append(
            f'<g><animateTransform attributeName="transform" type="translate" '
            f'values="0 0;0 {-bob};0 0" dur="{speed}s" begin="{delay:.2f}s" '
            f'repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" '
            f'keySplines=".3 0 .7 1;.3 0 .7 1"/>'
            f'<use xlink:href="#{cid}" x="{x * S}" y="{y * S}"/></g>')

    # ------------------------------------------------------------ lead (selected) panel
    if langs:
        L = langs[0]
        px, py, pw, ph = 6, 24, 150, 88
        _panel(static, px, py, pw, ph, True)
        d = ImageDraw.Draw(static)
        d.ellipse([px + 8, py + 40, px + 50, py + 51], fill=hx("1e5cb8"))   # platform
        d.ellipse([px + 10, py + 40, px + 48, py + 48], fill=hx("5aa8f4"))
        d.ellipse([px + 14, py + 41, px + 44, py + 46], fill=hx("8cc8ff"))
        name = L["name"].upper()
        draw_text(static, px + 56, py + 12, name if text_width(name) < 88 else name.split()[0],
                  color=WHITE, shadow=INK)
        draw_text(static, px + 56, py + 24, f"LV{max(1, round(L['percent']))}",
                  color=hx("fff07a"), shadow=INK)
        _badge(static, px + 56 + text_width(f"LV{max(1, round(L['percent']))}") + 6,
               py + 22, L)
        bx, by, bw = px + 32, py + 64, pw - 42
        _hp_frame(static, bx, by, bw)
        # glow pulse + shine sweep on the lead panel
        X, Y, Wd, Hd = px * S, py * S, pw * S, ph * S
        defs.append(f'<clipPath id="leadclip"><rect x="{X + 6}" y="{Y + 6}" width="{Wd - 12}" '
                    f'height="{Hd - 12}" rx="6"/></clipPath>')
        anim.append(
            f'<rect x="{X}" y="{Y}" width="{Wd}" height="{Hd}" rx="8" fill="none" '
            f'stroke="#ffb040" stroke-width="5" filter="url(#glow)" opacity=".2">'
            f'<animate attributeName="opacity" values=".15;.85;.15" dur="1.6s" '
            f'repeatCount="indefinite"/></rect>')
        body_shine = (
            f'<g clip-path="url(#leadclip)"><path d="M0 0h26l-40 {Hd}h-26z" fill="url(#shine)" '
            f'transform="translate({X - 60} {Y})">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="{X - 60} {Y};{X + Wd + 60} {Y};{X + Wd + 60} {Y}" keyTimes="0;.28;1" '
            f'dur="4.5s" begin="2s" repeatCount="indefinite"/></path></g>')
        creature(L, px + 13, py + 13, 2, 4, .55, 0)
        for k, (sx, sy) in enumerate(((px + 10, py + 14), (px + 46, py + 8), (px + 50, py + 36))):
            b = k * .55
            anim.append(
                f'<path d="M0 -5L1.2 -1.2L5 0L1.2 1.2L0 5L-1.2 1.2L-5 0L-1.2 -1.2Z" '
                f'fill="#fffbd0" transform="translate({sx * S} {sy * S})">'
                f'<animateTransform attributeName="transform" type="scale" additive="sum" '
                f'values="0;1.1;0;0" keyTimes="0;.15;.3;1" dur="1.8s" begin="-{b:.2f}s" '
                f'repeatCount="indefinite"/></path>')
        bar_anim(bx, by, bw, L["percent"], 0.5)
        body.append(body_shine)

    # ------------------------------------------------------------ other slots
    sx, sw, sh, gap = 164, w2 - 170, 23, 4
    for i in range(4):
        sy = 8 + i * (sh + gap)
        if i + 1 >= len(langs):                              # empty slot, like the games
            d = ImageDraw.Draw(static)
            rounded_box(static, sx, sy, sw, sh, hx("2a8e9a"), hx("17606c"))
            continue
        lang = langs[i + 1]
        _panel(static, sx, sy, sw, sh, False)
        rounded_box(static, sx + 3, sy + 3, 19, 17, hx("a8d8ff"), hx("1a3c80"), inner=hx("d8f0ff"))
        name = lang["name"].upper()
        if text_width(name) > 76:
            name = name.split()[0]
        draw_text(static, sx + 24, sy + 4, name, color=WHITE, shadow=INK)
        lv = f"LV{max(1, round(lang['percent']))}"
        draw_text(static, sx + 24, sy + 13, lv, color=hx("fff07a"), shadow=INK)
        _badge(static, sx + 24 + text_width(lv) + 5, sy + 11, lang)
        bx, bw = sx + sw - 128, 120
        _hp_frame(static, bx, sy + 4, bw)
        creature(lang, sx + 4, sy + 3, 1, 2, .9 + i * .12, i * .2)
        bar_anim(bx, sy + 4, bw, lang["percent"], 0.75 + i * 0.18)

    # ------------------------------------------------------------ text box + cancel
    ty = h2 - 40
    rounded_box(static, 6, ty, w2 - 84, 34, WHITE, hx("2a2a3a"), inner=hx("c8c8d8"))
    rounded_box(static, w2 - 74, ty + 6, 68, 22, hx("2a60c4"), hx("10285e"), inner=hx("6aa6f2"))
    draw_text(static, w2 - 40 - text_width("CANCEL") // 2, ty + 13, "CANCEL", color=WHITE,
              shadow=INK)
    msg = data["party_msg"]
    tim = Image.new("RGBA", (text_width(msg) + 4, 9), (0, 0, 0, 0))
    draw_text(tim, 0, 0, msg)
    defs.append(f'<image id="msg" width="{tim.width * S}" height="{tim.height * S}" '
                f'xlink:href="{_png(tim, EMBED * S)}"/>')
    n, t0, cps = len(msg), 1.6, 0.045
    widths = [0] + [(text_width(msg[:k]) + 2) * S for k in range(1, n + 1)]
    kts = [k / n for k in range(n + 1)]
    defs.append(
        f'<clipPath id="typeclip"><rect x="{16 * S}" y="{(ty + 8) * S}" width="0" '
        f'height="{12 * S}"><animate attributeName="width" values="{";".join(map(str, widths))}" '
        f'keyTimes="{";".join(f"{k:.4f}" for k in kts)}" calcMode="discrete" '
        f'dur="{n * cps:.2f}s" begin="{t0}s" fill="freeze"/></rect></clipPath>')
    body.append(f'<g clip-path="url(#typeclip)"><use xlink:href="#msg" x="{16 * S}" '
                f'y="{(ty + 9) * S}"/></g>')
    done = t0 + n * cps
    ax, ay = (16 + text_width(msg) + 6) * S, (ty + 12) * S
    body.append(
        f'<path d="M{ax} {ay}h12l-6 7z" fill="#e83a3a" opacity="0">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" '
        f'calcMode="discrete" dur=".9s" begin="{done:.2f}s" repeatCount="indefinite"/></path>')

    # ------------------------------------------------------------ background
    H = h2 * S
    bg = [f'<rect width="{W}" height="{H}" fill="url(#sky)"/>',
          '<g opacity=".22"><g>'
          f'<animateTransform attributeName="transform" type="translate" values="0 0;-48 0" '
          f'dur="3s" repeatCount="indefinite"/>']
    for k in range(-2, W // 24 + H // 24 + 4):
        x0 = k * 24
        bg.append(f'<path d="M{x0} 0h12l-{H} {H}h-12z" fill="#ffffff"/>')
    bg.append('</g></g>')
    for k in range(18):                                       # rising bubbles
        x = rng.uniform(0, W)
        r = rng.uniform(2, 6)
        dur = rng.uniform(6, 12)
        bg.append(
            f'<circle cx="{x:.0f}" cy="{H + 10}" r="{r:.1f}" fill="#ffffff" opacity="{rng.uniform(.12, .3):.2f}">'
            f'<animate attributeName="cy" values="{H + 10};-10" dur="{dur:.1f}s" '
            f'begin="-{rng.uniform(0, dur):.1f}s" repeatCount="indefinite"/></circle>')

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
        f'<style>image{{image-rendering:pixelated;image-rendering:crisp-edges}}'
        f'rect,path{{shape-rendering:crispEdges}}</style>'
        f'<defs>'
        f'<linearGradient id="sky" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="#3fd6c8"/><stop offset=".55" stop-color="#2fb4d8"/>'
        f'<stop offset="1" stop-color="#3a86e0"/></linearGradient>'
        f'<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="#fff" stop-opacity=".55"/>'
        f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<filter id="glow" x="-20%" y="-20%" width="140%" height="140%">'
        f'<feGaussianBlur stdDeviation="4"/></filter>'
        f'<image id="static" width="{W}" height="{H}" xlink:href="{_png(static, EMBED)}"/>'
        + "".join(defs) + '</defs>'
        + "".join(bg) + "".join(anim[:1])
        + '<use xlink:href="#static"/>'
        + "".join(body) + "".join(anim[1:]) + '</svg>')
    with open(out_path, "w") as fh:
        fh.write(svg)
