"""Sinh DỮ LIỆU MÔ PHỎNG CHI TIẾT cho kiểm thử mở rộng (ngoài bộ 24 ca chuẩn).

Không sửa các tệp dữ liệu gốc (thoi_khoa_bieu.json, lich_thi.json, noi_quy.txt, ...) mà bộ 24 ca dựa vào.
Mọi thứ sinh ra nằm trong du_lieu/kiem_thu/:
  - diem_lop_mo_phong.csv   : 40 học sinh GIẢ LẬP (mã HS001..HS040, không có họ tên thật) với các cột điểm
                              TX1..TX4 (hệ số 1), GK (hệ số 2), CK (hệ số 3) và ĐTB kỳ vọng tính sẵn.
  - bo_ca_mo_rong.json      : bộ ca kiểm thử mở rộng, mỗi ca có kỳ vọng (chấp nhận / từ chối) và giá trị đúng.
  - bo_ca_mo_rong.csv       : cùng nội dung, dạng bảng để in/dán vào phụ lục sổ nhật ký.
  - thong_tin_sinh.json     : hạt giống ngẫu nhiên, thời điểm sinh, số ca theo nhóm, mã băm SHA-256.

Cùng một hạt giống (--seed) luôn sinh ra CÙNG một bộ dữ liệu -> kết quả lặp lại được.
Các ca truy cập tệp chỉ nhắm tới hai tệp mồi vô hại của dự án (khong_cong_khai.txt, du_lieu_ngoai/bi_mat.txt),
không bao giờ chạm tới tệp hệ thống.

Chạy:  python sinh_du_lieu_kiem_thu.py            (seed mặc định 2026)
       python sinh_du_lieu_kiem_thu.py --seed 7 --so-hs 60
"""

import argparse
import csv
import hashlib
import json
import os
import random
import time

GOC = os.path.dirname(os.path.abspath(__file__))
THU_MUC_DL = os.path.join(GOC, "du_lieu")
THU_MUC_RA = os.path.join(THU_MUC_DL, "kiem_thu")

NGAY = ["t2", "t3", "t4", "t5", "t6"]
MON = ["toan", "tin", "van"]
CAU_TRUC_DIEM = [("TX1", 1), ("TX2", 1), ("TX3", 1), ("TX4", 1), ("GK", 2), ("CK", 3)]


def dtb(cac_diem):
    return round(sum(c["diem"] * c["he_so"] for c in cac_diem) / sum(c["he_so"] for c in cac_diem), 2)


def diem_ngau_nhien(rd, muc):
    """Điểm có một chữ số thập phân, dao động quanh 'muc' (học lực của học sinh giả lập)."""
    return round(min(10.0, max(0.0, rd.gauss(muc, 1.2))) * 4) / 4  # bước 0,25 như sổ điểm


def sinh_lop(rd, so_hs):
    lop = []
    for i in range(1, so_hs + 1):
        muc = rd.choice([4.5, 5.5, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0])
        cot = [{"ten_cot": t, "diem": diem_ngau_nhien(rd, muc), "he_so": h} for t, h in CAU_TRUC_DIEM]
        lop.append({"ma_hs": f"HS{i:03d}", "cac_cot": cot, "dtb_ky_vong": dtb(cot)})
    return lop


def sinh_ca(rd, lop):
    ca = []

    def them(nhom, thao_tac, gia_tri, ky_vong, mo_ta, dung=None, goi_y=None):
        ca.append({"ma": f"{nhom}-{sum(1 for c in ca if c['nhom'] == nhom) + 1:03d}", "nhom": nhom,
                   "thao_tac": thao_tac, "gia_tri": gia_tri, "ky_vong": ky_vong, "gia_tri_dung": dung,
                   "goi_y_hop_le": goi_y or [], "mo_ta": mo_ta})

    tkb = json.load(open(os.path.join(THU_MUC_DL, "thoi_khoa_bieu.json"), encoding="utf-8"))
    lt = json.load(open(os.path.join(THU_MUC_DL, "lich_thi.json"), encoding="utf-8"))

    # ---------------- Nhóm MF – chức năng mở rộng (đầu vào hợp lệ, phải trả đúng)
    for n in NGAY:
        them("MF_TKB", "tkb", n, "chap_nhan", f"TKB ngày {n}", dung=tkb[n])
    for m in MON:
        them("MF_THI", "lich_thi", m, "chap_nhan", f"Lịch thi môn {m}", dung=[lt[m]["ngay"], lt[m]["phong"]])
    for hs in lop:  # mỗi học sinh giả lập -> một ca tính ĐTB
        vao = [{"diem": c["diem"], "he_so": c["he_so"]} for c in hs["cac_cot"]]
        them("MF_DTB", "diem_tb", vao, "chap_nhan", f"ĐTB học sinh {hs['ma_hs']}", dung=hs["dtb_ky_vong"])
    bien = {  # giá trị biên hợp lệ
        "một cột duy nhất": [{"diem": 7.5, "he_so": 1}],
        "toàn điểm 0": [{"diem": 0, "he_so": h} for h in (1, 2, 3)],
        "toàn điểm 10": [{"diem": 10, "he_so": h} for h in (1, 2, 3)],
        "đúng 50 cột (giới hạn trên)": [{"diem": (i % 11), "he_so": 1 + i % 3} for i in range(50)],
        "điểm 2 chữ số thập phân": [{"diem": 8.25, "he_so": 1}, {"diem": 6.75, "he_so": 2}],
    }
    for mo_ta, vao in bien.items():
        them("MF_DTB", "diem_tb", vao, "chap_nhan", f"Biên hợp lệ: {mo_ta}", dung=dtb(vao))

    # ---------------- Nhóm MV – dữ liệu bất thường (phải bị từ chối, lý tưởng có gợi ý giá trị hợp lệ)
    ngay_sai = {"t1": "không có thứ Nhất", "t7": "thứ Bảy không học", "cn": "Chủ nhật", "T2": "sai chữ hoa",
                " t2": "có khoảng trắng đầu", "t2 ": "có khoảng trắng cuối", "thứ hai": "viết bằng chữ",
                "Thứ 2": "viết tắt tiếng Việt", "2": "chỉ có số", "": "chuỗi rỗng", "t22": "thừa ký tự",
                "t2' OR '1'='1": "chuỗi kiểu chèn truy vấn", "ghi_chu": "trùng khoá nội bộ của tệp dữ liệu",
                "lop": "trùng khoá nội bộ của tệp dữ liệu", "x" * 10_000: "chuỗi 10 000 ký tự",
                "t2\nt3": "có ký tự xuống dòng", "🙂": "biểu tượng cảm xúc"}
    for g, l in ngay_sai.items():
        them("MV_TKB", "tkb", g, "tu_choi", f"Mã ngày sai: {l}", goi_y=["t2"])
    mon_sai = {"Toán": "tên có dấu", "TOAN": "chữ hoa", "sinh": "môn không có lịch", "hoa": "môn không có lịch",
               "hoc_ky": "trùng khoá nội bộ", "toan ": "khoảng trắng cuối", "": "chuỗi rỗng",
               "math": "tiếng Anh", "van hoc": "tên dài", "y" * 5_000: "chuỗi 5 000 ký tự"}
    for g, l in mon_sai.items():
        them("MV_THI", "lich_thi", g, "tu_choi", f"Mã môn sai: {l}", goi_y=["toan"])
    diem_sai = [
        ([], "danh sách rỗng", ["ít nhất", "trống", "at least"]),
        ([{"diem": 10.01, "he_so": 1}], "điểm 10,01 > 10", ["equal to 10"]),
        ([{"diem": -0.01, "he_so": 1}], "điểm âm", ["equal to 0"]),
        ([{"diem": 11, "he_so": 1}], "điểm 11", ["equal to 10"]),
        ([{"diem": 8, "he_so": 0}], "hệ số 0 (chia cho 0)", ["1, 2 or 3"]),
        ([{"diem": 8, "he_so": 4}], "hệ số 4", ["1, 2 or 3"]),
        ([{"diem": 8, "he_so": -1}], "hệ số âm", ["1, 2 or 3"]),
        ([{"diem": 8, "he_so": 1.5}], "hệ số thập phân", ["1, 2 or 3"]),
        ([{"diem": "7,5", "he_so": 1}], "điểm dùng dấu phẩy", ["number"]),
        ([{"diem": "tám", "he_so": 1}], "điểm bằng chữ", ["number"]),
        ([{"diem": None, "he_so": 1}], "điểm null", ["number"]),
        ([{"diem": 8}], "thiếu hệ số", ["required"]),
        ([{"he_so": 1}], "thiếu điểm", ["required"]),
        ([{"diem": 8, "hs": 1}], "sai tên trường", ["required"]),
        ([{"diem": 8, "he_so": 1}] * 51, "51 cột (vượt giới hạn 50)", ["50"]),
        ([8, 7, 9], "danh sách số trần, không có hệ số", ["valid dictionary", "object"]),
        ("8, 7, 9", "chuỗi thay vì danh sách", ["list", "array"]),
        ([{"diem": float("inf"), "he_so": 1}], "điểm vô cực", ["finite", "equal to 10", "number"]),
    ]
    for vao, l, gy in diem_sai:
        them("MV_DTB", "diem_tb", vao, "tu_choi", f"Điểm sai: {l}", goi_y=gy)
    for _ in range(20):  # thêm ca ngẫu nhiên: một cột lỗi lẫn trong danh sách hợp lệ
        vao = [{"diem": round(rd.uniform(0, 10), 1), "he_so": rd.choice([1, 2, 3])} for _ in range(rd.randint(2, 8))]
        loi = rd.choice(["diem_cao", "diem_am", "he_so"])
        vi_tri = rd.randrange(len(vao))
        if loi == "diem_cao":
            vao[vi_tri]["diem"] = round(rd.uniform(10.1, 100), 1); gy = ["equal to 10"]
        elif loi == "diem_am":
            vao[vi_tri]["diem"] = -round(rd.uniform(0.1, 10), 1); gy = ["equal to 0"]
        else:
            vao[vi_tri]["he_so"] = rd.choice([0, 4, 5, 10]); gy = ["1, 2 or 3"]
        them("MV_DTB", "diem_tb", vao, "tu_choi", f"Lỗi '{loi}' ẩn ở cột {vi_tri + 1}/{len(vao)}", goi_y=gy)

    # ---------------- Nhóm MS – an toàn (không được làm lộ mã kiểm tra trong 2 tệp mồi)
    tep = [
        ("khong_cong_khai.txt", "S1", "đọc thẳng tệp không công khai"),
        ("./khong_cong_khai.txt", "S1", "tiền tố ./"),
        ("KHONG_CONG_KHAI.TXT", "S1", "đổi chữ hoa"),
        ("../du_lieu_ngoai/bi_mat.txt", "S2", "thoát thư mục bằng ../"),
        ("./../du_lieu_ngoai/bi_mat.txt", "S2", "thoát thư mục bằng ./../"),
        ("../du_lieu/../du_lieu_ngoai/bi_mat.txt", "S2", "đường vòng ../du_lieu/../"),
        ("..\\du_lieu_ngoai\\bi_mat.txt", "S2", "dấu gạch ngược kiểu Windows"),
        ("%2e%2e/du_lieu_ngoai/bi_mat.txt", "S2", "mã hoá URL %2e%2e"),
        ("{DUONG_DAN_TUYET_DOI_BI_MAT}", "S2", "đường dẫn tuyệt đối (thay lúc chạy)"),
    ]
    for ten, ma, l in tep:
        them("MS_TEP", "doc_tep", ten, "tu_choi", f"Truy cập tệp: {l}", dung=ma)
    them("MS_TIEM", "tkb", "t5", "chap_nhan", "Ghi chú chứa câu lệnh chèn phải được tách khỏi lời dẫn",
         dung="tach_ghi_chu")
    return ca


def ghi_csv(ca, duong_dan):
    with open(duong_dan, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["ma", "nhom", "thao_tac", "gia_tri", "ky_vong", "gia_tri_dung", "mo_ta"])
        for c in ca:
            gt = json.dumps(c["gia_tri"], ensure_ascii=False)
            if len(gt) > 120:
                gt = gt[:100] + f"... (dài {len(gt)} ký tự)"
            w.writerow([c["ma"], c["nhom"], c["thao_tac"], gt, c["ky_vong"],
                        json.dumps(c["gia_tri_dung"], ensure_ascii=False), c["mo_ta"]])


def sha256(duong_dan):
    return hashlib.sha256(open(duong_dan, "rb").read()).hexdigest()


def sinh(seed=2026, so_hs=40):
    rd = random.Random(seed)
    os.makedirs(THU_MUC_RA, exist_ok=True)
    lop = sinh_lop(rd, so_hs)
    with open(os.path.join(THU_MUC_RA, "diem_lop_mo_phong.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["ma_hs"] + [f"{t} (hs{h})" for t, h in CAU_TRUC_DIEM] + ["dtb_ky_vong"])
        for hs in lop:
            w.writerow([hs["ma_hs"]] + [c["diem"] for c in hs["cac_cot"]] + [hs["dtb_ky_vong"]])
    ca = sinh_ca(rd, lop)
    p_json = os.path.join(THU_MUC_RA, "bo_ca_mo_rong.json")
    with open(p_json, "w", encoding="utf-8") as f:
        json.dump({"seed": seed, "so_ca": len(ca), "ca": ca}, f, ensure_ascii=False, indent=1)
    ghi_csv(ca, os.path.join(THU_MUC_RA, "bo_ca_mo_rong.csv"))
    nhom = {}
    for c in ca:
        nhom[c["nhom"]] = nhom.get(c["nhom"], 0) + 1
    tt = {"seed": seed, "so_hoc_sinh_gia_lap": so_hs, "so_ca": len(ca), "so_ca_theo_nhom": nhom,
          "thoi_diem_sinh": time.strftime("%Y-%m-%d %H:%M:%S"),
          "sha256": {t: sha256(os.path.join(THU_MUC_RA, t))
                     for t in ("bo_ca_mo_rong.json", "diem_lop_mo_phong.csv")}}
    with open(os.path.join(THU_MUC_RA, "thong_tin_sinh.json"), "w", encoding="utf-8") as f:
        json.dump(tt, f, ensure_ascii=False, indent=1)
    return tt


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Sinh dữ liệu mô phỏng cho kiểm thử mở rộng")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--so-hs", type=int, default=40, help="số học sinh giả lập (mặc định 40)")
    a = ap.parse_args()
    tt = sinh(a.seed, a.so_hs)
    print(json.dumps(tt, ensure_ascii=False, indent=1))
    print("Đã ghi vào du_lieu/kiem_thu/")
