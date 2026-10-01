"""Development server for CareBridge web views.

Runs a FastAPI application that serves the static HTML files in the `web/` directory
and also proxies the MCP endpoints (already running on port 8000 from the main server).
For simplicity this dev server only serves the HTML; the MCP server should be started
separately (e.g., `uvicorn carebridge.server:app --port 8000`).
"""

import os
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Ensure the project root is on the path for imports if needed.
sys.path.append(os.path.abspath('.'))

app = FastAPI()

# Mount the web directory at the root URL.
app.mount("/", StaticFiles(directory="web", html=True), name="web")

if __name__ == "__main__":
    import uvicorn
    # Run on a different port to avoid clashing with the MCP server.
    uvicorn.run(app, host="0.0.0.0", port=8001)
