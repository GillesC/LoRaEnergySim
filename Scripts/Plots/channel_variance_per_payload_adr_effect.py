import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# from matplotlib2tikz import save as tikz_save

sns.axes_style('white')

dir = '../Simulations/Measurements/ChannelVariance/impact_adr_20sim/'

node_files = ['adr_confsimulation_results_node_', 'adr_no_confsimulation_results_node_',
              'no_adr_no_confsimulation_results_node_']
air_interface_files = ['no_adr_no_conf_avg_snr_air_interface_results_', 'no_adr_no_conf_min_snr_air_interface_results_',
                       'no_adr_no_conf_max_snr_air_interface_results_']
gateway_files = ['adr_confgateway_results_', 'adr_no_confgateway_results_',
                 'no_adr_no_confgateway_results_']

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

payload_sizes = range(5, 55, 5)
path_loss_variances = pd.read_pickle(dir + air_interface_files[0] + '{}'.format(payload_sizes[0])).index.values

for var in path_loss_variances:
    channel_variance[var] = dict()
    channel_var[var] = []
    for p in payload_sizes:
        channel_variance[var][p] = 0
i = 0

j = 0
colors = dict()
for var in path_loss_variances:
    colors[var] = color[j]
    j += 1

ax_id = range(0, 3)
# Two subplots, the axes array is 1-d
f, axarr = plt.subplots(3, sharex=True, sharey=True)

for ax_id, air_f, gateway_f, node_f in zip(ax_id, air_interface_files, gateway_files, node_files):
    ax = axarr[ax_id]
    ax.set_title(air_f)

    # clean variables
    for var in path_loss_variances:
        channel_variance[var] = dict()
        channel_var[var] = []
        for p in payload_sizes:
            channel_variance[var][p] = 0

    for p in payload_sizes:
        air_df = pd.read_pickle(dir + air_f + '{}'.format(p))
        gateway_df = pd.read_pickle(dir + gateway_f + '{}'.format(p))
        node_df = pd.read_pickle(dir + node_f + '{}'.format(p))
        for var, collided, weak, lost, sent in zip(air_df.index.values, air_df.NumberOfPacketsCollided,
                                                   gateway_df.ULWeakPackets, node_df.NoDLReceived, node_df.TotalBytes):
            channel_variance[var][p] = (((collided) * p) / sent)*100

    for p in payload_sizes:
        for var in path_loss_variances:
            channel_var[var].append(channel_variance[var][p])

    for var in path_loss_variances:
        ax.plot(payload_sizes, channel_var[var], label=('\sigma_{dB}$: ' + str(var) + ' (dB)'), color=colors[var])

    # Hide the right and top spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Only show ticks on the left and bottom spines
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')

f.legend()
plt.xlabel("Channel Variance")
plt.ylabel("Collisions")
plt.show()
