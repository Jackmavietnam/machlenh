# Tiến độ dự án - Mạch Lệnh

## Thông tin chung
- Tên dự án: Mạch Lệnh
- Mục tiêu: Xây hệ thống đánh giá/cảnh báo xu hướng cổ phiếu VNINDEX, bắt đầu từ 12 mã pilot.
- Trạng thái hiện tại: Đang phát triển V1

---

## Version 1.0.0 - Bộ khung đầu tiên

### Mục tiêu phiên bản
- Dựng bộ khung code V1 có thể chạy từ ingest -> feature -> model -> backtest -> alert -> dashboard.
- Tạo file xương sống dự án và cơ chế theo dõi tiến độ dài hạn.

### Đã hoàn thành
- Đặt tên dự án: **Mạch Lệnh**
- Tạo cấu trúc thư mục đầy đủ
- Tạo file cấu hình universe, paths, model config
- Tạo schema SQLite
- Tạo pipeline ingest daily đầu tiên
- Tạo pipeline cleaning dữ liệu daily
- Tạo feature engineering cơ bản
- Tạo regime detector cơ bản
- Tạo baseline model stack
- Tạo backtest walk-forward cơ bản
- Tạo alert engine cơ bản
- Tạo dashboard Streamlit cơ bản
- Tạo file xương sống dự án
- Tạo file tiến độ dự án
- Kiểm tra cú pháp bằng compileall: PASS

### Các vấn đề / lỗi / hạn chế đã nhận diện ngay từ V1.0.0

#### 1. Rủi ro từ nguồn dữ liệu miễn phí
- Vấn đề: Nguồn miễn phí có thể đổi format, nghẽn hoặc thiếu dữ liệu.
- Tác động: Pipeline ingest có thể lỗi hoặc một số mã bị thiếu ngày.
- Xử lý trong V1: Tách adapter dữ liệu riêng, thêm fallback lưu CSV raw, log lỗi từng mã.
- Hướng xử lý ở phiên bản sau: thêm nhiều adapter và cơ chế retry/backfill.

#### 2. Daily trước, intraday sau
- Vấn đề: Nếu làm intraday ngay từ đầu dự án dễ đổ vỡ vì ingest, clean, alignment phức tạp.
- Xử lý trong V1: khóa phạm vi ở daily core; intraday chỉ để chừa vị trí phát triển.
- Hướng sau: làm intraday-lite cho anomaly alert.

#### 3. Backtest V1 còn đơn giản
- Vấn đề: Chưa mô phỏng đầy đủ phí, slippage, liquidity constraint chi tiết.
- Xử lý trong V1: dùng backtest định hướng chất lượng tín hiệu, chưa coi là lợi nhuận thực chiến cuối.
- Hướng sau: thêm slippage, position sizing, portfolio simulation.

#### 4. Governance mới ở mức tối thiểu
- Vấn đề: Chưa có đủ drift control, anomaly governance, sandbox governance nâng cao.
- Xử lý trong V1: giữ các luật cứng tối thiểu như no future leakage, walk-forward mandatory, prediction logging.
- Hướng sau: thêm monitoring, downgrade rules, model retirement.

#### 5. Explainability còn ở mức cơ bản
- Vấn đề: Rationale hiện mới dựa vào feature quan trọng / score logic, chưa sâu như SHAP hoàn chỉnh.
- Xử lý trong V1: tạo rationale đủ đọc được cho bản pilot.
- Hướng sau: thêm SHAP, sector explanation, regime explanation.

### Kết quả chạy thử nội bộ V1.0.0
- compileall: PASS
- Chưa chạy ingest thực vì phụ thuộc môi trường cài đặt gói và nguồn dữ liệu ngoài
- Rủi ro còn treo: adapter nguồn dữ liệu miễn phí có thể thay đổi format

### Bài học kỹ thuật từ V1.0.0
- Khóa data contract trước khi tối ưu model.
- Universe nhỏ nhưng đa ngành giúp test tốt hơn universe lớn nhưng đồng dạng.
- File tiến độ phải đi cùng code ngay từ bản đầu.

### Việc còn tồn sau V1.0.0
- Kiểm thử thật trên máy người dùng
- Xác nhận adapter dữ liệu phù hợp ổn định
- Thêm scheduler tự động
- Thêm dashboard sâu hơn
- Thêm paper trading

---

## Mẫu ghi cho phiên bản mới

### Version X.Y.Z
- Mục tiêu:
- Đã hoàn thành:
- Lỗi phát sinh:
- Cách xử lý:
- Hạn chế còn lại:
- Việc tiếp theo:


## Bản vá V1.0.1 - Khắc phục lỗi ingest SQLite
- Ngày cập nhật: 2026-04-02
- Vấn đề phát sinh khi chạy thực tế:
  - Lệnh `python run_daily.py --start 2018-01-01 --end 2026-12-31` dừng ở bước ingest.
  - Lỗi cụ thể: `sqlite3.ProgrammingError: Error binding parameter 8: type 'NAType' is not supported`.
  - Ý nghĩa: dữ liệu tải từ nguồn thị trường có ô rỗng kiểu `pd.NA` ở cột `value`, nhưng SQLite không nhận kiểu này khi ghi bằng `executemany()`.
- Đối chiếu dự án tham khảo:
  - Bộ module tham khảo của người dùng chủ yếu lưu CSV trực tiếp và chưa ghi vào SQLite ở khâu này, vì vậy tránh được lỗi bind kiểu dữ liệu.
- Hướng xử lý đã áp dụng:
  - Bổ sung lớp chuẩn hóa dữ liệu trước khi ghi database: mọi giá trị thiếu được đổi từ `pd.NA` sang `None`.
  - Ép các cột giá/khối lượng/giá trị giao dịch sang kiểu số bằng `pd.to_numeric(..., errors='coerce')`.
  - Áp dụng chuẩn hóa cho cả `write_dataframe`, `upsert_prices_daily`, `upsert_index_daily`.
- Kết quả mong đợi sau bản vá:
  - Bước 12 chạy qua được giai đoạn ingest dữ liệu lịch sử.
  - Không còn lỗi bind dữ liệu rỗng vào SQLite ở cột `value`.
- Ghi chú:
  - Bản vá này tập trung xử lý lỗi thực tế đầu tiên để tiếp tục sang bước 13.
  - Nếu sau khi ingest xong phát sinh lỗi mới ở feature/backtest, tiếp tục cập nhật file tiến độ ở bản sau.


## V1.0.2 - Bo sung bao cao van hanh va giam canh bao train

Ngay cap nhat: 2026-04-02

### Van de / su co
- Ban V1.0.1 chua co file `run_report.py`, nen nguoi dung khong the chay buoc bao cao sau backtest.
- Qua trinh train/backtest con canh bao do hai feature `value`, `value_zscore_20` khong co gia tri quan sat hop le trong du lieu hien tai.

### Xu ly
- Bo sung file `run_report.py` de tao bao cao tong hop tu train report, backtest report, predictions, alerts va du lieu trong SQLite.
- Va `prepare_training_data()` de tu dong loai cac cot numeric bi rong hoan toan truoc khi dua vao imputer.

### Ket qua mong doi
- Co the chay `python run_report.py` sau buoc 13.
- Giam canh bao `Skipping features without any observed values` trong cac lan train/backtest tiep theo.
- Tao file `reports/BAO_CAO_VAN_HANH_V1.md` de luu vet tien do van hanh.

## V1.1.0 - Nang cap feature, ensemble, bao cao va giam canh bao

Ngay cap nhat: 2026-04-02

### Muc tieu phien ban
- Nang chat luong V1 tu bo khung chay duoc thanh ban de co the tiep tuc toi uu.
- Giam canh bao khi train/predict.
- Bo sung feature co y nghia giao dich hon.
- Tao ensemble prediction va bao cao van hanh de doc hon.

### Van de / han che quan sat tu ban truoc
1. Canh bao `X does not have valid feature names, but LGBMClassifier was fitted with feature names`.
2. Feature `value`, `value_zscore_20` de trong hoac khong on dinh khi nguon du lieu thieu cot `value`.
3. Predictions chi dang muc per-model, alert chua uu tien theo ensemble.
4. Bao cao van hanh con ngan va chua co top ma tang/giam ro rang.
5. Feature set con mong, chua co drawdown/breakout/recovery/relative strength da khung.

### Xu ly da ap dung
- Sua pipeline train de imputer giu dinh dang pandas, giam canh bao feature names.
- Tinh `effective_value = value neu co, neu thieu thi dung close * volume`.
- Bo sung feature moi:
  - ret_20, ret_60
  - sma_60_ratio
  - atr_pct_14
  - breakout_20, breakout_60
  - drawdown_20, drawdown_60
  - recovery_20, recovery_60
  - value_ratio_20
  - volume_trend_5_20
  - momentum_spread_20_60
  - rs_vs_vnindex_20
  - market_ret_20, market_breakout_20
  - stochastic_k_14
- Bo sung ensemble prediction va uu tien alert tu ensemble.
- Nang cap report: top 5 tang, top 5 giam, thong ke alert dau bang, auc backtest.
- Nang cap README cho dung quy trinh V1.1.

### Ket qua mong doi
- Giam canh bao LightGBM lien quan ten cot.
- Feature `value_zscore_20` khong con bi bo qua vi thieu du lieu rong hoan toan.
- Alert on dinh hon do lay tu ensemble.
- Bao cao de doc hon cho nguoi khong biet code.

### Rui ro con lai
- Nguon du lieu mien phi van la diem yeu lon nhat.
- Chat luong model van moi o muc V1.x, can them loc regime va toi uu nguong.
- Chua co paper trading va chua co portfolio simulation day du.

### Huong sau V1.1
- Them ranking top co phieu manh/yeu theo sector.
- Them bo loc regime gate de chi cho phep alert trong dieu kien phu hop.
- Them paper trading.
- Them giai thich alert sau hon.


## V1.2.0 - Bang xep hang, loc tin hieu, xuat Excel, dashboard

Ngay cap nhat: 2026-04-02

### Muc tieu phien ban
- Them bang xep hang tong hop theo ma co phieu.
- Giam nhieu bang cach loc tin hieu yeu truoc khi tao alert.
- Xuat them file Excel/CSV de nguoi dung de xem va luu tru.
- Nang dashboard local de xem ranking, alerts, backtest.
- Ghi chep tien do ro hon de co the tiep tuc du an khi mat cuoc tro chuyen.

### Van de / nhu cau dau vao
- V1.1 da chay on dinh, nhung nguoi dung can file de doc de hon thay vi chi nhin log.
- Can co bang xep hang tong hop de biet ma nao manh/yeu ngay lap tuc.
- Can giam cac alert nhieu, chi giu lai tin hieu co do tin cay va do lech du lon.
- Can mot dashboard don gian cho nguoi khong biet code.

### Xu ly da ap dung
1. Bo sung bang xep hang tong hop tai `src/models/predict.py`
   - Tao `ranking_latest_label_5d.csv`
   - Tao `ranking_latest_label_5d.xlsx`
   - Luu them bang `ranking_daily` vao database
   - Them cac cot: `direction`, `signal_strength`, `ranking_score`

2. Bo sung bo loc alert tai `src/alerts/engine.py`
   - Loc theo `confidence_threshold`
   - Loc theo `min_signal_strength`
   - Gioi han so alert moi ben tang/giam
   - Gioi han tong so alert toi da
   - Mac dinh khong dua `NEUTRAL` vao alert

3. Nang cap `run_report.py`
   - Bao cao V1.2 co them phan bang xep hang
   - Co thong ke so luong file, DB, top ma, top alert
   - Tao file `reports/BAO_CAO_VAN_HANH_V1_2.md`

4. Nang cap dashboard Streamlit
   - Tab bang xep hang
   - Tab alerts da loc
   - Tab backtest
   - Tab xem du lieu tung ma
   - Them nut tai CSV truc tiep

5. Nang cap tai lieu va test
   - Cap nhat `README.md`
   - Them `tests/test_v12_smoke.py`
   - Bo sung `openpyxl` vao `requirements.txt`

### Rui ro / han che con lai
- Xuat Excel can `openpyxl`; nguoi dung phai cap nhat moi truong bang `pip install -r requirements.txt` neu chua co.
- Loc tin hieu hien dang dung nguong cau hinh co ban, chua toi uu theo regime.
- Bang xep hang hien moi dua tren ensemble va signal strength, chua co sector ranking.
- Dashboard hien tai du de van hanh local, chua phai giao dien production.

### Loi / su co co the gap o V1.2
- Neu chay `run_report.py` hoac `run_daily.py` ma bao loi lien quan Excel writer, nguyen nhan thuong la thieu `openpyxl`.
- Neu ranking rong, can kiem tra lai predictions ensemble da duoc tao hay chua.
- Neu alert qua it hoac bang 0, can giam `confidence_threshold` hoac `min_signal_strength` trong `config/model_config.yaml`.

### Cach xu ly neu gap loi
- Loi `openpyxl`: chay lai `pip install -r requirements.txt`.
- Khong co alert: mo `config/model_config.yaml`, giam nhe nguong loc va chay lai `python run_daily.py --start ... --end ...`.
- Dashboard khong mo: chay lai `streamlit run src/dashboard/app.py` trong moi truong `.venv` da kich hoat.

### Ket qua mong doi sau V1.2
- Nguoi dung nhin ngay duoc top ma manh/yeu.
- Alert it nhieu hon, de doc hon.
- Co file Excel/CSV de luu tru ben ngoai.
- Co dashboard local de theo doi van hanh ma khong can doc code.

### Huong sau V1.2
- V1.3: regime gate cho alert
- V1.3: xep hang theo sector
- V1.3: paper trading co ky luat vao/ra lenh
- V1.3: giai thich alert sau hon


## V1.3.0 - Nang chat luong tin hieu va backtest

Ngay cap nhat: 2026-04-02

### Muc tieu phien ban
- Nang chat luong feature va giai thich tin hieu.
- Mo rong backtest theo huong thuc chien hon: precision + avg return + win rate + so trade.
- Giam tinh trang co ranking nhung khong ra alert.
- Hop nhat ban va Timestamp/SQLite vao ma nguon chinh de tranh phai patch rieng.

### Loi / han che o V1.2
1. Co luc ranking sinh ra du nhung bo loc alert qua chat nen file alert rong.
2. Backtest moi dung precision/AUC, chua phan anh gia tri giao dich.
3. Ma nguon goc V1.2 chua chua day du ban va Timestamp SQLite.
4. Feature set chua co trend slope, relative breakout, pullback gan dinh.

### Xu ly da ap dung o V1.3
- Them feature moi: dist_high_20, dist_low_20, trend_slope_20, trend_slope_60, range_pct, pullback_from_20d_high, bounce_from_20d_low, relative_breakout_20.
- Them future_return_3d / future_return_5d de backtest thuc chien hon.
- Sua DatabaseManager de tu dong doi datetime thanh chuoi truoc khi ghi SQLite.
- No bo loc alert: giam nguong confidence, giam min_signal_strength, them fallback top signal.
- Mo rong walkforward backtest: trade_count, avg_return, win_rate.
- Cap nhat run_report de sinh BAO_CAO_VAN_HANH_V1_3.md.

### Rui ro con lai
- Nguon du lieu mien phi van la diem yeu lon nhat.
- Chua co portfolio simulation day du va paper trading.
- Chua co toi uu nguong alert theo regime.

### Buoc tiep theo de nghi
- V1.4: market gate va regime filter.
- V1.5: paper trading va so theo doi lenh.
- V1.6: toi uu threshold theo tung che do thi truong.


## V1.3.1 - Ban va chong ro ri du lieu (anti-leakage)

Ngay cap nhat: 2026-04-02

### Su co phat sinh o V1.3
- Pipeline chay het, nhung metric model bat thuong: LightGBM va RandomForest dat AUC xap xi 1.0 va precision gan 1.0.
- Day la dau hieu rat manh cua ro ri du lieu (data leakage), nghia la model co kha nang da thay thong tin tuong lai khi train.

### Nguyen nhan goc re
- Trong file feature engineering co sinh ra cac cot `future_return_3d`, `future_return_5d`.
- Ham `prepare_training_data()` o V1.3 chi loai `label_*` khoi tap feature, nhung chua loai `future_return_*`.
- He qua: model co the hoc truc tiep tu loi giai cua bai toan.

### Cach xu ly o V1.3.1
1. Khoa hoan toan `future_return_3d`, `future_return_5d` khoi danh sach feature train.
2. Giu nguyen pipeline du bao/backtest nhung de chung su dung lai bo feature da duoc lam sach.
3. Them canh bao tu dong neu AUC >= 0.95 hoac precision >= 0.90.
4. Nang cap file bao cao van hanh de hien ro canh bao chat luong mo hinh.

### Tac dong mong doi
- Metric se giam ve muc hop ly hon.
- Backtest va xep hang se dang tin cay hon ve mat khoa hoc du lieu.
- Day la ban va uu tien do trung thuc cua he thong, khong uu tien lam dep so.

### Bai hoc rut ra
- Moi cot co tu khoa `future`, `target`, `label` phai bi cam tuyet doi trong tap feature train.
- Metric qua dep la mot loi canh bao, khong phai mot thanh tich.
- File tien do du an phai luu ro: "ban nao sua loi gi, vi sao sua, va sau khi sua doi mat voi han che nao".

### Huong tiep theo sau V1.3.1
- Chay lai V1.3.1 tren may nguoi dung.
- Neu metric quay ve muc hop ly thi moi lam V1.4.
- V1.4 du kien: nang cap quality gate, tach model report/best model, va bo sung danh gia on dinh theo ma/co cum co phieu.


## V1.4.0 - Quality gate, regime gate, model selection dong

Ngay cap nhat: 2026-04-02

### Co so quyet dinh nang cap len V1.4
- V1.3.1 da chay thanh cong tren may nguoi dung qua 3 buoc: `run_daily.py`, `run_backtest.py`, `run_report.py`.
- Metric sau khi va leakage da ve muc hop ly hon:
  - lightgbm: precision~0.5994, auc~0.6391
  - random_forest: precision~0.3937, auc~0.6289
  - logistic_regression: precision~0.2710, auc~0.5134
  - backtest mean precision~0.5317, auc~0.6020
- Khong con dau hieu metric dep bat thuong nhu V1.3 loi leakage.

### Muc tieu phien ban
1. Them quality gate truoc khi phat alert.
2. Them regime gate de giam tin hieu sai ngu truong hop thi truong xau.
3. Them co che chon trong so dong cho ensemble dua tren train + backtest.
4. Ghi nhat ky tien do du an chi tiet hon de bao toan tri nho du an.

### Van de o V1.3.1 can giai quyet
- Ensemble dang dung trong so co dinh, chua phan biet model nao dang tot hon trong thoi diem hien tai.
- Alert co the van phat ra du model da yeu di, vi chua co cong chat luong tong.
- Tin hieu BUY/WATCH-UP co the khong phu hop khi thi truong dang downtrend hoac bien dong qua cao.
- Bao cao van hanh chua cho thay ro quality gate va trong so ensemble dang dung.

### Xu ly da ap dung trong V1.4

#### 1. Bo sung dynamic model selection
- Them file moi: `src/models/model_selection.py`
- Co che moi:
  - Doc `train_report_label_5d.csv`
  - Doc `backtest_summary_label_5d.csv`
  - Tinh `train_score`, `backtest_score`, `final_score`
  - Sinh file `ensemble_weights_used_label_5d.json`
  - Sinh file `model_selection_scorecard_label_5d.csv`
- Muc tieu:
  - Giam tinh cam tinh khi dat trong so ensemble.
  - De trong so model thay doi theo chat luong that, khong dung cung 1 bo trong so mac dinh mai mai.

#### 2. Bo sung quality gate truoc alert
- Them file moi: `src/models/quality_gate.py`
- Danh gia cac nguong:
  - train_auc
  - train_precision
  - backtest_auc
  - backtest_precision
  - backtest_avg_return
- Neu gate fail:
  - He thong khong tat han pipeline
  - Nhung se ha cap so luong alert toi da
  - Va tang yeu cau confidence de tranh ban ra tin hieu yeu
- Sinh file: `quality_gate_label_5d.json`

#### 3. Bo sung regime gate trong prediction
- Sua `src/models/predict.py`
- Ap dung penalty vao confidence neu:
  - thi truong sideway
  - thi truong high_vol
- Chan/ha cap BUY va WATCH-UP khi thi truong downtrend
- Ghi lai `gate_notes` vao ranking de giai trinh sau nay

#### 4. Nang cap walkforward backtest thanh backtest da model
- Sua `src/backtest/walkforward.py`
- Truoc day chi backtest lightgbm/mac dinh
- V1.4 backtest tung model enabled:
  - logistic_regression
  - lightgbm
  - random_forest
- Sinh them file tong hop: `backtest_summary_label_5d.csv`
- Day la du lieu dau vao quan trong cho dynamic model selection

#### 5. Sua run_daily de dung quy trinh V1.4
- Thu tu moi:
  - ingest
  - cleaning
  - feature_engineering
  - train
  - backtest
  - predict
  - alerts
- Ly do:
  - predict/alerts V1.4 can co backtest_summary va quality_gate moi nhat

#### 6. Nang cap run_report.py
- Bao cao moi: `BAO_CAO_VAN_HANH_V1_4.md`
- Them cac muc:
  - tong hop backtest theo model
  - quality gate
  - trong so ensemble dang dung
  - ghi chu V1.4

### Kiem tra ky thuat da thuc hien
- Compile toan bo ma nguon V1.4: PASS
- Da compile cac file moi:
  - `src/models/model_selection.py`
  - `src/models/quality_gate.py`
  - `src/models/predict.py`
  - `src/alerts/engine.py`
  - `src/backtest/walkforward.py`
  - `run_daily.py`
  - `run_report.py`

### Rui ro / han che con lai sau V1.4
1. Dynamic weight hien van dua tren metric offline (train/backtest), chua phai online learning.
2. Regime gate hien la rule-based, chua hoc regime threshold toi uu theo du lieu lich su.
3. Quality gate moi la gate toan he thong, chua phan cap theo tung ma / tung cum nganh.
4. Backtest van la single-signal evaluation, chua phai mo phong portfolio day du co cap von va cost thuc chien.
5. Chua co paper trading / so theo doi lenh de kiem nghiem sau khi qua quality gate.

### Loi co the gap khi nguoi dung chay V1.4
- Neu `run_daily.py` loi o phan prediction:
  - thuong la do thieu `backtest_summary_label_5d.csv`
  - nhung V1.4 da goi backtest truoc predict, nen ve ly thuyet da tranh duoc
- Neu bao cao khong hien weight dong:
  - co the do train/backtest report rong
- Neu alert qua it:
  - co the quality gate fail hoac regime gate dang ha cap tin hieu
  - can doc file `quality_gate_label_5d.json`

### Gia tri chinh cua V1.4
- Day la ban dau tien bat dau tach ro:
  - model nao dang manh
  - he thong co du chat luong de phat alert khong
  - thi truong hien tai co cho phep tin hieu loai do khong
- V1.4 uu tien giam alert xau hon la tang alert cho dep mat.

### Huong sau V1.4
- V1.5: paper trading va theo doi lenh
- V1.5: loc theo cum nganh / sector ranking
- V1.6: toi uu threshold theo regime
- V1.6: them portfolio simulation, position sizing, stop logic


---

## Ban va V1.4.1 - Sua loi model selection doc sai ten cot

### Loi phat sinh khi chay V1.4
- `run_daily.py` dung sau backtest voi loi `KeyError: 'auc_train'`.
- Nguyen nhan: `src/models/model_selection.py` ky vong cac cot `auc_train`, `precision_train` sau khi merge, nhung file `train_report_label_5d.csv` cua he thong lai dang dung ten cot `auc`, `precision`.
- Vi vay, buoc tinh trong so dong (dynamic weights) bi vo ngay truoc khi sinh ranking va alert.

### Cach da xu ly
- Va `src/models/model_selection.py` theo huong chiu loi tot hon:
  - Neu co `auc_train` / `precision_train` thi dung.
  - Neu khong co, tu dong fallback sang `auc` / `precision`.
  - Giu nguyen `auc_bt`, `precision_bt`, `avg_return`, `win_rate` cho phan backtest.
- Muc tieu: tranh vo chuong trinh khi ten cot bao cao train thay doi nho giua cac phien ban.

### Tac dong ky vong
- `run_daily.py` se chay het pipeline V1.4.
- Co the sang tiep `run_report.py` de tao bao cao van hanh V1.4.
- Ban va nay khong doi logic model, chi sua tinh on dinh cua pipeline.

---

## V1.5.0 - Danh gia chat luong alert thuc chien va giai thich model

Ngay cap nhat: 2026-04-02

### Muc tieu phien ban
- Do chat luong alert theo top N thay vi chi nhin metric train/backtest tong quat.
- Hien ro model dang bam vao feature nao de de kiem tra tinh hop ly.
- Tach alert theo cac muc do tin cay de nguoi dung de doc va uu tien.
- Cap nhat ho so tien do day du de sau nay mat chat van co the noi lai du an.

### Van de / nhu cau dau vao
- V1.4 da chay thong toan pipeline, nhung chua tra loi ro cau hoi quan trong nhat: alert top dau co thuc su tot khong?
- Chua co bang feature importance de kiem tra model dang hoc cai gi.
- Chua co phan loai tin cay ro rang cho ranking/alert.
- Nguoi dung yeu cau tiep tuc nang cap va ghi ro cac thay doi vao file tien do.

### Xu ly da ap dung
#### 1. Bo sung alert quality summary trong walkforward backtest
- Sua `src/backtest/walkforward.py`.
- Ngoai cac metric cu (`precision`, `auc`, `avg_return`, `win_rate`), bo sung danh gia chat luong alert theo top N.
- Mac dinh tao thong ke cho `top_n = 3` va `top_n = 5`.
- Sinh file moi:
  - `artifacts/alert_quality_summary_label_5d.csv`
- Muc tieu:
  - Xem model nao thuc su cho top alert co chat luong tot.
  - Tranh viec model AUC kha nhung top signal lai yeu.

#### 2. Bo sung feature importance theo tung model
- Sua `src/models/train.py`.
- Tu dong trich xuat feature importance:
  - Logistic Regression: dung `abs(coef_)`
  - RandomForest / LightGBM: dung `feature_importances_`
- Sinh file moi:
  - `artifacts/feature_importance_label_5d.csv`
- Muc tieu:
  - De nguoi van hanh nhin ro model dang dua vao feature nao.
  - Ho tro debug leakage, hoc nham, hoac hoc qua muc vao 1 cum feature.

#### 3. Bo sung confidence band trong ranking va alert
- Sua `src/models/predict.py`.
- Them 4 muc:
  - `HIGH`
  - `MEDIUM`
  - `LOW`
  - `VERY_LOW`
- Ranking moi co them cot `confidence_band`.
- Sua `src/alerts/engine.py` de alert ghi ro `confidence_band` trong alert va rationale.
- Muc tieu:
  - De uu tien doc alert de hon.
  - Tach ro tin hieu manh va tin hieu chi mang tinh theo doi.

#### 4. Nang cap bao cao van hanh
- Sua `run_report.py`.
- Bao cao moi: `reports/BAO_CAO_VAN_HANH_V1_5.md`
- Them cac muc:
  - Chat luong alert theo top N
  - Top feature importance theo tung model
  - Confidence band trong ranking/alert
- Muc tieu:
  - Bao cao V1.5 khong chi noi he thong da chay, ma con noi chat luong tin hieu va logic model.

#### 5. Cap nhat cau hinh
- Sua `config/model_config.yaml`.
- Them:
  - `alerts.confidence_bands`
  - `backtest.alert_top_n_list`
  - `reporting.feature_importance_top_n`
- Muc tieu:
  - Bien cac nang cap V1.5 thanh cau hinh, de doi sau de sua khong can cham vao code.

### Kiem tra ky thuat da thuc hien
- Compile toan bo ma nguon V1.5: PASS
- Test tu dong: PASS (3 tests)
- Da bo sung test moi cho V1.5:
  - Kiem tra ranking co `confidence_band`
  - Kiem tra feature importance trich xuat duoc cho logistic regression

### Rui ro / han che con lai sau V1.5
1. Alert quality hien van dua tren walkforward top N, chua phai paper trading thuc chien co cost va slippage.
2. Feature importance la giai thich muc dau, chua phai SHAP hay giai thich theo tung du doan rieng le.
3. Confidence band dang rule-based, chua duoc calibration xac suat.
4. Chua co co che threshold toi uu theo tung cum nganh / sector.
5. Chua co bo theo doi paper trade de kiem nghiem alert sau khi phat ra.

### Gia tri chinh cua V1.5
- Day la ban dau tien cho phep danh gia: top alert co dang tin hay khong.
- Day la ban dau tien cho phep nhin ro model dang hoc cai gi.
- Day la ban dau tien tach signal theo cap do tin cay de de van hanh hon.

### Huong sau V1.5
- V1.6: paper trading / theo doi lenh sau alert
- V1.6: sector-aware ranking va sector cap
- V1.6: calibration xac suat va threshold theo regime
- V1.6+: portfolio simulation, cap von, stop logic, max exposure
