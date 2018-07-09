import multiprocessing as mp
import pickle

import numpy as np
import pandas as pd

import SimulationProcess
from Global import Config
from Location import Location

# The console attempts to auto-detect the width of the display area, but when that fails it defaults to 80
# characters. This behavior can be overridden with:
desired_width = 320
pd.set_option('display.width', desired_width)

transmission_rate = 0.02e-3  # 12*8 bits per hour (1 typical packet per hour)
simulation_time = 10 * 24 * 60 * 60 * 1000
cell_size = 1000
adr = True
confirmed_messages = True

middle = np.round(Config.CELL_SIZE / 2)
gateway_location = Location(x=middle, y=middle, indoor=False)

payload_sizes = range(5, 55, 5)
path_loss_variances = [0, 5, 7.8, 15, 20]

if __name__ == '__main__':
    output = mp.Queue()

    # load locations:
    with open('locations_100_locations_1000_sim.pkl', 'rb') as file_handler:
        locations_per_simulation = pickle.load(file_handler)
        num_of_simulations = len(locations_per_simulation)
        num_of_simulations = 10
        num_nodes = len(locations_per_simulation[0])
        num_nodes = 10

        results = {
            'cell_size': cell_size,
            'adr': adr,
            'confirmed_messages': confirmed_messages,
            'num_simulations': num_of_simulations,
            'total_devices': num_nodes,
            'transmission_rate': transmission_rate,
            'simulation_time': simulation_time,
            'nodes': dict(),
            'gateway': dict(),
            'air_interface': dict(),
            'path_loss_variances': path_loss_variances,
            'payload_sizes': payload_sizes,
            'mean_energy': dict(),
            'std_energy': dict()
        }

        print(results)

        for payload_size in payload_sizes:
            results['nodes'][payload_size] = dict()
            results['gateway'][payload_size] = dict()
            results['air_interface'][payload_size] = dict()
            results['mean_energy'][payload_size] = dict()
            results['std_energy'][payload_size] = dict()

        cnt = 0
        for n_sim in range(num_of_simulations):
            locations = locations_per_simulation[n_sim]
            processes = list()
            for payload_size in payload_sizes:
                for path_loss_variance in path_loss_variances:
                    p = mp.Process(target=SimulationProcess.run,
                                   args=(locations, payload_size, path_loss_variance, simulation_time,
                                         gateway_location, num_nodes,
                                         transmission_rate, confirmed_messages, adr, output))
                    p.start()
                    processes.append(p)
                    cnt = cnt + 1
                    print('start process #{}'.format(cnt))

            # wait for the processes to finish
            for p in processes:
                p.join()
                print('process ended')
                print('process result')
                r = output.get()
                # average and store results in global results variable
                sigma = r['path_loss_std']
                p_size = r['payload_size']
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

        pickle.dump(results, open("results_{}_{}_10_10_10.p".format(adr, confirmed_messages), "wb"))
