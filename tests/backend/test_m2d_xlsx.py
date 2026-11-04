"""M2d D3: deterministic XLSX writer tests (stdlib parse only, no API)."""

from __future__ import annotations

import copy
import io
import re
import time
import zipfile
from decimal import Decimal
from xml.etree import ElementTree as ET

import pytest

from app.domain.report.xlsx import write_xlsx

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
Q = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
SAVED = "2026-11-03T08:15:31.123456+00:00"
WEIRD_NAME = "Ống thép nhóm 002 — đặc biệt <&> \"q\" 'a'"


def make_report(n: int = 12, saved_utc: str = SAVED, generated_utc: str = "2026-11-04T01:00:00Z") -> dict:
    units, unplaced = [], []
    for i in range(n):
        pipe = i % 2 == 0
        status = ("PLACED", "UNPLACED", "EXCLUDED")[0 if i % 5 else (1 if i % 10 else 2)]
        req = "excluded" if status == "EXCLUDED" else ("required" if i % 3 else "optional")
        dims_um = [337600 + i * 1001, 911 * 1000 + i, 1234567 + i * 7]
        mass = 911400 + i * 13 - (i % 7) * 100000
        placed = status == "PLACED"
        u = {
            "id": f"U{i:04d}",
            "name": WEIRD_NAME if i == 0 else f"Bó {i}",
            "kind": "PIPE_BUNDLE" if pipe else "BAR_BUNDLE",
            "requirement": req,
            "group_id": f"G{i % 7:03d}" if pipe else None,
            "source_row": i + 2 if pipe else None,
            "revision_id": "BALTIMORE-PIPE-V1-1@R0000" if pipe else None,
            "confirmation": "CONFIRMED" if i % 4 else None,
            "dimension_warning": i % 9 == 0,
            "length_mm": dims_um[0] // 1000,
            "width_mm": dims_um[1] // 1000,
            "height_mm": dims_um[2] // 1000,
            "dimensions_um": dims_um,
            "mass_g": mass,
            "status": status,
            "placement": {"x_mm": 1234 + i * 3, "y_mm": -(i % 3) * 5 + 50, "z_mm": 0, "layer": 0, "yaw_deg": (i % 2) * 90} if placed else None,
            "packing": {
                "status": "DETAILED" if i % 4 == 0 else "ENVELOPE_ONLY",
                "layout": "HEX" if i % 4 == 0 else None,
                "columns": 3, "rows": 2, "pieces_placed": 6, "pieces_source": 7,
                "reason_codes": [],
            } if pipe else None,
        }
        units.append(u)
        if not placed:
            unplaced.append({
                "id": u["id"], "name": u["name"], "status": status, "requirement": req,
                "mass_g": mass, "dimensions_um": dims_um,
                "reason_code": "EXCLUDED" if status == "EXCLUDED" else "REQUIRED_UNPLACED",
                "reason": "Bó được loại trừ khỏi xếp." if status == "EXCLUDED" else "Hàng bắt buộc chưa được xếp.",
            })
    placed_n = sum(1 for u in units if u["status"] == "PLACED")
    return {
        "schema_version": "scst.plan-report.v1",
        "report_sha256": "ab" * 32,
        "header": {
            "plan_name": WEIRD_NAME, "snapshot_id": "snap-1", "saved_utc": saved_utc,
            "schema_version": "scst.saved-plan.v1", "contract_version": "1.2.3",
            "plan_sha256": "cd" * 32, "generated_utc": generated_utc,
        },
        "vessel": {
            "vessel_id": "VINAFCO268", "name": "VINAFCO 26-8", "case_id": "case-1", "builtin": False,
            "profile_version": 3, "profile_sha256": "ef" * 32,
            "field_status": {"dimensions_m": "SOURCED", "hold": "ESTIMATED", "cases": "MEASURED"},
        },
        "hold": {"id": "H1", "name": "Hầm 1", "length_mm": 41234, "width_mm": 11500, "height_mm": 7050, "status": "ESTIMATED"},
        "limits": {"certificate_cargo_limit_g": 5000000000, "voyage_cargo_limit_g": 4500000000, "cargo_onboard_g": 1000, "available_capacity_g": 4499999000},
        "cargo": {
            "plan_source": "pipe-list-v1", "cargo_source": "BALTIMORE", "dataset_id": "BALTIMORE-PIPE-V1-1",
            "revision_id": "BALTIMORE-PIPE-V1-1@R0000", "content_sha256": "12" * 32,
            "recheck": {"status": "NEEDS_RECHECK", "latest_revision_id": "X@R0001", "added": 1, "removed": 2, "changed": 3, "placed_affected": 4},
        },
        "totals": {
            "unit_count": n, "placed_count": placed_n, "unplaced_count": len([u for u in unplaced if u["status"] == "UNPLACED"]),
            "excluded_count": len([u for u in unplaced if u["status"] == "EXCLUDED"]),
            "manifest_mass_g": sum(u["mass_g"] for u in units),
            "placed_mass_g": sum(u["mass_g"] for u in units if u["status"] == "PLACED"),
            "remaining_capacity_g": 123456789,
            "manifest_envelope_volume_mm3": None, "placed_envelope_volume_mm3": 638350934,
            "manifest_envelope_volume_mm3_text": "638350934.4", "placed_envelope_volume_mm3_text": "638350934",
        },
        "units": units,
        "unplaced": unplaced,
        "issues": {
            "status": "BASIC_CHECKS_PASSED", "basic_checks_passed": True, "total_issues": 3, "issues_truncated": True,
            "items": [
                {"code": "OVERLAP", "unit_ids": ["U0001", "U0002"], "message": "Chồng lấn <&> \x00\x0b x"},
                {"code": "OOB", "unit_ids": [], "message": "Ra ngoài hầm"},
            ],
            "unchecked": ["Ổn định tàu", "Tải trọng sàn"], "operational_eligible": False,
        },
        "notices": [
            {"code": "SINGLE_LAYER", "message": "Phương án một tầng (xếp sơ bộ, chưa tối ưu)."},
            {"code": "NOT_OPERATIONAL", "message": "Chưa đủ điều kiện vận hành; các mục chưa kiểm: a · b."},
        ],
    }


def open_zip(data: bytes) -> zipfile.ZipFile:
    return zipfile.ZipFile(io.BytesIO(data))


def read_sheet(zf: zipfile.ZipFile, idx: int):
    """Return (root, rows) with rows as list of dict col_letter -> cell element."""
    root = ET.fromstring(zf.read(f"xl/worksheets/sheet{idx}.xml"))
    rows = []
    for row in root.find("m:sheetData", NS):
        d = {}
        for c in row:
            d[re.match(r"[A-Z]+", c.get("r")).group(0)] = c
        rows.append(d)
    return root, rows


def text_of(c) -> str:
    return "".join(t.text or "" for t in c.iter(Q + "t"))


def value_of(c) -> str:
    return c.find("m:v", NS).text


COLS = [
    "ID", "Tên", "Loại", "Yêu cầu", "Nhóm", "Revision", "Xác nhận", "Trạng thái xếp",
    "Dài (cm)", "Rộng (cm)", "Cao (cm)", "Khối lượng (kg)", "X (m)", "Y (m)", "Z (m)",
    "Góc xoay (°)", "Packing", "Cách xếp", "Số ống xếp", "Số ống nguồn",
    "Dài (µm)", "Rộng (µm)", "Cao (µm)", "Dài (mm)", "Rộng (mm)", "Cao (mm)",
    "Khối lượng (g)", "X (mm)", "Y (mm)", "Z (mm)",
]


def letter(i: int) -> str:
    out = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        out = chr(65 + r) + out
    return out


@pytest.fixture(scope="module")
def report():
    return make_report(40)


@pytest.fixture(scope="module")
def data(report):
    return write_xlsx(report)


def test_all_parts_parse_and_order(data):
    zf = open_zip(data)
    assert zf.testzip() is None
    assert zf.namelist() == [
        "[Content_Types].xml", "_rels/.rels", "xl/workbook.xml", "xl/_rels/workbook.xml.rels",
        "xl/styles.xml", "xl/worksheets/sheet1.xml", "xl/worksheets/sheet2.xml",
        "xl/worksheets/sheet3.xml", "xl/worksheets/sheet4.xml",
    ]
    for name in zf.namelist():
        ET.fromstring(zf.read(name))
    assert not any("sharedStrings" in n or "docProps" in n for n in zf.namelist())


def test_workbook_sheet_names(data):
    zf = open_zip(data)
    wb = ET.fromstring(zf.read("xl/workbook.xml"))
    names = [s.get("name") for s in wb.find("m:sheets", NS)]
    assert names == ["Tổng quan", "Hàng", "Chưa xếp", "Kiểm tra"]


def test_header_bold_and_frozen(data):
    zf = open_zip(data)
    styles = ET.fromstring(zf.read("xl/styles.xml"))
    fonts = list(styles.find("m:fonts", NS))
    xfs = list(styles.find("m:cellXfs", NS))
    for idx in range(1, 5):
        root, rows = read_sheet(zf, idx)
        for c in rows[0].values():
            xf = xfs[int(c.get("s"))]
            assert fonts[int(xf.get("fontId"))].find("m:b", NS) is not None
        pane = root.find("m:sheetViews/m:sheetView/m:pane", NS)
        assert pane.get("ySplit") == "1" and pane.get("topLeftCell") == "A2" and pane.get("state") == "frozen"
        assert root.find("m:cols", NS) is not None
    # number formats
    fmts = {f.get("numFmtId"): f.get("formatCode") for f in styles.find("m:numFmts", NS)}
    assert "0.000" in fmts.values() and "0.0###" in fmts.values()


def test_units_sheet_exact_and_display(report, data):
    zf = open_zip(data)
    _, rows = read_sheet(zf, 2)
    assert [text_of(rows[0][letter(i)]) for i in range(len(COLS))] == COLS
    assert len(rows) == 1 + len(report["units"])
    ci = {name: letter(i) for i, name in enumerate(COLS)}
    for u, row in zip(report["units"], rows[1:]):
        assert text_of(row[ci["ID"]]) == u["id"]
        assert text_of(row[ci["Tên"]]) == u["name"]
        # exact integer columns: numeric (no t attr)
        exact = {
            "Dài (µm)": u["dimensions_um"][0], "Rộng (µm)": u["dimensions_um"][1], "Cao (µm)": u["dimensions_um"][2],
            "Dài (mm)": u["length_mm"], "Rộng (mm)": u["width_mm"], "Cao (mm)": u["height_mm"],
            "Khối lượng (g)": u["mass_g"],
        }
        if u["placement"]:
            exact.update({"X (mm)": u["placement"]["x_mm"], "Y (mm)": u["placement"]["y_mm"], "Z (mm)": u["placement"]["z_mm"]})
        for col, val in exact.items():
            c = row[ci[col]]
            assert c.get("t") is None
            assert int(value_of(c)) == val and value_of(c) == str(val)
        disp = {
            "Dài (cm)": (u["dimensions_um"][0], 4), "Rộng (cm)": (u["dimensions_um"][1], 4), "Cao (cm)": (u["dimensions_um"][2], 4),
            "Khối lượng (kg)": (u["mass_g"], 3),
        }
        if u["placement"]:
            disp.update({"X (m)": (u["placement"]["x_mm"], 3), "Y (m)": (u["placement"]["y_mm"], 3), "Z (m)": (u["placement"]["z_mm"], 3)})
        for col, (val, k) in disp.items():
            c = row[ci[col]]
            assert c.get("t") is None
            txt = value_of(c)
            assert "e" not in txt.lower()
            assert Decimal(txt) == Decimal(val) / Decimal(10) ** k  # exact, no float
            assert not (txt.endswith("0") and "." in txt) and not txt.endswith(".")
        if not u["placement"]:
            for col in ("X (m)", "Y (m)", "Z (m)", "Góc xoay (°)", "X (mm)", "Y (mm)", "Z (mm)"):
                assert col not in {k for k in row if False} and ci[col] not in row
        if not u["packing"]:
            assert ci["Packing"] not in row and ci["Số ống xếp"] not in row


def test_display_texts_literal(data):
    zf = open_zip(data)
    r = make_report(1)
    u = r["units"][0]
    u["dimensions_um"] = [337600, 5, 1000000]
    u["mass_g"] = 911400
    u["placement"] = {"x_mm": -1, "y_mm": 0, "z_mm": 1500, "layer": 0, "yaw_deg": 90}
    u["status"] = "PLACED"
    _, rows = read_sheet(open_zip(write_xlsx(r)), 2)
    row = rows[1]
    assert value_of(row["I"]) == "33.76"
    assert value_of(row["J"]) == "0.0005"
    assert value_of(row["K"]) == "100"
    assert value_of(row["L"]) == "911.4"
    assert value_of(row["M"]) == "-0.001"
    assert value_of(row["N"]) == "0"
    assert value_of(row["O"]) == "1.5"
    assert text_of(row["H"]) == "Đã xếp" and text_of(row["C"]) == "Bó thép ống"


def test_labels_vietnamese(report, data):
    _, rows = read_sheet(open_zip(data), 2)
    seen = {text_of(r["H"]) for r in rows[1:]}
    assert seen == {"Đã xếp", "Chưa xếp", "Loại trừ"}
    assert {text_of(r["C"]) for r in rows[1:]} == {"Bó thép thanh", "Bó thép ống"}
    assert {text_of(r["D"]) for r in rows[1:]} == {"Bắt buộc", "Tùy chọn", "Loại trừ"}
    assert {text_of(r["Q"]) for r in rows[1:] if "Q" in r} == {"Chi tiết (dẫn xuất)", "Chỉ khối bao"}


def test_unicode_roundtrip_and_escape(report, data):
    zf = open_zip(data)
    raw = zf.read("xl/worksheets/sheet2.xml").decode("utf-8")
    assert "Ống thép nhóm 002 — đặc biệt &lt;&amp;&gt;" in raw
    _, rows = read_sheet(zf, 2)
    assert text_of(rows[1]["B"]) == WEIRD_NAME
    _, ov = read_sheet(zf, 1)
    assert any(text_of(r["B"]) == WEIRD_NAME for r in ov[1:] if "B" in r)


def test_control_chars_replaced(data):
    zf = open_zip(data)
    _, rows = read_sheet(zf, 4)
    assert text_of(rows[1]["C"]) == "Chồng lấn <&> �� x"
    for name in zf.namelist():
        assert not re.search("[\x00-\x08\x0b\x0c\x0e-\x1f]", zf.read(name).decode("utf-8"))
    r = make_report(2)
    r["units"][1]["name"] = "a\x01b\tc\nd\re\x1f\ud800"
    _, rows = read_sheet(open_zip(write_xlsx(r)), 2)
    assert text_of(rows[2]["B"]) == "a�b\tc\nd\re��"


def test_overview_and_other_sheets(report, data):
    zf = open_zip(data)
    _, ov = read_sheet(zf, 1)
    assert [text_of(ov[0][c]) for c in "ABC"] == ["Mục", "Giá trị", "Chính xác"]
    labels = {text_of(r["A"]): r for r in ov[1:]}
    allvals = " ".join(text_of(c) for r in ov for c in r.values())
    assert report["report_sha256"] in allvals and report["header"]["plan_sha256"] in allvals
    assert report["header"]["generated_utc"] not in allvals
    assert "Cảnh báo SINGLE_LAYER" in labels
    assert text_of(labels["Cảnh báo NOT_OPERATIONAL"]["B"]).startswith("Chưa đủ điều kiện vận hành")
    hold_len = labels["Hầm dài (m | mm chính xác)"]
    assert value_of(hold_len["B"]) == "41.234" and value_of(hold_len["C"]) == "41234" and hold_len["C"].get("t") is None
    lim = labels["Giới hạn hàng theo chứng chỉ (t | g chính xác)"]
    assert value_of(lim["B"]) == "5000" and value_of(lim["C"]) == "5000000000"
    mass = labels["Khối lượng bảng kê (kg | g chính xác)"]
    assert int(value_of(mass["C"])) == report["totals"]["manifest_mass_g"]
    vol = labels["Thể tích khối bao bảng kê (mm³ | mm³ chính xác nếu là số nguyên)"]
    assert value_of(vol["B"]) == "638350934.4" and "C" not in vol
    # unplaced
    _, up = read_sheet(zf, 3)
    assert len(up) == 1 + len(report["unplaced"])
    for u, row in zip(report["unplaced"], up[1:]):
        assert text_of(row["A"]) == u["id"] and int(value_of(row["F"])) == u["mass_g"]
        assert Decimal(value_of(row["E"])) == Decimal(u["mass_g"]) / 1000
        assert text_of(row["G"]) == u["reason"] and text_of(row["H"]) == u["reason_code"]
    # issues
    _, ks = read_sheet(zf, 4)
    assert text_of(ks[1]["A"]) == "OVERLAP" and text_of(ks[1]["B"]) == "U0001, U0002"
    assert text_of(ks[3]["A"]) == "Tổng số vấn đề" and value_of(ks[3]["B"]) == "3"
    assert "cắt bớt" in text_of(ks[3]["C"])
    assert [text_of(r["C"]) for r in ks[4:6]] == ["Ổn định tàu", "Tải trọng sàn"]
    assert text_of(ks[-1]["A"]) == "Chưa đủ điều kiện vận hành" and text_of(ks[-1]["B"]) == "Có"


def test_empty_and_no_vessel():
    r = make_report(0)
    r["vessel"] = None
    r["units"], r["unplaced"] = [], []
    r["issues"]["items"] = []
    zf = open_zip(write_xlsx(r))
    for i in range(1, 5):
        read_sheet(zf, i)


def test_deterministic_bytes(report):
    a, b = write_xlsx(report), write_xlsx(copy.deepcopy(report))
    assert a == b
    zf = open_zip(a)
    for zi in zf.infolist():
        assert zi.date_time == (2026, 11, 3, 8, 15, 30)
        assert zi.compress_type == zipfile.ZIP_DEFLATED
        assert zi.create_system == 3 and zi.external_attr == 0o644 << 16


def test_generated_utc_does_not_change_bytes():
    a = write_xlsx(make_report(20, generated_utc="2026-11-04T01:00:00Z"))
    b = write_xlsx(make_report(20, generated_utc="2030-01-01T00:00:00Z"))
    assert a == b


@pytest.mark.parametrize(
    "saved,expected",
    [
        ("2026-11-03T08:15:31Z", (2026, 11, 3, 8, 15, 30)),
        ("2026-11-03T10:15:31+02:00", (2026, 11, 3, 8, 15, 30)),
        ("2026-11-03T08:15:31", (2026, 11, 3, 8, 15, 30)),
        ("1970-01-01T00:00:00Z", (1980, 1, 1, 0, 0, 0)),
        ("garbage", (1980, 1, 1, 0, 0, 0)),
        ("", (1980, 1, 1, 0, 0, 0)),
        (None, (1980, 1, 1, 0, 0, 0)),
    ],
)
def test_zip_timestamp(saved, expected):
    zf = open_zip(write_xlsx(make_report(3, saved_utc=saved)))
    assert {zi.date_time for zi in zf.infolist()} == {expected}


def test_missing_saved_utc_key():
    r = make_report(3)
    del r["header"]["saved_utc"]
    assert {zi.date_time for zi in open_zip(write_xlsx(r)).infolist()} == {(1980, 1, 1, 0, 0, 0)}


@pytest.mark.parametrize("n", [1076, 2000])
def test_large_timing_and_exactness(n):
    r = make_report(n)
    t0 = time.perf_counter()
    data = write_xlsx(r)
    elapsed = time.perf_counter() - t0
    print(f"\nwrite_xlsx({n} units): {elapsed:.3f}s, {len(data)} bytes")
    assert elapsed < 5
    zf = open_zip(data)
    _, rows = read_sheet(zf, 2)
    assert len(rows) == n + 1
    ci = {name: letter(i) for i, name in enumerate(COLS)}
    for u, row in zip(r["units"], rows[1:]):
        assert int(value_of(row[ci["Khối lượng (g)"]])) == u["mass_g"]
        assert [int(value_of(row[ci[c]])) for c in ("Dài (µm)", "Rộng (µm)", "Cao (µm)")] == u["dimensions_um"]
    assert write_xlsx(r) == data
