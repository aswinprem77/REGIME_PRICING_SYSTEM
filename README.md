# Regime-Aware BS–Merton Pricing + Kelly Allocation System

A decision engine that detects option mispricing and outputs trade decisions with risk-controlled position sizing.

---

## What This Does

**Outputs:**
- BUY / SELL / REFUSE decisions
- Position size (Kelly-based, fractional)

**Not a forecasting model.**  
This is a pricing disagreement detector with disciplined risk management.

---

## Core Idea

Compare market option prices against theoretical prices from:
- Black–Scholes (diffusion)
- Merton (jumps)

Adapt parameters based on market regime (Bull / Sideways / Crisis).  
Size positions using fractional Kelly with uncertainty penalties.

---

## Pipeline
```
Prices
  ↓
Log Returns
  ↓
Jump Detection (separate jumps from diffusion)
  ↓
Volatility Estimation (σₜ, regime-aware, jumps excluded)
  ↓
Drift Estimation (μₜ via Kalman filter)
  ↓
Regime Detection (Bull / Sideways / Crisis probabilities)
  ↓
Effective Parameters (regime-weighted)
  ↓
BS–Merton Pricing
  ↓
Mispricing (Model - Market)
  ↓
Decision Logic (BUY / SELL / REFUSE)
  ↓
Kelly Position Sizing (fractional, capped)
```

Order is non-negotiable. Each stage feeds the next.

---

## Project Structure
```
regime_pricing_system/
│
├── data/
│   ├── raw/              # Your CSV files go here
│   └── processed/        # System outputs
│
├── modules/
│   ├── jump_detector.py       # Jump detection
│   ├── volatility_engine.py   # σₜ estimation
│   ├── drift_engine.py        # μₜ Kalman filter
│   ├── regime_engine.py       # Regime classification
│   ├── pricing_engine.py      # BS + Merton pricing
│   ├── mispricing_engine.py   # Signal generation
│   └── decision_engine.py     # Final BUY/SELL/REFUSE
│
├── configs/
│   └── parameters.yaml        # All system parameters
│
├── tests/                     # Unit tests
├── notebooks/                 # Jupyter notebooks
├── main.py                    # Run the system
├── requirements.txt
├── setup_guide.md
└── README.md
```

---

## Quick Start

**1. Install dependencies:**
```bash
pip install -r requirements.txt
```

**2. Run the system:**
```bash
python main.py
```

**3. Check outputs:**
- Console: Summary statistics
- `data/processed/`: Intermediate results

---

## Data Format

Minimum required columns in CSV:
- `Date` (YYYY-MM-DD)
- `Close` (price)

Optional (for option pricing):
- `Strike`
- `Expiry`
- `OptionPrice`
- `RiskFreeRate`

Place CSV files in `data/raw/`.

---

## Configuration

All parameters: `configs/parameters.yaml`

Key settings:
- Jump detection threshold (default: 3.0 std)
- Volatility decay rates (bull: 0.94, crisis: 0.85)
- Kalman filter noise
- Regime boundaries
- Kelly fraction (default: 0.25)
- Position caps (default: 10% max)

**Do not optimize parameters for profit.**  
They are tuned for stability and robustness.

---

## Design Principles

**Mispricing, not forecasting**  
We detect pricing disagreements, not predict returns.

**Separate jumps from diffusion**  
Jumps contaminate volatility. We estimate σₜ from diffusion returns only.

**Soft regime switching**  
No hard jumps between regimes. Smooth probability-weighted transitions.

**Conservative Kelly**  
Never use full Kelly. Fractional (≤0.25) with uncertainty penalties.

**Stability over performance**  
Calibrated for robustness, not short-term PnL.

---

## Current Status

**Implemented:**
- Jump detection with statistical thresholds
- Regime-aware volatility (EWMA + GARCH)
- Kalman filter for drift estimation
- Regime classification (Bull/Sideways/Crisis)
- BS–Merton pricing
- Mispricing signal generation
- Risk-controlled Kelly sizing
- Complete decision pipeline

**Not yet implemented:**
- Parameter calibration framework
- Backtesting module
- Live data feeds
- Greeks-based risk overlays

---

## Testing

Run unit tests:
```bash
python tests/test_jump_detector.py
```

Run individual modules:
```bash
python modules/jump_detector.py
python modules/volatility_engine.py
python modules/drift_engine.py
```

---

## Learning Path

**Week 1:** Understand jump detection  
**Week 2:** Volatility estimation  
**Week 3:** Drift (Kalman filter)  
**Week 4:** Regime detection  
**Week 5:** Pricing models  
**Week 6:** Mispricing + decisions  
**Week 7:** Kelly sizing  
**Week 8:** Full integration

Take your time. This is complex infrastructure.

---

## Important Notes

**This is a research system.**  
Not production-ready. Not for live trading.

**Parameters are NOT optimized.**  
They are intentionally conservative defaults.

**Calibration order matters:**  
1. Jump detection  
2. Volatility  
3. Drift  
4. Regime boundaries  
5. Kelly parameters  

Do not optimize everything simultaneously.

**REFUSE is the most common output.**  
This is correct. Most mispricing signals are noise.

---

## Warnings

⚠️ Do NOT use on real money without:
- Understanding every line of code
- Validating on 2+ years of historical data
- Paper trading for 3+ months
- Proper risk management infrastructure

⚠️ This system does NOT:
- Predict future returns
- Guarantee profits
- Handle execution risk
- Account for transaction costs
- Manage portfolio-level risk

⚠️ Kelly sizing is DANGEROUS if used incorrectly.  
Always use fractional Kelly (0.1 - 0.25).  
Never remove position caps.

---

## Disclaimer

**For educational and research purposes only.**

This software is provided "as is" without warranty of any kind.  
The authors are not responsible for any financial losses.  
Past performance does not guarantee future results.  
Options trading involves substantial risk.

**Not financial advice.**  
Consult a licensed professional before trading.

---

## Documentation

- `setup_guide.md` - Detailed installation instructions
- `notebooks/00_introduction.ipynb` - Interactive tutorial
- Module docstrings - Inline documentation
- `configs/parameters.yaml` - Parameter explanations

---

## License

Research and educational use only.  
Not for commercial deployment without explicit permission.

---