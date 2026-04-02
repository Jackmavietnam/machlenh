# BAO CAO VAN HANH V1.5

## 1. So luong du lieu
- prices_daily trong DB: 27818
- features_daily trong DB: 27818
- predictions_daily trong DB: 48
- ranking_daily trong DB: 12
- alerts trong DB: 6

## 2. Ket qua train
- lightgbm: precision=0.5994, auc=0.6391, so_feature=63
- random_forest: precision=0.3937, auc=0.6289, so_feature=63
- logistic_regression: precision=0.2710, auc=0.5134, so_feature=63

## 3. Tong hop backtest theo model
- random_forest: precision_bt=0.3739, auc_bt=0.6114, avg_return=0.0238, win_rate=0.6458, windows=5
- lightgbm: precision_bt=0.5317, auc_bt=0.6020, avg_return=0.0519, win_rate=0.7407, windows=5
- logistic_regression: precision_bt=0.2671, auc_bt=0.5290, avg_return=0.0143, win_rate=0.4385, windows=5

## 4. Chat luong alert theo top N
- random_forest | top_n=3: alert_precision=0.9333, alert_avg_return=0.1182, alert_win_rate=0.9333, windows=5
- lightgbm | top_n=3: alert_precision=0.8000, alert_avg_return=0.1056, alert_win_rate=0.8000, windows=5
- logistic_regression | top_n=3: alert_precision=0.6000, alert_avg_return=0.0413, alert_win_rate=0.6000, windows=5
- random_forest | top_n=5: alert_precision=0.8800, alert_avg_return=0.1115, alert_win_rate=0.8800, windows=5
- lightgbm | top_n=5: alert_precision=0.8400, alert_avg_return=0.1032, alert_win_rate=0.8400, windows=5
- logistic_regression | top_n=5: alert_precision=0.5200, alert_avg_return=0.0247, alert_win_rate=0.5200, windows=5

## 5. Quality gate
- passed: True
- Khong co ly do canh bao quality gate.

## 6. Trong so ensemble dang dung
- logistic_regression: 0.0909
- lightgbm: 0.5465
- random_forest: 0.3626

## 7. Top feature importance
- lightgbm:
  - market_ret_20: importance=424.000000, norm=0.0471
  - market_breakout_20: importance=393.000000, norm=0.0437
  - market_ret_5: importance=349.000000, norm=0.0388
  - stock_beta_60: importance=346.000000, norm=0.0384
  - rolling_vol_20: importance=334.000000, norm=0.0371
  - trend_slope_60: importance=322.000000, norm=0.0358
  - atr_pct_14: importance=304.000000, norm=0.0338
  - sma_60: importance=253.000000, norm=0.0281
  - market_ret_1: importance=239.000000, norm=0.0266
  - volume_trend_5_20: importance=235.000000, norm=0.0261
  - momentum_spread_20_60: importance=234.000000, norm=0.0260
  - rolling_vol_5: importance=230.000000, norm=0.0256
- logistic_regression:
  - volume: importance=0.000000, norm=0.9660
  - effective_value: importance=0.000000, norm=0.0340
  - low: importance=0.000000, norm=0.0000
  - open: importance=0.000000, norm=0.0000
  - close: importance=0.000000, norm=0.0000
  - sma_5: importance=0.000000, norm=0.0000
  - sma_10: importance=0.000000, norm=0.0000
  - ema_12: importance=0.000000, norm=0.0000
  - high: importance=0.000000, norm=0.0000
  - sma_20: importance=0.000000, norm=0.0000
  - sma_60: importance=0.000000, norm=0.0000
  - ema_26: importance=0.000000, norm=0.0000
- random_forest:
  - rolling_vol_20: importance=0.055989, norm=0.0560
  - rolling_vol_5: importance=0.050316, norm=0.0503
  - atr_pct_14: importance=0.049606, norm=0.0496
  - recovery_60: importance=0.036198, norm=0.0362
  - trend_slope_60: importance=0.033940, norm=0.0339
  - market_breakout_20: importance=0.030605, norm=0.0306
  - ret_60: importance=0.028005, norm=0.0280
  - range_pct: importance=0.023279, norm=0.0233
  - sma_60: importance=0.020908, norm=0.0209
  - market_ret_20: importance=0.020764, norm=0.0208
  - atr_14: importance=0.020399, norm=0.0204
  - stock_beta_60: importance=0.018936, norm=0.0189

## 8. Bang xep hang moi nhat
- TCB | dir=SELL | p_up_5d=0.2552 | confidence=0.3896 | band=VERY_LOW | gate=giam confidence do thi truong sideway; giam confidence do bien dong cao
- HSG | dir=SELL | p_up_5d=0.2632 | confidence=0.3735 | band=VERY_LOW | gate=giam confidence do thi truong sideway; giam confidence do bien dong cao
- SSI | dir=SELL | p_up_5d=0.2660 | confidence=0.3680 | band=VERY_LOW | gate=giam confidence do thi truong sideway; giam confidence do bien dong cao
- HPG | dir=SELL | p_up_5d=0.2731 | confidence=0.3537 | band=VERY_LOW | gate=giam confidence do thi truong sideway; giam confidence do bien dong cao
- VIC | dir=SELL | p_up_5d=0.2763 | confidence=0.3474 | band=VERY_LOW | gate=giam confidence do thi truong sideway; giam confidence do bien dong cao
- ACB | dir=SELL | p_up_5d=0.2889 | confidence=0.3222 | band=VERY_LOW | gate=giam confidence do thi truong sideway; giam confidence do bien dong cao
- MBB | dir=SELL | p_up_5d=0.2976 | confidence=0.3049 | band=VERY_LOW | gate=giam confidence do thi truong sideway; giam confidence do bien dong cao
- NKG | dir=SELL | p_up_5d=0.3030 | confidence=0.2940 | band=VERY_LOW | gate=giam confidence do thi truong sideway; giam confidence do bien dong cao
- FPT | dir=SELL | p_up_5d=0.3088 | confidence=0.2824 | band=VERY_LOW | gate=giam confidence do thi truong sideway; giam confidence do bien dong cao
- MWG | dir=SELL | p_up_5d=0.3103 | confidence=0.2793 | band=VERY_LOW | gate=giam confidence do thi truong sideway; giam confidence do bien dong cao
- VND | dir=SELL | p_up_5d=0.3386 | confidence=0.2228 | band=VERY_LOW | gate=giam confidence do thi truong sideway; giam confidence do bien dong cao
- VHM | dir=WATCH-DOWN | p_up_5d=0.3546 | confidence=0.1908 | band=VERY_LOW | gate=giam confidence do thi truong sideway; giam confidence do bien dong cao

## 9. Alerts moi nhat
- So alert sau loc: 6
- TCB | SELL | confidence=0.390 | strength=0.490 | band=UNKNOWN
- HSG | SELL | confidence=0.374 | strength=0.474 | band=UNKNOWN
- SSI | SELL | confidence=0.368 | strength=0.468 | band=UNKNOWN
- HPG | SELL | confidence=0.354 | strength=0.454 | band=UNKNOWN
- VIC | SELL | confidence=0.347 | strength=0.447 | band=UNKNOWN
- ACB | SELL | confidence=0.322 | strength=0.422 | band=UNKNOWN

## 10. Canh bao chat luong mo hinh
- Khong co canh bao metric bat thuong tu bo train.

## 11. Ghi chu V1.5
- Da bo sung alert quality summary theo top N de do chat luong tin hieu thuc chien.
- Da bo sung feature importance theo tung model de giai thich ro model dang bam vao dau.
- Da bo sung confidence band trong ranking va alerts de phan biet muc do tin cay.
- Da tiep tuc giu quality gate + regime gate + model selection dong cua V1.4.