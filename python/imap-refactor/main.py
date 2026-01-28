#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml
import getpass
import imaplib

CONFIG_PATH = Path("config.yaml")


def load_config(path: Path) -> dict[str, Any]:
    """Load YAML configuration from disk."""
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def connect_imap() -> imaplib.IMAP4_SSL:
    """Load config, connect to IMAP server and authenticate."""
    cfg = load_config(CONFIG_PATH)
    imap_cfg = cfg["imap"]

    password = getpass.getpass("IMAP password: ")

    try:
        client = imaplib.IMAP4_SSL(
            imap_cfg["host"],
            imap_cfg.get("port", 993),
        )
        client.login(imap_cfg["user"], password)
        print("Connection: OK")
    except imaplib.IMAP4.error as e:
        msg = e.args[0]
        if isinstance(msg, bytes):
            msg = msg.decode(errors="replace")
        print(msg)
        sys.exit(1)

    return client


def main() -> None:
    client = connect_imap()
    client.logout


if __name__ == "__main__":
    main()
