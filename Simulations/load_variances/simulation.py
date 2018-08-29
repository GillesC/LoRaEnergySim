import gc
import math
import multiprocessing as mp
import os
import pickle

import pandas as pd
from Location import Location
import SimulationProcess
from GlobalConfig import *

# The console attempts to auto-detect the width of the display area, but when that fails it defaults to 80
# characters. This behavior can be overridden with:
desired_width = 320
pd.set_option('display.width', desired_width)

gateway_location = Location(x=middle, y=middle, indoor=False)


def process_results(results, p_size, sigma, r):
    p_size = str(p_size)
    sigma = str(sigma)
    if sigma not in results['nodes'][p_size]:
        results['nodes'][p_size][sigma] = r['mean_nodes'] / num_of_simulations
        results['gateway'][p_size][sigma] = r['gateway'] / num_of_simulations
        results['air_interface'][p_size][sigma] = r['air_interface'] / num_of_simulations
        results['mean_energy'][p_size][sigma] = np.mean(r['mean_energy_all_nodes']) / num_of_simulations
        results['std_energy'][p_size][sigma] = np.std(r['mean_energy_all_nodes']) / num_of_simulations
    else:
        results['nodes'][p_size][sigma] = results['nodes'][p_size][sigma] + r[
            'mean_nodes'] / num_of_simulations
        results['gateway'][p_size][sigma] = results['gateway'][p_size][sigma] + r[
            'gateway'] / num_of_simulations
        results['air_interface'][p_size][sigma] = results['air_interface'][p_size][sigma] + r[
            'air_interface'] / num_of_simulations
        results['mean_energy'][p_size][sigma] = results['mean_energy'][p_size][sigma] + np.mean(
            r['mean_energy_all_nodes']) / num_of_simulations
        results['std_energy'][p_size][sigma] = results['std_energy'][p_size][sigma] + np.std(
            r['mean_energy_all_nodes']) / num_of_simulations


if __name__ == '__main__':

    # load locations:
    with open(locations_file, 'rb') as file_handler:
        locations_per_simulation = pickle.load(file_handler)
        num_of_simulations = len(locations_per_simulation)
        num_nodes = len(locations_per_simulation[0])

    resume_from_simulation = 0

    if os.path.isfile(results_file) and load_prev_simulation_results:
        _results = pickle.load(open(results_file, "rb"))
        if 'idx_of_simulations_done' in _results:
            resume_from_simulation = _results['idx_of_simulations_done'] + 1
    else:
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        _results = {
            'cell_size': cell_size,
            'adr': adr,
            'confirmed_messages': confirmed_messages,
            'num_simulations': num_of_simulations,
            'total_devices': num_nodes,
            'transmission_rate': transmission_rate_bit_per_ms,
            'simulation_time': simulation_time,
            'nodes': dict(),
            'gateway': dict(),
            'air_interface': dict(),
            'path_loss_variances': path_loss_variances,
            'payload_sizes': payload_sizes,
            'mean_energy': dict(),
            'std_energy': dict(),
            'num_of_simulations_done': 0
        }

    for payload_size in payload_sizes:
        _results['nodes'][str(payload_size)] = dict()
        _results['gateway'][str(payload_size)] = dict()
        _results['air_interface'][str(payload_size)] = dict()
        _results['mean_energy'][str(payload_size)] = dict()
        _results['std_energy'][str(payload_size)] = dict()

    pool = mp.Pool(math.floor(mp.cpu_count() / 5))
    for n_sim in range(resume_from_simulation, num_of_simulations):
        print('Simulation #{}'.format(n_sim))
        locations = locations_per_simulation[n_sim]
        args = []
        for payload_size in payload_sizes:
            for path_loss_variance in path_loss_variances:
                args.append((locations, payload_size, path_loss_variance, simulation_time,
                             gateway_location, num_nodes,
                             transmission_rate_bit_per_ms, confirmed_messages, adr))
        r_list = pool.map(func=SimulationProcess.run_helper, iterable=args)
        gc.collect()
        for _r in r_list:
            _sigma = _r['path_loss_std']
            _p_size = _r['payload_size']
            process_results(_results, _p_size, _sigma, _r)
            # update Results
            # can check progress during execution of simulation process

        _results['idx_of_simulations_done'] = n_sim
        pickle.dump(_results, open(results_file, "wb"))
    pool.close()
