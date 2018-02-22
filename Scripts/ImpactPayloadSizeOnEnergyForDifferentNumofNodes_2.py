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
cell_size = 1000
adr = True
confirmed_messages = True

tx_power_mW = {2: 91.8, 5: 95.9, 8: 101.6, 11: 120.8, 14: 146.5}  # measured TX power for each possible TP
middle = np.round(Config.CELL_SIZE / 2)
gateway_location = Location(x=middle, y=middle, indoor=False)
# plt.scatter(middle, middle, color='red')


mean_energy_per_bit_list = dict()

payload_sizes = range(10, 60, 10)
num_of_nodes = range(100, 1100, 250)
max_num_nodes = max(num_of_nodes)
locations = list()

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

# You typically want your plot to be ~1.33x wider than tall. This plot is a rare
# exception because of the number of lines being plotted on it.
# Common sizes: (10, 7.5) and (12, 9)
plt.figure(figsize=(12, 14))

# Remove the plot frame lines. They are unnecessary chartjunk.
ax = plt.subplot(111)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Ensure that the axis ticks only show up on the bottom and left of the plot.
# Ticks on the right and top of the plot are generally unnecessary chartjunk.
ax.get_xaxis().tick_bottom()
ax.get_yaxis().tick_left()

# Make sure your axis ticks are large enough to be easily read.
# You don't want your viewers squinting to read your plot.
plt.yticks(fontsize=14)
plt.xticks(payload_sizes, fontsize=14)
# Hide grid lines
ax.grid(False)

# TODO num_simulation outside other loops

for i in range(max_num_nodes):
    locations.append(Location(min=0, max=cell_size, indoor=False))

i = 0
for num_nodes in num_of_nodes:

    mean_energy_per_bit_list = []

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
            node = Node(node_id, energy_profile, lora_param, payload_size / transmission_rate, process_time=5,
                        adr=adr,
                        location=locations[node_id],
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
        num_retrans = 0


        for node in nodes:
            mean_energy_per_bit += node.energy_per_bit()
            num_retrans += node.num_retransmission

        print('{} total energy consumed'.format(mean_energy_per_bit))
        print('{} total energy consumed'.format(mean_energy_per_bit/ len(nodes)))
        mean_energy_per_bit_list.append(mean_energy_per_bit / len(nodes))
        mean_energy_per_bit_list.append(num_retrans / len(nodes))


    # Printing experiment parameters
    print('{} nodes in network'.format(num_nodes))
    print('{} transmission rate'.format(transmission_rate))
    print('{} ADR'.format(adr))
    print('{} confirmed msgs'.format(confirmed_messages))
    print('{}m cell size'.format(cell_size))

    plt.plot(payload_sizes, mean_energy_per_bit_list, lw=2.5, color=tableau20[i])
    y_pos = mean_energy_per_bit_list[-1]

    # Again, make sure that all labels are large enough to be easily read
    # by the viewer.
    plt.text(payload_sizes[-1] + 0.5, y_pos, num_nodes, fontsize=14, color=tableau20[i])

    i += 1

# matplotlib's title() call centers the title on the plot, but not the graph,
# so I used the text() call to customize where the title goes.

# Make the title big enough so it spans the entire plot, but don't make it
# so big that it requires two lines to show.

# Note that if the title is descriptive enough, it is unnecessary to include
# axis labels; they are self-evident, in this plot's case.
plt.title("Mean Energy per bit in mJ fo different payload sizes", fontsize=17, ha="center")
# Along the same vein, make sure your axis labels are large
# enough to be easily read as well. Make them slightly larger
# than your axis tick labels so they stand out.
plt.ylabel("E/bit [mJ]", fontsize=16)
plt.xlabel("Payload size [Bytes]", fontsize=16)
# Finally, save the figure as a PNG.
# You can also save it as a PDF, JPEG, etc.
# Just change the file extension in this call.
# bbox_inches="tight" removes all the extra whitespace on the edges of your plot.
plt.savefig("test.png", transparent=True, bbox_inches="tight")
plt.show()
