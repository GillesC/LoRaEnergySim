# LoRaEnergySim

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

## How to use?
The framework consists of three main components, i.e., nodes, an air interface and a gateway.
The nodes send messages to the gateway via the air interface.
Collisions and weak messages are detected in the air interface component.
The uncollided and strong packets are delivered to the gateway, whereafter a downlink message will be scheduled if requested by the node.

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
