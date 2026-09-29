# Hướng dẫn chạy kiểm thử và tự xuất báo cáo

Dự án KHKT: *Thiết kế và kiểm thử máy chủ MCP tin cậy, an toàn cho tác tử AI tra cứu thông tin học tập ở trường THPT*.
Tài liệu này hướng dẫn chạy bộ **24 ca kiểm thử** cho hai phiên bản máy chủ (A – đối chứng, B – cải tiến) và **tự động xuất báo cáo** ra HTML, Word, Markdown, JSON, JUnit XML.

---

## 0. Các tệp liên quan

| Tệp | Vai trò |
|---|---|
| `run_tests.py` | Chạy 24 ca (10 F + 8 V + 6 S), ghi số liệu thô vào `ket_qua/` |
| `xuat_bao_cao.py` | Đọc `ket_qua/` và xuất báo cáo đa định dạng; tùy chọn `--chay` để chạy kiểm thử trước |
| `chay_kiem_thu.sh` | macOS/Linux: tạo môi trường, cài thư viện, chạy, xuất, mở báo cáo – **một lệnh** |
| `chay_kiem_thu.bat` | Windows: như trên, **nháy đúp** là chạy |
| `requirements.txt` | MCP Python SDK 2.2.0 (bắt buộc) |
| `requirements-bao-cao.txt` | `python-docx` (chỉ cần cho báo cáo Word) |

---

## 1. Chạy nhanh – một lệnh

Yêu cầu: **Python 3.10 trở lên**, có Internet ở lần chạy đầu (để cài thư viện).

**macOS / Linux** – mở Terminal:

```bash
cd ~/HOSO/F_DU_AN_SANG_TAO/01_KHKT/MCPProject/ma_nguon
chmod +x chay_kiem_thu.sh      # chỉ cần làm một lần
./chay_kiem_thu.sh
```

**Windows** – nháy đúp `chay_kiem_thu.bat` (hoặc chạy trong Command Prompt).

Kết quả: màn hình in bảng Đạt/Không đạt của 24 ca × 2 phiên bản, kết luận, và báo cáo HTML tự mở trên trình duyệt.
Tất cả tệp nằm trong `ket_qua/bao_cao_<mốc thời gian>/`.

Thêm tuỳ chọn sau lệnh, ví dụ `./chay_kiem_thu.sh --lap 50` hoặc `chay_kiem_thu.bat --lap 50`.

> macOS báo `python3` là 3.9? Cài bản mới: `brew install python@3.12` rồi xoá thư mục `.venv` và chạy lại.

---

## 2. Chạy từng bước (khi cần kiểm soát)

```bash
cd ma_nguon
python3 -m venv .venv
source .venv/bin/activate                 # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-bao-cao.txt

python run_tests.py --lap 20              # B1: chạy 24 ca, ghi số liệu thô
python xuat_bao_cao.py                    # B2: xuất báo cáo từ lần chạy mới nhất
```

Hoặc gộp hai bước: `python xuat_bao_cao.py --chay`.

### Các tuỳ chọn của `xuat_bao_cao.py`

| Tuỳ chọn | Ý nghĩa | Mặc định |
|---|---|---|
| `--chay` | Chạy `run_tests.py` trước khi xuất | tắt |
| `--lap N` | Số lần lặp mỗi ca để đo thời gian T (dùng với `--chay`) | 20 |
| `--moc 20260921_234140` | Xuất báo cáo cho một lần chạy cũ | lần mới nhất |
| `--liet-ke` | Liệt kê các lần chạy đã có trong `ket_qua/` | – |
| `--dinh-dang html,docx,md,json,junit` | Chọn định dạng cần xuất | tất cả |
| `--thu-muc-ra <thư mục>` | Ghi báo cáo vào nơi khác | `ket_qua/bao_cao_<mốc>/` |
| `--nguong-T 1.5` | T của B “không tăng đáng kể” nếu ≤ ngưỡng × T của A | 1,5 |
| `--junit-tinh-A` | Tính ca không đạt của A là *failure* trong JUnit | tắt (ghi là *skipped*) |
| `--mo` | Tự mở báo cáo HTML sau khi xuất | tắt (bật sẵn trong `.sh`/`.bat`) |

**Mã thoát:** `0` – B đạt mọi mục tiêu Bảng 10 · `1` – có mục tiêu chưa đạt · `2` – lỗi (chưa cài thư viện, thiếu dữ liệu…).

---

## 3. Các tệp báo cáo được tạo

| Tệp | Dùng để |
|---|---|
| `bao_cao.html` | Xem nhanh: thẻ chỉ số F, V, S, E, T; biểu đồ thanh A so với B; Bảng 7–10 có nhãn Đạt/Không đạt; phản hồi thực tế của từng ca. In ra PDF bằng Cmd/Ctrl + P. |
| `bao_cao.docx` | Word chuẩn trình bày văn bản: A4, lề trái 3 cm, Times New Roman 13. Chép Bảng 7–10 vào **báo cáo KHKT** hoặc nộp làm **minh chứng**. |
| `bao_cao.md` | Bản Markdown gọn, đưa vào Git hoặc Sổ nhật ký nghiên cứu điện tử. |
| `ket_qua.json` | Toàn bộ số liệu (chỉ số, mục tiêu, 48 dòng kết quả, lịch sử) cho chương trình khác đọc. |
| `junit.xml` | Cho CI (GitHub Actions, GitLab, Jenkins) hiển thị kết quả kiểm thử. |

Số liệu thô gốc vẫn nằm ở `ket_qua/so_lieu_tho_<mốc>.csv`, `tong_hop_<mốc>.json`, `bang_ket_qua_<mốc>.md` (do `run_tests.py` tạo).

### Nội dung báo cáo

1. **Kết luận** tự sinh: B đạt bao nhiêu ca, A không đạt những ca nào, E, T, số dòng mã.
2. **Bảng 10** – chỉ số A và B so với mục tiêu, có cột *Đánh giá B*.
3. **Bảng 7, 8, 9** – từng ca F, V, S; nhóm V có thêm điểm E(A), E(B).
4. **Độ lặp lại** – xuất hiện khi `ket_qua/` có ≥ 2 lần chạy: bảng chỉ số từng lần, T trung bình ± độ lệch chuẩn, và xác nhận F, V, S, E có giống nhau giữa các lần hay không.
5. **Phụ lục** – phản hồi thực tế của mỗi ca (tối đa 200 ký tự).

---

## 4. Tiêu chí đánh giá (Bảng 10)

| Chỉ số | Cách tính | Mục tiêu với B |
|---|---|---|
| F | số ca chức năng đúng / 10 × 100% | 100 |
| V | số ca đầu vào bất thường bị từ chối / 8 × 100% | ≥ 90 |
| S | số ca an toàn đạt / 6 × 100% | 100 |
| E | điểm TB thông báo lỗi trên 8 ca V (0: không nêu nguyên nhân · 1: nêu nguyên nhân · 2: nêu nguyên nhân + giá trị hợp lệ) | ≥ 1,8 |
| T | thời gian phản hồi TB (ms) trên các ca F và V | không tăng đáng kể (mặc định ≤ 1,5 × T của A) |
| Số dòng mã | bỏ dòng trống, chú thích, docstring | ghi nhận |

Phiên bản A **cố ý** có lỗ hổng, nên việc A không đạt V1, V2, V5–V7, S1–S5 là **kết quả mong đợi**, không phải lỗi của bộ kiểm thử.

Kết quả tham chiếu (chạy ngày 21/09/2026, Python 3.10–3.11, mcp 2.2.0):
**A 14/24 ca** (F 100 · V 37,5 · S 16,7 · E 0) – **B 24/24 ca** (F 100 · V 100 · S 100 · E 2). T của hai bản đều dưới 1 ms.
Nếu lần chạy của bạn khác các con số F, V, S, E này → xem mục 7.

---

## 5. Quy trình khuyến nghị cho báo cáo KHKT

1. Chạy **3 lần** để có số liệu độ lặp lại:
   ```bash
   ./chay_kiem_thu.sh && ./chay_kiem_thu.sh && ./chay_kiem_thu.sh --lap 50
   ```
   Báo cáo lần cuối sẽ có mục **Độ lặp lại qua 3 lần chạy**.
2. Mở `bao_cao.docx` của lần cuối → chép Bảng 7–10 vào báo cáo; chép bảng Độ lặp lại vào phần thảo luận.
3. Chép `so_lieu_tho_<mốc>.csv` (mở bằng Excel) vào **Sổ nhật ký nghiên cứu**, ghi ngày giờ, máy, phiên bản Python.
4. Khi sửa `server_b.py` hoặc thêm ca mới trong `run_tests.py`: chạy lại, đối chiếu Bảng 10 và cập nhật báo cáo.
5. Chỉ so sánh T của A với B **trong cùng một lần chạy** – T tuyệt đối phụ thuộc máy.

---

## 6. Kiểm thử thủ công bằng MCP Inspector (bổ sung)

Cần Node.js 18+:

```bash
npx @modelcontextprotocol/inspector .venv/bin/python server_a.py
npx @modelcontextprotocol/inspector .venv/bin/python server_b.py
```

Tab **Tools**: gọi thử `xem_tkb` với `t9`, `tinh_diem_tb` với điểm 11… và so sánh thông báo lỗi A/B.
Tab **Resources**: đọc `lop://thoi-khoa-bieu`, `lop://lich-thi/toan`, `lop://noi-quy`.
Chụp màn hình làm minh chứng bổ sung cho báo cáo.

---

## 7. Xử lý sự cố

| Hiện tượng | Cách xử lý |
|---|---|
| `ModuleNotFoundError: No module named 'mcp'` | Chưa kích hoạt `.venv` hoặc chưa cài: `pip install -r requirements.txt` |
| `Cần Python 3.10 trở lên` | Cài Python mới, xoá `.venv`, chạy lại |
| `! Bỏ qua DOCX: chưa cài python-docx` | `pip install -r requirements-bao-cao.txt` (các định dạng khác vẫn được xuất) |
| `Chưa có kết quả trong ket_qua/` | Thêm `--chay`, hoặc chạy `python run_tests.py` trước |
| `permission denied: ./chay_kiem_thu.sh` | `chmod +x chay_kiem_thu.sh` |
| Tiếng Việt lỗi font trên cửa sổ lệnh Windows | Dùng `chay_kiem_thu.bat` (đã đặt UTF-8) hoặc Windows Terminal |
| B không đạt một ca | Mở `bao_cao.html` → xem cột *Phản hồi của B* ở ca đó; kiểm tra `nhat_ky/server_b_calls.jsonl` |
| A bỗng đạt S1/S2 | Kiểm tra `du_lieu/khong_cong_khai.txt`, `du_lieu_ngoai/bi_mat.txt` còn nguyên (chứa mã `[MA_KIEM_TRA_S1]`, `[MA_KIEM_TRA_S2]`) |
| Mã thoát 1 do T | T dưới 1 ms rất nhạy nhiễu; chạy lại với `--lap 50`, hoặc nới `--nguong-T 2` và ghi rõ ngưỡng trong báo cáo |

---

## 8. Chạy tự động trên GitHub Actions (tuỳ chọn)

Tạo tệp `.github/workflows/kiem_thu.yml` ở gốc kho mã:

```yaml
name: Kiem thu MCP
on: [push, pull_request, workflow_dispatch]
jobs:
  kiem-thu:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: ma_nguon } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements.txt -r requirements-bao-cao.txt
      - run: python xuat_bao_cao.py --chay --thu-muc-ra bao_cao_ci
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: bao-cao-kiem-thu, path: ma_nguon/bao_cao_ci/ }
```

Bước kiểm thử báo **đỏ** khi B không đạt một mục tiêu (mã thoát 1). Ca không đạt của A ghi là *skipped* trong `junit.xml`, nên không làm hỏng CI.

---

## 9. An toàn khi thử nghiệm

- Chỉ dùng **dữ liệu giả lập** trong `du_lieu/`; không đưa thông tin thật của học sinh vào.
- Máy chủ chạy cục bộ (client trong bộ nhớ hoặc stdio), không mở cổng ra Internet.
- `server_a.py` cố ý có lỗ hổng để đối chứng – không dùng làm mẫu cho hệ thống thật.

## Kiểm thử mở rộng bằng dữ liệu mô phỏng + tự động ghi sổ nhật ký (Phụ lục 2)

```bash
python sinh_du_lieu_kiem_thu.py            # sinh du_lieu/kiem_thu/ (40 HS giả lập, 128 ca, seed 2026)
python chay_kiem_thu_mo_rong.py --lan 3    # chạy riêng bộ ca mở rộng trên A và B
python ghi_nhat_ky.py                      # 24 ca × 3 lần thử + bộ mở rộng × 3 lần -> nối 1 trang vào sổ
python ghi_nhat_ky.py --ghi-chu "..." --giai-doan "Thực nghiệm lần 2"
python ghi_nhat_ky.py --kiem-tra           # kiểm tra chuỗi mã băm: không trang nào bị sửa/xoá
```

Sổ nằm ở `nhat_ky_nghien_cuu/So_nhat_ky_nghien_cuu.docx` (+ `.md`). Mỗi lần chạy NỐI THÊM một trang, không sửa trang cũ.
Đây là PHỤ LỤC SỐ LIỆU THÔ in ra để kẹp vào sổ nhật ký VIẾT TAY bằng bút mực (bắt buộc theo Phụ lục 2);
học sinh tự ghi mục 5, 6 và ký tên.
