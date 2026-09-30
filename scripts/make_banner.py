"""Rebuild the README/social banner from our real empty-state app capture.
Requires Pillow. Does not use any account data or external images.
"""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
W, H = 1280, 640
FONT_DIR = Path('/usr/share/fonts/truetype/liberation')

def font(size, bold=False):
    name = 'LiberationSans-Bold.ttf' if bold else 'LiberationSans-Regular.ttf'
    path = FONT_DIR / name
    if not path.exists():
        path = Path('/usr/share/fonts/truetype/dejavu') / ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')
    return ImageFont.truetype(str(path), size)

base = Image.new('RGB', (W, H))
px = base.load()
for y in range(H):
    for x in range(W):
        t = y / H
        # Extremely subtle near-black gradient: violet toward the top right.
        v = max(0, 1 - math.hypot((x - 955) / 950, (y - 135) / 750))
        px[x, y] = (round(7 + 7*t + 12*v), round(7 + 4*t + 5*v), round(17 + 11*t + 25*v))

# Ambient glow is a brand backdrop, not a mock desktop or application grid.
glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
g = ImageDraw.Draw(glow)
g.ellipse((720, -390, 1570, 460), fill=(115, 72, 247, 120))
g.ellipse((-470, 180, 370, 1010), fill=(74, 66, 191, 75))
base = Image.alpha_composite(base.convert('RGBA'), glow.filter(ImageFilter.GaussianBlur(130)))

# The real UI, shown directly; its header and border are part of the window, not a mock frame.
shot = Image.open(ROOT / 'site/app-preview.webp').convert('RGBA')
shot.thumbnail((740, 530), Image.Resampling.LANCZOS)
base.alpha_composite(shot, (650, 136))

# Calm left-side hierarchy; text deliberately stays outside the UI image.
d = ImageDraw.Draw(base)
for yy in range(84, 152):
    t = (yy - 84) / 68
    d.line((77, yy, 145, yy), fill=(round(99 + 69*t), round(102 - 17*t), round(241 + 6*t), 255))
d.rounded_rectangle((77, 84, 146, 153), radius=18, fill=(101, 92, 235, 255))
d.text((93, 87), 'Z', font=font(54, True), fill='#ffffff')
d.text((167, 108), 'ZENRBXMANAGER', font=font(18, True), fill='#d8d5ff', stroke_width=0)
d.text((77, 222), 'Your accounts.', font=font(68, True), fill='#f7f7ff')
d.text((77, 294), 'One place.', font=font(68, True), fill='#f7f7ff')
d.rounded_rectangle((77, 389, 155, 395), radius=3, fill='#7b72ff')
d.text((77, 428), 'Keep track of your Roblox accounts,', font=font(24), fill='#b9bfd2')
d.text((77, 462), 'then get back to the game.', font=font(24), fill='#b9bfd2')
# Understated, readable chips.
d.rounded_rectangle((77, 550, 257, 586), radius=18, fill=(32, 29, 55, 255), outline=(84, 78, 123, 255), width=1)
d.text((95, 559), 'WINDOWS 10 / 11', font=font(14, True), fill='#c4b9fe')
for left, right, text in [(270, 427, 'OPEN SOURCE'), (440, 623, 'LOCAL STORAGE')]:
    d.rounded_rectangle((left, 550, right, 586), radius=18, fill=(32, 29, 55, 255), outline=(84, 78, 123, 255), width=1)
    d.text((left + 17, 559), text, font=font(14, True), fill='#c4b9fe')

output = ROOT / 'site/og.png'
base.convert('RGB').save(output, optimize=True)
print(output, output.stat().st_size)
