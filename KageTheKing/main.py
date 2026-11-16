from __future__ import annotations
import argparse, json, logging, os, random, re, sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_CONFIG_PATH = Path("config.yaml")

def setup_logging(log_level: int = DEFAULT_LOG_LEVEL) -> None:
    logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler(sys.stdout)])

def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    config: dict[str, Any] = {"config_path": str(path)}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.strip().startswith("#") and ":" in line:
            k, v = line.split(":", 1)
            config[k.strip()] = v.strip()
    return config

def generate_reply(user_message: str, config: dict[str, Any]) -> str:
    raw = user_message.strip()
    text = raw.lower()
    name = config.get("app_name", "KageTheKing")
    if not text:
        return "Say something and I will reply!"
    if re.search(r"\b(hello|hi|hey|yo|sup|greetings)\b", text):
        return random.choice([f"Yo! {name} is online. What is on your mind?", f"Greetings! {name} is ready—ask away!", "Hey! Want a joke, a fun fact, a coin flip, or quick math?"])
    if any(p in text for p in ["how are you", "how's it going", "you good"]):
        return random.choice(["Running at 100% efficiency and feeling royal! How about you?", "Living the dream on Render! What is new with you?"])
    if any(p in text for p in ["who are you", "your name", "who made you"]):
        return f"I am {name}, custom-built in Python and running live on Render!"
    if any(w in text for w in ["joke", "funny", "laugh"]):
        return random.choice([
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "Why did the developer go broke? Because he used up all his cache.",
            "There are 10 types of people: those who understand binary, and those who don't.",
        ])
    if any(p in text for p in ["fact", "trivia", "tell me something"]):
        return random.choice([
            "Fun fact: Honey never spoils—3,000-year-old honey from Egyptian tombs is still edible!",
            "Did you know? Octopuses have three hearts, nine brains, and blue blood.",
            "Trivia: The first computer bug was a real moth found inside a computer relay in 1947.",
        ])
    if any(w in text for w in ["motivate", "quote", "inspire", "advice"]):
        return random.choice([
            "Every expert was once a beginner who refused to quit. Keep building!",
            "Code, test, break, fix, repeat. Progress is always worth it.",
        ])
    if "flip" in text or "coin" in text:
        return f"Coin flip result: {random.choice(['HEADS', 'TAILS'])}!"
    if "dice" in text or "roll" in text:
        return f"You rolled a {random.randint(1, 6)}!"
    if any(p in text for p in ["should i", "will i", "magic 8"]):
        return random.choice(["Without a doubt—go for it!", "Signs point to yes.", "My sources say no.", "100% yes!"])
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*([+\-*/])\s*(-?\d+(?:\.\d+)?)", text)
    if m:
        a, op, b = float(m.group(1)), m.group(2), float(m.group(3))
        if op == "/" and b == 0:
            return "Nice try—cannot divide by zero!"
        res = a + b if op == "+" else a - b if op == "-" else a * b if op == "*" else a / b
        return f"Answer: {int(res) if res.is_integer() else round(res, 4)}"
    if "time" in text or "date" in text:
        return f"Current UTC time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    if "config" in text:
        return f"Loaded config: {config}"
    if "help" in text:
        return "Ask me: 'Hello', 'Tell me a joke', 'Fun fact', 'Flip a coin', 'Roll a dice', 'Motivate me', '42 * 19', or 'What time is it?'"
    if raw.endswith("?"):
        return random.choice([f"Great question about '{raw[:-1]}'! Try asking for a joke, fun fact, coin flip, or math.", "Interesting question! Type 'help' to see everything I can do."])
    return random.choice([f"I hear you: '{raw}'. Want a joke, fun fact, or coin flip?", f"{name} approves! Ask me a question or type 'help'."])

HTML_PAGE = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>KageTheKing Chatbot</title>
<style>
body{font-family:system-ui,sans-serif;background:#0f172a;color:#f8fafc;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
.box{width:100%;max-width:500px;background:#1e293b;border-radius:12px;display:flex;flex-direction:column;height:82vh;overflow:hidden}
.hdr{background:#334155;padding:15px;font-weight:bold;text-align:center}
.msgs{flex:1;padding:15px;overflow-y:auto;display:flex;flex-direction:column;gap:10px}
.msg{padding:10px 14px;border-radius:10px;max-width:80%;line-height:1.4;white-space:pre-line}
.user{background:#2563eb;align-self:flex-end}.bot{background:#334155;align-self:flex-start}
.chips{display:flex;gap:6px;padding:8px;overflow-x:auto;border-top:1px solid #334155}
.chip{background:#0f172a;color:#94a3b8;border:1px solid #475569;border-radius:14px;padding:5px 10px;font-size:.8rem;cursor:pointer}
form{display:flex;border-top:1px solid #475569;padding:10px;gap:8px}
input{flex:1;padding:10px;border-radius:8px;border:1px solid #475569;background:#0f172a;color:#fff}
button.send{padding:10px 16px;border:none;border-radius:8px;background:#2563eb;color:#fff;font-weight:bold;cursor:pointer}
</style></head><body><div class="box"><div class="hdr">KageTheKing Chatbot</div>
<div class="msgs" id="m"><div class="msg bot">KageTheKing is online! Ask a question or tap a button below.</div></div>
<div class="chips">
<button class="chip" onclick="send('Tell me a joke')">Joke</button>
<button class="chip" onclick="send('Fun fact')">Fun Fact</button>
<button class="chip" onclick="send('Flip a coin')">Flip Coin</button>
<button class="chip" onclick="send('42 * 19')">Math</button>
<button class="chip" onclick="send('Motivate me')">Motivate</button>
<button class="chip" onclick="send('Help')">Help</button>
</div><form id="f"><input id="i" placeholder="Ask KageTheKing..." required><button class="send">Send</button></form></div>
<script>
const m=document.getElementById('m'),i=document.getElementById('i');
function add(t,c){const d=document.createElement('div');d.className='msg '+c;d.textContent=t;m.appendChild(d);m.scrollTop=m.scrollHeight}
async function send(t){if(!t)return;add(t,'user');const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:t})});const d=await r.json();add(d.reply,'bot')}
document.getElementById('f').onsubmit=e=>{e.preventDefault();const t=i.value.trim();i.value='';send(t)};
</script></body></html>"""

def run(config: dict[str, Any] | None = None) -> str:
    config = config or {}
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        def do_POST(self) -> None:
            if self.path != "/chat":
                self.send_response(404); self.end_headers(); return
            length = int(self.headers.get("Content-Length", 0))
            try:
                msg = str(json.loads(self.rfile.read(length).decode("utf-8")).get("message", ""))
            except Exception:
                msg = ""
            body = json.dumps({"reply": generate_reply(msg, config)}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    port = int(os.environ.get("PORT", 10000))
    logging.info("Serving KageTheKing on 0.0.0.0:%s", port)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
    return "KageTheKing is running!"

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    setup_logging(getattr(logging, args.log_level.upper(), DEFAULT_LOG_LEVEL))
    return 0 if run(load_config(args.config)) else 1

if __name__ == "__main__":
    raise SystemExit(main())
