"""
DRIFT ENGINE
============

Purpose: Estimate time-varying expected return μₜ using Kalman filter
Why: Tracks directional bias, NOT the main risk driver

Method: State-space model with adaptive noise
Output: μₜ (drift) + uncertainty Pₜ (used to penalize Kelly)

IMPORTANT: This is NOT optimized for profit, tuned for stability
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from filterpy.kalman import KalmanFilter
from loguru import logger


class DriftEngine:
    """
    Kalman filter for estimating time-varying drift μₜ.
    """

    def __init__(
        self,
        initial_drift: float = 0.0,
        state_noise_factor: float = 1e-5,
        min_obs_variance: float = 1e-6,
        adaptive: bool = True
    ):
        self.initial_drift = initial_drift
        self.state_noise_factor = state_noise_factor
        self.min_obs_variance = min_obs_variance
        self.adaptive = adaptive

        self.kf = KalmanFilter(dim_x=1, dim_z=1)

        self.kf.F = np.array([[1.0]])  # random walk
        self.kf.H = np.array([[1.0]])  # observe return directly

        logger.info(
            f"DriftEngine initialized | Q={state_noise_factor}, "
            f"min_R={min_obs_variance}"
        )

    def update_regime_parameters(self, regime: str, volatility: float):
        if regime == "bull":
            q_mult = 1.0
        elif regime == "sideways":
            q_mult = 3.0
        elif regime == "crisis":
            q_mult = 10.0
        else:
            q_mult = 1.0

        self.kf.Q = np.array([[self.state_noise_factor * q_mult]])

        if self.adaptive:
            r_val = max(volatility**2, self.min_obs_variance)
            if regime == "crisis":
                r_val *= 2.0
            self.kf.R = np.array([[r_val]])

    def estimate_drift(
        self,
        returns: pd.Series,
        volatility: pd.Series,
        regime_probabilities: Optional[pd.DataFrame] = None
    ) -> Tuple[pd.Series, pd.Series]:

        drift_vals = []
        uncertainty_vals = []

        # -------- WARM START (CRITICAL FIX) --------
        warmup = returns.dropna().iloc[:20]

        if len(warmup) > 0:
            mu0 = warmup.mean()
            P0 = max(warmup.var(), self.min_obs_variance)
        else:
            mu0 = self.initial_drift
            P0 = 1e-4

        self.kf.x = np.array([[mu0]])
        self.kf.P = np.array([[P0]])

        for idx, ret in returns.items():

            if regime_probabilities is not None and idx in regime_probabilities.index:
                regime = regime_probabilities.loc[idx].idxmax()
            else:
                regime = "sideways"

            if idx in volatility.index and np.isfinite(volatility.loc[idx]):
                vol = volatility.loc[idx]
            else:
                vol = np.nanmean(volatility.values)

            if not np.isfinite(vol) or vol <= 0:
                vol = np.sqrt(self.min_obs_variance)

            self.update_regime_parameters(regime, vol)

            self.kf.predict()

            if np.isfinite(ret):
                self.kf.update(np.array([[ret]]))

            drift_vals.append(self.kf.x[0, 0])
            uncertainty_vals.append(self.kf.P[0, 0])

        drift = pd.Series(drift_vals, index=returns.index, name="drift")
        uncertainty = pd.Series(uncertainty_vals, index=returns.index, name="uncertainty")

        logger.info(
            f"Drift estimation complete | "
            f"mean={drift.dropna().mean():.6f}, "
            f"current={drift.dropna().iloc[-1]:.6f}"
        )

        return drift, uncertainty

    def get_drift_stats(
        self,
        drift: pd.Series,
        uncertainty: pd.Series
    ) -> Dict[str, float]:

        d = drift.dropna()
        u = uncertainty.dropna()

        return {
            "mean_drift": d.mean(),
            "std_drift": d.std(),
            "current_drift": d.iloc[-1] if len(d) else np.nan,
            "mean_uncertainty": u.mean(),
            "current_uncertainty": u.iloc[-1] if len(u) else np.nan,
            "drift_range": d.max() - d.min()
        }
