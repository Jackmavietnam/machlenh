# GHI CHU BAN V1.5

## Muc tieu
Nang chat luong danh gia alert thuc chien va giai thich model ro hon.

## Diem moi chinh
- Backtest co them `alert_quality_summary_label_5d.csv`.
- Train co them `feature_importance_label_5d.csv`.
- Ranking va alert co `confidence_band`.
- Bao cao moi: `reports/BAO_CAO_VAN_HANH_V1_5.md`.
- Tien do du an da duoc cap nhat den V1.5.

## Cach chay
```powershell
python run_daily.py --start 2018-01-01 --end 2026-12-31
python run_report.py
```
