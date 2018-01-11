import random


class Location:
    def __init__(self, min, max, indoor=False):
        self.x = random.randint(min, max)
        self.y = random.randint(min, max)
        self.indoor = indoor


