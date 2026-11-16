from __future__ import annotations
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_CONFIG_PATH = Path("config.yaml")


def setup_logging(log_level: int = DEFAULT_LOG_LEVEL) -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    def log_exception(exc_type: type, exc_value: Exception, exc_traceback: Any) -> None:
        """Log uncaught exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = log_exception


def load_config(path: Path) -> dict[str, Any]:
    """Load runtime configuration from a file."""
    if not path.exists():
        logging.warning("Config file %s not found. Using defaults.", path)
        return {}

    logging.info("Loading config from %s", path)
    config: dict[str, Any] = {"config_path": str(path)}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and ":" in line:
            key, value = line.split(":", 1)
            config[key.strip()] = value.strip()
    return config


def generate_reply(user_message: str, config: dict[str, Any]) -> str:
    """Generate a chatbot response based on the user's message."""
    text = user_message.strip().lower()
    app_name = config.get("app_name", "KageTheKing")

    if not text:
        return "Say something and I'll reply!"
    if any(word in text for word in ["hello", "hi", "hey", "yo"]):
        return f"Hey there! I'm {app_name}. How can I help you today?"
    if "who are you" in text or "your name" in text:
        return f"I am {app_name}, running live on Render!"
    if "time" in text:
        return f"The current server UTC time is {datetime.utcnow().strftime('%H:%M:%S')}."
    if "config" in text:
        return f"Here is my active configuration: {config}"
    if "help" in text:
        return "Try asking me: 'hello', 'who are you', 'what time is it', or 'show config'."

    return f"You said: '{user_message}'. (Customize generate_reply() in main.py to teach me new responses!)"


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KageTheKing Chatbot</title>
    <style>
        body { font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .chat-container { width: 100%; max-width: 480px; background: #1e293b; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); display: flex; flex-direction: column; height: 80vh; overflow: hidden; }
        .header { background: #334155; padding: 16px; font-weight: bold; font-size: 1.1rem; text-align: center; border-bottom: 1px solid #475569; }
        .messages { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
        .msg { padding: 10px 14px; border-radius: 10px; max-width: 80%; line-height: 1.4; word-wrap: break-word; }
        .user { background: #2563eb; align-self: flex-end; }
        .bot { background: #334155; align-self: flex-start; }
        .input-area { display: flex; border-top: 1px solid #475569; padding: 10px; background: #1e293b; gap: 8px; }
        input { flex: 1; padding: 10px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #f8fafc; outline: none; }
        button { padding: 10px 18px; border: none; border-radius: 8px; background: #2563eb; color: white; font-weight: bold; cursor: pointer; }
        button:hover { background: #1d4ed8; }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="header">KageTheKing Chatbot</div>
        <div class="messages" id="messages">
            <div class="msg bot">KageTheKing is running! Type 'help' to see what I can do.</div>
        </div>
        <form class="input-area" id="chat-form">
            <input type="text" id="user-input" placeholder="Type a message..." autocomplete="off" required />
            <button type="submit">Send</button>
        </form>
    </div>
    <script>
        const form = document.getElementById('chat-form');
        const input = document.getElementById('user-input');
        const messages = document.getElementById('messages');

        function addMessage(text, sender) {
            const div = document.createElement('div');
            div.className = 'msg ' + sender;
            div.textContent = text;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = input.value.trim();
            if (!text) return;
            addMessage(text, 'user');
            input.value = '';

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await res.json();
                addMessage(data.reply, 'bot');
            } catch (err) {
                addMessage('Error connecting to server.', 'bot');
            }
        });
    </script>
</body>
</html>"""


def run(config: dict[str, Any] | None = None) -> str:
    """Run the application logic and serve the interactive chatbot webpage."""
    if config is None:
        config = {}

    logging.debug("Running with config: %s", config)
    message = "KageTheKing is running!"
    print(message, flush=True)

    class AppHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))

        def do_POST(self) -> None:
            if self.path != "/chat":
                self.send_response(404)
                self.end_headers()
                return

            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(raw_body)
                user_msg = str(payload.get("message", ""))
            except json.JSONDecodeError:
                user_msg = ""

            reply = generate_reply(user_msg, config)
            response_bytes = json.dumps({"reply": reply}).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_bytes)))
            self.end_headers()
            self.wfile.write(response_bytes)

        def log_message(self, format: str, *args: Any) -> None:
            logging.info("%s - %s", self.address_string(), format % args)

    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), AppHandler)
    logging.info("Serving KageTheKing Chatbot on http://0.0.0:%s", port)
    server.serve_forever()
    return message


def main() -> int:
    """Main function to run the application."""
    parser = argparse.ArgumentParser(description="KageTheKing Application")
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to a configuration file.",
    )
    args = parser.parse_args()

    log_level = getattr(logging, args.log_level.upper(), DEFAULT_LOG_LEVEL)
    setup_logging(log_level)

    logging.info("Starting KageTheKing application...")
    config = load_config(args.config)
    message = run(config)
    print(message)
    logging.info("KageTheKing application finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

