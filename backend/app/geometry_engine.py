from __future__ import annotations

import math
from typing import Any

from .models import GeometryDocument, GeometryObject


def _r(obj: GeometryObject) -> float:
    return float(obj.radius or (obj.diameter or 0) / 2 or 1)


def _path(points: list[list[float]]) -> str:
    first, rest = points[0], points[1:]
    return "M " + f"{first[0]:.3f} {first[1]:.3f} " + " ".join(f"L {x:.3f} {y:.3f}" for x, y in rest)


def parabola_points(obj: GeometryObject, steps: int = 48) -> list[list[float]]:
    vx, vy = obj.vertex or [0, 0]
    w, h = float(obj.width or 100), float(obj.height or 50)
    pts = []
    for i in range(steps + 1):
        t = -1 + 2 * i / steps
        if obj.direction in {"left", "right"}:
            x = vx + (h * t * t * (1 if obj.direction == "right" else -1))
            y = vy + (w / 2) * t
        else:
            x = vx + (w / 2) * t
            y = vy + (h * t * t * (-1 if obj.direction == "up" else 1))
        pts.append([x, y])
    return pts


def arc_points(obj: GeometryObject, steps: int = 48) -> list[list[float]]:
    cx, cy = obj.center or [0, 0]
    r = _r(obj)
    if obj.type == "semicircle":
        angles = {"up": (180, 360), "down": (0, 180), "left": (90, 270), "right": (-90, 90)}
        a1, a2 = angles.get(obj.direction or "up", (180, 360))
    else:
        a1, a2 = obj.start_angle or 0, obj.end_angle or 180
    return [
        [cx + r * math.cos(math.radians(a1 + (a2 - a1) * i / steps)), cy + r * math.sin(math.radians(a1 + (a2 - a1) * i / steps))]
        for i in range(steps + 1)
    ]


def slot_outline_points(obj: GeometryObject, steps: int = 24) -> list[list[float]]:
    cx, cy = obj.center or [0, 0]
    total, width = float(obj.total_length or 100), float(obj.width or 20)
    r = width / 2
    straight = max(total - width, 0)
    pts: list[list[float]] = []
    if obj.orientation == "vertical":
        top_y, bottom_y = cy - straight / 2, cy + straight / 2
        pts.append([cx - r, top_y])
        for i in range(steps + 1):
            a = math.radians(180 + 180 * i / steps)
            pts.append([cx + r * math.cos(a), top_y + r * math.sin(a)])
        pts.append([cx + r, bottom_y])
        for i in range(steps + 1):
            a = math.radians(180 * i / steps)
            pts.append([cx + r * math.cos(a), bottom_y + r * math.sin(a)])
    else:
        left_x, right_x = cx - straight / 2, cx + straight / 2
        pts.append([left_x, cy - r])
        pts.append([right_x, cy - r])
        for i in range(steps + 1):
            a = math.radians(-90 + 180 * i / steps)
            pts.append([right_x + r * math.cos(a), cy + r * math.sin(a)])
        pts.append([left_x, cy + r])
        for i in range(steps + 1):
            a = math.radians(90 + 180 * i / steps)
            pts.append([left_x + r * math.cos(a), cy + r * math.sin(a)])
    return pts


def object_to_svg(obj: GeometryObject) -> dict[str, Any]:
    style = obj.style.model_dump()
    style["stroke_width"] = min(float(style.get("stroke_width") or 0.5), 0.8)
    if obj.type == "circle":
        return {"tag": "circle", "attrs": {"cx": obj.center[0], "cy": obj.center[1], "r": _r(obj), **style}}
    if obj.type == "line":
        return {"tag": "line", "attrs": {"x1": obj.start[0], "y1": obj.start[1], "x2": obj.end[0], "y2": obj.end[1], **style}}
    if obj.type == "rectangle":
        return {"tag": "rect", "attrs": {"x": obj.x or 0, "y": obj.y or 0, "width": obj.width or 1, "height": obj.height or 1, **style}}
    if obj.type == "ellipse":
        cx, cy = obj.center or [0, 0]
        return {"tag": "ellipse", "attrs": {"cx": cx, "cy": cy, "rx": (obj.major_axis or 1) / 2, "ry": (obj.minor_axis or 1) / 2, "transform": f"rotate({obj.rotation} {cx} {cy})", **style}}
    if obj.type in {"semicircle", "arc"}:
        r = _r(obj)
        a1 = 0
        a2 = 180
        if obj.type == "semicircle":
            a1, a2 = {"up": (180, 360), "down": (0, 180), "left": (90, 270), "right": (-90, 90)}.get(obj.direction or "up", (180, 360))
        else:
            a1, a2 = obj.start_angle or 0, obj.end_angle or 180
        p1, p2 = arc_points(obj, 1)
        large = 1 if abs(a2 - a1) > 180 else 0
        return {"tag": "path", "attrs": {"d": f"M {p1[0]:.3f} {p1[1]:.3f} A {r:.3f} {r:.3f} 0 {large} 1 {p2[0]:.3f} {p2[1]:.3f}", **style}}
    if obj.type == "parabola":
        return {"tag": "path", "attrs": {"d": _path(parabola_points(obj)), **style}}
    if obj.type == "slot":
        cx, cy = obj.center or [0, 0]
        total, width = float(obj.total_length or 100), float(obj.width or 20)
        r = width / 2
        straight = max(total - width, 0)
        if obj.orientation == "vertical":
            x1, x2, y1, y2 = cx - r, cx + r, cy - straight / 2, cy + straight / 2
            d = f"M {x1} {y1} A {r} {r} 0 0 1 {x2} {y1} L {x2} {y2} A {r} {r} 0 0 1 {x1} {y2} Z"
        else:
            x1, x2, y1, y2 = cx - straight / 2, cx + straight / 2, cy - r, cy + r
            d = f"M {x1} {y1} L {x2} {y1} A {r} {r} 0 0 1 {x2} {y2} L {x1} {y2} A {r} {r} 0 0 1 {x1} {y1} Z"
        return {"tag": "path", "attrs": {"d": d, **style}}
    return {"tag": "g", "attrs": {}}


def bounding_box(obj: GeometryObject) -> list[float]:
    if obj.type == "circle":
        cx, cy = obj.center or [0, 0]; r = _r(obj); return [cx - r, cy - r, cx + r, cy + r]
    if obj.type == "line":
        xs = [obj.start[0], obj.end[0]]; ys = [obj.start[1], obj.end[1]]; return [min(xs), min(ys), max(xs), max(ys)]
    if obj.type == "rectangle":
        x, y, w, h = obj.x or 0, obj.y or 0, obj.width or 0, obj.height or 0; return [x, y, x + w, y + h]
    if obj.type == "ellipse":
        cx, cy = obj.center or [0, 0]; return [cx - (obj.major_axis or 0) / 2, cy - (obj.minor_axis or 0) / 2, cx + (obj.major_axis or 0) / 2, cy + (obj.minor_axis or 0) / 2]
    if obj.type in {"semicircle", "arc"}:
        pts = arc_points(obj); xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; return [min(xs), min(ys), max(xs), max(ys)]
    if obj.type == "parabola":
        pts = parabola_points(obj); xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; return [min(xs), min(ys), max(xs), max(ys)]
    if obj.type == "slot":
        cx, cy = obj.center or [0, 0]; total, width = obj.total_length or 0, obj.width or 0
        if obj.orientation == "vertical":
            return [cx - width / 2, cy - total / 2, cx + width / 2, cy + total / 2]
        return [cx - total / 2, cy - width / 2, cx + total / 2, cy + width / 2]
    return [0, 0, 0, 0]


def drawing_data(doc: GeometryDocument) -> dict[str, Any]:
    objects = [{"id": obj.id, "type": obj.type, "svg": object_to_svg(obj), "bbox": bounding_box(obj)} for obj in doc.objects]
    boxes = [item["bbox"] for item in objects] or [[0, 0, 400, 300]]
    return {"objects": objects, "bbox": [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]}
