"""Animated 'classified terminal' intro, generated from intro.txt.

intro.txt syntax:
  $ text     a command: typed out character by character after a prompt
  ! text     an error line (red)
  @user      replaced with your GitHub username
  █████      redaction bar (flickers, sometimes leaks garbage)
  anything else is printed output
"""
import html
import random

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono','Liberation Mono',monospace"
CW = 8.4             # approx monospace char width at 14px
LH = 21
PAD_X, TOP = 22, 54
TYPE = 0.055         # seconds per typed char
PAUSE = 0.45


def _esc(s):
    return html.escape(s).replace(" ", "\u00a0")


def _fit(n):
    """Force n characters to occupy exactly n grid cells, whatever the font."""
    return f'textLength="{CW * n:.1f}" lengthAdjust="spacingAndGlyphs"' if n else ""


def render_intro_svg(user, src_path, out_path, width=880):
    rng = random.Random(42)
    lines = [l.rstrip("\n") for l in open(src_path, encoding="utf-8")]
    while lines and not lines[-1].strip():
        lines.pop()
    prompt = f"{user}@unknown:~$ "

    defs, text, bars = [], [], []
    t = 0.8
    y = TOP
    last_cursor = None
    for i, raw in enumerate(lines):
        line = raw.replace("@user", user)
        if line.startswith("$"):
            cmd = line[1:].strip()
            # prompt appears, then the command is typed
            text.append(
                f'<text x="{PAD_X}" y="{y}" {_fit(len(prompt) - 1)} opacity="0"><set attributeName="opacity" to="1" '
                f'begin="{t:.2f}s"/><tspan fill="#3fb950">{html.escape(user)}</tspan>'
                f'<tspan fill="#6e7681">@</tspan><tspan fill="#a371f7">unknown</tspan>'
                f'<tspan fill="#6e7681">:~$</tspan></text>')
            x0 = PAD_X + CW * len(prompt)
            if cmd:
                n = len(cmd)
                ws = ";".join(f"{CW * k:.1f}" for k in range(n + 1))
                kt = ";".join(f"{k / n:.4f}" for k in range(n + 1))
                defs.append(
                    f'<clipPath id="ty{i}"><rect x="{x0}" y="{y - 16}" width="0" height="{LH}">'
                    f'<animate attributeName="width" values="{ws}" keyTimes="{kt}" '
                    f'calcMode="discrete" dur="{n * TYPE:.2f}s" begin="{t + .35:.2f}s" '
                    f'fill="freeze"/></rect></clipPath>')
                text.append(f'<text x="{x0}" y="{y}" fill="#e6edf3" {_fit(n)} '
                            f'clip-path="url(#ty{i})">{_esc(cmd)}</text>')
                # moving cursor while typing
                text.append(
                    f'<rect x="{x0}" y="{y - 13}" width="{CW:.1f}" height="16" fill="#e6edf3" '
                    f'opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s"/>'
                    f'<animate attributeName="x" values="{";".join(f"{x0 + CW * k:.1f}" for k in range(n + 1))}" '
                    f'keyTimes="{kt}" calcMode="discrete" dur="{n * TYPE:.2f}s" '
                    f'begin="{t + .35:.2f}s" fill="freeze"/>'
                    f'<set attributeName="opacity" to="0" begin="{t + .35 + n * TYPE + .15:.2f}s"/>'
                    f'</rect>')
                t += .35 + n * TYPE + PAUSE
            else:
                last_cursor = (x0, y, t)
                t += .3
        else:
            colour = "#ff7b72" if line.startswith("!") else "#8b949e"
            body = line[1:].lstrip() if line.startswith("!") else line
            parts, k = [], 0
            while k < len(body):                     # split out redaction runs
                j = k
                if body[k] == "█":
                    while j < len(body) and body[j] == "█":
                        j += 1
                    parts.append(("bar", k, j - k))
                else:
                    while j < len(body) and body[j] != "█":
                        j += 1
                    parts.append(("txt", k, body[k:j]))
                k = j
            plain = body.replace("█", " ")
            text.append(f'<text x="{PAD_X}" y="{y}" fill="{colour}" {_fit(len(plain))} opacity="0">'
                        f'<set attributeName="opacity" to="1" begin="{t:.2f}s"/>{_esc(plain)}</text>')
            for kind, k, n in parts:
                if kind != "bar":
                    continue
                bx, bw = PAD_X + CW * k, CW * n
                leak = "".join(rng.choice("#$%&@?!*<>/\\=+0123456789ABCDEFXZ") for _ in range(n))
                b = rng.uniform(1, 5)
                bars.append(
                    f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s"/>'
                    f'<text x="{bx:.1f}" y="{y}" fill="#ff7b72" {_fit(n)}>{_esc(leak)}</text>'
                    f'<rect x="{bx:.1f}" y="{y - 13}" width="{bw:.1f}" height="16" fill="#c9d1d9">'
                    f'<animate attributeName="opacity" values="1;1;.15;1;0;1;1" '
                    f'keyTimes="0;.86;.87;.9;.91;.94;1" calcMode="discrete" dur="{rng.uniform(4, 7):.1f}s" '
                    f'begin="{t + b:.2f}s" repeatCount="indefinite"/></rect></g>')
            if line.startswith("!"):                 # the denial makes the screen shudder
                text.append(
                    f'<rect x="0" y="0" width="{width}" height="100%" fill="#ff3b30" opacity="0">'
                    f'<animate attributeName="opacity" values="0;.12;0;.06;0" dur=".5s" '
                    f'begin="{t:.2f}s" fill="freeze"/></rect>')
            t += .22 if not line.startswith("!") else .9
        y += LH

    if last_cursor:                                  # final blinking cursor
        cx, cy, ct = last_cursor
        text.append(
            f'<rect x="{cx}" y="{cy - 13}" width="{CW:.1f}" height="16" fill="#e6edf3" opacity="0">'
            f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" '
            f'calcMode="discrete" dur="1.05s" begin="{ct:.2f}s" repeatCount="indefinite"/></rect>')

    H = y + 10
    glitch_dur = 7
    gl = 'values="0;0;.75;0;.75;0;0" keyTimes="0;.9;.905;.92;.93;.945;1" calcMode="discrete"'
    jitter = ('values="0 0;0 0;-3 0;2 0;0 0;0 0" keyTimes="0;.9;.905;.92;.935;1" '
              'calcMode="discrete"')
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {width} {H}" width="{width}" height="{H}" font-family="{FONT}" '
        f'font-size="14" xml:space="preserve">'
        f'<defs>{"".join(defs)}'
        f'<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse">'
        f'<rect width="4" height="1" fill="#000" opacity=".35"/></pattern>'
        f'<radialGradient id="crt" cx=".5" cy=".45" r=".75"><stop offset=".55" stop-color="#000" '
        f'stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".55"/></radialGradient>'
        f'<linearGradient id="beam" x1="0" y1="0" x2="0" y2="1"><stop offset="0" '
        f'stop-color="#58a6ff" stop-opacity="0"/><stop offset=".5" stop-color="#58a6ff" '
        f'stop-opacity=".07"/><stop offset="1" stop-color="#58a6ff" stop-opacity="0"/></linearGradient>'
        f'<g id="screen">{"".join(text)}{"".join(bars)}</g></defs>'
        f'<rect width="{width}" height="{H}" rx="10" fill="#0a0e14"/>'
        f'<rect x=".5" y=".5" width="{width - 1}" height="{H - 1}" rx="10" fill="none" stroke="#30363d"/>'
        # window bar
        f'<circle cx="22" cy="18" r="5.5" fill="#ff5f57"/><circle cx="40" cy="18" r="5.5" fill="#febc2e"/>'
        f'<circle cx="58" cy="18" r="5.5" fill="#28c840"/>'
        f'<text x="{width / 2}" y="22" text-anchor="middle" fill="#6e7681" font-size="12">'
        f'~/.{html.escape(user)} — transmission'
        f'<animate attributeName="fill" values="#6e7681;#6e7681;#ff7b72;#6e7681" '
        f'keyTimes="0;.9;.92;1" calcMode="discrete" dur="{glitch_dur}s" repeatCount="indefinite"/>'
        f'</text>'
        f'<line x1="0" y1="34" x2="{width}" y2="34" stroke="#21262d"/>'
        # chromatic glitch copies + main layer
        f'<use xlink:href="#screen" fill="#ff004c" opacity="0" transform="translate(3 0)" '
        f'style="mix-blend-mode:screen"><animate attributeName="opacity" {gl} '
        f'dur="{glitch_dur}s" repeatCount="indefinite"/></use>'
        f'<use xlink:href="#screen" opacity="0" transform="translate(-3 1)" '
        f'style="mix-blend-mode:screen;filter:hue-rotate(180deg)"><animate attributeName="opacity" '
        f'{gl} dur="{glitch_dur}s" repeatCount="indefinite"/></use>'
        f'<g><animateTransform attributeName="transform" type="translate" {jitter} '
        f'dur="{glitch_dur}s" repeatCount="indefinite"/><use xlink:href="#screen"/></g>'
        # CRT feel
        f'<rect y="35" width="{width}" height="60" fill="url(#beam)">'
        f'<animate attributeName="y" values="-60;{H}" dur="5s" repeatCount="indefinite"/></rect>'
        f'<rect y="35" width="{width}" height="{H - 35}" fill="url(#scan)" opacity=".5"/>'
        f'<rect width="{width}" height="{H}" rx="10" fill="url(#crt)"/>'
        f'</svg>')
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(svg)
