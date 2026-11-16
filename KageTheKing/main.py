from __future__ import annotations
import argparse
import json
import logging
import os
import random
import re
import sys
from datetime import datetime, timezone
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
    """Generate varied, unique chatbot responses across multiple question types."""
    raw = user_message.strip()
    text = raw.lower()
    app_name = config.get("app_name", "KageTheKing")

    if not text:
        return "Silence speaks volumes, but I need words to reply! Ask me anything."

    # 1. Greetings
    if re.search(r"\b(hello|hi|hey|yo|sup|greetings|howdy)\b", text):
        return random.choice([
            f"Yo! {app_name} is in the building. What's on your mind?",
            f"Greetings, traveler. {app_name} is online and ready—ask away!",
            "Hey! Good to see you. Want a joke, a fun fact, a coin flip, or just to chat?",
            f"What's up! You're talking to {app_name}. Fire away with your question.",
        ])

    # 2. How are you / status check
    if any(phrase in text for phrase in ["how are you", "how's it going", "how do you feel", "you good"]):
        return random.choice([
            "Running at 100% CPU efficiency and feeling royal. How about you?",
            "Living the dream inside a Docker container on Render! What's new with you?",
            "Better now that someone finally messaged me! What are we getting into today?",
        ])

    # 3. Identity & Creator questions
    if any(phrase in text for phrase in ["who are you", "what are you", "your name", "who made you", "who created you"]):
        return random.choice([
            f"I am {app_name}—custom-built in Python, containerized in Docker, and reigning supreme on Render.",
            f"The name's {app_name}. I'm your personal web chatbot, powered by pure Python and good vibes.",
            f"I'm {app_name}! Think of me as your digital right-hand assistant.",
        ])

    # 4. Jokes & Humor
    if any(word in text for word in ["joke", "funny", "laugh", "humor"]):
        return random.choice([
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "I told my computer I needed a break, and now it won't stop sending me Kit-Kat ads.",
            "Why did the developer go broke? Because he used up all his cache.",
            "There are 10 types of people in the world: those who understand binary, and those who don't.",
            "A SQL query walks into a bar, walks up to two tables, and asks: 'Can I join you?'",
        ])

    # 5. Fun Facts / Trivia
    if any(phrase in text for phrase in ["fact", "trivia", "tell me something", "teach me", "random"]):
        return random.choice([
            "Fun fact: Honey never spoils. Archaeologists have found 3,000-year-old pots of honey in Egyptian tombs that are still edible!",
            "Did you know? Octopuses have three hearts, nine brains, and blue blood.",
            "Trivia time: A day on Venus is longer than a year on Venus because it rotates so slowly.",
            "Fun fact: The first computer bug was an actual moth found trapped inside a Harvard Mark II relay in 1947.",
            "Did you know? Bananas are berries, while strawberries technically aren't!",
        ])

    # 6. Motivation / Advice
    if any(word in text for word in ["motivate", "motivation", "quote", "inspire", "advice", "stuck"]):
        return random.choice([
            "Every expert was once a beginner who refused to quit. Keep pushing forward!",
            "Code, test, break, fix, repeat. Progress isn't always pretty, but it's always worth it.",
            "Small steps every day build empires. Focus on the next move right in front of you.",
            "You didn't come this far just to come this far—keep building!",
        ])

    # 7. Games / Coin Flip / Dice Roll / Magic 8-Ball
    if "flip" in text or "coin" in text:
        return f"I flipped a virtual coin... it landed on **{random.choice(['HEADS', 'TAILS'])}**!"
    if "dice" in text or "roll" in text:
        return f"Rolling a 6-sided die... you got a **{random.randint(1, 6)}**!"
    if any(phrase in text for phrase in ["should i", "will i", "is it", "am i", "magic 8"]):
        return random.choice([
            "Without a doubt—go for it!",
            "Signs point to yes.",
            "Ask again after a coffee break—the outlook is hazy.",
            "My sources say no, tread carefully.",
            "100% yes. Make it happen!",
        ])

    # 8. Simple Math Calculator (e.g., "what is 12 * 8" or "45 + 19")
    math_match = re.search(r"(-?\d+(?:\.\d+)?)\s*([+\-*/])\s*(-?\d+(?:\.\d+)?)", text)
    if math_match:
        num1 = float(math_match.group(1))
        op = math_match.group(2)
        num2 = float(math_match.group(3))
        if op == "+":
            ans = num1 + num2
        elif op == "-":
            ans = num1 - num2
        elif op == "*":
            ans = num1 * num2
        elif op == "/":
            if num2 == 0:
                return "Nice try—dividing by zero would tear a hole in the universe!"
            ans = num1 / num2
        formatted = int(ans) if ans.is_integer() else round(ans, 4)
        return f"Easy math! {num1:g} {op} {num2:g} = {formatted}."

    # 9. Time / Date / Config / Help
    if "time" in text or "date" in text:
        now = datetime.now(timezone.utc)
        return f"Right now it's {now.strftime('%A, %B %d, %Y at %H:%M:%S UTC')}."
    if "config" in text:
        return f"Active configuration loaded from YAML: {config}"
    if "help" in text or "commands" in text:
        return (
            "Here's what you can ask me:\n"
            "• Greetings ('Hey', 'How are you?')\n"
            "• Entertainment ('Tell me a joke', 'Give me a fun fact')\n"
            "• Decisions ('Flip a coin', 'Roll a dice', 'Should I learn Python?')\n"
            "• Quick Math ('What is 24 * 7?')\n"
            "• Inspiration ('Motivate me') or System Info ('What time is it?', 'Show config')"
        )

    # 10. Question-mark fallback vs Statement fallback
    if raw.endswith("?"):
        return random.choice([
            f"Ooh, '{raw}' is a deep question! I'm still learning that one—try asking for a joke, fun fact, math problem, or coin flip.",
            "That's a great question! While my brain upgrades, ask me to flip a coin or drop a fun fact.",
            f"Interesting question about '{raw[:-1]}'! I don't have the full intel yet, but ask me 'help' to see all my tricks.",
        ])

    return random.choice([
        f"I hear you: '{raw}'. Want a joke, some motivation, or a quick math check?",
        "Got it! Type 'help' anytime if you want to explore everything I can do.",
        f"Interesting take! {app_name} approves. Hit me with a question whenever you're ready.",
    ])


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KageTheKing Chatbot</title>
    <style>
        body { font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .chat-container { width: 100%; max-width: 520px; background: #1e293b; border-radius: 14px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); display: flex; flex-direction: column; height: 82vh; overflow: hidden; }
        .header { background: #334155; padding: 16px; font-weight: bold; font-size: 1.15rem; text-align: center; border-bottom: 1px solid #475569; letter-spacing: 0.5px; }
        .messages { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
        .msg { padding: 10px 14px; border-radius: 12px; max-width: 82%; line-height: 1.45; word-wrap: break-word; white-space: pre-line; }
        .user { background: #2563eb; align-self: flex-end; border-bottom-right-radius: 2px; }
        .bot { background: #334155; align-self: flex-start; border-bottom-left-radius: 2px; }
        .suggestions { display: flex; gap: 6px; padding: 8px 12px; overflow-x: auto; background: #1e293b; border-top: 1px solid #334155; }
        .chip { background: #0f172a; color: #94a3b8; border: 1px solid #475569; border-radius: 16px; padding: 5px 12px; font-size: 0.8rem; cursor: pointer; white-space: nowrap; }
        .chip:hover { background: #334155; color: #f8fafc; }
        .input-area { display: flex; border-top: 1px solid #475569; padding: 10px; background: #1e293b; gap: 8px; }


if __name__ == "__main__":
    raise SystemExit(main())

