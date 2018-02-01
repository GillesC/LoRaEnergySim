# LoRaEnergySim



## Sending an uplink message

- First add message to the AirInterface.
- If packet has not collided the gateway will check if the packet is strong enough and schedules a DL message (if possible and requested)


### Uplink message from node -> AirInt.
- `air_interface.packet_in_air`
- after airtime
- `collided = air_interface.packet_received`

2 (packet collided)

### Downlink message from gateway -> node

if confirmed messages are requested by a node, the gateway will return a downlink message (dictornary) ith the following key-value pairs:

- "rx_slot"
	1
	2
- "lost"
	True
	False
- "lost_code"
	0 (dc_limit_reached)
	1 (packet too weak < sensitivity)
	


