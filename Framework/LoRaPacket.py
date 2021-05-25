import math
import numpy as np
from Framework.LoRaParameters import LoRaParameters


# this function computes the airtime for a specific set of parameters
# for a packet with `payloadSize` in bytes
# according to LoraDesignGuide_STD.pdf
# return the airtime of a packet in ms
def time_on_air(payload_size: int, lora_param: LoRaParameters):
    n_pream = 8  # https://www.google.com/patents/EP2763321A1?cl=en
    t_sym = (2.0 ** lora_param.sf) / lora_param.bw
    t_pream = (n_pream + 4.25) * t_sym
    payload_symb_n_b = 8 + max(
        math.ceil(
            (
                8.0 * payload_size - 4.0 * lora_param.sf + 28 + 16 * lora_param.crc - 20 * lora_param.h) / (
                4.0 * (lora_param.sf - 2 * lora_param.de)))
        * (lora_param.cr + 4), 0)
    t_payload = payload_symb_n_b * t_sym
    return t_pream + t_payload


class UplinkMessage:
    def __init__(self, node, start_on_air, payload_size,  id, collided=False,
                 confirmed_message=True, unique_msg = True):
        self. is_confirmed_message=confirmed_message
        self.node = node
        self.start_on_air = start_on_air
        self.lora_param = node.lora_param
        self.lora_param.freq = np.random.choice(LoRaParameters.DEFAULT_CHANNELS)
        self.payload_size = payload_size
        self.collided = collided
        self.received = False
        self.rss = None
        self.snr = None
        self.on_air = None
        self._time_on_air = None
        self.ack_retries_cnt = 0
        self.unique = unique_msg
        if self.is_confirmed_message:
            self.downlink_message = None
        self.id = id

    # this function computes the airtime of a packet
    # for a packet with `payloadSize` in bytes
    # according to LoraDesignGuide_STD.pdf
    # return the airtime of a packet in ms
    def my_time_on_air(self):

        if self._time_on_air is None:
            n_pream = 8  # https://www.google.com/patents/EP2763321A1?cl=en

            t_sym = (2.0 ** self.lora_param.sf) / self.lora_param.bw
            t_pream = (n_pream + 4.25) * t_sym
            payload_symb_n_b = 8 + max(
                math.ceil(
                    (
                            8.0 * self.payload_size - 4.0 * self.lora_param.sf + 28 + 16 * self.lora_param.crc - 20 * self.lora_param.h) / (
                            4.0 * (self.lora_param.sf - 2 * self.lora_param.de)))
                * (self.lora_param.cr + 4), 0)
            t_payload = payload_symb_n_b * t_sym
            self._time_on_air = t_pream + t_payload

        return self._time_on_air

    def set_random_freq(self):
        self.lora_param.freq = np.random.choice(LoRaParameters.DEFAULT_CHANNELS)

    @property
    def sf(self):
        # to be sure to return an int
        return int(self.lora_param.sf)

    @sf.setter
    def sf(self, sf):
        self.lora_param.sf = int(sf)


class DownlinkMetaMessage:
    RX_SLOT_1 = 1
    RX_SLOT_2 = 2

    def __init__(self, scheduled_receive_slot=None, dc_limit_reached=False, weak_packet=False):
        self.scheduled_receive_slot = scheduled_receive_slot
        self.dc_limit_reached = dc_limit_reached
        self.weak_packet = weak_packet

    def is_lost(self):
        return self.dc_limit_reached or self.weak_packet or self.scheduled_receive_slot is None


class DownlinkMessage:
    def __init__(self, payload=None, adr_param=None, dmm: DownlinkMetaMessage=None):
        self.payload = payload
        self.adr_param = adr_param
        self.meta = dmm
