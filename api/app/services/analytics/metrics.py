"""
Core analytics module — error metrics for wind forecast evaluation.

All calculations use only matched forecast/actual pairs.
MAPE explicitly excludes zero-actual periods and reports the exclusion count.
Sample sizes are tracked per metric to avoid misleading comparisons.

Error sign convention:
  error_mw = forecast_mw - actual_mw
  Positive bias → forecasts overestimated actual wind generation.
  Negative bias → forecasts underestimated actual wind generation.
"""
from __future__ import annotations

import math
import logging
from collections import defaultdict
from datetime import date
from typing import List, Optional, Tuple, Dict

from app.schemas.data_models import MatchedPeriod

log = logging.getLogger(__name__)


def _eligible_pairs(periods: List[MatchedPeriod]) -> List[MatchedPeriod]:
    """Return periods with both forecast and actual available."""
    return [
        p for p in periods
        if p.forecast_mw is not None and p.actual_mw is not None
    ]


def compute_mae(periods: List[MatchedPeriod]) -> Tuple[Optional[float], int]:
    """
    Mean Absolute Error in MW.
    MAE = mean(|forecast - actual|)
    Returns (mae, n_observations).
    """
    eligible = _eligible_pairs(periods)
    if not eligible:
        return None, 0
    mae = sum(p.abs_error_mw for p in eligible) / len(eligible)
    return round(mae, 2), len(eligible)


def compute_rmse(periods: List[MatchedPeriod]) -> Tuple[Optional[float], int]:
    """
    Root Mean Squared Error in MW.
    RMSE = sqrt(mean((forecast - actual)^2))
    Returns (rmse, n_observations).
    """
    eligible = _eligible_pairs(periods)
    if not eligible:
        return None, 0
    mse = sum((p.error_mw ** 2) for p in eligible) / len(eligible)
    return round(math.sqrt(mse), 2), len(eligible)


def compute_bias(periods: List[MatchedPeriod]) -> Tuple[Optional[float], int]:
    """
    Mean signed error (bias) in MW.
    Bias = mean(forecast - actual)
    Positive → over-forecast. Negative → under-forecast.
    Returns (bias, n_observations).
    """
    eligible = _eligible_pairs(periods)
    if not eligible:
        return None, 0
    bias = sum(p.error_mw for p in eligible) / len(eligible)
    return round(bias, 2), len(eligible)


def compute_mape(periods: List[MatchedPeriod]) -> Tuple[Optional[float], int, int]:
    """
    Mean Absolute Percentage Error (%).
    MAPE = mean(|forecast - actual| / |actual|) * 100
    Only computed for periods where actual_mw != 0.

    Returns (mape, n_valid_observations, n_excluded_zero_actual).
    Never divides by zero.
    """
    eligible = _eligible_pairs(periods)
    zero_actual = [p for p in eligible if p.actual_mw == 0]
    valid = [p for p in eligible if p.actual_mw != 0]

    if not valid:
        return None, 0, len(zero_actual)

    mape = sum(abs(p.error_mw) / abs(p.actual_mw) for p in valid) / len(valid) * 100
    return round(mape, 2), len(valid), len(zero_actual)


def compute_all_metrics(periods: List[MatchedPeriod]) -> Dict[str, dict]:
    """
    Compute all four core metrics.

    Returns a dict mapping metric name to its value, sample size, and metadata.
    All metrics use the same eligible sample (forecast + actual available),
    except MAPE which additionally excludes zero-actual periods.
    """
    mae, n_mae = compute_mae(periods)
    rmse, n_rmse = compute_rmse(periods)
    bias, n_bias = compute_bias(periods)
    mape, n_mape, n_mape_excl = compute_mape(periods)

    eligible = _eligible_pairs(periods)

    return {
        "mae": {
            "value": mae,
            "n": n_mae,
            "unit": "MW",
            "definition": "Mean Absolute Error = mean(|forecast − actual|)",
            "interpretation": "Average unsigned forecast deviation in MW. Lower is better.",
        },
        "rmse": {
            "value": rmse,
            "n": n_rmse,
            "unit": "MW",
            "definition": "Root Mean Squared Error = √mean((forecast − actual)²)",
            "interpretation": "Penalises large errors more than MAE. Lower is better.",
        },
        "bias": {
            "value": bias,
            "n": n_bias,
            "unit": "MW",
            "definition": "Mean signed error = mean(forecast − actual)",
            "interpretation": (
                "Positive → forecasts systematically over-estimated actual wind. "
                "Negative → forecasts under-estimated. Close to zero is better."
            ),
        },
        "mape": {
            "value": mape,
            "n": n_mape,
            "n_excluded": n_mape_excl,
            "unit": "%",
            "definition": "Mean Absolute Percentage Error = mean(|forecast − actual| / |actual|) × 100",
            "interpretation": "Relative error. Excludes periods where actual = 0 to avoid division by zero.",
            "excluded_reason": f"{n_mape_excl} period(s) with actual = 0 MW excluded from MAPE." if n_mape_excl else None,
        },
    }


def compute_error_histogram(
    periods: List[MatchedPeriod], n_bins: int = 12
) -> List[Dict[str, float]]:
    """
    Compute histogram bins for the absolute error distribution.
    Returns list of {bin_label, bin_min, bin_max, count}.
    """
    eligible = _eligible_pairs(periods)
    if not eligible:
        return []

    errors = [p.error_mw for p in eligible]
    min_err = min(errors)
    max_err = max(errors)

    if min_err == max_err:
        return [{"bin_label": f"{min_err:.0f}", "bin_min": min_err, "bin_max": max_err, "count": len(errors)}]

    bin_width = (max_err - min_err) / n_bins
    bins = [0] * n_bins

    for e in errors:
        idx = int((e - min_err) / bin_width)
        idx = min(idx, n_bins - 1)
        bins[idx] += 1

    result = []
    for i, count in enumerate(bins):
        lo = min_err + i * bin_width
        hi = lo + bin_width
        label = f"{lo:+.0f} to {hi:+.0f}"
        result.append({"bin_label": label, "bin_min": round(lo, 1), "bin_max": round(hi, 1), "count": count})

    return result


def compute_daily_metrics(periods: List[MatchedPeriod]) -> List[Dict]:
    """
    Break down metrics by delivery date.
    """
    by_date: Dict[date, List[MatchedPeriod]] = defaultdict(list)
    for p in periods:
        by_date[p.delivery_date].append(p)

    result = []
    for d in sorted(by_date.keys()):
        day_periods = by_date[d]
        mae, n_mae = compute_mae(day_periods)
        rmse, _ = compute_rmse(day_periods)
        bias, _ = compute_bias(day_periods)
        mape, n_mape, n_excl = compute_mape(day_periods)
        eligible = _eligible_pairs(day_periods)
        result.append({
            "date": d,
            "mae": mae,
            "rmse": rmse,
            "bias": bias,
            "mape": mape,
            "n_matched": len(eligible),
            "n_mape_excluded": n_excl,
        })
    return result


def compute_coverage(periods: List[MatchedPeriod]) -> Dict[str, int | float]:
    """Compute data coverage statistics."""
    total = len(periods)
    matched = len(_eligible_pairs(periods))
    missing_f = sum(1 for p in periods if p.missing_forecast)
    missing_a = sum(1 for p in periods if p.missing_actual)
    over = sum(1 for p in _eligible_pairs(periods) if p.error_mw > 0)
    under = sum(1 for p in _eligible_pairs(periods) if p.error_mw < 0)

    return {
        "total_expected_periods": total,
        "matched_periods": matched,
        "coverage_pct": round(matched / total * 100, 1) if total else 0.0,
        "missing_forecast_count": missing_f,
        "missing_actual_count": missing_a,
        "over_forecast_count": over,
        "under_forecast_count": under,
    }
