import pickle

from Location import Location

num_locations = 10
cell_size = 1000
num_of_simulations = 10

locations_per_simulation = list()
for num_sim in range(num_of_simulations):
    locations = list()
    for i in range(num_locations):
        locations.append(Location(min=0, max=cell_size, indoor=False))
    locations_per_simulation.append(locations)

with open('locations/{}_locations_{}_sim.pkl'.format(num_locations, num_of_simulations), 'wb') as f:
    pickle.dump(locations_per_simulation, f)

# just to test the code
# with open('locations_10000_locations_1000_sim.pkl', 'rb') as filehandler:
#     print(pickle.load(filehandler))
