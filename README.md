# AI Geometry CAD Assistant

Local desktop-style AI chat CAD application for Windows. It uses FastAPI for geometry parsing, dimensions, exports, and SQLite persistence, plus a React/Vite SVG CAD interface.

## Windows Setup

1. Install Python 3.11+.
2. Install Node.js LTS.
3. Install Ollama.
4. Pull the preferred model:

```bat
ollama pull qwen2.5-coder:7b
```

5. Start Ollama.
6. Run backend from Command Prompt or PowerShell:

```bat
cd /d "C:\Users\Public\BusinessAutomation\AI ChatCAD\AI-Geometry-CAD-Assistant\backend"
run_backend.bat
```

7. Run frontend in another terminal:

```bat
cd /d "C:\Users\Public\BusinessAutomation\AI ChatCAD\AI-Geometry-CAD-Assistant\frontend"
run_frontend.bat
```

8. Open `http://127.0.0.1:5175`.

For another PC or mobile on the same WiFi:

```bat
ipconfig
```

Find your IPv4 address, then open:

```text
http://YOUR_PC_IP:5175
```

The backend listens on `0.0.0.0:8020`, the frontend listens on `0.0.0.0:5175`, and the frontend automatically calls `http://YOUR_PC_IP:8020` when opened from another device.

If Ollama is offline, the backend automatically uses the built-in regex rule parser.

## Drawing Uploads

The Chat tab can attach DXF, SVG, image, and text-like drawing files.

- Summarize uses Ollama when available, with a local file inspection fallback.
- Edit supports safe DXF text-label edits through Groq. It extracts TEXT/MTEXT labels, asks Groq for strict JSON edits, applies exact byte-level replacements only when the old value appears exactly once, then checks the DXF skeleton before returning the edited file.

Set your Groq key before starting the backend:

```bat
set GROQ_API_KEY=your_key_here
```

## Useful URLs

- Frontend: `http://127.0.0.1:5175`
- Backend health: `http://127.0.0.1:8020/health`
- Backend API docs: `http://127.0.0.1:8020/docs`

## Supported Prompt Examples

- `Draw a circle of radius 50 mm at center 100,100.`
- `Draw a half circle of diameter 120 mm facing upward.`
- `Draw a straight line of 300 mm at 45 degrees.`
- `Draw an ellipse with major axis 200 mm and minor axis 100 mm.`
- `Draw an arc radius 80 start angle 0 end angle 120 at center 100,100.`
- `Draw a parabola with width 300 mm and height 150 mm.`
- `Draw a slot of total length 300 mm and width 80 mm.`
- `Draw one rectangle 200 x 100 mm with semicircles on both ends.`
- `Increase circle radius to 75 mm.`
- `Move the shape 20 mm upward.`
