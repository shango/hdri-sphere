# HDRI Tool

Convert on-set chrome ball EXR plates into equirectangular HDRI environment
maps for image-based lighting in Maya, Houdini, Blender, Nuke, and Unreal.

A 30–60 minute manual Photoshop+Nuke workflow becomes a 1–3 minute automated
pipeline that preserves real on-set HDR data while removing the photographer
and tripod reflection.

## Architecture

- **`core/`** — Pure-Python image pipeline (no web framework imports).
  Importable from both the CLI and the FastAPI app.
- **`app/`** — FastAPI backend serving `/api/*` endpoints and the built React
  app at `/`.
- **`frontend/`** — React 18 + Vite 5 + TypeScript single-page app.
- **`scripts/`** — Standalone CLI for running the pipeline without HTTP, plus
  a synthetic test-ball generator.
- **`tests/`** — Pytest suite covering the core pipeline.

## Pipeline (the work `core/` performs)

1. **Load** 32-bit EXR (`core/exr_io.py`).
2. **Detect** the chrome ball with HoughCircles + boundary-gradient scoring
   (`core/ball_detect.py`); manual override available.
3. **Estimate** the photographer/tripod mask from a geometric prior plus
   darkness + edge-density signals (`core/mask_estimate.py`).
4. **Inpaint** the masked region in log-space — choose a tier
   (`core/inpaint/{boundary,frequency,patchmatch}.py`):
   - `fast` (~0.3 s) — Navier-Stokes boundary extension
   - `good` (~2 s) — Frequency split: NS on the low band, radial median on
     the high band
   - `best` (~8 s) — PatchMatch exemplar fill (vectorized fallback if the
     C library isn't installed)
5. **Unwrap** mirror-ball → equirectangular (`core/unwrap.py`).
6. **Composite** with feathered mask edges; preserve outside-mask values
   exactly (`core/hdr_utils.py`).

## Local development

Two terminals.

### Terminal 1 — backend

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Terminal 2 — frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api/*` to FastAPI at `:8000`.

### CLI (no web)

```bash
python -m scripts.generate_test_ball /tmp/synth.exr --size 2048 --photog
python -m scripts.cli process /tmp/synth.exr /tmp/out.exr \
    --technique good --width 4096 --height 2048
```

### Tests

```bash
pytest
```

## Production build (single origin)

```bash
cd frontend && npm run build
cd .. && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`app/main.py` mounts `frontend/dist/` at `/` whenever the directory exists,
so the SPA and API are served from the same origin.

## Railway deployment

Railway is configured via `railway.toml` and `nixpacks.toml`:

- `nixpacks.toml` provisions Python 3.11 + Node, installs the system
  OpenEXR libraries, runs `pip install -r requirements.txt`, then
  `cd frontend && npm ci && npm run build`.
- `railway.toml` sets the start command to `uvicorn app.main:app` and
  configures the `/api/health` healthcheck.

To deploy:

```bash
git init                  # if not already a repo
git add .
git commit -m "Initial commit"
git remote add origin <github-url>
git push -u origin main
```

Connect the GitHub repo in the Railway dashboard. Subsequent deploys are
just `git push`.

## Environment variables

See `.env.example`:

| Variable              | Default | Notes                                      |
|-----------------------|---------|--------------------------------------------|
| `PORT`                | 8000    | Set automatically by Railway.              |
| `MAX_UPLOAD_SIZE_MB`  | 200     | Reject EXR uploads above this size.        |
| `PROJECT_TTL_HOURS`   | 24      | Auto-delete projects older than this.      |
| `LOG_LEVEL`           | INFO    | Standard Python logging level.             |
| `HDRI_UPLOAD_ROOT`    | /tmp/hdri_uploads | Override upload directory.       |

## Limitations

- The blind spot at the back of the ball is always approximated; no
  technique recovers what the camera didn't capture.
- Plates below ~1024×1024 will produce visibly smeared equirects.
- Highly reflective on-set environments may produce inpaint artifacts.
