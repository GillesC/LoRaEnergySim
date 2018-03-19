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
plt.ylabel('Data Extraction Rate (\%)', fontsize=16)
der = (gateway_adr_conf_df.UniquePacketsReceived / nodes_adr_conf_df.UniquePackets)*100
plt.plot(payload_sizes, der, marker='+', markersize=12, ls='--', label='$DER_{UN}$ ADR CONF')
der = (gateway_adr_conf_df.PacketsReceived / nodes_adr_conf_df.TotalPackets)*100
plt.plot(payload_sizes, der, marker='+', markersize=12, ls='--', label='DER ADR CONF')
der = (gateway_adr_conf_df.UniquePacketsReceived / nodes_adr_conf_df.TotalPackets)*100
plt.plot(payload_sizes, der, marker='+', markersize=12, ls='--', label='bytes sent to receive ADR CONF')


der = (gateway_adr_no_conf_df.UniquePacketsReceived / nodes_adr_no_conf_df.UniquePackets)*100
plt.plot(payload_sizes, der, marker='1', markersize=12, ls='-.', label='$DER_{UN}$ ADR NO CONF')
der = (gateway_adr_no_conf_df.PacketsReceived / nodes_adr_no_conf_df.TotalPackets)*100
plt.plot(payload_sizes, der, marker='1', markersize=12, ls='-.', label='DER ADR NO CONF')
der = (gateway_adr_no_conf_df.UniquePacketsReceived / nodes_adr_no_conf_df.TotalPackets)*100
plt.plot(payload_sizes, der, marker='1', markersize=12, ls='-.', label='bytes sent to receive ADR NO CONF')


der = (gateway_no_adr_no_conf_df.UniquePacketsReceived / nodes_no_adr_no_conf_df.UniquePackets)*100
plt.plot(payload_sizes, der, marker='.', markersize=12, ls='-.', label='$DER_{UN}$ NO ADR NO CONF')
der = (gateway_no_adr_no_conf_df.PacketsReceived / nodes_no_adr_no_conf_df.TotalPackets)*100
plt.plot(payload_sizes, der, marker='.', markersize=12, ls='-.', label='DER NO ADR NO CONF')
der = (gateway_no_adr_no_conf_df.UniquePacketsReceived / nodes_no_adr_no_conf_df.TotalPackets)*100
plt.plot(payload_sizes, der, marker='.', markersize=12, ls='-.', label='bytes sent to receive NO ADR NO CONF')

plt.grid(True)
plt.legend()
plt.tight_layout()
#plt.savefig('./Figures/payload_vs_energy.eps', format='eps', dpi=1000)
plt.show()
