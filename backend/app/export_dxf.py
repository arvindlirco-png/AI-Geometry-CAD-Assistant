from __future__ import annotations

import io
import math
from typing import Iterable

import ezdxf
from ezdxf import units

from .dimension_engine import dimension_table
from .geometry_engine import bounding_box, parabola_points
from .models import GeometryDocument, GeometryObject


SHAPES = "SHAPES"
DIMENSIONS = "DIMENSIONS"
CENTERLINES = "CENTERLINES"
TEXT = "TEXT"


def _r(obj: GeometryObject) -> float:
    return float(obj.radius or (obj.diameter or 0) / 2 or 1)


def _add_layers(dxf: ezdxf.document.Drawing) -> None:
    layer_specs = {
        SHAPES: {"color": 7, "linetype": "CONTINUOUS"},
        DIMENSIONS: {"color": 3, "linetype": "CONTINUOUS"},
        CENTERLINES: {"color": 5, "linetype": "CENTER"},
        TEXT: {"color": 2, "linetype": "CONTINUOUS"},
    }
    for name, attrs in layer_specs.items():
        if name not in dxf.layers:
            dxf.layers.add(name, **attrs)


def _ensure_center_linetype(dxf: ezdxf.document.Drawing) -> None:
    if "CENTER" in dxf.linetypes:
        return
    dxf.linetypes.add(
        "CENTER",
        pattern=[2.0, 1.25, -0.25, 0.25, -0.25],
        description="Center ____ _ ____ _ ____",
    )


def _add_lwpolyline(msp, points: Iterable[list[float] | tuple[float, float]], close: bool = False) -> None:
    msp.add_lwpolyline([(float(p[0]), float(p[1])) for p in points], close=close, dxfattribs={"layer": SHAPES})


def _semicircle_angles(obj: GeometryObject) -> tuple[float, float]:
    return {
        "up": (180, 360),
        "down": (0, 180),
        "left": (90, 270),
        "right": (-90, 90),
    }.get(obj.direction or "up", (180, 360))


def _add_centerlines(msp, obj: GeometryObject) -> None:
    if obj.type not in {"circle", "semicircle", "ellipse", "arc", "slot"}:
        return
    cx, cy = obj.center or [0, 0]
    if obj.type == "ellipse":
        half = max(float(obj.major_axis or 1), float(obj.minor_axis or 1)) / 2
    elif obj.type == "slot":
        half = max(float(obj.total_length or 1), float(obj.width or 1)) / 2
    else:
        half = _r(obj)
    ext = half * 1.2
    msp.add_line((cx - ext, cy), (cx + ext, cy), dxfattribs={"layer": CENTERLINES})
    msp.add_line((cx, cy - ext), (cx, cy + ext), dxfattribs={"layer": CENTERLINES})


def _add_shape_label(msp, obj: GeometryObject) -> None:
    x1, y1, _, _ = bounding_box(obj)
    msp.add_text(
        f"{obj.id} {obj.type}",
        height=5,
        dxfattribs={"layer": TEXT},
    ).set_placement((x1, y1 - 8))


def _add_dimension_text(msp, doc: GeometryDocument) -> None:
    if not doc.objects:
        return
    boxes = [bounding_box(obj) for obj in doc.objects]
    x = min(box[0] for box in boxes)
    y = max(box[3] for box in boxes) + 18
    for index, row in enumerate(dimension_table(doc)):
        text = _dimension_summary(row)
        msp.add_text(
            text,
            height=5,
            dxfattribs={"layer": DIMENSIONS},
        ).set_placement((x, y + index * 9))


def _dimension_summary(row: dict) -> str:
    shape_id = row.get("id", "")
    shape_type = row.get("type", "")
    fields = []
    for key in (
        "radius",
        "diameter",
        "length",
        "width",
        "height",
        "major_axis",
        "minor_axis",
        "angle",
        "arc_length",
        "area",
        "perimeter",
    ):
        if key in row:
            fields.append(f"{key}={row[key]}")
    return f"{shape_id} {shape_type}: " + ", ".join(fields)


def _add_rectangle(msp, obj: GeometryObject) -> None:
    x, y = float(obj.x or 0), float(obj.y or 0)
    w, h = float(obj.width or 0), float(obj.height or 0)
    _add_lwpolyline(msp, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], close=True)


def _add_ellipse(msp, obj: GeometryObject) -> None:
    cx, cy = obj.center or [0, 0]
    major = float(obj.major_axis or 1) / 2
    minor = float(obj.minor_axis or 1) / 2
    angle = math.radians(float(obj.rotation or 0))
    major_axis = (major * math.cos(angle), major * math.sin(angle), 0)
    ratio = max(minor / max(major, 1e-9), 1e-9)
    try:
        msp.add_ellipse(
            center=(cx, cy, 0),
            major_axis=major_axis,
            ratio=ratio,
            dxfattribs={"layer": SHAPES},
        )
    except Exception:
        points = []
        for i in range(97):
            t = 2 * math.pi * i / 96
            x = major * math.cos(t)
            y = minor * math.sin(t)
            points.append((cx + x * math.cos(angle) - y * math.sin(angle), cy + x * math.sin(angle) + y * math.cos(angle)))
        _add_lwpolyline(msp, points, close=True)


def _add_slot(msp, obj: GeometryObject) -> None:
    cx, cy = obj.center or [0, 0]
    total = float(obj.total_length or 1)
    width = float(obj.width or 1)
    radius = width / 2
    straight = max(total - width, 0)
    if obj.orientation == "vertical":
        top_y = cy - straight / 2
        bottom_y = cy + straight / 2
        x_left = cx - radius
        x_right = cx + radius
        msp.add_line((x_left, top_y), (x_left, bottom_y), dxfattribs={"layer": SHAPES})
        msp.add_line((x_right, top_y), (x_right, bottom_y), dxfattribs={"layer": SHAPES})
        msp.add_arc((cx, top_y), radius, start_angle=180, end_angle=360, dxfattribs={"layer": SHAPES})
        msp.add_arc((cx, bottom_y), radius, start_angle=0, end_angle=180, dxfattribs={"layer": SHAPES})
    else:
        left_x = cx - straight / 2
        right_x = cx + straight / 2
        y_top = cy - radius
        y_bottom = cy + radius
        msp.add_line((left_x, y_top), (right_x, y_top), dxfattribs={"layer": SHAPES})
        msp.add_line((left_x, y_bottom), (right_x, y_bottom), dxfattribs={"layer": SHAPES})
        msp.add_arc((right_x, cy), radius, start_angle=-90, end_angle=90, dxfattribs={"layer": SHAPES})
        msp.add_arc((left_x, cy), radius, start_angle=90, end_angle=270, dxfattribs={"layer": SHAPES})


def _add_object(msp, obj: GeometryObject) -> None:
    if obj.type == "circle":
        msp.add_circle(tuple(obj.center or [0, 0]), radius=_r(obj), dxfattribs={"layer": SHAPES})
    elif obj.type == "line":
        msp.add_line(tuple(obj.start or [0, 0]), tuple(obj.end or [0, 0]), dxfattribs={"layer": SHAPES})
    elif obj.type == "rectangle":
        _add_rectangle(msp, obj)
    elif obj.type == "ellipse":
        _add_ellipse(msp, obj)
    elif obj.type == "arc":
        msp.add_arc(
            tuple(obj.center or [0, 0]),
            radius=_r(obj),
            start_angle=float(obj.start_angle or 0),
            end_angle=float(obj.end_angle or 180),
            dxfattribs={"layer": SHAPES},
        )
    elif obj.type == "semicircle":
        start_angle, end_angle = _semicircle_angles(obj)
        msp.add_arc(tuple(obj.center or [0, 0]), radius=_r(obj), start_angle=start_angle, end_angle=end_angle, dxfattribs={"layer": SHAPES})
    elif obj.type == "parabola":
        _add_lwpolyline(msp, parabola_points(obj, steps=96))
    elif obj.type == "slot":
        _add_slot(msp, obj)
    _add_centerlines(msp, obj)
    _add_shape_label(msp, obj)


def render_dxf(doc: GeometryDocument) -> bytes:
    dxf = ezdxf.new("R2010", setup=True)
    dxf.units = units.MM
    dxf.header["$INSUNITS"] = 4
    _ensure_center_linetype(dxf)
    _add_layers(dxf)
    msp = dxf.modelspace()

    for obj in doc.objects:
        _add_object(msp, obj)
    _add_dimension_text(msp, doc)

    stream = io.StringIO()
    dxf.write(stream)
    return stream.getvalue().encode("utf-8")
