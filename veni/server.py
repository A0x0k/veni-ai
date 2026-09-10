"""
Live Canvas Web Dashboard Server for Veni AI.

Exposes Veni's internal state via a web interface:
- Real-time chat history
- System status and logs
- Browser automation feed
- Tool execution history
"""

import logging
import os
import secrets
import threading
from pathlib import Path
from typing import Any, Optional

from veni.config import config

try:
    import uvicorn
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse
    from fastapi.templating import Jinja2Templates
except ImportError:
    FastAPI = Any  # type: ignore
    HTTPException = Any  # type: ignore
    uvicorn = None  # type: ignore

logger = logging.getLogger("veni.server")


class VeniDashboard:
    """
    FastAPI server for Veni AI Dashboard.
    """

    def __init__(self, bot: Any, port: int = 8000):
        self.bot = bot
        self.port = port
        self.available = uvicorn is not None
        self.app = None
        self.templates = None
        self._thread: Optional[threading.Thread] = None
        self._server: Optional[uvicorn.Server] = None
        self.auth_token = (
            os.getenv("VENI_DASHBOARD_TOKEN")
            or config.get("security.dashboard_token")
            or secrets.token_urlsafe(24)
        )

        if not self.available:
            logger.warning("FastAPI/Uvicorn not installed. Dashboard disabled.")
            return

        self.app = FastAPI(title="Veni AI Live Canvas")

        # Templates directory
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(exist_ok=True)
        self.templates = Jinja2Templates(directory=str(template_dir))

        self._setup_routes()

    def _setup_routes(self):
        """Register FastAPI routes."""
        if self.app is None or self.templates is None:
            return

        def require_auth(request: Request) -> None:
            token = request.query_params.get("token", "")
            auth = request.headers.get("Authorization", "")
            header_token = request.headers.get("X-Veni-Token", "")
            if auth.lower().startswith("bearer "):
                header_token = auth[7:].strip()
            if not secrets.compare_digest(token or header_token, self.auth_token):
                raise HTTPException(status_code=401, detail="Unauthorized")

        @self.app.get("/", response_class=HTMLResponse)
        async def index(request: Request):
            require_auth(request)
            return self.templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "bot_name": "Veni AI",
                    "status": "Online",
                    "provider": self.bot.provider_name,
                    "model": self.bot.model_name,
                    "history": [m.to_dict() for m in self.bot.history.messages],
                    "dashboard_token": self.auth_token,
                },
            )

        @self.app.get("/api/status")
        async def get_status(request: Request):
            require_auth(request)
            return {
                "status": "Online",
                "provider": self.bot.provider_name,
                "model": self.bot.model_name,
                "memory_stats": self.bot.memory_system.get_stats(),
                "scheduler_jobs": self.bot.scheduler.get_status(),
            }

        @self.app.get("/api/history")
        async def get_history(request: Request):
            require_auth(request)
            return [m.to_dict() for m in self.bot.history.messages]

        @self.app.post("/api/chat")
        async def chat(request: Request):
            require_auth(request)
            data = await request.json()
            user_input = data.get("message")
            if not user_input:
                return {"error": "Message is required"}

            # Run in a separate thread to not block the FastAPI event loop
            # and to allow Veni core to process it properly
            def process():
                self.bot.history.add_message("user", user_input)
                self.bot._suggest_intelligence(user_input)
                self.bot._update_system_prompt(user_input)

                # Non-streaming for simplicity in web for now
                response = ""
                messages = self.bot.history.get_context_messages(
                    self.bot.context_tokens
                )
                for chunk in self.bot.ai_client.chat(messages, stream=True):
                    response += chunk

                if response:
                    self.bot.history.add_message("assistant", response)
                    self.bot._record_memory(user_input, response)

            threading.Thread(target=process).start()
            return {"status": "Processing"}

    def start(self):
        """Start the dashboard server in a background thread."""
        if not self.available or self.app is None:
            logger.error("FastAPI or Uvicorn not installed. Dashboard not started.")
            return

        config = uvicorn.Config(
            self.app, host="127.0.0.1", port=self.port, log_level="error"
        )
        self._server = uvicorn.Server(config)

        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()
        logger.info(
            "Live Canvas Dashboard starting on http://localhost:%d/?token=%s",
            self.port,
            self.auth_token,
        )
        logger.warning(
            "Dashboard uses bearer-token access but exposes chat history and shell "
            "output to anyone with the token. Do NOT expose port %d to the internet "
            "or untrusted networks.",
            self.port,
        )

    def stop(self):
        """Stop the server gracefully."""
        if self._server:
            self._server.should_exit = True
            if self._thread:
                self._thread.join(timeout=5)
            logger.info("Live Canvas Dashboard stopped.")
