from __future__ import annotations

import base64
import io
import json
import mimetypes
import re
from pathlib import Path
from typing import Any, Literal

import ezdxf
import httpx
from PIL import Image
from pydantic import BaseModel, Field

from .ai_parser import _extract_json, ai_status
from .settings import settings


class DrawingFileResponse(BaseModel):
    success: bool
    action: Literal["summarize", "edit"]
    source: str
    filename: str
    summary: str
    warnings: list[str] = Field(default_factory=list)
    edits: list[dict[str, str]] = Field(default_factory=list)
    edited_filename: str | None = None
    edited_content_type: str | None = None
    edited_base64: str | None = None


def _decode_text(data: bytes) -> str:
    return _decode_with_encoding(data)[0]


def _decode_with_encoding(data: bytes) -> tuple[str, str]:
    try:
        return data.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return data.decode("latin-1"), "latin-1"


def _text_labels_from_dxf(data: bytes) -> list[str]:
    doc = ezdxf.read(io.StringIO(_decode_text(data)))
    labels: list[str] = []
    for entity in doc.modelspace().query("TEXT MTEXT"):
        if entity.dxftype() == "MTEXT":
            value = entity.plain_text()
        else:
            value = entity.dxf.text
        cleaned = " ".join(str(value).split())
        if cleaned:
            labels.append(cleaned)
    return labels


def _raw_text_labels_from_dxf(data: bytes) -> list[str]:
    lines = _decode_text(data).splitlines()
    labels: list[str] = []
    index = 0
    while index < len(lines) - 1:
        code = lines[index].strip()
        value = lines[index + 1].strip()
        if code == "0" and value in {"TEXT", "MTEXT"}:
            index += 2
            chunks: list[str] = []
            while index < len(lines) - 1:
                next_code = lines[index].strip()
                next_value = lines[index + 1].strip()
                if next_code == "0":
                    break
                if next_code in {"1", "3"} and next_value:
                    chunks.append(next_value)
                index += 2
            label = " ".join(" ".join(chunks).split())
            if label:
                labels.append(label)
            continue
        index += 2
    return labels


def _safe_text_labels_from_dxf(data: bytes) -> tuple[list[str], list[str]]:
    try:
        return _text_labels_from_dxf(data), []
    except Exception as exc:
        labels = _raw_text_labels_from_dxf(data)
        return labels, [f"DXF parser warning: {exc}. Used raw TEXT/MTEXT label scan instead."]


def _dxf_entity_counts(data: bytes) -> dict[str, int]:
    doc = ezdxf.read(io.StringIO(_decode_text(data)))
    counts: dict[str, int] = {}
    for entity in doc.modelspace():
        counts[entity.dxftype()] = counts.get(entity.dxftype(), 0) + 1
    return counts


def _raw_dxf_entity_counts(data: bytes) -> dict[str, int]:
    known_entities = {
        "ARC",
        "CIRCLE",
        "ELLIPSE",
        "HATCH",
        "INSERT",
        "LINE",
        "LWPOLYLINE",
        "MTEXT",
        "POINT",
        "POLYLINE",
        "SOLID",
        "SPLINE",
        "TEXT",
    }
    lines = _decode_text(data).splitlines()
    counts: dict[str, int] = {}
    for index in range(0, len(lines) - 1, 2):
        if lines[index].strip() == "0":
            value = lines[index + 1].strip()
            if value in known_entities:
                counts[value] = counts.get(value, 0) + 1
    return counts


def _safe_dxf_entity_counts(data: bytes) -> tuple[dict[str, int], list[str]]:
    try:
        return _dxf_entity_counts(data), []
    except Exception as exc:
        counts = _raw_dxf_entity_counts(data)
        return counts, [f"DXF entity parser warning: {exc}. Used raw entity count scan instead."]


def _dxf_skeleton(data: bytes) -> dict[str, int]:
    text = _decode_text(data)
    return {
        "lines": len(text.splitlines()),
        "SECTION": len(re.findall(r"(?im)^\s*SECTION\s*$", text)),
        "ENDSEC": len(re.findall(r"(?im)^\s*ENDSEC\s*$", text)),
        "ENTITIES": len(re.findall(r"(?im)^\s*ENTITIES\s*$", text)),
        "EOF": len(re.findall(r"(?im)^\s*EOF\s*$", text)),
    }


def _extension(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def _summarize_locally(filename: str, data: bytes) -> tuple[str, list[str]]:
    ext = _extension(filename)
    warnings: list[str] = []
    if ext == "dxf":
        labels, label_warnings = _safe_text_labels_from_dxf(data)
        counts, count_warnings = _safe_dxf_entity_counts(data)
        warnings.extend(label_warnings)
        warnings.extend(count_warnings)
        label_text = ", ".join(labels[:20]) if labels else "none"
        if len(labels) > 20:
            label_text += f", plus {len(labels) - 20} more"
        return (
            f"DXF drawing with {sum(counts.values())} model-space entities. "
            f"Entity counts: {counts}. Text labels found: {len(labels)} ({label_text}).",
            warnings,
        )
    if ext in {"svg", "txt", "csv", "json"}:
        text = _decode_text(data)
        lines = text.splitlines()
        preview = " ".join(line.strip() for line in lines[:12] if line.strip())
        return f"{ext.upper()} file with {len(lines)} line(s), {len(data)} bytes. Preview: {preview[:900]}", warnings
    try:
        with Image.open(io.BytesIO(data)) as image:
            return f"Raster drawing/image: {image.format or ext.upper()}, {image.width} x {image.height} px, mode {image.mode}.", warnings
    except Exception:
        warnings.append("Unsupported drawing format for deep inspection.")
        return f"Uploaded {filename} ({len(data)} bytes).", warnings


async def _ollama_summarize(filename: str, data: bytes, local_summary: str) -> tuple[str | None, str | None]:
    status = await ai_status()
    if not status["connected"] or not status["selected_model"]:
        return None, "Ollama is offline or has no selected model."
    ext = _extension(filename)
    if ext == "dxf":
        labels, _ = _safe_text_labels_from_dxf(data)
        prompt = (
            "Summarize this CAD drawing for a machinist/designer. Be concise and mention visible dimensions, labels, "
            f"and likely edit targets.\nFile: {filename}\nLocal inspection: {local_summary}\nText labels: {json.dumps(labels[:80])}"
        )
        payload: dict[str, Any] = {
            "model": status["selected_model"],
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
        }
    else:
        content_type = mimetypes.guess_type(filename)[0] or ""
        is_image = content_type.startswith("image/")
        payload = {
            "model": status["selected_model"],
            "stream": False,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Summarize this uploaded drawing/image. Describe visible geometry, dimensions, labels, and likely editable text. "
                        f"File: {filename}. Local inspection: {local_summary}"
                    ),
                    **({"images": [base64.b64encode(data).decode("ascii")]} if is_image else {}),
                }
            ],
        }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{settings.ollama_url}/api/chat", json=payload)
            response.raise_for_status()
        content = response.json().get("message", {}).get("content", "").strip()
        return content or None, None
    except Exception as exc:
        return None, f"Ollama summary failed: {exc}"


async def summarize_drawing_file(filename: str, data: bytes) -> DrawingFileResponse:
    warnings: list[str] = []
    local_summary, local_warnings = _summarize_locally(filename, data)
    warnings.extend(local_warnings)
    ai_summary, ai_warning = await _ollama_summarize(filename, data, local_summary)
    if ai_warning:
        warnings.append(ai_warning)
    return DrawingFileResponse(
        success=True,
        action="summarize",
        source="ollama" if ai_summary else "local",
        filename=filename,
        summary=ai_summary or local_summary,
        warnings=warnings,
    )


async def _ask_groq_for_edits(labels: list[str], instruction: str) -> tuple[list[dict[str, str]], str | None]:
    if not settings.groq_api_key:
        return [], "GROQ_API_KEY is not configured; edit suggestions are unavailable."
    prompt = (
        "You edit CAD DXF text labels. Return strict JSON only with this shape: "
        '{"edits":[{"old_value":"exact existing label","new_value":"replacement label","reason":"short reason"}]}. '
        "Only propose edits when old_value exactly matches one supplied label. Do not alter geometry.\n"
        f"Instruction: {instruction}\nLabels: {json.dumps(labels, ensure_ascii=False)}"
    )
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={
                    "model": settings.groq_model,
                    "temperature": 0,
                    "messages": [
                        {"role": "system", "content": "Return valid JSON only. Never include markdown."},
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]
        parsed = _extract_json(raw) or {}
        edits = parsed.get("edits", [])
        if not isinstance(edits, list):
            return [], "Groq returned JSON without an edits list."
        valid_edits: list[dict[str, str]] = []
        for edit in edits:
            if isinstance(edit, dict) and edit.get("old_value") and edit.get("new_value"):
                valid_edits.append(
                    {
                        "old_value": str(edit["old_value"]),
                        "new_value": str(edit["new_value"]),
                        "reason": str(edit.get("reason") or "Requested edit"),
                    }
                )
        return valid_edits, None
    except Exception as exc:
        return [], f"Groq edit request failed: {exc}"


def _apply_exact_dxf_edits(data: bytes, edits: list[dict[str, str]]) -> tuple[bytes, list[dict[str, str]], list[str]]:
    _, encoding = _decode_with_encoding(data)
    original_skeleton = _dxf_skeleton(data)
    applied: list[dict[str, str]] = []
    warnings: list[str] = []
    edited_data = data
    for edit in edits:
        old_value = edit["old_value"].encode(encoding)
        new_value = edit["new_value"].encode(encoding)
        count = edited_data.count(old_value)
        if count != 1:
            warnings.append(f"Skipped '{edit['old_value']}' because it appears {count} time(s); expected exactly once.")
            continue
        edited_data = edited_data.replace(old_value, new_value, 1)
        applied.append(edit)
    if applied and _dxf_skeleton(edited_data) != original_skeleton:
        return data, [], ["Aborted edit because the DXF structural skeleton changed unexpectedly."]
    return edited_data, applied, warnings


async def edit_drawing_file(filename: str, data: bytes, instruction: str) -> DrawingFileResponse:
    ext = _extension(filename)
    if ext != "dxf":
        summary = "Editing is currently supported for DXF text labels only. Use Summarize for raster images and other drawing formats."
        return DrawingFileResponse(success=False, action="edit", source="local", filename=filename, summary=summary, warnings=[summary])
    labels, label_warnings = _safe_text_labels_from_dxf(data)
    edits, warning = await _ask_groq_for_edits(labels, instruction)
    warnings = [*label_warnings, *([warning] if warning else [])]
    edited_data, applied, apply_warnings = _apply_exact_dxf_edits(data, edits)
    warnings.extend(apply_warnings)
    if not applied:
        return DrawingFileResponse(
            success=False,
            action="edit",
            source="groq" if settings.groq_api_key else "local",
            filename=filename,
            summary="No safe edits were applied.",
            warnings=warnings,
            edits=edits,
        )
    output_name = f"{Path(filename).stem}_edited.dxf"
    return DrawingFileResponse(
        success=True,
        action="edit",
        source="groq",
        filename=filename,
        summary=f"Applied {len(applied)} safe DXF text edit(s). Geometry entities were not reshaped.",
        warnings=warnings,
        edits=applied,
        edited_filename=output_name,
        edited_content_type="application/dxf",
        edited_base64=base64.b64encode(edited_data).decode("ascii"),
    )
