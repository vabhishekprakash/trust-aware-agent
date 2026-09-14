"""Record the demo GIF: one take, no retries for polish.

Usage:
    python scripts/demo/record_gif.py [--url http://127.0.0.1:8000] [--out docs/assets/demo.gif]

Needs the dashboard running (scripts/serve.py) with Ollama up. Drives the
page with Playwright, takes screenshots at fixed moments, and assembles
them into a GIF with Pillow. The waits are cut: each live question takes
about 50 seconds, so the GIF holds a frame while the answer arrives and is
captioned as speeded up rather than faking latency. Content, under 15
seconds: one confident answer with its capped number and the sentence
about certainty, one ESCALATE with its hand-off, and the explanation
panel open showing the family breakdown.
"""

import argparse
import io
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
CONFIDENT = "What is AS9100 and which industry was it created for?"
ESCALATED = "Which NASA requirements document must software development follow when the technical team makes or codes a product?"


def caption(png: bytes, text: str) -> Image.Image:
    img = Image.open(io.BytesIO(png)).convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size
    draw.rectangle([0, h - 34, w, h], fill=(28, 28, 28))
    draw.text((12, h - 26), text, fill=(255, 255, 255))
    return img


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--out", default=str(ROOT / "docs" / "assets" / "demo.gif"))
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=720)
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright

    frames: list[tuple[Image.Image, int]] = []  # image, duration ms

    def shot(page, text, ms):
        frames.append((caption(page.screenshot(), text), ms))

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": args.width, "height": args.height})
        page.goto(args.url)
        page.fill("#q", CONFIDENT)
        shot(page, "Speeded up: each live question takes about 50 s on a 4 GB card.", 1500)
        page.click("#go")
        page.wait_for_selector("#result:not(.hidden)", timeout=240_000)
        shot(page, "A confident answer. The number is capped: the system does not report certainty.", 3500)
        page.click("#q", click_count=3)
        page.fill("#q", ESCALATED)
        page.click("#go")
        page.wait_for_selector("#result:not(.hidden)", timeout=240_000)
        shot(page, "A low-confidence answer is withheld and handed to a person, with the trace.", 3500)
        page.evaluate("document.querySelector('#confcard').scrollIntoView()")
        time.sleep(0.3)
        shot(page, "Why this number: contributions by signal family, in log-odds.", 3500)
        browser.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    images = [f for f, _ in frames]
    images[0].save(out, save_all=True, append_images=images[1:], duration=[d for _, d in frames], loop=0, optimize=False)
    total = sum(d for _, d in frames) / 1000
    print(f"{out}: {len(frames)} frames, {total:.1f} s, {out.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
