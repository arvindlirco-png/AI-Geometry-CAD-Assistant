import { Check, ChevronDown, ChevronRight, Eraser, Send } from "lucide-react";
import { useState } from "react";
import PromptExamples from "./PromptExamples";
import type { ChatMessage } from "../types";

interface Props {
  messages: ChatMessage[];
  pendingJson: string;
  prompt: string;
  onSend: (prompt: string) => void;
  onPromptChange: (prompt: string) => void;
  onApprove: (json: string) => void;
  onPendingJson: (json: string) => void;
  onClear: () => void;
}

export default function ChatPanel({ messages, pendingJson, prompt, onSend, onPromptChange, onApprove, onPendingJson, onClear }: Props) {
  const [jsonOpen, setJsonOpen] = useState(true);
  const submit = () => {
    if (!prompt.trim()) return;
    onSend(prompt.trim());
    onPromptChange("");
  };

  return (
    <section className="grid min-h-[calc(100vh-188px)] gap-4 xl:grid-cols-[minmax(420px,0.95fr)_minmax(420px,1.05fr)]">
      <div className="flex min-h-0 flex-col rounded border border-slate-300 bg-slate-50 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-300 px-4 py-3 dark:border-slate-800">
          <div>
            <div className="text-sm font-semibold text-slate-950 dark:text-white">Command Chat</div>
            <div className="text-xs text-slate-500 dark:text-slate-400">Natural language to CAD geometry</div>
          </div>
          <button className="inline-flex h-9 items-center gap-2 rounded border border-slate-300 bg-white px-3 text-sm text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700" title="Clear" onClick={onClear}><Eraser size={16} />Clear</button>
        </div>
        <div className="flex-1 space-y-2 overflow-auto p-4">
          {!messages.length && (
            <div className="rounded border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-400">
              Enter a drawing command or choose an example. Parsed geometry appears in the preview before approval.
            </div>
          )}
          {messages.map((msg, index) => (
            <div key={index} className={`max-w-[92%] rounded px-3 py-2 text-sm leading-6 ${msg.role === "user" ? "ml-auto bg-blue-600 text-white" : "mr-auto border border-slate-300 bg-white text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"}`}>
              {msg.content}
            </div>
          ))}
        </div>
        <div className="border-t border-slate-300 p-4 dark:border-slate-800">
          <PromptExamples onUse={onPromptChange} />
          <div className="mt-3 grid grid-cols-[1fr_42px] gap-2 sm:grid-cols-[1fr_42px_42px]">
            <textarea className="min-h-[54px] resize-none rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-950 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100" value={prompt} onChange={(event) => onPromptChange(event.target.value)} onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              submit();
            }
          }} placeholder="Draw a slot 300 mm long and 80 mm wide..." />
            <button className="grid h-[54px] place-items-center rounded bg-blue-600 text-white hover:bg-blue-700" title="Send" onClick={submit}><Send size={18} /></button>
            <button className="hidden h-[54px] place-items-center rounded border border-slate-300 bg-white text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 sm:grid" title="Clear prompt" onClick={() => onPromptChange("")}><Eraser size={18} /></button>
          </div>
        </div>
      </div>
      <div className="flex min-h-0 flex-col rounded border border-slate-300 bg-slate-50 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <button className="flex items-center justify-between border-b border-slate-300 px-4 py-3 text-left dark:border-slate-800" onClick={() => setJsonOpen((value) => !value)}>
          <span>
            <span className="block text-sm font-semibold text-slate-950 dark:text-white">AI JSON Preview</span>
            <span className="block text-xs text-slate-500 dark:text-slate-400">Review or edit before applying to the canvas</span>
          </span>
          {jsonOpen ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
        </button>
        {jsonOpen && (
          <>
            <div className="flex flex-1 p-4">
              <textarea className="min-h-[420px] flex-1 resize-none rounded border border-slate-300 bg-slate-950 p-3 font-mono text-xs leading-5 text-slate-100 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700" value={pendingJson} onChange={(event) => onPendingJson(event.target.value)} spellCheck={false} />
            </div>
            <div className="border-t border-slate-300 p-4 dark:border-slate-800">
              <button className="inline-flex h-10 w-full items-center justify-center gap-2 rounded bg-emerald-600 px-4 text-sm font-semibold text-white hover:bg-emerald-700" onClick={() => onApprove(pendingJson)}><Check size={16} />Approve Geometry JSON</button>
            </div>
          </>
        )}
        {!jsonOpen && (
          <div className="p-4">
            <button className="inline-flex h-10 items-center gap-2 rounded bg-emerald-600 px-4 text-sm font-semibold text-white hover:bg-emerald-700" onClick={() => onApprove(pendingJson)}><Check size={16} />Approve Geometry JSON</button>
          </div>
        )}
        </div>
    </section>
  );
}
