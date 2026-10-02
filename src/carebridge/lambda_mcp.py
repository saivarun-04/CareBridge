"""Lambda handler for the MCP server via API Gateway (using Mangum)."""

from mangum import Mangum

from carebridge.server import app

# Create the Mangum adapter for the FastAPI app
handler = Mangum(app, lifespan="off")