import numpy as np
from scipy.constants import c, pi
from processing.utils import objective_function, fminsearchbnd

def extract_analytical(freq_THz, H, phi_unwrapped, thickness_m):
    omega = 2 * pi * freq_THz * 1e12  # rad/s
    n = 1 + (phi_unwrapped * c) / (omega * thickness_m)

    # Absorption coefficient (in cm^-1)
    kappa = -c / (omega * thickness_m) * np.log((n + 1)**2 * H / (4 * n))
    alpha = (2 * omega / c) * kappa / 100  # cm^-1

    return {
        "n": n,
        "kappa": kappa,
        "alpha": alpha
    }

def extract_numerical(frequency, complex_ratio, thickness, nk_guess, tolerance):
    x0 = np.array(nk_guess, dtype=float)
    n_out = []
    kappa_out = []
    alpha_out = []

    for j in range(len(frequency)):
        def fun(x):
            return objective_function(x, frequency, complex_ratio, thickness, j)

        x_lb = x0 - tolerance
        x_ub = x0 + tolerance

        x_opt, fval, success, result = fminsearchbnd(fun, x0, x_lb, x_ub)

        n_j, kappa_j = x_opt
        alpha_j = (2 * 2 * pi * frequency[j] * 1e12 * kappa_j) / (100 * c)

        # Optional smoothing
        if j > 10:
            if abs(n_j - n_out[-1]) > 0.10:
                n_j = n_out[-1]
                alpha_j = alpha_out[-1]
            if abs(kappa_j - kappa_out[-1]) > 0.10:
                kappa_j = kappa_out[-1]
                alpha_j = alpha_out[-1]

        n_out.append(n_j)
        kappa_out.append(kappa_j)
        alpha_out.append(alpha_j)
        x0 = np.array([n_j, kappa_j])

    return {
        "n": np.array(n_out),
        "kappa": np.array(kappa_out),
        "alpha": np.array(alpha_out)
    }


def optimize_thickness(freq, H_exp, thickness_um_nominal, nk_guess, tolerance=1, resolution=1, span=10, progress_callback=None):
    """
    Optimizes sample thickness by minimizing total variation in n and kappa.

    Returns:
        best_thickness: optimal thickness in um
        n, kappa, alpha: spectra for best thickness
        all_thicknesses: list of trial thicknesses
        TV: total variation at each trial thickness
    """

    thickness_range = np.arange(thickness_um_nominal - span,
                                thickness_um_nominal + span + resolution,
                                resolution)
    total = len(thickness_range)

    n_list = []
    kappa_list = []
    alpha_list = []
    TV_list = []

    for i, thickness_um in enumerate(thickness_range):
        result = extract_numerical(
            freq,
            H_exp,
            thickness_um * 1e-6,  # meters
            nk_guess,
            tolerance
        )
        n = result["n"]
        kappa = result["kappa"]
        alpha = result["alpha"]

        # Compute total variation
        TV_n = np.sum(np.abs(np.diff(n)))
        TV_k = np.sum(np.abs(np.diff(kappa)))
        TV = TV_n + TV_k

        n_list.append(n)
        kappa_list.append(kappa)
        alpha_list.append(alpha)
        TV_list.append(TV)

        if progress_callback:
            progress_callback(int((i + 1) / total * 100))

    TV = np.array(TV_list)
    norm_fitness = TV / TV.max()
    idx_min = np.argmin(norm_fitness)
    best_thickness = thickness_range[idx_min]

    return {
        "best_thickness": best_thickness,
        "n": n_list[idx_min],
        "kappa": kappa_list[idx_min],
        "alpha": alpha_list[idx_min],
        "all_thicknesses": thickness_range,
        "TV": TV
    }


