"""AI CLIPPING STUDIO: YouTube Channel Branding & Banner Compositor.
Creates compliant 2560x1440 YouTube Channel Art with safe-zone typography and social handles.
Safe Zone: 1546 x 423 pixels in the exact center (X: 507..2053, Y: 508..931).
"""
import os
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BRAND_DIR = Path("assets/branding")
BRAND_DIR.mkdir(parents=True, exist_ok=True)

FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_IMPACT = r"C:\Windows\Fonts\impact.ttf"
FONT_REGULAR = r"C:\Windows\Fonts\tahoma.ttf"

def draw_glow_text(draw, position, text, font, text_color, glow_color, glow_radius=8):
    """Draw text with a soft radial neon glow behind it."""
    x, y = position
    for dx in range(-glow_radius, glow_radius + 1, 2):
        for dy in range(-glow_radius, glow_radius + 1, 2):
            if dx*dx + dy*dy <= glow_radius*glow_radius:
                draw.text((x + dx, y + dy), text, font=font, fill=glow_color)
    draw.text((x, y), text, font=font, fill=text_color)

def build_profile_avatar(base_bg_path=None, output_path="assets/branding/di7xu_youtube_profile.png"):
    """Build high-resolution 1024x1024 avatar logo."""
    size = 1024
    if base_bg_path and os.path.exists(base_bg_path):
        img = Image.open(base_bg_path).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    else:
        img = Image.new("RGBA", (size, size), (12, 10, 26, 255))
        draw_bg = ImageDraw.Draw(img)
        # Gradient background
        for i in range(size):
            r = int(14 + (i / size) * 20)
            g = int(8 + (i / size) * 10)
            b = int(35 + (i / size) * 45)
            draw_bg.line([(0, i), (size, i)], fill=(r, g, b, 255))

    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Circular border with neon cyan / magenta accents
    cx, cy, radius = size // 2, size // 2, 420
    for r_offset, alpha in [(6, 40), (4, 90), (2, 180), (0, 255)]:
        draw.ellipse([cx - radius - r_offset, cy - radius - r_offset,
                      cx + radius + r_offset, cy + radius + r_offset],
                     outline=(0, 220, 255, alpha), width=3)

    # Stylized logo text "di7xu"
    try:
        font_main = ImageFont.truetype(FONT_IMPACT, 220)
        font_sub = ImageFont.truetype(FONT_BOLD, 48)
    except Exception:
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    text_main = "di7xu"
    bbox = draw.textbbox((0, 0), text_main, font=font_main)
    w_main = bbox[2] - bbox[0]
    h_main = bbox[3] - bbox[1]
    pos_x = (size - w_main) // 2
    pos_y = cy - h_main // 2 - 20

    # Glow effect
    draw_glow_text(draw, (pos_x, pos_y), text_main, font_main,
                   text_color=(255, 255, 255, 255),
                   glow_color=(0, 230, 255, 120),
                   glow_radius=12)

    # Sub badge "OFFICIAL"
    text_sub = "OFFICIAL CHANNEL"
    bbox_sub = draw.textbbox((0, 0), text_sub, font=font_sub)
    w_sub = bbox_sub[2] - bbox_sub[0]
    pos_sub_x = (size - w_sub) // 2
    pos_sub_y = pos_y + h_main + 60
    
    # Sub badge pill
    pad_x, pad_y = 25, 8
    draw.rounded_rectangle([pos_sub_x - pad_x, pos_sub_y - pad_y,
                            pos_sub_x + w_sub + pad_x, pos_sub_y + 40 + pad_y],
                           radius=18, fill=(255, 0, 110, 200), outline=(255, 255, 255, 220), width=2)
    draw.text((pos_sub_x, pos_sub_y), text_sub, font=font_sub, fill=(255, 255, 255, 255))

    final = Image.alpha_composite(img, overlay)
    final.save(output_path, "PNG")
    print(f"✅ Generated Profile Avatar: {output_path}")
    return output_path

def build_youtube_banner(base_bg_path=None, output_path="assets/branding/di7xu_youtube_banner_2560x1440.png"):
    """Build full-size 2560x1440 banner with YouTube safe-zone typography."""
    width, height = 2560, 1440
    if base_bg_path and os.path.exists(base_bg_path):
        img = Image.open(base_bg_path).convert("RGBA").resize((width, height), Image.Resampling.LANCZOS)
    else:
        img = Image.new("RGBA", (width, height), (15, 12, 30, 255))
        draw_bg = ImageDraw.Draw(img)
        # Deep cyberpunk gradient
        for i in range(height):
            ratio = i / height
            r = int(16 + ratio * 28)
            g = int(8 + ratio * 15)
            b = int(38 + ratio * 60)
            draw_bg.line([(0, i), (width, i)], fill=(r, g, b, 255))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Center Coordinates & Safe Area
    # Safe area: X: 507..2053, Y: 508..931 (Center: X=1280, Y=720)
    cx, cy = 1280, 720

    # Ambient glow in center safe area
    glow_box = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_box)
    glow_draw.ellipse([cx - 500, cy - 180, cx + 500, cy + 180], fill=(0, 200, 255, 35))
    glow_draw.ellipse([cx - 400, cy - 120, cx + 400, cy + 120], fill=(255, 0, 120, 30))
    glow_box = glow_box.filter(ImageFilter.GaussianBlur(60))
    overlay = Image.alpha_composite(overlay, glow_box)
    draw = ImageDraw.Draw(overlay)

    # Fonts
    try:
        font_title = ImageFont.truetype(FONT_IMPACT, 150)
        font_tagline = ImageFont.truetype(FONT_BOLD, 36)
        font_social = ImageFont.truetype(FONT_BOLD, 32)
    except Exception:
        font_title = ImageFont.load_default()
        font_tagline = ImageFont.load_default()
        font_social = ImageFont.load_default()

    # 1. Main Title "DI7XU"
    title_text = "DI7XU"
    t_bbox = draw.textbbox((0, 0), title_text, font=font_title)
    tw, th = t_bbox[2] - t_bbox[0], t_bbox[3] - t_bbox[1]
    title_x = cx - tw // 2
    title_y = cy - 110

    draw_glow_text(draw, (title_x, title_y), title_text, font_title,
                   text_color=(255, 255, 255, 255),
                   glow_color=(0, 220, 255, 140),
                   glow_radius=14)

    # 2. Tagline
    tagline = "DAILY VIRAL CLIPS  •  GAMING HIGHLIGHTS  •  ENTERTAINMENT"
    tag_bbox = draw.textbbox((0, 0), tagline, font=font_tagline)
    tag_w = tag_bbox[2] - tag_bbox[0]
    tag_x = cx - tag_w // 2
    tag_y = title_y + th + 35

    draw_glow_text(draw, (tag_x, tag_y), tagline, font_tagline,
                   text_color=(235, 245, 255, 255),
                   glow_color=(255, 0, 110, 100),
                   glow_radius=6)

    # 3. Social Handles Pill: YouTube • Instagram • GitHub (@di7xu)
    social_text = "  YouTube  |  Instagram  |  GitHub  :  @di7xu  "
    soc_bbox = draw.textbbox((0, 0), social_text, font=font_social)
    soc_w = soc_bbox[2] - soc_bbox[0]
    soc_h = soc_bbox[3] - soc_bbox[1]
    soc_x = cx - soc_w // 2
    soc_y = tag_y + 60

    # Draw sleek dark pill behind social handle
    pad_h, pad_v = 36, 12
    draw.rounded_rectangle([soc_x - pad_h, soc_y - pad_v,
                            soc_x + soc_w + pad_h, soc_y + soc_h + pad_v],
                           radius=20,
                           fill=(12, 10, 28, 220),
                           outline=(0, 230, 255, 230),
                           width=2)
    draw.text((soc_x, soc_y), social_text, font=font_social, fill=(255, 255, 255, 255))

    final = Image.alpha_composite(img, overlay)
    final.save(output_path, "PNG")
    print(f"✅ Generated YouTube Banner: {output_path}")
    return output_path

if __name__ == "__main__":
    build_profile_avatar()
    build_youtube_banner()
