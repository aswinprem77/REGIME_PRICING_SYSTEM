"""
JUMP DETECTOR
=============

Purpose: Identify discontinuous jumps in price data (crashes, spikes)
Why: Jumps pollute volatility estimates - we need to separate them

Method: Statistical threshold based on standardized returns
Output: Boolean array marking jump days + cleaned returns

Author: Regime Pricing System
Date: 2026-01-30
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
from loguru import logger


class JumpDetector:
    """
    Detects jumps in return series using statistical thresholds.
    
    Jumps are defined as returns exceeding K standard deviations from normal.
    These are removed before volatility estimation to avoid contamination.
    
    Parameters:
    -----------
    threshold : float
        Number of standard deviations to qualify as jump (default: 3.0)
        Higher = fewer jumps detected
        Lower = more sensitive
        
    window : int
        Rolling window for calculating std (default: 20 days)
        Smaller = more reactive
        Larger = more stable
        
    min_observations : int
        Minimum data points needed before detecting jumps (default: 30)
    """
    
    def __init__(
        self, 
        threshold: float = 3.0,
        window: int = 20,
        min_observations: int = 30
    ):
        """Initialize the jump detector with parameters."""
        self.threshold = threshold
        self.window = window
        self.min_observations = min_observations
        
        logger.info(f"JumpDetector initialized with threshold={threshold}, window={window}")
        
    def detect_jumps(
        self, 
        returns: pd.Series,
        use_robust: bool = True
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Detect jumps in a return series.
        
        Parameters:
        -----------
        returns : pd.Series
            Log returns (NOT prices!)
        use_robust : bool
            If True, use median absolute deviation (more stable)
            If False, use standard deviation
            
        Returns:
        --------
        is_jump : pd.Series (boolean)
            True on days with detected jumps
        jump_returns : pd.Series
            Returns on jump days, 0 elsewhere
        diffusion_returns : pd.Series
            Returns with jumps removed (replaced by 0)
            
        Example:
        --------
        >>> detector = JumpDetector(threshold=3.0)
        >>> is_jump, jumps, diffusion = detector.detect_jumps(returns)
        >>> print(f"Found {is_jump.sum()} jumps out of {len(returns)} days")
        """
        
        # Validate input
        if len(returns) < self.min_observations:
            logger.warning(f"Only {len(returns)} observations, need {self.min_observations}")
            # Return all False (no jumps detected)
            return (
                pd.Series(False, index=returns.index),
                pd.Series(0.0, index=returns.index),
                returns.copy()
            )
        
        # Remove NaN values
        returns_clean = returns.dropna()
        
        if use_robust:
            # Median Absolute Deviation (more resistant to outliers)
            rolling_median = returns_clean.rolling(window=self.window, min_periods=5).median()
            rolling_mad = (returns_clean - rolling_median).abs().rolling(
                window=self.window, min_periods=5
            ).median()
            # MAD to std conversion factor (assumes normal distribution)
            rolling_std = rolling_mad * 1.4826
        else:
            # Standard rolling std
            rolling_std = returns_clean.rolling(window=self.window, min_periods=5).std()
        
        # Standardized returns (Z-score)
        z_scores = (returns_clean - returns_clean.rolling(
            window=self.window, min_periods=5
        ).mean()) / rolling_std
        
        # Mark jumps where |Z| > threshold
        is_jump = (z_scores.abs() > self.threshold).fillna(False)
        
        # Align with original index
        is_jump = is_jump.reindex(returns.index, fill_value=False)
        
        # Separate returns
        jump_returns = returns.copy()
        jump_returns[~is_jump] = 0.0
        
        diffusion_returns = returns.copy()
        diffusion_returns[is_jump] = 0.0
        
        # Log results
        n_jumps = is_jump.sum()
        pct_jumps = 100 * n_jumps / len(returns)
        logger.info(f"Detected {n_jumps} jumps ({pct_jumps:.2f}% of data)")
        
        if n_jumps > 0:
            avg_jump_size = jump_returns[is_jump].abs().mean()
            logger.info(f"Average jump magnitude: {avg_jump_size:.4f}")
        
        return is_jump, jump_returns, diffusion_returns
    
    def estimate_jump_parameters(
        self, 
        jump_returns: pd.Series
    ) -> dict:
        """
        Estimate jump size distribution parameters.
        
        Parameters:
        -----------
        jump_returns : pd.Series
            Returns on jump days (output from detect_jumps)
            
        Returns:
        --------
        dict with:
            mu_j : float (mean jump size)
            sigma_j : float (jump volatility)
            lambda : float (jump intensity - jumps per day)
            
        These are used in Merton jump-diffusion pricing.
        """
        # Filter to actual jumps (non-zero)
        jumps_only = jump_returns[jump_returns != 0]
        
        if len(jumps_only) == 0:
            logger.warning("No jumps found for parameter estimation")
            return {
                'mu_j': 0.0,
                'sigma_j': 0.0,
                'lambda': 0.0
            }
        
        # Jump size stats
        mu_j = jumps_only.mean()
        sigma_j = jumps_only.std()
        
        # Jump intensity (frequency)
        total_days = len(jump_returns)
        n_jumps = len(jumps_only)
        lambda_j = n_jumps / total_days  # jumps per day
        
        logger.info(f"Jump parameters: μⱼ={mu_j:.4f}, σⱼ={sigma_j:.4f}, λ={lambda_j:.4f}")
        
        return {
            'mu_j': mu_j,
            'sigma_j': sigma_j,
            'lambda': lambda_j
        }
    
    def visualize_jumps(
        self, 
        returns: pd.Series,
        is_jump: pd.Series,
        save_path: Optional[str] = None
    ):
        """
        Create visualization of detected jumps.
        
        Parameters:
        -----------
        returns : pd.Series
            Original returns
        is_jump : pd.Series
            Jump detection results
        save_path : str, optional
            If provided, save plot to this path
        """
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 8))
        
        # Plot 1: Returns with jumps highlighted
        axes[0].plot(returns.index, returns.values, label='Returns', alpha=0.7)
        axes[0].scatter(
            returns.index[is_jump], 
            returns.values[is_jump],
            color='red', 
            s=100, 
            label='Detected Jumps',
            zorder=5
        )
        axes[0].axhline(y=0, color='black', linestyle='--', alpha=0.3)
        axes[0].set_ylabel('Log Return')
        axes[0].set_title('Return Series with Jump Detection')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Plot 2: Histogram of returns (jumps vs diffusion)
        diffusion = returns[~is_jump]
        jumps = returns[is_jump]
        
        axes[1].hist(diffusion, bins=50, alpha=0.7, label='Diffusion', density=True)
        axes[1].hist(jumps, bins=20, alpha=0.7, label='Jumps', density=True, color='red')
        axes[1].set_xlabel('Return')
        axes[1].set_ylabel('Density')
        axes[1].set_title('Return Distribution: Diffusion vs Jumps')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150)
            logger.info(f"Plot saved to {save_path}")
        else:
            plt.show()
        
        plt.close()


# ============================================================================
# HELPER FUNCTIONS (for beginners)
# ============================================================================

def calculate_log_returns(prices: pd.Series) -> pd.Series:
    """
    Convert prices to log returns.
    
    Why log returns?
    - Time-additive (easier math)
    - Symmetric (up 10% then down 10% = net change)
    - Better statistical properties
    
    Formula: r_t = log(P_t / P_{t-1})
    """
    return np.log(prices / prices.shift(1)).dropna()


# ============================================================================
# EXAMPLE USAGE (run this file directly to test)
# ============================================================================

if __name__ == "__main__":
    # Configure logging
    logger.add("logs/jump_detector.log", rotation="1 MB")
    
    # Generate synthetic data for testing
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=500, freq='D')
    
    # Simulate returns with occasional jumps
    normal_returns = np.random.normal(0.0005, 0.02, size=500)
    
    # Add some jumps (10 random big moves)
    jump_indices = np.random.choice(500, size=10, replace=False)
    normal_returns[jump_indices] += np.random.choice([-1, 1], size=10) * np.random.uniform(0.05, 0.15, size=10)
    
    returns = pd.Series(normal_returns, index=dates, name='returns')
    
    # Initialize detector
    detector = JumpDetector(threshold=3.0, window=20)
    
    # Detect jumps
    is_jump, jump_rets, diffusion_rets = detector.detect_jumps(returns)
    
    # Estimate parameters
    params = detector.estimate_jump_parameters(jump_rets)
    
    # Print results
    print("\n" + "="*60)
    print("JUMP DETECTION RESULTS")
    print("="*60)
    print(f"Total observations: {len(returns)}")
    print(f"Jumps detected: {is_jump.sum()}")
    print(f"Jump percentage: {100 * is_jump.sum() / len(returns):.2f}%")
    print(f"\nJump parameters:")
    print(f"  Mean jump size (μⱼ): {params['mu_j']:.4f}")
    print(f"  Jump volatility (σⱼ): {params['sigma_j']:.4f}")
    print(f"  Jump intensity (λ): {params['lambda']:.4f} jumps/day")
    print("="*60 + "\n")
    
    # Visualize
    detector.visualize_jumps(returns, is_jump, save_path='../docs/jump_detection_example.png')
    
    print("✅ Jump detector test complete. Check ../docs/jump_detection_example.png")
