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

# Ambient glow sits BEHIND the grid and content.
glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
g = ImageDraw.Draw(glow)
g.ellipse((720, -390, 1570, 460), fill=(115, 72, 247, 120))
g.ellipse((-470, 180, 370, 1010), fill=(74, 66, 191, 75))
glow = glow.filter(ImageFilter.GaussianBlur(130))
base = Image.alpha_composite(base.convert('RGBA'), glow)
grid = Image.new('RGBA', (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(grid)
for x in range(0, W, 64): gd.line((x, 0, x, H), fill=(110, 105, 176, 13))
for y in range(0, H, 64): gd.line((0, y, W, y), fill=(110, 105, 176, 13))
base = Image.alpha_composite(base, grid)

# Real interface capture, with soft frame and shadow.
shot = Image.open(ROOT / 'site/app-preview.webp').convert('RGB')
shot = shot.crop((80, 105, 1930, 1190))
shot.thumbnail((695, 420), Image.Resampling.LANCZOS)
frame = Image.new('RGBA', (shot.width + 24, shot.height + 24), (0, 0, 0, 0))
fd = ImageDraw.Draw(frame)
fd.rounded_rectangle((0, 0, frame.width - 1, frame.height - 1), radius=19,
                     fill=(28, 25, 53, 255), outline=(119, 102, 221, 145), width=2)
frame.paste(shot, (12, 12))
frame = frame.rotate(5, resample=Image.Resampling.BICUBIC, expand=True)
shadow = Image.new('RGBA', frame.size, (0, 0, 0, 0))
shadow.putalpha(frame.getchannel('A'))
shadow = shadow.filter(ImageFilter.GaussianBlur(26))
# Right-hand device breaks the frame edge deliberately for depth.
x, y = 667, 142
black_shadow = Image.new('RGBA', frame.size, (0, 0, 0, 0))
black_shadow.paste((4, 2, 13, 185), (0, 0, frame.width, frame.height), shadow.getchannel('A'))
base.alpha_composite(black_shadow, (x + 18, y + 28))
base.alpha_composite(frame, (x, y))

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
