#!/usr/bin/env python3
"""
Enter the Drift — project_generator.py
--------------------------------------
Paste a GitHub repository link and this tool reads the project itself
(name, description, topics/tags, README, languages, stars) and writes a
card into ../data/projects.json, which the About-Me page renders.

Zero external dependencies — standard library only.

Usage
-----
    python project_generator.py https://github.com/ArmaLv/DialogueSystem
    python project_generator.py ArmaLv/StyTab ArmaLv/DialogueSystem
    python project_generator.py --list
    python project_generator.py --remove StyTab

Options
-------
    --out PATH        Path to projects.json (default: ../data/projects.json)
    --list            Print the projects currently stored, then exit.
    --remove NAME     Remove a stored project by name, then exit.
    --dry-run         Fetch and print the card as JSON, but don't save.

Rate limits
-----------
Unauthenticated GitHub API allows ~60 requests/hour. To raise that, set a
token (needs no scopes for public repos):

    Windows (PowerShell):  $env:GITHUB_TOKEN="ghp_xxx"
    macOS/Linux (bash):    export GITHUB_TOKEN=ghp_xxx
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

API = "https://api.github.com"
DEFAULT_OUT = Path(__file__).resolve().parent.parent / "data" / "projects.json"

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

C_GOLD = "\033[38;5;179m"
C_DIM = "\033[2m"
C_RED = "\033[31m"
C_OK = "\033[32m"
C_END = "\033[0m"


def glow(msg: str, color: str = C_GOLD) -> None:
    line = f"{color}{msg}{C_END}"
    try:
        print(line)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "ascii"
        print(line.encode(enc, "replace").decode(enc, "replace"))


# github api
def _request(url: str) -> tuple[int, dict | list | None]:
    """Return (status_code, parsed_json_or_None)."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "enter-the-drift-generator",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", "replace")
            return resp.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as e:
        return e.code, None
    except (urllib.error.URLError, TimeoutError) as e:
        glow(f"  ! network error: {e}", C_RED)
        return 0, None


def parse_repo(link: str) -> tuple[str, str] | None:
    """Accept full URLs or 'owner/repo' and return (owner, repo)."""
    link = link.strip().rstrip("/")
    m = re.search(r"github\.com[:/]+([^/]+)/([^/]+?)(?:\.git)?$", link)
    if m:
        return m.group(1), m.group(2)
    m = re.fullmatch(r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", link)
    if m:
        return m.group(1), m.group(2)
    return None


def first_paragraph(markdown: str, limit: int = 240) -> str:
    """Pull a human-readable excerpt out of a README."""
    text = markdown
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)

    for raw in text.splitlines():
        line = raw.strip().lstrip("#>*-+ ").strip()
        # skip headings, dividers, shields, empty lines
        if not line or set(line) <= {"=", "-", "_"}:
            continue
        if "shields.io" in line or line.startswith("|"):
            continue
        line = re.sub(r"[*_`]", "", line)
        if len(line) > limit:
            line = line[: limit - 1].rsplit(" ", 1)[0] + "…"
        return line
    return ""


def language_split(raw: dict) -> list[dict]:
    """Convert {lang: bytes} into [{name, percent}] sorted desc."""
    total = sum(raw.values()) or 1
    langs = [
        {"name": name, "percent": round(byts / total * 100)}
        for name, byts in sorted(raw.items(), key=lambda kv: kv[1], reverse=True)
    ]
    return [l for l in langs if l["percent"] > 0][:6]


def fetch_project(owner: str, repo: str) -> dict | None:
    glow(f"  ✦ reading {owner}/{repo} …", C_DIM)

    status, meta = _request(f"{API}/repos/{owner}/{repo}")
    if status == 403:
        glow("  ! rate-limited by GitHub. Set GITHUB_TOKEN and retry.", C_RED)
        return None
    if status == 404 or not isinstance(meta, dict):
        glow(f"  ! repo not found: {owner}/{repo}", C_RED)
        return None

    # languages
    _, lang_raw = _request(f"{API}/repos/{owner}/{repo}/languages")
    languages = language_split(lang_raw if isinstance(lang_raw, dict) else {})

    # readme (base64)
    readme_excerpt = ""
    _, readme = _request(f"{API}/repos/{owner}/{repo}/readme")
    if isinstance(readme, dict) and readme.get("content"):
        try:
            decoded = base64.b64decode(readme["content"]).decode("utf-8", "replace")
            readme_excerpt = first_paragraph(decoded)
        except (ValueError, UnicodeDecodeError):
            pass

    tags = meta.get("topics") or []
    if not tags and meta.get("language"):
        tags = [meta["language"].lower()]

    return {
        "name": meta.get("name", repo),
        "url": meta.get("html_url", f"https://github.com/{owner}/{repo}"),
        "description": (meta.get("description") or "").strip(),
        "tags": tags,
        "stars": meta.get("stargazers_count", 0),
        "languages": languages,
        "readme": readme_excerpt,
        "generated": date.today().isoformat(),
    }


# storage
def load_store(out: Path) -> list[dict]:
    if out.exists():
        try:
            data = json.loads(out.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else data.get("projects", [])
        except (json.JSONDecodeError, OSError):
            glow(f"  ! {out} was unreadable — starting fresh.", C_RED)
    return []


def save_store(out: Path, projects: list[dict]) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(projects, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def upsert(projects: list[dict], card: dict) -> list[dict]:
    """Replace an existing project with the same name, else append."""
    key = card["name"].lower()
    for i, p in enumerate(projects):
        if p.get("name", "").lower() == key:
            projects[i] = card
            return projects
    projects.append(card)
    return projects


# cli
def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Generate About-Me project cards from GitHub links.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("links", nargs="*", help="GitHub URLs or owner/repo")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="projects.json path")
    ap.add_argument("--list", action="store_true", help="list stored projects")
    ap.add_argument("--remove", metavar="NAME", help="remove a project by name")
    ap.add_argument("--dry-run", action="store_true", help="print card, don't save")
    args = ap.parse_args(argv)

    glow("\n  ✦ Enter the Drift — project generator ✦\n")

    # --list
    if args.list:
        store = load_store(args.out)
        if not store:
            glow("  (archive is empty)", C_DIM)
        for p in store:
            langs = ", ".join(l["name"] for l in p.get("languages", []))
            glow(f"  • {p['name']}  —  {langs or 'no languages'}")
        return 0

    # --remove
    if args.remove:
        store = load_store(args.out)
        before = len(store)
        store = [p for p in store if p.get("name", "").lower() != args.remove.lower()]
        if len(store) == before:
            glow(f"  ! no project named '{args.remove}'", C_RED)
            return 1
        save_store(args.out, store)
        glow(f"  ✓ removed '{args.remove}'", C_OK)
        return 0

    if not args.links:
        ap.print_help()
        return 1

    store = [] if args.dry_run else load_store(args.out)
    added = 0

    for link in args.links:
        parsed = parse_repo(link)
        if not parsed:
            glow(f"  ! can't parse a repo from: {link}", C_RED)
            continue
        card = fetch_project(*parsed)
        if not card:
            continue

        if args.dry_run:
            print(json.dumps(card, indent=2, ensure_ascii=False))
        else:
            store = upsert(store, card)
            added += 1
        glow(f"  ✓ {card['name']} drawn from the drift", C_OK)

    if not args.dry_run and added:
        save_store(args.out, store)
        glow(f"\n  ✦ saved {added} project(s) → {args.out}\n")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        glow("\n  interrupted.", C_RED)
        sys.exit(130)
