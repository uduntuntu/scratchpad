#!/usr/bin/env python3
from __future__ import annotations
from backend import IMAPBackend
from helpers import (
    filter_by_substring,
    all_uids,
    list_unique_addresses,
    list_headers,
    filter_by_header_value,
    print_messages,
)
import getpass


def main() -> None:
    # --- credentials ---
    host = input("IMAP server host: ").strip()
    user = input("Username: ").strip()
    password = getpass.getpass("Password: ")

    backend = IMAPBackend(host, user, password)
    client = backend.connect()
    print("Connection: OK")

    # --- fetch mailboxes ---
    mailboxes = backend.list_mailboxes(client)
    mailbox: str | None = None

    while mailbox is None:
        needle = input("Select mailbox (partial name OK or 'exit'): ").strip()
        if needle.lower() == "exit":
            client.logout()
            return

        matches = filter_by_substring(mailboxes, needle)
        if not matches:
            print("No matches found. Try again.")
        elif len(matches) > 1:
            print("Multiple matches found:")
            for mb in sorted(matches):
                print(f"- {mb}")
            print("Enter a more precise name.")
        else:
            mailbox = next(iter(matches))
            print(f"Selected mailbox: {mailbox}")

    # --- fetch headers ---
    headers_by_uid = backend.fetch_headers(client, mailbox)
    uid_set: set[bytes] = set(headers_by_uid.keys())
    print(f"Fetched {len(uid_set)} messages from {mailbox}")

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
