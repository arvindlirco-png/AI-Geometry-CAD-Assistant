import type { GeometryDocument } from "../types";

interface Props {
  geometry: GeometryDocument;
  json: string;
  onJson: (value: string) => void;
  onApply: () => void;
}

export default function ShapeTable({ geometry, json, onJson, onApply }: Props) {
  return (
    <section className="grid min-h-[calc(100vh-188px)] gap-4 xl:grid-cols-[minmax(420px,0.9fr)_minmax(420px,1.1fr)]">
      <div className="rounded border border-slate-300 bg-slate-50 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="mb-3">
          <div className="text-sm font-semibold text-slate-950 dark:text-white">Shape Data</div>
          <div className="text-xs text-slate-500 dark:text-slate-400">Object-level geometry parameters</div>
        </div>
        <div className="overflow-auto rounded border border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-950">
          <table className="w-full border-collapse text-sm">
            <thead><tr><th className="border-b border-slate-300 bg-slate-100 px-3 py-2 text-left text-xs uppercase text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">ID</th><th className="border-b border-slate-300 bg-slate-100 px-3 py-2 text-left text-xs uppercase text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">Type</th><th className="border-b border-slate-300 bg-slate-100 px-3 py-2 text-left text-xs uppercase text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">Primary data</th></tr></thead>
            <tbody>
              {geometry.objects.map((obj) => (
                <tr className="border-b border-slate-200 last:border-0 dark:border-slate-800" key={obj.id}>
                  <td className="px-3 py-2 font-semibold text-slate-900 dark:text-slate-100">{obj.id}</td>
                  <td className="px-3 py-2 text-slate-700 dark:text-slate-300">{obj.type}</td>
                  <td className="max-w-[460px] truncate px-3 py-2 font-mono text-xs text-slate-600 dark:text-slate-400">{JSON.stringify(obj)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="flex min-h-0 flex-col rounded border border-slate-300 bg-slate-50 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <div className="text-sm font-semibold text-slate-950 dark:text-white">Editable Geometry JSON</div>
            <div className="text-xs text-slate-500 dark:text-slate-400">Apply changes directly to the drawing model</div>
          </div>
          <button className="inline-flex h-9 items-center rounded bg-blue-600 px-3 text-sm font-semibold text-white hover:bg-blue-700" onClick={onApply}>Apply JSON</button>
        </div>
        <textarea className="min-h-[520px] flex-1 resize-none rounded border border-slate-300 bg-slate-950 p-3 font-mono text-xs leading-5 text-slate-100 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700" value={json} onChange={(event) => onJson(event.target.value)} spellCheck={false} />
      </div>
    </section>
  );
}
