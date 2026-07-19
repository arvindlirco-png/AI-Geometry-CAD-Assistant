import axios from "axios";
import type { ChatMessage, DrawingFileResponse, GeometryDocument, ParseResponse } from "./types";

export const defaultBackendUrl = () => {
  const host = window.location.hostname;
  if (host === "localhost" || host === "127.0.0.1") return "http://127.0.0.1:8020";
  return `http://${host}:8020`;
};

const stored = localStorage.getItem("backendUrl");
export const api = axios.create({ baseURL: stored || defaultBackendUrl() });

export function setBackendUrl(url: string) {
  localStorage.setItem("backendUrl", url);
  api.defaults.baseURL = url;
}

export async function health() {
  return (await api.get("/health")).data;
}

export async function aiStatus() {
  return (await api.get("/ai/status")).data;
}

export async function parsePrompt(prompt: string, current: GeometryDocument): Promise<ParseResponse> {
  return (await api.post("/parse", { prompt, current_geometry: current })).data;
}

export async function processDrawingFile(action: "summarize" | "edit", file: File, instruction = ""): Promise<DrawingFileResponse> {
  const form = new FormData();
  form.append("action", action);
  form.append("instruction", instruction);
  form.append("file", file);
  return (await api.post("/drawing-file", form)).data;
}

export function downloadBase64File(filename: string, contentType: string, base64: string) {
  const bytes = Uint8Array.from(atob(base64), (char) => char.charCodeAt(0));
  const url = URL.createObjectURL(new Blob([bytes], { type: contentType }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export async function drawGeometry(geometry: GeometryDocument) {
  return (await api.post("/draw", geometry)).data;
}

export async function saveDrawing(name: string, geometry: GeometryDocument, chat_history: ChatMessage[]) {
  return (await api.post("/save", { name, geometry, chat_history })).data;
}

export async function listDrawings() {
  return (await api.get("/drawings")).data;
}

export async function openDrawing(id: number) {
  return (await api.get(`/drawings/${id}`)).data;
}

export async function exportFile(format: "svg" | "png" | "pdf" | "dxf" | "json" | "csv", geometry: GeometryDocument) {
  const res = await api.post(`/export/${format}`, geometry, { responseType: "blob" });
  const url = URL.createObjectURL(res.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = format === "csv" ? "dimensions.csv" : `drawing.${format}`;
  link.click();
  URL.revokeObjectURL(url);
}
