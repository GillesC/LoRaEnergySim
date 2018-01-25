import datetime

import matplotlib
import matplotlib.pyplot as plt

from AirInterface import AirInterface
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


def plot_time(_env):
    while True:
        print('.', end='', flush=True)
        yield _env.timeout(np.round(GlobalConfig.SIMULATION_TIME / 10))


tx_power = {2: 91.8, 5: 95.9, 8: 101.6, 11: 120.8, 14: 146.5}  # measured TX power for each possible TP
middle = np.round(GlobalConfig.CELL_SIZE / 2)
gateway_location = Location(x=middle, y=middle, indoor=True)
plt.scatter(middle, middle, color='red')
env = simpy.Environment()
gateway = Gateway(env, gateway_location, SNRModel(), PropagationModel.LogShadow())
nodes = []
air_interface = AirInterface(gateway)
for node_id in range(GlobalConfig.num_nodes):
    location = Location(min=0, max=GlobalConfig.CELL_SIZE, indoor=True)
    # TODO check if random location is more than 1m from gateway
    # node = Node(node_id, EnergyProfile())
    energy_profile = EnergyProfile(5.7e-3, 15, tx_power)
    lora_param = LoRaParameters(freq=np.random.choice(LoRaParameters.DEFAULT_CHANNELS),
                                sf=np.random.choice(LoRaParameters.SPREADING_FACTORS),
                                bw=125, cr=5, crc_enabled=1, de_enabled=0, header_implicit_mode=0, tp=14)
    node = Node(node_id, energy_profile, lora_param, 1000*60, 20, True, location, gateway, env, 255, air_interface)
    nodes.append(node)
    env.process(node.run(env))
    plt.scatter(location.x, location.y, color='blue')

axes = plt.gca()
axes.set_xlim([0, GlobalConfig.CELL_SIZE])
axes.set_ylim([0, GlobalConfig.CELL_SIZE])
plt.ion()
plt.show()
env.process(plot_time(env))

d = datetime.timedelta(milliseconds=GlobalConfig.SIMULATION_TIME)
print('Running simulator for {}.'.format(d))
env.run(until=GlobalConfig.SIMULATION_TIME)

# for node in nodes:
#    node.plot_energy()

gateway.log()
#air_interface.plot_packets_in_air()
