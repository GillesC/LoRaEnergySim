import matplotlib.pyplot as plt

from GlobalConfig import GlobalConfig
from Location import Location
from Node import Node
from EnergyProfile import EnergyProfile
from LoRaParameters import LoRaParameters
from Gateway import Gateway
from SNRModel import SNRModel
import PropagationModel
import simpy

import numpy as np

if __name__ == "__main__":
    tx_power = {2: 91.8, 5: 95.9, 8: 101.6, 11: 120.8, 14: 146.5}  # measured TX power for each possible TP
    gateway_location = Location(x=50, y=50, indoor=True)
    plt.scatter(50, 50, color='red')
    env = simpy.Environment()
    gateway = Gateway(env, gateway_location, SNRModel(), PropagationModel.LogShadow())
    nodes = []
    for node_id in range(10):
        location = Location(min=0, max=100, indoor=True)
        #TODO check if random location is more than 1m from gateway
        # node = Node(node_id, EnergyProfile())
        energy_profile = EnergyProfile(5.7e-3, 15, tx_power)
        lora_param = LoRaParameters(freq=np.random.choice(LoRaParameters.DEFAULT_CHANNELS),
                                    sf=np.random.choice(LoRaParameters.SPREADING_FACTORS),
                                    bw=125, cr=5, crc_enabled=1, de_enabled=0, header_implicit_mode=0, tp=14)
        node = Node(node_id, energy_profile, lora_param, 60e3, 20, True, location, gateway, env, 20)
        nodes.append(node)
        env.process(node.run(env))
        plt.scatter(location.x, location.y, color='blue')

    axes = plt.gca()
    axes.set_xlim([0, 100])
    axes.set_ylim([0, 100])
    plt.show()
    env.run(until=1e9)

    for node in nodes:
        node.plot_energy()

    gateway.log()

