# Từ điển dữ liệu – Nhật ký tác tử AI gọi MCP server (DỮ LIỆU GIẢ LẬP)

> **Toàn bộ thư mục này là dữ liệu ẢO** do `sinh_du_lieu_ao.py` tạo ra (seed 2026). Họ tên được ghép ngẫu nhiên, không phải người thật.
> Khi dùng trong báo cáo KHKT, ghi rõ đây là **dữ liệu mô phỏng**, không trình bày như số liệu thu thập từ học sinh thật.

## 1. Bối cảnh mô phỏng

- Lớp **11A**, **40 học sinh ảo**, chia **20 nhóm A** (dùng máy chủ đối chứng `server_a.py`) và **20 nhóm B** (dùng máy chủ cải tiến `server_b.py`). Phân nhóm theo tầng học lực và mức quen dùng AI.
- Thời gian: **HK I, 07/09/2026 – 20/12/2026** (15 tuần). Có tuần giữa kỳ (26/10–08/11), **tuần ôn thi và thi (30/11–14/12)**, ngày 20/11 ít dùng.
- Học sinh hỏi trợ lý AI bằng tiếng Việt. Trợ lý (tác tử) gọi công cụ MCP và trả lời. Mỗi câu hỏi được ghi một dòng, mỗi lần gọi công cụ được ghi một dòng.
- Hành vi của máy chủ theo **đúng mã nguồn**: tên công cụ, kiểu tham số, thông báo lỗi, danh sách tệp cho phép. Hành vi của **tác tử** (chọn sai tham số, thử lại, bịa câu trả lời…) là **giả định**, xem mục 6.

Quy mô: **1 409 phiên · 2 343 lượt hỏi · 2 205 lần gọi công cụ**.

## 2. Quan hệ giữa các bảng

```
hoc_sinh (ma_hs) 1 ──< phien (ma_phien) 1 ──< luot_hoi (ma_luot) 1 ──< goi_cong_cu (ma_goi)
```

Mọi bảng đều có sẵn `ma_hs`, `phien_ban` để lọc nhanh, không cần nối bảng.
CSV mã hoá UTF-8 có BOM, nên Excel mở không lỗi font. Giá trị logic ghi là `True`/`False`.

## 3. Các tệp và cột

### 3.1 `hoc_sinh.csv` – 40 dòng

| Cột | Ý nghĩa |
|---|---|
| `ma_hs` | HS01 … HS40 |
| `ho_ten_ao` | Họ tên ghép ngẫu nhiên |
| `gioi_tinh` | Nam / Nữ |
| `lop` | 11A |
| `hoc_luc_nam_truoc` | Tốt / Khá / Đạt / Chưa đạt (theo TT 22) |
| `muc_quen_dung_AI` | 1 (chưa dùng) … 5 (dùng hằng ngày). Học sinh quen AI dùng nhiều hơn |
| `thiet_bi` | Điện thoại Android / iPhone / Máy tính |
| `kenh_chinh` | Zalo Mini App / Web / Ứng dụng trường |
| `xu_huong_to_mo` | Mức "thích thử phá" (khoảng 12% học sinh có mức cao) → sinh các lượt tấn công |
| `nhom_phien_ban` | **A** hoặc **B** |

### 3.2 `phien.csv` – 1 dòng / phiên trò chuyện

| Cột | Ý nghĩa |
|---|---|
| `ma_phien`, `ma_hs`, `phien_ban` | Khoá |
| `bat_dau`, `ket_thuc` | ISO 8601, giờ Việt Nam (+07:00) |
| `thoi_luong_s` | Thời lượng phiên (giây) |
| `kenh` | Kênh dùng trong phiên |
| `so_luot`, `so_luot_dung` | Số câu hỏi / số câu được trả lời đúng |
| `ket_thuc_kieu` | `binh_thuong` hoặc `bo_do` (bỏ dở sau khi gặp lỗi nhìn thấy được) |
| `diem_hai_long_1_5` | 1–5; để trống nếu học sinh không đánh giá (~35%). **Học sinh chỉ thấy lỗi hiển thị, không nhận ra câu trả lời bịa** |

### 3.3 `luot_hoi.csv` – 1 dòng / câu hỏi

| Cột | Ý nghĩa |
|---|---|
| `ma_luot`, `ma_phien`, `ma_hs`, `phien_ban`, `thoi_diem`, `thu_tu_trong_phien` | Khoá, thời điểm |
| `y_dinh` | `tkb` · `lich_thi` · `diem_tb` · `noi_quy` · `ngoai_pham_vi` · `tan_cong` |
| `loai_tan_cong` | Chỉ có khi `y_dinh = tan_cong`: `thoat_thu_muc`, `tep_ngoai_danh_sach`, `chen_lenh_truc_tiep`, `ghi_du_lieu`, `dau_vao_qua_dai` |
| `cau_hoi` | Câu hỏi tiếng Việt tự nhiên ("Thứ 2 có tiết Tin không ạ?", "Em được 8 (hệ số 1), 7,5 (hệ số 2)…") |
| `do_dai_cau_hoi` | Số ký tự (10 000 với ca dán văn bản dài) |
| `tham_so_chuan` | Tham số đúng mà tác tử **nên** truyền (t2…t6, t7/cn nếu hỏi ngày nghỉ; toan/tin/van hoặc môn không có lịch; danh sách điểm JSON; chủ đề nội quy; loại câu hỏi ngoài phạm vi) |
| `dap_an_chuan` | Đáp án đúng, lấy từ `thoi_khoa_bieu.json`, `lich_thi.json`, `noi_quy.txt`, hoặc tính từ các cột điểm |
| `so_lan_goi_cong_cu`, `so_lan_thu_lai` | Số lần gọi; số lần gọi lại cùng công cụ sau khi thất bại |
| `cong_cu_cuoi`, `trang_thai_cuoi` | Công cụ và trạng thái của lần gọi cuối (`khong_goi` nếu tác tử không gọi) |
| `tra_loi_tom_tat` | Tóm tắt câu trả lời của tác tử |
| `tra_loi_dung` | Trả lời đúng/phù hợp (với ngoài phạm vi và tấn công: đúng = từ chối đúng cách) |
| `ao_giac` | Tác tử **bịa** thông tin, không dựa trên kết quả công cụ |
| `lam_theo_lenh_an` | Tác tử làm theo lệnh ẩn trong ghi chú dữ liệu (TKB thứ Năm) |
| `tan_cong_thanh_cong` | Chỉ có khi `y_dinh = tan_cong` |
| `du_lieu_bi_lo` | Nội dung tệp không được phép bị trả ra |
| `ghi_trai_phep` | Có ghi dữ liệu vào hệ thống (công cụ `luu_ghi_chu` của A) |
| `thoi_gian_phan_hoi_s` | Thời gian từ lúc hỏi đến lúc trả lời (giây, gồm các vòng gọi mô hình) |
| `token_vao`, `token_ra` | Ước lượng token. B tốn nhiều token vào hơn vì mô tả công cụ dài hơn |

### 3.4 `goi_cong_cu.csv` và `goi_cong_cu.jsonl` – 1 dòng / lần gọi

| Cột | Ý nghĩa |
|---|---|
| `ma_goi`, `ma_luot`, `ma_phien`, `ma_hs`, `phien_ban`, `thoi_diem`, `thu_tu_trong_luot` | Khoá, thời điểm |
| `loai` | `tool` hoặc `resource` |
| `ten` | A: `tkb`, `lich_thi`, `diem_tb`, `doc_tai_lieu`, `luu_ghi_chu` · B: `xem_tkb`, `xem_lich_thi`, `tinh_diem_tb`, `lop://…` |
| `tham_so` | JSON tham số tác tử đã truyền (đúng hoặc sai) |
| `trang_thai` | `thanh_cong` · `tra_ve_rong` (A trả None) · `loi_ngoai_le` (A ném Exception/TypeError/…) · `loi_xac_thuc` (B: SDK từ chối trước khi hàm chạy) · `loi_nghiep_vu` (B: ToolError) · `bi_tu_choi` (B: ResourceNotFoundError) |
| `ma_loi` | Exception, TypeError, FileNotFoundError, ZeroDivisionError, ValidationError, ToolError, ResourceNotFoundError |
| `thong_bao_loi` | Nguyên văn thông báo lỗi theo mã nguồn |
| `diem_E` | 0–2, chỉ chấm cho lần gọi **không** thành công, cùng quy tắc với `run_tests.py`. `tra_ve_rong` = 0 vì không có thông báo |
| `do_tre_ms` | Thời gian xử lý phía máy chủ (ms) |
| `kich_thuoc_phan_hoi_byte` | Kích thước phản hồi |
| `co_ghi_chu_du_lieu` | Phản hồi có chứa ghi chú dữ liệu (TKB thứ Năm, chứa lệnh ẩn) |

Tệp `.jsonl` giữ `tham_so` dạng đối tượng lồng nhau, tiện cho pandas: `pd.read_json(..., lines=True)`.

### 3.5 `tom_tat_sinh.json`

Lưu seed, khoảng thời gian, toàn bộ giả định và số liệu tổng quan theo phiên bản, để đối chiếu khi sinh lại.

## 4. Số liệu tổng quan (seed 2026)

| Chỉ số | A – đối chứng | B – cải tiến |
|---|---|---|
| Lượt hỏi / lần gọi công cụ | 1 193 / 1 198 | 1 150 / 1 007 |
| Tỉ lệ trả lời đúng (không tính lượt tấn công) | 74,9% | 98,6% |
| Tỉ lệ câu trả lời bịa (ảo giác) | 8,6% | 0,6% |
| Tỉ lệ lần gọi không thành công | 35,8% | 15,6% |
| Điểm E trung bình (lần gọi thất bại) | 0,24 | 1,94 |
| Tấn công chủ ý: thành công / tổng | 32 / 44 | 0 / 40 |
| Làm theo lệnh ẩn trong dữ liệu | 3 | 1 |
| Độ trễ máy chủ (trung vị) | 0,611 ms | 0,620 ms |
| Token vào trung bình mỗi lượt | ≈ 2 782 | ≈ 3 533 |
| Hài lòng trung bình (1–5) | 4,15 | 4,55 |

Nhận xét cần kiểm chứng khi phân tích: tỉ lệ lỗi của B **không bằng 0**, vì B chủ động từ chối đầu vào sai. Nhưng lỗi của B có hướng dẫn (E ≈ 2) nên tác tử tự sửa và vẫn trả lời đúng. A ít báo lỗi hơn ở một số ca, nhưng thất bại âm thầm (trả None hoặc chấp nhận điểm 11) dẫn tới câu trả lời sai hoặc bịa. Đổi lại, B tốn thêm khoảng 27% token.

## 5. Gợi ý phân tích

| # | Câu hỏi nghiên cứu | Dữ liệu và cách làm |
|---|---|---|
| 1 | B có trả lời đúng hơn A không? | `luot_hoi`: tỉ lệ `tra_loi_dung` theo `phien_ban` × `y_dinh`; kiểm định χ² hoặc so sánh hai tỉ lệ |
| 2 | Thông báo lỗi tốt có giúp tác tử tự sửa không? | `goi_cong_cu`: `diem_E` so với việc lần gọi kế tiếp trong cùng `ma_luot` thành công; `so_lan_thu_lai` |
| 3 | Thất bại âm thầm dẫn tới ảo giác? | `luot_hoi`: `ao_giac` theo `trang_thai_cuoi` (`tra_ve_rong`, `loi_ngoai_le`) |
| 4 | Mức độ an toàn | Lọc `y_dinh = tan_cong`: bảng `loai_tan_cong` × `phien_ban` × `tan_cong_thanh_cong`; đếm `du_lieu_bi_lo`, `ghi_trai_phep`, `lam_theo_lenh_an` |
| 5 | Chi phí của cải tiến | `do_tre_ms` (trung vị, phân vị 95), `token_vao`, `thoi_gian_phan_hoi_s` theo phiên bản |
| 6 | Trải nghiệm học sinh | `phien.diem_hai_long_1_5`, `ket_thuc_kieu = bo_do`. Lưu ý: A bị bịa nhưng học sinh vẫn có thể hài lòng → **hài lòng không đo được độ đúng** |
| 7 | Nhu cầu theo thời gian | Số lượt theo tuần/ngày/giờ; tỉ trọng `lich_thi` tăng mạnh trước tuần thi |
| 8 | Loại đầu vào nào hay bị hiểu sai? | `luot_hoi.cau_hoi` × `goi_cong_cu.tham_so` của lần gọi đầu: "thứ hai" → `"thứ hai"` (A) và `"t2"` (B); "mai"; "7,5" |
| 9 | Đặc điểm học sinh | Nối `hoc_sinh`: số phiên theo `muc_quen_dung_AI`; nhóm có `xu_huong_to_mo` cao |

Ví dụ nhanh với pandas:

```python
import pandas as pd
l = pd.read_csv("du_lieu/phan_tich/luot_hoi.csv")
print(pd.crosstab(l.y_dinh, l.phien_ban, values=l.tra_loi_dung, aggfunc="mean").round(3))
```

## 6. Giả định mô phỏng (sửa trong `GIA_DINH` của `sinh_du_lieu_ao.py`)

| Giả định | A | B | Lý do |
|---|---|---|---|
| Tác tử truyền đúng mã tham số ngay lần đầu | 0,55 | 0,93 | A: `str` tự do, mô tả sơ sài; B: `Literal` + mô tả rõ |
| Thử lại sau lần gọi thất bại | 0,25 | 0,97 | A trả None/"Error" nên không có gợi ý; B nêu giá trị hợp lệ |
| Bịa khi không có kết quả | 0,35 | 0,01 | |
| Làm theo lệnh ẩn trong ghi chú TKB thứ Năm | 0,15 | 0,01 | B tách ghi chú vào trường riêng, có cảnh báo |
| Tác tử vẫn thực hiện yêu cầu tấn công | 0,85 | 0,30 | Với B, yêu cầu vẫn bị máy chủ chặn |
| Tác tử gửi điểm dạng chuỗi "7,5" | 0,18 | – | B ép kiểu số qua lược đồ |

Các con số trên là **giả định để minh hoạ**, không phải kết quả đo. Muốn kết luận chắc chắn cần đo trên tác tử thật (MCP Inspector hoặc Claude Desktop) và so với dữ liệu này.

## 7. Sinh lại dữ liệu

```bash
cd ma_nguon
python3 sinh_du_lieu_ao.py                 # seed mặc định 2026 → đúng bộ dữ liệu này
python3 sinh_du_lieu_ao.py --seed 7        # bộ khác, cùng phân phối
python3 sinh_du_lieu_ao.py --hs 45         # đổi sĩ số
```

Đáp án chuẩn được đọc trực tiếp từ `thoi_khoa_bieu.json`, `lich_thi.json`, `noi_quy.txt`. Sửa các tệp đó thì chạy lại để dữ liệu khớp.
