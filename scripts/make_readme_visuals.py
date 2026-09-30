"""Create the README feature board in the banner's visual language (Pillow only)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = Path('/usr/share/fonts/truetype/liberation')

def font(size, bold=False):
    name = 'LiberationSans-Bold.ttf' if bold else 'LiberationSans-Regular.ttf'
    path = FONT_DIR / name
    if not path.exists():
        path = Path('/usr/share/fonts/truetype/dejavu') / ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')
    return ImageFont.truetype(str(path), size)

W, H = 1280, 690
base = Image.new('RGBA', (W, H), '#0c0a19')
glow = Image.new('RGBA', (W, H))
g = ImageDraw.Draw(glow)
g.ellipse((850, -570, 1650, 340), fill=(108, 66, 223, 135))
g.ellipse((-550, 420, 480, 1080), fill=(74, 66, 191, 87))
base = Image.alpha_composite(base, glow.filter(ImageFilter.GaussianBlur(125)))
d = ImageDraw.Draw(base)
d.rounded_rectangle((50, 49, 89, 88), radius=10, fill='#665bef')
d.text((60, 52), 'Z', font=font(28, True), fill='#fff')
d.text((105, 61), 'ZENRBXMANAGER  /  THE WORKSPACE', font=font(16, True), fill='#c4b9fe')
d.text((50, 119), 'Everything in its place.', font=font(48, True), fill='#f5f4ff')
d.text((52, 176), 'One calm workspace for the accounts you actually use.', font=font(21), fill='#b5b4cc')

cards = [
    ('01', 'One list, zero guesswork', ['Search, filter, label and reorder', 'your accounts at a glance.']),
    ('02', 'Get to the right game', ['Launch Roblox Home, a Place ID', 'or a specific server Job ID.']),
    ('03', 'Notes that stay with you', ['Keep aliases and 250-character', 'notes beside the right account.']),
    ('04', 'Your setup, your way', ['Accent themes, browser choice,', 'launch delay and Bloxstrap option.']),
    ('05', 'Local by design', ['Your encrypted account vault stays', 'on your PC. Export omits cookies.']),
    ('06', 'Know what is known', ['Presence when Roblox responds;', 'Unknown when it does not.']),
]
for i, (number, title, lines) in enumerate(cards):
    col, row = i % 3, i // 3
    x, y = 50 + 398 * col, 238 + 218 * row
    x2, y2 = x + 382, y + 199
    d.rounded_rectangle((x, y, x2, y2), radius=22,
                        fill=(24, 21, 42, 244), outline=(83, 73, 126, 185), width=2)
    d.rounded_rectangle((x + 23, y + 23, x + 70, y + 70), radius=13,
                        fill='#363066', outline='#655bc2', width=1)
    d.text((x + 33, y + 35), number, font=font(17, True), fill='#c7b9ff')
    d.text((x + 23, y + 91), title, font=font(23, True), fill='#f4f0ff')
    for line_no, line in enumerate(lines):
        d.text((x + 23, y + 132 + line_no * 25), line, font=font(17), fill='#b8b6cf')

path = ROOT / 'site/readme-features.png'
base.convert('RGB').save(path, optimize=True)
print(path, path.stat().st_size)
