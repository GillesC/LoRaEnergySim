import numpy as np
from LoRaPacket import LoRaPacket
from LoRaParameters import LoRaParameters
from GlobalConfig import GlobalConfig
from enum import Enum, auto
from AirInterface import AirInterface
from EnergyProfile import EnergyProfile

class NodeState(Enum):
    OFFLINE = auto()
    JOIN_TX = auto()
    JOIN_RX = auto()
    SLEEP = auto()
    TX = auto()
    RX = auto()
    PROCESS = auto()


class Node:
    def __init__(self, node_id, energy_profile, lora_parameters, duty_cycle, process_time, adr, location,
                 base_station, env):
        self.node_id = node_id
        self.energy_profile = energy_profile
        self.base_station = base_station
        self.process_time = process_time
        self.air_interface = AirInterface(base_station)
        self.env = env
        self.stop_state_time = self.env.now()
        self.start_state_time = self.env.now()
        self.current_state = NodeState.OFFLINE

    def run(self):
        self.join()
        while True:
            self.change_state(NodeState.SLEEP)
            yield self.env.timeout(self.sleep_time)
            self.change_state(NodeState.PROCESS)
            yield self.env.timeout(self.process_time)

            lora_param = LoRaParameters(freq, sf, bw, cr, crc_enabled, de_enabled, header_implicit_mode)
            packet = LoRaPacket(self, env.now(), lora_param, payload_size)
            success = self.send(env, packet)

    def change_state(self, to, packet=None):
        """
        :param to: new NodeState
        :param packet: optional LoRaPacket which was sent
        :return: consumed energy when in the current state
        """
        # and start tracking for next state
        # return power consumed by node in the current state
        if GlobalConfig.track_changes:
            self.stop_state_time = self.env.now()
            time_spent_in_current_state = self.stop_state_time - self.start_state_time
            consumed_energy = 0
            if self.current_state == NodeState.SLEEP:
                consumed_energy = time_spent_in_current_state*self.energy_profile.sleep_power
            elif self.current_state == NodeState.JOIN_TX:
                consumed_energy = EnergyProfile.energy_consumption(NodeState.JOIN_TX)
            elif self.current_state == NodeState.JOIN_RX:
                consumed_energy = EnergyProfile.energy_consumption(NodeState.JOIN_RX) #TODO check RX1 or RX2
            elif self.current_state == NodeState.PROCESS:
                consumed_energy = time_spent_in_current_state*self.energy_profile.proc_power
            elif self.current_state == NodeState.TX:
                consumed_energy = EnergyProfile.energy_consumption(NodeState.TX, packet)
            elif self.current_state == NodeState.RX:
                consumed_energy = EnergyProfile.energy_consumption(NodeState.RX, packet) #TODO check RX1 or RX2
            self.current_state = to
            self.start_state_time = self.env.now()
            return consumed_energy
        return None

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
        self.base_station.packet_in_air(packet)
        airtime = packet.time_on_air()
        yield env.timeout(airtime)
        self.base_station.packet_received(packet)
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
                self.rx_energy += rx2_window_open * self.energy_profile.rx_power
            else:
                # the node just checks every rx window for incoming messages
                # there will not be any incoming messages because the uplink was never received
                rx1_window_open = packet.rx1_window_open()
                yield env.timeout(rx1_window_open)
                self.rx_energy += rx1_window_open * self.energy_profile.rx_power
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
