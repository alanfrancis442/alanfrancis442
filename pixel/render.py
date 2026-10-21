"""Render the overworld map GIF and the party screen GIF."""
from PIL import Image, ImageDraw
from .art import (WHITE, hx, TRAINER, TRAINER_PAL, draw_creature, draw_text,
                  text_width, rounded_box, down_arrow)
from .world import World, T as WT, ROAD_ROW

SCALE = 2
T = 8  # tile size


def _save_gif(frames, durations, path, scale=SCALE):
    if scale != 1:
        frames = [f.resize((f.width * scale, f.height * scale), Image.NEAREST) for f in frames]
    # one shared palette for every frame, so colours never flicker between frames
    master = frames[0].quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE)
    pal = [f.quantize(palette=master, dither=Image.NONE) for f in frames]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=durations,
                loop=0, optimize=True, disposal=1)


def _x2(img):
    return img.resize((img.width * 2, img.height * 2), Image.NEAREST)


def _trainer_sprite(frame):
    s = Image.new("RGBA", (8, 13), (0, 0, 0, 0))
    rows = TRAINER[frame % 4]
    for j, row in enumerate(rows):
        for i, c in enumerate(row):
            if c != ".":
                s.putpixel((i, j + 1 - (frame % 2)), TRAINER_PAL[c] + (255,))
    return _x2(s)


# ================================================================ overworld
def render_map(data, path):
    weeks = data["weeks"]
    world = World(weeks, data["languages"])
    W, MAP_H = world.W, world.H
    BOX_H = 34                                  # half-res units, drawn at 2x
    H = MAP_H + 4 + BOX_H * 2
    sign = _x2(_location_sign(data["title"]))

    today_x = (data["today_week"] + 1) * WT
    start_x = max(WT, today_x - 12 * WT)
    walk = (today_x - start_x) // 4
    line1, line2 = data["msg1"], data["msg2"]
    total = len(line1) + len(line2)
    typing, hold = (total + 1) // 2, 30
    road_y = ROAD_ROW * WT

    frames, durs = [], []
    for i in range(walk + typing + hold):
        img = Image.new("RGB", (W, H), hx("1c2430"))
        img.paste(world.frame(i), (0, 0))
        img.paste(sign, (6, 6))
        walking = i < walk
        tx = start_x + i * 4 if walking else today_x
        tr = _trainer_sprite(i // 2 if walking else 0)
        ImageDraw.Draw(img).ellipse([tx + 2, road_y + 11, tx + 13, road_y + 15],
                                    fill=hx("9a6a48"))
        img.paste(tr, (tx, road_y + 14 - tr.height), tr)

        box = Image.new("RGB", (W // 2, BOX_H), hx("1c2430"))
        rounded_box(box, 1, 0, W // 2 - 2, BOX_H, WHITE, hx("3a7090"), inner=hx("88c0d0"))
        shown = 0 if walking else min(total, (i - walk) * 2)
        draw_text(box, 9, 8, line1[:shown])
        draw_text(box, 9, 19, line2[:max(0, shown - len(line1))])
        if shown >= total and (i // 4) % 2 == 0:
            down_arrow(box, W // 2 - 16, 22)
        img.paste(_x2(box), (0, MAP_H + 4))
        frames.append(img)
        durs.append(80)
    durs[-1] = 1400
    _save_gif(frames, durs, path, scale=1)


def _location_sign(title):
    w = text_width(title) + 14
    s = Image.new("RGB", (w, 13))
    rounded_box(s, 0, 0, w, 13, hx("e8c890"), hx("5a3818"), inner=hx("a87040"))
    draw_text(s, 7, 3, title, color=hx("4a2810"), shadow=hx("f8e0b0"))
    return s


# ================================================================ party screen
def render_party(data, path):
    langs = data["languages"][:5]
    W = (len(data["weeks"]) + 2) * T          # same width as the map
    slot_h, gap, top = 24, 3, 26
    H = top + len(langs) * (slot_h + gap) + 26

    def bg():
        img = Image.new("RGB", (W, H), hx("50a8b8"))
        d = ImageDraw.Draw(img)
        for k in range(-H, W, 8):              # diagonal stripes
            d.line([k, 0, k + H, H], fill=hx("60b8c8"), width=3)
        return img

    base = bg()
    title = data["party_title"]
    rounded_box(base, 6, 5, text_width(title) + 16, 16, WHITE, hx("404048"), inner=hx("c8c8d0"))
    draw_text(base, 14, 9, title)

    fill_frames, hold = 16, 30
    frames, durs = [], []
    for i in range(fill_frames + hold):
        img = base.copy()
        d = ImageDraw.Draw(img)
        grow = min(1.0, (i + 1) / fill_frames)
        for s, lang in enumerate(langs):
            x, y = 6, top + s * (slot_h + gap)
            selected = s == 0
            border = hx("f89838") if selected else hx("183858")
            rounded_box(img, x, y, W - 12, slot_h, hx("3070b8"), border, inner=hx("78b0e8"))
            # icon bobs like a party icon (selected one bobs faster)
            speed = 3 if selected else 6
            bob = (i // speed) % 2
            draw_creature(img, x + 5, y + 4 - bob, lang["name"], lang["color"])

            name = lang["name"].upper()
            if text_width(name) > 120:
                name = name.split()[0]
            draw_text(img, x + 26, y + 4, name, color=WHITE, shadow=hx("183050"))
            draw_text(img, x + 26, y + 14, f"LV{max(1, round(lang['percent']))}",
                      color=hx("f8f0a8"), shadow=hx("183050"))

            # HP bar
            bx, bw = W - 164, 146
            rounded_box(img, bx - 18, y + 4, 17, 11, hx("f8a030"), hx("383838"))
            draw_text(img, bx - 14, y + 6, "HP", color=hx("383838"), shadow=None)
            d.rectangle([bx - 1, y + 6, bx + bw, y + 12], fill=hx("383838"))
            d.rectangle([bx, y + 7, bx + bw - 1, y + 11], fill=hx("506070"))
            frac = lang["percent"] / 100 * grow
            col = hx("58d080") if frac > 0.5 else hx("f8c030") if frac > 0.2 else hx("f05838")
            fw = max(1, round(bw * frac))
            d.rectangle([bx, y + 7, bx + fw - 1, y + 11], fill=col)
            d.line([bx, y + 7, bx + fw - 1, y + 7], fill=tuple(min(255, c + 60) for c in col))
            pct = f"{lang['percent'] * grow:.2f}%"
            draw_text(img, bx + bw - text_width(pct), y + 15, pct, color=WHITE,
                      shadow=hx("183050"))

        by = H - 22
        rounded_box(img, 6, by, W - 12, 18, WHITE, hx("404048"), inner=hx("c8c8d0"))
        draw_text(img, 14, by + 6, data["party_msg"])
        frames.append(img)
        durs.append(60 if i < fill_frames else 110)
    durs[-1] = 1500
    _save_gif(frames, durs, path)
