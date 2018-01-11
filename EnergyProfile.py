from Node import NodeState


class EnergyProfile:
    def __init__(self, sleep_power, proc_power, tx_power, rx_power):
        self.sleep_power = sleep_power
        self.proc_power = proc_power
        self.tx_power = tx_power
        self.rx_power = rx_power

    @staticmethod
    def energy_consumption(state: NodeState, lora_packet=None):
        elif state == NodeState.JOIN_TX:

        elif state == NodeState.JOIN_RX:

        elif state == NodeState.TX:

        elif state == NodeState.RX:

