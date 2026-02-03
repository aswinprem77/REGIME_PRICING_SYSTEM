# DETAILED SETUP GUIDE
# ====================
# Complete step-by-step instructions for beginners

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [VS Code Setup](#vs-code-setup)
4. [Testing Your Setup](#testing-your-setup)
5. [Common Issues](#common-issues)
6. [Next Steps](#next-steps)

---

## Prerequisites

### What You Need
1. **Python 3.9 or higher**
   - Check version: Open terminal/command prompt and type `python --version`
   - If not installed or version < 3.9, download from [python.org](https://python.org)
   
2. **VS Code (Visual Studio Code)**
   - Download from [code.visualstudio.com](https://code.visualstudio.com)
   
3. **Git** (optional but recommended)
   - Download from [git-scm.com](https://git-scm.com)

---

## Installation

### Step 1: Download the Project
If you have the project as a ZIP file:
1. Extract it to a folder (e.g., `C:\Users\YourName\Projects\regime_pricing_system`)
2. Remember this location!

If using Git:
```bash
git clone <repository-url>
cd regime_pricing_system
```

### Step 2: Open Terminal
**Windows:**
- Press `Win + R`, type `cmd`, press Enter

**Mac/Linux:**
- Press `Cmd + Space`, type "Terminal", press Enter

### Step 3: Navigate to Project Folder
```bash
cd path/to/regime_pricing_system
```

For example:
```bash
cd C:\Users\YourName\Projects\regime_pricing_system
```

### Step 4: Create Virtual Environment (Recommended)
This keeps your project's packages separate from other Python projects.

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

### Step 5: Install Required Packages
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will take a few minutes. You'll see packages being downloaded and installed.

**Expected Output:**
```
Collecting numpy>=1.24.0
  Downloading numpy-1.24.3-cp39-cp39-win_amd64.whl
Installing collected packages: numpy, pandas, ...
Successfully installed numpy-1.24.3 pandas-2.0.1 ...
```

---

## VS Code Setup

### Step 1: Open Project in VS Code
1. Open VS Code
2. File → Open Folder
3. Select your `regime_pricing_system` folder

### Step 2: Install Python Extension
1. Click Extensions icon (left sidebar) or press `Ctrl+Shift+X`
2. Search for "Python"
3. Install the one by Microsoft (it has a blue checkmark)

### Step 3: Select Python Interpreter
1. Press `Ctrl+Shift+P` (Command Palette)
2. Type "Python: Select Interpreter"
3. Choose the one that shows `('venv': venv)`

### Step 4: Open Integrated Terminal
1. View → Terminal (or press `Ctrl+~`)
2. You should see `(venv)` in the terminal prompt
3. If not, activate the venv again (see Step 4 of Installation)

---

## Testing Your Setup

### Test 1: Check Python and Packages
In VS Code terminal:
```bash
python -c "import numpy; import pandas; print('✅ Core packages OK')"
```

Expected output: `✅ Core packages OK`

### Test 2: Run Jump Detector Test
```bash
cd modules
python jump_detector.py
```

Expected output:
```
JUMP DETECTION RESULTS
=====================
Total observations: 500
Jumps detected: 10
Jump percentage: 2.00%
...
✅ Jump detector test complete
```

### Test 3: Run Volatility Engine Test
```bash
python volatility_engine.py
```

Expected output:
```
VOLATILITY ENGINE RESULTS
========================
Mean volatility: 0.0xxx
...
✅ Volatility engine test complete
```

### Test 4: Run Drift Engine Test
```bash
python drift_engine.py
```

Expected output:
```
DRIFT ENGINE RESULTS
===================
Mean drift: 0.000xxx
...
✅ Drift engine test complete
```

---

## Common Issues

### Issue 1: "Python not found"
**Solution:**
- Make sure Python is installed
- During installation, check "Add Python to PATH"
- Restart your terminal after installation

### Issue 2: "pip not found"
**Solution:**
```bash
python -m ensurepip --upgrade
```

### Issue 3: "Module not found" errors
**Solution:**
```bash
pip install --upgrade -r requirements.txt
```

### Issue 4: Virtual environment not activating
**Windows:**
- You might need to enable script execution:
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Mac/Linux:**
- Make sure you're using `source venv/bin/activate`, not `activate` alone

### Issue 5: Package installation fails
**Solution:**
- Update pip first:
```bash
python -m pip install --upgrade pip
```
- Try installing packages one by one:
```bash
pip install numpy
pip install pandas
# etc.
```

### Issue 6: GARCH model fails
**Solution:**
- Make sure arch package is installed:
```bash
pip install arch
```

---

## Next Steps

### Week 1: Understand the Data
1. Read `docs/ARCHITECTURE.md` (we'll create this next)
2. Create a simple CSV with test data
3. Run `notebooks/01_data_exploration.ipynb` (we'll create this)

### Week 2: Test Each Module
1. Study `modules/jump_detector.py`
2. Create your own test data
3. Experiment with parameters in `configs/parameters.yaml`

### Week 3: Integration
1. Run the full pipeline
2. Understand how modules connect
3. Visualize outputs

---

## Folder Structure Reminder

```
regime_pricing_system/
│
├── data/
│   ├── raw/              ← Put your CSV files here
│   └── processed/        ← System will create processed data here
│
├── modules/              ← Core components (don't edit yet)
│   ├── jump_detector.py
│   ├── volatility_engine.py
│   ├── drift_engine.py
│   └── ...
│
├── tests/                ← Unit tests (run these first)
├── notebooks/            ← Jupyter notebooks for learning
├── configs/              ← Parameters (edit carefully)
├── docs/                 ← Documentation
├── logs/                 ← System logs (created automatically)
│
├── requirements.txt      ← Package list
├── README.md            ← Start here
└── main.py              ← Run the full system
```

---

## Data Format

Your CSV should have these columns:
- `Date` (YYYY-MM-DD format)
- `Close` (closing price)
- `Strike` (option strike price)
- `Expiry` (option expiry date)
- `OptionPrice` (market option price)
- `RiskFreeRate` (annual rate, e.g., 0.04 for 4%)

Example:
```csv
Date,Close,Strike,Expiry,OptionPrice,RiskFreeRate
2023-01-01,100,105,2023-02-01,2.50,0.04
2023-01-02,101,105,2023-02-01,2.75,0.04
...
```

---

## Getting Help

1. **Read the module docstrings**
   - Every file has detailed comments
   - Functions explain what they do

2. **Check the logs**
   - Logs are in `logs/` folder
   - They show what the system is doing

3. **Run tests**
   - Tests show correct usage
   - Located in `tests/` folder

4. **Read examples**
   - Bottom of each module file has example usage
   - Run them: `python modules/module_name.py`

---

## Safety Checklist

Before running on real data:
- [ ] All tests pass
- [ ] You understand each module
- [ ] Parameters make sense
- [ ] You've tested on synthetic data
- [ ] You've read all documentation
- [ ] You understand the risks

**Remember: This is a research system, not production-ready!**

---

## Quick Reference Commands

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install packages
pip install -r requirements.txt

# Run a module test
python modules/jump_detector.py

# Run unit tests
python -m pytest tests/

# Deactivate virtual environment
deactivate
```

---

## Congratulations! 🎉

Your environment is now set up. Take your time to:
1. Understand the architecture
2. Read the code
3. Run the examples
4. Experiment with synthetic data

Don't rush. This is complex quantitative finance. Build understanding gradually.

**Next:** Read `README.md` and start with `notebooks/00_introduction.ipynb`
