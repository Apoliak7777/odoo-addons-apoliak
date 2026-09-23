import os
from PIL import Image, ImageDraw, ImageFont

dest_dir = os.path.join(os.path.dirname(__file__), "static", "description")
os.makedirs(dest_dir, exist_ok=True)

# 1. ICON (256x256)
icon_size = (256, 256)
icon = Image.new("RGBA", icon_size, (0, 0, 0, 0))
draw = ImageDraw.Draw(icon)

# Rounded rectangle background with gradient effect
for i in range(256):
    r = int(30 + (i / 256) * 40)
    g = int(27 + (i / 256) * 30)
    b = int(75 + (i / 256) * 120)
    draw.line([(0, i), (255, i)], fill=(r, g, b, 255))

# Draw border
draw.rounded_rectangle([4, 4, 251, 251], radius=48, outline=(139, 92, 246, 200), width=4)

# Draw stylized invoice sheet
draw.rounded_rectangle([60, 50, 196, 206], radius=16, fill=(255, 255, 255, 240), outline=(200, 210, 230, 255), width=2)
# Invoice lines
draw.rounded_rectangle([80, 80, 140, 88], radius=4, fill=(100, 116, 139, 255))
draw.rounded_rectangle([80, 105, 176, 113], radius=4, fill=(148, 163, 184, 255))
draw.rounded_rectangle([80, 125, 160, 133], radius=4, fill=(148, 163, 184, 255))
draw.rounded_rectangle([80, 145, 176, 153], radius=4, fill=(148, 163, 184, 255))

# AI Sparkle / Magic badge
draw.ellipse([145, 145, 215, 215], fill=(16, 185, 129, 255), outline=(255, 255, 255, 255), width=3)
# Star spark inside
draw.polygon([(180, 155), (185, 175), (205, 180), (185, 185), (180, 205), (175, 185), (155, 180), (175, 175)], fill=(255, 255, 255, 255))

icon_path = os.path.join(dest_dir, "icon.png")
icon.save(icon_path, "PNG")
print(f"Icon saved to {icon_path}")

# 2. BANNER (1200x630)
banner = Image.new("RGBA", (1200, 630), (15, 17, 23, 255))
b_draw = ImageDraw.Draw(banner)

# Gradient background
for y in range(630):
    r = int(15 + (y / 630) * 20)
    g = int(17 + (y / 630) * 15)
    b = int(28 + (y / 630) * 45)
    b_draw.line([(0, y), (1199, y)], fill=(r, g, b, 255))

# Accent glow
for rad in range(300, 0, -5):
    alpha = int((300 - rad) / 300 * 40)
    b_draw.ellipse([600 - rad, 100 - rad, 600 + rad, 100 + rad], fill=(139, 92, 246, alpha))

# Framing & Badges
b_draw.rounded_rectangle([60, 50, 360, 95], radius=22, fill=(139, 92, 246, 50), outline=(139, 92, 246, 150), width=2)

# Text using default font or basic drawing
b_draw.text((85, 62), "ODOO 16 / 17 / 18 / 19 COMPATIBLE", fill=(196, 181, 253, 255))

# Title box
b_draw.text((60, 130), "AI Vendor Bill & Invoice Extractor", fill=(255, 255, 255, 255))
b_draw.text((60, 180), "Zero-Cost OCR - No Expensive Odoo IAP Credits", fill=(16, 185, 129, 255))
b_draw.text((60, 230), "Extract supplier, dates, amounts & line items into Odoo in 3 seconds.", fill=(156, 163, 175, 255))

# Visual cards in banner
card_y = 300
b_draw.rounded_rectangle([60, card_y, 400, card_y + 260], radius=16, fill=(24, 29, 43, 255), outline=(255, 255, 255, 25), width=2)
b_draw.text((85, card_y + 30), "AUTO PARTNER MATCH", fill=(139, 92, 246, 255))
b_draw.text((85, card_y + 70), "• Matches by VAT / Tax ID / ICO\n• Auto-creates missing vendor\n• Multi-country validation", fill=(209, 213, 219, 255))

b_draw.rounded_rectangle([430, card_y, 770, card_y + 260], radius=16, fill=(24, 29, 43, 255), outline=(255, 255, 255, 25), width=2)
b_draw.text((455, card_y + 30), "LINE ITEMS & TAXES", fill=(16, 185, 129, 255))
b_draw.text((455, card_y + 70), "• Full item descriptions\n• Quantities & unit prices\n• Automatic tax calculation\n• Invoice & due date detection", fill=(209, 213, 219, 255))

b_draw.rounded_rectangle([800, card_y, 1140, card_y + 260], radius=16, fill=(24, 29, 43, 255), outline=(255, 255, 255, 25), width=2)
b_draw.text((825, card_y + 30), "MASSIVE ROI SAVINGS", fill=(245, 158, 11, 255))
b_draw.text((825, card_y + 70), "• Odoo OCR: ~0.20 EUR / bill\n• Our AI: <0.001 EUR / bill\n• Saves 500+ EUR yearly\n• Works with Gemini & OpenAI", fill=(209, 213, 219, 255))

banner_path = os.path.join(dest_dir, "banner.png")
banner.save(banner_path, "PNG")
print(f"Banner saved to {banner_path}")
