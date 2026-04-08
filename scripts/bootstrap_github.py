from __future__ import annotations

import base64
import json
import os
import subprocess
from pathlib import Path

import httpx
from nacl import encoding, public


REPO_NAME = "film-intelligence-agent"
OWNER = "lodewijkvos"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def create_repo(token: str) -> str:
    response = httpx.post(
        "https://api.github.com/user/repos",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        json={"name": REPO_NAME, "private": True, "auto_init": False},
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()["clone_url"]


def get_repo_public_key(token: str) -> dict:
    response = httpx.get(
        f"https://api.github.com/repos/{OWNER}/{REPO_NAME}/actions/secrets/public-key",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


def encrypt_value(public_key_base64: str, value: str) -> str:
    public_key = public.PublicKey(public_key_base64.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def put_secret(token: str, secret_name: str, secret_value: str, key_id: str, public_key: str) -> None:
    encrypted = encrypt_value(public_key, secret_value)
    response = httpx.put(
        f"https://api.github.com/repos/{OWNER}/{REPO_NAME}/actions/secrets/{secret_name}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        json={"encrypted_value": encrypted, "key_id": key_id},
        timeout=30.0,
    )
    response.raise_for_status()


def main() -> None:
    token = os.environ["GITHUB_TOKEN"]
    clone_url = create_repo(token)
    if not Path(".git").exists():
        run(["git", "init"])
        run(["git", "branch", "-M", "main"])
        run(["git", "remote", "add", "origin", clone_url])
    run(["git", "add", "."])
    run(["git", "commit", "-m", "Initial production scaffold"])
    run(["git", "push", "-u", "origin", "main"])

    secret_source = {
        "SUPABASE_URL": os.environ.get("SUPABASE_URL", ""),
        "SUPABASE_SERVICE_ROLE_KEY": os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""),
        "SUPABASE_DB_PASSWORD": os.environ.get("SUPABASE_DB_PASSWORD", ""),
        "NOTION_TOKEN": os.environ.get("NOTION_TOKEN", ""),
        "NOTION_PARENT_PAGE_ID": os.environ.get("NOTION_PARENT_PAGE_ID", ""),
        "RESEND_API_KEY": os.environ.get("RESEND_API_KEY", ""),
        "EMAIL_FROM": os.environ.get("EMAIL_FROM", ""),
        "EMAIL_TO": os.environ.get("EMAIL_TO", ""),
        "IMDB_PRO_USERNAME": os.environ.get("IMDB_PRO_USERNAME", ""),
        "IMDB_PRO_PASSWORD": os.environ.get("IMDB_PRO_PASSWORD", ""),
        "IMDB_PUBLIC_URL": os.environ.get("IMDB_PUBLIC_URL", ""),
    }
    public_key_payload = get_repo_public_key(token)
    for key, value in secret_source.items():
        if value:
            put_secret(
                token,
                key,
                value,
                public_key_payload["key_id"],
                public_key_payload["key"],
            )
    print(json.dumps({"repo": f"{OWNER}/{REPO_NAME}", "status": "bootstrapped"}))


if __name__ == "__main__":
    main()
