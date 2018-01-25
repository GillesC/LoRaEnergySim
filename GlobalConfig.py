import numpy as np


class GlobalConfig:
    MAX_DELAY_BEFORE_SLEEP_MS = 500
    SIMULATION_TIME = 10*1000*60*60*24
    PRINT_ENABLED = False
    CELL_SIZE = 1000
    MAX_DELAY_START_PER_NODE_MS = np.round(SIMULATION_TIME / 10)
    num_nodes = 10
    track_changes = True
