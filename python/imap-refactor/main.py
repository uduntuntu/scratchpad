#!/usr/bin/env python3
from __future__ import annotations
import getpass
import imaplib
import sys
from pathlib import Path
from typing import Any
import yaml
import email
from email.header import decode_header
from imapclient import IMAPClient
from imapclient import imap_utf7

CONFIG_PATH = Path("config.yaml")

# encode/decode helpers
def decode_imap_utf7(raw: bytes) -> str:
    return imap_utf7.decode(raw)

def encode_imap_utf7(text: str) -> bytes:
    return imap_utf7.encode(text)


def decode_mime_header(val: str) -> str:
    """Decodes MIME-encoded headers to UTF-8, unknown charsets fallback to latin1."""
    decoded = ""
    for part, charset in decode_header(val):
        if isinstance(part, bytes):
            try:
                decoded += part.decode(charset or "utf-8", errors="replace")
            except (LookupError, TypeError):
                decoded += part.decode("latin1", errors="replace")
        else:
            decoded += part
    return decoded

def filter_by_substring(items: set[bytes], needle: str) -> set[bytes]:
    """
    Returns subset of raw bytes where decoded item contains the Unicode needle.
    Works for mailbox selection or any IMAP raw-byte sets.
    """
    result: set[bytes] = set()
    for item in items:
        decoded = decode_imap_utf7(item)
        if needle in decoded:
            result.add(item)  # raw bytes IMAP-ready
    return result

# --- load config ---
def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)

# --- connect IMAP ---
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

# --- fetch mailboxes ---
def fetch_mailboxes(client: imaplib.IMAP4) -> set[bytes]:
    status, data = client.list()
    if status != "OK":
        raise RuntimeError("IMAP LIST failed")

    mailboxes: set[bytes] = set()
    for raw in data:
        if not raw:
            continue
        mbx = raw.rsplit(b" ", 1)[-1].strip()
        if mbx.startswith(b'"') and mbx.endswith(b'"'):
            mbx = mbx[1:-1]
        mailboxes.add(mbx)
    return mailboxes

# --- fetch all headers from a mailbox ---
def fetch_headers(client: imaplib.IMAP4, mailbox: bytes) -> dict[bytes, dict[str, str]]:
    """
    Fetches all message headers from the selected mailbox.
    Returns dict: {msg_uid: {header: value, ...}}, headers decoded to UTF-8.
    """
    client.select(mailbox, readonly=True)
    status, data = client.search(None, "ALL")
    if status != "OK":
        raise RuntimeError("IMAP SEARCH failed")

    msg_ids = data[0].split()
    headers_by_uid: dict[bytes, dict[str, str]] = {}

    for uid in msg_ids:
        status, msg_data = client.fetch(uid, "(BODY.PEEK[HEADER])")
        if status != "OK":
            continue
        raw_headers = msg_data[0][1]
        msg = email.message_from_bytes(raw_headers)
        decoded_headers = {k: decode_mime_header(v) for k, v in msg.items()}
        headers_by_uid[uid] = decoded_headers

    return headers_by_uid

# --- header helpers ---
def all_uids(headers_by_uid: dict[bytes, dict[str, str]]) -> set[bytes]:
    return set(headers_by_uid.keys())

def list_unique_addresses(headers_by_uid: dict[bytes, dict[str, str]], header: str) -> set[str]:
    unique: set[str] = set()
    for hdrs in headers_by_uid.values():
        val = hdrs.get(header, "")
        if val:
            addresses = [addr.strip() for addr in val.split(",")]
            unique.update(addresses)
    return unique

def list_headers(headers_by_uid: dict[bytes, dict[str, str]]) -> set[str]:
    all_headers: set[str] = set()
    for hdrs in headers_by_uid.values():
        all_headers.update(hdrs.keys())
    return all_headers

def filter_by_header_value(headers_by_uid: dict[bytes, dict[str, str]], header: str, needle: str) -> set[bytes]:
    """Returns UID set where the header contains the Unicode needle."""
    result: set[bytes] = set()
    for uid, hdrs in headers_by_uid.items():
        val = hdrs.get(header, "")
        if needle in val:
            result.add(uid)
    return result

def print_messages(headers_by_uid: dict[bytes, dict[str, str]], uid_set: set[bytes]) -> None:
    for uid in sorted(uid_set):
        hdrs = headers_by_uid[uid]
        date = hdrs.get("Date", "(no Date)")
        from_ = hdrs.get("From", "(no From)")
        to = hdrs.get("To", "(no To)")
        subject = hdrs.get("Subject", "(no Subject)")
        print(f"{date} | {from_} -> {to}: {subject}")

# --- main ---
def main() -> None:
    client = connect_imap()
    print("Connection: OK")

    mailboxes = fetch_mailboxes(client)
    mailbox_bytes: bytes | None = None

    # --- mailbox selection ---
    while mailbox_bytes is None:
        needle = input("Select mailbox (partial name OK): ").strip()
        matches = filter_by_substring(mailboxes, needle)

        if not matches:
            print("No matches found. Try again.")
        elif len(matches) > 1:
            print("Multiple matches found:")
            for mb in sorted(matches):
                print(f"- {decode_imap_utf7(mb)}")
            print("Enter a more precise name.")
        else:
            mailbox_bytes = next(iter(matches))
            print(f"Selected mailbox: {decode_imap_utf7(mailbox_bytes)}")

    headers_by_uid = fetch_headers(client, mailbox_bytes)
    uid_set: set[bytes] = set(headers_by_uid.keys())
    print(f"Fetched {len(uid_set)} messages from {decode_imap_utf7(mailbox_bytes)}")

    # --- main menu ---
    while True:
        print("\nMenu:")
        print("1. List unique senders")
        print("2. List unique recipients")
        print("3. List headers")
        print("4. Filter UID set by header")
        print("5. Print filtered set")
        print("0. Exit")
        choice = input("Choice: ").strip()

        if choice == "0":
            break
        elif choice == "1":
            senders = list_unique_addresses(headers_by_uid, "From")
            print(f"Unique senders ({len(senders)}):")
            for s in sorted(senders):
                print(s)
        elif choice == "2":
            recipients = list_unique_addresses(headers_by_uid, "To")
            print(f"Unique recipients ({len(recipients)}):")
            for r in sorted(recipients):
                print(r)
        elif choice == "3":
            hdrs = list_headers(headers_by_uid)
            print(f"Header fields ({len(hdrs)}):")
            for h in sorted(hdrs):
                print(h)
        elif choice == "4":
            reset = input("Reset UID set before filtering? (y/N) ").strip().lower()
            if reset == "y":
                uid_set = all_uids(headers_by_uid)
            header = input("Header: ").strip()
            needle = input("Value to search: ").strip()
            filtered = filter_by_header_value(headers_by_uid, header, needle)
            uid_set &= filtered
            print(f"Filtered, {len(uid_set)} messages remaining")
        elif choice == "5":
            print_messages(headers_by_uid, uid_set)
        else:
            print("Invalid choice")

    client.logout()

if __name__ == "__main__":
    main()
