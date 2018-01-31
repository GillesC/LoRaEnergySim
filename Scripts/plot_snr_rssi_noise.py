from datetime import datetime
import matplotlib.dates as md
import matplotlib.pyplot as plt
import requests

r = requests.get("https://dramco.be/api/lora/lora_packets.php")
rssi = {}
snr = {}

packet_per_dev = {}

for packet in r.json():
    dr = packet['data_rate']
    id = packet['dev_id']
    if dr not in rssi:
        rssi[dr] = []
        snr[dr] = []
    if id not in packet_per_dev:
        packet_per_dev[id] = []
    packet_per_dev[id].append(packet)

    rssi[dr].append(packet['rssi'])
    snr[dr].append(packet['snr'])

xfmt = md.DateFormatter('%Y-%m-%d %H:%M:%S')
i = 1

num_of_devices = 0
for device_id, packets in packet_per_dev.items():
    if "sf" in device_id:
        num_of_devices += 1

plt.figure(1)

for device_id, packets in packet_per_dev.items():
    t = []
    rssi = []
    snr = []
    noise = []

    # only show devices with more than 10 packets

    if "sf" in device_id:
        for p in packets:
            time = datetime.strptime(p['time_server'], '%Y-%m-%d %H:%M:%S')
            t.append(time)
            rssi.append(float(p['rssi']))
            snr.append(float(p['snr']))
            noise.append(float(p['rssi']) - float(p['snr']))
        t = md.date2num(t)
        ax = plt.subplot(num_of_devices, 1, i)
        ax.plot(t, rssi, label='RSSI [dBm]')
        ax.plot(t, snr, label='SNR [dB]')
        ax.plot(t, noise, label='Noise [dBm]')
        ax.set_title(device_id)
        i += 1


plt.legend()
plt.show()
