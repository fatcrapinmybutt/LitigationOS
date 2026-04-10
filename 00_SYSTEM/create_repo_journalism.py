import subprocess, json, urllib.request

proc = subprocess.run(
    ['git', 'credential', 'fill'],
    input='protocol=https\nhost=github.com\n\n',
    capture_output=True, text=True
)
lines = proc.stdout.strip().split('\n')
creds = dict(line.split('=', 1) for line in lines if '=' in line)
token = creds.get('password', '')

data = json.dumps({
    "name": "cortex-journalism",
    "description": "Free Investigative Journalism & Media Intelligence Starter Pack for CORTEX — source verification, corporate ownership tracing, public records analysis",
    "homepage": "https://fatcrapinmybutt.github.io/cortex-site/",
    "has_discussions": True,
    "auto_init": False
}).encode()

req = urllib.request.Request(
    'https://api.github.com/user/repos',
    data=data,
    headers={
        'Authorization': f'token {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github+json'
    }
)
try:
    resp = urllib.request.urlopen(req)
    print(f"Created: {json.loads(resp.read())['html_url']}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    if 'already exists' in body:
        print("Repo already exists - OK")
    else:
        print(f"Error {e.code}: {body}")
