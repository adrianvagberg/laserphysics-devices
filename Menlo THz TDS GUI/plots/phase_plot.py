from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.fft import fft, fftfreq
import numpy as np
from processing import utils

class PhasePlot(QWidget):
    def __init__(self, model):
        super().__init__()
        self.model = model
        layout = QVBoxLayout(self)

        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        #self.unwrap_button = QPushButton("Unwrap Phase")
        #layout.addWidget(self.unwrap_button)
        #self.unwrap_button.clicked.connect(self.unwrap)

        self.unwrap = False

    def update_plot(self):
        t, E_ref, E_sam = self.model.get_windowed_signals()
        if t is None: return

        #N = len(t)
        #dt = (t[1] - t[0]) * 1e-12
        #f = fftfreq(N, dt)[:N // 2] * 1e-12
        #H = fft(E_sam) / fft(E_ref)
        f, H, phase_wrapped = utils.compute_transfer_function(t, E_ref, E_sam)
        #phase_wrapped = np.angle(H[:N // 2])

        self.model.phase_wrapped = phase_wrapped
        self.model.phase_unwrapped = np.unwrap(phase_wrapped)
        self.model.fft_results["phi_unwrapped"] = self.model.phase_unwrapped

        if self.unwrap:
            phi = self.model.phase_unwrapped
            labelTxt = 'Unwrapped phase'
        else:
            phi = self.model.phase_wrapped
            labelTxt = 'Wrapped phase'

        mask = self.model.get_freq_mask(f)
        f = f[mask]
        phi = phi[mask]

        self.ax.clear()
        self.ax.plot(f, phi, color='black', label=labelTxt, linewidth=1)
        self.ax.set_xlabel("Frequency (THz)")
        self.ax.set_ylabel("FFT Phase Difference (rad)")
        self.ax.grid(True)
        self.canvas.draw()

    def set_unwrap(self, unwrap):
        self.unwrap = unwrap
        self.update_plot()

    #def unwrap(self):
    #    if self.model.phase_wrapped is None: return
    #    phase_unwrapped = np.unwrap(self.model.phase_wrapped)
    #    self.model.phase_unwrapped = phase_unwrapped
    #
    #    t, E_ref, E_sam = self.model.get_windowed_signals()
    #    N = len(t)
    #    dt = (t[1] - t[0]) * 1e-12
    #    f = fftfreq(N, dt)[:N // 2] * 1e-12
    #
    #    self.ax.clear()
    #    self.ax.plot(f, phase_unwrapped, label='Unwrapped Phase', linewidth=1)
    #    self.ax.set_xlabel("Frequency (THz)")
    #    self.ax.set_ylabel("Phase (rad)")
    #    self.ax.legend()
    #    self.canvas.draw()
