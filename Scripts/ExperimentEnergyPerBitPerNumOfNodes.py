import datetime

import matplotlib.pyplot as plt
import numpy as np
import simpy

import PropagationModel
from AirInterface import AirInterface
from EnergyProfile import EnergyProfile
from Gateway import Gateway
from Global import Config
from LoRaParameters import LoRaParameters
from Location import Location
from Node import Node
from SNRModel import SNRModel


def plot_time(_env):
    while True:
        print('.', end='', flush=True)
        yield _env.timeout(np.round(Config.SIMULATION_TIME / 10))


mean_energy_per_bit_list = []
mean_unique_packets_sent_list = []
mean_packets_sent_list = []
num_nodes_list = []
total_packets_sent = []
packets_received_by_gateway = []

for num_nodes in range(10, 1000, 100):
    print('{} nodes in network'.format(num_nodes))

    tx_power_mW = {2: 91.8, 5: 95.9, 8: 101.6, 11: 120.8, 14: 146.5}  # measured TX power for each possible TP
    middle = np.round(Config.CELL_SIZE / 2)
    gateway_location = Location(x=middle, y=middle, indoor=False)
    # plt.scatter(middle, middle, color='red')
    env = simpy.Environment()
    gateway = Gateway(env, gateway_location)
    nodes = []
    air_interface = AirInterface(gateway, PropagationModel.LogShadow(), SNRModel(), env)

    for node_id in range(num_nodes):
        location = Location(min=0, max=Config.CELL_SIZE, indoor=False)
        energy_profile = EnergyProfile(5.7e-3, 15, tx_power_mW,
                                       rx_power={'pre_mW': 8.2, 'pre_ms': 3.4, 'rx_lna_on_mW': 39, 'rx_lna_off_mW': 34,
                                                 'post_mW': 8.3, 'post_ms': 10.7})
        lora_param = LoRaParameters(freq=np.random.choice(LoRaParameters.DEFAULT_CHANNELS),
                                    sf=np.random.choice(LoRaParameters.SPREADING_FACTORS),
                                    bw=125, cr=5, crc_enabled=1, de_enabled=0, header_implicit_mode=0, tp=14)
        node = Node(node_id, energy_profile, lora_param, 1000000*2, process_time=5, adr=True, location=location,
                    base_station=gateway, env=env, payload_size=20*2, air_interface=air_interface)
        nodes.append(node)
        env.process(node.run())
        # plt.scatter(location.x, location.y, color='blue')

    # axes = plt.gca()
    # axes.set_xlim([0, Config.CELL_SIZE])
    # axes.set_ylim([0, Config.CELL_SIZE])
    # plt.show()
    env.process(plot_time(env))

    d = datetime.timedelta(milliseconds=Config.SIMULATION_TIME)
    print('Running simulator for {}.'.format(d))
    env.run(until=Config.SIMULATION_TIME)
    mean_energy_per_bit = 0
    mean_unique_packets_sent = 0
    mean_packets_sent = 0

    for node in nodes:
        # node.log()
        measurements = air_interface.get_prop_measurements(node.id)
        # node.plot(measurements)
        mean_energy_per_bit += node.energy_per_bit()
        mean_unique_packets_sent += node.num_unique_packets_sent
        mean_packets_sent += node.packets_sent

        # print('E/bit {}'.format(energy_per_bit))

    num_nodes_list.append(num_nodes)
    total_packets_sent.append(mean_packets_sent) # assign befor / num_nodes
    packets_received_by_gateway.append(gateway.num_of_packet_received)

    mean_energy_per_bit = mean_energy_per_bit / num_nodes
    mean_unique_packets_sent = mean_unique_packets_sent / num_nodes
    mean_packets_sent = mean_packets_sent / num_nodes

    mean_energy_per_bit_list.append(mean_energy_per_bit)
    mean_unique_packets_sent_list.append(mean_unique_packets_sent)
    mean_packets_sent_list.append(mean_packets_sent)



    print('E/bit {}'.format(mean_energy_per_bit))
    print('Unique packets {}'.format(mean_unique_packets_sent))
    print('Total packets {}'.format(mean_packets_sent))

ax = plt.subplot(4, 1, 1)
plt.plot(num_nodes_list, mean_energy_per_bit_list)
ax.set_title('Mean energy per bit')

ax = plt.subplot(4, 1, 2)
plt.plot(num_nodes_list, mean_unique_packets_sent_list)
ax.set_title('Mean unique packets sent')

ax = plt.subplot(4, 1, 3)
plt.plot(num_nodes_list, np.divide(np.subtract(mean_packets_sent_list, mean_unique_packets_sent_list),mean_unique_packets_sent_list))
ax.set_title('Mean extra packets ratio sent')


ax = plt.subplot(4, 1, 4)
plt.plot(num_nodes_list, np.divide(packets_received_by_gateway,total_packets_sent)) # total number of packets sent (ioncluding retransimissions)
ax.set_title('DER')

plt.show()
