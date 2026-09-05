from __future__ import annotations


def linear_forecast(values: list[float], periods: int = 3) -> dict:
    """Dependency-free least-squares trend forecast with explicit uncertainty proxy."""
    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    denominator = sum((x - x_mean) ** 2 for x in range(n)) or 1
    slope = sum((x - x_mean) * (y - y_mean) for x, y in enumerate(values)) / denominator
    intercept = y_mean - slope * x_mean
    fitted = [intercept + slope * x for x in range(n)]
    mae = sum(abs(actual - predicted) for actual, predicted in zip(values, fitted)) / n
    predicted = [max(0.0, intercept + slope * x) for x in range(n, n + periods)]
    return {
        "method": "ordinary_least_squares_trend",
        "horizon_periods": periods,
        "predicted_requests_per_hour": [round(value, 2) for value in predicted],
        "trend_per_period": round(slope, 2),
        "backtest_mae": round(mae, 2),
    }
