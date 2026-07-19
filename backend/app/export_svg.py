from __future__ import annotations

from html import escape

from .geometry_engine import drawing_data
from .models import GeometryDocument


def _attrs(attrs: dict) -> str:
    return " ".join(f'{k.replace("_", "-")}="{escape(str(v))}"' for k, v in attrs.items() if v is not None)


def render_svg(doc: GeometryDocument, width: int = 1200, height: int = 800) -> str:
    data = drawing_data(doc)
    x1, y1, x2, y2 = data["bbox"]
    pad = 80
    view = f"{x1 - pad} {y1 - pad} {max(x2 - x1 + 2 * pad, 400)} {max(y2 - y1 + 2 * pad, 300)}"
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="{view}">']
    parts.append('<defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="#e5e7eb" stroke-width="0.5"/></pattern></defs>')
    parts.append('<rect width="100%" height="100%" fill="#f8fafc"/><rect width="100%" height="100%" fill="url(#grid)"/>')
    parts.append('<line x1="-10000" y1="0" x2="10000" y2="0" stroke="#94a3b8" stroke-width="1"/><line x1="0" y1="-10000" x2="0" y2="10000" stroke="#94a3b8" stroke-width="1"/>')
    for item in data["objects"]:
        svg = item["svg"]
        parts.append(f'<{svg["tag"]} {_attrs(svg["attrs"])} />')
    parts.append("</svg>")
    return "\n".join(parts)

