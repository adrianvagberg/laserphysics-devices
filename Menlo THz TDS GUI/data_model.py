import numpy as np
from scipy.fft import fft, fftfreq


class THzDataModel:
    def __init__(self):
        self.time = None
        self.E_ref = None
        self.E_sam = None

        self.trunc_time_ps = None
        self.trunc_mask = None

        self.phase_wrapped = None
        self.phase_unwrapped = None

        self.freq = None
        self.freq_min = None
        self.freq_max = None

        self.fft_results = {
            "freq": None,
            "FFT_ref": None,
            "FFT_sam": None,
            "phi_unwrapped": None
        }

    def set_data(self, time, E_ref, E_sam):
        self.time = time
        self.E_ref = E_ref
        self.E_sam = E_sam
        self.set_freq(self.time)
        self.set_freq_bounds(min(self.freq), max(self.freq))

        if self.trunc_time_ps is None:
            # Default to full signal range
            self.trunc_time_ps = time[-1]

        self.update_truncation(self.trunc_time_ps)

    def set_freq(self, t):
        N = len(t)
        dt = (t[1] - t[0]) * 1e-12
        self.freq = fftfreq(N, dt)[:N // 2] * 1e-12

    def get_freq(self):
        return self.freq

    def set_freq_bounds(self, fmin, fmax):
        self.freq_min = fmin
        self.freq_max = fmax

    def get_freq_mask(self, freq):
        if self.freq_min is None or self.freq_max is None:
            return np.ones_like(freq, dtype=bool)
        return (freq >= self.freq_min) & (freq <= self.freq_max)

    def update_truncation(self, trunc_time_ps):
        self.trunc_time_ps = trunc_time_ps
        if self.time is not None and trunc_time_ps is not None:
            self.trunc_mask = self.time <= trunc_time_ps
        self.set_freq(self.time[self.trunc_mask])

    def get_truncated_signals(self):
        if self.trunc_mask is None or self.trunc_time_ps is None:
            return None, None, None
        return self.time[self.trunc_mask], self.E_ref[self.trunc_mask], self.E_sam[self.trunc_mask]

    def get_windowed_signals(self):
        t, E_ref, E_sam = self.get_truncated_signals()
        if t is None:
            return None, None, None
        N = len(t)
        edge_percent = 0.05
        n_taper = int(N * edge_percent)
        n_taper = min(n_taper, N // 4)

        rise = np.blackman(2 * n_taper)[:n_taper]
        fall = np.blackman(2 * n_taper)[n_taper:]
        flat = np.ones(N - 2 * n_taper)
        window = np.concatenate([rise, flat, fall])

        return t, E_ref * window, E_sam * window
