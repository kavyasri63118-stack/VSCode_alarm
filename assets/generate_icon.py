"""
Generate high-fidelity multi-resolution application icons for Code Alarm V2.
Creates:
- assets/code_alarm.ico (16, 32, 48, 64, 128, 256 px)
- assets/code_alarm.png (256x256)
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path(__file__).parent
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

def draw_bell_icon(size: int) -> Image.Image:
    # High resolution canvas for antialiasing
    scale = 4
    canvas_size = size * scale
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Background rounded circle with deep blue gradient
    margin = int(canvas_size * 0.06)
    draw.ellipse(
        [margin, margin, canvas_size - margin, canvas_size - margin],
        fill=(15, 23, 42, 255),
        outline=(59, 130, 246, 255),
        width=int(scale * 2)
    )

    # Inner subtle glow
    inner_margin = margin + int(scale * 4)
    draw.ellipse(
        [inner_margin, inner_margin, canvas_size - inner_margin, canvas_size - inner_margin],
        fill=(30, 41, 59, 255)
    )

    # 2. Draw modern bell in vibrant blue / cyan
    cx = canvas_size / 2
    cy = canvas_size / 2
    bell_w = canvas_size * 0.44
    bell_h = canvas_size * 0.44

    # Top loop
    loop_r = int(scale * 6)
    draw.ellipse([cx - loop_r, cy - bell_h*0.7 - loop_r, cx + loop_r, cy - bell_h*0.7 + loop_r], fill=(96, 165, 250, 255))

    # Bell Body
    top_w = bell_w * 0.35
    bot_w = bell_w * 0.95
    y_top = cy - bell_h * 0.55
    y_bot = cy + bell_h * 0.30

    points = [
        (cx - top_w, y_top + bell_h * 0.15),
        (cx - top_w * 0.8, y_top),
        (cx + top_w * 0.8, y_top),
        (cx + top_w, y_top + bell_h * 0.15),
        (cx + bot_w, y_bot),
        (cx - bot_w, y_bot)
    ]
    draw.polygon(points, fill=(59, 130, 246, 255))

    # Bell Base Rim
    rim_h = int(scale * 7)
    draw.rounded_rectangle(
        [cx - bot_w * 1.1, y_bot - rim_h * 0.3, cx + bot_w * 1.1, y_bot + rim_h],
        radius=int(scale * 3),
        fill=(96, 165, 250, 255)
    )

    # Clapper
    clap_r = int(scale * 9)
    draw.ellipse([cx - clap_r, y_bot + rim_h * 0.5, cx + clap_r, y_bot + rim_h * 0.5 + clap_r * 2], fill=(245, 158, 11, 255))

    # Downscale with high-quality Lanczos resampling
    return img.resize((size, size), Image.Resampling.LANCZOS)

def build_icons():
    sizes = [16, 32, 48, 64, 128, 256]
    images = [draw_bell_icon(s) for s in sizes]

    # Save PNG (256x256)
    png_path = ASSETS_DIR / "code_alarm.png"
    images[-1].save(str(png_path), format="PNG")
    print(f"✅ Generated: {png_path}")

    # Save multi-resolution ICO
    ico_path = ASSETS_DIR / "code_alarm.ico"
    images[0].save(
        str(ico_path),
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    print(f"✅ Generated multi-res ICO: {ico_path}")

if __name__ == "__main__":
    build_icons()
