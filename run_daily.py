from __future__ import annotations

import argparse

from src.ingest.pipeline import run_ingest
from src.cleaning.pipeline import run_cleaning
from src.feature_engineering.pipeline import run_feature_engineering
from src.models.train import train_all_models
from src.backtest.walkforward import run_walkforward_backtest
from src.models.predict import generate_predictions
from src.alerts.engine import build_alerts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', required=True)
    parser.add_argument('--end', required=True)
    args = parser.parse_args()

    run_ingest(start=args.start, end=args.end)
    run_cleaning()
    run_feature_engineering()
    train_all_models(label_horizon=5)
    run_walkforward_backtest(label_horizon=5)
    generate_predictions(label_horizon=5)
    build_alerts(label_horizon=5)


if __name__ == '__main__':
    main()
