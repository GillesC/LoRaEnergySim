from enum import Enum, auto

import matplotlib.pyplot as plt
import numpy as np

from EnergyProfile import EnergyProfile
from Gateway import Gateway
from Global import Config
from LoRaPacket import UplinkMessage
from LoRaPacket import DownlinkMessage
from LoRaPacket import DownlinkMetaMessage
from LoRaParameters import LoRaParameters

from copy import deepcopy

from Location import Location


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
        self.num_unique_packets_sent = 0
        self.start_device_active = 0
        self.num_collided = 0
        self.num_retransmission = 0
        self.packets_sent = 0
        self.last_packet = None
        self.adr = adr
        self.id = node_id
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

        self.bytes_sent = 0

        self.radio_on_time = dict()
        for ch in LoRaParameters.DEFAULT_CHANNELS:
            self.radio_on_time[ch] = 0

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

        plt.title(self.id)

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
        yield self.env.timeout(random_wait)
        self.start_device_active = self.env.now
        if Config.PRINT_ENABLED:
            print('{} ms delayed prior to joining'.format(random_wait))
            print('{} joining the network'.format(self.id))
            self.join(self.env)
        if Config.PRINT_ENABLED:
            print('{}: joined the network'.format(self.id))
        while True:
            # added also a random wait to accommodate for any timing issues on the node itself
            random_wait = np.random.randint(0, Config.MAX_DELAY_BEFORE_SLEEP_MS)
            yield self.env.timeout(random_wait)

            yield self.env.process(self.sleep())

            yield self.env.process(self.processing())

            # ------------SENDING------------ #
            if Config.PRINT_ENABLED:
                print('{}: SENDING packet'.format(self.id))

            packet = UplinkMessage(self, self.env.now, self.payload_size)
            self.last_packet = packet
            downlink_message = yield self.env.process(self.send(packet))
            if downlink_message is None:
                yield self.env.process(self.dl_message_lost(packet))
            else:
                yield self.env.process(self.process_downlink_message(downlink_message))

            if Config.PRINT_ENABLED:
                print('{}: DONE sending'.format(self.id))

            self.num_unique_packets_sent += 1 # at the end to be sure that this packet was tx

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
            print('{}: \t JOIN TX'.format(self.id))
        energy = LoRaParameters.JOIN_TX_ENERGY_MJ

        power = (LoRaParameters.JOIN_TX_ENERGY_MJ / LoRaParameters.JOIN_TX_TIME_MS) * 1000
        self.track_power(power)
        yield self.env.timeout(LoRaParameters.JOIN_TX_TIME_MS)
        self.track_power(power)
        self.track_energy('tx', energy)

    def join_wait(self):
        if Config.PRINT_ENABLED:
            print('{}: \t JOIN WAIT'.format(self.id))
        self.track_power(self.energy_profile.sleep_power_mW)
        yield self.env.timeout(LoRaParameters.JOIN_ACCEPT_DELAY1)
        energy = LoRaParameters.JOIN_ACCEPT_DELAY1 * self.energy_profile.sleep_power_mW

        self.track_power(self.energy_profile.sleep_power_mW)
        self.track_energy('sleep', energy)

    def join_rx(self):
        # TODO RX1 and RX2
        if Config.PRINT_ENABLED:
            print('{}: \t JOIN RX'.format(self.id))
        power = (LoRaParameters.JOIN_RX_ENERGY_MJ / LoRaParameters.JOIN_RX_TIME_MS) * 1000
        self.track_power(power)
        yield self.env.timeout(LoRaParameters.JOIN_RX_TIME_MS)
        self.track_power(power)
        self.track_energy('rx', LoRaParameters.JOIN_RX_ENERGY_MJ)

    # [----transmit----]        [rx1]      [--rx2--]
    # computes time spent in different states during tx and rx one package
    def send(self, packet):

        channel = packet.lora_param.freq
        airtime = packet.my_time_on_air()
        on_time = self.radio_on_time[channel]

        if on_time != 0:

            duty_cycle = ((on_time +airtime )/ (self.env.now - self.start_device_active))*100

            if duty_cycle > LoRaParameters.CHANNEL_DUTY_CYCLE_PROC[channel]:
                max_dc = LoRaParameters.CHANNEL_DUTY_CYCLE_PROC[channel]/100
                total_time = self.env.now - self.start_device_active
                # we need to wait to respect the duty cycle
                wait = (on_time + airtime - max_dc*total_time - max_dc*airtime)/max_dc
                #check_dc = (on_time + airtime)/(total_time+wait+airtime)
                if Config.PRINT_ENABLED:
                    print('Waiting {} to respect the duty cycle'.format(wait))
                yield self.env.timeout(wait)

        self.bytes_sent += packet.payload_size

        #            TX             #
        # fixed energy overhead
        collided = yield self.env.process(self.send_tx(packet))

        #      Received at BS      #

        if not collided:
            if Config.PRINT_ENABLED:
                print('{}: \t REC at BS'.format(self.id))
            downlink_message = self.base_station.packet_received(self, packet, self.env.now)
        else:
            self.num_collided += 1
            downlink_message = None

        yield self.env.process(self.send_rx(self.env, packet, downlink_message))

        return downlink_message

    def process_downlink_message(self, downlink_message):
        changed = False
        if downlink_message is None:
            ValueError('DL message can not be None')

        # TODO first extract information, than process it

        if downlink_message is not None:

            if downlink_message.meta.is_lost():
                self.lost_packages_time.append(self.env.now)
                yield self.env.process(self.dl_message_lost(self.last_packet))

            if downlink_message.adr_param is not None:
                if int(self.lora_param.dr) != int(downlink_message.adr_param['dr']):
                    #if Config.PRINT_ENABLED:
                    print('\t\t Change DR {} to {}'.format(self.lora_param.dr, downlink_message.adr_param['dr']))
                    self.lora_param.change_dr_to(downlink_message.adr_param['dr'])
                    changed = True
                # change tp based on downlink_message['tp']
                if int(self.lora_param.tp) != int(downlink_message.adr_param['tp']):
                    #if Config.PRINT_ENABLED:
                    print('\t\t Change TP {} to {}'.format(self.lora_param.tp, downlink_message.adr_param['tp']))
                    self.lora_param.change_tp_to(downlink_message.adr_param['tp'])
                    changed = True

            if changed:
                lora_param_str = str(self.lora_param)
                if lora_param_str not in self.change_lora_param:
                    self.change_lora_param[lora_param_str] = []
                self.change_lora_param[lora_param_str].append(self.env.now)

    def log(self):
        if Config.LOG_ENABLED:
            print('---------- LOG from Node {} ----------'.format(self.id))
            print('\t Location {},{}'.format(self.location.x, self.location.y))
            print('\t Distance from gateway {}'.format(Location.distance(self.location, self.base_station.location)))
            print('\t LoRa Param {}'.format(self.lora_param))
            print('\t ADR {}'.format(self.adr))
            print('\t Payload size {}'.format(self.payload_size))
            print('\t Energy spend transmitting {0:.2f}'.format(self.energy_tracking['tx']))
            print('\t Energy spend receiving {0:.2f}'.format(self.energy_tracking['rx']))
            print('\t Energy spend sleeping {0:.2f}'.format(self.energy_tracking['sleep']))
            print('\t Energy spend processing {0:.2f}'.format(self.energy_tracking['processing']))
            for lora_param, t in self.change_lora_param.items():
                print('\t {}:{}'.format(lora_param, t))
            print('Bytes sent by node {}'.format(self.bytes_sent))
            print('Total Packets sent by node {}'.format(self.packets_sent))
            print('Unique Packets sent by node {}'.format(self.num_unique_packets_sent))
            print('Retransmissions {}'.format(self.num_retransmission))
            print('Packets collided {}'.format(self.num_collided))
            print('-------------------------------------')

    def send_tx(self, packet: UplinkMessage) -> bool:

        self.packets_sent += 1

        if Config.PRINT_ENABLED:
            print('{}: \t TX'.format(self.id))

        # self.base_station.packet_in_air(packet)
        airtime_ms = packet.my_time_on_air()
        self.radio_on_time[packet.lora_param.freq] += airtime_ms
        energy_mJ = (airtime_ms * self.energy_profile.tx_power_mW[
            packet.lora_param.tp]) / 1000 + LoRaParameters.RADIO_TX_PREP_ENERGY_MJ

        power_prep_mW = LoRaParameters.RADIO_TX_PREP_ENERGY_MJ / (LoRaParameters.RADIO_TX_PREP_TIME_MS * 1000)

        self.track_power(power_prep_mW)
        yield self.env.timeout(LoRaParameters.RADIO_TX_PREP_TIME_MS)
        self.track_power(power_prep_mW)

        packet.on_air = self.env.now
        self.air_interface.packet_in_air(packet)

        power_tx_mW = self.energy_profile.tx_power_mW[packet.lora_param.tp]

        self.track_power(power_tx_mW)
        yield self.env.timeout(airtime_ms)
        self.track_power(power_tx_mW)

        collided = self.air_interface.packet_received(packet)

        self.track_energy('tx', energy_mJ)

        return collided

    def send_rx(self, env, packet: UplinkMessage, downlink_message: DownlinkMessage):

        if downlink_message is None:
            rx_on_rx1 = False
            rx_on_rx2 = False
        else:
            rx_on_rx1 = downlink_message.meta.scheduled_receive_slot == DownlinkMetaMessage.RX_SLOT_1
            rx_on_rx2 = downlink_message.meta.scheduled_receive_slot == DownlinkMetaMessage.RX_SLOT_2

        # RX1 wait             #
        if Config.PRINT_ENABLED:
            print('{}: \t WAIT'.format(self.id))

        self.track_power(self.energy_profile.sleep_power_mW)
        yield env.timeout(LoRaParameters.RX_WINDOW_1_DELAY)
        energy = (LoRaParameters.RX_WINDOW_1_DELAY * self.energy_profile.sleep_power_mW) * 1000
        self.track_power(self.energy_profile.sleep_power_mW)
        self.track_energy('sleep', energy)

        if Config.PRINT_ENABLED:
            print('{}: \t\t RX1'.format(self.id))

        rx_1_rx_time, rx_1_rx_energy = yield env.process(self.send_rx_ack(1, packet, rx_on_rx1))

        self.track_energy('rx', rx_1_rx_energy)

        self.track_power(self.energy_profile.sleep_power_mW)
        sleep_between_rx1_rx2_window = LoRaParameters.RX_WINDOW_2_DELAY - (
            LoRaParameters.RX_WINDOW_1_DELAY + rx_1_rx_time)
        yield env.timeout(sleep_between_rx1_rx2_window)
        self.track_power(self.energy_profile.sleep_power_mW)

        if Config.PRINT_ENABLED:
            print('{}: \t\t RX2'.format(self.id))

        if not rx_on_rx1:  # TODO check if check is needed msg received (not lost or dc limit reached)
            # if rx on rx1 than no more rx2
            rx_2_rx_time, rx_2_rx_energy = yield env.process(self.send_rx_ack(2, packet, rx_on_rx2))
            self.track_energy('rx', rx_2_rx_energy)

    def send_rx_ack(self, rec_window: int, packet: UplinkMessage, ack: bool):
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
            import LoRaPacket
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
            print('{}: START sleeping'.format(self.id))
        start = self.env.now

        self.track_power(self.energy_profile.sleep_power_mW)
        yield self.env.timeout(self.sleep_time)
        self.track_power(self.energy_profile.sleep_power_mW)  # -0.0001 to not overlap in time with next state
        now = self.env.now

        time = (now - start)
        energy = (time * self.energy_profile.sleep_power_mW) / 1000

        self.track_energy('sleep', energy)

        if Config.PRINT_ENABLED:
            print('{}: Waking up [time: {}; energy: {}]'.format(self.id, self.env.now, energy))

    def processing(self):
        # ------------PROCESSING------------ #
        if Config.PRINT_ENABLED:
            print('{}: PROCESSING'.format(self.id))
        start = self.env.now
        self.track_power(self.energy_profile.proc_power_mW)

        yield self.env.timeout(self.process_time)

        now = self.env.now
        time = (now - start)
        energy = (time * self.energy_profile.sleep_power_mW) / 1000

        self.track_power(self.energy_profile.proc_power_mW)

        self.track_energy('processing', energy)

        if Config.PRINT_ENABLED:
            print('{}: DONE PROCESSING [time: {}; energy: {}]'.format(self.id, self.env.now, energy))

    def track_power(self, power_mW):
        self.power_tracking['time'].append(self.env.now)
        self.power_tracking['val'].append(power_mW)

    def track_energy(self, state: str, energy_consumed_mJ: float):
        self.energy_tracking[state] += energy_consumed_mJ

    def dl_message_lost(self, packet: UplinkMessage):

        if self.adr:
            if self.last_packet.ack_retries_cnt < LoRaParameters.MAX_ACK_RETRIES:
                self.last_packet.ack_retries_cnt += 1
                if (self.last_packet.ack_retries_cnt % 2) == 1:
                    dr = np.amax([self.lora_param.dr - 1, LoRaParameters.LORAMAC_TX_MIN_DATARATE])
                    self.lora_param.change_dr_to(dr)

                # print('retry {}'.format(self.last_packet.ack_retries_cnt))
                self.num_retransmission +=1
                downlink_message = yield self.env.process(self.send(packet))

                if downlink_message is None:
                    yield self.env.process(self.dl_message_lost(packet))
                else:
                    yield self.env.process(self.process_downlink_message(downlink_message))



            else:
                # TODO go to default
                pass
