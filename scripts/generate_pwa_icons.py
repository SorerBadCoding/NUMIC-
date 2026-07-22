"""Generate PWA icons from static/img/logo.png.

Run whenever the logo changes:
    .venv/Scripts/python scripts/generate_pwa_icons.py

Produces, all in static/img/:
    icon-192.png            192x192, for the manifest "any" purpose icon
    icon-512.png             512x512, for the manifest "any" purpose icon
    icon-512-maskable.png     512x512, logo scaled into the ~80% safe zone on a
                              white backdrop so OS icon masks (circle/squircle/
                              rounded-square) never clip the logo
    apple-touch-icon.png     180x180, full-bleed square (no transparency) —
                              iOS applies its own rounded-corner mask on top
"""

from pathlib import Path

from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
SRC = BASE_DIR / "static" / "img" / "logo.png"
OUT_DIR = BASE_DIR / "static" / "img"

# The source logo is already a clean square (white background, centered
# circular badge), so a plain high-quality resize preserves it with no
# clipping for the regular and Apple touch icons.
REGULAR_SIZES = {
    "icon-192.png": 192,
    "icon-512.png": 512,
    "apple-touch-icon.png": 180,
}

# Maskable icons: OS icon masks (circle, squircle, rounded square, ...) can
# crop anything outside a centered ~80%-diameter safe zone. Scale the logo
# down to sit inside that zone, padded with the same white the logo already
# uses so the padding is seamless rather than a visible box behind a circle.
MASKABLE_SIZE = 512
MASKABLE_LOGO_SCALE = 0.72  # logo diameter as a fraction of the canvas
MASKABLE_BG = (255, 255, 255)


def main():
    if not SRC.exists():
        raise SystemExit(f"Source logo not found: {SRC}")

    logo = Image.open(SRC).convert("RGB")

    for filename, size in REGULAR_SIZES.items():
        resized = logo.resize((size, size), Image.LANCZOS)
        resized.save(OUT_DIR / filename, "PNG")
        print(f"wrote {filename} ({size}x{size})")

    canvas = Image.new("RGB", (MASKABLE_SIZE, MASKABLE_SIZE), MASKABLE_BG)
    logo_size = round(MASKABLE_SIZE * MASKABLE_LOGO_SCALE)
    resized_logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
    offset = ((MASKABLE_SIZE - logo_size) // 2, (MASKABLE_SIZE - logo_size) // 2)
    canvas.paste(resized_logo, offset)
    canvas.save(OUT_DIR / "icon-512-maskable.png", "PNG")
    print(f"wrote icon-512-maskable.png ({MASKABLE_SIZE}x{MASKABLE_SIZE}, logo at {logo_size}x{logo_size})")


if __name__ == "__main__":
    main()
