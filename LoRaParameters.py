
class LoRaParameters:
    # Radio wakeup time from SLEEP mode
    RADIO_OSC_STARTUP = 1
    # Radio PLL lock and Mode Ready delay which can vary with the temperature
    RADIO_SLEEP_TO_RX = 2
    # Radio complete Wake-up Time with margin for temperature compensation
    RADIO_WAKEUP_TIME = (RADIO_OSC_STARTUP + RADIO_SLEEP_TO_RX)
    RECEIVE_DELAY1 = 1000
    RECEIVE_DELAY2 = 2000
    JOIN_ACCEPT_DELAY1 = 5000
    JOIN_ACCEPT_DELAY2 = 6000

    RX_WINDOW_1_DELAY = RECEIVE_DELAY1 - RADIO_WAKEUP_TIME
    RX_WINDOW_2_DELAY = JOIN_ACCEPT_DELAY2 - RADIO_WAKEUP_TIME

    RX_JOIN_WINDOW_1_DELAY = JOIN_ACCEPT_DELAY1 - RADIO_WAKEUP_TIME
    RX_JOIN_WINDOW_2_DELAY = JOIN_ACCEPT_DELAY2 - RADIO_WAKEUP_TIME

    RX_1_ACK_AIR_TIME = [170]  # TODO
    RX_2_ACK_AIR_TIME = 3 #

    RX_1_ACK_ENERGY_MJ = [6.4]  # TODO
    RX_2_ACK_ENERGY_MJ = 3  # TODO

    RX_1_NO_ACK_AIR_TIME = [170]  # TODO
    RX_2_NO_ACK_AIR_TIME = 2

    RX_1_NO_ACK_ENERGY_MJ = [6.4]  # TODO
    RX_2_NO_ACK_ENERGY_MJ = 0.0066  # TODO

    DEFAULT_CHANNELS = [868100000, 868300000, 868500000]

    JOIN_TX_TIME_MS = 160
    JOIN_TX_ENERGY_MJ = 9

    # Time and Energy consumption of RX1 after join request
    # when a DL message is received
    JOIN_RX_TIME_MS = 120
    JOIN_RX_ENERGY_MJ = 3

    # Time and Energy consumption of RX1 after join request
    # when no DL message is received
    JOIN_RX_1_WINDOW_OPEN_TIME_MS = 26
    JOIN_RX_1_WINDOW_OPEN_ENERGY_MJ = 0.8

    # CR: % 5..8 This is the error correction coding. Higher values mean more overhead.
    def __init__(self, freq, sf, bw, cr, crc_enabled, de_enabled, header_implicit_mode):
        self.freq = freq
        self.sf = sf
        self.bw = bw
        self.crc = crc_enabled
        self.cr = cr

        if bw == 125 and sf in [11, 12]:
            # low data rate optimization mandated for BW125 with SF11 and SF12
            self.de = 1
        else:
            self.de = de_enabled
        if sf == 6:
            # can only have implicit header with SF6
            self.h = 1
        else:
            self.h = header_implicit_mode

