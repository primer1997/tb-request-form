#!/usr/bin/env python3
"""Deploy the NTEP Request Form web app as a GitHub Pages *project site*.

Creates repo <login>/ntep-form (if needed), pushes index.html, enables Pages,
so the app is live at https://<login>.github.io/ntep-form/ — free forever.
Uses the user-connected custom.github credential via dynamic_credentials.
"""
import argparse, base64, json, os, sys, urllib.request, urllib.error

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response

API = "https://api.github.com"
ALLOWED = ["api.github.com"]
CRED = "custom.github"
TIMEOUT = 180
REPO_NAME = "tb-request-form"


def req(method, url, data=None, headers=None):
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("X-GitHub-Api-Version", "2022-11-28")
    for k, v in (headers or {}).items():
        r.add_header(k, v)
    add_surrogate_to_request(r, CRED, entry_name="access_token", allowed_hosts=ALLOWED)
    try:
        return urllib.request.urlopen(r, timeout=TIMEOUT)
    except urllib.error.HTTPError as e:
        body = e.read()[:800]
        raise SystemExit(f"{method} {url} -> {e.code}: {body!r}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="folder containing index.html")
    args = ap.parse_args()

    login = read_json_response(req("GET", f"{API}/user"))["login"]
    print(f"github user: {login}", flush=True)

    # Ensure repo exists
    try:
        read_json_response(req("GET", f"{API}/repos/{login}/{REPO_NAME}"))
        print(f"repo exists: {login}/{REPO_NAME}", flush=True)
    except SystemExit as e:
        if "404" not in str(e):
            raise
        body = json.dumps({
            "name": REPO_NAME, "private": False, "auto_init": True,
            "description": "NTEP Smart Form — fill \u0026 export",
        }).encode()
        read_json_response(req("POST", f"{API}/user/repos", data=body,
                               headers={"Content-Type": "application/json"}))
        print(f"repo created: {login}/{REPO_NAME}", flush=True)

    # Push files (contents API, one file at a time)
    files = {}
    for dirpath, _dirs, names in os.walk(args.dir):
        for n in names:
            full = os.path.join(dirpath, n)
            rel = os.path.relpath(full, args.dir).replace(os.sep, "/")
            with open(full, "rb") as f:
                files[rel] = f.read()
    files[".nojekyll"] = b""

    for rel, content in files.items():
        sha = None
        try:
            existing = read_json_response(
                req("GET", f"{API}/repos/{login}/{REPO_NAME}/contents/{rel}"))
            sha = existing.get("sha")
        except SystemExit as e:
            if "404" not in str(e):
                raise
        payload = {
            "message": f"Deploy TB Request Form ({rel})",
            "content": base64.b64encode(content).decode(),
        }
        if sha:
            payload["sha"] = sha
        read_json_response(req("PUT", f"{API}/repos/{login}/{REPO_NAME}/contents/{rel}",
                               data=json.dumps(payload).encode(),
                               headers={"Content-Type": "application/json"}))
        print(f"pushed: {rel} ({len(content)} bytes)", flush=True)

    # Enable Pages (build_type legacy, source branch main)
    try:
        read_json_response(req("GET", f"{API}/repos/{login}/{REPO_NAME}/pages"))
        print("Pages already enabled", flush=True)
    except SystemExit as e:
        if "404" not in str(e):
            raise
        read_json_response(req("POST", f"{API}/repos/{login}/{REPO_NAME}/pages",
                               data=json.dumps(
                                   {"source": {"branch": "main", "path": "/"}}).encode(),
                               headers={"Content-Type": "application/json"}))
        print("Pages enabled", flush=True)

    print(f"LIVE URL: https://{login}.github.io/{REPO_NAME}/", flush=True)


if __name__ == "__main__":
    main()
