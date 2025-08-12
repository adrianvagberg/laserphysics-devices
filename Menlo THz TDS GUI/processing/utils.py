from scipy.fft import fft, fftfreq
import numpy as np
from scipy.optimize import minimize
from scipy.constants import c

def compute_transfer_function(time, E_ref, E_sam):
    N = len(time)
    dt = (time[1] - time[0]) * 1e-12  # convert ps → s
    freq = fftfreq(N, dt)[:N // 2]  # Hz

    E_ref_fft = fft(E_ref)
    E_sam_fft = fft(E_sam)
    H = E_sam_fft / E_ref_fft
    phase_wrapped = -np.angle(H[:N // 2])

    return freq * 1e-12, H[:N // 2], phase_wrapped

def fminsearchbnd(fun, x0, LB=None, UB=None, options=None, *args):
    """
    Python port of fminsearchbnd from MATLAB.
    Uses a variable transformation to enforce bounds during Nelder-Mead optimization.
    """
    x0 = np.atleast_1d(np.array(x0, dtype=float))
    n = len(x0)

    LB = np.full_like(x0, -np.inf) if LB is None else np.atleast_1d(LB).astype(float)
    UB = np.full_like(x0, np.inf) if UB is None else np.atleast_1d(UB).astype(float)

    if len(LB) != n or len(UB) != n:
        raise ValueError("x0, LB, and UB must have the same length")

    bound_class = np.zeros(n, dtype=int)
    for i in range(n):
        k = int(np.isfinite(LB[i])) + 2 * int(np.isfinite(UB[i]))
        if k == 3 and LB[i] == UB[i]:
            bound_class[i] = 4  # Fixed variable
        else:
            bound_class[i] = k

    # Transform x0 to unconstrained space
    def x2u(x):
        xu = []
        for i in range(n):
            if bound_class[i] == 0:
                xu.append(x[i])
            elif bound_class[i] == 1:
                xu.append(np.sqrt(max(0, x[i] - LB[i])))
            elif bound_class[i] == 2:
                xu.append(np.sqrt(max(0, UB[i] - x[i])))
            elif bound_class[i] == 3:
                val = (2 * (x[i] - LB[i]) / (UB[i] - LB[i])) - 1
                xu.append(2 * np.pi + np.arcsin(np.clip(val, -1, 1)))
            # Fixed variables are excluded
        return np.array(xu)

    def u2x(u):
        x = []
        k = 0
        for i in range(n):
            if bound_class[i] == 0:
                x.append(u[k])
                k += 1
            elif bound_class[i] == 1:
                x.append(LB[i] + u[k]**2)
                k += 1
            elif bound_class[i] == 2:
                x.append(UB[i] - u[k]**2)
                k += 1
            elif bound_class[i] == 3:
                sin_val = np.sin(u[k])
                x_val = ((sin_val + 1) / 2) * (UB[i] - LB[i]) + LB[i]
                x.append(np.clip(x_val, LB[i], UB[i]))
                k += 1
            elif bound_class[i] == 4:  # Fixed
                x.append(LB[i])
        return np.array(x)

    x0u = x2u(x0)

    def wrapped_fun(u):
        x = u2x(u)
        return fun(x, *args)

    res = minimize(wrapped_fun, x0u, method='Nelder-Mead', options=options or {})

    x = u2x(res.x)
    return x, res.fun, res.success, res


def objective_function(x, frequency, complex_ratio, thickness, j):
    """
    Objective function to match theoretical and experimental transfer functions
    at normal incidence with air on both sides.

    Parameters:
    - x: [n, kappa] guess
    - frequency: frequency array (THz)
    - complex_ratio: measured transfer function (complex)
    - thickness: sample thickness in meters
    - j: current frequency index

    Returns:
    - f: scalar error value (squared error in log-mag and phase)
    """
    n_real, kappa = x
    n_complex = n_real - 1j * kappa
    freq = frequency[j]
    n_air = 1.00027

    omega = 2 * np.pi * freq * 1e12
    beta_sam = omega * thickness * n_complex / c
    beta_air = omega * thickness * n_air / c

    # Fresnel coefficients at normal incidence (air-sample-air)

    t_12 = 2 * n_air / (n_air + n_complex)
    t_23 = 2 * n_complex / (n_complex + n_air)
    r_12 = (n_air - n_complex) / (n_air + n_complex)
    r_23 = (n_complex - n_air) / (n_complex + n_air)

    H_theo = (t_12 * t_23 * np.exp(-1j * (beta_sam - beta_air))) / (1 + r_12 * r_23 * np.exp(-2j * beta_sam))

    H_exp = complex_ratio[j]

    error_mag = np.log(np.abs(H_theo)) - np.log(np.abs(H_exp))
    error_phase = np.angle(H_theo) - np.angle(H_exp)

    return error_mag**2 + error_phase**2

def svg_to_offset_image(svg_path: str, width: int = 16, height: int = 10):
    from matplotlib.offsetbox import OffsetImage
    from PyQt6.QtGui import QPixmap, QPainter
    from PyQt6.QtSvg import QSvgRenderer
    from PyQt6.QtCore import Qt

    renderer = QSvgRenderer(svg_path)
    image = QPixmap(width, height)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()

    # Convert to numpy array
    image_bytes = image.toImage().bits().asstring(image.width() * image.height() * 4)
    arr = np.frombuffer(image_bytes, dtype=np.uint8).reshape((height, width, 4))

    return OffsetImage(arr, zoom=1)

