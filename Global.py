import numpy as np


class Config:
    LOG_ENABLED = True
    MAX_DELAY_BEFORE_SLEEP_MS = 500
    SIMULATION_TIME = 1000*60*60*24*10*10
    PRINT_ENABLED = False
    CELL_SIZE = 500
    MAX_DELAY_START_PER_NODE_MS = np.round(SIMULATION_TIME / 10)
    num_nodes = 10
    track_changes = True
