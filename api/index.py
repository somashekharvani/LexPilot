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
    # Check if __path query parameter was passed by Vercel rewrite
    query_str = request.scope.get("query_string", b"").decode("utf-8")
    if "__path=" in query_str:
        import urllib.parse
        parsed = urllib.parse.parse_qs(query_str)
        if "__path" in parsed and parsed["__path"]:
            sub = parsed["__path"][0].lstrip("/")
            request.scope["path"] = "/" + sub
    return await call_next(request)

try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    handler = app
