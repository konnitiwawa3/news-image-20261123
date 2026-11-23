"""Spot illustrations in the edition's 100-by-60 drawing coordinates."""

from random import Random


class Scene:
    def __init__(self, canvas, left, top, width, height):
        self.canvas = canvas
        self.left, self.top = left, top
        self.width, self.height = width, height

    def point(self, x, y):
        return self.left + x * self.width / 100, self.top + y * self.height / 60

    def rect(self, ink, x, y, width, height):
        left, top = self.point(x, y)
        self.canvas.box(left, top, width * self.width / 100, height * self.height / 60, ink)

    def ellipse(self, ink, x, y, width, height):
        left, top = self.point(x, y)
        self.canvas.oval(left, top, width * self.width / 100, height * self.height / 60, ink)

    def fill(self, ink, *coordinates):
        points = iter(coordinates)
        self.canvas.polygon([self.point(x, y) for x, y in zip(points, points, strict=True)], ink)

    def stroke(self, ink, weight, *coordinates):
        points = iter(coordinates)
        self.canvas.line([self.point(x, y) for x, y in zip(points, points, strict=True)], ink, weight)

    def horizon(self, edge, above, below):
        self.rect(above, 0, 0, 100, 60)
        self.rect(below, 0, edge, 100, 60 - edge)

    def stipple(self, ink, seed, count, band, longest=3):
        random = Random(seed)
        for _ in range(count):
            x = random.uniform(1, 97)
            y = random.uniform(*band)
            end = min(99, x + random.uniform(.6, longest))
            self.stroke(ink, .46, x, y, end, y - .3)


def draw_harbor(view):
    view.horizon(30, "lead_sky", "lead_water")
    view.ellipse("sun", 78, 4, 12, 15)
    for building in range(15):
        left, rise = building * 7, building % 3
        view.rect("limestone", left, 24 + rise, min(5, 100 - left), 6 - rise)
        view.rect("sand", left + 1, 27, .8, 1.3)
    view.fill("sand", 0, 27, 68, 27, 89, 39, 0, 34)
    view.fill("stone", 0, 31, 69, 29, 89, 39, 77, 41, 0, 36)
    for column in range(0, 79, 5):
        view.stroke("silt", .7, column, 33 + column / 27, column + 1, 35 + column / 28)
    view.stipple("lead_glint", 54, 142, (35, 58), 5)
    for column in range(11, 68, 5):
        height = column / 12
        view.stroke("sand", .55, column, 12 + height, column + 10, 11 + height)
    view.stipple("moss", 21, 57, (47, 58), 5)
    for base, top, arm in ((10, 14, 11), (24, 18, 8), (73, 10, 10)):
        view.stroke("silt", 1.5, base, 27, base, top, base + arm, top + 3)
        hook = base + arm - 1
        view.stroke("stone", .65, hook, top + 3, hook, top + 10)

    view.fill("navy", 24, 45, 32, 37, 77, 36, 89, 39, 96, 40, 89, 45, 39, 51)
    view.fill("slate", 24, 45, 32, 37, 77, 36, 89, 39, 90, 41, 45, 47)
    view.stroke("silver", 1.2, 25, 45, 43, 47, 91, 40)
    view.fill("mist", 40, 37, 48, 35, 51, 27, 70, 26, 78, 35, 73, 39, 47, 41)
    view.fill("steel", 48, 37, 51, 27, 70, 26, 78, 35, 66, 37)
    view.fill("shadow", 56, 29, 71, 28, 73, 31, 55, 32)
    view.fill("slate", 60, 26, 63, 17, 67, 17, 69, 26)
    view.stroke("shadow", 1.1, 65, 18, 65, 10)
    view.stroke("shadow", .8, 61, 15, 69, 15)
    view.fill("steel", 35, 38, 37, 34, 42, 34, 45, 38)
    for column in range(33, 89, 4):
        slope = (column - 32) / 16
        view.stroke("silver", .65, column, 44 - slope, column + 2, 45 - slope)
    for column in range(49, 73, 3):
        view.stroke("slate", .67, column, 34, column + .8, 33.2)
    view.stroke("mist", .9, 28, 51, 49, 52, 66, 48, 91, 47)
    view.stroke("silver", .75, 31, 54, 43, 55, 63, 51, 79, 51)


def draw_tanker(view):
    view.horizon(33, "cream", "sea")
    view.ellipse("sun", 75, 5, 15, 16)
    view.fill("sand", 0, 32, 0, 20, 12, 26, 29, 20, 50, 30, 70, 34)
    view.stipple("silver", 31, 69, (36, 58))
    view.fill("rust", 9, 37, 87, 37, 96, 34, 88, 47, 21, 48)
    view.fill("shadow", 10, 42, 92, 40, 88, 47, 21, 48)
    view.rect("mist", 19, 27, 19, 10)
    view.rect("slate", 23, 22, 12, 6)
    view.stroke("shadow", 1, 31, 23, 31, 18)
    view.stroke("shadow", 1.5, 40, 33, 81, 33, 87, 37)
    for column in range(45, 82, 9):
        view.rect("sand", column, 34, 3, 3)
    view.stroke("mist", .9, 19, 50, 46, 50, 72, 49, 92, 47)


def draw_chips(view):
    view.horizon(43, "shadow", "slate")
    for row in range(9, 57, 8):
        view.stroke("steel", .42, 5, row, 95, row)
    for column in range(7, 96, 9):
        view.stroke("steel", .4, column, 7, column, 55)
    view.stroke("salmon", 2, 6, 15, 23, 24, 31, 15, 47, 38, 55, 35, 71, 49, 94, 51)
    view.stroke("sun", 2, 6, 47, 25, 41, 36, 46, 52, 32, 64, 31, 75, 18, 94, 13)
    view.fill("moss", 35, 23, 51, 15, 66, 25, 53, 36)
    view.fill("sea", 35, 23, 53, 36, 53, 42, 35, 30)
    view.fill("pine", 53, 36, 66, 25, 66, 32, 53, 42)
    view.fill("shadow", 41, 24, 51, 19, 60, 25, 51, 32)
    for lead in range(38, 52, 3):
        pitch = (lead - 38) * .55
        view.stroke("cream", .7, lead, 27 + pitch, lead, 32 + pitch)


def draw_rubble(view):
    view.horizon(34, "haze", "sand")
    view.fill("stone", 6, 46, 11, 18, 25, 19, 25, 10, 36, 12, 40, 31, 53, 38, 61, 58)
    view.fill("silt", 23, 49, 56, 30, 59, 14, 74, 14, 74, 28, 88, 33, 96, 49)
    windows = ((18, 22), (29, 17), (32, 26), (62, 19), (68, 19), (62, 26), (80, 34))
    for left, top in windows:
        view.rect("shadow", left, top, 4, 4)
    debris = ((2, 43, 18), (39, 48, 10), (48, 44, 20), (73, 40, 15), (88, 46, 9))
    for left, top, span in debris:
        edge = left + span
        view.fill("limestone", left, top, edge, top - 3, edge - 2, top + 8, left + 2, top + 10)
    view.stipple("silt", 81, 36, (42, 58))


def draw_summit(view):
    view.horizon(34, "haze", "sea")
    view.fill("pine", 0, 36, 14, 28, 29, 33, 47, 27, 64, 34, 83, 30, 100, 34, 100, 48, 0, 51)
    view.ellipse("sun", 13, 7, 18, 17)
    view.stipple("silver", 12, 54, (46, 59))
    view.rect("shadow", 43, 19, 46, 27)
    view.rect("mist", 47, 22, 38, 21)
    for baseline, width in ((28, 28), (32, 26), (36, 18)):
        view.stroke("sea", 1, 51, baseline, 51 + width, baseline)
    view.fill("rust", 45, 44, 49, 40, 59, 46, 56, 49)
    view.fill("salmon", 77, 43, 81, 40, 91, 44, 88, 48)


def draw_refinery(view):
    view.horizon(41, "slate", "shadow")
    view.ellipse("silt", 63, 5, 27, 21)
    view.ellipse("steel", 51, 12, 26, 18)
    view.ellipse("stone", 58, 20, 15, 21)
    for left, top, width in ((8, 29, 15), (25, 35, 21), (70, 31, 19)):
        view.rect("steel", left, top, width, 19)
        view.ellipse("mist", left, top - 3, width, 6)
        seam = top + 11
        view.stroke("slate", .8, left + 2, seam, left + width - 2, seam)
    for left, top in ((16, 13), (39, 20), (78, 12), (91, 18)):
        view.rect("shadow", left, top, 3, 39 - top)
        view.rect("salmon", left, top + 3, 3, 2)
    view.fill("rust", 48, 51, 52, 34, 57, 44, 62, 30, 66, 43, 71, 49)
    view.fill("sun", 52, 50, 55, 45, 59, 46, 62, 39, 64, 49)
    view.stipple("sand", 77, 42, (52, 58))


def draw_castle(view):
    view.horizon(46, "haze", "sand")
    view.ellipse("sun", 74, 7, 15, 16)
    view.fill("moss", 0, 46, 11, 35, 24, 38, 39, 34, 55, 37, 82, 34, 100, 44, 100, 51, 0, 51)
    view.rect("brick", 22, 30, 56, 20)
    view.rect("rust", 34, 20, 32, 12)
    for pillar in range(27, 73, 9):
        view.rect("sun", pillar, 34, 3, 15)
        view.rect("shadow", pillar + 3, 36, 4, 11)
    view.fill("shadow", 13, 33, 25, 28, 36, 22, 63, 22, 74, 28, 87, 33)
    view.fill("rust", 17, 31, 36, 23, 63, 23, 82, 31)
    view.fill("shadow", 25, 22, 35, 15, 42, 12, 58, 12, 67, 16, 75, 22)
    view.fill("salmon", 30, 21, 42, 13, 58, 13, 69, 21)
    view.stroke("cream", 1.3, 24, 51, 76, 51)


def draw_quake(view):
    view.horizon(19, "haze", "sea")
    view.fill("pine", 44, 17, 54, 10, 61, 13, 71, 17, 65, 19, 50, 19)
    bands = (
        ("steel", (0, 22, 23, 25, 48, 23, 76, 31, 100, 27)),
        ("slate", (0, 34, 26, 36, 47, 34, 69, 44, 100, 37)),
        ("shadow", (0, 46, 22, 48, 50, 43, 72, 54, 100, 50)),
    )
    for ink, crest in bands:
        view.fill(ink, *crest, 100, 60, 0, 60)
    view.stroke("salmon", 1.1, 46, 22, 51, 29, 46, 34, 57, 41, 54, 50)
    view.ellipse("sun", 51, 46, 6, 7)
    view.stroke("cream", 1.2, 8, 51, 19, 51, 22, 47, 25, 54, 28, 36, 32, 53, 38, 50, 44, 50)
    view.stipple("silver", 43, 39, (25, 57))


def draw_runway(view):
    view.horizon(27, "haze", "stone")
    view.fill("slate", 28, 60, 43, 28, 57, 28, 78, 60)
    view.fill("cream", 49, 59, 49, 49, 52, 49, 53, 59)
    for start, end, weight in ((43, 39, 1), (35, 32, .72)):
        view.stroke("cream", weight, 49, start, 49, end)
    view.fill("shadow", 9, 19, 37, 22, 48, 17, 88, 17, 91, 19,
              69, 22, 59, 24, 49, 33, 42, 33, 43, 25, 20, 24)
    view.rect("slate", 79, 13, 4, 14)
    view.fill("slate", 76, 11, 86, 11, 85, 15, 77, 15)
    view.ellipse("brick", 68, 29, 13, 16)
    view.stroke("cream", 1.8, 71, 37, 78, 37)


def draw_cargo(view):
    view.horizon(35, "haze", "sea")
    view.fill("stone", 0, 44, 39, 33, 100, 42, 100, 60, 0, 60)
    view.stroke("slate", 1.2, 13, 45, 13, 12, 48, 12, 39, 26)
    view.stroke("rust", .8, 41, 13, 41, 26)
    view.rect("cream", 36, 26, 10, 7)
    containers = (("rust", 19, 43), ("sea", 42, 45), ("pine", 65, 46),
                  ("limestone", 39, 36), ("sand", 68, 37))
    for ink, left, top in containers:
        view.rect(ink, left, top, 20, 8)
        for seam in range(left + 3, left + 19, 3):
            view.stroke("shadow", .4, seam, top + 1, seam, top + 7)
    view.rect("brick", 47, 37.5, 4, 5)
    view.rect("brick", 45, 39, 8, 2)
    view.stipple("steel", 95, 30, (54, 58))


def draw_port(view):
    view.horizon(32, "haze", "sea")
    view.fill("sand", 0, 38, 0, 25, 43, 25, 57, 22, 70, 26, 100, 32, 100, 42)
    for left, top in ((8, 18), (18, 16), (26, 20), (49, 19), (58, 14), (70, 20)):
        view.rect("limestone", left, top, 7, 26 - top)
        view.rect("stone", left + 1, top + 3, 2, 2)
    for left in (20, 39, 48):
        tip = left + 15
        view.stroke("slate", 1.25, left, 39, left, 13, tip, 16, tip, 25)
    view.fill("brick", 60, 43, 90, 43, 96, 39, 94, 51, 64, 51)
    view.rect("mist", 69, 38, 13, 5)
    view.stipple("silver", 63, 49, (43, 59))


def draw_cabinet(view):
    view.horizon(45, "haze", "stone")
    view.ellipse("cream", 43, 7, 15, 17)
    view.fill("rust", 43, 15, 46, 12, 53, 12, 57, 16, 52, 17, 47, 16)
    view.fill("sea", 43, 15, 47, 16, 52, 17, 57, 16, 54, 21, 47, 21)
    for center in (21, 50, 79):
        view.ellipse("limestone", center - 4, 26, 8, 10)
        view.fill("slate", center - 11, 48, center - 7, 38, center, 36, center + 8, 38, center + 12, 48)
        view.stroke("shadow", .75, center + 2, 45, center + 6, 40, center + 7, 36)
    view.fill("pine", 11, 45, 89, 45, 97, 58, 3, 58)
    view.stroke("moss", .72, 9, 52, 91, 52)


def draw_river(view):
    view.horizon(32, "haze", "moss")
    view.fill("pine", 0, 41, 0, 26, 14, 18, 30, 25, 41, 21, 55, 33, 75, 19, 100, 17, 100, 56)
    view.fill("sea", 64, 30, 81, 33, 45, 44, 53, 50, 89, 60, 23, 60, 24, 49, 38, 40)
    view.fill("silt", 75, 25, 84, 15, 100, 23, 100, 40, 90, 36)
    view.stroke("sand", .75, 83, 21, 99, 26, 88, 27, 98, 32)
    view.stipple("silver", 24, 34, (46, 59))
    view.stroke("cream", 1, 44, 43, 35, 49, 45, 54, 61, 59)


def draw_cameras(view):
    view.horizon(35, "haze", "stone")
    view.fill("slate", 0, 59, 18, 46, 100, 43, 100, 60, 0, 60)
    for stripe in ((13, 57, 36, 55), (51, 54, 76, 51)):
        view.stroke("mist", .8, *stripe)
    view.fill("shadow", 42, 50, 43, 42, 53, 38, 74, 38, 81, 42, 88, 45, 87, 51, 47, 54)
    view.fill("steel", 53, 39, 73, 39, 80, 43, 47, 44)
    view.rect("cream", 71, 47, 8, 3)
    view.ellipse("shadow", 48, 49, 10, 9)
    view.ellipse("shadow", 79, 47, 9, 9)
    view.stroke("shadow", 2, 23, 52, 23, 20, 44, 16)
    view.fill("slate", 41, 10, 57, 10, 64, 16, 63, 23, 53, 23, 42, 17)
    view.ellipse("shadow", 58, 15, 8, 8)
    view.ellipse("silver", 59, 16, 4, 4)
    view.stipple("steel", 8, 28, (47, 58))


def draw_peso(view):
    view.horizon(50, "haze", "slate")
    view.fill("stone", 0, 49, 0, 32, 17, 28, 35, 17, 48, 27, 65, 8, 74, 20, 82, 27, 100, 31, 100, 48)
    view.fill("mist", 23, 24, 35, 17, 49, 27, 65, 8, 78, 24, 68, 21, 65, 16, 55, 27, 47, 30, 33, 22)
    for left, roof in ((10, 42), (22, 38), (34, 44), (47, 38), (72, 44), (84, 40)):
        view.rect("shadow", left, roof, 7, 50 - roof)
    view.ellipse("sand", 61, 24, 25, 25)
    view.ellipse("sun", 65, 27, 18, 19)
    view.stroke("rust", 1.25, 77, 30, 72, 31, 70, 34, 78, 38, 78, 41, 70, 43)
    view.stroke("rust", .9, 74, 29, 74, 45)


SCENES = {
    "benghazi": draw_harbor,
    "tanker": draw_tanker,
    "chips": draw_chips,
    "rubble": draw_rubble,
    "summit": draw_summit,
    "refinery": draw_refinery,
    "castle": draw_castle,
    "quake": draw_quake,
    "runway": draw_runway,
    "cargo": draw_cargo,
    "port": draw_port,
    "cabinet": draw_cabinet,
    "river": draw_river,
    "cameras": draw_cameras,
    "peso": draw_peso,
}
