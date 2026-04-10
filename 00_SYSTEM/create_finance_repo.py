import subprocess, json, urllib.request, urllib.error

proc = subprocess.run(
    ['git', 'credential', 'fill'],
    input='protocol=https\nhost=github.com\n\n',
    capture_output=True, text=True
)
lines = proc.stdout.strip().split('\n')
creds = dict(line.split('=', 1) for line in lines if '=' in line)
token = creds.get('password', '')
if not token:
    print("ERROR: No credential found"); exit(1)
print(f"Got credential (len={len(token)})")

data = json.dumps({
    "name": "cortex-finance",
    "description": "Free Financial Intelligence & Market Analysis Starter Pack for CORTEX — forensic accounting, market surveillance, insider trading detection, AML/KYC compliance",
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
    result = json.loads(resp.read())
    print(f"Created: {result['html_url']}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    if 'already exists' in body:
        print("Repo already exists - OK")
    else:
        print(f"Error {e.code}: {body}")

# Set topics
topics_data = json.dumps({
    "names": ["financial-intelligence","market-surveillance","fintech","forensic-accounting",
              "aml","kyc","cortex","intelligence-platform","sec-compliance","insider-trading",
              "fraud-detection","regtech","financial-crime","sanctions","dodd-frank"]
}).encode()
topics_req = urllib.request.Request(
    'https://api.github.com/repos/fatcrapinmybutt/cortex-finance/topics',
    data=topics_data,
    method='PUT',
    headers={
        'Authorization': f'token {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github+json'
    }
)
try:
    resp2 = urllib.request.urlopen(topics_req)
    print(f"Topics set: {json.loads(resp2.read())['names']}")
except Exception as e:
    print(f"Topics error: {e}")
