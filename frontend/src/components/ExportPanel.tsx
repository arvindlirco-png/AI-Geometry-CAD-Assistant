import { Braces, Download, FileCode2, FileImage, FileJson, FileSpreadsheet, FileText } from "lucide-react";
import { exportFile } from "../api";
import type { GeometryDocument } from "../types";

const formats = [
  ["svg", FileCode2, "Vector drawing"],
  ["png", FileImage, "Raster image"],
  ["pdf", FileText, "Drawing sheet"],
  ["dxf", Braces, "CAD exchange"],
  ["json", FileJson, "Geometry data"],
  ["csv", FileSpreadsheet, "Dimension table"]
] as const;

export default function ExportPanel({ geometry }: { geometry: GeometryDocument }) {
  return (
    <div className="min-h-[calc(100vh-188px)] rounded border border-slate-300 bg-slate-50 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-4">
        <div className="text-sm font-semibold text-slate-950 dark:text-white">Export Drawing</div>
        <div className="text-xs text-slate-500 dark:text-slate-400">Generate production files from the current geometry document</div>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {formats.map(([format, Icon, description]) => (
        <button key={format} className="group flex min-h-28 items-center justify-between rounded border border-slate-300 bg-white p-4 text-left shadow-sm transition hover:border-blue-400 hover:shadow-md dark:border-slate-700 dark:bg-slate-950 dark:hover:border-blue-500" onClick={() => exportFile(format, geometry)}>
          <span className="flex items-center gap-3">
            <span className="grid h-11 w-11 place-items-center rounded border border-slate-300 bg-slate-100 text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"><Icon size={20} /></span>
            <span>
              <span className="block text-sm font-semibold text-slate-950 dark:text-white">Export {format.toUpperCase()}</span>
              <span className="block text-xs text-slate-500 dark:text-slate-400">{description}</span>
            </span>
          </span>
          <Download size={18} className="text-slate-400 group-hover:text-blue-600" />
        </button>
      ))}
      </div>
    </div>
  );
}
