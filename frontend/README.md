# HDRI Tool — Frontend

React 18 + Vite 5 + TypeScript (strict) + Tailwind 3.

## Development

Two terminals:

```bash
# Terminal 1 — FastAPI on :8000
cd ..
.venv/bin/uvicorn app.main:app --reload --port 8000

# Terminal 2 — Vite on :5173 (proxies /api/* to :8000)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Production

```bash
cd frontend
npm run build  # outputs frontend/dist/
```

`app/main.py` automatically mounts `frontend/dist/` at `/` if it exists, so
production deploy is just `uvicorn app.main:app` once the build is in place.

## Notes

- `use-image` was added on top of the PRD-listed dependencies because
  `react-konva` doesn't ship a built-in image-loading helper and we need
  one for the mask editor.
- All API types live in `src/types/api.ts` and mirror `app/schemas.py`;
  keep them in sync when adding endpoints.
