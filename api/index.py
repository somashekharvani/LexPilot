"""
Vercel Serverless Function Entry Point for LexPilot FastAPI Backend
"""

import sys
import os
from pathlib import Path

# Add project root and backend directory to Python sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"

if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Import the FastAPI application instance
from backend.app.main import app

@app.middleware("http")
async def vercel_path_normalizer(request, call_next):
    # Check if Vercel passed original requested path in headers
    matched = request.headers.get("x-matched-path")
    if matched:
        request.scope["path"] = matched
    else:
        path = request.scope.get("path", "")
        for prefix in ["/api/index.py", "/index.py"]:
            if path.startswith(prefix):
                path = path[len(prefix):] or "/"
                break
        request.scope["path"] = path
    return await call_next(request)

try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    handler = app
