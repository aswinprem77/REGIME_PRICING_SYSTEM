"""
VOLATILITY ENGINE
=================

Purpose: Estimate time-varying volatility σₜ with regime awareness
Why: Volatility is the dominant pricing input and risk measure

Methods: 
- Bull regime: Slow EWMA
- Sideways: GARCH(1,1)
- Crisis: Fast EWMA (jumps excluded)

CRITICAL: Jumps NEVER enter σₜ estimation

Author: Regime Pricing System
Date: 2026-01-30
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
from arch import arch_model
from loguru import logger


class VolatilityEngine:
    """
    Regime-aware volatility estimation engine.
    
    Each regime uses a different model:
    - Bull: EWMA with slow decay (stable trends)
    - Sideways: GARCH(1,1) (mean-reverting vol)
    - Crisis: EWMA with fast decay (rapid adaptation)
    
    Parameters:
    -----------
    bull_ewma_lambda : float
        EWMA decay for bull regime (default: 0.94)
        Higher = slower reaction, smoother
        
    crisis_ewma_lambda : float
        EWMA decay for crisis regime (default: 0.85)
        Lower = faster reaction to shocks
        
    garch_p : int
        GARCH lag order (default: 1)
        
    garch_q : int
        ARCH lag order (default: 1)
        
    min_variance : float
        Floor for variance estimates (default: 1e-6)
        Prevents division by zero
    """
    
    def __init__(
        self,
        bull_ewma_lambda: float = 0.94,
        crisis_ewma_lambda: float = 0.85,
        garch_p: int = 1,
        garch_q: int = 1,
        min_variance: float = 1e-6
    ):
        """Initialize volatility engine with regime-specific parameters."""
        self.bull_lambda = bull_ewma_lambda
        self.crisis_lambda = crisis_ewma_lambda
        self.garch_p = garch_p
        self.garch_q = garch_q
        self.min_variance = min_variance
        
        logger.info(
            f"VolatilityEngine initialized: "
            f"bull_λ={bull_ewma_lambda}, crisis_λ={crisis_ewma_lambda}"
        )
    
    def ewma_volatility(
        self, 
        returns: pd.Series,
        lambda_decay: float,
        min_periods: int = 20
    ) -> pd.Series:
        """
        Exponentially Weighted Moving Average volatility.
        
        Formula:
            σₜ² = λ * σₜ₋₁² + (1-λ) * rₜ²
        
        Parameters:
        -----------
        returns : pd.Series
            Return series (diffusion only, no jumps!)
        lambda_decay : float
            Decay parameter (0.8 to 0.98)
            Higher = more weight on past
        min_periods : int
            Minimum observations before computing
            
        Returns:
        --------
        volatility : pd.Series
            Time-varying volatility σₜ
        """
        # Square returns for variance
        returns_squared = returns ** 2
        
        # EWMA of squared returns = variance
        variance = returns_squared.ewm(
            alpha=1-lambda_decay,
            min_periods=min_periods,
            adjust=False
        ).mean()
        
        # Apply floor
        variance = variance.clip(lower=self.min_variance)
        
        # Volatility = sqrt(variance)
        volatility = np.sqrt(variance)
        
        return volatility
    
    def garch_volatility(
        self,
        returns: pd.Series,
        p: int = 1,
        q: int = 1
    ) -> pd.Series:
        """
        GARCH(p,q) volatility estimation.
        
        GARCH captures:
        - Volatility clustering
        - Mean reversion
        - Fat tails
        
        Better for sideways regimes where vol oscillates.
        
        Parameters:
        -----------
        returns : pd.Series
            Return series (diffusion only!)
        p : int
            GARCH lag order
        q : int
            ARCH lag order
            
        Returns:
        --------
        conditional_volatility : pd.Series
            GARCH conditional volatility
        """
        try:
            # Scale returns to percentage (GARCH expects this)
            returns_pct = returns * 100
            
            # Fit GARCH model
            # Zero mean model (we handle drift separately)
            model = arch_model(
                returns_pct,
                mean='Zero',
                vol='GARCH',
                p=p,
                q=q,
                rescale=False
            )
            
            # Fit with limited output
            result = model.fit(disp='off', show_warning=False)
            
            # Extract conditional volatility
            cond_vol = result.conditional_volatility
            
            # Convert back to decimal
            cond_vol = cond_vol / 100
            
            # Apply floor
            cond_vol = cond_vol.clip(lower=np.sqrt(self.min_variance))
            
            logger.debug(f"GARCH fitted: ω={result.params['omega']:.6f}")
            
            return cond_vol
            
        except Exception as e:
            logger.warning(f"GARCH fitting failed: {e}. Falling back to EWMA.")
            # Fallback to EWMA
            return self.ewma_volatility(returns, lambda_decay=0.90)
    
    def estimate_regime_volatility(
        self,
        returns: pd.Series,
        regime: str,
        regime_probabilities: Optional[pd.DataFrame] = None
    ) -> pd.Series:
        """
        Estimate volatility for a specific regime.
        
        Parameters:
        -----------
        returns : pd.Series
            Diffusion returns (jumps removed!)
        regime : str
            'bull', 'sideways', or 'crisis'
        regime_probabilities : pd.DataFrame, optional
            If provided, use soft switching
            
        Returns:
        --------
        volatility : pd.Series
            Regime-specific volatility estimate
        """
        if regime == 'bull':
            vol = self.ewma_volatility(returns, lambda_decay=self.bull_lambda)
            logger.info("Computing bull regime volatility (slow EWMA)")
            
        elif regime == 'sideways':
            vol = self.garch_volatility(returns, p=self.garch_p, q=self.garch_q)
            logger.info("Computing sideways regime volatility (GARCH)")
            
        elif regime == 'crisis':
            vol = self.ewma_volatility(returns, lambda_decay=self.crisis_lambda)
            logger.info("Computing crisis regime volatility (fast EWMA)")
            
        else:
            raise ValueError(f"Unknown regime: {regime}")
        
        return vol
    
    def compute_effective_volatility(
        self,
        returns: pd.Series,
        regime_probabilities: pd.DataFrame
    ) -> pd.Series:
        """
        Compute regime-weighted effective volatility.
        
        This is what gets used in pricing:
            σ_eff = Σ P(regime) * σ_regime
            
        Smooth transitions between regimes (no whiplash).
        
        Parameters:
        -----------
        returns : pd.Series
            Diffusion returns (NO JUMPS)
        regime_probabilities : pd.DataFrame
            Columns: ['bull', 'sideways', 'crisis']
            Values: probabilities that sum to 1
            
        Returns:
        --------
        effective_vol : pd.Series
            Smoothly varying volatility
        """
        # Estimate volatility for each regime
        vol_bull = self.estimate_regime_volatility(returns, 'bull')
        vol_sideways = self.estimate_regime_volatility(returns, 'sideways')
        vol_crisis = self.estimate_regime_volatility(returns, 'crisis')
        
        # Align all series
        vol_df = pd.DataFrame({
            'bull': vol_bull,
            'sideways': vol_sideways,
            'crisis': vol_crisis
        }, index=returns.index)
        
        # Weight by regime probabilities
        effective_vol = (
            vol_df['bull'] * regime_probabilities['bull'] +
            vol_df['sideways'] * regime_probabilities['sideways'] +
            vol_df['crisis'] * regime_probabilities['crisis']
        )
        
        logger.info("Computed effective volatility (regime-weighted)")
        
        return effective_vol
    
    def get_volatility_stats(
        self,
        volatility: pd.Series
    ) -> Dict[str, float]:
        """
        Compute summary statistics for volatility series.
        
        Useful for monitoring and validation.
        """
        return {
            'mean': volatility.mean(),
            'std': volatility.std(),
            'min': volatility.min(),
            'max': volatility.max(),
            'median': volatility.median(),
            'current': volatility.iloc[-1] if len(volatility) > 0 else np.nan
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def annualize_volatility(
    daily_vol: pd.Series,
    periods_per_year: int = 252
) -> pd.Series:
    """
    Convert daily volatility to annual.
    
    Formula: σ_annual = σ_daily * sqrt(252)
    
    Use this for reporting, not pricing (pricing uses daily).
    """
    return daily_vol * np.sqrt(periods_per_year)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    logger.add("logs/volatility_engine.log", rotation="1 MB")
    
    # Generate synthetic returns with regime changes
    np.random.seed(42)
    
    # Bull period: low vol
    bull_returns = np.random.normal(0.001, 0.01, size=200)
    
    # Sideways: medium vol, oscillating
    sideways_returns = np.random.normal(0.0, 0.015, size=150)
    
    # Crisis: high vol
    crisis_returns = np.random.normal(-0.002, 0.035, size=150)
    
    all_returns = np.concatenate([bull_returns, sideways_returns, crisis_returns])
    dates = pd.date_range('2020-01-01', periods=len(all_returns), freq='D')
    returns = pd.Series(all_returns, index=dates, name='returns')
    
    # Create synthetic regime probabilities
    regime_probs = pd.DataFrame(index=dates)
    regime_probs['bull'] = 0.0
    regime_probs['sideways'] = 0.0
    regime_probs['crisis'] = 0.0
    
    # Assign regimes
    regime_probs.iloc[:200, 0] = 1.0  # Bull
    regime_probs.iloc[200:350, 1] = 1.0  # Sideways
    regime_probs.iloc[350:, 2] = 1.0  # Crisis
    
    # Initialize engine
    engine = VolatilityEngine(
        bull_ewma_lambda=0.94,
        crisis_ewma_lambda=0.85
    )
    
    # Compute effective volatility
    vol_eff = engine.compute_effective_volatility(returns, regime_probs)
    
    # Get statistics
    stats = engine.get_volatility_stats(vol_eff)
    
    print("\n" + "="*60)
    print("VOLATILITY ENGINE RESULTS")
    print("="*60)
    print(f"Mean volatility: {stats['mean']:.4f}")
    print(f"Volatility std: {stats['std']:.4f}")
    print(f"Min volatility: {stats['min']:.4f}")
    print(f"Max volatility: {stats['max']:.4f}")
    print(f"Current volatility: {stats['current']:.4f}")
    print(f"Annual volatility (current): {annualize_volatility(pd.Series([stats['current']])).iloc[0]:.2%}")
    print("="*60 + "\n")
    
    # Visualization
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    
    # Plot returns
    axes[0].plot(returns.index, returns.values, alpha=0.7, label='Returns')
    axes[0].axhline(y=0, color='black', linestyle='--', alpha=0.3)
    axes[0].set_ylabel('Return')
    axes[0].set_title('Returns (Regime Changes)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Plot volatility
    axes[1].plot(vol_eff.index, vol_eff.values, color='red', label='Effective Volatility')
    axes[1].fill_between(returns.index[:200], 0, vol_eff.max(), alpha=0.2, label='Bull', color='green')
    axes[1].fill_between(returns.index[200:350], 0, vol_eff.max(), alpha=0.2, label='Sideways', color='orange')
    axes[1].fill_between(returns.index[350:], 0, vol_eff.max(), alpha=0.2, label='Crisis', color='red')
    axes[1].set_ylabel('Volatility (σ)')
    axes[1].set_xlabel('Date')
    axes[1].set_title('Regime-Aware Volatility')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../docs/volatility_engine_example.png', dpi=150)
    plt.close()
    
    print("✅ Volatility engine test complete. Check ../docs/volatility_engine_example.png")
