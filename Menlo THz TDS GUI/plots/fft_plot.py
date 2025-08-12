from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.fft import fft, fftfreq
import numpy as np


class FFTPlot(QWidget):
    def __init__(self, model):
        super().__init__()
        self.model = model
        layout = QVBoxLayout(self)

        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.use_log = True

    def set_log_scale(self, log_scale):
        self.use_log = log_scale
        self.update_plot()

    def update_plot(self):
        t, E_ref, E_sam = self.model.get_windowed_signals()
        if t is None: return

        N = len(t)
        dt = (t[1] - t[0]) * 1e-12
        f = fftfreq(N, dt)[:N // 2] * 1e-12  # THz

        FFT_ref = np.abs(fft(E_ref))[:N // 2]
        FFT_sam = np.abs(fft(E_sam))[:N // 2]

        self.model.fft_results["freq"] = f
        self.model.fft_results["FFT_ref"] = FFT_ref
        self.model.fft_results["FFT_sam"] = FFT_sam

        mask = self.model.get_freq_mask(f)
        f = f[mask]
        FFT_ref = FFT_ref[mask]
        FFT_sam = FFT_sam[mask]

        self.ax.clear()
        if self.use_log:
            y_ref = 10*np.log10(FFT_ref / max(FFT_ref))
            y_sam = 10*np.log10(FFT_sam / max(FFT_ref))
            yLabelStr = "Spectral amplitude (dB)"
        else:
            y_ref = FFT_ref / max(FFT_ref)
            y_sam = FFT_sam / max(FFT_ref)
            yLabelStr = "Spectral amplitude (a.u.)"

        self.ax.plot(f, y_ref, color='blue', label='Ref (FFT)', linewidth=1)
        self.ax.plot(f, y_sam, color='red', label='Sam (FFT)', linewidth=1)
        self.ax.set_xlabel("Frequency (THz)")
        self.ax.set_ylabel(yLabelStr)
        self.ax.grid(True)
        self.ax.legend()
        self.canvas.draw()
