class AirInterface:
    def __init__(self, base_station):
        self.base_Station = base_station

    # frequencyCollision, conditions
    #
    #        |f1-f2| <= 120 kHz if f1 or f2 has bw 500
    #        |f1-f2| <= 60 kHz if f1 or f2 has bw 250
    #        |f1-f2| <= 30 kHz if f1 or f2 has bw 125
    def frequency(p1, p2):
        if abs(p1.freq - p2.freq) <= 120 and (p1.bw == 500 or p2.freq == 500):
            print("frequency coll 500")
            return True
        elif abs(p1.freq - p2.freq) <= 60 and (p1.bw == 250 or p2.freq == 250):
            print("frequency coll 250")
            return True
        else:
            if abs(p1.freq - p2.freq) <= 30:
                print("frequency coll 125")
                return True
            # else:
        print("no frequency coll")
        return False

    #
    # sfCollision, conditions
    #
    #       sf1 == sf2
    #
    def sf(p1, p2):
        if p1.sf == p2.sf:
            print("collision sf node {} and node {}".format(p1.nodeid, p2.nodeid))
            # p2 may have been lost too, will be marked by other checks
            return True
        print("no sf collision")
        return False

    def power(p1, p2):
        power_threshold = 6  # dB
        print(
            "pwr: node {0.nodeid} {0.rssi:3.2f} dBm node {1.nodeid} {1.rssi:3.2f} dBm; diff {2:3.2f} dBm".format(p1, p2,
                                                                                                                 round(
                                                                                                                     p1.rssi - p2.rssi,
                                                                                                                     2)))
        if abs(p1.rssi - p2.rssi) < power_threshold:
            print("collision pwr both node {} and node {}".format(p1.nodeid, p2.nodeid))
            # packets are too close to each other, both collide
            # return both packets as casualties
            return (p1, p2)
        elif p1.rssi - p2.rssi < power_threshold:
            # p2 overpowered p1, return p1 as casualty
            print("collision pwr node {} overpowered node {}".format(p2.nodeid, p1.nodeid))
            return (p1,)
        print("p1 wins, p2 lost")
        # p2 was the weaker packet, return it as a casualty
        return (p2,)

    def timing(p1, p2):
        # assuming p1 is the freshly arrived packet and this is the last check
        # we've already determined that p1 is a weak packet, so the only
        # way we can win is by being late enough (only the first n - 5 preamble symbols overlap)

        # assuming 8 preamble symbols
        Npream = 8

        # we can lose at most (Npream - 5) * Tsym of our preamble
        Tpreamb = 2 ** p1.sf / (1.0 * p1.bw) * (Npream - 5)

        # check whether p2 ends in p1's critical section
        p2_end = p2.addTime + p2.rectime
        p1_cs = env.now + Tpreamb
        print("collision timing node {} ({},{},{}) node {} ({},{})".format(
            p1.nodeid, env.now - env.now, p1_cs - env.now, p1.rectime,
            p2.nodeid, p2.addTime - env.now, p2_end - env.now
        ))
        if p1_cs < p2_end:
            # p1 collided with p2 and lost
            print("not late enough")
            return True
        print("saved by the preamble")
        return False

    def collided(self, packet):
        spackages_on_air = self.base_Station.packagesInAir
        print("CHECK node {} (sf:{} bw:{} freq:{:.6e}) others: {}".format(
            packet.node.id, packet.sf, packet.bw, packet.freq,
            len(spackages_on_air)))
        for other in spackages_on_air:
            if other.nodeid != packet.nodeid:
                print
                ">> node {} (sf:{} bw:{} freq:{:.6e})".format(
                    other.nodeid, other.packet.sf, other.packet.bw, other.packet.freq)
                # simple collision
                if frequencyCollision(packet, other.packet) \
                        and sfCollision(packet, other.packet):
                    if full_collision:
                        if timingCollision(packet, other.packet):
                            # check who collides in the power domain
                            c = powerCollision(packet, other.packet)
                            # mark all the collided packets
                            # either this one, the other one, or both
                            for p in c:
                                p.collided = 1
                        else:
                            # no timing collision, all fine
                            pass
                    else:
                        packet.collided = 1
                        other.packet.collided = 1  # other also got lost, if it wasn't lost already
                        col = 1
