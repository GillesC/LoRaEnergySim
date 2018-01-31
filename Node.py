from enum import Enum, auto

import matplotlib.pyplot as plt
import numpy as np

from EnergyProfile import EnergyProfile
from Gateway import Gateway
from Global import Config
import LoRaPacket
from LoRaParameters import LoRaParameters

from copy import deepcopy


class NodeState(Enum):
    OFFLINE = auto()
    JOIN_TX = auto()
    JOIN_RX = auto()
    SLEEP = auto()
    TX = auto()
    RX = auto()
    PROCESS = auto()


class Node:
    def __init__(self, node_id, energy_profile: EnergyProfile, lora_parameters, sleep_time, process_time, adr, location,
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

        self.sleep_time = sleep_time

        self.change_lora_param = dict()

        self.lost_packages_time = []

        self.power_tracking = {'val': [], 'time': []}

        self.energy_tracking = {'sleep': 0, 'processing': 0, 'rx': 0, 'tx': 0}

    def plot(self, prop_measurements):
        # plt.scatter(self.sleep_energy_time, self.sleep_energy_value, label='Sleep Power (mW)')
        # plt.scatter(self.proc_energy_time, self.proc_energy_value, label='Processing Energy (mW)')
        # plt.scatter(self.tx_power_time_mW, self.tx_power_value_mW, label='Tx Energy (mW)')
        plt.subplot(3, 1, 1)
        plt.plot(self.power_tracking['time'], self.power_tracking['val'], label='Power (mW)')

        # for lora_param_setting in self.change_lora_param:
        #    plt.scatter(self.change_lora_param[lora_param_setting],
        #                np.ones(len(self.change_lora_param[lora_param_setting])) * 140,
        #                label=lora_param_setting)  # 140 default
        # value (top of figure)

        plt.title(self.node_id)

        plt.subplot(3, 1, 2)
        plt.plot(prop_measurements['time'], prop_measurements['snr'], label='SNR (dBm)')
        plt.plot(prop_measurements['time'], prop_measurements['rss'], label='RSS (dBm)')

        # ax = plt.subplot(3, 1, 3)
        # for lora_param_id in self.change_lora_param:
        #     ax.scatter(self.change_lora_param[lora_param_id], np.ones(len(self.change_lora_param[lora_param_id])))
        #     ax.annotate(lora_param_id, self.change_lora_param[lora_param_id], np.ones(len(self.change_lora_param[lora_param_id])))
        # for t in self.lost_packages_time:
        #     plt.axvspan(t - 1000, t + 1000, facecolor='r', alpha=0.5)

        # Put a legend to the right of the current axis
        # ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.legend()
        # plt.plot(self.power_tracking_time, self.power_tracking_value, label='Power Tracking (mW)')
        plt.show()

    def run(self):
        random_wait = np.random.uniform(0, Config.MAX_DELAY_START_PER_NODE_MS)
        self.env.timeout(random_wait)
        if Config.PRINT_ENABLED:
            print('{} ms delayed prior to joining'.format(random_wait))
            print('{} joining the network'.format(self.node_id))
            self.join(self.env)
        if Config.PRINT_ENABLED:
            print('{}: joined the network'.format(self.node_id))
        while True:
            # added also a random wait to accommodate for any timing issues on the node itself
            random_wait = np.random.randint(0, Config.MAX_DELAY_BEFORE_SLEEP_MS)
            self.env.timeout(random_wait)

            yield self.env.process(self.sleep())

            yield self.env.process(self.processing())

            # ------------SENDING------------ #
            if Config.PRINT_ENABLED:
                print('{}: SENDING packet'.format(self.node_id))
            packet = LoRaPacket.LoRaPacket(self, self.env.now, self.lora_param, self.payload_size)
            downlink_message = yield self.env.process(self.send(packet))
            self.process_downlink_message(downlink_message)
            if Config.PRINT_ENABLED:
                print('{}: DONE sending'.format(self.node_id))

    # [----JOIN----]        [rx1]
    # computes time spent in different states during join procedure
    # TODO also allow join reqs to be collided
    def join(self, env):

        self.join_tx()

        self.join_wait()

        self.join_rx()
        return True

    def join_tx(self):

        if Config.PRINT_ENABLED:
            print('{}: \t JOIN TX'.format(self.node_id))
        energy = LoRaParameters.JOIN_TX_ENERGY_MJ

        power = (LoRaParameters.JOIN_TX_ENERGY_MJ / LoRaParameters.JOIN_TX_TIME_MS) * 1000
        self.track_power(power)
        yield self.env.timeout(LoRaParameters.JOIN_TX_TIME_MS)
        self.track_power(power)
        self.track_energy('tx', energy)

    def join_wait(self):
        if Config.PRINT_ENABLED:
            print('{}: \t JOIN WAIT'.format(self.node_id))
        self.track_power(self.energy_profile.sleep_power_mW)
        yield self.env.timeout(LoRaParameters.JOIN_ACCEPT_DELAY1)
        energy = LoRaParameters.JOIN_ACCEPT_DELAY1 * self.energy_profile.sleep_power_mW

        self.track_power(self.energy_profile.sleep_power_mW)
        self.track_energy('sleep', energy)

    def join_rx(self):
        # TODO RX1 and RX2
        if Config.PRINT_ENABLED:
            print('{}: \t JOIN RX'.format(self.node_id))
        power = (LoRaParameters.JOIN_RX_ENERGY_MJ / LoRaParameters.JOIN_RX_TIME_MS) * 1000
        self.track_power(power)
        yield self.env.timeout(LoRaParameters.JOIN_RX_TIME_MS)
        self.track_power(power)
        self.track_energy('rx', LoRaParameters.JOIN_RX_ENERGY_MJ)

    # [----transmit----]        [rx1]      [--rx2--]
    # computes time spent in different states during tx and rx one package
    def send(self, packet):

        #            TX             #
        # fixed energy overhead
        yield self.env.process(self.send_tx(packet))

        #      Received at BS      #
        if Config.PRINT_ENABLED:
            print('{}: \t REC at BS'.format(self.node_id))
        downlink_message = self.base_station.packet_received(self, packet, self.env.now)

        yield self.env.process(self.send_rx(self.env, packet, downlink_message))

        return downlink_message

    def process_downlink_message(self, downlink_message):
        changed = False
        if downlink_message is not None:
            # change dr based on downlink_message['dr']

            # if 'weak' in downlink_message:
            # TODO ADR

            if 'lost' in downlink_message:
                if downlink_message['lost']:
                    self.lost_packages_time.append(self.env.now)
                    self.node_adr()

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

    def node_adr(self):
        pass

    def log(self):
        if Config.LOG_ENABLED:
            print('---------- LOG from Node {} ----------'.format(self.node_id))
            print('\t Location {},{}'.format(self.location.x, self.location.y))
            print('\t LoRa Param {}'.format(self.lora_param))  # TODO make a list
            print('\t ADR {}'.format(self.adr))
            print('\t Payload size {}'.format(self.payload_size))
            print('\t Energy spend transmitting {0:.2f}'.format(self.energy_tracking['tx']))
            print('\t Energy spend receiving {0:.2f}'.format(self.energy_tracking['rx']))
            print('\t Energy spend sleeping {0:.2f}'.format(self.energy_tracking['sleep']))
            print('\t Energy spend processing {0:.2f}'.format(self.energy_tracking['processing']))
            print('-------------------------------------')

    def send_tx(self, packet):
        if Config.PRINT_ENABLED:
            print('{}: \t TX'.format(self.node_id))

        # self.base_station.packet_in_air(packet)
        airtime_ms = packet.my_time_on_air()
        energy_mJ = (airtime_ms * self.energy_profile.tx_power_mW[
            packet.lora_param.tp]) / 1000 + LoRaParameters.RADIO_TX_PREP_ENERGY_MJ
        self.air_interface.packet_in_air(packet, self.env.now, airtime_ms)

        power_prep_mW = LoRaParameters.RADIO_TX_PREP_ENERGY_MJ / (LoRaParameters.RADIO_TX_PREP_TIME_MS * 1000)

        self.track_power(power_prep_mW)
        yield self.env.timeout(LoRaParameters.RADIO_TX_PREP_TIME_MS)
        self.track_power(power_prep_mW)

        power_tx_mW = self.energy_profile.tx_power_mW[packet.lora_param.tp]

        self.track_power(power_tx_mW)
        yield self.env.timeout(airtime_ms)
        self.track_power(power_tx_mW)

        self.track_energy('tx', energy_mJ)

    def send_rx(self, env, packet: LoRaPacket, downlink_message):
        # TODO

        rx_on_rx1 = None
        rx_on_rx2 = None
        lost = None

        if downlink_message is not None:
            if 'tx_on_rx1' in downlink_message:
                rx_on_rx1 = downlink_message['tx_on_rx1']
                rx_on_rx2 = not rx_on_rx1
            if 'lost' in downlink_message:
                lost = downlink_message['lost']
                if lost:
                    rx_on_rx1 = False
                    rx_on_rx2 = False
        else:
            rx_on_rx1 = False
            rx_on_rx2 = False

        #            RX1 wait             #
        if Config.PRINT_ENABLED:
            print('{}: \t WAIT'.format(self.node_id))

        self.track_power(self.energy_profile.sleep_power_mW)
        yield env.timeout(LoRaParameters.RX_WINDOW_1_DELAY)
        energy = (LoRaParameters.RX_WINDOW_1_DELAY * self.energy_profile.sleep_power_mW) * 1000
        self.track_power(self.energy_profile.sleep_power_mW)
        self.track_energy('sleep', energy)

        if Config.PRINT_ENABLED:
            print('{}: \t\t RX1'.format(self.node_id))
        rx_1_rx_time, rx_1_rx_energy = yield env.process(self.send_rx_ack(1, packet, rx_on_rx1))

        self.track_power(self.energy_profile.sleep_power_mW)
        sleep_between_rx1_rx2_window = LoRaParameters.RX_WINDOW_2_DELAY - (
                LoRaParameters.RX_WINDOW_1_DELAY + rx_1_rx_time)
        yield env.timeout(sleep_between_rx1_rx2_window)
        self.track_power(self.energy_profile.sleep_power_mW)

        if Config.PRINT_ENABLED:
            print('{}: \t\t RX2'.format(self.node_id))

        if not rx_on_rx1:
            # if rx on rx1 than no more rx2
            rx_2_rx_time, rx_2_rx_energy = yield env.process(self.send_rx_ack(2, packet, rx_on_rx2))

    def send_rx_ack(self, rec_window: int, packet: LoRaPacket, ack: bool):
        rx_energy = 0

        self.track_power(self.energy_profile.rx_power['pre_mW'])
        yield self.env.timeout(self.energy_profile.rx_power['pre_ms'])
        self.track_power(self.energy_profile.rx_power['pre_mW'])

        rx_energy += self.energy_profile.rx_power['pre_mW'] * self.energy_profile.rx_power['pre_ms'] / 1000

        if not ack:

            if rec_window == 1:
                rx_time = self.lora_param.RX_1_NO_ACK_AIR_TIME[self.lora_param.dr]
                rx_energy += self.lora_param.RX_1_NO_ACK_ENERGY_MJ[self.lora_param.dr]
            else:
                rx_time = self.lora_param.RX_2_NO_ACK_AIR_TIME
                rx_energy += self.lora_param.RX_2_NO_ACK_ENERGY_MJ

            power = (rx_energy / rx_time) * 1000
            self.track_power(power)
            yield self.env.timeout(rx_time)
            self.track_power(power)

        else:
            if rec_window == 1:
                rx_time = LoRaPacket.time_on_air(12, self.lora_param)
                rx_energy += rx_time * self.energy_profile.rx_power['rx_lna_on_mW'] / 1000
                power = self.energy_profile.rx_power['rx_lna_on_mW']
            else:
                temp_lora_param = deepcopy(self.lora_param)
                temp_lora_param.change_dr_to(3)
                rx_time = LoRaPacket.time_on_air(12, temp_lora_param)
                rx_energy += rx_time * self.energy_profile.rx_power['rx_lna_off_mW'] / 1000
                power = self.energy_profile.rx_power['rx_lna_off_mW']

            self.track_power(power)
            yield self.env.timeout(rx_time)
            self.track_power(power)

            self.track_power(self.energy_profile.rx_power['post_mW'])
            yield self.env.timeout(self.energy_profile.rx_power['post_ms'])
            rx_energy += self.energy_profile.rx_power['post_mW'] * self.energy_profile.rx_power['post_ms'] / 1000
            self.track_power(self.energy_profile.rx_power['post_mW'])

        return rx_time, rx_energy

    def sleep(self):
        # ------------SLEEPING------------ #
        if Config.PRINT_ENABLED:
            print('{}: START sleeping'.format(self.node_id))
        start = self.env.now

        self.track_power(self.energy_profile.sleep_power_mW)
        yield self.env.timeout(self.sleep_time)
        self.track_power(self.energy_profile.sleep_power_mW)  # -0.0001 to not overlap in time with next state
        now = self.env.now

        time = (now - start)
        energy = (time * self.energy_profile.sleep_power_mW) / 1000

        self.track_energy('sleep', energy)

        if Config.PRINT_ENABLED:
            print('{}: Waking up [time: {}; energy: {}]'.format(self.node_id, self.env.now, energy))

    def processing(self):
        # ------------PROCESSING------------ #
        if Config.PRINT_ENABLED:
            print('{}: PROCESSING'.format(self.node_id))
        start = self.env.now
        self.track_power(self.energy_profile.proc_power_mW)

        yield self.env.timeout(self.process_time)

        now = self.env.now
        time = (now - start)
        energy = (time * self.energy_profile.sleep_power_mW) / 1000

        self.track_power(self.energy_profile.proc_power_mW)

        self.track_energy('processing', energy)

        if Config.PRINT_ENABLED:
            print('{}: DONE PROCESSING [time: {}; energy: {}]'.format(self.node_id, self.env.now, energy))

    def track_power(self, power_mW):
        self.power_tracking['time'].append(self.env.now)
        self.power_tracking['val'].append(power_mW)

    def track_energy(self, state: str, energy_consumed_mJ: float):
        self.energy_tracking[state] += energy_consumed_mJ
