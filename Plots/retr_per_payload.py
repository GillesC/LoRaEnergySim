import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("white")

# Latex specific settings
plt.rc('text', usetex=True)
plt.rc('font', family='serif')

dir = 'C:/Users/Calle/Documents/GitHub/LoRaEnergySim/Scripts/Simulations/Scripts/Measurements/payload_size_energy_2_sim_100_nodes_long/'
# gateway_adr_conf_df = pd.read_pickle(
#     dir+'adr_conf_gateway_results_100')
# nodes_adr_conf_df = pd.read_pickle(
#     dir+'adr_conf_simulation_results_node_100')

gateway_adr_no_conf_df = pd.read_pickle(
    dir+'adr_no_conf_gateway_results_100')
nodes_adr_no_conf_df = pd.read_pickle(
    dir+'adr_no_conf_simulation_results_node_100')
gateway_no_adr_no_conf_df = pd.read_pickle(
    dir+'no_adr_no_conf_gateway_results_100')
nodes_no_adr_no_conf_df = pd.read_pickle(
    dir+'no_adr_no_conf_simulation_results_node_100')

payload_sizes = nodes_no_adr_no_conf_df.index.values

plt.xlabel('Payload size (B)', fontsize=16)
plt.ylabel('Number of retransmissions', fontsize=16)

# nodes_df = nodes_adr_conf_df
# plt.plot(payload_sizes, nodes_df.RetransmittedPackets/nodes_df.TotalPackets, label='ADR CONF ')
# plt.plot(payload_sizes, nodes_df.CollidedPackets/nodes_df.TotalPackets, label='ADR CONF Col')

nodes_df = nodes_adr_no_conf_df
plt.plot(payload_sizes, nodes_df.RetransmittedPackets/nodes_df.TotalPackets, label='ADR NO CONF ')
plt.plot(payload_sizes, nodes_df.CollidedPackets/nodes_df.TotalPackets, label='ADR NO Col')

nodes_df = nodes_no_adr_no_conf_df
plt.plot(payload_sizes, nodes_df.RetransmittedPackets/nodes_df.TotalPackets, label='NO ADR NO CONF ')
plt.plot(payload_sizes, nodes_df.CollidedPackets/nodes_df.TotalPackets, label='NO ADR NO Col')

plt.grid(True)
plt.legend()
plt.tight_layout()
#plt.savefig('./Figures/payload_vs_energy.eps', format='eps', dpi=1000)
plt.show()
