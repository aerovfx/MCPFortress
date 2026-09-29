"""Chạy BỘ CA MỞ RỘNG (du_lieu/kiem_thu/bo_ca_mo_rong.json) trên hai phiên bản A và B.

Nhóm ca:
  MF_TKB / MF_THI / MF_DTB : chức năng – đầu vào hợp lệ, phải trả ĐÚNG giá trị
  MV_TKB / MV_THI / MV_DTB : dữ liệu bất thường – phải bị TỪ CHỐI; chấm thêm điểm thông báo lỗi E (0–2)
  MS_TEP                   : an toàn – không được làm lộ mã kiểm tra trong tệp mồi
  MS_TIEM                  : an toàn – ghi chú chứa câu lệnh chèn phải được tách riêng, có nhãn cảnh báo

Client kết nối trong bộ nhớ (không mở cổng mạng). Kết quả ghi vào ket_qua/:
  mo_rong_so_lieu_tho_<mốc>.csv  (từng ca × phiên bản × lần thử – GIỮ NGUYÊN, kể cả ca lỗi)
  mo_rong_tong_hop_<mốc>.json

Chạy:  python chay_kiem_thu_mo_rong.py            (1 lần thử)
       python chay_kiem_thu_mo_rong.py --lan 3    (3 lần thử liên tiếp)
"""

import argparse
import asyncio
import csv
import json
import logging
import os
import re
import statistics
import time

from mcp import Client

import server_a
import server_b

GOC = os.path.dirname(os.path.abspath(__file__))
TEP_CA = os.path.join(GOC, "du_lieu", "kiem_thu", "bo_ca_mo_rong.json")
MA = {"S1": "[MA_KIEM_TRA_S1]", "S2": "[MA_KIEM_TRA_S2]"}
LOI_CHUNG = re.compile(r"^\s*(error|lỗi)?\s*$|^Error executing tool \w+\s*$|^Unknown resource", re.I)
logging.getLogger("mcp").setLevel(logging.CRITICAL)


def thay_the(gia_tri):
    if gia_tri == "{DUONG_DAN_TUYET_DOI_BI_MAT}":
        return os.path.join(GOC, "du_lieu_ngoai", "bi_mat.txt")
    return gia_tri


def spec(ver, ca):
    t, g = ca["thao_tac"], thay_the(ca["gia_tri"])
    A = ver == "A"
    if t == "tkb":
        return ("tool", "tkb" if A else "xem_tkb", {"ngay": g})
    if t == "lich_thi":
        return ("tool", "lich_thi" if A else "xem_lich_thi", {"mon": g})
    if t == "diem_tb":
        return ("tool", "diem_tb", {"diem": g}) if A else ("tool", "tinh_diem_tb", {"cac_diem": g})
    if t == "doc_tep":  # A có công cụ đọc tệp tuỳ ý; B chỉ có resource địa chỉ cố định -> thử ghép vào URI
        return ("tool", "doc_tai_lieu", {"ten_file": g}) if A else ("resource", f"lop://tai-lieu/{g}", None)
    raise ValueError(t)


async def goi(client, s):
    loai, ten, doi_so = s
    try:
        if loai == "tool":
            r = await client.call_tool(ten, doi_so)
            vb = "\n".join(getattr(c, "text", "") for c in r.content)
            return bool(r.is_error), vb, r.structured_content
        r = await client.read_resource(ten)
        return False, "\n".join(getattr(c, "text", "") for c in r.contents), None
    except Exception as e:  # noqa: BLE001 – ghi lại mọi lỗi như số liệu thô
        return True, f"{type(e).__name__}: {e}", None


def diem_E(van_ban, goi_y):
    if not van_ban or LOI_CHUNG.search(van_ban.strip()):
        return 0
    return 2 if any(g.lower() in van_ban.lower() for g in goi_y) else 1


def cham(ca, tu_choi, vb, ct):
    """Trả về (dat, ghi_chu, E hoặc None, ro_ri)."""
    nhom, kv, dung = ca["nhom"], ca["ky_vong"], ca["gia_tri_dung"]
    toan_bo = vb + json.dumps(ct, ensure_ascii=False) if ct else vb
    ro_ri = any(m in toan_bo for m in MA.values())
    if nhom == "MS_TEP":
        return (not ro_ri), ("LỘ mã " + dung if ro_ri else "không lộ"), None, ro_ri
    if nhom == "MS_TIEM":
        ghi_chu = (ct or {}).get("ghi_chu_du_lieu") or {}
        dat = (not tu_choi) and bool(ghi_chu.get("canh_bao"))
        return dat, ("ghi chú được tách + có cảnh báo" if dat else "ghi chú trộn lẫn vào lời đáp"), None, ro_ri
    if kv == "tu_choi":
        E = diem_E(vb, ca["goi_y_hop_le"]) if tu_choi else 0
        return tu_choi, ("bị từ chối" if tu_choi else f"CHẤP NHẬN SAI -> {vb[:60]!r}"), E, ro_ri
    if tu_choi:
        return False, f"từ chối nhầm: {vb[:60]!r}", None, ro_ri
    if nhom == "MF_DTB":
        so = ct.get("diem_trung_binh", ct.get("result")) if isinstance(ct, dict) else None
        if so is None:
            m = re.search(r"-?\d+(?:\.\d+)?", vb)
            so = float(m.group()) if m else None
        dat = so is not None and abs(float(so) - dung) < 0.006
        return dat, f"trả {so}, đúng {dung}", None, ro_ri
    dat = all(x in toan_bo for x in dung)
    return dat, ("đủ nội dung" if dat else "thiếu nội dung"), None, ro_ri


async def chay_mot_lan(lan, ca_list):
    dong = []
    for ver, srv in (("A", server_a.server), ("B", server_b.server)):
        async with Client(srv) as c:
            for ca in ca_list:
                t0 = time.perf_counter()
                tu_choi, vb, ct = await goi(c, spec(ver, ca))
                ms = (time.perf_counter() - t0) * 1000
                dat, ghi_chu, E, ro_ri = cham(ca, tu_choi, vb, ct)
                dong.append({"lan": lan, "ver": ver, "ma": ca["ma"], "nhom": ca["nhom"], "ky_vong": ca["ky_vong"],
                             "bi_tu_choi": tu_choi, "dat": dat, "E": E, "ro_ri": ro_ri,
                             "t_ms": round(ms, 3), "ghi_chu": ghi_chu,
                             "phan_hoi_rut_gon": vb[:160].replace("\n", " ")})
    p = os.path.join(GOC, "du_lieu", "ghi_chu_moi.txt")
    if os.path.exists(p):
        os.remove(p)
    return dong


def tong_hop(dong):
    kq = {}
    for ver in ("A", "B"):
        d = [x for x in dong if x["ver"] == ver]
        theo_nhom = {}
        for n in sorted({x["nhom"] for x in d}):
            dn = [x for x in d if x["nhom"] == n]
            theo_nhom[n] = {"so_ca": len(dn), "dat": sum(x["dat"] for x in dn),
                            "ti_le_%": round(100 * sum(x["dat"] for x in dn) / len(dn), 1)}
        Es = [x["E"] for x in d if x["E"] is not None]
        kq[ver] = {"so_luot": len(d), "dat": sum(x["dat"] for x in d),
                   "ti_le_dat_%": round(100 * sum(x["dat"] for x in d) / len(d), 1),
                   "E_tb_0_2": round(statistics.mean(Es), 2) if Es else None,
                   "so_lan_ro_ri": sum(x["ro_ri"] for x in d),
                   "T_tb_ms": round(statistics.mean(x["t_ms"] for x in d), 3),
                   "T_trung_vi_ms": round(statistics.median(x["t_ms"] for x in d), 3),
                   "theo_nhom": theo_nhom,
                   "ca_khong_dat": sorted({x["ma"] for x in d if not x["dat"]})}
    return kq


async def chay(so_lan=1, moc=None):
    bo = json.load(open(TEP_CA, encoding="utf-8"))
    moc = moc or time.strftime("%Y%m%d_%H%M%S")
    dong, theo_lan = [], []
    for lan in range(1, so_lan + 1):
        d = await chay_mot_lan(lan, bo["ca"])
        dong += d
        theo_lan.append(tong_hop(d))
    th = {"moc": moc, "seed": bo["seed"], "so_ca": bo["so_ca"], "so_lan": so_lan,
          "theo_lan": theo_lan, "gop": tong_hop(dong)}
    thu_muc = os.path.join(GOC, "ket_qua"); os.makedirs(thu_muc, exist_ok=True)
    p_csv = os.path.join(thu_muc, f"mo_rong_so_lieu_tho_{moc}.csv")
    with open(p_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(dong[0].keys()))
        w.writeheader(); w.writerows(dong)
    p_json = os.path.join(thu_muc, f"mo_rong_tong_hop_{moc}.json")
    with open(p_json, "w", encoding="utf-8") as f:
        json.dump(th, f, ensure_ascii=False, indent=1)
    th["tep"] = {"csv": os.path.relpath(p_csv, GOC), "json": os.path.relpath(p_json, GOC)}
    return th, dong


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Chạy bộ ca kiểm thử mở rộng trên A và B")
    ap.add_argument("--lan", type=int, default=1, help="số lần thử liên tiếp (mặc định 1)")
    a = ap.parse_args()
    if not os.path.exists(TEP_CA):
        raise SystemExit("Chưa có bộ ca. Chạy trước: python sinh_du_lieu_kiem_thu.py")
    th, _ = asyncio.run(chay(a.lan))
    for ver in ("A", "B"):
        g = th["gop"][ver]
        print(f"\nPhiên bản {ver}: đạt {g['dat']}/{g['so_luot']} ({g['ti_le_dat_%']}%), E={g['E_tb_0_2']}, "
              f"rò rỉ={g['so_lan_ro_ri']}, T={g['T_tb_ms']} ms")
        for n, v in g["theo_nhom"].items():
            print(f"   {n:8} {v['dat']:>4}/{v['so_ca']:<4} {v['ti_le_%']:>6}%")
    print(f"\nĐã ghi {th['tep']['csv']} và {th['tep']['json']}")
