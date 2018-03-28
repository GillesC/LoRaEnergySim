import datetime

import numpy as np
import pandas as pd
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
import os
import pickle

# The console attempts to auto-detect the width of the display area, but when that fails it defaults to 80
# characters. This behavior can be overridden with:
desired_width = 320
pd.set_option('display.width', desired_width)

transmission_rate = 0.02e-3  # 12*8 bits per hour (1 typical packet per hour)
simulation_time = 30 * 24 * 60 * 60 * 1000
cell_size = 1000
adr = True
confirmed_messages = False


def plot_time(_env):
    while True:
        print('.', end='', flush=True)
        yield _env.timeout(np.round(simulation_time / 10))


tx_power_mW = {2: 91.8, 5: 95.9, 8: 101.6, 11: 120.8, 14: 146.5}  # measured TX power for each possible TP
middle = np.round(Config.CELL_SIZE / 2)
gateway_location = Location(x=middle, y=middle, indoor=False)

payload_sizes = range(5, 55, 5)

# load locations:
with open('locations.pkl', 'rb') as filehandler:
    locations_per_simulation = pickle.load(filehandler)

num_of_simulations = len(locations_per_simulation)
num_of_nodes = [len(locations_per_simulation[0])]  # now only for 1 num_of_nodes

simultation_results = dict()
gateway_results = dict()
air_interface_results = dict()

for num_nodes in num_of_nodes:
    simultation_results[num_nodes] = pd.DataFrame()
    gateway_results[num_nodes] = pd.DataFrame()
    air_interface_results[num_nodes] = pd.DataFrame()

mu_energy = dict()
sigma_energy = dict()
for num_nodes in num_of_nodes:
    mu_energy[num_nodes] = dict()
    sigma_energy[num_nodes] = dict()
    for payload_size in payload_sizes:
        mu_energy[num_nodes][payload_size] = 0
        sigma_energy[num_nodes][payload_size] = 0

for n_sim in range(num_of_simulations):

    print('Simulation #{}'.format(n_sim))
    locations = locations_per_simulation[n_sim]

    for num_nodes in num_of_nodes:

        for payload_size in payload_sizes:

            env = simpy.Environment()
            gateway = Gateway(env, gateway_location, fast_adr_on=True)
            nodes = []
            air_interface = AirInterface(gateway, PropagationModel.LogShadow(), SNRModel(), env)
            np.random.shuffle(locations)
            for node_id in range(num_nodes):
                energy_profile = EnergyProfile(5.7e-3, 15, tx_power_mW,
                                               rx_power={'pre_mW': 8.2, 'pre_ms': 3.4, 'rx_lna_on_mW': 39,
                                                         'rx_lna_off_mW': 34,
                                                         'post_mW': 8.3, 'post_ms': 10.7})
                lora_param = LoRaParameters(freq=np.random.choice(LoRaParameters.DEFAULT_CHANNELS),
                                            sf=np.random.choice(LoRaParameters.SPREADING_FACTORS),
                                            bw=125, cr=5, crc_enabled=1, de_enabled=0, header_implicit_mode=0, tp=14)
                node = Node(node_id, energy_profile, lora_param, sleep_time=(8 * payload_size / transmission_rate),
                            process_time=5,
                            adr=adr,
                            location=locations[node_id],
                            base_station=gateway, env=env, payload_size=payload_size, air_interface=air_interface,
                            confirmed_messages=confirmed_messages)
                nodes.append(node)
                env.process(node.run())

            # END adding nodes to simulation
            env.process(plot_time(env))

            d = datetime.timedelta(milliseconds=simulation_time)
            print('Running simulator for {}.'.format(d))
            env.run(until=simulation_time)
            print('Simulator is done for payload size {}'.format(payload_size))

            data_node = Node.get_mean_simulation_data_frame(nodes, name=payload_size) / (num_nodes * num_of_simulations)

            data_gateway = gateway.get_simulation_data(name=payload_size) / (num_nodes * num_of_simulations)
            data_air_interface = air_interface.get_simulation_data(name=payload_size) / (num_nodes * num_of_simulations)

            # print(data)
            if not payload_size in simultation_results[num_nodes].index:
                simultation_results[num_nodes] = simultation_results[num_nodes].append(data_node)
                gateway_results[num_nodes] = gateway_results[num_nodes].append(data_gateway)
                air_interface_results[num_nodes] = air_interface_results[num_nodes].append(data_air_interface)

            else:
                simultation_results[num_nodes].loc[[payload_size]] += data_node
                gateway_results[num_nodes].loc[[payload_size]] += data_gateway
                air_interface_results[num_nodes].loc[[payload_size]] += data_air_interface

            mu, sigma = Node.get_energy_per_byte_stats(nodes, gateway)
            print("mu: {}, sigma: {}".format(mu, sigma))
            mu_energy[num_nodes][payload_size] += mu / num_of_simulations
            sigma_energy[num_nodes][payload_size] += sigma / num_of_simulations

        # END loop payload_sizes

        # Printing experiment parameters
        print('{} nodes in network'.format(num_nodes))
        print('{} transmission rate'.format(transmission_rate))
        print('{} ADR'.format(adr))
        print('{} confirmed msgs'.format(confirmed_messages))
        print('{}m cell size'.format(cell_size))

        # END loop num_of_nodes

# END LOOP SIMULATION

directory = 'Scripts/Measurements/payload_size_energy_2_sim_100_nodes_long'
if not os.path.exists(directory):
    os.makedirs(directory)

for num_nodes in num_of_nodes:
    simultation_results[num_nodes]['mean_energy_per_byte'] = list(mu_energy[num_nodes].values())
    simultation_results[num_nodes]['sigma_energy_per_byte'] = list(sigma_energy[num_nodes].values())
    simultation_results[num_nodes]['UniqueBytes'] = simultation_results[num_nodes].UniquePackets * \
                                                    simultation_results[num_nodes].index.values
    simultation_results[num_nodes]['CollidedBytes'] = simultation_results[num_nodes].CollidedPackets * \
                                                      simultation_results[num_nodes].index.values

    simultation_results[num_nodes].to_pickle(directory + '/fast_adr_no_conf_simulation_results_node_{}'.format(num_nodes))
    print(simultation_results[num_nodes])
    gateway_results[num_nodes].to_pickle(directory + '/fast_adr_no_conf_gateway_results_{}'.format(num_nodes))
    print(gateway_results[num_nodes])
    air_interface_results[num_nodes].to_pickle(directory + '/fast_adr_no_conf_air_interface_results_{}'.format(num_nodes))
    print(air_interface_results[num_nodes])
