import numpy as np


class GlobalConfig:
    MAX_DELAY_BEFORE_SLEEP_MS = 500 #500 ms
    SIMULATION_TIME = 10*1000*60*60*24
    PRINT_ENABLED = False
    CELL_SIZE = 1000
    MAX_DELAY_START_PER_NODE_MS = np.round(SIMULATION_TIME / 10)
    PROB_RX1 = 0.8
    PROB_RX2 = 1 - PROB_RX1
    num_nodes = 100
    track_changes = True
