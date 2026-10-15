#!/usr/bin/env python3
"""DE: Prüft eingecheckte Dateien auf typische private Gerätewerte.
EN: Scan tracked files for common private device data before publication.
Heuristic only / Nur eine Heuristik: manual review is still required.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

PRIVATE_IP = re.compile(
    r"\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"
)
DEVICE_MAC = re.compile(r"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b")
PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
SAFE_MAC_PREFIX = "02:00:00:00:00:"
BLOCKED_BASENAMES = {"secrets.yaml", ".env", "id_rsa", "id_ed25519"}
BLOCKED_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".bin", ".elf"}

def main() -> int:
    tracked = subprocess.check_output(["git", "ls-files", "-z"]).split(b"\0")
    problems: list[str] = []
    inspected = 0
    for raw in tracked:
        if not raw:
            continue
        filename = Path(raw.decode("utf-8"))
        if filename.name.lower() in BLOCKED_BASENAMES or filename.suffix.lower() in BLOCKED_SUFFIXES:
            problems.append(f"{filename}: private file type / privater Dateityp")
            continue
        if not filename.is_file():
            continue
        contents = filename.read_bytes()
        if b"\0" in contents[:8192]:
            problems.append(f"{filename}: binary tracked file / binaere Datei im Repository")
            continue
        inspected += 1
        for number, line in enumerate(contents.decode("utf-8", errors="replace").splitlines(), 1):
            if PRIVATE_IP.search(line):
                problems.append(f"{filename}:{number}: private LAN address / interne IP")
            if PRIVATE_KEY.search(line):
                problems.append(f"{filename}:{number}: private key marker / privater Schluessel")
            for match in DEVICE_MAC.finditer(line):
                if not match.group().upper().startswith(SAFE_MAC_PREFIX):
                    problems.append(f"{filename}:{number}: non-example MAC / echte oder nicht freigegebene MAC")
    if problems:
        print("FAIL / FEHLER: Potential privacy exposures (values deliberately hidden):")
        print("\n".join(problems))
        return 1
    print(f"PASS / BESTANDEN: {inspected} tracked text files scanned; no recognized private identifiers.")
    print("Manual review and separate Git history review remain required. / History gesondert pruefen.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
