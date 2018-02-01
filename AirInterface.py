import PropagationModel
from Location import Location
from Gateway import Gateway
from LoRaPacket import LoRaPacket
import matplotlib.pyplot as plt
import random

from SNRModel import SNRModel


class AirInterface:

    def __init__(self, gateway: Gateway, prop_model: PropagationModel, snr_model: SNRModel, env):
        self.prop_measurements = {}
        self.num_of_packets_send = 0
        self.gateway = gateway
        self.packages_in_air = list()
        self.color_per_node = dict()
        self.prop_model = prop_model
        self.snr_model = snr_model
        self.env = env

    @staticmethod
    def frequency_collision(p1: LoRaPacket, p2: LoRaPacket):
        """frequencyCollision, conditions
                |f1-f2| <= 120 kHz if f1 or f2 has bw 500
                |f1-f2| <= 60 kHz if f1 or f2 has bw 250
                |f1-f2| <= 30 kHz if f1 or f2 has bw 125
        """

        p1_freq = p1.lora_param.freq
        p2_freq = p2.lora_param.freq

        p1_bw = p1.lora_param.bw
        p2_bw = p2.lora_param.bw

        if abs(p1_freq - p2_freq) <= 120 and (p1_bw == 500 or p2_bw == 500):
            print("frequency coll 500")
            return True
        elif abs(p1_freq - p2_freq) <= 60 and (p1_bw == 250 or p2_bw == 250):
            print("frequency coll 250")
            return True
        elif abs(p1_freq - p2_freq) <= 30 and (p1_bw == 125 or p2_bw == 125):
            print("frequency coll 125")
            return True

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
            print("collision sf node {} and node {}".format(p1.node.id, p2.node.id))
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
                                                                                                                     p1.rss - p2.rss,
                                                                                                                     2)))
        if abs(p1.rss - p2.rss) < power_threshold:
            print("collision pwr both node {} and node {}".format(p1.node.id, p2.node.id))
            # packets are too close to each other, both collide
            # return both packets as casualties
            p1.collided = True
            p2.collided = True
        elif p1.rss - p2.rss < power_threshold:
            # p2 overpowered p1, return p1 as casualty
            print("collision pwr node {} overpowered node {}".format(p2.node.id, p1.node.id))
            p1.collided = True
        print("p1 wins, p2 lost")
        # p2 was the weaker packet, return it as a casualty
        p2.collided = True

    @staticmethod
    def timing_collision(p1: LoRaPacket, p2: LoRaPacket):
        # Check if the interferer starts after the critical section of the interfered packet

        # assuming 8 preamble symbols
        # critical section is after 2 - 8 preamble symbols
        Tsym = 2 ** p1.lora_param.sf / (1.0 * p1.lora_param.bw)
        p1_critical_section = [p1.start_on_air + Tsym * 2, p1.start_on_air + Tsym * 8]
        Tsym = 2 ** p2.lora_param.sf / (1.0 * p2.lora_param.bw)
        p2_critical_section = [p2.start_on_air + Tsym * 2, p2.start_on_air + Tsym * 8]

        # if one packet starts or end in the others critical section = collided
        if p2.start_on_air < p1_critical_section[1] or p2.start_on_air + p2.time_on_air > p1_critical_section[0]:
            p1.collided = True
        if p1.start_on_air < p2_critical_section[1] or p1.start_on_air + p1.time_on_air > p2_critical_section[0]:
            p1.collided = True

        # if p1 has not yet collided but they time overlap
        if not p1.collided:


    def collision(self, packet) -> bool:
        print("CHECK node {} (sf:{} bw:{} freq:{:.6e}) others: {}".format(
            packet.node.id, packet.lora_param.sf, packet.lora_param.bw, packet.lora_param.freq,
            len(self.packages_in_air)))
        for other in self.packages_in_air:
            if other.node.id != packet.node.id:
                print(">> node {} (sf:{} bw:{} freq:{:.6e})".format(
                    other.node.id, other.packet.lora_param.sf, other.packet.lora_param.bw,
                    other.packet.lora_param.freq))
                if AirInterface.frequency_collision(packet, other.packet) and AirInterface.sf_collision(packet,
                                                                                                        other.packet):
                    if AirInterface.timing_collision(packet, other.packet):
                        # check who collides in the power domain
                        AirInterface.power_collision(packet, other.packet)
        return packet.collided

    # color_values = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']

    def packet_in_air(self, packet: LoRaPacket):
        self.num_of_packets_send += 1
        # id = packet.node.id
        # if id not in self.color_per_node:
        #     self.color_per_node[id] = '#' + random.choice(AirInterface.color_values) + random.choice(
        #         AirInterface.color_values) + random.choice(AirInterface.color_values) + random.choice(
        #         AirInterface.color_values) + random.choice(AirInterface.color_values) + random.choice(
        #         AirInterface.color_values)

        self.packages_in_air.append(packet)

    def packet_received(self, packet: LoRaPacket) -> bool:
        """Packet has fully received by the gateway
            This method checks if this packet has collided
            :return bool (True collided or False not collided)"""
        from_node = packet.node
        node_id = from_node.node_id
        rss = self.prop_model.tp_to_rss(from_node.location.indoor, packet.lora_param.tp,
                                        Location.distance(self.gateway.location, packet.node.location))
        if node_id not in self.prop_measurements:
            self.prop_measurements[node_id] = {'rss': [], 'snr': [], 'time': []}
        packet.rss = rss
        snr = self.snr_model.rss_to_snr(rss)
        packet.snr = snr

        self.prop_measurements[node_id]['time'].append(self.env.now)
        self.prop_measurements[node_id]['rss'].append(rss)
        self.prop_measurements[node_id]['snr'].append(snr)

        collided = self.collision(packet)
        self.packages_in_air.remove(packet)
        return collided

    def plot_packets_in_air(self):
        plt.figure()
        ax = plt.gca()
        plt.axis('off')
        ax.grid(False)
        for package in self.packages_in_air:
            node_id = package['id']
            plt.hlines(package['ch'], package['start'], package['stop'], color=self.color_per_node[node_id],
                       linewidth=2.0)
        plt.show()

    def log(self):
        print('Total number of packets in the air {}'.format(self.num_of_packets_send))
