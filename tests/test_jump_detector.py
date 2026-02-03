"""
TEST: Jump Detector Module
===========================

Simple tests to verify jump detection works correctly.
Run this to make sure the module is functioning.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Add modules to path
sys.path.append(str(Path(__file__).parent.parent / 'modules'))

from jump_detector import JumpDetector, calculate_log_returns


def test_log_returns():
    """Test log return calculation."""
    print("\n🧪 Testing log return calculation...")
    
    # Simple price series
    prices = pd.Series([100, 105, 110, 108, 115])
    returns = calculate_log_returns(prices)
    
    # Check length (should be n-1)
    assert len(returns) == len(prices) - 1, "Wrong return length"
    
    # Check first return manually
    expected_first = np.log(105 / 100)
    assert np.isclose(returns.iloc[0], expected_first), "Wrong return value"
    
    print("   ✅ Log returns OK")


def test_jump_detection():
    """Test jump detection on synthetic data."""
    print("\n🧪 Testing jump detection...")
    
    # Create data with known jumps
    np.random.seed(42)
    normal_returns = np.random.normal(0, 0.01, 100)
    
    # Add 3 obvious jumps
    normal_returns[20] = 0.08  # Big positive jump
    normal_returns[50] = -0.07  # Big negative jump
    normal_returns[80] = 0.09  # Another jump
    
    returns = pd.Series(normal_returns)
    
    # Detect jumps
    detector = JumpDetector(threshold=3.0, window=20)
    is_jump, jump_rets, diffusion_rets = detector.detect_jumps(returns)
    
    # Should detect at least 2 of the 3 jumps
    assert is_jump.sum() >= 2, f"Only detected {is_jump.sum()} jumps, expected >= 2"
    
    # Check that jump_returns and diffusion_returns are complementary
    total_check = (jump_rets + diffusion_rets - returns).abs().sum()
    assert total_check < 1e-10, "Jump and diffusion don't sum to original returns"
    
    print(f"   ✅ Detected {is_jump.sum()} jumps (expected ~3)")


def test_jump_parameters():
    """Test jump parameter estimation."""
    print("\n🧪 Testing jump parameter estimation...")
    
    # Create jump returns
    jump_returns = pd.Series([0, 0, 0.05, 0, -0.06, 0, 0, 0.04, 0])
    
    detector = JumpDetector()
    params = detector.estimate_jump_parameters(jump_returns)
    
    # Check structure
    assert 'mu_j' in params, "Missing mu_j"
    assert 'sigma_j' in params, "Missing sigma_j"
    assert 'lambda' in params, "Missing lambda"
    
    # Lambda should be 3/9 = 0.333
    expected_lambda = 3.0 / 9.0
    assert np.isclose(params['lambda'], expected_lambda), f"Wrong lambda: {params['lambda']}"
    
    print("   ✅ Jump parameters OK")


def test_empty_data():
    """Test handling of edge cases."""
    print("\n🧪 Testing edge cases...")
    
    # Very short series
    short_returns = pd.Series([0.01, -0.02, 0.015])
    
    detector = JumpDetector(min_observations=30)
    is_jump, _, _ = detector.detect_jumps(short_returns)
    
    # Should return all False (insufficient data)
    assert is_jump.sum() == 0, "Should not detect jumps with insufficient data"
    
    print("   ✅ Edge cases handled correctly")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("RUNNING JUMP DETECTOR TESTS")
    print("="*60)
    
    try:
        test_log_returns()
        test_jump_detection()
        test_jump_parameters()
        test_empty_data()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60 + "\n")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
