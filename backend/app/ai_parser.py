from __future__ import annotations

import json
import re
from typing import Any

import httpx
from pydantic import ValidationError

from .models import GeometryDocument, ParseResponse
from .rule_parser import ClarificationNeeded, parse_prompt
from .settings import settings


SYSTEM_PROMPT = """You convert natural language CAD geometry instructions into valid JSON only.
No markdown. No explanation. Return one JSON object only.
If required values are missing, return exactly:
{"success":false,"clarification_needed":true,"question":"Please provide the radius or diameter."}
For valid drawing commands return a complete geometry document JSON with unit, drawing_name, objects, and dimensions.
Supported object types and required fields:
circle: id,type,center,radius
line: id,type,start,end
semicircle: id,type,center,radius,direction
ellipse: id,type,center,major_axis,minor_axis,rotation
arc: id,type,center,radius,start_angle,end_angle
parabola: id,type,vertex,width,height,direction
rectangle: id,type,x,y,width,height
slot/capsule: id,type,center,total_length,width,orientation
Use only these type values: circle, line, semicircle, ellipse, arc, parabola, rectangle, slot.
For an arc with arc_length, calculate sweep_angle_degrees = arc_length / radius * 180 / pi, then set start_angle and end_angle. Center facing up at 90 degrees, right at 0, down at 270, left at 180."""


async def ai_status() -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            response = await client.get(f"{settings.ollama_url}/api/tags")
            response.raise_for_status()
        names = [m.get("name") for m in response.json().get("models", [])]
        model = settings.preferred_model if settings.preferred_model in names else settings.fallback_model if settings.fallback_model in names else None
        return {"connected": True, "models": names, "selected_model": model}
    except Exception as exc:
        return {"connected": False, "models": [], "selected_model": None, "error": str(exc)}


def _extract_json(text: str) -> dict[str, Any] | None:
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    candidates = [cleaned]
    match = re.search(r"\{.*\}", cleaned, flags=re.S)
    if match:
        candidates.append(match.group())
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def _document_from_ai(parsed: dict[str, Any], current: GeometryDocument | None) -> GeometryDocument:
    if "geometry" in parsed and isinstance(parsed["geometry"], dict):
        return GeometryDocument.model_validate(parsed["geometry"])
    if "objects" in parsed:
        return GeometryDocument.model_validate(parsed)
    if "type" in parsed:
        doc = current.model_copy(deep=True) if current else GeometryDocument()
        doc.objects.append(parsed)
        return GeometryDocument.model_validate(doc.model_dump())
    if "object" in parsed and isinstance(parsed["object"], dict):
        doc = current.model_copy(deep=True) if current else GeometryDocument()
        doc.objects.append(parsed["object"])
        return GeometryDocument.model_validate(doc.model_dump())
    raise ValueError("AI response is not a geometry document or object.")


def _rule_response(prompt: str, current: GeometryDocument | None, warnings: list[str] | None = None) -> ParseResponse:
    try:
        result = parse_prompt(prompt, current)
        return ParseResponse(
            success=True,
            source="rule_parser",
            geometry=GeometryDocument.model_validate(result.geometry.model_dump()),
            warnings=[*(warnings or []), *result.warnings],
            action=result.action,  # type: ignore[arg-type]
            export_format=result.export_format,  # type: ignore[arg-type]
        )
    except ClarificationNeeded as exc:
        return ParseResponse(
            success=False,
            source="rule_parser",
            geometry=current,
            warnings=warnings or [],
            clarification_needed=True,
            question=exc.question,
        )
    except (ValidationError, ValueError) as exc:
        return ParseResponse(
            success=False,
            source="rule_parser",
            geometry=current,
            warnings=[*(warnings or []), f"Validation failed: {exc}"],
            clarification_needed=True,
            question="Please provide complete valid geometry values.",
        )


async def parse_with_ai(prompt: str, current: GeometryDocument | None = None) -> ParseResponse:
    status = await ai_status()
    if not status["connected"] or not status["selected_model"]:
        return _rule_response(prompt, current)

    schema_hint = {
        "unit": "mm",
        "drawing_name": "Untitled Drawing",
        "objects": [
            {"id": "C1", "type": "circle", "center": [100, 100], "radius": 50},
            {"id": "L1", "type": "line", "start": [0, 0], "end": [300, 0]},
            {"id": "S1", "type": "semicircle", "center": [100, 100], "radius": 60, "direction": "up"},
            {"id": "E1", "type": "ellipse", "center": [100, 100], "major_axis": 200, "minor_axis": 100, "rotation": 0},
            {"id": "A1", "type": "arc", "center": [100, 100], "radius": 80, "start_angle": 0, "end_angle": 120},
            {"id": "P1", "type": "parabola", "vertex": [0, 0], "width": 300, "height": 150, "direction": "up"},
            {"id": "R1", "type": "rectangle", "x": 0, "y": 0, "width": 200, "height": 100},
            {"id": "SL1", "type": "slot", "center": [0, 0], "total_length": 300, "width": 80, "orientation": "horizontal"},
        ],
        "dimensions": {"show": True},
    }
    user_prompt = (
        "Return only valid JSON. Return a complete geometry document, or the clarification JSON if the request is missing required values. "
        f"Schema examples: {json.dumps(schema_hint)}\n"
        f"Current geometry: {current.model_dump_json() if current else '{}'}\n"
        f"Instruction: {prompt}"
    )
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{settings.ollama_url}/api/chat",
                json={
                    "model": status["selected_model"],
                    "stream": False,
                    "format": "json",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                },
            )
            response.raise_for_status()
        raw = response.json().get("message", {}).get("content", "")
        parsed = _extract_json(raw)
        if parsed:
            if parsed.get("success") is False and parsed.get("clarification_needed"):
                return ParseResponse(
                    success=False,
                    source="ollama",
                    geometry=current,
                    clarification_needed=True,
                    question=parsed.get("question") or "Please provide complete geometry values.",
                )
            geometry = _document_from_ai(parsed, current)
            return ParseResponse(success=True, source="ollama", geometry=geometry)
    except Exception:
        ai_error = "Ollama did not return valid geometry in time."
    else:
        ai_error = "Ollama returned no JSON content."
    return _rule_response(prompt, current, [ai_error])
