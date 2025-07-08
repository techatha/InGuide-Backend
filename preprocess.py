import pandas as pd
import numpy as np
from scipy.spatial.transform import Rotation as R
from scipy.fft import fft, fftfreq


def rotate_accelerometer_to_world_frame(sensor_df):
    acc_data = sensor_df[['acc_x', 'acc_y', 'acc_z']].copy()
    acc_gravity = sensor_df[['acc_gx', 'acc_gy', 'acc_gz']].copy()
    orientation = sensor_df[['gyro_x', 'gyro_y', 'gyro_z']].copy()  # temporary

    columns = ['acc_x', 'acc_y', 'acc_z', 'acc_gx', 'acc_gy', 'acc_gz', 'mean_magnitude']
    result_df = pd.DataFrame(columns=columns)

    for acc, acc_g, ori in zip(acc_data.itertuples(index=False), acc_gravity.itertuples(index=False), orientation.itertuples(index=False)):
        yaw = np.deg2rad(ori.gyro_x)  # was orientation_alpha
        pitch = np.deg2rad(ori.gyro_y)  # was orientation_beta
        roll = np.deg2rad(ori.gyro_z)  # was orientation_gamma

        r = R.from_euler('zyx', [yaw, pitch, roll])
        acc_world = r.apply([acc.acc_x, acc.acc_y, acc.acc_z])
        gravity_world = r.apply([acc_g.acc_gx, acc_g.acc_gy, acc_g.acc_gz])
        mean_magnitude = np.linalg.norm(acc_world)

        result = pd.DataFrame([list(acc_world) + list(gravity_world) + [mean_magnitude]], columns=columns)
        result_df = pd.concat([result_df, result], ignore_index=True)

    return result_df


def compute_frequency_domain(signal, interval):
    N = len(signal)
    fs = 1000 / interval
    frequencies = fftfreq(N, d=1 / fs)
    fft_values = np.abs(fft(signal))

    pos_mask = frequencies > 0
    frequencies = frequencies[pos_mask]
    fft_values = fft_values[pos_mask]

    power = fft_values ** 2
    return np.sum(frequencies * power) / np.sum(power), frequencies[np.argmax(fft_values)]


def preprocess(data, data_interval=500):

    features = [
        'avg_acc_x', 'median_acc_x', 'std_acc_x', 'min_x', 'max_x', 'mean_abs_x',
        'avg_acc_y', 'median_acc_y', 'std_acc_y', 'min_y', 'max_y', 'mean_abs_y',
        'avg_acc_z', 'median_acc_z', 'std_acc_z', 'min_z', 'max_z', 'mean_abs_z',
        'avg_acc_gx', 'avg_acc_gy', 'avg_acc_gz',
        'gyro_z_mean', 'gyro_z_std', 'gyro_z_max', 'gyro_z_min',
        'mean_magnitude', 'signal_magnitude_area',
        'mean_freq_x', 'dominant_freq_x',
        'mean_freq_y', 'dominant_freq_y',
        'mean_freq_z', 'dominant_freq_z',
        'lat_diff', 'lon_diff'
    ]
    result_df = pd.DataFrame(columns=features)

    rotated_df = rotate_accelerometer_to_world_frame(data)

    # accelerometer of this window frame
    mean_acc_x = rotated_df['acc_x'].mean()
    median_acc_x = rotated_df['acc_x'].median()
    std_acc_x = rotated_df['acc_x'].std()
    min_acc_x = rotated_df['acc_x'].min()
    max_acc_x = rotated_df['acc_x'].max()
    mean_abs_x = rotated_df['acc_x'].abs().mean()
    # ------------------------------------
    mean_acc_y = rotated_df['acc_y'].mean()
    median_acc_y = rotated_df['acc_y'].median()
    std_acc_y = rotated_df['acc_y'].std()
    min_acc_y = rotated_df['acc_y'].min()
    max_acc_y = rotated_df['acc_y'].max()
    mean_abs_y = rotated_df['acc_y'].abs().mean()
    # ------------------------------------
    mean_acc_z = rotated_df['acc_z'].mean()
    median_acc_z = rotated_df['acc_z'].median()
    std_acc_z = rotated_df['acc_z'].std()
    min_acc_z = rotated_df['acc_z'].min()
    max_acc_z = rotated_df['acc_z'].max()
    mean_abs_z = rotated_df['acc_z'].abs().mean()

    # accelerometer (including gravity) of this window frame
    mean_acc_gx = rotated_df['acc_gx'].mean()
    mean_acc_gy = rotated_df['acc_gy'].mean()
    mean_acc_gz = rotated_df['acc_gz'].mean()

    # new: gyro_z stats
    gyro_z = data['gyro_z']
    gyro_z_mean = gyro_z.mean()
    gyro_z_std = gyro_z.std()
    gyro_z_max = gyro_z.max()
    gyro_z_min = gyro_z.min()

    # other features
    mean_magnitude = rotated_df['mean_magnitude'].mean()
    signal_magnitude_area = np.sum(np.abs([mean_acc_x, mean_acc_y, mean_acc_z]))
    mean_freq_x, dominant_freq_x = compute_frequency_domain(rotated_df['acc_x'], data_interval)
    mean_freq_y, dominant_freq_y = compute_frequency_domain(rotated_df['acc_y'], data_interval)
    mean_freq_z, dominant_freq_z = compute_frequency_domain(rotated_df['acc_z'], data_interval)

    lats = list(data['gps_lat'])
    lons = list(data['gps_lon'])
    diff_lat = lats[0] - lats[-1]
    diff_lon = lons[0] - lons[-1]

    row = pd.DataFrame([[mean_acc_x, median_acc_x, std_acc_x, min_acc_x, max_acc_x, mean_abs_x,
                         mean_acc_y, median_acc_y, std_acc_y, min_acc_y, max_acc_y, mean_abs_y,
                         mean_acc_z, median_acc_z, std_acc_z, min_acc_z, max_acc_z, mean_abs_z,
                         mean_acc_gx, mean_acc_gy, mean_acc_gz,
                         gyro_z_mean, gyro_z_std, gyro_z_max, gyro_z_min,
                         mean_magnitude, signal_magnitude_area,
                         mean_freq_x, dominant_freq_x,
                         mean_freq_y, dominant_freq_y,
                         mean_freq_z, dominant_freq_z,
                         diff_lat, diff_lon]], columns=features)

    result_df = pd.concat([result_df, row], ignore_index=True)

    return result_df
