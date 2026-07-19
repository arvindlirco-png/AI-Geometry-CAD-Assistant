import { Download, FilePlus2, FolderOpen, HelpCircle, Hexagon, Save, Settings } from "lucide-react";

interface Props {
  onNew: () => void;
  onOpen: () => void;
  onSave: () => void;
  onExport: () => void;
  onSettings: () => void;
  onHelp: () => void;
}

const items = [
  ["New Drawing", FilePlus2, "onNew"],
  ["Open Drawing", FolderOpen, "onOpen"],
  ["Save Drawing", Save, "onSave"],
  ["Export", Download, "onExport"],
  ["Settings", Settings, "onSettings"],
  ["Help / Examples", HelpCircle, "onHelp"]
] as const;

export default function Sidebar(props: Props) {
  return (
    <aside className="flex min-h-screen flex-col border-r border-slate-900 bg-slate-950 px-3 py-4 text-white">
      <div className="mb-5 flex h-12 items-center justify-center gap-3 rounded border border-slate-700 bg-slate-900 lg:justify-start lg:px-3">
        <Hexagon size={22} className="text-cyan-400" />
        <div className="hidden min-w-0 lg:block">
          <div className="truncate text-sm font-semibold">AI ChatCAD</div>
          <div className="text-xs text-slate-400">Engineering tools</div>
        </div>
      </div>
      <div className="flex flex-1 flex-col gap-1">
      {items.map(([label, Icon, key]) => (
        <button key={label} className="group flex h-11 items-center justify-center gap-3 rounded border border-transparent px-3 text-slate-300 transition hover:border-slate-700 hover:bg-slate-900 hover:text-white lg:justify-start" onClick={props[key]} title={label}>
          <Icon size={18} />
          <span className="hidden text-sm font-medium lg:inline">{label}</span>
        </button>
      ))}
      </div>
      <div className="hidden rounded border border-slate-800 bg-slate-900 p-3 text-xs leading-5 text-slate-400 lg:block">
        Local CAD workstation<br />Backend port 8020
      </div>
    </aside>
  );
}
