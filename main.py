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

energy_per_bit = 0
tx_power_mW = {2: 91.8, 5: 95.9, 8: 101.6, 11: 120.8, 14: 146.5}  # measured TX power for each possible TP
middle = np.round(Config.CELL_SIZE / 2)
gateway_location = Location(x=middle, y=middle, indoor=False)
plt.scatter(middle, middle, color='red')
env = simpy.Environment()
gateway = Gateway(env, gateway_location)
nodes = []
air_interface = AirInterface(gateway, PropagationModel.LogShadow(), SNRModel(), env)
for node_id in range(1000):
    location = Location(min=0, max=Config.CELL_SIZE, indoor=False)
    # location = Location(x=60, y=60, indoor=True)
    # TODO check if random location is more than 1m from gateway
    # node = Node(id, EnergyProfile())
    energy_profile = EnergyProfile(5.7e-3, 15, tx_power_mW,
                                   rx_power={'pre_mW': 8.2, 'pre_ms': 3.4, 'rx_lna_on_mW': 39, 'rx_lna_off_mW': 34,
                                             'post_mW': 8.3, 'post_ms': 10.7})
    lora_param = LoRaParameters(freq=np.random.choice(LoRaParameters.DEFAULT_CHANNELS),
                                sf=np.random.choice(LoRaParameters.SPREADING_FACTORS),
                                bw=125, cr=5, crc_enabled=1, de_enabled=0, header_implicit_mode=0, tp=14)
    # lora_param = LoRaParameters(freq=np.random.choice(LoRaParameters.DEFAULT_CHANNELS),
    #                             sf=12,
    #                             bw=125, cr=5, crc_enabled=1, de_enabled=0, header_implicit_mode=0, tp=14)
    node = Node(node_id, energy_profile, lora_param, 1000 * 60*60, process_time=5, adr=True, location=location,
                base_station=gateway, env=env, payload_size=16, air_interface=air_interface)
    nodes.append(node)
    env.process(node.run())
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
    #node.log()
    measurements = air_interface.get_prop_measurements(node.id)
    #node.plot(measurements)
    energy_per_bit += node.energy_per_bit()
    #print('E/bit {}'.format(energy_per_bit))

energy_per_bit = energy_per_bit/1000.0
print('E/bit {}'.format(energy_per_bit))
gateway.log()
air_interface.log()
# air_interface.plot_packets_in_air()
