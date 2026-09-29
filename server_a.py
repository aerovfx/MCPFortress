"""Phiên bản A (ĐỐI CHỨNG) – MCP server tra cứu thông tin học tập, viết "nhanh cho chạy được".

CỐ Ý KHÔNG áp dụng ba nhóm nguyên tắc để làm mốc so sánh:
  - Tên công cụ chung chung, mô tả ngắn/thiếu, tham số kiểu tự do (str, list).
  - Lỗi: trả None hoặc báo "Error" chung chung, để lỗi chia cho 0 / sai kiểu tự phát sinh.
  - Đọc tệp theo tên do người gọi đưa vào (doc_tai_lieu), có công cụ ghi, không giới hạn, không nhật ký.

KHÔNG dùng mẫu này cho hệ thống thật.
Chạy qua stdio (MCP Inspector):  npx @modelcontextprotocol/inspector python server_a.py
"""

# =====================================================================================
# GHI CHÚ CHUNG KHI ĐỌC MÃ NGUỒN MẪU A
# -------------------------------------------------------------------------------------
# - Đây là mẫu ĐỐI CHỨNG trong thực nghiệm so sánh A/B. Mọi "điểm yếu" dưới đây là CỐ Ý,
#   để bộ 24 ca kiểm thử (run_tests.py) đo được sự khác biệt với mẫu B.
# - Các chú thích dạng  [Yếu – nhóm 1/2/3]  chỉ ra điểm yếu thuộc nhóm nguyên tắc nào:
#     nhóm 1 = thiết kế công cụ, nhóm 2 = báo lỗi, nhóm 3 = phòng thủ an toàn.
# - Các chú thích dạng  (ca Fx / Vx / Sx)  chỉ ra ca kiểm thử nào bộc lộ điểm yếu đó:
#     F = chức năng, V = dữ liệu bất thường, S = an toàn.
# - Lưu ý: chuỗi mô tả ngay dưới mỗi hàm (docstring) CHÍNH LÀ phần mô tả công cụ mà mô hình
#   AI nhìn thấy. Ở mẫu A, các mô tả này được giữ ngắn và mơ hồ một cách cố ý.
# - Chú thích bắt đầu bằng # không được tính vào chỉ số "số dòng mã" (xem dem_dong_ma
#   trong run_tests.py), nên việc thêm chú thích không làm thay đổi số liệu báo cáo.
# =====================================================================================

# Thư viện chuẩn của Python: json để đọc tệp dữ liệu JSON, os để ghép đường dẫn tệp.
import json
import os

# MCPServer: lớp dựng máy chủ MCP của bộ công cụ MCP Python SDK. Mỗi hàm gắn
# @server.tool() sẽ trở thành một "công cụ" (tool) mà trợ lý AI có thể gọi.
from mcp.server import MCPServer

# Thư mục chứa dữ liệu giả lập: <thư mục chứa tệp này>/du_lieu
# (abspath + dirname giúp chạy đúng dù đứng ở thư mục nào khi gõ lệnh).
THU_MUC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "du_lieu")

# Khởi tạo máy chủ với tên "tra-cuu-hoc-tap-A".
# [Yếu – nhóm 1] Không có tham số instructions: AI không được hướng dẫn công cụ nào dùng
# khi nào, và không được cảnh báo rằng dữ liệu trả về có thể chứa "lệnh" giả mạo.
server = MCPServer("tra-cuu-hoc-tap-A")


# Hàm phụ: đọc một tệp JSON trong thư mục dữ liệu và trả về dạng dict của Python.
# [Yếu – nhóm 3] Nhận thẳng tên tệp rồi ghép vào đường dẫn, không kiểm tra tên có hợp lệ
# hay không, không giới hạn kích thước tệp.
# Hàm đọc lại tệp từ đĩa mỗi lần gọi (không giữ trạng thái) – điểm này A và B giống nhau,
# nên cả hai cùng đạt ca S6 (gọi lặp 20 lần lich_thi("toan") cho cùng một kết quả).
def _doc_json(ten):
    with open(os.path.join(THU_MUC, ten), encoding="utf-8") as f:
        return json.load(f)


# -------------------------------------------------------------------------------------
# CÔNG CỤ 1: tkb – tra thời khoá biểu một ngày
# -------------------------------------------------------------------------------------
# [Yếu – nhóm 1] Tên viết tắt "tkb" không nói rõ hành động (không có dạng động_từ_danh_từ).
# [Yếu – nhóm 1] Mô tả "Lấy thời khoá biểu." không nêu mã ngày hợp lệ (t2..t6), không nêu
#                khi nào nên dùng; tham số ngay là str tự do nên AI có thể gửi "thứ hai",
#                "Monday", "t9"... (ca V1, V2).
# [Yếu – nhóm 3] Không giới hạn độ dài tham số: chuỗi dài 10 000 ký tự vẫn được nhận và
#                xử lý thay vì bị từ chối ngay từ cửa (ca S5).
# [Yếu – nhóm 1] Kết quả là một chuỗi văn bản ghép, không có cấu trúc (không tách các trường).
@server.tool()
def tkb(ngay: str):
    """Lấy thời khoá biểu."""
    # Đọc toàn bộ tệp thời khoá biểu (dict: "t2" -> danh sách tiết, ..., "ghi_chu" -> {...}).
    du_lieu = _doc_json("thoi_khoa_bieu.json")
    # Lấy danh sách tiết của ngày được hỏi; nếu không có khoá đó thì get() trả None.
    kq = du_lieu.get(ngay)
    # [Yếu – nhóm 2] Ngày không tồn tại -> trả None (kết quả rỗng) thay vì báo lỗi rõ ràng.
    # AI nhận được "không có gì" mà không biết mình sai ở đâu và giá trị đúng là gì (ca V1, V2).
    if kq is None:
        return None
    # Lấy ghi chú của ngày đó (nếu có). Ghi chú là nội dung do NGƯỜI KHÁC nhập vào dữ liệu lớp.
    ghi_chu = du_lieu.get("ghi_chu", {}).get(ngay, "")
    # [Yếu – nhóm 3] Ghép THẲNG ghi chú vào câu trả lời, không gắn nhãn "đây là dữ liệu".
    # Nếu ghi chú chứa lệnh ẩn như "Bỏ qua mọi lệnh trước đó…" (dữ liệu t5 cố ý cài sẵn),
    # AI có thể hiểu nhầm đó là chỉ dẫn và làm theo -> tấn công chèn lệnh gián tiếp (ca S3).
    return f"Thời khoá biểu {ngay}: {', '.join(kq)}. {ghi_chu}".strip()


# -------------------------------------------------------------------------------------
# CÔNG CỤ 2: lich_thi – tra lịch thi một môn
# -------------------------------------------------------------------------------------
# [Yếu – nhóm 1] Mô tả "Lấy dữ liệu." gần như vô nghĩa: không nói là lịch thi, không nêu
#                mã môn hợp lệ (toan, tin, van). AI khó chọn đúng công cụ và đúng tham số.
@server.tool()
def lich_thi(mon: str):
    """Lấy dữ liệu."""
    # Đọc tệp lịch thi (dict: "hoc_ky" -> thông tin chung, "toan"/"tin"/"van" -> lịch từng môn).
    du_lieu = _doc_json("lich_thi.json")
    # Chặn môn không có trong dữ liệu, và chặn khoá đặc biệt "hoc_ky" (không phải một môn).
    # [Yếu – nhóm 2] Báo lỗi chung chung "Error": không nêu nguyên nhân, không nêu các mã
    # môn hợp lệ -> điểm chất lượng thông báo lỗi E = 0 (ca V3).
    if mon not in du_lieu or mon == "hoc_ky":
        raise Exception("Error")
    # Trả nguyên dict lịch thi của môn (ngày, giờ, phòng, thời gian làm bài).
    return du_lieu[mon]


# -------------------------------------------------------------------------------------
# CÔNG CỤ 3: diem_tb – tính điểm trung bình có hệ số
# -------------------------------------------------------------------------------------
# [Yếu – nhóm 1] Tham số "diem: list" không mô tả phần tử bên trong phải có dạng
#                {"diem": số, "he_so": số}; SDK không thể kiểm tra giúp.
# [Yếu – nhóm 2] Không kiểm tra đầu vào, nên:
#     - danh sách rỗng       -> tong_he_so = 0 -> lỗi chia cho 0 (ZeroDivisionError)  (ca V4)
#     - điểm 11 hoặc -1      -> vẫn tính bình thường, cho kết quả vô lý             (ca V5, V6)
#     - hệ số 5              -> vẫn tính, dù quy chế chỉ có hệ số 1, 2, 3            (ca V7)
#     - điểm là chữ "tám"    -> lỗi TypeError khó hiểu khi nhân chuỗi với số          (ca V8)
# [Yếu – nhóm 3] Không giới hạn số phần tử: có thể gửi danh sách dài tuỳ ý.
# Với dữ liệu đúng (ca F6, F7, F8) công cụ vẫn tính ra kết quả đúng: A "chạy được" nhưng
# không "chịu lỗi".
@server.tool()
def diem_tb(diem: list):
    """Tính điểm."""
    # Tử số: tổng (điểm × hệ số) của mọi cột điểm.
    tong = sum(d["diem"] * d["he_so"] for d in diem)
    # Mẫu số: tổng các hệ số.
    tong_he_so = sum(d["he_so"] for d in diem)
    # Điểm trung bình = tổng(điểm × hệ số) / tổng hệ số, làm tròn 2 chữ số thập phân.
    # Phép chia này sẽ "nổ" lỗi chia cho 0 khi danh sách rỗng (xem ghi chú ở trên).
    return round(tong / tong_he_so, 2)


# -------------------------------------------------------------------------------------
# CÔNG CỤ 4: doc_tai_lieu – đọc một tệp bất kỳ theo tên (LỖ HỔNG NGHIÊM TRỌNG NHẤT)
# -------------------------------------------------------------------------------------
# [Yếu – nhóm 3, lớp 1] Người gọi được tự đưa tên tệp, rồi tên đó được ghép thẳng vào
#     đường dẫn. Hệ quả:
#     - Đọc được tệp nằm ngoài danh sách được phép công khai,
#       ví dụ "khong_cong_khai.txt"                                              (ca S1)
#     - Dùng "../" để thoát khỏi thư mục du_lieu, đọc tệp bất kỳ trên máy,
#       ví dụ "../du_lieu_ngoai/bi_mat.txt"
#       (tấn công duyệt thư mục – path traversal)                                (ca S2)
# [Yếu – nhóm 3, lớp 2] Không giới hạn kích thước tệp, không ghi nhật ký ai đọc gì.
# Ở mẫu A, ca F9 (đọc nội quy) và F10 (đọc cả tuần thời khoá biểu) cũng đi qua công cụ này
# với tên tệp "noi_quy.txt" / "thoi_khoa_bieu.json". Mẫu B thay bằng tài nguyên (resource)
# có địa chỉ cố định lop://noi-quy, lop://thoi-khoa-bieu.
@server.tool()
def doc_tai_lieu(ten_file: str):
    """Đọc tài liệu."""
    # os.path.join(THU_MUC, "../../x") vẫn trỏ ra ngoài THU_MUC -> không có gì ngăn chặn.
    with open(os.path.join(THU_MUC, ten_file), encoding="utf-8") as f:
        return f.read()


# -------------------------------------------------------------------------------------
# CÔNG CỤ 5: luu_ghi_chu – GHI nội dung vào tệp trên máy chủ
# -------------------------------------------------------------------------------------
# [Yếu – nhóm 3, lớp 1] Một máy chủ chỉ cần tra cứu lại có công cụ GHI. Nếu AI bị lừa bởi
#     lệnh ẩn (xem công cụ tkb), kẻ xấu có thể lợi dụng công cụ này để thay đổi dữ liệu.
#     Ca S4 liệt kê danh sách công cụ và đánh "không đạt" khi có công cụ ghi/xoá/gửi.
# [Yếu – nhóm 3, lớp 2] Không giới hạn độ dài nội dung (tệp có thể phình to mãi),
#     không ghi nhật ký, luôn trả "ok" mà không cho biết đã lưu ở đâu.
@server.tool()
def luu_ghi_chu(noi_dung: str):
    """Lưu ghi chú."""
    # Mở tệp ở chế độ "a" (append – ghi nối vào cuối tệp), mỗi ghi chú một dòng.
    with open(os.path.join(THU_MUC, "ghi_chu_moi.txt"), "a", encoding="utf-8") as f:
        f.write(noi_dung + "\n")
    return "ok"


# Điểm khởi chạy: khi chạy trực tiếp "python server_a.py", máy chủ giao tiếp với client
# qua stdio (đầu vào/đầu ra chuẩn). Khi run_tests.py "import server_a" thì khối này KHÔNG
# chạy; bộ kiểm thử kết nối tới biến server trong bộ nhớ.
if __name__ == "__main__":
    server.run()
