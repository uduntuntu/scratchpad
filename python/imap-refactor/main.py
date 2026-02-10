#!/usr/bin/env python3
from __future__ import annotations
from backend import IMAPBackend
from helpers import (
    all_uids,
    list_unique_addresses,
    available_headers,
    filter_by_header_value,
    print_messages,
    select_unique,
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

    # --- select mailbox  ---
    mailboxes = backend.list_mailboxes(client)
    mailbox = None

    while not mailbox:
        needle = None
        needle = input("Select mailbox (partial name OK or 'exit'): ").strip()
        if needle.lower() == "exit":
            client.logout()
            break
        else:
            mailbox = select_unique(mailboxes, needle)

    # --- fetch headers ---
    headers_by_uid = backend.fetch_headers(client, mailbox)
    uid_set: set[bytes] = set(headers_by_uid.keys())
    headers = available_headers(headers_by_uid,uid_set)
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
            print(f"Header fields ({len(headers)}):")
            for h in sorted(headers):
                print(h)
        elif choice == "4":
            header = None
            reset = input("Reset UID set before filtering? (y/N) ").strip().lower()
            if reset == "y":
                uid_set = all_uids(headers_by_uid)
            
            while not header:
                needle = None
                needle = input("Select header (partial name OK or 'exit'): ").strip()
                if needle.lower() == "exit":
                    client.logout()
                    break
                else:
                    header = select_unique(headers, needle)
            
            needle = input("Filter by value): ").strip()
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
