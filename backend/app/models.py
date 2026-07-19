from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


Point = list[float]


class Style(BaseModel):
    stroke: str = "#111827"
    stroke_width: float = 0.5
    fill: str = "none"


class GeometryObject(BaseModel):
    id: str
    type: Literal["circle", "semicircle", "line", "rectangle", "ellipse", "arc", "parabola", "slot"]
    center: Point | None = None
    start: Point | None = None
    end: Point | None = None
    vertex: Point | None = None
    x: float | None = None
    y: float | None = None
    radius: float | None = None
    diameter: float | None = None
    width: float | None = None
    height: float | None = None
    length: float | None = None
    total_length: float | None = None
    major_axis: float | None = None
    minor_axis: float | None = None
    rotation: float = 0
    angle: float | None = None
    start_angle: float | None = None
    end_angle: float | None = None
    direction: Literal["up", "down", "left", "right"] | None = None
    orientation: Literal["horizontal", "vertical"] = "horizontal"
    style: Style = Field(default_factory=Style)

    @model_validator(mode="after")
    def validate_required_geometry(self) -> "GeometryObject":
        if self.radius is None and self.diameter is not None:
            self.radius = self.diameter / 2
        required: dict[str, tuple[str, ...]] = {
            "circle": ("center", "radius"),
            "semicircle": ("center", "radius", "direction"),
            "line": ("start", "end"),
            "rectangle": ("x", "y", "width", "height"),
            "ellipse": ("center", "major_axis", "minor_axis"),
            "arc": ("center", "radius", "start_angle", "end_angle"),
            "parabola": ("vertex", "width", "height", "direction"),
            "slot": ("center", "total_length", "width", "orientation"),
        }
        missing = [field for field in required[self.type] if getattr(self, field) is None]
        if missing:
            raise ValueError(f"{self.type} is missing required field(s): {', '.join(missing)}")
        if self.radius is not None and self.radius <= 0:
            raise ValueError("radius must be greater than zero")
        for field in ("width", "height", "total_length", "major_axis", "minor_axis"):
            value = getattr(self, field)
            if value is not None and value <= 0:
                raise ValueError(f"{field} must be greater than zero")
        return self


class GeometryDocument(BaseModel):
    unit: Literal["mm", "cm", "inch"] = "mm"
    drawing_name: str = "Untitled Drawing"
    objects: list[GeometryObject] = Field(default_factory=list)
    dimensions: dict[str, Any] = Field(default_factory=lambda: {"show": True})


class ParseRequest(BaseModel):
    prompt: str
    current_geometry: GeometryDocument | None = None


class ParseResponse(BaseModel):
    success: bool
    source: str
    geometry: GeometryDocument | None = None
    warnings: list[str] = Field(default_factory=list)
    clarification_needed: bool = False
    question: str | None = None
    action: Literal["draw", "export"] = "draw"
    export_format: Literal["svg", "png", "pdf", "dxf", "json", "csv"] | None = None


class SaveRequest(BaseModel):
    name: str
    geometry: GeometryDocument
    chat_history: list[dict[str, Any]] = Field(default_factory=list)
