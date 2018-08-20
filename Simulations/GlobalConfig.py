import numpy as np

############### SIMULATION SPECIFIC PARAMETERS ###############
start_with_fixed_sf = False
start_sf = 7

transmission_rate_bit_per_ms = (12*8)/(60*60*1000)  # 12*8 bits per hour (1 typical packet per hour)
simulation_time = 24 * 60 * 60 * 1000 * 1
cell_size = 1000
adr = True
confirmed_messages = True

payload_sizes = range(5, 55, 5)
path_loss_variances = [7.9]  # [0, 5, 7.8, 15, 20]

MAC_IMPROVEMENT = False
locations_file = "Locations/"+"10_locations_10_sim.pkl"

############### SIMULATION SPECIFIC PARAMETERS ###############

############### DEFAULT PARAMETERS ###############
LOG_ENABLED = True
MAX_DELAY_BEFORE_SLEEP_MS = 500
PRINT_ENABLED = False
MAX_DELAY_START_PER_NODE_MS = np.round(simulation_time / 10)
track_changes = True
############### DEFAULT PARAMETERS ###############
