from datetime import datetime
import matplotlib.dates as md
import matplotlib.pyplot as plt
import requests
import pandas as pd

import seaborn as sns

req = requests.get("https://dramco.be/api/lora/lora_packets.php")
packet_per_dev = {}
plt.style.use('seaborn-white')
sns.set_context("paper")

# These are the "Tableau 20" colors as RGB.
tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
             (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
             (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
             (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
             (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]

# Scale the RGB values to the [0, 1] range, which is the format matplotlib accepts.
for i in range(len(tableau20)):
    r, g, b = tableau20[i]
    tableau20[i] = (r / 255., g / 255., b / 255.)

df = dict()
for packet in req.json():
    app_id = packet['app_id']
    id = packet['dev_id']

    if app_id == 'lambrechts-experiment':
        if id not in df:
            df[id] = pd.DataFrame(columns=['time', 'rss', 'snr'])
        series = pd.Series({
            'snr': packet['snr'],
            'rss': packet['rssi'],
            'time': datetime.strptime(packet['time_server'], '%Y-%m-%d %H:%M:%S')
        })
        df[id] = df[id].append(series, ignore_index=True)
del req

mpl_fig = plt.figure()
ax = mpl_fig.add_subplot(111)
i = 0
for dev in df:
    data = df[dev]
    ax.plot(data.time, data.snr, label=dev, color=tableau20[i])

    i += 1
plt.gcf().autofmt_xdate()
sns.despine()
plt.legend()
ax.set_title("Lambrechts measurements")
ax.set_xlabel("Time")
ax.set_ylabel("SNR [dBm]")
plt.tight_layout()
plt.show()
