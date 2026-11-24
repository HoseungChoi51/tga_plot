"""Tick values without matplotlib: the ones matplotlib.ticker.MaxNLocator picks.

A port of MaxNLocator.tick_values (matplotlib 3.11) for the settings plotkit uses: no integer, symmetric or prune
options, axes.autolimit_mode "data", and nbins "auto" meaning 9 (no axis to measure). The port follows matplotlib
(BSD-compatible licence); tests/test_engines.py checks it against matplotlib on many ranges.
"""
import math

import numpy as np

STEPS = (1, 2, 2.5, 5, 10)


def _nonsingular(vmin, vmax, expander, tiny):
    if not (np.isfinite(vmin) and np.isfinite(vmax)):
        return -expander, expander
    if vmax < vmin:
        vmin, vmax = vmax, vmin
    vmin, vmax = float(vmin), float(vmax)
    maxabs = max(abs(vmin), abs(vmax))
    if maxabs < (1e6 / tiny) * np.finfo(float).tiny:
        vmin, vmax = -expander, expander
    elif vmax - vmin <= maxabs * tiny:
        if vmax == 0 and vmin == 0:
            vmin, vmax = -expander, expander
        else:
            vmin -= expander * abs(vmin)
            vmax += expander * abs(vmax)
    return vmin, vmax


def _scale_range(vmin, vmax, n=1, threshold=100):
    dv = abs(vmax - vmin)
    meanv = (vmax + vmin) / 2
    if abs(meanv) / dv < threshold:
        offset = 0
    else:
        offset = math.copysign(10 ** (math.log10(abs(meanv)) // 1), meanv)
    scale = 10 ** (math.log10(dv / n) // 1)
    return scale, offset


class _EdgeInteger:
    def __init__(self, step, offset):
        self.step = step
        self._offset = abs(offset)

    def closeto(self, ms, edge):
        if self._offset > 0:
            digits = np.log10(self._offset / self.step)
            tol = min(0.4999, max(1e-10, 10 ** (digits - 12)))
        else:
            tol = 1e-10
        return abs(ms - edge) < tol

    def le(self, x):
        d, m = divmod(x, self.step)
        return d + 1 if self.closeto(m / self.step, 1) else d

    def ge(self, x):
        d, m = divmod(x, self.step)
        return d if self.closeto(m / self.step, 0) else d + 1


def _steps(steps):
    steps = np.asarray(steps, dtype=float)
    if steps[0] != 1:
        steps = np.concatenate([[1], steps])
    if steps[-1] != 10:
        steps = np.concatenate([steps, [10]])
    return np.concatenate([0.1 * steps[:-1], steps, [10 * steps[1]]])


def tick_values(vmin, vmax, nbins=10, steps=STEPS, min_n_ticks=2):
    """= matplotlib.ticker.MaxNLocator(nbins=nbins, steps=steps).tick_values(vmin, vmax), as a numpy array."""
    vmin, vmax = _nonsingular(vmin, vmax, expander=1e-13, tiny=1e-14)
    nbins = 9 if nbins == "auto" else int(nbins)
    scale, offset = _scale_range(vmin, vmax, nbins)
    _vmin, _vmax = vmin - offset, vmax - offset
    st = _steps(steps) * scale
    raw_step = (_vmax - _vmin) / nbins
    large = st >= raw_step
    istep = np.nonzero(large)[0][0] if any(large) else len(st) - 1
    ticks = None
    for step in st[:istep + 1][::-1]:
        best_vmin = (_vmin // step) * step
        edge = _EdgeInteger(step, offset)
        low = edge.le(_vmin - best_vmin)
        high = edge.ge(_vmax - best_vmin)
        ticks = np.arange(low, high + 1) * step + best_vmin
        if ((ticks <= _vmax) & (ticks >= _vmin)).sum() >= min_n_ticks:
            break
    return ticks + offset
