from collections import deque  # circular buffer for storing SNR history for the ADR algorithm

import numpy as np

import LoRaPacket
from LoRaParameters import LoRaParameters
import PropagationModel
from Location import Location


class Gateway:
    def __init__(self, env, location, snr_model, prop_model: PropagationModel.LogShadow):
        self.location = location
        self.packet_history = dict()
        self.channel_last_used = dict()
        for channel in LoRaParameters.CHANNELS:
            self.channel_last_used[channel] = 0
        self.num_of_packets_lost = []
        self.snr_model = snr_model
        self.prop_model = prop_model
        for freq in LoRaParameters.DEFAULT_CHANNELS:
            self.channel_last_used[freq] = 0
        self.num_of_packet_received = 0


    def packet_received(self, from_node, packet, now):
        self.num_of_packet_received += 1
        """
        The packet is received at the gateway.
        The packet is no longer in the air and has not collided.
        After receiving a packet the gateway sends the packet to the Network server and executes the ADR algorithm.
        For simplification, this algorithm is executed here.
        In addition, the gateway determines the best suitable DL Rx window.
        """
        if from_node.node_id not in self.packet_history:
            self.packet_history[from_node.node_id] = deque(maxlen=20)
        rss = self.prop_model.tp_to_rss(packet.lora_param.tp, Location.distance(self.location, from_node.location))
        snr = self.snr_model.rss_to_snr(rss)
        self.packet_history[from_node.node_id].append(snr)
        adr_settings = self.adr(from_node, packet)

        # first compute if DC can be done for RX1 and RX2
        possible_rx1 = self.check_duty_cycle(12, packet.lora_param.sf, packet.lora_param.freq, now)
        possible_rx2 = self.check_duty_cycle(12, LoRaParameters.RX_2_DEFAULT_SF, LoRaParameters.RX_2_DEFAULT_FREQ, now)

        tx_on_rx1 = False
        downlink_message = dict()

        if packet.lora_param.dr > 3:
            # we would like sending on the same channel with the same DR
            if not possible_rx1:
                if not possible_rx2:
                    self.num_of_packets_lost.append(packet)
                    downlink_message['lost'] = True
                else:
                    tx_on_rx1 = False
            else:
                tx_on_rx1 = True
        else:
            # we would like sending it on RX2 (less robust) but sending with 27dBm
            if not possible_rx2:
                if not possible_rx1:
                    self.num_of_packets_lost.append(packet)
                    downlink_message['lost'] = True
                else:
                    tx_on_rx1 = True
            else:
                tx_on_rx1 = False

        downlink_message['tx_on_rx1'] = tx_on_rx1
        if adr_settings is not None:
            downlink_message['dr'] = adr_settings['dr']
            downlink_message['tp'] = adr_settings['tp']
        return downlink_message

    def check_duty_cycle(self, payload_size, sf, freq, now):
        if self.channel_last_used[freq] is 0:
            return True

        time_on_air = LoRaPacket.time_on_air(payload_size, lora_param=LoRaParameters(freq, sf, 125, 5, 1, 0, 1))
        dc = time_on_air / (now - self.channel_last_used[freq])
        return dc <= LoRaParameters.CHANNEL_DUTY_CYCLE[freq]

    def adr(self, from_node, packet):
        history = self.packet_history[from_node.node_id]
        if len(history) is 20:
            # Execute adr else do nothing
            max_snr = np.amax(np.asanyarray(history))

            if from_node.lora_param.sf == 7:
                adr_required_snr = -7.5
            elif from_node.lora_param.sf == 8:
                adr_required_snr = -10
            elif from_node.lora_param.sf == 9:
                adr_required_snr = -12.5
            elif from_node.lora_param.sf == 10:
                adr_required_snr = -15
            elif from_node.lora_param.sf == 11:
                adr_required_snr = -17.5
            elif from_node.lora_param.sf == 12:
                adr_required_snr = -20

            snr_margin = max_snr - adr_required_snr - LoRaParameters.ADR_MARGIN_DB

            num_steps = np.round(snr_margin / 3)
            # If NStep > 0 the data rate can be increased and/or power reduced.
            # If Nstep < 0, power can be increased (to the max.).

            # Note: the data rate is never decreased,
            # this is done automatically by the node if ADRACKReq's get unacknowledged.

            current_tx_power = from_node.lora_param.tp
            dr_changing = 0
            change_tx_power = 0

            if num_steps > 0:
                # increase data rate by the num_steps until DR5 is reached
                num_steps_possible_dr = 5 - from_node.lora_param.dr
                decrease_tx_power = 0
                if num_steps > num_steps_possible_dr:
                    dr_changing = num_steps_possible_dr
                    num_steps_remaining = num_steps - num_steps_possible_dr
                    decrease_tx_power = num_steps_remaining * 3  # the remainder is used  to decrease the TXpower by
                    # 3dBm per step, until TXmin is reached. TXmin = 2 dBm for EU868.
                    decrease_tx_power = np.amax(current_tx_power - decrease_tx_power, 2)
                elif num_steps <= num_steps_possible_dr:
                    dr_changing = num_steps
                    # use default decrease tx power (0)
                change_tx_power = - decrease_tx_power
            elif num_steps < 0:
                # TX power is increased by 3dBm per step, until TXmax is reached (=14 dBm for EU868).
                num_steps = - num_steps  # invert so we do not need to work with negative numbers
                new_tx_power = np.amin([current_tx_power + num_steps * 3, 14])
                change_tx_power = new_tx_power - current_tx_power
            print(str({'dr': dr_changing, 'tp': change_tx_power}))
            if dr_changing != 0 or change_tx_power != 0:
                print(str({'dr': dr_changing, 'tp': change_tx_power}))

            return {'dr': dr_changing, 'tp': change_tx_power}
        else:
            return None

    def log(self):
        print('\t\t GATEWAY')
        print('Received {} packets'.format(self.num_of_packet_received))
        print('Lost {} packets'.format(self.num_of_packets_lost))

