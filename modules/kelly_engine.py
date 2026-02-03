"""
KELLY ENGINE
============

Computes safe, regime-aware, uncertainty-penalized Kelly position size.
"""

import numpy as np


class KellyEngine:

    def __init__(
        self,
        fraction: float,
        max_position: float,
        min_position: float,
        jump_risk_multiplier: float,
        uncertainty_scale: float
    ):
        self.fraction = fraction
        self.max_position = max_position
        self.min_position = min_position
        self.jump_risk_multiplier = jump_risk_multiplier
        self.uncertainty_scale = uncertainty_scale

    def compute_kelly(
        self,
        mispricing: float,
        volatility: float,
        jump_intensity: float,
        uncertainty: float,
        regime: str,
        regime_caps: dict
    ) -> float:

        # Guardrails
        if volatility <= 0 or not np.isfinite(volatility):
            return 0.0

        # Base Kelly (edge / variance)
        raw_kelly = mispricing / (volatility ** 2)

        # Fractional Kelly
        kelly = self.fraction * raw_kelly

        # Jump risk penalty
        kelly /= (1 + self.jump_risk_multiplier * jump_intensity)

        # Uncertainty penalty (Kalman P_t)
        kelly /= (1 + self.uncertainty_scale * uncertainty)

        # Directional (sign preserved)
        kelly = np.sign(kelly) * min(abs(kelly), self.max_position)

        # Regime cap
        regime_cap = regime_caps.get(regime, self.max_position)
        kelly = np.clip(kelly, -regime_cap, regime_cap)

        # Minimum size filter
        if abs(kelly) < self.min_position:
            return 0.0

        return float(kelly)
