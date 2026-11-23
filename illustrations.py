"""Original spot art, drawn in a shared frame of 100 by 60 units."""

from itertools import batched
from random import Random


class Scene:
    def __init__(self, plate, x, y, width, height):
        self.surface = plate
        self.x0 = x
        self.y0 = y
        self.width = width
        self.height = height

    def project(self, x, y):
        return self.x0 + x * self.width / 100, self.y0 + y * self.height / 60

    def filled_shape(self, draw, color, x, y, width, height):
        left, top = self.project(x, y)
        draw(left, top, width * self.width / 100, height * self.height / 60, color)

    def rect(self, color, x, y, width, height):
        self.filled_shape(self.surface.box, color, x, y, width, height)

    def ellipse(self, color, x, y, width, height):
        self.filled_shape(self.surface.oval, color, x, y, width, height)

    def project_path(self, coordinates):
        return [self.project(x, y) for x, y in batched(coordinates, 2, strict=True)]

    def fill(self, color, *coordinates):
        self.surface.polygon(self.project_path(coordinates), color)

    def stroke(self, color, width, *coordinates):
        self.surface.line(self.project_path(coordinates), color, width)

    def bands(self, sky, ground, level):
        self.rect(sky, 0, 0, 100, 60)
        self.rect(ground, 0, level, 100, 60 - level)

    def texture(self, color, seed, lower, upper, marks, max_length=3):
        rng = Random(seed)
        for _ in range(marks):
            start = rng.uniform(1, 97)
            y = rng.uniform(lower, upper)
            stop = min(99, start + rng.uniform(.6, max_length))
            self.stroke(color, .46, start, y, stop, y - .3)

    def hline(self, color, x, y, length, width):
        self.stroke(color, width, x, y, x + length, y)


def harbor(p):
    p.bands("haze", "sea", 30)
    p.ellipse("sun", 78, 4, 12, 15)
    for index, x in enumerate(range(0, 99, 7)):
        variation = index % 3
        p.rect("limestone", x, 24 + variation, min(5, 100 - x), 6 - variation)
        p.rect("sand", x + 1, 27, .8, 1.3)
    p.fill("sand", 0, 27, 68, 27, 89, 39, 0, 34)
    p.fill("stone", 0, 31, 69, 29, 89, 39, 77, 41, 0, 36)
    for x in range(0, 79, 5):
        p.stroke("silt", .7, x, 33 + x / 27, x + 1, 35 + x / 28)
    p.texture("silver", 54, 35, 58, 185, 6)
    for x in range(11, 68, 5):
        p.stroke("sand", .55, x, 12 + x / 12, x + 10, 11 + x / 12)
    p.texture("moss", 21, 47, 58, 57, 5)
    for x, top, boom in ((10, 14, 11), (24, 18, 8), (73, 10, 10)):
        p.stroke("silt", 1.5, x, 27, x, top, x + boom, top + 3)
        p.stroke("stone", .65, x + boom - 1, top + 3, x + boom - 1, top + 10)

    # Ship, bridge and mast over layered harbor water.
    p.fill("shadow", 24, 45, 32, 37, 77, 36, 89, 39, 96, 40, 89, 45, 39, 51)
    p.fill("slate", 24, 45, 32, 37, 77, 36, 89, 39, 90, 41, 45, 47)
    p.stroke("silver", 1.2, 25, 45, 43, 47, 91, 40)
    p.fill("mist", 40, 37, 48, 35, 51, 27, 70, 26, 78, 35, 73, 39, 47, 41)
    p.fill("steel", 48, 37, 51, 27, 70, 26, 78, 35, 66, 37)
    p.fill("shadow", 56, 29, 71, 28, 73, 31, 55, 32)
    p.fill("slate", 60, 26, 63, 17, 67, 17, 69, 26)
    p.stroke("shadow", 1.1, 65, 18, 65, 10)
    p.hline("shadow", 61, 15, 8, .8)
    p.fill("steel", 35, 38, 37, 34, 42, 34, 45, 38)
    for x in range(33, 89, 4):
        offset = (x - 32) / 16
        p.stroke("silver", .65, x, 44 - offset, x + 2, 45 - offset)
    for x in range(49, 73, 3):
        p.stroke("slate", .67, x, 34, x + .8, 33.2)
    p.stroke("mist", .9, 28, 51, 49, 52, 66, 48, 91, 47)
    p.stroke("silver", .75, 31, 54, 43, 55, 63, 51, 79, 51)


def oil_route(p):
    p.bands("cream", "sea", 33)
    p.ellipse("sun", 75, 5, 15, 16)
    p.fill("sand", 0, 32, 0, 20, 12, 26, 29, 20, 50, 30, 70, 34)
    p.texture("silver", 31, 36, 58, 69)
    p.fill("rust", 9, 37, 87, 37, 96, 34, 88, 47, 21, 48)
    p.fill("shadow", 10, 42, 92, 40, 88, 47, 21, 48)
    p.rect("mist", 19, 27, 19, 10)
    p.rect("slate", 23, 22, 12, 6)
    p.stroke("shadow", 1, 31, 23, 31, 18)
    p.stroke("shadow", 1.5, 40, 33, 81, 33, 87, 37)
    for x in range(45, 82, 9):
        p.rect("sand", x, 34, 3, 3)
    p.stroke("mist", .9, 19, 50, 46, 50, 72, 49, 92, 47)


def market_circuit(p):
    p.bands("shadow", "slate", 43)
    for y in range(9, 57, 8):
        p.hline("steel", 5, y, 90, .42)
    for x in range(7, 96, 9):
        p.stroke("steel", .4, x, 7, x, 55)
    p.stroke("salmon", 2, 6, 15, 23, 24, 31, 15, 47, 38, 55, 35, 71, 49, 94, 51)
    p.stroke("sun", 2, 6, 47, 25, 41, 36, 46, 52, 32, 64, 31, 75, 18, 94, 13)
    p.fill("moss", 35, 23, 51, 15, 66, 25, 53, 36)
    p.fill("sea", 35, 23, 53, 36, 53, 42, 35, 30)
    p.fill("pine", 53, 36, 66, 25, 66, 32, 53, 42)
    p.fill("shadow", 41, 24, 51, 19, 60, 25, 51, 32)
    for x in range(38, 52, 3):
        offset = (x - 38) * .55
        p.stroke("cream", .7, x, 27 + offset, x, 32 + offset)


def damaged_blocks(p):
    p.bands("haze", "sand", 34)
    p.fill("stone", 6, 46, 11, 18, 25, 19, 25, 10, 36, 12, 40, 31, 53, 38, 61, 58)
    p.fill("silt", 23, 49, 56, 30, 59, 14, 74, 14, 74, 28, 88, 33, 96, 49)
    openings = ((18, 22), (29, 17), (32, 26), (62, 19), (68, 19), (62, 26), (80, 34))
    for x, y in openings:
        p.rect("shadow", x, y, 4, 4)
    debris = ((2, 43, 18), (39, 48, 10), (48, 44, 20), (73, 40, 15), (88, 46, 9))
    for x, y, w in debris:
        p.fill("limestone", x, y, x + w, y - 3, x + w - 2, y + 8, x + 2, y + 10)
    p.texture("silt", 81, 42, 58, 36)


def island_summit(p):
    p.bands("haze", "sea", 34)
    p.fill("pine", 0, 36, 14, 28, 29, 33, 47, 27, 64, 34, 83, 30, 100, 34, 100, 48, 0, 51)
    p.ellipse("sun", 13, 7, 18, 17)
    p.texture("silver", 12, 46, 59, 54)
    p.rect("shadow", 43, 19, 46, 27)
    p.rect("mist", 47, 22, 38, 21)
    for top, length in zip((28, 32, 36), (28, 26, 18), strict=True):
        p.hline("sea", 51, top, length, 1)
    p.fill("rust", 45, 44, 49, 40, 59, 46, 56, 49)
    p.fill("salmon", 77, 43, 81, 40, 91, 44, 88, 48)


def smoke_over_tanks(p):
    p.bands("slate", "shadow", 41)
    for color, x, y, w, h in (
        ("silt", 63, 5, 27, 21), ("steel", 51, 12, 26, 18), ("stone", 58, 20, 15, 21),
    ):
        p.ellipse(color, x, y, w, h)
    for x, y, width in ((8, 29, 15), (25, 35, 21), (70, 31, 19)):
        p.rect("steel", x, y, width, 19)
        p.ellipse("mist", x, y - 3, width, 6)
        p.hline("slate", x + 2, y + 11, width - 4, .8)
    for x, y in ((16, 13), (39, 20), (78, 12), (91, 18)):
        p.rect("shadow", x, y, 3, 39 - y)
        p.rect("salmon", x, y + 3, 3, 2)
    p.fill("rust", 48, 51, 52, 34, 57, 44, 62, 30, 66, 43, 71, 49)
    p.fill("sun", 52, 50, 55, 45, 59, 46, 62, 39, 64, 49)
    p.texture("sand", 77, 52, 58, 42)


def shuri(p):
    p.bands("haze", "sand", 46)
    p.ellipse("sun", 74, 7, 15, 16)
    p.fill("moss", 0, 46, 11, 35, 24, 38, 39, 34, 55, 37, 82, 34, 100, 44, 100, 51, 0, 51)
    p.rect("brick", 22, 30, 56, 20)
    p.rect("rust", 34, 20, 32, 12)
    for x in range(27, 73, 9):
        p.rect("sun", x, 34, 3, 15)
        p.rect("shadow", x + 3, 36, 4, 11)
    p.fill("shadow", 13, 33, 25, 28, 36, 22, 63, 22, 74, 28, 87, 33)
    p.fill("rust", 17, 31, 36, 23, 63, 23, 82, 31)
    p.fill("shadow", 25, 22, 35, 15, 42, 12, 58, 12, 67, 16, 75, 22)
    p.fill("salmon", 30, 21, 42, 13, 58, 13, 69, 21)
    p.hline("cream", 24, 51, 52, 1.3)


def seafloor(p):
    p.bands("haze", "sea", 19)
    p.fill("pine", 44, 17, 54, 10, 61, 13, 71, 17, 65, 19, 50, 19)
    strata = (
        ("steel", (0, 22, 23, 25, 48, 23, 76, 31, 100, 27)),
        ("slate", (0, 34, 26, 36, 47, 34, 69, 44, 100, 37)),
        ("shadow", (0, 46, 22, 48, 50, 43, 72, 54, 100, 50)),
    )
    for color, profile in strata:
        p.fill(color, *profile, 100, 60, 0, 60)
    p.stroke("salmon", 1.1, 46, 22, 51, 29, 46, 34, 57, 41, 54, 50)
    p.ellipse("sun", 51, 46, 6, 7)
    p.stroke("cream", 1.2, 8, 51, 19, 51, 22, 47, 25, 54, 28, 36, 32, 53, 38, 50, 44, 50)
    p.texture("silver", 43, 25, 57, 39)


def closed_airfield(p):
    p.bands("haze", "stone", 27)
    p.fill("slate", 28, 60, 43, 28, 57, 28, 78, 60)
    p.fill("cream", 49, 59, 49, 49, 52, 49, 53, 59)
    p.stroke("cream", 1, 49, 43, 49, 39)
    p.stroke("cream", .72, 49, 35, 49, 32)
    p.fill("shadow", 9, 19, 37, 22, 48, 17, 88, 17, 91, 19, 69, 22, 59, 24,
           49, 33, 42, 33, 43, 25, 20, 24)
    p.rect("slate", 79, 13, 4, 14)
    p.fill("slate", 76, 11, 86, 11, 85, 15, 77, 15)
    p.ellipse("brick", 68, 29, 13, 16)
    p.hline("cream", 71, 37, 7, 1.8)


def container_terminal(p):
    p.bands("haze", "sea", 35)
    p.fill("stone", 0, 44, 39, 33, 100, 42, 100, 60, 0, 60)
    p.stroke("slate", 1.2, 13, 45, 13, 12, 48, 12, 39, 26)
    p.stroke("rust", .8, 41, 13, 41, 26)
    p.rect("cream", 36, 26, 10, 7)
    containers = (
        ("rust", 19, 43), ("sea", 42, 45), ("pine", 65, 46),
        ("limestone", 39, 36), ("sand", 68, 37),
    )
    for color, x, y in containers:
        p.rect(color, x, y, 20, 8)
        for rib in range(x + 3, x + 19, 3):
            p.stroke("shadow", .4, rib, y + 1, rib, y + 7)
    p.rect("brick", 47, 37.5, 4, 5)
    p.rect("brick", 45, 39, 8, 2)
    p.texture("steel", 95, 54, 58, 30)


def red_sea_port(p):
    p.bands("haze", "sea", 32)
    p.fill("sand", 0, 38, 0, 25, 43, 25, 57, 22, 70, 26, 100, 32, 100, 42)
    shoreline = ((8, 18), (18, 16), (26, 20), (49, 19), (58, 14), (70, 20))
    for x, roof in shoreline:
        p.rect("limestone", x, roof, 7, 26 - roof)
        p.rect("stone", x + 1, roof + 3, 2, 2)
    for x in (20, 39, 48):
        tip = x + 15
        p.stroke("slate", 1.25, x, 39, x, 13, tip, 16, tip, 25)
    p.fill("brick", 60, 43, 90, 43, 96, 39, 94, 51, 64, 51)
    p.rect("mist", 69, 38, 13, 5)
    p.texture("silver", 63, 43, 59, 49)


def ministers(p):
    p.bands("haze", "stone", 45)
    p.ellipse("cream", 43, 7, 15, 17)
    p.fill("rust", 43, 15, 46, 12, 53, 12, 57, 16, 52, 17, 47, 16)
    p.fill("sea", 43, 15, 47, 16, 52, 17, 57, 16, 54, 21, 47, 21)
    for x in (21, 50, 79):
        p.ellipse("limestone", x - 4, 26, 8, 10)
        p.fill("slate", x - 11, 48, x - 7, 38, x, 36, x + 8, 38, x + 12, 48)
        p.stroke("shadow", .75, x + 2, 45, x + 6, 40, x + 7, 36)
    p.fill("pine", 11, 45, 89, 45, 97, 58, 3, 58)
    p.hline("moss", 9, 52, 82, .72)


def border_river(p):
    p.bands("haze", "moss", 32)
    p.fill("pine", 0, 41, 0, 26, 14, 18, 30, 25, 41, 21, 55, 33, 75, 19, 100, 17, 100, 56)
    p.fill("sea", 64, 30, 81, 33, 45, 44, 53, 50, 89, 60, 23, 60, 24, 49, 38, 40)
    p.fill("silt", 75, 25, 84, 15, 100, 23, 100, 40, 90, 36)
    p.stroke("sand", .75, 83, 21, 99, 26, 88, 27, 98, 32)
    p.texture("silver", 24, 46, 59, 34)
    p.stroke("cream", 1, 44, 43, 35, 49, 45, 54, 61, 59)


def roadside_reader(p):
    p.bands("haze", "stone", 35)
    p.fill("slate", 0, 59, 18, 46, 100, 43, 100, 60, 0, 60)
    p.stroke("mist", .8, 13, 57, 36, 55)
    p.stroke("mist", .8, 51, 54, 76, 51)
    p.fill("shadow", 42, 50, 43, 42, 53, 38, 74, 38, 81, 42, 88, 45, 87, 51, 47, 54)
    p.fill("steel", 53, 39, 73, 39, 80, 43, 47, 44)
    p.rect("cream", 71, 47, 8, 3)
    p.ellipse("shadow", 48, 49, 10, 9)
    p.ellipse("shadow", 79, 47, 9, 9)
    p.stroke("shadow", 2, 23, 52, 23, 20, 44, 16)
    p.fill("slate", 41, 10, 57, 10, 64, 16, 63, 23, 53, 23, 42, 17)
    p.ellipse("shadow", 58, 15, 8, 8)
    p.ellipse("silver", 59, 16, 4, 4)
    p.texture("steel", 8, 47, 58, 28)


def andes_currency(p):
    p.bands("haze", "slate", 50)
    p.fill("stone", 0, 49, 0, 32, 17, 28, 35, 17, 48, 27, 65, 8, 74, 20, 82, 27, 100, 31, 100, 48)
    p.fill("mist", 23, 24, 35, 17, 49, 27, 65, 8, 78, 24, 68, 21, 65, 16, 55, 27, 47, 30, 33, 22)
    for left, roof in ((10, 42), (22, 38), (34, 44), (47, 38), (72, 44), (84, 40)):
        p.rect("shadow", left, roof, 7, 50 - roof)
    p.ellipse("sand", 61, 24, 25, 25)
    p.ellipse("sun", 65, 27, 18, 19)
    p.stroke("rust", 1.25, 77, 30, 72, 31, 70, 34, 78, 38, 78, 41, 70, 43)
    p.stroke("rust", .9, 74, 29, 74, 45)


SCENES = dict(
    benghazi=harbor,
    tanker=oil_route,
    chips=market_circuit,
    rubble=damaged_blocks,
    summit=island_summit,
    refinery=smoke_over_tanks,
    castle=shuri,
    quake=seafloor,
    runway=closed_airfield,
    cargo=container_terminal,
    port=red_sea_port,
    cabinet=ministers,
    river=border_river,
    cameras=roadside_reader,
    peso=andes_currency,
)
