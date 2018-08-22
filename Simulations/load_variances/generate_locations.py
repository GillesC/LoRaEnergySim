import os
import pickle

from GlobalConfig import locations_file, num_of_simulations, num_locations, cell_size
from Location import Location

locations_per_simulation = list()
for num_sim in range(num_of_simulations):
    locations = list()
    for i in range(num_locations):
        locations.append(Location(min=0, max=cell_size, indoor=False))
    locations_per_simulation.append(locations)

os.makedirs(os.path.dirname(locations_file), exist_ok=True)
with open(locations_file, 'wb') as f:
    pickle.dump(locations_per_simulation, f)
