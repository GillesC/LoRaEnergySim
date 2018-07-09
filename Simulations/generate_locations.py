import pickle
import sys
import os

sys.path.append(os.getcwd() + '../../LoRaEnergySim')

from Location import Location

num_locations = 100
cell_size = 1000
num_of_simulations = 1000

locations_per_simulation = list()
for num_sim in range(num_of_simulations):
    locations = list()
    for i in range(num_locations):
        locations.append(Location(min=0, max=cell_size, indoor=False))
    locations_per_simulation.append(locations)

with open('locations_100_locations_1000_sim.pkl', 'wb') as f:
    pickle.dump(locations_per_simulation, f)

# just to test the code
# with open('locations_10000_locations_1000_sim.pkl', 'rb') as filehandler:
#     print(pickle.load(filehandler))
