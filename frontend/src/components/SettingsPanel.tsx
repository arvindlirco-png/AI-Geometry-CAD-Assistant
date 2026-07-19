import type { Unit } from "../types";

interface Props {
  backendUrl: string;
  unit: Unit;
  theme: "light" | "dark";
  onBackendUrl: (value: string) => void;
  onUnit: (value: Unit) => void;
  onTheme: (value: "light" | "dark") => void;
}

export default function SettingsPanel({ backendUrl, unit, theme, onBackendUrl, onUnit, onTheme }: Props) {
  const inputClass = "mt-1 h-10 rounded border border-slate-300 bg-white px-3 text-sm text-slate-950 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100";
  return (
    <div className="min-h-[calc(100vh-188px)] rounded border border-slate-300 bg-slate-50 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-4">
        <div className="text-sm font-semibold text-slate-950 dark:text-white">Application Settings</div>
        <div className="text-xs text-slate-500 dark:text-slate-400">Connection, units, and workspace preferences</div>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Backend URL<input className={inputClass} value={backendUrl} onChange={(event) => onBackendUrl(event.target.value)} /></label>
        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Ollama URL<input className={inputClass} value="http://127.0.0.1:11434" readOnly /></label>
        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Model name<input className={inputClass} value="qwen2.5-coder:7b" readOnly /></label>
        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Unit<select className={inputClass} value={unit} onChange={(event) => onUnit(event.target.value as Unit)}><option>mm</option><option>cm</option><option>inch</option></select></label>
        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Canvas size<input className={inputClass} value="Responsive viewport" readOnly /></label>
        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Grid spacing<input className={inputClass} value="1 mm / 10 mm major" readOnly /></label>
        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Dimension font size<input className={inputClass} value="12" readOnly /></label>
        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Theme<select className={inputClass} value={theme} onChange={(event) => onTheme(event.target.value as "light" | "dark")}><option>light</option><option>dark</option></select></label>
      </div>
    </div>
  );
}
