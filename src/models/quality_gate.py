from __future__ import annotations

from pathlib import Path
import json
import pandas as pd


def evaluate_quality_gate(artifacts_dir: Path, cfg: dict) -> dict:
    gate_cfg = cfg.get('quality_gate', {})
    result = {
        'enabled': bool(gate_cfg.get('enabled', True)),
        'passed': True,
        'reasons': [],
        'max_alerts_override': None,
    }
    if not result['enabled']:
        return result

    train_path = artifacts_dir / 'train_report_label_5d.csv'
    bt_path = artifacts_dir / 'backtest_summary_label_5d.csv'
    if not train_path.exists() or not bt_path.exists():
        result['passed'] = False
        result['reasons'].append('thieu train_report hoac backtest_summary de danh gia quality gate')
    else:
        train_df = pd.read_csv(train_path)
        bt_df = pd.read_csv(bt_path)
        if train_df.empty or bt_df.empty:
            result['passed'] = False
            result['reasons'].append('train_report hoac backtest_summary rong')
        else:
            best_train_auc = float(train_df['auc'].max())
            best_train_precision = float(train_df['precision'].max())
            best_bt_auc = float(bt_df['auc_bt'].max())
            best_bt_precision = float(bt_df['precision_bt'].max())
            best_bt_avg_return = float(bt_df['avg_return'].max())

            if best_train_auc < float(gate_cfg.get('min_train_auc', 0.55)):
                result['passed'] = False
                result['reasons'].append(f'train_auc thap: {best_train_auc:.4f}')
            if best_train_precision < float(gate_cfg.get('min_train_precision', 0.28)):
                result['passed'] = False
                result['reasons'].append(f'train_precision thap: {best_train_precision:.4f}')
            if best_bt_auc < float(gate_cfg.get('min_backtest_auc', 0.57)):
                result['passed'] = False
                result['reasons'].append(f'backtest_auc thap: {best_bt_auc:.4f}')
            if best_bt_precision < float(gate_cfg.get('min_backtest_precision', 0.50)):
                result['passed'] = False
                result['reasons'].append(f'backtest_precision thap: {best_bt_precision:.4f}')
            if best_bt_avg_return < float(gate_cfg.get('min_backtest_avg_return', 0.0)):
                result['passed'] = False
                result['reasons'].append(f'backtest_avg_return am/yeu: {best_bt_avg_return:.4f}')

    if (not result['passed']) and bool(gate_cfg.get('downgrade_alerts_if_fail', True)):
        result['max_alerts_override'] = int(gate_cfg.get('max_alerts_when_degraded', 4))

    out = artifacts_dir / 'quality_gate_label_5d.json'
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result
