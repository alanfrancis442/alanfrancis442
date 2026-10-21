"""Original GBA-style pixel art: palette, bitmap font, tiles, trainer, creatures.

Everything here is hand-made for this project — no game assets are used.
Art is drawn at native resolution and upscaled with nearest-neighbour later.
"""
from PIL import Image, ImageDraw

# ---------------------------------------------------------------- palette
def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

PAL = {
    "g": hx("88d070"), "d": hx("58a848"), "l": hx("b8e890"),            # grass
    "p": hx("e0c088"), "q": hx("c09858"), "r": hx("f0d8a8"),            # dirt road
    "t": hx("286838"), "T": hx("3c8c48"), "L": hx("68b858"), "k": hx("785030"),  # tree
    "a": hx("2c7830"), "b": hx("48a040"), "c": hx("80c860"),            # tall grass
    "f": hx("e85050"), "F": hx("f8f8f8"), "y": hx("f8d838"),            # flowers
    "w": hx("f8f0e0"), "W": hx("c8b8a0"), "D": hx("6a4020"), "n": hx("78b8e8"),  # house
    "o": hx("282830"),                                                  # outline
}
ROOFS = [(hx("d04838"), hx("983028")), (hx("3878c8"), hx("204890")), (hx("48a058"), hx("2c6838"))]

TEXT = hx("404048")
TEXT_SHADOW = hx("d0d0c8")
WHITE = hx("f8f8f8")

# ---------------------------------------------------------------- font 5x7
_G = {
 "A": [" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
 "B": ["#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "],
 "C": [" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"],
 "D": ["#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "],
 "E": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"],
 "F": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "],
 "G": [" ####", "#    ", "#    ", "#  ##", "#   #", "#   #", " ####"],
 "H": ["#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
 "I": ["#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"],
 "J": ["  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "],
 "K": ["#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"],
 "L": ["#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"],
 "M": ["#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"],
 "N": ["#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"],
 "O": [" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
 "P": ["#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "],
 "Q": [" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"],
 "R": ["#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"],
 "S": [" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "],
 "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "],
 "U": ["#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
 "V": ["#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "],
 "W": ["#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"],
 "X": ["#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"],
 "Y": ["#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "],
 "Z": ["#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"],
 "0": [" ### ", "#   #", "#  ##", "# # #", "##  #", "#   #", " ### "],
 "1": ["  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "],
 "2": [" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"],
 "3": [" ### ", "#   #", "    #", "  ## ", "    #", "#   #", " ### "],
 "4": ["   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "],
 "5": ["#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "],
 "6": [" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "],
 "7": ["#####", "    #", "   # ", "  #  ", "  #  ", "  #  ", "  #  "],
 "8": [" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "],
 "9": [" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "],
 ".": [" ", " ", " ", " ", " ", " ", "#"],
 ",": ["  ", "  ", "  ", "  ", "  ", " #", "# "],
 "!": ["#", "#", "#", "#", "#", " ", "#"],
 ":": [" ", "#", " ", " ", " ", "#", " "],
 "'": ["#", "#", " ", " ", " ", " ", " "],
 "?": [" ### ", "#   #", "    #", "   # ", "  #  ", "     ", "  #  "],
 "-": ["    ", "    ", "    ", "####", "    ", "    ", "    "],
 "+": ["     ", "  #  ", "  #  ", "#####", "  #  ", "  #  ", "     "],
 "/": ["    #", "   # ", "   # ", "  #  ", " #   ", " #   ", "#    "],
 "%": ["##  #", "## # ", "   # ", "  #  ", " #   ", " # ##", "#  ##"],
 "(": [" #", "# ", "# ", "# ", "# ", "# ", " #"],
 ")": ["# ", " #", " #", " #", " #", " #", "# "],
 " ": ["   "] * 7,
}

def text_width(s):
    return sum(len(_G.get(ch, _G["?"])[0]) + 1 for ch in s.upper()) - 1 if s else 0

def draw_text(img, x, y, s, color=TEXT, shadow=TEXT_SHADOW):
    """Draw text with a GBA-style 1px drop shadow (right + down)."""
    px = img.load()
    W, H = img.size
    for layer, col, off in ((0, shadow, 1), (1, color, 0)):
        if col is None:
            continue
        cx = x
        for ch in s.upper():
            g = _G.get(ch, _G["?"])
            for gy, row in enumerate(g):
                for gx, c in enumerate(row):
                    if c == "#":
                        X, Y = cx + gx + off, y + gy + off
                        if 0 <= X < W and 0 <= Y < H:
                            px[X, Y] = col
            cx += len(g[0]) + 1

# ---------------------------------------------------------------- bitmaps
def blit(img, x, y, rows, pal, flip=False):
    px = img.load()
    W, H = img.size
    for j, row in enumerate(rows):
        if flip:
            row = row[::-1]
        for i, c in enumerate(row):
            if c in ".":
                continue
            X, Y = x + i, y + j
            if 0 <= X < W and 0 <= Y < H:
                px[X, Y] = pal[c]

GRASS = ["gggggggg", "gggggldg", "gggggdgg", "gggggggg",
         "gldggggg", "gdgggggg", "gggggggg", "gggggggg"]
GRASS_B = ["gggggggg", "gggggggg", "ggldgggg", "ggdggggg",
           "gggggggg", "ggggggld", "ggggggdg", "gggggggg"]
FLOWERS = ["gggggggg", "ggfggggg", "gfyfgggg", "ggfggFgg",
           "gggggFyF", "gdgggdFg", "gggggggg", "gggggggg"]
FLOWERS_B = ["gggggggg", "gggggFgg", "ggggFyFg", "gfgggFgg",
             "fyfggggg", "gfgggggd", "ggggggdg", "gggggggg"]
TALL = [
    ["gcggcggc", "cbcgbcgb", "bbbcbbbc", "abbbabbb",
     "acbcabcb", "abbbabbb", "aabaaaba", "gaagaaag"],
    ["cggcggcg", "bcgbcgbc", "cbbbcbbb", "babbbabb",
     "bcbcbcab", "babbbabb", "abaaabaa", "agaaagaa"],
]
TREE = ["ggtTTtgg", "gtTLLTtg", "tTLLTTTt", "tTLTTTTt",
        "ttTTTTtt", "gttttttg", "gggkkggg", "ggdkkdgg"]
HOUSE = ["gggRRggg", "ggRrrRgg", "gRrrrrRg", "RRRRRRRR",
         "gwwwwwwg", "gwnwwnwg", "gwwDDwwg", "gWWDDWWg"]
ROAD = ["pppppppp", "ppqppppp", "pppppprp", "pppppppp",
        "prppppqp", "pppppppp", "ppppqppp", "pppppppp"]

def tile(level, seed, frame=0):
    """8x8 tile for a contribution level (0..4)."""
    t = Image.new("RGB", (8, 8))
    flip = seed % 2 == 1
    if level == 0:
        blit(t, 0, 0, GRASS if seed % 3 else GRASS_B, PAL, flip)
    elif level == 1:
        blit(t, 0, 0, FLOWERS if seed % 2 else FLOWERS_B, PAL)
    elif level == 2:
        blit(t, 0, 0, TALL[(frame + seed) % 2], PAL)
    elif level == 3:
        blit(t, 0, 0, TREE, PAL)
    else:
        roof, roof_dark = ROOFS[seed % len(ROOFS)]
        blit(t, 0, 0, HOUSE, {**PAL, "r": roof, "R": roof_dark})
    return t

def road_tile(seed):
    t = Image.new("RGB", (8, 8))
    blit(t, 0, 0, ROAD, PAL, seed % 2 == 1)
    return t

def border_tile():
    t = Image.new("RGB", (8, 8))
    blit(t, 0, 0, TREE, PAL)
    return t

# ---------------------------------------------------------------- trainer (original design)
TRAINER_PAL = {
    "o": hx("282830"), "h": hx("d83830"), "H": hx("a02020"), "s": hx("f8c8a0"),
    "c": hx("3878d8"), "C": hx("2050a0"), "P": hx("404858"), "B": hx("202020"),
    "w": hx("f8f8f8"),
}
_TOP = [
    "..oooo..",
    ".ohhhwo.",
    ".ohhhhHH",
    ".osssos.",
    ".osssss.",
    "..occco.",
    ".occcccs",
    ".oCcccso",
]
TRAINER = [
    _TOP + ["..oPPo..", "..oPPo..", "..oBBo..", "........"],
    _TOP + ["..oPPo..", ".oPo.Po.", ".BB..BB.", "........"],
    _TOP + ["..oPPo..", "..oPPo..", "..oBBo..", "........"],
    _TOP + ["..oPPo..", ".oP.oPo.", ".BB..BB.", "........"],
]

def draw_trainer(img, x, y, frame):
    bob = 1 if frame % 2 else 0
    blit(img, x, y + bob - 1, TRAINER[frame % 4], TRAINER_PAL)

# ---------------------------------------------------------------- creatures (original designs)
CREATURES = {
 "bot": [
    "................", ".......o........", "......olo.......", ".......o........",
    "...oooooooooo...", "..obbbbbbbbbbo..", "..oblllbbbbbbo..", "..obwkbbbbwkbo..",
    "..obwkbbbbwkbo..", "..obbbbbbbbbbo..", "..obbboooobbbo..", "..odbbbbbbbbdo..",
    "...oooooooooo...", "....odo..odo....", "....oo....oo....", "................"],
 "spark": [
    "................", "...o...oo...o...", "..olo.olbo.olo..", "..obbobbbbobbo..",
    "...obbbbbbbbo...", "..obllbbbbbbbo..", ".obllbbbbbbbbbo.", ".obbwkbbbbwkbbo.",
    ".obbwkbbbbwkbbo.", ".obbbbboobbbbbo.", ".odbbbbbbbbbbdo.", "..odbbbbbbbbdo..",
    "...oddbbbbddo...", "....oooooooo....", "................", "................"],
 "moon": [
    "................", "................", "................", ".....oooooo.....",
    "....obbbbbbo....", "...obllbbbbbo...", "..obllbbbbbbbo..", "..obwkbbbbwkbo..",
    "..obwkbbbbwkbo..", "rrobbbbbbbbbborr", ".rrrrrrrrrrrrrr.", "..odbbbbbbbbdo..",
    "...odbbbbbbdo...", "....oddddddo....", ".....oooooo.....", "................"],
 "flame": [
    "........o.......", ".......olo......", "......olbo......", ".....olbbbo.....",
    "....olbbbbbo....", "...olbbbbbbbo...", "..olbbbbbbbbbo..", "..obbwkbbwkbbo..",
    "..obbwkbbwkbbo..", "..obbbbbbbbbbo..", "..odbbbllbbbdo..", "...odbbllbbdo...",
    "....oddddddo....", ".....oooooo.....", "................", "................"],
 "snake": [
    "................", ".........oooo...", "........obbbbo..", "........obwkbbo.",
    "........obbbbbo.", ".........obbbo..", "..........obo...", "....oooooobbo...",
    "...obbbbbbbbbo..", "..obllllbbbbbbo.", "..obbbbbbbbbbbo.", "..odbbbbbbbbbdo.",
    "...oddddddddddo.", "....ooooooooooo.", "................", "................"],
 "blob": [
    "................", "................", "................", ".....oooooo.....",
    "....obllbbbo....", "...obllbbbbbo...", "..obbbbbbbbbbo..", "..obbwkbbwkbbo..",
    "..obbwkbbwkbbo..", "..obbbbbbbbbbo..", "..odbbbbbbbbdo..", "...oddddddddo...",
    "....oooooooo....", "................", "................", "................"],
}
LANG_CREATURE = {
    "TypeScript": "bot", "JavaScript": "spark", "Jupyter Notebook": "moon",
    "HTML": "flame", "Python": "snake",
}

def _mix(c, other, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c, other))

CREATURES.update({
 "bunny": [
    "................", "....oo....oo....", "...olbo..obbo...", "...olbo..obbo...",
    "...olbo..obbo...", "....obooobbo....", "...obbbbbbbbo...", "..obbwkbbwkbbo..",
    "..obbwkbbwkbbo..", "..obbbbppbbbbo..", "..odbbbbbbbbdo..", "...odbbbbbbdo...",
    "...oddooddo.....", "....oo..oo......", "................", "................"],
 "bird": [
    "................", "................", "................", "................",
    ".....oooo.......", "....obbbbo......", "...obwkbbbo.....", "..yyobbbbbo.....",
    "....obbbbbbo....", "....obllllbbo...", "....odbbbbbdo...", ".....odddddo....",
    "......y..y......", "................", "................", "................"],
 "mushroom": [
    "................", "................", "................", ".....oooooo.....",
    "...oobbbbbboo...", "..obbwwbbbbbbo..", ".obbwwwbbbwwbbo.", ".obbbbbbbbwwbbo.",
    ".oddddddddddddo.", "..oooffffffooo..", "....ofkffffkfo..", "....offffffffo..",
    ".....oooooooo...", "................", "................", "................"],
})


def draw_creature(img, x, y, lang, color, template=False):
    base = hx(color or "#9aa0a6")
    pal = {
        "o": hx("282830"), "b": base, "d": _mix(base, (0, 0, 0), 0.35),
        "l": _mix(base, (255, 255, 255), 0.5), "w": WHITE, "k": hx("181820"),
        "r": hx("d8d8e0"), "p": hx("f0a0b0"), "y": hx("f8c838"), "f": hx("f8e8c8"),
    }
    name = lang if template else LANG_CREATURE.get(lang, "blob")
    blit(img, x, y, CREATURES.get(name, CREATURES["blob"]), pal)

# ---------------------------------------------------------------- UI helpers
def rounded_box(img, x, y, w, h, fill, border, inner=None):
    d = ImageDraw.Draw(img)
    d.rectangle([x + 1, y, x + w - 2, y + h - 1], fill=border)
    d.rectangle([x, y + 1, x + w - 1, y + h - 2], fill=border)
    if inner:
        d.rectangle([x + 2, y + 1, x + w - 3, y + h - 2], fill=inner)
        d.rectangle([x + 1, y + 2, x + w - 2, y + h - 3], fill=inner)
        d.rectangle([x + 3, y + 3, x + w - 4, y + h - 4], fill=fill)
    else:
        d.rectangle([x + 2, y + 1, x + w - 3, y + h - 2], fill=fill)
        d.rectangle([x + 1, y + 2, x + w - 2, y + h - 3], fill=fill)

def down_arrow(img, x, y, color=hx("e04040")):
    d = ImageDraw.Draw(img)
    for i in range(4):
        d.line([x + i, y + i, x + 6 - i, y + i], fill=color)
