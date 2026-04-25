import numpy as np
from scipy.optimize import curve_fit
from typing import Union

# Type alias for array-like inputs (lists, numpy arrays, single floats)
Numeric = Union[float, np.ndarray, list]


def four_parameter_logistic(
    x: Numeric, a: float, b: float, c: float, d: float
) -> Union[float, np.ndarray]:
    """
    4-parameter logistic (4PL) model function.

    Equation: y = d + (a - d) / (1 + (x / c)^b)

    Args:
        x: Concentration/Dose values.
        a: Minimum asymptote (Bottom).
        b: Hill slope (Slope factor).
        c: Inflection point (EC50/IC50).
        d: Maximum asymptote (Top).

    Returns:
        Predicted response y.
    """
    x = np.asarray(x)
    if np.any(np.asarray(c) == 0):
        raise ValueError("Inflection point 'c' (EC50/IC50) must be nonzero.")
    return d + (a - d) / (1 + np.power((x / c), b))


def percent_inhibition(
    high_control: Numeric, low_control: Numeric, sample: Numeric
) -> Union[float, np.ndarray]:
    """
    Calculate percent inhibition: 100 * (1 - (sample - low) / (high - low))
    """
    hc = np.mean(high_control)
    lc = np.mean(low_control)
    sample = np.asarray(sample)

    denominator = hc - lc
    if np.isclose(denominator, 0):
        return np.full_like(sample, np.nan)

    return 100 * (1 - (sample - lc) / denominator)


def fit_4pl_curve(xdata: Numeric, ydata: Numeric) -> dict[str, float]:
    """
    Fit a 4PL curve to data and return parameters matching Lab Guide specs.

    Returns:
        Dict with keys: 'bottom', 'hill_slope', 'ic50', 'top', 'r_squared'
    """
    x = np.asarray(xdata)
    y = np.asarray(ydata)

    _nan_result = {
        "bottom": np.nan,
        "hill_slope": np.nan,
        "ic50": np.nan,
        "top": np.nan,
        "r_squared": 0.0,
    }

    if len(x) == 0 or len(y) == 0:
        return _nan_result

    # Initial guesses: a (min), b (slope), c (inflection), d (max)
    min_y = np.min(y)
    max_y = np.max(y)
    mid_x = float(np.median(x))

    p0 = [min_y, 1.0, mid_x, max_y]

    try:
        popt, _ = curve_fit(four_parameter_logistic, x, y, p0=p0, maxfev=10000)
        a, b, c, d = popt

        # Calculate R²
        residuals = y - four_parameter_logistic(x, *popt)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if not np.isclose(ss_tot, 0) else 0.0

        return {
            "bottom": float(a),
            "hill_slope": float(b),
            "ic50": float(c),
            "top": float(d),
            "r_squared": float(r2),
        }
    except (RuntimeError, ValueError):
        return _nan_result
