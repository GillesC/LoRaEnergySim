import os
import pickle

from GlobalConfig import *
from Location import Location
from RectangularArea import RectangularArea

# Simulation specific parameters extracted from GlobalConfig.py

if indoor_nodes is True:
    indoor_area = RectangularArea(origin=Location(x=0, y=0), len_x=200, len_y=300)

locations_per_simulation = list()
for num_sim in range(num_of_simulations):
    locations = list()
    for i in range(num_locations):
        loc = Location(min=0, max=max_x, minY=0, maxY=max_y, indoor=False)
        if indoor_nodes and indoor_area.is_inside(loc):
            loc.indoor = True
        locations.append(loc)
    locations_per_simulation.append(locations)


os.makedirs(os.path.dirname(locations_file), exist_ok=True)
with open(locations_file, 'wb') as f:
    pickle.dump(locations_per_simulation, f)

# just to test the code
# with open('locations_10000_locations_1000_sim.pkl', 'rb') as filehandler:
#     print(pickle.load(filehandler))
