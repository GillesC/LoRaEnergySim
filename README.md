# LoRaEnergySim

![Simulation](lora_simulator_v2.png "LoRaWAN Simulator")

## How to cite?
```
@misc{callebautLoRaSim,
author =   {Gilles Callebaut},
title =    {{LoRaWAN Network Energy Simulator}},
doi = {10.5281/zenodo.1217125},
howpublished = {\url{https://github.com/GillesC/LoRaEnergySim}},
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
