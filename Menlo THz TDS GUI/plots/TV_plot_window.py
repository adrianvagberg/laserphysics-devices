from PyQt6.QtWidgets import QDialog, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


class TotalVariationPlot(QDialog):
    def __init__(self, thickness_array, tv_array, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Total Variation vs. Thickness")
        self.setMinimumSize(600, 400)

        # Normalize TV
        tv_norm = tv_array / np.max(tv_array)
        optimal_idx = np.argmin(tv_norm)
        optimal_thickness = thickness_array[optimal_idx]
        optimal_value = tv_norm[optimal_idx]

        mask = tv_norm != optimal_value

        # Create the figure
        fig = Figure(figsize=(6, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.scatter(thickness_array[mask], tv_norm[mask], color='black', label='Normalized Total Variation')
        ax.scatter([optimal_thickness], [optimal_value],
                   color='red', marker='*', s=150, label=f'Optimal = {optimal_thickness:.2f} µm')
        ax.set_xlabel("Thickness (µm)", fontsize=10, fontweight='bold')
        ax.set_ylabel("Normalized Total Variation", fontsize=10, fontweight='bold')
        ax.set_title("Thickness Optimization", fontsize=12, fontweight='bold')
        ax.tick_params(axis='both', labelsize=12)
        ax.legend()
        fig.tight_layout()

        layout = QVBoxLayout()
        layout.addWidget(canvas)
        self.setLayout(layout)
