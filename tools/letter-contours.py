"""Sample the exact Bézier outlines used to draw the landing-page wordmark."""
import json
from pathlib import Path

from lxml import etree
from svgpathtools import parse_path

root = Path(__file__).resolve().parents[1]
brand = root / "dist/media/brand"
svg = etree.parse(str(brand / "hero-wordmark.svg"))
paths = [parse_path(node.get("d")).continuous_subpaths()[0]
         for node in svg.xpath('//*[local-name()="path"]')]

# Coordinates here refer to the original Illustrator viewBox.
cut = {
    "cInner": (0, 33/40, 30/40),
    "cCeiling": (0, 30/40, 25.5/40),
    "littleO": (5, 13.2/40, 17.6/40),
    "bigO": (4, 16.5/40, 22.6/40),
    "kStem": (2, 31.6/40, 34.8/40),
    "kArm": (2, 1.6/40, 3.8/40),
    "mark": (3, 7.6/40, 15/40),
    "dStem": (1, 16.7/40, 22.5/40),
}
points = {}
for name, (index, a, b) in cut.items():
    path = paths[index]
    segment = [path.point(a + (b - a) * i / 48) for i in range(49)]
    points[name] = [[round(pt.real - 274, 2), round(pt.imag - 707, 2)] for pt in segment]
(brand / "climb-contours.json").write_text(json.dumps(points, separators=(",", ":")))
