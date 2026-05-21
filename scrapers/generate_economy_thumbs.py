"""
Generate economy browser thumbnails for /franchise/economics.

Produces public/assets/economy-thumbs/{title_id}.png (400×240 px) for every
economy that has an entry in the TITLE_IDS list.  Design is 100% data-driven:
  - Background colour from era_badge_color
  - Diagonal accent strips from node color_tokens
  - Title short name + complexity score rendered as text

No screenshots. No external fonts needed — uses PIL's default monospace-ish
font for the small label and falls back gracefully when system fonts are absent.

Run: python3 scrapers/generate_economy_thumbs.py
"""

import json
import math
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not found.  Run:  pip install pillow")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT  = Path(__file__).resolve().parent.parent
DATA_FILE  = REPO_ROOT / "data" / "franchise" / "economy-models.json"
OUT_DIR    = REPO_ROOT / "public" / "assets" / "economy-thumbs"

# Only generate thumbs for the five titles used by the economics browser.
TITLE_IDS = {"gta-vc", "gta-sa", "gta-5", "gta-online", "gta-6"}

# Thumbnail dimensions
W, H = 400, 240

# ---------------------------------------------------------------------------
# era_badge_color → (background_hex, primary_strip_hex, secondary_strip_hex)
# ---------------------------------------------------------------------------
ERA_PALETTE: dict[str, tuple[str, str, str]] = {
    "zinc":  ("#0e0e11", "#3f3f46", "#27272a"),
    "amber": ("#12100a", "#f59e0b", "#b45309"),
    "red":   ("#110a0a", "#ef4444", "#991b1b"),
    "green": ("#090f09", "#22c55e", "#15803d"),
    "teal":  ("#071210", "#0d9488", "#0f766e"),
    "gold":  ("#120f07", "#fbbf24", "#d97706"),
}

# color_token → strip hex (used for the thin accent strips from node tokens)
NODE_COLORS: dict[str, str] = {
    "amber":  "#f59e0b",
    "orange": "#f97316",
    "teal":   "#0d9488",
    "green":  "#22c55e",
    "purple": "#a78bfa",
    "blue":   "#818cf8",
    "zinc":   "#52525b",
    "gold":   "#fbbf24",
    "yellow": "#d97706",
    "red":    "#ef4444",
    "indigo": "#6366f1",
}


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgba(hex_color: str, alpha: int) -> tuple[int, int, int, int]:
    r, g, b = hex_to_rgb(hex_color)
    return r, g, b, alpha


def draw_diagonal_strip(
    draw: ImageDraw.ImageDraw,
    img_w: int,
    img_h: int,
    x_offset: int,
    strip_width: int,
    color: tuple[int, int, int, int],
    angle_deg: float = 25.0,
) -> None:
    """Draw a single parallelogram (diagonal strip) onto the image."""
    tan_a = math.tan(math.radians(angle_deg))
    vertical_shift = int(img_h * tan_a)
    pts = [
        (x_offset - vertical_shift, 0),
        (x_offset - vertical_shift + strip_width, 0),
        (x_offset + strip_width, img_h),
        (x_offset, img_h),
    ]
    draw.polygon(pts, fill=color)


def try_load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try common monospace fonts in priority order; fall back to PIL default."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
        "/usr/share/fonts/truetype/ubuntu/UbuntuMono-B.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_thumb(economy: dict) -> Path:
    title_id     = economy["title_id"]
    short        = economy["short"]
    badge_color  = economy.get("era_badge_color", "zinc")
    complexity   = economy.get("complexity_score", 0)
    era_label    = economy.get("era_label", "")
    economy_type = economy.get("economy_type", "")

    bg_hex, primary_hex, secondary_hex = ERA_PALETTE.get(badge_color, ERA_PALETTE["zinc"])

    # Collect unique node color tokens (preserve order, skip duplicates)
    node_tokens: list[str] = []
    seen: set[str] = set()
    for node in economy.get("nodes", []):
        tok = node.get("color_token", "zinc")
        if tok not in seen:
            seen.add(tok)
            node_tokens.append(tok)

    # Build image with RGBA so we can composite translucent strips
    img = Image.new("RGBA", (W, H), (*hex_to_rgb(bg_hex), 255))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)

    # --- Background gradient emulation: subtle lighter right half ---
    for x in range(W):
        alpha = int(8 * (x / W))
        draw_ov.line([(x, 0), (x, H)], fill=(255, 255, 255, alpha))

    # --- Wide primary diagonal ---
    draw_diagonal_strip(draw_ov, W, H, x_offset=W - 80, strip_width=120,
                        color=rgba(primary_hex, 22))

    # --- Secondary diagonal ---
    draw_diagonal_strip(draw_ov, W, H, x_offset=W + 20, strip_width=60,
                        color=rgba(secondary_hex, 18))

    # --- Thin accent strips from node tokens (right side) ---
    strip_x = W + 60
    for tok in reversed(node_tokens[:5]):  # up to 5 strips, rightmost first
        hex_col = NODE_COLORS.get(tok, "#52525b")
        draw_diagonal_strip(draw_ov, W, H, x_offset=strip_x, strip_width=14,
                            color=rgba(hex_col, 45))
        strip_x -= 22

    # --- Left-side bright accent edge ---
    draw_diagonal_strip(draw_ov, W, H, x_offset=-80, strip_width=90,
                        color=rgba(primary_hex, 10))

    # Composite overlay onto background
    img = Image.alpha_composite(img, overlay)

    # --- Dark vignette on left (text readability) ---
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vignette)
    for x in range(220):
        alpha = int(90 * (1 - x / 220))
        vdraw.line([(x, 0), (x, H)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img, vignette)

    # --- Thin top border in primary color ---
    border = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(border)
    bdraw.line([(0, 0), (W, 0)], fill=(*hex_to_rgb(primary_hex), 160), width=2)
    img = Image.alpha_composite(img, border)

    # --- Text ---
    draw_txt = ImageDraw.Draw(img)

    font_title = try_load_font(28)
    font_label = try_load_font(11)
    font_score = try_load_font(42)

    # Complexity score — large, lower-right, semi-transparent
    score_str = str(complexity)
    score_color = (*hex_to_rgb(primary_hex), 50)
    try:
        bbox = draw_txt.textbbox((0, 0), score_str, font=font_score)
        sw = bbox[2] - bbox[0]
        sh = bbox[3] - bbox[1]
    except AttributeError:
        sw, sh = draw_txt.textsize(score_str, font=font_score)  # type: ignore[attr-defined]
    draw_txt.text((W - sw - 18, H - sh - 12), score_str, font=font_score, fill=score_color)

    # Title name — main label
    title_color = (*hex_to_rgb(primary_hex), 230)
    draw_txt.text((20, 24), short, font=font_title, fill=title_color)

    # Economy type — subtitle, two lines max
    sub_lines = _wrap(economy_type, 34)[:2]
    y_sub = 62
    for line in sub_lines:
        draw_txt.text((20, y_sub), line, font=font_label, fill=(180, 180, 185, 200))
        y_sub += 16

    # Era label — smallest, bottom-left
    era_short = era_label.split(" — ")[0] if " — " in era_label else era_label
    era_short = era_short[:38]
    draw_txt.text((20, H - 22), era_short, font=font_label,
                  fill=(*hex_to_rgb(primary_hex), 120))

    # --- Horizontal rule above era label ---
    rdraw = ImageDraw.Draw(img)
    rdraw.line([(20, H - 29), (180, H - 29)], fill=(*hex_to_rgb(primary_hex), 40), width=1)

    # Save as PNG (convert RGBA → RGB first to keep file sizes small)
    out_path = OUT_DIR / f"{title_id}.png"
    img.convert("RGB").save(out_path, "PNG", optimize=True)
    return out_path


def _wrap(text: str, width: int) -> list[str]:
    """Naïve word-wrap."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for w in words:
        if len(current) + len(w) + 1 <= width:
            current = (current + " " + w).strip()
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines or [""]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(DATA_FILE) as fh:
        data = json.load(fh)

    generated = []
    for economy in data["economies"]:
        if economy["title_id"] in TITLE_IDS:
            path = generate_thumb(economy)
            generated.append(path)
            print(f"  ✓ {path.name}  ({economy['short']}  complexity={economy['complexity_score']})")

    print(f"\nGenerated {len(generated)} thumbnail(s) → {OUT_DIR}")


if __name__ == "__main__":
    main()
