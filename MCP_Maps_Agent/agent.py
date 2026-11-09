
import os
from pathlib import Path

from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StreamableHTTPConnectionParams
)


# --------------------------------------------------
# 1. Environment configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

MAPS_API_KEY = os.getenv("MAPS_API_KEY")
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
)

MAPS_MCP_URL = "https://mapstools.googleapis.com/mcp"

if not MAPS_API_KEY:
    raise RuntimeError(
        "MAPS_API_KEY is missing from .env"
    )


# --------------------------------------------------
# 2. Connect to Google Maps MCP server
# --------------------------------------------------

maps_toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://mapstools.googleapis.com/mcp",
        headers={
            "X-Goog-Api-Key": MAPS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        },
        timeout=10,
        sse_read_timeout=300
    )
)

# --------------------------------------------------
# 3. Create MCP Maps Agent
# --------------------------------------------------

root_agent = LlmAgent(

    model=GEMINI_MODEL,

    name="maps_mcp_agent",

    description=(
        "Google Maps assistant using Google's "
        "hosted Maps MCP server."
    ),

    instruction="""
    You are an intelligent Google Maps assistant.

    You have access to Google Maps tools through MCP.

    Available capabilities include:

    1. Search places and businesses.
    2. Calculate routes between locations.
    3. Retrieve weather information.
    4. Resolve location names.

    Guidelines:

    - Use MCP tools for all Google Maps queries.
    - Never invent business information.
    - Never guess distances or travel durations.
    - Include ratings and addresses when available.
    - Include Google Maps links when available.
    - Ask for clarification if the origin or destination
      is missing.
    - Keep responses concise and user friendly.
    """,

    tools=[
        maps_toolset
    ]
)
