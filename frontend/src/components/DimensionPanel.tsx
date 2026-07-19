import type { GeometryDocument } from "../types";

function calcRows(geometry: GeometryDocument) {
  return geometry.objects.map((obj) => {
    const row: Record<string, unknown> = { id: obj.id, type: obj.type };
    if (obj.type === "circle") {
      const r = obj.radius || (obj.diameter || 0) / 2;
      Object.assign(row, { radius: r, diameter: r * 2, area: Math.PI * r * r, perimeter: 2 * Math.PI * r, center: obj.center });
    }
    if (obj.type === "line" && obj.start && obj.end) {
      const dx = obj.end[0] - obj.start[0], dy = obj.end[1] - obj.start[1];
      Object.assign(row, { length: Math.hypot(dx, dy), angle: Math.atan2(dy, dx) * 180 / Math.PI, start: obj.start, end: obj.end });
    }
    if (obj.type === "rectangle") Object.assign(row, { width: obj.width, height: obj.height, area: (obj.width || 0) * (obj.height || 0), perimeter: 2 * ((obj.width || 0) + (obj.height || 0)) });
    if (obj.type === "ellipse") Object.assign(row, { major_axis: obj.major_axis, minor_axis: obj.minor_axis, area: Math.PI * ((obj.major_axis || 0) / 2) * ((obj.minor_axis || 0) / 2), center: obj.center });
    if (obj.type === "semicircle") {
      const r = obj.radius || 0;
      Object.assign(row, { radius: r, diameter: r * 2, area: Math.PI * r * r / 2, arc_length: Math.PI * r, chord_length: 2 * r, center: obj.center });
    }
    if (obj.type === "arc") {
      const r = obj.radius || 0;
      const sweep = Math.abs((obj.end_angle || 0) - (obj.start_angle || 0));
      Object.assign(row, { radius: r, start_angle: obj.start_angle, end_angle: obj.end_angle, angle: sweep, arc_length: (sweep * Math.PI / 180) * r, chord_length: 2 * r * Math.sin((sweep * Math.PI / 180) / 2), center: obj.center });
    }
    if (obj.type === "parabola") Object.assign(row, { width: obj.width, height: obj.height, vertex: obj.vertex });
    if (obj.type === "slot") {
      const straight = Math.max((obj.total_length || 0) - (obj.width || 0), 0);
      Object.assign(row, { length: obj.total_length, width: obj.width, area: straight * (obj.width || 0) + Math.PI * ((obj.width || 0) / 2) ** 2, perimeter: 2 * straight + Math.PI * (obj.width || 0) });
    }
    return row;
  });
}

export default function DimensionPanel({ geometry }: { geometry: GeometryDocument }) {
  const rows = calcRows(geometry);
  const keys = Array.from(new Set(rows.flatMap((row) => Object.keys(row))));
  return (
    <div className="min-h-[calc(100vh-188px)] rounded border border-slate-300 bg-slate-50 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-4 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="text-sm font-semibold text-slate-950 dark:text-white">Calculated Dimensions</div>
          <div className="text-xs text-slate-500 dark:text-slate-400">{rows.length} measured shape{rows.length === 1 ? "" : "s"}</div>
        </div>
      </div>
      <div className="mb-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {rows.map((row) => {
          const primary = Object.entries(row).filter(([key]) => !["id", "type", "center", "start", "end", "vertex"].includes(key)).slice(0, 4);
          return (
            <article key={String(row.id)} className="rounded border border-slate-300 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-950">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-slate-950 dark:text-white">{String(row.id)}</div>
                  <div className="text-xs uppercase tracking-normal text-slate-500 dark:text-slate-400">{String(row.type)}</div>
                </div>
                <span className="rounded border border-slate-300 bg-slate-100 px-2 py-1 text-xs text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">mm</span>
              </div>
              <dl className="grid grid-cols-2 gap-2">
                {primary.map(([key, value]) => (
                  <div key={key} className="rounded border border-slate-200 bg-slate-50 p-2 dark:border-slate-800 dark:bg-slate-900">
                    <dt className="text-[11px] uppercase tracking-normal text-slate-500 dark:text-slate-400">{key}</dt>
                    <dd className="mt-1 truncate text-sm font-semibold text-slate-900 dark:text-slate-100">{format(value)}</dd>
                  </div>
                ))}
              </dl>
            </article>
          );
        })}
      </div>
      <div className="overflow-auto rounded border border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-950">
        <table className="w-full border-collapse text-sm">
          <thead><tr>{keys.map((key) => <th className="sticky top-0 border-b border-slate-300 bg-slate-100 px-3 py-2 text-left text-xs font-semibold uppercase tracking-normal text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300" key={key}>{key}</th>)}</tr></thead>
          <tbody>
            {rows.map((row) => (
              <tr className="border-b border-slate-200 last:border-0 dark:border-slate-800" key={String(row.id)}>{keys.map((key) => <td className="px-3 py-2 text-slate-700 dark:text-slate-300" key={key}>{format(row[key])}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function format(value: unknown) {
  if (typeof value === "number") return Number.isFinite(value) ? value.toFixed(3) : "";
  if (Array.isArray(value)) return value.join(", ");
  return value ? String(value) : "";
}
