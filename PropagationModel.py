import numpy as np


class LogShadow:

    # http://ieeexplore.ieee.org.kuleuven.ezproxy.kuleuven.be/stamp/stamp.jsp?tp=&arnumber=7377400
    def __init__(self, gamma=2.32, d0=1000.0, std=7.8, Lpld0=128.95, GL=0):
        self.gamma = gamma
        self.d0 = d0
        self.std = std
        self.Lpld0 = Lpld0
        self.GL = GL

    def tp_to_rss(self, indoor: bool, tp_dBm: int, d: float):
        bpl = 0  # building path loss
        if indoor:
            bpl = np.random.choice([17, 27, 21, 30])  # according Rep. ITU-R P.2346-0
        Lpl = 10 * self.gamma * np.log10(d / self.d0) + np.random.normal(self.Lpld0, self.std) + bpl
        return tp_dBm - self.GL - Lpl
