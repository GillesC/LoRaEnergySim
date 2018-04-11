import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("white")

gateway_df = pd.read_pickle('../Measurements/fast_adr_on/gateway_results_100')
payload_sizes = gateway_df.index.values
bytes_lost = gateway_df.DLPacketsLost * payload_sizes

nodes_df = pd.read_pickle('../Measurements/fast_adr_on/simulation_results_node_100')
print(nodes_df)
print(gateway_df)
energy_per_byte = nodes_df.TxRxEnergy / (gateway_df.UniquePacketsReceived * payload_sizes)
print(energy_per_byte)
retransmitted_bytes = nodes_df.RetransmittedPackets * payload_sizes
wait_time = nodes_df.WaitTimeDC
der = gateway_df.UniquePacketsReceived / nodes_df.UniquePackets

fig, left_ax = plt.subplots()
right_ax = left_ax.twinx()

color = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
             (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
             (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
             (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
             (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]
# Scale the RGB values to the [0, 1] range, which is the format matplotlib accepts.
for i in range(len(color)):
    r, g, b = color[i]
    color[i] = (r / 255., g / 255., b / 255.)

left_ax.set_xlabel('payload size [B]')

left_ax.errorbar(x=payload_sizes, y=energy_per_byte, yerr=nodes_df.sigma_energy_per_byte, marker='o', linestyle='--', lw=1, color=color[0], markersize=10)
left_ax.set_ylabel('Energy per Byte [mJ/B]')

right_ax.plot(payload_sizes, bytes_lost / max(bytes_lost), marker='o', linestyle='--', lw=1, color=color[1],
              markersize=10, label='Lost DC limit')
retr_ratio = retransmitted_bytes / max(retransmitted_bytes)
right_ax.plot(payload_sizes,retr_ratio, marker='o', linestyle='--', lw=1,
              color=color[2], markersize=10, label='Retrans.')
rat = (nodes_df.RetransmittedPackets/gateway_df.UniquePacketsReceived)*100
print(rat)
for x, y, z in zip(payload_sizes, rat, retr_ratio):
    right_ax.annotate("{0:.2f}%".format(y), xy=(x, z-0.05), textcoords='data')

right_ax.plot(payload_sizes, wait_time / max(wait_time), marker='o', linestyle='--', lw=1, color=color[3],
              markersize=10, label='Wait time')
coll = nodes_df.CollidedBytes / max(nodes_df.CollidedBytes)
right_ax.plot(payload_sizes, coll, marker='o', linestyle='--', lw=1, color=color[5],
              markersize=10, label='Collided bytes norm')
for x, y in zip(payload_sizes, coll*100):
    right_ax.annotate("{0:.2f}%".format(y), xy=(x, (y/100)-0.02), textcoords='data')

right_ax.plot(payload_sizes, der, marker='o', linestyle='--', lw=1, color=color[4], markersize=10, label='DER')
for x, y in zip(payload_sizes, der*100):
    right_ax.annotate("{0:.2f}%".format(y), xy=(x, (y/100)-0.02), textcoords='data')

right_ax.set_ylabel('Normalized Bytes / max () [-]')

print((nodes_df.RetransmittedPackets / nodes_df.UniquePackets) * 100)
print('unique rx / unique tx')
print((gateway_df.UniquePacketsReceived/ nodes_df.UniquePackets) * 100)

right_ax.legend()
plt.show()
