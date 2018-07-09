import random
import numpy as np


class Location:

    def __init__(self, x=None, y=None, min=None, max=None, indoor=False):
        self.x = x
        self.y = y

        if x is None or y is None:
            if min is not None and max is not None:
                self.x = random.randint(min, max)
                self.y = random.randint(min, max)
            else:
                raise ValueError('Define min and max or give x and y coordinates')
        self.indoor = indoor

    @staticmethod
    def distance(loc_1, loc_2):
        delta_x = loc_1.x - loc_2.x
        delta_y = loc_1.y - loc_2.y
        return np.sqrt(np.power(delta_x, 2) + np.power(delta_y, 2))
