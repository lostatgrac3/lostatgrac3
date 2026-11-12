"""Generate tokyonight-style GitHub stats + top-languages SVG cards.

Usage: python stats.py <username> <out_dir>
Needs GITHUB_TOKEN in the environment (the Actions token is enough).
"""
import json
import os
import sys
import urllib.request
from html import escape

USER, OUT = sys.argv[1], sys.argv[2]
TOKEN = os.environ["GITHUB_TOKEN"]

BG, BORDER, TITLE, TEXT, ICON = "#1a1b27", "#e4e2e2", "#70a5fd", "#38bdae", "#bf91f3"

QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    name
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      totalPullRequestContributions
      totalIssueContributions
    }
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


def gql(variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "User-Agent": "profile-stats"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]


user, repos, after = None, [], None
while True:
    page = gql({"login": USER, "after": after})
    user = user or page
    repos += page["repositories"]["nodes"]
    info = page["repositories"]["pageInfo"]
    if not info["hasNextPage"]:
        break
    after = info["endCursor"]

cc = user["contributionsCollection"]
stars = sum(r["stargazerCount"] for r in repos)
forks = sum(r["forkCount"] for r in repos)
commits = cc["totalCommitContributions"] + cc["restrictedContributionsCount"]

langs = {}
for r in repos:
    for e in r["languages"]["edges"]:
        name = e["node"]["name"]
        size, color = langs.get(name, (0, e["node"]["color"] or "#858585"))
        langs[name] = (size + e["size"], color)
top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:8]
total = sum(v[0] for _, v in top) or 1


def fmt(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


STYLE = f"""<style>
  .t {{ font: 600 18px 'Segoe UI', Ubuntu, sans-serif; fill: {TITLE}; }}
  .s {{ font: 600 14px 'Segoe UI', Ubuntu, sans-serif; fill: {TEXT}; }}
  .b {{ font: 700 14px 'Segoe UI', Ubuntu, sans-serif; fill: {TEXT}; }}
  .l {{ font: 400 11px 'Segoe UI', Ubuntu, sans-serif; fill: {TEXT}; }}
</style>"""

# ---- stats card ----
rows = [
    ("★", "Total Stars", stars),
    ("⑂", "Total Forks", forks),
    ("◷", "Commits (last year)", commits),
    ("⇄", "Total PRs", user["pullRequests"]["totalCount"]),
    ("!", "Total Issues", user["issues"]["totalCount"]),
    ("◈", "Contributed to", user["repositoriesContributedTo"]["totalCount"]),
    ("♟", "Followers", user["followers"]["totalCount"]),
]
h = 60 + len(rows) * 25 + 10
title = escape(f"{user['name'] or USER}'s GitHub Stats")
lines = "".join(
    f'<text x="25" y="{70 + i * 25}" class="s"><tspan fill="{ICON}">{icon}</tspan>  {label}:</text>'
    f'<text x="300" y="{70 + i * 25}" class="b">{fmt(val)}</text>'
    for i, (icon, label, val) in enumerate(rows)
)
stats_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="420" height="{h}" viewBox="0 0 420 {h}">
{STYLE}
<rect x="0.5" y="0.5" rx="4.5" width="419" height="{h - 1}" fill="{BG}" stroke="{BORDER}"/>
<text x="25" y="35" class="t">{title}</text>
{lines}
</svg>"""

# ---- top languages card ----
bar, x = [], 25
for name, (size, color) in top:
    w = 300 * size / total
    bar.append(f'<rect x="{x:.2f}" y="55" width="{w:.2f}" height="8" fill="{color}"/>')
    x += w
legend = "".join(
    f'<circle cx="{30 + (i % 2) * 150}" cy="{86 + (i // 2) * 22}" r="5" fill="{color}"/>'
    f'<text x="{42 + (i % 2) * 150}" y="{90 + (i // 2) * 22}" class="l">{escape(name)} {100 * size / total:.1f}%</text>'
    for i, (name, (size, color)) in enumerate(top)
)
lh = 100 + ((len(top) + 1) // 2) * 22
langs_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="350" height="{lh}" viewBox="0 0 350 {lh}">
{STYLE}
<rect x="0.5" y="0.5" rx="4.5" width="349" height="{lh - 1}" fill="{BG}" stroke="{BORDER}"/>
<text x="25" y="35" class="t">Most Used Languages</text>
<mask id="m"><rect x="25" y="55" width="300" height="8" rx="4" fill="#fff"/></mask>
<g mask="url(#m)">{''.join(bar)}</g>
{legend}
</svg>"""

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "stats.svg"), "w", encoding="utf-8") as f:
    f.write(stats_svg)
with open(os.path.join(OUT, "top-langs.svg"), "w", encoding="utf-8") as f:
    f.write(langs_svg)
print(f"stars={stars} commits={commits} langs={[n for n, _ in top]}")
