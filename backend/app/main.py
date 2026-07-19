from __future__ import annotations

import csv
import io

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from .ai_parser import ai_status, parse_with_ai
from .database import delete_drawing, get_drawing, init_db, list_drawings, save_drawing
from .dimension_engine import dimension_table
from .drawing_file_ai import DrawingFileResponse, edit_drawing_file, summarize_drawing_file
from .export_dxf import render_dxf
from .export_pdf import render_pdf
from .export_png import render_png
from .export_svg import render_svg
from .geometry_engine import drawing_data
from .models import GeometryDocument, ParseRequest, ParseResponse, SaveRequest


app = FastAPI(title="AI Geometry CAD Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175", "http://127.0.0.1:5175"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+):5175",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": "AI Geometry CAD Assistant"}


@app.get("/ai/status")
async def status() -> dict:
    return await ai_status()


@app.post("/parse", response_model=ParseResponse)
async def parse(req: ParseRequest) -> ParseResponse:
    return await parse_with_ai(req.prompt, req.current_geometry)


@app.post("/drawing-file", response_model=DrawingFileResponse)
async def drawing_file(
    action: str = Form(...),
    instruction: str = Form(""),
    file: UploadFile = File(...),
) -> DrawingFileResponse:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    filename = file.filename or "drawing"
    if action == "summarize":
        return await summarize_drawing_file(filename, data)
    if action == "edit":
        if not instruction.strip():
            raise HTTPException(status_code=400, detail="Edit instruction is required")
        return await edit_drawing_file(filename, data, instruction.strip())
    raise HTTPException(status_code=400, detail="Action must be summarize or edit")


@app.post("/draw")
def draw(doc: GeometryDocument) -> dict:
    return {"geometry": doc, "drawing": drawing_data(doc), "dimensions": dimension_table(doc)}


@app.post("/dimensions")
def dimensions(doc: GeometryDocument) -> list[dict]:
    return dimension_table(doc)


@app.post("/export/svg")
def export_svg(doc: GeometryDocument) -> Response:
    return Response(render_svg(doc), media_type="image/svg+xml", headers={"Content-Disposition": 'attachment; filename="drawing.svg"'})


@app.post("/export/png")
def export_png(doc: GeometryDocument) -> Response:
    return Response(render_png(doc), media_type="image/png", headers={"Content-Disposition": 'attachment; filename="drawing.png"'})


@app.post("/export/pdf")
def export_pdf(doc: GeometryDocument) -> Response:
    return Response(render_pdf(doc), media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="drawing.pdf"'})


@app.post("/export/dxf")
def export_dxf(doc: GeometryDocument) -> Response:
    return Response(render_dxf(doc), media_type="application/dxf", headers={"Content-Disposition": 'attachment; filename="drawing.dxf"'})


@app.post("/export/json")
def export_json(doc: GeometryDocument) -> Response:
    return Response(doc.model_dump_json(indent=2), media_type="application/json", headers={"Content-Disposition": 'attachment; filename="drawing.json"'})


@app.post("/export/csv")
def export_csv(doc: GeometryDocument) -> StreamingResponse:
    rows = dimension_table(doc)
    buffer = io.StringIO()
    if rows:
        writer = csv.DictWriter(buffer, fieldnames=sorted({key for row in rows for key in row.keys()}))
        writer.writeheader()
        writer.writerows(rows)
    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="dimensions.csv"'})


@app.post("/save")
def save(req: SaveRequest) -> dict:
    return {"id": save_drawing(req.name, req.geometry, req.chat_history)}


@app.get("/drawings")
def drawings() -> list[dict]:
    return list_drawings()


@app.get("/drawings/{drawing_id}")
def drawing(drawing_id: int) -> dict:
    row = get_drawing(drawing_id)
    if not row:
        raise HTTPException(status_code=404, detail="Drawing not found")
    return row


@app.delete("/drawings/{drawing_id}")
def remove_drawing(drawing_id: int) -> dict:
    delete_drawing(drawing_id)
    return {"deleted": True}
