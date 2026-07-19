from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .models import GeometryDocument, GeometryObject


@dataclass
class ParseIntent:
    geometry: GeometryDocument
    warnings: list[str]
    action: str = "draw"
    export_format: str | None = None


class ClarificationNeeded(Exception):
    def __init__(self, question: str):
        super().__init__(question)
        self.question = question


NUMBER = r"-?\d+(?:\.\d+)?"


def _numbers(text: str) -> list[float]:
    return [float(x) for x in re.findall(NUMBER, text)]


def _next_id(doc: GeometryDocument, prefix: str) -> str:
    used = {
        int(match.group(1))
        for obj in doc.objects
        if (match := re.fullmatch(rf"{re.escape(prefix)}(\d+)", obj.id.upper()))
    }
    index = 1
    while index in used:
        index += 1
    return f"{prefix}{index}"


def _base(current: GeometryDocument | None) -> GeometryDocument:
    return current.model_copy(deep=True) if current else GeometryDocument()


def _direction(text: str, default: str = "up") -> str:
    if any(word in text for word in ("upward", "upwards", "opening upward", "opening up", "facing upward")):
        return "up"
    if any(word in text for word in ("downward", "downwards", "opening downward", "opening down", "facing down")):
        return "down"
    return next((d for d in ("up", "down", "left", "right") if re.search(rf"\b{d}\b", text)), default)


def _center(text: str, default: list[float]) -> list[float]:
    match = re.search(rf"(?:center|centre|at)\s*\(?\s*({NUMBER})\s*,\s*({NUMBER})\s*\)?", text)
    return [float(match.group(1)), float(match.group(2))] if match else default


def _keyword_number(text: str, keywords: str) -> float | None:
    match = re.search(rf"\b(?:{keywords})\b\s*(?:is|of|to|=)?\s*({NUMBER})", text)
    return float(match.group(1)) if match else None


def _length_number(text: str) -> float | None:
    match = re.search(rf"\blength(?:\s+of\s+(?:line(?:\s+\d+)?|[a-z]+\d+))?\s*(?:is|of|to|=)?\s*({NUMBER})", text)
    if match:
        return float(match.group(1))
    match = re.search(rf"({NUMBER})\s*mm\s+long\b", text)
    return float(match.group(1)) if match else None


def _circumference_number(text: str) -> float | None:
    match = re.search(rf"\b(?:circumference|perimeter)\s*(?:length)?\s*(?:is|of|to|=)?\s*({NUMBER})", text)
    if match:
        return float(match.group(1))
    match = re.search(rf"({NUMBER})\s*(?:mm|cm|inch)?\s+(?:circumference|perimeter)\b", text)
    return float(match.group(1)) if match else None


def _arc_length_number(text: str) -> float | None:
    match = re.search(rf"\barc\s+length\s*(?:is|of|to|=)?\s*({NUMBER})", text)
    if match:
        return float(match.group(1))
    match = re.search(rf"({NUMBER})\s*(?:mm|cm|inch)?\s+arc\s+length\b", text)
    return float(match.group(1)) if match else None


def _direction_angle(text: str) -> float:
    direction = _direction(text, "right")
    return {"right": 0.0, "up": 90.0, "left": 180.0, "down": 270.0}[direction]


def _angle_number(text: str) -> float | None:
    match = re.search(rf"({NUMBER})\s*(?:degree|degrees|deg)\b", text)
    if match:
        return float(match.group(1))
    match = re.search(rf"(?:angle|at)\s*(?:is|of|to|=)?\s*({NUMBER})", text)
    return float(match.group(1)) if match else None


def _require(value: float | None, question: str) -> float:
    if value is None:
        raise ClarificationNeeded(question)
    return value


def _move_object(obj: GeometryObject, dx: float, dy: float) -> None:
    for field in ("center", "start", "end", "vertex"):
        point = getattr(obj, field)
        if point:
            setattr(obj, field, [point[0] + dx, point[1] + dy])
    if obj.x is not None:
        obj.x += dx
    if obj.y is not None:
        obj.y += dy


def _target_shape(doc: GeometryDocument, shape_id: str | None, selected: bool = False) -> GeometryObject | None:
    if shape_id:
        return next((obj for obj in doc.objects if obj.id.lower() == shape_id.lower()), None)
    if selected and doc.objects:
        return doc.objects[-1]
    return doc.objects[-1] if doc.objects else None


def _line_id_from_text(text: str) -> str | None:
    match = re.search(r"\b(?:line\s*)?(l?\d+)\b", text)
    if not match:
        return None
    raw = match.group(1).upper()
    return raw if raw.startswith("L") else f"L{raw}"


def _line_length(obj: GeometryObject) -> float:
    start, end = obj.start or [0, 0], obj.end or [0, 0]
    return math.hypot(end[0] - start[0], end[1] - start[1])


def _line_angle(obj: GeometryObject) -> float:
    start, end = obj.start or [0, 0], obj.end or [0, 0]
    return math.degrees(math.atan2(end[1] - start[1], end[0] - start[0]))


def _line_edge(line: GeometryObject, side: str) -> list[float]:
    start, end = line.start or [0, 0], line.end or [0, 0]
    if side == "right":
        return start if start[0] >= end[0] else end
    if side == "left":
        return start if start[0] <= end[0] else end
    if side in {"top", "upper"}:
        return start if start[1] >= end[1] else end
    return start if start[1] <= end[1] else end


def _tangent_reference_line(doc: GeometryDocument, exclude_id: str | None = None) -> GeometryObject | None:
    candidates = [obj for obj in doc.objects if obj.type == "line" and obj.id.lower() != (exclude_id or "").lower()]
    horizontal = [obj for obj in candidates if obj.start and obj.end and abs(obj.start[1] - obj.end[1]) < 1e-6]
    return horizontal[-1] if horizontal else candidates[-1] if candidates else None


def _set_line_from_start_length_angle(line: GeometryObject, start: list[float], length: float, angle: float) -> None:
    line.start = [float(start[0]), float(start[1])]
    line.end = [
        line.start[0] + length * math.cos(math.radians(angle)),
        line.start[1] + length * math.sin(math.radians(angle)),
    ]


def _arc_point(arc: GeometryObject, endpoint: str) -> list[float]:
    cx, cy = arc.center or [0, 0]
    radius = float(arc.radius or 0)
    if endpoint == "middle":
        angle = ((arc.start_angle or 0) + (arc.end_angle or 0)) / 2
    else:
        angle = arc.start_angle if endpoint == "start" else arc.end_angle
    angle = float(angle if angle is not None else 0)
    return [
        cx + radius * math.cos(math.radians(angle)),
        cy + radius * math.sin(math.radians(angle)),
    ]


def _line_angle_from_text(text: str) -> float:
    if "left" in text:
        return 180
    if "right" in text:
        return 0
    if "upward" in text or re.search(r"\bup\b", text):
        return 90
    if "downward" in text or re.search(r"\bdown\b", text):
        return 270
    if "y axis" in text or "vertical" in text or "parallel to y" in text:
        return 90
    return _angle_number(text) or 0


def _circle(doc: GeometryDocument, text: str) -> GeometryObject:
    radius = _keyword_number(text, "radius|r")
    diameter = _keyword_number(text, "diameter|dia")
    if radius is None and diameter is not None:
        radius = diameter / 2
    circumference = _circumference_number(text)
    if radius is None and circumference is not None:
        radius = circumference / (2 * math.pi)
    radius = _require(radius, "Please provide the radius or diameter.")
    return GeometryObject(id=_next_id(doc, "C"), type="circle", center=_center(text, [100, 100]), radius=radius)


def _semicircle(doc: GeometryDocument, text: str) -> GeometryObject:
    radius = _keyword_number(text, "radius|r")
    diameter = _keyword_number(text, "diameter|dia")
    if radius is None and diameter is not None:
        radius = diameter / 2
    radius = _require(radius, "Please provide the radius or diameter.")
    return GeometryObject(id=_next_id(doc, "S"), type="semicircle", center=_center(text, [100, 100]), radius=radius, direction=_direction(text))


def _line(doc: GeometryDocument, text: str) -> GeometryObject:
    point_match = re.search(rf"from\s*\(?\s*({NUMBER})\s*,\s*({NUMBER})\s*\)?\s*to\s*\(?\s*({NUMBER})\s*,\s*({NUMBER})\s*\)?", text)
    if point_match:
        return GeometryObject(
            id=_next_id(doc, "L"),
            type="line",
            start=[float(point_match.group(1)), float(point_match.group(2))],
            end=[float(point_match.group(3)), float(point_match.group(4))],
        )
    length = _length_number(text) or _keyword_number(text, "line of|line")
    if length is None:
        nums = _numbers(text)
        length = nums[0] if nums else None
    length = _require(length, "Please provide the line length or start and end points.")
    angle = _angle_number(text) or 0
    return GeometryObject(
        id=_next_id(doc, "L"),
        type="line",
        start=[0, 0],
        end=[length * math.cos(math.radians(angle)), length * math.sin(math.radians(angle))],
    )


def _ellipse(doc: GeometryDocument, text: str) -> GeometryObject:
    major = _keyword_number(text, "major axis|major")
    minor = _keyword_number(text, "minor axis|minor")
    nums = _numbers(text)
    if major is None and nums:
        major = nums[0]
    if minor is None and len(nums) > 1:
        minor = nums[1]
    return GeometryObject(
        id=_next_id(doc, "E"),
        type="ellipse",
        center=_center(text, [100, 100]),
        major_axis=_require(major, "Please provide the major axis."),
        minor_axis=_require(minor, "Please provide the minor axis."),
    )


def _parabola(doc: GeometryDocument, text: str) -> GeometryObject:
    width = _keyword_number(text, "width|wide")
    height = _keyword_number(text, "height|high")
    nums = _numbers(text)
    if width is None and nums:
        width = nums[0]
    if height is None and len(nums) > 1:
        height = nums[1]
    return GeometryObject(
        id=_next_id(doc, "P"),
        type="parabola",
        vertex=_center(text, [0, 0]),
        width=_require(width, "Please provide the parabola width."),
        height=_require(height, "Please provide the parabola height."),
        direction=_direction(text),
    )


def _slot(doc: GeometryDocument, text: str) -> GeometryObject:
    length = _keyword_number(text, "total length|length|long")
    width = _keyword_number(text, "width|wide")
    nums = _numbers(text)
    if length is None and nums:
        length = nums[0]
    if width is None and len(nums) > 1:
        width = nums[1]
    orientation = "vertical" if "vertical" in text else "horizontal"
    return GeometryObject(
        id=_next_id(doc, "SL"),
        type="slot",
        center=_center(text, [0, 0]),
        total_length=_require(length, "Please provide the slot total length."),
        width=_require(width, "Please provide the slot width."),
        orientation=orientation,
    )


def _rectangle(doc: GeometryDocument, text: str) -> GeometryObject:
    nums = _numbers(text)
    width = _keyword_number(text, "width|wide") or (nums[0] if nums else None)
    height = _keyword_number(text, "height|high") or (nums[1] if len(nums) > 1 else None)
    return GeometryObject(
        id=_next_id(doc, "R"),
        type="rectangle",
        x=0,
        y=0,
        width=_require(width, "Please provide the rectangle width."),
        height=_require(height, "Please provide the rectangle height."),
    )


def _arc(doc: GeometryDocument, text: str) -> GeometryObject:
    radius = _require(_keyword_number(text, "radius|r"), "Please provide the arc radius.")
    start_angle = _keyword_number(text, "start angle|from angle|from")
    end_angle = _keyword_number(text, "end angle|to angle|to")
    arc_length = _arc_length_number(text)
    if arc_length is not None:
        if arc_length <= 0:
            raise ClarificationNeeded("Please provide an arc length greater than zero.")
        sweep_angle = math.degrees(arc_length / radius)
        if sweep_angle > 360:
            raise ClarificationNeeded("Arc length is greater than the full circle circumference for this radius.")
        if start_angle is not None and end_angle is None:
            end_angle = start_angle + sweep_angle
        elif end_angle is not None and start_angle is None:
            start_angle = end_angle - sweep_angle
        elif start_angle is None and end_angle is None:
            center_angle = _direction_angle(text)
            start_angle = center_angle - sweep_angle / 2
            end_angle = center_angle + sweep_angle / 2
    return GeometryObject(
        id=_next_id(doc, "A"),
        type="arc",
        center=_center(text, [100, 100]),
        radius=radius,
        start_angle=start_angle if start_angle is not None else 0,
        end_angle=end_angle if end_angle is not None else 90,
    )


def _right_side_line(doc: GeometryDocument, text: str) -> GeometryObject:
    circle = next((obj for obj in reversed(doc.objects) if obj.type == "circle"), None)
    if circle is None:
        raise ClarificationNeeded("Please create a circle before referencing its right side.")
    length = _keyword_number(text, "line") or _keyword_number(text, "length")
    nums = _numbers(text)
    if length is None:
        length = nums[-1] if nums else None
    length = _require(length, "Please provide the line length.")
    cx, cy = circle.center or [100, 100]
    start_x = cx + float(circle.radius or 0)
    return GeometryObject(id=_next_id(doc, "L"), type="line", start=[start_x, cy], end=[start_x + length, cy])


def _line_from_arc_point(doc: GeometryDocument, text: str) -> GeometryObject:
    id_match = re.search(r"\b([aA]\d+)\b", text)
    arc = next(
        (
            obj
            for obj in reversed(doc.objects)
            if obj.type == "arc" and (id_match is None or obj.id.lower() == id_match.group(1).lower())
        ),
        None,
    )
    if arc is None:
        raise ClarificationNeeded("Please create or identify an existing arc, such as A1.")

    if re.search(r"\b(?:middle|midpoint|mid\s+point|center\s+point)\b", text):
        arc_point = "middle"
    elif re.search(r"\bstart(?:ing)?\s+point\b", text):
        arc_point = "start"
    else:
        arc_point = "end"
    start = _arc_point(arc, arc_point)
    length = _length_number(text) or _keyword_number(text, "line")
    nums = _numbers(text)
    if length is None and nums:
        length = next((num for num in nums if num > 0), None)
    length = _require(length, "Please provide the line length.")
    angle = _line_angle_from_text(text)
    line = GeometryObject(id=_next_id(doc, "L"), type="line", start=[0, 0], end=[1, 0])
    _set_line_from_start_length_angle(line, start, length, angle)
    return line


def _circle_tangent_line(doc: GeometryDocument, text: str) -> GeometryObject:
    id_match = re.search(r"\b([cC]\d+)\b", text)
    circle = next(
        (
            obj
            for obj in reversed(doc.objects)
            if obj.type == "circle" and (id_match is None or obj.id.lower() == id_match.group(1).lower())
        ),
        None,
    )
    if circle is None:
        raise ClarificationNeeded("Please create or identify a circle for the tangent line.")

    cx, cy = circle.center or [100, 100]
    radius = float(circle.radius or (circle.diameter or 0) / 2)
    if radius <= 0:
        raise ClarificationNeeded("Please provide the circle radius or diameter before drawing a tangent.")

    horizontal = "x axis" in text or "horizontal" in text or "parallel to x" in text
    vertical = "y axis" in text or "vertical" in text or "parallel to y" in text

    length = _length_number(text)
    half_length = (length / 2) if length is not None else radius

    if "lower" in text or "bottom" in text or "below" in text:
        y = cy - radius
        return GeometryObject(id=_next_id(doc, "L"), type="line", start=[cx - half_length, y], end=[cx + half_length, y])
    if "upper" in text or "top" in text or "above" in text:
        y = cy + radius
        return GeometryObject(id=_next_id(doc, "L"), type="line", start=[cx - half_length, y], end=[cx + half_length, y])
    if "right" in text:
        x = cx + radius
        return GeometryObject(id=_next_id(doc, "L"), type="line", start=[x, cy - radius], end=[x, cy + radius])
    if "left" in text:
        x = cx - radius
        return GeometryObject(id=_next_id(doc, "L"), type="line", start=[x, cy - radius], end=[x, cy + radius])
    if horizontal:
        y = cy - radius
        return GeometryObject(id=_next_id(doc, "L"), type="line", start=[cx - half_length, y], end=[cx + half_length, y])
    if vertical:
        x = cx + radius
        return GeometryObject(id=_next_id(doc, "L"), type="line", start=[x, cy - radius], end=[x, cy + radius])
    raise ClarificationNeeded("Please specify which side of the circle needs the tangent: upper, lower, left, or right.")


def _line_from_tangent_edge(doc: GeometryDocument, text: str) -> GeometryObject:
    tangent = _tangent_reference_line(doc)
    if tangent is None:
        raise ClarificationNeeded("Please create the tangent line first.")
    side = "left" if "left" in text else "right" if "right" in text else "right"
    start = _line_edge(tangent, side)
    length = _length_number(text) or 100
    angle = _angle_number(text)
    if angle is None:
        raise ClarificationNeeded("Please provide the line angle.")
    line = GeometryObject(id=_next_id(doc, "L"), type="line", start=[0, 0], end=[1, 0])
    _set_line_from_start_length_angle(line, start, length, angle)
    return line


def _edit_line(doc: GeometryDocument, text: str) -> ParseIntent | None:
    if not re.search(r"\b(edit|change|modify|set)\b", text) or "line" not in text:
        return None
    line_id = _line_id_from_text(text)
    if line_id is None:
        raise ClarificationNeeded("Please provide the line id, such as L2.")
    target = next((obj for obj in doc.objects if obj.id.lower() == line_id.lower() and obj.type == "line"), None)
    if target is None:
        raise ClarificationNeeded(f"Line {line_id} was not found.")

    start = target.start or [0, 0]
    if "tangent" in text:
        tangent = _tangent_reference_line(doc, exclude_id=target.id)
        if tangent is None:
            raise ClarificationNeeded("Please create the tangent line first.")
        side = "left" if "left" in text else "right" if "right" in text else "right"
        start = _line_edge(tangent, side)

    length = _length_number(text) or _line_length(target)
    angle = _angle_number(text)
    if angle is None:
        angle = _line_angle(target)
    _set_line_from_start_length_angle(target, start, length, angle)
    return ParseIntent(doc, [])


def _append_shape(doc: GeometryDocument, text: str) -> None:
    if "line" in text and "tangent" in text and "edge" in text:
        doc.objects.append(_line_from_tangent_edge(doc, text))
    elif "tangent" in text and "circle" in text:
        doc.objects.append(_circle_tangent_line(doc, text))
    elif "line" in text and "arc" in text and re.search(r"\b(?:(?:start|end)(?:ing)?\s+point|middle|midpoint|mid\s+point|center\s+point)\b", text):
        doc.objects.append(_line_from_arc_point(doc, text))
    elif ("semicircle" in text or "semi circle" in text or "half circle" in text) and "capsule" not in text:
        doc.objects.append(_semicircle(doc, text))
    elif "arc" in text:
        doc.objects.append(_arc(doc, text))
    elif "circle" in text:
        doc.objects.append(_circle(doc, text))
    elif "line" in text and "right side" in text:
        doc.objects.append(_right_side_line(doc, text))
    elif "line" in text:
        doc.objects.append(_line(doc, text))
    elif "ellipse" in text:
        doc.objects.append(_ellipse(doc, text))
    elif "parabola" in text:
        doc.objects.append(_parabola(doc, text))
    elif "slot" in text or "capsule" in text:
        doc.objects.append(_slot(doc, text))
    elif "rectangle" in text:
        doc.objects.append(_rectangle(doc, text))
    else:
        raise ClarificationNeeded("Please describe a supported shape: circle, line, semicircle, ellipse, parabola, slot, rectangle, or arc.")


def parse_prompt(prompt: str, current: GeometryDocument | None = None) -> ParseIntent:
    text = re.sub(r"\s+", " ", prompt.lower().strip())
    doc = _base(current)
    warnings: list[str] = []

    if not text:
        raise ClarificationNeeded("Please enter a drawing instruction.")

    edit_result = _edit_line(doc, text)
    if edit_result is not None:
        return edit_result

    export_match = re.search(r"\bexport\b.*\b(svg|png|pdf|dxf|json|csv)\b", text)
    if export_match:
        return ParseIntent(doc, warnings, action="export", export_format=export_match.group(1))

    delete_match = re.search(r"\bdelete\s+(?:shape\s+)?([a-z]+\d+)\b", text)
    if delete_match:
        shape_id = delete_match.group(1)
        before = len(doc.objects)
        doc.objects = [obj for obj in doc.objects if obj.id.lower() != shape_id.lower()]
        if len(doc.objects) == before:
            raise ClarificationNeeded(f"Shape {shape_id.upper()} was not found.")
        return ParseIntent(doc, warnings)

    resize_match = re.search(r"\b(?:increase|set|change)\s+(?:circle\s+)?([a-z]+\d+)?\s*(?:circle\s+)?radius\s*(?:to)?\s*(" + NUMBER + r")\b", text)
    if resize_match and "circle" in text:
        target = _target_shape(doc, resize_match.group(1))
        if target is None or target.type != "circle":
            raise ClarificationNeeded("Please provide an existing circle id, such as C1.")
        target.radius = float(resize_match.group(2))
        GeometryObject.model_validate(target.model_dump())
        return ParseIntent(doc, warnings)

    move_match = re.search(r"\bmove\s+(?:(selected)\s+shape|shape\s+([a-z]+\d+)|([a-z]+\d+))?.*?\b(" + NUMBER + r")\s*(?:mm|cm|inch)?\s*(right|left|upward|up|downward|down)\b", text)
    if move_match:
        target = _target_shape(doc, move_match.group(2) or move_match.group(3), selected=bool(move_match.group(1)) or "selected" in text)
        if target is None:
            raise ClarificationNeeded("Please select or provide a shape to move.")
        amount = float(move_match.group(4))
        direction = move_match.group(5)
        dx = amount if direction == "right" else -amount if direction == "left" else 0
        dy = -amount if direction in {"up", "upward"} else amount if direction in {"down", "downward"} else 0
        _move_object(target, dx, dy)
        return ParseIntent(doc, warnings)

    if "dimension" in text:
        doc.dimensions["show"] = True
        return ParseIntent(doc, warnings)

    if " and " in text and "one circle" in text and "one line" in text:
        parts = [part.strip(" .") for part in re.split(r"\band\b", text, maxsplit=1)]
        _append_shape(doc, parts[0])
        _append_shape(doc, parts[1])
        return ParseIntent(doc, warnings)

    _append_shape(doc, text)
    GeometryDocument.model_validate(doc.model_dump())
    return ParseIntent(doc, warnings)
