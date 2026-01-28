#!/usr/bin/env python3

from __future__ import annotations

import getpass
import imaplib
from pathlib import Path
from typing import Any

import yaml


CONFIG_PATH = Path("config.yaml")


def load_config(path: Path) -> dict[str, Any]:
    """Load YAML configuration from disk."""
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def connect_imap(cfg: dict) -> imaplib.IMAP4_SSL:
    """Create an SSL IMAP connection and authenticate."""
    imap_cfg = cfg["imap"]
    password = getpass.getpass("IMAP password: ")

    client = imaplib.IMAP4_SSL(
        imap_cfg["host"],
        imap_cfg.get("port", 993),
    )
    client.login(imap_cfg["user"], password)
    return client


def main() -> None:
    cfg = load_config(CONFIG_PATH)

    try:
        client = connect_imap(cfg)
        print("Connection: OK")
    except imaplib.IMAP4.error as e:
        msg = e.args[0]
        if isinstance(msg, bytes):
            msg = msg.decode(errors="replace")
            print(msg)
    return
    


if __name__ == "__main__":
    main()
