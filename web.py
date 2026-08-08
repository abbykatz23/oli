#!/usr/bin/env python3
"""Tiny web UI to trigger a new artwork on the Inky display."""

import subprocess
from pathlib import Path
from flask import Flask, render_template_string, redirect, request, url_for

SCRIPT = Path(__file__).with_name("display_art.py")

WORDS = [
    "Awesome", "Amazing", "Brilliant", "Bold", "Brave",
    "Bright", "Caring", "Cheerful", "Clever", "Confident",
    "Creative", "Curious", "Daring", "Dazzling", "Delightful",
    "Dynamic", "Energetic", "Excellent", "Fantastic", "Fearless",
    "Friendly", "Funny", "Generous", "Genius", "Gentle",
    "Glowing", "Happy", "Helpful", "Honest", "Incredible",
    "Inspiring", "Jolly", "Joyful", "Kind", "Legendary",
    "Lovely", "Loyal", "Magnificent", "Marvelous", "Mighty",
    "Outstanding", "Patient", "Peaceful", "Playful", "Powerful",
    "Proud", "Radiant", "Remarkable", "Resilient", "Wonderful",
]

app = Flask(__name__)
current = None  # last subprocess.Popen, or None

PAGE = """
<!doctype html>
<title>Oli's Art Display</title>
<style>
  body { font-family: system-ui, sans-serif; display: grid; place-items: center;
         height: 100vh; margin: 0; background: #f4f1ea; }
  form { text-align: center; }
  button { font-size: 2rem; padding: 1.5rem 3rem; border-radius: 1rem;
           border: none; background: #2b2b2b; color: white; cursor: pointer;
           min-width: 20rem; }
  p { color: #666; margin-top: 1rem; }
</style>
<form method="post" action="/refresh">
  <button type="submit" id="btn">Oli Awesome!</button>
  {% if msg %}<p>{{ msg }}</p>{% endif %}
</form>
<script>
  const words = {{ words|tojson }};
  const btn = document.getElementById("btn");
  function pick() {
    const w = words[Math.floor(Math.random() * words.length)];
    btn.textContent = "Oli " + w + "!";
  }
  pick();
  setInterval(pick, 2500);
</script>
"""

MESSAGES = {
    "started": "Refreshing… give it about a minute.",
    "busy": "Already refreshing… please wait.",
}

@app.route("/")
def index():
    msg = MESSAGES.get(request.args.get("status"))
    return render_template_string(PAGE, words=WORDS, msg=msg)

@app.route("/refresh", methods=["POST"])
def refresh():
    global current
    if current is not None and current.poll() is None:
        return redirect(url_for("index", status="busy"))
    current = subprocess.Popen(["/usr/bin/python3", str(SCRIPT)])
    return redirect(url_for("index", status="started"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
