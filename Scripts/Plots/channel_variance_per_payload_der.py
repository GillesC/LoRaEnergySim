import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# from matplotlib2tikz import save as tikz_save

sns.axes_style('white')

fig, left_ax = plt.subplots()

color = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
         (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
         (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
         (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
         (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]

# Scale the RGB values to the [0, 1] range, which is the format matplotlib accepts.
for i in range(len(color)):
    r, g, b = color[i]
    color[i] = (r / 255., g / 255., b / 255.)

channel_variance = dict()
channel_var = dict()
path_loss_variances = [0, 1, 2, 3, 4, 5, 10, 15, 20]
payload_sizes = range(5, 55, 5)
for var in path_loss_variances:
    channel_variance[var] = dict()
    channel_var[var] = []
    for p in payload_sizes:
        channel_variance[var][p] = 0
i = 0

dir = 'C:/Users/GillesCallebaut/Documents/GitHub/LoRaEnergySim/Simulations/Measurements/ChannelVariance/2sim/'

node_files = ['adr_confsimulation_results_node_', 'adr_no_confsimulation_results_node_',
              'no_adr_no_confsimulation_results_node_']
gateway_files = ['adr_confgateway_results_', 'adr_no_confgateway_results_',
                 'no_adr_no_confgateway_results_']

node_f = node_files[2]
gateway_f = gateway_files[2]

for p in payload_sizes:
    nodes_df = pd.read_pickle(dir + node_f + '{}'.format(p))
    gateway_df = pd.read_pickle(dir + gateway_f + '{}'.format(p))
    for var, tx, rx in zip(nodes_df.index.values, nodes_df.UniquePackets, gateway_df.UniquePacketsReceived):
        channel_variance[var][p] = (rx / tx) * 100

for p in payload_sizes:
    for var in path_loss_variances:
        channel_var[var].append(channel_variance[var][p])

print(channel_var)
for var in path_loss_variances:
    plt.plot(payload_sizes, channel_var[var], label=('\sigma_{dB}$: ' + str(var) + ' (dB)'))

left_ax.set_xlabel("Payload Size (B)")
left_ax.set_ylabel('DER')

# Hide the right and top spines
left_ax.spines['right'].set_visible(False)
left_ax.spines['top'].set_visible(False)

# Only show ticks on the left and bottom spines
left_ax.yaxis.set_ticks_position('left')
left_ax.xaxis.set_ticks_position('bottom')

plt.legend()
# plt.savefig('./Figures/payload_vs_energy.eps', format='eps', dpi=1000)
plt.show()
# tikz_save('channel_vs_energy.tex')
