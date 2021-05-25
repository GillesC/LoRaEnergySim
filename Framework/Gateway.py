from collections import deque  # circular buffer for storing SNR history for the ADR algorithm

import pandas as pd

from Framework.LoRaPacket import UplinkMessage, DownlinkMetaMessage, DownlinkMessage
from Framework.LoRaParameters import LoRaParameters
from Simulations.GlobalConfig import *


def required_snr(dr):
    req_snr = 0
    if dr == 5:
        req_snr = -7.5
    elif dr == 4:
        req_snr = -10
    elif dr == 3:
        req_snr = -12.5
    elif dr == 2:
        req_snr = -15
    elif dr == 1:
        req_snr = -17.5
    elif dr == 0:
        req_snr = -20
    else:
        ValueError('DR {} not supported'.format(dr))

    return req_snr


class Gateway:
    SENSITIVITY = {6: -121, 7: -126.5, 8: -129, 9: -131.5, 10: -134, 11: -136.5, 12: -139.5}

    def __init__(self, env, location, fast_adr_on=False, max_snr_adr=True, min_snr_adr=False, avg_snr_adr=False,
                 adr_margin_db=10):
        self.bytes_received = 0
        self.location = location
        self.packet_history = dict()
        self.packet_num_received_from = dict()
        self.distinct_packets_received = 0
        self.distinct_bytes_received_from = dict()
        self.last_distinct_packets_received_from = dict()
        self.time_off = dict()
        for channel in LoRaParameters.CHANNELS:
            self.time_off[channel] = 0
        self.dl_not_schedulable = 0
        self.uplink_packet_weak = []
        self.num_of_packet_received = 0
        self.env = env

        self.adr_margin_db = adr_margin_db  # dB

        self.fast_adr_on = fast_adr_on
        self.max_snr_adr = max_snr_adr
        self.min_snr_adr = min_snr_adr
        self.avg_snr_adr = avg_snr_adr

        self.prop_measurements = {}

    def packet_received(self, from_node, packet: UplinkMessage, now):

        downlink_meta_msg = DownlinkMetaMessage()
        downlink_msg = DownlinkMessage(dmm=downlink_meta_msg)

        """
        The packet is received at the gateway.
        The packet is no longer in the air and has not collided.
        After receiving a packet the gateway sends the packet to the Network server and executes the ADR algorithm.
        For simplification, this algorithm is executed here.
        In addition, the gateway determines the best suitable DL Rx window.
        """

        if from_node.id not in self.packet_history:
            self.packet_history[from_node.id] = deque(maxlen=20)
            self.packet_num_received_from[from_node.id] = 0
            self.distinct_bytes_received_from[from_node.id] = 0

        if packet.rss < self.SENSITIVITY[packet.lora_param.sf] or packet.snr < required_snr(packet.lora_param.dr):
            # the packet received is to weak
            downlink_meta_msg.weak_packet = True
            self.uplink_packet_weak.append(packet)
            return downlink_msg

        self.bytes_received += packet.payload_size
        self.num_of_packet_received += 1

        # everytime a distinct message is received (i.e. id is diff from previous message
        if from_node.id not in self.last_distinct_packets_received_from:
            self.distinct_packets_received += 1
        elif self.last_distinct_packets_received_from[from_node.id] != packet.id:
            self.distinct_packets_received += 1
            self.distinct_bytes_received_from[from_node.id] += packet.payload_size
        self.last_distinct_packets_received_from[from_node.id] = packet.id

        self.packet_history[from_node.id].append(packet.snr)

        if from_node.adr:
            downlink_msg.adr_param = self.adr(packet)

        # first compute if DC can be done for RX1 and RX2
        possible_rx1, time_on_air_rx1, off_time_till_rx1 = self.check_duty_cycle(12, packet.lora_param.sf,
                                                                                 packet.lora_param.freq,
                                                                                 now)
        possible_rx2, time_on_air_rx2, off_time_till_rx2 = self.check_duty_cycle(12, LoRaParameters.RX_2_DEFAULT_SF,
                                                                                 LoRaParameters.RX_2_DEFAULT_FREQ,
                                                                                 now)

        if not packet.is_confirmed_message:
            # only schedule DL message if number of received msgs is > 20, i.e. every 20
            schedule_dl = False
            if self.packet_num_received_from[from_node.id] % 20 == 0:
                schedule_dl = True
                self.packet_num_received_from[from_node.id] = 0  # count again
        else:
            schedule_dl = True

        tx_on_rx1 = False
        lost = False

        if schedule_dl and not possible_rx1 and not possible_rx2:
            lost = True
            self.dl_not_schedulable += 1
        elif schedule_dl:
            if packet.lora_param.dr > 3:
                # we would like sending on the same channel with the same DR
                if not possible_rx1:
                    if possible_rx2:
                        tx_on_rx1 = False
                else:
                    tx_on_rx1 = True
            else:
                # we would like sending it on RX2 (less robust) but sending with 27dBm
                if not possible_rx2:
                    if possible_rx1:
                        tx_on_rx1 = True
                else:
                    tx_on_rx1 = False

        if not lost:
            if schedule_dl:
                downlink_meta_msg.scheduled_receive_slot = DownlinkMetaMessage.RX_SLOT_1 if tx_on_rx1 else DownlinkMetaMessage.RX_SLOT_2
                if tx_on_rx1:
                    time_off_for_channel = packet.lora_param.freq
                    time_off_till = off_time_till_rx1
                else:
                    time_off_for_channel = LoRaParameters.RX_2_DEFAULT_FREQ
                    time_off_till = off_time_till_rx2
                self.time_off[time_off_for_channel] = time_off_till
        else:
            downlink_meta_msg.dc_limit_reached = True
        return downlink_msg

    def check_duty_cycle(self, payload_size, sf, freq, now) -> (bool, float, float):
        from Framework import LoRaPacket
        time_on_air = LoRaPacket.time_on_air(payload_size, lora_param=LoRaParameters(freq=freq, sf=sf, bw=125, cr=5, crc_enabled=1, de_enabled=0, header_implicit_mode=1))
        # it is not possible to schedule a message now on this channel for this message
        if self.time_off[freq] > self.env.now:
            return False, time_on_air, -1

        # update time_off time
        # https://github.com/things4u/things4u.github.io/blob/master/DeveloperGuide/LoRa%20documents/LoRaWAN%20Specification%201R0.pdf
        time_off = time_on_air / LoRaParameters.CHANNEL_DUTY_CYCLE[freq] - time_on_air
        off_time_till = self.env.now + time_off
        return True, time_on_air, off_time_till

    def adr(self, packet: UplinkMessage):
        history = self.packet_history[packet.node.id]

        if len(history) == 20 or self.fast_adr_on:
            # Execute adr else do nothing

            if self.max_snr_adr:
                snr_history_val = np.amax(np.asanyarray(history))
            elif self.min_snr_adr:
                snr_history_val = np.amin(np.asanyarray(history))
            elif self.avg_snr_adr:
                snr_history_val = np.average(np.asanyarray(history))
            else:
                # default
                snr_history_val = np.amax(np.asanyarray(history))

            if packet.lora_param.sf == 7:
                adr_required_snr = -7.5
            elif packet.lora_param.sf == 8:
                adr_required_snr = -10
            elif packet.lora_param.sf == 9:
                adr_required_snr = -12.5
            elif packet.lora_param.sf == 10:
                adr_required_snr = -15
            elif packet.lora_param.sf == 11:
                adr_required_snr = -17.5
            elif packet.lora_param.sf == 12:
                adr_required_snr = -20
            else:
                ValueError('SF {} not supported'.format(packet.lora_param.sf))

            snr_margin = snr_history_val - adr_required_snr - self.adr_margin_db

            num_steps = np.round(snr_margin / 3)
            # If NStep > 0 the data rate can be increased and/or power reduced.
            # If Nstep < 0, power can be increased (to the max.).

            # Note: the data rate is never decreased,
            # this is done automatically by the node if ADRACKReq's get unacknowledged.

            current_tx_power = packet.lora_param.tp
            current_dr = packet.lora_param.dr
            dr_changing = 0
            new_tx_power = current_tx_power
            new_dr = current_dr

            if num_steps > 0:
                # increase data rate by the num_steps until DR5 is reached
                num_steps_possible_dr = 5 - packet.lora_param.dr
                if num_steps > num_steps_possible_dr:
                    dr_changing = num_steps_possible_dr
                    num_steps_remaining = num_steps - num_steps_possible_dr
                    decrease_tx_power = num_steps_remaining * 3  # the remainder is used  to decrease the TXpower by
                    # 3dBm per step, until TXmin is reached. TXmin = 2 dBm for EU868.
                    new_tx_power = np.amax([current_tx_power - decrease_tx_power, 2])
                elif num_steps <= num_steps_possible_dr:
                    dr_changing = num_steps
                    # use default decrease tx power (0)
                new_dr = current_dr + dr_changing
            elif num_steps < 0:
                # TX power is increased by 3dBm per step, until TXmax is reached (=14 dBm for EU868).
                num_steps = - num_steps  # invert so we do not need to work with negative numbers
                new_tx_power = np.amin([current_tx_power + (num_steps * 3), 14])
            if PRINT_ENABLED:
                print(str({'dr': new_dr, 'tp': new_tx_power}))

            return {'dr': new_dr, 'tp': new_tx_power}
        else:
            return None

    def log(self):
        print('\n\t\t GATEWAY')
        print('Received {} packets'.format(self.num_of_packet_received))
        print('Lost {} downlink packets'.format(self.dl_not_schedulable))
        if len(self.uplink_packet_weak) != 0 and self.num_of_packet_received != 0:
            weak_ratio = len(self.uplink_packet_weak) / self.num_of_packet_received
            print('Ratio Weak/Received is {0:.2f}%'.format(weak_ratio * 100))

        print('Bytes received at gateway {0:.2f}'.format(self.bytes_received))

    def get_der(self, nodes):
        packets_sent = 0
        for node in nodes:
            packets_sent += node.packets_sent

        return self.num_of_packet_received / packets_sent

    def get_simulation_data(self, name) -> pd.Series:
        series = pd.Series({
            'BytesReceived': self.bytes_received,
            'DLPacketsLost': self.dl_not_schedulable,
            'ULWeakPackets': len(self.uplink_packet_weak),
            'PacketsReceived': self.num_of_packet_received,
            'UniquePacketsReceived': self.distinct_packets_received
        })
        series.name = name
        return series.transpose()
