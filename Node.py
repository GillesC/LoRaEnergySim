from enum import Enum, auto

import matplotlib.pyplot as plt
import numpy as np

from Gateway import Gateway
from Global import Config
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
                 base_station: Gateway, env, payload_size, air_interface):
        self.adr = adr
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

        self.air_interface = air_interface

        self.location = location

        self.tx_energy = 0
        self.sleep_energy = 0
        self.rx_energy = 0

        self.tx_power_time_mW = []
        self.tx_power_value_mW = []
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

        self.change_lora_param = dict()

        self.tx_total_energy = 0
        self.rx_total_energy = 0
        self.sleep_total_energy = 0

    def plot_energy(self):
        plt.scatter(self.sleep_energy_time, self.sleep_energy_value, label='Sleep Power (mW)')
        plt.scatter(self.proc_energy_time, self.proc_energy_value, label='Processing Energy (mW)')
        plt.scatter(self.tx_power_time_mW, self.tx_power_value_mW, label='Tx Energy (mW)')

        for lora_param_setting in self.change_lora_param:
            plt.scatter(self.change_lora_param[lora_param_setting],
                        np.ones(len(self.change_lora_param[lora_param_setting])) * 140,
                        label=lora_param_setting)  # 140 default
            # value (top of figure)

        plt.title(self.node_id)
        ax = plt.gca()
        # Shrink current axis by 20%
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

        # Put a legend to the right of the current axis
        # ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.legend()
        # plt.plot(self.power_tracking_time, self.power_tracking_value, label='Power Tracking (mW)')
        plt.show()

    def run(self, env):
        random_wait = np.random.uniform(0, Config.MAX_DELAY_START_PER_NODE_MS)
        env.timeout(random_wait)
        if Config.PRINT_ENABLED:
            print('{} ms delayed prior to joining'.format(random_wait))
            print('{} joining the network'.format(self.node_id))
            self.join(env)
        if Config.PRINT_ENABLED:
            print('{}: joined the network'.format(self.node_id))
        while True:
            # added also a random wait to accommodate for any timing issues on the node itself
            random_wait = np.random.randint(0, Config.MAX_DELAY_BEFORE_SLEEP_MS)
            env.timeout(random_wait)
            # ------------SLEEPING------------ #
            if Config.PRINT_ENABLED:
                print('{}: START sleeping'.format(self.node_id))
            start = self.env.now

            self.power_tracking_time.append(start)
            self.power_tracking_value.append(self.energy_profile.sleep_power_mW)
            yield self.env.timeout(self.sleep_time)
            now = self.env.now

            time = (now - start)
            energy = (time * self.energy_profile.sleep_power_mW) / 1000
            if Config.PRINT_ENABLED:
                print('{}: Waking up [time: {}; energy: {}]'.format(self.node_id, env.now, energy))
            self.sleep_energy_time.append(now)
            self.sleep_energy_value.append(energy / time)
            self.sleep_prev_energy_value += energy
            self.sleep_total_energy += energy

            self.power_tracking_time.append(now-1) # -1 to not overlap in time with next state
            self.power_tracking_value.append(self.energy_profile.sleep_power_mW)

            # ------------PROCESSING------------ #
            if Config.PRINT_ENABLED:
                print('{}: PROCESSING'.format(self.node_id))
            start = self.env.now
            self.power_tracking_time.append(start)
            self.power_tracking_value.append(self.energy_profile.proc_power_mW)
            yield self.env.timeout(self.process_time)
            now = self.env.now
            time = (now - start)
            energy = time * self.energy_profile.sleep_power_mW
            self.proc_energy_time.append(now)
            self.proc_energy_value.append(energy / time)
            self.proc_prev_energy_value += energy
            self.power_tracking_time.append(now-1)
            self.power_tracking_value.append(self.energy_profile.proc_power_mW)
            if Config.PRINT_ENABLED:
                print('{}: DONE PROCESSING [time: {}; energy: {}]'.format(self.node_id, env.now, energy))

            # ------------SENDING------------ #
            if Config.PRINT_ENABLED:
                print('{}: SENDING packet'.format(self.node_id))
            packet = LoRaPacket(self, self.env.now, self.lora_param, self.payload_size)
            downlink_message = yield env.process(self.send(env, packet))
            self.process_downlink_message(downlink_message)
            if Config.PRINT_ENABLED:
                print('{}: DONE sending'.format(self.node_id))

    # [----JOIN----]        [rx1]
    # computes time spent in different states during join procedure
    # TODO also allow join reqs to be collided
    def join(self, env):
        yield env.timeout(LoRaParameters.JOIN_TX_TIME_MS)
        self.join_tx()
        yield env.timeout(LoRaParameters.JOIN_ACCEPT_DELAY1)
        self.join_wait()
        yield env.timeout(LoRaParameters.JOIN_RX_TIME_MS)
        self.join_rx()
        return True

    def join_tx(self):
        if Config.PRINT_ENABLED:
            print('{}: \t JOIN TX'.format(self.node_id))
        energy = LoRaParameters.JOIN_TX_ENERGY_MJ

        self.tx_prev_energy_value += energy
        # TODO check energy vs tx_prev_energy_value
        self.tx_power_time_mW.append(self.env.now)
        self.tx_power_value_mW.append((energy / LoRaParameters.JOIN_TX_TIME_MS) / 1000)  # for mW
        self.tx_total_energy += LoRaParameters.JOIN_TX_ENERGY_MJ

    def join_wait(self):
        if Config.PRINT_ENABLED:
            print('{}: \t JOIN WAIT'.format(self.node_id))
        energy = LoRaParameters.JOIN_ACCEPT_DELAY1 * self.energy_profile.sleep_power_mW
        self.sleep_energy_time.append(self.env.now)
        self.sleep_energy_value.append(self.energy_profile.sleep_power_mW)
        self.sleep_total_energy += energy

    def join_rx(self):
        if Config.PRINT_ENABLED:
            print('{}: \t JOIN RX'.format(self.node_id))
        self.rx_energy_time.append(self.env.now)
        self.rx_energy_value.append(
            (LoRaParameters.JOIN_RX_ENERGY_MJ / LoRaParameters.JOIN_RX_TIME_MS) / 1000)  # for mW

    # [----transmit----]        [rx1]      [--rx2--]
    # computes time spent in different states during tx and rx one package
    def send(self, env, packet):

        #            TX             #
        # fixed energy overhead
        if Config.PRINT_ENABLED:
            print('{}: \t TX'.format(self.node_id))
        # self.base_station.packet_in_air(packet)
        airtime_ms = packet.my_time_on_air()
        energy_mJ = (airtime_ms * self.energy_profile.tx_power_mW[
            packet.lora_param.tp]) / 1000 + LoRaParameters.RADIO_PREP_ENERGY_MJ
        self.air_interface.packet_in_air(packet, env.now, airtime_ms)

        self.power_tracking_time.append(env.now)
        self.power_tracking_value.append(self.energy_profile.tx_power_mW[
            packet.lora_param.tp] + (LoRaParameters.RADIO_PREP_ENERGY_MJ/(LoRaParameters.RADIO_PREP_TIME_MS*1000)))
        yield env.timeout(airtime_ms + LoRaParameters.RADIO_PREP_TIME_MS)
        self.tx_power_time_mW.append(self.env.now)
        self.tx_prev_energy_value += energy_mJ
        # TODO
        self.tx_power_value_mW.append(energy_mJ / (airtime_ms + LoRaParameters.RADIO_PREP_TIME_MS))
        self.tx_total_energy += energy_mJ

        #      Received at BS      #
        if Config.PRINT_ENABLED:
            print('{}: \t REC at BS'.format(self.node_id))
        downlink_message = self.base_station.packet_received(self, packet, env.now)
        # packet.strength = self.base_station.packetStrongEnough(packet)
        # packet.collided = self.air_interface.collided(packet)
        # packet.received = not packet.collided and packet.strength

        #            RX1 wait             #
        if Config.PRINT_ENABLED:
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
        return downlink_message

    def process_downlink_message(self, downlink_message):
        changed = False
        if downlink_message is not None:
            # change dr based on downlink_message['dr']

            # if 'weak' in downlink_message:
            # TODO ADR

            if 'dr' in downlink_message:
                if int(self.lora_param.dr) != int(downlink_message['dr']):
                    if Config.PRINT_ENABLED:
                        print('\t\t Change DR {} to {}'.format(self.lora_param.dr, downlink_message['dr']))
                    self.lora_param.change_dr_to(downlink_message['dr'])
                    changed = True
            # change tp based on downlink_message['tp']
            if 'tp' in downlink_message:
                if int(self.lora_param.tp) != int(downlink_message['tp']):
                    if Config.PRINT_ENABLED:
                        print('\t\t Change TP {} to {}'.format(self.lora_param.tp, downlink_message['tp']))
                    self.lora_param.change_tp_to(downlink_message['tp'])
                    changed = True

            if changed:
                lora_param_str = str(self.lora_param)
                if lora_param_str not in self.change_lora_param:
                    self.change_lora_param[lora_param_str] = []
                self.change_lora_param[lora_param_str].append(self.env.now)

    def log(self):
        if Config.LOG_ENABLED:
            print('---------- LOG from Node {} ----------'.format(self.node_id))
            print('\t Location {},{}'.format(self.location.x, self.location.y))
            print('\t LoRa Param {}'.format(self.lora_param))  # TODO make a list
            print('\t ADR {}'.format(self.adr))
            print('\t Payload size {}'.format(self.payload_size))
            print('\t Energy spend transmitting {0:.2f}'.format(self.tx_total_energy))
            print('\t Energy spend receiving {0:.2f}'.format(np.sum(self.rx_energy_value)))
            print('\t Energy spend sleeping {0:.2f}'.format(self.sleep_total_energy))
            print('-------------------------------------')
