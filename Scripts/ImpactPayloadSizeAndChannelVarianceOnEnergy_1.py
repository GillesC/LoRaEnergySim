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

# The console attempts to auto-detect the width of the display area, but when that fails it defaults to 80
# characters. This behavior can be overridden with:
desired_width = 1000
pd.set_option('display.width', desired_width)

transmission_rate = 0.02e-3  # 12*8 bits per hour (1 typical packet per hour)
simulation_time = 1000 * 50 / transmission_rate
cell_size = 1000
adr = True
confirmed_messages = True


def plot_time(_env):
    while True:
        print('.', end='', flush=True)
        yield _env.timeout(np.round(simulation_time / 10))


tx_power_mW = {2: 91.8, 5: 95.9, 8: 101.6, 11: 120.8, 14: 146.5}  # measured TX power for each possible TP
middle = np.round(Config.CELL_SIZE / 2)
gateway_location = Location(x=middle, y=middle, indoor=False)

payload_sizes = range(5, 65, 10)
num_nodes = 100
num_of_simulations = 2

simultation_results = dict()
gateway_results = dict()
air_interface_results = dict()
path_loss_variances = range(0, 25, 5)

for payload_size in payload_sizes:
    simultation_results[payload_size] = pd.DataFrame()
    gateway_results[payload_size] = pd.DataFrame()
    air_interface_results[payload_size] = pd.DataFrame()

mu_energy = dict()
sigma_energy = dict()
for payload_size in payload_sizes:
    mu_energy[payload_size] = dict()
    sigma_energy[payload_size] = dict()
    for path_loss_variance in path_loss_variances:
        mu_energy[payload_size][path_loss_variance] = 0
        sigma_energy[payload_size][path_loss_variance] = 0

for n_sim in range(num_of_simulations):

    locations = list()
    for i in range(num_nodes):
        locations.append(Location(min=0, max=cell_size, indoor=False))

    for payload_size in payload_sizes:

        for path_loss_variance in path_loss_variances:

            env = simpy.Environment()
            gateway = Gateway(env, gateway_location)
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

            data_node = Node.get_mean_simulation_data_frame(nodes, name=path_loss_variance) / (num_nodes * num_of_simulations)

            data_gateway = gateway.get_simulation_data(name=path_loss_variance) / (num_nodes * num_of_simulations)
            data_air_interface = air_interface.get_simulation_data(name=path_loss_variance) / (num_nodes * num_of_simulations)

            # print(data)
            if not path_loss_variance in simultation_results[payload_size].index:
                simultation_results[payload_size] = simultation_results[payload_size].append(data_node)
                gateway_results[payload_size] = gateway_results[payload_size].append(data_gateway)
                air_interface_results[payload_size] = air_interface_results[payload_size].append(data_air_interface)

            else:
                simultation_results[payload_size].loc[[path_loss_variance]] += data_node
                gateway_results[payload_size].loc[[path_loss_variance]] += data_gateway
                air_interface_results[payload_size].loc[[path_loss_variance]] += data_air_interface

            mu, sigma = Node.get_energy_per_byte_stats(nodes, gateway)
            print("mu: {}, sigma: {}".format(mu, sigma))
            mu_energy[payload_size][path_loss_variance] += mu / num_of_simulations
            sigma_energy[payload_size][path_loss_variance] += sigma / num_of_simulations

        # END loop path_loss_variances

        # Printing experiment parameters
        print('{} nodes in network'.format(payload_size))
        print('{} transmission rate'.format(transmission_rate))
        print('{} ADR'.format(adr))
        print('{} confirmed msgs'.format(confirmed_messages))
        print('{}m cell size'.format(cell_size))

        # END loop payload_sizes

# END LOOP SIMULATION

for payload_size in payload_sizes:
    simultation_results[payload_size]['mean_energy_per_byte'] = mu_energy[payload_size]
    simultation_results[payload_size]['sigma_energy_per_byte'] = sigma_energy[payload_size]
    simultation_results[payload_size]['UniqueBytes'] = simultation_results[payload_size].UniquePackets * \
                                                    simultation_results[payload_size].index.values
    simultation_results[payload_size]['CollidedBytes'] = simultation_results[payload_size].CollidedPackets * \
                                                      simultation_results[payload_size].index.values

    simultation_results[payload_size].to_pickle('simulation_results_node_{}'.format(payload_size))
    print(simultation_results[payload_size])
    gateway_results[payload_size].to_pickle('gateway_results_{}'.format(payload_size))
    print(gateway_results[payload_size])
    air_interface_results[payload_size].to_pickle('air_interface_results_{}'.format(payload_size))
    print(air_interface_results[payload_size])

