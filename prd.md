# PRD: Chrome Ball to HDRI Conversion Tool

## Document Purpose

This PRD is written for implementation by Claude Code in a command-line workflow. It is intentionally specific about file structures, function signatures, and architectural decisions. Algorithm choices, library choices, and packaging decisions are stated as **decisions already made** — when you encounter a choice, follow what's specified here unless it's technically impossible.

**For Claude Code: Read this entire document before writing any code. Implement in the phases listed in the Build Order section. After completing each phase, stop and ask the human to test before proceeding to the next phase.**

---

## 1. Product Overview

### 1.1 What This Is

A web application that converts on-set chrome ball reference plates (32-bit EXR) into HDRI environment maps (equirectangular EXR) suitable for image-based lighting in DCC applications (Maya, Houdini, Blender, Nuke, Unreal Engine).

### 1.2 Who It's For

VFX artists and lighting TDs who shoot chrome ball references on set and need to convert them into usable HDRIs without manually compositing the photographer/tripod reflection out of every plate.

### 1.3 Core Value Proposition

Replace a 30-60 minute manual Photoshop+Nuke workflow with a 1-3 minute automated pipeline that preserves real on-set HDR data while removing photographer/tripod reflections.

### 1.4 What This Is Not (Scope Boundaries)

- **Not a full HDRI editing suite** — single-purpose tool for chrome ball processing
- **Not a synthetic HDRI generator** — does not hallucinate environments from LDR (DiffusionLight territory)
- **Not a multi-bracket merger** — assumes input EXR is already a single 32-bit linear plate
- **Not a tone mapping tool** — outputs scene-referred linear HDR only

---

## 2. Technical Architecture

### 2.1 Deployment Target

- **Hosting:** Railway (single service, Python web app)
- **Deployment method:** `git push` to Railway-connected GitHub repo
- **Runtime:** Python 3.11
- **No GPU required** — CPU-only inference for all classical algorithms
- **Storage:** Railway volume for temporary EXR files (or S3-compatible if user adds it later)

### 2.2 Application Structure

```
hdri-tool/
├── app/                              # Python backend
│   ├── __init__.py
│   ├── main.py                       # FastAPI app entrypoint
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── upload.py                 # File upload handling
│   │   ├── process.py                # Processing job endpoints
│   │   ├── preview.py                # Preview rendering endpoints
│   │   └── download.py               # Final EXR download
│   └── workers/
│       ├── __init__.py
│       └── job_runner.py             # Background job execution
├── core/                             # Image processing pipeline (no web deps)
│   ├── __init__.py
│   ├── exr_io.py                     # EXR read/write
│   ├── ball_detect.py                # Sphere detection in plate
│   ├── mask_estimate.py              # Auto photographer mask
│   ├── inpaint/
│   │   ├── __init__.py
│   │   ├── base.py                   # Inpainter Protocol
│   │   ├── boundary.py               # cv2.inpaint Telea/NS
│   │   ├── frequency.py              # Frequency-aware fill
│   │   ├── radial.py                 # Radial sampling fill
│   │   └── patchmatch.py             # Exemplar-based fill
│   ├── unwrap.py                     # Mirror-ball → equirectangular
│   ├── hdr_utils.py                  # Tone mapping, log space, compositing
│   └── project.py                    # HDRIProject state container
├── frontend/                         # React + Vite + TypeScript frontend
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── index.html
│   ├── public/
│   │   └── favicon.ico
│   ├── src/
│   │   ├── main.tsx                  # React entrypoint
│   │   ├── App.tsx                   # Top-level layout
│   │   ├── components/
│   │   │   ├── Uploader.tsx          # Drag-and-drop EXR upload
│   │   │   ├── MaskEditor.tsx        # Konva-based mask painter
│   │   │   ├── PreviewPanel.tsx      # Main preview area
│   │   │   ├── CompareView.tsx       # Before/after slider
│   │   │   ├── ViewModeSelector.tsx  # Original/Mask/Inpainted/Compare
│   │   │   ├── TechniquePanel.tsx    # Fast/Good/Best radio buttons
│   │   │   ├── ExposureSlider.tsx    # Exposure adjustment
│   │   │   ├── BrushControls.tsx     # Brush size + add/remove mode
│   │   │   ├── ExportButton.tsx      # Final EXR export trigger
│   │   │   ├── ProgressIndicator.tsx # Job progress display
│   │   │   └── ShortcutHints.tsx     # Keyboard shortcut hint bar
│   │   ├── hooks/
│   │   │   ├── useProject.ts         # Project state via TanStack Query
│   │   │   ├── useJobPolling.ts      # Background job status polling
│   │   │   ├── usePreview.ts         # Preview image fetching
│   │   │   ├── useShortcuts.ts       # Global keyboard shortcuts
│   │   │   └── useDebouncedEffect.ts # For mask edit debouncing
│   │   ├── stores/
│   │   │   └── editorStore.ts        # Zustand: viewMode, exposure, brush, technique
│   │   ├── api/
│   │   │   ├── client.ts             # Fetch wrapper, base URL handling
│   │   │   ├── upload.ts             # Upload endpoint
│   │   │   ├── project.ts            # Project CRUD
│   │   │   ├── preview.ts            # Preview rendering
│   │   │   ├── process.ts            # Inpaint job triggers
│   │   │   └── export.ts             # Final export
│   │   ├── types/
│   │   │   └── api.ts                # TS types matching FastAPI responses
│   │   ├── utils/
│   │   │   ├── canvas.ts             # Mask encoding/decoding (Canvas <-> PNG)
│   │   │   └── coords.ts             # Image-space <-> canvas-space transforms
│   │   ├── styles/
│   │   │   └── index.css             # Global styles + Tailwind
│   │   └── vite-env.d.ts
│   └── dist/                         # Build output (gitignored, served by FastAPI)
├── tests/
│   ├── __init__.py
│   ├── test_exr_io.py
│   ├── test_ball_detect.py
│   ├── test_mask_estimate.py
│   ├── test_inpaint.py
│   ├── test_unwrap.py
│   └── fixtures/
│       └── README.md                 # How to add test EXR fixtures
├── scripts/
│   ├── cli.py                        # Standalone CLI for testing pipeline
│   └── generate_test_ball.py         # Synthesize test chrome ball EXR
├── pyproject.toml
├── requirements.txt
├── nixpacks.toml                     # Railway build config (Python + Node)
├── Procfile                          # Railway start command
├── railway.toml                      # Railway service config
├── runtime.txt                       # Python version pin
├── .gitignore
├── .env.example
├── README.md
└── PRD.md                            # This document
```

### 2.3 Key Architectural Decisions

These are **non-negotiable** unless impossible:

1. **`core/` is web-framework-agnostic.** No FastAPI, Flask, Railway-specific imports in `core/`. The CLI in `scripts/cli.py` and the web app both import from `core/`. This makes the algorithms testable without HTTP.

2. **All HDR processing happens in float32 linear scene-referred space.** No 8-bit conversion in the data path. 8-bit only used for display preview generation and (internally) for inpainting algorithms that require it — but always with proper tone-map round-trip.

3. **Inpainting uses log-space transformation.** Operating directly in linear HDR causes single bright pixels to dominate averaging operations. See `core/hdr_utils.py` requirements below.

4. **Background jobs use in-process asyncio task tracking via FastAPI `BackgroundTasks`.** Simple JobTracker class holds state in memory. Sufficient for v1. Migration path to `arq` (Redis-backed) is documented but not implemented.

5. **Frontend is React + Vite + TypeScript.** State management via Zustand (lightweight, no boilerplate). Server state via TanStack Query (job polling, cache invalidation, request deduplication). Canvas rendering via Konva.js with `react-konva`.

6. **TypeScript strict mode is enabled** in `tsconfig.json`. All API response types defined in `frontend/src/types/api.ts` and kept in sync with FastAPI Pydantic models.

7. **EXR I/O uses OpenEXR Python bindings (`OpenEXR` package).** OpenImageIO is better but harder to install on Railway. Use `OpenEXR` + `Imath` packages. If OpenEXR proves problematic in Railway's build environment, fall back to `imageio` with the `imageio[hdr]` extras as a secondary choice.

8. **Image preview transmission uses tone-mapped JPEG, not raw EXR.** Sending 100MB+ EXR files to the browser is wasteful. The browser displays tone-mapped 8-bit JPEGs; the actual processing operates on the server-side float32 data. Final EXR is only downloaded at export time.

9. **FastAPI serves the React build output.** In production, `frontend/dist/` is mounted as static files at `/`, with API routes at `/api/*`. Single-origin deployment means no CORS configuration needed in production. In development, Vite dev server proxies `/api/*` to the FastAPI backend.

10. **Styling is deferred.** Use Tailwind CSS utility classes for layout/spacing during initial build. Apply the design system in Phase 6 by configuring Tailwind theme tokens to match.

---

## 3. Processing Pipeline (Core Algorithm)

This section is the heart of the tool. Implement carefully. Test with real-world chrome ball EXR plates if available.

### 3.1 Stage 1: Load and Validate

**Module:** `core/exr_io.py`

**Functions:**

```python
def load_exr(path: str) -> np.ndarray:
    """
    Load 32-bit EXR file.
    
    Returns:
        np.ndarray of shape (H, W, 3), dtype float32, linear scene-referred.
        
    Raises:
        ValueError if file is not a valid EXR or not float32.
        ValueError if image is not 3-channel RGB.
    """

def save_exr(path: str, image: np.ndarray) -> None:
    """
    Save float32 RGB array as 32-bit EXR.
    
    Args:
        image: float32 array of shape (H, W, 3), linear scene-referred.
    
    Compression: ZIP (good balance of size vs read speed for DCCs).
    """

def validate_chrome_ball_plate(image: np.ndarray) -> tuple[bool, str]:
    """
    Sanity check that the input looks like a chrome ball plate.
    Returns (is_valid, message).
    
    Checks:
        - Image is at least 1024x1024 (smaller is unusable)
        - Image has reasonable dynamic range (max value > 1.0 suggests true HDR)
        - Image is not entirely black or saturated
    """
```

**Constraints:**
- Preserve all values exactly. No clipping, no normalization on load.
- If EXR has more than 3 channels (e.g., alpha, depth), use only RGB.
- Handle both `half` (float16) and `float` (float32) input EXR; promote half to float32 internally.

### 3.2 Stage 2: Ball Detection

**Module:** `core/ball_detect.py`

**Function:**

```python
def detect_ball(image: np.ndarray) -> tuple[int, int, int]:
    """
    Detect the chrome ball in the plate.
    
    Returns:
        (center_x, center_y, radius) in pixels.
    
    Algorithm:
        1. Tone-map to 8-bit for processing
        2. Use cv2.HoughCircles with parameters tuned for chrome balls:
           - dp=1.0, minDist=image_width//2, param1=100, param2=30
           - minRadius=image_min_dim//8, maxRadius=image_min_dim//2
        3. If multiple circles detected, choose the one with strongest gradient
           on its boundary (chrome balls have very sharp edge transitions)
        4. If no circle detected, raise BallDetectionError with helpful message
    """

class BallDetectionError(Exception):
    """Raised when chrome ball cannot be auto-detected."""
    pass
```

**Constraints:**
- Must work on plates where the ball doesn't fill the frame (often centered with background visible)
- Must work on plates where the ball is cropped tightly
- Provide a `manual_override` path: if auto-detect fails, the user can specify center+radius via the UI

### 3.3 Stage 3: Mask Estimation

**Module:** `core/mask_estimate.py`

**Function:**

```python
def estimate_photographer_mask(
    image: np.ndarray,
    ball_center: tuple[int, int],
    ball_radius: int,
) -> np.ndarray:
    """
    Generate an automatic mask for the photographer/tripod region.
    
    Returns:
        np.ndarray of shape (H, W), dtype uint8, values 0 or 255.
    
    Algorithm (combine all three signals, weighted):
        1. GEOMETRIC PRIOR (weight 1.0):
           Gaussian blob centered slightly below ball center, 
           extending downward to capture tripod.
           Center offset: 15% of ball radius below ball center.
           Sigma: 30% of ball radius horizontal, 45% vertical.
        
        2. DARKNESS SCORE (weight 0.6):
           In log-luminance space, identify regions darker than
           the median of the ball interior.
        
        3. EDGE DENSITY (weight 0.4):
           Canny edges, blurred. High edge density indicates
           camera/tripod hardware.
        
        Combined score = geometric * (0.5 + 0.3*darkness + 0.2*edges)
        Threshold at 0.5 to create binary mask.
        Apply morphological close (kernel 15x15) to fill gaps.
        Apply Gaussian blur (radius 11) to soften edges.
    """
```

**Constraints:**
- Mask must be confined to inside the ball circle (zero outside the ball boundary)
- Mask must be at least somewhat conservative — better to leave some photographer in than to mask out real environment

### 3.4 Stage 4: Inpainting (Tiered)

**Module:** `core/inpaint/`

**Protocol:**

```python
# core/inpaint/base.py

from typing import Protocol
import numpy as np

class Inpainter(Protocol):
    name: str
    description: str
    estimated_seconds: float  # rough estimate for UI display
    
    def inpaint(
        self,
        image: np.ndarray,      # float32 HDR, linear scene-referred
        mask: np.ndarray,        # uint8, 0 or 255
        ball_center: tuple[int, int],
        ball_radius: int,
    ) -> np.ndarray:
        """
        Inpaint the masked region of an HDR ball image.
        Returns float32 HDR with masked region filled.
        Values OUTSIDE the mask must be preserved exactly.
        """
        ...
```

**Three tiers to implement:**

#### 3.4.1 Tier 1: "Fast" — Boundary Extension

**Module:** `core/inpaint/boundary.py`

```python
class BoundaryInpainter:
    name = "fast"
    description = "Boundary extension (Navier-Stokes)"
    estimated_seconds = 0.3
    
    def inpaint(self, image, mask, ball_center, ball_radius):
        """
        Use cv2.inpaint with INPAINT_NS in log-space.
        
        Steps:
            1. Compute log-space transform: log_img = np.log(0.001 + image)
            2. Normalize log_img to [0, 255] uint8 for cv2.inpaint
            3. Run cv2.inpaint(log_8bit, mask, 15, cv2.INPAINT_NS) per channel
            4. Reverse: linear_inpainted = np.exp(restore_range(result)) - 0.001
            5. Composite: keep original outside mask, use inpainted inside
            6. Feather mask with cv2.GaussianBlur(mask, (31,31), 10) for smooth blend
        """
```

#### 3.4.2 Tier 2: "Good" — Frequency-Aware + Radial

**Module:** `core/inpaint/frequency.py` and `core/inpaint/radial.py`

```python
# core/inpaint/radial.py
def radial_fill(image, mask, ball_center, ball_radius):
    """
    For each masked pixel, sample at the same radius from ball center
    at multiple angles, take the median of unmasked samples.
    
    Sample angles: [60, 120, 180, 240, 300] degrees offset from each pixel.
    Use median of valid samples (those at unmasked locations).
    """

# core/inpaint/frequency.py
class FrequencyAwareInpainter:
    name = "good"
    description = "Frequency-aware fill with radial sampling"
    estimated_seconds = 2.0
    
    def inpaint(self, image, mask, ball_center, ball_radius):
        """
        Steps:
            1. Decompose into low and high frequency:
               low = cv2.GaussianBlur(image, (101, 101), 30)
               high = image - low
            
            2. Fill low frequencies with boundary inpaint (Tier 1 method)
            
            3. Fill high frequencies with radial sampling
            
            4. Recombine: result = low_filled + high_filled
            
            5. Composite back into original outside mask
        """
```

#### 3.4.3 Tier 3: "Best" — PatchMatch Exemplar

**Module:** `core/inpaint/patchmatch.py`

```python
class PatchMatchInpainter:
    name = "best"
    description = "Exemplar-based PatchMatch"
    estimated_seconds = 8.0
    
    def inpaint(self, image, mask, ball_center, ball_radius):
        """
        Use a Python PatchMatch implementation. 
        
        IMPLEMENTATION NOTE FOR CLAUDE CODE:
        Do NOT try to write PatchMatch from scratch. Use one of:
            - PyPatchMatch (https://github.com/vacancy/PyPatchMatch)
            - Try `pip install patchmatch` if available
            - If neither installs cleanly on Railway, implement a 
              simple exemplar fill as fallback (see below)
        
        FALLBACK if no PatchMatch library installs:
            Simple exemplar fill:
            1. Identify mask boundary
            2. For each masked pixel near boundary (in priority order
               by edge strength):
               a. Extract 9x9 patch centered at this pixel
               b. Search unmasked region of ball for best matching patch
                  (lowest SSD on known portion)
               c. Copy center pixel from matching patch
               d. Update boundary
            3. Repeat until mask is filled
            
            This is slow in pure Python — use numpy vectorization
            or accept ~30-60s for 1500x1500 region.
        
        Operate in log-space throughout, same as other tiers.
        """
```

**Inpainter Registry:**

```python
# core/inpaint/__init__.py

from .boundary import BoundaryInpainter
from .frequency import FrequencyAwareInpainter
from .patchmatch import PatchMatchInpainter

INPAINTERS = {
    "fast": BoundaryInpainter(),
    "good": FrequencyAwareInpainter(),
    "best": PatchMatchInpainter(),
}

def get_inpainter(name: str):
    if name not in INPAINTERS:
        raise ValueError(f"Unknown inpainter: {name}")
    return INPAINTERS[name]
```

### 3.5 Stage 5: Mirror Ball → Equirectangular Unwrap

**Module:** `core/unwrap.py`

```python
def ball_to_equirect(
    ball_image: np.ndarray,
    ball_center: tuple[int, int],
    ball_radius: int,
    output_width: int = 4096,
    output_height: int = 2048,
) -> np.ndarray:
    """
    Convert mirror ball image to equirectangular (lat-long) projection.
    
    Math:
        For each pixel (u, v) in equirectangular output:
            phi = (u/W - 0.5) * 2*pi   # longitude
            theta = (v/H - 0.5) * pi   # latitude
            
            # World direction vector
            dx = cos(theta) * sin(phi)
            dy = sin(theta)
            dz = cos(theta) * cos(phi)
            
            # Mirror ball reflection: ball normal N = normalize((0,0,1) + R)
            nx = dx
            ny = dy
            nz = dz + 1.0
            norm = sqrt(nx² + ny² + nz²)
            nx /= norm; ny /= norm
            
            # Sample from ball image at:
            ball_u = ball_center_x + nx * ball_radius
            ball_v = ball_center_y + ny * ball_radius   # NOTE: y-axis convention
    
    Use cv2.remap with INTER_CUBIC for resampling.
    Use BORDER_CONSTANT with value 0 for pixels outside the ball.
    
    Y-AXIS NOTE: Image coordinates have Y increasing downward, but our
    math treats Y as up. Flip ny when computing ball_v:
        ball_v = ball_center_y - ny * ball_radius
    
    VERIFY ORIENTATION: After implementing, generate a test pattern 
    (synthetic ball reflecting a known environment) and verify:
        - Front of ball (camera-facing point) maps to phi=0 (center column)
        - Top of ball (zenith of reflection) maps to top row
        - Result is right-side-up
    """
```

**Constraints:**
- Default output: 4096×2048 (2:1 aspect, standard for HDRI)
- Allow user to choose output resolution: 2048×1024, 4096×2048, 8192×4096
- Pixels in equirect that have no corresponding ball point (due to chrome ball's blind spot at the back) are filled with 0 — these will be the regions the user must accept as approximate

### 3.6 Stage 6: HDR Compositing Utilities

**Module:** `core/hdr_utils.py`

```python
def to_log_space(hdr: np.ndarray, epsilon: float = 0.001) -> tuple[np.ndarray, dict]:
    """
    Convert linear HDR to log-space normalized to [0, 1] then to uint8.
    Returns the uint8 image AND a dict of parameters needed to invert.
    """

def from_log_space(log_uint8: np.ndarray, params: dict) -> np.ndarray:
    """Inverse of to_log_space. Returns float32 linear HDR."""

def hdr_safe_composite(
    original_hdr: np.ndarray,
    inpainted_hdr: np.ndarray,
    mask: np.ndarray,
    feather_radius: int = 15,
) -> np.ndarray:
    """
    Composite inpainted region into original, preserving HDR values
    exactly outside the mask.
    
    Feather mask boundary for smooth blend. Use Gaussian blur on mask.
    """

def tonemap_for_preview(
    hdr: np.ndarray,
    exposure: float = 0.0,
    gamma: float = 2.2,
) -> np.ndarray:
    """
    Tone map HDR to 8-bit RGB for browser display.
    Simple Reinhard tone mapping with exposure adjustment.
    Returns uint8 array.
    """

def luminance(hdr: np.ndarray) -> np.ndarray:
    """Compute luminance (Rec. 709 weighting): 0.2126*R + 0.7152*G + 0.0722*B"""
```

### 3.7 Stage 7: Project State Container

**Module:** `core/project.py`

```python
from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import hashlib

@dataclass
class HDRIProject:
    """
    Holds the state of a single in-progress HDRI conversion.
    Caches expensive intermediate results.
    """
    project_id: str                              # UUID
    source_path: str                             # path to uploaded EXR
    
    ball_hdr: Optional[np.ndarray] = None
    ball_center: Optional[tuple[int, int]] = None
    ball_radius: Optional[int] = None
    
    mask: Optional[np.ndarray] = None
    
    # Cache: technique_name -> (mask_hash, inpainted_hdr)
    inpaint_cache: dict = field(default_factory=dict)
    
    selected_technique: str = "good"
    output_resolution: tuple[int, int] = (4096, 2048)
    
    def load(self):
        """Load EXR and detect ball. Idempotent."""
    
    def auto_mask(self):
        """Generate auto mask. Invalidates inpaint cache."""
    
    def update_mask(self, new_mask: np.ndarray):
        """Replace mask. Invalidates inpaint cache."""
    
    def get_inpainted(self, technique: str) -> np.ndarray:
        """Get inpainted ball, using cache if available."""
        mask_hash = hashlib.sha256(self.mask.tobytes()).hexdigest()
        cache_key = (technique, mask_hash)
        
        if cache_key in self.inpaint_cache:
            return self.inpaint_cache[cache_key]
        
        inpainter = get_inpainter(technique)
        result = inpainter.inpaint(
            self.ball_hdr, self.mask, 
            self.ball_center, self.ball_radius
        )
        self.inpaint_cache[cache_key] = result
        return result
    
    def export_equirect(self, output_path: str, technique: str = None):
        """Generate final equirect EXR and save."""
        technique = technique or self.selected_technique
        inpainted = self.get_inpainted(technique)
        equirect = ball_to_equirect(
            inpainted, self.ball_center, self.ball_radius,
            *self.output_resolution
        )
        save_exr(output_path, equirect)
```

---

## 4. Web Application

### 4.1 Backend (FastAPI)

**Module:** `app/main.py`

```python
# Minimum endpoints required:

POST /api/upload
    # Multipart file upload, accepts .exr file
    # Validates file
    # Creates HDRIProject, returns project_id

GET /api/project/{project_id}
    # Returns project state: ball_center, ball_radius, has_mask, etc.

GET /api/preview/{project_id}/ball
    # Query params: view_mode, exposure, technique
    # view_mode: "original" | "mask" | "inpainted" | "compare"
    # Returns JPEG (or two JPEGs for compare mode)

POST /api/mask/{project_id}
    # Body: { "mask_data": base64-encoded PNG } 
    # OR { "auto": true } to regenerate auto mask
    # Updates project mask, invalidates inpaint cache

POST /api/process/{project_id}
    # Body: { "technique": "fast"|"good"|"best" }
    # Triggers inpaint job (background)
    # Returns job_id

GET /api/job/{job_id}/status
    # Returns: { "status": "pending"|"running"|"complete"|"failed",
    #           "progress": 0-100, "message": "..." }

GET /api/preview/{project_id}/equirect
    # Query params: technique, exposure, size (preview-sized, e.g. 1024x512)
    # Returns JPEG of tone-mapped equirect

GET /api/export/{project_id}
    # Query params: technique, width, height
    # Triggers full-res equirect generation, returns final EXR file

DELETE /api/project/{project_id}
    # Cleanup uploaded and intermediate files
```

**Job execution:**

For Railway simplicity, use FastAPI's `BackgroundTasks` for short jobs (<30s) and an in-memory job tracker. If jobs need to outlive request handlers, switch to `arq` with Redis (Railway provides Redis as an addon).

```python
# app/workers/job_runner.py

class JobTracker:
    """In-memory job state. Project-scoped. Cleared on app restart."""
    jobs: dict[str, dict] = {}  # job_id -> {status, progress, message, result}
    
    def create_job(self) -> str: ...
    def update_progress(self, job_id, progress, message): ...
    def complete_job(self, job_id, result): ...
    def fail_job(self, job_id, error): ...
    def get_status(self, job_id) -> dict: ...
```

### 4.2 Frontend (React + Vite + TypeScript)

#### 4.2.1 Tech Stack (Locked Decisions)

```json
{
  "framework": "React 18.x",
  "buildTool": "Vite 5.x",
  "language": "TypeScript 5.x (strict mode)",
  "stateManagement": "Zustand 4.x",
  "serverState": "@tanstack/react-query 5.x",
  "canvas": "Konva 9.x + react-konva 18.x",
  "fileUpload": "react-dropzone 14.x",
  "compareSlider": "react-compare-slider 3.x",
  "shortcuts": "react-hotkeys-hook 4.x",
  "styling": "Tailwind CSS 3.x"
}
```

**`frontend/package.json` dependencies:**

```json
{
  "name": "hdri-tool-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "konva": "^9.3.16",
    "react-konva": "^18.2.10",
    "zustand": "^4.5.5",
    "@tanstack/react-query": "^5.59.0",
    "react-dropzone": "^14.2.3",
    "react-compare-slider": "^3.1.0",
    "react-hotkeys-hook": "^4.5.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.10",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.6.2",
    "vite": "^5.4.8",
    "tailwindcss": "^3.4.13",
    "postcss": "^8.4.47",
    "autoprefixer": "^10.4.20",
    "eslint": "^9.11.1",
    "@typescript-eslint/eslint-plugin": "^8.7.0",
    "@typescript-eslint/parser": "^8.7.0"
  }
}
```

**Note on versions:** These versions are accurate as of late 2025. When Claude Code initializes the project, run `npm install` and accept any minor version bumps in `package-lock.json`. Do NOT downgrade to older majors without explicit reason.

#### 4.2.2 Vite Configuration

**`frontend/vite.config.ts`:**

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // In dev, Vite serves on 5173 and proxies API calls to FastAPI on 8000
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    // Increase chunk size limit; Konva is sizeable but acceptable
    chunkSizeWarningLimit: 1000,
  },
});
```

**`frontend/tsconfig.json`:**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

#### 4.2.3 Layout (Visual Reference)

Initial empty state:

```
┌──────────────────────────────────────────────────┐
│ HDRI Tool                                  [?]   │
├──────────────────────────────────────────────────┤
│                                                  │
│  [Drag & drop EXR here, or click to browse]     │
│                                                  │
└──────────────────────────────────────────────────┘
```

After upload (working state):

```
┌──────────────────────────────────────────────────────┐
│ project_xyz.exr                              [Reset] │
├──────────────────────────────────────────────────────┤
│ View: [Original] [Mask] [Inpainted] [Compare]       │
├──────────────────────────────────────────────────────┤
│                                                      │
│              [Preview canvas (Konva)]                │
│                                                      │
├──────────────────────────────────────────────────────┤
│ Mask:  [Brush+] [Brush-] [Auto] [Reset]             │
│ Brush size: [───●───] 30px                           │
├──────────────────────────────────────────────────────┤
│ Technique:                                           │
│   ○ Fast   (~0.3s)  Boundary extension              │
│   ● Good   (~2s)    Frequency-aware + radial        │
│   ○ Best   (~8s)    PatchMatch exemplar             │
├──────────────────────────────────────────────────────┤
│ Exposure: [───●───] +0.0 EV                          │
│ Output: [4096×2048 ▼]                                │
│                                                      │
│                  [ Export EXR ]                      │
├──────────────────────────────────────────────────────┤
│ \: hold for original | M: toggle mask | 1-4: views  │
└──────────────────────────────────────────────────────┘
```

#### 4.2.4 Component Responsibilities

**`App.tsx`** — Top-level layout. Conditional render: `<Uploader />` when no project loaded, full editor layout when loaded. Wraps everything in `QueryClientProvider`.

**`Uploader.tsx`** — Uses `react-dropzone`. Validates file extension (`.exr`) and size before upload. Shows progress during upload. On success, sets `projectId` in Zustand store.

**`PreviewPanel.tsx`** — Container for the main preview area. Renders one of:
- `<MaskEditor />` when `viewMode === 'mask'`
- `<CompareView />` when `viewMode === 'compare'`
- A simple Konva `<Stage>` with image layer for `original` and `inpainted`

**`MaskEditor.tsx`** — The painting interface. Implementation details below in section 4.2.5.

**`CompareView.tsx`** — Uses `react-compare-slider` library. Two server-rendered preview images (original and inpainted) with a draggable divider. No custom canvas code needed.

**`ViewModeSelector.tsx`** — Four buttons. Hooked up to `editorStore.viewMode`. Highlighted state shows current mode.

**`TechniquePanel.tsx`** — Three radio buttons. On change, sets `editorStore.technique` AND triggers `useMutation` to start a new inpaint job. Shows estimated time per technique.

**`ExposureSlider.tsx`** — Range slider, -3.0 to +3.0 EV. Updates `editorStore.exposure`. All preview hooks include exposure as a query key — changing exposure refetches preview.

**`BrushControls.tsx`** — Brush mode toggle (add/remove), brush size slider, "Auto-detect" button, "Reset mask" button.

**`ExportButton.tsx`** — Triggers `POST /api/export/{projectId}`, polls job status, downloads resulting EXR via hidden anchor.

**`ProgressIndicator.tsx`** — Shows during active jobs. Pulled from `useJobPolling` hook. Spinner + percentage + status message.

**`ShortcutHints.tsx`** — Bottom bar showing key shortcuts. Pure presentational.

#### 4.2.5 MaskEditor Implementation Detail

This is the most complex component. Use `react-konva`:

```typescript
// frontend/src/components/MaskEditor.tsx (sketch)
import { Stage, Layer, Image as KonvaImage, Line } from 'react-konva';
import { useState, useRef, useEffect } from 'react';
import useImage from 'use-image';

export function MaskEditor() {
  const ballImageUrl = usePreview('original');  // 8-bit JPEG from server
  const [ballImg] = useImage(ballImageUrl ?? '');
  const [strokes, setStrokes] = useState<Stroke[]>([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const brushSize = useEditorStore(s => s.brushSize);
  const brushMode = useEditorStore(s => s.brushMode);
  const stageRef = useRef<Konva.Stage>(null);
  
  // On stroke end, rasterize all strokes to a mask canvas, encode PNG, POST to server
  // ... 
  
  return (
    <Stage
      width={800}
      height={800}
      onMouseDown={handleStart}
      onMouseMove={handleMove}
      onMouseUp={handleEnd}
      ref={stageRef}
    >
      <Layer>
        <KonvaImage image={ballImg} />
      </Layer>
      <Layer opacity={0.5}>
        {strokes.map((s, i) => (
          <Line
            key={i}
            points={s.points}
            stroke={s.mode === 'add' ? 'red' : 'blue'}
            strokeWidth={s.brushSize}
            lineCap="round"
            lineJoin="round"
            globalCompositeOperation={
              s.mode === 'add' ? 'source-over' : 'destination-out'
            }
          />
        ))}
      </Layer>
    </Stage>
  );
}
```

Key implementation requirements:

- **Coordinate space:** Konva stage is fixed display size (e.g., 800×800). Image coordinates (real ball image) may be different. Translate stage coords → image coords when serializing the mask.

- **Mask rasterization:** When the user finishes a stroke (`mouseup`), rasterize all strokes to an offscreen canvas at full image resolution. Encode as PNG via `canvas.toBlob()`. POST to `/api/mask/{projectId}`.

- **Initial mask from server:** On mount, fetch the auto-generated mask as a PNG. Display as a layer. When user paints, work with strokes locally; on stroke end, merge strokes with the base mask and send back.

- **Zoom/pan:** Konva supports stage scaling natively. Mouse wheel adjusts `stage.scale`. Middle-mouse-drag or shift-drag adjusts `stage.position`.

- **Brush cursor:** Custom cursor using a Konva circle that follows mouse position. Outline only, matches current brush size.

#### 4.2.6 Zustand Store

**`frontend/src/stores/editorStore.ts`:**

```typescript
import { create } from 'zustand';

type ViewMode = 'original' | 'mask' | 'inpainted' | 'compare';
type BrushMode = 'add' | 'remove';
type Technique = 'fast' | 'good' | 'best';

interface EditorState {
  projectId: string | null;
  viewMode: ViewMode;
  previousViewMode: ViewMode;       // for hold-to-compare
  brushMode: BrushMode;
  brushSize: number;
  exposure: number;
  technique: Technique;
  outputResolution: [number, number];
  showMaskOverlay: boolean;          // toggle independently of view mode
  
  setProjectId: (id: string | null) => void;
  setViewMode: (mode: ViewMode) => void;
  temporaryViewOriginal: () => void;  // for hold-backslash
  restoreViewMode: () => void;
  setBrushMode: (mode: BrushMode) => void;
  setBrushSize: (size: number) => void;
  setExposure: (exp: number) => void;
  setTechnique: (t: Technique) => void;
  setOutputResolution: (res: [number, number]) => void;
  toggleMaskOverlay: () => void;
  reset: () => void;
}

export const useEditorStore = create<EditorState>((set, get) => ({
  projectId: null,
  viewMode: 'inpainted',
  previousViewMode: 'inpainted',
  brushMode: 'add',
  brushSize: 30,
  exposure: 0,
  technique: 'good',
  outputResolution: [4096, 2048],
  showMaskOverlay: false,
  
  setProjectId: (id) => set({ projectId: id }),
  setViewMode: (mode) => set({ viewMode: mode, previousViewMode: get().viewMode }),
  temporaryViewOriginal: () => set({ 
    previousViewMode: get().viewMode, 
    viewMode: 'original' 
  }),
  restoreViewMode: () => set({ viewMode: get().previousViewMode }),
  setBrushMode: (mode) => set({ brushMode: mode }),
  setBrushSize: (size) => set({ brushSize: Math.max(2, Math.min(200, size)) }),
  setExposure: (exp) => set({ exposure: Math.max(-3, Math.min(3, exp)) }),
  setTechnique: (t) => set({ technique: t }),
  setOutputResolution: (res) => set({ outputResolution: res }),
  toggleMaskOverlay: () => set({ showMaskOverlay: !get().showMaskOverlay }),
  reset: () => set({ 
    projectId: null, 
    viewMode: 'inpainted',
    exposure: 0,
    showMaskOverlay: false,
  }),
}));
```

#### 4.2.7 TanStack Query Patterns

**`frontend/src/hooks/usePreview.ts`:**

```typescript
import { useQuery } from '@tanstack/react-query';
import { useEditorStore } from '@/stores/editorStore';

export function usePreview(viewMode: 'original' | 'inpainted') {
  const projectId = useEditorStore(s => s.projectId);
  const exposure = useEditorStore(s => s.exposure);
  const technique = useEditorStore(s => s.technique);
  
  return useQuery({
    queryKey: ['preview', projectId, viewMode, technique, exposure],
    queryFn: async () => {
      const params = new URLSearchParams({
        view_mode: viewMode,
        exposure: String(exposure),
        technique,
      });
      const res = await fetch(`/api/preview/${projectId}/ball?${params}`);
      if (!res.ok) throw new Error('Preview fetch failed');
      const blob = await res.blob();
      return URL.createObjectURL(blob);
    },
    enabled: !!projectId,
    staleTime: 60_000,  // preview images don't go stale
  });
}
```

**`frontend/src/hooks/useJobPolling.ts`:**

```typescript
import { useQuery } from '@tanstack/react-query';

export function useJobPolling(jobId: string | null) {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: async () => {
      const res = await fetch(`/api/job/${jobId}/status`);
      return res.json() as Promise<JobStatus>;
    },
    enabled: !!jobId,
    refetchInterval: (data) => {
      const status = data?.state?.data?.status;
      return status === 'pending' || status === 'running' ? 500 : false;
    },
  });
}
```

#### 4.2.8 Keyboard Shortcuts

**`frontend/src/hooks/useShortcuts.ts`:**

Use `react-hotkeys-hook`:

```typescript
import { useHotkeys } from 'react-hotkeys-hook';
import { useEditorStore } from '@/stores/editorStore';

export function useShortcuts() {
  const store = useEditorStore();
  
  useHotkeys('1', () => store.setViewMode('original'));
  useHotkeys('2', () => store.setViewMode('mask'));
  useHotkeys('3', () => store.setViewMode('inpainted'));
  useHotkeys('4', () => store.setViewMode('compare'));
  useHotkeys('m', () => store.toggleMaskOverlay());
  useHotkeys('x', () => store.setBrushMode(
    store.brushMode === 'add' ? 'remove' : 'add'
  ));
  useHotkeys('[', () => store.setBrushSize(store.brushSize - 5));
  useHotkeys(']', () => store.setBrushSize(store.brushSize + 5));
  
  // Hold-to-view-original (backslash)
  useHotkeys('\\', () => store.temporaryViewOriginal(), 
             { keydown: true, keyup: false });
  useHotkeys('\\', () => store.restoreViewMode(), 
             { keydown: false, keyup: true });
}
```

Mount this hook once in `App.tsx`.

#### 4.2.9 Type Definitions

**`frontend/src/types/api.ts`:** (kept in sync with FastAPI Pydantic models)

```typescript
export interface ProjectState {
  project_id: string;
  source_filename: string;
  ball_center: [number, number];
  ball_radius: number;
  has_mask: boolean;
  selected_technique: 'fast' | 'good' | 'best';
  output_resolution: [number, number];
  created_at: string;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'complete' | 'failed';
  progress: number;          // 0-100
  message: string;
  result_url?: string;       // populated when complete
  error?: string;            // populated on failure
}

export interface UploadResponse {
  project_id: string;
  filename: string;
  ball_center: [number, number];
  ball_radius: number;
}
```

#### 4.2.10 Frontend Implementation Notes

- **Coordinate space discipline.** Konva stage is in display pixels. Server expects mask in image pixels. Always convert when serializing/deserializing. Centralize the math in `utils/coords.ts`.

- **Mask transmission timing.** On stroke end (`onMouseUp`), rasterize strokes to a mask canvas at image resolution, encode PNG, POST to server. Don't transmit mid-stroke. Use `useDebouncedEffect` if rapid edits are happening.

- **Preview cache invalidation.** When mask updates server-side, invalidate `['preview', projectId, 'inpainted', ...]` queries. TanStack Query refetches automatically. Use `queryClient.invalidateQueries(['preview', projectId])`.

- **File upload progress.** Use `XMLHttpRequest` (not `fetch`) for upload progress events, OR a fetch-based stream wrapper. `react-dropzone` provides the file picker and drag handling but not progress.

- **Error boundaries.** Wrap the editor in a React error boundary. EXR processing can fail in subtle ways; surface errors to the user with a "Reset and try another file" CTA.

- **Production build serves from FastAPI.** No CORS in production. In dev, Vite proxy handles `/api/*`. Document this in `frontend/README.md`.

---

## 5. Railway Deployment

### 5.1 Required Files

**`Procfile`:**
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**`runtime.txt`:**
```
python-3.11.10
```

**`railway.toml`:**
```toml
[build]
builder = "NIXPACKS"

[deploy]
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

**`nixpacks.toml`** (required — handles dual Python + Node build):

```toml
[phases.setup]
nixPkgs = ["python311", "nodejs_20"]
aptPkgs = ["libopenexr-dev", "libimath-dev"]

[phases.install]
cmds = [
  "python -m venv --copies /opt/venv",
  ". /opt/venv/bin/activate && pip install --upgrade pip",
  ". /opt/venv/bin/activate && pip install -r requirements.txt",
  "cd frontend && npm ci"
]

[phases.build]
cmds = [
  "cd frontend && npm run build"
]

[start]
cmd = ". /opt/venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

**Notes on `nixpacks.toml`:**
- The dual `python311` + `nodejs_20` setup is the key change from a single-language deploy
- `libopenexr-dev` and `libimath-dev` are included preemptively; remove if `pip install OpenEXR` succeeds without them
- The venv pattern (`/opt/venv`) ensures Python deps persist between phases
- `npm ci` is faster and stricter than `npm install` for production builds — uses exact `package-lock.json` versions

**`requirements.txt`:**
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
python-multipart>=0.0.9
numpy>=1.26.0,<2.0.0
opencv-python-headless>=4.10.0
OpenEXR>=3.2.0
Pillow>=10.0.0
scipy>=1.13.0
```

**Important Railway notes:**
- Use `opencv-python-headless`, not `opencv-python` — Railway doesn't have GUI libs
- Pin numpy below 2.0 for compatibility with OpenCV and OpenEXR bindings (test and adjust if dependencies have updated)
- The frontend build output (`frontend/dist/`) is generated during deploy and served by FastAPI; it's gitignored

### 5.2 FastAPI Static File Serving

In `app/main.py`, mount the React build output:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import upload, process, preview, download
import os

app = FastAPI(title="HDRI Tool")

# API routes mounted FIRST (so they take precedence)
app.include_router(upload.router, prefix="/api")
app.include_router(process.router, prefix="/api")
app.include_router(preview.router, prefix="/api")
app.include_router(download.router, prefix="/api")

# Serve React build output for everything else
# Note: html=True enables SPA fallback (serves index.html for unknown routes)
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    # Dev mode: frontend served by Vite on :5173, FastAPI on :8000
    @app.get("/")
    def dev_message():
        return {"message": "Frontend not built. Run 'cd frontend && npm run dev' for development, or 'npm run build' to generate dist/"}
```

### 5.3 Development Workflow

Two terminal windows during local dev:

```bash
# Terminal 1: Backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev   # Serves on :5173 with HMR, proxies /api to :8000
```

Access the app at `http://localhost:5173` during development (Vite dev server).

For a production-like local test:

```bash
cd frontend && npm run build
cd ..
uvicorn app.main:app --port 8000
# Visit http://localhost:8000 — FastAPI serves the built React app
```

### 5.4 File Storage on Railway

Railway provides ephemeral filesystem by default. For this app:

- Upload EXRs to `/tmp/hdri_uploads/{project_id}/source.exr`
- Intermediate cached files in `/tmp/hdri_uploads/{project_id}/`
- Set up a periodic cleanup task to delete projects older than 24 hours

Add Railway volume only if persistent storage becomes necessary (it shouldn't — this is a transient processing tool).

### 5.5 Environment Variables

Document in `.env.example`:

```bash
# .env.example
PORT=8000                        # Railway sets this automatically
MAX_UPLOAD_SIZE_MB=200          # Reject files larger than this
PROJECT_TTL_HOURS=24             # Auto-delete projects older than this
LOG_LEVEL=INFO
```

### 5.6 Git Workflow

Initial setup:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <github-url>
git push -u origin main
```

Then connect the Railway project to the GitHub repo through Railway's dashboard. Subsequent deploys are just `git push`.

**`.gitignore`:**
```
# Python
__pycache__/
*.pyc
*.pyo
.env
.venv/
venv/
*.egg-info/
.pytest_cache/

# Node / Vite
node_modules/
frontend/dist/
frontend/.vite/
*.local

# Test artifacts
*.exr
/tmp/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
```

---

## 6. Build Order — Phased Implementation

**Implement in this order. Do not skip ahead. After each phase, stop and ask the human to test.**

### Phase 1: Core Pipeline (CLI-first, no web)

**Goal:** Convert a chrome ball EXR to equirect HDRI from the command line. Validate algorithms work before building web infrastructure.

**Tasks:**
1. Set up project structure (directories, `pyproject.toml`, `requirements.txt`)
2. Implement `core/exr_io.py` with load/save/validate
3. Implement `core/ball_detect.py`
4. Implement `core/mask_estimate.py`
5. Implement `core/hdr_utils.py` (log-space, tone mapping, composite)
6. Implement `core/inpaint/boundary.py` (Tier 1 — simplest)
7. Implement `core/unwrap.py`
8. Implement `scripts/cli.py` with this interface:
   ```
   python -m scripts.cli process input.exr output.exr [--technique=fast|good|best] [--width=4096] [--height=2048]
   ```
9. Implement `scripts/generate_test_ball.py` — synthesizes a fake chrome ball reflecting a known environment (use `numpy` to draw colored gradients on a sphere). Used for testing.
10. Write basic tests in `tests/` for each module.

**Stop here. Verify CLI produces valid HDRIs from test inputs.**

### Phase 2: Additional Inpaint Tiers

**Tasks:**
1. Implement `core/inpaint/radial.py`
2. Implement `core/inpaint/frequency.py` (Tier 2)
3. Implement `core/inpaint/patchmatch.py` (Tier 3, with fallback if no library)
4. Update `scripts/cli.py` to support all three techniques
5. Tests for each tier

**Stop. Compare outputs of all three tiers on test inputs.**

### Phase 3: Web Backend

**Tasks:**
1. `app/main.py` FastAPI app with CORS configured for same-origin
2. `core/project.py` HDRIProject class with caching
3. `app/routes/upload.py` — file upload endpoint
4. `app/routes/preview.py` — preview rendering endpoints
5. `app/routes/process.py` — inpaint job endpoints
6. `app/workers/job_runner.py` — in-memory job tracker
7. `app/routes/download.py` — final EXR export

**Stop. Test backend with curl or HTTPie before building frontend.**

### Phase 4: Frontend

**Goal:** Build the React + Vite + TypeScript frontend. Wire up to existing backend.

**Sub-phase 4a — Project setup and skeleton:**
1. Initialize Vite project: `cd frontend && npm create vite@latest . -- --template react-ts`
2. Install dependencies per the package.json in section 4.2.1
3. Configure Tailwind CSS (run `npx tailwindcss init -p`, configure `content` paths)
4. Set up `vite.config.ts` with API proxy (per section 4.2.2)
5. Set up `tsconfig.json` with strict mode (per section 4.2.2)
6. Create directory structure under `src/` (components, hooks, stores, api, types, utils)
7. Stub all components with placeholder content — verify the app builds and runs

**Sub-phase 4b — Core state and API plumbing:**
1. Implement `stores/editorStore.ts` (Zustand)
2. Implement `types/api.ts` with TS types matching FastAPI Pydantic models
3. Implement `api/client.ts` and individual API modules (upload, project, preview, process, export)
4. Set up `QueryClientProvider` in `main.tsx`
5. Implement `hooks/usePreview.ts` and `hooks/useJobPolling.ts`
6. Test upload flow end-to-end (Uploader → API → store update)

**Sub-phase 4c — Preview and view modes:**
1. Implement `PreviewPanel.tsx` with conditional rendering by view mode
2. Implement basic image display (Konva Stage with KonvaImage) for original and inpainted views
3. Implement `ViewModeSelector.tsx` with button states
4. Implement `CompareView.tsx` using `react-compare-slider`
5. Implement `ExposureSlider.tsx` and verify exposure changes refetch preview
6. Implement `useShortcuts.ts` and mount in `App.tsx`

**Sub-phase 4d — Mask editor (most complex piece):**
1. Implement `MaskEditor.tsx` with Konva Stage + Layers
2. Implement stroke recording (mouse events → array of points)
3. Implement mask rasterization (strokes → offscreen canvas → PNG blob)
4. Implement mask upload to `/api/mask/{projectId}` on stroke end
5. Implement zoom/pan on the Konva Stage
6. Implement custom brush cursor
7. Implement `BrushControls.tsx`
8. Test: paint stroke → server receives mask → next preview reflects new mask

**Sub-phase 4e — Technique panel and export:**
1. Implement `TechniquePanel.tsx` with mutation triggering on change
2. Implement `ProgressIndicator.tsx` showing job status from `useJobPolling`
3. Implement `ExportButton.tsx` with download flow
4. Implement `ShortcutHints.tsx` bottom bar

**Stop. End-to-end test: upload EXR → see preview → edit mask → switch techniques → export EXR.**

### Phase 5: Railway Deployment

**Tasks:**
1. Create `Procfile`, `railway.toml`, `runtime.txt`, `nixpacks.toml`
2. Verify `app/main.py` mounts `frontend/dist/` correctly (test locally first: build frontend, run uvicorn, visit :8000)
3. Add `frontend/dist/` and `node_modules/` to `.gitignore`
4. Initialize git, push to GitHub
5. Connect Railway project to GitHub
6. First deploy: monitor build logs for OpenEXR compilation issues, missing apt packages, npm install failures
7. Verify upload and processing work on Railway's resources
8. Verify `git push` triggers redeploy

**Stop. End-to-end test on Railway URL.**

### Phase 6: Polish (only after everything works)

**Tasks:**
1. Error handling and recovery (React error boundaries, FastAPI exception handlers)
2. Progress reporting on long inpaint jobs (already structured via JobTracker)
3. Cleanup task for old projects (background task that runs hourly)
4. README documentation (development workflow, deployment, troubleshooting)
5. Apply design system (provided separately) by configuring Tailwind theme tokens

---

## 7. Test Strategy

### 7.1 Test Fixtures

Create `tests/fixtures/` with:
- A synthetic chrome ball EXR (generated by `scripts/generate_test_ball.py`)
- A README explaining how to add real-world test plates

### 7.2 Unit Tests Required

- `test_exr_io.py`: round-trip load → save → load preserves data
- `test_ball_detect.py`: detects center+radius on synthetic ball
- `test_mask_estimate.py`: produces non-empty mask, mask is inside ball
- `test_hdr_utils.py`: log-space round-trip preserves values, tone mapping clamps to [0,255]
- `test_inpaint.py`: each inpainter preserves values outside mask exactly
- `test_unwrap.py`: equirect output has correct shape, known patterns map to expected coordinates

### 7.3 Integration Test

A single end-to-end test that runs the full pipeline on a synthetic chrome ball and validates the output equirect has expected properties (correct shape, no NaN, reasonable value range).

---

## 8. Known Issues and Decisions

### 8.1 Decisions Made

- **Single-shot only.** No multi-bracket HDR merging in v1. Users must provide a single 32-bit EXR.
- **CPU only.** No GPU acceleration in v1. Inpaint times: ~0.3s (fast), ~2s (good), ~10s (best) on Railway's standard CPU allocation.
- **No user accounts.** Sessions are anonymous. Project IDs are UUIDs in URLs.
- **No persistence.** Projects deleted after 24 hours.
- **No batch processing in v1.** One file at a time.

### 8.2 Known Limitations

- The blind spot at the back of the ball will always be approximated. No technique recovers what wasn't captured.
- Very low-resolution chrome balls (< 1024×1024 in original plate) will produce equirects with visible smearing.
- Highly complex environments (reflective stages, mirrored surfaces in the room) may produce artifacts in the inpainted region.

### 8.3 Future Considerations (Not v1)

- AI inpainting (LaMa via Replicate) as a "Premium" tier
- DiffusionLight integration for unseen-hemisphere refinement
- Multi-ball composite (front + back chrome ball merge)
- Cube map output format
- Batch processing
- DCC plugins (Nuke gizmo, Houdini HDA)

---

## 9. Instructions for Claude Code

### 9.1 General Approach

- **Read this entire PRD before writing any code.**
- **Implement phases in order.** Stop after each phase for human verification.
- **Don't write speculative code.** If something isn't specified, ask.
- **Don't add features not in this PRD.** If you have a strong idea, mention it but don't implement it.
- **Pin dependency versions.** Use `>=` constraints with upper bounds on major versions.
- **Add docstrings to every public function** matching the signatures shown in this PRD.

### 9.2 When You Encounter Problems

If a library specified in this PRD doesn't install or work on Railway:

1. First, try the documented fallback (e.g., `imageio` for EXR)
2. If no fallback works, **stop and report to the human** rather than choosing an alternative
3. Document the issue and the workaround in `README.md`

### 9.3 Code Style

**Python (`core/`, `app/`, `scripts/`, `tests/`):**
- Type hints on all function signatures
- Black formatting (line length 100)
- Sort imports with isort
- One module = one responsibility
- Prefer composition over inheritance
- Avoid global state outside `app/main.py`

**TypeScript (`frontend/src/`):**
- Strict mode enabled in `tsconfig.json` (no `any` without justification)
- Functional components only, no class components
- Hooks for all stateful logic
- ESLint with `@typescript-eslint` recommended rules
- Prefer named exports over default exports (better refactoring)
- Component files use PascalCase, hooks use camelCase with `use` prefix
- Co-locate component-specific types within the component file; shared types in `types/`

### 9.4 Communication

- After completing each phase, write a brief summary of what was built and what to test
- If you make a non-trivial decision not specified in the PRD, surface it explicitly
- Don't apologize for things; just describe what was done and what's next

### 9.5 Validation Before Phase Completion

Before marking a phase complete:

- Run all Python tests for that phase's modules: `pytest tests/`
- Run the CLI (Phase 1+) on a test input and verify output is valid
- For web phases, verify endpoints with curl/HTTPie
- For frontend phases, verify the build succeeds (`cd frontend && npm run build`)
- Check that TypeScript has no errors (`cd frontend && npx tsc --noEmit`)
- Check that no temporary files are left behind by tests

### 9.6 First Steps

When starting Phase 1 (backend pipeline):

1. Set up the directory structure exactly as shown in section 2.2
2. Initialize a Python venv: `python3.11 -m venv .venv && source .venv/bin/activate`
3. Install dev dependencies first: `pip install pytest black isort`
4. Then production dependencies from `requirements.txt`
5. Verify imports work before writing logic
6. Run `scripts/generate_test_ball.py` early — you'll need synthetic test data throughout

When starting Phase 4 (frontend):

1. Verify Node.js 20+ is installed: `node --version`
2. From the project root: `cd frontend && npm create vite@latest . -- --template react-ts`
   - When prompted about overwriting (the directory exists), choose to overwrite or merge as needed
3. Install all dependencies listed in section 4.2.1: `npm install <packages>`
4. Initialize Tailwind: `npx tailwindcss init -p`, then configure `tailwind.config.js` content paths
5. Run `npm run dev` and verify the placeholder page loads at :5173
6. Verify the proxy works: with FastAPI running on :8000, test that `/api/health` (add a stub endpoint) returns from :5173

---

## 10. Acceptance Criteria

The v1 build is complete when:

- [ ] User can upload a 32-bit EXR chrome ball plate via web browser
- [ ] System auto-detects ball position and photographer mask
- [ ] User can view original / mask / inpainted / compare views
- [ ] User can refine mask with brush tools (add/remove) using Konva canvas
- [ ] User can choose between three inpaint techniques
- [ ] Keyboard shortcuts work (1-4, M, X, [, ], hold-backslash)
- [ ] System produces a 32-bit EXR equirectangular output (4K default, configurable)
- [ ] Output EXR opens correctly in Blender, Maya, or Houdini and lights a scene plausibly
- [ ] Application is deployed to Railway and accessible via URL
- [ ] `git push` triggers Railway redeploy with both Python and Node build phases
- [ ] Frontend build output is served correctly by FastAPI in production
- [ ] Processing completes in under 30 seconds for typical 4K inputs (Tier 1 or 2)
- [ ] TypeScript compiles with no errors in strict mode
- [ ] All Python tests pass

---

*End of PRD*