"""Stdlib-only GLB reader: header/JSON chunk parsing and POSITION bounds. No file or network access."""
import json
import math
import struct

MAX_GLB_BYTES = 20 * 1024 * 1024
_CORNERS = [(x, y, z) for x in (0, 1) for y in (0, 1) for z in (0, 1)]
_IDENTITY = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]


class GlbError(ValueError):
    """Message is Vietnamese and safe to show to the user."""


def parse_glb(data: bytes) -> dict:
    if len(data) > MAX_GLB_BYTES:
        raise GlbError("Tệp GLB vượt quá giới hạn 20 MiB.")
    if len(data) < 12:
        raise GlbError("Tệp GLB quá ngắn, không có đủ phần đầu 12 byte.")
    magic, version, total = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF":
        raise GlbError("Tệp không phải GLB: sai chữ ký đầu tệp (cần 'glTF').")
    if version != 2:
        raise GlbError(f"Chỉ hỗ trợ glTF phiên bản 2, tệp này là phiên bản {version}.")
    if total != len(data):
        raise GlbError("Độ dài khai báo trong phần đầu GLB không khớp kích thước tệp.")
    if len(data) < 20:
        raise GlbError("Tệp GLB thiếu chunk JSON đầu tiên.")
    length, ctype = struct.unpack_from("<II", data, 12)
    if ctype != 0x4E4F534A:
        raise GlbError("Chunk đầu tiên của GLB phải là JSON.")
    if length > len(data) - 20:
        raise GlbError("Độ dài chunk JSON vượt quá kích thước tệp GLB.")
    try:
        gltf = json.loads(data[20:20 + length].decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise GlbError("Chunk JSON của GLB không phải UTF-8 hoặc JSON hợp lệ.") from None
    if not isinstance(gltf, dict):
        raise GlbError("Chunk JSON của GLB phải là một đối tượng JSON.")
    asset = gltf.get("asset")
    if not isinstance(asset, dict) or asset.get("version") != "2.0":
        raise GlbError("Trường asset.version của glTF phải là \"2.0\".")
    return gltf


def _mul(a: list, b: list) -> list:
    """Column-major 4x4 product a*b."""
    return [sum(a[k * 4 + r] * b[c * 4 + k] for k in range(4)) for c in range(4) for r in range(4)]


def _local_matrix(node: dict) -> list:
    matrix = node.get("matrix")
    if matrix is not None:
        if not _numbers(matrix, 16):
            raise GlbError("Node glTF có 'matrix' không hợp lệ (cần 16 số hữu hạn).")
        return [float(v) for v in matrix]
    t, q, s = node.get("translation", [0, 0, 0]), node.get("rotation", [0, 0, 0, 1]), node.get("scale", [1, 1, 1])
    if not (_numbers(t, 3) and _numbers(q, 4) and _numbers(s, 3)):
        raise GlbError("Node glTF có translation/rotation/scale không hợp lệ.")
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w)
    if n == 0:
        raise GlbError("Node glTF có quaternion xoay bằng 0.")
    x, y, z, w = x / n, y / n, z / n, w / n
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    out = [0.0] * 16
    for c in range(3):
        for row in range(3):
            out[c * 4 + row] = r[row][c] * s[c]
    out[12], out[13], out[14], out[15] = float(t[0]), float(t[1]), float(t[2]), 1.0
    return out


def _numbers(v, n: int) -> bool:
    return (isinstance(v, list) and len(v) == n
            and all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in v))


def _apply(m: list, p) -> tuple:
    return tuple(m[0 + i] * p[0] + m[4 + i] * p[1] + m[8 + i] * p[2] + m[12 + i] for i in range(3))


def _position_box(gltf: dict, mesh_index) -> list:
    meshes = gltf.get("meshes") or []
    if not isinstance(mesh_index, int) or isinstance(mesh_index, bool) or not 0 <= mesh_index < len(meshes):
        raise GlbError("Node glTF tham chiếu mesh không tồn tại.")
    boxes = []
    for prim in meshes[mesh_index].get("primitives") or []:
        index = (prim.get("attributes") or {}).get("POSITION")
        accessors = gltf.get("accessors") or []
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(accessors):
            raise GlbError("Primitive không có accessor POSITION hợp lệ.")
        acc = accessors[index]
        if acc.get("componentType") != 5126 or acc.get("type") != "VEC3":
            raise GlbError("Accessor POSITION phải là VEC3 kiểu float32 (componentType 5126).")
        if not (_numbers(acc.get("min"), 3) and _numbers(acc.get("max"), 3)):
            raise GlbError("Accessor POSITION thiếu min/max hợp lệ nên không dựng được hộp bao.")
        boxes.append((acc["min"], acc["max"]))
    return boxes


def glb_bounds(gltf: dict) -> tuple[list, list]:
    """Union box (metres, GLB frame) of every mesh POSITION min/max reachable from the default scene."""
    nodes = gltf.get("nodes") or []
    scenes = gltf.get("scenes") or []
    if scenes:
        si = gltf.get("scene", 0)
        if not isinstance(si, int) or isinstance(si, bool) or not 0 <= si < len(scenes):
            raise GlbError("Scene mặc định của glTF không tồn tại.")
        roots = scenes[si].get("nodes") or []
    else:
        children = {c for n in nodes for c in (n.get("children") or []) if isinstance(c, int)}
        roots = [i for i in range(len(nodes)) if i not in children]
    lo, hi = [math.inf] * 3, [-math.inf] * 3

    def visit(index, parent, path):
        nonlocal lo, hi
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(nodes):
            raise GlbError("Scene glTF tham chiếu node không tồn tại.")
        if index in path:
            raise GlbError("Cây node glTF có vòng lặp.")
        node = nodes[index]
        world = _mul(parent, _local_matrix(node))
        if "mesh" in node:
            for bmin, bmax in _position_box(gltf, node["mesh"]):
                for c in _CORNERS:
                    p = _apply(world, [bmax[i] if c[i] else bmin[i] for i in range(3)])
                    lo = [min(a, b) for a, b in zip(lo, p)]
                    hi = [max(a, b) for a, b in zip(hi, p)]
        for child in node.get("children") or []:
            visit(child, world, path | {index})

    try:
        for root in roots:
            visit(root, _IDENTITY, frozenset())
    except RecursionError:
        raise GlbError("Cây node glTF quá sâu.") from None
    if lo[0] == math.inf:
        raise GlbError("GLB không có mesh nào với accessor POSITION trong scene mặc định.")
    return lo, hi
