import numpy as np

class LogShadow:

    # http://ieeexplore.ieee.org.kuleuven.ezproxy.kuleuven.be/stamp/stamp.jsp?tp=&arnumber=7377400
    def __init__(self, gamma=2.32, d0=1000.0, std=7.8, Lpld0=128.95, GL=0):
        self.gamma = gamma
        self.d0 = d0
        self.std = std
        if self.std<0:
            self.std = 0
        self.Lpld0 = Lpld0
        self.GL = GL

    def tp_to_rss(self, indoor: bool, tp_dBm: int, d: float):
        bpl = 0  # building path loss
        if indoor:
            bpl = np.random.choice([17, 27, 21, 30])  # according Rep. ITU-R P.2346-0
        Lpl = 10 * self.gamma * np.log10(d / self.d0) + np.random.normal(self.Lpld0, self.std) + bpl
        if Lpl <0:
            Lpl = 0
        return tp_dBm - self.GL - Lpl


class COST231:

    def __init__(self, fc, W=None, b=None, hr=None, hm=2, phi=None, hb=15, metropolitan_center=True):

        # default desribed in Understanding UMTS Radio Network Modelling, Planning and Automated Optimisation: Theory
        #  and Practice no data about propagation path on page 87
        roof_height = round(np.random.uniform(0, 1)) * 3
        num_of_floors = round(2 + round(np.random.uniform(0, 1)) * (5 - 2))
        if hr is None:
            hr = 3 * num_of_floors + roof_height
        if phi is None:
            phi = 90
        if b is None:
            b = np.random.uniform(20, 50)
        if W is None:
            W = b / 2

        #   fc  Carrier Frequency(800-2000MHz)
        #   W   Street Width(m)
        #   b   distance b/w building(m)
        #   hr  height of roof
        #   hm  mobile antenna ht(1-3m)
        #   phi incident angle related to street(0-90degree)
        #   hb  base station ant. ht(4-50m)
        #   d   Link distance

        # Formulas based on "Understanding UMTS Radio Network Modelling, Planning and Automated Optimisation: Theory
        # and Practice" and https://www.itu.int/dms_pubrec/itu-r/rec/p/R-REC-P.1411-6-201202-S!!PDF-E.pdf

        # The basic propagation loss, Lb, is calculated as the sum of three components:
        #   1. the free-space loss, L0,
        #   2. the roof-to-street loss, Lrts, produced in the street where the receiver is located,
        #      as result of the diffraction on the next rooftop;
        #   3. and the multiscreen diffraction loss, Lmsd, produced by multiple diffractions on the building rooftops
        #      along the direct propagation path. The model also distinguishes LOS and NLOS situations.

        # self.fc = fc
        # self.W = W
        # self.b = b
        # self.hr = hr
        # self.hm = hm
        # self.phi = phi
        # self.hb = hb
        # self.metropoliton_center = metropolitan_center

        self.hb = None
        global Lori
        if fc < 800 or fc > 2000:
            ValueError('Carrier Frequency (in MHz) needs to be between 800 and 2000')

        if hm < 1 or hm > 3:
            ValueError('Mobile antenna height needs to be between 1 and 3m')

        if phi < 0 or phi > 90:
            ValueError('incident angle related to street(0-90degree)')

        if hb < 4 or hb > 50:
            ValueError('incident angle related to street(0-90degree)')

        dhb = hb - hr
        if dhb < 0:
            ValueError('Base station must be higher than the roof-top level.')

        # NLOS scenario
        dhm = hr - hm

        # The term Lori is a correction factor that accounts for the loss due to the orientation of the street.
        if (phi >= 0) and (phi < 35):
            Lori = -10 + 0.354 * phi
        elif (phi >= 35) and (phi < 55):
            Lori = 32.5 + 0.075 * (phi - 35)
        elif (phi >= 55) and (phi <= 90):
            Lori = 4 - 0.114 * (phi - 55)

        if Lori < 0:
            Lori = 0

        # The term Lrts takes into account the street width and its orientation
        # with respect to the propagation direction of the main beam.
        Lrts = -8.2 - 10 * np.log10(W) + 10 * np.log10(fc) + 20 * np.log10(dhm) + Lori

        if Lrts < 0:
            Lrts = 0

        # Lbsh depends on the base station height
        if hb > hr:
            Lbsh = -18 * np.log10(1 + dhb)
        elif hb >= hr:
            Lbsh = 0
        # The terms kd and kf control the dependence of Lmsd on distance and frequency, respectively.
        if (hb > hr):
            kd = 18
        else:
            kd = 18 - 15 * dhb / hr
        if metropolitan_center:
            kf = 4 + 1.5 * ((fc / 925) - 1)
        else:
            kf = 4 + 0.7 * ((fc / 925) - 1)
        if hb > hr:
            Lbsh = -18 * np.log10(1 + dhb)
            kd = 18 - 15 * dhb / dhm
        else:
            Lbsh = 0
            kd = 18

        self.fc = fc
        self.hr = hr
        self.dhb = dhb
        self.Lbsh = Lbsh
        self.kd = kd
        self.Lrts = Lrts
        self.kf = kf
        self.b = b

    def tp_to_rss(self, indoor: bool, tp_dBm: int, d: float):
        bpl = 0  # building path loss
        if indoor:
            bpl = np.random.choice([17, 27, 21, 30])  # according Rep. ITU-R P.2346-0
        # The propagation loss in free space conditions, L0, is obtained according to the expression:
        L0 = 32.4 + 20 * np.log10(d) + 20 * np.log10(self.fc)
        # NLOS - The term ka represents the increase of path loss for base station antennas below the average height
        # of the buildings.
        if self.hb > self.hr:
            ka = 54
        elif self.hb <= self.hr and d >= 0.5:
            ka = 54 - 8 * self.dhb
        elif self.hb <= self.hr and d > 0.5:
            ka = 54 - 0.8 * self.dhb / 0.5
        else:
            ValueError('ka referenced before assignment')

        # The multiscreen diffraction loss, Lmsd, is a function of frequency,
        # distance between the mobile station and the base station,
        # as well as base station height and building heights.
        Lmsd = self.Lbsh + ka + self.kd * np.log10(d) + self.kf * np.log10(self.fc) - 9 * np.log10(self.b)
        if Lmsd < 0:
            Lmsd = 0
        if (self.Lrts + Lmsd) > 0:
            L50 = L0 + self.Lrts + Lmsd
        else:
            L50 = L0
        return tp_dBm - L50 - bpl
