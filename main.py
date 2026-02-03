"""
MAIN SYSTEM ENTRY POINT
=======================

Regime-aware pricing with:
- Jump detection
- Volatility (diffusion only)
- Drift (Kalman)
- Regime probabilities
- Merton pricing
- Mispricing
- Smooth confidence
- Kelly sizing
- FINAL VERDICT: BUY / SELL / REFUSE
"""

import sys
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from loguru import logger

# ---------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR / "modules"))

# ---------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------
from jump_detector import JumpDetector, calculate_log_returns
from volatility_engine import VolatilityEngine
from drift_engine import DriftEngine
from regime_engine import RegimeEngine
from pricing_engine import PricingEngine
from mispricing_engine import MispricingEngine


# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------
def load_config(path="configs/parameters.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def sigmoid(x, k=5.0):
    return 1 / (1 + np.exp(-k * (x - 0.5)))


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main():

    print("\n" + "=" * 70)
    print("REGIME-AWARE PRICING — FINAL DECISION SYSTEM")
    print("=" * 70 + "\n")

    logger.remove()
    logger.add(sys.stdout, level="INFO")

    config = load_config()

    # --------------------------------------------------
    # Load data
    # --------------------------------------------------
    data_path = BASE_DIR / "data" / "raw" / "sample_data.csv"
    data_path.parent.mkdir(parents=True, exist_ok=True)

    if not data_path.exists():
        dates = pd.date_range("2022-01-01", periods=500, freq="D")
        prices = 100 * np.exp(np.cumsum(np.random.normal(0.0005, 0.02, 500)))
        pd.DataFrame({"Close": prices}, index=dates).to_csv(data_path)

    df = pd.read_csv(data_path, index_col=0, parse_dates=True)

    # --------------------------------------------------
    # Returns & jumps
    # --------------------------------------------------
    returns = calculate_log_returns(df["Close"])

    jump_cfg = config["jump_detection"]
    jump_detector = JumpDetector(
        threshold=jump_cfg["threshold"],
        window=jump_cfg["window"],
        min_observations=jump_cfg["min_observations"]
    )

    is_jump, jump_returns, diffusion_returns = jump_detector.detect_jumps(
        returns,
        use_robust=jump_cfg["use_robust"]
    )

    jump_params = jump_detector.estimate_jump_parameters(jump_returns)

    # --------------------------------------------------
    # Volatility
    # --------------------------------------------------
    vol_cfg = config["volatility"]
    vol_engine = VolatilityEngine(
        bull_ewma_lambda=vol_cfg["bull_ewma_lambda"],
        crisis_ewma_lambda=vol_cfg["crisis_ewma_lambda"],
        garch_p=vol_cfg["garch_p"],
        garch_q=vol_cfg["garch_q"],
        min_variance=vol_cfg["min_variance"]
    )

    volatility = vol_engine.ewma_volatility(
        diffusion_returns,
        lambda_decay=vol_cfg["bull_ewma_lambda"]
    )

    sigma_t = float(volatility.iloc[-1])

    # --------------------------------------------------
    # Drift
    # --------------------------------------------------
    drift_cfg = config["drift"]
    drift_engine = DriftEngine(
        initial_drift=drift_cfg["initial_drift"],
        state_noise_factor=drift_cfg["state_noise_factor"],
        min_obs_variance=drift_cfg["min_obs_variance"],
        adaptive=drift_cfg["adaptive"]
    )

    drift, uncertainty = drift_engine.estimate_drift(
        returns=diffusion_returns,
        volatility=volatility,
        regime_probabilities=None
    )

    uncertainty_t = float(uncertainty.iloc[-1])

    # --------------------------------------------------
    # Regimes
    # --------------------------------------------------
    regime_engine = RegimeEngine()
    regime_probs = regime_engine.detect_regimes(
        volatility=volatility,
        is_jump=is_jump
    )

    bull_p = float(regime_probs["bull"].iloc[-1])
    sideways_p = float(regime_probs["sideways"].iloc[-1])
    crisis_p = float(regime_probs["crisis"].iloc[-1])

    # --------------------------------------------------
    # Pricing (Merton)
    # --------------------------------------------------
    pricing_engine = PricingEngine()

    S = float(df["Close"].iloc[-1])
    K = S
    T = 30 / 252
    r = config["system"]["risk_free_rate"]

    lambda_eff = jump_params["lambda"] * (1 + 2 * crisis_p)

    model_price = pricing_engine.merton_call(
        S=S,
        K=K,
        T=T,
        r=r,
        sigma=sigma_t,
        lam=lambda_eff,
        mu_j=jump_params["mu_j"],
        sigma_j=jump_params["sigma_j"]
    )

    # Mock market price (until live feed)
    market_price = model_price * (1 + np.random.normal(0, 0.05))

    # --------------------------------------------------
    # Mispricing
    # --------------------------------------------------
    mis_cfg = config["mispricing"]
    mis_engine = MispricingEngine(
        ema_alpha=mis_cfg["ema_alpha"],
        min_signal_strength=mis_cfg["min_signal_strength"]
    )

    mispricing = mis_engine.compute_mispricing(
        market_price=pd.Series([market_price]),
        model_price=pd.Series([model_price])
    ).iloc[-1]

    # --------------------------------------------------
    # Bias & confidence
    # --------------------------------------------------
    threshold = mis_cfg["buy_threshold"]
    raw_bias = min(1.0, abs(mispricing) / threshold)
    confidence = sigmoid(raw_bias)

    direction = 0.0
    if mispricing < 0:
        direction = +1.0
    elif mispricing > 0:
        direction = -1.0

    # --------------------------------------------------
    # Kelly sizing
    # --------------------------------------------------
    kel_cfg = config["kelly"]

    risk = sigma_t * kel_cfg["jump_risk_multiplier"]
    base_kelly = confidence / max(risk, 1e-6)

    penalty = 1 / (1 + kel_cfg["uncertainty_scale"] * uncertainty_t)

    kelly_fraction = kel_cfg["fraction"] * base_kelly * penalty

    max_cap = (
        kel_cfg["bull_max_position"] * bull_p +
        kel_cfg["sideways_max_position"] * sideways_p +
        kel_cfg["crisis_max_position"] * crisis_p
    )

    position = direction * min(kelly_fraction, max_cap)

    position = max(
        -kel_cfg["max_position"],
        min(kel_cfg["max_position"], position)
    )

    # --------------------------------------------------
    # FINAL VERDICT
    # --------------------------------------------------
    verdict = "REFUSE"

    min_conf = config["decision"]["min_confidence"]
    min_pos = kel_cfg["min_position"]
    allow_crisis = config["decision"]["allow_crisis_trades"]

    if not (
        mispricing == 0.0 or
        confidence <= min_conf or
        abs(position) < min_pos or
        (crisis_p > 0.5 and not allow_crisis)
    ):
        if mispricing < 0:
            verdict = "BUY"
        elif mispricing > 0:
            verdict = "SELL"

    # --------------------------------------------------
    # OUTPUT
    # --------------------------------------------------
    print("REGIME PROBABILITIES")
    print(f"Bull     : {bull_p:.2f}")
    print(f"Sideways : {sideways_p:.2f}")
    print(f"Crisis   : {crisis_p:.2f}\n")

    print("PRICING")
    print(f"Model Price  : {model_price:.4f}")
    print(f"Market Price : {market_price:.4f}\n")

    print("MISPRICING & CONFIDENCE")
    print(f"Mispricing        : {mispricing:.4f}")
    print(f"Confidence        : {confidence:.2f}\n")

    print("FINAL VERDICT")
    print(f"Action        : {verdict}")
    print(f"Position Size : {position * 100:.2f}%")

    print("\n" + "=" * 70)
    print("SYSTEM EXECUTION COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
