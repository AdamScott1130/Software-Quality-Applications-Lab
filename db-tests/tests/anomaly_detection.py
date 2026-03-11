"""
Keycloak Authentication Anomaly Detection
==========================================
Uses scikit-learn Isolation Forest to detect suspicious authentication
patterns in Keycloak's event_entity table.

Anomaly signals:
- High login failure rate from a single IP
- Burst activity (many events in short time window)
- Unusual hour-of-day activity
- Rare/unknown IP addresses

Usage:
    pip install scikit-learn pandas psycopg tabulate
    python anomaly_detection.py
"""

import os
import json
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import psycopg
from psycopg.rows import dict_row
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# ── DB Connection ─────────────────────────────────────────────────────────

def get_conn():
    return psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        dbname=os.getenv("PGDATABASE", "keycloak_db"),
        user=os.getenv("PGUSER", "keycloak"),
        password=os.getenv("PGPASSWORD", "password"),
        row_factory=dict_row,
    )

# ── Feature Engineering ───────────────────────────────────────────────────

def load_events() -> pd.DataFrame:
    """Load raw events from Keycloak event_entity table."""
    query = """
        SELECT
            ip_address,
            type,
            error,
            event_time,
            user_id,
            session_id
        FROM event_entity
        WHERE event_time IS NOT NULL
        ORDER BY event_time ASC
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

    if not rows:
        raise ValueError("No events found in event_entity table.")

    df = pd.DataFrame(rows)
    # Convert epoch milliseconds to datetime
    df["event_dt"] = pd.to_datetime(df["event_time"], unit="ms")
    df["is_error"] = df["type"].isin(["LOGIN_ERROR", "TOKEN_EXCHANGE_ERROR"]).astype(int)
    df["hour"] = df["event_dt"].dt.hour
    return df


def build_ip_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate per-IP features for anomaly detection.

    Features:
    - total_events        : overall activity volume
    - error_count         : number of failed auth attempts
    - error_rate          : proportion of requests that failed
    - unique_users        : distinct user_ids targeted
    - unique_sessions     : distinct sessions initiated
    - avg_hour            : average hour of activity (0-23)
    - hour_std            : spread of activity across hours
    - burst_score         : events concentrated in short time windows
    """
    grouped = df.groupby("ip_address")

    features = pd.DataFrame({
        "total_events":    grouped["type"].count(),
        "error_count":     grouped["is_error"].sum(),
        "error_rate":      grouped["is_error"].mean(),
        "unique_users":    grouped["user_id"].nunique(),
        "unique_sessions": grouped["session_id"].nunique(),
        "avg_hour":        grouped["hour"].mean(),
        "hour_std":        grouped["hour"].std().fillna(0),
    })

    # Burst score: ratio of events to unique time windows (10-min buckets)
    def burst(g):
        buckets = (g["event_time"] // (10 * 60 * 1000)).nunique()
        return len(g) / max(buckets, 1)

    features["burst_score"] = grouped.apply(burst)
    features = features.reset_index()
    return features


# ── Anomaly Detection ─────────────────────────────────────────────────────

def detect_anomalies(features: pd.DataFrame, contamination: float = 0.1) -> pd.DataFrame:
    """
    Run Isolation Forest on IP-level features.

    contamination: expected proportion of anomalies (10% default).
    Returns features df with anomaly_score and is_anomaly columns added.
    """
    feature_cols = [
        "total_events", "error_count", "error_rate",
        "unique_users", "unique_sessions",
        "avg_hour", "hour_std", "burst_score"
    ]

    X = features[feature_cols].values

    # Standardise so no single feature dominates
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=42
    )
    model.fit(X_scaled)

    # score_samples: more negative = more anomalous
    features["anomaly_score"] = model.score_samples(X_scaled)
    features["is_anomaly"] = model.predict(X_scaled) == -1  # -1 = anomaly

    return features, model, scaler, feature_cols


# ── Reporting ─────────────────────────────────────────────────────────────

def print_report(features: pd.DataFrame):
    anomalies = features[features["is_anomaly"]].sort_values("anomaly_score")
    normal    = features[~features["is_anomaly"]]

    print("\n" + "="*65)
    print("  KEYCLOAK AUTHENTICATION ANOMALY DETECTION REPORT")
    print("="*65)
    print(f"\n  IPs analysed : {len(features)}")
    print(f"  Normal       : {len(normal)}")
    print(f"  Anomalous    : {len(anomalies)}")

    if anomalies.empty:
        print("\n  ✅ No anomalies detected.")
        return

    print("\n" + "-"*65)
    print("  FLAGGED IPs")
    print("-"*65)

    for _, row in anomalies.iterrows():
        reasons = []
        if row["error_rate"] > 0.5:
            reasons.append(f"high failure rate ({row['error_rate']:.0%})")
        if row["burst_score"] > 5:
            reasons.append(f"burst activity (score {row['burst_score']:.1f})")
        if row["unique_users"] > 3:
            reasons.append(f"targeting {int(row['unique_users'])} different users")
        if row["total_events"] > features["total_events"].quantile(0.9):
            reasons.append(f"high volume ({int(row['total_events'])} events)")
        if not reasons:
            reasons.append("unusual pattern combination")

        print(f"\n  🚨 IP: {row['ip_address']}")
        print(f"     Score       : {row['anomaly_score']:.4f}  (lower = more suspicious)")
        print(f"     Events      : {int(row['total_events'])}  |  Errors: {int(row['error_count'])}  |  Error rate: {row['error_rate']:.0%}")
        print(f"     Users hit   : {int(row['unique_users'])}  |  Burst score: {row['burst_score']:.1f}")
        print(f"     Avg hour    : {row['avg_hour']:.1f}  |  Hour spread: {row['hour_std']:.1f}")
        print(f"     ⚠ Signals  : {', '.join(reasons)}")

    print("\n" + "-"*65)
    print("  NORMAL ACTIVITY SUMMARY")
    print("-"*65)
    print(f"  Avg events/IP   : {normal['total_events'].mean():.1f}")
    print(f"  Avg error rate  : {normal['error_rate'].mean():.0%}")
    print(f"  Avg burst score : {normal['burst_score'].mean():.1f}")
    print("="*65 + "\n")


# ── Pytest-compatible test ────────────────────────────────────────────────

def test_anomaly_detection_runs():
    """
    Integration test: verifies the full pipeline runs against
    the live Keycloak DB and returns expected output shape.
    Can be run with: pytest anomaly_detection.py -v
    """
    df = load_events()
    assert len(df) > 0, "No events loaded from DB"

    features = build_ip_features(df)
    assert "error_rate" in features.columns
    assert "burst_score" in features.columns
    assert len(features) > 0

    features, model, scaler, feature_cols = detect_anomalies(features)
    assert "is_anomaly" in features.columns
    assert "anomaly_score" in features.columns

    # At least one anomaly should be detected with seeded data
    assert features["is_anomaly"].sum() >= 1, "Expected at least one anomaly"

    # The known suspicious IP should be flagged
    suspicious = features[features["ip_address"] == "185.220.101.45"]
    if not suspicious.empty:
        assert suspicious.iloc[0]["is_anomaly"], \
            "Known suspicious IP 185.220.101.45 should be flagged as anomaly"

    print(f"\n✅ Anomaly detection test passed — {features['is_anomaly'].sum()} anomalies detected")


# ── Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nLoading Keycloak events from PostgreSQL...")
    df = load_events()
    print(f"Loaded {len(df)} events from {df['ip_address'].nunique()} unique IPs")

    print("Engineering features per IP address...")
    features = build_ip_features(df)

    print("Running Isolation Forest anomaly detection...")
    features, model, scaler, feature_cols = detect_anomalies(features)

    print_report(features)