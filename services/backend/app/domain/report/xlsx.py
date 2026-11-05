"""Deterministic, standard-library-only XLSX writer for scst.plan-report.v1 (M2d D3).

``write_xlsx(report)`` is pure: it takes the report model (a dict, see the
shared report contract) and returns the bytes of a minimal Office Open XML
workbook. No I/O, no third-party packages, no imports from the package.

Determinism: the same model yields the same bytes. ``header.generated_utc`` is
deliberately NOT written anywhere (it changes on every download and is
excluded from ``report_sha256`` too). Zip members are written in a fixed order
with a ZipInfo timestamp derived from ``header.saved_utc`` (UTC, year >= 1980,
even seconds; (1980, 1, 1, 0, 0, 0) when missing or unparsable), fixed
``external_attr`` / ``create_system`` and a fixed compression level.

Numbers are numeric cells. Display values (cm, kg, m, t) are the EXACT decimal
value written as decimal text computed with integer arithmetic (never float);
exact values (um, mm, g) are integer cells. Strings are inline strings (no
sharedStrings part). Not verified with real Excel (stdlib parse only).
"""

from __future__ import annotations

import re
import zipfile
from datetime import datetime, timezone
from xml.sax.saxutils import escape as _xml_escape

__all__ = ["write_xlsx"]

SHEET_NAMES = ("Tổng quan", "Hàng", "Chưa xếp", "Kiểm tra")

# styles.xml cellXfs indices
S_DEFAULT = 0
S_HEADER = 1  # bold
S_KG = 2  # numFmt 164 "0.000"
S_CM = 3  # numFmt 165 "0.0###"
S_M = 4  # numFmt 164 "0.000"
S_INT = 5  # numFmt 1 "0"
S_T = 6  # numFmt 164 "0.000" (tonnes)

_ILLEGAL_RE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff￾￿]")

_STATUS_VI = {"PLACED": "Đã xếp", "UNPLACED": "Chưa xếp", "EXCLUDED": "Loại trừ"}
_REQ_VI = {"required": "Bắt buộc", "optional": "Tùy chọn", "excluded": "Loại trừ"}
_KIND_VI = {"BAR_BUNDLE": "Bó thép thanh", "PIPE_BUNDLE": "Bó thép ống"}
_PACK_VI = {"DETAILED": "Chi tiết (dẫn xuất)", "ENVELOPE_ONLY": "Chỉ khối bao"}


# --------------------------------------------------------------------------
# value helpers
# --------------------------------------------------------------------------
class _N:
    """Numeric cell: ``text`` is the decimal text written into <v>."""

    __slots__ = ("text", "style")

    def __init__(self, text: str, style: int = S_DEFAULT) -> None:
        self.text = text
        self.style = style


def _dec(n: int, k: int) -> str:
    """Exact decimal text of n / 10**k using integer arithmetic only."""
    n = int(n)
    if k <= 0:
        return str(n)
    sign = "-" if n < 0 else ""
    s = str(abs(n)).rjust(k + 1, "0")
    ip, fp = s[:-k], s[-k:].rstrip("0")
    out = ip + "." + fp if fp else ip
    if out == "0":
        return "0"
    return sign + out


def _num(n, k: int, style: int):
    return None if n is None else _N(_dec(n, k), style)


def _int(n):
    return None if n is None else _N(str(int(n)), S_INT)


def _yn(b) -> str:
    return "Có" if b else "Không"


def _s(v):
    """None stays None; everything else becomes text."""
    return None if v is None else str(v)


def _clean(text: str) -> str:
    return _ILLEGAL_RE.sub("�", text)


def _esc(text: str) -> str:
    return _xml_escape(_clean(text), {'"': "&quot;", "\r": "&#13;"})


def _col(i: int) -> str:
    """0-based column index -> letters."""
    out = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        out = chr(65 + r) + out
    return out


_COLS = [_col(i) for i in range(64)]


def _cell(ref: str, v, style_default: int) -> str:
    if v is None:
        return ""
    if isinstance(v, _N):
        st = v.style
        sa = f' s="{st}"' if st else ""
        return f'<c r="{ref}"{sa}><v>{v.text}</v></c>'
    sa = f' s="{style_default}"' if style_default else ""
    return (
        f'<c r="{ref}"{sa} t="inlineStr"><is><t xml:space="preserve">'
        f"{_esc(v)}</t></is></c>"
    )


def _sheet_xml(header: list, rows: list, widths: list) -> str:
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    ]
    ncols = max([len(header)] + [len(r) for r in rows]) if rows else len(header)
    last = f"{_COLS[ncols - 1]}{len(rows) + 1}"
    parts.append(f'<dimension ref="A1:{last}"/>')
    parts.append(
        '<sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        '<selection pane="bottomLeft" activeCell="A2" sqref="A2"/>'
        "</sheetView></sheetViews>"
    )
    parts.append('<sheetFormatPr defaultRowHeight="15"/>')
    parts.append(
        "<cols>"
        + "".join(
            f'<col min="{i + 1}" max="{i + 1}" width="{w}" customWidth="1"/>'
            for i, w in enumerate(widths)
        )
        + "</cols>"
    )
    parts.append("<sheetData>")
    parts.append(
        '<row r="1">'
        + "".join(_cell(f"{_COLS[i]}1", h, S_HEADER) for i, h in enumerate(header))
        + "</row>"
    )
    for ri, row in enumerate(rows, start=2):
        parts.append(
            f'<row r="{ri}">'
            + "".join(_cell(f"{_COLS[i]}{ri}", v, S_DEFAULT) for i, v in enumerate(row))
            + "</row>"
        )
    parts.append("</sheetData></worksheet>")
    return "".join(parts)


# --------------------------------------------------------------------------
# sheets
# --------------------------------------------------------------------------
def _overview_rows(r: dict) -> list:
    rows: list = []
    add = rows.append
    h = r.get("header") or {}
    add(["Tên phương án", _s(h.get("plan_name"))])
    add(["Mã snapshot", _s(h.get("snapshot_id"))])
    add(["Thời điểm lưu (UTC)", _s(h.get("saved_utc"))])
    add(["Phiên bản hợp đồng", _s(h.get("contract_version"))])
    add(["plan_sha256", _s(h.get("plan_sha256"))])
    add(["report_sha256", _s(r.get("report_sha256"))])

    v = r.get("vessel")
    if v:
        add(["Tàu", _s(v.get("name"))])
        add(["Mã tàu", _s(v.get("vessel_id"))])
        add(["Ca tàu", _s(v.get("case_id"))])
        add(["Tàu có sẵn (built-in)", _yn(v.get("builtin"))])
        add(["Phiên bản hồ sơ tàu", _int(v.get("profile_version"))])
        add(["Hồ sơ tàu sha256", _s(v.get("profile_sha256"))])
        fs = v.get("field_status") or {}
        add(["Trạng thái kích thước tàu", _s(fs.get("dimensions_m"))])
        add(["Trạng thái hầm (hồ sơ)", _s(fs.get("hold"))])
        add(["Trạng thái ca hàng", _s(fs.get("cases"))])
    else:
        add(["Tàu", "Không có hồ sơ tàu"])

    hd = r.get("hold") or {}
    add(["Hầm", _s(hd.get("name"))])
    add(["Mã hầm", _s(hd.get("id"))])
    for label, key in (("Dài", "length_mm"), ("Rộng", "width_mm"), ("Cao", "height_mm")):
        mm = hd.get(key)
        add([f"Hầm {label.lower()} (m | mm chính xác)", _num(mm, 3, S_M), _int(mm)])
    add(["Trạng thái kích thước hầm", _s(hd.get("status"))])

    lim = r.get("limits") or {}
    for label, key in (
        ("Giới hạn hàng theo chứng chỉ", "certificate_cargo_limit_g"),
        ("Giới hạn hàng chuyến", "voyage_cargo_limit_g"),
        ("Hàng đang trên tàu", "cargo_onboard_g"),
        ("Sức chứa còn lại", "available_capacity_g"),
    ):
        g = lim.get(key)
        add([f"{label} (t | g chính xác)", _num(g, 6, S_T), _int(g)])

    c = r.get("cargo") or {}
    add(["Nguồn phương án", _s(c.get("plan_source"))])
    add(["Nguồn hàng", _s(c.get("cargo_source"))])
    add(["Dataset", _s(c.get("dataset_id"))])
    add(["Revision hàng", _s(c.get("revision_id"))])
    add(["Revision content_sha256", _s(c.get("content_sha256"))])
    rc = c.get("recheck") or {}
    add(["Trạng thái kiểm lại", _s(rc.get("status"))])
    add(["Revision mới nhất", _s(rc.get("latest_revision_id"))])
    add(["Kiểm lại: số bó thêm", _int(rc.get("added"))])
    add(["Kiểm lại: số bó bỏ", _int(rc.get("removed"))])
    add(["Kiểm lại: số bó đổi", _int(rc.get("changed"))])
    add(["Kiểm lại: số bó đã đặt bị ảnh hưởng", _int(rc.get("placed_affected"))])

    t = r.get("totals") or {}
    add(["Tổng số bó", _int(t.get("unit_count"))])
    add(["Số bó đã xếp", _int(t.get("placed_count"))])
    add(["Số bó chưa xếp", _int(t.get("unplaced_count"))])
    if r.get("stacking") == "COLUMNS_V1":
        add(["Cách xếp", "Nhiều tầng theo cột (COLUMNS_V1)"])
        add(["Tổng số tầng", _int(t.get("layer_count"))])
        add(["Số cột", _int(t.get("column_count"))])
    add(["Số bó loại trừ", _int(t.get("excluded_count"))])
    for label, key in (
        ("Khối lượng bảng kê", "manifest_mass_g"),
        ("Khối lượng đã xếp", "placed_mass_g"),
        ("Sức chứa còn lại (tổng)", "remaining_capacity_g"),
    ):
        g = t.get(key)
        add([f"{label} (kg | g chính xác)", _num(g, 3, S_KG), _int(g)])
    for label, key in (
        ("Thể tích khối bao bảng kê", "manifest_envelope_volume_mm3"),
        ("Thể tích khối bao đã xếp", "placed_envelope_volume_mm3"),
    ):
        txt = t.get(key + "_text")
        add(
            [
                f"{label} (mm³ | mm³ chính xác nếu là số nguyên)",
                _N(txt) if txt else None,
                _int(t.get(key)),
            ]
        )

    for n in r.get("notices") or []:
        add([f"Cảnh báo {n.get('code', '')}".rstrip(), _s(n.get("message"))])
    return rows


def _units_rows(r: dict) -> list:
    rows = []
    for u in r.get("units") or []:
        dim = u.get("dimensions_um") or [None, None, None]
        pl = u.get("placement")
        pk = u.get("packing")
        mass = u.get("mass_g")
        row = [
            _s(u.get("id")),
            _s(u.get("name")),
            _KIND_VI.get(u.get("kind"), _s(u.get("kind"))),
            _REQ_VI.get(u.get("requirement"), _s(u.get("requirement"))),
            _s(u.get("group_id")),
            _s(u.get("revision_id")),
            _s(u.get("confirmation")),
            _STATUS_VI.get(u.get("status"), _s(u.get("status"))),
            _num(dim[0], 4, S_CM),
            _num(dim[1], 4, S_CM),
            _num(dim[2], 4, S_CM),
            _num(mass, 3, S_KG),
            _num(pl["x_mm"], 3, S_M) if pl else None,
            _num(pl["y_mm"], 3, S_M) if pl else None,
            _num(pl["z_mm"], 3, S_M) if pl else None,
            _int(pl["yaw_deg"]) if pl else None,
            _PACK_VI.get(pk.get("status"), _s(pk.get("status"))) if pk else None,
            _s(pk.get("layout")) if pk else None,
            _int(pk.get("pieces_placed")) if pk else None,
            _int(pk.get("pieces_source")) if pk else None,
            _int(dim[0]),
            _int(dim[1]),
            _int(dim[2]),
            _int(u.get("length_mm")),
            _int(u.get("width_mm")),
            _int(u.get("height_mm")),
            _int(mass),
            _int(pl["x_mm"]) if pl else None,
            _int(pl["y_mm"]) if pl else None,
            _int(pl["z_mm"]) if pl else None,
        ]
        if r.get("stacking") == "COLUMNS_V1":  # M3a: extra columns only for multi-layer reports
            row += [_int(pl["layer"]) if pl else None, _s(", ".join(pl.get("supported_by") or [])) if pl else None]
        rows.append(row)
    return rows


_UNITS_HEADER = [
    "ID", "Tên", "Loại", "Yêu cầu", "Nhóm", "Revision", "Xác nhận", "Trạng thái xếp",
    "Dài (cm)", "Rộng (cm)", "Cao (cm)", "Khối lượng (kg)", "X (m)", "Y (m)", "Z (m)",
    "Góc xoay (°)", "Packing", "Cách xếp", "Số ống xếp", "Số ống nguồn",
    "Dài (µm)", "Rộng (µm)", "Cao (µm)", "Dài (mm)", "Rộng (mm)", "Cao (mm)",
    "Khối lượng (g)", "X (mm)", "Y (mm)", "Z (mm)",
]  # fmt: skip
_UNITS_WIDTHS = [
    16, 34, 16, 12, 14, 24, 14, 14, 11, 11, 11, 16, 10, 10, 10, 13, 20, 12, 12, 14,
    14, 14, 14, 12, 12, 12, 16, 11, 11, 11,
]  # fmt: skip


def _unplaced_rows(r: dict) -> list:
    rows = []
    for u in r.get("unplaced") or []:
        mass = u.get("mass_g")
        rows.append(
            [
                _s(u.get("id")),
                _s(u.get("name")),
                _STATUS_VI.get(u.get("status"), _s(u.get("status"))),
                _REQ_VI.get(u.get("requirement"), _s(u.get("requirement"))),
                _num(mass, 3, S_KG),
                _int(mass),
                _s(u.get("reason")),
                _s(u.get("reason_code")),
            ]
        )
    return rows


def _issues_rows(r: dict) -> list:
    iss = r.get("issues") or {}
    rows = []
    items = iss.get("items") or []
    for it in items:
        rows.append(
            [
                _s(it.get("code")),
                ", ".join(str(x) for x in (it.get("unit_ids") or [])) or None,
                _s(it.get("message")),
            ]
        )
    total = iss.get("total_issues")
    if iss.get("issues_truncated"):
        note = (
            f"Danh sách bị cắt bớt: hiển thị {len(items)} trên tổng {total} vấn đề."
        )
    else:
        note = "Danh sách đầy đủ."
    note += (
        f" Trạng thái: {iss.get('status')}; kiểm cơ bản đạt: "
        f"{_yn(iss.get('basic_checks_passed'))}."
    )
    rows.append(["Tổng số vấn đề", _int(total), note])
    for u in iss.get("unchecked") or []:
        rows.append(["Chưa kiểm", None, _s(u)])
    rows.append(
        ["Chưa đủ điều kiện vận hành", _yn(not iss.get("operational_eligible")), None]
    )
    return rows


# --------------------------------------------------------------------------
# static parts
# --------------------------------------------------------------------------
_XML_DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'

_CONTENT_TYPES = (
    _XML_DECL
    + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
    + "".join(
        f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for i in range(1, 5)
    )
    + '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
    "</Types>"
)

_ROOT_RELS = (
    _XML_DECL
    + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
    "</Relationships>"
)

_WORKBOOK = (
    _XML_DECL
    + '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
    '<bookViews><workbookView xWindow="0" yWindow="0" windowWidth="28800" windowHeight="15000" activeTab="0"/></bookViews>'
    "<sheets>"
    + "".join(
        f'<sheet name="{_esc(n)}" sheetId="{i}" r:id="rId{i}"/>'
        for i, n in enumerate(SHEET_NAMES, start=1)
    )
    + "</sheets></workbook>"
)

_WORKBOOK_RELS = (
    _XML_DECL
    + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    + "".join(
        f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
        for i in range(1, 5)
    )
    + '<Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    "</Relationships>"
)

_STYLES = (
    _XML_DECL
    + '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<numFmts count="2">'
    '<numFmt numFmtId="164" formatCode="0.000"/>'
    '<numFmt numFmtId="165" formatCode="0.0###"/>'
    "</numFmts>"
    '<fonts count="2">'
    '<font><sz val="11"/><name val="Calibri"/><family val="2"/></font>'
    '<font><b/><sz val="11"/><name val="Calibri"/><family val="2"/></font>'
    "</fonts>"
    '<fills count="2"><fill><patternFill patternType="none"/></fill>'
    '<fill><patternFill patternType="gray125"/></fill></fills>'
    '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
    '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    '<cellXfs count="7">'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
    '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
    '<xf numFmtId="165" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
    '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
    '<xf numFmtId="1" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
    '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
    "</cellXfs>"
    '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
    "</styleSheet>"
)


# --------------------------------------------------------------------------
# zip
# --------------------------------------------------------------------------
_EPOCH = (1980, 1, 1, 0, 0, 0)


def _zip_datetime(saved_utc) -> tuple:
    if not isinstance(saved_utc, str) or not saved_utc:
        return _EPOCH
    try:
        txt = saved_utc.strip()
        if txt.endswith(("Z", "z")):
            txt = txt[:-1] + "+00:00"
        dt = datetime.fromisoformat(txt)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc)
    except (ValueError, OverflowError, OSError):
        return _EPOCH
    if dt.year < 1980:
        return _EPOCH
    if dt.year > 2107:
        return (2107, 12, 31, 23, 59, 58)
    return (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second - dt.second % 2)


def write_xlsx(report: dict) -> bytes:
    """Return the XLSX bytes for a scst.plan-report.v1 dict (pure, deterministic)."""
    import io

    overview = _sheet_xml(["Mục", "Giá trị", "Chính xác"], _overview_rows(report), [44, 60, 20])
    multi = report.get("stacking") == "COLUMNS_V1"
    units = _sheet_xml(_UNITS_HEADER + (["Tầng", "Bó đỡ"] if multi else []), _units_rows(report),
                       _UNITS_WIDTHS + ([8, 24] if multi else []))
    unplaced = _sheet_xml(
        ["ID", "Tên", "Trạng thái", "Yêu cầu", "Khối lượng (kg)", "Khối lượng (g)", "Lý do", "Mã lý do"],
        _unplaced_rows(report),
        [16, 34, 14, 12, 16, 16, 60, 22],
    )
    issues = _sheet_xml(
        ["Mã", "Bó liên quan", "Nội dung"], _issues_rows(report), [30, 40, 90]
    )

    members = [
        ("[Content_Types].xml", _CONTENT_TYPES),
        ("_rels/.rels", _ROOT_RELS),
        ("xl/workbook.xml", _WORKBOOK),
        ("xl/_rels/workbook.xml.rels", _WORKBOOK_RELS),
        ("xl/styles.xml", _STYLES),
        ("xl/worksheets/sheet1.xml", overview),
        ("xl/worksheets/sheet2.xml", units),
        ("xl/worksheets/sheet3.xml", unplaced),
        ("xl/worksheets/sheet4.xml", issues),
    ]
    stamp = _zip_datetime((report.get("header") or {}).get("saved_utc"))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for name, text in members:
            zi = zipfile.ZipInfo(name, stamp)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.create_system = 3
            zi.external_attr = 0o644 << 16
            zf.writestr(zi, text.encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    return buf.getvalue()
