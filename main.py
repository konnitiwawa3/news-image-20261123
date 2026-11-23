"""Render the World Dispatch front page using only the Python standard library."""

import json
import os
import struct
import sys
import zlib
from collections import Counter
from functools import lru_cache
from math import cos, sin, tau
from pathlib import Path
from random import Random

ASSET_DIR = Path(__file__).resolve().parent
# The grader uses -P, which omits the script directory from sys.path.
sys.path.insert(0, str(ASSET_DIR))

from illustrations import SCENES, Scene


SIDE = 1024
SCALE = 3
PLATE_SIZE = SIDE * SCALE
MARGIN = 26
RIGHT = SIDE - MARGIN
SPAN = RIGHT - MARGIN
PAPER = (247, 239, 220)
REGIONS = {
    "Europe": "europe",
    "Middle East": "middle_east",
    "Africa": "africa",
    "Asia": "asia",
    "Oceania": "oceania",
    "N. America": "north_america",
    "Latin America": "latin_america",
}
# Stone Light neutral stop 15 and regional hues at stop 30.
COLORS = {
    "ink": "25252a", "muted": "46464e", "europe": "344861",
    "middle_east": "603c37", "africa": "5e3f27", "asia": "2c4f44",
    "oceania": "264d57", "north_america": "4c405b", "latin_america": "524818",
    "red": "743f32", "rule": "a89a83", "hairline": "d2c3a9",
    "cream": "f8edd2", "white": "fff7e6", "map": "c2b395", "panel": "efe3cb",
    "haze": "b8c4bb", "mist": "e1e0c8", "limestone": "ddcb9e", "sand": "bca276",
    "silt": "6b615a", "stone": "918277", "shadow": "28323a", "steel": "83938f",
    "slate": "50656b", "sea": "416873", "silver": "91acaa", "pine": "3d5d51",
    "moss": "819481", "sun": "e0b96e", "rust": "ab6147", "brick": "75473f",
    "salmon": "ce8d70", "ink_light": "494038",
}
PALETTE = {name: index for index, name in enumerate(COLORS, 1)}
INKS = [PAPER, *(tuple(bytes.fromhex(value)) for value in COLORS.values())]
TRANSCRIPTIONS = str.maketrans({"·": "|", "−": "-", " ": " "})


class Press:
    def __init__(self):
        self.plate = bytearray(PLATE_SIZE ** 2)
        self.fonts = json.loads(zlib.decompress((ASSET_DIR / "materials/glyphs.json.z").read_bytes()))

    def row(self, y, x0, x1, color):
        if 0 <= y < PLATE_SIZE:
            left, right = max(0, x0), min(PLATE_SIZE, x1)
            if right > left:
                start = y * PLATE_SIZE + left
                self.plate[start:start + right - left] = bytes((color,)) * (right - left)

    def box(self, x, y, w, h, color):
        left, top, right, bottom = (round(item * SCALE) for item in (x, y, x + w, y + h))
        for row in range(max(0, top), min(PLATE_SIZE, bottom)):
            self.row(row, left, right, PALETTE[color])

    def line(self, points, color, weight=1):
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            steps = max(1, round(SCALE * max(abs(x1 - x0), abs(y1 - y0))))
            for step in range(steps + 1):
                fraction = step / steps
                x = x0 + (x1 - x0) * fraction
                y = y0 + (y1 - y0) * fraction
                self.box(x - weight / 2, y - weight / 2, weight, weight, color)

    def polygon(self, points, color):
        vertices = [(x * SCALE, y * SCALE) for x, y in points]
        edges = list(zip(vertices, vertices[1:] + vertices[:1]))
        low = max(0, int(min(y for _, y in vertices)))
        high = min(PLATE_SIZE, round(max(y for _, y in vertices)))
        for row in range(low, high):
            sample = row + .5
            crossings = sorted(
                x0 + (x1 - x0) * (sample - y0) / (y1 - y0)
                for (x0, y0), (x1, y1) in edges
                if min(y0, y1) <= sample < max(y0, y1)
            )
            for left, right in zip(crossings[::2], crossings[1::2], strict=True):
                self.row(row, round(left), round(right), PALETTE[color])

    def oval(self, x, y, w, h, color):
        points = [(x + w / 2 * (1 + cos(n * tau / 32)),
                   y + h / 2 * (1 + sin(n * tau / 32))) for n in range(32)]
        self.polygon(points, color)

    def rule(self, x, y, width, color="hairline", thickness=.8):
        self.box(x, y, width, thickness, color)

    def frame(self, x, y, w, h, color="rule"):
        self.rule(x, y, w, color)
        self.rule(x, y + h, w, color)
        self.box(x, y, .8, h, color)
        self.box(x + w - .8, y, .8, h, color)

    @lru_cache(maxsize=3600)
    def glyph(self, face, char, scale):
        _, dx, dy, width, height, mask = self.fonts[face][char]
        bits = bytes.fromhex(mask)
        stride = (width + 7) // 8
        points = []
        for y in range(round(height * scale)):
            source_y = min(height - 1, int(y / scale))
            for x in range(round(width * scale)):
                source_x = min(width - 1, int(x / scale))
                if bits[source_y * stride + source_x // 8] & (128 >> (source_x % 8)):
                    points.append((round(dx * scale) + x, round(dy * scale) + y))
        return points

    def width(self, value, face, scale):
        return sum(round(self.fonts[face][c][0] * scale) for c in value.translate(TRANSCRIPTIONS)) / SCALE

    def text(self, value, x, y, *, face="news12", size=1, color="ink", align=0, wear=False, width=None):
        value = value.translate(TRANSCRIPTIONS)
        if width is not None:
            while self.width(value, face, size) > width:
                size -= .01
                if size < .5:
                    raise ValueError(f"Text exceeds its box: {value}")
        cursor = round((x - align * self.width(value, face, size)) * SCALE)
        baseline = round(y * SCALE)
        ink = PALETTE[color]
        for index, char in enumerate(value):
            tone = (index * 101 + cursor * 541 + baseline) % 19
            dye = PALETTE["ink_light"] if wear and tone < 4 else ink
            for dx, dy in self.glyph(face, char, size):
                xx, yy = cursor + dx, baseline + dy
                position = yy * PLATE_SIZE + xx
                if not (0 <= xx < PLATE_SIZE and 0 <= yy < PLATE_SIZE):
                    continue
                speckle = (xx * 83 ^ yy * 173 ^ tone * 13) % 521
                if wear and speckle < 5:
                    continue
                self.plate[position] = dye
                if wear and speckle > 516 and xx + 1 < PLATE_SIZE and self.plate[position + 1] == 0:
                    self.plate[position + 1] = PALETTE["rule"]
            cursor += round(self.fonts[face][char][0] * size)

    def wrap(self, value, width, face, size):
        lines = []
        words = value.split()
        current = words[0]
        for word in words[1:]:
            combined = f"{current} {word}"
            if self.width(combined, face, size) <= width:
                current = combined
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    def paragraph(self, value, x, y, width, *, face="news12", size=1, leading=14, rows=2, color="muted"):
        lines = self.wrap(value, width, face, size)
        while len(lines) > rows and size > .65:
            size -= .02
            lines = self.wrap(value, width, face, size)
        if len(lines) > rows:
            raise ValueError(f"Paragraph exceeds {rows} lines: {value}")
        for i, line in enumerate(lines):
            self.text(line, x, y + i * leading, face=face, size=size, color=color, width=width)


# Simplified world coastline for the small equirectangular locator.
LAND = (
    ((-168,66),(-153,70),(-127,72),(-109,72),(-88,74),(-61,60),(-52,52),(-65,45),
     (-77,39),(-81,29),(-90,29),(-83,18),(-77,8),(-89,14),(-97,20),(-110,23),(-118,32),
     (-125,48),(-138,57),(-155,57)),
    ((-81,10),(-71,12),(-62,9),(-56,5),(-49,-1),(-35,-6),(-38,-17),(-49,-25),
     (-53,-34),(-64,-55),(-73,-53),(-73,-39),(-71,-21),(-78,-8)),
    ((-72,75),(-49,83),(-21,78),(-23,68),(-45,60),(-54,65)),
    ((-11,35),(-9,45),(2,51),(9,57),(19,57),(25,70),(44,70),(69,74),(91,76),
     (117,73),(142,72),(166,68),(178,63),(159,59),(146,49),(144,40),(132,35),(124,20),
     (107,7),(100,1),(98,17),(88,21),(78,7),(73,17),(67,25),(56,27),(47,35),
     (40,40),(32,40),(28,36),(23,37),(15,38),(9,44),(2,43),(-5,36)),
    ((-17,15),(-15,26),(-6,35),(13,37),(29,33),(35,25),(50,12),(44,-2),(40,-13),
     (34,-27),(25,-35),(17,-30),(12,-18),(12,-7),(7,4),(-6,5)),
    ((111,-21),(124,-14),(136,-12),(148,-18),(154,-28),(147,-39),(133,-34),(114,-35)),
    ((95,5),(109,-3),(120,-8),(131,-7),(142,-6),(147,-10),(135,-10),(114,-9),(102,-5)),
    ((46,-12),(51,-15),(49,-25),(44,-24)),
    ((130,31),(137,34),(141,41),(145,44),(143,34)),
    ((166,-46),(178,-37),(175,-35),(168,-41)),
)


def color_of(story):
    return REGIONS[story["region"]]


def story_label(p, story, x, y, width):
    color = color_of(story)
    p.box(x, y, 20, 13, color)
    p.text(f"{story['id']:02}", x + 10, y + 10.3, size=.86, color="white", align=.5)
    p.text(story["place"], x + 25, y + 10, size=.86, color=color, width=width - 27)


def credit(story):
    return f"{story['tag']}  /  {story['source']}"


def masthead(p, edition):
    p.rule(MARGIN, 22, SPAN, "ink", 1.8)
    p.text("THE WORLD DISPATCH", MARGIN, 40, face="display22", size=.89, color="red")
    p.text(f"MONDAY EDITION  /  THROUGH {edition['cutoff']}", RIGHT, 39, size=1.12, align=1)
    p.text(edition["date"], 512, 100, face="display55", size=1.32, align=.5, wear=True)

    counts = Counter(story["region"] for story in edition["stories"])
    step = SPAN / len(REGIONS)
    for i, (region, color) in enumerate(REGIONS.items()):
        x = MARGIN + i * step
        p.box(x, 112, step, 20, color)
        label = f"{region.upper()}   {counts[region]}"
        p.text(label, x + step / 2, 126, size=.97, align=.5, color="white")

    p.rule(MARGIN, 139.5, SPAN)
    p.rule(MARGIN, 162, SPAN)
    p.text("UTC", MARGIN, 154, size=1.15, color="red")
    step = (SPAN - 47) / len(edition["timeline"])
    for i, (time, title, kind) in enumerate(edition["timeline"]):
        x = MARGIN + 47 + i * step
        p.box(x - 6, 144, .65, 14, "rule")
        p.text(time, x, 153, size=.92, color="red")
        p.text(title, x + 38, 150, size=.87, width=step - 45)
        p.text(kind.upper(), x + 38, 158.5, size=.69, color="muted")


def leading(p, lead, secondary):
    x, y, w = MARGIN, 171, 612
    story_label(p, lead, x, y, w)
    p.text(credit(lead), x + w, y + 10, size=.88, align=1, color=color_of(lead))
    for i, line in enumerate(lead["lines"]):
        p.text(line, x, 226 + 48 * i, face="display55", size=1.03, width=w - 2)
    SCENES[lead["scene"]](Scene(p, x, 283, w, 121))
    p.text("ILLUSTRATION  /  BENGHAZI HARBOR", x + w - 6, 398, size=.74, align=1, color="white")
    p.paragraph(lead["detail"], x, 425, w, face="news14", size=1.2, leading=18, rows=2, color="ink")
    p.box(649, y, .8, 276, "rule")
    for s, top in zip(secondary, (171, 310), strict=True):
        x, w = 662, RIGHT - 662
        story_label(p, s, x, top, w)
        p.text(credit(s), x + w, top + 10, size=.81, align=1, color=color_of(s))
        SCENES[s["scene"]](Scene(p, x, top + 17, w, 60))
        p.text(s["title"], x, top + 99, face="display22", size=1.00, width=w)
        p.paragraph(s["detail"], x, top + 116, w, face="news14", size=.97, leading=13, rows=2)
        p.rule(x, top + 134, w)


def dispatches(p, stories):
    p.rule(MARGIN, 453, SPAN, "ink", 1.05)
    p.text("AROUND THE WORLD", MARGIN, 470, size=1.04, color="red")
    gutter = 12
    w = (SPAN - 3 * gutter) / 4
    for i, story in enumerate(stories):
        x = MARGIN + (i % 4) * (w + gutter)
        y = 479 + i // 4 * 77
        story_label(p, story, x, y, w)
        p.rule(x, y + 13.5, w)
        SCENES[story["scene"]](Scene(p, x + w - 67, y + 17, 67, 46))
        p.paragraph(story["title"], x, y + 27, w - 73, face="news14",
                    size=1.04, leading=13, color="ink")
        p.paragraph(story["detail"], x, y + 49.5, w - 73, size=.83, leading=8.2, rows=3)
        p.text(credit(story), x + w, y + 75, size=.75, align=1, color=color_of(story), width=w)


def briefs(p, stories):
    p.text("IN BRIEF", MARGIN, 730, size=1.02, color="red")
    for i, story in enumerate(stories):
        x = MARGIN + i // 11 * 315
        y = 738 + i % 11 * 21
        color = color_of(story)
        p.box(x, y + 1, 3, 17, color)
        p.text(f"{story['id']:02}  {story['place']}  /  {credit(story)}", x + 7, y + 8,
               size=.73, color=color, width=295)
        p.text(story["title"], x + 7, y + 18.3, size=.94, width=295)
        p.rule(x, y + 20.2, 304, thickness=.55)


def inside_polygon(x, y, vertices):
    hits = 0
    for (ax, ay), (bx, by) in zip(vertices, vertices[1:] + vertices[:1]):
        if (ay <= y < by) or (by <= y < ay):
            hits += x < ax + (bx - ax) * (y - ay) / (by - ay)
    return hits % 2


def atlas(p, edition):
    x, y, w, h = 662, 733, RIGHT - 662, 135
    p.text("STORY LOCATOR", x, 730, size=1.03, color="red")
    p.text("NUMBERS MATCH THE ARTICLES", RIGHT, 730, size=.75, align=1, color="muted")
    p.box(x, y, w, h, "panel")
    p.frame(x, y, w, h)

    def project(lon, lat):
        return x + 9 + (lon + 180) * (w - 18) / 360, y + 12 + (85 - lat) * (h - 25) / 146

    for lat in range(-57, 83, 4):
        for lon in range(-178, 180, 4):
            if any(inside_polygon(lon, lat, land) for land in LAND):
                px, py = project(lon, lat)
                p.oval(px - .95, py - .8, 1.9, 1.6, "map")

    pins = []
    for story in edition["stories"]:
        if "pin" not in story:
            continue
        lon, lat, dx, dy = story["pin"]
        px, py = project(lon, lat)
        cx, cy = px + dx, py + dy
        color = color_of(story)
        p.line(((px, py), (cx, cy)), color, .7)
        p.oval(px - 1.4, py - 1.4, 2.8, 2.8, color)
        pins.append((story["id"], cx, cy, color))
    for number, cx, cy, color in pins:
        p.oval(cx - 7.3, cy - 7.3, 14.6, 14.6, "white")
        p.oval(cx - 6.5, cy - 6.5, 13, 13, color)
        p.text(f"{number:02}", cx, cy + 2.65, size=.66, color="white", align=.5)

    y = 876
    p.box(x, y, w, 91, "panel")
    p.frame(x, y, w, 91, "rule")
    p.text("DATE CHECK", x + 9, y + 16, size=1, color="red")
    for i, (label, detail) in enumerate(edition["date_check"]):
        baseline = y + 31 + 14 * i
        p.text(label.upper(), x + 9, baseline, size=.79, color="red", width=84)
        p.text(detail, x + 96, baseline, size=.80, width=w - 105)


def markets(p, edition):
    p.rule(MARGIN, 977, SPAN, "ink", 1.15)
    p.text("MARKETS", MARGIN, 994, size=1.1, color="red")
    p.text(edition["market_source"], MARGIN, 1007, size=.73, color="muted")
    start = MARGIN + 194
    step = (RIGHT - start) / len(edition["markets"])
    for i, (name, value, detail) in enumerate(edition["markets"]):
        x = start + i * step
        p.box(x - 8, 982, .6, 25, "rule")
        p.text(name, x, 994, size=.92, color="red")
        p.text(value, x + 58, 995, face="display22", size=.77, width=step - 68)
        p.text(detail, x, 1007, size=.81, color="muted")
    p.rule(MARGIN, 1013, SPAN, "ink", 1.1)


def render(edition):
    p = Press()
    stories = edition["stories"]
    masthead(p, edition)
    leading(p, stories[0], stories[1:3])
    dispatches(p, stories[3:15])
    p.rule(MARGIN, 715, SPAN, "ink", 1.05)
    briefs(p, stories[15:])
    atlas(p, edition)
    markets(p, edition)
    return p.plate


def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


def print_png(plate):
    rng = Random(23112026)
    jitter = rng.randbytes(SIDE ** 2)
    rows = bytearray()
    for y in range(SIDE):
        previous = [0, 0, 0]
        rows.append(1)
        for x in range(SIDE):
            p = y * SCALE * PLATE_SIZE + x * SCALE
            a, b, c = p, p + PLATE_SIZE, p + PLATE_SIZE * 2
            pixels = (plate[a], plate[a+1], plate[a+2], plate[b], plate[b+1], plate[b+2],
                      plate[c], plate[c+1], plate[c+2])
            if pixels.count(pixels[0]) == 9:
                rgb = INKS[pixels[0]]
            else:
                inks = [INKS[i] for i in pixels]
                rgb = tuple(sum(channel) // 9 for channel in zip(*inks))
            grain = jitter[y * SIDE + x]
            aging = int(1.6 * sin(x / 71 + y / 88) + 1.2 * cos(y / 131 - x / 175))
            edge = -int(max(0, 30 - min(x, y, SIDE - x - 1, SIDE - y - 1)) / 11)
            paper = 0 in pixels
            noise = aging + edge + (grain % 4 - 1 if paper else grain % 3 - 1)
            for channel, base in enumerate(rgb):
                value = min(255, max(0, base + noise))
                rows.append((value - previous[channel]) & 255)
                previous[channel] = value
    header = struct.pack(">IIBBBBB", SIDE, SIDE, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(rows, level=9)) + chunk(b"IEND", b""))


def main():
    edition = json.loads((ASSET_DIR / "edition.json").read_text(encoding="utf-8"))
    png = print_png(render(edition))
    if len(png) > 1024 ** 2:
        raise ValueError(f"PNG exceeds 1 MiB: {len(png)}")
    output = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    output.mkdir(parents=True, exist_ok=True)
    (output / "entry.png").write_bytes(png)


if __name__ == "__main__":
    main()
