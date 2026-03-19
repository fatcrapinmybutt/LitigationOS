#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/drive"]

def load_cfg(cfg_path: Path) -> dict:
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}

def get_service(cfg: dict, base_dir: Path):
    drive_cfg = cfg.get("drive", {}) or {}
    cred_path = base_dir / str(drive_cfg.get("credentials_json", "credentials.json"))
    token_path = base_dir / str(drive_cfg.get("token_json", "token.json"))

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not cred_path.exists():
                raise FileNotFoundError(f"Missing credentials file: {cred_path}")
            flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return build("drive", "v3", credentials=creds, cache_discovery=False)

def main() -> int:
    ap = argparse.ArgumentParser(description="Drive rename test with rollback")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--file-id", required=True)
    ap.add_argument("--new-name", required=True)
    ap.add_argument("--rollback", action="store_true", help="Rename back to original after test")
    args = ap.parse_args()

    base_dir = Path(__file__).resolve().parent
    cfg = load_cfg(base_dir / args.config)
    svc = get_service(cfg, base_dir)

    fid = args.file_id.strip()
    new_name = args.new_name.strip()
    if not fid or not new_name:
        return 1

    try:
        meta = svc.files().get(fileId=fid, fields="id,name,mimeType,parents").execute()
        old_name = meta.get("name","")
        print(json.dumps({"fileId": fid, "old_name": old_name, "new_name": new_name}, indent=2))

        svc.files().update(fileId=fid, body={"name": new_name}, fields="id,name").execute()
        print("rename_ok")

        if args.rollback:
            svc.files().update(fileId=fid, body={"name": old_name}, fields="id,name").execute()
            print("rollback_ok")

        return 0
    except HttpError as e:
        print(f"http_error: {e}")
        return 2
    except Exception as e:
        print(f"error: {e}")
        return 3

if __name__ == "__main__":
    raise SystemExit(main())
