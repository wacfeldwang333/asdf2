# ZebraCrossings, Lights, Sidewalks, Portals, MindControllers, stuff that matters but seems "virtual"
# Sidewalks are here because they work with ZCs

import concrete, entities


class ZebraCrossing:
    # where pedestrians cross; pedestrians do not move, but take x time to cross
    # since by law you aren't allowed to drive if the pedestrians are anywhere on the pavement
    # belongs to Road object

    def __init__(self, parent):  # parent is a Road
        # when a pedestrian is crossing it adds 1 to numberofpedestrians, when it leaves it subtracts 1
        # the crossing checks when numberofpedestrians == 0 and then it becomes not occupied
        self.occupied = False
        self.peds = []
        self.parentroad = parent
        self.pedlight = Light(self)
        self.buttonpushed = False  # does what those buttons on telephone poles do IRL

        self.sw1 = self.parentroad.sw1
        self.sw2 = self.parentroad.sw2

    self.length = None  # FON, probably should be random

    def onetick(self):
        if self.buttonpushed:
            self.buttonpushed = False
            # TODO: do stuff

        for p in self.peds:
            p.ticksfromspawn += 1
            p.walkingtimeleft -= 1
            if p.walkingtimeleft <= 0:
                p.parent = p.currtarsw
                p.currtarsw = None
                p.justgothere = True

    def getrelad(self, sw):  # oxymoron?
        # we get the absolute direction of this ZC, relative to one of its adjacent sidewalks
        road = self.parentroad
        if sw == road.sw1:  # then it's on the right side, relative to the road
            return (road.absolutedir - 1) % 4
        else:
            return (road.absolutedir + 1) % 4
        print("Error in ZebraCrossin.retrelad()")

    def getoppositesw(self, sw):
        return self.sw1 if sw == self.sw2 else self.sw2


class Light:  # applies to traffic and pedestrian lights, since they are effectively the same, except in timing
    def __init__(self, parent):  # will figure out parenttype on its own
        self.state = 2  # same characters for pedestrian lights, in the matching which makes sense
        # ^ 0 is green, 1 is yellow, 2 is red
        self.parenttype = 'z' if type(parent) is ZebraCrossing else 'r'
        self.parent = parent  # can be road or zebra crossing

        self.yellowtimeleft = None

    yellowtime = None  # FON, the amount of time a light will be yellow


class Sidewalk:
    # small square at the four corners of intersections, where pedestrians stay when not crossing roads
    def __init__(self, p, c1, c2):
        self.parent = p
        self.peds = []
        self.crossing1, self.crossing2 = c1, c2

        # roads are from right to left, Sidewalk's perspective facing the Middle
        self.road1 = crossing1.parentroad
        self.road2 = crossing2.parentroad

    def onetick(self):
        for p in self.peds:
            p.ticksfromspawn += 1
            if p.justgothere:
                p.justgothere = False
                currgc = self.parent.gridcoords
                nextgc = p.path[0].gridcoords  # check if it should should be 0 or 1
                del p.path[0]
                ad = MindController.directiontotake(currgc, nextgc)  # check function name

                relad1 = self.crossing1.getrelad(self)  # check declaration
                relad2 = self.crossng2.getrelas(self)

                if ad == relad1:
                	p.currtarzc = self.crossing1
                elif ad == relad2:
                	p.crrtarzc = self.crossing2
                else:  # taking a road next
                	p.currtarzc = self.parent.roads[ad]  # TODO: change currtarzc to more genera

                # push the button!
                if type(p.currtarzc) is ZebraCrossing:
                	p.currtarzc.buttonpushed = True
                    p.currtarsw = p.currtarzc.getoppositesw(self)
                	if p.currtarzc.pedlight.state == 0:  # green
                        p.walkingtimeleft = Pedestrian.timeleft(ZebraCrossing.length)
                    	p.parent = p.currtarzc
                        p.currtarzc = None
                else:  # give to road
                	p.currtarzc.offerroad(p)


# I just realized how bad some editors can be - March 2 2018
class Portal:  # called Portal because cars/pedestrians start and end here (there are multiple portals)
    # attaches to road of intersection
    # cars coming from the intersection go directly from Middle to Portal

    def __init__(self, road, pos, p):
        self.cars = []
        self.peds = []
        self.adjroad = road  # the road it feeds into'
        self.finished = []  # cars and peds who are done
        self.position = pos  # 0, 1, 2, 3 -> up, right, down, left, see MindController.decidedest()
        self.parent = p


    # TODO: should we merge cars and peds into one list (as well as the functions)?
    def createcar(self):
        newcar = Car(self)

        self.cars.append(newcar)
        return newcar  # gives car to MindController, the one that calls the function and decides the car's destination

    def createped(self):  # basically same as createcar()
        newped = Pedestrian(self)
        self.peds.append(newped)
        return newped

    def deleteobj(self, c):  # removes car forever
        # TODO: make it increase the counter for how many cars/peds got through out of all time
        del self.finished[self.finished.index(c)]  # get index of c in cars, then delete that element

    def releasesome(self):
        # takes at most 1 car and all pedestrians and pushes them into the adjacent road
        c = self.cars.pop(0)
        success = self.adjroad.offerroad(c)  # if False the Lane must be full
        if not success:
            self.cars.append(c)

        # now the pedestrians
        succeeded = []  # list of stuff to remove after the next for loop
        for i in range(len(self.peds)):
            success = self.adjroad.offerroad(self.peds[i])
            if success:
                succeeded.append(self.peds[i])
        self.peds = list(succeeded)  # FIXME this area might break because of pointers
        del succeeded

    def deletefinished(self):
        self.parent.numgottenthrough += len(self.finished)
        for c in self.finished:
            self.deleteobj(c)

    def onetick(self):
        if random.random() < Portal.carprob:
            self.createcar()

        if random.random() < Portal.pedprob:
            self.createped()

        self.deletefinished()  # get rid of cars and peds who
        self.releasesome()

    carprob = None  # (FON) probability that a car will spawn in a given tick, similar below
    pedprob = None  # (FON)


class MindController:
    # this controls all the interactions of the simulation, aside from the traffic lights
    # does things like make cars move, spawn, etc.

    def __init__(self, s):
        self.sidelength = s  # not including Portals
        self.intersections = [[None] * s for _ in range(s)]
        self.initinter(s)
        self.portals = []  # for easy access
        self.ticks = 0  # time for the simulation; 1 tick is 1/10 a "second"

    def decidecolor(self, light):
        pass

    def decidedest(self, p):
        # takes portal and returns a portal which isn't on the same side
        ppos = p.position  # for convenience

        # aside from U-turns, cars never go back the same direction
        # and accuracy regarding destination choice shouldn't matter too much
        diffpos = lambda x: x.position != ppos
        allonothersides = list(filter(diffpos, self.portals))  # filter out portals on the same side as p
        dest = random.choice(allonothersides)

        return dest

    def pathfind(self, origin, dest):
        # we use the A* algorithm to simulate human pathfinding (with a map)
        # returns array of intersections to follow, and the portal (for conevnience and corner cases)
        closedset = []  # already evaluated intersections
        openset = [origin.adjroad.parent]  # currently discovered but not evaluated

    def initinter(self, s):
        for y in range(s):  # y goes top to bottom
            for x in range(s):  # x goes left to right
                self.intersections[y][x] = Intersection([x,y], self)

        # need to do this twice (^) to set the adjacent property
        for y in range(s):
            for x in range(s):
                inter = self.intersections[y][x]
                coords = [[x, y-1], [x+1, y], [x, y+1], [x-1, y]]

                for adjcoord in coords:
                    a = adjcoord[0]  # abbreviation
                    b = adjcoord[1]

                    if (not a in range(s)) or (not b in range(s)):  # then we create a portal
                        road = inter.roads[0] if a < y else inter.roads[1] if x < b else inter.roads[2] if y < a else inter.roads[3]

                        portalpos = coords.index([a, b])
                        portal = Portal(road, portalpos, self)
                        inter.adjacents[portalpos] = portal
                        self.portals.append(portal)
                    else:
                        inter.adjacents[coords.index([a, b])] = self.intersections[b][a]

    @staticmethod
    def directiontotake(currgc, nextgc):
        x1, x2, y1, y2 = currgc[0], currgc[1], nextgc[0], nextgc[1]
        if x1 < x2:
            return 2
        if x1 > x2:
            return 4
        if y1 < y2:
            return 3
        if y1 > y2:
            return 1

    def onetick(self):  # does everything that happens in a single tick
        # (almost?) every object has has a similar function which is called by this one
        # spawn and release cars, make everything move forwards, increments waiting counters, etc.
        for p in self.portals:
            p.onetick()

        # for
