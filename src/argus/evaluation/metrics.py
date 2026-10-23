"""Evaluation metrics for outbreak detection."""
from __future__ import annotations

import pandas as pd


def define_onsets(
    df: pd.DataFrame, p90_window: int = 52, min_consecutive: int = 2
) -> pd.Series:
    """Identify ground-truth outbreak onset dates from observed data.

    Definition: A week is an onset if the observed value exceeds the trailing
    90th percentile for at least `min_consecutive` consecutive weeks, and it is
    the FIRST week of that run.

    Returns:
        A boolean Series aligned with df.index, True where onset occurred.
    """
    df = df.copy()
    # Compute trailing 90th percentile (exclusive of current week)
    min_periods = max(3, p90_window // 4)
    df["p90"] = df["observed"].rolling(window=p90_window, min_periods=min_periods).quantile(0.90)

    # Define raw excursions
    df["excursion"] = df["observed"] > df["p90"]

    # A run of True values >= min_consecutive
    # We find runs and mark the first index of valid runs
    is_onset = pd.Series(False, index=df.index)

    # Simple loop to find runs (runs are short, so this is fine)
    run_start = None
    for i in range(len(df)):
        if df["excursion"].iloc[i]:
            if run_start is None:
                run_start = i
        else:
            if run_start is not None:
                if (i - run_start) >= min_consecutive:
                    is_onset.iloc[run_start] = True
                run_start = None
    # Handle run ending at the last element
    if run_start is not None and (len(df) - run_start) >= min_consecutive:
        is_onset.iloc[run_start] = True

    return is_onset


def compute_metrics(alerts_df: pd.DataFrame, p90_window: int = 52) -> dict:
    """Compute sensitivity, specificity, and lead time from a backtest run."""
    if alerts_df.empty or len(alerts_df) < 10:
        return {
            "sensitivity": 0.0,
            "specificity": 1.0,
            "false_alarm_rate": 0.0,
            "lead_time_median_days": None,
            "n_onsets": 0,
        }

    df = alerts_df.copy()
    # Warmup placeholder for rolling window
    df["onset"] = define_onsets(df, p90_window=p90_window, min_consecutive=2)

    # True Positives: alert occurs within 0-2 weeks AFTER an onset
    # (Alerting before the definition of onset is a bonus lead time)
    
    # We evaluate weekly overlap: for every onset, did we alert within +/- 2 weeks?
    onsets = df[df["onset"]]
    alerts = df[df["alert"]]

    tp = 0
    lead_times = []

    for idx, onset_row in onsets.iterrows():
        onset_time = onset_row["timestamp"]
        
        # Look for an alert in the window [onset - 4 weeks, onset + 2 weeks]
        window_start = onset_time - pd.Timedelta(weeks=4)
        window_end = onset_time + pd.Timedelta(weeks=2)
        
        hits = alerts[
            (alerts["timestamp"] >= window_start) & 
            (alerts["timestamp"] <= window_end)
        ]
        
        if not hits.empty:
            tp += 1
            # First alert in window
            first_alert_time = hits["timestamp"].min()
            lead_time = (onset_time - first_alert_time).days
            lead_times.append(lead_time)

    n_onsets = len(onsets)
    n_alerts = len(alerts)
    n_weeks = len(df)
    n_negative_weeks = n_weeks - n_onsets

    # False alarms: alerts that didn't hit an onset
    fp = n_alerts - tp
    # Adjust negative weeks roughly (deduct 1 week for each onset)
    n_negative_weeks = max(1, n_weeks - n_onsets - (tp * 1)) 

    sensitivity = tp / n_onsets if n_onsets > 0 else 0.0
    false_alarm_rate = fp / n_negative_weeks if n_negative_weeks > 0 else 0.0
    specificity = 1.0 - false_alarm_rate

    lead_time_median = float(pd.Series(lead_times).median()) if lead_times else None

    return {
        "sensitivity": float(sensitivity),
        "specificity": float(specificity),
        "false_alarm_rate": float(false_alarm_rate),
        "lead_time_median_days": lead_time_median,
        "n_onsets": n_onsets,
        "n_alerts": n_alerts,
    }