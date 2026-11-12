"""Generate the animated hero banner and the tech-stack card.

Usage: python stack.py <username> <out_dir>
Logos come from cdn.simpleicons.org; anything missing falls back to a >_ glyph.
Writes: hero.svg, stack.svg
"""
import os
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html import escape

USER, OUT = sys.argv[1], sys.argv[2]

BG, BAR, TRACK, PILL, PILL_STROKE = "#1a1b26", "#16161e", "#24283b", "#1f2335", "#2f334d"
FG, DIM, BLUE, PURPLE, CYAN, GREEN, YELLOW, RED, ORANGE = (
    "#c0caf5", "#565f89", "#7aa2f7", "#bb9af7", "#7dcfff",
    "#9ece6a", "#e0af68", "#f7768e", "#ff9e64",
)
MONO = "'JetBrains Mono','Fira Code','Cascadia Code',Consolas,'Courier New',monospace"

# (label, simple-icons slug or None)
STACK = [
    ("languages", [
        ("Python", "python"), ("Bash", "gnubash"), ("Zsh", "zsh"), ("PowerShell", None),
        ("JavaScript", "javascript"), ("TypeScript", "typescript"), ("SQL", "mysql"),
        ("HTML", "html5"), ("CSS", "css"), ("C", "c"), ("C++", "cplusplus"), ("Lua", "lua"),
    ]),
    ("web + desktop", [
        ("Svelte", "svelte"), ("SvelteKit", "svelte"), ("Tailwind", "tailwindcss"),
        ("Node.js", "nodedotjs"), ("npm", "npm"), ("Vite", "vite"), ("FastAPI", "fastapi"),
        ("Pydantic", "pydantic"), ("SQLAlchemy", "sqlalchemy"), ("Django", "django"),
        ("PyQt6", "qt"), ("Tauri", "tauri"), ("Electron", "electron"), ("React", "react"),
    ]),
    ("linux + ricing", [
        ("Arch", "archlinux"), ("Omarchy", "archlinux"), ("Hyprland", "hyprland"),
        ("Ubuntu", "ubuntu"), ("Kubuntu", "kubuntu"), ("KDE Plasma", "kdeplasma"),
        ("NixOS", "nixos"), ("Kali", "kalilinux"), ("systemd", None), ("Btrfs", None),
        ("SSH", None), ("Polybar", None), ("Rofi", None), ("p10k", None), ("fzf", None),
        ("tmux", "tmux"),
    ]),
    ("infra + automation", [
        ("Git", "git"), ("GitHub", "github"), ("GitLab", "gitlab"), ("Actions", "githubactions"),
        ("Docker", "docker"), ("Compose", "docker"), ("Ansible", "ansible"), ("Proxmox", "proxmox"),
        ("VMware", "vmware"), ("VirtualBox", "virtualbox"), ("Kubernetes", "kubernetes"),
        ("OpenShift", "redhatopenshift"),
    ]),
    ("networking + systems", [
        ("Cisco IOS", "cisco"), ("MikroTik", "mikrotik"), ("UniFi", "ubiquiti"),
        ("OPNsense", "opnsense"), ("OpenVPN", "openvpn"), ("Pi-hole", "pihole"),
        ("Active Directory", None), ("Group Policy", None), ("Server Core", None),
        ("DNS / DHCP", None),
    ]),
    ("security + monitoring", [
        ("Splunk", "splunk"), ("Elastic", "elastic"), ("Kibana", "kibana"), ("Logstash", "logstash"),
        ("Wireshark", "wireshark"), ("TShark", "wireshark"), ("Nmap", None),
        ("Burp Suite", "burpsuite"), ("TryHackMe", "tryhackme"), ("Hack The Box", "hackthebox"),
    ]),
    ("data + messaging", [
        ("MySQL", "mysql"), ("MariaDB", "mariadb"), ("SQLite", "sqlite"), ("NATS", "natsdotio"),
        ("MQTT", "mqtt"), ("Mosquitto", "eclipsemosquitto"),
    ]),
    ("daily drivers", [
        ("Neovim", "neovim"), ("VS Code", None), ("Alacritty", "alacritty"), ("Kitty", None),
        ("Obsidian", "obsidian"), ("Markdown", "markdown"), ("LaTeX", "latex"), ("Pandoc", None),
        ("Raspberry Pi", "raspberrypi"), ("Arduino", "arduino"),
    ]),
]


def fetch_icon(slug):
    try:
        req = urllib.request.Request(f"https://cdn.simpleicons.org/{slug}",
                                     headers={"User-Agent": "profile-stack"})
        with urllib.request.urlopen(req, timeout=15) as r:
            svg = r.read().decode()
        color = re.search(r'fill="(#[0-9A-Fa-f]{6})"', svg).group(1)
        path = re.search(r'<path d="([^"]+)"', svg).group(1)
        return slug, (color, path)
    except Exception:
        return slug, None


def readable(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return hex_color if 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.33 else FG


slugs = {s for _, items in STACK for _, s in items if s}
with ThreadPoolExecutor(8) as ex:
    ICONS = dict(ex.map(fetch_icon, slugs))

STYLE = f"""<style>
  text {{ font-family: {MONO}; }}
  .ttl {{ font-size: 12px; fill: {DIM}; }}
  .cmd {{ font-size: 13px; fill: {FG}; }}
  .p {{ fill: {GREEN}; font-weight: 700; }}
  .pill {{ font-size: 12px; fill: {FG}; }}
  .pop {{ opacity: 0; transform-box: fill-box; transform-origin: center;
          animation: pop .45s cubic-bezier(.3,1.6,.5,1) forwards; }}
  .in {{ opacity: 0; animation: fade .5s ease-out forwards; }}
  .cur {{ animation: blink 1s steps(1) infinite; }}
  .shine {{ animation: shine 7s ease-in-out 2.5s infinite; }}
  .breathe {{ animation: breathe 4s ease-in-out infinite; }}
  @keyframes pop {{ 0% {{ opacity: 0; transform: scale(.4) translateY(6px); }} 100% {{ opacity: 1; transform: none; }} }}
  @keyframes fade {{ from {{ opacity: 0; transform: translateX(-8px); }} to {{ opacity: 1; transform: none; }} }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
  @keyframes shine {{ 0% {{ transform: translateX(-400px); }} 35%, 100% {{ transform: translateX(1400px); }} }}
  @keyframes breathe {{ 50% {{ opacity: .55; }} }}
</style>"""

DEFS = f"""<defs>
  <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{BLUE}"/><stop offset=".5" stop-color="{PURPLE}"/><stop offset="1" stop-color="{CYAN}"/>
  </linearGradient>
  <linearGradient id="sh" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".07"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
  </linearGradient>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" opacity=".018"/></pattern>
</defs>"""


def window(w, h, title, body, clip_id="card"):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
{DEFS}
{STYLE}
<clipPath id="{clip_id}"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="10"/></clipPath>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="10" fill="{BG}"/>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="10" fill="url(#scan)"/>
<path d="M11 1.75h{w - 22}a9.25 9.25 0 0 1 9.25 9.25v20H1.75V11A9.25 9.25 0 0 1 11 1.75z" fill="{BAR}"/>
<line x1="1.75" y1="31" x2="{w - 1.75}" y2="31" stroke="{TRACK}"/>
<circle cx="20" cy="16" r="5.5" fill="{RED}"/><circle cx="38" cy="16" r="5.5" fill="{YELLOW}"/><circle cx="56" cy="16" r="5.5" fill="{GREEN}"/>
<text x="{w / 2}" y="20" text-anchor="middle" class="ttl">{escape(title)}</text>
{body}
<g clip-path="url(#{clip_id})"><g transform="skewX(-20)"><rect class="shine" x="0" y="0" width="260" height="{h}" fill="url(#sh)"/></g></g>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="10" fill="none" stroke="url(#g)" stroke-width="1.5"/>
</svg>"""


# ---------- stack card ----------
W = 1000
PAD, CH, PH, GAPX, GAPY = 22, 7.4, 28, 8, 9
body, y, n = [], 40, 0
for ci, (cat, items) in enumerate(STACK):
    y += 24
    body.append(f'<text x="{PAD}" y="{y}" class="cmd in" style="animation-delay:{0.15 + n * 0.025:.2f}s">'
                f'<tspan class="p">❯</tspan> ls <tspan fill="{CYAN}">~/stack/{escape(cat.replace(" + ", "-").replace(" ", "-"))}</tspan></text>')
    y += 12
    x = PAD
    for label, slug in items:
        icon = ICONS.get(slug) if slug else None
        pw = 12 + 16 + 7 + len(label) * CH + 12
        if x + pw > W - PAD:
            x, y = PAD, y + PH + GAPY
        d = 0.25 + n * 0.025
        if icon:
            color, path = icon
            glyph = (f'<g transform="translate({x + 12:.1f} {y + 6}) scale(.6667)">'
                     f'<path d="{path}" fill="{readable(color)}"/></g>')
            accent = readable(color)
        else:
            glyph = (f'<text x="{x + 12:.1f}" y="{y + 18.5}" font-size="12" font-weight="700" '
                     f'fill="{GREEN}">&gt;_</text>')
            accent = GREEN
        body.append(
            f'<g class="pop" style="animation-delay:{d:.3f}s">'
            f'<rect x="{x:.1f}" y="{y}" width="{pw:.1f}" height="{PH}" rx="7" fill="{PILL}" stroke="{PILL_STROKE}"/>'
            f'<rect x="{x:.1f}" y="{y + PH - 2}" width="{pw:.1f}" height="2" rx="1" fill="{accent}" opacity=".55"/>'
            f'{glyph}<text x="{x + 35:.1f}" y="{y + 18.5}" class="pill">{escape(label)}</text></g>'
        )
        x += pw + GAPX
        n += 1
    y += PH + 6
y += 26
body.append(f'<text x="{PAD}" y="{y}" class="cmd in" style="animation-delay:{0.3 + n * 0.025:.2f}s">'
            f'<tspan class="p">❯</tspan> <tspan class="cur" fill="{FG}">█</tspan></text>')
H = int(y + 22)
stack_svg = window(W, H, f"{USER}@arch: ~/stack", "\n".join(body))

# ---------- hero banner ----------
HW, HH = 1000, 300
boot = [
    (GREEN, "  OK  ", "Started dotfiles.service - ricing setups nobody asked for"),
    (GREEN, "  OK  ", "Reached target network-automation.target"),
    (GREEN, "  OK  ", "Mounted /home/lostatgrac3 on arch (hyprland, zsh, nvim)"),
    (GREEN, "  OK  ", "Started htl-it-student.service"),
    (YELLOW, " WARN ", "sleep.service: unit not found"),
]
lines = []
for i, (c, tag, msg) in enumerate(boot):
    lines.append(
        f'<text x="40" y="{196 + i * 18}" class="boot in" style="animation-delay:{1.6 + i * 0.35:.2f}s">'
        f'[<tspan fill="{c}" font-weight="700">{tag}</tspan>] {escape(msg)}</text>'
    )
name = escape(USER)
sub = "htl it student // network automation // linux tinkering"
hero_body = f"""
<style>
  .boot {{ font-size: 12.5px; fill: {DIM}; }}
  .name {{ font-size: 64px; font-weight: 800; letter-spacing: -1px; }}
  .sub {{ font-size: 15px; fill: {FG}; }}
  .gl1 {{ animation: gl1 3.2s steps(1) infinite; }}
  .gl2 {{ animation: gl2 3.2s steps(1) infinite; }}
  @keyframes gl1 {{
    0%, 86%, 100% {{ clip-path: inset(100% 0 0 0); transform: none; }}
    88% {{ clip-path: inset(10% 0 60% 0); transform: translate(-5px, 0); }}
    91% {{ clip-path: inset(55% 0 20% 0); transform: translate(4px, 0); }}
    94% {{ clip-path: inset(30% 0 45% 0); transform: translate(-3px, 0); }}
  }}
  @keyframes gl2 {{
    0%, 86%, 100% {{ clip-path: inset(100% 0 0 0); transform: none; }}
    89% {{ clip-path: inset(65% 0 5% 0); transform: translate(5px, 0); }}
    92% {{ clip-path: inset(5% 0 75% 0); transform: translate(-4px, 0); }}
    95% {{ clip-path: inset(40% 0 35% 0); transform: translate(3px, 0); }}
  }}
  @keyframes gridmove {{ to {{ transform: translateY(40px); }} }}
  .grid {{ animation: gridmove 3s linear infinite; }}
</style>
<g opacity=".35">
  <g class="grid">
    {''.join(f'<line x1="0" y1="{30 + k * 40}" x2="{HW}" y2="{30 + k * 40}" stroke="{TRACK}"/>' for k in range(-1, 8))}
  </g>
  {''.join(f'<line x1="{k * 40}" y1="31" x2="{k * 40}" y2="{HH}" stroke="{TRACK}"/>' for k in range(1, 25))}
</g>
<rect x="2" y="31" width="{HW - 4}" height="{HH - 33}" fill="url(#fadebg)"/>
<defs><linearGradient id="fadebg" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{BG}" stop-opacity=".95"/><stop offset=".6" stop-color="{BG}" stop-opacity=".6"/><stop offset="1" stop-color="{BG}" stop-opacity=".2"/>
</linearGradient></defs>
<text x="40" y="66" class="cmd in" style="animation-delay:.1s"><tspan class="p">❯</tspan> whoami</text>
<g class="in" style="animation-delay:.4s">
  <text x="36" y="134" class="name" fill="url(#g)" filter="url(#glow)">{name}</text>
  <text x="36" y="134" class="name gl1" fill="{RED}" opacity=".85">{name}</text>
  <text x="36" y="134" class="name gl2" fill="{CYAN}" opacity=".85">{name}</text>
</g>
<clipPath id="type"><rect x="40" y="148" height="24" width="0">
  <animate attributeName="width" from="0" to="{len(sub) * 9.1 + 4:.0f}" dur="1.6s" begin=".8s" fill="freeze" calcMode="discrete"
    values="{';'.join(str(round(k * 9.1)) for k in range(len(sub) + 1))}"/>
</rect></clipPath>
<text x="40" y="166" class="sub" clip-path="url(#type)">{escape(sub)}</text>
<rect x="{40 + len(sub) * 9.1 + 4:.0f}" y="152" width="9" height="17" fill="{PURPLE}" class="cur in" style="animation-delay:2.4s"/>
{''.join(lines)}
<g transform="translate(830 165)" class="breathe">
  <circle r="78" fill="none" stroke="{TRACK}" stroke-width="1"/>
  <circle r="58" fill="none" stroke="url(#g)" stroke-width="1.5" stroke-dasharray="4 8">
    <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="24s" repeatCount="indefinite"/>
  </circle>
  <circle r="78" fill="none" stroke="url(#g)" stroke-width="2" stroke-dasharray="60 430" filter="url(#glow)">
    <animateTransform attributeName="transform" type="rotate" from="360" to="0" dur="9s" repeatCount="indefinite"/>
  </circle>
  <path transform="translate(-24 -24) scale(2)" fill="{BLUE}" filter="url(#glow)"
    d="{ICONS.get('archlinux', ('', 'M12 0c-1.07 2.62-1.71 4.33-2.9 6.88.73.77 1.62 1.68 3.07 2.69-1.56-.64-2.62-1.29-3.42-1.96C7.22 10.8 4.86 15.26 0 24c3.82-2.2 6.78-3.56 9.54-4.08a7 7 0 0 1-.18-1.63v-.12c.06-2.45 1.33-4.33 2.85-4.2 1.51.13 2.69 2.21 2.63 4.66-.01.46-.06.9-.15 1.31 2.73.53 5.66 1.89 9.43 4.06l-2.02-3.68c-1.06-.82-2.17-1.89-4.43-3.05 1.55.4 2.66.87 3.53 1.39C15.8 6.76 15.25 5.08 12 0Z'))[1]}"/>
</g>
"""
hero_svg = window(HW, HH, f"{USER}@arch: ~", hero_body, clip_id="hero")

os.makedirs(OUT, exist_ok=True)
for fname, svg in [("hero.svg", hero_svg), ("stack.svg", stack_svg)]:
    with open(os.path.join(OUT, fname), "w", encoding="utf-8") as f:
        f.write(svg)
missing = sorted(s for s in slugs if not ICONS.get(s))
print(f"stack: {n} badges, {len(slugs) - len(missing)} logos, missing={missing}")
