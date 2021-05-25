from copy import deepcopy
from enum import Enum, auto

import matplotlib.pyplot as plt
import pandas as pd

from Framework.EnergyProfile import EnergyProfile
from Framework.Gateway import Gateway
from Framework.LoRaPacket import DownlinkMessage
from Framework.LoRaPacket import DownlinkMetaMessage
from Framework.LoRaPacket import UplinkMessage
from Framework.LoRaParameters import LoRaParameters
from Framework.Location import Location
from Simulations.GlobalConfig import *


class NodeState(Enum):
    OFFLINE = auto()
    JOIN_TX = auto()
    JOIN_RX = auto()
    SLEEP = auto()
    TX = auto()
    RADIO_TX_PREP_TIME_MS = auto()
    RX = auto()
    RADIO_PRE_RX = auto()
    RADIO_POST_RX = auto()
    PROCESS = auto()


class Node:
    def __init__(self, node_id, energy_profile: EnergyProfile, lora_parameters, sleep_time, process_time, adr, location,
                 base_station: Gateway, env, payload_size, air_interface, confirmed_messages=True,
                 massive_mimo_gain=False, number_of_antennas=1):
        self.power_gain = 1
        if massive_mimo_gain:
            self.power_gain = 1/np.sqrt(number_of_antennas)
        self.num_tx_state_changes = 0
        self.total_wait_time_because_dc = 0
        self.num_no_downlink = 0
        self.num_unique_packets_sent = 0
        self.start_device_active = 0
        self.num_collided = 0
        self.num_retransmission = 0
        self.packets_sent = 0
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

        self.prev_power_mW = 0

        self.air_interface = air_interface

        self.location = location

        self.sleep_time = sleep_time

        self.change_lora_param = dict()
        self.energy_value = 0

        self.lost_packages_time = []

        self.power_tracking = {'val': [], 'time': []}
        self.energy_measurements = {'val': [], 'time': []}
        self.state_changes = {'val': [], 'time': []}
        self.energy_tracking = {NodeState(NodeState.SLEEP).name: 0.0, NodeState(NodeState.PROCESS).name: 0.0,
                                NodeState(NodeState.RX).name: 0.0, NodeState(NodeState.TX).name: 0.0}

        self.bytes_sent = 0

        self.packet_to_sent = None

        self.time_off = dict()
        for ch in LoRaParameters.CHANNELS:
            self.time_off[ch] = 0

        self.confirmed_messages = confirmed_messages

        self.unique_packet_id = 0

    def plot(self, prop_measurements):
        plt.figure()
        # plt.scatter(self.sleep_energy_time, self.sleep_energy_value, label='Sleep Power (mW)')
        # plt.scatter(self.proc_energy_time, self.proc_energy_value, label='Processing Energy (mW)')
        # plt.scatter(self.tx_power_time_mW, self.tx_power_value_mW, label='Tx Energy (mW)')
        plt.subplot(3, 1, 1)
        plt.plot(self.power_tracking['time'], self.power_tracking['val'], label='Power (mW)')

        plt.subplot(3, 1, 2)
        plt.plot(self.energy_measurements['time'], self.energy_measurements['val'], label='Energy (mJ)')

        # for lora_param_setting in self.change_lora_param:
        #    plt.scatter(self.change_lora_param[lora_param_setting],
        #                np.ones(len(self.change_lora_param[lora_param_setting])) * 140,
        #                label=lora_param_setting)  # 140 default
        # value (top of figure)

        plt.title(self.id)

        plt.subplot(3, 1, 3)
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
        random_wait = np.random.uniform(0,  MAX_DELAY_START_PER_NODE_MS)
        yield self.env.timeout(random_wait)
        self.start_device_active = self.env.now
        if  PRINT_ENABLED:
            print('{} ms delayed prior to joining'.format(random_wait))
            print('{} joining the network'.format(self.id))
            # TODO ERROR!!!!! self.process
            self.join(self.env)
        if  PRINT_ENABLED:
            print('{}: joined the network'.format(self.id))
        while True:
            # added also a random wait to accommodate for any timing issues on the node itself
            random_wait = np.random.randint(0,  MAX_DELAY_BEFORE_SLEEP_MS)
            yield self.env.timeout(random_wait)

            yield self.env.process(self.sleep())

            yield self.env.process(self.processing())
            # after processing go back to sleep
            self.track_power(self.energy_profile.sleep_power_mW)

            # ------------SENDING------------ #
            if  PRINT_ENABLED:
                print('{}: SENDING packet'.format(self.id))

            self.unique_packet_id += 1

            payload_size = self.payload_size
            if MAC_IMPROVEMENT and self.packets_sent < 20:
                payload_size = 5

            packet = UplinkMessage(node=self, start_on_air=self.env.now, payload_size=payload_size,
                                   confirmed_message=self.confirmed_messages, id=self.unique_packet_id)
            downlink_message = yield self.env.process(self.send(packet))
            if downlink_message is None:
                # message is collided and not received at the BS
                yield self.env.process(self.dl_message_lost())
            else:
                yield self.env.process(self.process_downlink_message(downlink_message, packet))

            if  PRINT_ENABLED:
                print('{}: DONE sending'.format(self.id))

            self.num_unique_packets_sent += 1  # at the end to be sure that this packet was tx

    # [----JOIN----]        [rx1]
    # computes time spent in different states during join procedure
    # TODO also allow join reqs to be collided
    def join(self, env):

        self.join_tx()

        self.join_wait()

        self.join_rx()
        return True

    def join_tx(self):

        if  PRINT_ENABLED:
            print('{}: \t JOIN TX'.format(self.id))
        energy = LoRaParameters.JOIN_TX_ENERGY_MJ

        power = (LoRaParameters.JOIN_TX_ENERGY_MJ / LoRaParameters.JOIN_TX_TIME_MS) * 1000
        self.track_power(power)
        yield self.env.timeout(LoRaParameters.JOIN_TX_TIME_MS)
        self.track_power(power)
        self.track_energy('tx', energy)

    def join_wait(self):
        if  PRINT_ENABLED:
            print('{}: \t JOIN WAIT'.format(self.id))
        self.track_power(self.energy_profile.sleep_power_mW)
        yield self.env.timeout(LoRaParameters.JOIN_ACCEPT_DELAY1)
        energy = LoRaParameters.JOIN_ACCEPT_DELAY1 * self.energy_profile.sleep_power_mW

        self.track_power(self.energy_profile.sleep_power_mW)
        self.track_energy('sleep', energy)

    def join_rx(self):
        # TODO RX1 and RX2
        if  PRINT_ENABLED:
            print('{}: \t JOIN RX'.format(self.id))
        power = (LoRaParameters.JOIN_RX_ENERGY_MJ / LoRaParameters.JOIN_RX_TIME_MS) * 1000
        self.track_power(power)
        yield self.env.timeout(LoRaParameters.JOIN_RX_TIME_MS)
        self.track_power(power)
        self.track_energy('rx', LoRaParameters.JOIN_RX_ENERGY_MJ)

    # [----transmit----]        [rx1]      [--rx2--]
    # computes time spent in different states during tx and rx one package
    def send(self, packet):

        self.packet_to_sent = packet
        airtime = packet.my_time_on_air()

        # check channel with lowest wait time
        channel = min(self.time_off, key=self.time_off.get)
        # update to best_channel
        packet.lora_param.freq = channel

        if self.time_off[channel] > self.env.now:
            # wait for certaint time to respect duty cycle
            wait = self.time_off[channel] - self.env.now
            self.change_state(NodeState.SLEEP)
            self.total_wait_time_because_dc += wait
            yield self.env.timeout(wait)

        # update time_off time
        # https://github.com/things4u/things4u.github.io/blob/master/DeveloperGuide/LoRa%20documents/LoRaWAN%20Specification%201R0.pdf
        time_off = airtime / LoRaParameters.CHANNEL_DUTY_CYCLE[channel] - airtime
        self.time_off[channel] = self.env.now + time_off

        #            TX             #
        # fixed energy overhead
        collided = yield self.env.process(self.send_tx(packet))
        # print('\t Our packet has collided (2)')

        #      Received at BS      #

        if not collided:
            if  PRINT_ENABLED:
                print('{}: \t REC at BS'.format(self.id))
            downlink_message = self.base_station.packet_received(self, packet, self.env.now)
        else:
            self.num_collided += 1
            downlink_message = None

        yield self.env.process(self.send_rx(self.env, packet, downlink_message))

        return downlink_message

    def process_downlink_message(self, downlink_message, uplink_message):
        changed = False
        if downlink_message is None:
            ValueError('DL message can not be None')

        if downlink_message.meta.is_lost():
            # this is because no ack could be sent
            self.lost_packages_time.append(self.env.now)
            yield self.env.process(self.dl_message_lost())

        if downlink_message.adr_param is not None and self.adr:
            if int(self.lora_param.dr) != int(downlink_message.adr_param['dr']):
                if  PRINT_ENABLED:
                    print('\t\t Change DR {} to {}'.format(self.lora_param.dr, downlink_message.adr_param['dr']))
                self.lora_param.change_dr_to(downlink_message.adr_param['dr'])
                changed = True
            # change tp based on downlink_message['tp']
            if int(self.lora_param.tp) != int(downlink_message.adr_param['tp']):
                if  PRINT_ENABLED:
                    print('\t\t Change TP {} to {}'.format(self.lora_param.tp, downlink_message.adr_param['tp']))
                self.lora_param.change_tp_to(downlink_message.adr_param['tp'])
                changed = True

        if changed:
            lora_param_str = str(self.lora_param)
            if lora_param_str not in self.change_lora_param:
                self.change_lora_param[lora_param_str] = []
            self.change_lora_param[lora_param_str].append(self.env.now)

    def log(self):
        if  LOG_ENABLED:
            print('---------- LOG from Node {} ----------'.format(self.id))
            print('\t Location {},{}'.format(self.location.x, self.location.y))
            print('\t Distance from gateway {}'.format(Location.distance(self.location, self.base_station.location)))
            print('\t LoRa Param {}'.format(self.lora_param))
            print('\t ADR {}'.format(self.adr))
            print('\t Payload size {}'.format(self.payload_size))
            print('\t Energy spend transmitting {0:.2f}'.format(self.energy_tracking[NodeState(NodeState.TX).name]))
            print('\t Energy spend receiving {0:.2f}'.format(self.energy_tracking[NodeState(NodeState.RX).name]))
            print('\t Energy spend sleeping {0:.2f}'.format(self.energy_tracking[NodeState(NodeState.SLEEP).name]))
            print('\t Energy spend processing {0:.2f}'.format(self.energy_tracking[NodeState(NodeState.PROCESS).name]))
            for lora_param, t in self.change_lora_param.items():
                print('\t {}:{}'.format(lora_param, t))
            print('Bytes sent by node {}'.format(self.bytes_sent))
            print('Total Packets sent by node {}'.format(self.packets_sent))
            print('Total Packets sent by node (according to tx state changes) {}'.format(self.num_tx_state_changes))
            print('Unique Packets sent by node {}'.format(self.num_unique_packets_sent))
            print('Retransmissions {}'.format(self.num_retransmission))
            print('Packets collided {}'.format(self.num_collided))
            print('-------------------------------------')

    def send_tx(self, packet: UplinkMessage) -> bool:

        self.packets_sent += 1
        self.bytes_sent += packet.payload_size

        self.energy_value += packet.lora_param.tp + (5 - packet.lora_param.dr)

        if  PRINT_ENABLED:
            print('{}: \t TX'.format(self.id))

        self.change_state(NodeState.RADIO_TX_PREP_TIME_MS)
        yield self.env.timeout(LoRaParameters.RADIO_TX_PREP_TIME_MS)

        packet.on_air = self.env.now
        self.air_interface.packet_in_air(packet)

        self.change_state(NodeState.TX)
        yield self.env.timeout(packet.my_time_on_air())
        collided = self.air_interface.packet_received(packet)
        return collided

    def send_rx(self, env, packet: UplinkMessage, downlink_message: DownlinkMessage):

        if downlink_message is None:
            rx_on_rx1 = False
            rx_on_rx2 = False
        else:
            rx_on_rx1 = downlink_message.meta.scheduled_receive_slot == DownlinkMetaMessage.RX_SLOT_1
            rx_on_rx2 = downlink_message.meta.scheduled_receive_slot == DownlinkMetaMessage.RX_SLOT_2

        # RX1 wait             #
        if  PRINT_ENABLED:
            print('{}: \t WAIT'.format(self.id))

        self.change_state(NodeState.SLEEP)

        yield env.timeout(LoRaParameters.RX_WINDOW_1_DELAY)

        if  PRINT_ENABLED:
            print('{}: \t\t RX1'.format(self.id))

        # changed_state is called internally
        begin = self.env.now
        yield env.process(self.send_rx_ack(1, packet, rx_on_rx1))
        rx_1_rx_time = self.env.now - begin

        sleep_between_rx1_rx2_window = LoRaParameters.RX_WINDOW_2_DELAY - (
            LoRaParameters.RX_WINDOW_1_DELAY + rx_1_rx_time)
        if sleep_between_rx1_rx2_window > 0:
            self.change_state(NodeState.SLEEP)
            yield env.timeout(sleep_between_rx1_rx2_window)

        if  PRINT_ENABLED:
            print('{}: \t\t RX2'.format(self.id))

        if not rx_on_rx1:
            # changed_state is called internally
            yield env.process(self.send_rx_ack(2, packet, rx_on_rx2))

    def send_rx_ack(self, rec_window: int, packet: UplinkMessage, ack: bool):

        self.change_state(NodeState.RADIO_PRE_RX)
        yield self.env.timeout(self.energy_profile.rx_power['pre_ms'])

        if not ack:

            if rec_window == 1:
                rx_time = packet.lora_param.RX_1_NO_ACK_AIR_TIME[packet.lora_param.dr]
                rx_energy = packet.lora_param.RX_1_NO_ACK_ENERGY_MJ[packet.lora_param.dr]
            else:
                rx_time = packet.lora_param.RX_2_NO_ACK_AIR_TIME
                rx_energy = packet.lora_param.RX_2_NO_ACK_ENERGY_MJ

            power = (rx_energy / rx_time) * 1000
        else:
            from Framework import LoRaPacket
            if rec_window == 1:
                rx_time = LoRaPacket.time_on_air(12, packet.lora_param)
                rx_energy = (rx_time / 1000) * self.energy_profile.rx_power['rx_lna_on_mW']
                power = self.energy_profile.rx_power['rx_lna_on_mW']
            else:
                temp_lora_param = deepcopy(packet.lora_param)
                temp_lora_param.change_dr_to(3)
                rx_time = LoRaPacket.time_on_air(12, temp_lora_param)
                rx_energy = (rx_time / 1000) * self.energy_profile.rx_power['rx_lna_off_mW']
                power = self.energy_profile.rx_power['rx_lna_off_mW']

        self.change_state(NodeState.RX, consumed_power=power, consumed_energy=rx_energy)
        yield self.env.timeout(rx_time)

        if ack:
            self.change_state(NodeState.RADIO_POST_RX)
            yield self.env.timeout(self.energy_profile.rx_power['post_ms'])

    def sleep(self):
        # ------------SLEEPING------------ #
        if  PRINT_ENABLED:
            print('{}: START sleeping'.format(self.id))
        self.change_state(NodeState.SLEEP)
        yield self.env.timeout(self.sleep_time)

    def processing(self):
        # ------------PROCESSING------------ #
        if  PRINT_ENABLED:
            print('{}: PROCESSING'.format(self.id))
        self.change_state(NodeState.PROCESS)
        yield self.env.timeout(self.process_time)

    def dl_message_lost(self):
        self.num_no_downlink += 1
        packet = self.packet_to_sent
        if packet.is_confirmed_message:
            if packet.ack_retries_cnt < LoRaParameters.MAX_ACK_RETRIES:
                packet.ack_retries_cnt += 1
                if (packet.ack_retries_cnt % 2) == 1:
                    dr = np.amax([self.lora_param.dr - 1, LoRaParameters.LORAMAC_TX_MIN_DATARATE])
                    self.lora_param.change_dr_to(dr)
                    packet.lora_param = self.lora_param

                # set packet as retransmitted packet
                packet.unique = False
                downlink_message = yield self.env.process(self.send(packet))

                # after yield to be sure a transmission was sent
                self.num_retransmission += 1

                if downlink_message is None:
                    yield self.env.process(self.dl_message_lost())
                else:
                    yield self.env.process(self.process_downlink_message(downlink_message, packet))

            else:
                # TODO go to default
                NotImplementedError('This is not yet implemented')

    def change_state(self, new_state: NodeState, consumed_power=None, consumed_energy=None):
        if self.current_state == new_state:
            ValueError('You can not change state ({}) when the states are the same'.format(NodeState(new_state).name))
        else:
            self.track_state_change(new_state)
            self.track_power(self.prev_power_mW)  # this for figure purposes only
            track_node_state = new_state
            # track power and track energy consumed
            power_consumed_in_state_mW = 0
            energy_consumed_in_state_mJ = 0
            packet = self.packet_to_sent
            if self.current_state == NodeState.SLEEP:
                # if the previous state was sleep
                # record new energy state
                time_duration_sleep_s = (self.env.now - self.sleep_start_time) / 1000
                power_consumed_in_state_mW = self.energy_profile.sleep_power_mW
                energy_consumed_in_state_mJ = power_consumed_in_state_mW * time_duration_sleep_s
                # first track otherwise the next state will overwrite this
                self.track_power(power_consumed_in_state_mW)
                self.track_energy(NodeState.SLEEP, energy_consumed_in_state_mJ)
            if new_state == NodeState.RADIO_TX_PREP_TIME_MS:
                power_consumed_in_state_mW = LoRaParameters.RADIO_TX_PREP_ENERGY_MJ / (
                    LoRaParameters.RADIO_TX_PREP_TIME_MS / 1000)
                energy_consumed_in_state_mJ = LoRaParameters.RADIO_TX_PREP_ENERGY_MJ
                track_node_state = NodeState.TX
            elif new_state == NodeState.TX:
                power_consumed_in_state_mW = self.energy_profile.tx_power_mW[packet.lora_param.tp]*self.power_gain
                energy_consumed_in_state_mJ = power_consumed_in_state_mW * (packet.my_time_on_air() / 1000)
                self.num_tx_state_changes += 1
            elif new_state == NodeState.RADIO_PRE_RX:
                power_consumed_in_state_mW = self.energy_profile.rx_power['pre_mW']
                energy_consumed_in_state_mJ = self.energy_profile.rx_power['pre_mW'] * self.energy_profile.rx_power[
                    'pre_ms'] / 1000
                track_node_state = NodeState.RX
            elif new_state == NodeState.RX:
                power_consumed_in_state_mW = consumed_power
                energy_consumed_in_state_mJ = consumed_energy
            elif new_state == NodeState.RADIO_POST_RX:
                track_node_state = NodeState.RX
                power_consumed_in_state_mW = self.energy_profile.rx_power['post_mW']
                energy_consumed_in_state_mJ = self.energy_profile.rx_power['post_mW'] * (self.energy_profile.rx_power[
                                                                                             'post_ms'] / 1000)
            elif new_state == NodeState.SLEEP:
                # only set sleep start time
                # this is handled when a state is changed
                self.sleep_start_time = self.env.now
                power_consumed_in_state_mW = self.energy_profile.sleep_power_mW
                # we can not yet determine energy consumed
            elif new_state == NodeState.PROCESS:
                energy_consumed_in_state_mJ = (self.process_time / 1000) * self.energy_profile.sleep_power_mW
                power_consumed_in_state_mW = self.energy_profile.sleep_power_mW
            elif new_state != NodeState.OFFLINE:
                ValueError('State is not recognized')

            self.track_power(power_consumed_in_state_mW)
            self.track_energy(track_node_state, energy_consumed_in_state_mJ)
            self.prev_power_mW = power_consumed_in_state_mW
            self.current_state = new_state

    def energy_per_bit(self) -> float:
        return self.total_energy_consumed() / (self.packets_sent * self.payload_size * 8)

    def transmit_related_energy_per_bit(self) -> float:
        return self.transmit_related_energy_consumed() / (self.packets_sent * self.payload_size * 8)

    def transmit_related_energy_per_unique_bit(self) -> float:
        return self.transmit_related_energy_consumed() / (self.num_unique_packets_sent * self.payload_size * 8)

    def transmit_related_energy_consumed(self) -> float:
        return self.energy_tracking[NodeState(NodeState.TX).name] + self.energy_tracking[NodeState(NodeState.RX).name]

    def total_energy_consumed(self) -> float:
        total_energy = 0
        for key, value in self.energy_tracking.items():
            total_energy += value
        return total_energy

    def track_power(self, power_mW):
        self.power_tracking['time'].append(self.env.now)
        self.power_tracking['val'].append(power_mW)

    def track_energy(self, state: NodeState, energy_consumed_mJ: float):
        self.energy_measurements['time'].append(self.env.now)
        self.energy_measurements['val'].append(energy_consumed_mJ)
        self.energy_tracking[NodeState(state).name] += energy_consumed_mJ

    def track_state_change(self, new_state):
        self.state_changes['time'].append(self.env.now)
        self.state_changes['val'].append(new_state)

    def get_simulation_data(self) -> pd.Series:
        series = {
            'WaitTimeDC': self.total_wait_time_because_dc / 1000,  # [s] instead of [ms]
            'NoDLReceived': self.num_no_downlink,
            'UniquePackets': self.num_unique_packets_sent,
            'TotalPackets': self.packets_sent,
            'CollidedPackets': self.num_collided,
            'RetransmittedPackets': self.num_retransmission,
            'TotalBytes': self.bytes_sent,
            'TotalEnergy': self.total_energy_consumed(),
            'TxRxEnergy': self.transmit_related_energy_consumed(),
            'EnergyValuePackets': self.energy_value
        }
        return pd.Series(series)

    @staticmethod
    def get_simulation_data_frame(nodes: list) -> pd.DataFrame:
        column_names = ['WaitTimeDC', 'NoDLReceived', 'UniquePackets', 'TotalPackets', 'CollidedPackets',
                        'RetransmittedPackets', 'TotalBytes', 'TotalEnergy', 'TxRxEnergy', 'EnergyValuePackets']
        pdf = pd.DataFrame(columns=column_names)
        list_of_series = []
        for node in nodes:
            list_of_series.append(node.get_simulation_data())
        return pdf.append(list_of_series)

    @staticmethod
    def get_mean_simulation_data_frame(nodes: list, name) -> pd.DataFrame:
        data = Node.get_simulation_data_frame(nodes).sum(axis=0)
        data.name = name
        return pd.DataFrame(data).transpose()

    @staticmethod
    def get_energy_per_byte_stats(nodes: list, gateway: Gateway) -> (float, float):
        unique_bytes = gateway.distinct_bytes_received_from
        en_list = []
        for node in nodes:
            if node.id in unique_bytes:
                en_list.append(node.transmit_related_energy_consumed() / unique_bytes[node.id])
        en_list = np.array(en_list)
        return np.mean(en_list), np.std(en_list)
