import gc
import multiprocessing as mp
import pickle

import pandas as pd
from Location import Location
import SimulationProcess
from GlobalConfig import *

# The console attempts to auto-detect the width of the display area, but when that fails it defaults to 80
# characters. This behavior can be overridden with:
desired_width = 320
pd.set_option('display.width', desired_width)

middle = np.round(cell_size / 2)
gateway_location = Location(x=middle, y=middle, indoor=False)


def process_results(results, p_size, sigma):
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

        _results = {
            'cell_size': cell_size,
            'adr': adr,
            'confirmed_messages': confirmed_messages,
            'num_simulations': num_of_simulations,
            'total_devices': num_nodes,
            'transmission_rate': transmission_rate_ms_per_bit,
            'simulation_time': simulation_time,
            'nodes': dict(),
            'gateway': dict(),
            'air_interface': dict(),
            'path_loss_variances': path_loss_variances,
            'payload_sizes': payload_sizes,
            'mean_energy': dict(),
            'std_energy': dict()
        }

        print(_results)

        for payload_size in payload_sizes:
            _results['nodes'][str(payload_size)] = dict()
            _results['gateway'][str(payload_size)] = dict()
            _results['air_interface'][str(payload_size)] = dict()
            _results['mean_energy'][str(payload_size)] = dict()
            _results['std_energy'][str(payload_size)] = dict()

        cnt = 0
        pool = mp.Pool(mp.cpu_count())
        for n_sim in range(num_of_simulations):
            print('Simulation #{}'.format(n_sim))
            locations = locations_per_simulation[n_sim]
            args = []
            for payload_size in payload_sizes:
                for path_loss_variance in path_loss_variances:
                    args.append((locations, payload_size, path_loss_variance, simulation_time,
                                 gateway_location, num_nodes,
                                 transmission_rate_ms_per_bit, confirmed_messages, adr))
            r_list = pool.map(func=SimulationProcess.run_helper, iterable=args)
            gc.collect()
            for r in r_list:
                _sigma = r['path_loss_std']
                _p_size = r['payload_size']
                process_results(_results, _p_size, _sigma)
            # update Results
            # can check progress during execution of simulation process
            pickle.dump(_results, open(
                "results/{}_{}_{}_{}_SF_random.p".format(adr, confirmed_messages, num_of_simulations,
                                                                        num_nodes), "wb"))
        pool.close()
