import datetime

import requests
import matplotlib.dates as md
import matplotlib.pyplot as plt


#TODO

print('request GET')
r = requests.get("https://dramco.be/api/lora/lora_packets.php")

noise_per_dev = {}

print('processing packets')
packets = r.json()
for packet in packets:
    dev_id = packet['dev_id']
    if dev_id not in noise_per_dev:
        noise_per_dev[dev_id] = []
    noise_per_dev[dev_id].append(float(packet['rssi']) - float(packet['snr']))


xfmt = md.DateFormatter('%Y-%m-%d %H:%M:%S')
for device_id, packets in packet_per_dev.items():
    t = []
    rssi = []
    snr = []
    noise = []

    ax = plt.gca()

    for p in packets:
        time = datetime.strptime(p['time_server'], '%Y-%m-%d %H:%M:%S')
        t.append(time)
        rssi.append(float(p['rssi']))
        snr.append(float(p['snr']))
        noise.append(float(p['rssi']) - float(p['snr']))
    t = md.date2num(t)
    plt.plot(t, rssi, label='RSSI [dBm]')
    plt.plot(t, snr, label='SNR [dB]')
    plt.plot(t, noise, label='Noise [dBm]')
    plt.legend()
    plt.title(device_id)
    plt.show()