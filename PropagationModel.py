import numpy as np


class LogShadow:
    def __init__(self, gamma=2.08, d0=40.0, var=0, Lpld0=127.41, GL=0):
        self.gamma = gamma
        self.d0 = d0
        self.var = var
        self.Lpld0 = Lpld0
        self.GL = GL

    def tp_to_rss(self, tp: int, d: float):
        Lpl = self.Lpld0 + 10 * self.gamma * np.log10(d / self.d0) - np.random.normal(0, self.var)
        return tp - self.GL - Lpl
