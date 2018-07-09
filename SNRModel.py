#  ____  ____      _    __  __  ____ ___
# |  _ \|  _ \    / \  |  \/  |/ ___/ _ \
# | | | | |_) |  / _ \ | |\/| | |  | | | |
# | |_| |  _ <  / ___ \| |  | | |__| |_| |
# |____/|_| \_\/_/   \_\_|  |_|\____\___/
#                           research group
#                             dramco.be/
#
#  KU Leuven - Technology Campus Gent,
#  Gebroeders De Smetstraat 1,
#  B-9000 Gent, Belgium
#
#      Created: 2018-02-01
#       Author: Gilles Callebaut
#      Version: 0.1
#
#  Description: SNR Model
#      Try to derive a model for SNR behaviour of LoRa signals from measurements
#

import numpy as np


class SNRModel:
    def __init__(self, GRID_SIZE=2):
        # print('request GET')
        # r = requests.get("https://dramco.be/api/lora/lora_packets.php")
        #
        # noise_per_dev = {}
        #
        # print('processing packets')
        # self.packets = r.json()
        # for packet in self.packets:
        #     dev_id = packet['dev_id']
        #     if dev_id not in noise_per_dev:
        #         noise_per_dev[dev_id] = []
        #     noise_per_dev[dev_id].append(float(packet['rssi']) - float(packet['snr']))
        #
        # print('processing noise values')
        # mean_std_values = []
        # mean_mean_values = []
        # for device_id, noise_values in noise_per_dev.items():
        #     noise_values = np.asarray(noise_values, dtype=np.float)
        #     std_noise = np.std(noise_values,
        #                        ddof=1)  # for ddof see https://stackoverflow.com/questions/27600207/why-does-numpy-std-give-a-different-result-to-matlab-std
        #     mean_noise = np.mean(noise_values)
        #     if std_noise >= 0:
        #         mean_std_values.append(std_noise)
        #         mean_mean_values.append(mean_noise)
        #     print('Device {}\t mean: {} and std: {} (num of values: {})'.format(device_id, mean_noise, std_noise,
        #                                                                         np.size(noise_values)))
        #
        # mean_std_values = np.mean(mean_std_values)
        # mean_mean_values = np.mean(mean_mean_values)
        # print('Mean mean value:{} std value: {}'.format(mean_mean_values, mean_std_values))
        self.noise = -80  # mean_mean_values
        self.std_noise = 6  # mean_std_values
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

        # noise floor according to https://www.semtech.com/uploads/documents/an1200.22.pdf
        self.noise_floor = -174 + 10 * np.log10(125e3)

    def rss_to_snr(self, rss: float):
        # TODO make a better noise assumptionS

        return rss - self.noise_floor


def roundup(x, GRID_SIZE):
    x = np.divide(x, GRID_SIZE)
    return np.ceil(x).astype(int) * GRID_SIZE
