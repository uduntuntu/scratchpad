#!/usr/bin/env python3
from __future__ import annotations

import getpass
import imaplib
import sys
from pathlib import Path
from typing import Any
import yaml
import email
from email.utils import parsedate_to_datetime

CONFIG_PATH = Path("config.yaml")
MAX_MATCHES = 30


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def connect_imap() -> imaplib.IMAP4_SSL:
    cfg = load_config(CONFIG_PATH)
    imap_cfg = cfg["imap"]

    password = getpass.getpass("IMAP password: ")
    try:
        client = imaplib.IMAP4_SSL(
            imap_cfg["host"],
            imap_cfg.get("port", 993),
        )
        client.login(imap_cfg["user"], password)
    except imaplib.IMAP4.error as e:
        msg = e.args[0]
        if isinstance(msg, bytes):
            msg = msg.decode(errors="replace")
        print(msg)
        sys.exit(1)

    return client


def fetch_mailboxes(client: imaplib.IMAP4) -> list[str]:
    status, data = client.list()
    if status != "OK":
        raise RuntimeError("IMAP LIST failed")

    mailboxes: list[str] = []
    for raw in data:
        if raw is None:
            continue

        text = raw.decode("utf-8", errors="replace")
        # IMAP LIST: (<flags>) "<delimiter>" <mailbox>
        parts = text.split(" ", 2)
        if len(parts) < 3:
            continue

        mailbox = parts[2].strip().strip('"')
        mailboxes.append(mailbox)

    return mailboxes


def filter_by_substring(items: list[str], needle: str) -> list[str]:
    return [item for item in items if needle in item]


def search_by_header(
    client: imaplib.IMAP4,
    header: str,
    needle: str,
) -> None:
    try:
        status, data = client.search(
            None,
            "HEADER",
            header,
            f'"{needle}"',
        )
    except imaplib.IMAP4.error as e:
        print(f"SEARCH failed: {e}")
        return

    if status != "OK":
        print("SEARCH failed")
        return

    msg_ids = data[0].split()
    if not msg_ids:
        print("No matches.")
        return

    for msg_id in msg_ids:
        status, msg_data = client.fetch(
            msg_id,
            "(BODY.PEEK[HEADER.FIELDS (DATE SUBJECT)])",
        )
        if status != "OK":
            continue

        raw_headers = msg_data[0][1]
        msg = email.message_from_bytes(raw_headers)

        date_hdr = msg.get("Date")
        if date_hdr:
            try:
                dt = parsedate_to_datetime(date_hdr)
                date_str = dt.isoformat()
            except Exception:
                date_str = date_hdr
        else:
            date_str = "(no Date)"

        subject = msg.get("Subject", "(no Subject)")
        print(f"{date_str} | {subject}")



def main() -> None:
    client = connect_imap()
    print("Connection: OK")

    mailboxes = fetch_mailboxes(client)
    matches: list[str] = []

    while len(matches) != 1:
        user_input = input("Mailbox substring: ").strip()
        if not user_input:
            continue

        matches = filter_by_substring(mailboxes, user_input)

        if len(matches) == 0:
            print("No matches.")
        elif len(matches) > MAX_MATCHES:
            print(
                f"Too many matches ({len(matches)}). "
                "Please refine your input."
            )
        elif len(matches) > 1:
            for m in matches:
                print(m)
            print("Refine substring.")

    mailbox = matches[0]
    print(f"Selected mailbox: {mailbox}")

    client.select(mailbox, readonly=True)
    
    print("Select search header:")
    print("1. TO")
    print("2. X-Rspam-Report")

    while True:
        choice = input("Choice (1–2): ").strip()
        if choice == "1":
            search_header = "TO"
            break
        if choice == "2":
            search_header = "X-Rspam-Report"
            break
        print("Invalid choice.")

    # main search loop
    while True:
        needle = input(f"Search {search_header} substring (or 'exit'): ").strip()
        if not needle:
            continue
        if needle.lower() == "exit":
            break

        if search_header == "TO":
            try:
                status, data = client.search(None, "TO", f'"{needle}"')
            except imaplib.IMAP4.error as e:
                print(f"SEARCH failed: {e}")
                continue

            msg_ids = data[0].split()
            if not msg_ids:
                print("No matches.")
                continue

            for msg_id in msg_ids:
                status, msg_data = client.fetch(
                    msg_id,
                    "(BODY.PEEK[HEADER.FIELDS (DATE SUBJECT)])",
                )
                if status != "OK":
                    continue
                raw_headers = msg_data[0][1]
                msg = email.message_from_bytes(raw_headers)
                date_hdr = msg.get("Date")
                date_str = (
                    parsedate_to_datetime(date_hdr).isoformat()
                    if date_hdr else "(no Date)"
                )
                subject = msg.get("Subject", "(no Subject)")
                print(f"{date_str} | {subject}")

        else:
            search_by_header(
                client,
                header="X-Rspam-Report",
                needle=needle,
            )

    client.logout()


if __name__ == "__main__":
    main()
