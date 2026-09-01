from dataclasses import dataclass
from typing import List, Optional


@dataclass
class StepResponseMetrics:
    overshoot_pct: Optional[float]
    peak_time_s: Optional[float]
    settling_time_s: Optional[float]
    settling_time_s_5pct: Optional[float]
    steady_state_error_pct: Optional[float]


def _smooth_violations(out_of_band: List[bool], min_run: int) -> List[bool]:
    smoothed = list(out_of_band)
    n = len(smoothed)
    i = 0
    while i < n:
        if smoothed[i]:
            j = i
            while j < n and smoothed[j]:
                j += 1
            if j - i < min_run:
                for k in range(i, j):
                    smoothed[k] = False
            i = j
        else:
            i += 1
    return smoothed


def _settling_time_s(
    t: List[float], y: List[float], setpoint: float, band_pct: float, min_violation_samples: int
) -> Optional[float]:
    band = abs(setpoint) * band_pct
    out_of_band = [abs(value - setpoint) > band for value in y]
    out_of_band = _smooth_violations(out_of_band, min_violation_samples)

    settling_index = 0
    for idx in range(len(y) - 1, -1, -1):
        if out_of_band[idx]:
            settling_index = idx + 1
            break
    if settling_index >= len(t):
        return None
    return t[settling_index] - t[0]


def compute_step_response_metrics(
    t: List[float],
    y: List[float],
    setpoint: float,
    settling_band_pct: float = 0.02,
    settling_min_violation_samples: int = 3,
    settling_band_pct_5: float = 0.05,
) -> StepResponseMetrics:
    if not y or not t or len(y) != len(t) or setpoint == 0:
        return StepResponseMetrics(None, None, None, None, None)

    t0 = t[0]
    peak = max(y)
    peak_idx = y.index(peak)
    overshoot_pct = max(0.0, (peak - setpoint) / abs(setpoint) * 100.0)
    peak_time_s = t[peak_idx] - t0

    settling_time_s = _settling_time_s(t, y, setpoint, settling_band_pct, settling_min_violation_samples)
    settling_time_s_5pct = _settling_time_s(t, y, setpoint, settling_band_pct_5, settling_min_violation_samples)

    steady_state_error_pct = abs(setpoint - y[-1]) / abs(setpoint) * 100.0

    return StepResponseMetrics(
        overshoot_pct=round(overshoot_pct, 1),
        peak_time_s=round(peak_time_s, 2),
        settling_time_s=round(settling_time_s, 2) if settling_time_s is not None else None,
        settling_time_s_5pct=round(settling_time_s_5pct, 2) if settling_time_s_5pct is not None else None,
        steady_state_error_pct=round(steady_state_error_pct, 1),
    )
