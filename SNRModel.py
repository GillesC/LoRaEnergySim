import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import requests
import matplotlib.dates as md
import numpy as np
from datetime import datetime
import seaborn as sns
import pandas as pd

sns.set()


class SNRModel:

    def __init__(self):
        r = requests.get("https://dramco.be/api/lora/lora_packets.php")
        rssi = list()
        snr = list()
        for packet in r.json():
            rssi.append(packet['rssi'])
            snr.append(packet['snr'])

        model = LinearRegression(fit_intercept=True)
        rssi = np.round(np.asarray(rssi, dtype=np.float))
        snr = np.round(np.asanyarray(snr, dtype=np.float))
        model.fit(rssi[:, np.newaxis], rssi - snr)

        print("Model slope:    ", model.coef_[0])
        print("Model intercept:", model.intercept_)

        xfit = np.linspace(np.amin(rssi), -10, np.amax(110))
        yfit = model.predict(xfit[:, np.newaxis])

        rssi = roundup(rssi)
        snr = roundup(snr)

        min_rssi = np.amin(rssi)
        max_rssi = np.amax(rssi)

        min_snr = np.amin(snr)
        max_snr = np.amax(snr)

        heatmap = np.zeros(int((max_rssi - min_rssi) / 5), int((max_snr - min_snr) / 5))

        for idx in range(0, len(rssi)):
            rssi_index = (rssi[idx] - min_rssi) / 5
            snr_index = (snr[idx] - min_snr) / 5
            heatmap[rssi_index][snr_index] += 1

        ax = sns.heatmap(heatmap)

        plt.scatter(snr, rssi)
        # plt.scatter(snr_low_rssi, rssi_low)
        # plt.plot(xfit, yfit)
        plt.show()


GRID_SIZE = 2


def roundup(x):
    x = np.divide(x, GRID_SIZE)
    return np.ceil(x).astype(int) * GRID_SIZE


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

rssi_dict = rssi
snr_dict = snr
for key in rssi:
    rssi_list = rssi_dict[key]
    snr_list = snr_dict[key]

    # model = LinearRegression(fit_intercept=True)
    rssi_list = np.round(np.asarray(rssi_list, dtype=np.float))
    snr_list = np.round(np.asanyarray(snr_list, dtype=np.float))
    # model.fit(rssi[:, np.newaxis], rssi - snr)

    # print("Model slope:    ", model.coef_[0])
    # print("Model intercept:", model.intercept_)

    # xfit = np.linspace(np.amin(rssi), -10, np.amax(110))
    # yfit = model.predict(xfit[:, np.newaxis])

    rssi = roundup(rssi_list)
    snr = roundup(snr_list)

    min_rssi = np.amin(rssi)
    max_rssi = np.amax(rssi)

    min_snr = np.amin(snr)
    max_snr = np.amax(snr)

    num_rssi_values = np.abs(max_rssi - min_rssi) / GRID_SIZE + 1
    num_snr_values = np.abs(max_snr - min_snr) / GRID_SIZE + 1

    heatmap = np.zeros((int(num_rssi_values), int(num_snr_values)))

    for idx in range(0, len(rssi) - 1):
        rssi_index = int((max_rssi - rssi[idx]) / GRID_SIZE)
        snr_index = int((snr[idx] - min_snr) / GRID_SIZE)
        heatmap[rssi_index][snr_index] += 1

    yticks = np.arange(max_rssi, min_rssi - GRID_SIZE, -GRID_SIZE)
    xticks = np.arange(min_snr, max_snr + GRID_SIZE, GRID_SIZE)
    df = pd.DataFrame(heatmap, columns=xticks, index=yticks)
    ax = sns.heatmap(df)
    ax.set_title(key)
    ax.set_xlabel('SNR [dB]')
    ax.set_ylabel('RSSI [dBm]')

    plt.show()


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
        noise.append(float(p['rssi'])-float(p['snr']))
    t = md.date2num(t)
    plt.plot(t, rssi, label='RSSI [dBm]')
    plt.plot(t, snr, label='SNR [dB]')
    plt.plot(t, noise, label='Noise [dBm]')
    plt.legend()
    plt.title(device_id)
    plt.show()

    # sns.jointplot(snr, rssi, kind="reg")

    # plt.scatter(snr, rssi)
    # plt.scatter(snr_low_rssi, rssi_low)
    # plt.plot(xfit, yfit)
    # plt.show()
