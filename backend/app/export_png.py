from __future__ import annotations

import io

from PIL import Image, ImageDraw, ImageFont

from .dimension_engine import dimension_table
from .geometry_engine import arc_points, bounding_box, parabola_points, slot_outline_points
from .models import GeometryDocument


def _viewport(doc: GeometryDocument, width: int, height: int):
    boxes = [bounding_box(obj) for obj in doc.objects] or [[0, 0, 400, 300]]
    x1, y1 = min(b[0] for b in boxes), min(b[1] for b in boxes)
    x2, y2 = max(b[2] for b in boxes), max(b[3] for b in boxes)
    span_x, span_y = max(x2 - x1, 1), max(y2 - y1, 1)
    scale = min((width - 120) / span_x, (height - 220) / span_y, 4)
    ox = 60 - x1 * scale
    oy = 90 - y1 * scale
    return lambda p: (p[0] * scale + ox, p[1] * scale + oy)


def _draw_poly(draw: ImageDraw.ImageDraw, project, points: list[list[float]], close: bool = False) -> None:
    if len(points) < 2:
        return
    pts = [project(p) for p in points]
    if close:
        pts.append(pts[0])
    draw.line(pts, fill="#111827", width=1, joint="curve")


def _draw_shapes(draw: ImageDraw.ImageDraw, doc: GeometryDocument, project) -> None:
    for obj in doc.objects:
        if obj.type == "circle":
            cx, cy = obj.center or [0, 0]
            r = obj.radius or (obj.diameter or 0) / 2 or 1
            x1, y1 = project([cx - r, cy - r])
            x2, y2 = project([cx + r, cy + r])
            draw.ellipse((x1, y1, x2, y2), outline="#111827", width=1)
        elif obj.type == "line":
            draw.line((project(obj.start or [0, 0]), project(obj.end or [0, 0])), fill="#111827", width=1)
        elif obj.type == "rectangle":
            x, y, w, h = obj.x or 0, obj.y or 0, obj.width or 0, obj.height or 0
            draw.rectangle((*project([x, y]), *project([x + w, y + h])), outline="#111827", width=1)
        elif obj.type == "ellipse":
            cx, cy = obj.center or [0, 0]
            rx, ry = (obj.major_axis or 1) / 2, (obj.minor_axis or 1) / 2
            draw.ellipse((*project([cx - rx, cy - ry]), *project([cx + rx, cy + ry])), outline="#111827", width=1)
        elif obj.type in {"arc", "semicircle"}:
            _draw_poly(draw, project, arc_points(obj))
        elif obj.type == "parabola":
            _draw_poly(draw, project, parabola_points(obj))
        elif obj.type == "slot":
            _draw_poly(draw, project, slot_outline_points(obj), close=True)


def render_png(doc: GeometryDocument) -> bytes:
    image = Image.new("RGB", (1200, 800), "#f8fafc")
    draw = ImageDraw.Draw(image)
    for x in range(0, 1200, 20):
        draw.line((x, 0, x, 800), fill="#e5e7eb")
    for y in range(0, 800, 20):
        draw.line((0, y, 1200, y), fill="#e5e7eb")
    _draw_shapes(draw, doc, _viewport(doc, 1200, 800))
    draw.text((24, 24), doc.drawing_name, fill="#111827", font=ImageFont.load_default())
    y = 620
    for row in dimension_table(doc):
        draw.text((24, y), f"{row['id']} {row['type']} {row.get('bounding_box')}", fill="#334155", font=ImageFont.load_default())
        y += 18
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
