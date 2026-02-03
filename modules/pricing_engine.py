"""
PRICING ENGINE
==============

Black–Scholes and Merton Jump Diffusion pricing
"""

import numpy as np
import math
from scipy.stats import norm


class PricingEngine:

    @staticmethod
    def black_scholes_call(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0:
            return max(S - K, 0.0)

        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)

    @staticmethod
    def merton_call(
        S,
        K,
        T,
        r,
        sigma,
        lam,
        mu_j,
        sigma_j,
        n_terms=20
    ):
        """
        Merton jump-diffusion call price
        """

        price = 0.0

        for k in range(n_terms):
            poisson_weight = (
                math.exp(-lam * T)
                * (lam * T) ** k
                / math.factorial(k)
            )

            sigma_k = np.sqrt(sigma**2 + (k * sigma_j**2) / T)
            r_k = r - lam * (math.exp(mu_j + 0.5 * sigma_j**2) - 1) + (k * mu_j) / T

            price += poisson_weight * PricingEngine.black_scholes_call(
                S=S,
                K=K,
                T=T,
                r=r_k,
                sigma=sigma_k
            )

        return price
