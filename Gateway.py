from collections import deque  # circular buffer for storing SNR history for the ADR algorithm
import numpy as np

import LoRaPacket
from LoRaParameters import LoRaParameters
from SNRModel import SNRModel


class BaseStation:

    def __init__(self, env, location):
        self.location = location
        self.packet_history = dict()
        self.channel_use = dict()
        for freq in LoRaParameters.DEFAULT_CHANNELS:
            self.channel_use[freq] = 0

    def packet_received(self, from_node, packet, now):
        """
        The packet is received at the gateway.
        The packet is no longer in the air and has not collided.
        After receiving a packet the gateway sends the packet to the Network server and executes the ADR algorithm.
        For simplification, this algorithm is executed here.
        In addition, the gateway determines the best suitable DL Rx window.
        """
        if from_node.node_id not in self.packet_history:
            self.packet_history[from_node.node_id] = deque(maxlen=20)

        self.packet_history[from_node.node_id].append(SNRModel.rssi_to_snr(packet.rssi))
        adr_settings = self.adr(from_node, packet)
        if packet.lora_param.dr > 3:
            # we would like sending on the same channel with the same DR
            check_duty_cycle(12, packet.lora_param.sf, packet.lora_param.freq)

    def check_duty_cycle(self, payload_size, sf, freq):
        time_on_air = LoRaPacket.time_on_air(payload_size, lora_param=LoRaParameters(freq, sf, 125, 5, 1, 0, 1))

    def adr(self, from_node, packet):
        global change_tx_power, dr_changing, decrease_tx_power
        history = self.packet_history[from_node.node_id]
        if len(history) is 20:
            # Execute adr else do nothing
            max_snr = np.amax(np.asanyarray(history))

            if from_node.lora_param.sf is 7:
                adr_required_snr = -7.5
            elif from_node.lora_param.sf is 8:
                adr_required_snr = -10
            elif from_node.lora_param.sf is 9:
                adr_required_snr = -12.5
            elif from_node.lora_param.sf is 10:
                adr_required_snr = -15
            elif from_node.lora_param.sf is 11:
                adr_required_snr = -17.5
            elif from_node.lora_param.sf is 12:
                adr_required_snr = -20

            snr_margin = max_snr - adr_required_snr - LoRaParameters.ADR_MARGIN_DB

            num_steps = np.round(snr_margin / 3)
            # If NStep > 0 the data rate can be increased and/or power reduced.
            # If Nstep < 0, power can be increased (to the max.).

            # Note: the data rate is never decreased,
            # this is done automatically by the node if ADRACKReq's get unacknowledged.

            current_tx_power = from_node.energy_profile.tx_power
            if num_steps > 0:
                # increase data rate by the num_steps until DR5 is reached
                num_steps_possible_dr = 5 - from_node.lora_param.dr

                if num_steps > num_steps_possible_dr:
                    dr_changing = num_steps_possible_dr
                    num_steps_remaining = num_steps - num_steps_possible_dr
                    decrease_tx_power = num_steps_remaining * 3  # the remainder is used  to decrease the TXpower by
                    # 3dBm per step, until TXmin is reached. TXmin = 2 dBm for EU868.

                    if current_tx_power - decrease_tx_power < 2:
                        decrease_tx_power = current_tx_power - 2
                elif num_steps <= num_steps_possible_dr:
                    dr_changing = num_steps
                    decrease_tx_power = 0
                change_tx_power = - decrease_tx_power
            elif num_steps < 0:
                # TX power is increased by 3dBm per step, until TXmax is reached (=14 dBm for EU868).
                num_steps = - num_steps  # invert so we do not need to work with negative numbers
                new_tx_power = np.amin(current_tx_power + num_steps * 3, 14)
                change_tx_power = new_tx_power - current_tx_power

            return {'dr': dr_changing, 'tp': change_tx_power}
        else:
            return None
