from Location import Location
import math


class RectangularArea:

    def __init__(self, origin_point: Location = None, len_x=None, len_y=None, opposite_point: Location = None):
        self.origin = origin_point
        self.side_x = len_x
        self.side_y = len_y
        if len_x is None and len_y is None:
            if opposite_point is not None:
                self.side_x = math.abs(opposite_point.x - origin_point.x)
                self.side_y = math.abs(opposite_point.y - origin_point.y)
            else:
                raise ValueError('Define an end point or give len_x and len_y values')

    # check if loc is inside this rectangular area
    def is_inside(self, loc: Location) -> bool:
        inside = False
        if self.origin.x < loc.x < self.origin.x + self.side_x:
            if self.origin.y < loc.y < self.origin.y + self.side_y:
                inside = True

        return inside

