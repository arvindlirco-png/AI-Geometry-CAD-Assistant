# AI Geometry CAD Assistant Test Checklist

Use this checklist after starting the backend on port `8020` and the frontend on port `5175`.

## Start Commands

Backend:

```powershell
cd "C:\Users\Public\BusinessAutomation\AI ChatCAD\AI-Geometry-CAD-Assistant\backend"
.\.venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8020
```

Frontend:

```powershell
cd "C:\Users\Public\BusinessAutomation\AI ChatCAD\AI-Geometry-CAD-Assistant\frontend"
npm run dev
```

Open:

```text
http://127.0.0.1:5175
```

## 1. Backend API Tests

### Health

```powershell
Invoke-RestMethod http://127.0.0.1:8020/health
```

Expected:

```json
{"status":"ok","app":"AI Geometry CAD Assistant"}
```

### AI Status

```powershell
Invoke-RestMethod http://127.0.0.1:8020/ai/status
```

Expected when Ollama is running:

```json
{"connected":true,"models":["..."],"selected_model":"..."}
```

Expected when Ollama is stopped:

```json
{"connected":false,"models":[],"selected_model":null}
```

### Parse

```powershell
$body = @{
  prompt = "Draw a circle of radius 50 mm."
  current_geometry = $null
} | ConvertTo-Json -Depth 20
Invoke-RestMethod http://127.0.0.1:8020/parse -Method Post -ContentType "application/json" -Body $body
```

Expected:

- `success = true`
- `geometry.objects[0].type = "circle"`
- `geometry.objects[0].radius = 50`
- `source = "ollama"` when Ollama is available, otherwise `source = "rule_parser"`

### Clarification

```powershell
$body = @{
  prompt = "Draw a circle."
  current_geometry = $null
} | ConvertTo-Json -Depth 20
Invoke-RestMethod http://127.0.0.1:8020/parse -Method Post -ContentType "application/json" -Body $body
```

Expected:

```json
{
  "success": false,
  "clarification_needed": true,
  "question": "Please provide the radius or diameter."
}
```

### Draw And Dimensions

```powershell
$geometry = @{
  unit = "mm"
  drawing_name = "API Test"
  dimensions = @{ show = $true }
  objects = @(
    @{ id = "C1"; type = "circle"; center = @(100,100); radius = 50 }
  )
} | ConvertTo-Json -Depth 20
Invoke-RestMethod http://127.0.0.1:8020/draw -Method Post -ContentType "application/json" -Body $geometry
```

Expected:

- `drawing.objects[0].type = "circle"`
- `dimensions[0].radius = 50`
- `dimensions[0].diameter = 100`

## 2. Frontend UI Tests

- Open `http://127.0.0.1:5175`.
- Confirm left sidebar appears with icons.
- Confirm top status bar shows backend status and Ollama/rule parser status.
- Toggle dark/light mode and confirm the full UI changes theme.
- Confirm tabs exist: `Chat`, `Drawing`, `Dimensions`, `Shape Data`, `Export`, `Settings`.
- Enter a prompt in `Chat`, send it, and confirm the AI JSON preview updates.
- Collapse and expand the AI JSON preview.
- Click `Approve Geometry JSON` and confirm the app switches to the drawing workflow.
- Confirm prompt example chips populate the prompt box.
- Confirm Settings backend URL defaults to `http://127.0.0.1:8020` on localhost.

## 3. Shape Drawing Tests

For each prompt, send it in Chat, approve the JSON, then inspect the Drawing tab.

| Shape | Prompt | Expected Drawing |
| --- | --- | --- |
| Circle | `Draw a circle of radius 50 mm.` | Circle centered at default `100,100`, radius `50`. |
| Semicircle | `Draw a semicircle diameter 100 mm facing down.` | Down-facing arc, radius `50`. |
| Line | `Draw a line of 300 mm at 45 degrees.` | Line from `0,0` to approximately `212.132,212.132`. |
| Rectangle | `Draw a rectangle 200 mm by 100 mm.` | Rectangle at `0,0`, width `200`, height `100`. |
| Ellipse | `Draw an ellipse with major axis 200 mm and minor axis 100 mm.` | Ellipse centered at default `100,100`, rx `100`, ry `50`. |
| Parabola | `Draw a parabola width 300 mm height 150 mm opening upward.` | Up-opening polyline/parabolic curve, width `300`, height `150`. |
| Slot | `Draw a slot of total length 300 mm and width 80 mm.` | Horizontal slot, length `300`, width `80`, two straight edges and rounded ends. |

Canvas controls:

- Grid toggle hides/shows grid.
- Zoom in/out changes viewport scale.
- Fit resets zoom and pan.
- Dragging canvas pans the view.
- Dimension toggle hides/shows shape labels.

## 4. Dimension Calculation Tests

Expected values are in millimeters unless otherwise noted. Allow small rounding differences, usually `0.001`.

### Circle Radius 50

Prompt:

```text
Draw a circle of radius 50 mm.
```

Expected geometry:

```json
{"type":"circle","center":[100,100],"radius":50}
```

Expected dimensions:

| Field | Expected |
| --- | ---: |
| radius | `50` |
| diameter | `100` |
| area | `7853.982` |
| perimeter | `314.159` |
| bounding_box | `[50,50,150,150]` |

### Semicircle Diameter 100

Prompt:

```text
Draw a semicircle diameter 100 mm facing down.
```

Expected geometry:

```json
{"type":"semicircle","center":[100,100],"radius":50,"direction":"down"}
```

Expected dimensions:

| Field | Expected |
| --- | ---: |
| radius | `50` |
| diameter | `100` |
| area | `3926.991` |
| arc_length | `157.080` |
| chord_length | `100` |
| perimeter | `257.080` |

### Line 300 mm At 45 Degrees

Prompt:

```text
Draw a line of 300 mm at 45 degrees.
```

Expected geometry:

```json
{"type":"line","start":[0,0],"end":[212.132,212.132]}
```

Expected dimensions:

| Field | Expected |
| --- | ---: |
| length | `300` |
| angle | `45` |
| start_point | `[0,0]` |
| end_point | `[212.132,212.132]` |

### Rectangle 200 x 100

Prompt:

```text
Draw a rectangle 200 mm by 100 mm.
```

Expected geometry:

```json
{"type":"rectangle","x":0,"y":0,"width":200,"height":100}
```

Expected dimensions:

| Field | Expected |
| --- | ---: |
| width | `200` |
| height | `100` |
| area | `20000` |
| perimeter | `600` |
| bounding_box | `[0,0,200,100]` |

### Ellipse 200 x 100

Prompt:

```text
Draw an ellipse with major axis 200 mm and minor axis 100 mm.
```

Expected geometry:

```json
{"type":"ellipse","center":[100,100],"major_axis":200,"minor_axis":100}
```

Expected dimensions:

| Field | Expected |
| --- | ---: |
| major_axis | `200` |
| minor_axis | `100` |
| area | `15707.963` |
| perimeter | `484.421` |
| bounding_box | `[0,50,200,150]` |

### Parabola Width 300 Height 150

Prompt:

```text
Draw a parabola width 300 mm height 150 mm opening upward.
```

Expected geometry:

```json
{"type":"parabola","vertex":[0,0],"width":300,"height":150,"direction":"up"}
```

Expected dimensions:

| Field | Expected |
| --- | ---: |
| width | `300` |
| height | `150` |
| bounding_box | `[-150,-150,150,0]` |
| polyline length | Approximately `443.644` |

### Slot Length 300 Width 80

Prompt:

```text
Draw a slot of total length 300 mm and width 80 mm.
```

Expected geometry:

```json
{"type":"slot","center":[0,0],"total_length":300,"width":80,"orientation":"horizontal"}
```

Expected dimensions:

| Field | Expected |
| --- | ---: |
| length | `300` |
| width | `80` |
| area | `22626.548` |
| perimeter | `691.327` |
| bounding_box | `[-150,-40,150,40]` |

## 5. Export Tests

Use the Export tab after approving a drawing that contains all supported shapes.

Required formats:

- SVG downloads `drawing.svg`.
- PNG downloads `drawing.png`.
- PDF downloads `drawing.pdf`.
- DXF downloads `drawing.dxf`.
- JSON downloads `drawing.json`.
- CSV downloads `dimensions.csv`.

API export smoke test:

```powershell
$geometry = @{
  unit = "mm"
  drawing_name = "Export Test"
  dimensions = @{ show = $true }
  objects = @(
    @{ id = "C1"; type = "circle"; center = @(100,100); radius = 50 },
    @{ id = "L1"; type = "line"; start = @(0,0); end = @(300,100) },
    @{ id = "S1"; type = "semicircle"; center = @(260,100); radius = 60; direction = "up" },
    @{ id = "A1"; type = "arc"; center = @(420,100); radius = 80; start_angle = 0; end_angle = 120 },
    @{ id = "E1"; type = "ellipse"; center = @(100,260); major_axis = 200; minor_axis = 100; rotation = 0 },
    @{ id = "P1"; type = "parabola"; vertex = @(300,260); width = 300; height = 150; direction = "up" },
    @{ id = "R1"; type = "rectangle"; x = 0; y = 360; width = 250; height = 120 },
    @{ id = "SL1"; type = "slot"; center = @(420,400); total_length = 300; width = 80; orientation = "horizontal" }
  )
} | ConvertTo-Json -Depth 20

foreach ($format in @("svg","png","pdf","dxf","json","csv")) {
  Invoke-WebRequest "http://127.0.0.1:8020/export/$format" -Method Post -ContentType "application/json" -Body $geometry -OutFile "test-output.$format"
}
```

Expected:

- All files are created and non-empty.
- SVG opens in a browser.
- PNG opens in Photos or browser.
- PDF opens in a PDF reader.
- DXF opens in AutoCAD, LibreCAD, DraftSight, or FreeCAD.
- JSON contains the geometry document.
- CSV contains dimension rows.

DXF-specific expectations:

- Units are millimeters.
- Layers include `SHAPES`, `DIMENSIONS`, `CENTERLINES`, and `TEXT`.
- Circles are real DXF `CIRCLE` entities.
- Lines are real DXF `LINE` entities.
- Arcs and semicircles are real DXF `ARC` entities.
- Slot uses two `LINE` entities plus two `ARC` entities.
- Parabola is a dense polyline approximation.
- Dimension text exists on `DIMENSIONS`.

## 6. Ollama Online Test

Start Ollama and make sure at least one configured model is available.

```powershell
ollama serve
ollama list
```

Then run:

```powershell
$body = @{
  prompt = "Draw a circle of radius 50 mm."
  current_geometry = $null
} | ConvertTo-Json -Depth 20
Invoke-RestMethod http://127.0.0.1:8020/parse -Method Post -ContentType "application/json" -Body $body
```

Expected:

- `success = true`
- `source = "ollama"` if the configured model is available.
- Returned geometry validates as JSON and contains a circle with radius `50`.

Bad prompt online test:

```powershell
$body = @{
  prompt = "Draw a circle."
  current_geometry = $null
} | ConvertTo-Json -Depth 20
Invoke-RestMethod http://127.0.0.1:8020/parse -Method Post -ContentType "application/json" -Body $body
```

Expected:

- `success = false`
- `clarification_needed = true`
- `question = "Please provide the radius or diameter."`

## 7. Ollama Offline Fallback Test

Stop Ollama, or make `http://127.0.0.1:11434` unavailable.

Run:

```powershell
$body = @{
  prompt = "Draw a rectangle 200 mm by 100 mm."
  current_geometry = $null
} | ConvertTo-Json -Depth 20
Invoke-RestMethod http://127.0.0.1:8020/parse -Method Post -ContentType "application/json" -Body $body
```

Expected:

- `success = true`
- `source = "rule_parser"`
- Rectangle width `200`, height `100`.

Run:

```powershell
$body = @{
  prompt = "Draw a circle."
  current_geometry = $null
} | ConvertTo-Json -Depth 20
Invoke-RestMethod http://127.0.0.1:8020/parse -Method Post -ContentType "application/json" -Body $body
```

Expected:

- `success = false`
- `clarification_needed = true`
- No crash.

## 8. Local WiFi Access Test

Find the PC IP:

```powershell
ipconfig
```

Confirm backend is started with:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8020
```

Confirm frontend is started with:

```powershell
npm run dev
```

From another device on the same WiFi:

```text
http://YOUR-PC-IP:5175
```

Expected:

- Frontend loads.
- Backend status shows online.
- Chat prompt parses successfully.
- API URL resolves to `http://YOUR-PC-IP:8020`.
- Browser developer console has no CORS errors.

If blocked:

- Allow Python/Node through Windows Firewall on private networks.
- Confirm both devices are on the same WiFi network.
- Confirm the router does not isolate wireless clients.
