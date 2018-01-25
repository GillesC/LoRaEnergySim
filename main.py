import datetime

import matplotlib
import matplotlib.pyplot as plt

from AirInterface import AirInterface
from Global import Config
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
        yield _env.timeout(np.round(Config.SIMULATION_TIME / 10))


tx_power_mW = {2: 91.8, 5: 95.9, 8: 101.6, 11: 120.8, 14: 146.5}  # measured TX power for each possible TP
middle = np.round(Config.CELL_SIZE / 2)
gateway_location = Location(x=middle, y=middle, indoor=True)
plt.scatter(middle, middle, color='red')
env = simpy.Environment()
gateway = Gateway(env, gateway_location, SNRModel(), PropagationModel.LogShadow())
nodes = []
air_interface = AirInterface(gateway)
for node_id in range(Config.num_nodes):
    location = Location(min=0, max=Config.CELL_SIZE, indoor=True)
    # TODO check if random location is more than 1m from gateway
    # node = Node(node_id, EnergyProfile())
    energy_profile = EnergyProfile(5.7e-3, 15, tx_power_mW)
    lora_param = LoRaParameters(freq=np.random.choice(LoRaParameters.DEFAULT_CHANNELS),
                                sf=np.random.choice(LoRaParameters.SPREADING_FACTORS),
                                bw=125, cr=5, crc_enabled=1, de_enabled=0, header_implicit_mode=0, tp=14)
    node = Node(node_id, energy_profile, lora_param, 1000*60*60, 20, True, location, gateway, env, 25, air_interface)
    nodes.append(node)
    env.process(node.run(env))
    plt.scatter(location.x, location.y, color='blue')

axes = plt.gca()
axes.set_xlim([0, Config.CELL_SIZE])
axes.set_ylim([0, Config.CELL_SIZE])
plt.show()
env.process(plot_time(env))

d = datetime.timedelta(milliseconds=Config.SIMULATION_TIME)
print('Running simulator for {}.'.format(d))
env.run(until=Config.SIMULATION_TIME)

for node in nodes:
    node.log()
    #node.plot_energy()

gateway.log()
air_interface.log()
#air_interface.plot_packets_in_air()
