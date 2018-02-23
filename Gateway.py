from collections import deque  # circular buffer for storing SNR history for the ADR algorithm

import numpy as np

from LoRaPacket import UplinkMessage, DownlinkMetaMessage, DownlinkMessage
from Global import Config
from LoRaParameters import LoRaParameters
import pandas as pd


# sensititity : https://www.semtech.com/uploads/documents/sx1272.pdf
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
    SENSITIVITY = {6: -121, 7: -124, 8: -127, 9: -130, 10: -133, 11: -135, 12: -137}
    ADR_MARGIN_DB = 10  # dB

    def __init__(self, env, location):
        self.bytes_received = 0
        self.location = location
        self.packet_history = dict()
        self.channel_time_used = dict()
        for channel in LoRaParameters.CHANNELS:
            self.channel_time_used[channel] = 0
        self.downlink_packets_lost = []
        self.uplink_packet_weak = []
        for freq in LoRaParameters.DEFAULT_CHANNELS:
            self.channel_time_used[freq] = 0
        self.num_of_packet_received = 0

        self.env = env

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

        if packet.rss < self.SENSITIVITY[packet.lora_param.sf] or packet.snr < required_snr(packet.lora_param.dr):
            # the packet received is to weak
            downlink_meta_msg.weak_packet = True
            self.uplink_packet_weak.append(packet)
            return downlink_msg

        self.bytes_received += packet.payload_size
        self.num_of_packet_received += 1

        self.packet_history[from_node.id].append(packet.snr)

        if from_node.adr:
            downlink_msg.adr_param = self.adr(packet)

        # first compute if DC can be done for RX1 and RX2
        possible_rx1, time_on_air_rx1 = self.check_duty_cycle(12, packet.lora_param.sf, packet.lora_param.freq,
                                                              now)
        possible_rx2, time_on_air_rx2 = self.check_duty_cycle(12, LoRaParameters.RX_2_DEFAULT_SF,
                                                              LoRaParameters.RX_2_DEFAULT_FREQ, now)

        tx_on_rx1 = False

        lost = False

        if packet.lora_param.dr > 3:
            # we would like sending on the same channel with the same DR
            if not possible_rx1:
                if not possible_rx2:
                    self.downlink_packets_lost.append(packet)
                    lost = True
                else:
                    tx_on_rx1 = False
            else:
                tx_on_rx1 = True
        else:
            # we would like sending it on RX2 (less robust) but sending with 27dBm
            if not possible_rx2:
                if not possible_rx1:
                    self.downlink_packets_lost.append(packet)
                    lost = True
                else:
                    tx_on_rx1 = True
            else:
                tx_on_rx1 = False

        downlink_meta_msg.scheduled_receive_slot = DownlinkMetaMessage.RX_SLOT_1 if tx_on_rx1 else DownlinkMetaMessage.RX_SLOT_2

        if not lost:
            if tx_on_rx1:
                self.channel_time_used[packet.lora_param.freq] += time_on_air_rx1
            else:
                self.channel_time_used[LoRaParameters.RX_2_DEFAULT_FREQ] += time_on_air_rx2
                self.channel_time_used[LoRaParameters.RX_2_DEFAULT_FREQ] += time_on_air_rx2

        return downlink_msg

    def check_duty_cycle(self, payload_size, sf, freq, now):
        # TODO with new formula
        import LoRaPacket
        time_on_air = LoRaPacket.time_on_air(payload_size, lora_param=LoRaParameters(freq, sf, 125, 5, 1, 0, 1))
        if self.channel_time_used[freq] == 0:
            return True, time_on_air

        on_time = self.channel_time_used[freq]

        # off time per channel not total off time
        new_duty_cycle = ((on_time + time_on_air) / (now + time_on_air)) * 100  # on / total time =(on+off)
        return new_duty_cycle <= LoRaParameters.CHANNEL_DUTY_CYCLE_PROC[freq], time_on_air

    def adr(self, packet: UplinkMessage):
        history = self.packet_history[packet.node.id]
        if len(history) is 20:
            # Execute adr else do nothing
            max_snr = np.amax(np.asanyarray(history))

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

            snr_margin = max_snr - adr_required_snr - self.ADR_MARGIN_DB

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
            if Config.PRINT_ENABLED:
                print(str({'dr': new_dr, 'tp': new_tx_power}))

            return {'dr': new_dr, 'tp': new_tx_power}
        else:
            return None

    def log(self):
        print('\n\t\t GATEWAY')
        print('Received {} packets'.format(self.num_of_packet_received))
        print('Lost {} downlink packets'.format(len(self.downlink_packets_lost)))
        if len(self.downlink_packets_lost) != 0 and self.num_of_packet_received != 0:
            lost_ratio = len(self.downlink_packets_lost) / self.num_of_packet_received
            print('Ratio Lost/Received is {0:.2f}%'.format(lost_ratio * 100))

        for channel in self.channel_time_used:
            time_on_ratio = self.channel_time_used[channel] / self.env.now
            print('CH{0} spent on air {1:.2f}%'.format(channel, time_on_ratio * 100))

        if len(self.uplink_packet_weak) != 0 and self.num_of_packet_received != 0:
            weak_ratio = len(self.uplink_packet_weak) / self.num_of_packet_received
            print('Ratio Weak/Received is {0:.2f}%'.format(weak_ratio * 100))

        print('Bytes received at gateway {0:.2f}'.format(self.bytes_received))

    def get_der(self, nodes):
        packets_sent = 0
        for node in nodes:
            packets_sent += node.packets_sent

        return self.num_of_packet_received / packets_sent

    def get_simulation_data(self) -> pd.Series:
        return pd.Series({
            'BytesReceived': self.bytes_received,
            'DLPacketsLost': len(self.downlink_packets_lost),
            'ULWeakPackets': len(self.uplink_packet_weak),
            'PacketsReceived': self.num_of_packet_received
        })
