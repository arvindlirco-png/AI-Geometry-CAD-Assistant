import { useEffect, useMemo, useState } from "react";
import { Bot, Circle, Database, FileDown, FileSearch, MessageSquareText, Moon, Ruler, Settings, Shapes, Sun, Table2 } from "lucide-react";
import { aiStatus, defaultBackendUrl, downloadBase64File, health, listDrawings, openDrawing, parsePrompt, processDrawingFile, saveDrawing, setBackendUrl } from "./api";
import ChatPanel from "./components/ChatPanel";
import DimensionPanel from "./components/DimensionPanel";
import DrawingAssistantPanel from "./components/DrawingAssistantPanel";
import DrawingCanvas from "./components/DrawingCanvas";
import ExportPanel from "./components/ExportPanel";
import SettingsPanel from "./components/SettingsPanel";
import ShapeTable from "./components/ShapeTable";
import Sidebar from "./components/Sidebar";
import type { ChatMessage, GeometryDocument, Unit } from "./types";

const emptyGeometry: GeometryDocument = {
  unit: "mm",
  drawing_name: "Untitled Drawing",
  objects: [],
  dimensions: { show: true }
};

const tabs = ["Chat", "Drawing Assistant", "Drawing", "Dimensions", "Shape Data", "Export", "Settings"] as const;
type Tab = typeof tabs[number];

const tabIcons = {
  Chat: MessageSquareText,
  "Drawing Assistant": FileSearch,
  Drawing: Shapes,
  Dimensions: Ruler,
  "Shape Data": Table2,
  Export: FileDown,
  Settings
} satisfies Record<Tab, typeof MessageSquareText>;

export default function App() {
  const [geometry, setGeometry] = useState<GeometryDocument>(emptyGeometry);
  const [tab, setTab] = useState<Tab>("Chat");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [drawingAssistantMessages, setDrawingAssistantMessages] = useState<ChatMessage[]>([]);
  const [chatDraft, setChatDraft] = useState("");
  const [drawingAssistantDraft, setDrawingAssistantDraft] = useState("");
  const [pendingJson, setPendingJson] = useState(JSON.stringify(emptyGeometry, null, 2));
  const [clarificationPrompt, setClarificationPrompt] = useState<string | null>(null);
  const [backend, setBackend] = useState("checking");
  const [ai, setAi] = useState("checking");
  const [backendUrl, setUrl] = useState(localStorage.getItem("backendUrl") || defaultBackendUrl());
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    health().then(() => setBackend("online")).catch(() => setBackend("offline"));
    aiStatus().then((status) => setAi(status.connected ? `Ollama ${status.selected_model || "no model"}` : "offline fallback")).catch(() => setAi("offline fallback"));
  }, []);

  useEffect(() => {
    setPendingJson(JSON.stringify(geometry, null, 2));
  }, [geometry]);

  const bodyClass = useMemo(() => `${theme} min-h-screen`, [theme]);

  async function sendPrompt(prompt: string) {
    setMessages((m) => [...m, { role: "user", content: prompt }]);
    const effectivePrompt = clarificationPrompt ? `${clarificationPrompt} ${prompt}` : prompt;
    let contextGeometry = geometry;
    try {
      const draft = JSON.parse(pendingJson) as GeometryDocument;
      if (draft && Array.isArray(draft.objects)) {
        contextGeometry = draft;
      }
    } catch {
      contextGeometry = geometry;
    }
    const res = await parsePrompt(effectivePrompt, contextGeometry);
    if (!res.success) {
      setClarificationPrompt(effectivePrompt);
      setMessages((m) => [...m, { role: "assistant", content: res.question || "I need more information to create valid geometry." }]);
      return;
    }
    setClarificationPrompt(null);
    if (!res.geometry) {
      setMessages((m) => [...m, { role: "assistant", content: "Parser returned no geometry." }]);
      return;
    }
    const parsedGeometry = res.geometry;
    setPendingJson(JSON.stringify(parsedGeometry, null, 2));
    if (res.action === "export" && res.export_format) {
      const format = res.export_format;
      setMessages((m) => [...m, { role: "assistant", content: `${res.source}: export requested for ${format.toUpperCase()}. Open the Export tab to download it.` }]);
      setTab("Export");
      return;
    }
    const visibleWarnings = res.warnings.filter((warning) => !warning.toLowerCase().includes("ollama"));
    const warningText = visibleWarnings.length ? ` ${visibleWarnings.join(" ")}` : "";
    setMessages((m) => [...m, { role: "assistant", content: `${res.source}: parsed ${parsedGeometry.objects.length} shape(s).${warningText}` }]);
  }

  async function handleDrawingFile(action: "summarize" | "edit", file: File, instruction: string) {
    const userText = action === "edit" ? `Edit uploaded drawing ${file.name}: ${instruction}` : `Summarize uploaded drawing ${file.name}`;
    setDrawingAssistantMessages((m) => [...m, { role: "user", content: userText }]);
    try {
      const res = await processDrawingFile(action, file, instruction);
      const editText = res.edits.length
        ? ` Edits: ${res.edits.map((edit) => `${edit.old_value} -> ${edit.new_value}`).join("; ")}.`
        : "";
      const warningText = res.warnings.length ? ` Warnings: ${res.warnings.join(" ")}` : "";
      setDrawingAssistantMessages((m) => [...m, { role: "assistant", content: `${res.source}: ${res.summary}${editText}${warningText}` }]);
      if (res.edited_base64 && res.edited_filename) {
        downloadBase64File(res.edited_filename, res.edited_content_type || "application/octet-stream", res.edited_base64);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Drawing file processing failed.";
      setDrawingAssistantMessages((m) => [...m, { role: "assistant", content: message }]);
    }
  }

  function approve(json: string) {
    try {
      const parsed = JSON.parse(json) as GeometryDocument;
      setGeometry(parsed);
      setTab("Drawing");
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "JSON is invalid. Fix it before approving." }]);
    }
  }

  function updateBackend(value: string) {
    setUrl(value);
    setBackendUrl(value);
  }

  async function openSaved() {
    const drawings = await listDrawings();
    if (!drawings.length) {
      setMessages((m) => [...m, { role: "assistant", content: "No saved drawings found." }]);
      setTab("Chat");
      return;
    }
    const row = await openDrawing(drawings[0].id);
    setGeometry(row.geometry);
    setMessages(row.chat_history || []);
    setTab("Drawing");
  }

  async function persist() {
    const name = geometry.drawing_name || "Untitled Drawing";
    const row = await saveDrawing(name, geometry, messages);
    setMessages((m) => [...m, { role: "assistant", content: `Saved drawing #${row.id}.` }]);
  }

  return (
    <main className={bodyClass}>
      <div className="grid min-h-screen grid-cols-[76px_minmax(0,1fr)] bg-slate-200 text-slate-950 dark:bg-slate-950 dark:text-slate-100 lg:grid-cols-[248px_minmax(0,1fr)]">
        <Sidebar onNew={() => { setGeometry(emptyGeometry); setMessages([]); setDrawingAssistantMessages([]); setChatDraft(""); setDrawingAssistantDraft(""); setClarificationPrompt(null); setTab("Chat"); }} onOpen={openSaved} onSave={persist} onExport={() => setTab("Export")} onSettings={() => setTab("Settings")} onHelp={() => setTab("Chat")} />
        <section className="flex min-w-0 flex-col">
          <header className="border-b border-slate-300 bg-slate-50/95 px-4 py-3 dark:border-slate-800 dark:bg-slate-900/95 lg:px-6">
            <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
              <div className="min-w-0">
                <div className="flex items-center gap-3">
                  <h1 className="m-0 truncate text-xl font-semibold tracking-normal text-slate-950 dark:text-white">AI Geometry CAD Assistant</h1>
                  <span className="rounded border border-slate-300 bg-white px-2 py-1 text-xs font-semibold uppercase tracking-normal text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">CAD Workspace</span>
                </div>
                <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                  <span className="truncate">{geometry.drawing_name}</span>
                  <span>{geometry.objects.length} object{geometry.objects.length === 1 ? "" : "s"}</span>
                  <span>Unit: {geometry.unit}</span>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <select className="h-9 rounded border border-slate-300 bg-white px-3 text-sm text-slate-900 shadow-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100" value={geometry.unit} onChange={(event) => setGeometry({ ...geometry, unit: event.target.value as Unit })}><option>mm</option><option>cm</option><option>inch</option></select>
                <button className="inline-flex h-9 items-center gap-2 rounded border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} title="Toggle theme">
                  {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
                  <span className="hidden sm:inline">{theme === "dark" ? "Light" : "Dark"}</span>
                </button>
                <span className="inline-flex h-9 items-center gap-2 rounded border border-slate-300 bg-white px-3 text-sm text-slate-700 shadow-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"><Circle size={10} fill={backend === "online" ? "#16a34a" : "#ef4444"} className="text-transparent" />Backend {backend}</span>
                <span className="inline-flex h-9 items-center gap-2 rounded border border-slate-300 bg-white px-3 text-sm text-slate-700 shadow-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"><Circle size={10} fill={ai.includes("Ollama") ? "#16a34a" : "#f59e0b"} className="text-transparent" />{ai}</span>
              </div>
            </div>
            <div className="mt-3 grid gap-2 text-xs text-slate-600 dark:text-slate-400 sm:grid-cols-3">
              <div className="flex items-center gap-2 rounded border border-slate-300 bg-white px-3 py-2 dark:border-slate-800 dark:bg-slate-900"><Database size={14} />API {backendUrl}</div>
              <div className="flex items-center gap-2 rounded border border-slate-300 bg-white px-3 py-2 dark:border-slate-800 dark:bg-slate-900"><Bot size={14} />Parser {ai.includes("Ollama") ? "Ollama assisted" : "rule fallback"}</div>
              <div className="flex items-center gap-2 rounded border border-slate-300 bg-white px-3 py-2 dark:border-slate-800 dark:bg-slate-900"><Ruler size={14} />Dimensions {geometry.dimensions.show ? "visible" : "hidden"}</div>
            </div>
          </header>
          <nav className="flex gap-1 overflow-x-auto border-b border-slate-300 bg-slate-100 px-3 pt-2 dark:border-slate-800 dark:bg-slate-900 lg:px-6">
            {tabs.map((name) => {
              const Icon = tabIcons[name];
              return (
                <button key={name} className={`inline-flex shrink-0 items-center gap-2 rounded-t border px-3 py-2 text-sm font-medium transition ${tab === name ? "border-slate-300 border-b-slate-50 bg-slate-50 text-slate-950 dark:border-slate-700 dark:border-b-slate-950 dark:bg-slate-950 dark:text-white" : "border-transparent text-slate-600 hover:bg-white/60 hover:text-slate-950 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"}`} onClick={() => setTab(name)}>
                  <Icon size={16} />{name}
                </button>
              );
            })}
          </nav>
          <div className="min-h-0 flex-1 p-3 lg:p-5">
            {tab === "Chat" && <ChatPanel messages={messages} pendingJson={pendingJson} prompt={chatDraft} onPromptChange={setChatDraft} onSend={sendPrompt} onApprove={approve} onPendingJson={setPendingJson} onClear={() => { setMessages([]); setChatDraft(""); setClarificationPrompt(null); }} />}
            {tab === "Drawing Assistant" && <DrawingAssistantPanel messages={drawingAssistantMessages} prompt={drawingAssistantDraft} onPromptChange={setDrawingAssistantDraft} onFileAction={handleDrawingFile} onClear={() => { setDrawingAssistantMessages([]); setDrawingAssistantDraft(""); }} />}
            {tab === "Drawing" && <DrawingCanvas geometry={geometry} prompt={chatDraft} onPromptChange={setChatDraft} onSendPrompt={sendPrompt} onGeometryChange={setGeometry} onToggleDimensions={() => setGeometry({ ...geometry, dimensions: { ...geometry.dimensions, show: !geometry.dimensions.show } })} />}
            {tab === "Dimensions" && <DimensionPanel geometry={geometry} />}
            {tab === "Shape Data" && <ShapeTable geometry={geometry} json={pendingJson} onJson={setPendingJson} onApply={() => approve(pendingJson)} />}
            {tab === "Export" && <ExportPanel geometry={geometry} />}
            {tab === "Settings" && <SettingsPanel backendUrl={backendUrl} unit={geometry.unit} theme={theme} onBackendUrl={updateBackend} onUnit={(unit) => setGeometry({ ...geometry, unit })} onTheme={setTheme} />}
          </div>
        </section>
      </div>
    </main>
  );
}
