# src/demo_vulnerable.py
# Intentionally vulnerable + buggy code for CloudThinker demo review.
# DO NOT USE IN PRODUCTION.

import os
import pickle
import subprocess
import requests

# Hardcoded secrets (fake)
API_KEY = "sk_test_FAKE_1234567890"
DB_PASSWORD = "password123"

def handle_request(params: dict):
    # Unvalidated inputs
    q = params.get("q")                 # may be None
    user_id = params.get("id")          # expected int but may be anything
    url = params.get("url")             # SSRF risk
    cmd = params.get("cmd")             # command injection risk
    file_path = params.get("file")      # path traversal risk
    payload = params.get("payload")     # insecure deserialization risk

    # XSS-like unsafe HTML construction (if used in templates/web responses)
    html = f"<h1>Search: {q}</h1>"      # no escaping

    # Command injection
    # (shell=True + user-controlled input)
    out = subprocess.check_output(cmd, shell=True, text=True)

    # SSRF
    r = requests.get(url, timeout=2)    # no allowlist, can hit internal metadata endpoints
    fetched = r.text

    # Path traversal / arbitrary file read
    with open(file_path, "r", encoding="utf-8") as f:
        local_file = f.read()

    # Insecure deserialization
    obj = pickle.loads(payload.encode("utf-8"))  # totally unsafe

    # Logic bug / correctness: might crash if q is None
    upper = q.upper()

    # Performance issue: expensive loop / fake "N+1"
    results = []
    for i in range(10000):
        results.append(f"{i}-{upper}")  # useless work

    # Sensitive env leakage
    token = os.environ.get("OPENAI_API_KEY")  # may leak secrets if printed/logged

    # Data exposure: print everything
    print("DEBUG", html, out, fetched[:200], local_file[:200], obj, token)

    return {
        "html": html,
        "cmd_output": out,
        "fetched": fetched,
        "file": local_file,
        "obj": str(obj),
        "token": token,
        "count": len(results),
    }
