# Regime-Aware BS–Merton Pricing + Kelly Allocation System

## What This System Does

This is a **decision engine** that tells you:
- **BUY / SELL / REFUSE** (should you trade?)
- **POSITION SIZE** (how much to risk?)

It's NOT a prediction model. It's a **pricing disagreement detector** with smart risk control.

---

## 📁 Project Structure

```
regime_pricing_system/
│
├── data/                  # Your price data goes here
│   ├── raw/              # Original CSV files
│   └── processed/        # Cleaned data
│
├── modules/              # Core system components
│   ├── jump_detector.py      # Finds jumps in returns
│   ├── volatility_engine.py  # Calculates σₜ
│   ├── drift_engine.py       # Calculates μₜ (Kalman filter)
│   ├── regime_detector.py    # Bull/Sideways/Crisis detection
│   ├── pricing.py            # BS + Merton pricing
│   ├── mispricing.py         # Market vs Model comparison
│   ├── kelly_sizer.py        # Position sizing
│   └── decision_engine.py    # Final BUY/SELL/REFUSE output
│
├── tests/                # Test each module
├── notebooks/            # Jupyter notebooks for exploration
├── configs/              # Parameter settings
├── docs/                 # Documentation
│
├── requirements.txt      # Python packages needed
├── setup_guide.md       # Detailed setup instructions
└── main.py              # Run the whole system
```

---

## Quick Start

### Step 1: Install Python
- Download Python 3.9+ from [python.org](https://python.org)
- During installation, **CHECK "Add Python to PATH"**

### Step 2: Open VS Code
- Open this folder in VS Code
- Open Terminal (View → Terminal or Ctrl+`)

### Step 3: Install Required Packages
```bash
pip install -r requirements.txt
```

### Step 4: Prepare Your Data
- Put your price CSV in `data/raw/`
- Required columns: `Date`, `Close`, `Strike`, `Expiry`, `OptionPrice`, `RiskFreeRate`

### Step 5: Run Tests
```bash
python -m pytest tests/
```

### Step 6: Run the System
```bash
python main.py
```

---

## System Pipeline (In Order)

```
1. Prices → Log Returns
2. Jump Detection → Separate jumps from diffusion
3. Volatility Engine → Calculate σₜ (regime-aware)
4. Drift Engine → Calculate μₜ (Kalman filter)
5. Regime Detector → Bull/Sideways/Crisis probabilities
6. Effective Parameters → Smooth regime transitions
7. BS–Merton Pricing → Model price
8. Mispricing → ΔCₜ = Model - Market
9. Decision Logic → BUY/SELL/REFUSE
10. Kelly Sizing → How much to allocate
```

**Order is critical. Don't skip steps.**

---

## 🎓 Learning Path (For Beginners)

### 1: Understand the Data
- Run `notebooks/01_data_exploration.ipynb`
- Learn what log returns are
- Visualize price movements

### 2: Jump Detection
- Study `modules/jump_detector.py`
- Run `tests/test_jump_detector.py`
- Understand why we separate jumps

### 3: Volatility
- Study `modules/volatility_engine.py`
- Learn EWMA, GARCH
- See regime differences

### 4: Drift (Kalman Filter)
- Study `modules/drift_engine.py`
- Understand state-space models
- Run the Kalman filter

### 5: Regimes
- Study `modules/regime_detector.py`
- Learn Bull/Sideways/Crisis detection
- Soft switching logic

### 6: Pricing
- Study `modules/pricing.py`
- Black-Scholes formula
- Merton jump-diffusion

### 7: Integration
- Run full pipeline
- Understand mispricing
- Test decision logic

### 8: Kelly Sizing
- Study `modules/kelly_sizer.py`
- Learn fractional Kelly
- Understand risk controls

---

## ⚙️ Configuration

All parameters are in `configs/parameters.yaml`:

```yaml
jump_detection:
  threshold: 3.0  # Standard deviations
  
volatility:
  bull_ewma_lambda: 0.94
  crisis_ewma_lambda: 0.85
  
kelly:
  fraction: 0.25  # Never use full Kelly!
  max_position: 0.10  # 10% max
```

**NEVER touch these until you understand each module.**



## Key Concepts (Simple Explanations)

**Log Returns**: % change in price (safer math than raw %)

**Jump**: Huge sudden move (crisis, news)

**Diffusion**: Normal random wiggling

**Volatility (σ)**: How much prices swing daily

**Drift (μ)**: Average direction of movement

**Regime**: Market mood (Bull/Sideways/Crisis)

**Mispricing**: Your model price ≠ market price

**Kelly**: Math formula for bet sizing (we use fractional)

---

## 🎯 What Success Looks Like

✅ All tests pass  
✅ Regimes detected correctly on historical data  
✅ Volatility estimates are smooth  
✅ Jump detection finds obvious crashes  
✅ Kelly never suggests >10% position  
✅ REFUSE is the most common decision (this is good!)  

🚨 **Parameters are NOT optimized yet** (that comes later)

---


**thank you**
