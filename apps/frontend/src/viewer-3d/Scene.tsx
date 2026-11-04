import { useEffect, useRef } from "react";
import * as T from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { profileBody, type ProfileDetail } from "../api/client";
import { dimensions, footprint, type Plan } from "../features/model";
import type { PackingIndex } from "../features/packing";
import { packingFor } from "../features/packing";
import {
  buildPacking,
  isWarnUnit,
  ISSUE_COLOR,
  PIPE_BUDGET,
  PIPE_COLOR,
  SELECTED_COLOR,
  packingUsable,
  type BoxMode,
  type CargoView,
  type PackBundle,
  type PackRange,
  type PackingInfo,
} from "./packingMeshes";
type Props = {
  plan: Plan;
  profile: ProfileDetail | null;
  selected: string;
  onSelect: (id: string) => void;
  issueIds: Set<string>;
  onFailure: () => void;
  cameraCommand: { kind: string; serial: number };
  shipVisible: boolean;
  ghost: boolean;
  onAssetStatus: (status: string) => void;
  cargoView?: CargoView;
  packing?: PackingIndex | null;
  onPackingInfo?: (info: PackingInfo) => void;
  captureSerial?: number;
  onCapture?: (dataUrl: string) => void;
};
type Item = { mesh: T.Mesh; signature: string };
type State = {
  scene: T.Scene;
  renderer: T.WebGLRenderer;
  camera: T.PerspectiveCamera;
  controls: OrbitControls;
  hold: T.Group;
  cargo: T.Group;
  marker: T.Group;
  pack: T.Group;
  packMeshes: T.InstancedMesh[];
  packRanges: PackRange[];
  packProbes: { id: string; p: T.Vector3 }[];
  packModes: Map<string, BoxMode>;
  packInfo: PackingInfo | null;
  packDeps: {
    view: CargoView;
    packing: PackingIndex | null;
    units: Plan["units"];
    placements: Plan["placements"];
    hold: string;
    selected: string;
  } | null;
  restyle: () => void;
  tint: () => void;
  disposePack: () => void;
  ship: T.Object3D | null;
  items: Map<string, Item>;
  originals: Map<T.Mesh, T.Material | T.Material[]>;
  clones: Set<T.Material>;
  assetKey: string;
  contextKey: string;
  generation: number;
  loads: number;
  assetIdentity: number;
  renders: number;
  interaction: number;
  render: () => void;
  fit: (kind: string) => void;
  ghost: (on: boolean) => void;
  dispose: (o: T.Object3D) => void;
};
const diagnostic = () =>
  new URLSearchParams(window.location.search).get("viewerDiagnostics") === "1";
export default function Scene(props: Props) {
  const host = useRef<HTMLDivElement>(null),
    state = useRef<State | null>(null),
    latest = useRef(props);
  latest.current = props;
  useEffect(() => {
    const el = host.current!;
    let renderer: T.WebGLRenderer;
    try {
      renderer = new T.WebGLRenderer({ antialias: true, alpha: true });
    } catch {
      latest.current.onFailure();
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0xeaf0ed, 1);
    const canvas = renderer.domElement;
    el.appendChild(canvas);
    canvas.setAttribute(
      "aria-label",
      "Hầm hàng 3D, kéo để xoay và cuộn để phóng to",
    );
    canvas.dataset.testid = "three-canvas";
    const scene = new T.Scene(),
      camera = new T.PerspectiveCamera(38, 1, 0.05, 3000),
      controls = new OrbitControls(camera, canvas);
    controls.enableDamping = false;
    controls.minDistance = 0.05;
    controls.maxDistance = 10000;
    controls.maxPolarAngle = Math.PI / 2;
    scene.add(new T.HemisphereLight(0xffffff, 0x5b736b, 2.8));
    const sun = new T.DirectionalLight(0xffffff, 3);
    sun.position.set(-10, 20, 10);
    scene.add(sun);
    const hold = new T.Group(),
      cargo = new T.Group(),
      marker = new T.Group(),
      pack = new T.Group();
    scene.add(hold, cargo, marker, pack);
    const dispose = (root: T.Object3D) => {
      const geometries = new Set<T.BufferGeometry>(),
        materials = new Set<T.Material>(),
        textures = new Set<T.Texture>();
      root.traverse((o) => {
        if (o instanceof T.Mesh || o instanceof T.LineSegments) {
          geometries.add(o.geometry);
          (Array.isArray(o.material) ? o.material : [o.material]).forEach(
            (m: T.Material) => materials.add(m),
          );
        }
      });
      materials.forEach((m) => {
        Object.values(m).forEach((v) => {
          if (v instanceof T.Texture) textures.add(v);
        });
        m.dispose();
      });
      textures.forEach((t) => t.dispose());
      geometries.forEach((g) => g.dispose());
    };
    const s: State = {
      scene,
      renderer,
      camera,
      controls,
      hold,
      cargo,
      marker,
      pack,
      packMeshes: [],
      packRanges: [],
      packProbes: [],
      packModes: new Map(),
      packInfo: null,
      packDeps: null,
      restyle: () => {},
      tint: () => {},
      disposePack: () => {},
      ship: null,
      items: new Map(),
      originals: new Map(),
      clones: new Set(),
      assetKey: "",
      contextKey: "",
      generation: 0,
      loads: 0,
      assetIdentity: 0,
      renders: 0,
      interaction: 0,
      render: () => {},
      fit: () => {},
      ghost: () => {},
      dispose,
    };
    state.current = s;
    s.render = () => {
      renderer.render(scene, camera);
      s.renders++;
      if (!diagnostic()) return;
      canvas.dataset.meshes = JSON.stringify(
        Array.from(s.items, ([id, { mesh }]) => {
          mesh.updateMatrixWorld(true);
          const box = new T.Box3().setFromObject(mesh, true),
            p = (mesh.geometry as T.BoxGeometry).parameters;
          return {
            id,
            uuid: mesh.uuid,
            position: mesh.position.toArray(),
            dimensions: [p.width, p.height, p.depth],
            worldMatrix: mesh.matrixWorld.toArray(),
            boxMin: box.min.toArray(),
            boxMax: box.max.toArray(),
          };
        }),
      );
      canvas.dataset.projectedMeshes = JSON.stringify(
        Array.from(s.items, ([id, { mesh }]) => {
          const p = mesh.getWorldPosition(new T.Vector3()).project(camera);
          return {
            id,
            x: ((p.x + 1) * canvas.clientWidth) / 2,
            y: ((1 - p.y) * canvas.clientHeight) / 2,
          };
        }),
      );
      canvas.dataset.camera = JSON.stringify(camera.position.toArray());
      canvas.dataset.cameraState = JSON.stringify({
        position: camera.position.toArray(),
        target: controls.target.toArray(),
        near: camera.near,
        far: camera.far,
        aspect: camera.aspect,
        fov: camera.fov,
        projection: camera.projectionMatrix.toArray(),
        worldInverse: camera.matrixWorldInverse.toArray(),
      });
      canvas.dataset.viewerStats = JSON.stringify({
        loads: s.loads,
        renders: s.renders,
        assetIdentity: s.assetIdentity,
        geometries: renderer.info.memory.geometries,
        textures: renderer.info.memory.textures,
        calls: renderer.info.render.calls,
        objects: s.items.size,
        sceneUuid: scene.uuid,
      });
      if (s.packInfo) {
        canvas.dataset.packingView = JSON.stringify({
          ...s.packInfo,
          budget: PIPE_BUDGET,
          sceneUuid: scene.uuid,
          packUuid: pack.uuid,
        });
        canvas.dataset.packingProjected = JSON.stringify(
          s.packProbes.map(({ id, p }) => {
            const v = p.clone().project(camera);
            return {
              id,
              x: ((v.x + 1) * canvas.clientWidth) / 2,
              y: ((1 - v.y) * canvas.clientHeight) / 2,
            };
          }),
        );
      }
      const materialData: {
        name: string;
        ghost: boolean;
        opacity: number;
        transparent: boolean;
        depthWrite: boolean;
      }[] = [];
      s.ship?.traverse((o) => {
        if (o instanceof T.Mesh) {
          const m = Array.isArray(o.material) ? o.material[0] : o.material;
          materialData.push({
            name: o.name,
            ghost: s.originals.has(o) && o.material !== s.originals.get(o),
            opacity: m.opacity,
            transparent: m.transparent,
            depthWrite: m.depthWrite,
          });
        }
      });
      canvas.dataset.materials = JSON.stringify(materialData);
    };
    s.disposePack = () => {
      s.packMeshes.forEach((m) => m.dispose());
      pack.children.forEach((c) => dispose(c));
      pack.clear();
      s.packMeshes = [];
      s.packRanges = [];
      s.packProbes = [];
    };
    // Box meshes stay in s.items for every view; only their material/bands change (and never their uuid).
    s.restyle = () => {
      const sel = latest.current.selected;
      for (const [id, { mesh }] of s.items) {
        const mode = s.packModes.get(id) ?? "solid",
          solid = mode === "solid",
          base = mode === "detailed" ? 0.12 : 0.3,
          m = mesh.material as T.MeshStandardMaterial,
          transparent = !solid;
        if (m.transparent !== transparent) m.needsUpdate = true;
        m.transparent = transparent;
        m.opacity = solid ? 1 : id === sel ? Math.max(base, 0.45) : base;
        m.depthWrite = solid;
        for (const c of mesh.children) if (c.userData.band) c.visible = solid;
      }
    };
    s.tint = () => {
      const { selected, issueIds } = latest.current,
        dirty = new Set<T.InstancedMesh>(),
        c = new T.Color();
      for (const r of s.packRanges) {
        const color =
          r.id === selected ? SELECTED_COLOR : issueIds.has(r.id) ? ISSUE_COLOR : PIPE_COLOR;
        if (color === r.color || !r.mesh.instanceColor) continue;
        r.color = color;
        c.set(color);
        for (let i = r.start; i < r.start + r.count; i++) r.mesh.setColorAt(i, c);
        dirty.add(r.mesh);
      }
      dirty.forEach((m) => {
        if (m.instanceColor) m.instanceColor.needsUpdate = true;
      });
    };
    s.ghost = (on) => {
      for (const [mesh, orig] of s.originals) {
        if (!on) {
          mesh.material = orig;
          continue;
        }
        let clone = mesh.userData.ghostMaterial as
          | T.Material
          | T.Material[]
          | undefined;
        if (!clone) {
          const make = (m: T.Material) => {
            const c = m.clone();
            c.transparent = true;
            c.opacity = 0.32;
            c.depthWrite = false;
            s.clones.add(c);
            return c;
          };
          clone = Array.isArray(orig) ? orig.map(make) : make(orig);
          mesh.userData.ghostMaterial = clone;
        }
        mesh.material = clone;
      }
    };
    s.fit = (kind) => {
      let box = new T.Box3();
      if (kind === "focus") {
        const item = s.items.get(latest.current.selected);
        if (!item) return;
        const p = (item.mesh.geometry as T.BoxGeometry).parameters,
          half = new T.Vector3(p.width, p.height, p.depth).multiplyScalar(0.5);
        box.set(
          item.mesh.position.clone().sub(half),
          item.mesh.position.clone().add(half),
        );
      } else {
        box.setFromObject(hold);
        box.union(new T.Box3().setFromObject(cargo));
        if (s.ship && s.ship.visible)
          box.union(new T.Box3().setFromObject(s.ship));
      }
      if (box.isEmpty()) return;
      const center = box.getCenter(new T.Vector3()),
        size = box.getSize(new T.Vector3()),
        half = size.clone().multiplyScalar(0.5);
      const direction = (
        kind === "top"
          ? new T.Vector3(0, 1, 0.0001)
          : kind === "side"
            ? new T.Vector3(0, 0, 1)
            : new T.Vector3(0.83, 0.95, 1.05)
      ).normalize();
      const horizontal = new T.Vector3()
        .crossVectors(new T.Vector3(0, 1, 0), direction)
        .normalize();
      if (horizontal.lengthSq() < 0.1) horizontal.set(1, 0, 0);
      const vertical = new T.Vector3()
        .crossVectors(direction, horizontal)
        .normalize();
      const project = (v: T.Vector3) =>
        Math.abs(v.x) * half.x +
        Math.abs(v.y) * half.y +
        Math.abs(v.z) * half.z;
      const tv = Math.tan(T.MathUtils.degToRad(camera.fov / 2)),
        th = tv * Math.max(camera.aspect, 0.01),
        distance =
          (Math.max(project(vertical) / tv, project(horizontal) / th) +
            project(direction)) *
            1.18 +
          0.1;
      camera.position.copy(center).addScaledVector(direction, distance);
      camera.near = Math.max(0.01, distance / 10000);
      camera.far = Math.max(100, distance + size.length() * 4);
      camera.updateProjectionMatrix();
      controls.target.copy(center);
      controls.maxDistance = Math.max(100, distance * 8);
      controls.update();
      s.render();
    };
    const resize = () => {
      const w = el.clientWidth,
        h = el.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      s.render();
    };
    const observer = new ResizeObserver(resize);
    observer.observe(el);
    controls.addEventListener("change", s.render);
    let start = { x: 0, y: 0 };
    const down = (ev: PointerEvent) => {
      s.interaction++;
      start = { x: ev.clientX, y: ev.clientY };
    };
    const wheel = () => {
      s.interaction++;
    };
    const up = (ev: PointerEvent) => {
      if (Math.hypot(ev.clientX - start.x, ev.clientY - start.y) > 5) return;
      const r = canvas.getBoundingClientRect(),
        ray = new T.Raycaster();
      ray.setFromCamera(
        new T.Vector2(
          ((ev.clientX - r.left) / r.width) * 2 - 1,
          (-(ev.clientY - r.top) / r.height) * 2 + 1,
        ),
        camera,
      );
      const hit = ray.intersectObjects(
        [...Array.from(s.items.values(), (v) => v.mesh), ...s.packMeshes],
        false,
      )[0];
      if (hit) {
        // Pipe/ring instances map back to their bundle; boxes carry the bundle id directly.
        const id =
          hit.instanceId !== undefined
            ? (hit.object.userData.owners as string[])[hit.instanceId]
            : hit.object.userData.id;
        if (id) latest.current.onSelect(id);
      }
    };
    const lost = (ev: Event) => {
      ev.preventDefault();
      latest.current.onFailure();
    };
    canvas.addEventListener("wheel", wheel);
    canvas.addEventListener("pointerdown", down);
    canvas.addEventListener("pointerup", up);
    canvas.addEventListener("webglcontextlost", lost);
    resize();
    return () => {
      s.generation++;
      observer.disconnect();
      controls.removeEventListener("change", s.render);
      controls.dispose();
      canvas.removeEventListener("wheel", wheel);
      canvas.removeEventListener("pointerdown", down);
      canvas.removeEventListener("pointerup", up);
      canvas.removeEventListener("webglcontextlost", lost);
      if (s.ship) {
        s.ghost(false);
        dispose(s.ship);
      }
      s.clones.forEach((m) => m.dispose());
      dispose(hold);
      dispose(cargo);
      dispose(marker);
      s.disposePack();
      renderer.dispose();
      canvas.remove();
      state.current = null;
    };
  }, []);
  useEffect(() => {
    const s = state.current;
    if (!s) return;
    const { plan } = props,
      L = plan.hold.length_mm / 1000,
      W = plan.hold.width_mm / 1000,
      H = plan.hold.height_mm / 1000;
    const context = JSON.stringify([plan.source, L, W, H]),
      changedContext = context !== s.contextKey;
    if (changedContext) {
      s.contextKey = context;
      s.dispose(s.hold);
      s.hold.clear();
      const slab = new T.Mesh(
        new T.BoxGeometry(L, 0.13, W),
        new T.MeshStandardMaterial({ color: 0xd2ddd4, roughness: 0.9 }),
      );
      slab.position.y = -0.075;
      s.hold.add(slab);
      const outline = new T.LineSegments(
        new T.EdgesGeometry(new T.BoxGeometry(L, H, W)),
        new T.LineBasicMaterial({
          color: 0x8baba0,
          transparent: true,
          opacity: 0.55,
        }),
      );
      outline.position.y = H / 2;
      s.hold.add(outline);
      const points: T.Vector3[] = [];
      for (let x = 0; x <= L; x++)
        points.push(
          new T.Vector3(x - L / 2, 0.003, -W / 2),
          new T.Vector3(x - L / 2, 0.003, W / 2),
        );
      for (let y = 0; y <= W; y++)
        points.push(
          new T.Vector3(-L / 2, 0.003, y - W / 2),
          new T.Vector3(L / 2, 0.003, y - W / 2),
        );
      s.hold.add(
        new T.LineSegments(
          new T.BufferGeometry().setFromPoints(points),
          new T.LineBasicMaterial({ color: 0xb7c8bd }),
        ),
      );
    }
    const units = new Map(plan.units.map((u) => [u.id, u])),
      keep = new Set<string>();
    for (const p of plan.placements) {
      const u = units.get(p.unit_id);
      if (!u) continue;
      keep.add(u.id);
      const [dx, dy] = footprint(u, p).map((n) => n / 1000),
        dz = dimensions(u)[2] / 1000,
        signature = JSON.stringify([dx, dy, dz, u.kind, p.yaw_deg % 180]);
      let item = s.items.get(u.id);
      if (item && item.signature !== signature) {
        s.cargo.remove(item.mesh);
        s.dispose(item.mesh);
        s.items.delete(u.id);
        item = undefined;
      }
      if (!item) {
        const mesh = new T.Mesh(
          new T.BoxGeometry(dx, dz, dy),
          new T.MeshStandardMaterial({
            color: u.kind === "BAR_BUNDLE" ? 0x3a887c : 0xc69b56,
            roughness: 0.55,
            metalness: 0.2,
          }),
        );
        mesh.userData = { id: u.id, kind: u.kind };
        mesh.add(
          new T.LineSegments(
            new T.EdgesGeometry(mesh.geometry),
            new T.LineBasicMaterial({
              color: 0xffffff,
              transparent: true,
              opacity: 0.45,
            }),
          ),
        );
        for (const f of [-0.3, 0.3]) {
          const band = new T.Mesh(
            new T.BoxGeometry(
              p.yaw_deg % 180 ? dx + 0.015 : 0.065,
              dz + 0.015,
              p.yaw_deg % 180 ? 0.065 : dy + 0.015,
            ),
            new T.MeshStandardMaterial({ color: 0x314845, roughness: 0.6 }),
          );
          band.userData.band = true;
          if (p.yaw_deg % 180) band.position.z = dy * f;
          else band.position.x = dx * f;
          mesh.add(band);
        }
        s.cargo.add(mesh);
        item = { mesh, signature };
        s.items.set(u.id, item);
      }
      item.mesh.position.set(
        p.x_mm / 1000 + dx / 2 - L / 2,
        p.z_mm / 1000 + dz / 2,
        p.y_mm / 1000 + dy / 2 - W / 2,
      );
      const m = item.mesh.material as T.MeshStandardMaterial;
      m.color.set(
        u.id === props.selected
          ? 0x9ed7bb
          : props.issueIds.has(u.id)
            ? 0xc76b5a
            : u.kind === "BAR_BUNDLE"
              ? 0x3a887c
              : 0xc69b56,
      );
      m.emissive.set(u.id === props.selected ? 0x234f39 : 0);
    }
    for (const [id, item] of s.items)
      if (!keep.has(id)) {
        s.cargo.remove(item.mesh);
        s.dispose(item.mesh);
        s.items.delete(id);
      }
    s.restyle();
    s.tint();
    if (changedContext) s.fit("fit");
    else s.render();
  }, [props.plan, props.selected, props.issueIds]);
  // Cargo view (D4): rebuilds only the s.pack group. Never touches the renderer, scene, GLB, camera or selection.
  // It reruns for a new view / packing / plan units+placements, and for a new selection only while budget-capped.
  useEffect(() => {
    const s = state.current;
    if (!s) return;
    const view = props.cargoView ?? "ENVELOPE",
      packing = props.packing ?? null,
      { units, placements } = props.plan,
      hold = `${props.plan.hold.length_mm}|${props.plan.hold.width_mm}`,
      prev = s.packDeps;
    if (
      prev &&
      prev.view === view &&
      prev.packing === packing &&
      prev.units === units &&
      prev.placements === placements &&
      prev.hold === hold &&
      (!s.packInfo?.capped || prev.selected === props.selected)
    )
      return;
    s.packDeps = { view, packing, units, placements, hold, selected: props.selected };
    const { plan } = props,
      unitMap = new Map(plan.units.map((u) => [u.id, u])),
      bundles: PackBundle[] = [];
    for (const p of plan.placements) {
      const u = unitMap.get(p.unit_id),
        item = u && s.items.get(u.id);
      if (!u || !item) continue;
      const g = (item.mesh.geometry as T.BoxGeometry).parameters,
        size = new T.Vector3(g.width, g.height, g.depth),
        core = packing ? packingFor(packing, u) : null;
      bundles.push({
        id: u.id,
        core: packingUsable(core) ? core : null,
        warn: isWarnUnit(packing, u),
        min: item.mesh.position.clone().addScaledVector(size, -0.5),
        size,
        yaw: p.yaw_deg,
      });
    }
    s.disposePack();
    const build = buildPacking({
      view,
      bundles,
      selected: props.selected,
      issueIds: props.issueIds,
      camera: s.camera,
    });
    build.objects.forEach((o) => s.pack.add(o));
    s.packMeshes = build.meshes;
    s.packRanges = build.ranges;
    s.packProbes = build.probes;
    s.packModes = build.modes;
    s.packInfo = build.info;
    s.restyle();
    s.render();
    latest.current.onPackingInfo?.(build.info);
  }, [
    props.cargoView,
    props.packing,
    props.plan.units,
    props.plan.placements,
    props.plan.hold.length_mm,
    props.plan.hold.width_mm,
    props.selected,
  ]);
  useEffect(() => {
    const s = state.current;
    if (!s) return;
    const profile =
        props.plan.source === "MIXED_REFERENCE" ? props.profile : null,
      key = profile
        ? JSON.stringify([
            profile.asset_url,
            profile.viewer.translation_m,
            profile.viewer.yaw_deg,
          ])
        : "";
    if (key === s.assetKey) return;
    s.assetKey = key;
    const generation = ++s.generation;
    if (s.ship) {
      s.ghost(false);
      s.scene.remove(s.ship);
      s.dispose(s.ship);
      s.ship = null;
    }
    s.clones.forEach((m) => m.dispose());
    s.clones.clear();
    s.originals.clear();
    delete s.renderer.domElement.dataset.vesselBounds;
    s.render();
    if (!profile) {
      latest.current.onAssetStatus("");
      return;
    }
    latest.current.onAssetStatus("Đang tải mô hình tàu…");
    s.loads++;
    const interactionAtRequest = s.interaction;
    new GLTFLoader().load(
      profile.asset_url,
      (gltf) => {
        if (state.current !== s || generation !== s.generation) {
          s.dispose(gltf.scene);
          return;
        }
        s.ship = gltf.scene;
        s.assetIdentity++;
        // The server's transform is applied as given: no centring, scaling or extra rotation here.
        gltf.scene.position.fromArray(profile.viewer.translation_m);
        gltf.scene.rotation.y = (profile.viewer.yaw_deg * Math.PI) / 180;
        gltf.scene.visible = latest.current.shipVisible;
        const hullNames = new Set(profile.viewer.hull_mesh_names);
        gltf.scene.traverse((o) => {
          if (o instanceof T.Mesh && hullNames.has(o.name))
            s.originals.set(o, o.material);
        });
        s.ghost(latest.current.ghost);
        s.scene.add(gltf.scene);
        gltf.scene.updateMatrixWorld(true);
        if (diagnostic()) {
          const b = new T.Box3().setFromObject(gltf.scene);
          s.renderer.domElement.dataset.vesselBounds = JSON.stringify({
            min: b.min.toArray(),
            max: b.max.toArray(),
            position: gltf.scene.position.toArray(),
          });
        }
        latest.current.onAssetStatus("Mô hình minh họa đã tải.");
        if (s.interaction === interactionAtRequest) s.fit("fit");
        else s.render();
      },
      undefined,
      () => {
        if (state.current === s && generation === s.generation)
          latest.current.onAssetStatus(
            "Không tải được mô hình tàu; hầm và hàng vẫn dùng được.",
          );
      },
    );
  }, [props.plan.source, props.profile]);
  useEffect(() => {
    const s = state.current;
    if (!s) return;
    s.dispose(s.marker);
    s.marker.clear();
    delete s.renderer.domElement.dataset.draftMarker;
    const profile =
        props.plan.source === "MIXED_REFERENCE" ? props.profile : null,
      caseId = props.plan.vessel?.case_id,
      c = profile
        ? profileBody(profile).cases.find((x) => x.id === caseId)
        : undefined,
      draftMarker = profile?.viewer.draft_markers.find(
        (m) => m.case_id === caseId,
      );
    if (profile && c && draftMarker) {
      const [sx, sy, sz] = profile.viewer.hull_box_m;
      const marker = new T.LineSegments(
        new T.EdgesGeometry(new T.BoxGeometry(sx, sy, sz)),
        new T.LineBasicMaterial({ color: 0x067ca0 }),
      );
      marker.position.fromArray(draftMarker.center_m);
      s.marker.add(marker);
      if (diagnostic())
        s.renderer.domElement.dataset.draftMarker = JSON.stringify({
          caseId: c.id,
          y: marker.position.y,
          draft: c.draft_m,
        });
    }
    s.render();
  }, [props.plan.source, props.plan.vessel?.case_id, props.profile]);
  useEffect(() => {
    const s = state.current;
    if (!s) return;
    if (s.ship) s.ship.visible = props.shipVisible;
    s.ghost(props.ghost);
    s.render();
  }, [props.shipVisible, props.ghost]);
  useEffect(() => {
    const s = state.current;
    if (s) {
      if (props.cameraCommand.serial) s.interaction++;
      s.fit(props.cameraCommand.kind);
    }
  }, [props.cameraCommand]);
  useEffect(() => {
    const s = state.current;
    const serial = props.captureSerial ?? 0;
    if (!s || serial <= 0) return;
    // Render and read in the same task: the drawing buffer is not preserved between frames.
    s.render();
    props.onCapture?.(s.renderer.domElement.toDataURL("image/png"));
  }, [props.captureSerial]);
  return <div ref={host} className="scene" />;
}
