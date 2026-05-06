import os

from dotenv import load_dotenv

load_dotenv()

HMAC_SECRET = os.environ.get("HMAC_SECRET", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./defensor.db")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8001")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
