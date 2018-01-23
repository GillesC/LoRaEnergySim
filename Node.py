from enum import Enum, auto

import matplotlib.pyplot as plt
import numpy as np

from Gateway import Gateway
from GlobalConfig import GlobalConfig
from LoRaPacket import LoRaPacket
from LoRaParameters import LoRaParameters


class NodeState(Enum):
    OFFLINE = auto()
    JOIN_TX = auto()
    JOIN_RX = auto()
    SLEEP = auto()
    TX = auto()
    RX = auto()
    PROCESS = auto()


class Node:
    def __init__(self, node_id, energy_profile, lora_parameters, sleep_time, process_time, adr, location,
                 base_station: Gateway, env, payload_size):
        self.node_id = node_id
        self.energy_profile = energy_profile
        self.base_station = base_station
        self.process_time = process_time
        # self.air_interface = AirInterface(base_station)
        self.env = env
        self.stop_state_time = self.env.now
        self.start_state_time = self.env.now
        self.current_state = NodeState.OFFLINE
        self.lora_param = lora_parameters
        self.payload_size = payload_size

        self.location = location

        self.tx_energy = 0
        self.sleep_energy = 0
        self.rx_energy = 0

        self.tx_energy_time = []
        self.tx_energy_value = []
        self.tx_prev_energy_value = 0

        self.rx_energy_time = []
        self.rx_energy_value = []
        self.rx_prev_energy_value = 0

        self.sleep_energy_time = []
        self.sleep_energy_value = []
        self.sleep_prev_energy_value = 0

        self.proc_energy_time = []
        self.proc_energy_value = []
        self.proc_prev_energy_value = 0

        self.power_tracking_time = []
        self.power_tracking_value = []

        self.sleep_time = sleep_time

    def plot_energy(self):
        plt.plot(self.sleep_energy_time, self.sleep_energy_value, label='Sleep Energy (mJ)')
        plt.plot(self.proc_energy_time, self.proc_energy_value, label='Processing Energy (mJ)')
        plt.plot(self.tx_energy_time, self.tx_energy_value, label='Tx Energy (mJ)')
        # plt.plot(self.power_tracking_time, self.power_tracking_value, label='Power Tracking (mW)')
        plt.legend()
        plt.show()

    def run(self, env):
        random_wait = np.random.randint(0, GlobalConfig.MAX_DELAY_START_PER_NODE_MS)
        env.timeout(random_wait)
        print('{} ms delayed prior to joining'.format(random_wait))
        print('{} joining the network'.format(self.node_id))
        env.run(env.process(self.join(env)))
        print('{}: joined the network'.format(self.node_id))
        while True:
            # ------------SLEEPING------------ #
            print('{}: START sleeping'.format(self.node_id))
            start = self.env.now
            self.power_tracking_time.append(start)
            self.power_tracking_value.append(self.energy_profile.sleep_power)
            yield self.env.timeout(self.sleep_time)
            now = self.env.now

            energy = (now - start) * self.energy_profile.sleep_power
            print('{}: Waking up [time: {}; energy: {}]'.format(self.node_id, env.now, energy))
            self.sleep_energy_time.append(now)
            self.sleep_energy_value.append(energy + self.sleep_prev_energy_value)
            self.sleep_prev_energy_value += energy

            self.power_tracking_time.append(now)
            self.power_tracking_value.append(self.energy_profile.sleep_power)

            # ------------PROCESSING------------ #
            print('{}: PROCESSING'.format(self.node_id))
            start = self.env.now
            self.power_tracking_time.append(start)
            self.power_tracking_value.append(self.energy_profile.proc_power)
            yield self.env.timeout(self.process_time)
            now = self.env.now
            energy = (now - start) * self.energy_profile.sleep_power
            self.proc_energy_time.append(now)
            self.proc_energy_value.append(energy + self.proc_prev_energy_value)
            self.proc_prev_energy_value += energy
            self.power_tracking_time.append(now)
            self.power_tracking_value.append(self.energy_profile.proc_power)
            print('{}: DONE PROCESSING [time: {}; energy: {}]'.format(self.node_id, env.now, energy))

            # ------------SENDING------------ #
            print('{}: SENDING packet'.format(self.node_id))
            packet = LoRaPacket(self, env.now, self.lora_param, self.payload_size)
            downlink_message = env.run(env.process(self.send(env, packet)))
            # self.process_downlink_message(downlink_message)
            print('{}: DONE sending'.format(self.node_id))

    # [----JOIN----]        [rx1]
    # computes time spent in different states during join procedure
    # TODO also allow join reqs to be collided
    def join(self, env):

        yield env.timeout(LoRaParameters.JOIN_TX_TIME_MS)
        print('{}: \t JOIN TX'.format(self.node_id))
        energy = LoRaParameters.JOIN_TX_ENERGY_MJ
        self.tx_energy_time.append(self.env.now)
        self.tx_prev_energy_value += energy
        self.tx_energy_value.append(self.tx_prev_energy_value)

        yield env.timeout(LoRaParameters.JOIN_ACCEPT_DELAY1)
        print('{}: \t JOIN WAIT'.format(self.node_id))
        self.sleep_energy = LoRaParameters.JOIN_ACCEPT_DELAY1 * self.energy_profile.sleep_power
        yield env.timeout(LoRaParameters.JOIN_RX_TIME_MS)
        print('{}: \t JOIN RX'.format(self.node_id))
        self.rx_energy = LoRaParameters.JOIN_RX_ENERGY_MJ
        return True

    # [----transmit----]        [rx1]      [--rx2--]
    # computes time spent in different states during tx and rx one package
    def send(self, env, packet):

        #            TX             #
        # fixed energy overhead
        print('{}: \t TX'.format(self.node_id))
        # self.base_station.packet_in_air(packet)
        airtime = packet.my_time_on_air()
        energy = airtime * self.energy_profile.tx_power[packet.lora_param.tp] + LoRaParameters.RADIO_PREP_ENERGY_MJ
        yield env.timeout(airtime + LoRaParameters.RADIO_PREP_TIME_MS)
        self.tx_energy_time.append(self.env.now)
        self.tx_prev_energy_value += energy
        self.tx_energy_value.append(self.tx_prev_energy_value)

        #      Received at BS      #
        print('{}: \t REC at BS'.format(self.node_id))
        downlink_message = self.base_station.packet_received(self, packet, env.now)
        # packet.strength = self.base_station.packetStrongEnough(packet)
        # packet.collided = self.air_interface.collided(packet)
        # packet.received = not packet.collided and packet.strength

        #            RX1 wait             #
        print('{}: \t WAIT'.format(self.node_id))
        yield env.timeout(LoRaParameters.RX_WINDOW_1_DELAY)
        # self.sleep_energy += LoRaParameters.RX_WINDOW_1_DELAY * self.energy_profile.sleep_power
        # if packet.received:
        #     # packet is received by the gateway
        #     # the gateway then decides which rx slot to use
        #     rx_1_received = np.random.choice([True, False], p=[GlobalConfig.PROB_RX1, GlobalConfig.PROB_RX2])
        #     if rx_1_received:
        #         rx1_time = packet.time_on_air()
        #         yield env.timeout(rx1_time)
        #         self.rx_energy += rx1_time * self.energy_profile.rx_power
        #         sleep_between_rx1_rx2_window = LoRaParameters.RX_WINDOW_2_DELAY - LoRaParameters.RX_WINDOW_1_DELAY - rx1_time
        #         if sleep_between_rx1_rx2_window < 0:
        #             sleep_between_rx1_rx2_window = 0
        #         yield env.timeout(sleep_between_rx1_rx2_window)
        #         self.sleep_energy += sleep_between_rx1_rx2_window * self.energy_profile.sleep_power
        #         rx2_window_open = packet.rx2_window_open()
        #         yield env.timeout(rx2_window_open)
        #         self.rx_energy += rx2_window_open * self.energy_profile.rx_power
        #     else:
        #         # the node just checks every rx window for incoming messages
        #         # there will not be any incoming messages because the uplink was never received
        #         rx1_window_open = packet.rx1_window_open()
        #         yield env.timeout(rx1_window_open)
        #         self.rx_energy += rx1_window_open * self.energy_profile.rx_power
        #         sleep_between_rx1_rx2_window = LoRaParameters.RX_WINDOW_2_DELAY - LoRaParameters.RX_WINDOW_1_DELAY - rx1_window_open
        #         yield env.timeout(sleep_between_rx1_rx2_window)
        #         self.sleep_energy += sleep_between_rx1_rx2_window * self.energy_profile.sleep_power
        #         rx2_time = packet.rx2_time_on_air()
        #         yield env.timeout(rx2_time)
        #         self.rx_time += rx2_time * self.energy_profile.rx_power
        # else:
        #     # the node just checks every rx window for incoming messages
        #     # there will not be any incoming messages because the uplink was never received
        #     rx1_window_open = packet.rx1_window_open()
        #     yield env.timeout(rx1_window_open)
        #     self.rx_time = self.rx_time + rx1_window_open
        #     sleep_between_rx1_rx2_window = LoRaParameters.RX_WINDOW_2_DELAY - LoRaParameters.RX_WINDOW_1_DELAY - rx1_window_open
        #     yield env.timeout(sleep_between_rx1_rx2_window)
        #     self.sleep_time = self.sleep_time + sleep_between_rx1_rx2_window
        #     rx2_window_open = packet.rx2_window_open()
        #     yield env.timeout(rx2_window_open)
        #     self.rx_time = self.rx_time + rx2_window_open
        # return packet.received

    def process_downlink_message(self, downlink_message):
        # change dr based on downlink_message['dr']
        print('Change DR ' + self.lora_param.dr + ' with ' + downlink_message['dr'])
        self.lora_param.change_dr(downlink_message['dr'])
        # change tp based on downlink_message['tp']
        print('Change TP ' + self.lora_param.tp + ' with ' + downlink_message['tp'])
        self.lora_param.change_tp(downlink_message['tp'])
