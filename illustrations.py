"""Original spot illustrations on an engraved, two-ink-inspired print plate."""

from random import Random


class Scene:
    """Draw against a 100-by-60 local grid on the shared raster plate."""

    def __init__(self, press, x, y, w, h):
        self.press = press
        self.x, self.y, self.w, self.h = x, y, w, h

    def xy(self, point):
        x, y = point
        return self.x + x * self.w / 100, self.y + y * self.h / 60

    def block(self, x, y, w, h, ink):
        left, top = self.xy((x, y))
        self.press.box(left, top, w * self.w / 100, h * self.h / 60, ink)

    def poly(self, ink, *points):
        self.press.polygon([self.xy(point) for point in points], ink)

    def line(self, ink, *points, weight=1):
        self.press.line([self.xy(point) for point in points], ink, weight)

    def oval(self, x, y, w, h, ink):
        left, top = self.xy((x, y))
        self.press.oval(left, top, w * self.w / 100, h * self.h / 60, ink)

    def horizon(self, top, bottom, level=34):
        self.block(0, 0, 100, 60, top)
        self.block(0, level, 100, 60 - level, bottom)

    def flecks(self, seed, ink, lower=3, upper=57, count=78, length=3):
        rng = Random(seed)
        for _ in range(count):
            x, y = rng.uniform(1, 97), rng.uniform(lower, upper)
            self.line(ink, (x, y), (min(99, x + rng.uniform(.6, length)), y - .3), weight=.46)


def benghazi(s):
    s.horizon("haze", "sea", 30)
    s.oval(78, 4, 12, 15, "sun")
    for i in range(15):
        x = i * 7
        s.block(x, 24 + i % 3, min(5, 100 - x), 6 - i % 3, "limestone")
        s.block(x + 1, 27, .8, 1.3, "sand")
    s.poly("sand", (0, 27), (68, 27), (89, 39), (0, 34))
    s.poly("stone", (0, 31), (69, 29), (89, 39), (77, 41), (0, 36))
    for x in range(0, 79, 5):
        s.line("silt", (x, 33 + x / 27), (x + 1, 35 + x / 28), weight=.7)
    s.flecks(54, "silver", 35, 58, 185, 6)
    for x in range(11, 68, 5):
        s.line("sand", (x, 12 + x / 12), (x + 10, 11 + x / 12), weight=.55)
    s.flecks(21, "moss", 47, 58, 57, 5)
    for x, y, width in [(10, 14, 11), (24, 18, 8), (73, 10, 10)]:
        s.line("silt", (x, 27), (x, y), (x + width, y + 3), weight=1.5)
        s.line("stone", (x + width - 1, y + 3), (x + width - 1, y + 10), weight=.65)

    # The plate uses a symbolic silhouette of the corvette.
    s.poly("shadow", (24, 45), (32, 37), (77, 36), (89, 39), (96, 40), (89, 45), (39, 51))
    s.poly("slate", (24, 45), (32, 37), (77, 36), (89, 39), (90, 41), (45, 47))
    s.line("silver", (25, 45), (43, 47), (91, 40), weight=1.2)
    s.poly("mist", (40, 37), (48, 35), (51, 27), (70, 26), (78, 35), (73, 39), (47, 41))
    s.poly("steel", (48, 37), (51, 27), (70, 26), (78, 35), (66, 37))
    s.poly("shadow", (56, 29), (71, 28), (73, 31), (55, 32))
    s.poly("slate", (60, 26), (63, 17), (67, 17), (69, 26))
    s.line("shadow", (65, 18), (65, 10), weight=1.1)
    s.line("shadow", (61, 15), (69, 15), weight=.8)
    s.poly("steel", (35, 38), (37, 34), (42, 34), (45, 38))
    for x in range(33, 89, 4):
        s.line("silver", (x, 44 - (x - 32) / 16), (x + 2, 45 - (x - 32) / 16), weight=.65)
    for x in range(49, 73, 3):
        s.line("slate", (x, 34), (x + .8, 33.2), weight=.67)
    s.line("mist", (28, 51), (49, 52), (66, 48), (91, 47), weight=.9)
    s.line("silver", (31, 54), (43, 55), (63, 51), (79, 51), weight=.75)


def tanker(s):
    s.horizon("cream", "sea", 33)
    s.oval(75, 5, 15, 16, "sun")
    s.poly("sand", (0, 32), (0, 20), (12, 26), (29, 20), (50, 30), (70, 34))
    s.flecks(31, "silver", 36, 58, 69)
    s.poly("rust", (9, 37), (87, 37), (96, 34), (88, 47), (21, 48))
    s.poly("shadow", (10, 42), (92, 40), (88, 47), (21, 48))
    s.block(19, 27, 19, 10, "mist")
    s.block(23, 22, 12, 6, "slate")
    s.line("shadow", (31, 23), (31, 18))
    s.line("shadow", (40, 33), (81, 33), (87, 37), weight=1.5)
    for x in (45, 54, 63, 72, 81):
        s.block(x, 34, 3, 3, "sand")
    s.line("mist", (19, 50), (46, 50), (72, 49), (92, 47), weight=.9)


def chips(s):
    s.horizon("shadow", "slate", 43)
    for y in range(9, 57, 8):
        s.line("steel", (5, y), (95, y), weight=.42)
    for x in range(7, 96, 9):
        s.line("steel", (x, 7), (x, 55), weight=.4)
    s.line("salmon", (6, 15), (23, 24), (31, 15), (47, 38), (55, 35), (71, 49), (94, 51), weight=2)
    s.line("sun", (6, 47), (25, 41), (36, 46), (52, 32), (64, 31), (75, 18), (94, 13), weight=2)
    s.poly("moss", (35, 23), (51, 15), (66, 25), (53, 36))
    s.poly("sea", (35, 23), (53, 36), (53, 42), (35, 30))
    s.poly("pine", (53, 36), (66, 25), (66, 32), (53, 42))
    s.poly("shadow", (41, 24), (51, 19), (60, 25), (51, 32))
    for x in range(38, 52, 3):
        offset = (x - 38) * .55
        s.line("cream", (x, 27 + offset), (x, 32 + offset), weight=.7)


def rubble(s):
    s.horizon("haze", "sand", 34)
    s.poly("stone", (6, 46), (11, 18), (25, 19), (25, 10), (36, 12), (40, 31), (53, 38), (61, 58))
    s.poly("silt", (23, 49), (56, 30), (59, 14), (74, 14), (74, 28), (88, 33), (96, 49))
    for x, y in ((18,22),(29,17),(32,26),(62,19),(68,19),(62,26),(80,34)):
        s.block(x, y, 4, 4, "shadow")
    for x, y, w in ((2,43,18),(39,48,10),(48,44,20),(73,40,15),(88,46,9)):
        s.poly("limestone", (x,y), (x+w,y-3), (x+w-2,y+8), (x+2,y+10))
    s.flecks(81, "silt", 42, 58, 36)


def summit(s):
    s.horizon("haze", "sea", 34)
    s.poly("pine", (0,36), (14,28), (29,33), (47,27), (64,34), (83,30), (100,34), (100,48), (0,51))
    s.oval(13,7,18,17,"sun")
    s.flecks(12,"silver",46,59,54)
    s.block(43, 19, 46, 27, "shadow")
    s.block(47, 22, 38, 21, "mist")
    for x, y, w in ((51,28,28),(51,32,26),(51,36,18)):
        s.line("sea", (x,y), (x+w,y), weight=1)
    s.poly("rust", (45,44), (49,40), (59,46), (56,49))
    s.poly("salmon", (77,43), (81,40), (91,44), (88,48))


def refinery(s):
    s.horizon("slate", "shadow", 41)
    s.oval(63, 5, 27, 21, "silt")
    s.oval(51, 12, 26, 18, "steel")
    s.oval(58, 20, 15, 21, "stone")
    for x, y, w in ((8,29,15),(25,35,21),(70,31,19)):
        s.block(x,y,w,19,"steel")
        s.oval(x,y-3,w,6,"mist")
        s.line("slate",(x+2,y+11),(x+w-2,y+11),weight=.8)
    for x, y in ((16,13),(39,20),(78,12),(91,18)):
        s.block(x, y, 3, 39-y, "shadow")
        s.block(x, y+3, 3, 2, "salmon")
    s.poly("rust",(48,51),(52,34),(57,44),(62,30),(66,43),(71,49))
    s.poly("sun",(52,50),(55,45),(59,46),(62,39),(64,49))
    s.flecks(77,"sand",52,58,42)


def castle(s):
    s.horizon("haze", "sand", 46)
    s.oval(74, 7, 15, 16, "sun")
    s.poly("moss", (0,46),(11,35),(24,38),(39,34),(55,37),(82,34),(100,44),(100,51),(0,51))
    s.block(22, 30, 56, 20, "brick")
    s.block(34, 20, 32, 12, "rust")
    for x in (27,36,45,54,63,72):
        s.block(x, 34, 3, 15, "sun")
        s.block(x+3, 36, 4, 11, "shadow")
    s.poly("shadow",(13,33),(25,28),(36,22),(63,22),(74,28),(87,33))
    s.poly("rust",(17,31),(36,23),(63,23),(82,31))
    s.poly("shadow",(25,22),(35,15),(42,12),(58,12),(67,16),(75,22))
    s.poly("salmon",(30,21),(42,13),(58,13),(69,21))
    s.line("cream",(24,51),(76,51),weight=1.3)


def quake(s):
    s.horizon("haze", "sea", 19)
    s.poly("pine",(44,17),(54,10),(61,13),(71,17),(65,19),(50,19))
    s.poly("steel",(0,22),(23,25),(48,23),(76,31),(100,27),(100,60),(0,60))
    s.poly("slate",(0,34),(26,36),(47,34),(69,44),(100,37),(100,60),(0,60))
    s.poly("shadow",(0,46),(22,48),(50,43),(72,54),(100,50),(100,60),(0,60))
    s.line("salmon",(46,22),(51,29),(46,34),(57,41),(54,50),weight=1.1)
    s.oval(51,46,6,7,"sun")
    s.line("cream",(8,51),(19,51),(22,47),(25,54),(28,36),(32,53),(38,50),(44,50),weight=1.2)
    s.flecks(43,"silver",25,57,39)


def runway(s):
    s.horizon("haze", "stone", 27)
    s.poly("slate",(28,60),(43,28),(57,28),(78,60))
    s.poly("cream",(49,59),(49,49),(52,49),(53,59))
    s.line("cream",(49,43),(49,39),weight=1)
    s.line("cream",(49,35),(49,32),weight=.72)
    s.poly("shadow",(9,19),(37,22),(48,17),(88,17),(91,19),(69,22),(59,24),(49,33),(42,33),(43,25),(20,24))
    s.block(79,13,4,14,"slate")
    s.poly("slate",(76,11),(86,11),(85,15),(77,15))
    s.oval(68,29,13,16,"brick")
    s.line("cream",(71,37),(78,37),weight=1.8)


def cargo(s):
    s.horizon("haze", "sea", 35)
    s.poly("stone", (0,44), (39,33), (100,42), (100,60), (0,60))
    s.line("slate", (13,45), (13,12), (48,12), (39,26), weight=1.2)
    s.line("rust", (41,13), (41,26), weight=.8)
    s.block(36, 26, 10, 7, "cream")
    for x, y, color in ((19, 43, "rust"), (42, 45, "sea"), (65, 46, "pine"),
                         (39, 36, "limestone"), (68, 37, "sand")):
        s.block(x, y, 20, 8, color)
        for rib in range(3, 19, 3):
            s.line("shadow", (x + rib, y + 1), (x + rib, y + 7), weight=.4)
    s.block(47, 37.5, 4, 5, "brick")
    s.block(45, 39, 8, 2, "brick")
    s.flecks(95, "steel", 54, 58, 30)


def port(s):
    s.horizon("haze", "sea", 32)
    s.poly("sand",(0,38),(0,25),(43,25),(57,22),(70,26),(100,32),(100,42))
    for x,y in ((8,18),(18,16),(26,20),(49,19),(58,14),(70,20)):
        s.block(x,y,7,26-y,"limestone")
        s.block(x+1,y+3,2,2,"stone")
    for x in (20,39,48):
        s.line("slate",(x,39),(x,13),(x+15,16),(x+15,25),weight=1.25)
    s.poly("brick",(60,43),(90,43),(96,39),(94,51),(64,51))
    s.block(69,38,13,5,"mist")
    s.flecks(63,"silver",43,59,49)


def cabinet(s):
    s.horizon("haze","stone",45)
    s.oval(43,7,15,17,"cream")
    s.poly("rust",(43,15),(46,12),(53,12),(57,16),(52,17),(47,16))
    s.poly("sea",(43,15),(47,16),(52,17),(57,16),(54,21),(47,21))
    for x in (21,50,79):
        s.oval(x-4,26,8,10,"limestone")
        s.poly("slate",(x-11,48),(x-7,38),(x,36),(x+8,38),(x+12,48))
        s.line("shadow",(x+2,45),(x+6,40),(x+7,36),weight=.75)
    s.poly("pine",(11,45),(89,45),(97,58),(3,58))
    s.line("moss",(9,52),(91,52),weight=.72)


def river(s):
    s.horizon("haze","moss",32)
    s.poly("pine",(0,41),(0,26),(14,18),(30,25),(41,21),(55,33),(75,19),(100,17),(100,56))
    s.poly("sea",(64,30),(81,33),(45,44),(53,50),(89,60),(23,60),(24,49),(38,40))
    s.poly("silt",(75,25),(84,15),(100,23),(100,40),(90,36))
    s.line("sand",(83,21),(99,26),(88,27),(98,32),weight=.75)
    s.flecks(24,"silver",46,59,34)
    s.line("cream",(44,43),(35,49),(45,54),(61,59),weight=1)


def cameras(s):
    s.horizon("haze", "stone", 35)
    s.poly("slate", (0, 59), (18, 46), (100, 43), (100, 60), (0, 60))
    s.line("mist", (13, 57), (36, 55), weight=.8)
    s.line("mist", (51, 54), (76, 51), weight=.8)
    s.poly("shadow", (42, 50), (43, 42), (53, 38), (74, 38),
           (81, 42), (88, 45), (87, 51), (47, 54))
    s.poly("steel", (53, 39), (73, 39), (80, 43), (47, 44))
    s.block(71, 47, 8, 3, "cream")
    s.oval(48, 49, 10, 9, "shadow")
    s.oval(79, 47, 9, 9, "shadow")
    s.line("shadow", (23, 52), (23, 20), (44, 16), weight=2)
    s.poly("slate", (41, 10), (57, 10), (64, 16), (63, 23), (53, 23), (42, 17))
    s.oval(58, 15, 8, 8, "shadow")
    s.oval(59, 16, 4, 4, "silver")
    s.flecks(8, "steel", 47, 58, 28)


def peso(s):
    s.horizon("haze","slate",50)
    s.poly("stone",(0,49),(0,32),(17,28),(35,17),(48,27),(65,8),(74,20),(82,27),(100,31),(100,48))
    s.poly("mist",(23,24),(35,17),(49,27),(65,8),(78,24),(68,21),(65,16),(55,27),(47,30),(33,22))
    for x,y in ((10,42),(22,38),(34,44),(47,38),(72,44),(84,40)):
        s.block(x,y,7,50-y,"shadow")
    s.oval(61,24,25,25,"sand")
    s.oval(65,27,18,19,"sun")
    s.line("rust",(77,30),(72,31),(70,34),(78,38),(78,41),(70,43),weight=1.25)
    s.line("rust",(74,29),(74,45),weight=.9)


SCENES = {render.__name__: render for render in (
    benghazi, tanker, chips, rubble, summit, refinery, castle, quake, runway,
    cargo, port, cabinet, river, cameras, peso,
)}
