import simpy

import PropagationModel
from AirInterface import AirInterface
from EnergyProfile import EnergyProfile
from Gateway import Gateway
from LoRaParameters import LoRaParameters
from Node import Node
from SNRModel import SNRModel
import numpy as np

tx_power_mW = {2: 91.8, 5: 95.9, 8: 101.6, 11: 120.8, 14: 146.5}
rx_measurements = {'pre_mW': 8.2, 'pre_ms': 3.4, 'rx_lna_on_mW': 39,
                   'rx_lna_off_mW': 34,
                   'post_mW': 8.3, 'post_ms': 10.7}


def run(locs, p_size, sigma, sim_time, gateway_location, num_nodes, transmission_rate, confirmed_messages, adr,
        output):
    sim_env = simpy.Environment()
    gateway = Gateway(sim_env, gateway_location, max_snr_adr=False, avg_snr_adr=True)
    nodes = []
    air_interface = AirInterface(gateway, PropagationModel.LogShadow(std=sigma), SNRModel(), sim_env)
    for node_id in range(num_nodes):
        energy_profile = EnergyProfile(5.7e-3, 15, tx_power_mW,
                                       rx_power=rx_measurements)
        lora_param = LoRaParameters(freq=np.random.choice(LoRaParameters.DEFAULT_CHANNELS),
                                    sf=12,
                                    bw=125, cr=5, crc_enabled=1, de_enabled=0, header_implicit_mode=0, tp=14)
        node = Node(node_id, energy_profile, lora_param, sleep_time=(8 * p_size / transmission_rate),
                    process_time=5,
                    adr=adr,
                    location=locs[node_id],
                    base_station=gateway, env=sim_env, payload_size=p_size, air_interface=air_interface,
                    confirmed_messages=confirmed_messages)
        nodes.append(node)
        sim_env.process(node.run())

    sim_env.run(until=sim_time)

    # Simulation is done.
    # process data

    mean_anergy_per_bit_list = list()
    for n in nodes:
        mean_anergy_per_bit_list.append(n.energy_per_bit())

    data_mean_nodes = Node.get_mean_simulation_data_frame(nodes, name=sigma) / (
        num_nodes)

    data_gateway = gateway.get_simulation_data(name=sigma) / num_nodes
    data_air_interface = air_interface.get_simulation_data(name=sigma) / (
        num_nodes)

    output.put({
        'mean_nodes': data_mean_nodes,
        'gateway': data_gateway,
        'air_interface': data_air_interface,
        'path_loss_std': sigma,
        'payload_size': p_size,
        'mean_energy_all_nodes': mean_anergy_per_bit_list
    })
