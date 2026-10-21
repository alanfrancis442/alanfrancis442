#!/usr/bin/env python3
"""Build the pixel-world README images.

  python generate.py --user alanfrancis442            # real data (needs GH_TOKEN)
  python generate.py --user alanfrancis442 --sample   # offline preview data

Env:
  GH_TOKEN         token for the GitHub GraphQL API (the Action passes one in)
  DISPLAY_NAME     optional override for the name in the images (default: your GitHub username)
  EXCLUDE_LANGS    comma-separated languages to hide, e.g. "Jupyter Notebook,HTML"
"""
import argparse, datetime as dt, json, os, random, urllib.request
from pathlib import Path

from pixel.render import render_map, render_party
from pixel.svg import render_svg
from pixel.party_svg import render_party_svg
from pixel.intro_svg import render_intro_svg

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
          "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

QUERY = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}"""


def gql(token, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if "errors" in out:
        raise SystemExit(f"GitHub API error: {out['errors']}")
    return out["data"]["user"]


def fetch_real(login, token):
    days, sizes, colors, cursor, first = [], {}, {}, None, True
    while True:
        u = gql(token, {"login": login, "cursor": cursor})
        if first:
            cal = u["contributionsCollection"]["contributionCalendar"]
            for w in cal["weeks"]:
                for d in w["contributionDays"]:
                    days.append((d["date"], d["contributionCount"], LEVELS[d["contributionLevel"]]))
            first = False
        for repo in u["repositories"]["nodes"]:
            for e in repo["languages"]["edges"]:
                n = e["node"]["name"]
                sizes[n] = sizes.get(n, 0) + e["size"]
                colors[n] = e["node"]["color"]
        page = u["repositories"]["pageInfo"]
        if not page["hasNextPage"]:
            break
        cursor = page["endCursor"]
    return days, sizes, colors


def sample_data():
    rng = random.Random(442)
    today = dt.date.today()
    start = today - dt.timedelta(days=364 + (today.weekday() + 1) % 7)
    days, d = [], start
    while d <= today:
        busy = 0.15 if (d - start).days < 90 else 0.65
        c = 0 if rng.random() > busy else int(rng.expovariate(0.18)) + 1
        days.append([d.isoformat(), c, 0])
        d += dt.timedelta(days=1)
    nz = sorted(c for _, c, _ in days if c)
    q = [nz[len(nz) * k // 4] for k in (1, 2, 3)]
    for row in days:
        c = row[1]
        row[2] = 0 if c == 0 else 1 + sum(c > t for t in q)
    days[-1][1], days[-1][2] = 12, 3
    sizes = {"TypeScript": 75.77, "Jupyter Notebook": 8.72, "HTML": 6.00,
             "JavaScript": 5.42, "Python": 4.09}
    colors = {"TypeScript": "#3178c6", "Jupyter Notebook": "#DA5B0B", "HTML": "#e34c26",
              "JavaScript": "#f1e05a", "Python": "#3572A5"}
    return [tuple(r) for r in days], sizes, colors


def shape(days, sizes, colors, name):
    # contribution weeks (Sunday-first columns, like GitHub)
    weeks, cur = [], [None] * 7
    for date, count, level in days:
        wd = (dt.date.fromisoformat(date).weekday() + 1) % 7
        if wd == 0 and any(x is not None for x in cur):
            weeks.append(cur)
            cur = [None] * 7
        cur[wd] = (count, level)
    weeks.append(cur)
    weeks = weeks[-53:]

    today_count = days[-1][1]
    total = sum(c for _, c, _ in days)
    streak = 0
    for _, c, _ in reversed(days[:-1] if today_count == 0 else days):
        if not c:
            break
        streak += 1

    excluded = {s.strip() for s in os.environ.get("EXCLUDE_LANGS", "").split(",") if s.strip()}
    sizes = {k: v for k, v in sizes.items() if k not in excluded}
    tot = sum(sizes.values()) or 1
    langs = [{"name": k, "color": colors.get(k), "percent": v / tot * 100}
             for k, v in sorted(sizes.items(), key=lambda kv: -kv[1])][:5]

    n = name.upper()
    msg1 = (f"{n} MADE {today_count} CONTRIBUTION{'S' if today_count != 1 else ''} TODAY!"
            if today_count else f"{n} IS RESTING TODAY... ZZZ")
    msg2 = f"{total} THIS YEAR. STREAK: {streak} DAY{'S' if streak != 1 else ''}."
    return {
        "weeks": weeks, "today_week": len(weeks) - 1,
        "title": f"{n}'S TOWN", "msg1": msg1, "msg2": msg2,
        "languages": langs, "party_title": f"{n}'S PARTY",
        "party_msg": "CHOOSE A LANGUAGE TO SHIP.",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--out", default="dist")
    ap.add_argument("--sample", action="store_true")
    a = ap.parse_args()

    if a.sample:
        days, sizes, colors = sample_data()
    else:
        token = os.environ.get("GH_TOKEN")
        if not token:
            raise SystemExit("Set GH_TOKEN, or pass --sample for preview data.")
        days, sizes, colors = fetch_real(a.user, token)

    data = shape(days, sizes, colors, os.environ.get("DISPLAY_NAME") or a.user)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    render_map(data, out / "town.gif")
    render_party(data, out / "party.gif")
    render_svg(data, out / "town.svg")
    render_party_svg(data, out / "party.svg")
    render_intro_svg(a.user, Path(__file__).parent / "intro.txt", out / "intro.svg")
    print(f"wrote intro.svg, town.svg, party.svg (+ GIF fallbacks) to {out}")


if __name__ == "__main__":
    main()
