import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import type { VesselProfile } from "../api/client";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { dimensions, footprint, fmt, type Plan } from "../features/model";

type Props = {
  plan: Plan;
  profile: VesselProfile | null;
  selected: string;
  onSelect: (id: string) => void;
  issueIds: Set<string>;
};

function Scene({
  plan,
  profile,
  selected,
  onSelect,
  issueIds,
  onFailure,
  reset,
  shipVisible,
  onAssetStatus,
}: Props & { onFailure: () => void; reset: number; shipVisible: boolean; onAssetStatus: (status: string) => void }) {
  const host = useRef<HTMLDivElement>(null);
  const meshMap = useRef(new Map<string, THREE.Mesh>());
  const renderRef = useRef<() => void>(() => {});
  const resetRef = useRef<() => void>(() => {});
  useEffect(() => {
    const el = host.current!;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    } catch {
      onFailure();
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0xeaf0ed, 1);
    el.appendChild(renderer.domElement);
    renderer.domElement.setAttribute(
      "aria-label",
      "Hầm hàng 3D, kéo để xoay và cuộn để phóng to",
    );
    renderer.domElement.setAttribute("data-testid", "three-canvas");
    const scene = new THREE.Scene();
    const L = plan.hold.length_mm / 1000,
      W = plan.hold.width_mm / 1000,
      H = plan.hold.height_mm / 1000;
    const extent = plan.source === "MIXED_REFERENCE" ? 77.8 : Math.max(L, W, H);
    const camera = new THREE.PerspectiveCamera(38, 1, 0.05, extent * 30);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = false;
    controls.minDistance = 2;
    controls.maxDistance = extent * 5;
    controls.maxPolarAngle = Math.PI / 2 - 0.02;
    let exposeMeshes = () => {};
    const render = () => { renderer.render(scene, camera); exposeMeshes(); };
    renderRef.current = render;
    resetRef.current = () => {
      camera.position.set(extent * 0.83, extent * 0.95, extent * 1.05);
      controls.target.set(0, 0, 0);
      controls.update();
      render();
    };
    scene.add(new THREE.HemisphereLight(0xffffff, 0x5b736b, 2.8));
    const sun = new THREE.DirectionalLight(0xffffff, 3);
    sun.position.set(-10, 20, 10);
    scene.add(sun);
    let disposed = false;
    const disposeObject = (root: THREE.Object3D) => root.traverse((object) => {
      if (object instanceof THREE.Mesh || object instanceof THREE.LineSegments) {
        object.geometry.dispose();
        (Array.isArray(object.material) ? object.material : [object.material]).forEach((material: THREE.Material) => material.dispose());
      }
    });
    if (plan.source === "MIXED_REFERENCE" && profile) {
      onAssetStatus("Đang tải mô hình tàu…");
      new GLTFLoader().load(profile.asset_url, (gltf) => {
        if (disposed) { disposeObject(gltf.scene); return; }
        gltf.scene.position.fromArray(profile.geometry.glb_to_hold_translation_m);
        gltf.scene.visible = shipVisible;
        gltf.scene.traverse((object) => {
          if (object instanceof THREE.Mesh) {
            const materials = Array.isArray(object.material) ? object.material : [object.material];
            materials.forEach((material: THREE.Material) => { material.transparent = true; material.opacity = 0.32; material.depthWrite = false; });
          }
        });
        scene.add(gltf.scene); gltf.scene.updateMatrixWorld(true);
        const bbox = new THREE.Box3().setFromObject(gltf.scene);
        renderer.domElement.dataset.vesselBounds = JSON.stringify({min:bbox.min.toArray(),max:bbox.max.toArray(),position:gltf.scene.position.toArray()});
        onAssetStatus("Mô hình minh họa đã tải."); render();
      }, undefined, () => { if (!disposed) onAssetStatus("Không tải được mô hình tàu; hầm và hàng vẫn dùng được."); });
      const selectedCase = profile.cases.find(c => c.id === plan.vessel?.case_id);
      if (selectedCase) {
        const marker = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(77.8, 0.01, 13.24)), new THREE.LineBasicMaterial({color: 0x067ca0}));
        marker.position.set(profile.geometry.glb_to_hold_translation_m[0], selectedCase.draft_m - profile.geometry.source_floor_z_m, 0);
        scene.add(marker);
        renderer.domElement.dataset.draftMarker = JSON.stringify({caseId:selectedCase.id, y:marker.position.y, draft:selectedCase.draft_m});
      }
    }
    const slab = new THREE.Mesh(
      new THREE.BoxGeometry(L, 0.13, W),
      new THREE.MeshStandardMaterial({ color: 0xd2ddd4, roughness: 0.9 }),
    );
    slab.position.y = -0.075;
    scene.add(slab);
    const outline = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.BoxGeometry(L, H, W)),
      new THREE.LineBasicMaterial({
        color: 0x8baba0,
        transparent: true,
        opacity: 0.55,
      }),
    );
    outline.position.y = H / 2;
    scene.add(outline);
    const gridPoints: THREE.Vector3[] = [];
    for (let x = 0; x <= L; x++)
      gridPoints.push(
        new THREE.Vector3(x - L / 2, 0.003, -W / 2),
        new THREE.Vector3(x - L / 2, 0.003, W / 2),
      );
    for (let y = 0; y <= W; y++)
      gridPoints.push(
        new THREE.Vector3(-L / 2, 0.003, y - W / 2),
        new THREE.Vector3(L / 2, 0.003, y - W / 2),
      );
    scene.add(
      new THREE.LineSegments(
        new THREE.BufferGeometry().setFromPoints(gridPoints),
        new THREE.LineBasicMaterial({ color: 0xb7c8bd }),
      ),
    );
    const units = new Map(plan.units.map((u) => [u.id, u]));
    const meshes: THREE.Mesh[] = [];
    meshMap.current.clear();
    for (const p of plan.placements) {
      const u = units.get(p.unit_id)!;
      const [dx, dy] = footprint(u, p).map((n) => n / 1000);
      const dz = dimensions(u)[2] / 1000;
      const mesh = new THREE.Mesh(
        new THREE.BoxGeometry(dx, dz, dy),
        new THREE.MeshStandardMaterial({
          color: u.kind === "BAR_BUNDLE" ? 0x3a887c : 0xc69b56,
          roughness: 0.55,
          metalness: 0.2,
        }),
      );
      mesh.position.set(
        p.x_mm / 1000 + dx / 2 - L / 2,
        p.z_mm / 1000 + dz / 2,
        p.y_mm / 1000 + dy / 2 - W / 2,
      );
      mesh.userData = { id: u.id, kind: u.kind };
      const edge = new THREE.LineSegments(
        new THREE.EdgesGeometry(mesh.geometry),
        new THREE.LineBasicMaterial({
          color: 0xffffff,
          transparent: true,
          opacity: 0.45,
        }),
      );
      mesh.add(edge);
      // Two visible bands distinguish a physical bundle without implying individual pipe geometry.
      for (const fraction of [-0.3, 0.3]) {
        const band = new THREE.Mesh(
          new THREE.BoxGeometry(
            p.yaw_deg % 180 ? dx + 0.015 : 0.065,
            dz + 0.015,
            p.yaw_deg % 180 ? 0.065 : dy + 0.015,
          ),
          new THREE.MeshStandardMaterial({ color: 0x314845, roughness: 0.6 }),
        );
        if (p.yaw_deg % 180) band.position.z = dy * fraction;
        else band.position.x = dx * fraction;
        mesh.add(band);
      }
      scene.add(mesh);
      meshes.push(mesh);
      meshMap.current.set(u.id, mesh);
    }
    const canvas = renderer.domElement;
    exposeMeshes = () => {
      const data = Array.from(meshMap.current, ([id, mesh]) => {
        mesh.updateMatrixWorld(true);
        const box = new THREE.Box3().setFromObject(mesh, true);
        const position = mesh.position.toArray();
        const parameters = (mesh.geometry as THREE.BoxGeometry).parameters;
        return { id, position, dimensions: [parameters.width, parameters.height, parameters.depth], worldMatrix: mesh.matrixWorld.toArray(), boxMin: box.min.toArray(), boxMax: box.max.toArray() };
      });
      canvas.dataset.meshes = JSON.stringify(data);
      canvas.dataset.projectedMeshes = JSON.stringify(Array.from(meshMap.current, ([id, mesh]) => {
        const point = mesh.getWorldPosition(new THREE.Vector3()).project(camera);
        return { id, x: (point.x + 1) * canvas.clientWidth / 2, y: (1 - point.y) * canvas.clientHeight / 2 };
      }));
      canvas.dataset.camera = JSON.stringify(camera.position.toArray());
    };
    const resize = () => {
      const width = el.clientWidth,
        height = el.clientHeight;
      if (!width || !height) return;
      renderer.setSize(width, height);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      render();
    };
    const observer = new ResizeObserver(resize);
    observer.observe(el);
    controls.addEventListener("change", render);
    let start = { x: 0, y: 0 };
    const down = (event: PointerEvent) => {
      start = { x: event.clientX, y: event.clientY };
    };
    const up = (event: PointerEvent) => {
      if (Math.hypot(event.clientX - start.x, event.clientY - start.y) > 5)
        return;
      const box = renderer.domElement.getBoundingClientRect();
      const ray = new THREE.Raycaster();
      ray.setFromCamera(
        new THREE.Vector2(
          ((event.clientX - box.left) / box.width) * 2 - 1,
          (-(event.clientY - box.top) / box.height) * 2 + 1,
        ),
        camera,
      );
      const hit = ray.intersectObjects(meshes, false)[0];
      if (hit) onSelect(hit.object.userData.id);
    };
    const contextLost = (event: Event) => {
      event.preventDefault();
      onFailure();
    };
    renderer.domElement.addEventListener("pointerdown", down);
    renderer.domElement.addEventListener("pointerup", up);
    renderer.domElement.addEventListener("webglcontextlost", contextLost);
    resetRef.current();
    resize();
    return () => {
      disposed = true;
      observer.disconnect();
      controls.dispose();
      renderer.domElement.removeEventListener("pointerdown", down);
      renderer.domElement.removeEventListener("pointerup", up);
      renderer.domElement.removeEventListener("webglcontextlost", contextLost);
      scene.traverse((object) => {
        if (
          object instanceof THREE.Mesh ||
          object instanceof THREE.LineSegments
        ) {
          object.geometry.dispose();
          const mats = Array.isArray(object.material)
            ? object.material
            : [object.material];
          mats.forEach((m: THREE.Material) => m.dispose());
        }
      });
      renderer.dispose();
      el.replaceChildren();
      meshMap.current.clear();
      renderRef.current = () => {};
      resetRef.current = () => {};
    };
  }, [plan, profile, shipVisible, onSelect, onFailure, onAssetStatus]);
  useEffect(() => {
    for (const [id, mesh] of meshMap.current) {
      const material = mesh.material as THREE.MeshStandardMaterial;
      material.color.set(
        id === selected
          ? 0x9ed7bb
          : issueIds.has(id)
            ? 0xc76b5a
            : mesh.userData.kind === "BAR_BUNDLE"
              ? 0x3a887c
              : 0xc69b56,
      );
      material.emissive.set(id === selected ? 0x234f39 : 0x000000);
    }
    renderRef.current();
  }, [selected, issueIds, plan]);
  useEffect(() => {
    resetRef.current();
  }, [reset]);
  return <div ref={host} className="scene" />;
}

export default function Viewer(props: Props) {
  const [view, setView] = useState<"3d" | "2d">("3d");
  const [failed, setFailed] = useState(false);
  const [reset, setReset] = useState(0);
  const [shipVisible, setShipVisible] = useState(true);
  const [assetStatus, setAssetStatus] = useState("");
  const failureRef = useRef(() => {
    setFailed(true);
    setView("2d");
  });
  const { plan, selected, onSelect, issueIds } = props;
  const margin = 1100;
  const unitMap = new Map(plan.units.map(u => [u.id,u]));
  return (
    <section className="viewer-card" aria-label="Mô hình chất xếp">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">PHƯƠNG ÁN / 01</span>
          <h2>Không gian chất xếp</h2>
        </div>
        <div className="view-toggle" aria-label="Chế độ xem">
          <button
            className={view === "3d" ? "active" : ""}
            onClick={() => {
              setFailed(false);
              setView("3d");
            }}
            aria-pressed={view === "3d"}
          >
            3D
          </button>
          <button
            className={view === "2d" ? "active" : ""}
            onClick={() => setView("2d")}
            aria-pressed={view === "2d"}
          >
            Mặt bằng
          </button>
        </div>
      </div>
      <div className="viewport">
        <div className="viewport-label">
          <span className="dot" />
          BOX · MỘT LỚP <span className="muted">/</span> {plan.hold.name}
        </div>
        {view === "3d" ? (
          <Scene {...props} onFailure={failureRef.current} reset={reset} shipVisible={shipVisible} onAssetStatus={setAssetStatus} />
        ) : (
          <svg
            className="plan-svg"
            viewBox={`${-margin} ${-margin} ${plan.hold.length_mm + 2 * margin} ${plan.hold.width_mm + 2 * margin}`}
            role="img"
            aria-label="Mặt bằng hầm và ID từng bó"
          >
            <defs>
              <pattern
                id="floor-grid"
                width="1000"
                height="1000"
                patternUnits="userSpaceOnUse"
              >
                <path
                  d="M 1000 0 L 0 0 0 1000"
                  fill="none"
                  stroke="#ccd8cf"
                  strokeWidth="20"
                />
              </pattern>
            </defs>
            <rect
              width={plan.hold.length_mm}
              height={plan.hold.width_mm}
              fill="url(#floor-grid)"
              stroke="#7f9a8a"
              strokeWidth="50"
            />
            {plan.placements.map((p) => {
              const u = unitMap.get(p.unit_id)!;
              const [w, h] = footprint(u, p);
              return (
                <g
                  key={u.id}
                  role="button"
                  tabIndex={0}
                  aria-label={`Chọn ${u.id}`}
                  aria-pressed={selected === u.id}
                  onClick={() => onSelect(u.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onSelect(u.id);
                    }
                  }}
                  className="svg-unit"
                >
                  <rect
                    x={p.x_mm}
                    y={p.y_mm}
                    width={w}
                    height={h}
                    rx="60"
                    fill={
                      selected === u.id
                        ? "#9ed7bb"
                        : issueIds.has(u.id)
                          ? "#cf8275"
                          : u.kind === "BAR_BUNDLE"
                            ? "#388778"
                            : "#c69b56"
                    }
                    stroke={selected === u.id ? "#173e31" : "#ffffff"}
                    strokeWidth={selected === u.id ? 65 : 20}
                  />
                  <text
                    x={p.x_mm + w / 2}
                    y={p.y_mm + h / 2 + 75}
                    textAnchor="middle"
                    fontSize="240"
                    fill={selected === u.id ? "#173e31" : "#fff"}
                  >
                    {u.id}
                  </text>
                </g>
              );
            })}
            <text
              x={plan.hold.length_mm / 2}
              y={plan.hold.width_mm + 650}
              textAnchor="middle"
              fontSize="300"
              fill="#587064"
            >
              X · {fmt(plan.hold.length_mm / 1000)} m
            </text>
            <text x="0" y="-400" fontSize="260" fill="#587064">
              Gốc (0, 0) · Y theo chiều rộng
            </text>
          </svg>
        )}
        <div className="viewport-bottom">
          <span>
            {failed
              ? "WebGL không khả dụng · đang dùng mặt bằng 2D"
              : view === "3d"
                ? "Kéo để xoay · Cuộn để zoom · Bấm bó để chọn"
                : "Bấm bó hoặc dùng Tab + Enter để chọn"}
          </span>
          {view === "3d" && (
            <button
              className="icon-button"
              onClick={() => setReset((n) => n + 1)}
              aria-label="Đặt lại góc nhìn"
            >
              ↺
            </button>
          )}
        </div>
      </div>
      {plan.placements.length === 0 && <p className="scope-note" role="status">Chưa có bó nào được đặt. Chọn Xếp thử tự động → Áp dụng xếp thử, hoặc đặt từng bó bằng tay.</p>}
      {plan.source === "MIXED_REFERENCE" && <div className="scope-note"><button className="button secondary" onClick={() => setShipVisible(v => !v)} aria-pressed={shipVisible}>{shipVisible ? "Ẩn tàu" : "Hiện tàu"}</button><p role="status">{assetStatus} Màu thân GLB cố định theo mớn 4,85 m; khung xanh biểu thị mớn tham chiếu đã chọn.</p></div>}
      <div className="viewer-legend">
        <span>
          <i className="swatch steel" />
          Thép thanh
        </span>
        <span>
          <i className="swatch pipe" />
          Thép ống
        </span>
        <span>
          <i className="swatch selected" />
          Đang chọn
        </span>
        <span className="legend-end">Khối bao bó hàng · mm</span>
      </div>
    </section>
  );
}
