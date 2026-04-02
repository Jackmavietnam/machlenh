from __future__ import annotations

from pathlib import Path
import json
import sqlite3
import pandas as pd

from src.utils.config import load_yaml, resolve_project_paths


def _safe_read_csv(path: Path) -> pd.DataFrame:
    if path.exists() and path.stat().st_size > 0:
        return pd.read_csv(path)
    return pd.DataFrame()


def _safe_read_json(path: Path) -> dict:
    if path.exists() and path.stat().st_size > 0:
        return json.loads(path.read_text(encoding='utf-8'))
    return {}


def _table_count(db_path: Path, table_name: str) -> int:
    if not db_path.exists():
        return 0
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(f'SELECT COUNT(*) FROM {table_name}')
        return int(cur.fetchone()[0])
    except Exception:
        return 0
    finally:
        conn.close()


def _top_feature_lines(feature_df: pd.DataFrame, top_n: int) -> list[str]:
    lines = []
    if feature_df.empty:
        return ['- Chua co feature importance.']
    for model_name, part in feature_df.groupby('model_name'):
        lines.append(f'- {model_name}:')
        for _, row in part.sort_values('importance', ascending=False).head(top_n).iterrows():
            lines.append(f"  - {row['feature']}: importance={float(row['importance']):.6f}, norm={float(row['importance_norm']):.4f}")
    return lines


def main() -> None:
    paths = resolve_project_paths('.')
    cfg = load_yaml('config/model_config.yaml')
    artifacts = paths['artifacts_dir']
    reports_dir = paths['report_dir']
    reports_dir.mkdir(parents=True, exist_ok=True)

    train_df = _safe_read_csv(artifacts / 'train_report_label_5d.csv')
    backtest_summary_df = _safe_read_csv(artifacts / 'backtest_summary_label_5d.csv')
    alert_quality_df = _safe_read_csv(artifacts / 'alert_quality_summary_label_5d.csv')
    alert_df = _safe_read_csv(artifacts / 'alerts_latest_label_5d.csv')
    ranking_df = _safe_read_csv(artifacts / 'ranking_latest_label_5d.csv')
    model_scorecard = _safe_read_csv(artifacts / 'model_selection_scorecard_label_5d.csv')
    feature_importance_df = _safe_read_csv(artifacts / 'feature_importance_label_5d.csv')
    weights_json = _safe_read_json(artifacts / 'ensemble_weights_used_label_5d.json')
    quality_gate = _safe_read_json(artifacts / 'quality_gate_label_5d.json')
    warning_file = artifacts / 'train_warnings_label_5d.txt'
    train_warnings = warning_file.read_text(encoding='utf-8').strip() if warning_file.exists() else ''
    top_n = int(cfg.get('reporting', {}).get('ranking_top_n', 12))
    top_feature_n = int(cfg.get('reporting', {}).get('feature_importance_top_n', 12))

    lines = [
        '# BAO CAO VAN HANH V1.5',
        '',
        '## 1. So luong du lieu',
        f"- prices_daily trong DB: {_table_count(paths['db_path'], 'prices_daily')}",
        f"- features_daily trong DB: {_table_count(paths['db_path'], 'features_daily')}",
        f"- predictions_daily trong DB: {_table_count(paths['db_path'], 'predictions_daily')}",
        f"- ranking_daily trong DB: {_table_count(paths['db_path'], 'ranking_daily')}",
        f"- alerts trong DB: {_table_count(paths['db_path'], 'alerts')}",
        '',
        '## 2. Ket qua train',
    ]
    if not train_df.empty:
        for _, row in train_df.sort_values('auc', ascending=False).iterrows():
            lines.append(f"- {row['model_name']}: precision={float(row['precision']):.4f}, auc={float(row['auc']):.4f}, so_feature={int(row.get('n_features', 0))}")
    else:
        lines.append('- Chua co train report')

    lines += ['', '## 3. Tong hop backtest theo model']
    if not backtest_summary_df.empty:
        for _, row in backtest_summary_df.sort_values(['auc_bt', 'avg_return'], ascending=[False, False]).iterrows():
            lines.append(
                f"- {row['model_name']}: precision_bt={float(row['precision_bt']):.4f}, auc_bt={float(row['auc_bt']):.4f}, "
                f"avg_return={float(row['avg_return']):.4f}, win_rate={float(row['win_rate']):.4f}, windows={int(row['windows'])}"
            )
    else:
        lines.append('- Chua co backtest summary')

    lines += ['', '## 4. Chat luong alert theo top N']
    if not alert_quality_df.empty:
        for _, row in alert_quality_df.sort_values(['top_n', 'alert_precision', 'alert_avg_return'], ascending=[True, False, False]).iterrows():
            lines.append(
                f"- {row['model_name']} | top_n={int(row['top_n'])}: alert_precision={float(row['alert_precision']):.4f}, "
                f"alert_avg_return={float(row['alert_avg_return']):.4f}, alert_win_rate={float(row['alert_win_rate']):.4f}, windows={int(row['windows'])}"
            )
    else:
        lines.append('- Chua co alert quality summary')

    lines += ['', '## 5. Quality gate']
    if quality_gate:
        lines.append(f"- passed: {quality_gate.get('passed')}")
        if quality_gate.get('reasons'):
            for reason in quality_gate['reasons']:
                lines.append(f'- reason: {reason}')
        else:
            lines.append('- Khong co ly do canh bao quality gate.')
        if quality_gate.get('max_alerts_override'):
            lines.append(f"- max_alerts_override: {quality_gate['max_alerts_override']}")
    else:
        lines.append('- Chua co file quality gate')

    lines += ['', '## 6. Trong so ensemble dang dung']
    if weights_json:
        for k, v in weights_json.items():
            lines.append(f'- {k}: {float(v):.4f}')
    else:
        lines.append('- Dang dung trong so cau hinh mac dinh.')

    lines += ['', '## 7. Top feature importance']
    lines += _top_feature_lines(feature_importance_df, top_feature_n)

    lines += ['', '## 8. Bang xep hang moi nhat']
    if not ranking_df.empty:
        for _, row in ranking_df.head(top_n).iterrows():
            gate_note = row['gate_notes'] if 'gate_notes' in ranking_df.columns and pd.notna(row['gate_notes']) else ''
            band = row['confidence_band'] if 'confidence_band' in ranking_df.columns and pd.notna(row['confidence_band']) else 'UNKNOWN'
            lines.append(
                f"- {row['symbol']} | dir={row['direction']} | p_up_5d={float(row['p_up_5d']):.4f} | confidence={float(row['confidence']):.4f} | band={band} | gate={gate_note}"
            )
    else:
        lines.append('- Chua co ranking')

    lines += ['', '## 9. Alerts moi nhat']
    if not alert_df.empty:
        lines.append(f'- So alert sau loc: {len(alert_df)}')
        for _, row in alert_df[['symbol', 'direction', 'confidence', 'signal_strength', 'confidence_band']].head(10).iterrows():
            lines.append(
                f"- {row['symbol']} | {row['direction']} | confidence={float(row['confidence']):.3f} | strength={float(row['signal_strength']):.3f} | band={row.get('confidence_band', 'UNKNOWN')}"
            )
    else:
        lines.append('- Chua co alert; co the quality gate dang ha cap hoac bo loc dang chat.')

    lines += ['', '## 10. Canh bao chat luong mo hinh']
    if train_warnings:
        for line in train_warnings.splitlines():
            lines.append(f'- {line}')
    else:
        lines.append('- Khong co canh bao metric bat thuong tu bo train.')

    lines += [
        '',
        '## 11. Ghi chu V1.5',
        '- Da bo sung alert quality summary theo top N de do chat luong tin hieu thuc chien.',
        '- Da bo sung feature importance theo tung model de giai thich ro model dang bam vao dau.',
        '- Da bo sung confidence band trong ranking va alerts de phan biet muc do tin cay.',
        '- Da tiep tuc giu quality gate + regime gate + model selection dong cua V1.4.',
    ]

    out = reports_dir / 'BAO_CAO_VAN_HANH_V1_5.md'
    out.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Da tao bao cao: {out}')


if __name__ == '__main__':
    main()
