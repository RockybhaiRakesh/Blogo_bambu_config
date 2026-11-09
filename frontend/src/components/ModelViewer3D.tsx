import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import { Box, Grid, Layers, Sparkles, Sliders, Maximize2, Paintbrush, Eraser, Scissors } from 'lucide-react';

interface ModelViewer3DProps {
  modelId?: string;
  meshUrl?: string;
  cutPlaneZ?: number; // Single cut plane Z height
  cutPlanesZ?: number[]; // Multi-cut planes visualization
  showCutPlane?: boolean;
  part1Url?: string; // Optional legacy dual split parts
  part2Url?: string;
  partsUrls?: string[]; // Dynamic N-part visualization
  externalViewMode?: 'assembled' | 'exploded' | 'plate' | 'solo';
  externalSoloIndex?: number;
  onSelectPart?: (index: number) => void;
  // Paint-to-cut integration
  enablePaintMode?: boolean;
  externalPaintedFaces?: number[];
  onPaintedFacesChange?: (indices: number[]) => void;
  height?: string;
}

interface LoadedPartInfo {
  mesh: THREE.Mesh;
  initialBBox: THREE.Box3;
  initialCenter: THREE.Vector3;
  triangles: number;
}

const PART_COLORS = [
  0x0284c7, // Sapphire Blue (Part 1 - Base)
  0xd97706, // Amber Gold (Part 2 - Legs/Body)
  0x059669, // Emerald Green (Part 3 - Torso)
  0x7c3aed, // Violet Purple (Part 4 - Cowl)
  0xe11d48, // Crimson Red (Part 5 - Cape)
  0x0d9488  // Teal
];

export const ModelViewer3D: React.FC<ModelViewer3DProps> = ({
  modelId,
  meshUrl,
  cutPlaneZ,
  cutPlanesZ,
  showCutPlane = false,
  part1Url,
  part2Url,
  partsUrls,
  externalViewMode,
  externalSoloIndex,
  onSelectPart,
  enablePaintMode = false,
  externalPaintedFaces,
  onPaintedFacesChange,
  height = '500px'
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [wireframe, setWireframe] = useState<boolean>(false);
  const [showBox, setShowBox] = useState<boolean>(true);
  const [showGrid, setShowGrid] = useState<boolean>(true);
  const [triangles, setTriangles] = useState<number>(0);

  // Multi-part visualization modes: 'exploded' | 'plate' | 'assembled' | 'solo'
  const [viewMode, setViewMode] = useState<'assembled' | 'exploded' | 'plate' | 'solo'>('exploded');
  const [explodeGap, setExplodeGap] = useState<number>(25);
  const [soloIndex, setSoloIndex] = useState<number>(-1);

  // Paint-to-cut brush state
  const [paintActive, setPaintActive] = useState<boolean>(enablePaintMode);
  const [brushRadius, setBrushRadius] = useState<number>(12);
  const [paintedCount, setPaintedCount] = useState<number>(0);
  const paintedSetRef = useRef<Set<number>>(new Set());

  useEffect(() => {
    setPaintActive(enablePaintMode);
  }, [enablePaintMode]);

  // Sync external painted faces selection (e.g. from AI anatomical presets)
  useEffect(() => {
    if (!mainMeshRef.current || !externalPaintedFaces) return;
    const mesh = mainMeshRef.current;
    const geom = mesh.geometry;
    const col = geom.attributes.color as THREE.BufferAttribute;
    if (!col) return;

    paintedSetRef.current = new Set(externalPaintedFaces);
    setPaintedCount(externalPaintedFaces.length);

    const numFaces = geom.attributes.position.count / 3;
    for (let f = 0; f < numFaces; f++) {
      const isPainted = paintedSetRef.current.has(f);
      const r = isPainted ? 0.98 : 0.01;
      const g = isPainted ? 0.75 : 0.52;
      const b = isPainted ? 0.12 : 0.78;
      for (let k = 0; k < 3; k++) {
        col.setXYZ(f * 3 + k, r, g, b);
      }
    }
    col.needsUpdate = true;
  }, [externalPaintedFaces]);

  // Sync with external props if provided
  useEffect(() => {
    if (externalViewMode) setViewMode(externalViewMode);
  }, [externalViewMode]);

  useEffect(() => {
    if (externalSoloIndex !== undefined) setSoloIndex(externalSoloIndex);
  }, [externalSoloIndex]);

  // Three.js internal references
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const meshesRef = useRef<THREE.Mesh[]>([]);
  const mainMeshRef = useRef<THREE.Mesh | null>(null);
  const partsInfoRef = useRef<LoadedPartInfo[]>([]);
  const cutPlanesRef = useRef<THREE.Mesh[]>([]);
  const bBoxHelperRef = useRef<THREE.BoxHelper | null>(null);
  const gridHelperRef = useRef<THREE.GridHelper | null>(null);
  const brushCursorRef = useRef<THREE.Mesh | null>(null);

  const requestRenderRef = useRef<() => void>(() => {});

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const width = container.clientWidth;
    const h = container.clientHeight || 500;

    // 1. Scene with clean studio light background
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf8fafc);
    sceneRef.current = scene;

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(45, width / h, 0.1, 2000);
    camera.position.set(180, -220, 180);
    camera.up.set(0, 0, 1); // Z-up for 3D printing
    cameraRef.current = camera;

    // 3. Hardware-accelerated renderer (Unused shadow map passes stripped for speed)
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(width, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    renderer.shadowMap.enabled = false;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // 4. Orbit Controls (left-drag rotates by default, right-drag pans)
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxDistance = 1000;
    controls.minDistance = 10;
    controlsRef.current = controls;

    // 5. Studio Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight1.position.set(200, 300, 400);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0xbae6fd, 0.6); // Soft blue rim light
    dirLight2.position.set(-200, -200, 150);
    scene.add(dirLight2);

    // 6. Bambu Lab A1 Bed Grid (256 x 256 mm)
    const grid = new THREE.GridHelper(256, 16, 0x0284c7, 0xcbd5e1);
    grid.rotation.x = Math.PI / 2; // Lie flat on XY plane
    scene.add(grid);
    gridHelperRef.current = grid;

    const plateGeo = new THREE.PlaneGeometry(256, 256);
    const plateMat = new THREE.MeshBasicMaterial({
      color: 0xe2e8f0,
      transparent: true,
      opacity: 0.5,
      depthWrite: false
    });
    const plate = new THREE.Mesh(plateGeo, plateMat);
    scene.add(plate);

    // Brush cursor sphere helper for 3D painting
    const cursorGeo = new THREE.SphereGeometry(1, 16, 16);
    const cursorMat = new THREE.MeshBasicMaterial({
      color: 0xf59e0b,
      transparent: true,
      opacity: 0.45,
      depthTest: false
    });
    const cursorMesh = new THREE.Mesh(cursorGeo, cursorMat);
    cursorMesh.visible = false;
    scene.add(cursorMesh);
    brushCursorRef.current = cursorMesh;

    // 7. Demand-Driven (Dirty-Flag) Render Loop: 0% CPU at idle
    let animId: number;
    let needsRender = true;

    const requestRender = () => {
      needsRender = true;
    };
    requestRenderRef.current = requestRender;

    controls.addEventListener('change', requestRender);

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const isDamping = controls.update();
      if (isDamping || needsRender) {
        renderer.render(scene, camera);
        needsRender = isDamping; // Remain active only while damping smoothly settles
      }
    };
    animate();

    // Resize handler
    const handleResize = () => {
      if (!containerRef.current || !rendererRef.current || !cameraRef.current) return;
      const w = containerRef.current.clientWidth;
      const newH = containerRef.current.clientHeight;
      cameraRef.current.aspect = w / newH;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(w, newH);
      requestRender();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      controls.removeEventListener('change', requestRender);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
      container.innerHTML = '';
    };
  }, []);

  // Frame current scene visible objects
  const frameScene = useCallback(() => {
    if (!cameraRef.current || !controlsRef.current) return;
    const currentBox = new THREE.Box3();
    let hasVisible = false;

    partsInfoRef.current.forEach((info) => {
      if (info.mesh.visible) {
        const b = new THREE.Box3().setFromObject(info.mesh);
        currentBox.union(b);
        hasVisible = true;
      }
    });

    if (!hasVisible && meshesRef.current.length > 0) {
      meshesRef.current.forEach((m) => {
        if (m.visible) {
          const b = new THREE.Box3().setFromObject(m);
          currentBox.union(b);
          hasVisible = true;
        }
      });
    }

    if (hasVisible && !currentBox.isEmpty()) {
      const size = currentBox.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);
      const center = currentBox.getCenter(new THREE.Vector3());
      controlsRef.current.target.copy(center);
      cameraRef.current.position.set(center.x + maxDim * 1.5, center.y - maxDim * 1.8, center.z + maxDim * 1.3);
      controlsRef.current.update();
      requestRenderRef.current();
    }
  }, []);

  // Apply layout transformations (assembled, exploded, plate, solo)
  const applyLayout = useCallback((mode: string, gap: number, soloIdx: number) => {
    const parts = partsInfoRef.current;
    if (parts.length === 0) return;

    const combinedBox = new THREE.Box3();
    parts.forEach((p) => combinedBox.union(p.initialBBox));
    const combinedCenter = combinedBox.getCenter(new THREE.Vector3());

    if (mode === 'solo' && soloIdx >= 0 && soloIdx < parts.length) {
      parts.forEach((p, idx) => {
        if (idx === soloIdx) {
          p.mesh.position.set(-p.initialCenter.x, -p.initialCenter.y, -p.initialBBox.min.z);
          p.mesh.visible = true;
        } else {
          p.mesh.visible = false;
        }
      });
    } else if (mode === 'plate') {
      let totalWidth = 0;
      const spacing = 18;
      parts.forEach((p, idx) => {
        const w = p.initialBBox.max.x - p.initialBBox.min.x;
        totalWidth += w + (idx > 0 ? spacing : 0);
      });

      let currentX = -totalWidth / 2;
      parts.forEach((p) => {
        const w = p.initialBBox.max.x - p.initialBBox.min.x;
        const partCenterX = currentX + w / 2;
        p.mesh.position.set(
          partCenterX - p.initialCenter.x,
          -p.initialCenter.y,
          -p.initialBBox.min.z
        );
        p.mesh.visible = true;
        currentX += w + spacing;
      });
    } else if (mode === 'exploded') {
      parts.forEach((p, idx) => {
        const zLift = idx * gap;
        p.mesh.position.set(-combinedCenter.x, -combinedCenter.y, -combinedBox.min.z + zLift);
        p.mesh.visible = true;
      });
    } else {
      parts.forEach((p) => {
        p.mesh.position.set(-combinedCenter.x, -combinedCenter.y, -combinedBox.min.z);
        p.mesh.visible = true;
      });
    }

    frameScene();
  }, [frameScene]);

  // Load Model / Meshes
  useEffect(() => {
    if (!sceneRef.current) return;
    const scene = sceneRef.current;

    // Free GPU VRAM from previous geometries & materials (prevents memory leak)
    meshesRef.current.forEach((m) => {
      scene.remove(m);
      if (m.geometry) m.geometry.dispose();
      if (Array.isArray(m.material)) {
        m.material.forEach((mat) => mat.dispose());
      } else if (m.material) {
        m.material.dispose();
      }
    });
    meshesRef.current = [];
    mainMeshRef.current = null;
    partsInfoRef.current = [];
    paintedSetRef.current.clear();
    setPaintedCount(0);

    if (bBoxHelperRef.current) scene.remove(bBoxHelperRef.current);
    cutPlanesRef.current.forEach((p) => scene.remove(p));
    cutPlanesRef.current = [];

    setLoading(true);
    setError(null);

    const loader = new STLLoader();
    const url = meshUrl || (modelId ? `/api/models/${modelId}/mesh` : null);

    const allUrls = (partsUrls && partsUrls.length > 0)
      ? partsUrls
      : (part1Url && part2Url ? [part1Url, part2Url] : []);

    if (allUrls.length === 0 && !url) {
      setLoading(false);
      return;
    }

    const loadSingleSTL = (fileUrl: string, color: number = 0x0284c7): Promise<THREE.Mesh> => {
      let targetUrl = fileUrl;
      if (targetUrl.includes('\\') || targetUrl.includes('split_parts') || /^[a-zA-Z]:/.test(targetUrl)) {
        const fname = targetUrl.split(/[\\/]/).pop();
        if (modelId && fname) {
          targetUrl = `/api/models/${modelId}/parts/${fname}`;
        }
      }

      return new Promise((resolve, reject) => {
        loader.load(
          targetUrl,
          (geometry) => {
            geometry.computeVertexNormals();
            geometry.computeBoundingBox();

            // Allocate vertex color buffer ONLY when 3D painting is active (saves 1.2MB-12MB VRAM per mesh)
            if (enablePaintMode) {
              const posAttr = geometry.attributes.position;
              const vCount = posAttr.count;
              const colors = new Float32Array(vCount * 3);
              const r = ((color >> 16) & 255) / 255;
              const g = ((color >> 8) & 255) / 255;
              const b = (color & 255) / 255;
              for (let i = 0; i < vCount; i++) {
                colors[i * 3] = r;
                colors[i * 3 + 1] = g;
                colors[i * 3 + 2] = b;
              }
              geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
            }

            const material = new THREE.MeshStandardMaterial({
              color: enablePaintMode ? 0xffffff : color,
              vertexColors: enablePaintMode,
              roughness: 0.35,
              metalness: 0.15,
              wireframe: wireframe,
              side: THREE.DoubleSide
            });
            const mesh = new THREE.Mesh(geometry, material);
            resolve(mesh);
          },
          undefined,
          (err) => {
            console.error('Failed to load STL from:', targetUrl, err);
            reject(err);
          }
        );
      });
    };

    if (allUrls.length > 0) {
      Promise.all(allUrls.map((u, i) => loadSingleSTL(u, PART_COLORS[i % PART_COLORS.length])))
        .then((loadedMeshes) => {
          let triCount = 0;
          const infos: LoadedPartInfo[] = [];

          loadedMeshes.forEach((mesh) => {
            scene.add(mesh);
            const bbox = mesh.geometry.boundingBox!.clone();
            const center = bbox.getCenter(new THREE.Vector3());
            const count = mesh.geometry.attributes.position.count / 3;
            triCount += count;
            infos.push({
              mesh,
              initialBBox: bbox,
              initialCenter: center,
              triangles: count
            });
          });

          meshesRef.current = loadedMeshes;
          partsInfoRef.current = infos;
          setTriangles(triCount);

          applyLayout(viewMode, explodeGap, soloIndex);
          setLoading(false);
          requestRenderRef.current();
        })
        .catch(() => {
          setError('Failed to load multi-part 3D assembly preview.');
          setLoading(false);
        });
    } else if (url) {
      loadSingleSTL(url, 0x0284c7)
        .then((mesh) => {
          scene.add(mesh);
          meshesRef.current = [mesh];
          mainMeshRef.current = mesh;

          const geom = mesh.geometry;
          if (geom.boundingBox) {
            const bbox = geom.boundingBox;
            const center = new THREE.Vector3();
            bbox.getCenter(center);

            mesh.position.x = -center.x;
            mesh.position.y = -center.y;
            mesh.position.z = -bbox.min.z;

            if (showBox) {
              const boxHelper = new THREE.BoxHelper(mesh, 0x0284c7);
              scene.add(boxHelper);
              bBoxHelperRef.current = boxHelper;
            }

            if (cameraRef.current && controlsRef.current) {
              const maxDim = Math.max(bbox.max.x - bbox.min.x, bbox.max.y - bbox.min.y, bbox.max.z - bbox.min.z);
              cameraRef.current.position.set(maxDim * 1.5, -maxDim * 2, maxDim * 1.5);
              controlsRef.current.target.set(0, 0, (bbox.max.z - bbox.min.z) / 2);
              controlsRef.current.update();
            }

            setTriangles(geom.attributes.position.count / 3);
          }

          setLoading(false);
          requestRenderRef.current();
        })
        .catch((err) => {
          console.error(err);
          setError('Unable to load 3D mesh. Check if file is valid STL.');
          setLoading(false);
        });
    }
  }, [modelId, meshUrl, part1Url, part2Url, partsUrls]);

  // Update layout when viewMode, explodeGap, or soloIndex changes
  useEffect(() => {
    if (partsInfoRef.current.length > 0) {
      applyLayout(viewMode, explodeGap, soloIndex);
    }
  }, [viewMode, explodeGap, soloIndex, applyLayout]);

  // Update wireframe mode
  useEffect(() => {
    meshesRef.current.forEach((m) => {
      if (m.material instanceof THREE.MeshStandardMaterial) {
        m.material.wireframe = wireframe;
      }
    });
    requestRenderRef.current();
  }, [wireframe]);

  // Update Cut Plane(s) preview
  useEffect(() => {
    if (!sceneRef.current) return;
    const scene = sceneRef.current;

    cutPlanesRef.current.forEach((p) => scene.remove(p));
    cutPlanesRef.current = [];

    const planes = (cutPlanesZ && cutPlanesZ.length > 0)
      ? cutPlanesZ
      : (cutPlaneZ !== undefined ? [cutPlaneZ] : []);

    if (showCutPlane && planes.length > 0 && !paintActive) {
      planes.forEach((pz) => {
        const planeGeo = new THREE.PlaneGeometry(260, 260);
        const planeMat = new THREE.MeshBasicMaterial({
          color: 0xef4444,
          transparent: true,
          opacity: 0.35,
          side: THREE.DoubleSide
        });
        const planeMesh = new THREE.Mesh(planeGeo, planeMat);
        planeMesh.position.set(0, 0, pz);
        scene.add(planeMesh);
        cutPlanesRef.current.push(planeMesh);
      });
    }
    requestRenderRef.current();
  }, [showCutPlane, cutPlaneZ, cutPlanesZ, paintActive]);

  // Interactive 3D Surface / Sphere Brush Painter
  useEffect(() => {
    const container = containerRef.current;
    if (!container || !paintActive) {
      if (brushCursorRef.current) brushCursorRef.current.visible = false;
      if (controlsRef.current) controlsRef.current.enabled = true;
      return;
    }

    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    let isMouseDown = false;

    const paintAtPoint = (worldPoint: THREE.Vector3) => {
      const mesh = mainMeshRef.current;
      if (!mesh) return;

      const geom = mesh.geometry;
      const pos = geom.attributes.position;
      const col = geom.attributes.color as THREE.BufferAttribute;
      if (!pos || !col) return;

      const localPt = mesh.worldToLocal(worldPoint.clone());
      const rSq = brushRadius * brushRadius;
      const numFaces = pos.count / 3;

      for (let f = 0; f < numFaces; f++) {
        const i0 = f * 3;
        const cx = (pos.getX(i0) + pos.getX(i0 + 1) + pos.getX(i0 + 2)) / 3;
        const cy = (pos.getY(i0) + pos.getY(i0 + 1) + pos.getY(i0 + 2)) / 3;
        const cz = (pos.getZ(i0) + pos.getZ(i0 + 1) + pos.getZ(i0 + 2)) / 3;

        const dSq = (cx - localPt.x) ** 2 + (cy - localPt.y) ** 2 + (cz - localPt.z) ** 2;
        if (dSq <= rSq) {
          paintedSetRef.current.add(f);
          // Highlight with Neon Amber Gold (RGB: 0.98, 0.75, 0.12)
          for (let k = 0; k < 3; k++) {
            col.setXYZ(i0 + k, 0.98, 0.75, 0.12);
          }
        }
      }

      col.needsUpdate = true;
      setPaintedCount(paintedSetRef.current.size);
      if (onPaintedFacesChange) {
        onPaintedFacesChange(Array.from(paintedSetRef.current));
      }
    };

    const onPointerDown = (e: MouseEvent) => {
      if (e.button === 0) {
        // Left click: Paint
        isMouseDown = true;
        if (controlsRef.current) controlsRef.current.enabled = false;

        const rect = container.getBoundingClientRect();
        mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

        if (cameraRef.current && mainMeshRef.current) {
          raycaster.setFromCamera(mouse, cameraRef.current);
          const hits = raycaster.intersectObject(mainMeshRef.current);
          if (hits.length > 0) {
            paintAtPoint(hits[0].point);
          }
        }
      }
    };

    const onPointerMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      if (cameraRef.current && mainMeshRef.current) {
        raycaster.setFromCamera(mouse, cameraRef.current);
        const hits = raycaster.intersectObject(mainMeshRef.current);
        if (hits.length > 0) {
          const hitPt = hits[0].point;
          if (brushCursorRef.current) {
            brushCursorRef.current.position.copy(hitPt);
            brushCursorRef.current.scale.setScalar(brushRadius);
            brushCursorRef.current.visible = true;
          }
          if (isMouseDown) {
            paintAtPoint(hitPt);
          }
        } else {
          if (brushCursorRef.current) brushCursorRef.current.visible = false;
        }
      }
    };

    const onPointerUp = () => {
      isMouseDown = false;
      if (controlsRef.current) controlsRef.current.enabled = true;
    };

    container.addEventListener('mousedown', onPointerDown);
    container.addEventListener('mousemove', onPointerMove);
    window.addEventListener('mouseup', onPointerUp);

    return () => {
      container.removeEventListener('mousedown', onPointerDown);
      container.removeEventListener('mousemove', onPointerMove);
      window.removeEventListener('mouseup', onPointerUp);
      if (controlsRef.current) controlsRef.current.enabled = true;
      if (brushCursorRef.current) brushCursorRef.current.visible = false;
    };
  }, [paintActive, brushRadius, onPaintedFacesChange]);

  const clearPaintedSelection = () => {
    paintedSetRef.current.clear();
    setPaintedCount(0);
    const mesh = mainMeshRef.current;
    if (mesh) {
      const col = mesh.geometry.attributes.color as THREE.BufferAttribute;
      if (col) {
        const count = col.count;
        for (let i = 0; i < count; i++) {
          col.setXYZ(i, 0.01, 0.52, 0.78);
        }
        col.needsUpdate = true;
      }
    }
    if (onPaintedFacesChange) {
      onPaintedFacesChange([]);
    }
  };

  // Camera presets
  const setCameraView = (view: 'iso' | 'front' | 'top' | 'side') => {
    if (!cameraRef.current || !controlsRef.current) return;
    const cam = cameraRef.current;
    const ctrl = controlsRef.current;
    const dist = 280;

    if (view === 'iso') {
      cam.position.set(dist * 0.7, -dist * 0.7, dist * 0.7);
    } else if (view === 'front') {
      cam.position.set(0, -dist, 40);
    } else if (view === 'top') {
      cam.position.set(0, 0, dist);
    } else if (view === 'side') {
      cam.position.set(dist, 0, 40);
    }
    ctrl.update();
  };

  const hasMultiParts = partsUrls && partsUrls.length > 1;

  return (
    <div className="relative w-full rounded-2xl overflow-hidden border border-slate-200 bg-white shadow-sm" style={{ height }}>
      {/* 3D WebGL Canvas */}
      <div
        ref={containerRef}
        className={`w-full h-full ${paintActive ? 'cursor-crosshair' : 'cursor-grab active:cursor-grabbing'}`}
      />

      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 bg-white/80 backdrop-blur-xs flex flex-col items-center justify-center gap-3 z-20">
          <div className="w-9 h-9 border-3 border-sky-200 border-t-sky-600 rounded-full animate-spin" />
          <div className="text-xs font-semibold text-slate-700 font-mono">Loading 3D Mesh in WebGL...</div>
        </div>
      )}

      {/* Error Overlay */}
      {error && (
        <div className="absolute inset-0 bg-white/95 flex flex-col items-center justify-center p-6 text-center z-20">
          <div className="text-rose-600 font-semibold mb-1 text-sm">Preview Unavailable</div>
          <div className="text-xs text-slate-500 max-w-sm">{error}</div>
        </div>
      )}

      {/* Top Left: Multi-Part View Mode Switcher Pills */}
      {hasMultiParts && (
        <div className="absolute top-3 left-3 flex flex-wrap items-center gap-1.5 bg-white/95 backdrop-blur border border-slate-200/90 p-1.5 rounded-xl z-10 shadow-xs">
          <button
            type="button"
            onClick={() => {
              setViewMode('exploded');
              setSoloIndex(-1);
              if (onSelectPart) onSelectPart(-1);
            }}
            className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
              viewMode === 'exploded' && soloIndex === -1
                ? 'bg-amber-500 text-slate-950 shadow-2xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            💥 Exploded View
          </button>

          <button
            type="button"
            onClick={() => {
              setViewMode('plate');
              setSoloIndex(-1);
              if (onSelectPart) onSelectPart(-1);
            }}
            className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
              viewMode === 'plate' && soloIndex === -1
                ? 'bg-sky-600 text-white shadow-2xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            🖨️ Print Bed View
          </button>

          <button
            type="button"
            onClick={() => {
              setViewMode('assembled');
              setSoloIndex(-1);
              if (onSelectPart) onSelectPart(-1);
            }}
            className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
              viewMode === 'assembled' && soloIndex === -1
                ? 'bg-slate-900 text-white shadow-2xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            🧩 Assembled View
          </button>
        </div>
      )}

      {/* Top Explode Gap Slider */}
      {hasMultiParts && viewMode === 'exploded' && soloIndex === -1 && (
        <div className="absolute top-14 left-3 flex items-center gap-2 bg-white/90 backdrop-blur border border-amber-200 px-3 py-1.5 rounded-xl z-10 shadow-xs">
          <Sliders className="w-3.5 h-3.5 text-amber-600" />
          <span className="text-[11px] font-mono text-slate-700 font-semibold">Separation:</span>
          <input
            type="range"
            min="5"
            max="60"
            step="1"
            value={explodeGap}
            onChange={(e) => setExplodeGap(parseInt(e.target.value))}
            className="w-24 accent-amber-500 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
          />
          <span className="text-[11px] font-mono text-amber-700 font-bold w-10 text-right">{explodeGap} mm</span>
        </div>
      )}

      {/* Paint-to-Cut Floating Controls Bar (When Single Model Mesh is Displayed) */}
      {!hasMultiParts && (
        <div className="absolute top-3 left-3 flex flex-wrap items-center gap-2 bg-white/95 backdrop-blur border border-slate-200 p-1.5 rounded-xl z-10 shadow-xs font-mono">
          <button
            type="button"
            onClick={() => setPaintActive(!paintActive)}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              paintActive
                ? 'bg-amber-500 text-slate-950 shadow-2xs ring-2 ring-amber-400'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
            }`}
          >
            <Paintbrush className="w-3.5 h-3.5" />
            <span>{paintActive ? '🎨 Paint Brush: ON' : '🎨 Paint-to-Cut Brush'}</span>
          </button>

          {paintActive && (
            <>
              <div className="flex items-center gap-1.5 px-2 border-l border-slate-200">
                <span className="text-[10px] text-slate-500">Radius:</span>
                <input
                  type="range"
                  min="4"
                  max="40"
                  step="1"
                  value={brushRadius}
                  onChange={(e) => setBrushRadius(parseInt(e.target.value))}
                  className="w-20 accent-amber-500 h-1 bg-slate-200 rounded cursor-pointer"
                />
                <span className="text-[11px] font-bold text-amber-700">{brushRadius}mm</span>
              </div>

              {paintedCount > 0 && (
                <>
                  <div className="px-2 py-0.5 rounded bg-amber-50 border border-amber-200 text-[11px] font-bold text-amber-800">
                    {paintedCount.toLocaleString()} faces
                  </div>
                  <button
                    type="button"
                    onClick={clearPaintedSelection}
                    className="p-1.5 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded cursor-pointer"
                    title="Clear Selection"
                  >
                    <Eraser className="w-3.5 h-3.5" />
                  </button>
                </>
              )}
            </>
          )}
        </div>
      )}

      {/* Top Right Floating Controls Bar */}
      <div className="absolute top-3 right-3 flex items-center gap-1 bg-white/95 backdrop-blur border border-slate-200 p-1 rounded-xl z-10 shadow-xs">
        <button
          onClick={() => setWireframe(!wireframe)}
          title="Toggle Wireframe"
          className={`p-1.5 rounded-lg text-xs transition-colors cursor-pointer ${
            wireframe ? 'bg-sky-50 text-sky-700 font-semibold' : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'
          }`}
        >
          <Layers className="w-4 h-4" />
        </button>

        <button
          onClick={() => {
            setShowBox(!showBox);
            if (bBoxHelperRef.current) bBoxHelperRef.current.visible = !showBox;
          }}
          title="Toggle Bounding Box"
          className={`p-1.5 rounded-lg text-xs transition-colors cursor-pointer ${
            showBox ? 'bg-sky-50 text-sky-700 font-semibold' : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'
          }`}
        >
          <Box className="w-4 h-4" />
        </button>

        <button
          onClick={() => {
            setShowGrid(!showGrid);
            if (gridHelperRef.current) gridHelperRef.current.visible = !showGrid;
          }}
          title="Toggle Plate Grid"
          className={`p-1.5 rounded-lg text-xs transition-colors cursor-pointer ${
            showGrid ? 'bg-sky-50 text-sky-700 font-semibold' : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'
          }`}
        >
          <Grid className="w-4 h-4" />
        </button>

        <button
          onClick={frameScene}
          title="Recenter & Frame Model"
          className="p-1.5 rounded-lg text-xs text-slate-500 hover:text-slate-800 hover:bg-slate-100 cursor-pointer"
        >
          <Maximize2 className="w-4 h-4" />
        </button>

        <div className="w-[1px] h-4 bg-slate-200 mx-1" />

        <button
          onClick={() => setCameraView('iso')}
          title="Isometric View"
          className="px-2 py-1 text-xs text-slate-700 hover:bg-slate-100 rounded-md font-mono cursor-pointer"
        >
          ISO
        </button>
        <button
          onClick={() => setCameraView('front')}
          title="Front View"
          className="px-2 py-1 text-xs text-slate-700 hover:bg-slate-100 rounded-md font-mono cursor-pointer"
        >
          F
        </button>
        <button
          onClick={() => setCameraView('top')}
          title="Top View"
          className="px-2 py-1 text-xs text-slate-700 hover:bg-slate-100 rounded-md font-mono cursor-pointer"
        >
          T
        </button>
        <button
          onClick={() => setCameraView('side')}
          title="Side View"
          className="px-2 py-1 text-xs text-slate-700 hover:bg-slate-100 rounded-md font-mono cursor-pointer"
        >
          S
        </button>
      </div>

      {/* Bottom Status Overlay */}
      <div className="absolute bottom-3 left-3 flex items-center gap-2 pointer-events-none z-10">
        <div className="bg-white/90 backdrop-blur border border-slate-200 text-xs text-slate-700 px-3 py-1.5 rounded-lg font-mono shadow-xs flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          Bambu A1 Bed: 256×256mm
          {triangles > 0 && <span className="text-slate-400">| {triangles.toLocaleString()} triangles</span>}
          {paintActive && (
            <span className="text-amber-800 font-bold bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
              Paint Mode Active (Left-Click to Paint • Right-Click to Rotate)
            </span>
          )}
          {soloIndex >= 0 && (
            <span className="text-sky-700 font-bold bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
              Solo View: Part {soloIndex + 1}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
