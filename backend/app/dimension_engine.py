from __future__ import annotations

import math
from typing import Any

from .geometry_engine import bounding_box, parabola_points
from .models import GeometryDocument, GeometryObject


def _dist(a: list[float], b: list[float]) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def dimensions_for_object(obj: GeometryObject) -> dict[str, Any]:
    row: dict[str, Any] = {"id": obj.id, "type": obj.type, "bounding_box": bounding_box(obj)}
    if obj.center:
        row["center_point"] = obj.center
    if obj.start:
        row["start_point"] = obj.start
    if obj.end:
        row["end_point"] = obj.end
    if obj.type == "circle":
        r = obj.radius or (obj.diameter or 0) / 2
        row.update(radius=r, diameter=2 * r, area=math.pi * r * r, perimeter=2 * math.pi * r)
    elif obj.type == "semicircle":
        r = obj.radius or (obj.diameter or 0) / 2
        row.update(radius=r, diameter=2 * r, area=math.pi * r * r / 2, arc_length=math.pi * r, chord_length=2 * r, perimeter=math.pi * r + 2 * r)
    elif obj.type == "line":
        length = _dist(obj.start or [0, 0], obj.end or [0, 0])
        angle = math.degrees(math.atan2((obj.end or [0, 0])[1] - (obj.start or [0, 0])[1], (obj.end or [0, 0])[0] - (obj.start or [0, 0])[0]))
        row.update(length=length, angle=angle)
    elif obj.type == "rectangle":
        w, h = obj.width or 0, obj.height or 0
        row.update(width=w, height=h, area=w * h, perimeter=2 * (w + h))
    elif obj.type == "ellipse":
        a, b = (obj.major_axis or 0) / 2, (obj.minor_axis or 0) / 2
        row.update(major_axis=obj.major_axis, minor_axis=obj.minor_axis, area=math.pi * a * b, perimeter=math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b))))
    elif obj.type == "arc":
        r = obj.radius or 0
        sweep = abs((obj.end_angle or 0) - (obj.start_angle or 0))
        row.update(radius=r, angle=sweep, arc_length=math.radians(sweep) * r, chord_length=2 * r * math.sin(math.radians(sweep) / 2))
    elif obj.type == "parabola":
        pts = parabola_points(obj)
        row.update(width=obj.width, height=obj.height, length=sum(_dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)))
    elif obj.type == "slot":
        total, width = obj.total_length or 0, obj.width or 0
        straight = max(total - width, 0)
        row.update(length=total, width=width, area=straight * width + math.pi * (width / 2) ** 2, perimeter=2 * straight + math.pi * width)
    return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()}


def dimension_table(doc: GeometryDocument) -> list[dict[str, Any]]:
    return [dimensions_for_object(obj) for obj in doc.objects]

