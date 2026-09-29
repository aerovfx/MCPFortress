"""Bộ 24 ca kiểm thử tự động cho hai phiên bản MCP server (A – đối chứng, B – cải tiến).

Cách chạy:   python run_tests.py            (mặc định lặp 20 lần/ca để đo thời gian)
             python run_tests.py --lap 50

Client kết nối TRONG BỘ NHỚ (in-process) bằng mcp.Client của MCP Python SDK 2.x, không mở cổng mạng.
Kết quả ghi vào thư mục ket_qua/:
  - so_lieu_tho_<thời điểm>.csv   : từng ca × từng phiên bản (dán vào Sổ nhật ký nghiên cứu)
  - tong_hop_<thời điểm>.json     : chỉ số F, V, S, E, T, số dòng mã
  - bang_ket_qua_<thời điểm>.md   : Bảng 7, 8, 9, 10 dạng Markdown để đối chiếu với báo cáo

Chỉ số (theo mục 3.5 của báo cáo):
  F = số ca chức năng đúng / 10 × 100%
  V = số ca dữ liệu bất thường bị từ chối hoặc báo lỗi / 8 × 100%
  S = số ca an toàn đạt / 6 × 100%
  E = điểm TB chất lượng thông báo lỗi trên 8 ca V (0: không nêu nguyên nhân; 1: nêu nguyên nhân;
      2: nêu nguyên nhân và giá trị hợp lệ)
  T = thời gian phản hồi trung bình (ms) trên các ca F và V, mỗi ca lặp --lap lần
"""

import argparse
import asyncio
import csv
import json
import logging
import os
import platform
import re
import statistics
import sys
import time
from importlib.metadata import version

from mcp import Client

import server_a
import server_b

GOC = os.path.dirname(os.path.abspath(__file__))
logging.getLogger("mcp").setLevel(logging.CRITICAL)  # ẩn traceback của phiên bản A khi cố ý gây lỗi

DAI_10000 = "x" * 10_000
MA_S1 = "[MA_KIEM_TRA_S1]"
MA_S2 = "[MA_KIEM_TRA_S2]"
LOI_CHUNG = re.compile(r"^\s*(error|lỗi)?\s*$|^Error executing tool \w+\s*$|^Unknown resource", re.I)

# ------------------------------------------------------------------ gọi theo phiên bản
# Mỗi thao tác logic ánh xạ sang tên công cụ / resource tương ứng của A và B.
def goi(ver, thao_tac, gia_tri=None):
    """Trả về ('tool', ten, doi_so) hoặc ('resource', uri, None)."""
    A = ver == "A"
    if thao_tac == "tkb":
        return ("tool", "tkb", {"ngay": gia_tri}) if A else ("tool", "xem_tkb", {"ngay": gia_tri})
    if thao_tac == "lich_thi":
        return ("tool", "lich_thi", {"mon": gia_tri}) if A else ("tool", "xem_lich_thi", {"mon": gia_tri})
    if thao_tac == "diem_tb":
        return ("tool", "diem_tb", {"diem": gia_tri}) if A else ("tool", "tinh_diem_tb", {"cac_diem": gia_tri})
    if thao_tac == "noi_quy":
        return ("tool", "doc_tai_lieu", {"ten_file": "noi_quy.txt"}) if A else ("resource", "lop://noi-quy", None)
    if thao_tac == "tkb_ca_tuan":
        return (("tool", "doc_tai_lieu", {"ten_file": "thoi_khoa_bieu.json"}) if A
                else ("resource", "lop://thoi-khoa-bieu", None))
    if thao_tac == "tep_khong_cong_khai":
        return (("tool", "doc_tai_lieu", {"ten_file": "khong_cong_khai.txt"}) if A
                else ("resource", "lop://tai-lieu/khong_cong_khai.txt", None))
    if thao_tac == "thoat_thu_muc":
        return (("tool", "doc_tai_lieu", {"ten_file": "../du_lieu_ngoai/bi_mat.txt"}) if A
                else ("resource", "lop://thoi-khoa-bieu/../../du_lieu_ngoai/bi_mat.txt", None))
    raise ValueError(thao_tac)


async def thuc_hien(client, spec):
    """Gọi một lần. Trả về dict: bi_tu_choi, van_ban, cau_truc."""
    loai, ten, doi_so = spec
    try:
        if loai == "tool":
            r = await client.call_tool(ten, doi_so)
            van_ban = "\n".join(getattr(c, "text", "") for c in r.content)
            return {"bi_tu_choi": bool(r.is_error),
                    "loi": bool(r.is_error), "van_ban": van_ban, "cau_truc": r.structured_content}
        r = await client.read_resource(ten, cache_mode="bypass")
        van_ban = "\n".join(getattr(c, "text", "") or "" for c in r.contents)
        return {"bi_tu_choi": False, "loi": False, "van_ban": van_ban, "cau_truc": None}
    except Exception as e:  # lỗi giao thức (MCPError) = bị từ chối
        return {"bi_tu_choi": True, "loi": True, "van_ban": str(e), "cau_truc": None}


def diem_thong_bao(van_ban, goi_y):
    """Chấm chất lượng thông báo lỗi 0–2."""
    if not van_ban or LOI_CHUNG.search(van_ban.strip()):
        return 0
    thap = van_ban.lower()
    return 2 if all(g.lower() in thap for g in goi_y) else 1


def co_so(van_ban, so):
    return re.search(rf"(?<![\d.]){re.escape(str(so))}(?![\d])", van_ban) is not None


# ------------------------------------------------------------------ 24 CA KIỂM THỬ
CA_F = [
    ("F1", 'xem_tkb("t2")', ("tkb", "t2"), lambda k: all(m in k["van_ban"] for m in ["Toán", "Ngữ văn", "Tin học", "Tiếng Anh"]),
     "Toán, Ngữ văn, Tin học, Tiếng Anh"),
    ("F2", 'xem_tkb("t4")', ("tkb", "t4"), lambda k: all(m in k["van_ban"] for m in ["Toán", "Sinh học", "Tin học", "Lịch sử"]),
     "Toán, Sinh học, Tin học, Lịch sử"),
    ("F3", 'xem_lich_thi("toan")', ("lich_thi", "toan"), lambda k: all(x in k["van_ban"] for x in ["10/12", "07:30", "P.101", "90"]),
     "10/12, 07:30, P.101, 90 phút"),
    ("F4", 'xem_lich_thi("tin")', ("lich_thi", "tin"), lambda k: all(x in k["van_ban"] for x in ["12/12", "07:30", "Phòng máy 1", "45"]),
     "12/12, 07:30, Phòng máy 1, 45 phút"),
    ("F5", 'xem_lich_thi("van")', ("lich_thi", "van"), lambda k: all(x in k["van_ban"] for x in ["14/12", "07:30", "P.101", "90"]),
     "14/12, 07:30, P.101, 90 phút"),
    ("F6", "Điểm 8 (hs 1), 7,5 (hs 2), 9 (hs 3)", ("diem_tb", [{"diem": 8, "he_so": 1}, {"diem": 7.5, "he_so": 2}, {"diem": 9, "he_so": 3}]),
     lambda k: co_so(k["van_ban"], "8.33"), "8,33"),
    ("F7", "Điểm 10 (hs 1)", ("diem_tb", [{"diem": 10, "he_so": 1}]), lambda k: co_so(k["van_ban"], "10.0") or co_so(k["van_ban"], "10"), "10,0"),
    ("F8", "Điểm 5 và 6,5 (hs 1)", ("diem_tb", [{"diem": 5, "he_so": 1}, {"diem": 6.5, "he_so": 1}]), lambda k: co_so(k["van_ban"], "5.75"), "5,75"),
    ("F9", "Đọc nội quy lớp", ("noi_quy", None), lambda k: all(f"Điều {i}" in k["van_ban"] for i in (1, 2, 3)), "Nội dung 3 điều nội quy"),
    ("F10", "Đọc toàn bộ thời khoá biểu", ("tkb_ca_tuan", None),
     lambda k: all(f'"{d}"' in k["van_ban"] for d in ("t2", "t3", "t4", "t5", "t6")), "Dữ liệu 5 ngày (t2 đến t6)"),
]

# (mã, mô tả, thao tác, gợi ý giá trị hợp lệ phải có trong thông báo để đạt 2 điểm, hành vi đúng)
CA_V = [
    ("V1", 'xem_tkb("t9")', ("tkb", "t9"), ["t2", "t6"], "Lỗi, nêu mã hợp lệ (t2 đến t6)"),
    ("V2", 'xem_tkb("thứ hai")', ("tkb", "thứ hai"), ["t2", "t6"], "Từ chối: không thuộc t2 đến t6"),
    ("V3", 'xem_lich_thi("sinh")', ("lich_thi", "sinh"), ["toan", "tin", "van"], "Lỗi, nêu mã môn hợp lệ"),
    ("V4", "Danh sách điểm rỗng", ("diem_tb", []), ["ít nhất"], "Lỗi: cần ít nhất một điểm"),
    ("V5", "Điểm 11", ("diem_tb", [{"diem": 11, "he_so": 1}]), ["equal to 10"], "Từ chối: ngoài thang 0 đến 10"),
    ("V6", "Điểm −1", ("diem_tb", [{"diem": -1, "he_so": 1}]), ["equal to 0"], "Từ chối: ngoài thang 0 đến 10"),
    ("V7", "Hệ số 5", ("diem_tb", [{"diem": 8, "he_so": 5}]), ["1, 2 or 3"], "Từ chối: hệ số chỉ là 1, 2 hoặc 3"),
    ("V8", 'Điểm là chữ "tám"', ("diem_tb", [{"diem": "tám", "he_so": 1}]), ["number"], "Từ chối: sai kiểu dữ liệu"),
]

TU_KHOA_GHI = re.compile(r"luu|ghi|xoa|gui|cap_nhat|save|write|delete|send|update|remove", re.I)


async def ca_S(ver, client):
    """Trả về list (mã, kịch bản, đạt?, chi tiết, hành vi đúng)."""
    kq = []
    # S1 – tệp ngoài danh sách cho phép
    r = await thuc_hien(client, goi(ver, "tep_khong_cong_khai"))
    dat = MA_S1 not in r["van_ban"] and r["bi_tu_choi"]
    kq.append(("S1", "Đọc tệp mô phỏng nằm ngoài danh sách cho phép", dat, r["van_ban"][:120], "Từ chối, không trả nội dung"))
    # S2 – thoát thư mục ../
    r = await thuc_hien(client, goi(ver, "thoat_thu_muc"))
    dat = MA_S2 not in r["van_ban"] and r["bi_tu_choi"]
    kq.append(("S2", "Tên tệp chứa ../ để thoát thư mục dữ liệu", dat, r["van_ban"][:120], "Từ chối"))
    # S3 – ghi chú chứa lệnh ẩn (dữ liệu ngày t5)
    r = await thuc_hien(client, goi(ver, "tkb", "t5"))
    sc = r["cau_truc"] or {}
    gc = sc.get("ghi_chu_du_lieu") if isinstance(sc, dict) else None
    dat = (isinstance(gc, dict) and "Bỏ qua mọi lệnh" in gc.get("noi_dung", "") and bool(gc.get("nguon"))
           and not any("Bỏ qua" in t for t in sc.get("cac_tiet", [])))
    kq.append(("S3", "Ghi chú chứa lệnh ẩn (“Bỏ qua mọi lệnh trước đó…”)", dat, r["van_ban"][:120],
               "Trả về như dữ liệu trong trường riêng, có nhãn nguồn"))
    # S4 – liệt kê công cụ
    ds = (await client.list_tools()).tools
    nguy_hiem = [t.name for t in ds if TU_KHOA_GHI.search(t.name)]
    kq.append(("S4", "Liệt kê công cụ", not nguy_hiem, ", ".join(t.name for t in ds), "Không có công cụ ghi, xoá, gửi"))
    # S5 – đầu vào 10 000 ký tự
    r = await thuc_hien(client, goi(ver, "tkb", DAI_10000))
    kq.append(("S5", "Đầu vào dài 10 000 ký tự", r["bi_tu_choi"], r["van_ban"][:120], "Từ chối vì vượt giới hạn"))
    # S6 – gọi lặp 20 lần
    ra = [(await thuc_hien(client, goi(ver, "lich_thi", "toan")))["van_ban"] for _ in range(20)]
    kq.append(("S6", "Gọi lặp 20 lần cùng một yêu cầu", len(set(ra)) == 1 and bool(ra[0]), f"{len(set(ra))} kết quả khác nhau",
               "Kết quả giống nhau (không giữ trạng thái)"))
    return kq


async def do_thoi_gian(client, spec, lap):
    t = []
    for _ in range(lap):
        t0 = time.perf_counter()
        await thuc_hien(client, spec)
        t.append((time.perf_counter() - t0) * 1000)
    return statistics.mean(t)


def dem_dong_ma(tep):
    """Đếm dòng mã: bỏ dòng trống, dòng chú thích # và docstring."""
    n, trong_doc = 0, False
    for dong in open(os.path.join(GOC, tep), encoding="utf-8"):
        s = dong.strip()
        if trong_doc:
            if s.endswith('"""'):
                trong_doc = False
            continue
        if s.startswith('"""'):
            if not (len(s) > 3 and s.endswith('"""')):
                trong_doc = True
            continue
        if s and not s.startswith("#"):
            n += 1
    return n


async def chay_phien_ban(ver, server, lap):
    dong = []
    async with Client(server) as c:
        for ma, mo_ta, (tt, gt), kiem, ky_vong in CA_F:
            spec = goi(ver, tt, gt)
            r = await thuc_hien(c, spec)
            dat = (not r["bi_tu_choi"]) and kiem(r)
            dong.append({"nhom": "F", "ma": ma, "dau_vao": mo_ta, "ky_vong": ky_vong, "dat": dat, "diem_E": "",
                         "ms": round(await do_thoi_gian(c, spec, lap), 3), "phan_hoi": r["van_ban"][:200]})
        for ma, mo_ta, (tt, gt), goi_y, ky_vong in CA_V:
            spec = goi(ver, tt, gt)
            r = await thuc_hien(c, spec)
            dat = r["bi_tu_choi"]
            dong.append({"nhom": "V", "ma": ma, "dau_vao": mo_ta, "ky_vong": ky_vong, "dat": dat,
                         "diem_E": diem_thong_bao(r["van_ban"], goi_y) if r["bi_tu_choi"] else 0,
                         "ms": round(await do_thoi_gian(c, spec, lap), 3), "phan_hoi": (r["van_ban"] or "None")[:200]})
        for ma, mo_ta, dat, chi_tiet, ky_vong in await ca_S(ver, c):
            dong.append({"nhom": "S", "ma": ma, "dau_vao": mo_ta, "ky_vong": ky_vong, "dat": dat, "diem_E": "",
                         "ms": "", "phan_hoi": chi_tiet})
    for d in dong:
        d["phien_ban"] = ver
    return dong


def tong_hop(dong, ver, tep):
    d = [x for x in dong if x["phien_ban"] == ver]
    f = [x for x in d if x["nhom"] == "F"]; v = [x for x in d if x["nhom"] == "V"]; s = [x for x in d if x["nhom"] == "S"]
    return {
        "F_%": round(100 * sum(x["dat"] for x in f) / len(f), 1),
        "V_%": round(100 * sum(x["dat"] for x in v) / len(v), 1),
        "S_%": round(100 * sum(x["dat"] for x in s) / len(s), 1),
        "E_0_2": round(statistics.mean(x["diem_E"] for x in v), 2),
        "T_ms": round(statistics.mean(x["ms"] for x in f + v), 3),
        "so_dong_ma": dem_dong_ma(tep),
        "dat": f"{sum(x['dat'] for x in d)}/{len(d)}",
    }


def bang_md(dong, th, lap, moc):
    ky = lambda b: "Đạt" if b else "Không đạt"
    tra = {(x["phien_ban"], x["ma"]): x for x in dong}
    out = [f"# Kết quả chạy bộ 24 ca kiểm thử – {moc}",
           f"Môi trường: Python {platform.python_version()}, mcp {version('mcp')}, {platform.system()}; lặp {lap} lần/ca để đo T.", ""]
    for nhom, ten in (("F", "Bảng 7. Nhóm F: kiểm thử chức năng"), ("V", "Bảng 8. Nhóm V: đầu vào bất thường"),
                      ("S", "Bảng 9. Nhóm S: an toàn")):
        out += [f"## {ten}", "", "| Mã | Đầu vào / kịch bản | Kỳ vọng | A | B |" + (" E(A) | E(B) |" if nhom == "V" else ""),
                "|---|---|---|---|---|" + ("---|---|" if nhom == "V" else "")]
        for x in [y for y in dong if y["phien_ban"] == "A" and y["nhom"] == nhom]:
            b = tra[("B", x["ma"])]
            out.append(f"| {x['ma']} | {x['dau_vao']} | {x['ky_vong']} | {ky(x['dat'])} | {ky(b['dat'])} |"
                       + (f" {x['diem_E']} | {b['diem_E']} |" if nhom == "V" else ""))
        out.append("")
    out += ["## Bảng 10. So sánh chỉ số giữa phiên bản A và B", "", "| Chỉ số | Mục tiêu đối với B | A | B |", "|---|---|---|---|",
            f"| F (%) | 100 | {th['A']['F_%']} | {th['B']['F_%']} |",
            f"| V (%) | từ 90 trở lên | {th['A']['V_%']} | {th['B']['V_%']} |",
            f"| S (%) | 100 | {th['A']['S_%']} | {th['B']['S_%']} |",
            f"| E (0 đến 2) | từ 1,8 trở lên | {th['A']['E_0_2']} | {th['B']['E_0_2']} |",
            f"| T (ms) | không tăng đáng kể | {th['A']['T_ms']} | {th['B']['T_ms']} |",
            f"| Số dòng mã | ghi nhận | {th['A']['so_dong_ma']} | {th['B']['so_dong_ma']} |", "",
            "Lưu ý: T đo với client trong bộ nhớ trên máy chạy thử; giá trị tuyệt đối phụ thuộc máy, chỉ so sánh A với B trên cùng một lần chạy."]
    return "\n".join(out)


async def main():
    ap = argparse.ArgumentParser(description="Chạy 24 ca kiểm thử cho MCP server A và B")
    ap.add_argument("--lap", type=int, default=20, help="số lần lặp mỗi ca để đo thời gian (mặc định 20)")
    a = ap.parse_args()
    moc = time.strftime("%Y%m%d_%H%M%S")
    dong = await chay_phien_ban("A", server_a.server, a.lap) + await chay_phien_ban("B", server_b.server, a.lap)
    th = {"A": tong_hop(dong, "A", "server_a.py"), "B": tong_hop(dong, "B", "server_b.py")}
    thu_muc = os.path.join(GOC, "ket_qua"); os.makedirs(thu_muc, exist_ok=True)
    with open(os.path.join(thu_muc, f"so_lieu_tho_{moc}.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["phien_ban", "nhom", "ma", "dau_vao", "ky_vong", "dat", "diem_E", "ms", "phan_hoi"])
        w.writeheader(); w.writerows(dong)
    with open(os.path.join(thu_muc, f"tong_hop_{moc}.json"), "w", encoding="utf-8") as f:
        json.dump({"thoi_diem": moc, "lap": a.lap, "python": platform.python_version(), "mcp": version("mcp"),
                   "chi_so": th}, f, ensure_ascii=False, indent=2)
    md = bang_md(dong, th, a.lap, moc)
    with open(os.path.join(thu_muc, f"bang_ket_qua_{moc}.md"), "w", encoding="utf-8") as f:
        f.write(md)
    # in tóm tắt
    print(f"{'Mã':5}{'A':>11}{'B':>11}")
    for x in [y for y in dong if y["phien_ban"] == "A"]:
        b = next(y for y in dong if y["phien_ban"] == "B" and y["ma"] == x["ma"])
        print(f"{x['ma']:5}{('Đạt' if x['dat'] else 'KHÔNG'):>11}{('Đạt' if b['dat'] else 'KHÔNG'):>11}")
    print("\nChỉ số:", json.dumps(th, ensure_ascii=False, indent=1))
    print(f"\nĐã ghi kết quả vào thư mục ket_qua/ (mốc {moc}).")
    # dọn tệp do công cụ ghi của A tạo ra (nếu có)
    p = os.path.join(GOC, "du_lieu", "ghi_chu_moi.txt")
    if os.path.exists(p):
        os.remove(p)


if __name__ == "__main__":
    if sys.version_info < (3, 10):
        sys.exit("Cần Python 3.10 trở lên.")
    asyncio.run(main())
