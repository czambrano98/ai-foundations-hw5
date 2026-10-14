"""Configuration for the Campus Customs agents.

Every agent uses the SAME model: `gpt-6-luna`, reached through the user's
Portkey gateway (an OpenAI-compatible endpoint). Claude Code is only the tool
that wrote this code; at runtime the agents call gpt-6-luna via Portkey, never a
Claude model.

Nothing here reads the network at import time. `build_model()` is called lazily
when the agents actually run, so the backend imports fine without a key.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

# The one model every agent must use (instructor requirement).
MODEL_NAME = os.getenv("CAMPUS_MODEL", "gpt-6-luna")

# Portkey's OpenAI-compatible gateway. Override via env if your Portkey setup
# uses a different base URL.
PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")

# Project paths.
HW5_ROOT = Path(__file__).resolve().parent.parent
MCP_CONFIG_PATH = HW5_ROOT / ".mcp.json"
AUDIT_PATH = HW5_ROOT / "output" / "audit_trail.json"

# Keep token use in check: cap total model requests per top-level board run and
# bound each agent's tool-call iterations.
MAX_REQUESTS_PER_RUN = int(os.getenv("CAMPUS_MAX_REQUESTS", "60"))
MAX_DELEGATION_DEPTH = int(os.getenv("CAMPUS_MAX_DELEGATION_DEPTH", "3"))
# Total delegations allowed across a whole board run (cycle guard + this cap keep
# full-connectivity delegation from looping and burning the request budget).
MAX_DELEGATIONS_PER_RUN = int(os.getenv("CAMPUS_MAX_DELEGATIONS", "8"))
AGENT_TOOL_RETRIES = int(os.getenv("CAMPUS_AGENT_RETRIES", "2"))

# The FastMCP server cold-starts slowly on Windows; give the toolset room to
# connect before timing out.
MCP_INIT_TIMEOUT = float(os.getenv("CAMPUS_MCP_INIT_TIMEOUT", "60"))


@lru_cache(maxsize=1)
def build_model():
    """Build the shared gpt-6-luna model routed through Portkey.

    Reads PORTKEY_API_KEY from the environment. Optional extras:
      - PORTKEY_VIRTUAL_KEY  -> sent as x-portkey-virtual-key
      - PORTKEY_PROVIDER     -> sent as x-portkey-provider
    Raises a clear error if the key is missing so runs fail loudly, not silently.
    """
    from openai import AsyncOpenAI
    from pydantic_ai.models.openai import OpenAIResponsesModel
    from pydantic_ai.providers.openai import OpenAIProvider

    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        raise RuntimeError(
            "PORTKEY_API_KEY is not set. Set it (and optionally PORTKEY_VIRTUAL_KEY / "
            "PORTKEY_PROVIDER) to run the agents against gpt-6-luna via Portkey."
        )

    headers: dict[str, str] = {}
    if os.getenv("PORTKEY_VIRTUAL_KEY"):
        headers["x-portkey-virtual-key"] = os.environ["PORTKEY_VIRTUAL_KEY"]
    if os.getenv("PORTKEY_PROVIDER"):
        headers["x-portkey-provider"] = os.environ["PORTKEY_PROVIDER"]

    client = AsyncOpenAI(
        base_url=PORTKEY_BASE_URL,
        api_key=api_key,
        default_headers=headers or None,
    )
    # gpt-6-luna is a reasoning model: with function tools it must use the
    # Responses API (/v1/responses), not Chat Completions.
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))
