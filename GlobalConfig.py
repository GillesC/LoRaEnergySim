class GlobalConfig:
    CELL_SIZE = 1000
    MAX_DELAY_START_PER_NODE_MS = 10*60*1000 # 10 minutes
    PROB_RX1 = 0.8
    PROB_RX2 = 1 - PROB_RX1
    num_nodes = 100
    track_changes = True
