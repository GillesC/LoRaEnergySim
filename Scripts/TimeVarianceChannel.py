from datetime import datetime

import matplotlib.dates as md
import matplotlib.pyplot as plt
import pandas as pd
import requests

r = requests.get("https://dramco.be/api/lora/lora_packets.php")
rss = []
snr = []
t = []

for packet in r.json():
    if packet['dev_id'] == 'sf9-bw125-2dbm-2':
        rss.append(packet['rssi'])
        snr.append(packet['snr'])
        time = datetime.strptime(packet['time_server'], '%Y-%m-%d %H:%M:%S')
        t.append(time)

serie_rss = pd.Series(rss, t)
serie_snr = pd.Series(snr, t)

plt.figure(1)

plt.subplot(4, 1, 1)
plt.plot(t, snr, label='SNR')
plt.legend()
plt.subplot(4, 1, 2)
plt.plot(t, rss, label='RSS')
plt.legend()
plt.subplot(4, 1, 3)
plt.plot(serie_snr.rolling(window=240).mean(), label='SNR')
plt.legend()
plt.subplot(4, 1, 4)
plt.plot(serie_rss.rolling(window=240).mean(), label='RSS')

plt.legend()
plt.show()
