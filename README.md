# Mạch Lệnh - V1.3

Mạch Lệnh là bộ khung cho hệ thống đánh giá và phát cảnh báo xu hướng cổ phiếu VNINDEX trên máy cá nhân, ưu tiên:

- chạy được end-to-end
- không cần API trả phí
- dễ mở rộng từ 12 mã pilot lên 100 mã
- quản trị được dữ liệu, mô hình, cảnh báo và tiến độ dự án

## Điểm mới ở V1.3

- giữ nền ổn định của V1.1
- thêm **bảng xếp hạng tổng hợp theo mã**
- thêm **lọc tín hiệu yếu** trước khi phát alert
- thêm **xuất Excel/CSV** để dễ xem
- nâng **dashboard local** để đọc ranking, alerts, backtest
- cập nhật **tiến độ dự án** chi tiết hơn để có thể nối lại dự án nếu mất cuộc trò chuyện

## Universe V1

12 mã pilot:

- HPG
- SSI
- VND
- TCB
- MBB
- FPT
- ACB
- VHM
- VIC
- HSG
- NKG
- MWG

## Cách chạy nhanh

### 1) Tạo môi trường

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Chạy pipeline daily

```bash
python run_daily.py --start 2018-01-01 --end 2026-12-31
```

### 3) Chạy backtest

```bash
python run_backtest.py --label-horizon 5
```

### 4) Tạo báo cáo

```bash
python run_report.py
```

### 5) Chạy dashboard

```bash
streamlit run src/dashboard/app.py
```

## File quan trọng sau khi chạy

- `data/artifacts/predictions_latest_label_5d.csv`
- `data/artifacts/ranking_latest_label_5d.csv`
- `data/artifacts/ranking_latest_label_5d.xlsx`
- `data/artifacts/alerts_latest_label_5d.csv`
- `data/artifacts/walkforward_report_label_5d.csv`
- `reports/BAO_CAO_VAN_HANH_V1_2.md`
- `reports/TIEN_DO_DU_AN.md`
- `reports/XUONG_SONG_DU_AN.md`

## Mục tiêu của V1.3

1. Tải dữ liệu daily OHLCV miễn phí
2. Làm sạch và chuẩn hóa dữ liệu
3. Sinh feature kỹ thuật và feature tương quan với VNINDEX
4. Huấn luyện baseline model + ensemble
5. Backtest walk-forward
6. Sinh alert hằng ngày sau khi lọc tín hiệu yếu
7. Sinh bảng xếp hạng mã mạnh/yếu
8. Xuất báo cáo Markdown + CSV + Excel
9. Hiển thị dashboard Streamlit dễ đọc cho người không biết code

## Ghi chú quan trọng

- V1.3 vẫn là bản nền kỹ thuật, chưa phải production cuối.
- Alert hiện đã có lọc, nhưng vẫn cần tiếp tục tối ưu ở V1.3 trở đi.
- Nguồn dữ liệu miễn phí vẫn là rủi ro lớn nhất của toàn dự án.
- Chưa có paper trading và chưa có portfolio simulation đầy đủ.


## Bo sung V1.3

- them feature so sanh suc manh voi VNINDEX va khoang cach MA
- mo rong walk-forward backtest theo avg return, win rate, so trade
- no logic alert de tranh tinh trang ra 0 alert
- da hop nhat ban va SQLite/Timestamp vao ma nguon chinh


## Ghi chu V1.3.1
- Da khoa cac cot future_return_3d/future_return_5d khong cho tham gia train de tranh ro ri du lieu.
- Neu thay AUC hoac precision > 0.95, hay xem file `data/artifacts/train_warnings_label_5d.txt`.
- V1.3.1 la ban va do tin cay, uu tien metric hop ly hon la metric dep.


## Ghi chu V1.4
- Co dynamic model selection dua tren train + backtest.
- Co quality gate truoc alert.
- Co regime gate de giam BUY/WATCH-UP khi thi truong khong phu hop.
- `run_daily.py` se tu chay backtest truoc prediction de tao du lieu cho ensemble dong.
- Sau khi chay xong, xem them cac file: `artifacts/backtest_summary_label_5d.csv`, `artifacts/ensemble_weights_used_label_5d.json`, `artifacts/quality_gate_label_5d.json`.
