import { Eraser, Eye, EyeOff, Grid2X2, LocateFixed, Minus, Move, Plus, Send } from "lucide-react";
import { PointerEvent, useMemo, useRef, useState } from "react";
import type { GeometryDocument, GeometryObject } from "../types";

type DragTarget = { id: string; x: number; y: number };

function arcPolylinePoints(obj: GeometryObject, steps = 48) {
  const r = obj.radius || (obj.diameter || 0) / 2 || 1;
  const [cx, cy] = obj.center || [0, 0];
  let a1 = obj.start_angle ?? 0;
  let a2 = obj.end_angle ?? 180;
  if (obj.type === "semicircle") {
    const map = { up: [180, 360], down: [0, 180], left: [90, 270], right: [-90, 90] } as const;
    [a1, a2] = map[obj.direction || "up"];
  }
  return Array.from({ length: steps + 1 }, (_, i) => {
    const angle = a1 + ((a2 - a1) * i) / steps;
    return [
      cx + r * Math.cos(angle * Math.PI / 180),
      cy + r * Math.sin(angle * Math.PI / 180)
    ];
  });
}

function fmt(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(3);
}

function mainPoint(obj: GeometryObject): { point: number[]; label: string } | null {
  if (obj.center && ["circle", "semicircle", "ellipse", "arc", "slot"].includes(obj.type)) return { point: obj.center, label: "C" };
  if (obj.type === "line" && obj.start) return { point: obj.start, label: "S" };
  if (obj.type === "rectangle" && obj.x !== undefined && obj.y !== undefined) return { point: [obj.x || 0, obj.y || 0], label: "O" };
  if (obj.type === "parabola" && obj.vertex) return { point: obj.vertex, label: "V" };
  return null;
}

function mainPointMarker(obj: GeometryObject) {
  const main = mainPoint(obj);
  if (!main) return null;
  const [cx, cy] = main.point;
  return (
    <g key={`${obj.id}-main-point`}>
      <line x1={cx - 6} y1={cy} x2={cx + 6} y2={cy} stroke="#0891b2" strokeWidth="1.2" />
      <line x1={cx} y1={cy - 6} x2={cx} y2={cy + 6} stroke="#0891b2" strokeWidth="1.2" />
      <circle cx={cx} cy={cy} r={2.5} fill="#0891b2" />
    </g>
  );
}

function mainPointLabel(obj: GeometryObject) {
  const main = mainPoint(obj);
  if (!main) return null;
  const [cx, cy] = main.point;
  return <text key={`${obj.id}-main-point-label`} x={cx + 8} y={-cy - 8} className="svgLabel">{obj.id} {main.label}=({fmt(cx)},{fmt(cy)})</text>;
}

function arcEndpointLabels(obj: GeometryObject) {
  if (obj.type !== "arc" && obj.type !== "semicircle") return null;
  const r = obj.radius || (obj.diameter || 0) / 2 || 1;
  const [cx, cy] = obj.center || [0, 0];
  let a1 = obj.start_angle ?? 0;
  let a2 = obj.end_angle ?? 180;
  if (obj.type === "semicircle") {
    const map = { up: [180, 360], down: [0, 180], left: [90, 270], right: [-90, 90] } as const;
    [a1, a2] = map[obj.direction || "up"];
  }
  const p1 = [cx + r * Math.cos(a1 * Math.PI / 180), cy + r * Math.sin(a1 * Math.PI / 180)];
  const p2 = [cx + r * Math.cos(a2 * Math.PI / 180), cy + r * Math.sin(a2 * Math.PI / 180)];
  return (
    <g key={`${obj.id}-arc-point-labels`}>
      <text x={p1[0] + 5} y={-p1[1] - 5} className="svgLabel">start</text>
      <text x={p2[0] + 5} y={-p2[1] - 5} className="svgLabel">end</text>
    </g>
  );
}

function shapeElement(obj: GeometryObject) {
  const style = obj.style || { stroke: "#111827", stroke_width: 0.5, fill: "none" };
  const common = { stroke: style.stroke, strokeWidth: Math.min(style.stroke_width || 0.5, 0.8), fill: style.fill };
  if (obj.type === "circle") return <circle key={obj.id} cx={obj.center?.[0]} cy={obj.center?.[1]} r={obj.radius || (obj.diameter || 0) / 2} {...common} />;
  if (obj.type === "line") return <line key={obj.id} x1={obj.start?.[0]} y1={obj.start?.[1]} x2={obj.end?.[0]} y2={obj.end?.[1]} {...common} />;
  if (obj.type === "rectangle") return <rect key={obj.id} x={obj.x || 0} y={obj.y || 0} width={obj.width || 0} height={obj.height || 0} {...common} />;
  if (obj.type === "ellipse") return <ellipse key={obj.id} cx={obj.center?.[0]} cy={obj.center?.[1]} rx={(obj.major_axis || 0) / 2} ry={(obj.minor_axis || 0) / 2} transform={`rotate(${obj.rotation || 0} ${obj.center?.[0] || 0} ${obj.center?.[1] || 0})`} {...common} />;
  if (obj.type === "semicircle" || obj.type === "arc") return <polyline key={obj.id} points={arcPolylinePoints(obj).map((p) => p.join(",")).join(" ")} {...common} />;
  if (obj.type === "slot") {
    const [cx, cy] = obj.center || [0, 0];
    const total = obj.total_length || 100;
    const width = obj.width || 20;
    const r = width / 2;
    const straight = Math.max(total - width, 0);
    if (obj.orientation === "vertical") {
      const x1 = cx - r, x2 = cx + r, y1 = cy - straight / 2, y2 = cy + straight / 2;
      return <path key={obj.id} d={`M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y1} L ${x2} ${y2} A ${r} ${r} 0 0 1 ${x1} ${y2} Z`} {...common} />;
    }
    const x1 = cx - straight / 2, x2 = cx + straight / 2, y1 = cy - r, y2 = cy + r;
    return <path key={obj.id} d={`M ${x1} ${y1} L ${x2} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2} L ${x1} ${y2} A ${r} ${r} 0 0 1 ${x1} ${y1} Z`} {...common} />;
  }
  if (obj.type === "parabola") {
    const [vx, vy] = obj.vertex || [0, 0];
    const w = obj.width || 100, h = obj.height || 50;
    const points = Array.from({ length: 49 }, (_, i) => {
      const t = -1 + (2 * i) / 48;
      if (obj.direction === "left" || obj.direction === "right") {
        return [vx + h * t * t * (obj.direction === "right" ? 1 : -1), vy + (w / 2) * t];
      }
      return [vx + (w / 2) * t, vy + h * t * t * (obj.direction === "up" ? -1 : 1)];
    });
    return <polyline key={obj.id} points={points.map((p) => p.join(",")).join(" ")} {...common} />;
  }
  return null;
}

function bounds(doc: GeometryDocument) {
  if (!doc.objects.length) return [-120, -120, 520, 360];
  const boxes = doc.objects.map((obj) => objectBounds(obj));
  const x1 = Math.min(...boxes.map((b) => b[0]));
  const y1 = Math.min(...boxes.map((b) => b[1]));
  const x2 = Math.max(...boxes.map((b) => b[2]));
  const y2 = Math.max(...boxes.map((b) => b[3]));
  const pad = 80;
  return [x1 - pad, y1 - pad, x2 + pad, y2 + pad];
}

function objectBounds(obj: GeometryObject) {
  if (obj.type === "circle") {
    const [cx, cy] = obj.center || [0, 0];
    const r = obj.radius || (obj.diameter || 0) / 2 || 1;
    return [cx - r, cy - r, cx + r, cy + r];
  }
  if (obj.type === "line") {
    const s = obj.start || [0, 0], e = obj.end || [0, 0];
    return [Math.min(s[0], e[0]), Math.min(s[1], e[1]), Math.max(s[0], e[0]), Math.max(s[1], e[1])];
  }
  if (obj.type === "rectangle") return [obj.x || 0, obj.y || 0, (obj.x || 0) + (obj.width || 0), (obj.y || 0) + (obj.height || 0)];
  if (obj.type === "ellipse") {
    const [cx, cy] = obj.center || [0, 0];
    return [cx - (obj.major_axis || 0) / 2, cy - (obj.minor_axis || 0) / 2, cx + (obj.major_axis || 0) / 2, cy + (obj.minor_axis || 0) / 2];
  }
  if (obj.type === "arc" || obj.type === "semicircle") {
    const [cx, cy] = obj.center || [0, 0];
    const r = obj.radius || (obj.diameter || 0) / 2 || 1;
    return [cx - r, cy - r, cx + r, cy + r];
  }
  if (obj.type === "parabola") {
    const [vx, vy] = obj.vertex || [0, 0];
    const w = obj.width || 0, h = obj.height || 0;
    return obj.direction === "left" || obj.direction === "right"
      ? [vx + (obj.direction === "left" ? -h : 0), vy - w / 2, vx + (obj.direction === "right" ? h : 0), vy + w / 2]
      : [vx - w / 2, vy + (obj.direction === "up" ? -h : 0), vx + w / 2, vy + (obj.direction === "down" ? h : 0)];
  }
  if (obj.type === "slot") {
    const [cx, cy] = obj.center || [0, 0];
    const total = obj.total_length || 0, width = obj.width || 0;
    return obj.orientation === "vertical"
      ? [cx - width / 2, cy - total / 2, cx + width / 2, cy + total / 2]
      : [cx - total / 2, cy - width / 2, cx + total / 2, cy + width / 2];
  }
  return [0, 0, 0, 0];
}

function hitBounds(obj: GeometryObject) {
  const [x1, y1, x2, y2] = objectBounds(obj);
  const pad = 6;
  return [x1 - pad, y1 - pad, Math.max(x2 - x1 + pad * 2, 12), Math.max(y2 - y1 + pad * 2, 12)];
}

function movePoint(point: number[] | undefined, dx: number, dy: number) {
  return point ? [point[0] + dx, point[1] + dy] : point;
}

function moveObject(obj: GeometryObject, dx: number, dy: number): GeometryObject {
  return {
    ...obj,
    center: movePoint(obj.center, dx, dy),
    start: movePoint(obj.start, dx, dy),
    end: movePoint(obj.end, dx, dy),
    vertex: movePoint(obj.vertex, dx, dy),
    x: obj.x !== undefined ? obj.x + dx : obj.x,
    y: obj.y !== undefined ? obj.y + dy : obj.y
  };
}

function moveShape(doc: GeometryDocument, id: string, dx: number, dy: number): GeometryDocument {
  return {
    ...doc,
    objects: doc.objects.map((obj) => obj.id === id ? moveObject(obj, dx, dy) : obj)
  };
}

export default function DrawingCanvas({
  geometry,
  prompt,
  onPromptChange,
  onSendPrompt,
  onToggleDimensions,
  onGeometryChange
}: {
  geometry: GeometryDocument;
  prompt: string;
  onPromptChange: (prompt: string) => void;
  onSendPrompt: (prompt: string) => void;
  onToggleDimensions: () => void;
  onGeometryChange: (geometry: GeometryDocument) => void;
}) {
  const [zoom, setZoom] = useState(1);
  const [showCoords, setShowCoords] = useState(true);
  const [showGrid, setShowGrid] = useState(true);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const drag = useRef<{ x: number; y: number } | null>(null);
  const shapeDrag = useRef<DragTarget | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const box = useMemo(() => bounds(geometry), [geometry]);
  const cadX = box[0] + pan.x;
  const cadY = box[1] + pan.y;
  const w = (box[2] - box[0]) / zoom;
  const h = (box[3] - box[1]) / zoom;
  const viewX = cadX;
  const viewY = -(cadY + h);

  function fit() {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }

  function onPointerDown(event: PointerEvent<SVGSVGElement>) {
    if (shapeDrag.current) return;
    drag.current = { x: event.clientX, y: event.clientY };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function onPointerMove(event: PointerEvent<SVGSVGElement>) {
    if (shapeDrag.current && svgRef.current) {
      const rect = svgRef.current.getBoundingClientRect();
      const dx = ((event.clientX - shapeDrag.current.x) / rect.width) * w;
      const dy = -((event.clientY - shapeDrag.current.y) / rect.height) * h;
      if (dx || dy) {
        onGeometryChange(moveShape(geometry, shapeDrag.current.id, dx, dy));
      }
      shapeDrag.current = { id: shapeDrag.current.id, x: event.clientX, y: event.clientY };
      return;
    }
    if (!drag.current || !svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const dx = ((event.clientX - drag.current.x) / rect.width) * w;
    const dy = ((event.clientY - drag.current.y) / rect.height) * h;
    setPan((value) => ({ x: value.x - dx, y: value.y + dy }));
    drag.current = { x: event.clientX, y: event.clientY };
  }

  function onPointerEnd() {
    drag.current = null;
    shapeDrag.current = null;
  }

  function onShapePointerDown(event: PointerEvent<SVGGElement>, id: string) {
    if (!event.ctrlKey) return;
    event.stopPropagation();
    shapeDrag.current = { id, x: event.clientX, y: event.clientY };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function submitPrompt() {
    if (!prompt.trim()) return;
    onSendPrompt(prompt.trim());
    onPromptChange("");
  }

  return (
    <section className="relative h-[calc(100vh-188px)] min-h-[560px] overflow-hidden rounded border border-slate-300 bg-slate-100 shadow-sm dark:border-slate-800 dark:bg-slate-950">
      <div className="absolute left-4 top-4 z-10 flex flex-wrap items-center gap-2 rounded border border-slate-300 bg-white/95 p-2 shadow-sm backdrop-blur dark:border-slate-700 dark:bg-slate-900/95">
        <button className="grid h-9 w-9 place-items-center rounded border border-slate-300 bg-slate-50 text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700" title="Zoom in" onClick={() => setZoom((z) => Math.min(6, z + 0.25))}><Plus size={16} /></button>
        <button className="grid h-9 w-9 place-items-center rounded border border-slate-300 bg-slate-50 text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700" title="Zoom out" onClick={() => setZoom((z) => Math.max(0.25, z - 0.25))}><Minus size={16} /></button>
        <button className="grid h-9 w-9 place-items-center rounded border border-slate-300 bg-slate-50 text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700" title="Fit to screen" onClick={fit}><LocateFixed size={16} /></button>
        <button className="grid h-9 w-9 place-items-center rounded border border-slate-300 bg-slate-50 text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700" title="Pan canvas by dragging"><Move size={16} /></button>
        <button className={`grid h-9 w-9 place-items-center rounded border text-slate-700 hover:bg-slate-200 dark:text-slate-200 dark:hover:bg-slate-700 ${showGrid ? "border-blue-400 bg-blue-50 dark:border-blue-500 dark:bg-blue-950" : "border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-slate-800"}`} title="Toggle grid" onClick={() => setShowGrid((v) => !v)}><Grid2X2 size={16} /></button>
        <button className="grid h-9 w-9 place-items-center rounded border border-slate-300 bg-slate-50 text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700" title="Show dimensions" onClick={onToggleDimensions}>{geometry.dimensions.show ? <Eye size={16} /> : <EyeOff size={16} />}</button>
        <button className="h-9 rounded border border-slate-300 bg-slate-50 px-3 text-xs font-semibold text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700" onClick={() => setShowCoords((v) => !v)}>XY</button>
        <span className="hidden border-l border-slate-300 pl-3 text-xs text-slate-500 dark:border-slate-700 dark:text-slate-400 sm:inline">Zoom {(zoom * 100).toFixed(0)}%</span>
      </div>
      <svg ref={svgRef} className="h-full w-full cursor-grab active:cursor-grabbing" viewBox={`${viewX} ${viewY} ${w} ${h}`} onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerEnd} onPointerLeave={onPointerEnd}>
        <defs>
          <pattern id="grid" width="1" height="1" patternUnits="userSpaceOnUse"><path d="M 1 0 L 0 0 0 1" fill="none" stroke="#e2e8f0" strokeWidth="0.08" /></pattern>
          <pattern id="majorGrid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="#94a3b8" strokeWidth="0.18" /></pattern>
        </defs>
        <g transform="scale(1 -1)">
          <rect x="-50000" y="-50000" width="100000" height="100000" fill="#f8fafc" />
          {showGrid && <rect x="-50000" y="-50000" width="100000" height="100000" fill="url(#grid)" />}
          {showGrid && <rect x="-50000" y="-50000" width="100000" height="100000" fill="url(#majorGrid)" />}
          <line x1="-50000" y1="0" x2="50000" y2="0" stroke="#ef4444" strokeWidth="1.4" />
          <line x1="0" y1="-50000" x2="0" y2="50000" stroke="#2563eb" strokeWidth="1.4" />
          {geometry.objects.map((obj) => {
            const [hx, hy, hw, hh] = hitBounds(obj);
            return (
              <g key={`${obj.id}-interactive`} onPointerDown={(event) => onShapePointerDown(event, obj.id)} className="cursor-move">
                <rect x={hx} y={hy} width={hw} height={hh} fill="transparent" pointerEvents="all" />
                {shapeElement(obj)}
              </g>
            );
          })}
          {showCoords && geometry.objects.map(mainPointMarker)}
        </g>
        {showCoords && geometry.objects.map(mainPointLabel)}
        {showCoords && geometry.objects.map(arcEndpointLabels)}
        {geometry.dimensions.show && geometry.objects.map((obj, i) => (
          <g key={`${obj.id}-label`}>
            <text x={viewX + 20} y={viewY + 26 + i * 14} className="svgLabel">{obj.id} {obj.type}</text>
          </g>
        ))}
        {showCoords && <text x={10} y={10} className="svgLabel">0,0</text>}
      </svg>
      <div className="absolute bottom-4 left-4 z-10 w-[min(720px,calc(100%-2rem))] rounded border border-slate-300 bg-white/95 p-2 shadow-sm backdrop-blur dark:border-slate-700 dark:bg-slate-900/95">
        <div className="grid grid-cols-[1fr_42px] gap-2 sm:grid-cols-[1fr_42px_42px]">
          <textarea
            className="min-h-[44px] resize-none rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-950 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            value={prompt}
            onChange={(event) => onPromptChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                submitPrompt();
              }
            }}
            placeholder="Type a drawing command..."
          />
          <button className="grid h-[44px] place-items-center rounded bg-blue-600 text-white hover:bg-blue-700" title="Send command" onClick={submitPrompt}><Send size={18} /></button>
          <button className="hidden h-[44px] place-items-center rounded border border-slate-300 bg-white text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 sm:grid" title="Clear command" onClick={() => onPromptChange("")}><Eraser size={18} /></button>
        </div>
      </div>
      <div className="absolute bottom-20 right-4 rounded border border-slate-300 bg-white/95 px-3 py-2 text-xs text-slate-600 shadow-sm dark:border-slate-700 dark:bg-slate-900/95 dark:text-slate-300">
        Drag canvas to pan · Fit resets view
      </div>
    </section>
  );
}
