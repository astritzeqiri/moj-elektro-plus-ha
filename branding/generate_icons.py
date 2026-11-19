"""Generate the brand icons in custom_components/mojelektro_plus/brand/.

Run: python branding/generate_icons.py   (needs Pillow)
Original artwork: a lightning bolt over a 15-minute bar chart.
"""

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "custom_components" / "mojelektro_plus" / "brand"


def icon(size: int, dark: bool) -> Image.Image:
    scale = size / 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bg = (32, 46, 66, 255) if dark else (233, 242, 251, 255)
    bar = (88, 166, 230, 255) if dark else (36, 112, 186, 255)
    bolt = (255, 196, 61, 255)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(56 * scale), fill=bg)
    heights = [70, 110, 90, 150, 120, 175]
    for i, h in enumerate(heights):
        x0 = (36 + i * 32) * scale
        d.rounded_rectangle(
            [x0, (220 - h) * scale, x0 + 22 * scale, 220 * scale], radius=int(5 * scale), fill=bar
        )
    pts = [(150, 22), (92, 132), (130, 132), (106, 236), (176, 108), (136, 108), (164, 22)]
    d.polygon([(x * scale, y * scale) for x, y in pts], fill=bolt)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for dark, prefix in ((False, ""), (True, "dark_")):
        icon(256, dark).save(OUT / f"{prefix}icon.png", optimize=True)
        icon(512, dark).save(OUT / f"{prefix}icon@2x.png", optimize=True)


if __name__ == "__main__":
    main()
