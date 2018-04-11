import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


sns.set(style='ticks', palette='Set2')
sns.despine()


dir = 'C:/Users/Calle/Documents/GitHub/LoRaEnergySim/Scripts/Simulations/Scripts/Measurements/payload_size_energy_2_sim_100_nodes_long/'

nodes_adr_conf_df = pd.read_pickle(dir+'adr_conf_simulation_results_node_100')

nodes_adr_no_conf_df = pd.read_pickle(
    dir+'adr_no_conf_simulation_results_node_100')
nodes_no_adr_no_conf_df = pd.read_pickle(
    dir+'no_adr_no_conf_simulation_results_node_100')

payload_sizes = nodes_adr_no_conf_df.index.values
plt.xlabel('Payload size (B)', fontsize=16)
plt.ylabel('Energy per payload byte $E_B$ (mJ)', fontsize=16)

nodes = nodes_adr_conf_df
plt.plot(payload_sizes, nodes.mean_energy_per_byte, marker='+', markersize=12, ls='--', label='ADR CONF')

nodes = nodes_adr_no_conf_df
plt.plot(payload_sizes, nodes.mean_energy_per_byte, marker='1', markersize=12, ls='-.', label='ADR NO CONF ')
plt.fill_between(payload_sizes, nodes.mean_energy_per_byte-nodes.sigma_energy_per_byte, nodes.mean_energy_per_byte+nodes.sigma_energy_per_byte, alpha=0.25)

nodes = nodes_no_adr_no_conf_df
plt.plot(payload_sizes, nodes.mean_energy_per_byte, marker='.', markersize=12, ls='-.', label='NO ADR NO CONF')
plt.fill_between(payload_sizes, nodes.mean_energy_per_byte-nodes.sigma_energy_per_byte, nodes.mean_energy_per_byte+nodes.sigma_energy_per_byte, alpha=0.25)

plt.legend()
#plt.savefig('./Figures/payload_vs_energy.eps', format='eps', dpi=1000)
plt.show()
