import AirInterface
import numpy as np
from LoRaPacket import LoRaPacket
from LoRaParameters import LoRaParameters
from GlobalConfig import GlobalConfig

class Node:

    def __init__(self, node_id, energy_profile, lora_parameters, duty_cycle, adr, location,
                 base_station):
        self.node_id = node_id
        self.energy_profile = energy_profile
        self.base_station = base_station
        self.tx_energy = 0
        self.rx_energy = 0
        self.sense_energy = 0
        self.sleep_energy = 0
        self.air_interface = AirInterface(base_station)

    def run(self, env):
        self.join()
        while True:
            sleep()
            yield env.timeout(sleep_time)
            self.sleep_time = self.sleep_time + sleep_time
            sense()
            yield env.timeout(sense_time)
            self.sense_time = self.sense_time + sense_time
            lora_param = LoRaParameters(freq, sf, bw, cr, crc_enabled, de_enabled, header_implicit_mode)
            packet = LoRaPacket(self, env.now(), lora_param, payload_size)
            success = self.send(env, packet)

    # [----JOIN----]        [rx1]
    # computes time spent in different states during join procedure
    # TODO also allow join reqs to be collided
    def join(self, env):
        yield env.timeout(LoRaParameters.JOIN_TX_TIME_MS)
        self.tx_energy = LoRaParameters.JOIN_TX_ENERGY_MJ
        yield env.timeout(LoRaParameters.JOIN_ACCEPT_DELAY1)
        self.sleep_energy = LoRaParameters.JOIN_ACCEPT_DELAY1 * self.energy_profile.proc_power
        yield env.timeout(LoRaParameters.JOIN_RX_TIME_MS)
        self.rx_energy = LoRaParameters.JOIN_RX_ENERGY_MJ
        return True

    # [----transmit----]        [rx1]      [--rx2--]
    # computes time spent in different states during tx and rx one package
    def send(self, env, packet):
        self.base_station.addPackage(packet)
        airtime = packet.time_on_air()
        yield env.timeout(airtime)
        self.base_station.removePackage(packet)
        self.tx_energy += airtime * self.energy_profile.tx_power
        packet.strength = self.base_station.packetStrongEnough(packet)
        packet.collided = self.air_interface.collided(packet)
        packet.received = not packet.collided and packet.strength
        yield env.timeout(LoRaParameters.RX_WINDOW_1_DELAY)
        self.sleep_energy += LoRaParameters.RX_WINDOW_1_DELAY * self.energy_profile.sleep_power
        if packet.received:
            # packet is received by the gateway
            # the gateway then decides which rx slot to use
            rx_1_received = np.random.choice([True, False], p=[GlobalConfig.PROB_RX1, GlobalConfig.PROB_RX2])
            if rx_1_received:
                rx1_time = packet.time_on_air()
                yield env.timeout(rx1_time)
                self.rx_energy += rx1_time * self.energy_profile.rx_power
                sleep_between_rx1_rx2_window = LoRaParameters.RX_WINDOW_2_DELAY - LoRaParameters.RX_WINDOW_1_DELAY - rx1_time
                if sleep_between_rx1_rx2_window < 0:
                    sleep_between_rx1_rx2_window = 0
                yield env.timeout(sleep_between_rx1_rx2_window)
                self.sleep_energy += sleep_between_rx1_rx2_window * self.energy_profile.sleep_power
                rx2_window_open = packet.rx2_window_open()
                yield env.timeout(rx2_window_open)
                self.rx_energy += rx2_window_open* self.energy_profile.rx_power
            else:
                # the node just checks every rx window for incoming messages
                # there will not be any incoming messages because the uplink was never received
                rx1_window_open = packet.rx1_window_open()
                yield env.timeout(rx1_window_open)
                self.rx_energy += rx1_window_open*self.energy_profile.rx_power
                sleep_between_rx1_rx2_window = LoRaParameters.RX_WINDOW_2_DELAY - LoRaParameters.RX_WINDOW_1_DELAY - rx1_window_open
                yield env.timeout(sleep_between_rx1_rx2_window)
                self.sleep_energy += sleep_between_rx1_rx2_window * self.energy_profile.sleep_power
                rx2_time = packet.rx2_time_on_air()
                yield env.timeout(rx2_time)
                self.rx_time += rx2_time * self.energy_profile.rx_power
        else:
            # the node just checks every rx window for incoming messages
            # there will not be any incoming messages because the uplink was never received
            rx1_window_open = packet.rx1_window_open()
            yield env.timeout(rx1_window_open)
            self.rx_time = self.rx_time + rx1_window_open
            sleep_between_rx1_rx2_window = LoRaParameters.RX_WINDOW_2_DELAY - LoRaParameters.RX_WINDOW_1_DELAY - rx1_window_open
            yield env.timeout(sleep_between_rx1_rx2_window)
            self.sleep_time = self.sleep_time + sleep_between_rx1_rx2_window
            rx2_window_open = packet.rx2_window_open()
            yield env.timeout(rx2_window_open)
            self.rx_time = self.rx_time + rx2_window_open
        return packet.received