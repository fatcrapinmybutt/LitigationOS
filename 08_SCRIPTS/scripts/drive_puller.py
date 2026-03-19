
import os, sys, csv, io, json, re, time
from typing import Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import google.auth.exceptions
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
CREDS_DIR = os.path.join(os.path.dirname(__file__), 'creds')

def parse_file_id(file_id_or_url: str) -> str:
    s = file_id_or_url.strip()
    if s.startswith('http'):
        # extract /d/<id>/ or id=<id>
        m = re.search(r'/d/([a-zA-Z0-9_-]+)', s)
        if m:
            return m.group(1)
        m = re.search(r'id=([a-zA-Z0-9_-]+)', s)
        if m:
            return m.group(1)
        raise ValueError(f"Could not parse file id from URL: {s}")
    return s

def get_credentials(service_account_file: Optional[str] = None):
    creds = None
    if service_account_file and os.path.exists(service_account_file):
        creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=SCOPES)
    else:
        token_path = os.path.join(CREDS_DIR, 'token.pickle')
        client_secret = os.path.join(CREDS_DIR, 'client_secret.json')
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(client_secret):
                    raise FileNotFoundError(f"Missing OAuth client at {client_secret}. Place your Google OAuth client JSON there or use a service account.")
                flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
    return creds

def ensure_dir(path):
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def download_file(service, file_id: str, out_path: str, export_mime_override: Optional[str] = None):
    meta = service.files().get(fileId=file_id, fields="id,name,mimeType,modifiedTime,size").execute()
    mime = meta.get('mimeType')
    name = meta.get('name')
    is_google_doc = mime.startswith('application/vnd.google-apps')
    if is_google_doc:
        export_mime = export_mime_override or 'text/html'
        request = service.files().export_media(fileId=file_id, mimeType=export_mime)
    else:
        request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(out_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        # you could print progress here if you like
    return { "id": file_id, "name": name, "mimeType": mime, "out": out_path, "modifiedTime": meta.get('modifiedTime'), "size": meta.get('size') }

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Google Drive Puller → artifacts/")
    ap.add_argument("--manifest", default=os.path.join(os.path.dirname(__file__), "drive_manifest.csv"))
    ap.add_argument("--artifacts-dir", default=os.path.join(os.path.dirname(__file__), "..", "artifacts"))
    ap.add_argument("--service-account", default=os.path.join(os.path.dirname(__file__), "creds", "service_account.json"))
    args = ap.parse_args()

    # auth
    try:
        creds = get_credentials(service_account_file=args.service_account if os.path.exists(args.service_account) else None)
    except Exception as e:
        print("Auth failed:", e)
        sys.exit(1)
    service = build('drive', 'v3', credentials=creds, cache_discovery=False)

    ensure_dir(args.artifacts_dir)

    report = []
    with open(args.manifest, newline='', encoding='utf-8') as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            fid = parse_file_id(row['file_id_or_url'])
            target_name = row['target_filename'] or "downloaded_" + fid
            subdir = row.get('target_subdir','').strip()
            export_mime = (row.get('export_mime_override') or '').strip() or None
            out_dir = os.path.join(args.artifacts_dir, subdir) if subdir else args.artifacts_dir
            ensure_dir(out_dir)
            out_path = os.path.join(out_dir, target_name)
            try:
                info = download_file(service, fid, out_path, export_mime_override=export_mime)
                report.append({**info, "status": "ok"})
            except Exception as e:
                report.append({"id": fid, "out": out_path, "error": str(e), "status": "error"})
    with open(os.path.join(args.artifacts_dir, "drive_pull_report.json"), "w", encoding="utf-8") as rf:
        json.dump(report, rf, indent=2)
    print(f"Wrote report with {len(report)} entries to artifacts/drive_pull_report.json")

if __name__ == "__main__":
    main()
