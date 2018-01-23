from datetime import datetime
import matplotlib.dates as md
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns

sns.set()


class SNRModel:
    def __init__(self, GRID_SIZE=2):
        self.noise = -100  # dBm
        rssi = {}
        # r = requests.get("https://dramco.be/api/lora/lora_packets.php")
        # rssi = {}
        # snr = {}
        #
        # packet_per_dev = {}
        #
        # for packet in r.json():
        #     dr = packet['data_rate']
        #     id = packet['dev_id']
        #     if dr not in rssi:
        #         rssi[dr] = []
        #         snr[dr] = []
        #     if id not in packet_per_dev:
        #         packet_per_dev[id] = []
        #     packet_per_dev[id].append(packet)
        #
        #     rssi[dr].append(packet['rssi'])
        #     snr[dr].append(packet['snr'])
        #
        # rssi_dict = rssi
        # snr_dict = snr
        # for key in rssi:
        #     rssi_list = rssi_dict[key]
        #     snr_list = snr_dict[key]
        #
        #     # model = LinearRegression(fit_intercept=True)
        #     rssi_list = np.round(np.asarray(rssi_list, dtype=np.float))
        #     snr_list = np.round(np.asanyarray(snr_list, dtype=np.float))
        #     # model.fit(rssi[:, np.newaxis], rssi - snr)
        #
        #     # print("Model slope:    ", model.coef_[0])
        #     # print("Model intercept:", model.intercept_)
        #
        #     # xfit = np.linspace(np.amin(rssi), -10, np.amax(110))
        #     # yfit = model.predict(xfit[:, np.newaxis])
        #
        #     rssi = roundup(rssi_list, GRID_SIZE)
        #     snr = roundup(snr_list, GRID_SIZE)
        #
        #     min_rssi = np.amin(rssi)
        #     max_rssi = np.amax(rssi)
        #
        #     min_snr = np.amin(snr)
        #     max_snr = np.amax(snr)
        #
        #     num_rssi_values = np.abs(max_rssi - min_rssi) / GRID_SIZE + 1
        #     num_snr_values = np.abs(max_snr - min_snr) / GRID_SIZE + 1
        #
        #     heatmap = np.zeros((int(num_rssi_values), int(num_snr_values)))
        #
        #     for idx in range(0, len(rssi) - 1):
        #         rssi_index = int((max_rssi - rssi[idx]) / GRID_SIZE)
        #         snr_index = int((snr[idx] - min_snr) / GRID_SIZE)
        #         heatmap[rssi_index][snr_index] += 1
        #
        #     yticks = np.arange(max_rssi, min_rssi - GRID_SIZE, -GRID_SIZE)
        #     xticks = np.arange(min_snr, max_snr + GRID_SIZE, GRID_SIZE)
        #     df = pd.DataFrame(heatmap, columns=xticks, index=yticks)
        #     ax = sns.heatmap(df)
        #     ax.set_title(key)
        #     ax.set_xlabel('SNR [dB]')
        #     ax.set_ylabel('RSSI [dBm]')
        #
        #     plt.show()
        #
        # xfmt = md.DateFormatter('%Y-%m-%d %H:%M:%S')
        # for device_id, packets in packet_per_dev.items():
        #     t = []
        #     rssi = []
        #     snr = []
        #     noise = []
        #
        #     ax = plt.gca()
        #
        #     for p in packets:
        #         time = datetime.strptime(p['time_server'], '%Y-%m-%d %H:%M:%S')
        #         t.append(time)
        #         rssi.append(float(p['rssi']))
        #         snr.append(float(p['snr']))
        #         noise.append(float(p['rssi']) - float(p['snr']))
        #     t = md.date2num(t)
        #     plt.plot(t, rssi, label='RSSI [dBm]')
        #     plt.plot(t, snr, label='SNR [dB]')
        #     plt.plot(t, noise, label='Noise [dBm]')
        #     plt.legend()
        #     plt.title(device_id)
        #     # plt.show()

    def rss_to_snr(self, rss: float):
        # TODO make a better noise assummption
        return rss - self.noise - np.random.randint(0, 10)


def roundup(x, GRID_SIZE):
    x = np.divide(x, GRID_SIZE)
    return np.ceil(x).astype(int) * GRID_SIZE
