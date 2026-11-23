"""Render the November 23 World Dispatch from its edition manifest."""

import json
import os
import struct
import sys
import zlib
from collections import Counter
from functools import lru_cache
from itertools import pairwise
from math import cos, sin, tau
from pathlib import Path
from random import Random

HERE = Path(__file__).resolve().parent
# Python's safe-path mode leaves the script directory off the module path.
sys.path.insert(0, str(HERE))

from illustrations import SCENES, Scene

SIDE = 1024
SCALE = 3
RASTER_SIDE = SIDE * SCALE
MARGIN = 26
RIGHT_EDGE = SIDE - MARGIN
PRINT_WIDTH = RIGHT_EDGE - MARGIN
PAPER = (247, 239, 220)

REGION_COLOR = dict(zip(
    ("Europe", "Middle East", "Africa", "Asia", "Oceania", "N. America", "Latin America"),
    ("europe", "middle_east", "africa", "asia", "oceania", "north_america", "latin_america"),
    strict=True,
))
# The press palette retains the edition's Astryx Stone Light colors.
COLOR_SWATCHES = dict(
    ink="25252a", muted="46464e", europe="344861", middle_east="603c37",
    africa="5e3f27", asia="2c4f44", oceania="264d57", north_america="4c405b",
    latin_america="524818", red="743f32", rule="a89a83", hairline="d2c3a9",
    cream="f8edd2", white="fff7e6", map="c2b395", panel="efe3cb", haze="b8c4bb",
    mist="e1e0c8", limestone="ddcb9e", sand="bca276", silt="6b615a",
    stone="918277", shadow="28323a", steel="83938f", slate="50656b", sea="416873",
    silver="91acaa", pine="3d5d51", moss="819481", sun="e0b96e", rust="ab6147",
    brick="75473f", salmon="ce8d70", ink_light="494038",
)
COLOR_ID = dict(zip(COLOR_SWATCHES, range(1, len(COLOR_SWATCHES) + 1), strict=True))
RGB = (PAPER, *(tuple(bytes.fromhex(code)) for code in COLOR_SWATCHES.values()))
FONT_TEXT = str.maketrans({"·": "|", "−": "-", "\u00a0": " "})


def outline_edges(vertices):
    return pairwise((*vertices, vertices[0]))


class Plate:
    def __init__(self):
        self.cells = bytearray(RASTER_SIDE ** 2)
        atlas = HERE / "materials" / "glyphs.json.z"
        self.atlas = json.loads(zlib.decompress(atlas.read_bytes()))

    def span(self, row, x0, x1, ink):
        begin = max(x0, 0)
        end = min(x1, RASTER_SIDE)
        if 0 <= row < RASTER_SIDE and begin < end:
            base = row * RASTER_SIDE
            self.cells[base + begin:base + end] = bytes((ink,)) * (end - begin)

    def box(self, x, y, width, height, color):
        x0, x1 = round(x * SCALE), round((x + width) * SCALE)
        y0, y1 = round(y * SCALE), round((y + height) * SCALE)
        code = COLOR_ID[color]
        for row in range(max(0, y0), min(y1, RASTER_SIDE)):
            self.span(row, x0, x1, code)

    def line(self, vertices, color, weight=1):
        brush = weight / 2
        for (x0, y0), (x1, y1) in pairwise(vertices):
            dx, dy = x1 - x0, y1 - y0
            steps = max(1, round(SCALE * max(abs(dx), abs(dy))))
            for step in range(steps + 1):
                progress = step / steps
                x = x0 + dx * progress - brush
                y = y0 + dy * progress - brush
                self.box(x, y, weight, weight, color)

    def polygon(self, vertices, color):
        enlarged = [(x * SCALE, y * SCALE) for x, y in vertices]
        edges = tuple(outline_edges(enlarged))
        rows = [point[1] for point in enlarged]
        ink = COLOR_ID[color]
        for row in range(max(0, int(min(rows))), min(RASTER_SIDE, round(max(rows)))):
            center = row + .5
            cuts = []
            for (xa, ya), (xb, yb) in edges:
                if min(ya, yb) <= center < max(ya, yb):
                    cuts.append(xa + (xb - xa) * (center - ya) / (yb - ya))
            cuts.sort()
            crossings = iter(cuts)
            for left, right in zip(crossings, crossings, strict=True):
                self.span(row, round(left), round(right), ink)

    def oval(self, x, y, width, height, color):
        rx, ry = width / 2, height / 2
        angles = (index * tau / 32 for index in range(32))
        points = [(x + rx * (1 + cos(a)), y + ry * (1 + sin(a))) for a in angles]
        self.polygon(points, color)

    def rule(self, x, y, width, color="hairline", thickness=.8):
        self.box(x, y, width, thickness, color)

    def frame(self, x, y, width, height):
        for top in (y, y + height):
            self.rule(x, top, width, "rule")
        for left in (x, x + width - .8):
            self.box(left, y, .8, height, "rule")

    @lru_cache(maxsize=3600)
    def stencil(self, face, letter, size):
        _, offset_x, offset_y, width, height, encoded = self.atlas[face][letter]
        bitmap = bytes.fromhex(encoded)
        stride = (width + 7) // 8
        left, top = round(offset_x * size), round(offset_y * size)
        x_indices = [min(width - 1, int(x / size)) for x in range(round(width * size))]
        pixels = []
        for y in range(round(height * size)):
            start = stride * min(height - 1, int(y / size))
            for x, column in enumerate(x_indices):
                byte, bit = divmod(column, 8)
                if bitmap[start + byte] & (128 >> bit):
                    pixels.append((left + x, top + y))
        return pixels

    def measure(self, value, face, size):
        glyphs = self.atlas[face]
        advances = (round(glyphs[c][0] * size) for c in value.translate(FONT_TEXT))
        return sum(advances) / SCALE

    def text(self, value, x, y, *, face="news12", size=1, color="ink", align=0,
             wear=False, width=None):
        value = value.translate(FONT_TEXT)
        while width is not None and self.measure(value, face, size) > width:
            size -= .01
            if size < .5:
                raise ValueError(f"Text cannot fit in {width} px: {value}")
        cursor = round((x - align * self.measure(value, face, size)) * SCALE)
        baseline = round(y * SCALE)
        flat_ink = COLOR_ID[color]
        for position, letter in enumerate(value):
            offset = (position * 101 + cursor * 541 + baseline) % 19
            ink = COLOR_ID["ink_light"] if wear and offset < 4 else flat_ink
            for i, j in self.stencil(face, letter, size):
                px, py = cursor + i, baseline + j
                if min(px, py) < 0 or max(px, py) >= RASTER_SIDE:
                    continue
                grain = (px * 83 ^ py * 173 ^ offset * 13) % 521
                if wear and grain < 5:
                    continue
                cell = py * RASTER_SIDE + px
                self.cells[cell] = ink
                if wear and grain > 516 and px + 1 < RASTER_SIDE and self.cells[cell + 1] == 0:
                    self.cells[cell + 1] = COLOR_ID["rule"]
            cursor += round(self.atlas[face][letter][0] * size)

    def lines(self, value, width, face, size):
        words = iter(value.split())
        line = next(words)
        lines = []
        for word in words:
            trial = " ".join((line, word))
            if self.measure(trial, face, size) > width:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
        return lines

    def paragraph(self, value, x, y, width, *, face="news12", size=1, leading=14,
                  rows=2, color="muted"):
        while True:
            lines = self.lines(value, width, face, size)
            if len(lines) <= rows:
                break
            if size <= .65:
                raise ValueError(f"Paragraph cannot fit in {rows} rows: {value}")
            size -= .02
        for line_number, line in enumerate(lines):
            self.text(line, x, y + leading * line_number, face=face, size=size,
                      color=color, width=width)


# Longitudes and latitudes of the locator's continental outlines.
COASTLINES = (
    ((-168, 66), (-153, 70), (-127, 72), (-109, 72), (-88, 74), (-61, 60), (-52, 52),
     (-65, 45), (-77, 39), (-81, 29), (-90, 29), (-83, 18), (-77, 8), (-89, 14),
     (-97, 20), (-110, 23), (-118, 32), (-125, 48), (-138, 57), (-155, 57)),
    ((-81, 10), (-71, 12), (-62, 9), (-56, 5), (-49, -1), (-35, -6), (-38, -17),
     (-49, -25), (-53, -34), (-64, -55), (-73, -53), (-73, -39), (-71, -21), (-78, -8)),
    ((-72, 75), (-49, 83), (-21, 78), (-23, 68), (-45, 60), (-54, 65)),
    ((-11, 35), (-9, 45), (2, 51), (9, 57), (19, 57), (25, 70), (44, 70), (69, 74),
     (91, 76), (117, 73), (142, 72), (166, 68), (178, 63), (159, 59), (146, 49),
     (144, 40), (132, 35), (124, 20), (107, 7), (100, 1), (98, 17), (88, 21),
     (78, 7), (73, 17), (67, 25), (56, 27), (47, 35), (40, 40), (32, 40),
     (28, 36), (23, 37), (15, 38), (9, 44), (2, 43), (-5, 36)),
    ((-17, 15), (-15, 26), (-6, 35), (13, 37), (29, 33), (35, 25), (50, 12),
     (44, -2), (40, -13), (34, -27), (25, -35), (17, -30), (12, -18), (12, -7),
     (7, 4), (-6, 5)),
    ((111, -21), (124, -14), (136, -12), (148, -18), (154, -28), (147, -39),
     (133, -34), (114, -35)),
    ((95, 5), (109, -3), (120, -8), (131, -7), (142, -6), (147, -10),
     (135, -10), (114, -9), (102, -5)),
    ((46, -12), (51, -15), (49, -25), (44, -24)),
    ((130, 31), (137, 34), (141, 41), (145, 44), (143, 34)),
    ((166, -46), (178, -37), (175, -35), (168, -41)),
)


def news_color(article):
    return REGION_COLOR[article["region"]]


def credit(article):
    source = article["attribution"]
    return "  /  ".join((source["certainty"], source["outlet"]))


def slug(plate, article, left, top, width):
    shade = news_color(article)
    plate.box(left, top, 20, 13, shade)
    plate.text(format(article["id"], "02"), left + 10, top + 10.3,
               size=.86, color="white", align=.5)
    plate.text(article["place"], left + 25, top + 10, size=.86, color=shade, width=width - 27)


def masthead(plate, edition, articles):
    plate.rule(MARGIN, 22, PRINT_WIDTH, "ink", 1.8)
    plate.text("THE WORLD DISPATCH", MARGIN, 40, face="display22", size=.89, color="red")
    plate.text("MONDAY EDITION  /  THROUGH " + edition["cutoff"], RIGHT_EDGE, 39, size=1.12, align=1)
    plate.text(edition["date"], SIDE / 2, 100, face="display55", size=1.32, align=.5, wear=True)

    counts = Counter(item["region"] for item in articles)
    band_width = PRINT_WIDTH / len(edition["regions"])
    for position, region in enumerate(edition["regions"]):
        left = MARGIN + band_width * position
        plate.box(left, 112, band_width, 20, REGION_COLOR[region])
        plate.text(f"{region.upper()}   {counts[region]}", left + band_width / 2, 126,
                   size=.97, color="white", align=.5)

    plate.rule(MARGIN, 139.5, PRINT_WIDTH)
    plate.rule(MARGIN, 162, PRINT_WIDTH)
    plate.text("UTC", MARGIN, 154, size=1.15, color="red")
    timeline = edition["timeline"]
    cell_width = (PRINT_WIDTH - 47) / len(timeline)
    for position, event in enumerate(timeline):
        left = MARGIN + 47 + position * cell_width
        plate.box(left - 6, 144, .65, 14, "rule")
        plate.text(event["time_utc"], left, 153, size=.92, color="red")
        plate.text(event["label"], left + 38, 150, size=.87, width=cell_width - 45)
        plate.text(event["kind"].upper(), left + 38, 158.5, size=.69, color="muted")


def illustration(plate, article, left, top, width, height):
    scene = Scene(plate, left, top, width, height)
    SCENES[article["scene"]](scene)


def lead_story(plate, article):
    width = 612
    end = MARGIN + width
    slug(plate, article, MARGIN, 171, width)
    plate.text(credit(article), end, 181, size=.88, align=1, color=news_color(article))
    for number, title in enumerate(article["lines"]):
        plate.text(title, MARGIN, 226 + 48 * number, face="display55", size=1.03, width=width - 2)
    illustration(plate, article, MARGIN, 283, width, 121)
    plate.text(article["art_caption"], end - 6, 398, size=.74, align=1, color="white")
    plate.paragraph(article["copy"]["summary"], MARGIN, 425, width, face="news14",
                    size=1.2, leading=18, color="ink")
    plate.box(649, 171, .8, 276, "rule")


def side_story(plate, article, top):
    left = 662
    width = RIGHT_EDGE - left
    slug(plate, article, left, top, width)
    plate.text(credit(article), left + width, top + 10, size=.81,
               align=1, color=news_color(article))
    illustration(plate, article, left, top + 17, width, 60)
    title = article["copy"]["headline"]
    plate.text(title, left, top + 99, face="display22", width=width)
    plate.paragraph(article["copy"]["summary"], left, top + 116, width,
                    face="news14", size=.97, leading=13)
    plate.rule(left, top + 134, width)


def dispatches(plate, articles):
    plate.rule(MARGIN, 453, PRINT_WIDTH, "ink", 1.05)
    plate.text("AROUND THE WORLD", MARGIN, 470, size=1.04, color="red")
    width = (PRINT_WIDTH - 36) / 4
    text_width = width - 73
    for position, article in enumerate(articles):
        row, col = divmod(position, 4)
        left, top = MARGIN + col * (width + 12), 479 + row * 77
        slug(plate, article, left, top, width)
        plate.rule(left, top + 13.5, width)
        illustration(plate, article, left + width - 67, top + 17, 67, 46)
        plate.paragraph(article["copy"]["headline"], left, top + 27, text_width,
                        face="news14", size=1.04, leading=13, color="ink")
        plate.paragraph(article["copy"]["summary"], left, top + 49.5, text_width,
                        size=.83, leading=8.2, rows=3)
        plate.text(credit(article), left + width, top + 75, size=.75,
                   align=1, color=news_color(article), width=width)


def briefs(plate, articles):
    plate.text("IN BRIEF", MARGIN, 730, size=1.02, color="red")
    for position, article in enumerate(articles):
        col, row = divmod(position, 11)
        left, top = MARGIN + col * 315, 738 + row * 21
        ink = news_color(article)
        heading = "{id:02}  {place}".format_map(article) + "  /  " + credit(article)
        plate.box(left, top + 1, 3, 17, ink)
        plate.text(heading, left + 7, top + 8, size=.73, color=ink, width=295)
        plate.text(article["copy"]["headline"], left + 7, top + 18.3, size=.94, width=295)
        plate.rule(left, top + 20.2, 304, thickness=.55)


def inside_coast(lon, lat, coast):
    crossings = 0
    for (x0, y0), (x1, y1) in outline_edges(coast):
        if min(y0, y1) <= lat < max(y0, y1) and lon < x0 + (x1 - x0) * (lat - y0) / (y1 - y0):
            crossings += 1
    return crossings % 2 == 1


def locator(plate, articles):
    left, top, height = 662, 733, 135
    width = RIGHT_EDGE - left

    def project(lon, lat):
        x = left + 9 + (lon + 180) * (width - 18) / 360
        y = top + 12 + (85 - lat) * (height - 25) / 146
        return x, y

    plate.text("STORY LOCATOR", left, 730, size=1.03, color="red")
    plate.text("NUMBERS MATCH THE ARTICLES", RIGHT_EDGE, 730, size=.75, align=1, color="muted")
    plate.box(left, top, width, height, "panel")
    plate.frame(left, top, width, height)
    for lat in range(-57, 83, 4):
        for lon in range(-178, 180, 4):
            if any(inside_coast(lon, lat, coast) for coast in COASTLINES):
                x, y = project(lon, lat)
                plate.oval(x - .95, y - .8, 1.9, 1.6, "map")

    badges = []
    for article in articles:
        if "pin" not in article:
            continue
        lon, lat, dx, dy = article["pin"]
        x, y = project(lon, lat)
        center = (x + dx, y + dy)
        ink = news_color(article)
        plate.line(((x, y), center), ink, .7)
        plate.oval(x - 1.4, y - 1.4, 2.8, 2.8, ink)
        badges.append((article["id"], center, ink))
    for number, (x, y), ink in badges:
        plate.oval(x - 7.3, y - 7.3, 14.6, 14.6, "white")
        plate.oval(x - 6.5, y - 6.5, 13, 13, ink)
        plate.text(format(number, "02"), x, y + 2.65, size=.66, color="white", align=.5)


def date_box(plate, notes):
    left, top, height = 662, 876, 91
    width = RIGHT_EDGE - left
    plate.box(left, top, width, height, "panel")
    plate.frame(left, top, width, height)
    plate.text("DATE CHECK", left + 9, top + 16, color="red")
    for row, item in enumerate(notes):
        y = top + 31 + 14 * row
        plate.text(item["subject"].upper(), left + 9, y, size=.79, color="red", width=84)
        plate.text(item["note"], left + 96, y, size=.8, width=width - 105)


def markets_strip(plate, edition):
    plate.rule(MARGIN, 977, PRINT_WIDTH, "ink", 1.15)
    plate.text("MARKETS", MARGIN, 994, size=1.1, color="red")
    plate.text(edition["market_source"], MARGIN, 1007, size=.73, color="muted")
    start = MARGIN + 194
    step = (RIGHT_EDGE - start) / len(edition["markets"])
    for position, quote in enumerate(edition["markets"]):
        x = start + position * step
        plate.box(x - 8, 982, .6, 25, "rule")
        plate.text(quote["index"], x, 994, size=.92, color="red")
        plate.text(quote["value"], x + 58, 995, face="display22", size=.77, width=step - 68)
        plate.text(quote["session"], x, 1007, size=.81, color="muted")
    plate.rule(MARGIN, 1013, PRINT_WIDTH, "ink", 1.1)


def compose(edition):
    plate = Plate()
    sections = edition["stories"]
    lead = sections["lead"]
    side = sections["side"]
    grid = sections["dispatches"]
    short = sections["briefs"]
    articles = (lead, *side, *grid, *short)
    masthead(plate, edition, articles)
    lead_story(plate, lead)
    for top, article in zip((171, 310), side, strict=True):
        side_story(plate, article, top)
    dispatches(plate, grid)
    plate.rule(MARGIN, 715, PRINT_WIDTH, "ink", 1.05)
    briefs(plate, short)
    locator(plate, articles)
    date_box(plate, edition["date_check"])
    markets_strip(plate, edition)
    return plate.cells


def mix_pixel(cells, start):
    middle = start + RASTER_SIDE
    bottom = middle + RASTER_SIDE
    inks = (*cells[start:start + 3], *cells[middle:middle + 3], *cells[bottom:bottom + 3])
    if inks.count(inks[0]) == 9:
        return RGB[inks[0]], inks[0] == 0
    return tuple(sum(channel) // 9 for channel in zip(*(RGB[ink] for ink in inks))), 0 in inks


def scanlines(cells):
    noise = Random(23112026).randbytes(SIDE * SIDE)
    encoded = bytearray()
    for y in range(SIDE):
        encoded.append(1)
        previous = [0, 0, 0]
        row = y * SCALE * RASTER_SIDE
        for x in range(SIDE):
            rgb, bare_paper = mix_pixel(cells, row + x * SCALE)
            wave = int(1.6 * sin(x / 71 + y / 88) + 1.2 * cos(y / 131 - x / 175))
            distance = min(x, y, SIDE - 1 - x, SIDE - 1 - y)
            falloff = -int(max(0, 30 - distance) / 11)
            grain = noise[y * SIDE + x] % (4 if bare_paper else 3) - 1
            shift = wave + falloff + grain
            for index, channel in enumerate(rgb):
                value = max(0, min(255, channel + shift))
                encoded.append((value - previous[index]) & 255)
                previous[index] = value
    return encoded


def chunk(kind, payload):
    data = kind + payload
    return struct.pack(">I", len(payload)) + data + struct.pack(">I", zlib.crc32(data))


def export_png(cells):
    ihdr = struct.pack(">IIBBBBB", SIDE, SIDE, 8, 2, 0, 0, 0)
    data = zlib.compress(scanlines(cells), level=9)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", data) + chunk(b"IEND", b"")


def main():
    manifest = HERE / "edition.json"
    edition = json.loads(manifest.read_text(encoding="utf-8"))
    printed_page = export_png(compose(edition))
    if len(printed_page) > 1024 * 1024:
        raise ValueError(f"Newspaper exceeds the 1 MiB PNG limit: {len(printed_page)} bytes")
    destination = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "entry.png").write_bytes(printed_page)


if __name__ == "__main__":
    main()
