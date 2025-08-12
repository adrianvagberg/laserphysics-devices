from datetime import datetime, date

from PyQt6.QtWidgets import (
    QMainWindow,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QWidget,
    QLabel,
    QCheckBox,
    QMessageBox,
    QDoubleSpinBox,
    QTabWidget,
    QComboBox,
    QTextEdit,
    QFormLayout,
    QProgressBar,
    QStackedLayout,
    QFrame
)
from PyQt6.QtCore import QLocale, QSize, Qt
from PyQt6.QtGui import QIntValidator, QTextOption
from data_model import THzDataModel
from plots.results_window import ResultsWindow
from plots.time_plot import TimeDomainPlot
from plots.fft_plot import FFTPlot
from plots.phase_plot import PhasePlot
from plots.TV_plot_window import TotalVariationPlot
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
from processing import utils, extraction
from processing.extraction import optimize_thickness, extract_analytical, extract_numerical


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("THz TDS GUI")
        self.resize(1400, 900)

        self.model = THzDataModel()

        # --- Initialize plots ---
        self.time_plot = TimeDomainPlot(self.model)
        self.time_plot.truncation_changed.connect(self.on_truncation_changed)
        self.time_toolbar = NavigationToolbar(self.time_plot.canvas, self)
        self.time_toolbar.setIconSize(QSize(16, 16))

        self.log_fft_checkbox = QCheckBox("Log scale")
        self.log_fft_checkbox.setChecked(True)
        self.log_fft_checkbox.stateChanged.connect(self.on_toggle_fft_log)
        self.fft_plot = FFTPlot(self.model)
        self.fft_toolbar = NavigationToolbar(self.fft_plot.canvas, self)
        self.fft_toolbar.setIconSize(QSize(16, 16))

        self.phase_plot = PhasePlot(self.model)
        self.phase_toolbar = NavigationToolbar(self.phase_plot.canvas, self)
        self.phase_toolbar.setIconSize(QSize(16, 16))
        self.unwrap_checkbox = QCheckBox("Unwrap Phase")
        self.unwrap_checkbox.setChecked(False)
        self.unwrap_checkbox.stateChanged.connect(self.on_toggle_unwrap)

        # --- Data input ---
        btn_height = 50
        self.load_data_btn = QPushButton("Load Data")
        self.load_data_btn.clicked.connect(self.load_data_files)
        #self.load_data_btn.setStyleSheet(self.btn_style)
        self.load_data_btn.setMinimumHeight(btn_height)
        font = self.load_data_btn.font()
        font.setPointSize(12)
        self.load_data_btn.setFont(font)

        # --- Save data ---
        self.save_params_btn = QPushButton("Save Material Parameters")
        self.save_params_btn.setEnabled(False)
        self.save_params_btn.clicked.connect(self.save_material_parameters)
        #self.save_params_btn.setStyleSheet(self.btn_style)
        self.save_params_btn.setMinimumHeight(btn_height)
        self.save_params_btn.setFont(font)

        self.save_fft_btn = QPushButton("Save FFT Data")
        self.save_fft_btn.setEnabled(False)
        self.save_fft_btn.clicked.connect(self.save_fft_data)
        #self.save_fft_btn.setStyleSheet(self.btn_style)
        self.save_fft_btn.setMinimumHeight(btn_height)
        self.save_fft_btn.setFont(font)

        # --- Parameter extraction buttons ---
        self.extract_btn = QPushButton("Extract Parameters")
        self.extract_btn.clicked.connect(self.on_extract_button_clicked)
        self.extract_btn.setMinimumHeight(btn_height)
        self.extract_btn.setFont(font)

        self.extract_progress = QProgressBar()
        self.extract_progress.setRange(0, 100)
        self.extract_progress.setValue(0)
        self.extract_progress.setTextVisible(False)
        self.extract_progress.setFormat("Extract Parameters")
        self.extract_progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.extract_progress.setStyleSheet("""
                    QProgressBar {
                        border: none;
                        border-radius: 4px;
                        background-color: transparent;
                        text-align: center;
                    }
                    QProgressBar::chunk {
                        background-color: rgba(0, 180, 0, 0.5);
                        border-radius: 4px;
                        margin: 2px;
                    }
                """)
        self.extract_progress.setFont(font)
        self.extract_progress.setMinimumHeight(btn_height)
        self.extract_progress.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.extract_stack = QStackedLayout()
        self.extract_stack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        self.extract_stack.addWidget(self.extract_btn)
        self.extract_stack.addWidget(self.extract_progress)

        # Create a frame to host the stacked layout
        self.extract_frame = QFrame()
        self.extract_frame.setLayout(self.extract_stack)

        # --- Frequency ROI ---
        self.freq_min_input = QDoubleSpinBox()
        self.freq_max_input = QDoubleSpinBox()
        for spinbox in (self.freq_min_input, self.freq_max_input):
            spinbox.setDecimals(2)
            spinbox.setSingleStep(0.1)  # Step size when clicking arrows
            spinbox.setRange(0.0, 15.0)  # Or something suitable for your THz range
            spinbox.setMaximumWidth(100)
            spinbox.valueChanged.connect(self.on_freq_bounds_changed)

        ## LAYOUT GENERATION ##
        layout = QGridLayout()

        ## Control panel ##
        controls_layout = QHBoxLayout()

        # -- Left side --#
        left_controls = QVBoxLayout()
        left_controls.addWidget(self.load_data_btn)
        left_controls.addWidget(self.save_fft_btn)
        left_controls.addWidget(self.extract_frame)
        left_controls.addWidget(self.save_params_btn)
        left_controls.addWidget(QLabel("Reference File:"))
        self.ref_path_field = QTextEdit()
        self.ref_path_field.setReadOnly(True)
        self.ref_path_field.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        self.ref_path_field.setMinimumHeight(40)
        left_controls.addWidget(self.ref_path_field)

        left_controls.addWidget(QLabel("Sample File:"))
        self.sam_path_field = QTextEdit()
        self.sam_path_field.setReadOnly(True)
        self.sam_path_field.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        self.sam_path_field.setMinimumHeight(40)
        left_controls.addWidget(self.sam_path_field)

        left_widget = QWidget()
        left_widget.setLayout(left_controls)

        # -- Right side --#
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("QTabWidget::pane { border: 1px solid black; }")

        # Create tab for "Extraction Settings"
        self.extraction_tab = QWidget()
        extraction_layout = QVBoxLayout()
        self.method_widget = QWidget()
        method_form = QFormLayout()
        self.method_selector = QComboBox()
        self.method_selector.addItems(["Analytical", "Numerical"])
        self.method_selector.currentTextChanged.connect(self.update_method_ui)
        method_form.addRow(QLabel("Extraction Method:"), self.method_selector)
        extraction_layout.addLayout(method_form)

        #extraction_layout.addWidget(QLabel("Extraction Method:"))
        #extraction_layout.addWidget(self.method_selector)

        # Frequency ROI
        extraction_layout.addWidget(QLabel("Frequency Range (THz):"))
        freq_bounds_layout = QHBoxLayout()
        freq_bounds_layout.addWidget(self.freq_min_input)
        freq_bounds_layout.addWidget(QLabel("–"))
        freq_bounds_layout.addWidget(self.freq_max_input)
        freq_bounds_layout.addStretch()
        extraction_layout.addLayout(freq_bounds_layout)

        # Additional fields for numerical extraction
        self.n_input = QDoubleSpinBox()
        self.kappa_input = QDoubleSpinBox()
        self.tolerance_input = QDoubleSpinBox()
        self.step_input = QDoubleSpinBox()
        self.span_input = QDoubleSpinBox()
        for sb in [self.n_input, self.kappa_input, self.tolerance_input, self.step_input, self.span_input]:
            sb.setDecimals(2)
            sb.setRange(0.0, 100.0)
            sb.setSingleStep(0.1)
            sb.setMaximumWidth(100)

        self.tolerance_input.setValue(1)
        self.step_input.setValue(0.5)
        self.span_input.setValue(5.0)

        self.thickness_input = QDoubleSpinBox()
        self.thickness_input.setDecimals(1)
        self.thickness_input.setSingleStep(1)
        self.thickness_input.setRange(0, 10000)

        self.thickness_fields = QWidget()
        thickness_form = QFormLayout()
        thickness_form.addRow(QLabel("Sample Thickness (µm):"), self.thickness_input)
        self.thickness_fields.setLayout(thickness_form)
        extraction_layout.addWidget(self.thickness_fields)

        self.numerical_fields = QWidget()
        numerical_form = QFormLayout()

        numerical_form.addRow(QLabel("Thickness Step (µm):"), self.step_input)
        numerical_form.addRow(QLabel("Thickness Span (± µm):"), self.span_input)
        numerical_form.addRow(QLabel("Initial n guess:"), self.n_input)
        numerical_form.addRow(QLabel("Initial κ guess:"), self.kappa_input)
        numerical_form.addRow(QLabel("Search bounds tolerance:"), self.tolerance_input)

        self.numerical_fields.setLayout(numerical_form)
        self.numerical_fields.setVisible(False)
        extraction_layout.addWidget(self.numerical_fields)

        us_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        for spinbox in [
            self.n_input,
            self.kappa_input,
            self.tolerance_input,
            self.step_input,
            self.span_input,
            self.freq_min_input,
            self.freq_max_input,
            self.thickness_input
        ]:
            spinbox.valueChanged.connect(self.validate_inputs)
            spinbox.setLocale(us_locale)

        self.extraction_tab.setLayout(extraction_layout)
        self.tab_widget.addTab(self.extraction_tab, "Extraction Settings")

        self.thickness_input.valueChanged.connect(self.validate_inputs)

        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.tab_widget)
        right_layout.addStretch()
        #right_layout.addWidget(self.extract_btn)
        right_widget.setLayout(right_layout)

        controls_layout.addWidget(left_widget)
        controls_layout.addWidget(right_widget)

        controls_widget = QWidget()
        controls_widget.setLayout(controls_layout)
        controls_layout.setStretch(0, 1)
        controls_layout.setStretch(1, 1)

        time_domain_layout = QVBoxLayout()
        time_domain_layout.addWidget(self.time_toolbar)
        time_domain_layout.addWidget(self.time_plot)

        row1_widget = QWidget()
        row1_layout = QHBoxLayout(row1_widget)
        row1_layout.addWidget(controls_widget)
        row1_layout.addLayout(time_domain_layout)
        row1_layout.setStretch(0,1)
        row1_layout.setStretch(1,1)

        layout.addWidget(row1_widget, 1, 0, 1, 2)
        row1_widget.setFixedHeight(430)

        phase_toolbar_row = QWidget()
        phase_toolbar_layout = QHBoxLayout(phase_toolbar_row)
        phase_toolbar_layout.addWidget(self.unwrap_checkbox)
        phase_toolbar_layout.addWidget(self.phase_toolbar)

        fft_toolbar_row = QWidget()
        fft_toolbar_layout = QHBoxLayout(fft_toolbar_row)
        fft_toolbar_layout.addWidget(self.log_fft_checkbox)
        fft_toolbar_layout.addWidget(self.fft_toolbar)

        fft_toolbar_layout.setContentsMargins(15, 15, 15, 0)
        phase_toolbar_layout.setContentsMargins(15, 15, 15, 0)
        self.fft_plot.setContentsMargins(0, 0, 0, 15)
        self.phase_plot.setContentsMargins(0, 0, 0, 15)

        #layout.addWidget(fft_toolbar_row, 2, 0)
        #layout.addWidget(self.fft_plot, 3, 0)

        #layout.addWidget(phase_toolbar_row, 2, 1)
        #layout.addWidget(self.phase_plot, 3, 1)

        self.bottom_tabs = QTabWidget()
        # --- Tab 1: FFT Plots ---
        fft_tab = QWidget()
        fft_layout = QGridLayout()

        fft_layout.addWidget(fft_toolbar_row, 0, 0)
        fft_layout.addWidget(self.fft_plot, 1, 0)
        fft_layout.addWidget(phase_toolbar_row, 0, 1)
        fft_layout.addWidget(self.phase_plot, 1, 1)

        fft_tab.setLayout(fft_layout)
        self.bottom_tabs.addTab(fft_tab, "FFT Plots")

        # --- Placeholder for Results Tab ---
        self.results_tab = QWidget()  # Will get content dynamically
        self.bottom_tabs.addTab(self.results_tab, "Material Parameters")
        self.bottom_tabs.setTabEnabled(1, False)  # Disable until ready

        layout.addWidget(self.bottom_tabs, 2, 0, 1, 2)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.initialize_plots()

    def initialize_plots(self):
        self.time_plot.ax.set_xlabel("Time (ps)")
        self.time_plot.ax.set_ylabel("Amplitude (V)")
        self.fft_plot.ax.set_xlabel("Frequency (THz)")
        self.fft_plot.ax.set_ylabel("Amplitude")
        self.phase_plot.ax.set_xlabel("Frequency (THz)")
        self.phase_plot.ax.set_ylabel("FFT Phase Difference (rad)")

        for plot in [self.time_plot, self.fft_plot, self.phase_plot]:
            plot.ax.grid(True)
            plot.fig.subplots_adjust(bottom=0.15)

    def load_data_files(self):
        # First: load reference
        ref_path, _ = QFileDialog.getOpenFileName(
            self, "Select Reference File", "", "Text Files (*.txt *.dat *.csv)"
        )
        if not ref_path:
            return  # Cancelled

        # Then: load sample
        sam_path, _ = QFileDialog.getOpenFileName(
            self, "Select Sample File", "", "Text Files (*.txt *.dat *.csv)"
        )
        if not sam_path:
            return  # Cancelled

        # Load data
        ref_data = np.loadtxt(ref_path)
        sam_data = np.loadtxt(sam_path)

        # Set file paths in UI
        self.ref_path_field.setText(ref_path)
        self.sam_path_field.setText(sam_path)

        # Assume time is first column, E-field is second
        time = ref_data[:, 0]
        E_ref = ref_data[:, 1]
        E_sam = sam_data[:, 1]

        # Send to model
        self.model.set_data(time, E_ref, E_sam)

        # Update plots
        self.time_plot.update_plot()
        self.fft_plot.update_plot()
        self.phase_plot.update_plot()

        self.validate_inputs()
        self.save_fft_btn.setEnabled(True)

    def try_update(self):
        if self.model.E_ref is not None and self.model.E_sam is not None:
            self.model.set_data(self.model.time, self.model.E_ref, self.model.E_sam)
            self.time_plot.update_plot()
            self.fft_plot.update_plot()
            self.phase_plot.update_plot()

    def on_truncation_changed(self):
        self.model.update_truncation(self.model.trunc_time_ps)
        self.fft_plot.update_plot()
        self.phase_plot.update_plot()

    def on_toggle_unwrap(self, state):
        self.phase_plot.set_unwrap(self.unwrap_checkbox.isChecked())

    def on_toggle_fft_log(self, state):
        self.fft_plot.set_log_scale(self.log_fft_checkbox.isChecked())

    def on_freq_bounds_changed(self):
        fmin = self.freq_min_input.value()
        fmax = self.freq_max_input.value()
        if fmin >= fmax:
            return
        self.model.set_freq_bounds(fmin, fmax)
        self.fft_plot.update_plot()
        self.phase_plot.update_plot()

    def update_method_ui(self):
        is_numerical = self.method_selector.currentText() == "Numerical"
        self.numerical_fields.setVisible(is_numerical)
        self.validate_inputs()

    def validate_inputs(self):
        valid = bool(self.thickness_input.value()) and \
                self.freq_min_input.value() < self.freq_max_input.value() and \
                self.model.E_ref is not None and self.model.E_sam is not None

        if self.method_selector.currentText() == "Numerical":
            valid = valid and all([
                self.n_input.value() > 0,
                self.kappa_input.value() >= 0,
                self.tolerance_input.value() > 0,
                self.step_input.value() > 0,
                self.span_input.value() > 0
            ])
        self.extract_btn.setEnabled(valid)

    def on_extract_button_clicked(self):
        self.extract_btn.clearFocus()
        method = self.method_selector.currentText().lower()
        self.extract_parameters(method=method)

    def extract_parameters(self, method="analytical"):
        # Validate inputs
        try:
            thickness_um = float(self.thickness_input.text())
            thickness_m = thickness_um * 1e-6  # Convert to meters
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid sample thickness in µm.")
            return

        if not self.check_data_is_loaded():
            return

        # Perform FFT
        t, E_ref, E_sam = self.model.get_truncated_signals()
        freq, H, phi_wrapped = utils.compute_transfer_function(
            t, E_ref, E_sam
        )

        phi_unwrapped = np.unwrap(phi_wrapped)

        mask = self.model.get_freq_mask(freq)
        freq = freq[mask]
        H = H[mask]
        phi_unwrapped = phi_unwrapped[mask]

        if method == "analytical":
            # Extract parameters
            result = extract_analytical(freq, np.abs(H), phi_unwrapped, thickness_m)
            n = result["n"]
            kappa = result["kappa"]
            alpha = result["alpha"]
            d = thickness_m * 1e6
        else:
            self.extract_btn.setEnabled(False)
            self.extract_progress.setValue(0)
            self.extract_progress.setVisible(True)

            def update_progress(value):
                self.extract_progress.setValue(value)

            nk_guess = [self.n_input.value(), self.kappa_input.value()]
            tolerance = self.tolerance_input.value()
            step = self.step_input.value()
            span = self.span_input.value()
            #result = extract_numerical(freq, H, thickness_m, nk_guess, tolerance=0.5)
            result = optimize_thickness(
                freq, H, thickness_um, nk_guess,
                tolerance=tolerance,
                resolution=step,
                span=span,
                progress_callback = update_progress
            )

            self.extract_btn.setEnabled(True)
            self.extract_progress.setValue(0)
            self.extract_progress.setVisible(False)

            n = result["n"]
            kappa = result["kappa"]
            alpha = result["alpha"]
            d = result["best_thickness"]

            tv_dialog = TotalVariationPlot(result["all_thicknesses"], result["TV"], self)
            tv_dialog.exec()

        # Create results widget
        results_widget = ResultsWindow(freq, n, kappa, alpha, d, self.model.freq_min, self.model.freq_max)

        # Store for saving
        self.last_extraction_results = {
            "freq": freq,
            "n": n,
            "kappa": kappa,
            "alpha": alpha,
            "thickness": d,
            "method": method,
            "freq_min": self.model.freq_min,
            "freq_max": self.model.freq_max
        }
        self.save_params_btn.setEnabled(True)

        # Replace tab content
        self.bottom_tabs.removeTab(1)
        self.bottom_tabs.addTab(results_widget, "Material Parameters")
        self.bottom_tabs.setCurrentIndex(1)
        self.bottom_tabs.setTabEnabled(1, True)

        self.extract_progress.reset()

    def check_data_is_loaded(self):
        if self.model.E_ref is None or self.model.E_sam is None or self.model.time is None:
            QMessageBox.warning(self, "Missing Data", "Please load both reference and sample files first.")
            return False
        else:
            return True

    def save_fft_data(self):
        if self.model.fft_results is None:
            QMessageBox.warning(self, "No data", "No FFT data available to save.")
            return

        for var in self.model.fft_results:
            if var is None:
                QMessageBox.warning(self, "No data", f"No FFT data available to save. {var} is None")
                return

        results = self.model.fft_results
        freq = results["freq"]
        FFT_ref = results["FFT_ref"]
        FFT_sam = results["FFT_sam"]
        phi = results["phi_unwrapped"]

        today = date.today().isoformat()
        # Suggested filename
        default_filename = f"fft_data_{today}.csv"

        # Ask user where to save
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save FFT Data",
            default_filename,
            "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, "w") as f:
                # Write headers
                f.write("FFT Data from THz-TDS\n")
                f.write(f"Timestamp: {datetime.today().isoformat()}\n")
                f.write("\n")
                f.write("f (THz)\t|FFT_r|\t|FFT_s|\tPhi\n")

                # Write data
                for i in range(len(results["freq"])):
                    line = f"{freq[i]:.4f}\t{FFT_ref[i]:.4f}\t{FFT_sam[i]:.4f}\t{phi[i]:.4f}\n"
                    f.write(line)

            #QMessageBox.information(self, "Success", f"FFT data saved to:\n{path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save FFT data:\n{str(e)}")

    def save_material_parameters(self):
        if not hasattr(self, "last_extraction_results"):
            QMessageBox.warning(self, "No data", "No extracted data to save.")
            return

        results = self.last_extraction_results
        method = results["method"].capitalize()
        thickness = results["thickness"]
        fmin = results["freq_min"]
        fmax = results["freq_max"]

        # Suggest a default filename
        today = date.today().isoformat()
        default_filename = f"material_params_{method}_d{int(thickness)}um_{fmin:.2f}-{fmax:.2f}THz_{today}.csv"

        # Ask where to save
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Material Parameters",
            default_filename,
            "CSV Files (*.csv)"
        )
        if not path:
            return  # User cancelled

        try:
            with open(path, "w") as f:
                # Write headers
                f.write("Material Parameters Extracted from THz-TDS\n")
                f.write(f"Timestamp: {datetime.today().isoformat()}\n")
                f.write(f"Extraction Method: {method}\n")
                f.write(f"Sample Thickness: {thickness:.1f} µm\n")
                f.write(f"Frequency Range: {fmin:.2f} – {fmax:.2f} THz\n")
                f.write("\n")  # Spacer
                f.write("f (THz)\tn\tkappa\talpha\n")

                # Write data
                for i in range(len(results["freq"])):
                    line = f"{results['freq'][i]:.4f}\t{results['n'][i]:.4f}\t{results['kappa'][i]:.4f}\t{results['alpha'][i]:.4f}\n"
                    f.write(line)

            #QMessageBox.information(self, "Success", f"Parameters saved to:\n{path}")

        except Exception as e:
            QMessageBox.critical(self, "Save Failed", f"An error occurred:\n{str(e)}")


