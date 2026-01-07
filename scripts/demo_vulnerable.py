# scripts/demo_vulnerable.py
# Intentionally vulnerable code for CloudThinker demo
# DO NOT USE IN PRODUCTION

import os
import subprocess
import requests
import pickle

# Hardcoded secrets (security issue)
API_KEY = "sk_test_FAKE_1234567890"
DB_PASSWORD = "password123"

def handle_request(params):
    # No input validation
    user_id = params.get("id")
    query = params.get("q")
    url = params.get("url")
    cmd = params.get("cmd")
    file_path = params.get("file")
    payload = params.get("payload")

    # XSS-like issue (if used in web response)
    html = f"<h1>Search result for {query}</h1>"

    # Command injection
    output = subprocess.check_output(
        cmd,
        shell=True,
        text=True
    )

    # SSRF vulnerability
    response = requests.get(url)
    remote_data = response.text

    # Path traversal / arbitrary file read
    with open(file_path, "r") as f:
        local_data = f.read()

    # Insecure deserialization
    obj = pickle.loads(payload.encode())

    # Logic bug: query may be None
    upper_query = query.upper()

    # Performance issue
    results = []
    for i in range(10000):
        results.append(f"{i}-{upper_query}")

    # Sensitive data exposure
    print("DEBUG LOG:")
    print("API_KEY:", API_KEY)
    print("ENV TOKEN:", os.environ.get("OPENAI_API_KEY"))
    print("CMD OUTPUT:", output)
    print("REMOTE DATA:", remote_data[:200])
    print("LOCAL FILE:", local_data[:200])
    print("OBJ:", obj)

    return {
        "html": html,
        "count": len(results),
        "data": results[:10]
    }
