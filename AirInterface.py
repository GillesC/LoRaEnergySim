from LoRaPacket import LoRaPacket


class AirInterface:
    def __init__(self, base_station):
        self.base_Station = base_station
        self.packages_in_air = list()

    @staticmethod
    def frequency_collision(p1: LoRaPacket, p2: LoRaPacket):
        """frequencyCollision, conditions
                |f1-f2| <= 120 kHz if f1 or f2 has bw 500
                |f1-f2| <= 60 kHz if f1 or f2 has bw 250
                |f1-f2| <= 30 kHz if f1 or f2 has bw 125
        """
        if abs(p1.lora_param.freq - p2.lora_param.freq) <= 120 and (p1.lora_param.bw == 500 or p2.lora_param.freq == 500):
            print("frequency coll 500")
            return True
        elif abs(p1.lora_param.freq - p2.lora_param.freq) <= 60 and (p1.lora_param.bw == 250 or p2.lora_param.freq == 250):
            print("frequency coll 250")
            return True
        else:
            if abs(p1.lora_param.freq - p2.lora_param.freq) <= 30:
                print("frequency coll 125")
                return True
                # else:
        print("no frequency coll")
        return False

    @staticmethod
    def sf_collision(p1: LoRaPacket, p2: LoRaPacket):
        #
        # sfCollision, conditions
        #
        #       sf1 == sf2
        #
        if p1.lora_param.sf == p2.lora_param.sf:
            print("collision sf node {} and node {}".format(p1.nodeid, p2.nodeid))
            # p2 may have been lost too, will be marked by other checks
            return True
        print("no sf collision")
        return False

    @staticmethod
    def power_collision(p1: LoRaPacket, p2: LoRaPacket):
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

    @staticmethod
    def timing_collision(p1: LoRaPacket, p2: LoRaPacket):
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

    def collision(self, packet):
        print("CHECK node {} (sf:{} bw:{} freq:{:.6e}) others: {}".format(
            packet.node.id, packet.sf, packet.bw, packet.freq,
            len(self.packages_in_air)))
        for other in self.packages_in_air:
            if other.nodeid != packet.nodeid:
                print(">> node {} (sf:{} bw:{} freq:{:.6e})".format(
                    other.nodeid, other.packet.sf, other.packet.bw, other.packet.freq))
                # simple collision
                if AirInterface.frequency_collision(packet, other.packet) \
                        and AirInterface.sf_collision(packet, other.packet):
                        if AirInterface.timing_collision(packet, other.packet):
                            # check who collides in the power domain
                            c = AirInterface.power_collision(packet, other.packet)
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

    def packet_in_air(self, package):
        self.packages_in_air.insert(package)

    def packet_received(self, package):
        self.packages_in_air.remove(package)
