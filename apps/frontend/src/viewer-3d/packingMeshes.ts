// SPEC D4: derived pipe packing meshes for the 3D viewer. Everything here is DERIVED geometry (not measured).
// Pure helpers (allocatePacking, bundleToWorld) plus one builder that turns packing data into three objects.
import * as T from "three";
import { packingFor, type PackingCore, type PackingIndex } from "../features/packing";
import type { Unit } from "../features/model";

export type CargoView = "ENVELOPE" | "SIMPLIFIED" | "DETAILED";
export const PIPE_BUDGET = 60000;
export const RING_BUDGET = 120000;
export const RADIAL_SEGMENTS = 12;
export const SELECTED_COLOR = 0x9ed7bb;
export const ISSUE_COLOR = 0xc76b5a;
export const PIPE_COLOR = 0x7f98a8;
export const WARN_COLOR = 0xe07a1f;

export type PackingInfo = {
  view: CargoView;
  detailedBundles: number; // bundles drawn as hollow/solid tubes
  simplifiedBundles: number; // bundles drawn as end-face rings
  envelopeBundles: number; // everything else drawn as a plain box (non-pipe units, budget overflow)
  envelopeOnlyBundles: number; // pipe bundles without usable packing (warning outline)
  pipeInstances: number;
  ringInstances: number;
  capped: boolean;
  buildMs: number;
  candidateBundles: number; // bundles that have usable derived packing
  totalBundles: number;
  budgetBoxBundles: number; // candidates that fell back to the translucent box because of the ring budget
};

/** How a bundle's box mesh is shown: solid (today), or translucent beside rings/tubes/fallback. */
export type BoxMode = "solid" | "simplified" | "detailed" | "box";

export const packingUsable = (core: PackingCore | null | undefined): core is PackingCore =>
  !!core && core.status === "DETAILED" && !!core.od_um && core.od_um > 0 && core.pipe_centres_um.length > 0;

/** Pipe unit whose packing is missing/ENVELOPE_ONLY while packing data is loaded: shown with a warning outline. */
export const isWarnUnit = (packing: PackingIndex | null, unit: Unit): boolean =>
  !!packing && !!unit.source_ref?.group_id && !packingUsable(packingFor(packing, unit));

// ---------------------------------------------------------------- budget allocation (pure)
export type AllocInput = { id: string; pipes: number; inFrustum: boolean; distance: number };
export type Allocation = {
  detailed: string[]; // tubes, in priority order
  simplified: string[]; // rings, in priority order
  box: string[]; // translucent box only (ring budget overflow)
  pipeInstances: number;
  ringInstances: number;
  capped: boolean;
};

/**
 * Allocation order: selected bundle first, then bundles inside the camera frustum by distance, then the rest by distance.
 * DETAILED: tubes until total pipes would exceed pipeBudget (only selected/in-frustum bundles compete when over budget);
 * the rest become rings until ringBudget (2 per pipe) would be exceeded; the rest of those stay as a translucent box.
 */
export function allocatePacking(
  view: CargoView,
  bundles: AllocInput[],
  selectedId: string,
  budgets: { pipes: number; rings: number } = { pipes: PIPE_BUDGET, rings: RING_BUDGET },
): Allocation {
  const out: Allocation = { detailed: [], simplified: [], box: [], pipeInstances: 0, ringInstances: 0, capped: false };
  if (view === "ENVELOPE") return out;
  const rank = (b: AllocInput) => (b.id === selectedId ? 0 : b.inFrustum ? 1 : 2);
  const sorted = bundles
    .filter((b) => b.pipes > 0)
    .sort((a, b) => rank(a) - rank(b) || a.distance - b.distance || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
  let rest = sorted;
  if (view === "DETAILED") {
    const total = sorted.reduce((n, b) => n + b.pipes, 0);
    if (total <= budgets.pipes) {
      out.detailed = sorted.map((b) => b.id);
      out.pipeInstances = total;
      rest = [];
    } else {
      out.capped = true;
      const left: AllocInput[] = [];
      let used = 0,
        closed = false;
      for (const b of sorted) {
        const eligible = b.id === selectedId || b.inFrustum;
        if (!closed && eligible && used + b.pipes <= budgets.pipes) {
          used += b.pipes;
          out.detailed.push(b.id);
        } else {
          if (!closed && eligible && b.id !== selectedId) closed = true; // would exceed: stop adding further bundles
          left.push(b);
        }
      }
      out.pipeInstances = used;
      rest = left;
    }
  }
  let rings = 0,
    closed = false;
  for (const b of rest) {
    const need = 2 * b.pipes;
    if (!closed && rings + need <= budgets.rings) {
      rings += need;
      out.simplified.push(b.id);
    } else {
      if (b.id !== selectedId) closed = true;
      out.capped = true;
      out.box.push(b.id);
    }
  }
  out.ringInstances = rings;
  return out;
}

// ---------------------------------------------------------------- bundle pose
/**
 * Offset (metres, relative to the box's min corner in world X/Z) of the point at `length` l along the bundle and
 * `across` w across its width, for yaw 0/90/180/270 (counter-clockwise in plan; footprint [sx, sz] is already swapped
 * for 90/270). The bundle length runs along world X for 0/180 and along world Z for 90/270.
 */
export function bundleToWorld(yawDeg: number, sx: number, sz: number, l: number, w: number): [number, number] {
  const q = (((Math.round(yawDeg / 90) % 4) + 4) % 4) as 0 | 1 | 2 | 3;
  if (q === 0) return [l, w];
  if (q === 1) return [sx - w, l];
  if (q === 2) return [sx - l, sz - w];
  return [w, sz - l];
}
export const lengthAlongX = (yawDeg: number) => (((Math.round(yawDeg / 90) % 2) + 2) % 2) === 0;

// ---------------------------------------------------------------- geometry
/** Hollow tube along Y, height 1 (y in [-0.5, 0.5]); front faces point out of the material. */
export function tubeGeometry(ro: number, ri: number, seg = RADIAL_SEGMENTS): T.BufferGeometry {
  const pos: number[] = [],
    nor: number[] = [],
    idx: number[] = [];
  const wall = (r: number, sign: 1 | -1) => {
    const base = pos.length / 3;
    for (let i = 0; i <= seg; i++) {
      const a = (i / seg) * Math.PI * 2,
        c = Math.cos(a),
        s = Math.sin(a);
      pos.push(r * c, -0.5, r * s, r * c, 0.5, r * s);
      nor.push(sign * c, 0, sign * s, sign * c, 0, sign * s);
    }
    for (let i = 0; i < seg; i++) {
      const v = base + 2 * i;
      if (sign === 1) idx.push(v, v + 1, v + 2, v + 1, v + 3, v + 2);
      else idx.push(v, v + 2, v + 1, v + 1, v + 2, v + 3);
    }
  };
  const cap = (y: number) => {
    const base = pos.length / 3,
      ny = y > 0 ? 1 : -1;
    for (let i = 0; i <= seg; i++) {
      const a = (i / seg) * Math.PI * 2,
        c = Math.cos(a),
        s = Math.sin(a);
      pos.push(ro * c, y, ro * s, ri * c, y, ri * s);
      nor.push(0, ny, 0, 0, ny, 0);
    }
    for (let i = 0; i < seg; i++) {
      const v = base + 2 * i; // v outer_i, v+1 inner_i, v+2 outer_i+1, v+3 inner_i+1
      if (ny > 0) idx.push(v, v + 1, v + 2, v + 1, v + 3, v + 2);
      else idx.push(v, v + 2, v + 1, v + 1, v + 2, v + 3);
    }
  };
  wall(ro, 1);
  wall(ri, -1);
  cap(0.5);
  cap(-0.5);
  const g = new T.BufferGeometry();
  g.setAttribute("position", new T.Float32BufferAttribute(pos, 3));
  g.setAttribute("normal", new T.Float32BufferAttribute(nor, 3));
  g.setIndex(idx);
  return g;
}

// ---------------------------------------------------------------- builder
export type PackBundle = {
  id: string;
  core: PackingCore | null; // usable packing only (else null)
  warn: boolean;
  min: T.Vector3; // world min corner of the (axis-aligned) box mesh
  size: T.Vector3; // world extents X, Y, Z of the box mesh
  yaw: number;
};
export type PackRange = { id: string; mesh: T.InstancedMesh; start: number; count: number; color: number };
export type PackBuild = {
  objects: T.Object3D[];
  meshes: T.InstancedMesh[];
  ranges: PackRange[];
  probes: { id: string; p: T.Vector3 }[];
  modes: Map<string, BoxMode>;
  info: PackingInfo;
};

const um = (n: number) => n / 1e6;
const colorOf = (id: string, selected: string, issueIds: Set<string>) =>
  id === selected ? SELECTED_COLOR : issueIds.has(id) ? ISSUE_COLOR : PIPE_COLOR;

type KeyData = { od: number; wall: number; tubes: number; rings: number };

export function buildPacking(args: {
  view: CargoView;
  bundles: PackBundle[];
  selected: string;
  issueIds: Set<string>;
  camera: T.Camera;
}): PackBuild {
  const t0 = performance.now();
  const { view, bundles, selected, issueIds, camera } = args;
  const byId = new Map(bundles.map((b) => [b.id, b]));
  const modes = new Map<string, BoxMode>();
  const objects: T.Object3D[] = [],
    meshes: T.InstancedMesh[] = [],
    ranges: PackRange[] = [],
    probes: { id: string; p: T.Vector3 }[] = [];
  const warnBundles = bundles.filter((b) => b.warn);
  const candidates = bundles.filter((b) => b.core);
  const finish = (alloc: Allocation): PackBuild => ({
    objects,
    meshes,
    ranges,
    probes,
    modes,
    info: {
      view,
      detailedBundles: alloc.detailed.length,
      simplifiedBundles: alloc.simplified.length,
      envelopeBundles: bundles.length - alloc.detailed.length - alloc.simplified.length - warnBundles.length,
      envelopeOnlyBundles: view === "ENVELOPE" ? 0 : warnBundles.length,
      pipeInstances: alloc.pipeInstances,
      ringInstances: alloc.ringInstances,
      capped: alloc.capped,
      buildMs: Math.round((performance.now() - t0) * 100) / 100,
      candidateBundles: view === "ENVELOPE" ? 0 : candidates.length,
      totalBundles: bundles.length,
      budgetBoxBundles: alloc.box.length,
    },
  });
  if (view === "ENVELOPE") return finish(allocatePacking(view, [], selected));

  // Camera frustum / distance, evaluated once at build time (never on camera move).
  camera.updateMatrixWorld();
  const frustum = new T.Frustum().setFromProjectionMatrix(
    new T.Matrix4().multiplyMatrices(camera.projectionMatrix, new T.Matrix4().copy(camera.matrixWorld).invert()),
  );
  const box = new T.Box3(),
    centre = new T.Vector3();
  const inputs: AllocInput[] = candidates.map((b) => {
    box.set(b.min, new T.Vector3().addVectors(b.min, b.size));
    box.getCenter(centre);
    return {
      id: b.id,
      pipes: b.core!.pipe_centres_um.length,
      inFrustum: frustum.intersectsBox(box),
      distance: camera.position.distanceTo(centre),
    };
  });
  const alloc = allocatePacking(view, inputs, selected);

  // Group instances by geometry key (od, wall).
  const keys = new Map<string, KeyData>();
  const keyOf = (core: PackingCore) => {
    const od = core.od_um!,
      wall = core.wall_thickness_um != null && core.wall_thickness_um > 0 && 2 * core.wall_thickness_um < od ? core.wall_thickness_um : 0;
    const k = `${od}|${wall}`;
    let d = keys.get(k);
    if (!d) keys.set(k, (d = { od, wall, tubes: 0, rings: 0 }));
    return { k, d };
  };
  for (const id of alloc.detailed) {
    const { d } = keyOf(byId.get(id)!.core!);
    d.tubes += byId.get(id)!.core!.pipe_centres_um.length;
  }
  for (const id of alloc.simplified) {
    const { d } = keyOf(byId.get(id)!.core!);
    d.rings += 2 * byId.get(id)!.core!.pipe_centres_um.length;
  }

  const tubeMat = new T.MeshStandardMaterial({ color: 0xffffff, roughness: 0.45, metalness: 0.45 });
  const ringMat = new T.MeshBasicMaterial({
    color: 0xffffff,
    side: T.DoubleSide,
    polygonOffset: true,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -2,
  });
  const tubeMeshes = new Map<string, { mesh: T.InstancedMesh; next: number }>(),
    ringMeshes = new Map<string, { mesh: T.InstancedMesh; next: number }>();
  for (const [k, d] of keys) {
    const ro = um(d.od) / 2,
      ri = d.wall ? um(d.od - 2 * d.wall) / 2 : 0;
    if (d.tubes) {
      const geometry = d.wall ? tubeGeometry(ro, ri) : new T.CylinderGeometry(ro, ro, 1, RADIAL_SEGMENTS, 1, false);
      const mesh = new T.InstancedMesh(geometry, tubeMat, d.tubes);
      mesh.userData = { owners: new Array<string>(d.tubes), kind: "tubes" };
      tubeMeshes.set(k, { mesh, next: 0 });
    }
    if (d.rings) {
      const geometry = new T.RingGeometry(ri > 0 ? ri : ro * 0.78, ro, 16, 1);
      const mesh = new T.InstancedMesh(geometry, ringMat, d.rings);
      mesh.userData = { owners: new Array<string>(d.rings), kind: "rings" };
      ringMeshes.set(k, { mesh, next: 0 });
    }
  }

  const m = new T.Matrix4(),
    pos = new T.Vector3(),
    scale = new T.Vector3(),
    colour = new T.Color();
  const qTubeX = new T.Quaternion().setFromAxisAngle(new T.Vector3(0, 0, 1), -Math.PI / 2),
    qTubeZ = new T.Quaternion().setFromAxisAngle(new T.Vector3(1, 0, 0), Math.PI / 2),
    qRingX = new T.Quaternion().setFromAxisAngle(new T.Vector3(0, 1, 0), Math.PI / 2),
    qRingZ = new T.Quaternion();
  const EPS = 0.002; // rings sit just outside the end faces

  const place = (b: PackBundle, core: PackingCore, slot: { mesh: T.InstancedMesh; next: number }, rings: boolean) => {
    const alongX = lengthAlongX(b.yaw),
      length = um(core.length_um),
      color = colorOf(b.id, selected, issueIds),
      start = slot.next;
    colour.set(color);
    for (const [y, z] of core.pipe_centres_um) {
      const wy = b.min.y + um(z);
      if (!rings) {
        const [ex, ez] = bundleToWorld(b.yaw, b.size.x, b.size.z, length / 2, um(y));
        pos.set(b.min.x + ex, wy, b.min.z + ez);
        scale.set(1, length, 1);
        m.compose(pos, alongX ? qTubeX : qTubeZ, scale);
        slot.mesh.setMatrixAt(slot.next, m);
        slot.mesh.setColorAt(slot.next, colour);
        slot.mesh.userData.owners[slot.next++] = b.id;
      } else {
        scale.set(1, 1, 1);
        for (const l of [-EPS, length + EPS]) {
          const [rx, rz] = bundleToWorld(b.yaw, b.size.x, b.size.z, l, um(y));
          pos.set(b.min.x + rx, wy, b.min.z + rz);
          m.compose(pos, alongX ? qRingX : qRingZ, scale);
          slot.mesh.setMatrixAt(slot.next, m);
          slot.mesh.setColorAt(slot.next, colour);
          slot.mesh.userData.owners[slot.next++] = b.id;
        }
      }
    }
    ranges.push({ id: b.id, mesh: slot.mesh, start, count: slot.next - start, color });
  };

  for (const id of alloc.detailed) {
    const b = byId.get(id)!,
      core = b.core!,
      { k } = keyOf(core),
      slot = tubeMeshes.get(k)!,
      first = slot.next;
    place(b, core, slot, false);
    modes.set(id, "detailed");
    if (probes.length < 20 && slot.next > first) {
      const [y, z] = core.pipe_centres_um[0],
        [ex, ez] = bundleToWorld(b.yaw, b.size.x, b.size.z, um(core.length_um) / 2, um(y));
      probes.push({ id, p: new T.Vector3(b.min.x + ex, b.min.y + um(z), b.min.z + ez) });
    }
  }
  for (const id of alloc.simplified) {
    const b = byId.get(id)!,
      core = b.core!;
    place(b, core, ringMeshes.get(keyOf(core).k)!, true);
    modes.set(id, "simplified");
  }
  for (const id of alloc.box) modes.set(id, "box");

  for (const { mesh } of [...tubeMeshes.values(), ...ringMeshes.values()]) {
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    mesh.frustumCulled = false; // instance bounds are not tracked; cheap enough for a handful of meshes
    meshes.push(mesh);
    objects.push(mesh);
  }

  // One merged warning outline for every pipe bundle that only has its envelope.
  if (warnBundles.length) {
    const p: number[] = [],
      g = 0.01;
    for (const b of warnBundles) {
      const x0 = b.min.x - g,
        y0 = b.min.y - g,
        z0 = b.min.z - g,
        x1 = b.min.x + b.size.x + g,
        y1 = b.min.y + b.size.y + g,
        z1 = b.min.z + b.size.z + g;
      const c = [
        [x0, y0, z0],
        [x1, y0, z0],
        [x1, y0, z1],
        [x0, y0, z1],
        [x0, y1, z0],
        [x1, y1, z0],
        [x1, y1, z1],
        [x0, y1, z1],
      ];
      for (const [a, d] of [
        [0, 1], [1, 2], [2, 3], [3, 0],
        [4, 5], [5, 6], [6, 7], [7, 4],
        [0, 4], [1, 5], [2, 6], [3, 7],
      ])
        p.push(...c[a], ...c[d]);
    }
    const outline = new T.LineSegments(
      new T.BufferGeometry().setAttribute("position", new T.Float32BufferAttribute(p, 3)),
      new T.LineBasicMaterial({ color: WARN_COLOR }),
    );
    outline.frustumCulled = false;
    outline.userData.warnOutline = true;
    objects.push(outline);
  }
  return finish(alloc);
}
