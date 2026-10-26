"""
Vercel Serverless Function entrypoint for WindLens UK FastAPI backend.
"""
import sys
import os

# Ensure backend directory is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

for path in [CURRENT_DIR, BACKEND_DIR, ROOT_DIR]:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)

from app.main import app as fastapi_app

class VercelNormalizerASGI:
    """
    ASGI middleware wrapping FastAPI to normalize all Vercel serverless paths
    and proxy headers BEFORE route dispatch.
    """
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            
            # 1. Inspect Vercel edge headers
            headers = dict(scope.get("headers", []))
            matched = headers.get(b"x-matched-path") or headers.get(b"x-vercel-matched-path")
            if matched:
                try:
                    clean = matched.decode("utf-8").split("?")[0]
                    if clean and not clean.endswith(".py"):
                        path = clean
                except Exception:
                    pass

            # 2. Strip Vercel function filename prefixes (/api/index.py or /api/index)
            for pfx in ["/api/index.py", "/api/index"]:
                if path == pfx or path == pfx + "/":
                    path = "/api"
                    break
                elif path.startswith(pfx + "/"):
                    path = "/api/" + path[len(pfx) + 1:]
                    break

            scope["path"] = path

        await self.asgi_app(scope, receive, send)

# Export app as the Vercel serverless entrypoint
app = VercelNormalizerASGI(fastapi_app)


