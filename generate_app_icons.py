import os
import math
from PIL import Image, ImageDraw, ImageFilter

SIZE = 1024
img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# 1. Background Rounded Squircle with Deep Slate / Navy Gradient
# Draw radial background
bg = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
bg_draw = ImageDraw.Draw(bg)

# Center and radius for background squircle
center = SIZE // 2
margin = 40
rect = [margin, margin, SIZE - margin, SIZE - margin]
radius = 220

# Draw subtle outer neon glow
for offset, alpha in [(30, 20), (20, 35), (10, 60), (4, 120)]:
    bg_draw.rounded_rectangle(
        [margin - offset, margin - offset, SIZE - margin + offset, SIZE - margin + offset],
        radius=radius + offset,
        outline=(56, 189, 248, alpha),
        width=offset
    )

# Base background gradient fill (Radial from #1e293b to #090d16)
for r in range(SIZE // 2 - margin, 0, -2):
    ratio = r / (SIZE // 2 - margin)
    # Lerp from #0f172a (outer) to #1e3a5f (inner)
    red = int(15 * (1 - ratio) + 30 * ratio)
    green = int(23 * (1 - ratio) + 58 * ratio)
    blue = int(42 * (1 - ratio) + 95 * ratio)
    # Mask to rounded rect
    # We will do a full fill and mask it
base_layer = Image.new("RGBA", (SIZE, SIZE), (15, 23, 42, 255))
base_draw = ImageDraw.Draw(base_layer)

# Radial gradient on base_layer
for y in range(SIZE):
    for x in range(0, SIZE, 4):
        dx = x - center
        dy = y - center
        dist = math.sqrt(dx*dx + dy*dy)
        if dist < SIZE // 2:
            t = dist / (SIZE // 2)
            c = int(35 * (1 - t) + 12 * t), int(60 * (1 - t) + 20 * t), int(105 * (1 - t) + 36 * t)
            base_draw.line([(x, y), (x + 3, y)], fill=c + (255,))

# Create rounded mask
mask = Image.new("L", (SIZE, SIZE), 0)
mask_draw = ImageDraw.Draw(mask)
mask_draw.rounded_rectangle(rect, radius=radius, fill=255)

# Composite base onto img with mask
img.paste(base_layer, (0, 0), mask)

# 2. Draw Sleek Modern Radar Rings & Crosshairs
radar_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
radar_draw = ImageDraw.Draw(radar_layer)

# Concentric Radar Rings
for ring_r in [140, 240, 340, 420]:
    radar_draw.ellipse(
        [center - ring_r, center - ring_r, center + ring_r, center + ring_r],
        outline=(56, 189, 248, 65 if ring_r < 400 else 110),
        width=4 if ring_r < 400 else 6
    )

# Radar crosshair grid lines
radar_draw.line([(center, center - 420), (center, center + 420)], fill=(56, 189, 248, 55), width=3)
radar_draw.line([(center - 420, center), (center + 420, center)], fill=(56, 189, 248, 55), width=3)
# 45-degree dotted/faint diagonals
radar_draw.line([(center - 297, center - 297), (center + 297, center + 297)], fill=(56, 189, 248, 30), width=2)
radar_draw.line([(center - 297, center + 297), (center + 297, center - 297)], fill=(56, 189, 248, 30), width=2)

# Radar sweep gradient arc (60 degree glowing sweep)
sweep = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
sweep_draw = ImageDraw.Draw(sweep)
sweep_draw.pieslice([center - 420, center - 420, center + 420, center + 420], -60, 0, fill=(2, 132, 199, 45))
sweep_draw.pieslice([center - 420, center - 420, center + 420, center + 420], -30, 0, fill=(56, 189, 248, 65))
sweep_draw.line([(center, center), (center + 420, center)], fill=(56, 189, 248, 220), width=5)

img = Image.alpha_composite(img, radar_layer)
img = Image.alpha_composite(img, sweep)

# 3. Center Emblem: Medical Cross blended with Botanical Homeopathic Sprout
center_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
c_draw = ImageDraw.Draw(center_layer)

# Glowing Medical Cross
cw = 75   # half width of cross arm
cl = 210  # length from center

# Cross shadow / outer glow
c_draw.rounded_rectangle([center - cw - 12, center - cl - 12, center + cw + 12, center + cl + 12], radius=24, fill=(14, 165, 233, 100))
c_draw.rounded_rectangle([center - cl - 12, center - cw - 12, center + cl + 12, center + cw + 12], radius=24, fill=(14, 165, 233, 100))

# Cross body (Bright Electric Cyan / Emerald Gradient)
c_draw.rounded_rectangle([center - cw, center - cl, center + cw, center + cl], radius=20, fill=(240, 253, 250, 255))
c_draw.rounded_rectangle([center - cl, center - cw, center + cl, center + cw], radius=20, fill=(240, 253, 250, 255))

# Center Botanical Sprout Leaf (Homeopathy Symbolism in Emerald Green)
leaf = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
l_draw = ImageDraw.Draw(leaf)

# Draw central emerald green diamond / leaf emblem
points = [
    (center, center - 130),       # Top
    (center + 95, center),        # Right
    (center, center + 130),       # Bottom
    (center - 95, center)         # Left
]
l_draw.polygon(points, fill=(16, 185, 129, 240))

# Inner leaf highlight
inner_leaf = [
    (center, center - 100),
    (center + 65, center),
    (center, center + 100),
    (center - 65, center)
]
l_draw.polygon(inner_leaf, fill=(52, 211, 153, 255))

# Leaf vein
l_draw.line([(center, center - 105), (center, center + 105)], fill=(255, 255, 255, 230), width=6)
l_draw.line([(center, center - 40), (center + 35, center - 70)], fill=(255, 255, 255, 200), width=4)
l_draw.line([(center, center + 40), (center - 35, center + 10)], fill=(255, 255, 255, 200), width=4)
l_draw.line([(center, center), (center + 35, center - 30)], fill=(255, 255, 255, 200), width=4)

# Compass points dots around the cross
for angle in [0, 90, 180, 270]:
    rad = math.radians(angle)
    px = center + int(290 * math.cos(rad))
    py = center + int(290 * math.sin(rad))
    l_draw.ellipse([px - 14, py - 14, px + 14, py + 14], fill=(56, 189, 248, 255), outline=(255, 255, 255, 255), width=3)

center_layer = Image.alpha_composite(center_layer, leaf)
img = Image.alpha_composite(img, center_layer)

# Border highlight ring around the squircle
border_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
b_draw = ImageDraw.Draw(border_layer)
b_draw.rounded_rectangle(rect, radius=radius, outline=(56, 189, 248, 220), width=8)
img = Image.alpha_composite(img, border_layer)

# Save Master Icon
res_dir = r"L:\Project\OpenRadar\android\app\src\main\res"
os.makedirs(res_dir, exist_ok=True)
master_path = os.path.join(res_dir, "icon_master_1024.png")
img.save(master_path, "PNG")
print(f"Saved master icon to {master_path}")

# Generate Android mipmap sizes
sizes = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192
}

# Circular mask for round icons
round_mask = Image.new("L", (SIZE, SIZE), 0)
rm_draw = ImageDraw.Draw(round_mask)
rm_draw.ellipse([margin - 10, margin - 10, SIZE - margin + 10, SIZE - margin + 10], fill=255)
round_img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
round_img.paste(img, (0, 0), round_mask)

# Circular border
rb_draw = ImageDraw.Draw(round_img)
rb_draw.ellipse([margin - 10, margin - 10, SIZE - margin + 10, SIZE - margin + 10], outline=(56, 189, 248, 240), width=10)

for folder, s in sizes.items():
    f_path = os.path.join(res_dir, folder)
    os.makedirs(f_path, exist_ok=True)
    
    # Square / squircle icon
    icon_resized = img.resize((s, s), Image.LANCZOS)
    icon_resized.save(os.path.join(f_path, "ic_launcher.png"), "PNG")
    
    # Round icon
    round_resized = round_img.resize((s, s), Image.LANCZOS)
    round_resized.save(os.path.join(f_path, "ic_launcher_round.png"), "PNG")
    print(f"Generated {folder}: {s}x{s} (standard & round)")

print("All Android launcher icons generated successfully!")
