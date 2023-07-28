import pickle

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

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

file = './True_True_0.1_cnst_num_bytes.p'

results = pickle.load(open(file, "rb"))
path_loss_variances = results['path_loss_variances']
sigmas = results['path_loss_variances']
payload_sizes = results['payload_sizes']

channel_variance = dict()
channel_var = dict()

i = 0

j = 0
colors = dict()
for var in path_loss_variances:
    colors[var] = color[j]
    j += 1

f, ax = plt.subplots()

# Hide the right and top spines
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)

# Only show ticks on the left and bottom spines
ax.yaxis.set_ticks_position('left')
ax.xaxis.set_ticks_position('bottom')

nodes = results['nodes']

plot_retransmitted_bytes = False
plot_energy = False
plot_collisions = False
plot_wait_time = False
plot_total_bytes = True
plot_unique_bytes = False

mean_val = dict()
std_val = dict()

for s in sigmas:
    mean_val[s] = np.empty(len(payload_sizes))
    std_val[s] = np.empty(len(payload_sizes))

for idx_p, p in enumerate(payload_sizes):
    for idx, s in enumerate(sigmas):
        p_str = str(p)
        s_str = str(s)
        node_data = results['nodes'][p_str][s_str]
        print(node_data)
        if plot_retransmitted_bytes:
            plt.scatter(p, node_data['RetransmittedPackets']*p, color=color[idx])
        if plot_energy:
            eff_en = node_data['TotalEnergy'] / (p * node_data['UniquePackets'])
            plt.scatter(p, eff_en, color=color[idx])
            # mean = Results['mean_energy'][p][s]
            # mean_val[s][idx_p] = mean
            # std = Results['std_energy'][p][s]
            # std_val[s][idx_p] = std
        if plot_collisions:
            #plt.scatter(p, Results['air_interface'][p_str][s_str]['NumberOfPacketsCollided'], color=color[idx]
            plt.scatter(p, node_data['CollidedPackets']*p, color=color[idx])
        if plot_wait_time:
            plt.scatter(p, node_data['WaitTimeDC'], color=color[idx])
        if plot_total_bytes:
            plt.scatter(p, node_data['TotalBytes'], color=color[idx])
        if plot_unique_bytes:
            plt.scatter(p, node_data['UniquePackets']*p, color=color[idx])

# if plot_energy:
#     for idx, s in enumerate(sigmas):
#         plt.scatter(payload_sizes, mean_val[s], color=color[idx])
#         plt.fill_between(payload_sizes, mean_val[s]-std_val[s], mean_val[s]+std_val[s], color=color[idx], alpha=0.2)

plt.xlabel("Payload size")
plt.show()