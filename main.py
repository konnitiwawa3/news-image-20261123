"""Typeset the 23 November edition and save it as a reproducible RGB PNG."""

from collections import Counter
from functools import lru_cache
from itertools import pairwise
import json
from math import cos, sin, tau
from os import environ
from pathlib import Path
from random import Random
from struct import pack
import sys
from zlib import compress, crc32, decompress

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from illustrations import SCENES, Scene

SIDE = 1024
SUPERSAMPLE = 3
STRIDE = SIDE * SUPERSAMPLE
LEFT = 26
RIGHT = SIDE - LEFT
CONTENT = RIGHT - LEFT
REGION_INK = {
    "Europe": "europe",
    "Middle East": "middle_east",
    "Africa": "africa",
    "Asia": "asia",
    "Oceania": "oceania",
    "N. America": "north_america",
    "Latin America": "latin_america",
}

# Astryx Stone Light informs the editorial inks. The other entries paint the scenes.
SWATCHES = {
    "ink": "25252a", "muted": "46464e", "europe": "344861",
    "middle_east": "603c37", "africa": "5e3f27", "asia": "2c4f44",
    "oceania": "264d57", "north_america": "4c405b", "latin_america": "524818",
    "red": "603c37", "navy": "17263a", "rule": "848489", "hairline": "d4d3dd",
    "cream": "f8edd2", "white": "ffffff", "map": "ababb3", "panel": "f0f0f7",
    "lead_sky": "c2d6f1", "lead_water": "264d57", "lead_glint": "8ab3be",
    "haze": "b8c4bb", "mist": "e1e0c8", "limestone": "ddcb9e", "sand": "bca276",
    "silt": "6b615a", "stone": "918277", "shadow": "28323a", "steel": "83938f",
    "slate": "50656b", "sea": "416873", "silver": "91acaa", "pine": "3d5d51",
    "moss": "819481", "sun": "e0b96e", "rust": "ab6147", "brick": "75473f",
    "salmon": "ce8d70",
}
INK_INDEX = {name: index for index, name in enumerate(SWATCHES, start=1)}
RGB = [(250, 248, 241)] + [tuple(bytes.fromhex(code)) for code in SWATCHES.values()]
GLYPH_ALIASES = str.maketrans("·−\u00a0", "|- ")
UNIT_CIRCLE = [(cos(i * tau / 32), sin(i * tau / 32)) for i in range(32)]
PAPER_TONES = tuple(tuple(channel + shift for channel in RGB[0]) for shift in (-1, 0, 1))


class Canvas:
    def __init__(self, fonts):
        self.pixels = bytearray(STRIDE * STRIDE)
        self.fonts = fonts

    def _span(self, y, left, right, paint):
        left = max(left, 0)
        right = min(right, STRIDE)
        if left < right:
            offset = y * STRIDE
            self.pixels[offset + left:offset + right] = paint * (right - left)

    def box(self, x, y, w, h, color):
        x0, x1 = round(x * SUPERSAMPLE), round((x + w) * SUPERSAMPLE)
        y0, y1 = round(y * SUPERSAMPLE), round((y + h) * SUPERSAMPLE)
        paint = bytes([INK_INDEX[color]])
        for sample_y in range(max(y0, 0), min(y1, STRIDE)):
            self._span(sample_y, x0, x1, paint)

    def line(self, points, color, weight=1):
        half = weight / 2
        for (x0, y0), (x1, y1) in pairwise(points):
            dx, dy = x1 - x0, y1 - y0
            segments = max(1, round(max(abs(dx), abs(dy)) * SUPERSAMPLE))
            for step in range(segments + 1):
                t = step / segments
                self.box(x0 + dx * t - half, y0 + dy * t - half, weight, weight, color)

    def polygon(self, points, color):
        vertices = [(x * SUPERSAMPLE, y * SUPERSAMPLE) for x, y in points]
        edges = tuple(pairwise([*vertices, vertices[0]]))
        first = max(0, int(min(point[1] for point in vertices)))
        last = min(STRIDE, round(max(point[1] for point in vertices)))
        paint = bytes([INK_INDEX[color]])
        for row in range(first, last):
            level = row + .5
            intersections = []
            for (x0, y0), (x1, y1) in edges:
                if min(y0, y1) <= level < max(y0, y1):
                    intersections.append(x0 + (x1 - x0) * (level - y0) / (y1 - y0))
            crossings = iter(sorted(intersections))
            for left, right in zip(crossings, crossings, strict=True):
                self._span(row, round(left), round(right), paint)

    def oval(self, x, y, w, h, color):
        self.polygon([(x + w / 2 * (1 + cx), y + h / 2 * (1 + cy))
                      for cx, cy in UNIT_CIRCLE], color)

    def rule(self, x, y, width, color="hairline", thickness=.8):
        self.box(x, y, width, thickness, color)

    def frame(self, x, y, width, height):
        for edge in (y, y + height):
            self.rule(x, edge, width, "rule")
        for edge in (x, x + width - .8):
            self.box(edge, y, .8, height, "rule")

    @lru_cache(maxsize=3600)
    def _mask(self, face, letter, size):
        _, dx, dy, width, height, encoded = self.fonts[face][letter]
        if not width or not height:
            return ()
        stride = (width + 7) // 8
        data = bytes.fromhex(encoded)
        offset_x, offset_y = round(dx * size), round(dy * size)
        columns = [min(width - 1, int(x / size)) for x in range(round(width * size))]
        dots = []
        for y in range(round(height * size)):
            row = min(height - 1, int(y / size)) * stride
            for x, source_x in enumerate(columns):
                if data[row + source_x // 8] & (0x80 >> (source_x % 8)):
                    dots.append((offset_x + x, offset_y + y))
        return tuple(dots)

    def measure(self, value, face, size):
        alphabet = self.fonts[face]
        advances = (round(alphabet[letter][0] * size) for letter in value.translate(GLYPH_ALIASES))
        return sum(advances) / SUPERSAMPLE

    def text(self, value, x, y, *, face="sans11", size=1, color="ink", align=0, width=None):
        value = value.translate(GLYPH_ALIASES)
        if width is not None:
            while self.measure(value, face, size) > width:
                size -= .01
                if size < .5:
                    raise ValueError(f"Cannot fit text into {width}px: {value}")
        pen = round((x - align * self.measure(value, face, size)) * SUPERSAMPLE)
        baseline = round(y * SUPERSAMPLE)
        paint = INK_INDEX[color]
        for letter in value:
            for dx, dy in self._mask(face, letter, size):
                px, py = pen + dx, baseline + dy
                if 0 <= px < STRIDE and 0 <= py < STRIDE:
                    self.pixels[py * STRIDE + px] = paint
            pen += round(self.fonts[face][letter][0] * size)

    def _wrap(self, value, width, face, size):
        first, *rest = value.split()
        lines = [first]
        for word in rest:
            trial = " ".join((lines[-1], word))
            if self.measure(trial, face, size) > width:
                lines.append(word)
            else:
                lines[-1] = trial
        return lines

    def paragraph(self, value, x, y, width, *, face, size, leading, rows, color="muted"):
        lines = self._wrap(value, width, face, size)
        while len(lines) > rows and size > .65:
            size -= .02
            lines = self._wrap(value, width, face, size)
        if len(lines) > rows:
            raise ValueError(f"Cannot fit text into {rows} lines: {value}")
        for index, line in enumerate(lines):
            self.text(line, x, y + index * leading, face=face, size=size, color=color, width=width)


# Low-resolution coastline, arranged as rings in geographic degrees.
COASTLINES = (
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


def is_land(lon, lat, ring):
    inside = False
    for (x0, y0), (x1, y1) in pairwise((*ring, ring[0])):
        if min(y0, y1) <= lat < max(y0, y1):
            crossing = x0 + (x1 - x0) * (lat - y0) / (y1 - y0)
            inside ^= lon < crossing
    return inside


def byline(article):
    return "  /  ".join((article["tag"], article["source"]))


def slug(canvas, article, left, top, available):
    ink = REGION_INK[article["region"]]
    base = top + 10.1
    canvas.box(left, top, 20, 13, ink)
    canvas.text(f"{article['id']:02}", left + 10, base, align=.5, size=.96, color="white")
    canvas.text(article["place"], left + 25, base, width=available - 27, color=ink)


def picture(canvas, article, x, y, width, height):
    scene = Scene(canvas, x, y, width, height)
    SCENES[article["scene"]](scene)


def set_flag(canvas, issue):
    canvas.rule(LEFT, 20, CONTENT, "navy", 2)
    canvas.text("THE WORLD DISPATCH", LEFT, 54, face="display27", color="navy", size=1.15)
    canvas.text("MONDAY EDITION  /  THROUGH " + issue["cutoff"], LEFT, 69, color="muted")
    canvas.text(issue["date"], RIGHT, 63, align=1, face="display55", color="navy", size=.79)

    totals = Counter(article["region"] for article in issue["stories"])
    slot = CONTENT / len(REGION_INK)
    for index, (region, ink) in enumerate(REGION_INK.items()):
        left = LEFT + index * slot
        canvas.rule(left, 78, slot - 6, ink, 2)
        canvas.text(f"{region.upper()}  {totals[region]}", left, 94, color=ink, size=1.04)

    canvas.box(LEFT, 101, CONTENT, 24, "panel")
    canvas.text("UTC", LEFT + 7, 117, color="red", size=1.16)
    slot = (CONTENT - 47) / len(issue["timeline"])
    for index, (hour, headline, event) in enumerate(issue["timeline"]):
        left = LEFT + 47 + index * slot
        canvas.box(left - 6, 106, .65, 14, "rule")
        canvas.text(hour, left, 116, color="red", size=1.07)
        canvas.text(headline, left + 38, 111, width=slot - 45)
        canvas.text(event.upper(), left + 38, 121, color="muted", size=.79)


def set_front_stories(canvas, cover):
    lead, *sidebar = cover
    lead_width = 638
    slug(canvas, lead, LEFT, 136, lead_width)
    ink = REGION_INK[lead["region"]]
    canvas.text(byline(lead), LEFT + lead_width, 146, align=1, color=ink)
    for baseline, headline in zip((196, 246), lead["lines"], strict=True):
        canvas.text(headline, LEFT, baseline, face="display55", color="navy",
                    width=lead_width, size=1.09)
    picture(canvas, lead, LEFT, 256, lead_width, 142)
    edge = LEFT + lead_width
    canvas.box(edge - 189, 381, 189, 17, "navy")
    canvas.text("BENGHAZI HARBOR  /  ILLUSTRATION", edge - 7, 393, align=1,
                color="white", size=.91)
    canvas.paragraph(lead["detail"], LEFT, 419, lead_width, face="sans13", color="ink",
                     size=1.28, leading=18, rows=2)

    left = 690
    width = RIGHT - left
    canvas.box(left - 12, 136, width + 12, 306, "panel")
    for top, article in zip((142, 291), sidebar, strict=True):
        slug(canvas, article, left, top, width)
        canvas.text(byline(article), RIGHT - 9, top + 10, align=1, size=.88,
                    color=REGION_INK[article["region"]])
        canvas.paragraph(article["title"], left, top + 34, width - 9, face="display27",
                         size=.99, leading=23, rows=2, color="navy")
        picture(canvas, article, left, top + 61, width - 9, 46)
        canvas.paragraph(article["detail"], left, top + 123, width - 9, face="sans13",
                         size=.97, leading=13, rows=2, color="ink")
    canvas.rule(left, 282, width - 9, "rule")


def set_dispatch_grid(canvas, articles):
    canvas.box(LEFT, 450, CONTENT, 21, "navy")
    canvas.text("AROUND THE WORLD", LEFT + 8, 465, color="white", size=1.21)
    gap = 12
    width = (CONTENT - gap * 3) / 4
    for index, article in enumerate(articles):
        row, column = divmod(index, 4)
        left = LEFT + column * (width + gap)
        top = 477 + row * 80
        slug(canvas, article, left, top, width)
        canvas.text(article["title"], left, top + 29, width=width, face="display22", size=.90)
        picture(canvas, article, left + width - 76, top + 34, 76, 42)
        text_width = width - 83
        canvas.paragraph(article["detail"], left, top + 44, text_width, face="sans13",
                         size=.83, leading=10.6, rows=3)
        canvas.text(byline(article), left, top + 76, width=text_width, size=.82,
                    color=REGION_INK[article["region"]])
        if row < 2:
            canvas.rule(left, top + 78.5, width)
    canvas.rule(LEFT, 719, CONTENT, "navy", 1.05)


def set_brief_columns(canvas, articles):
    canvas.text("IN BRIEF", LEFT, 734, color="navy", size=1.19)
    for index, article in enumerate(articles):
        column, row = divmod(index, 11)
        left = LEFT + column * 315
        top = 741 + row * 20.7
        ink = REGION_INK[article["region"]]
        credit = f"{article['id']:02}  {article['place']}  /  {byline(article)}"
        canvas.box(left, top + 1, 3, 17, ink)
        canvas.text(credit, left + 7, top + 7.4, width=295, color=ink, size=.78)
        canvas.text(article["title"], left + 7, top + 18.5, width=295, face="sans13", size=.99)
        canvas.rule(left, top + 20.2, 304, thickness=.55)


def set_locator(canvas, issue):
    left, top = 662, 740
    width, height = RIGHT - left, 130
    canvas.text("STORY LOCATOR", left, 734, color="navy", size=1.19)
    canvas.text("NUMBERS MATCH THE ARTICLES", RIGHT, 734, align=1, color="muted", size=.86)
    canvas.box(left, top, width, height, "panel")
    canvas.frame(left, top, width, height)

    def plot(lon, lat):
        x = left + 9 + (lon + 180) * (width - 18) / 360
        y = top + 12 + (85 - lat) * (height - 25) / 146
        return x, y

    for lat in range(-57, 83, 4):
        for lon in range(-178, 180, 4):
            if any(is_land(lon, lat, ring) for ring in COASTLINES):
                x, y = plot(lon, lat)
                canvas.oval(x - .95, y - .8, 1.9, 1.6, "map")

    badges = []
    for article in issue["stories"]:
        pin = article.get("pin")
        if pin is None:
            continue
        lon, lat, dx, dy = pin
        x, y = plot(lon, lat)
        label_x, label_y = x + dx, y + dy
        ink = REGION_INK[article["region"]]
        canvas.line([(x, y), (label_x, label_y)], ink, .7)
        canvas.oval(x - 1.4, y - 1.4, 2.8, 2.8, ink)
        badges.append((article["id"], label_x, label_y, ink))

    for number, x, y, ink in badges:
        canvas.oval(x - 7.3, y - 7.3, 14.6, 14.6, "white")
        canvas.oval(x - 6.5, y - 6.5, 13, 13, ink)
        canvas.text(f"{number:02}", x, y + 2.8, align=.5, color="white", size=.78)

    canvas.box(left, 876, width, 91, "panel")
    canvas.frame(left, 876, width, 91)
    canvas.text("DATE CHECK", left + 9, 892, color="navy", size=1.15)
    for index, (event, date) in enumerate(issue["date_check"]):
        baseline = 907 + index * 14
        canvas.text(event.upper(), left + 9, baseline, color="red", size=.94, width=84)
        canvas.text(date, left + 96, baseline, face="sans13", size=.87, width=width - 105)


def set_market_strip(canvas, issue):
    canvas.box(LEFT, 977, CONTENT, 35, "navy")
    canvas.text("MARKETS", LEFT + 8, 994, color="white", size=1.14)
    canvas.text(issue["market_source"], LEFT + 8, 1007, color="lead_sky", size=.84)
    first = LEFT + 194
    width = (RIGHT - first) / len(issue["markets"])
    for index, (name, reading, context) in enumerate(issue["markets"]):
        left = first + index * width
        canvas.box(left - 8, 982, .6, 25, "rule")
        canvas.text(name, left, 994, color="lead_sky", size=1.04)
        canvas.text(reading, left + 58, 995, width=width - 68, face="display22",
                    size=.83, color="white")
        canvas.text(context, left, 1007, size=.94, color="white")


def typeset(issue, fonts):
    canvas = Canvas(fonts)
    articles = issue["stories"]
    set_flag(canvas, issue)
    set_front_stories(canvas, articles[:3])
    set_dispatch_grid(canvas, articles[3:15])
    set_brief_columns(canvas, articles[15:])
    set_locator(canvas, issue)
    set_market_strip(canvas, issue)
    return canvas.pixels


def encode_rows(samples):
    grain = iter(Random(23112026).randbytes(SIDE * SIDE))
    scanlines = bytearray()
    for row in range(SIDE):
        top = row * SUPERSAMPLE * STRIDE
        previous = (0, 0, 0)
        scanlines.append(1)  # PNG Sub filter.
        for offset in range(top, top + STRIDE, SUPERSAMPLE):
            middle, bottom = offset + STRIDE, offset + 2 * STRIDE
            block = samples[offset:offset + 3] + samples[middle:middle + 3] + samples[bottom:bottom + 3]
            texture = next(grain) % 3
            ink = block[0]
            if block.count(ink) == len(block):
                color = RGB[ink] if ink else PAPER_TONES[texture]
            else:
                shift = texture - 1 if 0 in block else 0
                components = zip(*(RGB[index] for index in block))
                color = tuple(max(0, min(255, sum(values) // 9 + shift)) for values in components)
            scanlines.extend((channel - prior) & 255 for channel, prior in zip(color, previous))
            previous = color
    return scanlines


def png_chunk(tag, payload):
    body = tag + payload
    return pack(">I", len(payload)) + body + pack(">I", crc32(body))


def main():
    issue = json.loads((ROOT / "edition.json").read_text(encoding="utf-8"))
    fonts = json.loads(decompress((ROOT / "materials" / "glyphs.json.z").read_bytes()))
    header = pack(">IIBBBBB", SIDE, SIDE, 8, 2, 0, 0, 0)
    scanlines = encode_rows(typeset(issue, fonts))
    png = b"\x89PNG\r\n\x1a\n" + b"".join((
        png_chunk(b"IHDR", header),
        png_chunk(b"IDAT", compress(scanlines, 9)),
        png_chunk(b"IEND", b""),
    ))
    if len(png) > 1024 * 1024:
        raise ValueError("The finished page exceeds the 1 MiB output limit.")
    folder = Path(environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "entry.png").write_bytes(png)


if __name__ == "__main__":
    main()
