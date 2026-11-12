"""Minimal profile cards: header, stats, stack. Each in a dark and a light variant.

Usage: python profile.py <username> <out_dir>
Env:
  GITHUB_TOKEN  repo/language data (a PAT also counts private repos)
  COUNT_TOKEN   optional second token; contribution counts take the max of both
Writes: {header,stats,stack}-{dark,light}.svg
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html import escape

USER, OUT = sys.argv[1], sys.argv[2]
TOKEN = os.environ["GITHUB_TOKEN"]
COUNT_TOKEN = os.environ.get("COUNT_TOKEN")

THEMES = {
    "dark": {"fg": "#e6edf3", "muted": "#7d8590", "faint": "#21262d", "accent": "#8ca8ff"},
    "light": {"fg": "#1f2328", "muted": "#656d76", "faint": "#eaeef2", "accent": "#4f6bd8"},
}
SANS = "-apple-system,'Segoe UI','Inter',system-ui,'Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,'JetBrains Mono','SF Mono','Cascadia Code',Consolas,monospace"
W = 1000

TAGLINE = "IT student at an HTL. Network automation, Linux and small tools."

STACK = [
    ("languages", [("Python", "python"), ("Bash", "gnubash"), ("TypeScript", "typescript"),
                   ("JavaScript", "javascript"), ("SQL", None), ("C", "c")]),
    ("web", [("Svelte", "svelte"), ("Tailwind", "tailwindcss"), ("FastAPI", "fastapi"),
             ("Django", "django"), ("Node.js", "nodedotjs"), ("Tauri", "tauri")]),
    ("linux", [("Arch", "archlinux"), ("Hyprland", "hyprland"), ("NixOS", "nixos"),
               ("Kubuntu", "kubuntu"), ("Neovim", "neovim"), ("tmux", "tmux")]),
    ("infra", [("Docker", "docker"), ("Ansible", "ansible"), ("Proxmox", "proxmox"),
               ("Kubernetes", "kubernetes"), ("GitHub Actions", "githubactions")]),
    ("network", [("Cisco", "cisco"), ("MikroTik", "mikrotik"), ("UniFi", "ubiquiti"),
                 ("OPNsense", "opnsense"), ("OpenVPN", "openvpn")]),
    ("security", [("Splunk", "splunk"), ("Elastic", "elastic"), ("Wireshark", "wireshark"),
                  ("Burp Suite", "burpsuite"), ("TryHackMe", "tryhackme")]),
    ("data", [("MySQL", "mysql"), ("SQLite", "sqlite"), ("NATS", "natsdotio"), ("MQTT", "mqtt")]),
]

# ---------------------------------------------------------------- GitHub data
REPO_QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    pullRequests { totalCount }
    repositories(first: 100, after: $after, ownerAffiliations: OWNER, isFork: false) {
      pageInfo { hasNextPage endCursor }
      nodes {
        stargazerCount
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
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-cards"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]


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
prs = user["pullRequests"]["totalCount"]
langs = {}
for r in repos:
    for e in r["languages"]["edges"]:
        name = e["node"]["name"]
        size, color = langs.get(name, (0, e["node"]["color"] or "#8b949e"))
        langs[name] = (size + e["size"], color)
lang_total = sum(v[0] for v in langs.values()) or 1
top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:6]

dates = sorted(days)
contributions = sum(days.values())
longest = run = 0
for d in dates:
    run = run + 1 if days[d] else 0
    longest = max(longest, run)
current, i = 0, len(dates) - 1
if dates and days[dates[i]] == 0:
    i -= 1
while i >= 0 and days[dates[i]]:
    current += 1
    i -= 1


# ---------------------------------------------------------------- icons
def fetch_icon(slug):
    try:
        req = urllib.request.Request(f"https://cdn.simpleicons.org/{slug}", headers={"User-Agent": "profile-cards"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return slug, re.search(r'<path d="([^"]+)"', r.read().decode()).group(1)
    except Exception:
        return slug, None


with ThreadPoolExecutor(8) as ex:
    ICONS = dict(ex.map(fetch_icon, {s for _, items in STACK for _, s in items if s}))


# ---------------------------------------------------------------- svg helpers
def svg(w, h, t, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none">
<style>
  .sans {{ font-family: {SANS}; }}
  .mono {{ font-family: {MONO}; }}
  .lbl {{ font-family: {MONO}; font-size: 11px; letter-spacing: 1.2px; fill: {t['muted']}; }}
  .in {{ opacity: 0; animation: in .7s cubic-bezier(.2,.7,.2,1) forwards; }}
  .grow {{ transform-box: fill-box; transform-origin: left center; transform: scaleX(0);
           animation: grow 1.2s cubic-bezier(.2,.7,.2,1) forwards; }}
  .blink {{ animation: blink 1.1s steps(1) infinite; }}
  @keyframes in {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
  @keyframes grow {{ to {{ transform: scaleX(1); }} }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
</style>
{body}
</svg>"""


def d(sec):
    return f'style="animation-delay:{sec:.2f}s"'


def fmt(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


# ---------------------------------------------------------------- header
def header(t):
    body = f"""
<text x="0" y="62" class="sans in" font-size="46" font-weight="650" letter-spacing="-1.5" fill="{t['fg']}">{escape(USER)}<tspan class="blink" fill="{t['accent']}">_</tspan></text>
<text x="1" y="100" class="sans in" {d(.15)} font-size="17" fill="{t['muted']}">{escape(TAGLINE)}</text>
<rect x="1" y="128" width="{W - 2}" height="1" fill="{t['faint']}"/>
<rect x="1" y="128" width="140" height="1" fill="{t['accent']}" class="grow" {d(.35)}/>
"""
    return svg(W, 132, t, body)


# ---------------------------------------------------------------- stats
def stats(t):
    metrics = [(fmt(commits), "COMMITS"), (fmt(contributions), "CONTRIBUTIONS"),
               (fmt(prs), "PULL REQUESTS"), (f"{current}d", "CURRENT STREAK"), (f"{longest}d", "LONGEST STREAK")]
    col = W / len(metrics)
    parts = []
    for i, (val, label) in enumerate(metrics):
        x = i * col
        parts.append(
            f'<g class="in" {d(.05 + i * .07)}>'
            f'<text x="{x:.0f}" y="38" class="sans" font-size="30" font-weight="600" letter-spacing="-.5" fill="{t["fg"]}">{val}</text>'
            f'<text x="{x + 1:.0f}" y="62" class="lbl">{label}</text></g>'
        )
    # language bar
    parts.append(f'<rect x="0" y="94" width="{W}" height="6" rx="3" fill="{t["faint"]}"/>')
    parts.append('<clipPath id="bar"><rect x="0" y="94" width="1000" height="6" rx="3"/></clipPath>')
    x, segs = 0.0, []
    shown = sum(v[0] for _, v in top) or 1
    for name, (size, color) in top:
        w = W * size / shown
        segs.append(f'<rect x="{x:.1f}" y="94" width="{max(w - 2, 1):.1f}" height="6" fill="{color}"/>')
        x += w
    parts.append(f'<g clip-path="url(#bar)"><g class="grow" {d(.4)}>{"".join(segs)}</g></g>')
    lx = 0
    for i, (name, (size, color)) in enumerate(top):
        label = f"{name} {100 * size / lang_total:.0f}%"
        parts.append(
            f'<g class="in" {d(.6 + i * .05)}><circle cx="{lx + 4}" cy="126" r="4" fill="{color}"/>'
            f'<text x="{lx + 14}" y="130" class="mono" font-size="12" fill="{t["muted"]}">{escape(label)}</text></g>'
        )
        lx += 14 + len(label) * 7.4 + 26
    return svg(W, 140, t, "\n".join(parts))


# ---------------------------------------------------------------- stack
def stack(t):
    parts, y = [], 18
    for r, (cat, items) in enumerate(STACK):
        g = [f'<text x="0" y="{y + 5}" class="lbl">{cat.upper()}</text>']
        x = 150
        for label, slug in items:
            path = ICONS.get(slug) if slug else None
            if path:
                g.append(f'<g transform="translate({x} {y - 8}) scale(.6667)"><path d="{path}" fill="{t["fg"]}"/></g>')
                tx = x + 24
            else:
                tx = x
            g.append(f'<text x="{tx}" y="{y + 5}" class="sans" font-size="14" fill="{t["fg"]}">{escape(label)}</text>')
            x = tx + len(label) * 7.6 + 34
        parts.append(f'<g class="in" {d(.05 + r * .08)}>{"".join(g)}</g>')
        if r < len(STACK) - 1:
            parts.append(f'<rect x="0" y="{y + 20}" width="{W}" height="1" fill="{t["faint"]}"/>')
        y += 42
    return svg(W, y - 14, t, "\n".join(parts))


os.makedirs(OUT, exist_ok=True)
for theme, t in THEMES.items():
    for name, fn in [("header", header), ("stats", stats), ("stack", stack)]:
        with open(os.path.join(OUT, f"{name}-{theme}.svg"), "w", encoding="utf-8") as f:
            f.write(fn(t))
print(f"commits={commits} contributions={contributions} prs={prs} streak={current}/{longest} "
      f"langs={[n for n, _ in top]} icons={sum(1 for v in ICONS.values() if v)}/{len(ICONS)}")
