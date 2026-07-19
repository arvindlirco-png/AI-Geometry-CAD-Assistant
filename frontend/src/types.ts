export type Unit = "mm" | "cm" | "inch";
export type ShapeType = "circle" | "semicircle" | "line" | "rectangle" | "ellipse" | "arc" | "parabola" | "slot";

export interface GeometryObject {
  id: string;
  type: ShapeType;
  center?: number[];
  start?: number[];
  end?: number[];
  vertex?: number[];
  x?: number;
  y?: number;
  radius?: number;
  diameter?: number;
  width?: number;
  height?: number;
  length?: number;
  total_length?: number;
  major_axis?: number;
  minor_axis?: number;
  rotation?: number;
  angle?: number;
  start_angle?: number;
  end_angle?: number;
  direction?: "up" | "down" | "left" | "right";
  orientation?: "horizontal" | "vertical";
  style?: { stroke: string; stroke_width: number; fill: string };
}

export interface GeometryDocument {
  unit: Unit;
  drawing_name: string;
  objects: GeometryObject[];
  dimensions: { show: boolean; [key: string]: unknown };
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ParseResponse {
  success: boolean;
  source: string;
  geometry: GeometryDocument | null;
  warnings: string[];
  clarification_needed?: boolean;
  question?: string | null;
  action?: "draw" | "export";
  export_format?: "svg" | "png" | "pdf" | "dxf" | "json" | "csv" | null;
}

export interface DrawingData {
  objects: Array<{ id: string; type: ShapeType; svg: { tag: string; attrs: Record<string, string | number> }; bbox: number[] }>;
  bbox: number[];
}
