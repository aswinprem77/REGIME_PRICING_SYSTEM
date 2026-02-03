"""
MISPRICING ENGINE
=================

Purpose:
Compare market option price with model price
and compute relative mispricing.

This module does NOT trade.
It only measures deviation.
"""

import pandas as pd
import numpy as np


class MispricingEngine:

    def __init__(
        self,
        ema_alpha: float = 0.3,
        min_signal_strength: float = 0.01
    ):
        self.ema_alpha = ema_alpha
        self.min_signal_strength = min_signal_strength

    def compute_mispricing(
        self,
        market_price: pd.Series,
        model_price: pd.Series
    ) -> pd.Series:
        """
        Mispricing = (Market - Model) / Model
        """

        raw = (market_price - model_price) / model_price

        # Smooth to reduce noise
        smoothed = raw.ewm(alpha=self.ema_alpha).mean()

        # Ignore tiny noise
        smoothed[np.abs(smoothed) < self.min_signal_strength] = 0.0

        return smoothed
