import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("white")

# Latex specific settings
plt.rc('text', usetex=True)
plt.rc('font', family='serif')

gateway_adr_conf_df = pd.read_pickle(
    '../Measurements/payload_size_energy_1000_sim_100_nodes/adr_conf_gateway_results_100')
nodes_adr_conf_df = pd.read_pickle(
    '../Measurements/payload_size_energy_1000_sim_100_nodes/adr_conf_simulation_results_node_100')
payload_sizes = nodes_adr_conf_df.index.values
gateway_adr_no_conf_df = pd.read_pickle(
    '../Measurements/payload_size_energy_1000_sim_100_nodes/adr_no_conf_gateway_results_100')
nodes_adr_no_conf_df = pd.read_pickle(
    '../Measurements/payload_size_energy_1000_sim_100_nodes/adr_no_conf_simulation_results_node_100')
gateway_no_adr_no_conf_df = pd.read_pickle(
    '../Measurements/payload_size_energy_1000_sim_100_nodes/no_adr_no_conf_gateway_results_100')
nodes_no_adr_no_conf_df = pd.read_pickle(
    '../Measurements/payload_size_energy_1000_sim_100_nodes/no_adr_no_conf_simulation_results_node_100')

plt.xlabel('Payload size (B)', fontsize=16)
plt.ylabel('Energy per payload byte $E_B$ (mJ)', fontsize=16)
energy_per_byte = nodes_adr_conf_df.TxRxEnergy / (gateway_adr_conf_df.UniquePacketsReceived * payload_sizes)
plt.plot(payload_sizes, energy_per_byte, marker='+', markersize=12, ls='--', label='ADR CONF (per successful byte)')
energy_per_byte = nodes_adr_conf_df.TxRxEnergy / nodes_adr_conf_df.TotalBytes
plt.plot(payload_sizes, energy_per_byte, marker='+', markersize=12, ls='--', label='ADR CONF (per byte)')


energy_per_byte = nodes_adr_no_conf_df.TxRxEnergy / (gateway_adr_no_conf_df.UniquePacketsReceived * payload_sizes)
plt.plot(payload_sizes, energy_per_byte, marker='1', markersize=12, ls='-.', label='ADR NO CONF (per successful byte)')


energy_per_byte = nodes_no_adr_no_conf_df.TxRxEnergy / (gateway_no_adr_no_conf_df.UniquePacketsReceived * payload_sizes)
plt.plot(payload_sizes, energy_per_byte, marker='.', markersize=12, ls='-.', label='NO ADR NO CONF (per successful '
                                                                                   'byte)')

plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig('./Figures/payload_vs_energy.eps', format='eps', dpi=1000)
plt.show()
