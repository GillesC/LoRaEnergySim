import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("white")

payload_sizes = range(15,55,5)
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
left_ax.set_xlabel("channel variance [$\sigma_{dB}$]")

channel_variance = dict()
channel_var = dict()
for var in range(0,22,2):
    channel_variance[var] = dict()
    channel_var[var] = []
    for p in payload_sizes:
        channel_variance[var][p] = 0
i = 0
for p in payload_sizes:
    nodes_df = pd.read_pickle('../Measurements/180309/simulation_results_node_{}'.format(p))
    for var, en in zip(nodes_df.index.values, nodes_df.mean_energy_per_byte):
        channel_variance[var][p] = en
for p in payload_sizes:
    for var in range(0,22,2):
        channel_var[var].append(channel_variance[var][p])

for var in [0,8,10,16,20]:
    plt.plot(payload_sizes, channel_var[var], marker='o', linestyle='--', lw=1, color=color[i],
             markersize=10, label=var)
    i += 1

left_ax.set_ylabel('Energy per Byte [mJ/B]')

plt.legend()
plt.show()
