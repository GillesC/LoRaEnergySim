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

transmission_rate = 0.02e-3  # 12*8 bits per hour (1 typical packet per hour)
simulation_time = 1000 * 50 / transmission_rate
cell_size = 2000
adr = True
confirmed_messages = True


def plot_time(_env):
    while True:
        print('.', end='', flush=True)
        yield _env.timeout(np.round(simulation_time / 10))


tx_power_mW = {2: 91.8, 5: 95.9, 8: 101.6, 11: 120.8, 14: 146.5}  # measured TX power for each possible TP
middle = np.round(Config.CELL_SIZE / 2)
gateway_location = Location(x=middle, y=middle, indoor=False)

payload_sizes = range(10, 60, 10)
num_of_nodes = [100]  # [100, 500, 1000, 2000, 5000, 10000]
max_num_nodes = max(num_of_nodes)
num_of_simulations = 1

plt.style.use('seaborn-white')
# These are the "Tableau 20" colors as RGB.
tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
             (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
             (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
             (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
             (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]

# Scale the RGB values to the [0, 1] range, which is the format matplotlib accepts.
for i in range(len(tableau20)):
    r, g, b = tableau20[i]
    tableau20[i] = (r / 255., g / 255., b / 255.)

f, ax = plt.subplots(4, sharex=True)
# ax[1].spines["top"].set_visible(False)
# ax.spines["right"].set_visible(False)
ax[0].get_xaxis().tick_bottom()
ax[0].get_yaxis().tick_left()
plt.yticks(fontsize=14)
plt.xticks(payload_sizes, fontsize=14)
# Hide grid lines
ax[0].grid(False)
ax[1].grid(False)

##### INIT VARIABLES #####
mean_energy_per_bit_list = dict()
mean_num_trans_list = dict()
total_bytes_sent = dict()
unique_bytes_sent = dict()
mean_wait_time = dict()
collided_bytes = dict()
for num_nodes in num_of_nodes:
    mean_energy_per_bit_list[num_nodes] = dict()
    mean_num_trans_list[num_nodes] = dict()
    total_bytes_sent[num_nodes] = dict()
    unique_bytes_sent[num_nodes] = dict()
    mean_wait_time[num_nodes] = dict()
    collided_bytes[num_nodes] = dict()
    for payload_size in payload_sizes:
        mean_energy_per_bit_list[num_nodes][payload_size] = 0
        mean_num_trans_list[num_nodes][payload_size] = 0
        total_bytes_sent[num_nodes][payload_size] = 0
        unique_bytes_sent[num_nodes][payload_size] = 0
        mean_wait_time[num_nodes][payload_size] = 0
        collided_bytes[num_nodes][payload_size] = 0
##### INIT VARIABLES #####


##### SIMULTATION SCRIPT #####
for n_sim in range(num_of_simulations):
    locations = list()
    for i in range(max_num_nodes):
        locations.append(Location(min=0, max=cell_size, indoor=False))

    for num_nodes in num_of_nodes:

        for payload_size in payload_sizes:

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

            for node in nodes:
                mean_energy_per_bit_list[num_nodes][payload_size] += (
                        node.transmit_related_energy_per_unique_bit() / (num_nodes * num_of_simulations))
                mean_num_trans_list[num_nodes][payload_size] += (
                        (node.num_retransmission * payload_size) / (num_nodes * num_of_simulations))
                total_bytes_sent[num_nodes][payload_size] += (
                        node.bytes_sent / (num_nodes * num_of_simulations))
                unique_bytes_sent[num_nodes][payload_size] += (
                        node.num_unique_packets_sent * payload_size / (num_nodes * num_of_simulations))
                collided_bytes[num_nodes][payload_size] += (
                        node.num_collided * payload_size / (num_nodes * num_of_simulations))
                mean_wait_time[num_nodes][payload_size] += (
                        node.total_wait_time_because_dc / (num_nodes * num_of_simulations))
            # END processing simulation for fixed payload and fixed num of nodes

        # END loop payload_sizes

        # Printing experiment parameters
        print('{} nodes in network'.format(num_nodes))
        print('{} transmission rate'.format(transmission_rate))
        print('{} ADR'.format(adr))
        print('{} confirmed msgs'.format(confirmed_messages))
        print('{}m cell size'.format(cell_size))

# END loop num_of_nodes


# loop through num_of_nodes to plot energy
i = 0
for num_nodes in num_of_nodes:
    energy_per_bit = np.asarray(list(mean_energy_per_bit_list[num_nodes].values()))
    num_bytes_retransmitted = np.asarray(list(mean_num_trans_list[num_nodes].values()))
    num_bytes_sent_in_total = np.asarray(list(total_bytes_sent[num_nodes].values()))
    num_unique_bytes_sent = np.asarray(list(unique_bytes_sent[num_nodes].values()))
    num_collided_bytes = np.asarray(list(collided_bytes[num_nodes].values()))

    ax[0].plot(payload_sizes, energy_per_bit, lw=2.5, color=tableau20[i])

    ax[1].plot(payload_sizes, num_bytes_sent_in_total, lw=2.5, color=tableau20[i])

    bar_width = 0.4  # default: 0.8
    ax[2].bar(np.asarray(payload_sizes)-bar_width, num_bytes_retransmitted / num_bytes_sent_in_total, lw=2.5, color=tableau20[i],
               label='Ratio retrans', linestyle='--', width=bar_width)
    for xy in zip(payload_sizes, (num_bytes_retransmitted / num_bytes_sent_in_total) * 100):
        ax[2].annotate('(%s, %s)' % xy, xy=xy, textcoords='data')
    ax[2].bar(payload_sizes, num_unique_bytes_sent / num_bytes_sent_in_total, lw=2.5, color=tableau20[i],
               label='Ratio unique', linestyle=':', width=bar_width)
    ax[2].bar(np.asarray(payload_sizes)+bar_width, num_collided_bytes / num_bytes_sent_in_total, lw=2.5, color=tableau20[i],
               label='Ratio collided', width=bar_width)

    #
    # # for each payload size print energy for fixed num nodes in network
    #
    # y_pos = energy_list[-1]
    # ax[0].text(payload_sizes[-1] + 0.5, y_pos, num_nodes, fontsize=14, color=tableau20[i])
    # packets_sent_list = np.asarray([total_bytes_sent[num_nodes][payload_size] for payload_size in payload_sizes])
    # ax[2].plot(payload_sizes, packets_sent_list, lw=2.5, color=tableau20[i], linestyle='--')
    # # i += 1
    # retrans_list = np.divide(np.asarray(list(mean_num_trans_list[num_nodes].values())),total_bytes_sent)
    # ax[1].plot(payload_sizes, retrans_list, lw=2.5, color=tableau20[i], linestyle=':')
    # y_pos = retrans_list[-1]
    #
    mean_wait_time_list = np.asarray(list(mean_wait_time[num_nodes].values()))
    ax[3].plot(payload_sizes, mean_wait_time_list / 1000, lw=2.5, color=tableau20[i], linestyle=':')
    #
    # unique_bytes_list = np.asarray(list(unique_bytes_sent[num_nodes].values()))
    # ax[2].plot(payload_sizes, unique_bytes_list, lw=2.5, color=tableau20[i], linestyle=':')
    # # Again, make sure that all labels are large enough to be easily read
    # # by the viewer.
    # ax[1].text(payload_sizes[-1] + 0.5, y_pos, num_nodes, fontsize=14, color=tableau20[i])

    i += 1

# plt.title("Mean Energy per bit in mJ fo different payload sizes", fontsize=17, ha="center")
ax[0].set_ylabel("E/bit [mJ]", fontsize=16)
ax[1].set_ylabel("Total bytes sent [B]", fontsize=16)
# ax[2].set_ylabel("Total / Unique [B]", fontsize=16)
ax[2].set_ylim(0, 1)
ax[3].set_ylabel("Wait [s]", fontsize=16)
f.tight_layout()
plt.savefig("test.png", transparent=True, bbox_inches="tight")
ax[2].legend()
plt.show()
##### SIMULTATION SCRIPT #####
