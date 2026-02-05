# Regime-Aware BS–Merton Pricing & Kelly Allocation System

## Overview

This project implements a **regime-aware option mispricing and decision engine**.  
It compares market option prices against model prices derived from Black–Scholes and Merton jump-diffusion models, dynamically adjusts parameters based on market conditions, and produces **BUY / SELL / REFUSE** decisions with **risk-controlled position sizing**.

The system is designed for **pricing disagreement detection and capital allocation**, not for return prediction.

---

## Design Philosophy

- Focus on **mispricing**, not forecasting
- Explicit separation of **diffusion risk vs jump risk**
- **Soft regime transitions** instead of hard switches
- Conservative, fractional **Kelly sizing**
- Stability and robustness prioritized over profit optimization

This is a **research-oriented system**, not a production trading engine.

---

## System Pipeline

Prices
↓
Log Returns
↓
Jump Detection (Jump / Diffusion split)
↓
Volatility Estimation (σₜ, regime-aware)
↓
Drift Estimation (μₜ via Kalman filter)
↓
Regime Detection (Bull / Sideways / Crisis)
↓
BS–Merton Pricing
↓
Mispricing Measurement
↓
Decision Logic (BUY / SELL / REFUSE)
↓
Kelly-Based Position Sizing


---

## Project Structure

regime_pricing_system/
│
├── configs/ # System parameters
├── data/
│ ├── raw/ # Input market data
│ └── processed/ # Intermediate outputs
│
├── modules/
│ ├── jump_detector.py
│ ├── volatility_engine.py
│ ├── drift_engine.py
│ ├── regime_engine.py
│ ├── pricing_engine.py
│ ├── mispricing_engine.py
│ └── decision_engine.py
│
├── notebooks/ # Analysis & exploration
├── tests/ # Unit tests
│
├── main.py # System entry point
├── requirements.txt
└── README.md


---

## Data Requirements

Minimum required columns:
- `Date`
- `Close`

Optional (for option-level analysis):
- `Strike`
- `Expiry`
- `OptionPrice`
- `RiskFreeRate`

Input data is expected in CSV format under `data/raw/`.

---

## Usage

Install dependencies:
```bash
pip install -r requirements.txt
Run the system:

python main.py
The system outputs:

Regime probabilities

Model vs market price comparison

Mispricing signal

Final action (BUY / SELL / REFUSE)

Suggested position size

Configuration
All parameters are defined in:

configs/parameters.yaml
Configurable components include:

Jump detection thresholds

Volatility decay factors

Kalman filter noise parameters

Regime transition rules

Kelly sizing constraints

Parameters are intentionally conservative and not optimized for profit.

Current Status
Implemented:

Jump detection

Volatility estimation

Drift estimation (Kalman filter)

Regime classification

BS–Merton pricing

Mispricing measurement

Risk-controlled Kelly sizing

End-to-end decision output

Planned:

Historical backtesting

Parameter calibration framework

Live data integration

Greeks-aware risk overlays

Disclaimer
This project is for research and educational purposes only.
It is not intended for live trading or financial advice.