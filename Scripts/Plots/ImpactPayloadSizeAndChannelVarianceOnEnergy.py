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


transmission_rate = 1e-6  # number of bytes sent per ms
num_nodes = 100
cell_size = 1000
adr = True
confirmed_messages = True

tx_power_mW = {2: 91.8, 5: 95.9, 8: 101.6, 11: 120.8, 14: 146.5}  # measured TX power for each possible TP
middle = np.round(Config.CELL_SIZE / 2)
gateway_location = Location(x=middle, y=middle, indoor=False)
# plt.scatter(middle, middle, color='red')

simulation_num_of_times = 100
mean_energy_per_bit_list = dict()
mean_der = dict()
num_collided_per_node = dict()
num_no_down_per_node = dict()
num_retrans_per_node = dict()
payload_sizes = range(10, 50)
for payload_size in payload_sizes:

    path_loss_variances = range(0, 20, 2)
    for path_loss_variance in path_loss_variances:

        mean_energy_per_bit_list[path_loss_variance] = 0
        mean_der[path_loss_variance] = 0
        num_collided_per_node[path_loss_variance] = 0
        num_no_down_per_node[path_loss_variance] = 0
        num_retrans_per_node[path_loss_variance] = 0

        print('Path loss variance {}'.format(path_loss_variance))

        for num_of_times in range(simulation_num_of_times):
            env = simpy.Environment()
            gateway = Gateway(env, gateway_location)
            nodes = []
            air_interface = AirInterface(gateway, PropagationModel.LogShadow(std=path_loss_variance), SNRModel(), env)

            for node_id in range(num_nodes):
                location = Location(min=0, max=cell_size, indoor=False)
                energy_profile = EnergyProfile(5.7e-3, 15, tx_power_mW,
                                               rx_power={'pre_mW': 8.2, 'pre_ms': 3.4, 'rx_lna_on_mW': 39,
                                                         'rx_lna_off_mW': 34,
                                                         'post_mW': 8.3, 'post_ms': 10.7})
                lora_param = LoRaParameters(freq=np.random.choice(LoRaParameters.DEFAULT_CHANNELS),
                                            sf=np.random.choice(LoRaParameters.SPREADING_FACTORS),
                                            bw=125, cr=5, crc_enabled=1, de_enabled=0, header_implicit_mode=0, tp=14)
                node = Node(node_id, energy_profile, lora_param, payload_size / transmission_rate, process_time=5,
                            adr=adr,
                            location=location,
                            base_station=gateway, env=env, payload_size=payload_size, air_interface=air_interface,
                            confirmed_messages=confirmed_messages)
                nodes.append(node)
                env.process(node.run())

            env.process(plot_time(env))

            d = datetime.timedelta(milliseconds=Config.SIMULATION_TIME)
            print('Running simulator for {}.'.format(d))
            env.run(until=Config.SIMULATION_TIME)
            print('Simulator is done for payload size {}'.format(payload_size))
            mean_energy_per_bit = 0
            num_collided = 0
            num_retrans = 0

            num_no_down = 0
            for node in nodes:
                mean_energy_per_bit += node.transmit_related_energy_per_bit()
                num_collided += node.num_collided
                num_retrans += node.num_retransmission
                num_no_down += node.num_no_downlink

            num_collided_per_node[path_loss_variance] = num_collided / num_nodes
            num_no_down_per_node[path_loss_variance] = num_no_down / num_nodes
            num_retrans_per_node[path_loss_variance] = num_retrans / num_nodes

            mean_energy_per_bit_list[path_loss_variance] += mean_energy_per_bit / num_nodes
            mean_energy_per_bit_list[path_loss_variance] += mean_energy_per_bit / num_nodes

            der = gateway.get_der(nodes)
            mean_der[path_loss_variance] += der

        mean_energy_per_bit_list[path_loss_variance] = mean_energy_per_bit_list[
                                                           path_loss_variance] / simulation_num_of_times
        mean_der[path_loss_variance] = mean_der[path_loss_variance] / simulation_num_of_times
        num_collided_per_node[path_loss_variance] = num_collided_per_node[path_loss_variance] / simulation_num_of_times
        num_no_down_per_node[path_loss_variance] = num_no_down_per_node[path_loss_variance] / simulation_num_of_times
        num_retrans_per_node[path_loss_variance] = num_retrans_per_node[path_loss_variance] / simulation_num_of_times

    # Printing experiment parameters
    print('{} nodes in network'.format(num_nodes))
    print('{} transmission rate'.format(transmission_rate))
    print('{} ADR'.format(adr))
    print('{} confirmed msgs'.format(confirmed_messages))
    print('{}m cell size'.format(cell_size))
    print('{}B payload size'.format(payload_size))

    plt.figure(1)
    plt.subplot(6, 1, 1)
    plt.plot(path_loss_variances, list(mean_energy_per_bit_list.values()), label=payload_size)
    plt.subplot(6, 1, 2)
    plt.plot(path_loss_variances, list(mean_der.values()), label=payload_size)
    plt.subplot(6, 1, 4)
    plt.plot(path_loss_variances, list(num_no_down_per_node.values()), label=payload_size)
    plt.subplot(6, 1, 5)
    plt.plot(path_loss_variances, list(num_collided_per_node.values()), label=payload_size)
    plt.subplot(6, 1, 6)
    plt.plot(path_loss_variances, list(num_retrans_per_node.values()), label=payload_size)


plt.savefig('example.pdf')
plt.savefig('example.pgf')
plt.legend()
plt.show()
