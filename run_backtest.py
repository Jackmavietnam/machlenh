from __future__ import annotations

import argparse

from src.backtest.walkforward import run_walkforward_backtest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--label-horizon', type=int, default=5)
    args = parser.parse_args()
    run_walkforward_backtest(label_horizon=args.label_horizon)


if __name__ == '__main__':
    main()
