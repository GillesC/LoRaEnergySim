import numpy as np


class Config:
    LOG_ENABLED = True
    MAX_DELAY_BEFORE_SLEEP_MS = 500
    SIMULATION_TIME = 10*1000*60*60*24
    PRINT_ENABLED = False
    CELL_SIZE = 100
    MAX_DELAY_START_PER_NODE_MS = np.round(SIMULATION_TIME / 10)
    num_nodes = 1
    track_changes = True
