"""
Minimal conductor - Cloud-safe fallback that actually calls AI providers.
Supports OpenAI, xAI (Grok), and Google Gemini via their REST APIs.
No ChromaDB, no heavy dependencies - works on Cloud Run read-only filesystem.
"""
import os
from pathlib import Path
from typing import Dict, Any, Iterator
from utils.logger import logger

# ---------------------------------------------------------------------------
# Optional SDK imports - use whichever is installed
# ---------------------------------------------------------------------------
try:
    from openai import OpenAI as _OpenAI
    _OPENAI_SDK = True
except ImportError:
    _OPENAI_SDK = False

try:
        import google.generativeai as _genai
    _GOOGLE_SDK = True
except (ImportError, Exception):
    _GOOGLE_SDK = False


class MinimalConductor:
    """Cloud-safe conductor that calls real AI APIs without ChromaDB."""

    def __init__(self):
        self.model = "minimal"
        self.retriever = None
        self.current_skill = None
        self.skill_manager = None
        self._client = None
        self._provider = None
        self._model_name = None
        self._setup_provider()
        logger.info(f"MinimalConductor initialized with provider: {self._provider}")

    def _setup_provider(self):
        """Detect which AI provider is available and configure the client."""
        openai_key = os.getenv("OPENAI_API_KEY", "")
        xai_key = os.getenv("XAI_API_KEY", "")
        google_key = os.getenv("GOOGLE_API_KEY", "")

        # Priority: OpenAI → xAI (Grok) → Google
        if openai_key and openai_key.startswith("sk-") and _OPENAI_SDK:
            try:
                self._client = _OpenAI(api_key=openai_key)
                self._provider = "openai"
                self._model_name = "gpt-4o-mini"
                logger.info("MinimalConductor: using OpenAI")
                return
            except Exception as e:
                logger.warning(f"OpenAI init failed: {e}")

        if xai_key and _OPENAI_SDK:
            try:
                self._client = _OpenAI(api_key=xai_key, base_url="https://api.x.ai/v1")
                self._provider = "xai"
                self._model_name = "grok-beta"
                logger.info("MinimalConductor: using xAI (Grok)")
                return
            except Exception as e:
                logger.warning(f"xAI init failed: {e}")

        if google_key:
            if _GOOGLE_SDK:
                try:
                    _genai.configure(api_key=google_key)
                    self._client = _genai.GenerativeModel("gemini-1.5-flash")
                    self._provider = "google"
                    self._model_name = "gemini-1.5-flash"
                    logger.info("MinimalConductor: using Google Gemini")
                    return
                except Exception as e:
                    logger.warning(f"Google SDK init failed: {e}")
            # Fallback: call Gemini via httpx REST
            try:
                import httpx
                self._client = {"key": google_key}
                self._provider = "google_rest"
                self._model_name = "gemini-1.5-flash"
                logger.info("MinimalConductor: using Google Gemini (REST)")
                return
            except ImportError:
                pass

        # No provider available
        self._provider = None
        logger.warning("MinimalConductor: no AI provider configured")

    def _call_ai(self, query: str) -> str:
        """Call the configured AI provider and return the response text."""
        if self._provider is None:
            keys = [k for k in ("OPENAI_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY") if os.getenv(k)]
            if keys:
                return (f"API key(s) found ({', '.join(keys)}) but could not connect. "
                        f"Check that the key is valid and the provider SDK is installed.")
            return ("Minimal mode: no AI provider configured. "
                    "Set OPENAI_API_KEY, GOOGLE_API_KEY or XAI_API_KEY to enable full-mode. "
                    f"(You asked: {query})")

        try:
            if self._provider in ("openai", "xai"):
                response = self._client.chat.completions.create(
                    model=self._model_name,
                    messages=[
                        {"role": "system", "content": (
                            "You are Conductor, a helpful Voice AI assistant with memory. "
                            "Be concise and conversational."
                        )},
                        {"role": "user", "content": query}
                    ],
                    max_tokens=500,
                    temperature=0.7,
                )
                return response.choices[0].message.content

            elif self._provider == "google":
                response = self._client.generate_content(query)
                return response.text

            elif self._provider == "google_rest":
                import httpx
                url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                       f"{self._model_name}:generateContent?key={self._client['key']}")
                payload = {"contents": [{"parts": [{"text": query}]}]}
                r = httpx.post(url, json=payload, timeout=30)
                r.raise_for_status()
                data = r.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]

        except Exception as e:
            logger.error(f"AI call failed ({self._provider}): {e}")
            return f"I encountered an error calling {self._provider}: {str(e)}"

        return "Unexpected error in MinimalConductor._call_ai"

    def activate_skill(self, skill_name: str) -> bool:
        """Stub - no skill execution in minimal mode."""
        return False

    def chat(self, query: str, platform_filter: str = None) -> Dict[str, Any]:
        """Chat with the AI provider."""
        response_text = self._call_ai(query)
        return {
            "response": response_text,
            "sources": [],
            "context_used": 0,
            "model": f"minimal/{self._provider or 'none'}",
        }

    def stream_chat(self, query: str, platform_filter: str = None) -> Iterator[Dict[str, Any]]:
        """Stream chat - yields content in chunks."""
        yield {"type": "sources", "data": []}
        response_text = self._call_ai(query)
        # Stream in chunks of 80 chars for a natural feel
        chunk_size = 80
        for i in range(0, len(response_text), chunk_size):
            yield {"type": "content", "data": response_text[i:i + chunk_size]}
