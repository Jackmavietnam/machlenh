# Xương sống dự án - Mạch Lệnh V1

## 1. Mục tiêu bất biến

- Xây hệ thống đánh giá và cảnh báo xu hướng cổ phiếu VNINDEX chạy trên máy cá nhân
- Không dùng API trả phí
- Có khả năng mở rộng từ 12 mã pilot lên khoảng 100 mã
- Mọi phiên bản đều phải:
  - lưu dữ liệu
  - lưu dự báo
  - lưu alert
  - lưu kết quả thực tế hậu kiểm
  - lưu tiến độ và bài học lỗi

## 2. Trục phát triển

### Trục dữ liệu
- Daily OHLCV trước
- Intraday-lite sau
- Chuẩn hóa schema trước khi tối ưu model

### Trục mô hình
- Baseline dễ hiểu trước
- Phi tuyến sau
- Ensemble sau khi benchmark rõ ràng

### Trục quản trị
- Không dùng dữ liệu tương lai
- Không cho model mới vào production nếu chưa walk-forward
- Mọi alert đều có rationale + invalidation

### Trục người dùng
- Hệ thống hỗ trợ Sếp ra quyết định
- Không thay thế chủ quyền quyết định của Sếp
- Mọi phiên bản phải tăng tính đọc hiểu chứ không chỉ tăng độ chính xác

## 3. Universe V1
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

## 4. Mốc kỹ thuật V1

### V1.0.0
- Skeleton project
- ingest daily
- cleaning
- feature engineering cơ bản
- baseline model
- backtest cơ bản
- dashboard cơ bản
- progress tracker

### V1.1.0
- regime engine
- alert policy refinement
- feature drift
- model health report

### V1.2.0
- paper trading
- daily scheduler
- email/telegram alert
- sector-relative diagnostics

## 5. Luật phát triển

1. Không sửa nền tảng khi chưa log lý do.
2. Mọi lỗi mới phải ghi vào `reports/TIEN_DO_DU_AN.md`.
3. Mọi phiên bản mới phải có:
   - mục tiêu
   - thay đổi
   - lỗi đã gặp
   - hướng xử lý
   - việc còn tồn
4. Khi mở universe, phải pass lại pipeline toàn bộ.
5. Khi thêm feature hay model, phải benchmark so với bản gần nhất.

## 6. Tiêu chí đạt production sơ bộ

- ingest ổn định
- dữ liệu không lỗi hàng loạt
- baseline tốt hơn benchmark naïve
- alert có logic rõ ràng
- backtest có log minh bạch
- dashboard đọc được và kiểm tra được
