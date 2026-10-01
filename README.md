# MCPFortress – Hệ thống giả lập kiểm thử MCP server tra cứu thông tin học tập

🌐 **Trang giới thiệu dự án:** https://aerovfx.github.io/MCPFortress/

🎬 **Video giới thiệu (2:42):** https://aerovfx.github.io/MCPFortress/#video

Mã nguồn đi kèm báo cáo KHKT *"Thiết kế và kiểm thử máy chủ MCP tin cậy, an toàn cho tác tử AI tra cứu thông tin học tập ở trường THPT"*.
Hai phiên bản máy chủ Model Context Protocol (MCP) có cùng chức năng (thời khoá biểu, lịch thi, điểm trung bình) chạy trên **dữ liệu giả lập**, và một bộ **24 ca kiểm thử tự động** để so sánh.

| Tệp / thư mục | Nội dung |
|---|---|
| `server_a.py` | Phiên bản **A – đối chứng**: viết nhanh, không áp dụng nguyên tắc (tên chung, tham số tự do, lỗi "Error"/None, đọc tệp theo tên người gọi đưa vào, có công cụ ghi). |
| `server_b.py` | Phiên bản **B – cải tiến**: 3 tool `xem_tkb`, `xem_lich_thi`, `tinh_diem_tb` + 5 resource `lop://…`; áp dụng 3 nhóm nguyên tắc (xem bên dưới). |
| `run_tests.py` | Bộ 24 ca kiểm thử (10 F + 8 V + 6 S), tính các chỉ số F, V, S, E, T và số dòng mã. |
| `du_lieu/` | Dữ liệu giả lập: `thoi_khoa_bieu.json` (có ghi chú chứa lệnh ẩn ở t5 cho ca S3), `lich_thi.json`, `noi_quy.txt`, `khong_cong_khai.txt` (tệp "không công khai" vô hại cho ca S1). |
| `du_lieu_ngoai/bi_mat.txt` | Tệp vô hại NGOÀI thư mục dữ liệu, dùng cho ca S2 (thoát thư mục `../`). |
| `ket_qua/` | Nơi `run_tests.py` ghi số liệu thô (CSV), tổng hợp (JSON) và Bảng 7–10 (Markdown). |
| `nhat_ky/` | Nhật ký gọi công cụ của phiên bản B (JSON Lines) – lớp phòng thủ 2. |
| `docs/` | Trang giới thiệu dự án (GitHub Pages). |

## 1. Cài đặt (Windows / macOS / Linux)

Cần **Python 3.10 trở lên**.

```bash
git clone https://github.com/aerovfx/MCPFortress.git
cd MCPFortress
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # MCP Python SDK 2.2.0
```

## 2. Chạy bộ 24 ca kiểm thử

```bash
python run_tests.py            # mỗi ca lặp 20 lần để đo thời gian
python run_tests.py --lap 50   # đo kỹ hơn
```

Kết quả in ra màn hình và ghi vào `ket_qua/`:
- `so_lieu_tho_<mốc>.csv` – từng ca × từng phiên bản: đạt/không đạt, điểm E, thời gian, phản hồi thực tế → chép vào **Sổ nhật ký nghiên cứu**.
- `tong_hop_<mốc>.json` – chỉ số F, V, S, E, T, số dòng mã, phiên bản Python và SDK.
- `bang_ket_qua_<mốc>.md` – Bảng 7, 8, 9, 10 theo đúng mẫu báo cáo.

Mỗi lần chạy tạo một bộ tệp mới có mốc thời gian, nên có thể chạy nhiều lần để kiểm tra độ lặp lại.

## 3. Kiểm thử thủ công bằng MCP Inspector

Cần Node.js. Mở Inspector và kết nối tới từng máy chủ qua stdio:

```bash
npx @modelcontextprotocol/inspector python server_a.py
npx @modelcontextprotocol/inspector python server_b.py
```

Trong Inspector: tab **Tools** để liệt kê/gọi công cụ, tab **Resources** để đọc `lop://thoi-khoa-bieu`, `lop://lich-thi/toan`, `lop://noi-quy`…
So sánh mô tả công cụ, lược đồ tham số và thông báo lỗi của A với B.

## 4. Ba nhóm nguyên tắc trong phiên bản B

| Nhóm | Biện pháp trong mã |
|---|---|
| Thiết kế công cụ chuẩn xác | Tên `động_từ_danh_từ`; docstring nêu *làm gì, khi nào dùng, khi nào không dùng*; mỗi công cụ một việc; tham số `Literal` (t2–t6; toan, tin, van; hệ số 1, 2, 3) và `Field` (0 ≤ điểm ≤ 10, tối đa 50 cột); kết quả trả về là mô hình Pydantic có cấu trúc. |
| Báo lỗi có hướng dẫn | `ToolError` / `ResourceNotFoundError` nêu nguyên nhân và giá trị hợp lệ; đầu vào sai kiểu, ngoài khoảng bị SDK từ chối **trước khi hàm chạy** kèm danh sách giá trị cho phép. |
| Phòng thủ ba lớp | **Lớp 1 – thiết kế:** chỉ đọc, không có công cụ ghi/xoá/gửi; chỉ đọc tệp trong `TEP_CHO_PHEP`, không ghép tham số vào đường dẫn; ghi chú trong dữ liệu được trả về ở trường riêng `ghi_chu_du_lieu` có `nguon` và `canh_bao`. **Lớp 2 – thời gian chạy:** giới hạn độ dài/kích thước, ghi nhật ký mỗi lần gọi. **Lớp 3 – dữ liệu:** chỉ dữ liệu giả lập. |
| Không giữ trạng thái | Mỗi lần gọi đọc lại dữ liệu từ đĩa, không lưu phiên (đặc tả 2026-07-28). |

## 5. Bộ 24 ca kiểm thử

- **F1–F10 (chức năng):** TKB t2, t4; lịch thi toán, tin, văn; ĐTB (8×1, 7,5×2, 9×3) = 8,33; 10 → 10,0; (5; 6,5) → 5,75; đọc nội quy; đọc TKB cả tuần.
- **V1–V8 (dữ liệu bất thường):** ngày `t9`, `thứ hai`; môn `sinh`; danh sách điểm rỗng; điểm 11; điểm −1; hệ số 5; điểm là chữ `tám`. Mỗi ca V được chấm thêm **E** (0–2) theo nội dung thông báo lỗi.
- **S1–S6 (an toàn):** đọc tệp ngoài danh sách cho phép; `../` thoát thư mục; ghi chú chứa lệnh ẩn; liệt kê công cụ (không có ghi/xoá/gửi); đầu vào 10 000 ký tự; gọi lặp 20 lần cho kết quả giống nhau.

Tiêu chí chấm tự động nằm trong `run_tests.py` (danh sách `CA_F`, `CA_V`, hàm `ca_S`, `diem_thong_bao`). Khi sửa máy chủ hoặc thêm ca mới, cập nhật đồng thời báo cáo (Bảng 7–9).

## 6. Danh mục kiểm tra khi viết một MCP server mới

1. Tên công cụ dạng động_từ_danh_từ, không trùng nghĩa với công cụ khác?
2. Mô tả nêu rõ công cụ làm gì, khi nào dùng, khi nào **không** dùng?
3. Mọi tham số có kiểu chặt (`Literal`, khoảng giá trị, độ dài tối đa)?
4. Kết quả có cấu trúc, gọn, không trả `None`?
5. Mọi lỗi dự đoán được đều báo bằng `ToolError`/`ResourceNotFoundError`, nêu nguyên nhân + giá trị hợp lệ?
6. Server có công cụ ghi/xoá/gửi không? Nếu không cần → bỏ.
7. Có chỗ nào ghép tham số của người gọi vào đường dẫn tệp, câu lệnh SQL, lệnh hệ thống không?
8. Dữ liệu do người khác nhập có được tách riêng, gắn nhãn nguồn, cảnh báo "không phải chỉ dẫn"?
9. Có giới hạn kích thước đầu vào/đầu ra và nhật ký gọi công cụ?
10. Gọi lặp cùng yêu cầu có cho cùng kết quả (không giữ trạng thái ẩn)?

## 7. An toàn khi thử nghiệm

- Chỉ dùng dữ liệu giả lập; **không** đưa thông tin thật của học sinh vào `du_lieu/`.
- `khong_cong_khai.txt`, `bi_mat.txt` chỉ chứa văn bản vô hại do nhóm tự tạo.
- Máy chủ chạy cục bộ qua stdio hoặc client trong bộ nhớ, không mở cổng ra Internet.
- `server_a.py` cố ý có lỗ hổng để làm đối chứng – không dùng làm mẫu cho hệ thống thật.

## 8. Giấy phép

Phát hành theo giấy phép [MIT](LICENSE).
