"""Builds small valid glTF 2.0 binaries (real BIN chunk) and corrupt variants for offline tests."""
import json
import struct

_CUBE_INDICES = [0, 1, 3, 0, 3, 2, 4, 6, 7, 4, 7, 5, 0, 4, 5, 0, 5, 1,
                 2, 3, 7, 2, 7, 6, 0, 2, 6, 0, 6, 4, 1, 5, 7, 1, 7, 3]


def _f32(v):
    return struct.unpack("<f", struct.pack("<f", v))[0]


def pack_glb(json_bytes: bytes, bin_bytes: bytes = b"", *, magic=b"glTF", version=2, total_length=None,
             json_type=0x4E4F534A, json_length=None) -> bytes:
    pad = (-len(json_bytes)) % 4
    json_chunk = json_bytes + b" " * pad
    body = struct.pack("<II", len(json_chunk) if json_length is None else json_length, json_type) + json_chunk
    if bin_bytes:
        bin_chunk = bin_bytes + b"\0" * ((-len(bin_bytes)) % 4)
        body += struct.pack("<II", len(bin_chunk), 0x004E4942) + bin_chunk
    total = 12 + len(body) if total_length is None else total_length
    return struct.pack("<4sII", magic, version, total) + body


def make_glb(boxes, *, node_translation=None, node_rotation=None, node_scale=None, node_matrix=None,
             include_minmax=True, component_type=5126, asset_version="2.0", **pack_kwargs) -> bytes:
    """boxes: [((minx,miny,minz),(maxx,maxy,maxz)), ...] -> one mesh, one primitive per box, one node."""
    blob, views, accessors, prims = b"", [], [], []
    for lo, hi in boxes:
        pts = [[_f32(hi[k] if (i >> (2 - k)) & 1 else lo[k]) for k in range(3)] for i in range(8)]
        pos = b"".join(struct.pack("<3f", *p) for p in pts)
        idx = struct.pack("<36H", *_CUBE_INDICES)
        for data, target in ((pos, 34962), (idx, 34963)):
            views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data), "target": target})
            blob += data + b"\0" * ((-len(data)) % 4)
        position = {"bufferView": len(views) - 2, "componentType": component_type, "count": 8, "type": "VEC3"}
        if include_minmax:
            position["min"] = [min(p[k] for p in pts) for k in range(3)]
            position["max"] = [max(p[k] for p in pts) for k in range(3)]
        accessors += [position, {"bufferView": len(views) - 1, "componentType": 5123, "count": 36, "type": "SCALAR"}]
        prims.append({"attributes": {"POSITION": len(accessors) - 2}, "indices": len(accessors) - 1})
    node = {"mesh": 0}
    for key, value in (("translation", node_translation), ("rotation", node_rotation),
                       ("scale", node_scale), ("matrix", node_matrix)):
        if value is not None:
            node[key] = list(value)
    gltf = {"asset": {"version": asset_version}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [node],
            "meshes": [{"primitives": prims}], "accessors": accessors, "bufferViews": views,
            "buffers": [{"byteLength": len(blob)}]}
    return pack_glb(json.dumps(gltf).encode(), blob, **pack_kwargs)


# corrupt variants -----------------------------------------------------------------------------

def bad_magic(glb: bytes) -> bytes:
    return b"XXXX" + glb[4:]


def bad_version(glb: bytes, version: int = 1) -> bytes:
    return glb[:4] + struct.pack("<I", version) + glb[8:]


def bad_total_length(glb: bytes) -> bytes:
    return glb[:8] + struct.pack("<I", len(glb) + 4) + glb[12:]


def non_json_first_chunk(glb: bytes) -> bytes:
    return glb[:16] + struct.pack("<I", 0x004E4942) + glb[20:]


def bad_chunk_length(glb: bytes) -> bytes:
    return glb[:12] + struct.pack("<I", len(glb)) + glb[16:]


def with_json_bytes(raw: bytes) -> bytes:
    return pack_glb(raw)
