import { Eraser, FileText, Paperclip, Send, Wand2 } from "lucide-react";
import { useRef, useState } from "react";
import type { ChatMessage } from "../types";

interface Props {
  messages: ChatMessage[];
  prompt: string;
  onPromptChange: (prompt: string) => void;
  onFileAction: (action: "summarize" | "edit", file: File, instruction: string) => void;
  onClear: () => void;
}

export default function DrawingAssistantPanel({ messages, prompt, onPromptChange, onFileAction, onClear }: Props) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);

  const summarizeFile = () => {
    if (!selectedFile) return;
    onFileAction("summarize", selectedFile, "");
  };

  const editFile = () => {
    if (!selectedFile || !prompt.trim()) return;
    onFileAction("edit", selectedFile, prompt.trim());
    onPromptChange("");
  };

  return (
    <section className="grid min-h-[calc(100vh-188px)] gap-4 xl:grid-cols-[minmax(420px,0.95fr)_minmax(420px,1.05fr)]">
      <div className="flex min-h-0 flex-col rounded border border-slate-300 bg-slate-50 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-300 px-4 py-3 dark:border-slate-800">
          <div>
            <div className="text-sm font-semibold text-slate-950 dark:text-white">Drawing Assistant</div>
            <div className="text-xs text-slate-500 dark:text-slate-400">Upload drawings for summary or safe DXF text edits</div>
          </div>
          <button className="inline-flex h-9 items-center gap-2 rounded border border-slate-300 bg-white px-3 text-sm text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700" title="Clear" onClick={onClear}><Eraser size={16} />Clear</button>
        </div>
        <div className="flex-1 space-y-2 overflow-auto p-4">
          {!messages.length && (
            <div className="rounded border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-400">
              Attach a drawing file, then summarize it or type an edit instruction and run Edit.
            </div>
          )}
          {messages.map((msg, index) => (
            <div key={index} className={`max-w-[92%] rounded px-3 py-2 text-sm leading-6 ${msg.role === "user" ? "ml-auto bg-indigo-600 text-white" : "mr-auto border border-slate-300 bg-white text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"}`}>
              {msg.content}
            </div>
          ))}
        </div>
        <div className="border-t border-slate-300 p-4 dark:border-slate-800">
          <input
            ref={fileRef}
            className="hidden"
            type="file"
            accept=".dxf,.svg,.png,.jpg,.jpeg,.webp,.bmp,.txt,.csv,.json,image/*"
            onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
          />
          <div className="flex flex-wrap items-center gap-2">
            <button className="inline-flex h-9 items-center gap-2 rounded border border-slate-300 bg-white px-3 text-sm text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700" title="Attach drawing" onClick={() => fileRef.current?.click()}>
              <Paperclip size={16} />Attach
            </button>
            {selectedFile && (
              <span className="inline-flex h-9 min-w-0 max-w-full items-center gap-2 rounded border border-slate-300 bg-slate-100 px-3 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200">
                <FileText size={16} className="shrink-0" />
                <span className="truncate">{selectedFile.name}</span>
              </span>
            )}
          </div>
          <div className="mt-3 grid grid-cols-[1fr_auto_auto] gap-2">
            <textarea className="min-h-[54px] resize-none rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-950 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100" value={prompt} onChange={(event) => onPromptChange(event.target.value)} placeholder="change the length from 12560 to 11500" />
            <button className="inline-flex h-[54px] items-center gap-2 rounded bg-slate-700 px-3 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-slate-600 dark:hover:bg-slate-500" title="Summarize drawing" onClick={summarizeFile} disabled={!selectedFile}>
              <FileText size={16} /><span className="hidden sm:inline">Summarize</span>
            </button>
            <button className="inline-flex h-[54px] items-center gap-2 rounded bg-indigo-600 px-3 text-sm font-medium text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50" title="Edit drawing" onClick={editFile} disabled={!selectedFile || !prompt.trim()}>
              <Wand2 size={16} /><span className="hidden sm:inline">Edit</span>
            </button>
          </div>
        </div>
      </div>
      <div className="flex min-h-0 flex-col rounded border border-slate-300 bg-slate-50 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="border-b border-slate-300 px-4 py-3 dark:border-slate-800">
          <div className="text-sm font-semibold text-slate-950 dark:text-white">Returned File</div>
          <div className="text-xs text-slate-500 dark:text-slate-400">Edited DXF files download automatically when a safe edit is applied</div>
        </div>
        <div className="flex flex-1 items-center justify-center p-6 text-center text-sm text-slate-500 dark:text-slate-400">
          Groq edits are limited to exact DXF TEXT/MTEXT label replacements. Geometry changes still need the CAD geometry tools.
        </div>
      </div>
    </section>
  );
}
