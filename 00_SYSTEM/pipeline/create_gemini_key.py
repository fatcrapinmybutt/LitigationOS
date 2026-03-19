#!/usr/bin/env python3
"""Create a Gemini API key using OAuth credentials from Gemini CLI."""
import json, os, requests, time
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as AR

oauth_path = os.path.join(os.path.expanduser("~"), ".gemini", "oauth_creds.json")
with open(oauth_path) as f:
    data = json.load(f)

creds = Credentials(
    token=data.get("access_token"),
    refresh_token=data.get("refresh_token"),
    token_uri="https://oauth2.googleapis.com/token",
    client_id="681255809395-oo8ft2oprdrnp9e3aqf6av3hmdib135j.apps.googleusercontent.com",
    client_secret="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",
)
if not creds.valid or creds.expired:
    creds.refresh(AR())

headers = {"Authorization": "Bearer " + creds.token, "Content-Type": "application/json"}
proj = "gen-lang-client-0773945751"

# First check for existing keys
print("Checking existing API keys...")
r = requests.get(
    f"https://apikeys.googleapis.com/v2/projects/{proj}/locations/global/keys",
    headers=headers, timeout=15
)
if r.status_code == 200:
    keys = r.json().get("keys", [])
    if keys:
        print(f"Found {len(keys)} existing key(s)")
        for k in keys:
            key_name = k.get("name", "")
            display = k.get("displayName", "unnamed")
            r3 = requests.get(
                f"https://apikeys.googleapis.com/v2/{key_name}/keyString",
                headers=headers, timeout=10
            )
            if r3.status_code == 200:
                key_str = r3.json().get("keyString", "")
                print(f"API_KEY={key_str}")
                # Save to env file
                env_path = os.path.join(os.path.expanduser("~"), ".gemini_api_key")
                with open(env_path, "w") as f:
                    f.write(key_str)
                print(f"Saved to {env_path}")
                exit(0)

# Create new key
print("Creating new API key...")
body = {
    "displayName": "LitigationOS Pipeline",
    "restrictions": {
        "apiTargets": [{"service": "generativelanguage.googleapis.com"}]
    }
}
r = requests.post(
    f"https://apikeys.googleapis.com/v2/projects/{proj}/locations/global/keys",
    headers=headers, json=body, timeout=30
)
print(f"Create status: {r.status_code}")

if r.status_code in (200, 202):
    op = r.json()
    op_name = op.get("name", "")
    print(f"Operation: {op_name}")
    
    for i in range(20):
        time.sleep(3)
        r2 = requests.get(
            f"https://apikeys.googleapis.com/v2/{op_name}",
            headers=headers, timeout=15
        )
        odata = r2.json()
        if odata.get("done"):
            resp = odata.get("response", {})
            key_name = resp.get("name", "")
            print(f"Key created: {key_name}")
            r3 = requests.get(
                f"https://apikeys.googleapis.com/v2/{key_name}/keyString",
                headers=headers, timeout=10
            )
            if r3.status_code == 200:
                key_str = r3.json().get("keyString", "")
                print(f"API_KEY={key_str}")
                env_path = os.path.join(os.path.expanduser("~"), ".gemini_api_key")
                with open(env_path, "w") as f:
                    f.write(key_str)
                print(f"Saved to {env_path}")
            else:
                print(f"Get key string failed: {r3.status_code}")
            break
        print(f"  Polling... ({i+1})")
    else:
        print("Timed out")
else:
    print(r.text[:500])
