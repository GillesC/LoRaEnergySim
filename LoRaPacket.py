import math
import numpy as np
import LoRaParameters


class LoRaPacket:
    def __init__(self, node, start_on_air, lora_param, payload_size, collided=False):
        self.freq = np.random.choice(LoRaParameters.DEFAULT_CHANNELS)
        self.node = node
        self.start_on_air = start_on_air
        self.lora_param = lora_param
        self.payload_size = payload_size
        self.collided = collided
        self.received = False

    # this function computes the airtime of a packet
    # for a packet with `payloadSize` in bytes
    # according to LoraDesignGuide_STD.pdf
    # return the airtime of a packet in ms
    def time_on_air(self):
        n_pream = 8  # https://www.google.com/patents/EP2763321A1?cl=en

        t_sym = (2.0 ** self.lora_param.sf) / self.lora_param.bw
        t_pream = (n_pream + 4.25) * t_sym
        payload_symb_n_b = 8 + max(
            math.ceil(
                (8.0 * self.payload_size - 4.0 * self.lora_param.sf + 28 + 16*self.lora_param.crc - 20 * self.lora_param.h) / (
                        4.0 * (self.lora_param.sf - 2 * self.lora_param.de)))
            * (self.lora_param.cr + 4), 0)
        t_payload = payload_symb_n_b * t_sym
        return t_pream + t_payload
