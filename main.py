import matplotlib.pyplot as plt

from GlobalConfig import GlobalConfig
from Location import Location

if __name__ == "__main__":
    for node_id in range(GlobalConfig.num_nodes):
        location = Location(0, 100, True)
        # node = Node(node_id, EnergyProfile())
        plt.scatter(location.x, location.y, color='blue')
    gateway = Location(0, 100, True)
    plt.scatter(50, 50, color='red')
    plt.show()