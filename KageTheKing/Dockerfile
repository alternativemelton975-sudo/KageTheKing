FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create config.yaml directly inside the image
RUN cat <<'EOF' > config.yaml
app_name: KageTheKing
environment: production
EOF

# Write your Python application directly into main.py
RUN cat <<'EOF' > main.py
from __future__ import annotations
import argparse
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_CONFIG_PATH = Path("config.yaml")


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Lightweight HTTP handler to keep the Render Web Service alive."""

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"KageTheKing is running!")

    def log_message(self, format: str, *args: Any) -> None:
        logging.info("%s - %s", self.address_string(), format % args)


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
    return {"config_path": str(path)}


def run(config: dict[str, Any] | None = None) -> str:
    """Run the application logic and keep the web server listening."""
    if config is None:
        config = {}

    logging.debug("Running with config: %s", config)
    print("KageTheKing is running!", flush=True)

    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logging.info("Listening on 0.0.0.0:%s...", port)
    server.serve_forever()
    return "KageTheKing stopped."


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
    run(config)
    logging.info("KageTheKing application finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
EOF

# Run the application
CMD ["python", "main.py", "--log-level", "INFO", "--config", "config.yaml"]
