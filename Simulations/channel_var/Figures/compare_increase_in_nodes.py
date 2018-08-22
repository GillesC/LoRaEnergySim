import pickle

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from collections import OrderedDict

sns.axes_style('white')

color = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
         (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
         (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
         (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
         (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]

# Scale the RGB values to the [0, 1] range, which is the format matplotlib accepts.
for i in range(len(color)):
    r, g, b = color[i]
    color[i] = (r / 255., g / 255., b / 255.)


num_nodes = [50,100,200,500]
files = {}

for n in num_nodes:
    files[n] = '../Results/True_True_1000_{}_SF_random.p'.format(n)


results = dict()
for n in num_nodes:
    results[n] = pickle.load(open(files[n], "rb"))


sigmas = results[num_nodes[0]]['path_loss_variances']
payload_sizes = results[num_nodes[0]]['payload_sizes']

f, ax = plt.subplots()

# Hide the right and top spines
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)

# Only show ticks on the left and bottom spines
ax.yaxis.set_ticks_position('left')
ax.xaxis.set_ticks_position('bottom')

plot_retransmitted_bytes = True
plot_energy = True
plot_collisions = True
plot_wait_time = True
plot_total_bytes = True
plot_unique_bytes = True
plot_der = True
plot_no_dl = True


def show(plot):
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys())
    plt.show()


if plot_retransmitted_bytes:
    for idx_p, p in enumerate(payload_sizes):
        for idx, s in enumerate(sigmas):
            p_str = str(p)
            s_str = str(s)
            for i, (start_sf, result) in enumerate(results.items()):
                node_data = result['nodes'][p_str][s_str]
                plt.scatter(p, (node_data['RetransmittedPackets'] / node_data['UniquePackets']) * 100, color=color[i],
                            label=start_sf)
    plt.title('Relative retransmitted (retr./unique) %')
    show(plt)

if plot_collisions:
    for idx_p, p in enumerate(payload_sizes):
        for idx, s in enumerate(sigmas):
            p_str = str(p)
            s_str = str(s)
            for i, (start_sf, result) in enumerate(results.items()):
                node_data = result['nodes'][p_str][s_str]
                plt.scatter(p, (node_data['CollidedPackets'] / node_data['UniquePackets']) * 100, color=color[i],
                            label=start_sf)
    plt.title('Rel. collisions (collided/unique) %')
    show(plt)
if plot_no_dl:
    for idx_p, p in enumerate(payload_sizes):
        for idx, s in enumerate(sigmas):
            p_str = str(p)
            s_str = str(s)
            for i, (start_sf, result) in enumerate(results.items()):
                node_data = result['nodes'][p_str][s_str]
                plt.scatter(p, (node_data['NoDLReceived'] / node_data['UniquePackets']) * 100, color=color[i],
                            label=start_sf)
    plt.title('Rel. no dl rec. (NoDLReceived/unique) %')
    show(plt)
if plot_energy:
    for idx_p, p in enumerate(payload_sizes):
        for idx, s in enumerate(sigmas):
            p_str = str(p)
            s_str = str(s)
            for i, (start_sf, result) in enumerate(results.items()):
                node_data = result['nodes'][p_str][s_str]
                eff_en = node_data['TxRxEnergy'] / (p * node_data['UniquePackets'])
                plt.scatter(p, eff_en, color=color[i], label=start_sf)
    plt.title('Eb (txrxen)')
    show(plt)
if plot_energy:
    for idx_p, p in enumerate(payload_sizes):
        for idx, s in enumerate(sigmas):
            p_str = str(p)
            s_str = str(s)
            for i, (start_sf, result) in enumerate(results.items()):
                node_data = result['nodes'][p_str][s_str]
                eff_en = node_data['TotalEnergy'] / (p * node_data['UniquePackets'])
                plt.scatter(p, eff_en, color=color[i], label=start_sf)
    plt.title('Eb (total)')
    show(plt)
if plot_total_bytes:
    for idx_p, p in enumerate(payload_sizes):
        for idx, s in enumerate(sigmas):
            p_str = str(p)
            s_str = str(s)
            for i, (start_sf, result) in enumerate(results.items()):
                node_data = result['nodes'][p_str][s_str]
                # plt.scatter(p, node_data['TotalBytes'], color=color[i], label=start_sf)
                plt.scatter(p, ((node_data['TotalBytes'] - (node_data['UniquePackets'] * p)) / (
                        node_data['UniquePackets'] * p)) * 100, color=color[i], label=start_sf)
    plt.title('Rel. redundant Bytes %')
    show(plt)
if plot_unique_bytes:
    for idx_p, p in enumerate(payload_sizes):
        for idx, s in enumerate(sigmas):
            p_str = str(p)
            s_str = str(s)
            for i, (start_sf, result) in enumerate(results.items()):
                node_data = result['nodes'][p_str][s_str]
                plt.scatter(p, node_data['UniquePackets'] * p, color=color[i], label=start_sf)
    plt.title('Unique Bytes')
    show(plt)

if plot_wait_time:
    for idx_p, p in enumerate(payload_sizes):
        for idx, s in enumerate(sigmas):
            p_str = str(p)
            s_str = str(s)
            for i, (start_sf, result) in enumerate(results.items()):
                node_data = result['nodes'][p_str][s_str]
                plt.scatter(p, node_data['WaitTimeDC'], color=color[i], label=start_sf)
    plt.title('Wait time')
    show(plt)
if plot_der:
    for idx_p, p in enumerate(payload_sizes):
        for idx, s in enumerate(sigmas):
            p_str = str(p)
            s_str = str(s)
            for i, (start_sf, result) in enumerate(results.items()):
                node_data = result['nodes'][p_str][s_str]
                gateway_data = result['gateway'][p_str][s_str]
                plt.scatter(p, ((gateway_data['UniquePacketsReceived'] * p) / node_data['TotalBytes']) * 100,
                            color=color[i], label=start_sf)
    plt.title('DER')
    show(plt)
