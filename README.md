# LoRaEnergySim

The framework consists of three main components, i.e., nodes, an air interface and a gateway.
The nodes send messages to the gateway via the air interface.
Collisions and weak messages are detected in the air interface component.
The uncollided and strong packets are delivered to the gateway, whereafter a downlink message will be scheduled if requested by the node.

![Simulation](lora_simulator_v2.png "LoRaWAN Simulator")

## How to cite?

```latex
@INPROCEEDINGS{8885739,  
author={G. {Callebaut} and G. {Ottoy} and L. {van der Perre}},  
booktitle={2019 IEEE Wireless Communications and Networking Conference (WCNC)},   
title={Cross-Layer Framework and Optimization for Efficient Use of the Energy Budget of IoT Nodes},   
year={2019},  
volume={},  
number={},  
pages={1-6},
}
```

Other publications:

```
G. Callebaut, G. Ottoy and L. V. d. Perre, "Optimizing Transmission of IoT Nodes in Dynamic Environments," 
2020 International Conference on Omni-layer Intelligent Systems (COINS), 2020, pp. 1-5, doi: 10.1109/COINS49042.2020.9191674.
```


## How to use?
The source of the framework is located in the `Framework` folder.
The `Simulations` folder contains some examples.

### General Workflow
In order to compare different settings/configurations, it is imperative that the locations of the nodes are the same for all simulations.
Therefore, a file `generate_locations.py` is included in the examples.

#### Generate Node locations

Configurable parameters:
- number of locations, i.e., number of IoT nodes
- cell size, the cell is here a rectangular area. The cell size will determine the length of the edges in meters
- number of Monto-carlo simulations to run. As the simulation contains random and non-determinstic behavior and different location sets, 
  averaging the results over multiple simulations will have a more statistical meaning.
  
For each simulation, a random set of locations inside the area is generated and is stored in the `location_file` 
which is a parameter defined in the `GlobalConfig.py` file. 


#### Simulation.py
In the simulation file, you will use the building blocks in the framework to simulate a specific environment and 
acquire results such as the consumed energy, and the number of collided messages. See section `Framework` (below) for configurable parameters and output.



## Framework

### Propagation Model
The propagation model determines how the messages are impacted by the environment. 
It predicts the path loss, i.e., how much the signal is attenuated, for a given environment. 
The `PropagationModel.py` contains (currently) two implementations.

#### log shadow model or log-distance path loss model
It is described as:
![formula](https://render.githubusercontent.com/render/math?math=PL=P_{Tx_{dBm}}-P_{Rx_{dBm}}=PL_{0}%2B10\gamma%20\log%20_{10}{\frac%20{d}{d_{0}}}%2BX_{g})
<img alt="formula" src="https://render.githubusercontent.com/render/math?math=PL=P_{Tx_{dBm}}-P_{Rx_{dBm}}=PL_{0}%2B10\gamma%20\log%20_{10}{\frac%20{d}{d_{0}}}%2BX_{g}" />


### Air interface


### Energy Profile

### Gateway

### Global

### Location

### LoRaPacket







### The node

#### Configurable Properties
- energy_profile: EnergyProfile, 
- lora_parameters, 
- sleep_time, 
- process_time, 
- adr, 
- location,
- payload_size,  
- confirmed_messages=True

#### What is currently tracked
 - 'WaitTimeDC': total_wait_time_because_dc
 - 'NoDLReceived': num_no_downlink,
 - 'UniquePackets': num_unique_packets_sent,
 - 'TotalPackets': packets_sent,
 - 'CollidedPackets': num_collided,
 - 'RetransmittedPackets': num_retransmission,
 - 'TotalBytes': bytes_sent,
 - 'TotalEnergy': total_energy_consumed(),
 - 'TxRxEnergy': transmit_related_energy_consumed(),



## Common Erros

Q: Can't find Globaconfig, Locations, ....

A: Ensure that the folders Framework and Simulations are marked as Source Root. For Pycharm right click on the folder > Mark directory as > Source Root