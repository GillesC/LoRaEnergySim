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
In order to compare different `settings/configurations`, it is imperative that the locations of the nodes are the same for all simulations.
Therefore, a file `generate_locations.py` is included in the examples.

Workflow:
- Define your the settings for a simulation environment, e.g., start spreading factor, simulation duration (real-time), in the [GlobalConfig](https://github.com/GillesC/LoRaEnergySim/blob/master/Simulations/GlobalConfig.py) file
- Generate your locations see [here](#generate-node-locations). It will use the settings defined in the GlobalConfig file.
- Create a `Simulation.py` file as detailed [here](#simulation).


#### Generate Node locations

Configurable parameters:
- number of locations, i.e., number of IoT nodes
- cell size, the cell is here a rectangular area. The cell size will determine the length of the edges in meters
- number of Monto-carlo simulations to run. As the simulation contains random and non-determinstic behavior and different location sets, 
  averaging the results over multiple simulations will have a more statistical meaning.
  
For each simulation, a random set of locations inside the area is generated and is stored in the `location_file` 
which is a parameter defined in the `GlobalConfig.py` file. 


#### Simulation
In the simulation file, you will use the building blocks in the framework to simulate a specific environment and 
acquire results such as the consumed energy, and the number of collided messages. See section `Framework` (below) for configurable parameters and output.
Please see the comments in the `Example>simulation.py` on how to write a simulation file. 
In `simulation.py` you load the locations, specify the object to hold the results and specify what you want to simulate.
In `SimulationProcess`, the simulation itself is run. The gateway is created, the nodes are generated with their lora parameters and energy profile.
Afterwhich the simulation is run. After completion of one simulation the results are extracted from the objects and returned, to be used in the `simulation.py` file.

The project can now be run by first running `generate_locations.py` and then `simulation.py`.

## Framework

Please read first the paper to have a more detailed understanding of the framework with respect to LoRaWAN operation and limitations.

### Propagation Model
The propagation model determines how the messages are impacted by the environment. 
It predicts the path loss, i.e., how much the signal is attenuated between the transmitter and receiver, for a given environment. 
The `PropagationModel.py` contains (currently) two implementations:

- log shadow model or log-distance path loss model, where the default parameters are based on the Rep. ITU-R P.2346-0 and J. Petajajarvi, K. Mikhaylov, A. Roivainen, T. Hanninen and M. Pettissalo, "On the coverage of LPWANs: range evaluation and channel attenuation model for LoRa technology," 2015 14th International Conference on ITS Telecommunications (ITST), 2015, pp. 55-59, doi: 10.1109/ITST.2015.7377400.
- COST231, including more details about the environment, e.g., building heights

### SNR Model
This model transforms the received signal strength (RSS) to a signal-to-noise ratio (SNR) by the method `rss_to_snr`.
At this moment the noise is only affected by the [thermal noise](https://en.wikipedia.org/wiki/Johnson%E2%80%93Nyquist_noise).
This results in (dB):
```python
SNR = RSS - (-174 + 10 * log10(125e3))
```



### LoRa Parameters
All parameters specific to the lora protocol (lorawan) and measured energy consumption related to these parameters are here included.

### LoRaPacket
LoRaPackets are send over the air interface from the nodes to the gateway.
`LoRaPacket` contains a uplink and downlink message class, including relevant metadata and information concerning the state of the message, e.g., received, collided,...

### Energy Profile
The energy profile class contains the sleep, processing, transmitting and received power of a node.
This can be different for each node and can be defined in the `simulation.py` file.

### Node
The Node class contains all information regarding the power consumption, number of messages send, payload send, retransmissions, ...
Nodes act as real IoT nodes, joining the network, waiting, sleeping, transmittion and receiving. Their behaviour is determined in the main `simulation.py` file.


After running the simulation, you can extract the following iniformation:
- `energy_per_bit`. This is the amount of energy consumed to send one bit of data
- `transmit_related_energy_per_bit`. This only contains the energy spend in transmit mode.
- `transmit_related_energy_per_unique_bit`. This only contains the energy spend in transmit mode and tx'ed retransmissions are not count against the transmitted bits
-  `total_energy_consumed`
- `get_simulation_data`:
```python
series = {
            'WaitTimeDC': self.total_wait_time_because_dc / 1000,  # [s] instead of [ms]
            'NoDLReceived': self.num_no_downlink,
            'UniquePackets': self.num_unique_packets_sent,
            'TotalPackets': self.packets_sent,
            'CollidedPackets': self.num_collided,
            'RetransmittedPackets': self.num_retransmission,
            'TotalBytes': self.bytes_sent,
            'TotalEnergy': self.total_energy_consumed(),
            'TxRxEnergy': self.transmit_related_energy_consumed(),
            'EnergyValuePackets': self.energy_value
        }
```

### Air interface
The air interface detects collisions and alters the LoRaPacket object so the node and gateway know what happened during the transmission of the message.
It employs the used propagation model and snr model to determine if the transfer was successful or not.

### Gateway
At the gateway, the received SNR is checked and messages below the required threshold are marked as weak and is not rx'ed.
The gateway also handles DL messages if requested by the node.


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

Q: Can't find Globaconfig, Locations, ....<br>
A: Ensure that the folders Framework and Simulations are marked as Source Root. For Pycharm right click on the folder > Mark directory as > Source Root

Q: no output in IPython/Spyder<br>
A: The code is run in parralel by default and the std output is not handled well in that case. You can run the code sequently, see the comments in Example/simulation.py regarding the pool.map function at the bottom.

## Academic work using our simulator

Cited [in](https://scholar.google.com/scholar?cites=2795983333038395209&as_sdt=2005&sciodt=0,5&hl=en).

Simulator used in:
- F. De Rango, D. Stumpo and A. Iera, "Interference Region Aware Channel Assignments for a Scalable LoRa Network," 2024 20th International Conference on Wireless and Mobile Computing, Networking and Communications (WiMob), Paris, France, 2024, pp. 19-24, doi: 10.1109/WiMob61911.2024.10770310. 
- G. L. Scapin, G. Alvarez, N. Quiroga, F. Collado and J. A. Fraire, "Performance Assessment of LoRaWAN DtS-IoT Networks: Operation Modes and Server Placement," 2024 IEEE Biennial Congress of Argentina (ARGENCON), San Nicolás de los Arroyos, Argentina, 2024, pp. 1-8, doi: 10.1109/ARGENCON62399.2024.10735884.
- Park, G., Lee, W., & Joe, I. (2020). Network resource optimization with reinforcement learning for low power wide area networks. EURASIP Journal on Wireless Communications and Networking, 2020(1), 1-20.
- L. Beltramelli, A. Mahmood, P. Österberg, M. Gidlund, P. Ferrari and E. Sisinni, "Energy Efficiency of Slotted LoRaWAN Communication With Out-of-Band Synchronization," in IEEE Transactions on Instrumentation and Measurement, vol. 70, pp. 1-11, 2021, Art no. 5501211, doi: 10.1109/TIM.2021.3051238.
- Thoen B, Callebaut G, Leenders G, Wielandt S. A Deployable LPWAN Platform for Low-Cost and Energy-Constrained IoT Applications. Sensors. 2019; 19(3):585. https://doi.org/10.3390/s19030585
- T. Fedullo, A. Morato, F. Tramarin, P. Bellagente, P. Ferrari and E. Sisinni, "Adaptive LoRaWAN Transmission exploiting Reinforcement Learning: the Industrial Case," 2021 IEEE International Workshop on Metrology for Industry 4.0 & IoT (MetroInd4.0&IoT), Rome, Italy, 2021, pp. 671-676, doi: 10.1109/MetroInd4.0IoT51437.2021.9488498.
- Leenders G, Callebaut G, Ottoy G, Van der Perre L, De Strycker L. An Energy-Efficient LoRa Multi-Hop Protocol through Preamble Sampling for Remote Sensing. Sensors. 2023; 23(11):4994. https://doi.org/10.3390/s23114994
- Acosta-Garcia, L., Aznar-Poveda, J., Garcia-Sanchez, A. J., Garcia-Haro, J., & Fahringer, T. (2023). Dynamic transmission policy for enhancing LoRa network performance: A deep reinforcement learning approach. Internet of Things, 24, 100974.
- G. Leenders, G. Ottoy, G. Callebaut, L. Van der Perre and L. De Strycker, "An Energy-Efficient LoRa Multi-Hop Protocol through Preamble Sampling," 2023 IEEE Wireless Communications and Networking Conference (WCNC), Glasgow, United Kingdom, 2023, pp. 1-6, doi: 10.1109/WCNC55385.2023.10118770.
- E. Sisinni et al., "A new LoRaWAN adaptive strategy for smart metering applications," 2020 IEEE International Workshop on Metrology for Industry 4.0 & IoT, Roma, Italy, 2020, pp. 690-695, doi: 10.1109/MetroInd4.0IoT48571.2020.9138226.
- T. Fedullo, A. Mahmood, F. Tramarin, A. Morato, M. Gidlund and L. Rovati, "Exploiting Hybrid Medium Access Control and Relaying Strategies to Overcome Duty-Cycle Limitations in LoRa-Based Sensor Networks," 2023 IEEE International Instrumentation and Measurement Technology Conference (I2MTC), Kuala Lumpur, Malaysia, 2023, pp. 01-06, doi: 10.1109/I2MTC53148.2023.10176039.
- F. De Rango, A. Lipari, D. Stumpo and A. Iera, "Dynamic Switching in LoRaWAN under multiple Gateways and Heavy Traffic Load," 2021 IEEE Global Communications Conference (GLOBECOM), Madrid, Spain, 2021, pp. 1-6, doi: 10.1109/GLOBECOM46510.2021.9685009.
- D. Stumpo, F. De Rango, F. Buffone and M. Tropea, "Performance of Extended LoRaEnergySim Simulator in supporting Multi-Gateway scenarios and Interference Management," 2022 IEEE/ACM 26th International Symposium on Distributed Simulation and Real Time Applications (DS-RT), Alès, France, 2022, pp. 135-142, doi: 10.1109/DS-RT55542.2022.9932063.
- G. Callebaut, G. Ottoy and L. V. d. Perre, "Optimizing Transmission of IoT Nodes in Dynamic Environments," 2020 International Conference on Omni-layer Intelligent Systems (COINS), Barcelona, Spain, 2020, pp. 1-5, doi: 10.1109/COINS49042.2020.9191674.
- Križanović, V.; Grgić, K.; Spišić, J.; Žagar, D. An Advanced Energy-Efficient Environmental Monitoring in Precision Agriculture Using LoRa-Based Wireless Sensor Networks. Sensors 2023, 23, 6332.
- Zhang, Jiayue. "Design Guidelines of A Low Power Communication Protocol for Zero Energy Devices." (2023).
- Stumpo, Daniele, Floriano De Rango, and Francesco Buffone. "Extending LoRaEnergySim Simulator to Support Interference Management under Multi-Gateway IoT Scenarios." (2022).
- T. Fedullo, A. Morato, F. Tramarin, P. Ferrari and E. Sisinni, "Smart Measurement Systems Exploiting Adaptive LoRaWAN Under Power Consumption Constraints: a RL Approach," 2022 IEEE International Workshop on Metrology for Industry 4.0 & IoT (MetroInd4.0&IoT), Trento, Italy, 2022, pp. 354-359, doi: 10.1109/MetroInd4.0IoT54413.2022.9831487.


