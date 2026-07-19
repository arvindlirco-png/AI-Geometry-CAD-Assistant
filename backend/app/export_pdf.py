from __future__ import annotations

import io

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .dimension_engine import dimension_table
from .geometry_engine import arc_points, bounding_box, parabola_points, slot_outline_points
from .models import GeometryDocument


def _viewport(doc: GeometryDocument, width: float, height: float):
    boxes = [bounding_box(obj) for obj in doc.objects] or [[0, 0, 400, 300]]
    x1, y1 = min(b[0] for b in boxes), min(b[1] for b in boxes)
    x2, y2 = max(b[2] for b in boxes), max(b[3] for b in boxes)
    scale = min((width - 100) / max(x2 - x1, 1), (height - 360) / max(y2 - y1, 1), 2.2)
    ox = 50 - x1 * scale
    oy = height - 110 + y1 * scale
    return lambda p: (p[0] * scale + ox, oy - p[1] * scale)


def _poly(pdf: canvas.Canvas, project, points: list[list[float]], close: bool = False) -> None:
    if len(points) < 2:
        return
    path = pdf.beginPath()
    x, y = project(points[0])
    path.moveTo(x, y)
    for point in points[1:]:
        x, y = project(point)
        path.lineTo(x, y)
    if close:
        path.close()
    pdf.drawPath(path, stroke=1, fill=0)


def _draw_shapes(pdf: canvas.Canvas, doc: GeometryDocument, project) -> None:
    pdf.setStrokeColorRGB(0.07, 0.09, 0.15)
    pdf.setLineWidth(0.5)
    for obj in doc.objects:
        if obj.type == "circle":
            cx, cy = obj.center or [0, 0]
            r = obj.radius or (obj.diameter or 0) / 2 or 1
            x1, y1 = project([cx - r, cy + r])
            x2, y2 = project([cx + r, cy - r])
            pdf.ellipse(x1, y1, x2, y2, stroke=1, fill=0)
        elif obj.type == "line":
            x1, y1 = project(obj.start or [0, 0])
            x2, y2 = project(obj.end or [0, 0])
            pdf.line(x1, y1, x2, y2)
        elif obj.type == "rectangle":
            x, y, w, h = obj.x or 0, obj.y or 0, obj.width or 0, obj.height or 0
            x1, y1 = project([x, y + h])
            x2, y2 = project([x + w, y])
            pdf.rect(x1, y1, x2 - x1, y2 - y1, stroke=1, fill=0)
        elif obj.type == "ellipse":
            cx, cy = obj.center or [0, 0]
            rx, ry = (obj.major_axis or 1) / 2, (obj.minor_axis or 1) / 2
            x1, y1 = project([cx - rx, cy + ry])
            x2, y2 = project([cx + rx, cy - ry])
            pdf.ellipse(x1, y1, x2, y2, stroke=1, fill=0)
        elif obj.type in {"arc", "semicircle"}:
            _poly(pdf, project, arc_points(obj))
        elif obj.type == "parabola":
            _poly(pdf, project, parabola_points(obj))
        elif obj.type == "slot":
            _poly(pdf, project, slot_outline_points(obj), close=True)


def render_pdf(doc: GeometryDocument) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, height - 50, doc.drawing_name)
    pdf.setStrokeColorRGB(0.86, 0.89, 0.93)
    pdf.rect(40, height - 330, width - 80, 250, stroke=1, fill=0)
    _draw_shapes(pdf, doc, _viewport(doc, width, height))
    pdf.setFont("Helvetica", 9)
    y = height - 360
    for row in dimension_table(doc):
        pdf.drawString(40, y, str(row))
        y -= 16
        if y < 50:
            pdf.showPage()
            y = height - 50
    pdf.save()
    return buffer.getvalue()
