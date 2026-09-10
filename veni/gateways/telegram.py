"""
Telegram Gateway for Veni AI.

Allows remote interaction with Veni via a Telegram bot.
Supports:
- Sending commands and messages
- Receiving AI responses (Markdown formatted)
- Remote project status checks
- File notifications
"""

import asyncio
import logging
import os
import threading
from typing import Any, Optional

try:
    from telegram import Update
    from telegram.ext import (
        ApplicationBuilder,
        CommandHandler,
        ContextTypes,
        MessageHandler,
        filters,
    )
except ImportError:
    Update = Any  # type: ignore
    ApplicationBuilder = None  # type: ignore

logger = logging.getLogger("veni.gateways.telegram")


class TelegramGateway:
    """
    Gateway for Telegram interaction.
    """

    def __init__(self, bot: Any, token: Optional[str] = None):
        self.bot = bot
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.application = None
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._stop_event = threading.Event()

    def start(self):
        """Start the Telegram bot in a background thread."""
        if not self.token:
            logger.warning("Telegram token missing. Gateway not started.")
            return

        if not ApplicationBuilder:
            logger.error("python-telegram-bot is not installed.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_bot, daemon=True)
        self._thread.start()
        logger.info("Telegram gateway starting...")

    def _run_bot(self):
        """Internal bot runner."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        self.application = ApplicationBuilder().token(self.token).build()

        # Add handlers
        self.application.add_handler(CommandHandler("start", self._start_cmd))
        self.application.add_handler(CommandHandler("status", self._status_cmd))
        self.application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self._handle_message))

        logger.info("Telegram bot initialized and polling.")
        
        # run_polling is blocking, so we run it in the loop
        self._loop.run_until_complete(self.application.initialize())
        self._loop.run_until_complete(self.application.start())
        self._loop.run_until_complete(self.application.updater.start_polling())
        
        # Wait for stop event
        while not self._stop_event.is_set():
            self._loop.run_until_complete(asyncio.sleep(1))
            
        # Cleanup
        self._loop.run_until_complete(self.application.updater.stop())
        self._loop.run_until_complete(self.application.stop())
        self._loop.run_until_complete(self.application.shutdown())

    async def _start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        await update.message.reply_text(
            "👋 Hello! I am Veni AI Gateway.\n"
            "Send me any message or command, and I will process it on your terminal."
        )

    async def _status_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        status = (
            f"🤖 Veni AI Status\n"
            f"Provider: {self.bot.provider_name}\n"
            f"Model: {self.bot.model_name}\n"
            f"CWD: {self.bot.cwd.name}"
        )
        await update.message.reply_text(status)

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route Telegram message to Veni Core."""
        user_input = update.message.text
        logger.info("Telegram message: %s", user_input)

        try:
            self.bot.history.add_message("user", user_input)

            messages = self.bot.history.get_context_messages(self.bot.context_tokens)
            response = ""
            for chunk in self.bot.ai_client.chat(messages, stream=True):
                response += chunk

            self.bot.history.add_message("assistant", response)

            if len(response) > 4000:
                response = response[:3900] + "\n\n... (truncated)"

            await update.message.reply_text(response, parse_mode=None)
        except Exception as e:
            logger.error("Error processing Telegram message: %s", e)
            await update.message.reply_text(f"❌ Error: {str(e)}")

    def stop(self):
        """Stop the gateway."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Telegram gateway stopped.")
