from PyQt6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QLabel, QDialog
from PyQt6.QtCore import Qt, QSize
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec

class ResultsWindow(QWidget):
    def __init__(self, freq, n, kappa, alpha, thickness, fmin, fmax, parent=None):
        super().__init__(parent)
        #self.setWindowTitle("Extracted Parameters")
        #self.setMinimumSize(900, 500)

        # Create title label (centered)
        title_label = QLabel(f"<h2>Thickness d = {thickness:.1f} µm</h2>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        fig = Figure(figsize=(16, 4))
        canvas = FigureCanvas(fig)
        #toolbar = NavigationToolbar(canvas, self)
        #toolbar.setIconSize(QSize(16, 16))

        gs = GridSpec(1, 3, figure = fig, wspace = 0.3, width_ratios = [1, 1, 1])
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[0, 1])
        ax3 = fig.add_subplot(gs[0, 2])
        fig.subplots_adjust(
            left = 0.05,
            right = 0.95,
            bottom = 0.15
        )

        lw = 1.5
        ax1.plot(freq, n, color='blue', linewidth=lw)
        ax1.set_title("Refractive Index, n", fontsize=12, fontweight='bold')

        ax2.plot(freq, kappa, color='red', linewidth=lw)
        ax2.set_title("Extinction coefficient, κ", fontsize=12, fontweight='bold')

        ax3.plot(freq, alpha, color='green', linewidth=lw)
        ax3.set_title("Attenuation Coefficient [cm⁻¹]", fontsize=12, fontweight='bold')

        for ax in [ax1, ax2, ax3]:
            ax.set_xlim(fmin, fmax)
            ax.grid(True)
            ax.set_xlabel("Frequency (THz)", fontsize=10, fontweight='bold')
            ax.tick_params(axis='both', labelsize=10)

        # Layouts
        main_layout = QVBoxLayout()
        main_layout.addWidget(title_label)
        #main_layout.addWidget(toolbar)
        main_layout.addWidget(canvas)

        self.setLayout(main_layout)
