"""Generate terminal-style (tokyonight) GitHub profile cards.

Usage: python stats.py <username> <out_dir>
Env:
  GITHUB_TOKEN  token for repo/language data (a PAT also counts private repos)
  COUNT_TOKEN   optional second token; contribution counts take the max of both,
                because org repos a PAT can't reach drop out of its counts entirely
Writes: stats.svg, top-langs.svg, streak.svg
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from html import escape

USER, OUT = sys.argv[1], sys.argv[2]
TOKEN = os.environ["GITHUB_TOKEN"]
COUNT_TOKEN = os.environ.get("COUNT_TOKEN")

# tokyonight palette
BG, BAR, TRACK = "#1a1b26", "#16161e", "#24283b"
FG, DIM, BLUE, PURPLE, CYAN, GREEN, ORANGE, RED, YELLOW = (
    "#c0caf5", "#565f89", "#7aa2f7", "#bb9af7", "#7dcfff",
    "#9ece6a", "#ff9e64", "#f7768e", "#e0af68",
)
MONO = "'JetBrains Mono','Fira Code','Cascadia Code',Consolas,'Courier New',monospace"

REPO_QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    name
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, ISSUE]) { totalCount }
    repositories(first: 100, after: $after, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        stargazerCount
        forkCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""

COUNT_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}
"""


def gql(query, variables, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-stats"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]


# ---------- data ----------
user, repos, after = None, [], None
while True:
    page = gql(REPO_QUERY, {"login": USER, "after": after}, TOKEN)
    user = user or page
    repos += page["repositories"]["nodes"]
    info = page["repositories"]["pageInfo"]
    if not info["hasNextPage"]:
        break
    after = info["endCursor"]

commits, days = 0, {}
for tok in filter(None, {TOKEN, COUNT_TOKEN}):
    cc = gql(COUNT_QUERY, {"login": USER}, tok)["contributionsCollection"]
    commits = max(commits, cc["totalCommitContributions"] + cc["restrictedContributionsCount"])
    for w in cc["contributionCalendar"]["weeks"]:
        for d in w["contributionDays"]:
            days[d["date"]] = max(days.get(d["date"], 0), d["contributionCount"])

stars = sum(r["stargazerCount"] for r in repos)
forks = sum(r["forkCount"] for r in repos)
prs = user["pullRequests"]["totalCount"]
issues = user["issues"]["totalCount"]
contrib = user["repositoriesContributedTo"]["totalCount"]
followers = user["followers"]["totalCount"]

langs = {}
for r in repos:
    for e in r["languages"]["edges"]:
        name = e["node"]["name"]
        size, color = langs.get(name, (0, e["node"]["color"] or "#858585"))
        langs[name] = (size + e["size"], color)
top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:8]

# streaks (last year of calendar data)
dates = sorted(days)
today = dt.date.fromisoformat(dates[-1]) if dates else dt.date.today()
total_contrib = sum(days.values())
longest = run = 0
for d in dates:
    run = run + 1 if days[d] else 0
    longest = max(longest, run)
current, i = 0, len(dates) - 1
if dates and days[dates[i]] == 0:  # today without contributions doesn't break the streak yet
    i -= 1
while i >= 0 and days[dates[i]]:
    current += 1
    i -= 1

# rank (just for fun)
score = commits + 3 * prs + issues + 4 * stars + 2 * followers + 2 * contrib
bands = [(1000, "S"), (600, "A+"), (350, "A"), (200, "B+"), (100, "B"), (0, "C")]
rank = next(name for limit, name in bands if score >= limit)
progress = min(score / 1000, 1)


def fmt(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


# ---------- shared frame ----------
def frame(w, h, title, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs>
  <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{BLUE}"/><stop offset=".5" stop-color="{PURPLE}"/><stop offset="1" stop-color="{CYAN}"/>
  </linearGradient>
  <linearGradient id="gh" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{BLUE}"/><stop offset=".5" stop-color="{PURPLE}"/><stop offset="1" stop-color="{RED}"/>
  </linearGradient>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#ffffff" opacity=".018"/></pattern>
</defs>
<style>
  text {{ font-family: {MONO}; }}
  .ttl {{ font-size: 12px; fill: {DIM}; }}
  .cmd {{ font-size: 13px; fill: {FG}; }}
  .p {{ fill: {GREEN}; font-weight: 700; }}
  .k {{ font-size: 13px; fill: {BLUE}; }}
  .d {{ fill: #3b4261; }}
  .v {{ font-size: 13px; font-weight: 700; fill: {FG}; }}
  .sm {{ font-size: 11px; fill: {DIM}; }}
  .in {{ opacity: 0; animation: fade .5s ease-out forwards; }}
  .grow {{ transform-box: fill-box; transform-origin: left center; transform: scaleX(0); animation: grow 1.1s cubic-bezier(.2,.8,.2,1) forwards; }}
  .up {{ transform-box: fill-box; transform-origin: center bottom; transform: scaleY(0); animation: up .7s ease-out forwards; }}
  .cur {{ animation: blink 1s steps(1) infinite; }}
  @keyframes fade {{ from {{ opacity: 0; transform: translateX(-6px); }} to {{ opacity: 1; transform: none; }} }}
  @keyframes grow {{ to {{ transform: scaleX(1); }} }}
  @keyframes up {{ to {{ transform: scaleY(1); }} }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
</style>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="10" fill="{BG}" stroke="url(#g)" stroke-width="1.5"/>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="10" fill="url(#scan)"/>
<path d="M11 1.75h{w - 22}a9.25 9.25 0 0 1 9.25 9.25v20H1.75V11A9.25 9.25 0 0 1 11 1.75z" fill="{BAR}"/>
<line x1="1.75" y1="31" x2="{w - 1.75}" y2="31" stroke="{TRACK}"/>
<circle cx="20" cy="16" r="5.5" fill="{RED}"/><circle cx="38" cy="16" r="5.5" fill="{YELLOW}"/><circle cx="56" cy="16" r="5.5" fill="{GREEN}"/>
<text x="{w / 2}" y="20" text-anchor="middle" class="ttl">{escape(title)}</text>
{body}
</svg>"""


def prompt(y, cmd, delay=0):
    return (f'<text x="22" y="{y}" class="cmd in" style="animation-delay:{delay}s">'
            f'<tspan class="p">❯</tspan> {escape(cmd)}</text>')


def cursor(y, delay):
    return (f'<text x="22" y="{y}" class="cmd in" style="animation-delay:{delay}s">'
            f'<tspan class="p">❯</tspan> <tspan class="cur" fill="{FG}">█</tspan></text>')


# ---------- stats card ----------
W, H = 495, 270
rows = [
    ("commits", commits), ("pull_requests", prs), ("issues", issues),
    ("stars", stars), ("forks", forks), ("contributed_to", contrib), ("followers", followers),
]
body = [prompt(56, f"gh stats --user {USER}")]
for i, (label, val) in enumerate(rows):
    y = 86 + i * 22
    dots = "." * (22 - len(label))
    body.append(
        f'<g class="in" style="animation-delay:{0.25 + i * 0.1:.2f}s">'
        f'<text x="22" y="{y}" class="k">{label} <tspan class="d">{dots}</tspan></text>'
        f'<text x="300" y="{y}" text-anchor="end" class="v">{fmt(val)}</text></g>'
    )
body.append(cursor(86 + len(rows) * 22 + 8, 1.2))
circ = 2 * 3.14159 * 48
body.append(f"""
<g transform="translate(400 150)">
  <circle r="48" fill="none" stroke="{TRACK}" stroke-width="7"/>
  <circle r="48" fill="none" stroke="url(#g)" stroke-width="7" stroke-linecap="round" transform="rotate(-90)"
    stroke-dasharray="{circ:.1f}" stroke-dashoffset="{circ:.1f}" filter="url(#glow)">
    <animate attributeName="stroke-dashoffset" from="{circ:.1f}" to="{circ * (1 - progress):.1f}" dur="1.4s" begin=".4s" fill="freeze" calcMode="spline" keySplines=".2 .8 .2 1" keyTimes="0;1"/>
  </circle>
  <text y="10" text-anchor="middle" font-size="30" font-weight="800" fill="url(#g)" filter="url(#glow)">{rank}</text>
  <text y="74" text-anchor="middle" class="sm">rank</text>
</g>""")
stats_svg = frame(W, H, f"{USER}@github: ~/stats", "\n".join(body))

# ---------- languages card ----------
lang_total = sum(v[0] for v in langs.values()) or 1
top_max = top[0][1][0] if top else 1
body = [prompt(56, "tokei --sort code")]
for i, (name, (size, color)) in enumerate(top):
    y = 84 + i * 21
    pct = 100 * size / lang_total
    bw = max(7, 200 * size / top_max)
    d = 0.25 + i * 0.09
    body.append(
        f'<g class="in" style="animation-delay:{d:.2f}s">'
        f'<circle cx="27" cy="{y - 4}" r="4.5" fill="{color}"/>'
        f'<text x="40" y="{y}" class="k" fill="{FG}">{escape(name)}</text>'
        f'<rect x="185" y="{y - 9}" width="200" height="7" rx="3.5" fill="{TRACK}"/>'
        f'<text x="472" y="{y}" text-anchor="end" class="v">{pct:.1f}%</text></g>'
        f'<rect class="grow" style="animation-delay:{d + 0.2:.2f}s" x="185" y="{y - 9}" width="{bw:.1f}" height="7" rx="3.5" fill="{color}"/>'
    )
body.append(cursor(84 + len(top) * 21 + 8, 1.3))
langs_svg = frame(W, H, f"{USER}@github: ~/langs", "\n".join(body))

# ---------- streak card ----------
SW, SH = 1000, 230
weeks = {}
for d in dates:
    wk = dt.date.fromisoformat(d) - dt.timedelta(days=(dt.date.fromisoformat(d).weekday() + 1) % 7)
    weeks[wk] = weeks.get(wk, 0) + days[d]
wvals = [weeks[k] for k in sorted(weeks)][-53:]
wmax = max(wvals or [1]) or 1
first = dates[0] if dates else ""
cols = [
    (180, fmt(total_contrib), "contributions", f"{first} → {today}"),
    (500, f"{current}", "current streak", "days in a row" + (" 🔥" if current else "")),
    (820, f"{longest}", "longest streak", "days, last 12 months"),
]
body = [prompt(56, f"git log --author={USER} --since='1 year ago' | streak")]
for i, (x, big, label, sub) in enumerate(cols):
    hl = i == 1
    body.append(
        f'<g class="in" style="animation-delay:{0.3 + i * 0.15:.2f}s">'
        f'<text x="{x}" y="108" text-anchor="middle" font-size="38" font-weight="800" '
        f'fill="{"url(#gh)" if hl else FG}"{" filter=\"url(#glow)\"" if hl else ""}>{big}</text>'
        f'<text x="{x}" y="130" text-anchor="middle" class="k" fill="{ORANGE if hl else BLUE}">{label}</text>'
        f'<text x="{x}" y="147" text-anchor="middle" class="sm">{escape(sub)}</text></g>'
    )
body.append(f'<line x1="340" y1="72" x2="340" y2="150" stroke="{TRACK}"/>'
            f'<line x1="660" y1="72" x2="660" y2="150" stroke="{TRACK}"/>')
bw = (SW - 44) / max(len(wvals), 1)
for i, v in enumerate(wvals):
    bh = max(2, 46 * v / wmax)
    body.append(
        f'<rect class="up" style="animation-delay:{0.6 + i * 0.012:.3f}s" x="{22 + i * bw + 1:.1f}" '
        f'y="{214 - bh:.1f}" width="{bw - 2:.1f}" height="{bh:.1f}" rx="1.5" '
        f'fill="{"url(#g)" if v else TRACK}" opacity="{0.35 + 0.65 * v / wmax if v else 1:.2f}"/>'
    )
streak_svg = frame(SW, SH, f"{USER}@github: ~/streak", "\n".join(body))

os.makedirs(OUT, exist_ok=True)
for name, svg in [("stats.svg", stats_svg), ("top-langs.svg", langs_svg), ("streak.svg", streak_svg)]:
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)
print(f"commits={commits} rank={rank} streak={current}/{longest} total={total_contrib} langs={[n for n, _ in top]}")
