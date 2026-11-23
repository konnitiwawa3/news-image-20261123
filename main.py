"""Compose the World Dispatch front page and export its deterministic print."""

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
# Safe-path mode omits the script directory, which contains the scene module.
sys.path.insert(0, str(ASSET_DIR))

from illustrations import SCENES, Scene

PAGE_SIZE = 1024
SUPERSAMPLE = 3
PLATE_WIDTH = PAGE_SIZE * SUPERSAMPLE
LEFT = 26
RIGHT = PAGE_SIZE - LEFT
BODY_WIDTH = RIGHT - LEFT
PAPER_RGB = (247, 239, 220)

REGION_INK = {
    "Europe": "europe",
    "Middle East": "middle_east",
    "Africa": "africa",
    "Asia": "asia",
    "Oceania": "oceania",
    "N. America": "north_america",
    "Latin America": "latin_america",
}
# Astryx Stone Light neutral 15 and region colors at stop 30.
PRINT_COLORS = {
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
INK_INDEX = {name: number for number, name in enumerate(PRINT_COLORS, start=1)}
RGB_BY_INK = (PAPER_RGB, *(tuple(bytes.fromhex(rgb)) for rgb in PRINT_COLORS.values()))
GLYPH_SUBSTITUTIONS = str.maketrans({"·": "|", "−": "-", "\u00a0": " "})


class PrintPlate:
    def __init__(self):
        self.pixels = bytearray(PLATE_WIDTH * PLATE_WIDTH)
        font_bytes = (ASSET_DIR / "materials" / "glyphs.json.z").read_bytes()
        self.fonts = json.loads(zlib.decompress(font_bytes))

    def paint_span(self, row, start, stop, ink):
        start = max(0, start)
        stop = min(PLATE_WIDTH, stop)
        if start >= stop or row < 0 or row >= PLATE_WIDTH:
            return
        offset = row * PLATE_WIDTH
        self.pixels[offset + start:offset + stop] = bytes([ink]) * (stop - start)

    def box(self, x, y, w, h, color):
        left = round(x * SUPERSAMPLE)
        top = round(y * SUPERSAMPLE)
        right = round((x + w) * SUPERSAMPLE)
        bottom = round((y + h) * SUPERSAMPLE)
        ink = INK_INDEX[color]
        for row in range(max(top, 0), min(bottom, PLATE_WIDTH)):
            self.paint_span(row, left, right, ink)

    def line(self, points, color, weight=1):
        for start, end in zip(points, points[1:]):
            x, y = start
            dx, dy = end[0] - x, end[1] - y
            samples = max(1, round(SUPERSAMPLE * max(abs(dx), abs(dy))))
            for index in range(samples + 1):
                t = index / samples
                self.box(x + dx * t - weight / 2, y + dy * t - weight / 2, weight, weight, color)

    def polygon(self, points, color):
        vertices = [(x * SUPERSAMPLE, y * SUPERSAMPLE) for x, y in points]
        sides = list(zip(vertices, vertices[1:] + vertices[:1]))
        top = max(0, int(min(y for _, y in vertices)))
        bottom = min(PLATE_WIDTH, round(max(y for _, y in vertices)))
        ink = INK_INDEX[color]
        for row in range(top, bottom):
            sample_y = row + .5
            intersections = []
            for (ax, ay), (bx, by) in sides:
                if min(ay, by) <= sample_y < max(ay, by):
                    ix = ax + (bx - ax) * (sample_y - ay) / (by - ay)
                    intersections.append(ix)
            intersections.sort()
            for left, right in zip(intersections[::2], intersections[1::2], strict=True):
                self.paint_span(row, round(left), round(right), ink)

    def oval(self, x, y, w, h, color):
        outline = []
        for n in range(32):
            angle = n * tau / 32
            outline.append((x + w / 2 * (1 + cos(angle)), y + h / 2 * (1 + sin(angle))))
        self.polygon(outline, color)

    def rule(self, x, y, width, color="hairline", thickness=.8):
        self.box(x, y, width, thickness, color)

    def frame(self, x, y, w, h, color="rule"):
        self.rule(x, y, w, color)
        self.rule(x, y + h, w, color)
        self.box(x, y, .8, h, color)
        self.box(x + w - .8, y, .8, h, color)

    @lru_cache(maxsize=3600)
    def glyph_pixels(self, face, char, zoom):
        _, dx, dy, width, height, mask = self.fonts[face][char]
        bits = bytes.fromhex(mask)
        row_bytes = (width + 7) // 8
        origin_x = round(dx * zoom)
        origin_y = round(dy * zoom)
        points = []
        for y in range(round(height * zoom)):
            source_y = min(height - 1, int(y / zoom))
            for x in range(round(width * zoom)):
                source_x = min(width - 1, int(x / zoom))
                mask_byte = bits[source_y * row_bytes + source_x // 8]
                if mask_byte & (128 >> (source_x % 8)):
                    points.append((origin_x + x, origin_y + y))
        return points

    def width(self, text, face, zoom):
        advances = self.fonts[face]
        text = text.translate(GLYPH_SUBSTITUTIONS)
        return sum(round(advances[letter][0] * zoom) for letter in text) / SUPERSAMPLE

    def text(self, value, x, y, *, face="news12", size=1, color="ink", align=0, wear=False, width=None):
        value = value.translate(GLYPH_SUBSTITUTIONS)
        if width is not None:
            while self.width(value, face, size) > width:
                size -= .01
                if size < .5:
                    raise ValueError(f"Text exceeds its box: {value}")
        cursor = round((x - align * self.width(value, face, size)) * SUPERSAMPLE)
        baseline = round(y * SUPERSAMPLE)
        ink = INK_INDEX[color]
        for index, letter in enumerate(value):
            tone = (index * 101 + cursor * 541 + baseline) % 19
            visible_ink = INK_INDEX["ink_light"] if wear and tone < 4 else ink
            for dx, dy in self.glyph_pixels(face, letter, size):
                px = cursor + dx
                py = baseline + dy
                if not (0 <= px < PLATE_WIDTH and 0 <= py < PLATE_WIDTH):
                    continue
                grain = (px * 83 ^ py * 173 ^ tone * 13) % 521
                if wear and grain < 5:
                    continue
                offset = py * PLATE_WIDTH + px
                self.pixels[offset] = visible_ink
                if wear and grain > 516 and px + 1 < PLATE_WIDTH and not self.pixels[offset + 1]:
                    self.pixels[offset + 1] = INK_INDEX["rule"]
            cursor += round(self.fonts[face][letter][0] * size)

    def wrap(self, value, width, face, size):
        first, *rest = value.split()
        current_line = first
        lines = []
        for word in rest:
            next_line = f"{current_line} {word}"
            if self.width(next_line, face, size) <= width:
                current_line = next_line
            else:
                lines.append(current_line)
                current_line = word
        return [*lines, current_line]

    def paragraph(self, value, x, y, width, *, face="news12", size=1, leading=14, rows=2, color="muted"):
        lines = self.wrap(value, width, face, size)
        while len(lines) > rows and size > .65:
            size -= .02
            lines = self.wrap(value, width, face, size)
        if len(lines) > rows:
            raise ValueError(f"Paragraph exceeds {rows} lines: {value}")
        for number, line in enumerate(lines):
            self.text(line, x, y + number * leading, face=face, size=size, color=color, width=width)


# Simplified coastline for the equirectangular story locator.
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
    return REGION_INK[story["region"]]


def source_line(story):
    return f"{story['tag']}  /  {story['source']}"


def story_label(plate, story, x, y, width):
    ink = color_of(story)
    plate.box(x, y, 20, 13, ink)
    plate.text(f"{story['id']:02}", x + 10, y + 10.3, size=.86, color="white", align=.5)
    plate.text(story["place"], x + 25, y + 10, size=.86, color=ink, width=width - 27)


def draw_header(plate, edition):
    plate.rule(LEFT, 22, BODY_WIDTH, "ink", 1.8)
    plate.text("THE WORLD DISPATCH", LEFT, 40, face="display22", size=.89, color="red")
    line = f"MONDAY EDITION  /  THROUGH {edition['cutoff']}"
    plate.text(line, RIGHT, 39, size=1.12, align=1)
    plate.text(edition["date"], PAGE_SIZE / 2, 100, face="display55", size=1.32, align=.5, wear=True)

    by_region = Counter(article["region"] for article in edition["stories"])
    region_span = BODY_WIDTH / len(REGION_INK)
    for index, region in enumerate(REGION_INK):
        block_left = LEFT + index * region_span
        plate.box(block_left, 112, region_span, 20, REGION_INK[region])
        plate.text(f"{region.upper()}   {by_region[region]}", block_left + region_span / 2, 126,
                   size=.97, align=.5, color="white")

    for y in (139.5, 162):
        plate.rule(LEFT, y, BODY_WIDTH)
    plate.text("UTC", LEFT, 154, size=1.15, color="red")
    time_span = (BODY_WIDTH - 47) / len(edition["timeline"])
    for index, event in enumerate(edition["timeline"]):
        column = LEFT + 47 + index * time_span
        plate.box(column - 6, 144, .65, 14, "rule")
        plate.text(event["time_utc"], column, 153, size=.92, color="red")
        plate.text(event["label"], column + 38, 150, size=.87, width=time_span - 45)
        plate.text(event["kind"].upper(), column + 38, 158.5, size=.69, color="muted")


def paint_scene(plate, story, frame):
    SCENES[story["scene"]](Scene(plate, *frame))


def draw_top_stories(plate, primary, secondary):
    lead_width = 612
    lead_right = LEFT + lead_width
    story_label(plate, primary, LEFT, 171, lead_width)
    plate.text(source_line(primary), lead_right, 181, size=.88, align=1, color=color_of(primary))
    for index, line in enumerate(primary["lines"]):
        plate.text(line, LEFT, 226 + 48 * index, face="display55", size=1.03, width=lead_width - 2)
    paint_scene(plate, primary, (LEFT, 283, lead_width, 121))
    plate.text("ILLUSTRATION  /  BENGHAZI HARBOR", lead_right - 6, 398, size=.74, align=1, color="white")
    plate.paragraph(primary["detail"], LEFT, 425, lead_width, face="news14", size=1.2,
                    leading=18, rows=2, color="ink")
    plate.box(649, 171, .8, 276, "rule")

    column_left = 662
    column_width = RIGHT - column_left
    for top, story in zip((171, 310), secondary, strict=True):
        story_label(plate, story, column_left, top, column_width)
        plate.text(source_line(story), column_left + column_width, top + 10, size=.81, align=1,
                   color=color_of(story))
        paint_scene(plate, story, (column_left, top + 17, column_width, 60))
        plate.text(story["title"], column_left, top + 99, face="display22", size=1, width=column_width)
        plate.paragraph(story["detail"], column_left, top + 116, column_width, face="news14",
                        size=.97, leading=13, rows=2)
        plate.rule(column_left, top + 134, column_width)


def draw_dispatch_grid(plate, stories):
    plate.rule(LEFT, 453, BODY_WIDTH, "ink", 1.05)
    plate.text("AROUND THE WORLD", LEFT, 470, size=1.04, color="red")
    gutter = 12
    column_width = (BODY_WIDTH - 3 * gutter) / 4
    copy_width = column_width - 73
    for index, story in enumerate(stories):
        row, column = divmod(index, 4)
        x = LEFT + column * (column_width + gutter)
        y = 479 + row * 77
        story_label(plate, story, x, y, column_width)
        plate.rule(x, y + 13.5, column_width)
        paint_scene(plate, story, (x + column_width - 67, y + 17, 67, 46))
        plate.paragraph(story["title"], x, y + 27, copy_width, face="news14",
                        size=1.04, leading=13, color="ink")
        plate.paragraph(story["detail"], x, y + 49.5, copy_width, size=.83, leading=8.2, rows=3)
        plate.text(source_line(story), x + column_width, y + 75, size=.75, align=1,
                   color=color_of(story), width=column_width)


def draw_briefs(plate, stories):
    plate.text("IN BRIEF", LEFT, 730, size=1.02, color="red")
    for index, story in enumerate(stories):
        column, row = divmod(index, 11)
        x = LEFT + column * 315
        y = 738 + row * 21
        ink = color_of(story)
        label = f"{story['id']:02}  {story['place']}  /  {source_line(story)}"
        plate.box(x, y + 1, 3, 17, ink)
        plate.text(label, x + 7, y + 8, size=.73, color=ink, width=295)
        plate.text(story["title"], x + 7, y + 18.3, size=.94, width=295)
        plate.rule(x, y + 20.2, 304, thickness=.55)


def point_on_land(lon, lat, outline):
    land = False
    for (ax, ay), (bx, by) in zip(outline, outline[1:] + outline[:1]):
        if min(ay, by) <= lat < max(ay, by):
            if lon < ax + (bx - ax) * (lat - ay) / (by - ay):
                land = not land
    return land


def draw_locator(plate, stories):
    x, y = 662, 733
    width, height = RIGHT - x, 135
    plate.text("STORY LOCATOR", x, 730, size=1.03, color="red")
    plate.text("NUMBERS MATCH THE ARTICLES", RIGHT, 730, size=.75, align=1, color="muted")
    plate.box(x, y, width, height, "panel")
    plate.frame(x, y, width, height)

    def project(lon, lat):
        return (
            x + 9 + (lon + 180) * (width - 18) / 360,
            y + 12 + (85 - lat) * (height - 25) / 146,
        )

    for lat in range(-57, 83, 4):
        for lon in range(-178, 180, 4):
            if any(point_on_land(lon, lat, outline) for outline in LAND):
                px, py = project(lon, lat)
                plate.oval(px - .95, py - .8, 1.9, 1.6, "map")

    positions = []
    for story in stories:
        pin = story.get("pin")
        if pin is None:
            continue
        lon, lat, dx, dy = pin
        px, py = project(lon, lat)
        label_x, label_y = px + dx, py + dy
        ink = color_of(story)
        plate.line(((px, py), (label_x, label_y)), ink, .7)
        plate.oval(px - 1.4, py - 1.4, 2.8, 2.8, ink)
        positions.append((story["id"], label_x, label_y, ink))

    # Place all number discs on top of the leader lines.
    for number, cx, cy, ink in positions:
        plate.oval(cx - 7.3, cy - 7.3, 14.6, 14.6, "white")
        plate.oval(cx - 6.5, cy - 6.5, 13, 13, ink)
        plate.text(f"{number:02}", cx, cy + 2.65, size=.66, color="white", align=.5)


def draw_date_notes(plate, notes):
    left, top = 662, 876
    width = RIGHT - left
    plate.box(left, top, width, 91, "panel")
    plate.frame(left, top, width, 91)
    plate.text("DATE CHECK", left + 9, top + 16, size=1, color="red")
    for index, item in enumerate(notes):
        baseline = top + 31 + 14 * index
        plate.text(item["subject"].upper(), left + 9, baseline, size=.79, color="red", width=84)
        plate.text(item["note"], left + 96, baseline, size=.80, width=width - 105)


def draw_market_strip(plate, edition):
    plate.rule(LEFT, 977, BODY_WIDTH, "ink", 1.15)
    plate.text("MARKETS", LEFT, 994, size=1.1, color="red")
    plate.text(edition["market_source"], LEFT, 1007, size=.73, color="muted")
    first = LEFT + 194
    spacing = (RIGHT - first) / len(edition["markets"])
    for index, quote in enumerate(edition["markets"]):
        x = first + index * spacing
        plate.box(x - 8, 982, .6, 25, "rule")
        plate.text(quote["index"], x, 994, size=.92, color="red")
        plate.text(quote["value"], x + 58, 995, face="display22", size=.77, width=spacing - 68)
        plate.text(quote["session"], x, 1007, size=.81, color="muted")
    plate.rule(LEFT, 1013, BODY_WIDTH, "ink", 1.1)


def layout_page(edition):
    plate = PrintPlate()
    articles = edition["stories"]
    draw_header(plate, edition)
    draw_top_stories(plate, articles[0], articles[1:3])
    draw_dispatch_grid(plate, articles[3:15])
    plate.rule(LEFT, 715, BODY_WIDTH, "ink", 1.05)
    draw_briefs(plate, articles[15:])
    draw_locator(plate, articles)
    draw_date_notes(plate, edition["date_check"])
    draw_market_strip(plate, edition)
    return plate.pixels


def sample(plate, high_x, high_y):
    first = high_y * PLATE_WIDTH + high_x
    second = first + PLATE_WIDTH
    third = second + PLATE_WIDTH
    samples = (
        plate[first], plate[first + 1], plate[first + 2],
        plate[second], plate[second + 1], plate[second + 2],
        plate[third], plate[third + 1], plate[third + 2],
    )
    if samples.count(samples[0]) == len(samples):
        return RGB_BY_INK[samples[0]], samples[0] == 0
    channels = zip(*(RGB_BY_INK[ink] for ink in samples))
    return tuple(sum(channel) // len(samples) for channel in channels), 0 in samples


def filtered_rows(plate):
    speckle = Random(23112026).randbytes(PAGE_SIZE ** 2)
    rows = bytearray()
    for y in range(PAGE_SIZE):
        previous = [0, 0, 0]
        rows.append(1)  # PNG Sub filter, reset at the start of each row.
        for x in range(PAGE_SIZE):
            rgb, paper_visible = sample(plate, x * SUPERSAMPLE, y * SUPERSAMPLE)
            grain = speckle[y * PAGE_SIZE + x]
            aging = int(1.6 * sin(x / 71 + y / 88) + 1.2 * cos(y / 131 - x / 175))
            edge_distance = min(x, y, PAGE_SIZE - x - 1, PAGE_SIZE - y - 1)
            edge = -int(max(0, 30 - edge_distance) / 11)
            noise = aging + edge + (grain % (4 if paper_visible else 3) - 1)
            for channel, ink in enumerate(rgb):
                value = min(255, max(0, ink + noise))
                rows.append((value - previous[channel]) & 255)
                previous[channel] = value
    return rows


def png_chunk(tag, payload):
    contents = tag + payload
    return struct.pack(">I", len(payload)) + contents + struct.pack(">I", zlib.crc32(contents))


def encode_png(plate):
    header = struct.pack(">IIBBBBB", PAGE_SIZE, PAGE_SIZE, 8, 2, 0, 0, 0)
    raster = zlib.compress(filtered_rows(plate), level=9)
    return b"".join((
        b"\x89PNG\r\n\x1a\n",
        png_chunk(b"IHDR", header),
        png_chunk(b"IDAT", raster),
        png_chunk(b"IEND", b""),
    ))


def main():
    edition = json.loads((ASSET_DIR / "edition.json").read_text(encoding="utf-8"))
    png = encode_png(layout_page(edition))
    if len(png) > 1024 ** 2:
        raise ValueError(f"PNG exceeds 1 MiB: {len(png)}")
    output = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    output.mkdir(parents=True, exist_ok=True)
    (output / "entry.png").write_bytes(png)


if __name__ == "__main__":
    main()
