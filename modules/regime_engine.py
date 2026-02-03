"""
REGIME ENGINE
=============

Purpose:
Classify market conditions into probabilistic regimes:
Bull / Sideways / Crisis

Inputs:
- Volatility σₜ
- Jump indicator
- Rolling statistics

Output:
- Regime probability DataFrame
"""

import numpy as np
import pandas as pd
from loguru import logger


class RegimeEngine:

    def __init__(
        self,
        vol_window: int = 60,
        jump_window: int = 60,
        high_vol_pct: float = 0.8,
        low_vol_pct: float = 0.3,
        jump_rate_threshold: float = 0.05
    ):
        self.vol_window = vol_window
        self.jump_window = jump_window
        self.high_vol_pct = high_vol_pct
        self.low_vol_pct = low_vol_pct
        self.jump_rate_threshold = jump_rate_threshold

        logger.info(
            f"RegimeEngine initialized | vol_window={vol_window}, jump_window={jump_window}"
        )

    def detect_regimes(
        self,
        volatility: pd.Series,
        is_jump: pd.Series
    ) -> pd.DataFrame:

        regimes = pd.DataFrame(index=volatility.index)
        regimes["bull"] = 0.0
        regimes["sideways"] = 0.0
        regimes["crisis"] = 0.0

        # Rolling volatility percentile
        vol_rank = (
            volatility
            .rolling(self.vol_window)
            .apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1], raw=False)
        )

        # Rolling jump rate
        jump_rate = (
            is_jump
            .rolling(self.jump_window)
            .mean()
        )

        for t in volatility.index:

            v = vol_rank.loc[t]
            j = jump_rate.loc[t]

            if not np.isfinite(v) or not np.isfinite(j):
                regimes.loc[t, "sideways"] = 1.0
                continue

            # Crisis
            if v > self.high_vol_pct or j > self.jump_rate_threshold:
                regimes.loc[t, "crisis"] = 0.7
                regimes.loc[t, "sideways"] = 0.3

            # Bull
            elif v < self.low_vol_pct and j < self.jump_rate_threshold / 2:
                regimes.loc[t, "bull"] = 0.7
                regimes.loc[t, "sideways"] = 0.3

            # Sideways
            else:
                regimes.loc[t, "sideways"] = 1.0

        logger.info("Regime detection complete")

        return regimes
